"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS, TOOLTIP_STYLE, pct } from "@/lib/chart-utils";

export interface SpreadBar {
  date: string;
  spread: number;
}

interface Props {
  data: SpreadBar[];
  height?: number;
}

export function SpreadBars({ data, height = 180 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: CHART_COLORS.textMuted, fontSize: 11 }}
          tickFormatter={(d: string) => d.slice(0, 7)}
          interval="preserveStartEnd"
          minTickGap={60}
        />
        <YAxis
          tick={{ fill: CHART_COLORS.textMuted, fontSize: 11 }}
          tickFormatter={(v: number) => `${(v * 100).toFixed(1)}%`}
          width={55}
        />
        <Tooltip
          {...TOOLTIP_STYLE}
          labelFormatter={(d) => String(d)}
          formatter={(value) => pct(Number(value))}
        />
        <Bar dataKey="spread">
          {data.map((d, i) => (
            <Cell
              key={i}
              fill={d.spread >= 0 ? CHART_COLORS.green : CHART_COLORS.red}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
