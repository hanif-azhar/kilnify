"""SQLAlchemy ORM models for Kilnify.

Entities: Company (facility), ProductionData, EmissionEntry, Report.
All emission values are stored in kgCO2e internally; reports convert to tCO2e.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    # facility_type drives which emission categories are available across the app.
    facility_type = Column(String, nullable=False)  # cement_plant | grinding_plant | packing_plant
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    grid_region = Column(String, nullable=True, default="national")  # java_bali | sumatra | kalimantan | national
    reporting_year = Column(Integer, nullable=True)
    headcount = Column(Integer, nullable=True)
    annual_cement_capacity_tonnes = Column(Float, nullable=True)
    annual_clinker_capacity_tonnes = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    production = relationship("ProductionData", back_populates="company", cascade="all, delete-orphan")
    emissions = relationship("EmissionEntry", back_populates="company", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="company", cascade="all, delete-orphan")


class ProductionData(Base):
    __tablename__ = "production_data"

    id = Column(String, primary_key=True, default=_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    clinker_produced_tonnes = Column(Float, default=0.0)
    clinker_purchased_tonnes = Column(Float, default=0.0)
    cement_produced_tonnes = Column(Float, default=0.0)
    cement_dispatched_tonnes = Column(Float, default=0.0)
    clinker_to_cement_ratio = Column(Float, nullable=True)  # auto-calculated
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="production")


class EmissionEntry(Base):
    __tablename__ = "emission_entries"

    id = Column(String, primary_key=True, default=_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    scope = Column(String, nullable=False)  # "1" | "2" | "3"
    category = Column(String, nullable=False)
    sub_category = Column(String, nullable=True)
    activity_data = Column(Float, nullable=False)
    activity_unit = Column(String, nullable=False)
    emission_factor = Column(Float, nullable=False)
    emission_factor_unit = Column(String, nullable=True)
    emission_factor_source = Column(String, nullable=False)
    # Raw activity_data and emission_factor are stored separately for audit/recalculation.
    total_emissions_kgco2e = Column(Float, nullable=False)
    biogenic_co2_kgco2 = Column(Float, default=0.0)  # excluded from totals, disclosed separately
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    plant_area = Column(String, nullable=True)
    data_quality = Column(String, nullable=False)  # measured | estimated | calculated
    calculation_method = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="emissions")


class CustomFactor(Base):
    """User-added emission factor. Merged with the read-only JSON library.

    Built-in JSON factors stay read-only; these are fully editable/deletable so
    users can add plant-specific, supplier-certified, or updated factors. A null
    company_id makes the factor global (available to every facility).
    """
    __tablename__ = "custom_factors"

    id = Column(String, primary_key=True, default=_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=True)  # null = global
    scope = Column(String, nullable=True)  # "1" | "2" | "3" — for use in Data Entry
    category = Column(String, nullable=False)
    sub_category = Column(String, nullable=True)
    factor_value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    activity_unit = Column(String, nullable=True)  # so it can drive Data Entry
    source = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    # Comma-separated facility-type values; empty/null means all facilities.
    applicable_facility_types = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=_uuid)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    report_period = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    # Scope 1 broken down by sub-type (process / combustion / mobile / fugitive), all in tCO2e.
    total_scope1_process = Column(Float, default=0.0)
    total_scope1_combustion = Column(Float, default=0.0)
    total_scope1_mobile = Column(Float, default=0.0)
    total_scope1_fugitive = Column(Float, default=0.0)
    total_scope1 = Column(Float, default=0.0)
    total_scope2_lb = Column(Float, default=0.0)  # location-based
    total_scope2_mb = Column(Float, default=0.0)  # market-based
    total_scope3 = Column(Float, default=0.0)
    total_emissions = Column(Float, default=0.0)
    biogenic_co2_total = Column(Float, default=0.0)  # disclosed separately, excluded from total
    specific_emissions_per_tonne_cement = Column(Float, nullable=True)
    specific_emissions_per_tonne_clinker = Column(Float, nullable=True)
    clinker_to_cement_ratio = Column(Float, nullable=True)
    unit = Column(String, default="tCO2e")
    status = Column(String, default="draft")  # draft | final
    generated_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="reports")
