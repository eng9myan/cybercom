"""
Write a `SimResult` into the real cyshop tables for one demo tenant.

Everything the engine decided becomes ordinary business data:

    opening balances     -> StockMovement (OPENING)
    supplier deliveries  -> PurchaseOrder / PurchaseOrderLine / GoodsReceipt
    daily raw usage       -> StockMovement (ISSUE)          [aggregated per branch/day]
    daily spoilage        -> StockMovement (ADJUSTMENT)     [aggregated per branch/day]
    paid orders           -> PosSession / PosOrder / PosOrderLine / PosPayment
    crew                  -> hr.Employee

The only simulation-owned row is `SimulationRun`; every business row carries the
run tag in its reference/notes so a run can be wiped and replayed.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.catalog.models import Category, KitComponent, Product, ProductUnit, TaxClass
from apps.hr.models import Employee
from apps.identity.models import User
from apps.inventory.models import StockLevel, StockLocation, StockMovement, Warehouse
from apps.pos.models import PosOrder, PosOrderLine, PosPayment, PosSession
from apps.purchasing.models import (
    GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine, Vendor,
)
from apps.tenants.models import Branch, Company, Department, Tenant, TenantSettings

from .engine import SimResult
from .models import SimulationRun
from .scenarios import qsr as S

UTC = ZoneInfo("UTC")
D4 = Decimal("0.0001")


def _d(x) -> Decimal:
    return Decimal(str(round(float(x), 4))).quantize(D4)


class QsrSeeder:
    def __init__(self, result: SimResult, *, subdomain: str, tenant_name: str,
                 run: SimulationRun, stdout=None):
        self.r = result
        self.subdomain = subdomain
        self.tenant_name = tenant_name
        self.run = run
        self.tag = run.tag
        self.counts: dict[str, int] = defaultdict(int)
        self._out = stdout

        # lookup caches populated by _build_master
        self.tenant: Tenant | None = None
        self.companies: dict[str, Company] = {}
        self.branches: dict[str, Branch] = {}
        self.warehouses: dict[str, Warehouse] = {}
        self.main_loc: dict[str, StockLocation] = {}
        self.recv_loc: dict[str, StockLocation] = {}
        self.products: dict[tuple[str, str], Product] = {}   # (country, sku/code) -> Product
        self.vendors: dict[tuple[str, str], Vendor] = {}     # (country, supplier_key) -> Vendor
        self.cashiers: dict[str, list[User]] = {}

    def log(self, msg: str):
        if self._out:
            self._out.write(msg)

    # ------------------------------------------------------------------

    @transaction.atomic
    def wipe(self):
        """Delete a prior run's data for this tenant (keeps master data)."""
        t = Tenant.objects.filter(subdomain=self.subdomain).first()
        if not t:
            return
        tid = t.id
        PosPayment.objects.filter(tenant_id=tid).delete()
        PosOrderLine.objects.filter(tenant_id=tid).delete()
        PosOrder.objects.filter(tenant_id=tid).delete()
        PosSession.objects.filter(tenant_id=tid).delete()
        GoodsReceiptLine.objects.filter(tenant_id=tid).delete()
        GoodsReceipt.objects.filter(tenant_id=tid).delete()
        PurchaseOrderLine.objects.filter(tenant_id=tid).delete()
        PurchaseOrder.objects.filter(tenant_id=tid).delete()
        StockMovement.objects.filter(tenant_id=tid).delete()
        StockLevel.objects.filter(tenant_id=tid).delete()
        Employee.objects.filter(tenant=t).delete()
        SimulationRun.objects.filter(tenant_id=tid).exclude(pk=self.run.pk).delete()
        self.log(f"  wiped prior operational data for tenant '{self.subdomain}'")

    # ------------------------------------------------------------------

    def seed(self) -> dict:
        self._build_master()
        self._seed_opening_stock()
        self._seed_deliveries()
        self._seed_consumption()
        self._seed_orders()
        self._seed_staff()
        self.run.record_counts = dict(self.counts)
        return dict(self.counts)

    # ------------------------------------------------------------------

    def _build_master(self):
        self.tenant, created = Tenant.objects.get_or_create(
            subdomain=self.subdomain, defaults={"name": self.tenant_name},
        )
        tid = self.tenant.id
        self.run.tenant_id = tid
        self.run.save(update_fields=["tenant_id"])

        settings_obj, _ = TenantSettings.objects.get_or_create(tenant=self.tenant)
        settings_obj.currency = S.REPORTING_CURRENCY
        settings_obj.timezone = "Asia/Amman"
        settings_obj.onboarding_completed = True
        settings_obj.save()

        admin, a_created = User.objects.get_or_create(
            username=f"{self.subdomain}-ops",
            defaults={"email": f"ops@{self.subdomain}.demo", "tenant_id": tid,
                      "first_name": "Operations", "last_name": "Console", "is_staff": True},
        )
        if a_created:
            admin.set_unusable_password()   # login provisioning is a separate concern
            admin.save()

        unit_defs = {"pc": "Piece", "kg": "Kilogram", "l": "Litre", "each": "Each"}

        for c in S.COUNTRIES:
            company, _ = Company.objects.get_or_create(
                tenant_id=tid, name=f"McCybercom {c.name}",
                defaults={"country_code": c.code, "legal_name": f"McCybercom {c.name} Ltd"},
            )
            self.companies[c.code] = company

            units = {}
            for abbr, name in unit_defs.items():
                u, _ = ProductUnit.objects.get_or_create(
                    tenant_id=tid, company=company, abbreviation=abbr, defaults={"name": name},
                )
                units[abbr] = u
            tax, _ = TaxClass.objects.get_or_create(
                tenant_id=tid, company=company, code="VAT",
                defaults={"name": f"VAT {c.vat_rate}", "rate": _d(c.vat_rate)},
            )
            if tax.rate != _d(c.vat_rate):
                tax.rate = _d(c.vat_rate)
                tax.save(update_fields=["rate", "updated_at", "version"])

            categories = {}
            for cat_name in sorted({m.category for m in S.MENU} | {"Raw Materials"}):
                cat, _ = Category.objects.get_or_create(
                    tenant_id=tid, company=company, name=cat_name,
                )
                categories[cat_name] = cat

            # raw goods
            for rg in S.RAW_GOODS:
                p, _ = Product.objects.get_or_create(
                    tenant_id=tid, company=company, internal_ref=rg.sku,
                    defaults={
                        "name": rg.name, "product_type": "STORABLE",
                        "unit": units.get(rg.uom, units["pc"]), "tax_class": tax,
                        "category": categories["Raw Materials"],
                        "cost_price": _d(rg.unit_cost), "sell_price": _d(0),
                        "track_stock": True, "pos_available": False,
                        "min_stock_qty": _d(self._expected_reorder_point(rg, c)),
                    },
                )
                self.products[(c.code, rg.sku)] = p

            # menu items
            for m in S.MENU:
                p, _ = Product.objects.get_or_create(
                    tenant_id=tid, company=company, internal_ref=m.code,
                    defaults={
                        "name": m.name, "product_type": "KIT",
                        "unit": units["each"], "tax_class": tax,
                        "category": categories[m.category],
                        "cost_price": _d(self._menu_cost(m)),
                        "sell_price": _d(m.price * c.price_index),
                        "track_stock": False, "pos_available": True,
                    },
                )
                self.products[(c.code, m.code)] = p

            # BOM
            for m in S.MENU:
                kit = self.products[(c.code, m.code)]
                for sku, per in m.components.items():
                    KitComponent.objects.get_or_create(
                        product=kit, component_product=self.products[(c.code, sku)],
                        defaults={"tenant_id": tid, "quantity_per_unit": _d(per)},
                    )

            # vendors
            for sup in S.SUPPLIERS:
                v, _ = Vendor.objects.get_or_create(
                    tenant_id=tid, company=company, name=f"{sup.name} - {c.name}",
                    defaults={"code": f"{sup.key.upper()}-{c.code}", "currency": S.REPORTING_CURRENCY,
                              "notes": f"lead time {sup.lead_time_days}d"},
                )
                self.vendors[(c.code, sup.key)] = v

            # branches + warehouses
            for br in c.branches:
                branch, _ = Branch.objects.get_or_create(
                    tenant_id=tid, company=company, name=br.name,
                    defaults={"address": f"{br.city}, {c.name}", "timezone": c.timezone},
                )
                self.branches[br.code] = branch
                wh, _ = Warehouse.objects.get_or_create(
                    tenant_id=tid, company=company, code=f"WH-{br.code}",
                    defaults={"name": f"{br.city} store room", "branch": branch},
                )
                self.warehouses[br.code] = wh
                self.main_loc[br.code], _ = StockLocation.objects.get_or_create(
                    warehouse=wh, code="MAIN",
                    defaults={"name": "Store room", "location_type": "INTERNAL", "tenant_id": tid},
                )
                self.recv_loc[br.code], _ = StockLocation.objects.get_or_create(
                    warehouse=wh, code="RECV",
                    defaults={"name": "Receiving", "location_type": "RECEIVING", "tenant_id": tid},
                )

                # cashier pool
                n_cash = max(2, round(S.STAFF_TEMPLATE["Cashier"]["count"] * S.TIER_FOOTFALL[br.tier]))
                pool = []
                for i in range(n_cash):
                    u, cr = User.objects.get_or_create(
                        username=f"{self.subdomain}.{br.code.lower()}.cashier{i + 1}",
                        defaults={"tenant_id": tid, "first_name": "Cashier",
                                  "last_name": f"{br.code}-{i + 1}",
                                  "email": f"{br.code.lower()}.c{i + 1}@{self.subdomain}.demo"},
                    )
                    if cr:
                        u.set_unusable_password()
                        u.save()
                    pool.append(u)
                self.cashiers[br.code] = pool

        self.counts["companies"] = Company.objects.filter(tenant_id=tid).count()
        self.counts["branches"] = Branch.objects.filter(tenant_id=tid).count()
        self.counts["products"] = Product.objects.filter(tenant_id=tid).count()
        self.counts["vendors"] = Vendor.objects.filter(tenant_id=tid).count()
        self.log(f"  master data ready: {self.counts['companies']} companies, "
                 f"{self.counts['branches']} branches, {self.counts['products']} products")

    def _menu_cost(self, m: S.MenuItem) -> float:
        return sum(S.RAW_BY_SKU[s].unit_cost * per for s, per in m.components.items())

    def _expected_daily_usage_all(self) -> dict:
        from .engine import QsrSimulator
        if not getattr(self, "_edu_cache", None):
            self._edu_cache = QsrSimulator(
                seed=self.r.seed, start_date=self.r.start_date, days=self.r.days,
                variant="baseline", volume=self.r.volume,
            )._expected_daily_usage
        return self._edu_cache

    def _expected_reorder_point(self, rg: S.RawGood, c: S.CountrySpec) -> float:
        usage = self._expected_daily_usage_all().get(rg.sku, 0.0)
        return round(usage * c.demand_index * S.REORDER_POINT_DAYS, 2)

    # ------------------------------------------------------------------

    def _seed_opening_stock(self):
        tid = self.tenant.id
        opening_dt = datetime.combine(self.r.start_date, time(6, 0), tzinfo=UTC) - timedelta(hours=6)
        n = 0
        for op in self.r.opening:
            if op.qty <= 0:
                continue
            country = op.branch_code.split("-")[0]
            mv = StockMovement.objects.create(
                tenant_id=tid, product=self.products[(country, op.sku)],
                to_location=self.main_loc[op.branch_code],
                warehouse=self.warehouses[op.branch_code],
                quantity=_d(op.qty), unit_cost=_d(op.unit_cost),
                movement_type="OPENING", reference=f"{self.tag} opening",
                notes="simulation opening balance",
            )
            StockMovement.objects.filter(pk=mv.pk).update(created_at=opening_dt)
            n += 1
        self.counts["stock_movements_opening"] = n
        self.log(f"  opening stock: {n} movements")

    def _seed_deliveries(self):
        tid = self.tenant.id
        by_po = defaultdict(list)
        for dv in self.r.deliveries:
            by_po[(dv.branch_code, dv.supplier_key, dv.ordered_day)].append(dv)

        n_po = n_grn = 0
        for (branch_code, sup_key, ordered_day), dvs in by_po.items():
            country = branch_code.split("-")[0]
            vendor = self.vendors[(country, sup_key)]
            company = self.companies[country]
            branch = self.branches[branch_code]
            wh = self.warehouses[branch_code]

            merged: dict[str, float] = defaultdict(float)
            received: dict[str, float] = defaultdict(float)
            expected_day = dvs[0].expected_day
            any_received = False
            status = "OPEN"
            for dv in dvs:
                for sku, q in dv.lines.items():
                    if dv.status in ("RECEIVED", "PARTIAL"):
                        received[sku] += q
                        any_received = True
                    else:
                        merged[sku] += q
                if dv.status in ("RECEIVED", "PARTIAL"):
                    status = dv.status
            # ordered quantity = max(received, planned)
            ordered = defaultdict(float)
            for sku in set(list(merged) + list(received)):
                ordered[sku] = max(merged.get(sku, 0.0), received.get(sku, 0.0),
                                   self._orig_planned(dvs, sku))

            po = PurchaseOrder.objects.create(
                tenant_id=tid, vendor=vendor, company=company, branch=branch, warehouse=wh,
                po_number=f"{branch_code}-PO-{ordered_day:%Y%m%d}-{sup_key[:3].upper()}",
                status="CONFIRMED", currency=S.REPORTING_CURRENCY,
                order_date=ordered_day, expected_date=expected_day,
                notes=f"{self.tag} auto-replenishment",
            )
            PurchaseOrder.objects.filter(pk=po.pk).update(
                created_at=datetime.combine(ordered_day, time(7, 0), tzinfo=UTC))
            po_lines = {}
            for sku, q in ordered.items():
                if q <= 0:
                    continue
                pl = PurchaseOrderLine.objects.create(
                    tenant_id=tid, order=po, product=self.products[(country, sku)],
                    quantity=_d(q), unit_cost=_d(S.RAW_BY_SKU[sku].unit_cost),
                )
                po_lines[sku] = pl
            po.recalculate()
            n_po += 1

            if any_received and any(received.values()):
                grn = GoodsReceipt.objects.create(
                    tenant_id=tid, purchase_order=po, status="DRAFT",
                    warehouse=wh, location=self.main_loc[branch_code],
                    grn_number=f"{branch_code}-GRN-{expected_day:%Y%m%d}-{sup_key[:3].upper()}",
                    notes=f"{self.tag}",
                )
                GoodsReceipt.objects.filter(pk=grn.pk).update(
                    received_at=datetime.combine(expected_day, time(8, 0), tzinfo=UTC))
                made_line = False
                for sku, q in received.items():
                    if q <= 0 or sku not in po_lines:
                        continue
                    GoodsReceiptLine.objects.create(
                        tenant_id=tid, receipt=grn, po_line=po_lines[sku],
                        product=self.products[(country, sku)],
                        received_qty=_d(q), unit_cost=_d(S.RAW_BY_SKU[sku].unit_cost),
                    )
                    made_line = True
                if made_line:
                    grn.refresh_from_db()
                    grn.post()
                    # push the RECEIPT movements back to the delivery date
                    StockMovement.objects.filter(reference=grn.grn_number).update(
                        created_at=datetime.combine(expected_day, time(8, 0), tzinfo=UTC))
                    n_grn += 1
                else:
                    grn.delete()

        self.counts["purchase_orders"] = n_po
        self.counts["goods_receipts"] = n_grn
        self.log(f"  purchasing: {n_po} POs, {n_grn} goods receipts")

    def _orig_planned(self, dvs, sku) -> float:
        # deliveries store what actually landed; planned may be higher. Use note as hint only.
        return max((dv.lines.get(sku, 0.0) for dv in dvs), default=0.0)

    def _seed_consumption(self):
        tid = self.tenant.id
        n_use = n_waste = 0
        agg = defaultdict(lambda: defaultdict(lambda: [0.0, 0.0]))  # (branch,day) -> sku -> [use,waste]
        for c in self.r.consumption:
            slot = agg[(c.branch_code, c.day)][c.sku]
            slot[0] += c.usage_qty
            slot[1] += c.waste_qty

        for (branch_code, day), skus in agg.items():
            country = branch_code.split("-")[0]
            use_dt = datetime.combine(day, time(23, 30), tzinfo=UTC)
            for sku, (use, waste) in skus.items():
                if use > 0:
                    mv = StockMovement.objects.create(
                        tenant_id=tid, product=self.products[(country, sku)],
                        from_location=self.main_loc[branch_code],
                        warehouse=self.warehouses[branch_code],
                        quantity=_d(use), unit_cost=_d(S.RAW_BY_SKU[sku].unit_cost),
                        movement_type="ISSUE", reference=f"{self.tag} usage {day}",
                        notes="kitchen consumption (BOM)",
                    )
                    StockMovement.objects.filter(pk=mv.pk).update(created_at=use_dt)
                    n_use += 1
                if waste > 0:
                    mv = StockMovement.objects.create(
                        tenant_id=tid, product=self.products[(country, sku)],
                        from_location=self.main_loc[branch_code],
                        warehouse=self.warehouses[branch_code],
                        quantity=_d(waste), unit_cost=_d(S.RAW_BY_SKU[sku].unit_cost),
                        movement_type="ADJUSTMENT", reference=f"{self.tag} waste {day}",
                        notes="spoilage / shelf-life waste",
                    )
                    StockMovement.objects.filter(pk=mv.pk).update(created_at=use_dt)
                    n_waste += 1
        self.counts["stock_movements_usage"] = n_use
        self.counts["stock_movements_waste"] = n_waste
        self.log(f"  consumption: {n_use} usage + {n_waste} waste movements")

    def _seed_orders(self):
        tid = self.tenant.id
        orders_by_bd = defaultdict(list)
        for o in self.r.orders:
            orders_by_bd[(o.branch_code, o.placed_utc.date())].append(o)

        n_sessions = n_orders = n_lines = n_pay = 0
        for (branch_code, day), day_orders in sorted(orders_by_bd.items()):
            country = branch_code.split("-")[0]
            company = self.companies[country]
            branch = self.branches[branch_code]
            pool = self.cashiers[branch_code]
            day_orders.sort(key=lambda o: o.placed_utc)

            # one session per cashier per day
            sessions = {}
            for idx, cash in enumerate(pool):
                s = PosSession.objects.create(
                    tenant_id=tid, company=company, branch=branch, cashier=cash,
                    status="CLOSED", opening_float=_d(100),
                    closing_float=_d(100), notes=f"{self.tag}",
                )
                open_dt = datetime.combine(day, time(6, 30), tzinfo=UTC)
                close_dt = datetime.combine(day, time(23, 59), tzinfo=UTC)
                PosSession.objects.filter(pk=s.pk).update(
                    opening_at=open_dt, closing_at=close_dt, created_at=open_dt)
                sessions[idx] = s
                n_sessions += 1

            order_rows = []
            meta = []
            for i, o in enumerate(day_orders):
                cash_idx = i % len(pool)
                subtotal = Decimal(str(o.subtotal))
                discount = Decimal(str(o.discount))
                tax = Decimal(str(o.tax))
                total = subtotal - discount + tax
                seq = f"{i + 1:04d}"
                order_rows.append(PosOrder(
                    tenant_id=tid, session=sessions[cash_idx], company=company, branch=branch,
                    cashier=pool[cash_idx],
                    order_number=f"{branch_code}-{day:%Y%m%d}-{seq}",
                    source=o.channel, status="PAID", daypart=o.daypart,
                    subtotal=_d(subtotal), discount_amount=_d(discount),
                    tax_amount=_d(tax), total=_d(total),
                    kitchen_status="SERVED",
                    placed_at=o.placed_utc, prep_started_at=o.prep_started_utc,
                    ready_at=o.ready_utc, served_at=o.served_utc, paid_at=o.served_utc,
                    notes=f"{self.tag}",
                ))
                meta.append(o)

            PosOrder.objects.bulk_create(order_rows, batch_size=1000)
            ids = [r.pk for r in order_rows]
            PosOrder.objects.filter(pk__in=ids).update(
                created_at=F("placed_at"), updated_at=F("served_at"))
            n_orders += len(order_rows)

            line_rows = []
            pay_rows = []
            for row, o in zip(order_rows, meta):
                for ln in o.lines:
                    prod = self.products[(country, ln.menu_code)]
                    line_rows.append(PosOrderLine(
                        tenant_id=tid, order=row, product=prod,
                        quantity=_d(ln.qty), unit_price=_d(ln.unit_price),
                        tax_rate=_d(ln.tax_rate), discount_percent=Decimal("0.00"),
                    ))
                if o.channel == "ONLINE":
                    method = "MOBILE"
                elif o.channel == "KIOSK":
                    method = "CARD"
                else:
                    method = "CARD" if row.total > _d(8) else "CASH"
                pay_rows.append(PosPayment(
                    tenant_id=tid, order=row, method=method,
                    amount=_d(row.total), reference=f"{self.tag}",
                ))
            PosOrderLine.objects.bulk_create(line_rows, batch_size=2000)
            PosPayment.objects.bulk_create(pay_rows, batch_size=2000)
            n_lines += len(line_rows)
            n_pay += len(pay_rows)

        self.counts["pos_sessions"] = n_sessions
        self.counts["pos_orders"] = n_orders
        self.counts["pos_order_lines"] = n_lines
        self.counts["pos_payments"] = n_pay
        self.log(f"  sales: {n_orders} orders, {n_lines} lines across {n_sessions} sessions")

    def _seed_staff(self):
        tid = self.tenant.id
        hire = self.r.start_date - timedelta(days=420)
        n = 0
        for c in S.COUNTRIES:
            company = self.companies[c.code]
            dept, _ = Department.objects.get_or_create(
                tenant_id=tid, company=company, name="Restaurant Operations",
            )
            for br in c.branches:
                branch = self.branches[br.code]
                foot = S.TIER_FOOTFALL[br.tier]
                for role, spec in S.STAFF_TEMPLATE.items():
                    count = max(1, round(spec["count"] * (foot if spec["kind"] == "hourly" else 1)))
                    for i in range(count):
                        emp_id = f"{br.code}-{role[:3].upper()}{i + 1}"
                        _, created = Employee.objects.get_or_create(
                            tenant=self.tenant, employee_id=emp_id,
                            defaults={
                                "first_name": role, "last_name": f"{br.code}-{i + 1}",
                                "branch": branch, "department": dept, "job_title": role,
                                "employment_type": "full_time" if spec["kind"] == "salaried" else "part_time",
                                "hire_date": hire, "base_salary": Decimal(str(spec["monthly_salary"])),
                                "currency": S.REPORTING_CURRENCY, "status": "active",
                            },
                        )
                        if created:
                            n += 1
        self.counts["employees"] = n
        self.log(f"  staff: {n} employees")
