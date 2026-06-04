import { NavLink } from "react-router-dom";
import CompanySelector from "./CompanySelector.jsx";

const LINKS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/facilities", label: "Facilities" },
  { to: "/data-entry", label: "Data Entry" },
  { to: "/production", label: "Production Log" },
  { to: "/reports", label: "Reports" },
  { to: "/factors", label: "Factor Library" },
];

export default function Navbar() {
  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🏭</span>
          <span className="text-xl font-bold text-kiln-700">Kilnify</span>
        </div>
        <nav className="flex items-center gap-1 flex-1">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-lg text-sm font-medium ${
                  isActive ? "bg-kiln-100 text-kiln-700" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
        <CompanySelector />
      </div>
    </header>
  );
}
