"""CRUD endpoints for production data (clinker / cement volumes).

Auto-calculates the clinker-to-cement ratio and enforces its 0.50-1.00 bound.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Company, ProductionData
from ..schemas import ProductionCreate, ProductionOut, orm_dict
from ..services.emission_calculator import clinker_to_cement_ratio

router = APIRouter(prefix="/api/production", tags=["production"])


@router.get("/", response_model=list[ProductionOut])
def list_production(company_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(ProductionData)
    if company_id:
        q = q.filter(ProductionData.company_id == company_id)
    return q.order_by(ProductionData.period_start.desc()).all()


@router.post("/", response_model=ProductionOut, status_code=201)
def create_production(payload: ProductionCreate, db: Session = Depends(get_db)):
    if not db.get(Company, payload.company_id):
        raise HTTPException(status_code=404, detail="Company not found")

    # Clinker used = produced (cement plant) + purchased (grinding plant).
    clinker_used = payload.clinker_produced_tonnes + payload.clinker_purchased_tonnes
    ratio = clinker_to_cement_ratio(clinker_used, payload.cement_produced_tonnes)

    # Validation rule: ratio must be between 0.50 and 1.00 when cement was produced.
    if payload.cement_produced_tonnes > 0 and ratio and not (0.50 <= ratio <= 1.00):
        raise HTTPException(
            status_code=422,
            detail=f"clinker_to_cement_ratio {ratio:.3f} out of bounds (must be 0.50-1.00)",
        )

    entry = ProductionData(**orm_dict(payload), clinker_to_cement_ratio=round(ratio, 4))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=ProductionOut)
def get_production(entry_id: str, db: Session = Depends(get_db)):
    entry = db.get(ProductionData, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Production entry not found")
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_production(entry_id: str, db: Session = Depends(get_db)):
    entry = db.get(ProductionData, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Production entry not found")
    db.delete(entry)
    db.commit()
