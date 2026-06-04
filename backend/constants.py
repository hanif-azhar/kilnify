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
