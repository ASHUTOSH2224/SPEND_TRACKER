"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const navigationItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/cards", label: "Cards" },
  { href: "/upload", label: "Upload Statements" },
  { href: "/transactions", label: "Transactions" },
  { href: "/categories", label: "Categories" },
  { href: "/statements", label: "Statements" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full flex-col rounded-[1.5rem] bg-[#15231d] p-4 text-[#f7f2e8] shadow-panel">
      <div className="border-b border-white/10 pb-4">
        <p className="font-display text-xl font-semibold tracking-tight">SpendSense</p>
        <p className="mt-1 text-sm text-white/60">Card visibility without spreadsheet drift.</p>
      </div>

      <nav className="mt-6 flex flex-1 flex-col gap-2 md:flex-col">
        {navigationItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-2xl px-4 py-3 text-sm font-medium transition hover:bg-white/8 hover:text-white",
                active ? "bg-white/14 text-white" : "text-white/70",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
        Local development uploads are stored on disk before the statement job is queued.
      </div>
    </aside>
  );
}
