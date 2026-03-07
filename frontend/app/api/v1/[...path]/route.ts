import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";
import { getBackendBaseUrl } from "@/lib/config";

async function proxyRequest(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const search = new URL(request.url).search;
  const backendUrl = `${getBackendBaseUrl()}/api/v1/${path.join("/")}${search}`;
  const bodyText = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();

  const headers = new Headers();
  headers.set("accept", "application/json");

  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const token = (await cookies()).get(AUTH_COOKIE_NAME)?.value;
  if (token) {
    headers.set("authorization", `Bearer ${token}`);
  }

  const backendResponse = await fetch(backendUrl, {
    method: request.method,
    headers,
    body: bodyText ? bodyText : undefined,
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  const responseContentType = backendResponse.headers.get("content-type");
  if (responseContentType) {
    responseHeaders.set("content-type", responseContentType);
  }

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
