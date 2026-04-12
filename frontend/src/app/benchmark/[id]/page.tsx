"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { fmt, pct } from "@/lib/chart-utils";
import { MetricCard } from "@/components/metric-card";
import { PerformanceOverlay } from "@/components/charts/performance-overlay";
import { SpreadBars } from "@/components/charts/spread-bars";
import type { BenchmarkComparison, Portfolio } from "@/lib/types";

const BENCHMARKS = [
  { ticker: "SPY", label: "S&P 500 (SPY)" },
  { ticker: "QQQ", label: "Nasdaq 100 (QQQ)" },
  { ticker: "IWM", label: "Russell 2000 (IWM)" },
  { ticker: "AGG", label: "US Aggregate Bond (AGG)" },
];

export default function BenchmarkPage() {
  const { id } = useParams<{ id: string }>();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [ticker, setTicker] = useState("SPY");
  const [comparison, setComparison] = useState<BenchmarkComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.portfolios
      .get(id)
      .then(setPortfolio)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    setError(null);
    api.risk
      .benchmark(id, ticker)
      .then(setComparison)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, ticker]);

  const overlaySeries = comparison
    ? [
        {
          name: portfolio?.name ?? "Portfolio",
          data: comparison.spread_series.map((p) => ({
            date: p.date,
            value: p.portfolio_cum,
          })),
        },
        {
          name: comparison.benchmark_ticker,
          data: comparison.spread_series.map((p) => ({
            date: p.date,
            value: p.benchmark_cum,
          })),
        },
      ]
    : [];

  const spreadData = comparison
    ? comparison.spread_series.map((p) => ({ date: p.date, spread: p.spread }))
    : [];

  return (
    <div className="max-w-6xl">
      <div className="mb-6">
        <Link
          href={`/portfolios/${id}`}
          className="text-text-muted text-sm hover:text-text-secondary transition-colors"
        >
          &larr; Back to portfolio
        </Link>
        <h1 className="text-2xl font-bold mt-1">
          {portfolio ? `${portfolio.name} vs Benchmark` : "Benchmark Comparison"}
        </h1>
      </div>

      <div className="bg-bg-card border border-border rounded-lg p-5 mb-6">
        <label className="block text-sm text-text-secondary mb-2">
          Benchmark
        </label>
        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          className="w-full sm:w-72 bg-bg-primary border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent"
        >
          {BENCHMARKS.map((b) => (
            <option key={b.ticker} value={b.ticker}>
              {b.label}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="bg-red/10 border border-red/20 rounded-lg p-3 text-red text-sm mb-6">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      ) : comparison ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <MetricCard
              label="Beta"
              value={fmt(comparison.beta, 2)}
              color={comparison.beta >= 1 ? "text-accent" : "text-text-secondary"}
            />
            <MetricCard
              label="Alpha (ann.)"
              value={pct(comparison.alpha)}
              color={comparison.alpha >= 0 ? "text-green" : "text-red"}
            />
            <MetricCard
              label="Tracking Error"
              value={pct(comparison.tracking_error)}
            />
            <MetricCard
              label="Up Capture"
              value={fmt(comparison.up_capture, 2)}
              color="text-green"
            />
            <MetricCard
              label="Down Capture"
              value={fmt(comparison.down_capture, 2)}
              color="text-red"
            />
          </div>

          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Cumulative Return
            </h2>
            <PerformanceOverlay series={overlaySeries} height={280} />
          </div>

          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Spread (Portfolio &minus; {comparison.benchmark_ticker})
            </h2>
            <SpreadBars data={spreadData} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
