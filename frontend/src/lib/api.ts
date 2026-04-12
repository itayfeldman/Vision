import type {
  BenchmarkComparison,
  FactorDecomposition,
  FrontierRequest,
  FrontierResult,
  Holding,
  OptimizeRequest,
  OptimizeResult,
  PerformanceSeries,
  Portfolio,
  PortfolioSummary,
  PriceHistory,
  RiskReport,
  ValuedPortfolio,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = Array.isArray(body.detail)
      ? body.detail.map((d: { msg: string }) => d.msg).join(", ")
      : body.detail;
    throw new Error(detail || `Request failed: ${res.status}`);
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
    benchmark: (id: string, ticker = "SPY", lookbackYears = 3) =>
      request<BenchmarkComparison>(
        `/portfolios/${id}/benchmark?ticker=${encodeURIComponent(ticker)}&lookback_years=${lookbackYears}`
      ),
  },
  factors: {
    get: (id: string, lookbackYears = 3) =>
      request<FactorDecomposition>(
        `/factors/${id}?lookback_years=${lookbackYears}`
      ),
  },
  marketData: {
    prices: (
      ticker: string,
      start?: string,
      end?: string,
      signal?: AbortSignal
    ) => {
      const params = new URLSearchParams();
      if (start) params.set("start", start);
      if (end) params.set("end", end);
      const qs = params.toString();
      return request<PriceHistory>(
        `/market-data/${encodeURIComponent(ticker)}/prices${qs ? `?${qs}` : ""}`,
        { signal }
      );
    },
  },
  optimize: {
    run: (req: OptimizeRequest) =>
      request<OptimizeResult>("/optimize", {
        method: "POST",
        body: JSON.stringify(req),
      }),
    frontier: (req: FrontierRequest) =>
      request<FrontierResult>("/optimize/frontier", {
        method: "POST",
        body: JSON.stringify(req),
      }),
  },
};
