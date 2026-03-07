import Link from "next/link";

export function EmptyState({
  title,
  description,
  actionHref,
  actionLabel,
  compact = false,
}: {
  title: string;
  description: string;
  actionHref?: string;
  actionLabel?: string;
  compact?: boolean;
}) {
  return (
    <div
      className={[
        "rounded-[1.25rem] border border-dashed border-line bg-white/60 text-center",
        compact ? "px-4 py-6" : "px-6 py-10",
      ].join(" ")}
    >
      <h3 className="font-display text-xl font-semibold tracking-tight">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm text-muted">{description}</p>
      {actionHref && actionLabel ? (
        <div className="mt-5">
          <Link className="app-button" href={actionHref}>
            {actionLabel}
          </Link>
        </div>
      ) : null}
    </div>
  );
}
