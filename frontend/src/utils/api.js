// Fetch wrappers for the Kilnify API. All paths are relative /api so the
// Vite dev server proxies them to the FastAPI backend on port 8003.

async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch (_) {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

const qs = (params) => {
  const clean = Object.fromEntries(Object.entries(params || {}).filter(([, v]) => v != null && v !== ""));
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
};

export const api = {
  // Companies
  listCompanies: () => request("/companies/"),
  createCompany: (data) => request("/companies/", { method: "POST", body: JSON.stringify(data) }),
  getCompany: (id) => request(`/companies/${id}`),
  deleteCompany: (id) => request(`/companies/${id}`, { method: "DELETE" }),

  // Production
  listProduction: (companyId) => request(`/production/${qs({ company_id: companyId })}`),
  createProduction: (data) => request("/production/", { method: "POST", body: JSON.stringify(data) }),
  deleteProduction: (id) => request(`/production/${id}`, { method: "DELETE" }),

  // Emissions
  listEmissions: (companyId, scope) => request(`/emissions/${qs({ company_id: companyId, scope })}`),
  createEmission: (data) => request("/emissions/", { method: "POST", body: JSON.stringify(data) }),
  deleteEmission: (id) => request(`/emissions/${id}`, { method: "DELETE" }),

  // Reports
  listReports: (companyId) => request(`/reports/${qs({ company_id: companyId })}`),
  generateReport: (data) => request("/reports/generate", { method: "POST", body: JSON.stringify(data) }),
  getReportDetail: (id) => request(`/reports/${id}/detail`),
  deleteReport: (id) => request(`/reports/${id}`, { method: "DELETE" }),
  csvUrl: (id) => `/api/reports/${id}/export/csv`,
  pdfUrl: (id) => `/api/reports/${id}/export/pdf`,

  // Factors
  listFactors: (params) => request(`/factors/${qs(params)}`),
  factorCategories: () => request("/factors/categories"),
  listCustomFactors: (companyId) => request(`/factors/custom${qs({ company_id: companyId })}`),
  createCustomFactor: (data) => request("/factors/custom", { method: "POST", body: JSON.stringify(data) }),
  updateCustomFactor: (id, data) => request(`/factors/custom/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteCustomFactor: (id) => request(`/factors/custom/${id}`, { method: "DELETE" }),

  // Dashboard
  dashboard: (companyId) => request(`/dashboard/${qs({ company_id: companyId })}`),
};
