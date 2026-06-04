import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import FormSelect from "../components/FormSelect.jsx";
import { useCompany } from "../CompanyContext.jsx";
import { api } from "../utils/api.js";
import { FACILITY_TYPES, GRID_REGIONS } from "../utils/catalog.js";
import FacilityTypeBadge from "../components/FacilityTypeBadge.jsx";

const EMPTY = {
  name: "",
  facility_type: "cement_plant",
  country: "Indonesia",
  region: "",
  grid_region: "national",
  reporting_year: new Date().getFullYear(),
  headcount: "",
  annual_cement_capacity_tonnes: "",
  annual_clinker_capacity_tonnes: "",
};

export default function Facilities() {
  const { companies, refresh, setSelectedId } = useCompany();
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const setVal = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        ...form,
        reporting_year: form.reporting_year ? Number(form.reporting_year) : null,
        headcount: form.headcount ? Number(form.headcount) : null,
        annual_cement_capacity_tonnes: form.annual_cement_capacity_tonnes
          ? Number(form.annual_cement_capacity_tonnes)
          : null,
        annual_clinker_capacity_tonnes: form.annual_clinker_capacity_tonnes
          ? Number(form.annual_clinker_capacity_tonnes)
          : null,
      };
      const created = await api.createCompany(payload);
      await refresh();
      setSelectedId(created.id);
      setForm(EMPTY);
      toast.success(`Facility "${created.name}" added.`);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(id, name) {
    if (!confirm(`Delete "${name}" and all its data?`)) return;
    try {
      await api.deleteCompany(id);
      await refresh();
      toast.success("Facility deleted.");
    } catch (err) {
      toast.error(err.message);
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-4">Facility Setup</h1>
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="name">Facility / plant name</Label>
                <Input id="name" value={form.name} onChange={set("name")} required />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Facility type</Label>
                  <FormSelect value={form.facility_type} onValueChange={setVal("facility_type")} options={FACILITY_TYPES} />
                </div>
                <div className="space-y-1.5">
                  <Label>Grid region</Label>
                  <FormSelect value={form.grid_region} onValueChange={setVal("grid_region")} options={GRID_REGIONS} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="country">Country</Label>
                  <Input id="country" value={form.country} onChange={set("country")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="region">Region / province</Label>
                  <Input id="region" value={form.region} onChange={set("region")} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="year">Reporting year</Label>
                  <Input id="year" type="number" value={form.reporting_year} onChange={set("reporting_year")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="headcount">Headcount</Label>
                  <Input id="headcount" type="number" min="0" value={form.headcount} onChange={set("headcount")} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="cement">Cement capacity (t/yr)</Label>
                  <Input id="cement" type="number" min="0" value={form.annual_cement_capacity_tonnes} onChange={set("annual_cement_capacity_tonnes")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="clinker">Clinker capacity (t/yr)</Label>
                  <Input id="clinker" type="number" min="0" value={form.annual_clinker_capacity_tonnes} onChange={set("annual_clinker_capacity_tonnes")} />
                </div>
              </div>
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Add facility"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-foreground mb-4">Registered Facilities</h2>
        <div className="space-y-3">
          {companies.length === 0 && <p className="text-muted-foreground">None yet.</p>}
          {companies.map((c) => (
            <Card key={c.id}>
              <CardContent className="pt-6 flex items-start justify-between">
                <div>
                  <div className="font-semibold text-foreground">{c.name}</div>
                  <div className="mt-1 flex items-center gap-2">
                    <FacilityTypeBadge type={c.facility_type} />
                    <span className="text-xs text-muted-foreground">
                      {c.region ? `${c.region}, ` : ""}{c.country} · grid: {c.grid_region}
                    </span>
                  </div>
                  {c.annual_cement_capacity_tonnes != null && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Cement cap: {Number(c.annual_cement_capacity_tonnes).toLocaleString()} t/yr
                    </div>
                  )}
                </div>
                <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive" onClick={() => remove(c.id, c.name)}>
                  Delete
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
