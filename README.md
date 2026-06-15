# Kilnify

A carbon accounting tool for cement manufacturing companies. Track, quantify, and report greenhouse gas (GHG) emissions across Scope 1, 2, and 3 following the GHG Protocol Corporate Standard and WBCSD CSI Cement CO₂ Protocol — supporting **cement plants**, **grinding plants**, and **packing plants**.

---

## Table of Contents

- [Overview](#overview)
- [Facility Types](#facility-types)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Emission Calculation Methodology](#emission-calculation-methodology)
- [Emission Factor Library](#emission-factor-library)
- [Data Models](#data-models)
- [Running Tests](#running-tests)
- [Standards & Compliance](#standards--compliance)
- [Disclaimer](#disclaimer)

---

## Overview

Kilnify enables cement manufacturers to:

- Log and calculate emissions from Scope 1 (direct process + combustion + mobile + fugitive), Scope 2 (purchased electricity), and Scope 3 (value chain)
- Apply cement-specific calculation methods including clinker calcination process emissions (Method A and Method B)
- Track intensity metrics including **specific emissions per tonne cement**, **specific emissions per tonne clinker**, and **clinker-to-cement ratio**
- Gate available emission categories by **facility type** — cement plant fields are not shown to grinding or packing plant operators
- Generate structured carbon footprint reports exportable as PDF and CSV
- View a live dashboard with monthly trends, scope breakdowns, intensity KPIs, and data quality summaries
- Browse a built-in emission factor library sourced from WBCSD CSI, IPCC 2006, PLN RUPTL 2023, DEFRA 2024, and GNR

All internal calculations use **kgCO₂e**. All reports and dashboard figures display in **tCO₂e**.
Biogenic CO₂ from alternative fuels is tracked separately and excluded from GHG inventory totals, but disclosed in reports.

> **Scope 3-only mode.** Kilnify ships configured as a **Scope 3 (value chain) specialist**: only Scope 3 emission
> entries can be logged, and the dashboard/reports focus on the Scope 3 category breakdown (GHG Protocol Cat 1–11).
> Scope 1/2 figures, cement/clinker intensity KPIs, and the Thermal Substitution Rate are hidden because they are
> derived from Scope 1/2 data that is no longer collected. This is controlled by a single flag — `SCOPE3_ONLY` in
> [`backend/constants.py`](backend/constants.py) and the mirrored `SCOPE3_ONLY` in
> [`frontend/src/utils/catalog.js`](frontend/src/utils/catalog.js). Set both to `False` to restore the full
> Scope 1/2/3 application.

---

## Facility Types

Kilnify supports three facility types within the cement value chain:

| Facility Type | Description | Key Scope 1 Sources |
|---|---|---|
| **Cement Plant** | Full integrated plant: quarry → raw mill → kiln → cement mill → dispatch | Clinker calcination process CO₂, kiln fuel combustion, on-site mobile equipment |
| **Grinding Plant** | Clinker import → finish grinding with additives → cement dispatch (no kiln) | On-site mobile equipment, diesel generators only |
| **Packing Plant** | Bulk cement reception → packaging → dispatch | On-site mobile equipment, diesel generators only |

> Facility type is set at company/plant registration and drives which emission categories are available throughout the application. Process emission (calcination) fields are exclusive to Cement Plants.

---

## Features

### Dashboard
- Total emissions (tCO₂e) with Scope 1 (process / combustion / mobile / fugitive breakdown), Scope 2, and Scope 3
- Monthly trend chart grouped by period and scope
- Intensity KPI cards: kgCO₂e/t cement, kgCO₂e/t clinker, clinker-to-cement ratio, specific electricity use
- Alternative-fuel KPIs: **Thermal Substitution Rate (TSR)** (energy-based), biogenic share of fuel, total kiln thermal energy
- Scope 3 breakdown by GHG Protocol category (1–15)
- Top 5 emission hotspots with percentage contribution
- Recent 10 entries
- Data quality summary (measured / estimated / calculated counts)

### Facility Setup
- Register a company/plant with facility type, country, region, Indonesian grid region, and production capacities
- Grid region selection determines default electricity emission factor (Java-Bali, Sumatra, Kalimantan, or national)

### Data Entry
- Facility-type-aware category selection — cement plants see kiln fuel and clinker calcination fields; packing plants see packaging material and electricity fields
- Live kgCO₂e preview (`activity_data × emission_factor`)
- Support for both **Method A** (clinker tonnes × default EF) and **Method B** (CaO content-based) for process emissions
- Biogenic CO₂ field for alternative fuel entries (excluded from totals, disclosed separately)
- Outlier detection: warns when a new entry exceeds 3× the historical average for the same scope + category
- Full validation: no negative values, date range enforcement, facility-type gating, clinker ratio bounds

### Production Log
- Monthly entry of clinker produced, clinker purchased, cement produced, cement dispatched
- Auto-calculates clinker-to-cement ratio
- Data feeds into intensity metric calculations on dashboard and reports

### Emission Factor Library
- Searchable and filterable factor library
- **User-defined custom factors**: add/edit/delete plant-specific or supplier-certified factors directly in the UI. Custom factors merge into the library (flagged `custom`) and become selectable in Data Entry. Built-in JSON factors stay read-only. Custom factors can be global or scoped to a specific facility.
- Covers: clinker process (WBCSD CSI / IPCC 2006), kiln fuels (coal, petcoke, HFO, natural gas, diesel, RDF), Indonesian grid by region (PLN RUPTL 2023), transport (DEFRA 2024), packaging materials (Ecoinvent), and the full Scope 3 value chain (purchased goods/SCMs, capital goods, fuel & energy WTT, up/downstream transport, waste, processing & use of sold products, commuting, business travel), refrigerants
- Each factor shows applicable facility types, value, unit, and source citation

### Report Generator
- Generate draft or final reports for any time period
- Scope 1 split by sub-type: process / combustion / mobile / fugitive
- Scope 2 location-based and market-based totals in tCO₂e
- Scope 3 total with category breakdown
- Intensity metrics: kgCO₂e/t cement, kgCO₂e/t clinker, clinker-to-cement ratio
- Biogenic CO₂ disclosed separately
- Data quality summary and methodology notes
- Disclaimer statement
- CSV export of all entries in the report period
- PDF export with cover page and executive summary

### Companies / Plants
- Multi-plant support
- Filter all data (emissions, production, reports, dashboard) by `company_id`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, shadcn/ui, Recharts |
| Backend | Python 3.9+, FastAPI, SQLAlchemy |
| Database | SQLite (development), PostgreSQL (production) |
| Validation | Pydantic v2 |
| Testing | pytest, httpx, FastAPI TestClient |

---

## Project Structure

```
kilnify/
├── backend/
│   ├── api/
│   │   ├── companies.py          # CRUD for companies/plants (with facility_type)
│   │   ├── emissions.py          # CRUD for emission entries + facility-type gating + outlier detection
│   │   ├── production.py         # CRUD for production data (clinker/cement volumes)
│   │   ├── reports.py            # Report generation, detail, CSV/PDF export, delete
│   │   ├── factors.py            # Read-only emission factor library endpoints
│   │   └── dashboard.py          # Aggregated dashboard data + intensity metrics
│   ├── data/
│   │   └── emission_factors/
│   │       ├── factors.json          # General factors (transport, commuting, travel, refrigerants)
│   │       ├── clinker_factors.json  # Clinker process EFs by method and region
│   │       ├── fuel_factors.json     # Kiln and mobile fuel EFs (coal, petcoke, HFO, diesel, RDF)
│   │       └── scope3_factors.json   # Full Scope 3 value-chain EFs (GHG Protocol Cat 1-11)
│   ├── services/
│   │   ├── emission_calculator.py   # Core calculation engine (9 modules)
│   │   ├── aggregator.py            # Scope breakdown, intensity metrics, hotspots, trend
│   │   └── factor_loader.py         # Loads/flattens the read-only factor JSON datasets
│   ├── constants.py              # Enums (FacilityType, Scope, ...) + facility-type gating map
│   ├── database.py               # SQLAlchemy engine and session setup
│   ├── models.py                 # ORM models: Company, ProductionData, EmissionEntry, Report
│   ├── schemas.py                # Pydantic v2 request/response schemas
│   ├── main.py                   # FastAPI app, CORS, router registration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                     # shadcn/ui primitives (generated, owned in-repo)
│   │   │   │   ├── button.jsx
│   │   │   │   ├── card.jsx
│   │   │   │   ├── input.jsx
│   │   │   │   ├── label.jsx
│   │   │   │   ├── select.jsx
│   │   │   │   ├── dialog.jsx
│   │   │   │   ├── table.jsx
│   │   │   │   ├── badge.jsx
│   │   │   │   └── sonner.jsx          # Toaster (sonner)
│   │   │   ├── Navbar.jsx
│   │   │   ├── ScopeCard.jsx
│   │   │   ├── IntensityKPICard.jsx
│   │   │   ├── DataQualityBadge.jsx    # wraps shadcn Badge
│   │   │   ├── FacilityTypeBadge.jsx   # wraps shadcn Badge
│   │   │   ├── FormSelect.jsx          # thin wrapper over shadcn Select for option lists
│   │   │   └── CompanySelector.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Facilities.jsx          # Facility setup / registration
│   │   │   ├── DataEntry.jsx           # Facility-type-aware emission entry form
│   │   │   ├── ProductionLog.jsx       # Monthly clinker/cement production entry
│   │   │   ├── Reports.jsx             # Report list + detail Dialog + CSV/PDF export
│   │   │   └── FactorLibrary.jsx
│   │   ├── lib/
│   │   │   └── utils.js                # cn() class-merge helper (clsx + tailwind-merge)
│   │   ├── utils/
│   │   │   ├── api.js                  # All fetch wrappers (relative /api paths via Vite proxy)
│   │   │   └── catalog.js              # Facility-type-gated emission category catalog
│   │   ├── CompanyContext.jsx          # Selected company/plant state shared across pages
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css                   # Tailwind + shadcn CSS theme variables
│   ├── components.json                 # shadcn/ui config (style, aliases, JSX mode)
│   ├── jsconfig.json                   # "@/..." path alias for editor/tooling
│   ├── tailwind.config.js              # Tailwind theme + shadcn design tokens
│   ├── vite.config.js                  # "@" alias + proxies /api -> http://localhost:8003
│   └── package.json
├── database/
│   └── schema.sql                      # Raw SQL schema with constraints
├── tests/
│   ├── conftest.py
│   ├── test_emission_calculator.py     # All 9 modules, clinker Method A & B, unit converters
│   ├── test_api_companies.py
│   ├── test_api_emissions.py           # Facility-type gating, entry creation + math
│   ├── test_api_production.py
│   ├── test_api_reports.py             # Scope sub-type totals, intensity metrics, CSV/PDF
│   ├── test_api_factors.py
│   └── test_api_dashboard.py
├── .env.example
└── GUIDELINES.md
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ and npm
- Git

---

### Backend Setup

**1. Navigate to the project root:**

```bash
cd kilnify
```

**2. Create and activate a virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

**3. Install Python dependencies:**

```bash
pip install -r backend/requirements.txt
```

**4. Set up environment variables:**

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local SQLite development)
```

**5. Start the API server:**

```bash
uvicorn backend.main:app --reload --port 8003
```

The API will be available at `http://localhost:8003`.
Interactive docs: `http://localhost:8003/docs`

---

### Frontend Setup

**1. Navigate to the frontend directory:**

```bash
cd frontend
```

**2. Install dependencies:**

```bash
npm install
```

**3. Start the dev server:**

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.
The Vite dev server proxies all `/api` requests to `http://localhost:8003`, so both services must be running concurrently.

> **shadcn/ui note:** The UI primitives in `src/components/ui/` are checked into the
> repository (shadcn/ui is copy-in, not a runtime dependency), so `npm install` is all
> that's needed — no `shadcn init` step. To add more primitives later, run
> `npx shadcn@latest add <component>` from the `frontend/` directory; `components.json`
> is already configured for JSX + the `@/` alias. Toast notifications use `sonner`
> (mounted in `App.jsx`), and the report detail view uses the shadcn `Dialog`.

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./kilnify.db` | SQLAlchemy database URL |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Comma-separated list of allowed frontend origins |

For production with PostgreSQL:

```
DATABASE_URL=postgresql://user:password@localhost:5432/kilnify
```

> Never hardcode credentials in source code. Always use environment variables.

---

## API Reference

All endpoints are prefixed with `/api`. Interactive docs available at `/docs` when the server is running.

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check |

### Companies — `/api/companies`

| Method | Path | Description |
|---|---|---|
| GET | `/api/companies/` | List all companies/plants |
| POST | `/api/companies/` | Create a company/plant |
| GET | `/api/companies/{id}` | Get a company by ID |
| DELETE | `/api/companies/{id}` | Delete a company |

**POST body example:**
```json
{
  "name": "PT Semen Nusantara — Tuban Plant",
  "facility_type": "cement_plant",
  "country": "Indonesia",
  "region": "East Java",
  "grid_region": "java_bali",
  "reporting_year": 2025,
  "headcount": 450,
  "annual_cement_capacity_tonnes": 3000000,
  "annual_clinker_capacity_tonnes": 2200000
}
```

### Production Data — `/api/production`

| Method | Path | Description |
|---|---|---|
| GET | `/api/production/` | List production entries (filter: `company_id`) |
| POST | `/api/production/` | Create a production entry |
| GET | `/api/production/{id}` | Get entry by ID |
| DELETE | `/api/production/{id}` | Delete entry |

**POST body example:**
```json
{
  "company_id": "uuid",
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "clinker_produced_tonnes": 150000,
  "clinker_purchased_tonnes": 0,
  "cement_produced_tonnes": 185000,
  "cement_dispatched_tonnes": 180000
}
```

### Emissions — `/api/emissions`

| Method | Path | Description |
|---|---|---|
| GET | `/api/emissions/` | List entries (filter: `company_id`, `scope`) |
| POST | `/api/emissions/` | Create entry, auto-calculate total, check outlier, validate facility type |
| GET | `/api/emissions/{id}` | Get entry by ID |
| DELETE | `/api/emissions/{id}` | Delete entry |

**POST body example (Cement Plant — clinker process emissions):**
```json
{
  "company_id": "uuid",
  "scope": "1",
  "category": "clinker_calcination",
  "sub_category": "method_a",
  "activity_data": 150000.0,
  "activity_unit": "tonnes_clinker",
  "emission_factor": 525.0,
  "emission_factor_unit": "kgCO2e/tonne_clinker",
  "emission_factor_source": "WBCSD CSI 2022 / GNR global average",
  "biogenic_co2_kgco2": 0.0,
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "plant_area": "Kiln",
  "data_quality": "calculated",
  "calculation_method": "Method A — clinker production × default EF"
}
```

**POST body example (Grinding Plant — purchased clinker upstream Scope 3):**
```json
{
  "company_id": "uuid",
  "scope": "3",
  "category": "purchased_clinker_upstream",
  "sub_category": "supplier_default",
  "activity_data": 80000.0,
  "activity_unit": "tonnes_clinker",
  "emission_factor": 842.0,
  "emission_factor_unit": "kgCO2e/tonne_clinker",
  "emission_factor_source": "GNR 2022 global average (process + combustion)",
  "period_start": "2025-01-01",
  "period_end": "2025-01-31",
  "data_quality": "calculated"
}
```

**Response includes:**
- `total_emissions_kgco2e` — auto-calculated (`activity_data × emission_factor`)
- `warning` — present if the entry is >3× the historical average for that scope + category

### Reports — `/api/reports`

| Method | Path | Description |
|---|---|---|
| GET | `/api/reports/` | List reports (filter: `company_id`) |
| POST | `/api/reports/generate` | Generate a report for a period |
| GET | `/api/reports/{id}` | Get report summary |
| GET | `/api/reports/{id}/detail` | Full detail with scope sub-type breakdown, Scope 3 category breakdown, TSR metrics, and intensity metrics |
| GET | `/api/reports/{id}/export/csv` | Download entries as CSV |
| GET | `/api/reports/{id}/export/pdf` | Download a formatted PDF (cover page, executive summary, scope/hotspot tables). Requires `reportlab`. |
| DELETE | `/api/reports/{id}` | Delete a report |

**Generate body example:**
```json
{
  "company_id": "uuid",
  "report_period": "2025 Annual",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "status": "draft"
}
```

### Emission Factors — `/api/factors`

| Method | Path | Description |
|---|---|---|
| GET | `/api/factors/` | List factors — built-in + custom (filter: `category`, `search`, `facility_type`, `company_id`) |
| GET | `/api/factors/categories` | List all available categories (built-in + custom) |
| GET | `/api/factors/raw` | Raw built-in factors JSON content |
| GET | `/api/factors/custom` | List user-added custom factors (filter: `company_id`) |
| POST | `/api/factors/custom` | Create a custom factor |
| PUT | `/api/factors/custom/{id}` | Update a custom factor |
| DELETE | `/api/factors/custom/{id}` | Delete a custom factor |

Built-in factors from the JSON datasets are **read-only**. Custom factors are stored in the
database, fully editable, flagged `editable: true` in listings, and become selectable in Data Entry.
A custom factor with a null `company_id` is **global** (available to every facility); otherwise it
is scoped to that company. `applicable_facility_types: []` means it applies to all facility types.

**Custom factor POST body example:**
```json
{
  "company_id": "uuid",
  "scope": "3",
  "category": "purchased_goods",
  "sub_category": "supplier_x_slag",
  "factor_value": 65.0,
  "unit": "kgCO2e/tonne",
  "activity_unit": "tonnes",
  "source": "Supplier EPD 2025",
  "year": 2025,
  "applicable_facility_types": ["cement_plant"]
}
```

### Dashboard — `/api/dashboard`

| Method | Path | Description |
|---|---|---|
| GET | `/api/dashboard/` | Aggregated stats + intensity metrics (filter: `company_id`) |

**Response shape:**
```json
{
  "total_tco2e": 94500.0,
  "scope1_process_tco2e": 78750.0,
  "scope1_combustion_tco2e": 8400.0,
  "scope1_mobile_tco2e": 1200.0,
  "scope1_fugitive_tco2e": 50.0,
  "scope1_tco2e": 88400.0,
  "scope2_tco2e": 4200.0,
  "scope3_tco2e": 1900.0,
  "biogenic_co2_tco2e": 320.0,
  "intensity_kgco2e_per_tonne_cement": 510.8,
  "intensity_kgco2e_per_tonne_clinker": 595.3,
  "clinker_to_cement_ratio": 0.81,
  "monthly_trend": [
    { "month": "2025-01", "scope1": 7200.0, "scope2": 350.0, "scope3": 158.0, "total": 7708.0 }
  ],
  "top_hotspots": [
    { "category": "clinker_calcination", "emissions_tco2e": 78750.0, "percentage": 83.3 }
  ],
  "scope3_by_category": [
    { "ghg_category": 1, "label": "Cat 1 — Purchased goods & services", "emissions_tco2e": 1200.0, "percentage": 63.2 },
    { "ghg_category": 9, "label": "Cat 9 — Downstream transportation & distribution", "emissions_tco2e": 700.0, "percentage": 36.8 }
  ],
  "alternative_fuel_metrics": {
    "total_thermal_gj": 4485.0,
    "alternative_thermal_gj": 1800.0,
    "thermal_substitution_rate_pct": 40.13,
    "biogenic_share_pct": 5.2
  },
  "recent_entries": [...],
  "data_quality_summary": { "measured": 12, "calculated": 8, "estimated": 3 }
}
```

---

## Emission Calculation Methodology

All calculations follow: `Emissions (kgCO₂e) = Activity Data × Emission Factor`

### Module 1 — Clinker Process Emissions (Scope 1 — Cement Plant Only)

**Method A (default):**
```
Emissions = Clinker Produced (tonnes) × 525 kgCO₂/tonne
```

**Method B (plant-specific, higher accuracy):**
```
Emissions = Clinker (t) × [(CaO% × 0.785 + MgO% × 1.092) / 100 × (44/56)]
```
- CaO_content: % CaO in clinker (typically 63–67%)
- Used when plant has lab-certified raw meal / clinker chemistry data

### Module 2 — Kiln Fuel Combustion (Scope 1 — Cement Plant)
```
Emissions = Fuel Consumption (tonnes) × Fuel Emission Factor (kgCO₂e/tonne fuel)
```
Only fossil-derived fraction counted for alternative fuels / RDF. Biogenic fraction tracked separately.

### Module 3 — Electricity (Scope 2)
```
Emissions = kWh consumed × Grid Emission Factor (kgCO₂e/kWh)
```
Default: Indonesian PLN grid by region (Java-Bali: 0.85, Sumatra: 0.79, Kalimantan: 0.92, national avg: 0.87 kgCO₂e/kWh).

### Module 4 — On-Site Mobile Equipment (Scope 1)
```
Emissions = Fuel Consumption (liters) × Fuel EF (kgCO₂e/liter)
```
Diesel: 2.68 kgCO₂e/liter | Petrol: 2.31 kgCO₂e/liter

### Module 5 — Purchased Clinker Upstream (Scope 3 — Grinding Plant)
```
Emissions = Clinker Purchased (tonnes) × 842 kgCO₂e/tonne (GNR 2022 default)
```
Override with supplier-certified clinker emission factor if available.

### Module 6 — Outbound Transport (Scope 3)
```
Emissions = Product Shipped (tonnes) × Distance (km) × Transport Mode Factor (kgCO₂e/tonne·km)
```
Modes: heavy truck >32t (0.062), train (0.028), bulk ship handysize (0.011), bulk ship supramax (0.009).

### Module 7 — Packaging Materials (Scope 3 — Packing & Grinding Plants)
```
Emissions = Packaging Units × Packaging Material EF (kgCO₂e/unit)
```
Paper bag 50kg (0.55), PP woven bag 50kg (0.38), big bag/FIBC 1t (14.0).

### Module 8 — Business Travel (Scope 3)
```
Emissions = Distance (km) × Transport Mode Factor (kgCO₂e/km/passenger)
```

### Module 9 — Employee Commuting (Scope 3)
```
Emissions = Employees × Avg Distance (km/day) × Working Days × Mode Factor × 2
```
Multiplied by 2 for return trip.

### Full Scope 3 Value Chain (GHG Protocol Categories 1–15)

Scope 3 entries are classified by GHG Protocol Corporate Value Chain category for breakdown in the dashboard and reports:

| Cat | Category | Example cement-sector sources |
|---|---|---|
| 1 | Purchased goods & services | Gypsum, limestone filler, SCMs (fly ash, GGBFS slag, pozzolan), grinding aids, refractories, packaging, purchased clinker |
| 2 | Capital goods | Machinery & vehicles (spend-based), structural steel |
| 3 | Fuel- & energy-related activities | Grid T&D losses, well-to-tank (WTT) of coal / diesel / gas |
| 4 | Upstream transportation & distribution | Inbound raw material / fuel haulage (tonne·km) |
| 5 | Waste generated in operations | CKD to landfill, general waste, wastewater |
| 6 | Business travel | Flights, rail, car (passenger·km) |
| 7 | Employee commuting | Car, motorcycle, public transit |
| 9 | Downstream transportation & distribution | Outbound cement dispatch (tonne·km) |
| 10 | Processing of sold products | Third-party grinding of sold clinker |
| 11 | Use of sold products | Cement is inert in use (~0); recarbonation disclosed separately if quantified |

All Scope 3 categories use the generic `Emissions = Activity Data × Emission Factor` formula. Categories 8, 12–15 are not modelled (typically immaterial for cement).

### Thermal Substitution Rate (TSR) & Alternative Fuels

```
TSR = Σ(alternative-fuel thermal energy GJ) / Σ(total kiln-fuel thermal energy GJ)
```
Thermal energy is derived from each kiln-fuel entry's mass × net calorific value (GJ/t, IPCC 2006 / GNR). Alternative fuels (RDF, biomass, tires, solvents, etc.) are counted in the numerator; the biogenic share is derived from each entry's disclosed biogenic CO₂. Surfaced on the dashboard and in report detail.

### Unit Conversions
- Internal storage: **kgCO₂e**
- Display / reports: **tCO₂e** (`kg ÷ 1000`)

### GWP Values (IPCC AR6, 2021 — GWP-100)

| Gas | GWP-100 |
|---|---|
| CO₂ | 1 |
| CH₄ | 29.8 |
| N₂O | 273 |
| SF₆ | 25,200 |
| HFC R-410A | 2,088 |

---

## Emission Factor Library

Built-in factors stored in `backend/data/emission_factors/`.

| Category | Key Sub-Categories | Source |
|---|---|---|
| clinker_process | method_a default (525 kgCO₂/t), method_b formula | WBCSD CSI / IPCC 2006 |
| kiln_fuel | coal (2,540), petcoke (3,150), natural_gas (1,900), HFO (3,150), diesel (2,680), RDF (fossil fraction ~495) | IPCC 2006 |
| electricity | java_bali (0.850), sumatra (0.790), kalimantan (0.920), national (0.870) | PLN RUPTL 2023 / IEA |
| mobile_equipment | diesel (2.68 kgCO₂e/liter), petrol (2.31 kgCO₂e/liter) | DEFRA 2024 |
| purchased_clinker | supplier_default (842 kgCO₂e/tonne) | GNR 2022 |
| transport_outbound | truck_heavy (0.062), train (0.028), ship_handysize (0.011), ship_supramax (0.009) | DEFRA 2024 |
| packaging | paper_bag_50kg (0.55), pp_bag_50kg (0.38), big_bag_1t (14.0) | Ecoinvent 3.9 |
| travel | flight_short_haul (0.255), flight_long_haul (0.195), train (0.041), car_petrol (0.192) | DEFRA 2024 |
| commuting | car_petrol (0.192), car_ev (0.073), motorcycle (0.113), public_transit (0.089) | DEFRA 2024 |
| refrigerants | r410a (2,088 GWP), r32 (771 GWP), r134a (1,430 GWP) | IPCC AR6 2021 |

The **built-in** factors above are read-only — to change them, edit the JSON files in `backend/data/emission_factors/` directly. The full Scope 3 value-chain factors live in `scope3_factors.json` (GHG Protocol categories 1–11).

End users can also add their own **custom factors** through the UI (Emission Factor Library → *Add factor*) or the `/api/factors/custom` endpoints. Custom factors are stored in the database, are fully editable/deletable, merge into the library listing, and become selectable in Data Entry — without touching the read-only reference data.

---

## Data Models

### Company
| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| name | string | Company/plant name |
| facility_type | enum | `cement_plant`, `grinding_plant`, or `packing_plant` |
| country | string | Country of operations |
| region | string | Province/region |
| grid_region | enum | `java_bali`, `sumatra`, `kalimantan`, `national` |
| reporting_year | integer | Target reporting year |
| headcount | integer | Number of employees (optional) |
| annual_cement_capacity_tonnes | float | Nameplate cement capacity in t/year (optional) |
| annual_clinker_capacity_tonnes | float | Nameplate clinker capacity in t/year (optional) |

### ProductionData
| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| company_id | UUID | Foreign key to Company |
| period_start | date | Start of production period |
| period_end | date | End of production period |
| clinker_produced_tonnes | float | Clinker produced (Cement Plant only) |
| clinker_purchased_tonnes | float | Clinker purchased externally (Grinding Plant) |
| cement_produced_tonnes | float | Cement produced in period |
| cement_dispatched_tonnes | float | Cement dispatched to customers |
| clinker_to_cement_ratio | float | Auto-calculated: clinker / cement produced |

### EmissionEntry
| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| company_id | UUID | Foreign key to Company |
| scope | string | "1", "2", or "3" |
| category | string | Emission category (e.g., `clinker_calcination`, `kiln_fuel`) |
| sub_category | string | Sub-category (e.g., `coal`, `method_a`) — optional |
| activity_data | float | Raw activity quantity (>= 0) |
| activity_unit | string | Unit of activity (tonnes_clinker, liters, kWh, etc.) |
| emission_factor | float | Factor value (kgCO₂e per activity unit) |
| emission_factor_unit | string | Unit of the emission factor |
| emission_factor_source | string | Source citation |
| total_emissions_kgco2e | float | Calculated: activity_data × emission_factor |
| biogenic_co2_kgco2 | float | Biogenic CO₂ (excluded from totals, disclosed separately) |
| period_start | date | Start of reporting period |
| period_end | date | End of reporting period |
| plant_area | string | Plant area attribution (e.g., Kiln, Raw Mill, Cement Mill) |
| data_quality | string | "measured", "estimated", or "calculated" |
| calculation_method | string | Method used (e.g., Method A, Method B) |
| notes | string | Optional free-text notes |
| created_at | datetime | Auto-set on creation |

### CustomFactor
| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| company_id | UUID | Foreign key to Company — `null` makes the factor global (all facilities) |
| scope | string | "1", "2", or "3" — lets the factor drive Data Entry |
| category | string | Emission category (existing or new) |
| sub_category | string | Sub-category label (optional) |
| factor_value | float | Emission factor value (>= 0) |
| unit | string | EF unit (e.g., kgCO2e/tonne) |
| activity_unit | string | Activity unit the factor applies to (optional) |
| source | string | Source citation (optional) |
| year | integer | Source/vintage year (optional) |
| applicable_facility_types | string | Comma-separated facility types; empty = all |
| notes | string | Optional free-text notes |
| created_at | datetime | Auto-set on creation |

### Report
| Field | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| company_id | UUID | Foreign key to Company |
| report_period | string | Label (e.g., "2025 Annual") |
| period_start | date | Start of report period |
| period_end | date | End of report period |
| total_scope1_process | float | Scope 1 calcination emissions in tCO₂e |
| total_scope1_combustion | float | Scope 1 fuel combustion in tCO₂e |
| total_scope1_mobile | float | Scope 1 mobile equipment in tCO₂e |
| total_scope1_fugitive | float | Scope 1 fugitive (refrigerants) in tCO₂e |
| total_scope1 | float | Scope 1 total in tCO₂e |
| total_scope2_lb | float | Scope 2 location-based in tCO₂e |
| total_scope2_mb | float | Scope 2 market-based in tCO₂e |
| total_scope3 | float | Scope 3 total in tCO₂e |
| total_emissions | float | Sum of all scopes in tCO₂e |
| biogenic_co2_total | float | Total biogenic CO₂ disclosed separately (tCO₂) |
| specific_emissions_per_tonne_cement | float | kgCO₂e/t cement |
| specific_emissions_per_tonne_clinker | float | kgCO₂e/t clinker |
| clinker_to_cement_ratio | float | Clinker-to-cement ratio for the period |
| unit | string | Always "tCO₂e" |
| status | string | "draft" or "final" |
| generated_at | datetime | Auto-set on generation |

> Raw `activity_data` and `emission_factor` are always stored separately on each entry to enable audit trails and recalculations when factors are updated. Biogenic CO₂ is always tracked but excluded from the `total_emissions` field.

---

## Running Tests

Tests use an in-memory SQLite database and are fully isolated — they do not touch the development database.

**Install test dependencies** (already included in `requirements.txt`):
```bash
pip install pytest httpx
```

**Run all tests:**
```bash
cd kilnify
pytest tests/ -v
```

**Run a specific test file:**
```bash
pytest tests/test_emission_calculator.py -v
pytest tests/test_api_emissions.py -v
```

### Test Coverage

| File | What It Tests |
|---|---|
| `test_emission_calculator.py` | All 9 calculation modules, clinker Method A and B, biogenic CO₂ separation, unit converters |
| `test_api_companies.py` | Company CRUD with facility_type, validation, 404 handling |
| `test_api_production.py` | Production data CRUD, clinker-to-cement ratio auto-calc |
| `test_api_emissions.py` | Facility-type gating (calcination blocked for grinding/packing), entry math, outlier warning |
| `test_api_reports.py` | Scope sub-type totals, intensity metrics, biogenic disclosure, CSV export |
| `test_api_factors.py` | Factor values, facility_type filtering, search, categories endpoint |
| `test_api_dashboard.py` | Scope math, intensity KPIs, monthly trend, hotspots, company isolation |
| `test_scope3_and_custom_factors.py` | Scope 3 category breakdown, TSR / alternative-fuel metrics, `processing_sold_products` gating, custom factor CRUD + global/company scoping |

### Test Architecture

- `conftest.py` sets up a **session-scoped** in-memory database and creates all tables once
- An `autouse` function-scoped fixture **truncates all tables** between tests to ensure isolation
- `app.dependency_overrides[get_db]` replaces the production DB session with the test session
- Fixtures: `client` (TestClient), `cement_company`, `grinding_company`, `packing_company`, `production_entry`, `emission_entry`

---

## Standards & Compliance

Kilnify follows these standards:

| Standard | Usage |
|---|---|
| GHG Protocol Corporate Standard | Core accounting framework for Scope 1, 2, 3 classification |
| WBCSD CSI / GCCA Cement CO₂ and Energy Protocol | Cement-specific process emission methodology, biogenic rules, clinker EF |
| GNR (Getting the Numbers Right) | Cement sector benchmark database for clinker upstream EF and intensity benchmarks |
| IPCC 2006 Guidelines Vol. 3 Ch. 2 | Process emission calculation for clinker production |
| IPCC AR6 (2021) GWP-100 | Global Warming Potential values for all GHGs |
| PLN RUPTL 2023 | Indonesian regional grid emission factors |
| DEFRA GHG Conversion Factors 2024 | Fuel combustion, transport, commuting, and business travel factors |
| Ecoinvent v3.9 | Lifecycle emission factors for packaging materials |
| ISO 14064-1 | GHG inventory verification standard (reference) |

---

## Disclaimer

> This tool generates carbon footprint estimates based on user-provided activity data and industry-standard emission factors. Results have **not been independently verified**. Figures should not be used for external regulatory reporting, public disclosure, or GHG verification submissions without review by a certified carbon accountant or accredited third-party verifier.

---

*Follow GHG Protocol and WBCSD CSI Cement CO₂ Protocol. Verify with a certified carbon accountant before external reporting.*
