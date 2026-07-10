// components/ui-kit/StatCard.tsx
import { LucideIcon } from "lucide-react";
import Link from "next/link";

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "neutral",
  hint,
  href,
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "neutral" | "success" | "danger" | "warning" | "brand";
  hint?: string;
  href?: string;
}) {
  const tones = {
    neutral: "bg-slate-50 text-slate-600",
    success: "bg-emerald-50 text-emerald-600",
    danger: "bg-red-50 text-red-600",
    warning: "bg-amber-50 text-amber-600",
    brand: "bg-teal-50 text-teal-600",
  };

  const contenu = (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all ${
        href ? "cursor-pointer hover:border-teal-300 hover:shadow-md" : "hover:shadow-md"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {label}
        </span>
        <div className={`rounded-lg p-2 ${tones[tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="mt-3 text-2xl font-semibold text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );

  if (href) {
    return <Link href={href}>{contenu}</Link>;
  }
  return contenu;
}