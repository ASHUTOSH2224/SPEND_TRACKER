import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthForm } from "@/components/forms/auth-form";

const { pushMock, refreshMock, loginMock, signupMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
  refreshMock: vi.fn(),
  loginMock: vi.fn(),
  signupMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    refresh: refreshMock,
  }),
}));

vi.mock("@/lib/auth/browser", () => ({
  browserAuth: {
    login: loginMock,
    signup: signupMock,
  },
}));

describe("AuthForm", () => {
  beforeEach(() => {
    pushMock.mockReset();
    refreshMock.mockReset();
    loginMock.mockReset();
    signupMock.mockReset();
  });

  it("shows the session-expired message when provided", () => {
    render(
      <AuthForm
        mode="login"
        statusMessage="Your session expired. Sign in again to continue."
      />,
    );

    expect(
      screen.getByText("Your session expired. Sign in again to continue."),
    ).toBeInTheDocument();
  });
});
