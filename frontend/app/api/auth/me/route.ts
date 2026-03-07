import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import type { ResponseEnvelope, UserRead } from "@/lib/api/types";
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

export async function GET() {
  const token = (await cookies()).get(AUTH_COOKIE_NAME)?.value;
  if (!token) {
    return errorResponse(401, "UNAUTHORIZED", "Authentication required");
  }

  try {
    const result = await requestEnvelope<UserRead>("/api/v1/auth/me", {
      baseUrl: getBackendBaseUrl(),
      token,
    });
    const payload: ResponseEnvelope<UserRead> = {
      data: result.data,
      meta: result.meta,
      error: null,
    };
    return NextResponse.json(payload);
  } catch (error) {
    if (error instanceof ApiClientError) {
      if (error.status === 401) {
        (await cookies()).delete(AUTH_COOKIE_NAME);
      }
      return errorResponse(error.status, error.code, error.message, error.details);
    }
    return errorResponse(500, "INTERNAL_ERROR", "Unable to load user");
  }
}
