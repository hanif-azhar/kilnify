import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { facilityLabel } from "../utils/catalog.js";

const STYLES = {
  cement_plant: "bg-kiln-100 text-kiln-700 hover:bg-kiln-100",
  grinding_plant: "bg-amber-100 text-amber-700 hover:bg-amber-100",
  packing_plant: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
};

export default function FacilityTypeBadge({ type }) {
  return (
    <Badge variant="secondary" className={cn("border-transparent", STYLES[type])}>
      {facilityLabel(type)}
    </Badge>
  );
}
