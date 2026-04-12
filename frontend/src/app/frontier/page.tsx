"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { pct, sharpeColor } from "@/lib/chart-utils";
import { MetricCard } from "@/components/metric-card";
import {
  FrontierScatter,
  type FrontierScatterPoint,
} from "@/components/charts/frontier-scatter";
import type {
  FrontierPoint,
  FrontierResult,
  WeightConstraint,
} from "@/lib/types";

interface ConstraintRow {
  ticker: string;
  min: string;
  max: string;
}

export default function FrontierPage() {
  const [tickerInput, setTickerInput] = useState("");
  const [tickers, setTickers] = useState<string[]>([]);
  const [constraints, setConstraints] = useState<ConstraintRow[]>([]);
  const [lookbackYears, setLookbackYears] = useState(3);
  const [points, setPoints] = useState(50);
  const [result, setResult] = useState<FrontierResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<FrontierPoint | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  function addTicker() {
    const t = tickerInput.toUpperCase().trim();
    if (t && !tickers.includes(t)) {
      setTickers([...tickers, t]);
      setConstraints([...constraints, { ticker: t, min: "", max: "" }]);
    }
    setTickerInput("");
  }

  function removeTicker(ticker: string) {
    setTickers(tickers.filter((t) => t !== ticker));
    setConstraints(constraints.filter((c) => c.ticker !== ticker));
  }

  function updateConstraint(
    ticker: string,
    field: "min" | "max",
    value: string
  ) {
    setConstraints(
      constraints.map((c) => (c.ticker === ticker ? { ...c, [field]: value } : c))
    );
  }

  function handleTickerKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      addTicker();
    }
  }

  function buildConstraints(): WeightConstraint[] {
    const out: WeightConstraint[] = [];
    for (const c of constraints) {
      const hasMin = c.min.trim() !== "";
      const hasMax = c.max.trim() !== "";
      if (!hasMin && !hasMax) continue;
      out.push({
        ticker: c.ticker,
        min_weight: hasMin ? Number(c.min) : 0,
        max_weight: hasMax ? Number(c.max) : 1,
      });
    }
    return out;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (tickers.length < 2) {
      setError("Add at least 2 tickers");
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    setSelected(null);
    setSelectedIndex(null);

    try {
      const req = {
        tickers,
        lookback_years: lookbackYears,
        points,
        constraints: buildConstraints(),
      };
      const r = await api.optimize.frontier(req);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Frontier computation failed");
    } finally {
      setLoading(false);
    }
  }

  function toScatterPoints(r: FrontierResult): FrontierScatterPoint[] {
    const labeled = new Map<number, FrontierScatterPoint["label"]>();
    const markNamed = (p: FrontierPoint, label: FrontierScatterPoint["label"]) => {
      const idx = r.points.findIndex(
        (q) =>
          Math.abs(q.expected_return - p.expected_return) < 1e-9 &&
          Math.abs(q.expected_volatility - p.expected_volatility) < 1e-9
      );
      if (idx >= 0 && !labeled.has(idx)) labeled.set(idx, label);
    };
    markNamed(r.min_volatility, "min_vol");
    markNamed(r.max_sharpe, "max_sharpe");
    markNamed(r.equal_weight, "equal_weight");

    const base: FrontierScatterPoint[] = r.points.map((p, i) => ({
      volatility: p.expected_volatility,
      return_: p.expected_return,
      sharpe: p.sharpe_ratio,
      label: labeled.get(i) ?? null,
      index: i,
    }));

    // Append named portfolios that weren't exact matches on the sweep.
    const namedExtras: Array<[FrontierPoint, FrontierScatterPoint["label"]]> = [
      [r.min_volatility, "min_vol"],
      [r.max_sharpe, "max_sharpe"],
      [r.equal_weight, "equal_weight"],
    ];
    let cursor = base.length;
    for (const [p, label] of namedExtras) {
      const exists = base.some(
        (b) =>
          b.label === label &&
          Math.abs(b.return_ - p.expected_return) < 1e-9 &&
          Math.abs(b.volatility - p.expected_volatility) < 1e-9
      );
      if (!exists) {
        base.push({
          volatility: p.expected_volatility,
          return_: p.expected_return,
          sharpe: p.sharpe_ratio,
          label,
          index: cursor++,
        });
      }
    }
    return base;
  }

  const scatterPoints = result ? toScatterPoints(result) : [];

  function resolveFrontierPoint(p: FrontierScatterPoint): FrontierPoint | null {
    if (!result) return null;
    if (p.index < result.points.length) return result.points[p.index];
    if (p.label === "min_vol") return result.min_volatility;
    if (p.label === "max_sharpe") return result.max_sharpe;
    if (p.label === "equal_weight") return result.equal_weight;
    return null;
  }

  function handleSelectPoint(p: FrontierScatterPoint) {
    const fp = resolveFrontierPoint(p);
    if (fp) {
      setSelected(fp);
      setSelectedIndex(p.index);
    }
  }

  const sortedWeights = selected
    ? Object.entries(selected.weights).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <div className="max-w-6xl">
      <h1 className="text-2xl font-bold mb-6">Efficient Frontier</h1>

      <form onSubmit={handleSubmit} className="space-y-6 mb-8">
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

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
          <div>
            <label className="block text-sm text-text-secondary mb-2">
              Points: <span className="text-text-primary font-mono">{points}</span>
            </label>
            <input
              type="range"
              min={10}
              max={100}
              step={1}
              value={points}
              onChange={(e) => setPoints(Number(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
        </div>

        {tickers.length > 0 && (
          <div>
            <label className="block text-sm text-text-secondary mb-2">
              Constraints (optional)
            </label>
            <div className="bg-bg-card border border-border rounded-lg divide-y divide-border">
              <div className="grid grid-cols-[1fr_1fr_1fr] gap-3 px-4 py-2 text-xs text-text-muted uppercase tracking-wider">
                <span>Ticker</span>
                <span>Min</span>
                <span>Max</span>
              </div>
              {constraints.map((c) => (
                <div
                  key={c.ticker}
                  className="grid grid-cols-[1fr_1fr_1fr] gap-3 px-4 py-2 items-center"
                >
                  <span className="font-mono text-sm">{c.ticker}</span>
                  <input
                    type="number"
                    min={0}
                    max={1}
                    step={0.05}
                    value={c.min}
                    onChange={(e) =>
                      updateConstraint(c.ticker, "min", e.target.value)
                    }
                    placeholder="0"
                    className="bg-bg-primary border border-border rounded px-2 py-1 text-sm w-full"
                  />
                  <input
                    type="number"
                    min={0}
                    max={1}
                    step={0.05}
                    value={c.max}
                    onChange={(e) =>
                      updateConstraint(c.ticker, "max", e.target.value)
                    }
                    placeholder="1"
                    className="bg-bg-primary border border-border rounded px-2 py-1 text-sm w-full"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

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
          {loading ? "Computing..." : "Compute Frontier"}
        </button>
      </form>

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
            <div className="bg-bg-card border border-border rounded-lg p-5">
              <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
                Risk / Return
              </h2>
              <FrontierScatter
                points={scatterPoints}
                onSelect={handleSelectPoint}
                selectedIndex={selectedIndex}
              />
              <div className="flex flex-wrap gap-4 mt-3 text-xs text-text-muted">
                <LegendDot color="#34d399" label="Min Volatility" />
                <LegendDot color="#fbbf24" label="Max Sharpe" />
                <LegendDot color="#a78bfa" label="Equal Weight" />
                <LegendDot color="#4f8ff7" label="Frontier" />
              </div>
            </div>

            <div className="bg-bg-card border border-border rounded-lg p-5">
              <h2 className="text-sm font-semibold text-text-secondary uppercase tracking-wider mb-4">
                {selected ? "Selected Portfolio" : "Click a point"}
              </h2>
              {selected ? (
                <>
                  <div className="grid grid-cols-1 gap-2 mb-4">
                    <MetricCard
                      label="Return"
                      value={pct(selected.expected_return)}
                      color="text-green"
                    />
                    <MetricCard
                      label="Volatility"
                      value={pct(selected.expected_volatility)}
                    />
                    <MetricCard
                      label="Sharpe"
                      value={selected.sharpe_ratio.toFixed(2)}
                      color={sharpeColor(selected.sharpe_ratio)}
                    />
                  </div>
                  <table className="w-full">
                    <thead>
                      <tr className="text-text-muted text-xs uppercase border-b border-border">
                        <th className="text-left pb-2">Ticker</th>
                        <th className="text-right pb-2">Weight</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedWeights.map(([ticker, w]) => (
                        <tr key={ticker} className="border-b border-border/50">
                          <td className="py-2 font-mono text-sm">{ticker}</td>
                          <td className="py-2 text-right font-mono text-sm text-text-secondary">
                            {(w * 100).toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              ) : (
                <p className="text-text-muted text-sm">
                  Select a point on the scatter to see its weights.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className="inline-block w-2.5 h-2.5 rounded-full"
        style={{ background: color }}
      />
      {label}
    </span>
  );
}
