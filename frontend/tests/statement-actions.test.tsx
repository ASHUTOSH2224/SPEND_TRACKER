import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StatementActions } from "@/components/forms/statement-actions";

const {
  refreshMock,
  retryMock,
  removeMock,
} = vi.hoisted(() => ({
  refreshMock: vi.fn(),
  retryMock: vi.fn(),
  removeMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    refresh: refreshMock,
  }),
}));

vi.mock("@/lib/api/browser", () => ({
  browserApi: {
    statements: {
      retry: retryMock,
      remove: removeMock,
    },
  },
}));

describe("StatementActions", () => {
  beforeEach(() => {
    refreshMock.mockReset();
    retryMock.mockReset();
    removeMock.mockReset();
  });

  it("shows retry for failed statements and retries through the centralized API client", async () => {
    const user = userEvent.setup();
    retryMock.mockResolvedValue({
      data: {
        id: "statement-1",
      },
      meta: {},
    });

    render(<StatementActions statementId="statement-1" uploadStatus="failed" />);

    await user.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => expect(retryMock).toHaveBeenCalledWith("statement-1"));
    expect(refreshMock).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });

  it("hides retry for non-failed statements and still allows delete", async () => {
    const user = userEvent.setup();
    removeMock.mockResolvedValue({
      data: {
        id: "statement-1",
        deleted: true,
      },
      meta: {},
    });

    render(<StatementActions statementId="statement-1" uploadStatus="completed" />);

    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(removeMock).toHaveBeenCalledWith("statement-1"));
    expect(refreshMock).toHaveBeenCalled();
  });
});
