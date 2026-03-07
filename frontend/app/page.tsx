import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AUTH_COOKIE_NAME } from "@/lib/auth/constants";

export default async function HomePage() {
  const hasSession = Boolean((await cookies()).get(AUTH_COOKIE_NAME)?.value);
  redirect(hasSession ? "/dashboard" : "/login");
}
