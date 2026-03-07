"use client";

import { createApiClient } from "@/lib/api/client";
import { requestEnvelope } from "@/lib/api/http";

export const browserApi = createApiClient((path, options = {}) =>
  requestEnvelope(`/api/v1${path}`, options),
);
