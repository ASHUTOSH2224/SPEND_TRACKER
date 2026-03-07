import { redirect } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { ApiClientError } from "@/lib/api/http";
import { serverApi } from "@/lib/api/server";

export default async function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  try {
    const { data: user } = await serverApi.auth.me();
    return <AppShell user={user}>{children}</AppShell>;
  } catch (error) {
    if (error instanceof ApiClientError && error.status === 401) {
      redirect("/login");
    }
    throw error;
  }
}
