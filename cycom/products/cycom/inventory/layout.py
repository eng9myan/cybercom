"""
Warehouse layout + occupancy for the visual map.

Builds the location tree once from a flat queryset (no N+1 per node) and
rolls stock up from bins to their parents, so a zone shows the total of
everything beneath it.

Occupancy is only meaningful where a capacity was actually set; a location
without one reports occupancy None rather than 0%, because "we don't know"
and "empty" are different things and colouring them the same would lie.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal


def build_layout(locations, stock_items) -> dict:
    """
    locations: StorageLocation queryset for one warehouse
    stock_items: StockItem queryset for the same warehouse (location may be null)

    Returns {"tree": [...roots], "unassigned": {...}, "totals": {...}}
    """
    # Keyed by str(id) throughout: parent_id is serialized as a string for
    # the client, and mixing UUID keys with string lookups silently fails to
    # link anything (every node becomes a root).
    nodes = {}
    for loc in locations:
        nodes[str(loc.id)] = {
            "id": str(loc.id),
            "code": loc.code,
            "name": loc.name,
            "location_type": loc.location_type,
            "capacity": float(loc.capacity) if loc.capacity is not None else None,
            "sort_order": loc.sort_order,
            "is_active": loc.is_active,
            "parent_id": str(loc.parent_id) if loc.parent_id else None,
            "children": [],
            "direct_quantity": 0.0,
            "direct_value": 0.0,
            "product_count": 0,
        }

    direct_qty = defaultdict(Decimal)
    direct_val = defaultdict(Decimal)
    direct_products = defaultdict(int)
    unassigned_qty = Decimal("0")
    unassigned_val = Decimal("0")
    unassigned_products = 0

    for item in stock_items:
        qty = item.quantity_on_hand or Decimal("0")
        val = qty * (item.average_cost or Decimal("0"))
        loc_key = str(item.location_id) if item.location_id else None
        if loc_key and loc_key in nodes:
            direct_qty[loc_key] += qty
            direct_val[loc_key] += val
            direct_products[loc_key] += 1
        else:
            unassigned_qty += qty
            unassigned_val += val
            unassigned_products += 1

    for loc_id, node in nodes.items():
        node["direct_quantity"] = float(direct_qty[loc_id])
        node["direct_value"] = float(direct_val[loc_id])
        node["product_count"] = direct_products[loc_id]

    roots = []
    for loc_id, node in nodes.items():
        parent = node["parent_id"]
        if parent and parent in nodes:
            nodes[parent]["children"].append(node)
        else:
            roots.append(node)

    def sort_and_roll(node):
        node["children"].sort(key=lambda c: (c["sort_order"], c["code"]))
        total_qty = Decimal(str(node["direct_quantity"]))
        total_val = Decimal(str(node["direct_value"]))
        total_products = node["product_count"]
        for child in node["children"]:
            sort_and_roll(child)
            total_qty += Decimal(str(child["total_quantity"]))
            total_val += Decimal(str(child["total_value"]))
            total_products += child["total_product_count"]
        node["total_quantity"] = float(total_qty)
        node["total_value"] = float(total_val)
        node["total_product_count"] = total_products
        cap = node["capacity"]
        # Unknown capacity stays None -- see module docstring.
        node["occupancy_percent"] = (
            round(min(float(total_qty) / cap * 100, 999), 1) if cap else None
        )
        return node

    roots.sort(key=lambda n: (n["sort_order"], n["code"]))
    for root in roots:
        sort_and_roll(root)

    return {
        "tree": roots,
        "unassigned": {
            "quantity": float(unassigned_qty),
            "value": float(unassigned_val),
            "product_count": unassigned_products,
        },
        "totals": {
            "locations": len(nodes),
            "bins": sum(1 for n in nodes.values() if n["location_type"] == "bin"),
            "quantity": float(sum(Decimal(str(r["total_quantity"])) for r in roots) + unassigned_qty),
            "value": float(sum(Decimal(str(r["total_value"])) for r in roots) + unassigned_val),
        },
    }
