"use client";

import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { COLORS, TOOLTIP_STYLE } from "@/lib/chart-utils";

export interface AllocationSlice {
  name: string;
  value: number;
}

interface Props {
  data: AllocationSlice[];
  height?: number;
}

export function AllocationPie({ data, height = 250 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          dataKey="value"
          stroke="none"
          label={({ name, value }) => `${name} ${Number(value).toFixed(0)}%`}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          {...TOOLTIP_STYLE}
          formatter={(value) => `${Number(value).toFixed(1)}%`}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
