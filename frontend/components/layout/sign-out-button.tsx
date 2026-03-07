"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { browserAuth } from "@/lib/auth/browser";

export function SignOutButton() {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  return (
    <button
      type="button"
      className="app-button app-button-secondary text-sm"
      onClick={() => {
        setPending(true);
        startTransition(async () => {
          try {
            await browserAuth.logout();
            router.push("/login");
            router.refresh();
          } finally {
            setPending(false);
          }
        });
      }}
      disabled={pending}
    >
      {pending ? "Signing out..." : "Sign out"}
    </button>
  );
}
