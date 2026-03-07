import "server-only";

import { cookies } from "next/headers";

import { createApiClient } from "@/lib/api/client";
import { requestEnvelope } from "@/lib/api/http";
import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";
import { getBackendBaseUrl } from "@/lib/config";

export const serverApi = createApiClient(async (path, options = {}) => {
  const token = (await cookies()).get(AUTH_COOKIE_NAME)?.value || null;
  return requestEnvelope(`/api/v1${path}`, {
    ...options,
    baseUrl: getBackendBaseUrl(),
    token,
  });
});
