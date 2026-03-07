"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { CategorySelect } from "@/components/shared/category-select";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusPill } from "@/components/shared/status-pill";
import { browserApi } from "@/lib/api/browser";
import type {
  CategoryRead,
  RuleMatchType,
  TransactionBulkUpdatePayload,
  TransactionRead,
  TransactionUpdatePayload,
} from "@/lib/api/types";
import { cn, formatCurrency, formatDate, formatDecimal } from "@/lib/utils";

type BulkActionState = "assign" | "review" | null;

interface RuleDraft {
  transactionId: string;
  matchType: RuleMatchType;
  matchValue: string;
}

interface RetryMutation {
  label: string;
  run: () => Promise<void>;
}

function findCategorySummary(
  categories: CategoryRead[],
  categoryId: string | null | undefined,
): TransactionRead["category"] {
  if (!categoryId) {
    return null;
  }
  const category = categories.find((item) => item.id === categoryId);
  return category ? { id: category.id, name: category.name } : null;
}

function getDefaultRuleValue(
  transaction: TransactionRead,
  matchType: RuleMatchType,
): string {
  if (matchType === "merchant_equals") {
    return transaction.normalized_merchant;
  }
  return transaction.raw_description;
}

function applyLocalTransactionUpdate(
  transaction: TransactionRead,
  categories: CategoryRead[],
  payload: TransactionUpdatePayload | TransactionBulkUpdatePayload,
): TransactionRead {
  let nextTransaction = transaction;

  if (payload.category_id !== undefined && payload.category_id !== null) {
    nextTransaction = {
      ...nextTransaction,
      category: findCategorySummary(categories, payload.category_id),
      category_source: "manual",
      category_confidence: "1.0000",
      category_explanation: null,
    };
  }

  if (payload.review_required !== undefined) {
    nextTransaction = {
      ...nextTransaction,
      review_required: payload.review_required,
    };
  }

  return nextTransaction;
}

export function TransactionTable({
  transactions,
  categories,
  showCardColumn = true,
  emptyTitle = "No transactions found",
  emptyDescription = "No transactions match the current filter set.",
  reviewOnlyMode = false,
}: {
  transactions: TransactionRead[];
  categories: CategoryRead[];
  showCardColumn?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  reviewOnlyMode?: boolean;
}) {
  const router = useRouter();
  const [rows, setRows] = useState(transactions);
  const rowsRef = useRef(transactions);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkCategoryId, setBulkCategoryId] = useState<string | null>(null);
  const [pendingRowId, setPendingRowId] = useState<string | null>(null);
  const [pendingBulkAction, setPendingBulkAction] = useState<BulkActionState>(null);
  const [pendingRuleId, setPendingRuleId] = useState<string | null>(null);
  const [activeRuleDraft, setActiveRuleDraft] = useState<RuleDraft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const retryRef = useRef<RetryMutation | null>(null);

  useEffect(() => {
    rowsRef.current = transactions;
    setRows(transactions);
    setSelectedIds((currentSelection) =>
      currentSelection.filter((transactionId) =>
        transactions.some((transaction) => transaction.id === transactionId),
      ),
    );
    setActiveRuleDraft((currentDraft) =>
      currentDraft &&
      transactions.some((transaction) => transaction.id === currentDraft.transactionId)
        ? currentDraft
        : null,
    );
  }, [transactions]);

  const selectedCount = selectedIds.length;
  const reviewCount = rows.filter((transaction) => transaction.review_required).length;
  const allSelected = rows.length > 0 && selectedCount === rows.length;
  const columnCount = showCardColumn ? 9 : 8;

  function commitRows(nextRows: TransactionRead[]) {
    rowsRef.current = nextRows;
    setRows(nextRows);
    setSelectedIds((currentSelection) =>
      currentSelection.filter((transactionId) =>
        nextRows.some((transaction) => transaction.id === transactionId),
      ),
    );
    setActiveRuleDraft((currentDraft) =>
      currentDraft &&
      nextRows.some((transaction) => transaction.id === currentDraft.transactionId)
        ? currentDraft
        : null,
    );
  }

  function syncUpdatedRow(updatedTransaction: TransactionRead) {
    const nextRows = reviewOnlyMode && !updatedTransaction.review_required
      ? rowsRef.current.filter((transaction) => transaction.id !== updatedTransaction.id)
      : rowsRef.current.map((transaction) =>
          transaction.id === updatedTransaction.id ? updatedTransaction : transaction,
        );
    commitRows(nextRows);
  }

  async function performMutation(run: () => Promise<void>, retryLabel: string) {
    setError(null);
    try {
      await run();
      retryRef.current = null;
    } catch (mutationError) {
      setError(
        mutationError instanceof Error
          ? mutationError.message
          : "Unable to update transactions",
      );
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

  async function updateTransaction(
    transactionId: string,
    payload: TransactionUpdatePayload,
    retryLabel = "Retry transaction update",
  ) {
    const run = async () => {
      setPendingRowId(transactionId);
      try {
        const result = await browserApi.transactions.update(transactionId, payload);
        syncUpdatedRow(result.data);
        router.refresh();
      } finally {
        setPendingRowId(null);
      }
    };

    await performMutation(run, retryLabel);
  }

  async function bulkUpdateTransactions(
    payload: TransactionBulkUpdatePayload,
    action: Exclude<BulkActionState, null>,
  ) {
    const selectedSet = new Set(payload.transaction_ids);
    const run = async () => {
      setPendingBulkAction(action);
      try {
        await browserApi.transactions.bulkUpdate(payload);
        const nextRows = rowsRef.current
          .map((transaction) => {
            if (!selectedSet.has(transaction.id)) {
              return transaction;
            }
            return applyLocalTransactionUpdate(transaction, categories, payload);
          })
          .filter((transaction) => !(reviewOnlyMode && payload.review_required === false && !transaction.review_required));
        commitRows(nextRows);
        setSelectedIds([]);
        router.refresh();
      } finally {
        setPendingBulkAction(null);
      }
    };

    await performMutation(
      run,
      action === "assign" ? "Retry bulk category update" : "Retry mark reviewed",
    );
  }

  function toggleSelection(transactionId: string) {
    setSelectedIds((currentSelection) =>
      currentSelection.includes(transactionId)
        ? currentSelection.filter((selectedId) => selectedId !== transactionId)
        : [...currentSelection, transactionId],
    );
  }

  function toggleSelectAll() {
    setSelectedIds((currentSelection) =>
      currentSelection.length === rows.length ? [] : rows.map((transaction) => transaction.id),
    );
  }

  function openRuleDraft(transaction: TransactionRead) {
    setError(null);
    retryRef.current = null;
    setActiveRuleDraft({
      transactionId: transaction.id,
      matchType: "description_contains",
      matchValue: getDefaultRuleValue(transaction, "description_contains"),
    });
  }

  async function saveRuleFromDraft() {
    if (!activeRuleDraft) {
      return;
    }

    const transaction = rowsRef.current.find(
      (currentTransaction) => currentTransaction.id === activeRuleDraft.transactionId,
    );
    if (!transaction || !transaction.category?.id) {
      setError("Assign a category before creating a reusable rule.");
      retryRef.current = null;
      return;
    }

    const payload: TransactionUpdatePayload = {
      category_id: transaction.category.id,
      review_required: false,
      create_rule: true,
      rule_match_type: activeRuleDraft.matchType,
      rule_match_value: activeRuleDraft.matchValue,
    };

    const run = async () => {
      setPendingRuleId(transaction.id);
      try {
        const result = await browserApi.transactions.update(transaction.id, payload);
        syncUpdatedRow(result.data);
        setActiveRuleDraft(null);
        router.refresh();
      } finally {
        setPendingRuleId(null);
      }
    };

    await performMutation(run, "Retry create rule");
  }

  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} compact />;
  }

  return (
    <div className="app-panel overflow-hidden">
      <div className="border-b border-line bg-white/70 px-4 py-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <p className="text-sm font-medium text-ink">
              {reviewOnlyMode ? "Review queue" : "Transaction review"}
            </p>
            <p className="mt-1 text-sm text-muted">
              {reviewOnlyMode
                ? `${rows.length} transaction${rows.length === 1 ? "" : "s"} remain in this filtered review queue.`
                : reviewCount
                  ? `${reviewCount} transaction${reviewCount === 1 ? "" : "s"} on this page still need review.`
                  : "All visible transactions are currently reviewed."}
            </p>
          </div>

          {selectedCount ? (
            <div className="flex flex-col gap-3 xl:min-w-[36rem] xl:items-end">
              <p className="text-sm text-muted">
                {selectedCount} selected
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <CategorySelect
                  ariaLabel="Bulk category"
                  value={bulkCategoryId}
                  categories={categories}
                  onChange={setBulkCategoryId}
                  disabled={pendingBulkAction !== null}
                  allowEmpty
                  emptyLabel="Assign category"
                  className="min-w-[220px]"
                />
                <button
                  type="button"
                  className="app-button app-button-secondary"
                  onClick={() =>
                    bulkCategoryId
                      ? void bulkUpdateTransactions(
                          {
                            transaction_ids: selectedIds,
                            category_id: bulkCategoryId,
                          },
                          "assign",
                        )
                      : undefined
                  }
                  disabled={!bulkCategoryId || pendingBulkAction !== null}
                >
                  {pendingBulkAction === "assign" ? "Assigning..." : "Assign category"}
                </button>
                <button
                  type="button"
                  className="app-button"
                  onClick={() =>
                    void bulkUpdateTransactions(
                      {
                        transaction_ids: selectedIds,
                        review_required: false,
                      },
                      "review",
                    )
                  }
                  disabled={pendingBulkAction !== null}
                >
                  {pendingBulkAction === "review" ? "Updating..." : "Mark reviewed"}
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted">
              Select rows to bulk assign a category or mark reviewed.
            </p>
          )}
        </div>
      </div>

      {error ? (
        <div className="flex flex-col gap-3 border-b border-line bg-[rgba(157,65,52,0.08)] px-4 py-3 text-sm text-danger md:flex-row md:items-center md:justify-between">
          <p>{error}</p>
          {retryRef.current ? (
            <button
              type="button"
              className="app-button app-button-secondary w-fit"
              onClick={() => void retryLastMutation()}
            >
              Retry
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead className="border-b border-line bg-white/60 text-left text-xs uppercase tracking-[0.18em] text-muted">
            <tr>
              <th className="px-4 py-3">
                <input
                  aria-label="Select all transactions on page"
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleSelectAll}
                />
              </th>
              <th className="px-4 py-3">Date</th>
              {showCardColumn ? <th className="px-4 py-3">Card</th> : null}
              <th className="px-4 py-3">Merchant</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((transaction) => {
              const pending =
                pendingRowId === transaction.id || pendingRuleId === transaction.id;
              const ruleDraftOpen = activeRuleDraft?.transactionId === transaction.id;

              return (
                <FragmentRow
                  key={transaction.id}
                  rowKey={transaction.id}
                  showCardColumn={showCardColumn}
                  columnCount={columnCount}
                  transaction={transaction}
                  selected={selectedIds.includes(transaction.id)}
                  categories={categories}
                  pending={pending}
                  ruleDraftOpen={ruleDraftOpen}
                  activeRuleDraft={activeRuleDraft}
                  onToggleSelection={() => toggleSelection(transaction.id)}
                  onCategoryChange={(categoryId) =>
                    void updateTransaction(
                      transaction.id,
                      { category_id: categoryId },
                      "Retry category update",
                    )
                  }
                  onToggleReview={() =>
                    void updateTransaction(
                      transaction.id,
                      { review_required: !transaction.review_required },
                      transaction.review_required
                        ? "Retry mark reviewed"
                        : "Retry mark for review",
                    )
                  }
                  onToggleRuleDraft={() =>
                    ruleDraftOpen
                      ? setActiveRuleDraft(null)
                      : openRuleDraft(transaction)
                  }
                  onRuleMatchTypeChange={(matchType) =>
                    setActiveRuleDraft((currentDraft) =>
                      currentDraft && currentDraft.transactionId === transaction.id
                        ? {
                            ...currentDraft,
                            matchType,
                            matchValue: getDefaultRuleValue(transaction, matchType),
                          }
                        : currentDraft,
                    )
                  }
                  onRuleMatchValueChange={(matchValue) =>
                    setActiveRuleDraft((currentDraft) =>
                      currentDraft && currentDraft.transactionId === transaction.id
                        ? {
                            ...currentDraft,
                            matchValue,
                          }
                        : currentDraft,
                    )
                  }
                  onSaveRule={() => void saveRuleFromDraft()}
                  onCancelRule={() => setActiveRuleDraft(null)}
                />
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function FragmentRow({
  rowKey,
  showCardColumn,
  columnCount,
  transaction,
  selected,
  categories,
  pending,
  ruleDraftOpen,
  activeRuleDraft,
  onToggleSelection,
  onCategoryChange,
  onToggleReview,
  onToggleRuleDraft,
  onRuleMatchTypeChange,
  onRuleMatchValueChange,
  onSaveRule,
  onCancelRule,
}: {
  rowKey: string;
  showCardColumn: boolean;
  columnCount: number;
  transaction: TransactionRead;
  selected: boolean;
  categories: CategoryRead[];
  pending: boolean;
  ruleDraftOpen: boolean;
  activeRuleDraft: RuleDraft | null;
  onToggleSelection: () => void;
  onCategoryChange: (categoryId: string | null) => void;
  onToggleReview: () => void;
  onToggleRuleDraft: () => void;
  onRuleMatchTypeChange: (matchType: RuleMatchType) => void;
  onRuleMatchValueChange: (matchValue: string) => void;
  onSaveRule: () => void;
  onCancelRule: () => void;
}) {
  return (
    <>
      <tr
        className={cn(
          "border-b border-line/70 last:border-b-0",
          transaction.review_required ? "bg-[rgba(165,109,31,0.06)]" : undefined,
        )}
      >
        <td className="px-4 py-4 align-top">
          <input
            aria-label={`Select ${transaction.normalized_merchant}`}
            type="checkbox"
            checked={selected}
            onChange={onToggleSelection}
          />
        </td>
        <td className="px-4 py-4 align-top">{formatDate(transaction.txn_date)}</td>
        {showCardColumn ? (
          <td className="px-4 py-4 align-top">{transaction.card_name}</td>
        ) : null}
        <td className="px-4 py-4 align-top">
          <p className="font-medium">{transaction.normalized_merchant}</p>
          <p className="mt-1 text-xs text-muted">{transaction.raw_description}</p>
        </td>
        <td className="px-4 py-4 align-top font-medium">
          {formatCurrency(transaction.amount)}
        </td>
        <td className="px-4 py-4 align-top">
          <CategorySelect
            value={transaction.category?.id ?? null}
            categories={categories}
            onChange={onCategoryChange}
            disabled={pending}
            ariaLabel={`Category for ${transaction.normalized_merchant}`}
          />
        </td>
        <td className="px-4 py-4 align-top">
          {transaction.category_confidence !== null
            ? formatDecimal(transaction.category_confidence, 2)
            : "NA"}
        </td>
        <td className="px-4 py-4 align-top">
          {transaction.review_required ? (
            <StatusPill status="pending" />
          ) : (
            <StatusPill status="completed" />
          )}
        </td>
        <td className="px-4 py-4 align-top">
          <div className="flex flex-col items-start gap-2">
            <button
              type="button"
              className="app-button app-button-secondary text-sm"
              onClick={onToggleReview}
              disabled={pending}
            >
              {pending
                ? "Saving..."
                : transaction.review_required
                  ? "Mark reviewed"
                  : "Needs review"}
            </button>
            <button
              type="button"
              className="text-sm font-medium text-accent disabled:cursor-not-allowed disabled:text-muted"
              onClick={onToggleRuleDraft}
              disabled={pending || !transaction.category}
            >
              {ruleDraftOpen ? "Cancel rule" : "Create rule"}
            </button>
          </div>
        </td>
      </tr>

      {ruleDraftOpen && activeRuleDraft ? (
        <tr key={`${rowKey}-rule`} className="border-b border-line/70 bg-white/80">
          <td colSpan={columnCount} className="px-4 pb-4 pt-0">
            <div className="rounded-[1.25rem] border border-line bg-[rgba(247,243,236,0.88)] p-4">
              <div className="flex flex-col gap-3">
                <div>
                  <h4 className="font-medium">Create reusable rule</h4>
                  <p className="mt-1 text-sm text-muted">
                    Save this correction so future matching does not need the same manual review.
                  </p>
                </div>
                <div className="grid gap-3 md:grid-cols-[220px_minmax(0,1fr)_auto_auto]">
                  <label className="grid gap-2 text-sm text-muted">
                    <span>Match type</span>
                    <select
                      aria-label="Rule match type"
                      className="app-select"
                      value={activeRuleDraft.matchType}
                      onChange={(event) =>
                        onRuleMatchTypeChange(event.target.value as RuleMatchType)
                      }
                      disabled={pending}
                    >
                      <option value="description_contains">Description contains</option>
                      <option value="merchant_equals">Merchant equals</option>
                      <option value="regex">Regex</option>
                    </select>
                  </label>
                  <label className="grid gap-2 text-sm text-muted">
                    <span>Match value</span>
                    <input
                      aria-label="Rule match value"
                      className="app-input"
                      value={activeRuleDraft.matchValue}
                      onChange={(event) => onRuleMatchValueChange(event.target.value)}
                      disabled={pending}
                    />
                  </label>
                  <button
                    type="button"
                    className="app-button self-end"
                    onClick={onSaveRule}
                    disabled={pending || !activeRuleDraft.matchValue.trim()}
                  >
                    {pending ? "Saving..." : "Save rule"}
                  </button>
                  <button
                    type="button"
                    className="app-button app-button-secondary self-end"
                    onClick={onCancelRule}
                    disabled={pending}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </td>
        </tr>
      ) : null}
    </>
  );
}
