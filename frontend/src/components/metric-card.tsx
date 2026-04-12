export function MetricCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-4">
      <p className="text-text-muted text-xs uppercase tracking-wider">{label}</p>
      <p className={`text-xl font-mono font-semibold mt-1 ${color || "text-text-primary"}`}>
        {value}
      </p>
    </div>
  );
}
