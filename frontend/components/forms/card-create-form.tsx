"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { browserApi } from "@/lib/api/browser";

export function CardCreateForm() {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <form
      className="grid gap-3 rounded-[1.25rem] border border-line bg-white/70 p-4 md:grid-cols-5"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const formData = new FormData(event.currentTarget);
        setPending(true);
        setError(null);
        startTransition(async () => {
          try {
            await browserApi.cards.create({
              nickname: String(formData.get("nickname") || ""),
              issuer_name: String(formData.get("issuer_name") || ""),
              network: String(formData.get("network") || "visa"),
              last4: String(formData.get("last4") || ""),
              reward_type: "points",
              reward_program_name: "Rewards",
              reward_conversion_rate: "0.5000",
            });
            form.reset();
            router.refresh();
          } catch (submissionError) {
            setError(submissionError instanceof Error ? submissionError.message : "Unable to add card");
          } finally {
            setPending(false);
          }
        });
      }}
    >
      <input className="app-input" name="nickname" placeholder="Card nickname" required />
      <input className="app-input" name="issuer_name" placeholder="Issuer" required />
      <input className="app-input" name="network" placeholder="Network" defaultValue="visa" required />
      <input className="app-input" name="last4" inputMode="numeric" maxLength={4} placeholder="Last 4" required />
      <button className="app-button" type="submit" disabled={pending}>
        {pending ? "Saving..." : "Add card"}
      </button>
      {error ? <p className="md:col-span-5 text-sm text-danger">{error}</p> : null}
    </form>
  );
}
