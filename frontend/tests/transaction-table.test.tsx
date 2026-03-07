import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { TransactionTable } from "@/components/shared/transaction-table";
import type { CategoryRead, TransactionRead } from "@/lib/api/types";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    refresh: vi.fn(),
  }),
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
});
