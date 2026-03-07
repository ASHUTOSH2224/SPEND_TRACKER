export function getBackendBaseUrl(): string {
  return process.env.BACKEND_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";
}
