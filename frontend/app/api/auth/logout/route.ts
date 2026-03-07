import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import type { ResponseEnvelope } from "@/lib/api/types";
import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";

export async function POST() {
  (await cookies()).delete(AUTH_COOKIE_NAME);

  const payload: ResponseEnvelope<{ success: boolean }> = {
    data: { success: true },
    meta: {},
    error: null,
  };
  return NextResponse.json(payload);
}
