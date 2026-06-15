import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import FormSelect from "../components/FormSelect.jsx";
import { useCompany } from "../CompanyContext.jsx";
import { api } from "../utils/api.js";
import { SCOPE3_ONLY } from "../utils/catalog.js";

export default function Reports() {
  const { selectedId, selected } = useCompany();
  const [reports, setReports] = useState([]);
  const [detail, setDetail] = useState(null);
  const [open, setOpen] = useState(false);
  const year = new Date().getFullYear();
  const [form, setForm] = useState({
    report_period: `${year} Annual`,
    period_start: `${year}-01-01`,
    period_end: `${year}-12-31`,
    status: "draft",
  });

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  function load() {
    if (!selectedId) return;
    api.listReports(selectedId).then(setReports).catch((e) => toast.error(e.message));
  }
  useEffect(load, [selectedId]);

  async function generate(e) {
    e.preventDefault();
    try {
      await api.generateReport({ company_id: selectedId, ...form });
      toast.success("Report generated.");
      load();
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function openDetail(id) {
    try {
      setDetail(await api.getReportDetail(id));
      setOpen(true);
    } catch (err) {
      toast.error(err.message);
    }
  }

  async function remove(id) {
    try {
      await api.deleteReport(id);
      if (detail?.id === id) setOpen(false);
      toast.success("Report deleted.");
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
      <h1 className="text-2xl font-bold text-foreground">Reports — {selected?.name}</h1>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={generate} className="grid grid-cols-2 md:grid-cols-5 gap-3 items-end">
            <div className="md:col-span-2 space-y-1.5">
              <Label htmlFor="label">Report label</Label>
              <Input id="label" value={form.report_period} onChange={set("report_period")} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="start">Start</Label>
              <Input id="start" type="date" value={form.period_start} onChange={set("period_start")} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="end">End</Label>
              <Input id="end" type="date" value={form.period_end} onChange={set("period_end")} required />
            </div>
            <div className="space-y-1.5">
              <Label>Status</Label>
              <FormSelect value={form.status} onValueChange={(v) => setForm((f) => ({ ...f, status: v }))} options={["draft", "final"]} />
            </div>
            <Button type="submit" className="md:col-span-1">Generate</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Period</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">{SCOPE3_ONLY ? "Scope 3 tCO₂e" : "Total tCO₂e"}</TableHead>
                {!SCOPE3_ONLY && <TableHead className="text-right">Clk/Cem</TableHead>}
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reports.length === 0 && (
                <TableRow>
                  <TableCell colSpan={SCOPE3_ONLY ? 4 : 5} className="text-muted-foreground">No reports yet.</TableCell>
                </TableRow>
              )}
              {reports.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.report_period}</TableCell>
                  <TableCell className="capitalize">{r.status}</TableCell>
                  <TableCell className="text-right">
                    {Number(SCOPE3_ONLY ? r.total_scope3 : r.total_emissions).toLocaleString()}
                  </TableCell>
                  {!SCOPE3_ONLY && (
                    <TableCell className="text-right">
                      {r.clinker_to_cement_ratio != null ? `${(r.clinker_to_cement_ratio * 100).toFixed(1)}%` : "—"}
                    </TableCell>
                  )}
                  <TableCell className="text-right space-x-1 whitespace-nowrap">
                    <Button variant="ghost" size="sm" className="h-7" onClick={() => openDetail(r.id)}>view</Button>
                    <Button variant="ghost" size="sm" className="h-7" asChild>
                      <a href={api.csvUrl(r.id)}>CSV</a>
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7" asChild>
                      <a href={api.pdfUrl(r.id)}>PDF</a>
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 text-destructive hover:text-destructive" onClick={() => remove(r.id)}>delete</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          {detail && (
            <>
              <DialogHeader>
                <DialogTitle>{detail.report_period} — {detail.company_name}</DialogTitle>
                <DialogDescription>
                  {detail.facility_type} · {detail.period_start} to {detail.period_end} · {detail.status}
                </DialogDescription>
              </DialogHeader>
              <ReportDetailBody detail={detail} />
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between py-1 border-b border-border text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-foreground">{value}</span>
    </div>
  );
}

function ReportDetailBody({ detail }) {
  const t = (v) => Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="font-semibold text-foreground mb-2">Scope Breakdown (tCO₂e)</h3>
          {!SCOPE3_ONLY && (
            <>
              <Row label="Scope 1 — Process" value={t(detail.total_scope1_process)} />
              <Row label="Scope 1 — Combustion" value={t(detail.total_scope1_combustion)} />
              <Row label="Scope 1 — Mobile" value={t(detail.total_scope1_mobile)} />
              <Row label="Scope 1 — Fugitive" value={t(detail.total_scope1_fugitive)} />
              <Row label="Scope 1 — Total" value={t(detail.total_scope1)} />
              <Row label="Scope 2 (location-based)" value={t(detail.total_scope2_lb)} />
            </>
          )}
          <Row label="Scope 3" value={t(detail.total_scope3)} />
          <Row label="TOTAL" value={`${t(SCOPE3_ONLY ? detail.total_scope3 : detail.total_emissions)} tCO₂e`} />
          <Row label="Biogenic CO₂ (separate)" value={`${t(detail.biogenic_co2_total)} tCO₂`} />
        </div>
        <div>
          {SCOPE3_ONLY ? (
            <h3 className="font-semibold text-foreground mb-2">Scope 3 by GHG Protocol Category</h3>
          ) : (
            <>
              <h3 className="font-semibold text-foreground mb-2">Intensity Metrics</h3>
              <Row label="Per tonne cement" value={`${t(detail.specific_emissions_per_tonne_cement)} kgCO₂e/t`} />
              <Row label="Per tonne clinker" value={`${t(detail.specific_emissions_per_tonne_clinker)} kgCO₂e/t`} />
              <Row
                label="Clinker-to-cement ratio"
                value={detail.clinker_to_cement_ratio != null ? `${(detail.clinker_to_cement_ratio * 100).toFixed(1)}%` : "—"}
              />
            </>
          )}

          {SCOPE3_ONLY
            ? (detail.scope3_by_category || []).map((c) => (
                <Row key={c.ghg_category} label={c.label} value={`${t(c.emissions_tco2e)} (${c.percentage}%)`} />
              ))
            : null}

          <h3 className="font-semibold text-foreground mb-2 mt-4">Top Hotspots</h3>
          {detail.top_hotspots.map((h) => (
            <Row key={h.category} label={h.category} value={`${t(h.emissions_tco2e)} (${h.percentage}%)`} />
          ))}
        </div>
      </div>

      <div className="mt-6">
        <h3 className="font-semibold text-foreground mb-2">Data Quality</h3>
        <div className="flex gap-4 text-sm">
          {Object.entries(detail.data_quality_summary).map(([k, v]) => (
            <span key={k} className="text-muted-foreground">{k}: <b className="text-foreground">{v}</b></span>
          ))}
        </div>
      </div>

      <details className="mt-6">
        <summary className="cursor-pointer font-semibold text-foreground">Methodology Notes</summary>
        <ul className="list-disc ml-5 mt-2 text-sm text-muted-foreground space-y-1">
          {detail.methodology_notes.map((n, i) => <li key={i}>{n}</li>)}
        </ul>
      </details>

      <p className="mt-6 text-xs text-muted-foreground italic border-t border-border pt-4">{detail.disclaimer}</p>
    </div>
  );
}
