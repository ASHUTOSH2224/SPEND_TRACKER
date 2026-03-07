"use client";

import Link from "next/link";
import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { browserAuth } from "@/lib/auth/browser";

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <section className="app-panel w-full max-w-xl p-8">
        <p className="text-sm uppercase tracking-[0.22em] text-muted">SpendSense</p>
        <h1 className="mt-3 font-display text-4xl font-semibold tracking-tight">
          {mode === "login" ? "Track your cards in one place" : "Create your SpendSense account"}
        </h1>
        <p className="mt-3 text-sm text-muted">
          Use your backend auth account to enter the MVP shell. OAuth is not wired yet.
        </p>

        <form
          className="mt-8 grid gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            const formData = new FormData(event.currentTarget);
            const payload = {
              email: String(formData.get("email") || ""),
              password: String(formData.get("password") || ""),
              full_name: String(formData.get("full_name") || ""),
            };

            setPending(true);
            setError(null);
            startTransition(async () => {
              try {
                if (mode === "login") {
                  await browserAuth.login({
                    email: payload.email,
                    password: payload.password,
                  });
                } else {
                  await browserAuth.signup(payload);
                }
                router.push("/dashboard");
                router.refresh();
              } catch (submissionError) {
                const message =
                  submissionError instanceof Error ? submissionError.message : "Authentication failed";
                setError(message);
              } finally {
                setPending(false);
              }
            });
          }}
        >
          {mode === "signup" ? (
            <label className="grid gap-2">
              <span className="text-sm font-medium">Full name</span>
              <input className="app-input" name="full_name" placeholder="Aarav Sharma" required />
            </label>
          ) : null}

          <label className="grid gap-2">
            <span className="text-sm font-medium">Email</span>
            <input className="app-input" name="email" type="email" placeholder="you@example.com" required />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-medium">Password</span>
            <input className="app-input" name="password" type="password" placeholder="••••••••" required />
          </label>

          {error ? <p className="rounded-2xl bg-[rgba(157,65,52,0.1)] px-4 py-3 text-sm text-danger">{error}</p> : null}

          <button className="app-button mt-2" type="submit" disabled={pending}>
            {pending ? "Working..." : mode === "login" ? "Sign In" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-sm text-muted">
          {mode === "login" ? "Need an account?" : "Already have an account?"}{" "}
          <Link className="app-link" href={mode === "login" ? "/signup" : "/login"}>
            {mode === "login" ? "Sign up" : "Sign in"}
          </Link>
        </p>
      </section>
    </main>
  );
}
