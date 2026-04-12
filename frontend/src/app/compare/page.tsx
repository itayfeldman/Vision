"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { CHART_COLORS, COLORS, TOOLTIP_STYLE, fmt, pct } from "@/lib/chart-utils";
import { PerformanceOverlay } from "@/components/charts/performance-overlay";
import type {
  FactorDecomposition,
  PerformanceSeries,
  Portfolio,
  PortfolioSummary,
  RiskReport,
} from "@/lib/types";

interface LoadedPortfolio {
  id: string;
  name: string;
  summary: PortfolioSummary;
  risk: RiskReport;
  factors: FactorDecomposition;
  performance: PerformanceSeries;
}

const MAX_SELECTION = 4;

type MetricDirection = "higher" | "lower";

interface MetricDef {
  key: string;
  label: string;
  pick: (p: LoadedPortfolio) => number;
  format: (n: number) => string;
  direction: MetricDirection;
}

const METRICS: MetricDef[] = [
  {
    key: "return",
    label: "Ann. Return",
    pick: (p) => p.summary.risk.annualized_return,
    format: pct,
    direction: "higher",
  },
  {
    key: "vol",
    label: "Ann. Volatility",
    pick: (p) => p.summary.risk.annualized_volatility,
    format: pct,
    direction: "lower",
  },
  {
    key: "sharpe",
    label: "Sharpe Ratio",
    pick: (p) => p.summary.risk.sharpe_ratio,
    format: (n) => fmt(n, 2),
    direction: "higher",
  },
  {
    key: "sortino",
    label: "Sortino Ratio",
    pick: (p) => p.risk.metrics.sortino_ratio,
    format: (n) => fmt(n, 2),
    direction: "higher",
  },
  {
    key: "mdd",
    label: "Max Drawdown",
    pick: (p) => p.summary.risk.max_drawdown,
    format: pct,
    direction: "higher", // less negative is better
  },
  {
    key: "var95",
    label: "VaR 95%",
    pick: (p) => p.summary.risk.var_95,
    format: pct,
    direction: "higher",
  },
];

export default function ComparePage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loaded, setLoaded] = useState<LoadedPortfolio[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.portfolios
      .list()
      .then(setPortfolios)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoadingList(false));
  }, []);

  function toggleSelection(id: string) {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((x) => x !== id));
    } else if (selectedIds.length < MAX_SELECTION) {
      setSelectedIds([...selectedIds, id]);
    }
  }

  async function handleCompare() {
    if (selectedIds.length < 2) return;
    setComparing(true);
    setError(null);
    setLoaded([]);
    try {
      const results = await Promise.all(
        selectedIds.map(async (id) => {
          const [summary, risk, factors, performance] = await Promise.all([
            api.portfolios.getSummary(id),
            api.risk.get(id),
            api.factors.get(id),
            api.risk.performance(id),
          ]);
          return {
            id,
            name: summary.name,
            summary,
            risk,
            factors,
            performance,
          } satisfies LoadedPortfolio;
        })
      );
      setLoaded(results);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Comparison failed");
    } finally {
      setComparing(false);
    }
  }

  const bestWorst = useMemo(() => {
    const map = new Map<string, { best: number; worst: number }>();
    if (loaded.length === 0) return map;
    for (const m of METRICS) {
      const values = loaded.map((p) => m.pick(p));
      const max = Math.max(...values);
      const min = Math.min(...values);
      map.set(m.key, {
        best: m.direction === "higher" ? max : min,
        worst: m.direction === "higher" ? min : max,
      });
    }
    return map;
  }, [loaded]);

  const factorChartData = useMemo(() => {
    if (loaded.length === 0) return [];
    const factorNames = new Set<string>();
    for (const p of loaded) {
      for (const e of p.factors.exposures) factorNames.add(e.factor_name);
    }
    return Array.from(factorNames).map((name) => {
      const row: Record<string, number | string> = { factor: name };
      for (const p of loaded) {
        const e = p.factors.exposures.find((x) => x.factor_name === name);
        row[p.name] = e ? e.beta : 0;
      }
      return row;
    });
  }, [loaded]);

  const overlaySeries = useMemo(
    () =>
      loaded.map((p) => ({
        name: p.name,
        data: p.performance.points.map((pt) => ({
          date: pt.date,
          value: pt.cumulative_return,
        })),
      })),
    [loaded]
  );

  return (
    <div className="max-w-6xl">
      <h1 className="text-2xl font-bold mb-6">Compare Portfolios</h1>

      <div className="bg-bg-card border border-border rounded-lg p-5 mb-6">
        <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
          Select 2–{MAX_SELECTION} portfolios
        </h2>
        {loadingList ? (
          <p className="text-text-muted text-sm">Loading...</p>
        ) : portfolios.length === 0 ? (
          <p className="text-text-muted text-sm">No portfolios yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {portfolios.map((p) => {
              const checked = selectedIds.includes(p.id);
              const disabled = !checked && selectedIds.length >= MAX_SELECTION;
              return (
                <label
                  key={p.id}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg border transition-colors ${
                    checked
                      ? "border-accent bg-accent/10"
                      : "border-border hover:border-accent/40"
                  } ${disabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggleSelection(p.id)}
                    className="accent-accent"
                  />
                  <span className="text-sm">{p.name}</span>
                  <span className="ml-auto text-xs text-text-muted">
                    {p.holdings.length} holdings
                  </span>
                </label>
              );
            })}
          </div>
        )}

        <button
          onClick={handleCompare}
          disabled={selectedIds.length < 2 || comparing}
          className="mt-5 bg-accent hover:bg-accent-hover disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          {comparing ? "Loading..." : "Compare"}
        </button>
      </div>

      {error && (
        <div className="bg-red/10 border border-red/20 rounded-lg p-3 text-red text-sm mb-6">
          {error}
        </div>
      )}

      {loaded.length > 0 && (
        <div className="space-y-6">
          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Metrics
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px]">
                <thead>
                  <tr className="text-text-muted text-xs uppercase border-b border-border">
                    <th className="text-left pb-2">Metric</th>
                    {loaded.map((p) => (
                      <th key={p.id} className="text-right pb-2">
                        {p.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {METRICS.map((m) => {
                    const bw = bestWorst.get(m.key);
                    return (
                      <tr key={m.key} className="border-b border-border/50">
                        <td className="py-2.5 text-sm text-text-muted">
                          {m.label}
                        </td>
                        {loaded.map((p) => {
                          const v = m.pick(p);
                          const isBest = bw && v === bw.best && bw.best !== bw.worst;
                          const isWorst =
                            bw && v === bw.worst && bw.best !== bw.worst;
                          const color = isBest
                            ? "text-green"
                            : isWorst
                              ? "text-red"
                              : "text-text-secondary";
                          return (
                            <td
                              key={p.id}
                              className={`py-2.5 text-right font-mono text-sm ${color}`}
                            >
                              {m.format(v)}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Cumulative Performance
            </h2>
            <PerformanceOverlay series={overlaySeries} height={320} />
          </div>

          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Factor Exposures
            </h2>
            <ResponsiveContainer width="100%" height={Math.max(240, factorChartData.length * 60)}>
              <BarChart data={factorChartData} layout="vertical" margin={{ left: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} />
                <XAxis
                  type="number"
                  tick={{ fill: CHART_COLORS.textMuted, fontSize: 12 }}
                />
                <YAxis
                  dataKey="factor"
                  type="category"
                  tick={{ fill: CHART_COLORS.textMuted, fontSize: 12 }}
                  width={80}
                />
                <Tooltip
                  {...TOOLTIP_STYLE}
                  formatter={(value) => fmt(Number(value), 3)}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                {loaded.map((p, i) => (
                  <Bar
                    key={p.id}
                    dataKey={p.name}
                    fill={COLORS[i % COLORS.length]}
                    radius={[0, 4, 4, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
