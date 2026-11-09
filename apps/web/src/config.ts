export const API_BASE_URL = "/api/v1" as const;

export type RuntimeScope = "local-private-research";

export function isLoopbackHostname(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}
