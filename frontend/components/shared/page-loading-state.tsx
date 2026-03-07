function SkeletonBlock({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-[1.25rem] bg-[rgba(217,208,194,0.55)] ${className}`} />;
}

export function PageLoadingState() {
  return (
    <div className="grid gap-4">
      <div className="app-panel p-5">
        <SkeletonBlock className="h-7 w-40" />
        <SkeletonBlock className="mt-3 h-4 w-72 max-w-full" />
        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <SkeletonBlock className="h-11" />
          <SkeletonBlock className="h-11" />
          <SkeletonBlock className="h-11" />
          <SkeletonBlock className="h-11" />
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SkeletonBlock className="h-36" />
        <SkeletonBlock className="h-36" />
        <SkeletonBlock className="h-36" />
        <SkeletonBlock className="h-36" />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <SkeletonBlock className="h-80" />
        <SkeletonBlock className="h-80" />
      </div>
    </div>
  );
}
