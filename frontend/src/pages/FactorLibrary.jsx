import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import FormSelect from "../components/FormSelect.jsx";
import { useCompany } from "../CompanyContext.jsx";
import { api } from "../utils/api.js";
import { FACILITY_TYPES } from "../utils/catalog.js";

const EMPTY_FORM = {
  category: "", sub_category: "", scope: "3", factor_value: "", unit: "",
  activity_unit: "", source: "", year: "", applicable_facility_types: [], notes: "",
  global: false,
};

export default function FactorLibrary() {
  const { selectedId } = useCompany();
  const [factors, setFactors] = useState([]);
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("all");
  const [facilityType, setFacilityType] = useState("all");
  const [search, setSearch] = useState("");

  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);

  function loadCategories() {
    api.factorCategories().then(setCategories).catch(() => {});
  }
  useEffect(loadCategories, [factors.length]);

  function loadFactors() {
    api
      .listFactors({
        category: category === "all" ? "" : category,
        facility_type: facilityType === "all" ? "" : facilityType,
        search,
        company_id: selectedId,
      })
      .then(setFactors)
      .catch((e) => toast.error(e.message));
  }
  useEffect(loadFactors, [category, facilityType, search, selectedId]);

  const setField = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  function toggleFacility(value) {
    setForm((f) => {
      const has = f.applicable_facility_types.includes(value);
      return {
        ...f,
        applicable_facility_types: has
          ? f.applicable_facility_types.filter((t) => t !== value)
          : [...f.applicable_facility_types, value],
      };
    });
  }

  function openCreate() {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setOpen(true);
  }

  function openEdit(f) {
    setEditingId(f.id);
    setForm({
      category: f.category || "",
      sub_category: f.sub_category || "",
      scope: f.scope || "3",
      factor_value: f.factor_value ?? "",
      unit: f.unit || "",
      activity_unit: f.activity_unit || "",
      source: f.source || "",
      year: f.year ?? "",
      applicable_facility_types: f.applicable_facility_types || [],
      notes: f.notes || "",
      global: false,
    });
    setOpen(true);
  }

  async function save(e) {
    e.preventDefault();
    if (!form.category || form.factor_value === "") {
      toast.error("Category and factor value are required.");
      return;
    }
    const payload = {
      company_id: form.global ? null : selectedId || null,
      scope: form.scope || null,
      category: form.category.trim(),
      sub_category: form.sub_category.trim() || null,
      factor_value: Number(form.factor_value),
      unit: form.unit.trim() || null,
      activity_unit: form.activity_unit.trim() || null,
      source: form.source.trim() || null,
      year: form.year === "" ? null : Number(form.year),
      applicable_facility_types: form.applicable_facility_types,
      notes: form.notes.trim() || null,
    };
    try {
      if (editingId) {
        await api.updateCustomFactor(editingId, payload);
        toast.success("Factor updated.");
      } else {
        await api.createCustomFactor(payload);
        toast.success("Custom factor added.");
      }
      setOpen(false);
      loadFactors();
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function remove(id) {
    try {
      await api.deleteCustomFactor(id);
      toast.success("Factor deleted.");
      loadFactors();
    } catch (err) {
      toast.error(err.message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Emission Factor Library</h1>
          <p className="text-sm text-muted-foreground">
            Built-in factors are read-only reference values with source citations. Add your own
            plant-specific or supplier-certified factors — they appear here and become selectable in
            Data Entry.
          </p>
        </div>
        <Button onClick={openCreate}>+ Add factor</Button>
      </div>

      <Card>
        <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="space-y-1.5">
            <Label>Category</Label>
            <FormSelect
              value={category}
              onValueChange={setCategory}
              options={[{ value: "all", label: "All" }, ...categories.map((c) => ({ value: c, label: c }))]}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Facility type</Label>
            <FormSelect
              value={facilityType}
              onValueChange={setFacilityType}
              options={[{ value: "all", label: "All" }, ...FACILITY_TYPES]}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="search">Search</Label>
            <Input id="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="coal, DEFRA, java…" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead>Sub-category</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead>Unit</TableHead>
                <TableHead>Facilities</TableHead>
                <TableHead>Source</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {factors.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-muted-foreground">No factors match.</TableCell>
                </TableRow>
              )}
              {factors.map((f, i) => (
                <TableRow key={f.id || `${f.category}-${f.sub_category}-${i}`}>
                  <TableCell>
                    {f.category}
                    {f.editable && <Badge variant="secondary" className="ml-2">custom</Badge>}
                  </TableCell>
                  <TableCell>{f.sub_category}</TableCell>
                  <TableCell className="text-right font-medium">
                    {f.factor_value == null ? "formula" : f.factor_value}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{f.unit}</TableCell>
                  <TableCell className="text-xs">
                    {(f.applicable_facility_types || []).length === 0
                      ? (f.editable ? "all" : "")
                      : (f.applicable_facility_types || []).map((t) => t.replace("_plant", "")).join(", ")}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {f.source}{f.year ? ` (${f.year})` : ""}
                  </TableCell>
                  <TableCell className="text-right whitespace-nowrap">
                    {f.editable && (
                      <>
                        <Button variant="ghost" size="sm" className="h-7" onClick={() => openEdit(f)}>edit</Button>
                        <Button variant="ghost" size="sm" className="h-7 text-destructive hover:text-destructive" onClick={() => remove(f.id)}>delete</Button>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit custom factor" : "Add custom factor"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={save} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="cf-cat">Category *</Label>
                <Input id="cf-cat" value={form.category} onChange={(e) => setField("category", e.target.value)} placeholder="e.g. purchased_goods" required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="cf-sub">Sub-category</Label>
                <Input id="cf-sub" value={form.sub_category} onChange={(e) => setField("sub_category", e.target.value)} placeholder="e.g. supplier_x_clinker" />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label>Scope</Label>
                <FormSelect value={form.scope} onValueChange={(v) => setField("scope", v)} options={["1", "2", "3"]} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="cf-val">Factor value *</Label>
                <Input id="cf-val" type="number" step="any" min="0" value={form.factor_value} onChange={(e) => setField("factor_value", e.target.value)} required />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="cf-year">Year</Label>
                <Input id="cf-year" type="number" value={form.year} onChange={(e) => setField("year", e.target.value)} placeholder="2025" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="cf-unit">EF unit</Label>
                <Input id="cf-unit" value={form.unit} onChange={(e) => setField("unit", e.target.value)} placeholder="kgCO2e/tonne" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="cf-au">Activity unit</Label>
                <Input id="cf-au" value={form.activity_unit} onChange={(e) => setField("activity_unit", e.target.value)} placeholder="tonnes" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cf-src">Source</Label>
              <Input id="cf-src" value={form.source} onChange={(e) => setField("source", e.target.value)} placeholder="Supplier EPD 2025" />
            </div>
            <div className="space-y-1.5">
              <Label>Applicable facilities (none = all)</Label>
              <div className="flex flex-wrap gap-3">
                {FACILITY_TYPES.map((ft) => (
                  <label key={ft.value} className="flex items-center gap-1.5 text-sm">
                    <input
                      type="checkbox"
                      checked={form.applicable_facility_types.includes(ft.value)}
                      onChange={() => toggleFacility(ft.value)}
                    />
                    {ft.label}
                  </label>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cf-notes">Notes</Label>
              <Input id="cf-notes" value={form.notes} onChange={(e) => setField("notes", e.target.value)} />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.global} onChange={(e) => setField("global", e.target.checked)} />
              Make global (available to all facilities, not just the selected one)
            </label>
            {!form.global && !selectedId && (
              <p className="text-xs text-amber-600">No facility selected — this factor will be saved as global.</p>
            )}
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
              <Button type="submit">{editingId ? "Save changes" : "Add factor"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
