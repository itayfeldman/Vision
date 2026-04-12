"use client";

import { useEffect, useRef } from "react";
import {
  ColorType,
  LineSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { CHART_COLORS, COLORS } from "@/lib/chart-utils";

export interface OverlaySeries {
  name: string;
  data: { date: string; value: number }[];
}

interface Props {
  series: OverlaySeries[];
  height?: number;
}

function toTimestamp(iso: string): UTCTimestamp {
  return Math.floor(new Date(iso).getTime() / 1000) as UTCTimestamp;
}

function toChartData(data: OverlaySeries["data"]) {
  return data.map((p) => ({ time: toTimestamp(p.date), value: p.value * 100 }));
}

/** Deterministic color for a series name — stable across renders, no state needed. */
function seriesColor(name: string): string {
  let h = 5381;
  for (let i = 0; i < name.length; i++) h = ((h << 5) + h) ^ name.charCodeAt(i);
  return COLORS[Math.abs(h) % COLORS.length];
}

export function PerformanceOverlay({ series, height = 320 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const lineMapRef = useRef<Map<string, ISeriesApi<"Line">>>(new Map());

  // Chart init / teardown.
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: CHART_COLORS.textMuted,
        fontSize: 11,
      },
      grid: {
        vertLines: { color: CHART_COLORS.border },
        horzLines: { color: CHART_COLORS.border },
      },
      rightPriceScale: { borderColor: CHART_COLORS.border },
      timeScale: { borderColor: CHART_COLORS.border, timeVisible: false },
      crosshair: { mode: 1 },
    });
    chartRef.current = chart;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);

    const lineMap = lineMapRef.current;
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
      lineMap.clear();
    };
  }, [height]);

  // Reconcile series — preserves chart zoom/pan on data-only updates.
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const incomingNames = new Set(series.map((s) => s.name));
    const lineMap = lineMapRef.current;

    // Remove stale.
    for (const [name, api] of lineMap) {
      if (!incomingNames.has(name)) {
        chart.removeSeries(api);
        lineMap.delete(name);
      }
    }

    // Add new / update existing.
    let didAdd = false;
    for (const s of series) {
      const existing = lineMap.get(s.name);
      if (existing) {
        existing.setData(toChartData(s.data));
      } else {
        const color = seriesColor(s.name);
        const line = chart.addSeries(LineSeries, {
          color,
          lineWidth: 2,
          priceFormat: { type: "percent", precision: 2, minMove: 0.01 },
        });
        line.setData(toChartData(s.data));
        lineMap.set(s.name, line);
        didAdd = true;
      }
    }

    if (didAdd) chart.timeScale().fitContent();
  }, [series]);

  return (
    <div>
      <div ref={containerRef} style={{ width: "100%", height }} />
      <div className="flex flex-wrap gap-4 mt-3 text-xs text-text-muted">
        {series.map((s) => (
          <span key={s.name} className="flex items-center gap-1.5">
            <span
              className="inline-block w-3 h-0.5"
              style={{ background: seriesColor(s.name) }}
            />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}
