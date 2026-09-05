"""Deterministic last-mile courier engine. No DB access."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .scenarios import courier as C

UTC = ZoneInfo("UTC")
TZ = ZoneInfo(C.TIMEZONE)


def _rng(*p):
    return random.Random("|".join(str(x) for x in p))


def _weighted(rng, items, weights):
    tot = sum(weights)
    r = rng.random() * tot
    u = 0.0
    for it, w in zip(items, weights):
        u += w
        if u >= r:
            return it
    return items[-1]


@dataclass(eq=False)
class Parcel:
    ref: int
    sender: str
    recipient: str
    zone: str
    size: str
    weight_kg: float
    dims_cm: tuple[int, int, int]
    service_level: str
    intake_utc: datetime
    promised_date: date
    delivered_utc: datetime | None = None
    status: str = "at_hub"        # at_hub | out_for_delivery | delivered | failed | returned
    attempts: int = 0

    @property
    def on_time(self):
        if self.delivered_utc is None:
            return False
        return self.delivered_utc.date() <= self.promised_date

    @property
    def transit_hours(self):
        if self.delivered_utc is None:
            return None
        return (self.delivered_utc - self.intake_utc).total_seconds() / 3600.0


@dataclass
class Stop:
    seq: int
    parcel_ref: int
    zone: str
    dist_km: float
    arrival_utc: datetime
    dwell_min: float
    status: str                    # completed | failed


@dataclass
class RouteDay:
    day: date
    routing: str
    started_utc: datetime
    ended_utc: datetime
    planned_stops: int
    completed_stops: int
    failed_stops: int
    planned_km: float
    actual_km: float
    load_kg: float
    capacity_kg: float
    driver: str
    fuel_cost: float
    stops: list[Stop] = field(default_factory=list)


@dataclass
class SimResult:
    scenario: str
    variant_label: str
    seed: int
    start_date: date
    days: int
    parcels: list[Parcel] = field(default_factory=list)
    routes: list[RouteDay] = field(default_factory=list)
    disruption_log: list[str] = field(default_factory=list)


class CourierSimulator:
    def __init__(self, *, seed, start_date, days=7, variant="baseline"):
        self.seed = seed
        self.start_date = start_date
        self.days = days
        self.variant = C.variant(variant)
        self.variant_name = variant
        self.result = SimResult("courier", self.variant["label"], seed, start_date, days)
        self._next_ref = 0

    def _disr(self, di):
        return [d for d in self.variant.get("disruptions", ()) if di in d.day_index]

    def run(self) -> SimResult:
        backlog: list[Parcel] = []
        for di in range(self.days):
            day = self.start_date + timedelta(days=di)
            disr = self._disr(di)
            new = self._intake(day, di, disr)
            self.result.parcels.extend(new)
            depart = datetime.combine(day, time(11, 0), tzinfo=TZ).astimezone(UTC)
            # only parcels booked in before the van leaves can go out today
            same_day_ready = [p for p in new if (p.promised_date <= day
                              or p.service_level == "same_day") and p.intake_utc < depart]
            deferred = [p for p in new if p not in same_day_ready]
            ready = backlog + same_day_ready
            route, undelivered = self._run_route(day, di, ready, disr)
            if route:
                self.result.routes.append(route)
            backlog = undelivered + deferred
        # anything never delivered by horizon end
        for p in backlog:
            if p.status not in ("delivered", "returned"):
                p.status = "at_hub"
        self.result.disruption_log = [
            f"day {min(d.day_index) + 1}: {d.kind} - {d.note}"
            for d in self.variant.get("disruptions", ())
        ]
        return self.result

    def _intake(self, day, di, disr):
        rng = _rng(self.seed, "intake", di)
        base = C.PARCELS_PER_DAY * C.WEEKDAY_FACTOR[day.weekday()]
        for d in disr:
            if d.kind == "surge":
                base *= (1 + d.magnitude)
        n = max(0, int(rng.gauss(base, math.sqrt(max(base, 1)))))
        out = []
        for _ in range(n):
            zone = _weighted(rng, [z.name for z in C.ZONES], [z.demand_share for z in C.ZONES])
            size = _weighted(rng, list(C.PARCEL_SIZES),
                             [C.PARCEL_SIZES[s][2] for s in C.PARCEL_SIZES])
            (wlo, whi), dims, _ = C.PARCEL_SIZES[size]
            sl = _weighted(rng, list(C.SERVICE_LEVELS),
                           [C.SERVICE_LEVELS[s][1] for s in C.SERVICE_LEVELS])
            am = rng.random() < C.AM_INTAKE_SHARE
            hour = rng.randint(7, 10) if am else rng.randint(11, 17)
            intake = datetime.combine(day, time(hour, rng.randint(0, 59)), tzinfo=TZ).astimezone(UTC)
            promise_days = C.SERVICE_LEVELS[sl][0]
            if sl == "same_day" and not am:
                promise_days = 1        # missed the cutoff
            out.append(Parcel(
                self._ref(), rng.choice(C.SENDERS),
                f"{rng.choice(C.RECIPIENT_FIRST)} {rng.choice(C.RECIPIENT_LAST)}",
                zone, size, round(rng.uniform(wlo, whi), 2), dims, sl, intake,
                day + timedelta(days=promise_days)))
        return out

    def _ref(self):
        self._next_ref += 1
        return self._next_ref

    def _run_route(self, day, di, ready, disr):
        if not ready:
            return None, []
        rng = _rng(self.seed, "route", di)
        driver = C.EMPLOYEES[di % len(C.EMPLOYEES)]

        cap_kg = C.VAN_CAPACITY_KG
        shift_h = C.DRIVER_SHIFT_HOURS
        breakdown = next((d for d in disr if d.kind == "van_breakdown"), None)
        if breakdown:
            cap_kg *= breakdown.magnitude
            shift_h *= 0.55

        # sort/dispatch: load van up to capacity, prioritising urgency then intake age
        ready.sort(key=lambda p: (C.SERVICE_LEVELS[p.service_level][0], p.intake_utc))
        load, load_kg = [], 0.0
        for p in ready:
            if len(load) >= C.VAN_CAPACITY_PARCELS or load_kg + p.weight_kg > cap_kg:
                continue
            load.append(p)
            load_kg += p.weight_kg
        undelivered_at_hub = [p for p in ready if p not in load]

        routing = self.variant["routing"]
        zone_km = {z.name: z.km_from_hub for z in C.ZONES}
        if routing == "nearest_neighbour":
            # continuous outward sweep by distance from hub, tie-break recipient
            seq = sorted(load, key=lambda p: (round(zone_km[p.zone]), p.recipient))
            eff = 0.86
        else:  # zone batched — nearest zone first
            seq = sorted(load, key=lambda p: (zone_km[p.zone], p.recipient))
            eff = 1.0

        depart = datetime.combine(day, time(11, 0), tzinfo=TZ).astimezone(UTC)
        t = depart
        km = 0.0
        planned_km = 0.0
        zone_by_name = {z.name: z for z in C.ZONES}
        weather = rng.uniform(0.92, 1.35)
        completed = failed = 0
        stops: list[Stop] = []
        prev_zone = None
        cutoff = depart + timedelta(hours=shift_h)

        for i, p in enumerate(seq):
            z = zone_by_name[p.zone]
            if prev_zone is None:
                leg = z.km_from_hub                       # hub -> first stop
            elif prev_zone != p.zone:
                leg = abs(z.km_from_hub - zone_km[prev_zone]) + z.intra_leg_km
            else:
                leg = z.intra_leg_km
            leg *= eff * rng.uniform(0.8, 1.3)
            planned_km += leg
            if t >= cutoff:
                p.attempts += 1
                p.status = "failed" if p.attempts < C.MAX_ATTEMPTS else "returned"
                failed += 1
                continue
            hour_local = t.astimezone(TZ).hour
            traffic = C.TRAFFIC_BY_HOUR.get(hour_local, 1.1)
            travel_min = (leg / C.AVG_SPEED_KMH) * 60 * min(1.7, traffic * weather)
            t = t + timedelta(minutes=travel_min)
            km += leg
            dwell = C.SERVICE_MIN_PER_STOP * rng.uniform(0.6, 1.8)
            if i and i % 12 == 0:
                t += timedelta(minutes=C.DRIVER_BREAK_MIN / 2)

            success_p = C.BASE_FIRST_ATTEMPT_SUCCESS - 0.06 * max(0.0, weather - 1.1)
            if p.service_level == "same_day" and t.astimezone(TZ).hour >= 18:
                success_p -= 0.15
            if p.attempts >= 1:
                success_p += 0.05
            if rng.random() < success_p:
                p.delivered_utc = t + timedelta(minutes=dwell)
                p.status = "delivered"
                completed += 1
                stops.append(Stop(len(stops) + 1, p.ref, p.zone, round(leg, 2),
                                  t, round(dwell, 1), "completed"))
            else:
                p.attempts += 1
                p.status = "failed" if p.attempts < C.MAX_ATTEMPTS else "returned"
                failed += 1
                stops.append(Stop(len(stops) + 1, p.ref, p.zone, round(leg, 2),
                                  t, round(dwell, 1), "failed"))
            t += timedelta(minutes=dwell)
            prev_zone = p.zone

        # return leg to hub
        if seq:
            back = zone_by_name[seq[-1].zone].km_from_hub * eff
            km += back
            planned_km += back
            t += timedelta(minutes=(back / C.AVG_SPEED_KMH) * 60)

        route = RouteDay(
            day=day, routing=routing, started_utc=depart, ended_utc=t,
            planned_stops=len(load), completed_stops=completed, failed_stops=failed,
            planned_km=round(planned_km, 1), actual_km=round(km, 1),
            load_kg=round(load_kg, 1), capacity_kg=round(cap_kg, 1), driver=driver,
            fuel_cost=round(km * C.FUEL_COST_PER_KM, 2), stops=stops)

        carry = [p for p in load if p.status in ("failed",)] + undelivered_at_hub
        return route, carry

    def _nn_sequence(self, load):
        if not load:
            return []
        zone_by_name = {z.name: z for z in C.ZONES}
        remaining = list(load)
        seq = [remaining.pop(0)]
        while remaining:
            cz = zone_by_name[seq[-1].zone]
            remaining.sort(key=lambda p: abs(zone_by_name[p.zone].km_from_hub - cz.km_from_hub))
            seq.append(remaining.pop(0))
        return seq
