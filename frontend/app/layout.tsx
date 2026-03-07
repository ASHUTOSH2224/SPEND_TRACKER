import type { Metadata } from "next";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "Spend Tracker",
  description: "Credit card spend, rewards, and statement tracking dashboard.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-canvas font-body text-text antialiased">
        {children}
      </body>
    </html>
  );
}
