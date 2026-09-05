"""KPI rollup + CSV/JSON export for a courier `SimResult`."""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .engine_courier import SimResult
from .scenarios import courier as C


def _pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


def _p90(xs):
    if not xs:
        return 0.0
    s = sorted(xs)
    return round(s[max(0, int(round(0.9 * (len(s) - 1))))], 1)


class CourierKpis:
    def __init__(self, result: SimResult):
        self.r = result

    def summary(self) -> dict:
        p = self.r.parcels
        delivered = [x for x in p if x.status == "delivered"]
        returned = [x for x in p if x.status == "returned"]
        undelivered = [x for x in p if x.status in ("at_hub", "failed")]
        transit = [x.transit_hours for x in delivered if x.transit_hours is not None]
        on_time = [x for x in delivered if x.on_time]

        first_try = sum(1 for x in delivered if x.attempts == 0)

        total_km = sum(r.actual_km for r in self.r.routes)
        planned_km = sum(r.planned_km for r in self.r.routes)
        stops_done = sum(r.completed_stops for r in self.r.routes)
        loads = [r.load_kg / r.capacity_kg for r in self.r.routes if r.capacity_kg]
        shift_used = [
            (r.ended_utc - r.started_utc).total_seconds() / 3600.0 / C.DRIVER_SHIFT_HOURS
            for r in self.r.routes
        ]
        fuel = sum(r.fuel_cost for r in self.r.routes)
        handling = len(p) * C.HANDLING_COST_PER_PARCEL

        by_zone = defaultdict(lambda: {"n": 0, "ot": 0, "delivered": 0})
        by_sl = defaultdict(lambda: {"n": 0, "ot": 0, "delivered": 0, "transit": []})
        for x in p:
            by_zone[x.zone]["n"] += 1
            by_sl[x.service_level]["n"] += 1
            if x.status == "delivered":
                by_zone[x.zone]["delivered"] += 1
                by_sl[x.service_level]["delivered"] += 1
                if x.transit_hours is not None:
                    by_sl[x.service_level]["transit"].append(x.transit_hours)
                if x.on_time:
                    by_zone[x.zone]["ot"] += 1
                    by_sl[x.service_level]["ot"] += 1

        by_day = []
        for r in self.r.routes:
            by_day.append({
                "date": r.day.isoformat(), "routing": r.routing,
                "planned_stops": r.planned_stops, "completed": r.completed_stops,
                "failed": r.failed_stops, "km": round(r.actual_km, 1),
                "load_factor_pct": _pct(r.load_kg, r.capacity_kg),
                "fuel_cost": round(r.fuel_cost, 2)})

        csat = 100.0
        csat -= max(0.0, (95.0 - _pct(len(on_time), len(delivered)))) * 0.8
        csat -= _pct(len(returned), max(len(p), 1)) * 2.5
        csat -= max(0.0, (statistics.mean(transit) - 24.0) / 3.0) if transit else 0.0

        return {
            "scenario": self.r.scenario,
            "variant": self.r.variant_label,
            "seed": self.r.seed,
            "start_date": self.r.start_date.isoformat(),
            "days": self.r.days,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "parcels": {
                "intake": len(p),
                "delivered": len(delivered),
                "returned": len(returned),
                "undelivered_at_horizon": len(undelivered),
                "on_time_rate": _pct(len(on_time), len(delivered)),
                "first_attempt_success_rate": _pct(first_try, len(delivered)),
                "avg_transit_hours": round(statistics.mean(transit), 1) if transit else 0.0,
                "p90_transit_hours": _p90(transit),
            },
            "operations": {
                "routes": len(self.r.routes),
                "total_distance_km": round(total_km, 1),
                "planned_distance_km": round(planned_km, 1),
                "km_per_delivered_parcel": round(total_km / len(delivered), 2) if delivered else 0.0,
                "avg_stops_per_route": round(stops_done / len(self.r.routes), 1)
                if self.r.routes else 0.0,
                "avg_load_factor_pct": round(100.0 * statistics.mean(loads), 1) if loads else 0.0,
                "avg_driver_utilisation_pct": round(100.0 * statistics.mean(shift_used), 1)
                if shift_used else 0.0,
            },
            "cost": {
                "fuel": round(fuel, 2),
                "handling": round(handling, 2),
                "total": round(fuel + handling, 2),
                "cost_per_parcel": round((fuel + handling) / len(p), 3) if p else 0.0,
                "cost_per_delivered": round((fuel + handling) / len(delivered), 3)
                if delivered else 0.0,
            },
            "by_zone": [
                {"zone": z, "parcels": v["n"], "delivered": v["delivered"],
                 "on_time_rate": _pct(v["ot"], v["delivered"])}
                for z, v in sorted(by_zone.items())
            ],
            "by_service_level": [
                {"level": s, "parcels": v["n"], "delivered": v["delivered"],
                 "on_time_rate": _pct(v["ot"], v["delivered"]),
                 "avg_transit_hours": round(statistics.mean(v["transit"]), 1) if v["transit"] else 0.0}
                for s, v in sorted(by_sl.items())
            ],
            "by_day": by_day,
            "csat_proxy": round(max(0.0, min(100.0, csat)), 1),
            "disruptions": self.r.disruption_log,
        }

    def write_files(self, out_dir: Path) -> list[str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        p = out_dir / "kpi_summary.json"
        p.write_text(json.dumps(self.summary(), indent=2), encoding="utf-8")
        written.append(str(p))

        p = out_dir / "parcels.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ref", "sender", "recipient", "zone", "size", "weight_kg",
                        "service_level", "intake_utc", "promised_date", "delivered_utc",
                        "status", "attempts", "on_time"])
            for x in self.r.parcels:
                w.writerow([x.ref, x.sender, x.recipient, x.zone, x.size, x.weight_kg,
                            x.service_level, x.intake_utc.isoformat(), x.promised_date.isoformat(),
                            x.delivered_utc.isoformat() if x.delivered_utc else "",
                            x.status, x.attempts, x.on_time])
        written.append(str(p))

        p = out_dir / "routes.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "driver", "routing", "planned_stops", "completed", "failed",
                        "actual_km", "load_kg", "capacity_kg", "fuel_cost"])
            for r in self.r.routes:
                w.writerow([r.day.isoformat(), r.driver, r.routing, r.planned_stops,
                            r.completed_stops, r.failed_stops, round(r.actual_km, 1),
                            round(r.load_kg, 1), round(r.capacity_kg, 1), round(r.fuel_cost, 2)])
        written.append(str(p))
        return written
