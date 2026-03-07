"use client";

import type { CategoryRead } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export function CategorySelect({
  value,
  categories,
  onChange,
  disabled,
  allowEmpty = false,
  emptyLabel = "Unassigned",
  className,
  id,
  name,
  ariaLabel,
}: {
  value: string | null;
  categories: CategoryRead[];
  onChange: (value: string | null) => void;
  disabled?: boolean;
  allowEmpty?: boolean;
  emptyLabel?: string;
  className?: string;
  id?: string;
  name?: string;
  ariaLabel?: string;
}) {
  const selectableCategories = categories.filter((category) => !category.is_archived || category.id === value);

  return (
    <select
      className={cn("app-select min-w-[180px]", className)}
      value={value ?? ""}
      onChange={(event) => onChange(event.target.value || null)}
      disabled={disabled}
      id={id}
      name={name}
      aria-label={ariaLabel}
    >
      {value === null || allowEmpty ? <option value="">{emptyLabel}</option> : null}
      {selectableCategories.map((category) => (
        <option key={category.id} value={category.id}>
          {category.name}
        </option>
      ))}
    </select>
  );
}
