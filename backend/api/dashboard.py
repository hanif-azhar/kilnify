"""Aggregated dashboard data.

With SCOPE3_ONLY enabled the dashboard is Scope 3-centric: it omits Scope 1/2
totals, cement/clinker intensity, and thermal-substitution (kiln-fuel) metrics,
which are all derived from Scope 1/2 data that is no longer collected.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..constants import SCOPE3_ONLY
from ..database import get_db
from ..models import EmissionEntry, ProductionData
from ..schemas import EmissionOut
from ..services import aggregator

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard(company_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    eq = db.query(EmissionEntry)
    pq = db.query(ProductionData)
    if company_id:
        eq = eq.filter(EmissionEntry.company_id == company_id)
        pq = pq.filter(ProductionData.company_id == company_id)

    entries = eq.all()
    production = pq.all()

    breakdown = aggregator.scope_breakdown(entries)
    recent = (
        sorted(entries, key=lambda e: e.created_at or e.period_start, reverse=True)[:10]
    )

    data = {
        "scope3_only": SCOPE3_ONLY,
        "total_tco2e": round(breakdown["scope3_tco2e"] if SCOPE3_ONLY else breakdown["total_tco2e"], 4),
        "scope3_tco2e": round(breakdown["scope3_tco2e"], 4),
        "biogenic_co2_tco2e": round(breakdown["biogenic_co2_tco2e"], 4),
        "monthly_trend": aggregator.monthly_trend(entries),
        "top_hotspots": aggregator.top_hotspots(entries),
        "scope3_by_category": aggregator.scope3_category_breakdown(entries),
        "recent_entries": [EmissionOut.model_validate(e).model_dump(mode="json") for e in recent],
        "data_quality_summary": aggregator.data_quality_summary(entries),
    }

    if not SCOPE3_ONLY:
        intensity = aggregator.intensity_metrics(entries, production)
        data.update(
            {
                "total_tco2e": round(breakdown["total_tco2e"], 4),
                "scope1_process_tco2e": round(breakdown["scope1_process_tco2e"], 4),
                "scope1_combustion_tco2e": round(breakdown["scope1_combustion_tco2e"], 4),
                "scope1_mobile_tco2e": round(breakdown["scope1_mobile_tco2e"], 4),
                "scope1_fugitive_tco2e": round(breakdown["scope1_fugitive_tco2e"], 4),
                "scope1_tco2e": round(breakdown["scope1_tco2e"], 4),
                "scope2_tco2e": round(breakdown["scope2_tco2e"], 4),
                "intensity_kgco2e_per_tonne_cement": intensity["intensity_kgco2e_per_tonne_cement"],
                "intensity_kgco2e_per_tonne_clinker": intensity["intensity_kgco2e_per_tonne_clinker"],
                "clinker_to_cement_ratio": intensity["clinker_to_cement_ratio"],
                "scope2_by_category": aggregator.emissions_by_category(entries, "2"),
                "alternative_fuel_metrics": aggregator.alternative_fuel_metrics(entries),
            }
        )

    return data
