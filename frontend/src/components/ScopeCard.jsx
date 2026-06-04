import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// Displays a scope total in tCO2e, optionally with sub-type breakdown rows.
export default function ScopeCard({ title, total, accent = "kiln", subRows = [] }) {
  const accents = {
    kiln: "border-l-kiln-500",
    amber: "border-l-amber-500",
    emerald: "border-l-emerald-500",
  };
  return (
    <Card className={cn("border-l-4", accents[accent] || accents.kiln)}>
      <CardContent className="pt-5">
        <div className="text-sm text-muted-foreground">{title}</div>
        <div className="text-2xl font-bold text-foreground mt-1">
          {Number(total || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}
          <span className="text-sm font-normal text-muted-foreground ml-1">tCO₂e</span>
        </div>
        {subRows.length > 0 && (
          <div className="mt-3 space-y-1">
            {subRows.map((r) => (
              <div key={r.label} className="flex justify-between text-xs text-muted-foreground">
                <span>{r.label}</span>
                <span className="font-medium text-foreground">
                  {Number(r.value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
