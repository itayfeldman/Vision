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
import { CHART_COLORS, TOOLTIP_STYLE, fmt } from "@/lib/chart-utils";

export interface FactorBar {
  name: string;
  beta: number;
}

interface Props {
  data: FactorBar[];
  height?: number;
}

export function FactorBars({ data, height = 220 }: Props) {
  const colored = data.map((d) => ({
    ...d,
    fill: d.beta >= 0 ? CHART_COLORS.accent : CHART_COLORS.red,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={colored} layout="vertical" margin={{ left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} />
        <XAxis
          type="number"
          tick={{ fill: CHART_COLORS.textMuted, fontSize: 12 }}
        />
        <YAxis
          dataKey="name"
          type="category"
          tick={{ fill: CHART_COLORS.textMuted, fontSize: 12 }}
          width={50}
        />
        <Tooltip
          {...TOOLTIP_STYLE}
          formatter={(value) => fmt(Number(value), 3)}
        />
        <Bar dataKey="beta" radius={[0, 4, 4, 0]}>
          {colored.map((entry, i) => (
            <Cell key={i} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
