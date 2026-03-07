import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import type { ResponseEnvelope } from "@/lib/api/types";
import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";
import { sanitizeNextPath } from "@/lib/auth/session";

export async function GET(request: Request) {
  const nextPath = sanitizeNextPath(new URL(request.url).searchParams.get("next"));

  (await cookies()).delete(AUTH_COOKIE_NAME);

  return NextResponse.redirect(new URL(nextPath, request.url));
}

export async function POST() {
  (await cookies()).delete(AUTH_COOKIE_NAME);

  const payload: ResponseEnvelope<{ success: boolean }> = {
    data: { success: true },
    meta: {},
    error: null,
  };
  return NextResponse.json(payload);
}
