"use client";

export function PageErrorState({
  title = "Unable to load this screen",
  description = "The latest request to the backend failed. Retry once the API is reachable again.",
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry: () => void;
}) {
  return (
    <div className="app-panel mx-auto max-w-2xl p-8 text-center">
      <h2 className="font-display text-2xl font-semibold tracking-tight">{title}</h2>
      <p className="mt-3 text-sm text-muted">{description}</p>
      <div className="mt-6">
        <button className="app-button" type="button" onClick={onRetry}>
          Retry
        </button>
      </div>
    </div>
  );
}
