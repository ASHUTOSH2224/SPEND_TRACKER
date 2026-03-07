import type { QueryFilters, ResponseEnvelope } from "@/lib/api/types";

export interface ApiResult<T> {
  data: T;
  meta: Record<string, unknown>;
}

export interface ApiRequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  query?: QueryFilters;
  body?: unknown;
  headers?: HeadersInit;
  baseUrl?: string;
  token?: string | null;
}

export class ApiClientError extends Error {
  status: number;
  code: string;
  details?: Record<string, unknown> | null;

  constructor(status: number, code: string, message: string, details?: Record<string, unknown> | null) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function buildUrl(path: string, query?: QueryFilters, baseUrl?: string): string {
  const url = new URL(path, baseUrl || "http://localhost");
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === null || value === undefined || value === "") {
        continue;
      }
      url.searchParams.set(key, String(value));
    }
  }
  return baseUrl ? url.toString() : `${url.pathname}${url.search}`;
}

export async function requestEnvelope<T>(path: string, options: ApiRequestOptions = {}): Promise<ApiResult<T>> {
  const headers = new Headers(options.headers);
  headers.set("accept", "application/json");

  if (options.body !== undefined) {
    headers.set("content-type", "application/json");
  }
  if (options.token) {
    headers.set("authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(buildUrl(path, options.query, options.baseUrl), {
    method: options.method || "GET",
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    headers,
    cache: "no-store",
  });

  const payload = (await response.json().catch(() => null)) as ResponseEnvelope<T> | null;
  if (!response.ok || !payload || payload.error || payload.data === null) {
    const error = payload?.error;
    throw new ApiClientError(
      response.status,
      error?.code || "REQUEST_FAILED",
      error?.message || "Request failed",
      error?.details || null,
    );
  }

  return {
    data: payload.data,
    meta: payload.meta || {},
  };
}
