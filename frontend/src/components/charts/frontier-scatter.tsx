"use client";

import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { CHART_COLORS, TOOLTIP_STYLE, pct } from "@/lib/chart-utils";

export interface FrontierScatterPoint {
  volatility: number;
  return_: number;
  sharpe: number;
  label?: "min_vol" | "max_sharpe" | "equal_weight" | null;
  index: number;
}

interface Props {
  points: FrontierScatterPoint[];
  onSelect?: (p: FrontierScatterPoint) => void;
  selectedIndex?: number | null;
  height?: number;
}

const NAMED_COLORS: Record<string, string> = {
  min_vol: CHART_COLORS.green,
  max_sharpe: "#fbbf24",
  equal_weight: "#a78bfa",
};

function colorFor(p: FrontierScatterPoint, selected: boolean): string {
  if (selected) return CHART_COLORS.red;
  if (p.label) return NAMED_COLORS[p.label];
  return CHART_COLORS.accent;
}

export function FrontierScatter({
  points,
  onSelect,
  selectedIndex,
  height = 380,
}: Props) {
  const data = points.map((p) => ({
    ...p,
    x: p.volatility * 100,
    y: p.return_ * 100,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 16, right: 16, bottom: 24, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} />
        <XAxis
          type="number"
          dataKey="x"
          name="Volatility"
          unit="%"
          tick={{ fill: CHART_COLORS.textMuted, fontSize: 12 }}
          label={{
            value: "Volatility",
            position: "insideBottom",
            offset: -10,
            fill: CHART_COLORS.textMuted,
            fontSize: 12,
          }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name="Return"
          unit="%"
          tick={{ fill: CHART_COLORS.textMuted, fontSize: 12 }}
          label={{
            value: "Return",
            angle: -90,
            position: "insideLeft",
            fill: CHART_COLORS.textMuted,
            fontSize: 12,
          }}
        />
        <ZAxis range={[80, 80]} />
        <Tooltip
          {...TOOLTIP_STYLE}
          cursor={{ strokeDasharray: "3 3" }}
          formatter={(value, name) => {
            if (name === "Volatility" || name === "Return") {
              return pct(Number(value) / 100);
            }
            return value;
          }}
        />
        <Scatter
          data={data}
          onClick={(pt: unknown) => {
            const p = pt as FrontierScatterPoint;
            onSelect?.(p);
          }}
        >
          {data.map((p, i) => (
            <Cell
              key={i}
              fill={colorFor(p, selectedIndex === p.index)}
              stroke={p.label ? "#fff" : undefined}
              strokeWidth={p.label ? 1.5 : 0}
              style={{ cursor: "pointer" }}
            />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}
