import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { Sidebar } from "@/components/layout/sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/transactions",
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    className,
    children,
  }: {
    href: string;
    className?: string;
    children: React.ReactNode;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

describe("Sidebar", () => {
  it("renders all shell destinations and highlights the active route", () => {
    render(<Sidebar />);

    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Cards" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Upload Statements" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Transactions" })).toHaveClass("bg-white/14");
  });
});
