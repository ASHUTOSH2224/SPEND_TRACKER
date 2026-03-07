export type ResolvedSearchParams = Record<string, string | string[] | undefined>;

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
