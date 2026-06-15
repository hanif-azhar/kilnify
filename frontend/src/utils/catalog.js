// Emission category catalog, gated by facility type.
// Mirrors backend FACILITY_RESTRICTED_CATEGORIES — the backend re-validates,
// this just controls which options the form shows.

// When true, Kilnify is a Scope 3-only tool: Data Entry only offers Scope 3
// categories and the dashboard hides Scope 1/2 figures. Mirror of the backend
// SCOPE3_ONLY flag in constants.py — keep the two in sync.
export const SCOPE3_ONLY = true;

export const FACILITY_TYPES = [
  { value: "cement_plant", label: "Cement Plant (Integrated)" },
  { value: "grinding_plant", label: "Grinding Plant" },
  { value: "packing_plant", label: "Packing Plant" },
];

export const GRID_REGIONS = [
  { value: "java_bali", label: "Java-Bali (0.850)" },
  { value: "sumatra", label: "Sumatra (0.790)" },
  { value: "kalimantan", label: "Kalimantan (0.920)" },
  { value: "national", label: "National avg (0.870)" },
];

export const DATA_QUALITY = ["measured", "estimated", "calculated"];

// Each category: scope, sub-types with default EF + unit, and which facility
// types may use it. `all` = available to every facility type.
export const CATEGORIES = [
  {
    key: "clinker_calcination",
    label: "Clinker Calcination (Process)",
    scope: "1",
    facilities: ["cement_plant"],
    activityUnit: "tonnes_clinker",
    efUnit: "kgCO2e/tonne_clinker",
    subTypes: [
      { value: "method_a", label: "Method A — default EF", ef: 525.0, source: "WBCSD CSI 2022 / GNR" },
      { value: "method_b", label: "Method B — CaO content based", ef: null, source: "IPCC 2006 (stoichiometry)" },
    ],
  },
  {
    key: "kiln_fuel",
    label: "Kiln / Dryer Fuel Combustion",
    scope: "1",
    facilities: ["cement_plant", "grinding_plant"],
    activityUnit: "tonnes_fuel",
    efUnit: "kgCO2e/tonne_fuel",
    biogenic: true,
    subTypes: [
      { value: "coal", label: "Coal", ef: 2540.0, source: "IPCC 2006" },
      { value: "petcoke", label: "Petroleum coke", ef: 3150.0, source: "IPCC 2006" },
      { value: "natural_gas", label: "Natural gas", ef: 1900.0, source: "IPCC 2006" },
      { value: "hfo", label: "Heavy fuel oil", ef: 3150.0, source: "IPCC 2006" },
      { value: "diesel", label: "Diesel", ef: 2680.0, source: "DEFRA 2024" },
      { value: "rdf", label: "RDF (fossil fraction)", ef: 495.0, source: "Variable" },
    ],
  },
  {
    key: "mobile_equipment",
    label: "On-Site Mobile Equipment",
    scope: "1",
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "liters",
    efUnit: "kgCO2e/liter",
    subTypes: [
      { value: "diesel", label: "Diesel", ef: 2.68, source: "DEFRA 2024" },
      { value: "petrol", label: "Petrol", ef: 2.31, source: "DEFRA 2024" },
    ],
  },
  {
    key: "refrigerants",
    label: "Refrigerant Leaks (Fugitive)",
    scope: "1",
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "kg",
    efUnit: "kgCO2e/kg (GWP-100)",
    subTypes: [
      { value: "r410a", label: "R-410A", ef: 2088.0, source: "IPCC AR6 2021" },
      { value: "r32", label: "R-32", ef: 771.0, source: "IPCC AR6 2021" },
      { value: "r134a", label: "R-134a", ef: 1430.0, source: "IPCC AR6 2021" },
    ],
  },
  {
    key: "electricity",
    label: "Purchased Electricity (Grid)",
    scope: "2",
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "kWh",
    efUnit: "kgCO2e/kWh",
    subTypes: [
      { value: "java_bali", label: "Java-Bali grid", ef: 0.85, source: "PLN RUPTL 2023" },
      { value: "sumatra", label: "Sumatra grid", ef: 0.79, source: "PLN RUPTL 2023" },
      { value: "kalimantan", label: "Kalimantan grid", ef: 0.92, source: "PLN RUPTL 2023" },
      { value: "national", label: "National avg", ef: 0.87, source: "MEMR / IEA 2023" },
    ],
  },
  {
    key: "purchased_clinker_upstream",
    label: "Purchased Clinker — Upstream",
    scope: "3",
    ghgCategory: 1,
    facilities: ["grinding_plant"],
    activityUnit: "tonnes_clinker",
    efUnit: "kgCO2e/tonne_clinker",
    subTypes: [{ value: "supplier_default", label: "GNR default", ef: 842.0, source: "GNR 2022" }],
  },
  {
    key: "transport_outbound",
    label: "Outbound Transport (Downstream)",
    scope: "3",
    ghgCategory: 9,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "tonne_km",
    efUnit: "kgCO2e/tonne_km",
    subTypes: [
      { value: "truck_heavy_over_32t", label: "Heavy truck >32t", ef: 0.062, source: "DEFRA 2024" },
      { value: "train_freight", label: "Freight train", ef: 0.028, source: "DEFRA 2024" },
      { value: "ship_handysize", label: "Bulk ship (Handysize)", ef: 0.011, source: "DEFRA 2024" },
      { value: "ship_supramax", label: "Bulk ship (Supramax)", ef: 0.009, source: "DEFRA 2024" },
    ],
  },
  {
    key: "purchased_goods",
    label: "Purchased Goods & Services",
    scope: "3",
    ghgCategory: 1,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "tonnes",
    efUnit: "kgCO2e/tonne",
    subTypes: [
      { value: "gypsum", label: "Gypsum", ef: 14.0, source: "Ecoinvent 3.9" },
      { value: "limestone_additive", label: "Limestone filler", ef: 6.0, source: "Ecoinvent 3.9" },
      { value: "fly_ash_scm", label: "Fly ash (SCM)", ef: 4.0, source: "Ecoinvent 3.9" },
      { value: "ggbfs_slag", label: "GGBFS slag (SCM)", ef: 80.0, source: "Ecoinvent 3.9" },
      { value: "natural_pozzolan", label: "Natural pozzolan (SCM)", ef: 7.0, source: "Ecoinvent 3.9" },
      { value: "grinding_aid", label: "Grinding aid", ef: 1900.0, source: "Ecoinvent 3.9" },
      { value: "refractory_brick", label: "Refractory brick", ef: 1800.0, source: "Ecoinvent 3.9" },
    ],
  },
  {
    key: "capital_goods",
    label: "Capital Goods",
    scope: "3",
    ghgCategory: 2,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "USD",
    efUnit: "kgCO2e/USD",
    subTypes: [
      { value: "machinery_spend", label: "Machinery (spend-based)", ef: 0.4, source: "EXIOBASE EEIO" },
      { value: "steel_construction", label: "Structural steel", ef: 2400.0, source: "worldsteel 2022", activityUnit: "tonnes", efUnit: "kgCO2e/tonne" },
      { value: "vehicles_spend", label: "Vehicles (spend-based)", ef: 0.35, source: "EXIOBASE EEIO" },
    ],
  },
  {
    key: "fuel_energy_related",
    label: "Fuel & Energy-Related Activities",
    scope: "3",
    ghgCategory: 3,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "kWh",
    efUnit: "kgCO2e/kWh",
    subTypes: [
      { value: "electricity_td_loss", label: "Grid T&D losses", ef: 0.085, source: "DEFRA 2024 WTT" },
      { value: "wtt_coal", label: "Coal well-to-tank", ef: 200.0, source: "DEFRA 2024 WTT", activityUnit: "tonnes", efUnit: "kgCO2e/tonne" },
      { value: "wtt_diesel", label: "Diesel well-to-tank", ef: 0.62, source: "DEFRA 2024 WTT", activityUnit: "liters", efUnit: "kgCO2e/liter" },
      { value: "wtt_natural_gas", label: "Natural gas well-to-tank", ef: 350.0, source: "DEFRA 2024 WTT", activityUnit: "tonnes", efUnit: "kgCO2e/tonne" },
    ],
  },
  {
    key: "upstream_transport",
    label: "Upstream Transport (Inbound)",
    scope: "3",
    ghgCategory: 4,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "tonne_km",
    efUnit: "kgCO2e/tonne_km",
    subTypes: [
      { value: "truck_heavy_over_32t", label: "Heavy truck >32t", ef: 0.062, source: "DEFRA 2024" },
      { value: "train_freight", label: "Freight train", ef: 0.028, source: "DEFRA 2024" },
      { value: "ship_handysize", label: "Bulk ship (Handysize)", ef: 0.011, source: "DEFRA 2024" },
    ],
  },
  {
    key: "waste_generated",
    label: "Waste Generated in Operations",
    scope: "3",
    ghgCategory: 5,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "tonnes",
    efUnit: "kgCO2e/tonne",
    subTypes: [
      { value: "ckd_landfill", label: "Cement kiln dust → landfill", ef: 20.0, source: "DEFRA 2024" },
      { value: "general_waste_landfill", label: "General waste → landfill", ef: 450.0, source: "DEFRA 2024" },
      { value: "wastewater_treatment", label: "Wastewater treatment", ef: 0.7, source: "DEFRA 2024", activityUnit: "m3", efUnit: "kgCO2e/m3" },
    ],
  },
  {
    key: "processing_sold_products",
    label: "Processing of Sold Products",
    scope: "3",
    ghgCategory: 10,
    facilities: ["cement_plant"],
    activityUnit: "tonnes_clinker",
    efUnit: "kgCO2e/tonne_clinker",
    subTypes: [
      { value: "third_party_grinding", label: "Third-party grinding of sold clinker", ef: 34.0, source: "Derived (grinding electricity)" },
    ],
  },
  {
    key: "use_sold_products",
    label: "Use of Sold Products",
    scope: "3",
    ghgCategory: 11,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "tonnes",
    efUnit: "kgCO2e/tonne",
    subTypes: [
      { value: "cement_inert_use", label: "Cement (inert in use)", ef: 0.0, source: "GHG Protocol Scope 3" },
    ],
  },
  {
    key: "packaging",
    label: "Packaging Materials",
    scope: "3",
    ghgCategory: 1,
    facilities: ["grinding_plant", "packing_plant"],
    activityUnit: "units",
    efUnit: "kgCO2e/unit",
    subTypes: [
      { value: "paper_bag_50kg", label: "Paper bag 50kg", ef: 0.55, source: "Ecoinvent 3.9" },
      { value: "pp_bag_50kg", label: "PP woven bag 50kg", ef: 0.38, source: "Ecoinvent 3.9" },
      { value: "big_bag_1t", label: "Big bag / FIBC 1t", ef: 14.0, source: "Ecoinvent 3.9" },
    ],
  },
  {
    key: "business_travel",
    label: "Business Travel",
    scope: "3",
    ghgCategory: 6,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "passenger_km",
    efUnit: "kgCO2e/passenger_km",
    subTypes: [
      { value: "flight_short_haul", label: "Short-haul flight", ef: 0.255, source: "DEFRA 2024" },
      { value: "flight_long_haul", label: "Long-haul flight", ef: 0.195, source: "DEFRA 2024" },
      { value: "train", label: "Train", ef: 0.041, source: "DEFRA 2024" },
      { value: "car_petrol", label: "Car (petrol)", ef: 0.192, source: "DEFRA 2024" },
    ],
  },
  {
    key: "employee_commuting",
    label: "Employee Commuting",
    scope: "3",
    ghgCategory: 7,
    facilities: ["cement_plant", "grinding_plant", "packing_plant"],
    activityUnit: "km",
    efUnit: "kgCO2e/km",
    subTypes: [
      { value: "car_petrol", label: "Car (petrol)", ef: 0.192, source: "DEFRA 2024" },
      { value: "car_ev", label: "Car (EV)", ef: 0.073, source: "DEFRA 2024" },
      { value: "motorcycle", label: "Motorcycle", ef: 0.113, source: "DEFRA 2024" },
      { value: "public_transit", label: "Public transit", ef: 0.089, source: "DEFRA 2024" },
    ],
  },
];

export function categoriesForFacility(facilityType) {
  const scoped = SCOPE3_ONLY ? CATEGORIES.filter((c) => c.scope === "3") : CATEGORIES;
  if (!facilityType) return scoped;
  return scoped.filter((c) => c.facilities.includes(facilityType));
}

export const facilityLabel = (v) =>
  FACILITY_TYPES.find((f) => f.value === v)?.label || v;
