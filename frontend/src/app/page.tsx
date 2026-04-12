"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Portfolio } from "@/lib/types";

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.portfolios
      .list()
      .then(setPortfolios)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red/10 border border-red/20 rounded-lg p-4 text-red">
        {error}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold">Portfolios</h1>
          <p className="text-text-secondary text-sm mt-1">
            {portfolios.length} portfolio{portfolios.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Link
          href="/portfolios/new"
          className="bg-accent hover:bg-accent-hover text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + New Portfolio
        </Link>
      </div>

      {portfolios.length === 0 ? (
        <div className="bg-bg-card border border-border rounded-lg p-12 text-center">
          <p className="text-text-secondary mb-4">No portfolios yet</p>
          <Link
            href="/portfolios/new"
            className="text-accent hover:text-accent-hover transition-colors"
          >
            Create your first portfolio
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {portfolios.map((p) => (
            <Link
              key={p.id}
              href={`/portfolios/${p.id}`}
              className="bg-bg-card border border-border rounded-lg p-5 hover:border-accent/40 transition-colors group"
            >
              <h3 className="font-semibold text-lg group-hover:text-accent transition-colors">
                {p.name}
              </h3>
              <p className="text-text-muted text-sm mt-1">
                {p.holdings.length} holding{p.holdings.length !== 1 ? "s" : ""}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {p.holdings.slice(0, 5).map((h) => (
                  <span
                    key={h.ticker}
                    className="bg-bg-hover text-text-secondary text-xs px-2 py-1 rounded"
                  >
                    {h.ticker}{" "}
                    <span className="text-text-muted">
                      {(h.weight * 100).toFixed(0)}%
                    </span>
                  </span>
                ))}
                {p.holdings.length > 5 && (
                  <span className="text-text-muted text-xs px-2 py-1">
                    +{p.holdings.length - 5} more
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
