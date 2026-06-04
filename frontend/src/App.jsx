import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import { Toaster } from "@/components/ui/sonner";
import { CompanyProvider } from "./CompanyContext.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Facilities from "./pages/Facilities.jsx";
import DataEntry from "./pages/DataEntry.jsx";
import ProductionLog from "./pages/ProductionLog.jsx";
import Reports from "./pages/Reports.jsx";
import FactorLibrary from "./pages/FactorLibrary.jsx";

export default function App() {
  return (
    <CompanyProvider>
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/facilities" element={<Facilities />} />
          <Route path="/data-entry" element={<DataEntry />} />
          <Route path="/production" element={<ProductionLog />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/factors" element={<FactorLibrary />} />
        </Routes>
      </main>
      <footer className="max-w-7xl mx-auto px-4 py-6 text-xs text-muted-foreground">
        Kilnify follows GHG Protocol &amp; WBCSD CSI Cement CO₂ Protocol. Figures are unverified
        estimates — confirm with a certified carbon accountant before external reporting.
      </footer>
      <Toaster richColors position="top-right" />
    </CompanyProvider>
  );
}
