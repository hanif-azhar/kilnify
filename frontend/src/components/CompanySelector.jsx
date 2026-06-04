import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { useCompany } from "../CompanyContext.jsx";
import { facilityLabel } from "../utils/catalog.js";

// Dropdown that switches the active company/plant for all pages.
export default function CompanySelector() {
  const { companies, selectedId, setSelectedId } = useCompany();

  if (companies.length === 0) {
    return <span className="text-sm text-muted-foreground">No plants yet</span>;
  }

  return (
    <Select value={selectedId} onValueChange={setSelectedId}>
      <SelectTrigger className="w-[260px]">
        <SelectValue placeholder="Select a plant" />
      </SelectTrigger>
      <SelectContent>
        {companies.map((c) => (
          <SelectItem key={c.id} value={c.id}>
            {c.name} — {facilityLabel(c.facility_type)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
