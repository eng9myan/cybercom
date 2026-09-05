"""Deterministic multi-line sweets-business engine (manufacturing + retail + export). No DB."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .scenarios import anabtawi as A

UTC = ZoneInfo("UTC")
TZ = ZoneInfo(A.TIMEZONE)


def _rng(*p):
    return random.Random("|".join(str(x) for x in p))


@dataclass
class ProductionBatch:
    day: date
    product_sku: str
    planned_kg: float
    good_kg: float
    scrap_kg: float
    cycle_hours: float
    raw_consumed: dict[str, float]
    blocked: bool = False
    note: str = ""


@dataclass
class RetailSale:
    day: date
    branch: str
    product_sku: str
    kg: float
    revenue: float


@dataclass
class ExportLine:
    product_sku: str
    kg: float
    cartons: int
    net_kg: float
    gross_kg: float


@dataclass(eq=False)
class ExportOrder:
    dest_country: str
    dest_city: str
    distributor: str
    order_day: date
    incoterm: str
    promised_date: date
    lines: list[ExportLine] = field(default_factory=list)
    shipment_ref: int | None = None
    fulfilled: bool = False

    @property
    def net_kg(self):
        return sum(l.net_kg for l in self.lines)


@dataclass
class ExportShipment:
    ref: int
    dest_country: str
    dest_city: str
    incoterm: str
    mode: str
    order_refs: list[int]
    dispatch_utc: datetime
    arrival_utc: datetime
    delivered_utc: datetime
    customs_hours: float
    total_net_kg: float
    total_gross_kg: float
    total_cartons: int
    total_quantity: float
    freight_cost: float
    promised_latest: date

    @property
    def on_time(self):
        return self.delivered_utc.date() <= self.promised_latest


@dataclass
class RawReceipt:
    day: date
    sku: str
    kg: float
    cost: float


@dataclass
class SimResult:
    scenario: str
    variant_label: str
    seed: int
    start_date: date
    days: int
    scale: float
    batches: list[ProductionBatch] = field(default_factory=list)
    retail: list[RetailSale] = field(default_factory=list)
    export_orders: list[ExportOrder] = field(default_factory=list)
    shipments: list[ExportShipment] = field(default_factory=list)
    raw_receipts: list[RawReceipt] = field(default_factory=list)
    backorders_kg: float = 0.0
    disruption_log: list[str] = field(default_factory=list)


class AnabtawiSimulator:
    def __init__(self, *, seed, start_date, days=7, variant="baseline", scale=1.0):
        self.seed = seed
        self.start_date = start_date
        self.days = days
        self.variant = A.variant(variant)
        self.variant_name = variant
        self.scale = scale
        self.result = SimResult("anabtawi", self.variant["label"], seed, start_date, days, scale)
        self._exp_daily = self._expected_daily()
        self._raw_daily = self._expected_raw_daily()

    # -- expectations -------------------------------------------------

    AVG_EXPORT_ORDER_KG = 300.0

    def _expected_daily(self) -> dict[str, float]:
        rshare = sum(p.retail_share for p in A.PRODUCTS)
        eshare = sum(p.export_share for p in A.PRODUCTS)
        retail_total = sum(b.daily_kg_base for b in A.RETAIL_BRANCHES) * self.scale * 1.08
        export_total = (sum(d.orders_per_week for d in A.DESTINATIONS) / 7.0
                        * self.AVG_EXPORT_ORDER_KG * self.scale)
        out = {}
        for p in A.PRODUCTS:
            out[p.sku] = (retail_total * p.retail_share / rshare
                          + export_total * p.export_share / eshare)
        return out

    def _expected_raw_daily(self) -> dict[str, float]:
        out = {r.sku: 0.0 for r in A.RAW_MATERIALS}
        for p in A.PRODUCTS:
            out_kg = self._exp_daily[p.sku]
            in_kg = out_kg / p.yield_pct
            for sku, per in p.recipe.items():
                out[sku] += in_kg * per
        return out

    def _disr(self, di):
        return [d for d in self.variant.get("disruptions", ()) if di in d.day_index]

    # -- main -----------------------------------------------------

    def run(self) -> SimResult:
        raw = {r.sku: self._raw_daily[r.sku] * A.OPENING_RAW_DAYS for r in A.RAW_MATERIALS}
        fg = {p.sku: self._exp_daily[p.sku] * A.OPENING_FG_DAYS for p in A.PRODUCTS}
        raw_pending: list[RawReceipt] = []
        export_backlog: list[ExportOrder] = []
        ship_ref = 0

        for di in range(self.days):
            day = self.start_date + timedelta(days=di)
            rng = _rng(self.seed, di)
            disr = self._disr(di)

            forced_zero = set()
            constrained = set()
            plant_factor = 1.0
            export_mult = 1.0
            promo = {}
            for d in disr:
                if d.kind == "raw_shortage":
                    constrained.update(d.target.split(","))
                    if di == min(d.day_index):
                        forced_zero.update(d.target.split(","))
                elif d.kind == "plant_downtime":
                    plant_factor *= (1.0 - d.magnitude)
                elif d.kind == "export_spike":
                    export_mult += d.magnitude
                elif d.kind == "retail_promo":
                    promo[d.target] = d.magnitude
            for sku in forced_zero:
                raw[sku] = 0.0
            for sku in constrained - forced_zero:
                raw[sku] = min(raw.get(sku, 0.0), self._raw_daily[sku] * 0.4)

            # raw receipts landing today
            still = []
            for rr in raw_pending:
                if rr.day <= day:
                    if rr.sku not in forced_zero:
                        raw[rr.sku] += rr.kg
                        self.result.raw_receipts.append(rr)
                else:
                    still.append(rr)
            raw_pending = still
            self._reorder_raw(day, raw, raw_pending)

            self._produce(day, di, rng, raw, fg, plant_factor, forced_zero)
            self._retail(day, di, rng, fg, promo)
            ship_ref = self._export(day, di, rng, fg, export_backlog, export_mult, ship_ref)

        self.result.backorders_kg = round(sum(o.net_kg for o in export_backlog if not o.fulfilled), 1)
        self.result.disruption_log = [
            f"day {min(d.day_index) + 1}-{max(d.day_index) + 1}: {d.kind}"
            f"{(' ' + d.target) if d.target else ''} - {d.note}"
            for d in self.variant.get("disruptions", ())
        ]
        return self.result

    # -- purchasing ---------------------------------------------

    def _reorder_raw(self, day, raw, pending):
        for r in A.RAW_MATERIALS:
            daily = self._raw_daily[r.sku]
            if daily <= 0.01:
                continue
            incoming = sum(rr.kg for rr in pending if rr.sku == r.sku)
            if (raw[r.sku] + incoming) / daily < A.REORDER_RAW_DAYS:
                need = daily * A.REORDER_UP_TO_RAW_DAYS - raw[r.sku] - incoming
                packs = math.ceil(need / r.pack_kg)
                if packs > 0:
                    pending.append(RawReceipt(day + timedelta(days=r.lead_time_days), r.sku,
                                              float(packs * r.pack_kg),
                                              round(packs * r.pack_kg * r.cost_per_kg, 2)))

    # -- production -------------------------------------------

    def _produce(self, day, di, rng, raw, fg, plant_factor, forced_zero):
        budget = max(0, int(round(A.PLANT_BATCHES_PER_DAY * self.scale * plant_factor)))
        # priority: lowest days-of-cover first
        order = sorted(A.PRODUCTS, key=lambda p: fg[p.sku] / max(self._exp_daily[p.sku], 0.1))
        for p in order:
            if budget <= 0:
                break
            cover = fg[p.sku] / max(self._exp_daily[p.sku], 0.1)
            if cover > 3.0:
                continue
            target_kg = self._exp_daily[p.sku] * 3.5 - fg[p.sku]
            n_batches = min(budget, max(1, math.ceil(target_kg / p.batch_kg)))
            for _ in range(n_batches):
                if budget <= 0:
                    break
                budget -= 1
                in_needed = {s: (p.batch_kg / p.yield_pct) * per for s, per in p.recipe.items()}
                short = [s for s, q in in_needed.items() if raw.get(s, 0) < q]
                if short:
                    self.result.batches.append(ProductionBatch(
                        day, p.sku, p.batch_kg, 0.0, 0.0, p.cycle_hours, {}, blocked=True,
                        note=f"raw short: {','.join(short)}"))
                    continue
                for s, q in in_needed.items():
                    raw[s] -= q
                defect = A.PLANT_QC_DEFECT_PCT * rng.uniform(0.6, 1.8)
                good = p.batch_kg * (1 - defect) * rng.uniform(0.985, 1.0)
                scrap = p.batch_kg - good
                fg[p.sku] += good
                self.result.batches.append(ProductionBatch(
                    day, p.sku, p.batch_kg, round(good, 1), round(scrap, 1), p.cycle_hours,
                    {s: round(q, 2) for s, q in in_needed.items()}))

    # -- retail ---------------------------------------------

    def _retail(self, day, di, rng, fg, promo):
        wf = A.RETAIL_WEEKDAY_FACTOR[day.weekday()]
        rshare = sum(p.retail_share for p in A.PRODUCTS)
        for b in A.RETAIL_BRANCHES:
            for p in A.PRODUCTS:
                base = b.daily_kg_base * self.scale * wf * (p.retail_share / rshare)
                base *= (1 + promo.get(p.sku, 0.0))
                demand = max(0.0, rng.gauss(base, base * 0.18))
                sold = min(demand, fg[p.sku])
                fg[p.sku] -= sold
                if sold > 0.5:
                    self.result.retail.append(RetailSale(
                        day, b.code, p.sku, round(sold, 1), round(sold * p.retail_per_kg, 2)))

    # -- export -------------------------------------------

    def _export(self, day, di, rng, fg, backlog, export_mult, ship_ref):
        eshare = sum(p.export_share for p in A.PRODUCTS)
        for dest in A.DESTINATIONS:
            n_orders = rng.random() < (dest.orders_per_week / 7.0 * export_mult * self.scale)
            extra = int(rng.random() < (dest.orders_per_week / 7.0 * export_mult * self.scale - 1))
            for _ in range(int(n_orders) + extra):
                distributor = rng.choice(dest.distributors)
                lines = []
                for p in rng.sample(list(A.PRODUCTS), rng.randint(2, 4)):
                    kg = round(rng.uniform(50, 130) * (1.0 + p.export_share / eshare), 1)
                    cartons = max(1, math.ceil(kg / A.CARTON_NET_KG))
                    net = round(cartons * A.CARTON_NET_KG, 1)
                    gross = round(net + cartons * A.CARTON_TARE_KG, 1)
                    lines.append(ExportLine(p.sku, net, cartons, net, gross))
                if not lines:
                    continue
                promised = day + timedelta(days=dest.transit_days
                                           + math.ceil(dest.customs_hours / 24)
                                           + A.EXPORT_PROMISE_BUFFER_DAYS + 1)
                backlog.append(ExportOrder(dest.country, dest.city, distributor, day,
                                           dest.incoterm, promised, lines))
                self.result.export_orders.append(backlog[-1])

        # try to allocate + consolidate per destination
        for dest in A.DESTINATIONS:
            pend = [o for o in backlog if o.dest_country == dest.country and not o.fulfilled]
            if not pend:
                continue
            ready = []
            for o in pend:
                if all(fg.get(l.product_sku, 0) >= l.net_kg for l in o.lines):
                    for l in o.lines:
                        fg[l.product_sku] -= l.net_kg
                    o.fulfilled = True
                    ready.append(o)
            # dispatch a consolidated shipment once orders are ready and either
            # aging, or enough volume has accrued, or it's the last day.
            aging = any((day - o.order_day).days >= 1 for o in ready)
            accrued = sum(o.net_kg for o in ready)
            last_day = day == self.start_date + timedelta(days=self.days - 1)
            if ready and (aging or accrued >= 250 or last_day):
                ship_ref += 1
                net = sum(o.net_kg for o in ready)
                gross = sum(sum(l.gross_kg for l in o.lines) for o in ready)
                cartons = sum(sum(l.cartons for l in o.lines) for o in ready)
                dispatch = datetime.combine(day, time(16, 0), tzinfo=TZ).astimezone(UTC)
                arrival = dispatch + timedelta(days=dest.transit_days)
                delivered = arrival + timedelta(hours=dest.customs_hours * rng.uniform(0.7, 1.9)
                                                + rng.uniform(4, 20))
                freight = dest.freight_base + net * (0.8 if dest.mode == "air" else 0.25)
                promised_latest = max(o.promised_date for o in ready)
                sh = ExportShipment(
                    ship_ref, dest.country, dest.city, dest.incoterm, dest.mode,
                    [self.result.export_orders.index(o) for o in ready],
                    dispatch, arrival, delivered,
                    round(dest.customs_hours, 1), round(net, 1), round(gross, 1), cartons,
                    round(net, 1), round(freight, 2), promised_latest)
                for o in ready:
                    o.shipment_ref = ship_ref
                self.result.shipments.append(sh)
        return ship_ref
