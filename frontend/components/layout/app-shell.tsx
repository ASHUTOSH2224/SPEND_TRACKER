import type { UserRead } from "@/lib/api/types";

import { Sidebar } from "@/components/layout/sidebar";
import { TopNav } from "@/components/layout/top-nav";

export function AppShell({
  user,
  children,
}: {
  user: UserRead;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen p-4 md:p-6">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-[1500px] gap-4 md:grid-cols-[280px_minmax(0,1fr)]">
        <Sidebar />
        <div className="flex min-w-0 flex-col gap-4">
          <TopNav user={user} />
          <main className="flex-1">{children}</main>
        </div>
      </div>
    </div>
  );
}
