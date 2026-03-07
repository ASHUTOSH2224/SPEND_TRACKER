import { cn } from "@/lib/utils";

export function KpiCard({
  label,
  value,
  helper,
  tone = "default",
}: {
  label: string;
  value: string;
  helper?: string;
  tone?: "default" | "accent" | "danger";
}) {
  return (
    <article
      className={cn(
        "app-panel p-5",
        tone === "accent" && "bg-[linear-gradient(135deg,rgba(36,95,83,0.16),rgba(255,250,240,0.92))]",
        tone === "danger" && "bg-[linear-gradient(135deg,rgba(157,65,52,0.14),rgba(255,250,240,0.92))]",
      )}
    >
      <p className="text-xs uppercase tracking-[0.22em] text-muted">{label}</p>
      <p className="mt-3 font-display text-3xl font-semibold tracking-tight">{value}</p>
      {helper ? <p className="mt-2 text-sm text-muted">{helper}</p> : null}
    </article>
  );
}
