"""Aggregation helpers shared by the dashboard and report endpoints.

All emission entry totals are stored in kgCO2e; helpers return tCO2e where noted.
"""
from collections import defaultdict
from typing import List

from ..constants import (
    SCOPE1_COMBUSTION_CATEGORIES,
    SCOPE3_CATEGORY_LABELS,
    classify_scope1_subtype,
    classify_scope3_category,
)
from ..models import EmissionEntry, ProductionData
from ..services.emission_calculator import (
    clinker_to_cement_ratio,
    fuel_thermal_energy_gj,
    is_alternative_fuel,
    kg_to_tonnes,
    thermal_substitution_rate,
)


def scope_breakdown(entries: List[EmissionEntry]) -> dict:
    """Return tCO2e totals by scope, with Scope 1 split by sub-type."""
    s1 = {"process": 0.0, "combustion": 0.0, "mobile": 0.0, "fugitive": 0.0}
    s2 = 0.0
    s3 = 0.0
    biogenic = 0.0

    for e in entries:
        biogenic += e.biogenic_co2_kgco2 or 0.0
        if e.scope == "1":
            s1[classify_scope1_subtype(e.category)] += e.total_emissions_kgco2e
        elif e.scope == "2":
            s2 += e.total_emissions_kgco2e
        elif e.scope == "3":
            s3 += e.total_emissions_kgco2e

    scope1_total = sum(s1.values())
    return {
        "scope1_process_tco2e": kg_to_tonnes(s1["process"]),
        "scope1_combustion_tco2e": kg_to_tonnes(s1["combustion"]),
        "scope1_mobile_tco2e": kg_to_tonnes(s1["mobile"]),
        "scope1_fugitive_tco2e": kg_to_tonnes(s1["fugitive"]),
        "scope1_tco2e": kg_to_tonnes(scope1_total),
        "scope2_tco2e": kg_to_tonnes(s2),
        "scope3_tco2e": kg_to_tonnes(s3),
        "biogenic_co2_tco2e": kg_to_tonnes(biogenic),
        "total_tco2e": kg_to_tonnes(scope1_total + s2 + s3),
    }


def scope3_category_breakdown(entries: List[EmissionEntry]) -> List[dict]:
    """Scope 3 emissions grouped by GHG Protocol category number (1-15), in tCO2e."""
    by_cat = defaultdict(float)
    for e in entries:
        if e.scope == "3":
            by_cat[classify_scope3_category(e.category)] += e.total_emissions_kgco2e
    total = sum(by_cat.values())
    out = []
    for num in sorted(by_cat):
        val = by_cat[num]
        out.append(
            {
                "ghg_category": num,
                "label": SCOPE3_CATEGORY_LABELS.get(num, f"Cat {num}"),
                "emissions_tco2e": round(kg_to_tonnes(val), 4),
                "percentage": round((val / total * 100) if total > 0 else 0.0, 2),
            }
        )
    return out


def emissions_by_category(entries: List[EmissionEntry], scope: str) -> List[dict]:
    """Per-category tCO2e breakdown within a single scope, ranked descending."""
    by_cat = defaultdict(float)
    for e in entries:
        if e.scope == scope:
            by_cat[e.category] += e.total_emissions_kgco2e
    total = sum(by_cat.values())
    ranked = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {
            "category": cat,
            "emissions_tco2e": round(kg_to_tonnes(val), 4),
            "percentage": round((val / total * 100) if total > 0 else 0.0, 2),
        }
        for cat, val in ranked
    ]


def alternative_fuel_metrics(entries: List[EmissionEntry]) -> dict:
    """Thermal Substitution Rate (TSR) and alternative-fuel share from kiln fuels.

    TSR is energy-based (GJ from alternative fuels / total kiln-fuel GJ). The
    biogenic share is derived from each fuel entry's biogenic_co2 disclosure.
    """
    total_gj = 0.0
    alt_gj = 0.0
    fossil_fuel_kg = 0.0
    biogenic_kg = 0.0
    for e in entries:
        if e.category not in SCOPE1_COMBUSTION_CATEGORIES:
            continue
        gj = fuel_thermal_energy_gj(e.sub_category, e.activity_data or 0.0)
        total_gj += gj
        if is_alternative_fuel(e.sub_category):
            alt_gj += gj
        fossil_fuel_kg += e.total_emissions_kgco2e or 0.0
        biogenic_kg += e.biogenic_co2_kgco2 or 0.0

    tsr = thermal_substitution_rate(alt_gj, total_gj)
    gross_kg = fossil_fuel_kg + biogenic_kg
    return {
        "total_thermal_gj": round(total_gj, 2),
        "alternative_thermal_gj": round(alt_gj, 2),
        "thermal_substitution_rate_pct": round(tsr * 100, 2),
        "biogenic_share_pct": round((biogenic_kg / gross_kg * 100) if gross_kg > 0 else 0.0, 2),
    }


def top_hotspots(entries: List[EmissionEntry], limit: int = 5) -> List[dict]:
    """Top emitting categories by tCO2e with percentage contribution."""
    by_cat = defaultdict(float)
    total = 0.0
    for e in entries:
        by_cat[e.category] += e.total_emissions_kgco2e
        total += e.total_emissions_kgco2e
    ranked = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [
        {
            "category": cat,
            "emissions_tco2e": round(kg_to_tonnes(val), 4),
            "percentage": round((val / total * 100) if total > 0 else 0.0, 2),
        }
        for cat, val in ranked
    ]


def data_quality_summary(entries: List[EmissionEntry]) -> dict:
    summary = {"measured": 0, "estimated": 0, "calculated": 0}
    for e in entries:
        if e.data_quality in summary:
            summary[e.data_quality] += 1
    return summary


def monthly_trend(entries: List[EmissionEntry]) -> List[dict]:
    """Group emissions by YYYY-MM (using period_start) and scope, in tCO2e."""
    buckets = defaultdict(lambda: {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0})
    for e in entries:
        month = e.period_start.strftime("%Y-%m")
        buckets[month][f"scope{e.scope}"] += e.total_emissions_kgco2e
    out = []
    for month in sorted(buckets):
        b = buckets[month]
        s1, s2, s3 = kg_to_tonnes(b["scope1"]), kg_to_tonnes(b["scope2"]), kg_to_tonnes(b["scope3"])
        out.append(
            {
                "month": month,
                "scope1": round(s1, 4),
                "scope2": round(s2, 4),
                "scope3": round(s3, 4),
                "total": round(s1 + s2 + s3, 4),
            }
        )
    return out


def production_metrics(production: List[ProductionData]) -> dict:
    """Aggregate production volumes and derive intensity ratios."""
    clinker_produced = sum(p.clinker_produced_tonnes or 0.0 for p in production)
    clinker_purchased = sum(p.clinker_purchased_tonnes or 0.0 for p in production)
    cement_produced = sum(p.cement_produced_tonnes or 0.0 for p in production)
    clinker_used = clinker_produced + clinker_purchased
    return {
        "clinker_produced_tonnes": clinker_produced,
        "clinker_purchased_tonnes": clinker_purchased,
        "cement_produced_tonnes": cement_produced,
        "clinker_used_tonnes": clinker_used,
        "clinker_to_cement_ratio": round(clinker_to_cement_ratio(clinker_used, cement_produced), 4),
    }


def intensity_metrics(entries: List[EmissionEntry], production: List[ProductionData]) -> dict:
    """Specific emissions per tonne cement / clinker and clinker-to-cement ratio."""
    pm = production_metrics(production)
    breakdown = scope_breakdown(entries)

    # Net CO2 per tonne cement uses Scope 1 + 2 (kgCO2e) per GNR convention.
    scope12_kg = (breakdown["scope1_tco2e"] + breakdown["scope2_tco2e"]) * 1000.0
    process_kg = breakdown["scope1_process_tco2e"] * 1000.0

    per_cement = scope12_kg / pm["cement_produced_tonnes"] if pm["cement_produced_tonnes"] > 0 else None
    per_clinker = process_kg / pm["clinker_produced_tonnes"] if pm["clinker_produced_tonnes"] > 0 else None

    return {
        "intensity_kgco2e_per_tonne_cement": round(per_cement, 2) if per_cement is not None else None,
        "intensity_kgco2e_per_tonne_clinker": round(per_clinker, 2) if per_clinker is not None else None,
        "clinker_to_cement_ratio": pm["clinker_to_cement_ratio"],
    }
