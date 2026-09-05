"""KPI rollup + flat-file export for a hospital `SimResult`."""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .engine import SimResult
from .scenarios import hospital as H

_INPATIENT_WARDS = [w for w in H.WARDS if w not in ("ED", "OR", "PACU")]
_ICU_WARDS = ["ICU", "CCU", "NICU"]
_INPATIENT_BEDS = sum(H.WARDS[w][2] for w in _INPATIENT_WARDS)
_ICU_BEDS = sum(H.WARDS[w][2] for w in _ICU_WARDS)


def _pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


def _p90(xs):
    if not xs:
        return 0.0
    s = sorted(xs)
    return round(s[max(0, int(round(0.9 * (len(s) - 1))))], 1)


def _overlap_hours(a0, a1, w0, w1):
    lo, hi = max(a0, w0), min(a1, w1)
    return max(0.0, (hi - lo).total_seconds() / 3600.0)


class HospitalKpis:
    def __init__(self, result: SimResult):
        self.r = result
        self.w0 = datetime.combine(result.start_date, datetime.min.time(), tzinfo=timezone.utc)
        self.w1 = self.w0 + timedelta(days=result.days)
        self._win_h = (self.w1 - self.w0).total_seconds() / 3600.0

    # -- census ------------------------------------------------------

    def _timeweighted_census(self, stays, wards=None):
        h = 0.0
        for s in stays:
            if wards and s.ward not in wards:
                continue
            h += _overlap_hours(s.admit_utc, s.discharge_utc, self.w0, self.w1)
        return h / self._win_h if self._win_h else 0.0

    def _icu_timeweighted(self):
        h = 0.0
        for s in self.r.stays:
            if s.icu and s.icu_admit_utc and s.icu_release_utc:
                h += _overlap_hours(s.icu_admit_utc, s.icu_release_utc, self.w0, self.w1)
        return h / self._win_h if self._win_h else 0.0

    def _peak_census(self):
        ev = []
        for s in self.r.stays:
            ev.append((s.admit_utc, 1))
            ev.append((s.discharge_utc, -1))
        ev.sort()
        cur = peak = 0
        for _, d in ev:
            cur += d
            peak = max(peak, cur)
        return peak

    # -- summary ---------------------------------------------------

    def summary(self) -> dict:
        ed = self.r.ed_visits
        seen = [v for v in ed if v.disposition != "lwbs"]
        d2p = [v.door_to_provider_min for v in seen if v.door_to_provider_min is not None]
        d2d = [v.door_to_dispo_min for v in seen]
        admits = [v for v in ed if v.disposition in ("admitted", "transferred")]
        lwbs = [v for v in ed if v.disposition == "lwbs"]

        by_esi = defaultdict(lambda: {"visits": 0, "dispo": []})
        for v in seen:
            by_esi[v.esi]["visits"] += 1
            by_esi[v.esi]["dispo"].append(v.door_to_dispo_min)

        all_orders = ([o for v in ed for o in v.orders]
                      + [o for v in self.r.clinic_visits for o in v.orders]
                      + [o for s in self.r.stays for o in s.orders])
        by_kind = defaultdict(lambda: {"tat": [], "stat": 0})
        for o in all_orders:
            bucket = o.kind
            if o.kind == "lab" and o.code in H.LAB_BY_CODE and H.LAB_BY_CODE[o.code].turnaround[0] > 600:
                bucket = "microbiology"
            by_kind[bucket]["tat"].append(o.tat_min)
            by_kind[bucket]["stat"] += int(o.priority == "stat")

        clinic = self.r.clinic_visits
        booked = [c for c in clinic if c.status in ("fulfilled", "no_show")]
        fulfilled = [c for c in clinic if c.status == "fulfilled"]
        no_show = [c for c in clinic if c.status == "no_show"]
        walk_ins = [c for c in clinic if c.status == "walk_in"]

        boarding = [s for s in self.r.stays if s.boarding_min > 5]

        sl_stats = defaultdict(lambda: {"ed": 0, "adm": 0, "los": [], "orders": 0})
        for v in ed:
            sl_stats[v.service_line]["ed"] += 1
        for s in self.r.stays:
            sl_stats[s.service_line]["adm"] += 1
            sl_stats[s.service_line]["los"].append(s.los_hours / 24.0)
            sl_stats[s.service_line]["orders"] += len(s.orders)

        ward_adm = defaultdict(int)
        for s in self.r.stays:
            ward_adm[s.ward] += 1

        census = self._timeweighted_census(self.r.stays, _INPATIENT_WARDS)
        los_days = [s.los_hours / 24.0 for s in self.r.stays]

        return {
            "scenario": self.r.scenario,
            "variant": self.r.variant_label,
            "seed": self.r.seed,
            "start_date": self.r.start_date.isoformat(),
            "days": self.r.days,
            "scale": self.r.scale,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "emergency": {
                "visits": len(ed),
                "admit_rate": _pct(len(admits), len(ed)),
                "lwbs_rate": _pct(len(lwbs), len(ed)),
                "avg_door_to_provider_min": round(statistics.mean(d2p), 1) if d2p else 0.0,
                "avg_door_to_disposition_min": round(statistics.mean(d2d), 1) if d2d else 0.0,
                "p90_door_to_disposition_min": _p90(d2d),
                "by_esi": {
                    str(k): {"visits": v["visits"],
                             "avg_disposition_min": round(statistics.mean(v["dispo"]), 1)
                             if v["dispo"] else 0.0}
                    for k, v in sorted(by_esi.items())
                },
            },
            "inpatient": {
                "admissions": len(self.r.stays),
                "avg_daily_census": round(census, 1),
                "peak_census": self._peak_census(),
                "bed_occupancy_pct": _pct(census, _INPATIENT_BEDS),
                "alos_days": round(statistics.mean(los_days), 2) if los_days else 0.0,
                "icu": {
                    "stays": sum(1 for s in self.r.stays if s.icu),
                    "avg_daily_census": round(self._icu_timeweighted(), 1),
                    "occupancy_pct": _pct(self._icu_timeweighted(), _ICU_BEDS),
                },
                "boarding": {
                    "count": len(boarding),
                    "avg_boarding_min": round(statistics.mean([s.boarding_min for s in boarding]), 1)
                    if boarding else 0.0,
                    "total_boarding_hours": round(sum(s.boarding_min for s in boarding) / 60.0, 1),
                },
            },
            "orders": {
                "total": len(all_orders),
                "by_kind": {
                    k: {"count": len(v["tat"]),
                        "avg_tat_min": round(statistics.mean(v["tat"]), 1) if v["tat"] else 0.0,
                        "p90_tat_min": _p90(v["tat"]),
                        "stat_count": v["stat"]}
                    for k, v in sorted(by_kind.items())
                },
            },
            "clinics": {
                "scheduled": len(booked),
                "fulfilled": len(fulfilled),
                "no_show_rate": _pct(len(no_show), len(booked)),
                "walk_ins": len(walk_ins),
                "utilization_pct": _pct(len(fulfilled) + len(walk_ins), len(booked) + len(walk_ins)),
            },
            "by_service_line": [
                {"key": k, "display": H.SL_BY_KEY[k].display if k in H.SL_BY_KEY else k,
                 "ed_visits": v["ed"], "admissions": v["adm"],
                 "admit_rate": _pct(v["adm"], v["ed"]) if v["ed"] else None,
                 "alos_days": round(statistics.mean(v["los"]), 2) if v["los"] else 0.0,
                 "orders": v["orders"]}
                for k, v in sorted(sl_stats.items())
            ],
            "wards": [
                {"code": w, "name": H.WARDS[w][0], "beds": H.WARDS[w][2],
                 "occupancy_pct": _pct(self._timeweighted_census(self.r.stays, [w]), H.WARDS[w][2]),
                 "admissions": ward_adm[w]}
                for w in _INPATIENT_WARDS
            ],
            "by_day": self._by_day(),
            "csat_proxy": self._csat(d2d, lwbs, ed, boarding),
            "disruptions": self.r.disruption_log,
        }

    def _by_day(self):
        rows = []
        for di in range(self.r.days):
            d0 = self.w0 + timedelta(days=di)
            d1 = d0 + timedelta(days=1)
            rows.append({
                "date": d0.date().isoformat(),
                "ed_arrivals": sum(1 for v in self.r.ed_visits if d0 <= v.arrival_utc < d1),
                "admissions": sum(1 for s in self.r.stays if d0 <= s.admit_utc < d1),
                "discharges": sum(1 for s in self.r.stays if d0 <= s.discharge_utc < d1),
                "census_end": sum(1 for s in self.r.stays if s.admit_utc <= d1 <= s.discharge_utc),
            })
        return rows

    def _csat(self, d2d, lwbs, ed, boarding):
        score = 100.0
        if d2d:
            score -= max(0.0, (statistics.mean(d2d) - 180.0) / 10.0)
        score -= _pct(len(lwbs), max(len(ed), 1)) * 2.0
        score -= _pct(len(boarding), max(len(self.r.stays), 1)) * 0.4
        return round(max(0.0, min(100.0, score)), 1)

    # -- files ----------------------------------------------------

    def write_files(self, out_dir: Path) -> list[str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        s = self.summary()
        p = out_dir / "kpi_summary.json"
        p.write_text(json.dumps(s, indent=2), encoding="utf-8")
        written.append(str(p))

        p = out_dir / "ed_visits.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["arrival_utc", "service_line", "arrival_method", "esi",
                        "door_to_provider_min", "door_to_dispo_min", "disposition"])
            for v in sorted(self.r.ed_visits, key=lambda x: x.arrival_utc):
                w.writerow([v.arrival_utc.isoformat(), v.service_line, v.arrival_method, v.esi,
                            round(v.door_to_provider_min or 0, 1), round(v.door_to_dispo_min, 1),
                            v.disposition])
        written.append(str(p))

        p = out_dir / "orders.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ordered_utc", "kind", "code", "display", "priority", "context",
                        "service_line", "tat_min", "note"])
            allo = ([("ED", o) for v in self.r.ed_visits for o in v.orders]
                    + [("clinic", o) for v in self.r.clinic_visits for o in v.orders]
                    + [("inpatient", o) for st in self.r.stays for o in st.orders])
            for _, o in sorted(allo, key=lambda x: x[1].ordered_utc):
                w.writerow([o.ordered_utc.isoformat(), o.kind, o.code, o.display, o.priority,
                            o.context, o.service_line, round(o.tat_min, 1), o.note])
        written.append(str(p))

        p = out_dir / "census_by_day.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["date", "ed_arrivals", "admissions",
                                              "discharges", "census_end"])
            w.writeheader()
            for row in s["by_day"]:
                w.writerow(row)
        written.append(str(p))
        return written
