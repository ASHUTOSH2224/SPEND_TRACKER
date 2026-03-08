"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { browserApi } from "@/lib/api/browser";
import type { StatementRead } from "@/lib/api/types";

export function StatementActions({
  statementId,
  uploadStatus,
}: {
  statementId: string;
  uploadStatus: StatementRead["upload_status"];
}) {
  const router = useRouter();
  const [pendingAction, setPendingAction] = useState<"retry" | "delete" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const canRetry = uploadStatus === "failed";

  function runAction(action: "retry" | "delete") {
    setPendingAction(action);
    setError(null);
    startTransition(async () => {
      try {
        if (action === "retry") {
          await browserApi.statements.retry(statementId);
        } else {
          await browserApi.statements.remove(statementId);
        }
        router.refresh();
      } catch (submissionError) {
        setError(submissionError instanceof Error ? submissionError.message : "Unable to update statement");
      } finally {
        setPendingAction(null);
      }
    });
  }

  return (
    <div className="grid gap-2">
      <div className="flex gap-2">
        {canRetry ? (
          <button
            type="button"
            className="app-button app-button-secondary text-xs"
            onClick={() => runAction("retry")}
            disabled={pendingAction !== null}
          >
            {pendingAction === "retry" ? "Retrying..." : "Retry"}
          </button>
        ) : null}
        <button
          type="button"
          className="app-button app-button-danger text-xs"
          onClick={() => runAction("delete")}
          disabled={pendingAction !== null}
        >
          {pendingAction === "delete" ? "Deleting..." : "Delete"}
        </button>
      </div>
      {error ? <p className="text-xs text-danger">{error}</p> : null}
    </div>
  );
}
