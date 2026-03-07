import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { RewardLedgerManager } from "@/components/forms/reward-ledger-manager";
import type { RewardLedgerRead } from "@/lib/api/types";

const {
  refreshMock,
  createMock,
  updateMock,
  removeMock,
} = vi.hoisted(() => ({
  refreshMock: vi.fn(),
  createMock: vi.fn(),
  updateMock: vi.fn(),
  removeMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    refresh: refreshMock,
  }),
}));

vi.mock("@/lib/api/browser", () => ({
  browserApi: {
    rewardLedgers: {
      create: createMock,
      update: updateMock,
      remove: removeMock,
    },
  },
}));

function makeRewardEvent(overrides: Partial<RewardLedgerRead> = {}): RewardLedgerRead {
  return {
    id: "reward-ledger-1",
    card_id: "card-1",
    statement_id: null,
    event_date: "2026-03-05",
    event_type: "adjusted",
    reward_points: "300.00",
    reward_value_estimate: "150.00",
    source: "manual",
    notes: "Manual adjustment",
    created_at: "2026-03-05T00:00:00Z",
    updated_at: "2026-03-05T00:00:00Z",
    ...overrides,
  };
}

describe("RewardLedgerManager", () => {
  beforeEach(() => {
    refreshMock.mockReset();
    createMock.mockReset();
    updateMock.mockReset();
    removeMock.mockReset();
  });

  it("creates a manual reward entry through the centralized API client", async () => {
    const user = userEvent.setup();
    createMock.mockResolvedValue({
      data: makeRewardEvent({
        id: "reward-ledger-2",
        event_date: "2026-03-10",
        event_type: "earned",
        reward_points: "1200.00",
        reward_value_estimate: null,
        notes: "March bonus",
      }),
      meta: {},
    });

    render(<RewardLedgerManager cardId="card-1" rewardEvents={[]} />);

    await user.click(screen.getByRole("button", { name: "Add reward entry" }));
    fireEvent.change(screen.getByLabelText("Event date"), {
      target: { value: "2026-03-10" },
    });
    await user.selectOptions(screen.getByLabelText("Event type"), "earned");
    await user.type(screen.getByLabelText("Reward points"), "1200");
    await user.type(screen.getByLabelText("Notes"), "March bonus");
    await user.click(screen.getByRole("button", { name: "Create reward event" }));

    await waitFor(() =>
      expect(createMock).toHaveBeenCalledWith({
        card_id: "card-1",
        event_date: "2026-03-10",
        event_type: "earned",
        reward_points: "1200",
        reward_value_estimate: null,
        source: "manual",
        notes: "March bonus",
      }),
    );
    expect(await screen.findByText("March bonus")).toBeInTheDocument();
    expect(refreshMock).toHaveBeenCalled();
  });

  it("updates a manual reward entry from the card detail flow", async () => {
    const user = userEvent.setup();
    updateMock.mockResolvedValue({
      data: makeRewardEvent({
        reward_points: "450.00",
        reward_value_estimate: "225.00",
        notes: "Updated adjustment",
      }),
      meta: {},
    });

    render(<RewardLedgerManager cardId="card-1" rewardEvents={[makeRewardEvent()]} />);

    await user.click(screen.getByRole("button", { name: "Edit adjusted reward event" }));
    await user.clear(screen.getByLabelText("Reward points"));
    await user.type(screen.getByLabelText("Reward points"), "450");
    await user.clear(screen.getByLabelText("Reward value"));
    await user.type(screen.getByLabelText("Reward value"), "225");
    await user.clear(screen.getByLabelText("Notes"));
    await user.type(screen.getByLabelText("Notes"), "Updated adjustment");
    await user.click(screen.getByRole("button", { name: "Save reward event" }));

    await waitFor(() =>
      expect(updateMock).toHaveBeenCalledWith("reward-ledger-1", {
        event_date: "2026-03-05",
        event_type: "adjusted",
        reward_points: "450",
        reward_value_estimate: "225",
        source: "manual",
        notes: "Updated adjustment",
      }),
    );
    expect(await screen.findByText("Updated adjustment")).toBeInTheDocument();
    expect(refreshMock).toHaveBeenCalled();
  });

  it("shows imported rows as read-only", () => {
    render(
      <RewardLedgerManager
        cardId="card-1"
        rewardEvents={[
          makeRewardEvent({
            id: "reward-ledger-3",
            source: "extracted",
            notes: "Imported from statement",
          }),
        ]}
      />,
    );

    expect(screen.queryByRole("button", { name: "Edit adjusted reward event" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete adjusted reward event" })).not.toBeInTheDocument();
    expect(screen.getByText("Imported rows are read-only from card detail.")).toBeInTheDocument();
  });

  it("shows a retryable error state when reward deletion fails", async () => {
    const user = userEvent.setup();
    removeMock
      .mockRejectedValueOnce(new Error("Delete failed"))
      .mockResolvedValueOnce({
        data: makeRewardEvent(),
        meta: {},
      });

    render(<RewardLedgerManager cardId="card-1" rewardEvents={[makeRewardEvent()]} />);

    await user.click(screen.getByRole("button", { name: "Delete adjusted reward event" }));

    await waitFor(() => expect(screen.getByText("Delete failed")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => expect(removeMock).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(screen.queryByText("Manual adjustment")).not.toBeInTheDocument(),
    );
    expect(refreshMock).toHaveBeenCalled();
  });
});
