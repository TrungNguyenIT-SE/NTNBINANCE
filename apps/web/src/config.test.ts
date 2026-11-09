import { describe, expect, it } from "vitest";

import { API_BASE_URL, isLoopbackHostname } from "./config";

describe("local runtime configuration", () => {
  it("uses a relative API path", () => {
    expect(API_BASE_URL).toBe("/api/v1");
  });

  it.each(["localhost", "127.0.0.1", "::1"])("accepts loopback host %s", (host) => {
    expect(isLoopbackHostname(host)).toBe(true);
  });

  it("rejects public bindings", () => {
    expect(isLoopbackHostname("0.0.0.0")).toBe(false);
  });
});
