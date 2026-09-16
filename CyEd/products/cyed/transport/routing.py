"""
Route optimization + ETA. Real geo maths (haversine + greedy nearest-neighbour);
no external routing provider required. A traffic-aware provider can slot in behind
`optimize_route` later without changing callers.
"""

import math
from decimal import Decimal


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlmb = math.radians(float(lng2) - float(lng1))
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def optimize_order(stops, start=None):
    """
    Greedy nearest-neighbour ordering of stops (each: dict with lat/lng/id).
    `start` = (lat, lng) origin (e.g. the school); defaults to the first stop.
    Returns (ordered_stops, total_distance_km).
    """
    pts = [s for s in stops if s.get("lat") is not None and s.get("lng") is not None]
    if not pts:
        return stops, 0.0
    remaining = pts[:]
    if start is None:
        current = remaining.pop(0)
        ordered = [current]
        cx, cy = current["lat"], current["lng"]
    else:
        cx, cy = start
        ordered = []
    total = 0.0
    while remaining:
        nxt = min(remaining, key=lambda s: haversine_km(cx, cy, s["lat"], s["lng"]))
        total += haversine_km(cx, cy, nxt["lat"], nxt["lng"])
        ordered.append(nxt)
        cx, cy = nxt["lat"], nxt["lng"]
        remaining.remove(nxt)
    return ordered, round(total, 2)


def eta_minutes(bus_lat, bus_lng, ordered_stops, avg_speed_kmh=30.0):
    """Cumulative ETA (minutes) to each remaining stop from the bus's position."""
    speed = max(5.0, float(avg_speed_kmh))
    out = []
    cx, cy = bus_lat, bus_lng
    cumulative = 0.0
    for s in ordered_stops:
        if s.get("lat") is None or s.get("lng") is None:
            continue
        d = haversine_km(cx, cy, s["lat"], s["lng"])
        cumulative += d
        out.append({"stop": s.get("id"), "name": s.get("name"),
                    "distance_km": round(d, 2), "eta_min": round(cumulative / speed * 60, 1)})
        cx, cy = s["lat"], s["lng"]
    return out
