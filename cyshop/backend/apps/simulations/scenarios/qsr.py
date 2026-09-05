"""
QSR ("McDonald's-style") scenario definition - data only, no engine logic.

Geography: 4 countries, 4 branches each (16 branches). One nominal reporting
currency keeps intercompany maths simple (see `REPORTING_CURRENCY`); per-country
demand, price index and VAT still differ.

The menu carries a real bill of materials: selling a `MenuItem` consumes its
`components` (raw goods, keyed by raw SKU) - that is what drives inventory
depletion, reorder points and supplier deliveries in the engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field

REPORTING_CURRENCY = "USD"

# ---------------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BranchSpec:
    code: str
    name: str
    city: str
    tier: str                # "flagship" | "standard" | "compact"
    opens_hour: int
    closes_hour: int         # 24 == closes midnight; 30 == closes 06:00 next day
    has_drive_thru: bool


@dataclass(frozen=True)
class CountrySpec:
    code: str                # ISO-3166-1 alpha-2
    name: str
    timezone: str
    vat_rate: str            # decimal string, e.g. "0.16"
    demand_index: float      # multiplies baseline footfall
    price_index: float       # multiplies menu prices
    branches: tuple[BranchSpec, ...]


def _branches(prefix: str, cities: list[str], drive_thru: tuple[bool, ...]) -> tuple[BranchSpec, ...]:
    tiers = ("flagship", "standard", "standard", "compact")
    hours = ((7, 24), (7, 24), (8, 24), (9, 23))
    out = []
    for i, city in enumerate(cities):
        out.append(
            BranchSpec(
                code=f"{prefix}-B{i + 1}",
                name=f"{city} ({prefix}-B{i + 1})",
                city=city,
                tier=tiers[i],
                opens_hour=hours[i][0],
                closes_hour=hours[i][1],
                has_drive_thru=drive_thru[i],
            )
        )
    return tuple(out)


COUNTRIES: tuple[CountrySpec, ...] = (
    CountrySpec(
        code="JO", name="Jordan", timezone="Asia/Amman", vat_rate="0.16",
        demand_index=1.00, price_index=1.00,
        branches=_branches("JO", ["Amman Abdali", "Amman Mecca St", "Zarqa", "Irbid"],
                           (True, True, True, False)),
    ),
    CountrySpec(
        code="SA", name="Saudi Arabia", timezone="Asia/Riyadh", vat_rate="0.15",
        demand_index=1.45, price_index=1.10,
        branches=_branches("SA", ["Riyadh Olaya", "Jeddah Tahlia", "Dammam", "Mecca"],
                           (True, True, True, True)),
    ),
    CountrySpec(
        code="AE", name="United Arab Emirates", timezone="Asia/Dubai", vat_rate="0.05",
        demand_index=1.20, price_index=1.25,
        branches=_branches("AE", ["Dubai Marina", "Abu Dhabi Corniche", "Sharjah", "Al Ain"],
                           (True, True, False, True)),
    ),
    CountrySpec(
        code="EG", name="Egypt", timezone="Africa/Cairo", vat_rate="0.14",
        demand_index=1.70, price_index=0.65,
        branches=_branches("EG", ["Cairo Nasr City", "Giza", "Alexandria", "New Cairo"],
                           (True, False, True, True)),
    ),
)

TIER_FOOTFALL = {"flagship": 1.35, "standard": 1.0, "compact": 0.7}

# ---------------------------------------------------------------------------
# Raw goods (inventory-tracked). unit_cost is in REPORTING_CURRENCY per unit.
# shelf_life_days drives spoilage; pack_size / lead_time_days drive purchasing.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawGood:
    sku: str
    name: str
    uom: str
    unit_cost: float
    shelf_life_days: int
    pack_size: int
    supplier_key: str


RAW_GOODS: tuple[RawGood, ...] = (
    RawGood("RM-BEEF", "Beef patty", "pc", 0.42, 4, 240, "meat"),
    RawGood("RM-CHKN", "Chicken breast fillet", "pc", 0.38, 4, 200, "meat"),
    RawGood("RM-FISH", "Fish fillet portion", "pc", 0.55, 5, 120, "meat"),
    RawGood("RM-SAUS", "Sausage patty", "pc", 0.30, 6, 200, "meat"),
    RawGood("RM-EGG", "Egg", "pc", 0.12, 14, 360, "meat"),
    RawGood("RM-BUN-REG", "Regular bun", "pc", 0.11, 3, 300, "bakery"),
    RawGood("RM-BUN-SES", "Sesame bun", "pc", 0.13, 3, 300, "bakery"),
    RawGood("RM-MUFFIN", "English muffin", "pc", 0.14, 4, 240, "bakery"),
    RawGood("RM-CHEESE", "Cheese slice", "pc", 0.09, 20, 500, "beverage"),
    RawGood("RM-LETT", "Shredded lettuce", "kg", 1.90, 3, 10, "produce"),
    RawGood("RM-TOM", "Tomato", "kg", 1.40, 5, 12, "produce"),
    RawGood("RM-ONION", "Onion", "kg", 0.80, 14, 20, "produce"),
    RawGood("RM-PICKLE", "Pickle slices", "kg", 2.10, 60, 8, "produce"),
    RawGood("RM-POTATO", "Fries-cut potato", "kg", 0.70, 12, 25, "produce"),
    RawGood("RM-OIL", "Frying oil", "l", 1.30, 30, 20, "supplies"),
    RawGood("RM-COLA", "Cola syrup", "l", 2.40, 120, 10, "beverage"),
    RawGood("RM-OJ", "Orange juice", "l", 1.60, 20, 12, "beverage"),
    RawGood("RM-COFFEE", "Coffee beans", "kg", 7.50, 180, 5, "beverage"),
    RawGood("RM-MILK", "Milk", "l", 0.90, 10, 12, "beverage"),
    RawGood("RM-HASH", "Hash brown", "pc", 0.16, 60, 300, "supplies"),
    RawGood("RM-CUP", "Paper cup + lid", "pc", 0.05, 720, 1000, "supplies"),
    RawGood("RM-BOX", "Carton / clamshell", "pc", 0.06, 720, 1000, "supplies"),
    RawGood("RM-NAPKIN", "Napkin + tray liner", "pc", 0.01, 720, 5000, "supplies"),
    RawGood("RM-KETCHUP", "Ketchup sachet", "pc", 0.02, 365, 4000, "supplies"),
    RawGood("RM-SALT", "Fry salt sachet", "pc", 0.005, 365, 5000, "supplies"),
)
RAW_BY_SKU = {r.sku: r for r in RAW_GOODS}

# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SupplierSpec:
    key: str
    name: str
    lead_time_days: int
    delivery_weekdays: tuple[int, ...]   # 0=Mon .. 6=Sun
    reliability: float                   # P(delivery arrives on time & full)


SUPPLIERS: tuple[SupplierSpec, ...] = (
    SupplierSpec("meat", "Regional Meat & Poultry Co", 2, (0, 2, 4), 0.96),
    SupplierSpec("bakery", "Golden Crust Bakery", 1, (0, 1, 2, 3, 4, 5), 0.98),
    SupplierSpec("produce", "FreshField Produce", 1, (0, 1, 2, 3, 4, 5, 6), 0.93),
    SupplierSpec("beverage", "Gulf Beverage Distributors", 3, (1, 4), 0.95),
    SupplierSpec("supplies", "PackRight Restaurant Supplies", 5, (2,), 0.97),
)
SUPPLIER_BY_KEY = {s.key: s for s in SUPPLIERS}

# ---------------------------------------------------------------------------
# Menu (sellable). price is REPORTING_CURRENCY before per-country price_index.
# components: {raw_sku: qty_per_unit_sold}
# dayparts: which dayparts the item is sold in (None == all)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MenuItem:
    code: str
    name: str
    category: str
    price: float
    components: dict[str, float]
    dayparts: tuple[str, ...] | None = None
    popularity: float = 1.0
    is_bundle: bool = False


_ALL_DAY = None
_BREAKFAST = ("BREAKFAST",)

MENU: tuple[MenuItem, ...] = (
    MenuItem("MNU-BIGMAC", "Big Mac", "Burgers", 4.20,
             {"RM-BUN-SES": 1.5, "RM-BEEF": 2, "RM-CHEESE": 1, "RM-LETT": 0.03,
              "RM-ONION": 0.01, "RM-PICKLE": 0.01, "RM-KETCHUP": 1, "RM-BOX": 1, "RM-NAPKIN": 1},
             popularity=1.6),
    MenuItem("MNU-QP", "Quarter Pounder with Cheese", "Burgers", 4.60,
             {"RM-BUN-SES": 1, "RM-BEEF": 1, "RM-CHEESE": 2, "RM-ONION": 0.01,
              "RM-PICKLE": 0.01, "RM-KETCHUP": 1, "RM-BOX": 1, "RM-NAPKIN": 1},
             popularity=1.1),
    MenuItem("MNU-MCCHKN", "McChicken", "Chicken", 3.60,
             {"RM-BUN-REG": 1, "RM-CHKN": 1, "RM-LETT": 0.03, "RM-KETCHUP": 1,
              "RM-BOX": 1, "RM-NAPKIN": 1},
             popularity=1.4),
    MenuItem("MNU-FOF", "Filet-O-Fish", "Fish", 3.90,
             {"RM-BUN-REG": 1, "RM-FISH": 1, "RM-CHEESE": 0.5, "RM-BOX": 1, "RM-NAPKIN": 1},
             popularity=0.6),
    MenuItem("MNU-NUG6", "6pc Chicken McNuggets", "Chicken", 3.30,
             {"RM-CHKN": 0.9, "RM-OIL": 0.03, "RM-BOX": 1, "RM-KETCHUP": 2, "RM-NAPKIN": 1},
             popularity=1.2),
    MenuItem("MNU-FRIES-M", "Fries (Medium)", "Sides", 1.80,
             {"RM-POTATO": 0.14, "RM-OIL": 0.02, "RM-SALT": 1, "RM-BOX": 1},
             popularity=1.9),
    MenuItem("MNU-FRIES-L", "Fries (Large)", "Sides", 2.20,
             {"RM-POTATO": 0.19, "RM-OIL": 0.025, "RM-SALT": 1, "RM-BOX": 1},
             popularity=1.0),
    MenuItem("MNU-COLA-M", "Coca-Cola (Medium)", "Drinks", 1.50,
             {"RM-COLA": 0.05, "RM-CUP": 1},
             popularity=1.8),
    MenuItem("MNU-OJ", "Orange Juice", "Drinks", 1.70,
             {"RM-OJ": 0.3, "RM-CUP": 1},
             popularity=0.5),
    MenuItem("MNU-COFFEE", "Coffee", "Drinks", 1.60,
             {"RM-COFFEE": 0.018, "RM-MILK": 0.05, "RM-CUP": 1},
             popularity=0.9),
    MenuItem("MNU-MCMUFFIN", "Egg & Sausage McMuffin", "Breakfast", 3.10,
             {"RM-MUFFIN": 1, "RM-EGG": 1, "RM-SAUS": 1, "RM-CHEESE": 1, "RM-BOX": 1, "RM-NAPKIN": 1},
             dayparts=_BREAKFAST, popularity=1.3),
    MenuItem("MNU-HASH", "Hash Browns", "Breakfast", 1.40,
             {"RM-HASH": 1, "RM-OIL": 0.01, "RM-BOX": 1},
             dayparts=_BREAKFAST, popularity=1.1),
    MenuItem("MNU-BIGMAC-MEAL", "Big Mac Meal", "Meals", 6.90,
             {"RM-BUN-SES": 1.5, "RM-BEEF": 2, "RM-CHEESE": 1, "RM-LETT": 0.03, "RM-ONION": 0.01,
              "RM-PICKLE": 0.01, "RM-KETCHUP": 1, "RM-POTATO": 0.14, "RM-OIL": 0.02, "RM-SALT": 1,
              "RM-COLA": 0.05, "RM-CUP": 1, "RM-BOX": 2, "RM-NAPKIN": 2},
             popularity=1.7, is_bundle=True),
    MenuItem("MNU-HAPPY", "Happy Meal", "Meals", 4.10,
             {"RM-BUN-REG": 1, "RM-CHKN": 0.6, "RM-POTATO": 0.08, "RM-OIL": 0.01, "RM-SALT": 1,
              "RM-OJ": 0.2, "RM-CUP": 1, "RM-BOX": 2, "RM-NAPKIN": 1},
             popularity=0.9, is_bundle=True),
)
MENU_BY_CODE = {m.code: m for m in MENU}

# ---------------------------------------------------------------------------
# Staffing template (per branch, scaled by tier footfall). Roles map to POS
# behaviour: cashiers open PosSessions; kitchen size scales prep throughput.
# ---------------------------------------------------------------------------

STAFF_TEMPLATE = {
    "Branch Manager": {"count": 1, "monthly_salary": 1800, "kind": "salaried"},
    "Shift Manager": {"count": 2, "monthly_salary": 1200, "kind": "salaried"},
    "Cashier": {"count": 5, "monthly_salary": 720, "kind": "hourly"},
    "Kitchen Crew": {"count": 6, "monthly_salary": 700, "kind": "hourly"},
    "Drive-Thru Crew": {"count": 3, "monthly_salary": 720, "kind": "hourly"},
    "Cleaner": {"count": 2, "monthly_salary": 620, "kind": "hourly"},
    "Maintenance Tech": {"count": 1, "monthly_salary": 950, "kind": "hourly"},
}

# ---------------------------------------------------------------------------
# Demand shape
# ---------------------------------------------------------------------------

# Baseline paid transactions per day for a standard-tier branch, before country
# demand_index and tier footfall multipliers.
BASELINE_ORDERS_PER_DAY = 520

WEEKDAY_FACTOR = {0: 0.92, 1: 0.90, 2: 0.95, 3: 1.00, 4: 1.18, 5: 1.30, 6: 1.15}

# Hourly weights (local hour -> share). Sums are normalised by the engine over
# each branch's open hours.
HOURLY_WEIGHTS = {
    6: 0.5, 7: 2.2, 8: 3.4, 9: 2.6, 10: 1.6, 11: 2.4,
    12: 6.2, 13: 6.8, 14: 4.1, 15: 2.6, 16: 2.4, 17: 3.2,
    18: 5.4, 19: 6.0, 20: 4.8, 21: 3.1, 22: 2.0, 23: 1.2, 0: 0.6, 1: 0.3,
}

DAYPART_BY_HOUR = {
    **{h: "BREAKFAST" for h in (6, 7, 8, 9, 10)},
    **{h: "LUNCH" for h in (11, 12, 13, 14)},
    **{h: "AFTERNOON" for h in (15, 16, 17)},
    **{h: "DINNER" for h in (18, 19, 20, 21)},
    **{h: "LATE_NIGHT" for h in (22, 23, 0, 1, 2, 3, 4, 5)},
}

CHANNEL_MIX = {"POS": 0.40, "KIOSK": 0.24, "DRIVE_THRU": 0.26, "ONLINE": 0.10}
CHANNEL_MIX_NO_DT = {"POS": 0.60, "KIOSK": 0.30, "ONLINE": 0.10}

# Target handover time (seconds) by channel - used for the on-time service level.
SERVICE_TARGET_SECONDS = {"DRIVE_THRU": 240, "POS": 300, "KIOSK": 330, "ONLINE": 420}

# Base prep seconds per menu item, before kitchen-load stretch.
BASE_PREP_SECONDS = {
    "Burgers": 55, "Chicken": 60, "Fish": 70, "Sides": 40, "Drinks": 15,
    "Breakfast": 50, "Meals": 80,
}

AVG_BASKET_LINES = 2.4          # Poisson-ish lambda for lines per order
SPOILAGE_RATE = {               # fraction of that day's usage additionally wasted
    3: 0.020, 4: 0.018, 5: 0.015, 6: 0.010,
}                               # keyed by shelf_life_days bucket; default below
DEFAULT_SPOILAGE = 0.004
OPENING_STOCK_DAYS = 5.0        # days of cover seeded as opening balance
REORDER_POINT_DAYS = 3.0
REORDER_UP_TO_DAYS = 7.0

# ---------------------------------------------------------------------------
# Scenario variants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Disruption:
    kind: str                       # see engine handling
    day_index: tuple[int, ...]      # which sim days (0-based)
    branches: tuple[str, ...] = ()  # branch codes ("" == all)
    countries: tuple[str, ...] = ()
    raw_skus: tuple[str, ...] = ()
    magnitude: float = 1.0
    note: str = ""


VARIANTS: dict[str, dict] = {
    "baseline": {
        "label": "Baseline week",
        "disruptions": (),
    },
    "promo_week": {
        "label": "Promotion week - daily lunch deal on the Big Mac Meal",
        "promo": {"code": "MNU-BIGMAC-MEAL", "discount": 0.25,
                  "dayparts": ("LUNCH",), "demand_uplift": 0.22},
        "disruptions": (),
    },
    "supply_disruption": {
        "label": "Supplier delay - fries potato + buns short at two branches, days 3-4",
        "disruptions": (
            Disruption("stockout", (2, 3), branches=("JO-B2", "SA-B3"),
                       raw_skus=("RM-POTATO", "RM-BUN-SES", "RM-BUN-REG"),
                       note="FreshField/Golden Crust missed delivery window"),
        ),
    },
    "staffing_shortage": {
        "label": "Absenteeism - one branch loses 40% of kitchen crew, days 5-6",
        "disruptions": (
            Disruption("kitchen_shortage", (4, 5), branches=("EG-B1",),
                       magnitude=0.40, note="flu outbreak among kitchen crew"),
        ),
    },
    "import_delay": {
        "label": "Customs hold - cola syrup stuck at UAE port, day 2",
        "disruptions": (
            Disruption("stockout", (1,), countries=("AE",), raw_skus=("RM-COLA",),
                       note="import/duty inspection delay"),
        ),
    },
}


def variant(name: str) -> dict:
    if name not in VARIANTS:
        raise KeyError(f"unknown QSR scenario variant '{name}'; choose from {sorted(VARIANTS)}")
    return VARIANTS[name]
