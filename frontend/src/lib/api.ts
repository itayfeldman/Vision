import type {
  Portfolio,
  ValuedPortfolio,
  PortfolioSummary,
  RiskReport,
  FactorDecomposition,
  PerformanceSeries,
  OptimizeRequest,
  OptimizeResult,
  Holding,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  portfolios: {
    list: () => request<Portfolio[]>("/portfolios"),
    get: (id: string) => request<Portfolio>(`/portfolios/${id}`),
    getValued: (id: string) =>
      request<ValuedPortfolio>(`/portfolios/${id}?valued=true`),
    getSummary: (id: string) =>
      request<PortfolioSummary>(`/portfolios/${id}/summary`),
    create: (name: string, holdings: Holding[]) =>
      request<Portfolio>("/portfolios", {
        method: "POST",
        body: JSON.stringify({ name, holdings }),
      }),
    update: (id: string, name: string, holdings: Holding[]) =>
      request<Portfolio>(`/portfolios/${id}`, {
        method: "PUT",
        body: JSON.stringify({ name, holdings }),
      }),
    delete: (id: string) =>
      request<void>(`/portfolios/${id}`, { method: "DELETE" }),
  },
  risk: {
    get: (id: string, lookbackYears = 3) =>
      request<RiskReport>(`/risk/${id}?lookback_years=${lookbackYears}`),
    performance: (id: string, lookbackYears = 3) =>
      request<PerformanceSeries>(
        `/risk/${id}/performance?lookback_years=${lookbackYears}`
      ),
  },
  factors: {
    get: (id: string, lookbackYears = 3) =>
      request<FactorDecomposition>(
        `/factors/${id}?lookback_years=${lookbackYears}`
      ),
  },
  optimize: (req: OptimizeRequest) =>
    request<OptimizeResult>("/optimize", {
      method: "POST",
      body: JSON.stringify(req),
    }),
};
