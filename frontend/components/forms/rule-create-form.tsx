"use client";

import { startTransition, useState } from "react";
import { useRouter } from "next/navigation";

import type { CategoryRead } from "@/lib/api/types";
import { browserApi } from "@/lib/api/browser";

export function RuleCreateForm({ categories }: { categories: CategoryRead[] }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const assignableCategories = categories.filter((category) => !category.is_archived);
  const disabled = pending || assignableCategories.length === 0;

  return (
    <form
      className="grid gap-3 md:grid-cols-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (!assignableCategories.length) {
          setError("Create or keep at least one assignable category before adding a rule");
          return;
        }
        const form = event.currentTarget;
        const formData = new FormData(event.currentTarget);
        setPending(true);
        setError(null);
        startTransition(async () => {
          try {
            await browserApi.rules.create({
              rule_name: String(formData.get("rule_name") || ""),
              match_type: String(formData.get("match_type") || "description_contains") as
                | "description_contains"
                | "merchant_equals"
                | "regex",
              match_value: String(formData.get("match_value") || ""),
              assigned_category_id: String(formData.get("assigned_category_id") || ""),
            });
            form.reset();
            router.refresh();
          } catch (submissionError) {
            setError(submissionError instanceof Error ? submissionError.message : "Unable to add rule");
          } finally {
            setPending(false);
          }
        });
      }}
    >
      <input className="app-input" name="rule_name" placeholder="Rule name" required disabled={disabled} />
      <input className="app-input" name="match_value" placeholder="SWIGGY" required disabled={disabled} />
      <select className="app-select" name="assigned_category_id" required defaultValue="" disabled={disabled}>
        <option value="" disabled>
          Category
        </option>
        {assignableCategories.map((category) => (
          <option key={category.id} value={category.id}>
            {category.name}
          </option>
        ))}
      </select>
      <div className="flex gap-3">
        <select className="app-select" name="match_type" defaultValue="description_contains" disabled={disabled}>
          <option value="description_contains">Description contains</option>
          <option value="merchant_equals">Merchant equals</option>
          <option value="regex">Regex</option>
        </select>
        <button className="app-button" type="submit" disabled={disabled}>
          {pending ? "Saving..." : "Add rule"}
        </button>
      </div>
      {error ? <p className="md:col-span-4 text-sm text-danger">{error}</p> : null}
    </form>
  );
}
