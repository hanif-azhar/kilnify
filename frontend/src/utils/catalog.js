// Emission category catalog, gated by facility type.
// Mirrors backend FACILITY_RESTRICTED_CATEGORIES — the backend re-validates,
// this just controls which options the form shows.

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
    facilities: ["grinding_plant"],
    activityUnit: "tonnes_clinker",
    efUnit: "kgCO2e/tonne_clinker",
    subTypes: [{ value: "supplier_default", label: "GNR default", ef: 842.0, source: "GNR 2022" }],
  },
  {
    key: "transport_outbound",
    label: "Outbound Transport",
    scope: "3",
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
    key: "packaging",
    label: "Packaging Materials",
    scope: "3",
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
  if (!facilityType) return CATEGORIES;
  return CATEGORIES.filter((c) => c.facilities.includes(facilityType));
}

export const facilityLabel = (v) =>
  FACILITY_TYPES.find((f) => f.value === v)?.label || v;
