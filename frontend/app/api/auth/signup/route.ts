import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import type { AuthResponse, ResponseEnvelope, UserRead } from "@/lib/api/types";
import { ApiClientError, requestEnvelope } from "@/lib/api/http";
import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";
import { getBackendBaseUrl } from "@/lib/config";

function errorResponse(status: number, code: string, message: string, details?: Record<string, unknown> | null) {
  const payload: ResponseEnvelope<null> = {
    data: null,
    meta: {},
    error: {
      code,
      message,
      details,
    },
  };
  return NextResponse.json(payload, { status });
}

export async function POST(request: Request) {
  const body = await request.json();

  try {
    const { data } = await requestEnvelope<AuthResponse>("/api/v1/auth/signup", {
      method: "POST",
      body,
      baseUrl: getBackendBaseUrl(),
    });

    (await cookies()).set(AUTH_COOKIE_NAME, data.token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });

    const payload: ResponseEnvelope<UserRead> = {
      data: data.user,
      meta: {},
      error: null,
    };
    return NextResponse.json(payload, { status: 201 });
  } catch (error) {
    if (error instanceof ApiClientError) {
      return errorResponse(error.status, error.code, error.message, error.details);
    }
    return errorResponse(500, "INTERNAL_ERROR", "Signup failed");
  }
}
