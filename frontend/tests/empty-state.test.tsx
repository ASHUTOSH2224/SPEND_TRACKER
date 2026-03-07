import { render, screen } from "@testing-library/react";

import { EmptyState } from "@/components/shared/empty-state";

describe("EmptyState", () => {
  it("renders the supplied copy", () => {
    render(<EmptyState title="No cards yet" description="Add a card to continue." />);

    expect(screen.getByText("No cards yet")).toBeInTheDocument();
    expect(screen.getByText("Add a card to continue.")).toBeInTheDocument();
  });
});
