export const CHART_COLORS = {
  accent: "#4f8ff7",
  green: "#34d399",
  red: "#f87171",
  bgCard: "#1a1f2e",
  border: "#2a3142",
  textMuted: "#8b95a5",
  textSecondary: "#e1e4e8",
} as const;

export const COLORS = [
  "#4f8ff7", "#34d399", "#f87171", "#fbbf24",
  "#a78bfa", "#f472b6", "#fb923c", "#38bdf8",
];

export const TOOLTIP_STYLE = {
  contentStyle: {
    background: CHART_COLORS.bgCard,
    border: `1px solid ${CHART_COLORS.border}`,
    borderRadius: 8,
  },
  itemStyle: { color: CHART_COLORS.textSecondary },
};

export function fmt(n: number, decimals = 2) {
  return n.toFixed(decimals);
}

export function pct(n: number) {
  return (n * 100).toFixed(2) + "%";
}

export function sharpeColor(sharpe: number) {
  if (sharpe >= 1) return "text-green";
  if (sharpe >= 0) return "text-yellow";
  return "text-red";
}
