// components/ui-kit/ProgressBar.tsx
export function ProgressBar({
  value,
  max = 100,
  tone = "brand",
}: {
  value: number;
  max?: number;
  tone?: "brand" | "success" | "danger" | "warning";
}) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  const tones = {
    brand: "bg-teal-500",
    success: "bg-emerald-500",
    danger: "bg-red-500",
    warning: "bg-amber-500",
  };
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full transition-all duration-500 ${tones[tone]}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}