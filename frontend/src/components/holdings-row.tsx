"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { PriceChart } from "@/components/charts/price-chart";
import type { PriceHistory, ValuedHolding } from "@/lib/types";

interface Props {
  holding: ValuedHolding | { ticker: string; weight: number };
  expanded: boolean;
  onToggle: () => void;
  valued: boolean;
  columns: number;
}

function isValued(h: Props["holding"]): h is ValuedHolding {
  return "current_price" in h;
}

const THREE_YEARS_AGO = (() => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 3);
  return d.toISOString().slice(0, 10);
})();

export function HoldingsRow({
  holding,
  expanded,
  onToggle,
  valued,
  columns,
}: Props) {
  const [prices, setPrices] = useState<PriceHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Guards state updates after unmount and in-flight request cancellation.
  const mountedRef = useRef(true);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  function handleToggle() {
    const wasExpanded = expanded;
    onToggle();
    if (!wasExpanded && !prices && !loading) {
      // Cancel any previous in-flight request for this row.
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);
      api.marketData
        .prices(holding.ticker, THREE_YEARS_AGO, undefined, controller.signal)
        .then((p) => {
          if (mountedRef.current) setPrices(p);
        })
        .catch((e: Error) => {
          if (mountedRef.current && !controller.signal.aborted) {
            setError(e.message);
          }
        })
        .finally(() => {
          if (mountedRef.current) setLoading(false);
        });
    }
  }

  const chartData = prices
    ? prices.dates.map((d, i) => ({ date: d, price: prices.close_prices[i] }))
    : [];

  return (
    <>
      <tr
        className="border-b border-border/50 hover:bg-bg-hover/30 cursor-pointer transition-colors"
        onClick={handleToggle}
      >
        <td className="py-2.5 pl-2">
          <span
            className={`inline-block text-text-muted transition-transform ${
              expanded ? "rotate-90" : ""
            }`}
          >
            &rsaquo;
          </span>
        </td>
        <td className="py-2.5 font-mono font-medium">{holding.ticker}</td>
        <td className="py-2.5 text-right font-mono text-text-secondary">
          {(holding.weight * 100).toFixed(1)}%
        </td>
        {valued && isValued(holding) && (
          <>
            <td className="py-2.5 text-right font-mono text-text-secondary">
              ${holding.current_price.toFixed(2)}
            </td>
            <td className="py-2.5 text-right font-mono text-text-secondary">
              ${holding.market_value.toFixed(2)}
            </td>
          </>
        )}
      </tr>
      {expanded && (
        <tr className="border-b border-border/50 bg-bg-primary/40">
          <td colSpan={columns} className="p-4">
            {loading && (
              <div className="flex items-center justify-center h-32">
                <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            )}
            {error && (
              <div className="bg-red/10 border border-red/20 rounded-lg p-3 text-red text-sm">
                {error}
              </div>
            )}
            {!loading && !error && chartData.length > 0 && (
              <>
                <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-2">
                  {holding.ticker} &middot; 3Y Price
                </h3>
                <PriceChart data={chartData} height={220} />
              </>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
