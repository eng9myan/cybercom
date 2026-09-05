"""KPI rollup + CSV/JSON export for an Anabtawi `SimResult`."""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .engine_anabtawi import SimResult
from .scenarios import anabtawi as A


def _pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


class AnabtawiKpis:
    def __init__(self, result: SimResult):
        self.r = result

    def summary(self) -> dict:
        b = self.r.batches
        made = [x for x in b if not x.blocked]
        planned_kg = sum(x.planned_kg for x in made)
        good_kg = sum(x.good_kg for x in made)
        scrap_kg = sum(x.scrap_kg for x in made)
        raw_val_in = sum(rr.cost for rr in self.r.raw_receipts)
        raw_val_used = sum(
            q * A.RAW_BY_SKU[s].cost_per_kg
            for x in made for s, q in x.raw_consumed.items()
        )

        prod_by = defaultdict(lambda: {"batches": 0, "good": 0.0, "scrap": 0.0, "blocked": 0})
        for x in b:
            pb = prod_by[x.product_sku]
            pb["batches"] += 1
            if x.blocked:
                pb["blocked"] += 1
            else:
                pb["good"] += x.good_kg
                pb["scrap"] += x.scrap_kg

        retail = self.r.retail
        retail_rev = sum(s.revenue for s in retail)
        retail_kg = sum(s.kg for s in retail)
        by_branch = defaultdict(lambda: {"kg": 0.0, "rev": 0.0})
        for s in retail:
            by_branch[s.branch]["kg"] += s.kg
            by_branch[s.branch]["rev"] += s.revenue

        shipments = self.r.shipments
        exp_orders = self.r.export_orders
        on_time = [s for s in shipments if s.on_time]
        exp_net = sum(s.total_net_kg for s in shipments)
        exp_gross = sum(s.total_gross_kg for s in shipments)
        exp_cartons = sum(s.total_cartons for s in shipments)
        freight = sum(s.freight_cost for s in shipments)
        exp_rev = sum(
            l.net_kg * A.PRODUCT_BY_SKU[l.product_sku].wholesale_per_kg
            for o in exp_orders if o.fulfilled for l in o.lines
        )
        by_dest = defaultdict(lambda: {"orders": 0, "shipments": 0, "net_kg": 0.0,
                                       "cartons": 0, "on_time": 0, "freight": 0.0})
        for o in exp_orders:
            by_dest[o.dest_country]["orders"] += 1
        for s in shipments:
            dd = by_dest[s.dest_country]
            dd["shipments"] += 1
            dd["net_kg"] += s.total_net_kg
            dd["cartons"] += s.total_cartons
            dd["on_time"] += int(s.on_time)
            dd["freight"] += s.freight_cost

        total_rev = retail_rev + exp_rev
        gross_margin = total_rev - raw_val_used

        return {
            "scenario": self.r.scenario,
            "variant": self.r.variant_label,
            "seed": self.r.seed,
            "start_date": self.r.start_date.isoformat(),
            "days": self.r.days,
            "scale": self.r.scale,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "manufacturing": {
                "batches": len(b),
                "blocked_batches": sum(1 for x in b if x.blocked),
                "good_kg": round(good_kg, 1),
                "scrap_kg": round(scrap_kg, 1),
                "yield_pct": _pct(good_kg, planned_kg),
                "qc_defect_pct": _pct(scrap_kg, planned_kg),
                "avg_cycle_hours": round(statistics.mean([x.cycle_hours for x in made]), 1)
                if made else 0.0,
                "raw_consumed_value": round(raw_val_used, 2),
                "by_product": [
                    {"sku": k, "name": A.PRODUCT_BY_SKU[k].name, "batches": v["batches"],
                     "blocked": v["blocked"], "good_kg": round(v["good"], 1),
                     "scrap_kg": round(v["scrap"], 1)}
                    for k, v in sorted(prod_by.items())
                ],
            },
            "raw_materials": {
                "receipts": len(self.r.raw_receipts),
                "received_value": round(raw_val_in, 2),
                "shortage_blocked_batches": sum(1 for x in b if x.blocked),
            },
            "retail": {
                "revenue": round(retail_rev, 2),
                "kg_sold": round(retail_kg, 1),
                "sales_orders": len({(s.branch, s.day) for s in retail}),
                "by_branch": [
                    {"branch": k, "kg": round(v["kg"], 1), "revenue": round(v["rev"], 2)}
                    for k, v in sorted(by_branch.items())
                ],
            },
            "export": {
                "orders": len(exp_orders),
                "fulfilled_orders": sum(1 for o in exp_orders if o.fulfilled),
                "shipments": len(shipments),
                "consolidation_ratio": round(len([o for o in exp_orders if o.shipment_ref])
                                             / len(shipments), 2) if shipments else 0.0,
                "on_time_pct": _pct(len(on_time), len(shipments)),
                "total_net_weight_kg": round(exp_net, 1),
                "total_gross_weight_kg": round(exp_gross, 1),
                "total_cartons": exp_cartons,
                "freight_cost": round(freight, 2),
                "freight_per_kg": round(freight / exp_net, 3) if exp_net else 0.0,
                "backorder_kg": self.r.backorders_kg,
                "revenue": round(exp_rev, 2),
                "by_destination": [
                    {"country": k, "orders": v["orders"], "shipments": v["shipments"],
                     "net_kg": round(v["net_kg"], 1), "cartons": v["cartons"],
                     "on_time_pct": _pct(v["on_time"], v["shipments"]),
                     "freight": round(v["freight"], 2)}
                    for k, v in sorted(by_dest.items())
                ],
            },
            "financials": {
                "total_revenue": round(total_rev, 2),
                "retail_revenue": round(retail_rev, 2),
                "export_revenue": round(exp_rev, 2),
                "raw_material_cost": round(raw_val_used, 2),
                "gross_margin": round(gross_margin, 2),
                "gross_margin_pct": _pct(gross_margin, total_rev),
            },
            "disruptions": self.r.disruption_log,
        }

    def write_files(self, out_dir: Path) -> list[str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        p = out_dir / "kpi_summary.json"
        p.write_text(json.dumps(self.summary(), indent=2), encoding="utf-8")
        written.append(str(p))

        p = out_dir / "production_batches.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["day", "product", "planned_kg", "good_kg", "scrap_kg", "blocked", "note"])
            for x in self.r.batches:
                w.writerow([x.day.isoformat(), x.product_sku, x.planned_kg, x.good_kg,
                            x.scrap_kg, x.blocked, x.note])
        written.append(str(p))

        p = out_dir / "export_shipments.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ref", "destination", "incoterm", "mode", "orders", "cartons",
                        "net_kg", "gross_kg", "dispatch", "delivered", "promised", "on_time",
                        "freight"])
            for s in self.r.shipments:
                w.writerow([s.ref, f"{s.dest_city},{s.dest_country}", s.incoterm, s.mode,
                            len(s.order_refs), s.total_cartons, s.total_net_kg, s.total_gross_kg,
                            s.dispatch_utc.isoformat(), s.delivered_utc.isoformat(),
                            s.promised_latest.isoformat(), s.on_time, s.freight_cost])
        written.append(str(p))

        p = out_dir / "retail_sales.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["day", "branch", "product", "kg", "revenue"])
            for s in self.r.retail:
                w.writerow([s.day.isoformat(), s.branch, s.product_sku, s.kg, s.revenue])
        written.append(str(p))
        return written
