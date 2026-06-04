import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

// Thin wrapper over shadcn Select for simple option lists.
// options: array of { value, label } OR strings.
export default function FormSelect({ value, onValueChange, options, placeholder, className }) {
  const items = options.map((o) => (typeof o === "string" ? { value: o, label: o } : o));
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className={className}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {items.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
