import { cn } from "@/lib/utils";

const toneMap: Record<string, string> = {
  completed: "bg-[rgba(36,95,83,0.12)] text-accent",
  active: "bg-[rgba(36,95,83,0.12)] text-accent",
  uploaded: "bg-[rgba(36,95,83,0.12)] text-accent",
  processing: "bg-[rgba(165,109,31,0.12)] text-warning",
  running: "bg-[rgba(165,109,31,0.12)] text-warning",
  failed: "bg-[rgba(157,65,52,0.12)] text-danger",
  archived: "bg-slate-200 text-slate-600",
  pending: "bg-slate-200 text-slate-700",
  earned: "bg-[rgba(36,95,83,0.12)] text-accent",
  cashback: "bg-[rgba(36,95,83,0.12)] text-accent",
  adjusted: "bg-[rgba(165,109,31,0.12)] text-warning",
  redeemed: "bg-slate-200 text-slate-700",
  expired: "bg-[rgba(157,65,52,0.12)] text-danger",
};

export function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]",
        toneMap[normalized] || "bg-slate-200 text-slate-700",
      )}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}
