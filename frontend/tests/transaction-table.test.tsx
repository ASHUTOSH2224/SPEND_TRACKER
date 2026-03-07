import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TransactionTable } from "@/components/shared/transaction-table";
import type { CategoryRead, TransactionRead } from "@/lib/api/types";

const {
  refreshMock,
  updateMock,
  bulkUpdateMock,
} = vi.hoisted(() => ({
  refreshMock: vi.fn(),
  updateMock: vi.fn(),
  bulkUpdateMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    refresh: refreshMock,
  }),
}));

vi.mock("@/lib/api/browser", () => ({
  browserApi: {
    transactions: {
      update: updateMock,
      bulkUpdate: bulkUpdateMock,
    },
  },
}));

const categories: CategoryRead[] = [
  {
    id: "category-1",
    name: "Dining",
    slug: "dining",
    group_name: "spend",
    is_default: false,
    is_archived: false,
  },
  {
    id: "category-2",
    name: "Travel",
    slug: "travel",
    group_name: "spend",
    is_default: false,
    is_archived: false,
  },
];

function makeTransaction(overrides: Partial<TransactionRead>): TransactionRead {
  return {
    id: "transaction-1",
    txn_date: "2026-03-01",
    posted_date: null,
    card_id: "card-1",
    card_name: "Primary Card",
    statement_id: "statement-1",
    raw_description: "Coffee shop",
    normalized_merchant: "Coffee Shop",
    amount: "450.00",
    currency: "INR",
    txn_direction: "debit",
    txn_type: "spend",
    category: {
      id: "category-1",
      name: "Dining",
    },
    category_source: "rule",
    category_confidence: "0.95",
    category_explanation: null,
    review_required: false,
    duplicate_flag: false,
    is_card_charge: false,
    charge_type: null,
    is_reward_related: false,
    reward_points_delta: null,
    cashback_amount: null,
    source_hash: null,
    metadata_json: null,
    created_at: "2026-03-01T00:00:00Z",
    updated_at: "2026-03-01T00:00:00Z",
    ...overrides,
  };
}

describe("TransactionTable", () => {
  beforeEach(() => {
    refreshMock.mockReset();
    updateMock.mockReset();
    bulkUpdateMock.mockReset();
  });

  it("syncs local rows when fresh server props arrive", () => {
    const firstTransaction = makeTransaction({
      id: "transaction-1",
      normalized_merchant: "Coffee Shop",
      raw_description: "Coffee shop",
    });
    const secondTransaction = makeTransaction({
      id: "transaction-2",
      normalized_merchant: "Grocer",
      raw_description: "Grocery market",
    });

    const { rerender } = render(
      <TransactionTable transactions={[firstTransaction]} categories={categories} />,
    );

    expect(screen.getByText("Coffee Shop")).toBeInTheDocument();

    rerender(<TransactionTable transactions={[secondTransaction]} categories={categories} />);

    expect(screen.queryByText("Coffee Shop")).not.toBeInTheDocument();
    expect(screen.getByText("Grocer")).toBeInTheDocument();
  });

  it("submits bulk recategorization through the centralized API client", async () => {
    const user = userEvent.setup();
    bulkUpdateMock.mockResolvedValue({
      data: {
        updated_count: 2,
        audit_count: 2,
      },
      meta: {},
    });

    render(
      <TransactionTable
        transactions={[
          makeTransaction({ id: "transaction-1", normalized_merchant: "Coffee Shop" }),
          makeTransaction({
            id: "transaction-2",
            normalized_merchant: "Airport Taxi",
            raw_description: "Airport taxi",
          }),
        ]}
        categories={categories}
      />,
    );

    await user.click(screen.getByLabelText("Select Coffee Shop"));
    await user.click(screen.getByLabelText("Select Airport Taxi"));
    await user.selectOptions(screen.getByLabelText("Bulk category"), "category-2");
    await user.click(screen.getByRole("button", { name: "Assign category" }));

    await waitFor(() =>
      expect(bulkUpdateMock).toHaveBeenCalledWith({
        transaction_ids: ["transaction-1", "transaction-2"],
        category_id: "category-2",
      }),
    );
    expect(refreshMock).toHaveBeenCalled();
  });

  it("creates a reusable rule from a corrected transaction", async () => {
    const user = userEvent.setup();
    updateMock.mockResolvedValue({
      data: makeTransaction({
        review_required: false,
        category_source: "manual",
        category_confidence: "1.0000",
      }),
      meta: {},
    });

    render(
      <TransactionTable
        transactions={[makeTransaction({ review_required: true })]}
        categories={categories}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Create rule" }));
    await user.clear(screen.getByLabelText("Rule match value"));
    await user.type(screen.getByLabelText("Rule match value"), "COFFEE");
    await user.click(screen.getByRole("button", { name: "Save rule" }));

    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith("transaction-1", {
        category_id: "category-1",
        review_required: false,
        create_rule: true,
        rule_match_type: "description_contains",
        rule_match_value: "COFFEE",
      }),
    );
    expect(refreshMock).toHaveBeenCalled();
  });

  it("shows a retryable error state when a mutation fails", async () => {
    const user = userEvent.setup();
    bulkUpdateMock
      .mockRejectedValueOnce(new Error("Bulk update failed"))
      .mockResolvedValueOnce({
        data: {
          updated_count: 1,
          audit_count: 1,
        },
        meta: {},
      });

    render(
      <TransactionTable
        transactions={[makeTransaction()]}
        categories={categories}
      />,
    );

    await user.click(screen.getByLabelText("Select Coffee Shop"));
    await user.selectOptions(screen.getByLabelText("Bulk category"), "category-2");
    await user.click(screen.getByRole("button", { name: "Assign category" }));

    await waitFor(() =>
      expect(screen.getByText("Bulk update failed")).toBeInTheDocument(),
    );

    await user.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => expect(bulkUpdateMock).toHaveBeenCalledTimes(2));
  });
});
