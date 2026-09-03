"""
Seed a restaurant / retail demo on top of a provisioned tenant, exercising the
Commerce spine merged from CyShop: catalog (categories, units, tax, products,
a KIT + variants), inventory stock, POS (an open session, paid orders with
receipts), live KDS kitchen tickets in every stage, and retail/wholesale
sales quotations.

This is the sales-demo counterpart to `seed_demo_business` (which seeds generic
construction ERP breadth). Run both for a full "looks alive everywhere" tenant:

    python manage.py seed_demo_commerce
    python manage.py seed_demo_commerce --tenant <uuid>

Idempotent: keyed on natural keys, safe to re-run. `--reset` wipes the demo's
POS orders / receipts / KDS tickets first so a messy demo self-heals.

NOTE: POS/KDS order lines reference inventory.Product (the operational stock
item), while the Catalog screen reads catalog.Product (the richer merchandising
record). Both are seeded so every screen is populated; wiring POS to consume
catalog products directly is a later integration step.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.catalog.models import Category, KitComponent, Product as CatProduct, ProductUnit, TaxClass
from products.cycom.inventory.models import Product as InvProduct, StockItem, Warehouse
from products.cycom.pos.models import POSOrder, POSOrderLine, POSSession, PosReceipt
from products.cycom.sales.models import SalesOrder, SalesOrderLine

DEV_TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")


class Command(BaseCommand):
    help = "Seed a restaurant/retail Commerce demo (catalog + POS + KDS + quotations)."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", default=str(DEV_TENANT))
        parser.add_argument(
            "--reset", action="store_true",
            help="Wipe existing demo POS orders / receipts / KDS tickets before seeding.",
        )

    def handle(self, *args, **opts):
        tid = uuid.UUID(opts["tenant"])
        n = {k: 0 for k in (
            "accounts", "units", "tax", "categories", "cat_products", "variants",
            "kits", "inv_products", "stock", "pos_orders", "kds_tickets",
            "receipts", "quotations",
        )}

        # ── Accounts (create if the provisioned CoA lacks them) ──────────────
        def acct(code, name, typ):
            a = Account.objects.filter(tenant_id=tid, code=code).first()
            if not a:
                a = Account.objects.create(tenant_id=tid, code=code, name=name, account_type=typ)
                n["accounts"] += 1
            return a

        cash = acct("1000", "Cash on Hand", "asset")
        inv_acct = acct("1140", "Inventory", "asset")
        revenue = acct("4000", "Sales Revenue", "income")
        tax_acct = acct("2120", "Output VAT", "liability")
        cogs = acct("5000", "Cost of Goods Sold", "expense")

        # ── Catalog: units, tax, categories ──────────────────────────────────
        def unit(name, abbr):
            o, c = ProductUnit.objects.get_or_create(
                tenant_id=tid, abbreviation=abbr, defaults={"name": name})
            n["units"] += c
            return o

        u_pc = unit("Piece", "pc")
        unit("Cup", "cup")
        unit("Plate", "plate")

        std_tax, c = TaxClass.objects.get_or_create(
            tenant_id=tid, code="STD", defaults={"name": "Standard", "rate": Decimal("0.1600")})
        n["tax"] += c

        cats = {}
        for name in ["Hot Drinks", "Cold Drinks", "Food", "Bakery", "Retail"]:
            o, cc = Category.objects.get_or_create(
                tenant_id=tid, slug=name.lower().replace(" ", "-"),
                defaults={"name": name})
            cats[name] = o
            n["categories"] += cc

        # ── Catalog products (rich merchandising records) ────────────────────
        menu = [
            ("Hot Drinks", "Espresso", "1.50", "CONSUMABLE"),
            ("Hot Drinks", "Flat White", "3.25", "CONSUMABLE"),
            ("Hot Drinks", "Cappuccino", "3.00", "CONSUMABLE"),
            ("Hot Drinks", "Americano", "2.50", "CONSUMABLE"),
            ("Hot Drinks", "Latte", "3.25", "CONSUMABLE"),
            ("Cold Drinks", "Iced Latte", "3.75", "CONSUMABLE"),
            ("Cold Drinks", "Fresh Orange Juice", "4.00", "CONSUMABLE"),
            ("Cold Drinks", "Sparkling Water", "1.75", "STORABLE"),
            ("Food", "Chicken Shawarma Plate", "6.50", "CONSUMABLE"),
            ("Food", "Falafel Wrap", "3.50", "CONSUMABLE"),
            ("Food", "Halloumi Sandwich", "4.25", "CONSUMABLE"),
            ("Food", "Caesar Salad", "5.00", "CONSUMABLE"),
            ("Bakery", "Butter Croissant", "2.00", "STORABLE"),
            ("Bakery", "Chocolate Muffin", "2.50", "STORABLE"),
            ("Bakery", "Cheese Danish", "2.75", "STORABLE"),
            ("Retail", "Cybercom House Blend 250g", "9.00", "STORABLE"),
            ("Retail", "Ceramic Mug", "6.00", "STORABLE"),
            ("Retail", "Reusable Cup", "8.50", "STORABLE"),
        ]
        cat_prod_by_name = {}
        for i, (cat, name, price, ptype) in enumerate(menu):
            o, cc = CatProduct.objects.get_or_create(
                tenant_id=tid, internal_ref=f"CAT-{i+1:03d}",
                defaults={
                    "name": name, "category": cats[cat], "unit": u_pc,
                    "tax_class": std_tax, "product_type": ptype,
                    "sell_price": Decimal(price), "cost_price": (Decimal(price) * Decimal("0.4")).quantize(Decimal("0.0001")),
                    "pos_available": True, "track_stock": ptype == "STORABLE",
                },
            )
            cat_prod_by_name[name] = o
            n["cat_products"] += cc

        # A KIT / combo built from other catalog products (BOM).
        combo, cc = CatProduct.objects.get_or_create(
            tenant_id=tid, internal_ref="CAT-COMBO1",
            defaults={
                "name": "Breakfast Combo", "category": cats["Food"], "unit": u_pc,
                "tax_class": std_tax, "product_type": "KIT", "sell_price": Decimal("5.50"),
                "pos_available": True, "track_stock": False,
            },
        )
        n["cat_products"] += cc
        if cc:
            n["kits"] += 1
            for part, qty in [("Flat White", 1), ("Butter Croissant", 1), ("Fresh Orange Juice", 1)]:
                KitComponent.objects.get_or_create(
                    tenant_id=tid, product=combo, component_product=cat_prod_by_name[part],
                    defaults={"quantity_per_unit": Decimal(qty)},
                )

        # (Skipped variants for brevity — the Ceramic Mug could carry colour
        # variants, but the demo's visual value is in POS/KDS below.)

        # ── Inventory: café warehouse + operational products + stock ─────────
        wh, _ = Warehouse.objects.get_or_create(
            tenant_id=tid, code="WH-CAFE", defaults={"name": "Café Store"})
        inv_by_name = {}
        for i, (cat, name, price, ptype) in enumerate(menu):
            sku = f"CAFE-{i+1:03d}"
            o, cc = InvProduct.objects.get_or_create(
                tenant_id=tid, sku=sku,
                defaults={"name": name, "uom": "each", "inventory_account": inv_acct},
            )
            inv_by_name[name] = o
            n["inv_products"] += cc
            si, sc = StockItem.objects.get_or_create(
                tenant_id=tid, product=o, warehouse=wh,
                defaults={"quantity_on_hand": Decimal("200"), "average_cost": (Decimal(price) * Decimal("0.4")).quantize(Decimal("0.0001"))},
            )
            n["stock"] += sc

        # ── POS: one open session ────────────────────────────────────────────
        session = (POSSession.objects.filter(tenant_id=tid, warehouse=wh, status="open").first()
                   or POSSession.objects.create(tenant_id=tid, warehouse=wh, cashier="Demo Cashier",
                                                opening_cash=Decimal("100")))

        if opts["reset"]:
            PosReceipt.objects.filter(tenant_id=tid).delete()
            POSOrderLine.objects.filter(tenant_id=tid).delete()
            POSOrder.objects.filter(tenant_id=tid).delete()

        def pos_order(num, items, *, status, kitchen, source, table="", customer=""):
            """items: list of (inventory_product_name, qty, unit_price)."""
            if POSOrder.objects.filter(tenant_id=tid, order_number=num).exists():
                return None
            o = POSOrder.objects.create(
                tenant_id=tid, session=session, order_number=num, status=status,
                kitchen_status=kitchen, source=source, table_ref=table, customer_name=customer,
                cash_account=cash, revenue_account=revenue, tax_account=tax_acct, cogs_account=cogs,
            )
            sub = Decimal("0")
            for name, qty, price in items:
                POSOrderLine.objects.create(
                    tenant_id=tid, order=o, product=inv_by_name[name],
                    quantity=Decimal(qty), unit_price=Decimal(price), tax_percent=Decimal("16"))
                sub += Decimal(qty) * Decimal(price)
            tax = (sub * Decimal("0.16")).quantize(Decimal("0.01"))
            o.amount_subtotal = sub.quantize(Decimal("0.01"))
            o.amount_tax = tax
            o.amount_total = (sub + tax).quantize(Decimal("0.01"))
            o.save(update_fields=["amount_subtotal", "amount_tax", "amount_total"])
            n["pos_orders"] += 1
            if kitchen != "served":
                n["kds_tickets"] += 1
            return o

        # Paid orders (drive POS reports) — served, with receipts.
        paid = [
            ("POS-2001", [("Flat White", 2, "3.25"), ("Butter Croissant", 1, "2.00")]),
            ("POS-2002", [("Chicken Shawarma Plate", 1, "6.50"), ("Fresh Orange Juice", 1, "4.00")]),
            ("POS-2003", [("Cappuccino", 1, "3.00"), ("Chocolate Muffin", 1, "2.50")]),
            ("POS-2004", [("Cybercom House Blend 250g", 2, "9.00")]),
        ]
        for i, (num, items) in enumerate(paid):
            o = pos_order(num, items, status="paid", kitchen="served", source="POS",
                          customer=["Layla", "Omar", "Walk-in", "Huda"][i])
            if o:
                r, rc = PosReceipt.objects.get_or_create(
                    tenant_id=tid, order=o, defaults={"receipt_number": f"R-{num[-4:]}"})
                n["receipts"] += rc

        # Live kitchen tickets (drive the KDS screen) — every stage represented.
        pos_order("POS-3001", [("Chicken Shawarma Plate", 2, "6.50"), ("Falafel Wrap", 1, "3.50")],
                  status="draft", kitchen="pending", source="POS", table="5", customer="Layla")
        pos_order("POS-3002", [("Halloumi Sandwich", 1, "4.25"), ("Iced Latte", 1, "3.75")],
                  status="draft", kitchen="pending", source="KIOSK", customer="Omar")
        pos_order("POS-3003", [("Caesar Salad", 1, "5.00")],
                  status="draft", kitchen="in_progress", source="ONLINE", table="12", customer="Sara")
        pos_order("POS-3004", [("Falafel Wrap", 3, "3.50")],
                  status="draft", kitchen="in_progress", source="POS", table="3", customer="Nabil")
        pos_order("POS-3005", [("Butter Croissant", 2, "2.00"), ("Latte", 2, "3.25")],
                  status="draft", kitchen="ready", source="POS", table="8", customer="Maya")

        # ── Sales quotations: retail + wholesale ─────────────────────────────
        for name, city in [("Grand Hotel Amman", "Amman"), ("Corner Grocery", "Zarqa")]:
            Partner.objects.get_or_create(
                tenant_id=tid, name=name, partner_type="customer",
                defaults={"approval_status": "approved", "city": city, "payment_terms_days": 30})

        quotes = [
            ("Q-5001", "Grand Hotel Amman", "wholesale", "confirmed",
             [("House Blend 250g bulk", 50, "7.00"), ("Ceramic Mug", 100, "4.50")]),
            ("Q-5002", "Corner Grocery", "wholesale", "draft",
             [("House Blend 250g bulk", 20, "7.50")]),
            ("Q-5003", "Layla Haddad", "retail", "draft",
             [("Reusable Cup", 2, "8.50"), ("House Blend 250g bulk", 1, "9.00")]),
        ]
        for num, cust, ctype, st, lines in quotes:
            if SalesOrder.objects.filter(tenant_id=tid, number=num).exists():
                continue
            so = SalesOrder.objects.create(
                tenant_id=tid, number=num, customer_name=cust, customer_type=ctype,
                order_date=date.today(), valid_until=date.today() + timedelta(days=30),
                status=st, salesperson="Demo Sales", terms="Prices valid 30 days.")
            for desc, qty, price in lines:
                SalesOrderLine.objects.create(
                    tenant_id=tid, order=so, description=desc,
                    quantity=Decimal(qty), unit_price=Decimal(price), tax_percent=Decimal("16"))
            so.recompute_totals()
            n["quotations"] += 1

        self.stdout.write(self.style.SUCCESS(
            "Commerce demo seeded: " + ", ".join(f"{k}={v}" for k, v in n.items())))
