export function captureTokenAndCleanSearch(search: string, tokenKey = "token") {
  const params = new URLSearchParams(search);
  const token = params.get(tokenKey) || "";
  if (token) params.delete(tokenKey);
  const cleanedSearch = params.toString();
  return { token, cleanedSearch: cleanedSearch ? `?${cleanedSearch}` : "" };
}
