"""
Deterministic QSR operations engine.

Given a seed, a start date and a scenario variant it produces a full week of
branch-level activity: every paid order (with lines, channel, daypart and
kitchen timing), the raw-goods each branch consumed and wasted per day, the
supplier deliveries that fed them, and the opening balances everything started
from. It keeps its own lightweight per-branch inventory ledger so that a
stockout - organic or injected by a disruption - actually costs sales and
stretches queues, exactly as it would on the floor.

Nothing here touches the database; `seeder.QsrSeeder` writes the result.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .scenarios import qsr as S

UTC = ZoneInfo("UTC")


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class SimLine:
    menu_code: str
    qty: int
    unit_price: float
    tax_rate: float


@dataclass
class SimOrder:
    country_code: str
    branch_code: str
    channel: str
    daypart: str
    placed_utc: datetime
    prep_started_utc: datetime
    ready_utc: datetime
    served_utc: datetime
    target_seconds: int
    on_time: bool
    lines: list[SimLine] = field(default_factory=list)
    subtotal: float = 0.0
    discount: float = 0.0
    tax: float = 0.0
    total: float = 0.0

    @property
    def wait_seconds(self) -> float:
        return (self.served_utc - self.placed_utc).total_seconds()


@dataclass
class SimConsumption:
    branch_code: str
    day: date
    sku: str
    usage_qty: float
    waste_qty: float


@dataclass
class SimDelivery:
    branch_code: str
    supplier_key: str
    ordered_day: date
    expected_day: date
    arrived_day: date | None
    lines: dict[str, float]
    unit_costs: dict[str, float]
    status: str            # "RECEIVED" | "PARTIAL" | "OPEN"
    note: str = ""

    @property
    def value(self) -> float:
        return round(sum(self.lines[s] * self.unit_costs[s] for s in self.lines), 2)


@dataclass
class SimOpening:
    branch_code: str
    sku: str
    qty: float
    unit_cost: float


@dataclass
class LostSale:
    branch_code: str
    day: date
    daypart: str
    reason: str


@dataclass
class SimResult:
    scenario: str
    variant_label: str
    seed: int
    start_date: date
    days: int
    volume: float
    orders: list[SimOrder] = field(default_factory=list)
    consumption: list[SimConsumption] = field(default_factory=list)
    deliveries: list[SimDelivery] = field(default_factory=list)
    opening: list[SimOpening] = field(default_factory=list)
    lost_sales: list[LostSale] = field(default_factory=list)
    disruption_log: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _rng(*parts) -> random.Random:
    return random.Random("|".join(str(p) for p in parts))


def _weighted_choice(rng: random.Random, items: list, weights: list[float]):
    total = sum(weights)
    if total <= 0:
        return rng.choice(items)
    r = rng.random() * total
    upto = 0.0
    for it, w in zip(items, weights):
        upto += w
        if upto >= r:
            return it
    return items[-1]


class QsrSimulator:
    def __init__(self, *, seed: int, start_date: date, days: int = 7,
                 variant: str = "baseline", volume: float = 1.0,
                 countries: list[str] | None = None):
        self.seed = seed
        self.start_date = start_date
        self.days = days
        self.variant_name = variant
        self.variant = S.variant(variant)
        self.volume = volume
        self._countries = [c for c in S.COUNTRIES
                           if countries is None or c.code in countries]
        self.result = SimResult(
            scenario="qsr", variant_label=self.variant["label"], seed=seed,
            start_date=start_date, days=days, volume=volume,
        )
        self._expected_daily_usage = self._estimate_daily_usage()

    # -- expected usage, used for opening stock and reorder sizing ------------

    def _estimate_daily_usage(self) -> dict[str, float]:
        """Per-SKU expected units consumed by a standard branch on an average day."""
        avg_orders = S.BASELINE_ORDERS_PER_DAY * self.volume
        avg_lines = avg_orders * S.AVG_BASKET_LINES
        pop_total = sum(m.popularity for m in S.MENU)
        usage: dict[str, float] = {r.sku: 0.0 for r in S.RAW_GOODS}
        for m in S.MENU:
            share = m.popularity / pop_total
            item_units = avg_lines * share
            for sku, per in m.components.items():
                usage[sku] += item_units * per
        return usage

    # -- disruptions --------------------------------------------------------

    def _active_disruptions(self, day_index: int, country: str, branch: str):
        for d in self.variant.get("disruptions", ()):
            if day_index not in d.day_index:
                continue
            if d.branches and branch not in d.branches:
                continue
            if d.countries and country not in d.countries:
                continue
            yield d

    # -- main --------------------------------------------------------------

    def run(self) -> SimResult:
        for country in self._countries:
            tz = ZoneInfo(country.timezone)
            for br in country.branches:
                self._run_branch(country, br, tz)
        self.result.disruption_log = [
            f"day {di + 1}: {d.kind} - {d.note or d.kind} "
            f"({', '.join(d.branches or d.countries) or 'all'})"
            for d in self.variant.get("disruptions", ())
            for di in d.day_index
        ]
        return self.result

    def _branch_factor(self, country: S.CountrySpec, br: S.BranchSpec) -> float:
        """Demand of this branch relative to a standard branch (volume already
        baked into `_expected_daily_usage`)."""
        return country.demand_index * S.TIER_FOOTFALL[br.tier]

    def _run_branch(self, country: S.CountrySpec, br: S.BranchSpec, tz: ZoneInfo):
        bf = self._branch_factor(country, br)
        # opening inventory — cover at least until this SKU's supplier can
        # realistically refill (lead time + the gap between delivery days).
        inv: dict[str, float] = {}
        for r in S.RAW_GOODS:
            sup = S.SUPPLIER_BY_KEY[r.supplier_key]
            cadence_gap = 7.0 / max(1, len(sup.delivery_weekdays))
            cover_days = max(S.OPENING_STOCK_DAYS, sup.lead_time_days + cadence_gap + 2.0)
            daily = self._expected_daily_usage[r.sku] * bf
            cover = daily * cover_days
            packs = max(1, math.ceil(cover / r.pack_size)) if cover else 1
            qty = float(packs * r.pack_size) if cover else float(r.pack_size)
            inv[r.sku] = qty
            self.result.opening.append(
                SimOpening(br.code, r.sku, qty, r.unit_cost)
            )

        pending: list[SimDelivery] = []          # scheduled, not yet arrived
        blocked_skus_by_day: dict[int, set[str]] = {}

        for di in range(self.days):
            day = self.start_date + timedelta(days=di)
            rng = _rng(self.seed, br.code, di)

            # apply disruptions for the day
            forced_zero: set[str] = set()
            kitchen_factor = 1.0
            for d in self._active_disruptions(di, country.code, br.code):
                if d.kind == "stockout":
                    forced_zero.update(d.raw_skus)
                elif d.kind == "kitchen_shortage":
                    kitchen_factor *= (1.0 - d.magnitude)
            for sku in forced_zero:
                inv[sku] = 0.0
            blocked_skus_by_day[di] = forced_zero

            # receive deliveries expected today
            still_pending = []
            for dv in pending:
                if dv.expected_day <= day:
                    self._receive(dv, inv, rng, blocked=forced_zero)
                else:
                    still_pending.append(dv)
            pending = still_pending

            # place replenishment orders for suppliers delivering off today's stock
            self._maybe_reorder(country, br, day, di, inv, pending, rng)

            # generate the day's demand
            usage_today: dict[str, float] = {r.sku: 0.0 for r in S.RAW_GOODS}
            unavailable: set[str] = set()      # menu codes out for the rest of today
            self._simulate_day(country, br, tz, day, di, rng, inv,
                               usage_today, unavailable, kitchen_factor)

            # end-of-day spoilage on perishables
            for r in S.RAW_GOODS:
                used = usage_today[r.sku]
                rate = self._spoilage_rate(r.shelf_life_days)
                waste = 0.0
                if r.shelf_life_days <= 6:
                    waste = round(used * rate + inv[r.sku] * (rate / 3), 3)
                    waste = min(waste, inv[r.sku])
                    inv[r.sku] -= waste
                self.result.consumption.append(
                    SimConsumption(br.code, day, r.sku, round(used, 3), round(waste, 3))
                )

        # any deliveries still in flight at horizon end -> OPEN purchase orders
        for dv in pending:
            dv.status = "OPEN"
            dv.arrived_day = None
            self.result.deliveries.append(dv)

    # -- day simulation ---------------------------------------------------

    def _simulate_day(self, country, br, tz, day, di, rng, inv,
                      usage_today, unavailable, kitchen_factor):
        weekday = day.weekday()
        base = (S.BASELINE_ORDERS_PER_DAY * country.demand_index
                * S.TIER_FOOTFALL[br.tier] * S.WEEKDAY_FACTOR[weekday] * self.volume)

        promo = self.variant.get("promo")
        if promo:
            base *= (1.0 + promo["demand_uplift"] * 0.35)

        n_orders = max(0, int(rng.gauss(base, math.sqrt(max(base, 1)))))

        open_hours = [h for h in range(br.opens_hour, br.closes_hour)
                      if (h % 24) in S.HOURLY_WEIGHTS]
        hour_weights = [S.HOURLY_WEIGHTS[h % 24] for h in open_hours]

        # kitchen queue state: N stations free at a given time
        crew = S.STAFF_TEMPLATE["Kitchen Crew"]["count"] + S.STAFF_TEMPLATE["Drive-Thru Crew"]["count"]
        stations = max(2, int(round(crew * S.TIER_FOOTFALL[br.tier] * kitchen_factor)))
        free_at = [datetime.combine(day, time(0, 0), tzinfo=tz)] * stations

        # 1) generate order timestamps + baskets, 2) sort into service order,
        #    3) run the kitchen queue strictly in time order.
        pending_orders: list[SimOrder] = []
        for _ in range(n_orders):
            hour = _weighted_choice(rng, open_hours, hour_weights) % 24
            local_dt = datetime.combine(
                day, time(hour, rng.randint(0, 59), rng.randint(0, 59)), tzinfo=tz,
            )
            placed_utc = local_dt.astimezone(UTC)
            daypart = S.DAYPART_BY_HOUR.get(hour, "AFTERNOON")

            channel = self._pick_channel(rng, br, daypart)
            lines = self._build_basket(rng, br, daypart, inv, usage_today,
                                       unavailable, promo)
            if not lines:
                self.result.lost_sales.append(
                    LostSale(br.code, day, daypart, "no sellable items in stock")
                )
                continue
            pending_orders.append(
                self._price_order(country, br, channel, daypart, placed_utc, lines, promo)
            )

        pending_orders.sort(key=lambda o: o.placed_utc)
        for order in pending_orders:
            self._schedule_kitchen(order, free_at, rng, kitchen_factor)
        self.result.orders.extend(pending_orders)

    def _pick_channel(self, rng, br, daypart):
        mix = dict(S.CHANNEL_MIX if br.has_drive_thru else S.CHANNEL_MIX_NO_DT)
        if daypart == "BREAKFAST" and br.has_drive_thru:
            mix["DRIVE_THRU"] = mix.get("DRIVE_THRU", 0) + 0.12
        if daypart == "LATE_NIGHT":
            mix = {"DRIVE_THRU": 0.7, "ONLINE": 0.3} if br.has_drive_thru else {"POS": 1.0}
        items = list(mix)
        return _weighted_choice(rng, items, [mix[i] for i in items])

    def _available(self, m: S.MenuItem, daypart: str, inv, unavailable: set) -> bool:
        if m.code in unavailable:
            return False
        if m.dayparts is not None and daypart not in m.dayparts:
            return False
        if m.dayparts is None and m.category in ("Burgers", "Chicken", "Fish", "Meals") \
                and daypart == "BREAKFAST":
            return False
        for sku, per in m.components.items():
            if inv.get(sku, 0.0) < per:
                return False
        return True

    def _build_basket(self, rng, br, daypart, inv, usage_today, unavailable, promo):
        n_lines = max(1, min(6, int(rng.gauss(S.AVG_BASKET_LINES, 1.1))))
        lines: list[SimLine] = []
        for _ in range(n_lines):
            candidates = [m for m in S.MENU if self._available(m, daypart, inv, unavailable)]
            if not candidates:
                break
            weights = []
            for m in candidates:
                w = m.popularity
                if daypart in ("LUNCH", "DINNER") and m.is_bundle:
                    w *= 1.8
                if promo and m.code == promo["code"] and daypart in promo["dayparts"]:
                    w *= (1.0 + promo["demand_uplift"] * 3)
                weights.append(w)
            m = _weighted_choice(rng, candidates, weights)
            qty = 1 if rng.random() > 0.16 else rng.randint(2, 3)
            # commit stock
            ok = all(inv.get(sku, 0.0) >= per * qty for sku, per in m.components.items())
            if not ok:
                unavailable.add(m.code)
                continue
            for sku, per in m.components.items():
                inv[sku] -= per * qty
                usage_today[sku] += per * qty
            price = m.price
            lines.append(SimLine(m.code, qty, price, 0.0))
        return lines

    def _price_order(self, country, br, channel, daypart, placed_utc, lines, promo):
        vat = float(country.vat_rate)
        subtotal = 0.0
        discount = 0.0
        for ln in lines:
            ln.unit_price = round(ln.unit_price * country.price_index, 2)
            ln.tax_rate = vat
            gross = ln.unit_price * ln.qty
            if promo and ln.menu_code == promo["code"] and daypart in promo["dayparts"]:
                d = round(gross * promo["discount"], 2)
                discount += d
                gross -= d
            subtotal += gross
        tax = round(subtotal * vat, 2)
        order = SimOrder(
            country_code=country.code, branch_code=br.code, channel=channel,
            daypart=daypart, placed_utc=placed_utc, prep_started_utc=placed_utc,
            ready_utc=placed_utc, served_utc=placed_utc,
            target_seconds=S.SERVICE_TARGET_SECONDS.get(channel, 300),
            on_time=True, lines=lines,
            subtotal=round(subtotal, 2), discount=round(discount, 2),
            tax=tax, total=round(subtotal + tax, 2),
        )
        return order

    def _schedule_kitchen(self, order: SimOrder, free_at: list[datetime], rng, kitchen_factor):
        base = sum(S.BASE_PREP_SECONDS.get(S.MENU_BY_CODE[ln.menu_code].category, 45) * ln.qty
                   for ln in order.lines)
        # queue: earliest free station
        free_at.sort()
        start = max(order.placed_utc, free_at[0])
        queue_wait = (start - order.placed_utc).total_seconds()
        load_stretch = 1.0 + min(1.5, queue_wait / 300.0) + (1.0 / max(kitchen_factor, 0.3) - 1.0) * 0.6
        prep = base * load_stretch * rng.uniform(0.85, 1.25)
        prep = max(20.0, prep)
        ready = start + timedelta(seconds=prep)
        free_at[0] = ready
        handover = {"DRIVE_THRU": 35, "POS": 25, "KIOSK": 40, "ONLINE": 90}.get(order.channel, 30)
        served = ready + timedelta(seconds=handover * rng.uniform(0.7, 1.6))
        order.prep_started_utc = start
        order.ready_utc = ready
        order.served_utc = served
        order.on_time = order.wait_seconds <= order.target_seconds

    # -- purchasing ------------------------------------------------------

    def _spoilage_rate(self, shelf_life_days: int) -> float:
        return S.SPOILAGE_RATE.get(shelf_life_days, S.DEFAULT_SPOILAGE)

    def _maybe_reorder(self, country, br, day, di, inv, pending, rng):
        bf = self._branch_factor(country, br)
        for sup in S.SUPPLIERS:
            if any(dv.supplier_key == sup.key for dv in pending):
                continue                       # one outstanding PO per supplier
            cadence_gap = 7.0 / max(1, len(sup.delivery_weekdays))
            reorder_at = max(S.REORDER_POINT_DAYS, sup.lead_time_days + cadence_gap + 1.0)
            up_to = reorder_at + S.REORDER_UP_TO_DAYS
            need: dict[str, float] = {}
            for r in (rg for rg in S.RAW_GOODS if rg.supplier_key == sup.key):
                daily = self._expected_daily_usage[r.sku] * bf
                if daily <= 0.001:
                    continue
                if inv[r.sku] / daily < reorder_at:
                    order_qty = max(0.0, daily * up_to - inv[r.sku])
                    packs = math.ceil(order_qty / r.pack_size)
                    if packs > 0:
                        need[r.sku] = float(packs * r.pack_size)
            if not need:
                continue
            expected = day + timedelta(days=sup.lead_time_days)
            for _ in range(7):
                if expected.weekday() in sup.delivery_weekdays:
                    break
                expected += timedelta(days=1)
            pending.append(SimDelivery(
                branch_code=br.code, supplier_key=sup.key, ordered_day=day,
                expected_day=expected, arrived_day=None, lines=need,
                unit_costs={s: S.RAW_BY_SKU[s].unit_cost for s in need},
                status="PARTIAL", note="",
            ))

    def _receive(self, dv: SimDelivery, inv, rng, blocked: set[str]):
        sup = S.SUPPLIER_BY_KEY[dv.supplier_key]
        on_time = rng.random() < sup.reliability
        received_lines = {}
        for sku, qty in dv.lines.items():
            if sku in blocked:
                received_lines[sku] = 0.0
                continue
            factor = 1.0 if on_time else rng.uniform(0.0, 0.7)
            got = round(qty * factor, 2)
            received_lines[sku] = got
            inv[sku] = inv.get(sku, 0.0) + got
        dv.arrived_day = dv.expected_day
        full = all(received_lines[s] >= dv.lines[s] - 1e-6 for s in dv.lines)
        dv.status = "RECEIVED" if full else "PARTIAL"
        dv.lines = received_lines            # store what actually landed
        if not full:
            dv.note = "short / late delivery"
        self.result.deliveries.append(dv)
