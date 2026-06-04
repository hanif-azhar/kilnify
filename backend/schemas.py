"""Pydantic v2 request/response schemas."""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .constants import DataQuality, FacilityType, GridRegion, Scope


def orm_dict(payload: BaseModel) -> dict:
    """Dump a schema to a dict suitable for an ORM model constructor.

    Keeps date/datetime objects intact (SQLite requires real date objects) while
    coercing Enum members to their underlying string value.
    """
    data = payload.model_dump()
    return {k: (v.value if isinstance(v, Enum) else v) for k, v in data.items()}


# ----------------------------- Company -----------------------------
class CompanyBase(BaseModel):
    name: str
    facility_type: FacilityType
    country: Optional[str] = None
    region: Optional[str] = None
    grid_region: GridRegion = GridRegion.NATIONAL
    reporting_year: Optional[int] = None
    headcount: Optional[int] = Field(default=None, ge=0)
    annual_cement_capacity_tonnes: Optional[float] = Field(default=None, ge=0)
    annual_clinker_capacity_tonnes: Optional[float] = Field(default=None, ge=0)


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: Optional[datetime] = None


# --------------------------- ProductionData ---------------------------
class ProductionBase(BaseModel):
    company_id: str
    period_start: date
    period_end: date
    clinker_produced_tonnes: float = Field(default=0.0, ge=0)
    clinker_purchased_tonnes: float = Field(default=0.0, ge=0)
    cement_produced_tonnes: float = Field(default=0.0, ge=0)
    cement_dispatched_tonnes: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _check_dates(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class ProductionCreate(ProductionBase):
    pass


class ProductionOut(ProductionBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    clinker_to_cement_ratio: Optional[float] = None
    created_at: Optional[datetime] = None


# --------------------------- EmissionEntry ---------------------------
class EmissionBase(BaseModel):
    company_id: str
    scope: Scope
    category: str
    sub_category: Optional[str] = None
    activity_data: float = Field(ge=0)
    activity_unit: str
    emission_factor: float = Field(ge=0)
    emission_factor_unit: Optional[str] = None
    emission_factor_source: str
    biogenic_co2_kgco2: float = Field(default=0.0, ge=0)
    period_start: date
    period_end: date
    plant_area: Optional[str] = None
    data_quality: DataQuality
    calculation_method: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _check_dates(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class EmissionCreate(EmissionBase):
    pass


class EmissionOut(EmissionBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    total_emissions_kgco2e: float
    created_at: Optional[datetime] = None
    # Populated by the API when an outlier is detected (>3x historical average).
    warning: Optional[str] = None


# ----------------------------- Report -----------------------------
class ReportGenerate(BaseModel):
    company_id: str
    report_period: str
    period_start: date
    period_end: date
    status: str = "draft"

    @model_validator(mode="after")
    def _check_dates(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    company_id: str
    report_period: str
    period_start: date
    period_end: date
    total_scope1_process: float
    total_scope1_combustion: float
    total_scope1_mobile: float
    total_scope1_fugitive: float
    total_scope1: float
    total_scope2_lb: float
    total_scope2_mb: float
    total_scope3: float
    total_emissions: float
    biogenic_co2_total: float
    specific_emissions_per_tonne_cement: Optional[float] = None
    specific_emissions_per_tonne_clinker: Optional[float] = None
    clinker_to_cement_ratio: Optional[float] = None
    unit: str
    status: str
    generated_at: Optional[datetime] = None


class HotspotOut(BaseModel):
    category: str
    emissions_tco2e: float
    percentage: float


class ReportDetailOut(ReportOut):
    company_name: str
    facility_type: str
    entries: List[EmissionOut]
    top_hotspots: List[HotspotOut]
    data_quality_summary: dict
    methodology_notes: List[str]
    disclaimer: str
