"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import { browserApi } from "@/lib/api/browser";

export function CategoryCreateForm() {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <form
      className="grid gap-3 md:grid-cols-[minmax(0,1fr)_180px_auto]"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const formData = new FormData(event.currentTarget);
        setPending(true);
        setError(null);
        startTransition(async () => {
          try {
            await browserApi.categories.create({
              name: String(formData.get("name") || ""),
              group_name: String(formData.get("group_name") || "spend") as "spend" | "charges" | "rewards",
            });
            form.reset();
            router.refresh();
          } catch (submissionError) {
            setError(submissionError instanceof Error ? submissionError.message : "Unable to add category");
          } finally {
            setPending(false);
          }
        });
      }}
    >
      <input className="app-input" name="name" placeholder="New category name" required />
      <select className="app-select" name="group_name" defaultValue="spend">
        <option value="spend">Spend</option>
        <option value="charges">Charges</option>
        <option value="rewards">Rewards</option>
      </select>
      <button className="app-button" type="submit" disabled={pending}>
        {pending ? "Saving..." : "Add category"}
      </button>
      {error ? <p className="md:col-span-3 text-sm text-danger">{error}</p> : null}
    </form>
  );
}
