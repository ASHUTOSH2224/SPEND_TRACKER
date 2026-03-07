"use client";

import type { UserRead } from "@/lib/api/types";
import { requestEnvelope } from "@/lib/api/http";

export const browserAuth = {
  login: async (payload: { email: string; password: string }) =>
    requestEnvelope<UserRead>("/api/auth/login", { method: "POST", body: payload }),
  signup: async (payload: { email: string; password: string; full_name: string }) =>
    requestEnvelope<UserRead>("/api/auth/signup", { method: "POST", body: payload }),
  logout: async () => requestEnvelope<{ success: boolean }>("/api/auth/logout", { method: "POST" }),
  me: async () => requestEnvelope<UserRead>("/api/auth/me"),
};
