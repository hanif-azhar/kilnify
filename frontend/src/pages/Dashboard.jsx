import { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useCompany } from "../CompanyContext.jsx";
import { api } from "../utils/api.js";
import ScopeCard from "../components/ScopeCard.jsx";
import IntensityKPICard from "../components/IntensityKPICard.jsx";
import DataQualityBadge from "../components/DataQualityBadge.jsx";
import FacilityTypeBadge from "../components/FacilityTypeBadge.jsx";

export default function Dashboard() {
  const { selectedId, selected, loading: companyLoading } = useCompany();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!selectedId) return;
    api.dashboard(selectedId).then(setData).catch((e) => toast.error(e.message));
  }, [selectedId]);

  if (companyLoading) return <p className="text-muted-foreground">Loading…</p>;
  if (!selectedId)
    return (
      <Card>
        <CardContent className="pt-6 text-muted-foreground">
          No facilities yet. Add one on the <b>Facilities</b> page to get started.
        </CardContent>
      </Card>
    );
  if (!data) return <p className="text-muted-foreground">Loading dashboard…</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{selected?.name}</h1>
          <div className="mt-1">{selected && <FacilityTypeBadge type={selected.facility_type} />}</div>
        </div>
        <div className="text-right">
          <div className="text-sm text-muted-foreground">Total emissions</div>
          <div className="text-3xl font-bold text-primary">
            {data.total_tco2e.toLocaleString(undefined, { maximumFractionDigits: 1 })}
            <span className="text-base font-normal text-muted-foreground ml-1">tCO₂e</span>
          </div>
        </div>
      </div>

      {/* Scope breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ScopeCard
          title="Scope 1 — Direct"
          total={data.scope1_tco2e}
          accent="kiln"
          subRows={[
            { label: "Process (calcination)", value: data.scope1_process_tco2e },
            { label: "Combustion", value: data.scope1_combustion_tco2e },
            { label: "Mobile", value: data.scope1_mobile_tco2e },
            { label: "Fugitive", value: data.scope1_fugitive_tco2e },
          ]}
        />
        <ScopeCard title="Scope 2 — Electricity" total={data.scope2_tco2e} accent="amber" />
        <ScopeCard title="Scope 3 — Value Chain" total={data.scope3_tco2e} accent="emerald" />
      </div>

      {/* Intensity KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <IntensityKPICard
          title="Clinker-to-Cement Ratio"
          value={data.clinker_to_cement_ratio != null ? data.clinker_to_cement_ratio * 100 : null}
          unit="%"
          benchmark="65–90%"
          highlight
        />
        <IntensityKPICard
          title="Per tonne cement"
          value={data.intensity_kgco2e_per_tonne_cement}
          unit="kgCO₂e/t"
          benchmark="GNR ~600"
        />
        <IntensityKPICard
          title="Per tonne clinker (process)"
          value={data.intensity_kgco2e_per_tonne_clinker}
          unit="kgCO₂e/t"
          benchmark="490–540"
        />
        <IntensityKPICard title="Biogenic CO₂ (separate)" value={data.biogenic_co2_tco2e} unit="tCO₂" />
      </div>

      {/* Monthly trend */}
      <Card>
        <CardContent className="pt-6">
          <h2 className="font-semibold text-foreground mb-3">Monthly Emissions Trend (tCO₂e)</h2>
          {data.monthly_trend.length === 0 ? (
            <p className="text-sm text-muted-foreground">No emission entries yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.monthly_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis dataKey="month" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Legend />
                <Bar dataKey="scope1" stackId="a" fill="#1f6feb" name="Scope 1" />
                <Bar dataKey="scope2" stackId="a" fill="#f59e0b" name="Scope 2" />
                <Bar dataKey="scope3" stackId="a" fill="#10b981" name="Scope 3" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Hotspots */}
        <Card>
          <CardContent className="pt-6">
            <h2 className="font-semibold text-foreground mb-3">Top 5 Emission Hotspots</h2>
            {data.top_hotspots.length === 0 ? (
              <p className="text-sm text-muted-foreground">No data.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">tCO₂e</TableHead>
                    <TableHead className="text-right">%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.top_hotspots.map((h) => (
                    <TableRow key={h.category}>
                      <TableCell>{h.category}</TableCell>
                      <TableCell className="text-right">{h.emissions_tco2e.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{h.percentage}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Data quality */}
        <Card>
          <CardContent className="pt-6">
            <h2 className="font-semibold text-foreground mb-3">Data Quality Summary</h2>
            <div className="flex gap-6">
              {Object.entries(data.data_quality_summary).map(([k, v]) => (
                <div key={k} className="text-center">
                  <div className="text-3xl font-bold text-foreground">{v}</div>
                  <DataQualityBadge quality={k} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent entries */}
      <Card>
        <CardContent className="pt-6">
          <h2 className="font-semibold text-foreground mb-3">Recent Entries</h2>
          {data.recent_entries.length === 0 ? (
            <p className="text-sm text-muted-foreground">No entries yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Scope</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Activity</TableHead>
                  <TableHead className="text-right">tCO₂e</TableHead>
                  <TableHead>Quality</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.recent_entries.map((e) => (
                  <TableRow key={e.id}>
                    <TableCell>{e.scope}</TableCell>
                    <TableCell>{e.category}</TableCell>
                    <TableCell className="text-right">
                      {e.activity_data.toLocaleString()} {e.activity_unit}
                    </TableCell>
                    <TableCell className="text-right">
                      {(e.total_emissions_kgco2e / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell>
                      <DataQualityBadge quality={e.data_quality} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
