import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import FormSelect from "../components/FormSelect.jsx";
import { useCompany } from "../CompanyContext.jsx";
import { api } from "../utils/api.js";
import { categoriesForFacility, DATA_QUALITY, SCOPE3_ONLY } from "../utils/catalog.js";
import DataQualityBadge from "../components/DataQualityBadge.jsx";

// CaO/MgO stoichiometry for Method B (matches backend emission_calculator).
const CAO_STOICH = 0.785;
const MGO_STOICH = 1.092;
const CO2_CAO = 44 / 56;

export default function DataEntry() {
  const { selectedId, selected } = useCompany();
  const [customFactors, setCustomFactors] = useState([]);

  useEffect(() => {
    if (!selectedId) return;
    api.listCustomFactors(selectedId).then(setCustomFactors).catch(() => {});
  }, [selectedId]);

  // Catalog categories for this facility, with user-defined custom factors merged
  // in as extra sub-types (matching category) or as their own custom category.
  const categories = useMemo(() => {
    const facility = selected?.facility_type;
    const base = categoriesForFacility(facility).map((c) => ({ ...c, subTypes: [...c.subTypes] }));
    const byKey = Object.fromEntries(base.map((c) => [c.key, c]));
    const synthetic = {};

    for (const cf of customFactors) {
      // In Scope 3-only mode, ignore custom factors for other scopes.
      if (SCOPE3_ONLY && (cf.scope || "3") !== "3") continue;
      const facs = cf.applicable_facility_types || [];
      if (facility && facs.length > 0 && !facs.includes(facility)) continue;
      const sub = {
        value: cf.id,
        label: `${cf.sub_category || cf.category} (custom)`,
        ef: cf.factor_value,
        source: cf.source || "User-defined",
        activityUnit: cf.activity_unit || undefined,
        efUnit: cf.unit || undefined,
        custom: true,
        subCategoryName: cf.sub_category || null,
      };
      if (byKey[cf.category]) {
        byKey[cf.category].subTypes.push(sub);
      } else {
        if (!synthetic[cf.category]) {
          synthetic[cf.category] = {
            key: cf.category,
            label: `${cf.category} (custom)`,
            scope: cf.scope || "3",
            facilities: facility ? [facility] : [],
            activityUnit: cf.activity_unit || "units",
            efUnit: cf.unit || "kgCO2e/unit",
            subTypes: [],
            custom: true,
          };
        }
        synthetic[cf.category].subTypes.push(sub);
      }
    }
    return [...base, ...Object.values(synthetic)];
  }, [selected?.facility_type, customFactors]);

  const [categoryKey, setCategoryKey] = useState("");
  const [subType, setSubType] = useState("");
  const [activityData, setActivityData] = useState("");
  const [efOverride, setEfOverride] = useState("");
  const [biogenicFraction, setBiogenicFraction] = useState("");
  const [caoPct, setCaoPct] = useState("");
  const [mgoPct, setMgoPct] = useState("");
  const [dataQuality, setDataQuality] = useState("calculated");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [plantArea, setPlantArea] = useState("");
  const [notes, setNotes] = useState("");

  const [entries, setEntries] = useState([]);

  const category = categories.find((c) => c.key === categoryKey) || null;
  const sub = category?.subTypes.find((s) => s.value === subType) || null;
  const isMethodB = categoryKey === "clinker_calcination" && subType === "method_b";
  // Sub-types may override the category's units (e.g. capital goods in USD vs tonnes).
  const activeActivityUnit = sub?.activityUnit || category?.activityUnit;
  const activeEfUnit = sub?.efUnit || category?.efUnit;

  // Reset the form's category when facility changes (gating may remove it).
  useEffect(() => {
    setCategoryKey(categories[0]?.key || "");
  }, [categories]);

  useEffect(() => {
    setSubType(category?.subTypes[0]?.value || "");
  }, [categoryKey]);

  function loadEntries() {
    if (!selectedId) return;
    api.listEmissions(selectedId).then(setEntries).catch((e) => toast.error(e.message));
  }
  useEffect(loadEntries, [selectedId]);

  // Resolve the effective emission factor (override > Method B computed > catalog default).
  const effectiveEf = useMemo(() => {
    if (efOverride !== "") return Number(efOverride);
    if (isMethodB) {
      const cao = Number(caoPct) || 0;
      const mgo = Number(mgoPct) || 0;
      return ((cao * CAO_STOICH + mgo * MGO_STOICH) / 100) * CO2_CAO * 1000;
    }
    return sub?.ef ?? 0;
  }, [efOverride, isMethodB, caoPct, mgoPct, sub]);

  const previewKg = (Number(activityData) || 0) * (effectiveEf || 0);

  async function submit(e) {
    e.preventDefault();
    if (!category || !sub) return;
    try {
      const ef = effectiveEf;
      const biogenic =
        category.biogenic && biogenicFraction !== ""
          ? (Number(activityData) || 0) * ef * (Number(biogenicFraction) / 100)
          : 0;
      const payload = {
        company_id: selectedId,
        scope: category.scope,
        category: category.key,
        sub_category: sub.custom ? sub.subCategoryName : subType,
        activity_data: Number(activityData),
        activity_unit: activeActivityUnit,
        emission_factor: ef,
        emission_factor_unit: activeEfUnit,
        emission_factor_source: sub.source || (isMethodB ? "IPCC 2006 stoichiometry" : "custom"),
        biogenic_co2_kgco2: biogenic,
        period_start: periodStart,
        period_end: periodEnd,
        plant_area: plantArea || null,
        data_quality: dataQuality,
        calculation_method: sub.custom
          ? "Custom factor"
          : isMethodB
          ? "Method B — CaO content based"
          : sub.label,
        notes: notes || null,
      };
      const created = await api.createEmission(payload);
      if (created.warning) {
        toast.warning(created.warning, { duration: 8000 });
      } else {
        toast.success("Entry saved.");
      }
      setActivityData("");
      setEfOverride("");
      setBiogenicFraction("");
      setNotes("");
      loadEntries();
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function remove(id) {
    try {
      await api.deleteEmission(id);
      toast.success("Entry deleted.");
      loadEntries();
    } catch (err) {
      toast.error(err.message);
    }
  }

  if (!selectedId)
    return (
      <Card>
        <CardContent className="pt-6 text-muted-foreground">
          Add a facility first on the Facilities page.
        </CardContent>
      </Card>
    );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-1">Data Entry</h1>
        <p className="text-sm text-muted-foreground mb-4">
          {SCOPE3_ONLY
            ? `Scope 3 (value chain) categories only, filtered by facility type (${selected?.facility_type}).`
            : `Categories are filtered by facility type (${selected?.facility_type}). Process/kiln fields appear only where applicable.`}
        </p>
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={submit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Category</Label>
                  <FormSelect
                    value={categoryKey}
                    onValueChange={setCategoryKey}
                    options={categories.map((c) => ({ value: c.key, label: `Scope ${c.scope} · ${c.label}` }))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Sub-type</Label>
                  <FormSelect
                    value={subType}
                    onValueChange={setSubType}
                    options={(category?.subTypes || []).map((s) => ({ value: s.value, label: s.label }))}
                  />
                </div>
              </div>

              {isMethodB && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="cao">CaO content (%)</Label>
                    <Input id="cao" type="number" step="0.01" value={caoPct} onChange={(e) => setCaoPct(e.target.value)} placeholder="63–67" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="mgo">MgO content (%)</Label>
                    <Input id="mgo" type="number" step="0.01" value={mgoPct} onChange={(e) => setMgoPct(e.target.value)} placeholder="optional" />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="activity">Activity data ({activeActivityUnit})</Label>
                  <Input id="activity" type="number" step="any" min="0" value={activityData} onChange={(e) => setActivityData(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ef">
                    Emission factor {isMethodB ? "(computed)" : `(default ${sub?.ef ?? "—"})`}
                  </Label>
                  <Input
                    id="ef"
                    type="number"
                    step="any"
                    min="0"
                    placeholder={isMethodB ? effectiveEf.toFixed(2) : String(sub?.ef ?? "")}
                    value={efOverride}
                    onChange={(e) => setEfOverride(e.target.value)}
                    disabled={isMethodB}
                  />
                  <p className="text-xs text-muted-foreground">{activeEfUnit} · {sub?.source}</p>
                </div>
              </div>

              {category?.biogenic && (
                <div className="space-y-1.5">
                  <Label htmlFor="bio">Biogenic fraction (%) — excluded from total</Label>
                  <Input id="bio" type="number" min="0" max="100" value={biogenicFraction} onChange={(e) => setBiogenicFraction(e.target.value)} placeholder="e.g. 40 for RDF" />
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="ps">Period start</Label>
                  <Input id="ps" type="date" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="pe">Period end</Label>
                  <Input id="pe" type="date" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} required />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="area">Plant area</Label>
                  <Input id="area" value={plantArea} onChange={(e) => setPlantArea(e.target.value)} placeholder="Kiln, Cement Mill…" />
                </div>
                <div className="space-y-1.5">
                  <Label>Data quality</Label>
                  <FormSelect value={dataQuality} onValueChange={setDataQuality} options={DATA_QUALITY} />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="notes">Notes</Label>
                <Input id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
              </div>

              <div className="flex items-center justify-between bg-kiln-50 rounded-lg p-3">
                <span className="text-sm text-muted-foreground">Live preview</span>
                <span className="font-bold text-primary">
                  {(previewKg / 1000).toLocaleString(undefined, { maximumFractionDigits: 3 })} tCO₂e
                  <span className="text-xs font-normal text-muted-foreground ml-1">({previewKg.toLocaleString()} kg)</span>
                </span>
              </div>

              <Button type="submit">Save entry</Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-foreground mb-4">Entries for this facility</h2>
        <Card>
          <CardContent className="pt-6">
            {entries.length === 0 ? (
              <p className="text-sm text-muted-foreground">No entries yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Scope</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">tCO₂e</TableHead>
                    <TableHead>Quality</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell>{e.scope}</TableCell>
                      <TableCell>
                        {e.category}
                        <div className="text-xs text-muted-foreground">{e.sub_category}</div>
                      </TableCell>
                      <TableCell className="text-right">
                        {(e.total_emissions_kgco2e / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                      </TableCell>
                      <TableCell><DataQualityBadge quality={e.data_quality} /></TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive h-7" onClick={() => remove(e.id)}>
                          delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
