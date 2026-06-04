import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import FormSelect from "../components/FormSelect.jsx";
import { api } from "../utils/api.js";
import { FACILITY_TYPES } from "../utils/catalog.js";

export default function FactorLibrary() {
  const [factors, setFactors] = useState([]);
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("all");
  const [facilityType, setFacilityType] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.factorCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    api
      .listFactors({
        category: category === "all" ? "" : category,
        facility_type: facilityType === "all" ? "" : facilityType,
        search,
      })
      .then(setFactors)
      .catch((e) => toast.error(e.message));
  }, [category, facilityType, search]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Emission Factor Library</h1>
        <p className="text-sm text-muted-foreground">
          Read-only reference values with source citations. To change factors, edit the JSON files in
          <code className="mx-1">backend/data/emission_factors/</code>.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="space-y-1.5">
            <Label>Category</Label>
            <FormSelect
              value={category}
              onValueChange={setCategory}
              options={[{ value: "all", label: "All" }, ...categories.map((c) => ({ value: c, label: c }))]}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Facility type</Label>
            <FormSelect
              value={facilityType}
              onValueChange={setFacilityType}
              options={[{ value: "all", label: "All" }, ...FACILITY_TYPES]}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="search">Search</Label>
            <Input id="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="coal, DEFRA, java…" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead>Sub-category</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead>Unit</TableHead>
                <TableHead>Facilities</TableHead>
                <TableHead>Source</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {factors.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-muted-foreground">No factors match.</TableCell>
                </TableRow>
              )}
              {factors.map((f, i) => (
                <TableRow key={`${f.category}-${f.sub_category}-${i}`}>
                  <TableCell>{f.category}</TableCell>
                  <TableCell>{f.sub_category}</TableCell>
                  <TableCell className="text-right font-medium">
                    {f.factor_value == null ? "formula" : f.factor_value}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{f.unit}</TableCell>
                  <TableCell className="text-xs">
                    {(f.applicable_facility_types || []).map((t) => t.replace("_plant", "")).join(", ")}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {f.source}{f.year ? ` (${f.year})` : ""}
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
