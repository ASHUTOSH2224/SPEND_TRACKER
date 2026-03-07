import { AuthForm } from "@/components/forms/auth-form";
import { SESSION_EXPIRED_PARAM } from "@/lib/auth/session";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = await searchParams;
  const expiredParam = resolvedSearchParams[SESSION_EXPIRED_PARAM];
  const sessionExpired =
    expiredParam === "1" || (Array.isArray(expiredParam) && expiredParam.includes("1"));

  return (
    <AuthForm
      mode="login"
      statusMessage={sessionExpired ? "Your session expired. Sign in again to continue." : null}
    />
  );
}
