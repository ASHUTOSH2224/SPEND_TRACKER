export type ResolvedSearchParams = Record<string, string | string[] | undefined>;
export type SearchParamUpdateValue = string | number | boolean | null | undefined;

export function getSearchParam(
  params: ResolvedSearchParams,
  key: string,
): string | undefined {
  const value = params[key];
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
}

export function getBooleanSearchParam(
  params: ResolvedSearchParams,
  key: string,
): boolean | undefined {
  const value = getSearchParam(params, key);
  if (value === undefined) {
    return undefined;
  }
  return value === "true";
}

export function buildSearchPath(
  pathname: string,
  params: ResolvedSearchParams,
  updates: Record<string, SearchParamUpdateValue>,
): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    const normalized = Array.isArray(value) ? value[0] : value;
    if (normalized !== undefined && normalized !== "") {
      searchParams.set(key, normalized);
    }
  }

  for (const [key, value] of Object.entries(updates)) {
    if (value === undefined || value === null || value === "") {
      searchParams.delete(key);
      continue;
    }
    searchParams.set(key, String(value));
  }

  const query = searchParams.toString();
  return query ? `${pathname}?${query}` : pathname;
}
