# 🏭 GUIDELINES.md — Carbon Accounting Tool for Cement Industries
> Agent Reference Document | Built for: Claude Code or any AI coding agent
> Project Codename: **Kilnify**

---

## 📌 Overview

This document defines the **scope, architecture, data logic, calculation methodology, and development rules** for building a carbon accounting tool tailored to **cement manufacturing companies**. Follow this as your source of truth throughout the build.

The tool supports three facility types across the cement value chain:
- **Cement Plant** — Full integrated facility: raw material preparation, kiln/clinker production, finish grinding, and dispatch
- **Grinding Plant** — Clinker import, finish grinding, and cement dispatch (no kiln operations)
- **Packing Plant** — Cement reception in bulk, packaging into bags/big-bags, and dispatch

The tool enables cement companies to:
- Track and quantify GHG emissions per facility type
- Categorize emissions by Scope 1, 2, and 3 (GHG Protocol)
- Apply cement-specific methodologies including process emissions from clinker production
- Generate carbon footprint reports per plant, department, product type, or time period
- Track clinker-to-cement ratio as a key intensity metric
- Identify emission hotspots and reduction opportunities

---

## 🏗️ Project Architecture

### Tech Stack (Default Recommendation)
| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS + shadcn/ui |
| Backend / Logic | Python (FastAPI) |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Data Viz | Recharts |
| Export | PDF (reportlab), CSV |
| Deployment | Docker-ready, cloud-agnostic |

> **Agent Rule**: Unless the user specifies otherwise, default to the stack above. Backend on port 8003, frontend on port 5173.

### Directory Structure
```
kilnify/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   └── public/
├── backend/
│   ├── api/
│   │   ├── companies.py
│   │   ├── emissions.py
│   │   ├── reports.py
│   │   ├── factors.py
│   │   └── dashboard.py
│   ├── models/
│   ├── services/
│   │   └── emission_calculator.py
│   ├── data/
│   │   └── emission_factors/        ← Cement-specific emission factor datasets
│   │       ├── factors.json
│   │       ├── clinker_factors.json
│   │       └── fuel_factors.json
│   └── main.py
├── database/
│   └── schema.sql
├── tests/
├── docs/
└── GUIDELINES.md                    ← This file
```

---

## 🏭 Facility Types & Their Emission Profiles

### Facility Type 1: Cement Plant (Integrated)
A full integrated cement plant includes raw material quarrying/preparation, pre-heating, kiln firing for clinker production, clinker cooling, finish grinding with additives, and bagging/dispatch.

**Key emission sources:**
- Scope 1: Clinker process emissions (calcination of limestone — the largest single source), kiln fuel combustion (coal, petcoke, alternative fuels), on-site mobile equipment (haul trucks, loaders), diesel generators, refrigerant leaks
- Scope 2: Grid electricity for raw mills, cement mills, fans, compressors, lighting
- Scope 3: Quarrying raw materials, upstream fuel supply chain, purchased additives (fly ash, slag, gypsum), employee commuting, business travel, downstream transport of clinker/cement

### Facility Type 2: Grinding Plant
A grinding plant receives clinker (imported from a cement plant or purchased), grinds it with additives (gypsum, fly ash, limestone filler, slag), and dispatches finished cement.

**Key emission sources:**
- Scope 1: Diesel fuel for on-site mobile equipment (forklifts, loaders), diesel generators, refrigerant leaks. **No kiln — no calcination process emissions at this facility.**
- Scope 2: Grid electricity for cement mills, separators, fans, compressors, packaging machines, lighting
- Scope 3: Upstream emissions from clinker production (most significant — must be calculated using supplier clinker emission factor), purchased additives, employee commuting, outbound transport

### Facility Type 3: Packing Plant
A packing plant receives finished cement in bulk (via truck or ship), stores it in silos, then packages it into bags (25kg, 40kg, 50kg) or big-bags, and dispatches.

**Key emission sources:**
- Scope 1: Diesel for on-site mobile equipment (forklifts), diesel generators
- Scope 2: Grid electricity for silo equipment, packaging machines, conveyor belts, dust collectors, lighting
- Scope 3: Upstream transport of bulk cement to packing plant, packaging materials (paper bags, polypropylene bags), employee commuting, outbound transport of packed cement

> **Agent Rule**: The application must require `facility_type` on every Company record and use it to filter available emission categories in the Data Entry forms. A Packing Plant should not show clinker calcination fields. A Grinding Plant should not show kiln fuel consumption fields.

---

## 📐 Scope of Emissions (GHG Protocol — Cement Context)

### Scope 1 — Direct Emissions

#### 1A. Process Emissions (Cement Plant ONLY)
The **dominant source** in integrated cement plants — CO₂ released from calcination of calcium carbonate (limestone) during clinker production in the rotary kiln.

```
CaCO₃ → CaO + CO₂
```

This is a **chemistry-driven emission**, not a combustion emission. It must be tracked separately.

| Sub-Category | Description |
|---|---|
| Clinker calcination | CO₂ from limestone decomposition in rotary kiln |
| Raw meal kiln bypass | CO₂ from kiln bypass dust disposal |
| CKD (Cement Kiln Dust) | CO₂ from CKD that is not returned to kiln |

#### 1B. Fuel Combustion Emissions (Cement Plant + Grinding Plant)
CO₂ from burning fuels to heat the kiln, pre-heater, calciner, and dryers.

| Fuel Type | Application |
|---|---|
| Coal / Anthracite | Primary kiln fuel |
| Petroleum coke (petcoke) | Primary kiln fuel (high carbon content) |
| Natural gas | Pre-heater, calciner, ignition |
| Heavy fuel oil (HFO) | Backup kiln fuel |
| Alternative fuels (RDF, waste-derived) | Co-processing in kiln |
| Diesel | On-site mobile equipment, generators |

#### 1C. Fugitive Emissions
| Sub-Category | Description |
|---|---|
| Refrigerant leaks | HVAC/cooling systems (R-410A, R-32, R-134a) |
| Dust emissions | (Not a GHG — tracked separately for environmental compliance) |

---

### Scope 2 — Indirect Energy Emissions
Electricity purchased from the grid for plant operations.

| Consumer | Facility Types |
|---|---|
| Raw mills (ball mill, VRM) | Cement Plant |
| Rotary kiln drives + fans | Cement Plant |
| Cooler fans | Cement Plant |
| Cement mills (ball mill, VRM) | Cement Plant, Grinding Plant |
| Separators / classifiers | Cement Plant, Grinding Plant |
| Compressors (pneumatic transport) | All |
| Packaging machines | Cement Plant, Grinding Plant, Packing Plant |
| Conveyor belts and bucket elevators | All |
| Dust collectors / bag filters | All |
| Lighting and general facilities | All |

> **Agent Rule**: Use **location-based** method as default for cement companies (Indonesian grid emission factor: 0.87 kgCO₂e/kWh based on PLN grid average). Allow market-based override if supplier certificate is available.

---

### Scope 3 — Value Chain Emissions (Cement-Specific)

| Category | Cement Relevance | Facility Types |
|---|---|---|
| Purchased raw materials | Limestone quarrying upstream emissions | Cement Plant |
| Purchased clinker | Upstream production emissions of imported clinker | Grinding Plant |
| Purchased additives | Fly ash (from coal power plants), slag (from steel), gypsum | All |
| Fuel & energy upstream | Extraction and transport of coal/petcoke to plant | Cement Plant |
| Upstream transport (inbound) | Delivery of clinker, coal, additives, gypsum to plant | All |
| Downstream transport (outbound) | Delivery of clinker/cement to customers | All |
| Waste generated | Kiln dust disposal, wastewater treatment | Cement Plant |
| Business travel | Flights, hotels for technical/management staff | All |
| Employee commuting | Daily travel to plant | All |
| **Packaging materials** | ⭐ Paper bags, PP bags, big-bags — significant for Packing Plants | Grinding Plant, Packing Plant |
| **Leased assets** | Co-processing waste from external parties | Cement Plant |
| **Use of sold products** | Downstream concrete/construction emissions (optional, boundary dependent) | Optional |

> **Agent Rule**: For Grinding Plants, purchased clinker upstream emissions (Scope 3, Category 1) are typically the **single largest emission category** and must always be included.

---

## 🔢 Calculation Methodology

### General Formula
```
Emissions (kgCO₂e) = Activity Data × Emission Factor
```

### Emission Factor Sources (Priority Order)
1. **Plant-specific measured data** — lab-certified clinker CaO content, fuel calorific values
2. **Supplier-specific** emission factors (vendor EPD, clinker supplier declaration)
3. **Regional defaults** — Indonesian grid factor, MEMR fuel factors
4. **International standards** — IPCC 2006/2019, GNR (Getting the Numbers Right) cement database, WBCSD CSI
5. **DEFRA / EPA** as fallback for non-cement categories

---

### Key Calculation Modules

#### Module 1: Clinker Process Emissions (Scope 1 — Cement Plant ONLY)

**Method A — Clinker-Based (Recommended)**
```
Emissions (kgCO₂) = Clinker Production (tonnes) × Clinker EF (kgCO₂/tonne clinker)
```
Default clinker emission factor: **525 kgCO₂/tonne clinker** (WBCSD CSI / GNR global average)
Plant-specific range: 490–540 kgCO₂/tonne clinker depending on raw material CaO content.

**Method B — CaO Content Based (Plant-Specific, Higher Accuracy)**
```
Emissions = Clinker Production × (CaO_content% × 0.785 + MgO_content% × 1.092) / 100 × 44/56
```
- CaO_content: % CaO in clinker (typically 63–67%)
- 0.785 and 1.092 are stoichiometric factors for CO₂ release per unit CaO/MgO
- 44/56 = molecular weight ratio CO₂/CaO

> **Agent Rule**: Default to Method A. Allow Method B when plant-specific CaO content data is available.

#### Module 2: Kiln Fuel Combustion (Scope 1 — Cement Plant)
```
Emissions = Fuel Consumption (tonnes or GJ) × Fuel Emission Factor (kgCO₂e/tonne or kgCO₂e/GJ)
```

| Fuel | EF (kgCO₂e/tonne fuel) | EF (kgCO₂e/GJ) | Source |
|---|---|---|---|
| Coal (bituminous) | 2,540 | 94.6 | IPCC 2006 |
| Petroleum coke | 3,150 | 97.5 | IPCC 2006 |
| Natural gas | 1,900 | 56.1 | IPCC 2006 |
| Heavy fuel oil | 3,150 | 77.4 | IPCC 2006 |
| Diesel | 2,680 | 74.1 | DEFRA 2024 |
| RDF (Refuse Derived Fuel) | 330–660 | — | Variable (biogenic fraction excluded) |
| Biomass (waste wood, etc.) | 0 (biogenic) | 0 | GHG Protocol biogenic rules |

> **Agent Rule**: For alternative fuels and co-processing, only count the **fossil-derived fraction** of emissions. Biogenic CO₂ is excluded from the GHG inventory per GHG Protocol rules but must be reported separately for transparency.

#### Module 3: Electricity Consumption (Scope 2)
```
Emissions = kWh consumed × Grid Emission Factor (kgCO₂e/kWh)
```

| Region / Grid | EF (kgCO₂e/kWh) | Source |
|---|---|---|
| Indonesia (PLN national avg) | 0.870 | MEMR / IEA 2023 |
| Java-Bali (PLN) | 0.850 | PLN RUPTL 2023 |
| Sumatra (PLN) | 0.790 | PLN RUPTL 2023 |
| Kalimantan (PLN) | 0.920 | PLN RUPTL 2023 |
| Self-generation (diesel genset) | 0.700 | IPCC 2006 |

> **Agent Rule**: Always ask for which Indonesian grid region the plant is connected to. Default to national average (0.87) if unknown.

#### Module 4: On-Site Mobile Equipment (Scope 1)
```
Emissions = Fuel Consumption (liters) × Fuel Emission Factor (kgCO₂e/liter)
```
- Diesel for haul trucks, wheel loaders, forklifts, bulldozers at quarry/plant
- Diesel EF: **2.68 kgCO₂e/liter** (DEFRA 2024)
- Petrol EF: **2.31 kgCO₂e/liter** (DEFRA 2024)

#### Module 5: Purchased Clinker — Upstream Emissions (Scope 3 — Grinding Plant)
```
Emissions = Clinker Purchased (tonnes) × Clinker Upstream EF (kgCO₂e/tonne)
```
- If supplier provides a certified clinker emission factor (EPD / carbon declaration), use that
- Default fallback: **842 kgCO₂e/tonne clinker** (includes process + fuel combustion, GNR 2022 global average)

#### Module 6: Outbound Transport (Scope 3)
```
Emissions = Cement/Clinker Shipped (tonnes) × Distance (km) × Transport Mode Factor (kgCO₂e/tonne·km)
```

| Mode | EF (kgCO₂e/tonne·km) | Source |
|---|---|---|
| Heavy truck (>32t) | 0.062 | DEFRA 2024 |
| Heavy truck (16–32t) | 0.096 | DEFRA 2024 |
| Train (freight) | 0.028 | DEFRA 2024 |
| Bulk ship (Handysize) | 0.011 | DEFRA 2024 |
| Bulk ship (Supramax) | 0.009 | DEFRA 2024 |

#### Module 7: Packaging Materials (Scope 3 — Packing Plants & Grinding Plants)
```
Emissions = Packaging Units × Packaging Material EF (kgCO₂e/unit)
```

| Packaging Type | Weight | EF (kgCO₂e/unit) | Source |
|---|---|---|---|
| Paper bag (50kg cement) | ~0.25 kg | 0.55 | Ecoinvent 3.9 |
| Paper bag (40kg cement) | ~0.20 kg | 0.44 | Ecoinvent 3.9 |
| PP woven bag (50kg) | ~0.10 kg | 0.38 | Ecoinvent 3.9 |
| Big bag / FIBC (1 tonne) | ~5 kg | 14.0 | Ecoinvent 3.9 |
| Bulk dispatch | 0 | 0 | — |

#### Module 8: Business Travel (Scope 3)
```
Emissions = Distance (km) × Transport Mode Factor (kgCO₂e/km/passenger)
```
Same as Emitly (IT version) — modes: short-haul flight, long-haul flight, train, car.

#### Module 9: Employee Commuting (Scope 3)
```
Emissions = Employees × Avg Distance (km/day) × Working Days × Mode Factor × 2
```
Same as original — multiply by 2 for return trip.

---

## 📊 Cement-Specific Intensity Metrics

The application must support and display these intensity metrics alongside absolute figures:

| Metric | Formula | Unit | Industry Benchmark |
|---|---|---|---|
| Specific process emissions | Process CO₂ / Clinker produced | kgCO₂/t clinker | 490–540 |
| Specific thermal energy | Heat input / Clinker produced | GJ/t clinker | 3.0–3.7 (modern kiln) |
| Specific electrical energy | kWh / Cement produced | kWh/t cement | 90–120 |
| Clinker-to-cement ratio | Clinker used / Cement produced | % | 65–90% |
| Net CO₂ per tonne cement | Total Scope 1+2 / Cement produced | kgCO₂e/t cement | GNR 2022: ~600 |

> **Agent Rule**: Clinker-to-cement ratio is a **strategic decarbonization lever** — lower ratio means more supplementary cementitious materials (SCMs) replacing clinker. Display it prominently on the dashboard.

---

## 🗄️ Data Models

### Core Entities

#### `Company` (extended for cement)
```json
{
  "id": "uuid",
  "name": "string",
  "facility_type": "cement_plant | grinding_plant | packing_plant",
  "country": "string",
  "region": "string",
  "grid_region": "java_bali | sumatra | kalimantan | national",
  "reporting_year": "integer",
  "headcount": "integer",
  "annual_cement_capacity_tonnes": "float",
  "annual_clinker_capacity_tonnes": "float"
}
```

#### `ProductionData`
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "period_start": "date",
  "period_end": "date",
  "clinker_produced_tonnes": "float",
  "clinker_purchased_tonnes": "float",
  "cement_produced_tonnes": "float",
  "cement_dispatched_tonnes": "float",
  "clinker_to_cement_ratio": "float",
  "notes": "string"
}
```

#### `EmissionEntry` (extended)
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "scope": "1 | 2 | 3",
  "category": "string",
  "sub_category": "string",
  "activity_data": "float",
  "activity_unit": "string",
  "emission_factor": "float",
  "emission_factor_unit": "kgCO2e/unit",
  "emission_factor_source": "string",
  "total_emissions_kgco2e": "float",
  "biogenic_co2_kgco2": "float",
  "period_start": "date",
  "period_end": "date",
  "plant_area": "string",
  "data_quality": "measured | estimated | calculated",
  "calculation_method": "string",
  "notes": "string",
  "created_at": "timestamp"
}
```

#### `EmissionFactor`
```json
{
  "id": "uuid",
  "category": "string",
  "sub_category": "string",
  "factor_value": "float",
  "unit": "string",
  "source": "IPCC | WBCSD_CSI | GNR | DEFRA | EPA | PLN | custom",
  "region": "string",
  "year": "integer",
  "applicable_facility_types": ["cement_plant", "grinding_plant", "packing_plant"]
}
```

#### `Report`
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "report_period": "string",
  "period_start": "date",
  "period_end": "date",
  "total_scope1_process": "float",
  "total_scope1_combustion": "float",
  "total_scope1_mobile": "float",
  "total_scope1_fugitive": "float",
  "total_scope1": "float",
  "total_scope2_lb": "float",
  "total_scope2_mb": "float",
  "total_scope3": "float",
  "total_emissions": "float",
  "biogenic_co2_total": "float",
  "unit": "tCO2e",
  "specific_emissions_per_tonne_cement": "float",
  "specific_emissions_per_tonne_clinker": "float",
  "clinker_to_cement_ratio": "float",
  "generated_at": "timestamp",
  "status": "draft | final"
}
```

> **Agent Rule**: Always store raw `activity_data` and `emission_factor` separately. Track `biogenic_co2` separately — it is excluded from totals but must be disclosed. Scope 1 must be broken down by sub-type (process, combustion, mobile, fugitive).

---

## 🖥️ Features & Pages

### Required Features (MVP)

- [ ] **Dashboard** — Total emissions by scope, clinker-to-cement ratio, specific emissions intensity, monthly trend
- [ ] **Facility Setup** — Company/facility profile with type, capacity, and grid region
- [ ] **Data Entry** — Facility-type-aware forms (Cement Plant shows kiln fields; Grinding Plant shows clinker import fields; Packing Plant shows packaging fields)
- [ ] **Production Log** — Monthly clinker/cement production data entry (used for intensity metrics)
- [ ] **Emission Factor Library** — Cement-specific reference values with source citations
- [ ] **Report Generator** — Annual/quarterly summary with scope breakdown, intensity metrics, exportable as PDF + CSV
- [ ] **Data Quality Indicator** — Flag entries as measured / estimated / calculated

### Nice-to-Have (Post-MVP)
- [ ] **Multi-facility support** — A cement group may have 1 cement plant + multiple grinding/packing plants
- [ ] **Clinker allocation** — Allocate clinker carbon between dispatch to grinding plants vs own cement production
- [ ] **Alternative fuel tracker** — Track % thermal substitution rate (TSR) over time
- [ ] **Decarbonization pathway** — Set reduction targets, model SCM substitution scenarios
- [ ] **Benchmarking** — Compare against GNR / GCCA cement sector averages
- [ ] **Biogenic CO₂ separate reporting** — Full disclosure including biogenic from alternative fuels

---

## 📏 Units & Conversion Rules

| Metric | Unit |
|---|---|
| Primary output unit | **tCO₂e** (tonnes CO₂ equivalent) |
| Internal calculation unit | **kgCO₂e** |
| Clinker / Cement production | **tonnes** |
| Energy / Fuel heat value | **GJ** or **kWh** |
| Fuel mass | **tonnes** |
| Liquid fuel volume | **liters** |
| Electricity | **kWh** or **MWh** |
| Distance | **km** |
| Intensity ratio | **kgCO₂e/tonne** |

> **Agent Rule**: All user inputs allow flexible unit entry. Always convert to **kgCO₂e internally** before storing. Display results in **tCO₂e** on reports and dashboards.

### GWP Values (AR6, IPCC 2021)
| Gas | GWP-100 |
|---|---|
| CO₂ | 1 |
| CH₄ | 29.8 |
| N₂O | 273 |
| SF₆ | 25,200 |
| HFCs (R-410A) | 2,088 |

---

## ✅ Data Quality & Validation Rules

1. **No negative values** — Emission values and activity data must be ≥ 0
2. **Date range validation** — `period_end` must be after `period_start`
3. **Required fields** — scope, category, activity_data, activity_unit, emission_factor_source, facility_type
4. **Facility type gating** — Process emissions (calcination) only allowed for `cement_plant` facility type
5. **Kiln fuel fields** — Only enabled for `cement_plant` and `grinding_plant` (dryers)
6. **Unit consistency** — Validate that activity_unit matches the selected emission factor unit
7. **Clinker-to-cement ratio bounds** — Ratio must be between 0.50 and 1.00 (50–100%)
8. **Outlier warning** — Flag entries >3× the historical average for the same category (warn, don't block)
9. **Data quality tagging** — Every entry must be tagged: `measured`, `estimated`, or `calculated`
10. **Emission factor versioning** — Track which version/year of emission factors was used
11. **Biogenic CO₂ separation** — Alternative fuel entries must declare biogenic vs fossil fraction

---

## 🔒 Security & Privacy Rules

- Store company/plant data in isolated schemas or separate databases (multi-tenant ready)
- No PII of individual employees should be stored — only aggregated commute data
- Emission factor library is read-only for end users
- All exports must include a disclaimer: *"This report is generated based on user-provided activity data and industry-standard emission factors. It has not been independently verified and should not be used for regulatory reporting without review by a certified carbon accountant or third-party verifier."*
- API keys for any third-party integrations must be stored in environment variables, never hardcoded

---

## 📄 Report Output Requirements

Every generated report must include:

1. **Cover page** — Company/plant name, facility type, reporting period, report date, methodology statement
2. **Executive Summary** — Total emissions in tCO₂e, specific emissions per tonne cement, YoY comparison if available
3. **Scope Breakdown** — Scope 1 (further split: process / combustion / mobile / fugitive), Scope 2, Scope 3
4. **Category Detail Table** — All emission categories with activity data, factors, and totals
5. **Top 5 Hotspots** — Highest emitting categories with % contribution
6. **Intensity Metrics** — kgCO₂e/t cement, kgCO₂e/t clinker, clinker-to-cement ratio, specific electricity use
7. **Data Quality Summary** — Breakdown of measured vs. estimated vs. calculated entries
8. **Biogenic CO₂ Disclosure** — Total biogenic CO₂ (excluded from totals, disclosed separately)
9. **Methodology Notes** — Emission factor sources, GWP values used, calculation methods (Method A/B for clinker), any assumptions
10. **Disclaimer** — Standard unverified data disclaimer

---

## 🚦 Development Rules for Agent

### DO ✅
- Follow GHG Protocol Corporate Accounting and Reporting Standard
- Follow WBCSD CSI / GCCA Cement CO₂ and Energy Protocol for cement-specific modules
- Use `kgCO₂e` for internal storage, `tCO₂e` for display
- Gate emission category availability by `facility_type` — cement plant / grinding plant / packing plant
- Separate emission factor data from application logic (keep factors in `/data/emission_factors/`)
- Write modular, testable calculation functions
- Include unit tests for all emission calculation modules, especially the clinker calcination module
- Comment all emission factor values with their source and year
- Use enum/constants for scope categories — never free-text strings
- Track biogenic CO₂ separately from fossil CO₂ for alternative fuels
- Display clinker-to-cement ratio prominently as a decarbonization KPI
- Provide CSV import templates for bulk production data entry

### DON'T ❌
- Show clinker calcination input fields to Grinding Plants or Packing Plants
- Show kiln fuel consumption fields to Packing Plants
- Hardcode emission factors inside UI components
- Mix Scope 2 market-based and location-based values in the same total without clear separation
- Assume a single global grid emission factor — always use the Indonesian regional grid factor by default
- Skip data quality tagging
- Include biogenic CO₂ in the GHG inventory total (disclose separately)
- Generate reports without methodology notes and a disclaimer section
- Omit clinker-to-cement ratio from reports and the dashboard

---

## 📚 Reference Standards & Resources

| Standard / Tool | Purpose |
|---|---|
| GHG Protocol Corporate Standard | Core accounting framework |
| GHG Protocol Scope 3 Standard | Scope 3 category definitions |
| WBCSD CSI / GCCA Cement CO₂ Protocol | Cement-specific calculation methodology (process emissions, clinker EF, biogenic rules) |
| GNR (Getting the Numbers Right) | Cement sector emissions benchmarking database (GCCA) |
| IPCC 2006 Guidelines Vol. 3 Ch. 2 | Process emission factors for clinker production |
| IPCC AR6 (2021) GWP-100 | Global Warming Potential values |
| PLN RUPTL 2023 | Indonesian grid emission factors by region |
| DEFRA GHG Conversion Factors (annual) | Fuel combustion, transport, and other factors |
| Ecoinvent v3.9 | Lifecycle data for packaging materials |
| ISO 14064-1 | GHG inventory verification standard |
| ISO 14067 | Carbon footprint of products (optional, for product-level reporting) |
| SNI / TKDN regulations | Indonesian standards for cement and environmental compliance |

---

## 🗺️ Build Sequence (Recommended)

Follow this order to build the MVP:

```
Phase 1 — Foundation
  1. Database schema setup (including ProductionData and facility_type on Company)
  2. Emission factor library (clinker factors, fuel factors, grid factors, transport factors)
  3. Core calculation engine with all 9 modules
  4. Unit tests for calculation engine (especially clinker modules)

Phase 2 — Backend API
  5. CRUD endpoints for Company (with facility_type)
  6. CRUD endpoints for ProductionData
  7. CRUD endpoints for EmissionEntry (facility-type-aware validation)
  8. Report generation endpoint (with intensity metrics)
  9. Emission factor lookup endpoint

Phase 3 — Frontend
  10. Dashboard page (scope breakdown, intensity KPIs, clinker-to-cement ratio card)
  11. Facility type-aware data entry forms
  12. Production log page
  13. Report viewer + export (PDF, CSV)

Phase 4 — Polish
  14. Facility-type gating validation and user feedback
  15. Data quality indicators
  16. Emission factor source citations in UI
  17. Biogenic CO₂ separate disclosure section
  18. User documentation
```

---

*Last updated: 2026 | Maintained by: Lunavia / Kilnify Project*
*Follow GHG Protocol and WBCSD CSI Cement CO₂ Protocol. Verify with a certified carbon accountant before external reporting.*
