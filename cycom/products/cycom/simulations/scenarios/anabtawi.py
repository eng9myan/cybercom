"""
"Anabtawi Group" — a diversified sweets business run as three connected lines:

  * Anabtawi Sweets Manufacturing  — a plant producing oriental sweets in batches
  * Anabtawi Oriental Sweets       — a 4-branch retail network
  * Anabtawi Export & Distribution — consolidated international shipments

Manufacturing output feeds both retail and export. Data only; the engine turns
this into a 7-day flow from raw-material consumption to delivery abroad.
"""
from __future__ import annotations

from dataclasses import dataclass

ORG_NAME = "Anabtawi Group"
ORIGIN_CITY = "Amman"
ORIGIN_COUNTRY = "JO"
TIMEZONE = "Asia/Amman"
CURRENCY = "USD"

DIVISIONS = ("Anabtawi Sweets Manufacturing", "Anabtawi Oriental Sweets", "Anabtawi Export & Distribution")

# ---------------------------------------------------------------------------
# raw materials — cost per kg, shelf life, pack (kg), supplier lead time (days)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Raw:
    sku: str
    name: str
    cost_per_kg: float
    shelf_life_days: int
    pack_kg: int
    lead_time_days: int


RAW_MATERIALS: tuple[Raw, ...] = (
    Raw("RM-FLOUR", "Wheat flour", 0.7, 120, 50, 3),
    Raw("RM-SEMOLINA", "Semolina", 0.9, 120, 50, 3),
    Raw("RM-SUGAR", "Sugar", 0.8, 365, 50, 4),
    Raw("RM-PISTA", "Pistachio", 22.0, 180, 20, 7),
    Raw("RM-WALNUT", "Walnut", 11.0, 180, 20, 7),
    Raw("RM-GHEE", "Clarified butter (ghee)", 6.5, 90, 20, 5),
    Raw("RM-HONEY", "Honey / sugar syrup", 3.2, 365, 25, 4),
    Raw("RM-ROSE", "Rosewater", 4.0, 365, 10, 6),
    Raw("RM-PHYLLO", "Phyllo dough", 2.4, 20, 15, 2),
    Raw("RM-DATES", "Date paste", 3.6, 180, 20, 5),
    Raw("RM-BOX", "Gift box + liner", 0.45, 720, 500, 10),
)
RAW_BY_SKU = {r.sku: r for r in RAW_MATERIALS}

# ---------------------------------------------------------------------------
# finished goods — recipe (raw kg per 1 kg output), yield, batch size, cycle
# wholesale + retail price per kg
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    recipe: dict[str, float]
    yield_pct: float
    batch_kg: int
    cycle_hours: float
    wholesale_per_kg: float
    retail_per_kg: float
    shelf_life_days: int
    export_share: float             # relative export demand weight
    retail_share: float


PRODUCTS: tuple[Product, ...] = (
    Product("FG-BAKLAVA", "Baklava", {"RM-PHYLLO": 0.35, "RM-PISTA": 0.22, "RM-GHEE": 0.20,
                                      "RM-HONEY": 0.18, "RM-SUGAR": 0.08},
            0.93, 120, 5.0, 14.0, 24.0, 45, export_share=1.6, retail_share=1.4),
    Product("FG-MAAMOUL", "Maamoul (date & nut)", {"RM-SEMOLINA": 0.42, "RM-DATES": 0.28,
                                                   "RM-GHEE": 0.16, "RM-WALNUT": 0.08, "RM-SUGAR": 0.06},
            0.95, 150, 4.0, 9.5, 18.0, 60, export_share=1.3, retail_share=1.6),
    Product("FG-KUNAFA", "Kunafa", {"RM-PHYLLO": 0.40, "RM-GHEE": 0.22, "RM-SUGAR": 0.20,
                                    "RM-PISTA": 0.10, "RM-ROSE": 0.02},
            0.90, 90, 3.0, 11.0, 20.0, 7, export_share=0.5, retail_share=1.5),
    Product("FG-BARAZEK", "Barazek (sesame)", {"RM-FLOUR": 0.45, "RM-SUGAR": 0.20, "RM-GHEE": 0.18,
                                               "RM-HONEY": 0.10},
            0.94, 100, 3.5, 10.0, 19.0, 60, export_share=1.0, retail_share=0.8),
    Product("FG-GHRAYBEH", "Ghraybeh (shortbread)", {"RM-FLOUR": 0.5, "RM-GHEE": 0.28, "RM-SUGAR": 0.18},
            0.96, 100, 3.0, 8.0, 15.0, 90, export_share=0.7, retail_share=0.7),
    Product("FG-MIXEDBOX", "Assorted gift box", {"RM-PHYLLO": 0.18, "RM-PISTA": 0.12, "RM-SEMOLINA": 0.15,
                                                 "RM-DATES": 0.12, "RM-GHEE": 0.16, "RM-HONEY": 0.10,
                                                 "RM-SUGAR": 0.09, "RM-BOX": 0.02},
            0.92, 80, 6.0, 20.0, 38.0, 30, export_share=1.8, retail_share=1.2),
)
PRODUCT_BY_SKU = {p.sku: p for p in PRODUCTS}

PLANT_BATCHES_PER_DAY = 16
PLANT_QC_DEFECT_PCT = 0.025
OPENING_RAW_DAYS = 9.0
OPENING_FG_DAYS = 3.0
REORDER_RAW_DAYS = 6.0
REORDER_UP_TO_RAW_DAYS = 12.0

# ---------------------------------------------------------------------------
# retail — 4 branches
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Branch:
    code: str
    city: str
    daily_kg_base: float


RETAIL_BRANCHES: tuple[Branch, ...] = (
    Branch("R-AMMAN", "Amman (Sweifieh)", 210.0),
    Branch("R-ZARQA", "Zarqa", 120.0),
    Branch("R-IRBID", "Irbid", 140.0),
    Branch("R-AQABA", "Aqaba", 80.0),
)
RETAIL_WEEKDAY_FACTOR = {0: 0.95, 1: 0.92, 2: 0.98, 3: 1.05, 4: 1.30, 5: 1.35, 6: 1.10}

# ---------------------------------------------------------------------------
# export destinations
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Destination:
    country: str
    city: str
    incoterm: str
    mode: str
    transit_days: int
    customs_hours: float
    freight_base: float             # per shipment
    orders_per_week: float
    distributors: tuple[str, ...]


DESTINATIONS: tuple[Destination, ...] = (
    Destination("SA", "Riyadh", "CIF", "road", 3, 20, 900, 5.0,
                ("Al-Tazaj Distribution", "Sweets House KSA")),
    Destination("AE", "Dubai", "CIF", "sea", 6, 24, 1400, 4.0,
                ("Gulf Gourmet FZE", "Dubai Sweets Trading")),
    Destination("US", "Detroit", "DDP", "air", 4, 30, 3200, 2.5,
                ("Levant Foods Inc", "Dearborn Mediterranean Market")),
    Destination("DE", "Berlin", "DAP", "air", 3, 26, 2600, 2.0,
                ("Orient Feinkost GmbH", "Baklava Berlin")),
)

CARTON_NET_KG = 8.0                 # target net weight per export carton
CARTON_TARE_KG = 1.4
CARTON_DIMS_CM = (40, 30, 25)
EXPORT_PROMISE_BUFFER_DAYS = 2      # promised = dispatch + transit + customs + buffer

# ---------------------------------------------------------------------------
# variants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Disruption:
    kind: str
    day_index: tuple[int, ...]
    magnitude: float = 1.0
    target: str = ""
    note: str = ""


VARIANTS: dict[str, dict] = {
    "baseline": {"label": "Baseline week", "disruptions": ()},
    "peak_export": {
        "label": "Trade-show spike — export orders +90% on days 2-3",
        "disruptions": (Disruption("export_spike", (1, 2), 0.90, note="Gulfood follow-up orders"),),
    },
    "raw_shortage": {
        "label": "Raw-material shortage — pistachio + ghee short on days 3-5",
        "disruptions": (Disruption("raw_shortage", (2, 3, 4), target="RM-PISTA,RM-GHEE",
                                   note="supplier crop shortfall"),),
    },
    "plant_downtime": {
        "label": "Plant downtime — heavy output loss on days 4-5 (oven failure)",
        "disruptions": (Disruption("plant_downtime", (3, 4), 0.65, note="tunnel oven breakdown"),),
    },
    "retail_promo": {
        "label": "Retail promotion — +35% maamoul demand on days 5-6",
        "disruptions": (Disruption("retail_promo", (4, 5), 0.35, target="FG-MAAMOUL",
                                   note="Eid gifting campaign"),),
    },
}


def variant(name: str) -> dict:
    if name not in VARIANTS:
        raise KeyError(f"unknown anabtawi scenario '{name}'; choose from {sorted(VARIANTS)}")
    return VARIANTS[name]
