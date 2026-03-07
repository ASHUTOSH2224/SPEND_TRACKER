"use client";

import type { CategoryRead } from "@/lib/api/types";

export function CategorySelect({
  value,
  categories,
  onChange,
  disabled,
  allowEmpty = false,
}: {
  value: string | null;
  categories: CategoryRead[];
  onChange: (value: string | null) => void;
  disabled?: boolean;
  allowEmpty?: boolean;
}) {
  return (
    <select
      className="app-select min-w-[180px]"
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value || null)}
      disabled={disabled}
    >
      {value === null || allowEmpty ? <option value="">Unassigned</option> : null}
      {categories.map((category) => (
        <option key={category.id} value={category.id}>
          {category.name}
        </option>
      ))}
    </select>
  );
}
