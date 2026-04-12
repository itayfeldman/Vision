"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

interface HoldingRow {
  ticker: string;
  weight: string;
}

export default function NewPortfolio() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [holdings, setHoldings] = useState<HoldingRow[]>([
    { ticker: "", weight: "" },
  ]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const totalWeight = holdings.reduce(
    (sum, h) => sum + (parseFloat(h.weight) || 0),
    0
  );

  function addRow() {
    setHoldings([...holdings, { ticker: "", weight: "" }]);
  }

  function removeRow(i: number) {
    setHoldings(holdings.filter((_, idx) => idx !== i));
  }

  function updateRow(i: number, field: keyof HoldingRow, value: string) {
    const updated = [...holdings];
    updated[i] = { ...updated[i], [field]: value };
    setHoldings(updated);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const parsed = holdings
        .filter((h) => h.ticker && h.weight)
        .map((h) => ({
          ticker: h.ticker.toUpperCase().trim(),
          weight: parseFloat(h.weight) / 100,
        }));

      if (parsed.length === 0) {
        setError("Add at least one holding");
        setSubmitting(false);
        return;
      }

      const portfolio = await api.portfolios.create(name, parsed);
      router.push(`/portfolios/${portfolio.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create portfolio");
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Create Portfolio</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm text-text-secondary mb-2">
            Portfolio Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent"
            placeholder="My Portfolio"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm text-text-secondary">Holdings</label>
            <span
              className={`text-sm font-mono ${
                Math.abs(totalWeight - 100) < 0.01
                  ? "text-green"
                  : "text-yellow"
              }`}
            >
              {totalWeight.toFixed(1)}% / 100%
            </span>
          </div>

          <div className="space-y-2">
            {holdings.map((h, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={h.ticker}
                  onChange={(e) => updateRow(i, "ticker", e.target.value)}
                  className="flex-1 bg-bg-card border border-border rounded-lg px-4 py-2.5 text-text-primary focus:outline-none focus:border-accent uppercase"
                  placeholder="AAPL"
                />
                <div className="relative w-32">
                  <input
                    type="number"
                    value={h.weight}
                    onChange={(e) => updateRow(i, "weight", e.target.value)}
                    className="w-full bg-bg-card border border-border rounded-lg px-4 py-2.5 pr-8 text-text-primary focus:outline-none focus:border-accent"
                    placeholder="50"
                    step="0.1"
                    min="0"
                    max="100"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted text-sm">
                    %
                  </span>
                </div>
                {holdings.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeRow(i)}
                    className="text-text-muted hover:text-red px-2 transition-colors"
                  >
                    &times;
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={addRow}
            className="mt-3 text-sm text-accent hover:text-accent-hover transition-colors"
          >
            + Add holding
          </button>
        </div>

        {error && (
          <div className="bg-red/10 border border-red/20 rounded-lg p-3 text-red text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="bg-accent hover:bg-accent-hover disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          {submitting ? "Creating..." : "Create Portfolio"}
        </button>
      </form>
    </div>
  );
}
