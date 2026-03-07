export const SESSION_EXPIRED_PARAM = "expired";
export const SESSION_EXPIRED_LOGIN_PATH = `/login?${SESSION_EXPIRED_PARAM}=1`;

export function buildSessionExpiredLogoutPath(): string {
  return `/api/auth/logout?next=${encodeURIComponent(SESSION_EXPIRED_LOGIN_PATH)}`;
}

export function sanitizeNextPath(nextPath: string | null | undefined, fallback = "/login"): string {
  if (!nextPath || !nextPath.startsWith("/") || nextPath.startsWith("//")) {
    return fallback;
  }
  return nextPath;
}
