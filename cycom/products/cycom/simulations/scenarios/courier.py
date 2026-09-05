"""
"Cycom Courier Co" — a two-person last-mile courier operation.

One hub, one van, two employees who both sort and drive. Data only; the engine
turns it into a 7-day run of parcel intake -> sort -> route -> deliver -> POD /
exception -> returns.
"""
from __future__ import annotations

from dataclasses import dataclass

CITY = "Amman"
COUNTRY = "JO"
TIMEZONE = "Asia/Amman"
COMPANY_NAME = "Cycom Courier Co"
EMPLOYEES = ["Sami Haddad", "Rami Odeh"]

VAN_LABEL = "VAN-01"
VAN_CAPACITY_KG = 850.0
VAN_CAPACITY_PARCELS = 110

DRIVER_SHIFT_HOURS = 9.0
DRIVER_BREAK_MIN = 45
SERVICE_MIN_PER_STOP = 6.5          # doorstep time
SORT_PARCELS_PER_PERSON_HR = 90
AVG_SPEED_KMH = 34.0


@dataclass(frozen=True)
class Zone:
    name: str
    km_from_hub: float
    intra_leg_km: float             # avg distance between two stops in the zone
    cross_city: bool
    demand_share: float


ZONES: tuple[Zone, ...] = (
    Zone("Amman Central", 5.0, 1.3, False, 0.40),
    Zone("Amman West", 9.0, 1.8, False, 0.26),
    Zone("Amman East", 8.0, 1.7, False, 0.20),
    Zone("Zarqa", 21.0, 2.4, True, 0.08),
    Zone("Salt", 25.0, 2.8, True, 0.04),
    Zone("Madaba", 24.0, 2.6, True, 0.02),
)

# size -> (weight_kg range, (L,W,H) cm, share)
PARCEL_SIZES = {
    "small": ((0.2, 2.0), (25, 20, 10), 0.52),
    "medium": ((2.0, 8.0), (40, 30, 25), 0.36),
    "large": ((8.0, 25.0), (60, 45, 40), 0.12),
}

SERVICE_LEVELS = {          # -> (promise_days, share, on_time_target_hours)
    "same_day": (0, 0.14, 9),
    "express": (1, 0.30, 28),
    "standard": (2, 0.56, 52),
}

PARCELS_PER_DAY = 44
WEEKDAY_FACTOR = {0: 1.10, 1: 1.05, 2: 1.02, 3: 1.00, 4: 0.85, 5: 0.55, 6: 0.95}
AM_INTAKE_SHARE = 0.58              # rest arrive in the afternoon (miss same-day cutoff)

TRAFFIC_BY_HOUR = {
    6: 0.9, 7: 1.25, 8: 1.5, 9: 1.35, 10: 1.1, 11: 1.05, 12: 1.1, 13: 1.15,
    14: 1.1, 15: 1.2, 16: 1.45, 17: 1.6, 18: 1.5, 19: 1.2, 20: 1.0,
}

BASE_FIRST_ATTEMPT_SUCCESS = 0.90
MAX_ATTEMPTS = 3
FUEL_COST_PER_KM = 0.11            # USD-equivalent
HANDLING_COST_PER_PARCEL = 0.35

RECIPIENT_FIRST = ["Ahmad", "Mohammad", "Omar", "Sara", "Rania", "Layla", "Yousef", "Huda",
                   "Khaled", "Dina", "Tariq", "Noor"]
RECIPIENT_LAST = ["Al-Zoubi", "Haddad", "Nazzal", "Khoury", "Al-Masri", "Saleh", "Odeh",
                  "Barakat", "Mansour", "Darwish", "Qasem"]
SENDERS = ["Souq.com JO", "Amman Books", "GreenLeaf Pharmacy", "TechBox", "Zaatar Foods",
           "Petra Cosmetics", "Desert Gear", "CityFlowers"]

# ---------------------------------------------------------------------------
# variants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Disruption:
    kind: str
    day_index: tuple[int, ...]
    magnitude: float = 1.0
    note: str = ""


VARIANTS: dict[str, dict] = {
    "baseline": {"label": "Baseline week", "routing": "zone_batched", "disruptions": ()},
    "surge": {
        "label": "Volume surge — +30% parcels on day 3 (sale event)",
        "routing": "zone_batched",
        "disruptions": (Disruption("surge", (2,), 0.30, "flash-sale backlog"),),
    },
    "van_breakdown": {
        "label": "Van breakdown on day 4 — half a shift lost, reduced capacity",
        "routing": "zone_batched",
        "disruptions": (Disruption("van_breakdown", (3,), 0.5, "gearbox failure, afternoon recovery"),),
    },
    "route_optimization": {
        "label": "Route optimisation — nearest-neighbour sequencing instead of zone batching",
        "routing": "nearest_neighbour",
        "disruptions": (),
    },
}


def variant(name: str) -> dict:
    if name not in VARIANTS:
        raise KeyError(f"unknown courier scenario '{name}'; choose from {sorted(VARIANTS)}")
    return VARIANTS[name]
