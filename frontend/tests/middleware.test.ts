import { describe, expect, it } from "vitest";
import { NextRequest } from "next/server";

import { middleware } from "@/middleware";
import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";

describe("middleware", () => {
  it("allows public auth pages even when a session cookie exists", () => {
    const request = new NextRequest("http://localhost:3000/login", {
      headers: {
        cookie: `${AUTH_COOKIE_NAME}=stale-token`,
      },
    });

    const response = middleware(request);

    expect(response.headers.get("location")).toBeNull();
  });

  it("redirects protected pages to login when no session cookie exists", () => {
    const request = new NextRequest("http://localhost:3000/dashboard");

    const response = middleware(request);

    expect(response.headers.get("location")).toBe("http://localhost:3000/login");
  });
});
