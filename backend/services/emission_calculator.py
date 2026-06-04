"""Core emission calculation engine for Kilnify.

All 9 modules follow: Emissions (kgCO2e) = Activity Data x Emission Factor.
Internal unit is kgCO2e; use kg_to_tonnes() for display in tCO2e.

Follows GHG Protocol Corporate Standard and WBCSD CSI Cement CO2 Protocol.
"""

# Stoichiometric constants for clinker calcination (IPCC 2006 Vol.3 Ch.2).
CAO_STOICH = 0.785          # kg CO2 implied per % CaO (per the GUIDELINES Method B formula)
MGO_STOICH = 1.092          # kg CO2 implied per % MgO
CO2_CAO_MW_RATIO = 44 / 56  # molecular weight ratio CO2/CaO

# Default emission factors (commented with source + year).
DEFAULT_CLINKER_EF = 525.0          # kgCO2/tonne clinker — WBCSD CSI 2022 / GNR global average
DEFAULT_CLINKER_UPSTREAM_EF = 842.0  # kgCO2e/tonne clinker — GNR 2022 (process + combustion)
DIESEL_EF_PER_LITER = 2.68          # kgCO2e/liter — DEFRA 2024
PETROL_EF_PER_LITER = 2.31          # kgCO2e/liter — DEFRA 2024

GRID_FACTORS = {  # kgCO2e/kWh — PLN RUPTL 2023 / IEA
    "java_bali": 0.850,
    "sumatra": 0.790,
    "kalimantan": 0.920,
    "national": 0.870,
    "diesel_genset": 0.700,
}


def calculate_emissions(activity_data: float, emission_factor: float) -> float:
    """General formula: Emissions (kgCO2e) = Activity Data x Emission Factor."""
    if activity_data < 0 or emission_factor < 0:
        raise ValueError("activity_data and emission_factor must be >= 0")
    return activity_data * emission_factor


# --------------------------- Unit conversion ---------------------------
def kg_to_tonnes(kg: float) -> float:
    """Convert kgCO2e to tCO2e for display."""
    return kg / 1000.0


def tonnes_to_kg(tonnes: float) -> float:
    return tonnes * 1000.0


# ----------- Module 1: Clinker Process Emissions (Scope 1, Cement Plant) -----------
def clinker_process_method_a(clinker_tonnes: float, clinker_ef: float = DEFAULT_CLINKER_EF) -> float:
    """Method A (default): Clinker Produced (t) x Clinker EF (kgCO2/t)."""
    return calculate_emissions(clinker_tonnes, clinker_ef)


def clinker_process_method_b(clinker_tonnes: float, cao_content_pct: float, mgo_content_pct: float = 0.0) -> float:
    """Method B (plant-specific): CaO/MgO stoichiometry.

    Emissions = Clinker(t) x [(CaO% x 0.785 + MgO% x 1.092) / 100 x (44/56)] x 1000 kg/t.
    Returns kgCO2.
    """
    if clinker_tonnes < 0 or cao_content_pct < 0 or mgo_content_pct < 0:
        raise ValueError("inputs must be >= 0")
    ef_per_tonne = ((cao_content_pct * CAO_STOICH + mgo_content_pct * MGO_STOICH) / 100.0) * CO2_CAO_MW_RATIO
    # ef_per_tonne is in tCO2 per tonne clinker; multiply by 1000 for kgCO2.
    return clinker_tonnes * ef_per_tonne * 1000.0


# ----------- Module 2: Kiln Fuel Combustion (Scope 1) -----------
def kiln_fuel_combustion(fuel_quantity: float, fuel_ef: float, biogenic_fraction: float = 0.0):
    """Fuel Consumption x Fuel EF. Returns (fossil_kgco2e, biogenic_kgco2e).

    For alternative fuels, only the fossil-derived fraction counts toward the inventory.
    biogenic_fraction is a value 0..1 of total emissions that is biogenic.
    """
    if not 0.0 <= biogenic_fraction <= 1.0:
        raise ValueError("biogenic_fraction must be between 0 and 1")
    total = calculate_emissions(fuel_quantity, fuel_ef)
    biogenic = total * biogenic_fraction
    fossil = total - biogenic
    return fossil, biogenic


# ----------- Module 3: Electricity (Scope 2) -----------
def electricity_emissions(kwh: float, grid_region: str = "national", custom_ef: float = None) -> float:
    """kWh x Grid EF. Defaults to the Indonesian regional grid factor."""
    ef = custom_ef if custom_ef is not None else GRID_FACTORS.get(grid_region, GRID_FACTORS["national"])
    return calculate_emissions(kwh, ef)


# ----------- Module 4: On-Site Mobile Equipment (Scope 1) -----------
def mobile_equipment_emissions(liters: float, fuel_type: str = "diesel") -> float:
    """Fuel (liters) x Fuel EF (kgCO2e/liter)."""
    ef = DIESEL_EF_PER_LITER if fuel_type == "diesel" else PETROL_EF_PER_LITER
    return calculate_emissions(liters, ef)


# ----------- Module 5: Purchased Clinker Upstream (Scope 3, Grinding Plant) -----------
def purchased_clinker_upstream(clinker_tonnes: float, upstream_ef: float = DEFAULT_CLINKER_UPSTREAM_EF) -> float:
    """Clinker Purchased (t) x Upstream EF. Override EF with supplier EPD if available."""
    return calculate_emissions(clinker_tonnes, upstream_ef)


# ----------- Module 6: Outbound Transport (Scope 3) -----------
def outbound_transport(tonnes_shipped: float, distance_km: float, mode_factor: float) -> float:
    """Tonnes x Distance (km) x Mode Factor (kgCO2e/tonne-km)."""
    if tonnes_shipped < 0 or distance_km < 0 or mode_factor < 0:
        raise ValueError("inputs must be >= 0")
    return tonnes_shipped * distance_km * mode_factor


# ----------- Module 7: Packaging Materials (Scope 3) -----------
def packaging_emissions(units: float, packaging_ef: float) -> float:
    """Packaging Units x Packaging Material EF (kgCO2e/unit)."""
    return calculate_emissions(units, packaging_ef)


# ----------- Module 8: Business Travel (Scope 3) -----------
def business_travel(distance_km: float, mode_factor: float) -> float:
    """Distance (km) x Mode Factor (kgCO2e/km/passenger)."""
    return calculate_emissions(distance_km, mode_factor)


# ----------- Module 9: Employee Commuting (Scope 3) -----------
def employee_commuting(employees: float, avg_distance_km_day: float, working_days: float, mode_factor: float) -> float:
    """Employees x Avg Distance/day x Working Days x Mode Factor x 2 (return trip)."""
    if min(employees, avg_distance_km_day, working_days, mode_factor) < 0:
        raise ValueError("inputs must be >= 0")
    return employees * avg_distance_km_day * working_days * mode_factor * 2


# --------------------------- Production metrics ---------------------------
def clinker_to_cement_ratio(clinker_used_tonnes: float, cement_produced_tonnes: float) -> float:
    """Clinker used / Cement produced. Returns 0 when cement is 0 to avoid divide-by-zero."""
    if cement_produced_tonnes <= 0:
        return 0.0
    return clinker_used_tonnes / cement_produced_tonnes
