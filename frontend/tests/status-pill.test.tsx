import { render, screen } from "@testing-library/react";

import { StatusPill } from "@/components/shared/status-pill";

describe("StatusPill", () => {
  it("renders completed styles for positive states", () => {
    render(<StatusPill status="completed" />);
    expect(screen.getByText("completed")).toHaveClass("text-accent");
  });

  it("renders failed styles for error states", () => {
    render(<StatusPill status="failed" />);
    expect(screen.getByText("failed")).toHaveClass("text-danger");
  });
});
