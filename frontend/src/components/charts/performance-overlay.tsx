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

export function PerformanceOverlay({ series, height = 320 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRefs = useRef<ISeriesApi<"Line">[]>([]);

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

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
      seriesRefs.current = [];
    };
  }, [height]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    for (const s of seriesRefs.current) {
      chart.removeSeries(s);
    }
    seriesRefs.current = [];

    series.forEach((s, i) => {
      const line = chart.addSeries(LineSeries, {
        color: COLORS[i % COLORS.length],
        lineWidth: 2,
        priceFormat: { type: "percent", precision: 2, minMove: 0.01 },
      });
      line.setData(
        s.data.map((p) => ({
          time: toTimestamp(p.date),
          value: p.value * 100,
        }))
      );
      seriesRefs.current.push(line);
    });
    chart.timeScale().fitContent();
  }, [series]);

  return (
    <div>
      <div ref={containerRef} style={{ width: "100%", height }} />
      <div className="flex flex-wrap gap-4 mt-3 text-xs text-text-muted">
        {series.map((s, i) => (
          <span key={s.name} className="flex items-center gap-1.5">
            <span
              className="inline-block w-3 h-0.5"
              style={{ background: COLORS[i % COLORS.length] }}
            />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}
