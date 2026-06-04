import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const STYLES = {
  measured: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
  calculated: "bg-kiln-100 text-kiln-700 hover:bg-kiln-100",
  estimated: "bg-amber-100 text-amber-700 hover:bg-amber-100",
};

export default function DataQualityBadge({ quality }) {
  return (
    <Badge variant="secondary" className={cn("border-transparent font-medium", STYLES[quality])}>
      {quality}
    </Badge>
  );
}
