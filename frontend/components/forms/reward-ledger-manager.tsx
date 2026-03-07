"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { EmptyState } from "@/components/shared/empty-state";
import { StatusPill } from "@/components/shared/status-pill";
import { browserApi } from "@/lib/api/browser";
import type {
  RewardEventType,
  RewardLedgerCreatePayload,
  RewardLedgerRead,
  RewardLedgerUpdatePayload,
} from "@/lib/api/types";
import { formatCurrency, formatDate, formatDecimal } from "@/lib/utils";

interface RetryMutation {
  label: string;
  run: () => Promise<void>;
}

interface RewardLedgerDraft {
  event_date: string;
  event_type: RewardEventType;
  reward_points: string;
  reward_value_estimate: string;
  notes: string;
}

type FormMode =
  | { kind: "closed" }
  | { kind: "create" }
  | { kind: "edit"; rewardLedgerId: string };

const EVENT_TYPE_OPTIONS: Array<{ value: RewardEventType; label: string }> = [
  { value: "adjusted", label: "Adjusted" },
  { value: "earned", label: "Earned" },
  { value: "cashback", label: "Cashback" },
  { value: "redeemed", label: "Redeemed" },
  { value: "expired", label: "Expired" },
];

const DEFAULT_DRAFT: RewardLedgerDraft = {
  event_date: "",
  event_type: "adjusted",
  reward_points: "",
  reward_value_estimate: "",
  notes: "",
};

function sortRewardEvents(events: RewardLedgerRead[]): RewardLedgerRead[] {
  return [...events].sort((left, right) => {
    const dateComparison = right.event_date.localeCompare(left.event_date);
    if (dateComparison !== 0) {
      return dateComparison;
    }
    return right.created_at.localeCompare(left.created_at);
  });
}

function buildDraftFromEvent(event: RewardLedgerRead): RewardLedgerDraft {
  return {
    event_date: event.event_date,
    event_type: event.event_type,
    reward_points: event.reward_points === null ? "" : String(event.reward_points),
    reward_value_estimate: event.reward_value_estimate === null ? "" : String(event.reward_value_estimate),
    notes: event.notes || "",
  };
}

function buildCreatePayload(cardId: string, draft: RewardLedgerDraft): RewardLedgerCreatePayload | null {
  const rewardPoints = draft.reward_points.trim();
  const rewardValue = draft.reward_value_estimate.trim();
  if (!draft.event_date || (!rewardPoints && !rewardValue)) {
    return null;
  }

  return {
    card_id: cardId,
    event_date: draft.event_date,
    event_type: draft.event_type,
    reward_points: rewardPoints || null,
    reward_value_estimate: rewardValue || null,
    source: "manual",
    notes: draft.notes.trim() || null,
  };
}

function buildUpdatePayload(draft: RewardLedgerDraft): RewardLedgerUpdatePayload | null {
  const rewardPoints = draft.reward_points.trim();
  const rewardValue = draft.reward_value_estimate.trim();
  if (!draft.event_date || (!rewardPoints && !rewardValue)) {
    return null;
  }

  return {
    event_date: draft.event_date,
    event_type: draft.event_type,
    reward_points: rewardPoints || null,
    reward_value_estimate: rewardValue || null,
    source: "manual",
    notes: draft.notes.trim() || null,
  };
}

export function RewardLedgerManager({
  cardId,
  rewardEvents,
}: {
  cardId: string;
  rewardEvents: RewardLedgerRead[];
}) {
  const router = useRouter();
  const [rows, setRows] = useState(() => sortRewardEvents(rewardEvents));
  const rowsRef = useRef(rows);
  const [formMode, setFormMode] = useState<FormMode>({ kind: "closed" });
  const [draft, setDraft] = useState<RewardLedgerDraft>(DEFAULT_DRAFT);
  const [pendingSave, setPendingSave] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const retryRef = useRef<RetryMutation | null>(null);
  const editingRewardLedgerId = formMode.kind === "edit" ? formMode.rewardLedgerId : null;

  useEffect(() => {
    const nextRows = sortRewardEvents(rewardEvents);
    rowsRef.current = nextRows;
    setRows(nextRows);
  }, [rewardEvents]);

  useEffect(() => {
    if (editingRewardLedgerId) {
      const currentEvent = rewardEvents.find((event) => event.id === editingRewardLedgerId);
      if (!currentEvent) {
        setFormMode({ kind: "closed" });
        setDraft(DEFAULT_DRAFT);
      }
    }
  }, [editingRewardLedgerId, rewardEvents]);

  function commitRows(nextRows: RewardLedgerRead[]) {
    const sortedRows = sortRewardEvents(nextRows);
    rowsRef.current = sortedRows;
    setRows(sortedRows);
  }

  function openCreateForm() {
    setError(null);
    retryRef.current = null;
    setFormMode({ kind: "create" });
    setDraft(DEFAULT_DRAFT);
  }

  function openEditForm(event: RewardLedgerRead) {
    setError(null);
    retryRef.current = null;
    setFormMode({ kind: "edit", rewardLedgerId: event.id });
    setDraft(buildDraftFromEvent(event));
  }

  function closeForm() {
    setFormMode({ kind: "closed" });
    setDraft(DEFAULT_DRAFT);
  }

  async function performMutation(run: () => Promise<void>, retryLabel: string) {
    setError(null);
    try {
      await run();
      retryRef.current = null;
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Unable to update reward events");
      retryRef.current = {
        label: retryLabel,
        run,
      };
    }
  }

  async function retryLastMutation() {
    if (!retryRef.current) {
      return;
    }
    await performMutation(retryRef.current.run, retryRef.current.label);
  }

  async function handleSubmit() {
    if (formMode.kind === "edit") {
      const payload = buildUpdatePayload(draft);
      if (!payload) {
        setError("Enter an event date and at least reward points or reward value.");
        retryRef.current = null;
        return;
      }

      const run = async () => {
        setPendingSave(true);
        try {
          const result = await browserApi.rewardLedgers.update(formMode.rewardLedgerId, payload);
          commitRows(
            rowsRef.current.map((event) =>
              event.id === result.data.id ? result.data : event,
            ),
          );
          closeForm();
          router.refresh();
        } finally {
          setPendingSave(false);
        }
      };

      await performMutation(run, "Retry reward update");
      return;
    }

    const payload = buildCreatePayload(cardId, draft);
    if (!payload) {
      setError("Enter an event date and at least reward points or reward value.");
      retryRef.current = null;
      return;
    }

    const run = async () => {
      setPendingSave(true);
      try {
        const result = await browserApi.rewardLedgers.create(payload);
        commitRows([result.data, ...rowsRef.current]);
        closeForm();
        router.refresh();
      } finally {
        setPendingSave(false);
      }
    };

    await performMutation(run, "Retry reward creation");
  }

  async function deleteRewardEvent(rewardLedgerId: string) {
    const run = async () => {
      setPendingDeleteId(rewardLedgerId);
      try {
        await browserApi.rewardLedgers.remove(rewardLedgerId);
        commitRows(rowsRef.current.filter((event) => event.id !== rewardLedgerId));
        if (formMode.kind === "edit" && formMode.rewardLedgerId === rewardLedgerId) {
          closeForm();
        }
        router.refresh();
      } finally {
        setPendingDeleteId(null);
      }
    };

    await performMutation(run, "Retry reward deletion");
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium text-ink">Reward event management</p>
          <p className="mt-1 text-sm text-muted">
            Imported rows stay read-only. Manual entries refresh the card reward summary after save.
          </p>
        </div>
        <button
          type="button"
          className="app-button w-fit"
          onClick={openCreateForm}
          disabled={pendingSave || pendingDeleteId !== null || formMode.kind !== "closed"}
        >
          Add reward entry
        </button>
      </div>

      {error ? (
        <div className="rounded-2xl border border-danger/20 bg-danger/5 px-4 py-3">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <p className="text-sm text-danger">{error}</p>
            {retryRef.current ? (
              <button
                type="button"
                className="app-button app-button-secondary"
                onClick={() => void retryLastMutation()}
                disabled={pendingSave || pendingDeleteId !== null}
              >
                Retry
              </button>
            ) : null}
          </div>
        </div>
      ) : null}

      {formMode.kind !== "closed" ? (
        <div className="rounded-[1.5rem] border border-line bg-white/70 p-4">
          <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="font-display text-xl font-semibold tracking-tight">
                {formMode.kind === "edit" ? "Edit reward entry" : "Add reward entry"}
              </h3>
              <p className="mt-1 text-sm text-muted">
                Enter a manual reward event or correction for this card.
              </p>
            </div>
            <button
              type="button"
              className="app-button app-button-secondary"
              onClick={closeForm}
              disabled={pendingSave}
            >
              Cancel
            </button>
          </div>

          <form
            className="grid gap-4"
            onSubmit={(event) => {
              event.preventDefault();
              void handleSubmit();
            }}
          >
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <label className="grid gap-2 text-sm font-medium text-ink">
                Event date
                <input
                  className="app-input"
                  type="date"
                  value={draft.event_date}
                  onChange={(event) =>
                    setDraft((currentDraft) => ({
                      ...currentDraft,
                      event_date: event.target.value,
                    }))
                  }
                  disabled={pendingSave}
                />
              </label>

              <label className="grid gap-2 text-sm font-medium text-ink">
                Event type
                <select
                  className="app-select"
                  value={draft.event_type}
                  onChange={(event) =>
                    setDraft((currentDraft) => ({
                      ...currentDraft,
                      event_type: event.target.value as RewardEventType,
                    }))
                  }
                  disabled={pendingSave}
                >
                  {EVENT_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-2 text-sm font-medium text-ink">
                Reward points
                <input
                  className="app-input"
                  type="number"
                  step="0.01"
                  inputMode="decimal"
                  value={draft.reward_points}
                  onChange={(event) =>
                    setDraft((currentDraft) => ({
                      ...currentDraft,
                      reward_points: event.target.value,
                    }))
                  }
                  disabled={pendingSave}
                  placeholder="1200"
                />
              </label>

              <label className="grid gap-2 text-sm font-medium text-ink">
                Reward value
                <input
                  className="app-input"
                  type="number"
                  step="0.01"
                  inputMode="decimal"
                  value={draft.reward_value_estimate}
                  onChange={(event) =>
                    setDraft((currentDraft) => ({
                      ...currentDraft,
                      reward_value_estimate: event.target.value,
                    }))
                  }
                  disabled={pendingSave}
                  placeholder="450"
                />
              </label>
            </div>

            <label className="grid gap-2 text-sm font-medium text-ink">
              Notes
              <textarea
                className="app-input min-h-24 resize-y"
                value={draft.notes}
                onChange={(event) =>
                  setDraft((currentDraft) => ({
                    ...currentDraft,
                    notes: event.target.value,
                  }))
                }
                disabled={pendingSave}
                placeholder="Optional notes about the reward adjustment"
              />
            </label>

            <div className="flex flex-wrap items-center gap-3">
              <button className="app-button" type="submit" disabled={pendingSave}>
                {pendingSave ? "Saving..." : formMode.kind === "edit" ? "Save reward event" : "Create reward event"}
              </button>
              <p className="text-sm text-muted">
                Add at least reward points or reward value. Manual entries are saved with source <code>manual</code>.
              </p>
            </div>
          </form>
        </div>
      ) : null}

      {rows.length ? (
        <div className="grid gap-3">
          {rows.map((event) => {
            const isManual = event.source === "manual";
            const isDeleting = pendingDeleteId === event.id;
            return (
              <div
                key={event.id}
                className="rounded-2xl border border-line bg-white/70 px-4 py-4"
              >
                <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                  <div className="grid gap-3 md:grid-cols-[120px_110px_minmax(0,1fr)] md:items-start">
                    <p className="text-sm text-muted">{formatDate(event.event_date)}</p>
                    <StatusPill status={event.event_type} />
                    <div className="min-w-0">
                      <p className="truncate text-sm text-muted">
                        {event.notes || `Source: ${event.source}`}
                      </p>
                      {!isManual ? (
                        <p className="mt-1 text-xs text-muted">Imported rows are read-only from card detail.</p>
                      ) : null}
                    </div>
                  </div>

                  <div className="flex flex-col gap-3 xl:items-end">
                    <div className="text-left xl:text-right">
                      {event.reward_points !== null ? (
                        <p className="font-medium">{formatDecimal(event.reward_points, 0)} pts</p>
                      ) : null}
                      {event.reward_value_estimate !== null ? (
                        <p className="text-sm text-muted">{formatCurrency(event.reward_value_estimate)}</p>
                      ) : null}
                    </div>

                    {isManual ? (
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          className="app-button app-button-secondary"
                          onClick={() => openEditForm(event)}
                          disabled={pendingSave || pendingDeleteId !== null}
                          aria-label={`Edit ${event.event_type} reward event`}
                        >
                          {editingRewardLedgerId === event.id ? "Editing..." : "Edit"}
                        </button>
                        <button
                          type="button"
                          className="app-button app-button-secondary"
                          onClick={() => void deleteRewardEvent(event.id)}
                          disabled={pendingSave || pendingDeleteId !== null}
                          aria-label={`Delete ${event.event_type} reward event`}
                        >
                          {isDeleting ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : formMode.kind === "closed" ? (
        <EmptyState
          title="No reward events yet"
          description="Manual reward entries and imported reward rows will appear here once they are available."
          compact
        />
      ) : null}
    </div>
  );
}
