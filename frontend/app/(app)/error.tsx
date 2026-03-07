"use client";

import { useEffect } from "react";

import { PageErrorState } from "@/components/shared/page-error-state";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <PageErrorState
      description={error.message || "The latest request to the backend failed. Retry once the API is reachable again."}
      onRetry={reset}
    />
  );
}
