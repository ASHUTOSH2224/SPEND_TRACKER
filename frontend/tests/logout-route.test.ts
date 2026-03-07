import { beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/auth/logout/route";
import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";

const { deleteMock } = vi.hoisted(() => ({
  deleteMock: vi.fn(),
}));

vi.mock("next/headers", () => ({
  cookies: async () => ({
    delete: deleteMock,
  }),
}));

describe("logout route", () => {
  beforeEach(() => {
    deleteMock.mockReset();
  });

  it("clears the session cookie and redirects to the provided in-app path", async () => {
    const response = await GET(
      new Request("http://localhost:3000/api/auth/logout?next=%2Flogin%3Fexpired%3D1"),
    );

    expect(deleteMock).toHaveBeenCalledWith(AUTH_COOKIE_NAME);
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("http://localhost:3000/login?expired=1");
  });

  it("falls back to /login for unsafe redirect targets", async () => {
    const response = await GET(
      new Request("http://localhost:3000/api/auth/logout?next=https%3A%2F%2Fevil.example"),
    );

    expect(deleteMock).toHaveBeenCalledWith(AUTH_COOKIE_NAME);
    expect(response.headers.get("location")).toBe("http://localhost:3000/login");
  });
});
