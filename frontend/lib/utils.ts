export type NumberLike = number | string | null | undefined;

export function cn(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(" ");
}

export function toNumber(value: NumberLike): number {
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

export function formatCurrency(value: NumberLike, currency = "INR"): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(toNumber(value));
}

export function formatDecimal(value: NumberLike, digits = 2): string {
  return toNumber(value).toFixed(digits);
}

export function formatDate(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function formatMonthLabel(value: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function formatPercent(value: NumberLike): string {
  return `${toNumber(value).toFixed(2)}%`;
}

export function inferStatementFileType(fileName: string): "pdf" | "csv" | "xls" | "xlsx" {
  const extension = fileName.split(".").pop()?.toLowerCase();
  if (extension === "csv") {
    return "csv";
  }
  if (extension === "xls") {
    return "xls";
  }
  if (extension === "xlsx") {
    return "xlsx";
  }
  return "pdf";
}

export function inferContentType(fileName: string): string {
  const extension = fileName.split(".").pop()?.toLowerCase();
  if (extension === "csv") {
    return "text/csv";
  }
  if (extension === "xls") {
    return "application/vnd.ms-excel";
  }
  if (extension === "xlsx") {
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  }
  return "application/pdf";
}

export function toBarWidth(value: NumberLike, max: number): string {
  if (max <= 0) {
    return "0%";
  }
  return `${Math.max(8, Math.round((toNumber(value) / max) * 100))}%`;
}
