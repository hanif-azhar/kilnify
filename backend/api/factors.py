"""Read-only emission factor library endpoints."""
from typing import Optional

from fastapi import APIRouter, Query

from ..services import factor_loader

router = APIRouter(prefix="/api/factors", tags=["factors"])


@router.get("/")
def list_factors(
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    facility_type: Optional[str] = Query(default=None),
):
    return factor_loader.query_factors(category=category, search=search, facility_type=facility_type)


@router.get("/categories")
def list_categories():
    return factor_loader.list_categories()


@router.get("/raw")
def raw_factors():
    return factor_loader.load_all_raw()
