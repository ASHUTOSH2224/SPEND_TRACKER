"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import type { CategoryRead, TransactionRead } from "@/lib/api/types";
import { browserApi } from "@/lib/api/browser";
import { CategorySelect } from "@/components/shared/category-select";
import { StatusPill } from "@/components/shared/status-pill";
import { formatCurrency, formatDate, formatDecimal } from "@/lib/utils";

export function TransactionTable({
  transactions,
  categories,
  showCardColumn = true,
}: {
  transactions: TransactionRead[];
  categories: CategoryRead[];
  showCardColumn?: boolean;
}) {
  const router = useRouter();
  const [rows, setRows] = useState(transactions);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function updateTransaction(
    transactionId: string,
    payload: { category_id?: string | null; review_required?: boolean },
  ) {
    setPendingId(transactionId);
    setError(null);
    startTransition(async () => {
      try {
        const result = await browserApi.transactions.update(transactionId, payload);
        setRows((currentRows) =>
          currentRows.map((row) => (row.id === transactionId ? result.data : row)),
        );
        router.refresh();
      } catch (submissionError) {
        setError(submissionError instanceof Error ? submissionError.message : "Unable to update transaction");
      } finally {
        setPendingId(null);
      }
    });
  }

  if (!rows.length) {
    return (
      <div className="app-panel p-6 text-sm text-muted">
        No transactions match the current filter set.
      </div>
    );
  }

  return (
    <div className="app-panel overflow-hidden">
      {error ? <div className="border-b border-line bg-[rgba(157,65,52,0.08)] px-4 py-3 text-sm text-danger">{error}</div> : null}
      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-sm">
          <thead className="border-b border-line bg-white/60 text-left text-xs uppercase tracking-[0.18em] text-muted">
            <tr>
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
              const pending = pendingId === transaction.id;
              return (
                <tr key={transaction.id} className="border-b border-line/70 last:border-b-0">
                  <td className="px-4 py-4 align-top">{formatDate(transaction.txn_date)}</td>
                  {showCardColumn ? <td className="px-4 py-4 align-top">{transaction.card_name}</td> : null}
                  <td className="px-4 py-4 align-top">
                    <p className="font-medium">{transaction.normalized_merchant}</p>
                    <p className="mt-1 text-xs text-muted">{transaction.raw_description}</p>
                  </td>
                  <td className="px-4 py-4 align-top font-medium">{formatCurrency(transaction.amount)}</td>
                  <td className="px-4 py-4 align-top">
                    <CategorySelect
                      value={transaction.category?.id ?? null}
                      categories={categories}
                      onChange={(categoryId) => updateTransaction(transaction.id, { category_id: categoryId })}
                      disabled={pending}
                    />
                  </td>
                  <td className="px-4 py-4 align-top">
                    {transaction.category_confidence !== null ? formatDecimal(transaction.category_confidence, 2) : "NA"}
                  </td>
                  <td className="px-4 py-4 align-top">
                    {transaction.review_required ? <StatusPill status="pending" /> : <StatusPill status="completed" />}
                  </td>
                  <td className="px-4 py-4 align-top">
                    <button
                      type="button"
                      className="app-button app-button-secondary text-sm"
                      onClick={() =>
                        updateTransaction(transaction.id, {
                          review_required: !transaction.review_required,
                        })
                      }
                      disabled={pending}
                    >
                      {pending
                        ? "Saving..."
                        : transaction.review_required
                          ? "Mark reviewed"
                          : "Needs review"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
