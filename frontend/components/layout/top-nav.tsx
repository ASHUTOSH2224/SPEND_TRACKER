import type { UserRead } from "@/lib/api/types";

import { SignOutButton } from "@/components/layout/sign-out-button";

export function TopNav({ user }: { user: UserRead }) {
  return (
    <header className="app-panel flex items-center justify-between gap-4 px-5 py-4">
      <div>
        <p className="text-xs uppercase tracking-[0.22em] text-muted">Spend Tracker MVP</p>
        <h1 className="font-display text-xl font-semibold tracking-tight">Personal card control room</h1>
      </div>

      <div className="flex items-center gap-3">
        <div className="rounded-full border border-line bg-white/80 px-4 py-2 text-right">
          <p className="text-sm font-medium">{user.full_name}</p>
          <p className="text-xs text-muted">{user.email}</p>
        </div>
        <SignOutButton />
      </div>
    </header>
  );
}
