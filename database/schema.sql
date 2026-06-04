-- Kilnify database schema (raw SQL reference)
-- Dev: SQLite. Prod: PostgreSQL. The ORM (backend/models.py) is the source of truth;
-- this file documents the schema with constraints for direct DB setup.

CREATE TABLE IF NOT EXISTS companies (
    id                              TEXT PRIMARY KEY,
    name                            TEXT NOT NULL,
    facility_type                   TEXT NOT NULL
        CHECK (facility_type IN ('cement_plant', 'grinding_plant', 'packing_plant')),
    country                         TEXT,
    region                          TEXT,
    grid_region                     TEXT DEFAULT 'national'
        CHECK (grid_region IN ('java_bali', 'sumatra', 'kalimantan', 'national')),
    reporting_year                  INTEGER,
    headcount                       INTEGER CHECK (headcount IS NULL OR headcount >= 0),
    annual_cement_capacity_tonnes   REAL CHECK (annual_cement_capacity_tonnes IS NULL OR annual_cement_capacity_tonnes >= 0),
    annual_clinker_capacity_tonnes  REAL CHECK (annual_clinker_capacity_tonnes IS NULL OR annual_clinker_capacity_tonnes >= 0),
    created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production_data (
    id                        TEXT PRIMARY KEY,
    company_id                TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    period_start              DATE NOT NULL,
    period_end                DATE NOT NULL,
    clinker_produced_tonnes   REAL DEFAULT 0 CHECK (clinker_produced_tonnes >= 0),
    clinker_purchased_tonnes  REAL DEFAULT 0 CHECK (clinker_purchased_tonnes >= 0),
    cement_produced_tonnes    REAL DEFAULT 0 CHECK (cement_produced_tonnes >= 0),
    cement_dispatched_tonnes  REAL DEFAULT 0 CHECK (cement_dispatched_tonnes >= 0),
    clinker_to_cement_ratio   REAL,
    notes                     TEXT,
    created_at                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (period_end >= period_start)
);

CREATE TABLE IF NOT EXISTS emission_entries (
    id                       TEXT PRIMARY KEY,
    company_id               TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    scope                    TEXT NOT NULL CHECK (scope IN ('1', '2', '3')),
    category                 TEXT NOT NULL,
    sub_category             TEXT,
    activity_data            REAL NOT NULL CHECK (activity_data >= 0),
    activity_unit            TEXT NOT NULL,
    emission_factor          REAL NOT NULL CHECK (emission_factor >= 0),
    emission_factor_unit     TEXT,
    emission_factor_source   TEXT NOT NULL,
    total_emissions_kgco2e   REAL NOT NULL CHECK (total_emissions_kgco2e >= 0),
    biogenic_co2_kgco2       REAL DEFAULT 0 CHECK (biogenic_co2_kgco2 >= 0),
    period_start             DATE NOT NULL,
    period_end               DATE NOT NULL,
    plant_area               TEXT,
    data_quality             TEXT NOT NULL
        CHECK (data_quality IN ('measured', 'estimated', 'calculated')),
    calculation_method       TEXT,
    notes                    TEXT,
    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (period_end >= period_start)
);

CREATE TABLE IF NOT EXISTS reports (
    id                                   TEXT PRIMARY KEY,
    company_id                           TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    report_period                        TEXT NOT NULL,
    period_start                         DATE NOT NULL,
    period_end                           DATE NOT NULL,
    total_scope1_process                 REAL DEFAULT 0,
    total_scope1_combustion              REAL DEFAULT 0,
    total_scope1_mobile                  REAL DEFAULT 0,
    total_scope1_fugitive                REAL DEFAULT 0,
    total_scope1                         REAL DEFAULT 0,
    total_scope2_lb                      REAL DEFAULT 0,
    total_scope2_mb                      REAL DEFAULT 0,
    total_scope3                         REAL DEFAULT 0,
    total_emissions                      REAL DEFAULT 0,
    biogenic_co2_total                   REAL DEFAULT 0,
    specific_emissions_per_tonne_cement  REAL,
    specific_emissions_per_tonne_clinker REAL,
    clinker_to_cement_ratio              REAL,
    unit                                 TEXT DEFAULT 'tCO2e',
    status                               TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'final')),
    generated_at                         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (period_end >= period_start)
);

CREATE INDEX IF NOT EXISTS idx_emissions_company ON emission_entries(company_id);
CREATE INDEX IF NOT EXISTS idx_emissions_scope ON emission_entries(scope);
CREATE INDEX IF NOT EXISTS idx_production_company ON production_data(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_company ON reports(company_id);
