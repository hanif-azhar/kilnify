import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useCompany } from "../CompanyContext.jsx";
import { api } from "../utils/api.js";

const EMPTY = {
  period_start: "",
  period_end: "",
  clinker_produced_tonnes: "",
  clinker_purchased_tonnes: "",
  cement_produced_tonnes: "",
  cement_dispatched_tonnes: "",
  notes: "",
};

export default function ProductionLog() {
  const { selectedId, selected } = useCompany();
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState(EMPTY);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  function load() {
    if (!selectedId) return;
    api.listProduction(selectedId).then(setRows).catch((e) => toast.error(e.message));
  }
  useEffect(load, [selectedId]);

  // Live clinker-to-cement ratio preview.
  const clinkerUsed = (Number(form.clinker_produced_tonnes) || 0) + (Number(form.clinker_purchased_tonnes) || 0);
  const cement = Number(form.cement_produced_tonnes) || 0;
  const ratio = cement > 0 ? clinkerUsed / cement : null;

  async function submit(e) {
    e.preventDefault();
    try {
      await api.createProduction({
        company_id: selectedId,
        period_start: form.period_start,
        period_end: form.period_end,
        clinker_produced_tonnes: Number(form.clinker_produced_tonnes) || 0,
        clinker_purchased_tonnes: Number(form.clinker_purchased_tonnes) || 0,
        cement_produced_tonnes: Number(form.cement_produced_tonnes) || 0,
        cement_dispatched_tonnes: Number(form.cement_dispatched_tonnes) || 0,
        notes: form.notes || null,
      });
      setForm(EMPTY);
      toast.success("Production period added.");
      load();
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function remove(id) {
    try {
      await api.deleteProduction(id);
      toast.success("Period deleted.");
      load();
    } catch (err) {
      toast.error(err.message);
    }
  }

  if (!selectedId)
    return (
      <Card>
        <CardContent className="pt-6 text-muted-foreground">Add a facility first.</CardContent>
      </Card>
    );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Production Log — {selected?.name}</h1>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={submit} className="grid grid-cols-2 md:grid-cols-4 gap-3 items-end">
            <div className="space-y-1.5">
              <Label htmlFor="ps">Period start</Label>
              <Input id="ps" type="date" value={form.period_start} onChange={set("period_start")} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="pe">Period end</Label>
              <Input id="pe" type="date" value={form.period_end} onChange={set("period_end")} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cp">Clinker produced (t)</Label>
              <Input id="cp" type="number" min="0" step="any" value={form.clinker_produced_tonnes} onChange={set("clinker_produced_tonnes")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cpu">Clinker purchased (t)</Label>
              <Input id="cpu" type="number" min="0" step="any" value={form.clinker_purchased_tonnes} onChange={set("clinker_purchased_tonnes")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cmp">Cement produced (t)</Label>
              <Input id="cmp" type="number" min="0" step="any" value={form.cement_produced_tonnes} onChange={set("cement_produced_tonnes")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cmd">Cement dispatched (t)</Label>
              <Input id="cmd" type="number" min="0" step="any" value={form.cement_dispatched_tonnes} onChange={set("cement_dispatched_tonnes")} />
            </div>
            <div className="space-y-1.5">
              <Label>Clinker-to-cement ratio</Label>
              <div className="flex h-9 items-center rounded-md border border-input bg-muted px-3 text-sm text-muted-foreground">
                {ratio != null ? `${(ratio * 100).toFixed(1)}%` : "—"}
              </div>
            </div>
            <Button type="submit">Add period</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Period</TableHead>
                <TableHead className="text-right">Clinker prod.</TableHead>
                <TableHead className="text-right">Clinker purch.</TableHead>
                <TableHead className="text-right">Cement prod.</TableHead>
                <TableHead className="text-right">Dispatched</TableHead>
                <TableHead className="text-right">Clk/Cem ratio</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-muted-foreground">No production data yet.</TableCell>
                </TableRow>
              )}
              {rows.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.period_start} → {r.period_end}</TableCell>
                  <TableCell className="text-right">{Number(r.clinker_produced_tonnes).toLocaleString()}</TableCell>
                  <TableCell className="text-right">{Number(r.clinker_purchased_tonnes).toLocaleString()}</TableCell>
                  <TableCell className="text-right">{Number(r.cement_produced_tonnes).toLocaleString()}</TableCell>
                  <TableCell className="text-right">{Number(r.cement_dispatched_tonnes).toLocaleString()}</TableCell>
                  <TableCell className="text-right font-medium">
                    {r.clinker_to_cement_ratio != null ? `${(r.clinker_to_cement_ratio * 100).toFixed(1)}%` : "—"}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive h-7" onClick={() => remove(r.id)}>
                      delete
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
