"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { browserApi } from "@/lib/api/browser";

export function CardArchiveButton({
  cardId,
  disabled = false,
}: {
  cardId: string;
  disabled?: boolean;
}) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="grid gap-2">
      <button
        type="button"
        className="app-button app-button-danger"
        onClick={() => {
          setPending(true);
          setError(null);
          startTransition(async () => {
            try {
              await browserApi.cards.archive(cardId);
              router.refresh();
            } catch (submissionError) {
              setError(submissionError instanceof Error ? submissionError.message : "Unable to archive card");
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
