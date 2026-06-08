"""Enums and shared constants — never use free-text strings for these in logic."""
from enum import Enum


class FacilityType(str, Enum):
    CEMENT_PLANT = "cement_plant"
    GRINDING_PLANT = "grinding_plant"
    PACKING_PLANT = "packing_plant"


class Scope(str, Enum):
    SCOPE_1 = "1"
    SCOPE_2 = "2"
    SCOPE_3 = "3"


class DataQuality(str, Enum):
    MEASURED = "measured"
    ESTIMATED = "estimated"
    CALCULATED = "calculated"


class GridRegion(str, Enum):
    JAVA_BALI = "java_bali"
    SUMATRA = "sumatra"
    KALIMANTAN = "kalimantan"
    NATIONAL = "national"


# Scope 1 sub-type classification by category — drives report sub-type breakdown.
# Categories not listed default to "combustion" within Scope 1.
SCOPE1_PROCESS_CATEGORIES = {"clinker_calcination", "kiln_bypass", "ckd"}
SCOPE1_COMBUSTION_CATEGORIES = {"kiln_fuel", "fuel_combustion", "dryer_fuel"}
SCOPE1_MOBILE_CATEGORIES = {"mobile_equipment", "on_site_mobile", "diesel_genset"}
SCOPE1_FUGITIVE_CATEGORIES = {"refrigerants", "fugitive"}

# Scope 3 categories mapped to GHG Protocol Corporate Value Chain (Scope 3) category
# numbers (1-15). Drives the Scope 3 category breakdown in dashboard and reports.
# Categories not listed default to GHG category 1 (purchased goods) within Scope 3.
SCOPE3_CATEGORY_MAP = {
    # Cat 1 — Purchased goods and services
    "purchased_goods": 1,
    "purchased_clinker_upstream": 1,
    "packaging": 1,
    # Cat 2 — Capital goods
    "capital_goods": 2,
    # Cat 3 — Fuel- and energy-related activities (not in Scope 1 or 2)
    "fuel_energy_related": 3,
    # Cat 4 — Upstream transportation and distribution (inbound logistics)
    "upstream_transport": 4,
    # Cat 5 — Waste generated in operations
    "waste_generated": 5,
    # Cat 6 — Business travel
    "business_travel": 6,
    # Cat 7 — Employee commuting
    "employee_commuting": 7,
    # Cat 9 — Downstream transportation and distribution (outbound cement dispatch)
    "transport_outbound": 9,
    "downstream_transport": 9,
    # Cat 10 — Processing of sold products (clinker sold to third-party grinders)
    "processing_sold_products": 10,
    # Cat 11 — Use of sold products
    "use_sold_products": 11,
}

# Human-readable labels for each GHG Protocol Scope 3 category number.
SCOPE3_CATEGORY_LABELS = {
    1: "Cat 1 — Purchased goods & services",
    2: "Cat 2 — Capital goods",
    3: "Cat 3 — Fuel- & energy-related activities",
    4: "Cat 4 — Upstream transportation & distribution",
    5: "Cat 5 — Waste generated in operations",
    6: "Cat 6 — Business travel",
    7: "Cat 7 — Employee commuting",
    9: "Cat 9 — Downstream transportation & distribution",
    10: "Cat 10 — Processing of sold products",
    11: "Cat 11 — Use of sold products",
}

# Categories that may only be entered for specific facility types (facility-type gating).
# Process emissions (calcination) are exclusive to cement plants.
FACILITY_RESTRICTED_CATEGORIES = {
    "clinker_calcination": {FacilityType.CEMENT_PLANT.value},
    "kiln_bypass": {FacilityType.CEMENT_PLANT.value},
    "ckd": {FacilityType.CEMENT_PLANT.value},
    # Kiln/dryer fuel only for cement plants (kiln) and grinding plants (dryers).
    "kiln_fuel": {FacilityType.CEMENT_PLANT.value, FacilityType.GRINDING_PLANT.value},
    "dryer_fuel": {FacilityType.CEMENT_PLANT.value, FacilityType.GRINDING_PLANT.value},
    # Purchased clinker upstream is the dominant Scope 3 for grinding plants.
    "purchased_clinker_upstream": {FacilityType.GRINDING_PLANT.value},
    # Only integrated cement plants sell clinker for third-party processing.
    "processing_sold_products": {FacilityType.CEMENT_PLANT.value},
}


def classify_scope1_subtype(category: str) -> str:
    """Map an emission category to its Scope 1 sub-type."""
    if category in SCOPE1_PROCESS_CATEGORIES:
        return "process"
    if category in SCOPE1_MOBILE_CATEGORIES:
        return "mobile"
    if category in SCOPE1_FUGITIVE_CATEGORIES:
        return "fugitive"
    return "combustion"


def classify_scope3_category(category: str) -> int:
    """Map an emission category to its GHG Protocol Scope 3 category number (1-15)."""
    return SCOPE3_CATEGORY_MAP.get(category, 1)
