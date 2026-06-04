import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./utils/api.js";

// Holds the list of companies/plants and the currently selected one.
// All pages filter their data by the selected company_id.
const CompanyContext = createContext(null);

export function CompanyProvider({ children }) {
  const [companies, setCompanies] = useState([]);
  const [selectedId, setSelectedId] = useState(
    () => localStorage.getItem("kilnify.selectedCompany") || ""
  );
  const [loading, setLoading] = useState(true);

  async function refresh() {
    const list = await api.listCompanies();
    setCompanies(list);
    setSelectedId((prev) => {
      if (prev && list.some((c) => c.id === prev)) return prev;
      return list[0]?.id || "";
    });
    return list;
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedId) localStorage.setItem("kilnify.selectedCompany", selectedId);
  }, [selectedId]);

  const selected = companies.find((c) => c.id === selectedId) || null;

  return (
    <CompanyContext.Provider
      value={{ companies, selected, selectedId, setSelectedId, refresh, loading }}
    >
      {children}
    </CompanyContext.Provider>
  );
}

export const useCompany = () => useContext(CompanyContext);
