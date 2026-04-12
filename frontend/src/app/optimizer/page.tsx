"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { api } from "@/lib/api";
import { COLORS, TOOLTIP_STYLE, pct, sharpeColor } from "@/lib/chart-utils";
import { MetricCard } from "@/components/metric-card";
import type { OptimizeResult } from "@/lib/types";

const OBJECTIVES = [
  { value: "min_volatility", label: "Minimum Volatility" },
  { value: "max_sharpe", label: "Maximum Sharpe Ratio" },
  { value: "risk_parity", label: "Risk Parity" },
  { value: "max_return", label: "Maximum Return" },
];

export default function OptimizerPage() {
  const router = useRouter();
  const [tickerInput, setTickerInput] = useState("");
  const [tickers, setTickers] = useState<string[]>([]);
  const [objective, setObjective] = useState("max_sharpe");
  const [lookbackYears, setLookbackYears] = useState(3);
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [portfolioName, setPortfolioName] = useState("");

  function addTicker() {
    const t = tickerInput.toUpperCase().trim();
    if (t && !tickers.includes(t)) {
      setTickers([...tickers, t]);
    }
    setTickerInput("");
  }

  function removeTicker(ticker: string) {
    setTickers(tickers.filter((t) => t !== ticker));
  }

  function handleTickerKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      addTicker();
    }
  }

  async function handleOptimize(e: React.FormEvent) {
    e.preventDefault();
    if (tickers.length < 2) {
      setError("Add at least 2 tickers");
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const r = await api.optimize({
        tickers,
        objective,
        lookback_years: lookbackYears,
      });
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimization failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!result || !portfolioName.trim()) return;
    setSaving(true);
    try {
      const holdings = Object.entries(result.weights).map(([ticker, weight]) => ({
        ticker,
        weight,
      }));
      const portfolio = await api.portfolios.create(portfolioName.trim(), holdings);
      router.push(`/portfolios/${portfolio.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save portfolio");
      setSaving(false);
    }
  }

  const chartData = result
    ? Object.entries(result.weights)
        .map(([name, weight]) => ({ name, weight: weight * 100 }))
        .sort((a, b) => b.weight - a.weight)
    : [];

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Portfolio Optimizer</h1>

      <form onSubmit={handleOptimize} className="space-y-6 mb-8">
        {/* Ticker Input */}
        <div>
          <label className="block text-sm text-text-secondary mb-2">Tickers</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={tickerInput}
              onChange={(e) => setTickerInput(e.target.value)}
              onKeyDown={handleTickerKeyDown}
              className="flex-1 bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent uppercase"
              placeholder="Enter ticker and press Enter"
            />
            <button
              type="button"
              onClick={addTicker}
              className="bg-bg-card border border-border hover:border-accent/40 px-4 py-2.5 rounded-lg text-sm transition-colors"
            >
              Add
            </button>
          </div>
          {tickers.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-3">
              {tickers.map((t) => (
                <span
                  key={t}
                  className="bg-bg-hover text-text-secondary text-sm px-3 py-1.5 rounded-lg flex items-center gap-2"
                >
                  {t}
                  <button
                    type="button"
                    onClick={() => removeTicker(t)}
                    className="text-text-muted hover:text-red transition-colors"
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>
          )}
          <p className="text-text-muted text-xs mt-2">
            {tickers.length} ticker{tickers.length !== 1 ? "s" : ""} selected
            {tickers.length < 2 && " (minimum 2)"}
          </p>
        </div>

        {/* Objective & Lookback */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-text-secondary mb-2">Objective</label>
            <select
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent"
            >
              {OBJECTIVES.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-text-secondary mb-2">
              Lookback Period
            </label>
            <select
              value={lookbackYears}
              onChange={(e) => setLookbackYears(Number(e.target.value))}
              className="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent"
            >
              <option value={1}>1 Year</option>
              <option value={2}>2 Years</option>
              <option value={3}>3 Years</option>
              <option value={5}>5 Years</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="bg-red/10 border border-red/20 rounded-lg p-3 text-red text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || tickers.length < 2}
          className="bg-accent hover:bg-accent-hover disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          {loading ? "Optimizing..." : "Optimize"}
        </button>
      </form>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Metrics */}
          <div className="grid grid-cols-3 gap-3">
            <MetricCard label="Expected Return" value={pct(result.expected_return)} color="text-green" />
            <MetricCard label="Expected Volatility" value={pct(result.expected_volatility)} />
            <MetricCard label="Sharpe Ratio" value={result.sharpe_ratio.toFixed(2)} color={sharpeColor(result.sharpe_ratio)} />
          </div>

          {/* Weight Chart */}
          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Optimal Weights
            </h2>
            <ResponsiveContainer width="100%" height={Math.max(200, chartData.length * 40)}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3142" />
                <XAxis
                  type="number"
                  tick={{ fill: "#8b95a5", fontSize: 12 }}
                  tickFormatter={(v) => `${v}%`}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  tick={{ fill: "#8b95a5", fontSize: 12 }}
                  width={50}
                />
                <Tooltip
                  {...TOOLTIP_STYLE}
                  formatter={(value) => `${Number(value).toFixed(1)}%`}
                />
                <Bar dataKey="weight" radius={[0, 4, 4, 0]}>
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Weight Table */}
            <table className="w-full mt-4">
              <thead>
                <tr className="text-text-muted text-xs uppercase border-b border-border">
                  <th className="text-left pb-2">Ticker</th>
                  <th className="text-right pb-2">Weight</th>
                </tr>
              </thead>
              <tbody>
                {chartData.map((d) => (
                  <tr key={d.name} className="border-b border-border/50">
                    <td className="py-2.5 font-mono font-medium">{d.name}</td>
                    <td className="py-2.5 text-right font-mono text-text-secondary">
                      {d.weight.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Save as Portfolio */}
          <div className="bg-bg-card border border-border rounded-lg p-5">
            <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
              Save as Portfolio
            </h2>
            <div className="flex gap-3">
              <input
                type="text"
                value={portfolioName}
                onChange={(e) => setPortfolioName(e.target.value)}
                className="flex-1 bg-bg-primary border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent"
                placeholder="Portfolio name"
              />
              <button
                onClick={handleSave}
                disabled={saving || !portfolioName.trim()}
                className="bg-accent hover:bg-accent-hover disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
              >
                {saving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
