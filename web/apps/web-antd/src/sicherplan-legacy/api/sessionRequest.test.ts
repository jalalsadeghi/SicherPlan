// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  accessStoreState,
  legacyAuthStoreState,
} = vi.hoisted(() => ({
  accessStoreState: {
    accessToken: null as null | string,
  },
  legacyAuthStoreState: {
    accessToken: "legacy-access",
    refreshToken: "legacy-refresh",
    effectiveAccessToken: "legacy-access",
    syncFromPrimarySession: vi.fn(),
    refreshSessionTokens: vi.fn(),
    clearSession: vi.fn(),
  },
}));

vi.mock("@vben/stores", () => ({
  useAccessStore: () => accessStoreState,
}));

vi.mock("@/stores/auth", () => ({
  useAuthStore: () => legacyAuthStoreState,
}));

describe("legacy session request", () => {
  beforeEach(() => {
    vi.resetModules();
    accessStoreState.accessToken = null;
    legacyAuthStoreState.accessToken = "legacy-access";
    legacyAuthStoreState.refreshToken = "legacy-refresh";
    legacyAuthStoreState.effectiveAccessToken = "legacy-access";
    legacyAuthStoreState.syncFromPrimarySession.mockClear();
    legacyAuthStoreState.refreshSessionTokens.mockReset();
    legacyAuthStoreState.clearSession.mockClear();
    vi.restoreAllMocks();
  });

  it("sends a request with the current legacy bearer token", async () => {
    const { legacySessionRequest } = await import("./sessionRequest");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await legacySessionRequest("/api/example");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/example"),
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );
    const [, init] = fetchMock.mock.calls[0] ?? [];
    expect((init?.headers as Headers).get("Authorization")).toBe("Bearer legacy-access");
  });

  it("refreshes once and retries when the first request returns 401", async () => {
    const { legacySessionRequest } = await import("./sessionRequest");
    legacyAuthStoreState.refreshSessionTokens.mockResolvedValue("fresh-access");

    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response("{}", { status: 401, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response("{}", { status: 200, headers: { "Content-Type": "application/json" } }));

    const response = await legacySessionRequest("/api/example");

    expect(response.status).toBe(200);
    expect(legacyAuthStoreState.refreshSessionTokens).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [, retryInit] = fetchMock.mock.calls[1] ?? [];
    expect((retryInit?.headers as Headers).get("Authorization")).toBe("Bearer fresh-access");
  });

  it("shares one refresh across concurrent 401 responses", async () => {
    const { legacySessionRequest } = await import("./sessionRequest");
    legacyAuthStoreState.refreshSessionTokens.mockImplementation(
      async () => {
        await new Promise((resolve) => setTimeout(resolve, 0));
        return "fresh-access";
      },
    );

    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response("{}", { status: 401, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response("{}", { status: 401, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValue(new Response("{}", { status: 200, headers: { "Content-Type": "application/json" } }));

    const first = legacySessionRequest("/api/one");
    const second = legacySessionRequest("/api/two");

    const [firstResponse, secondResponse] = await Promise.all([first, second]);

    expect(firstResponse.status).toBe(200);
    expect(secondResponse.status).toBe(200);
    expect(legacyAuthStoreState.refreshSessionTokens).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

  it("rejects cleanly when refresh fails", async () => {
    const { legacySessionRequest } = await import("./sessionRequest");
    const refreshError = new Error("refresh failed");
    legacyAuthStoreState.refreshSessionTokens.mockRejectedValue(refreshError);

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("{}", { status: 401, headers: { "Content-Type": "application/json" } }),
    );

    await expect(legacySessionRequest("/api/example")).rejects.toBe(refreshError);
  });
});
