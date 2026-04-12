"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import { CHART_COLORS, TOOLTIP_STYLE, fmt, pct, sharpeColor } from "@/lib/chart-utils";
import { MetricCard } from "@/components/metric-card";
import { AllocationPie } from "@/components/charts/allocation-pie";
import { FactorBars } from "@/components/charts/factor-bars";
import { PerformanceChart } from "@/components/charts/performance-chart";
import type {
  PortfolioSummary, RiskReport, FactorDecomposition,
  ValuedPortfolio, PerformanceSeries,
} from "@/lib/types";

export default function PortfolioDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [risk, setRisk] = useState<RiskReport | null>(null);
  const [factors, setFactors] = useState<FactorDecomposition | null>(null);
  const [valued, setValued] = useState<ValuedPortfolio | null>(null);
  const [performance, setPerformance] = useState<PerformanceSeries | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!id) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    Promise.all([
      api.portfolios.getSummary(id),
      api.risk.get(id),
      api.factors.get(id),
      api.portfolios.getValued(id),
      api.risk.performance(id),
    ])
      .then(([s, r, f, v, p]) => {
        setSummary(s);
        setRisk(r);
        setFactors(f);
        setValued(v);
        setPerformance(p);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleDelete() {
    if (!confirm("Delete this portfolio?")) return;
    setDeleting(true);
    try {
      await api.portfolios.delete(id);
      router.push("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-red/10 border border-red/20 rounded-lg p-4 text-red">
        {error || "Portfolio not found"}
      </div>
    );
  }

  const pieData = summary.holdings.map((h) => ({
    name: h.ticker,
    value: h.weight * 100,
  }));

  const factorData = factors?.exposures.map((e) => ({
    name: e.factor_name,
    beta: e.beta,
  })) || [];

  const perfPoints = performance?.points.map((p) => ({
    date: p.date,
    value: p.cumulative_return,
  })) || [];

  const volumeData = performance?.points.map((p) => ({
    date: p.date,
    volume: p.volume,
  })) || [];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link href="/" className="text-text-muted text-sm hover:text-text-secondary transition-colors">
            &larr; Back
          </Link>
          <h1 className="text-2xl font-bold mt-1">{summary.name}</h1>
          <p className="text-text-secondary text-sm">
            {summary.holdings.length} holdings
            {valued && (
              <span className="ml-2 font-mono">
                &middot; ${valued.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/benchmark/${id}`}
            className="border border-border hover:border-accent/40 px-4 py-2 rounded-lg text-sm text-text-secondary transition-colors"
          >
            Benchmark
          </Link>
          <Link
            href={`/portfolios/${id}/edit`}
            className="border border-border hover:border-accent/40 px-4 py-2 rounded-lg text-sm text-text-secondary transition-colors"
          >
            Edit
          </Link>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="border border-red/30 text-red hover:bg-red/10 px-4 py-2 rounded-lg text-sm transition-colors"
          >
            {deleting ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>

      {/* Risk Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
        <MetricCard
          label="Ann. Return"
          value={pct(summary.risk.annualized_return)}
          color={summary.risk.annualized_return >= 0 ? "text-green" : "text-red"}
        />
        <MetricCard label="Ann. Volatility" value={pct(summary.risk.annualized_volatility)} />
        <MetricCard
          label="Sharpe Ratio"
          value={fmt(summary.risk.sharpe_ratio)}
          color={sharpeColor(summary.risk.sharpe_ratio)}
        />
        <MetricCard label="Max Drawdown" value={pct(summary.risk.max_drawdown)} color="text-red" />
        <MetricCard label="VaR 95%" value={pct(summary.risk.var_95)} />
      </div>

      {/* Performance Chart — full width */}
      {perfPoints.length > 0 && (
        <div className="bg-bg-card border border-border rounded-lg p-5 mb-8">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
            Cumulative Performance (3Y)
          </h2>
          <PerformanceChart data={perfPoints} height={280} />

          {/* Volume Chart */}
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mt-6 mb-4">
            Trading Volume
          </h2>
          <ResponsiveContainer width="100%" height={120}>
            <BarChart data={volumeData}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} vertical={false} />
              <XAxis
                dataKey="date"
                tick={{ fill: CHART_COLORS.textMuted, fontSize: 11 }}
                tickFormatter={(d: string) => d.slice(0, 7)}
                interval="preserveStartEnd"
                minTickGap={60}
              />
              <YAxis
                tick={{ fill: CHART_COLORS.textMuted, fontSize: 10 }}
                tickFormatter={(v: number) => {
                  if (v >= 1e9) return `${(v / 1e9).toFixed(1)}B`;
                  if (v >= 1e6) return `${(v / 1e6).toFixed(0)}M`;
                  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
                  return String(v);
                }}
                width={45}
              />
              <Tooltip
                {...TOOLTIP_STYLE}
                labelFormatter={(d) => String(d)}
                formatter={(value) => Number(value).toLocaleString()}
              />
              <Bar dataKey="volume" fill={CHART_COLORS.accent} opacity={0.5} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Valued Holdings Table */}
        <div className="bg-bg-card border border-border rounded-lg p-5">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
            Holdings
          </h2>
          <table className="w-full">
            <thead>
              <tr className="text-text-muted text-xs uppercase border-b border-border">
                <th className="text-left pb-2">Ticker</th>
                <th className="text-right pb-2">Weight</th>
                {valued && (
                  <>
                    <th className="text-right pb-2">Price</th>
                    <th className="text-right pb-2">Value</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody>
              {valued ? (
                valued.holdings.map((h) => (
                  <tr key={h.ticker} className="border-b border-border/50">
                    <td className="py-2.5 font-mono font-medium">{h.ticker}</td>
                    <td className="py-2.5 text-right font-mono text-text-secondary">
                      {(h.weight * 100).toFixed(1)}%
                    </td>
                    <td className="py-2.5 text-right font-mono text-text-secondary">
                      ${h.current_price.toFixed(2)}
                    </td>
                    <td className="py-2.5 text-right font-mono text-text-secondary">
                      ${h.market_value.toFixed(2)}
                    </td>
                  </tr>
                ))
              ) : (
                summary.holdings.map((h) => (
                  <tr key={h.ticker} className="border-b border-border/50">
                    <td className="py-2.5 font-mono font-medium">{h.ticker}</td>
                    <td className="py-2.5 text-right font-mono text-text-secondary">
                      {(h.weight * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Weight Pie Chart */}
        <div className="bg-bg-card border border-border rounded-lg p-5">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
            Allocation
          </h2>
          <AllocationPie data={pieData} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Factor Exposures */}
        <div className="bg-bg-card border border-border rounded-lg p-5">
          <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
            Factor Exposures
          </h2>
          {factors && (
            <>
              <FactorBars data={factorData} />
              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="text-center">
                  <p className="text-text-muted text-xs">R-squared</p>
                  <p className="font-mono font-semibold">{fmt(factors.r_squared, 3)}</p>
                </div>
                <div className="text-center">
                  <p className="text-text-muted text-xs">Alpha</p>
                  <p className="font-mono font-semibold">{pct(factors.alpha)}</p>
                </div>
                <div className="text-center">
                  <p className="text-text-muted text-xs">Residual Risk</p>
                  <p className="font-mono font-semibold">{pct(factors.residual_risk)}</p>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Extended Risk Metrics */}
        {risk && (
          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Risk Detail
            </h2>
            <div className="grid grid-cols-2 gap-x-6 gap-y-3">
              {[
                ["Sortino Ratio", fmt(risk.metrics.sortino_ratio)],
                ["Max DD Duration", `${risk.metrics.max_drawdown_duration}d`],
                ["VaR 95%", pct(risk.metrics.var_95)],
                ["VaR 99%", pct(risk.metrics.var_99)],
                ["CVaR 95%", pct(risk.metrics.cvar_95)],
                ["CVaR 99%", pct(risk.metrics.cvar_99)],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between py-2 border-b border-border/50">
                  <span className="text-text-muted text-sm">{label}</span>
                  <span className="font-mono text-sm">{value}</span>
                </div>
              ))}
            </div>

            {/* Correlation Matrix */}
            {risk.correlation.tickers.length > 1 && (
              <div className="mt-6">
                <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
                  Correlation
                </h3>
                <div className="overflow-x-auto">
                  <table className="text-xs font-mono">
                    <thead>
                      <tr>
                        <th />
                        {risk.correlation.tickers.map((t) => (
                          <th key={t} className="px-2 py-1 text-text-muted">
                            {t}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {risk.correlation.tickers.map((t, i) => (
                        <tr key={t}>
                          <td className="pr-2 text-text-muted">{t}</td>
                          {risk.correlation.matrix[i].map((val, j) => {
                            const intensity = Math.abs(val);
                            const bg =
                              i === j
                                ? "transparent"
                                : val > 0
                                  ? `rgba(79, 143, 247, ${intensity * 0.4})`
                                  : `rgba(248, 113, 113, ${intensity * 0.4})`;
                            return (
                              <td
                                key={j}
                                className="px-2 py-1 text-center"
                                style={{ background: bg }}
                              >
                                {val.toFixed(2)}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
