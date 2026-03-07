export function TopFilterBar({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <section className="app-panel p-5">
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="font-display text-2xl font-semibold tracking-tight">{title}</h2>
          {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
        </div>
        {children}
      </div>
    </section>
  );
}
