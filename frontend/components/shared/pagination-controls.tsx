import Link from "next/link";

import { buildSearchPath, type ResolvedSearchParams } from "@/lib/search-params";

export function PaginationControls({
  pathname,
  searchParams,
  page,
  totalPages,
}: {
  pathname: string;
  searchParams: ResolvedSearchParams;
  page: number;
  totalPages: number;
}) {
  if (totalPages <= 1) {
    return null;
  }

  const previousHref = buildSearchPath(pathname, searchParams, { page: page - 1 });
  const nextHref = buildSearchPath(pathname, searchParams, { page: page + 1 });

  return (
    <div className="flex items-center justify-between gap-4 rounded-[1.25rem] border border-line bg-white/70 px-4 py-3 text-sm">
      <p className="text-muted">
        Page {page} of {totalPages}
      </p>
      <div className="flex gap-2">
        {page > 1 ? (
          <Link className="app-button app-button-secondary" href={previousHref}>
            Previous
          </Link>
        ) : (
          <span className="app-button app-button-secondary cursor-not-allowed opacity-60">Previous</span>
        )}
        {page < totalPages ? (
          <Link className="app-button app-button-secondary" href={nextHref}>
            Next
          </Link>
        ) : (
          <span className="app-button app-button-secondary cursor-not-allowed opacity-60">Next</span>
        )}
      </div>
    </div>
  );
}
