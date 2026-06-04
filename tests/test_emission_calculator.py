"""Unit tests for the core calculation engine — all 9 modules."""
import pytest

from backend.services import emission_calculator as ec


def test_general_formula():
    assert ec.calculate_emissions(100, 2.5) == 250.0


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        ec.calculate_emissions(-1, 2)
    with pytest.raises(ValueError):
        ec.calculate_emissions(1, -2)


def test_unit_conversion():
    assert ec.kg_to_tonnes(1000) == 1.0
    assert ec.tonnes_to_kg(2) == 2000.0


# Module 1 — clinker process
def test_clinker_method_a_default():
    # 150,000 t x 525 kg/t = 78,750,000 kg
    assert ec.clinker_process_method_a(150000) == 78_750_000.0


def test_clinker_method_a_custom_ef():
    assert ec.clinker_process_method_a(1000, 510) == 510_000.0


def test_clinker_method_b_cao():
    # CaO 65%, MgO 0: (65*0.785)/100 * (44/56) = 0.401016... tCO2/t
    result = ec.clinker_process_method_b(1000, 65.0, 0.0)
    expected = 1000 * ((65 * 0.785) / 100) * (44 / 56) * 1000
    assert result == pytest.approx(expected)
    # Per-tonne value should be in a sane range (~400 kgCO2/t for CaO-only).
    assert 380 < result / 1000 < 450


def test_clinker_method_b_with_mgo():
    r_no_mg = ec.clinker_process_method_b(1000, 65.0, 0.0)
    r_with_mg = ec.clinker_process_method_b(1000, 65.0, 2.0)
    assert r_with_mg > r_no_mg


# Module 2 — kiln fuel + biogenic separation
def test_kiln_fuel_no_biogenic():
    fossil, biogenic = ec.kiln_fuel_combustion(100, 2540)
    assert fossil == 254_000.0
    assert biogenic == 0.0


def test_kiln_fuel_biogenic_fraction():
    fossil, biogenic = ec.kiln_fuel_combustion(100, 1000, biogenic_fraction=0.4)
    assert fossil == pytest.approx(60_000.0)
    assert biogenic == pytest.approx(40_000.0)


def test_kiln_fuel_invalid_fraction():
    with pytest.raises(ValueError):
        ec.kiln_fuel_combustion(100, 1000, biogenic_fraction=1.5)


# Module 3 — electricity
def test_electricity_regions():
    assert ec.electricity_emissions(1000, "java_bali") == 850.0
    assert ec.electricity_emissions(1000, "national") == 870.0
    assert ec.electricity_emissions(1000, "kalimantan") == 920.0


def test_electricity_custom_ef():
    assert ec.electricity_emissions(1000, custom_ef=0.5) == 500.0


def test_electricity_unknown_region_defaults_national():
    assert ec.electricity_emissions(1000, "atlantis") == 870.0


# Module 4 — mobile equipment
def test_mobile_diesel_petrol():
    assert ec.mobile_equipment_emissions(100, "diesel") == 268.0
    assert ec.mobile_equipment_emissions(100, "petrol") == 231.0


# Module 5 — purchased clinker upstream
def test_purchased_clinker_default():
    assert ec.purchased_clinker_upstream(80000) == 80000 * 842.0


# Module 6 — outbound transport
def test_outbound_transport():
    assert ec.outbound_transport(1000, 500, 0.062) == pytest.approx(31_000.0)


# Module 7 — packaging
def test_packaging():
    assert ec.packaging_emissions(10000, 0.55) == 5500.0


# Module 8 — business travel
def test_business_travel():
    assert ec.business_travel(1000, 0.195) == 195.0


# Module 9 — employee commuting (x2 return trip)
def test_employee_commuting():
    # 100 emp x 20 km x 22 days x 0.192 x 2 = 16,896
    assert ec.employee_commuting(100, 20, 22, 0.192) == pytest.approx(16_896.0)


def test_clinker_to_cement_ratio():
    assert ec.clinker_to_cement_ratio(150000, 185000) == pytest.approx(0.8108, abs=1e-3)
    assert ec.clinker_to_cement_ratio(100, 0) == 0.0
