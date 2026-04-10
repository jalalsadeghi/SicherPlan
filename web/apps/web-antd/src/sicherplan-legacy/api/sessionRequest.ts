import { useAccessStore } from "@vben/stores";

import { webAppConfig } from "@/config/env";
import { useAuthStore } from "@/stores/auth";

let refreshInFlight: null | Promise<string> = null;

function generateRequestId(prefix = "legacy-session") {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function readPrimaryAccessToken() {
  try {
    return useAccessStore().accessToken ?? "";
  } catch {
    return "";
  }
}

function isUnauthorizedResponse(response: Response) {
  return response.status === 401;
}

async function runRawSessionRequest(
  path: string,
  accessToken: string,
  options: RequestInit & { body?: BodyInit | null; jsonBody?: unknown } = {},
) {
  const headers = new Headers(options.headers ?? {});
  if (!headers.has("Content-Type") && options.jsonBody !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (!headers.has("X-Request-Id")) {
    headers.set("X-Request-Id", generateRequestId());
  }

  return fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    ...options,
    headers,
    body: options.body ?? (options.jsonBody === undefined ? undefined : JSON.stringify(options.jsonBody)),
  });
}

async function refreshLegacySessionToken() {
  if (refreshInFlight) {
    return refreshInFlight;
  }

  const authStore = useAuthStore();
  refreshInFlight = authStore
    .refreshSessionTokens()
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

export async function legacySessionRequest(
  path: string,
  options: RequestInit & { accessToken?: string; body?: BodyInit | null; jsonBody?: unknown } = {},
) {
  const authStore = useAuthStore();
  authStore.syncFromPrimarySession();
  const initialToken = authStore.effectiveAccessToken || authStore.accessToken || options.accessToken || readPrimaryAccessToken();

  let response = await runRawSessionRequest(path, initialToken, options);
  if (!isUnauthorizedResponse(response)) {
    return response;
  }

  const refreshedToken = await refreshLegacySessionToken();
  if (!refreshedToken || refreshedToken === initialToken) {
    return response;
  }

  response = await runRawSessionRequest(path, refreshedToken, options);
  return response;
}
