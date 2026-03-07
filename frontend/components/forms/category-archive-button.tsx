"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { browserApi } from "@/lib/api/browser";

export function CategoryArchiveButton({
  categoryId,
  disabled = false,
}: {
  categoryId: string;
  disabled?: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="grid gap-2">
      <button
        type="button"
        className="app-button app-button-danger text-xs"
        onClick={() => {
          setPending(true);
          setError(null);
          startTransition(async () => {
            try {
              await browserApi.categories.archive(categoryId);
              router.refresh();
            } catch (submissionError) {
              setError(submissionError instanceof Error ? submissionError.message : "Unable to archive category");
            } finally {
              setPending(false);
            }
          });
        }}
        disabled={disabled || pending}
      >
        {pending ? "Archiving..." : disabled ? "Archived" : "Archive"}
      </button>
      {error ? <p className="text-xs text-danger">{error}</p> : null}
    </div>
  );
}
