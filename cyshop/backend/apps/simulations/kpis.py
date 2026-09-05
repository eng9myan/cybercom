"""
KPI rollup + flat-file export for a QSR `SimResult`.

Computed straight off the engine result (deterministic, no DB round-trip). The
management command persists `summary()` onto `SimulationRun.summary` and writes
the CSVs from `write_files()` next to it.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .engine import SimResult
from .scenarios import qsr as S


def _pct(n, d) -> float:
    return round(100.0 * n / d, 2) if d else 0.0


def _p90(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, int(round(0.9 * (len(s) - 1))))
    return round(s[k], 1)


class QsrKpis:
    def __init__(self, result: SimResult):
        self.r = result
        self._country_name = {c.code: c.name for c in S.COUNTRIES}
        self._branch_meta = {b.code: (c.code, b.tier)
                             for c in S.COUNTRIES for b in c.branches}

    # -- inventory reconstruction --------------------------------------

    def _inventory_table(self):
        opening = defaultdict(float)
        for op in self.r.opening:
            opening[(op.branch_code, op.sku)] += op.qty
        received = defaultdict(float)
        for dv in self.r.deliveries:
            if dv.status in ("RECEIVED", "PARTIAL"):
                for sku, q in dv.lines.items():
                    received[(dv.branch_code, sku)] += q
        used = defaultdict(float)
        wasted = defaultdict(float)
        for c in self.r.consumption:
            used[(c.branch_code, c.sku)] += c.usage_qty
            wasted[(c.branch_code, c.sku)] += c.waste_qty

        rows = []
        keys = set(opening) | set(received) | set(used) | set(wasted)
        for (branch, sku) in sorted(keys):
            o, rcv, u, w = (opening[(branch, sku)], received[(branch, sku)],
                            used[(branch, sku)], wasted[(branch, sku)])
            end = o + rcv - u - w
            daily = u / self.r.days if self.r.days else 0.0
            cover = round(end / daily, 2) if daily > 0.01 else None
            rows.append({
                "branch": branch, "sku": sku, "name": S.RAW_BY_SKU[sku].name,
                "opening": round(o, 2), "received": round(rcv, 2),
                "used": round(u, 2), "wasted": round(w, 2),
                "end_qty": round(end, 2), "days_cover": cover,
                "value_used": round(u * S.RAW_BY_SKU[sku].unit_cost, 2),
                "value_wasted": round(w * S.RAW_BY_SKU[sku].unit_cost, 2),
            })
        return rows

    # -- summary ------------------------------------------------------

    def summary(self) -> dict:
        orders = self.r.orders
        gross = sum(o.subtotal for o in orders)
        discount = sum(o.discount for o in orders)
        tax = sum(o.tax for o in orders)
        units = sum(ln.qty for o in orders for ln in o.lines)
        waits = [o.wait_seconds for o in orders]
        on_time = sum(1 for o in orders if o.on_time)

        by_channel = defaultdict(lambda: {"orders": 0, "on_time": 0, "waits": []})
        for o in orders:
            ch = by_channel[o.channel]
            ch["orders"] += 1
            ch["on_time"] += int(o.on_time)
            ch["waits"].append(o.wait_seconds)
        channel_kpi = {
            k: {"orders": v["orders"],
                "on_time_rate": _pct(v["on_time"], v["orders"]),
                "avg_wait_seconds": round(statistics.mean(v["waits"]), 1) if v["waits"] else 0.0,
                "p90_wait_seconds": _p90(v["waits"])}
            for k, v in sorted(by_channel.items())
        }

        # by country / branch / day
        cty = defaultdict(lambda: {"orders": 0, "gross": 0.0, "on_time": 0, "waits": []})
        brn = defaultdict(lambda: {"orders": 0, "gross": 0.0, "units": 0, "on_time": 0, "waits": []})
        day = defaultdict(lambda: {"orders": 0, "gross": 0.0, "on_time": 0})
        for o in orders:
            for bucket in (cty[o.country_code], brn[o.branch_code]):
                bucket["orders"] += 1
                bucket["gross"] += o.subtotal
                bucket["on_time"] += int(o.on_time)
                bucket["waits"].append(o.wait_seconds)
            brn[o.branch_code]["units"] += sum(ln.qty for ln in o.lines)
            dd = day[o.placed_utc.date().isoformat()]
            dd["orders"] += 1
            dd["gross"] += o.subtotal
            dd["on_time"] += int(o.on_time)

        inv_rows = self._inventory_table()
        used_val = sum(r["value_used"] for r in inv_rows)
        waste_val = sum(r["value_wasted"] for r in inv_rows)
        covers = [(r["days_cover"], r["branch"], r["sku"]) for r in inv_rows
                  if r["days_cover"] is not None]
        worst_cover = min(covers) if covers else (None, None, None)

        branch_waste = defaultdict(lambda: [0.0, 0.0])
        branch_cover = defaultdict(list)
        for r in inv_rows:
            branch_waste[r["branch"]][0] += r["value_used"]
            branch_waste[r["branch"]][1] += r["value_wasted"]
            if r["days_cover"] is not None:
                branch_cover[r["branch"]].append(r["days_cover"])

        weekly_labor = self._weekly_labor_cost()
        lost = len(self.r.lost_sales)
        avg_check = (gross - discount) / len(orders) if orders else 0.0

        csat = self._csat_proxy(_pct(on_time, len(orders)),
                                statistics.mean(waits) if waits else 0.0, lost, len(orders))

        return {
            "scenario": self.r.scenario,
            "variant": self.r.variant_label,
            "seed": self.r.seed,
            "start_date": self.r.start_date.isoformat(),
            "days": self.r.days,
            "volume": self.r.volume,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "totals": {
                "gross_sales": round(gross, 2),
                "discounts": round(discount, 2),
                "net_sales": round(gross - discount, 2),
                "tax": round(tax, 2),
                "orders": len(orders),
                "units_sold": int(units),
                "avg_check": round(avg_check, 2),
                "lost_sales_orders": lost,
                "lost_sales_est_revenue": round(lost * avg_check, 2),
            },
            "service": {
                "on_time_rate": _pct(on_time, len(orders)),
                "avg_wait_seconds": round(statistics.mean(waits), 1) if waits else 0.0,
                "p90_wait_seconds": _p90(waits),
                "by_channel": channel_kpi,
            },
            "inventory": {
                "usage_value": round(used_val, 2),
                "waste_value": round(waste_val, 2),
                "waste_pct_of_usage": _pct(waste_val, used_val),
                "tightest_cover_days": worst_cover[0],
                "tightest_cover_at": f"{worst_cover[1]}/{worst_cover[2]}" if worst_cover[1] else None,
                "deliveries": len(self.r.deliveries),
                "open_purchase_orders": sum(1 for d in self.r.deliveries if d.status == "OPEN"),
            },
            "labor": {
                "weekly_labor_cost": round(weekly_labor, 2),
                "labor_pct_of_net_sales": _pct(weekly_labor, gross - discount),
            },
            "csat_proxy": csat,
            "by_country": [
                {"code": k, "name": self._country_name[k],
                 "gross_sales": round(v["gross"], 2), "orders": v["orders"],
                 "avg_check": round(v["gross"] / v["orders"], 2) if v["orders"] else 0.0,
                 "on_time_rate": _pct(v["on_time"], v["orders"]),
                 "avg_wait_seconds": round(statistics.mean(v["waits"]), 1) if v["waits"] else 0.0}
                for k, v in sorted(cty.items())
            ],
            "by_branch": [
                {"code": k, "country": self._branch_meta[k][0], "tier": self._branch_meta[k][1],
                 "gross_sales": round(v["gross"], 2), "orders": v["orders"],
                 "units": int(v["units"]),
                 "avg_check": round(v["gross"] / v["orders"], 2) if v["orders"] else 0.0,
                 "on_time_rate": _pct(v["on_time"], v["orders"]),
                 "avg_wait_seconds": round(statistics.mean(v["waits"]), 1) if v["waits"] else 0.0,
                 "min_days_cover": round(min(branch_cover[k]), 2) if branch_cover[k] else None,
                 "waste_pct": _pct(branch_waste[k][1], branch_waste[k][0])}
                for k, v in sorted(brn.items())
            ],
            "by_day": [
                {"date": k, "gross_sales": round(v["gross"], 2), "orders": v["orders"],
                 "on_time_rate": _pct(v["on_time"], v["orders"])}
                for k, v in sorted(day.items())
            ],
            "disruptions": self.r.disruption_log,
        }

    def _weekly_labor_cost(self) -> float:
        total_month = 0.0
        for c in S.COUNTRIES:
            for b in c.branches:
                foot = S.TIER_FOOTFALL[b.tier]
                for role, spec in S.STAFF_TEMPLATE.items():
                    count = max(1, round(spec["count"] * (foot if spec["kind"] == "hourly" else 1)))
                    total_month += count * spec["monthly_salary"]
        return total_month * (self.r.days / 30.0)

    def _csat_proxy(self, on_time_rate, avg_wait, lost, orders) -> float:
        score = 100.0
        score -= max(0.0, (95.0 - on_time_rate)) * 0.6
        score -= max(0.0, (avg_wait - 210.0) / 12.0)
        score -= _pct(lost, max(orders + lost, 1)) * 1.5
        return round(max(0.0, min(100.0, score)), 1)

    # -- flat files -------------------------------------------------

    def write_files(self, out_dir: Path) -> list[str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        written = []

        summ = self.summary()
        p = out_dir / "kpi_summary.json"
        p.write_text(json.dumps(summ, indent=2), encoding="utf-8")
        written.append(str(p))

        # orders by branch/day/daypart/channel
        agg = defaultdict(lambda: {"orders": 0, "gross": 0.0, "units": 0})
        for o in self.r.orders:
            key = (o.country_code, o.branch_code, o.placed_utc.date().isoformat(),
                   o.daypart, o.channel)
            a = agg[key]
            a["orders"] += 1
            a["gross"] += o.subtotal
            a["units"] += sum(ln.qty for ln in o.lines)
        p = out_dir / "orders_by_branch_day.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["country", "branch", "date", "daypart", "channel", "orders", "gross_sales", "units"])
            for (cc, bc, d, dp, ch), a in sorted(agg.items()):
                w.writerow([cc, bc, d, dp, ch, a["orders"], round(a["gross"], 2), int(a["units"])])
        written.append(str(p))

        # hourly heatmap feed
        hourly = defaultdict(lambda: {"orders": 0, "gross": 0.0})
        for o in self.r.orders:
            key = (o.country_code, o.branch_code, o.placed_utc.date().isoformat(),
                   o.placed_utc.hour)
            hourly[key]["orders"] += 1
            hourly[key]["gross"] += o.subtotal
        p = out_dir / "orders_by_hour.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["country", "branch", "date", "utc_hour", "orders", "gross_sales"])
            for (cc, bc, d, h), a in sorted(hourly.items()):
                w.writerow([cc, bc, d, h, a["orders"], round(a["gross"], 2)])
        written.append(str(p))

        # menu mix
        mix = defaultdict(lambda: {"qty": 0, "gross": 0.0})
        for o in self.r.orders:
            for ln in o.lines:
                m = mix[(o.country_code, ln.menu_code)]
                m["qty"] += ln.qty
                m["gross"] += ln.qty * ln.unit_price
        p = out_dir / "menu_mix.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["country", "menu_code", "name", "qty_sold", "gross_sales"])
            for (cc, code), m in sorted(mix.items()):
                w.writerow([cc, code, S.MENU_BY_CODE[code].name, int(m["qty"]), round(m["gross"], 2)])
        written.append(str(p))

        # inventory
        p = out_dir / "inventory_by_branch_sku.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "branch", "sku", "name", "opening", "received", "used", "wasted",
                "end_qty", "days_cover", "value_used", "value_wasted"])
            w.writeheader()
            for row in self._inventory_table():
                w.writerow(row)
        written.append(str(p))

        # deliveries
        p = out_dir / "deliveries.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["branch", "supplier", "ordered_day", "expected_day", "arrived_day",
                        "status", "value", "note"])
            for dv in sorted(self.r.deliveries, key=lambda d: (d.branch_code, d.ordered_day)):
                w.writerow([dv.branch_code, dv.supplier_key, dv.ordered_day,
                            dv.expected_day, dv.arrived_day or "", dv.status, dv.value, dv.note])
        written.append(str(p))

        return written
