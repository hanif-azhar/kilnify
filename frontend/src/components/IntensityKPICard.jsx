import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Highlights a cement intensity metric with optional benchmark hint.
export default function IntensityKPICard({ title, value, unit, benchmark, highlight = false }) {
  const display =
    value == null ? "—" : Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
  return (
    <Card className={cn(highlight && "ring-2 ring-primary")}>
      <CardContent className="pt-5">
        <div className="text-sm text-muted-foreground">{title}</div>
        <div className="text-2xl font-bold text-foreground mt-1">
          {display}
          {unit && value != null && <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>}
        </div>
        {benchmark && <div className="text-xs text-muted-foreground mt-1">Benchmark: {benchmark}</div>}
      </CardContent>
    </Card>
  );
}
