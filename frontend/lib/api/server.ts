import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { createApiClient } from "@/lib/api/client";
import { ApiClientError, requestEnvelope } from "@/lib/api/http";
import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";
import { buildSessionExpiredLogoutPath } from "@/lib/auth/session";
import { getBackendBaseUrl } from "@/lib/config";

export const serverApi = createApiClient(async (path, options = {}) => {
  const token = (await cookies()).get(AUTH_COOKIE_NAME)?.value || null;
  try {
    return await requestEnvelope(`/api/v1${path}`, {
      ...options,
      baseUrl: getBackendBaseUrl(),
      token,
    });
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 401) {
      redirect(buildSessionExpiredLogoutPath());
    }
    throw error;
  }
});
