"""CRUD for emission entries.

On create: auto-calculates total emissions, enforces facility-type gating,
and warns (does not block) when an entry is an outlier (>3x historical average).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..constants import FACILITY_RESTRICTED_CATEGORIES
from ..database import get_db
from ..models import Company, EmissionEntry
from ..schemas import EmissionCreate, EmissionOut, orm_dict
from ..services.emission_calculator import calculate_emissions

router = APIRouter(prefix="/api/emissions", tags=["emissions"])

OUTLIER_MULTIPLIER = 3.0


def _check_facility_gating(category: str, facility_type: str) -> None:
    """Block categories not permitted for the company's facility type."""
    allowed = FACILITY_RESTRICTED_CATEGORIES.get(category)
    if allowed is not None and facility_type not in allowed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Category '{category}' is not available for facility type "
                f"'{facility_type}'. Allowed: {sorted(allowed)}"
            ),
        )


@router.get("/", response_model=list[EmissionOut])
def list_emissions(
    company_id: Optional[str] = Query(default=None),
    scope: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(EmissionEntry)
    if company_id:
        q = q.filter(EmissionEntry.company_id == company_id)
    if scope:
        q = q.filter(EmissionEntry.scope == scope)
    return q.order_by(EmissionEntry.created_at.desc()).all()


@router.post("/", response_model=EmissionOut, status_code=201)
def create_emission(payload: EmissionCreate, db: Session = Depends(get_db)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    _check_facility_gating(payload.category, company.facility_type)

    total = calculate_emissions(payload.activity_data, payload.emission_factor)

    # Outlier detection: warn if total exceeds 3x the historical average for
    # the same scope + category (warn, don't block).
    warning = None
    prior = (
        db.query(EmissionEntry)
        .filter(
            EmissionEntry.company_id == payload.company_id,
            EmissionEntry.scope == payload.scope.value,
            EmissionEntry.category == payload.category,
        )
        .all()
    )
    if prior:
        avg = sum(e.total_emissions_kgco2e for e in prior) / len(prior)
        if avg > 0 and total > OUTLIER_MULTIPLIER * avg:
            warning = (
                f"Outlier: {total:.0f} kgCO2e is more than {OUTLIER_MULTIPLIER:g}x the "
                f"historical average ({avg:.0f} kgCO2e) for {payload.scope.value}/{payload.category}."
            )

    entry = EmissionEntry(**orm_dict(payload), total_emissions_kgco2e=total)
    db.add(entry)
    db.commit()
    db.refresh(entry)

    out = EmissionOut.model_validate(entry)
    out.warning = warning
    return out


@router.get("/{entry_id}", response_model=EmissionOut)
def get_emission(entry_id: str, db: Session = Depends(get_db)):
    entry = db.get(EmissionEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Emission entry not found")
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_emission(entry_id: str, db: Session = Depends(get_db)):
    entry = db.get(EmissionEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Emission entry not found")
    db.delete(entry)
    db.commit()
