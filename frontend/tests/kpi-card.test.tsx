import { render, screen } from "@testing-library/react";

import { KpiCard } from "@/components/shared/kpi-card";

describe("KpiCard", () => {
  it("renders the label, value, and helper copy", () => {
    render(<KpiCard label="Total Spend" value="₹54,000" helper="Previous period ₹48,000" />);

    expect(screen.getByText("Total Spend")).toBeInTheDocument();
    expect(screen.getByText("₹54,000")).toBeInTheDocument();
    expect(screen.getByText("Previous period ₹48,000")).toBeInTheDocument();
  });
});
