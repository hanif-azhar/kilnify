"""Emission factor library endpoints.

The JSON-backed library is read-only. User-added (custom) factors live in the
database and are fully editable — they are merged into the library listing and
can be used as emission factors in Data Entry.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CustomFactor
from ..schemas import CustomFactorCreate, CustomFactorOut
from ..services import factor_loader

router = APIRouter(prefix="/api/factors", tags=["factors"])


def _custom_to_record(m: CustomFactor) -> dict:
    """Render a custom factor in the same shape as built-in library records."""
    facilities = [t for t in (m.applicable_facility_types or "").split(",") if t]
    return {
        "id": m.id,
        "category": m.category,
        "sub_category": m.sub_category,
        "factor_value": m.factor_value,
        "unit": m.unit,
        "scope": m.scope,
        "source": m.source or "User-defined",
        "year": m.year,
        "applicable_facility_types": facilities,
        "notes": m.notes,
        "editable": True,
    }


def _matches(rec: dict, category, search, facility_type) -> bool:
    if category and rec["category"] != category:
        return False
    if facility_type:
        facs = rec.get("applicable_facility_types") or []
        # Empty facility list on a custom factor means "all facilities".
        if facs and facility_type not in facs:
            return False
    if search:
        needle = search.lower()
        haystack = " ".join(
            str(rec.get(k) or "") for k in ("category", "sub_category", "source")
        ).lower()
        if needle not in haystack:
            return False
    return True


@router.get("/")
def list_factors(
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    facility_type: Optional[str] = Query(default=None),
    company_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Built-in factors plus matching custom factors (global + this company's)."""
    results = factor_loader.query_factors(
        category=category, search=search, facility_type=facility_type
    )

    q = db.query(CustomFactor)
    if company_id:
        q = q.filter(
            (CustomFactor.company_id == company_id) | (CustomFactor.company_id.is_(None))
        )
    custom = [_custom_to_record(m) for m in q.all()]
    custom = [r for r in custom if _matches(r, category, search, facility_type)]

    return results + custom


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    builtin = set(factor_loader.list_categories())
    custom = {c.category for c in db.query(CustomFactor.category).distinct()}
    return sorted(builtin | custom)


@router.get("/raw")
def raw_factors():
    return factor_loader.load_all_raw()


# ----------------------------- Custom factors -----------------------------
@router.get("/custom", response_model=List[CustomFactorOut])
def list_custom_factors(
    company_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(CustomFactor)
    if company_id:
        q = q.filter(
            (CustomFactor.company_id == company_id) | (CustomFactor.company_id.is_(None))
        )
    return [CustomFactorOut.from_orm_model(m) for m in q.order_by(CustomFactor.created_at.desc()).all()]


@router.post("/custom", response_model=CustomFactorOut, status_code=201)
def create_custom_factor(payload: CustomFactorCreate, db: Session = Depends(get_db)):
    factor = CustomFactor(
        company_id=payload.company_id,
        scope=payload.scope.value if payload.scope else None,
        category=payload.category,
        sub_category=payload.sub_category,
        factor_value=payload.factor_value,
        unit=payload.unit,
        activity_unit=payload.activity_unit,
        source=payload.source,
        year=payload.year,
        applicable_facility_types=",".join(payload.applicable_facility_types or []),
        notes=payload.notes,
    )
    db.add(factor)
    db.commit()
    db.refresh(factor)
    return CustomFactorOut.from_orm_model(factor)


@router.put("/custom/{factor_id}", response_model=CustomFactorOut)
def update_custom_factor(factor_id: str, payload: CustomFactorCreate, db: Session = Depends(get_db)):
    factor = db.get(CustomFactor, factor_id)
    if not factor:
        raise HTTPException(status_code=404, detail="Custom factor not found")
    factor.company_id = payload.company_id
    factor.scope = payload.scope.value if payload.scope else None
    factor.category = payload.category
    factor.sub_category = payload.sub_category
    factor.factor_value = payload.factor_value
    factor.unit = payload.unit
    factor.activity_unit = payload.activity_unit
    factor.source = payload.source
    factor.year = payload.year
    factor.applicable_facility_types = ",".join(payload.applicable_facility_types or [])
    factor.notes = payload.notes
    db.commit()
    db.refresh(factor)
    return CustomFactorOut.from_orm_model(factor)


@router.delete("/custom/{factor_id}", status_code=204)
def delete_custom_factor(factor_id: str, db: Session = Depends(get_db)):
    factor = db.get(CustomFactor, factor_id)
    if not factor:
        raise HTTPException(status_code=404, detail="Custom factor not found")
    db.delete(factor)
    db.commit()
