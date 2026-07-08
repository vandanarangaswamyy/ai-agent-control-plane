export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDurationMs(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }

  if (value < 1000) {
    return `${Math.round(value)} ms`;
  }

  const seconds = value / 1000;
  return `${seconds.toFixed(seconds >= 10 ? 1 : 2)} s`;
}

export function formatPercent(
  value: number | string | null | undefined,
  digits = 1,
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const parsed = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(parsed)) {
    return "—";
  }

  return `${parsed.toFixed(digits)}%`;
}

export function formatCurrency(
  value: number | string | null | undefined,
  digits = 4,
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const parsed = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(parsed)) {
    return "—";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(parsed);
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }

  return new Intl.NumberFormat("en-US").format(value);
}

export function formatTitle(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

