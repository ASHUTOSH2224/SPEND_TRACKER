import type { LocalSettingsPreference } from "@/lib/api/types";

// Temporary local-only settings adapter until backend settings endpoints exist.
export function getMockSettingsPreferences(): LocalSettingsPreference[] {
  return [
    {
      id: "currency",
      label: "Display currency",
      value: "Indian Rupee (INR)",
      note: "Rendered locally in the frontend shell.",
    },
    {
      id: "default_range",
      label: "Default dashboard range",
      value: "Current month",
      note: "Used as the page fallback when no filters are selected.",
    },
    {
      id: "statement_privacy",
      label: "Statement storage mode",
      value: "Local fake storage",
      note: "Matches the current MVP backend upload adapter.",
    },
  ];
}
