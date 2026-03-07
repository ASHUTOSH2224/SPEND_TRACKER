import { render, screen } from "@testing-library/react";

import { PaginationControls } from "@/components/shared/pagination-controls";

describe("PaginationControls", () => {
  it("hides itself when there is only one page", () => {
    const { container } = render(
      <PaginationControls pathname="/transactions" searchParams={{}} page={1} totalPages={1} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("preserves existing filters in the previous and next links", () => {
    render(
      <PaginationControls
        pathname="/transactions"
        searchParams={{ card_id: "card-1", search: "coffee", page_size: "50" }}
        page={2}
        totalPages={4}
      />,
    );

    expect(screen.getByRole("link", { name: "Previous" })).toHaveAttribute(
      "href",
      "/transactions?card_id=card-1&search=coffee&page_size=50&page=1",
    );
    expect(screen.getByRole("link", { name: "Next" })).toHaveAttribute(
      "href",
      "/transactions?card_id=card-1&search=coffee&page_size=50&page=3",
    );
  });
});
