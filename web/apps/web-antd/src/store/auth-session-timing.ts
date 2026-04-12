const SESSION_REFRESH_LEAD_MS = 60_000;

function parseExpiry(value: string) {
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function isAuthSessionExpiringSoon(
  expiresAt: string,
  now = Date.now(),
  leadMs = SESSION_REFRESH_LEAD_MS,
) {
  const parsed = parseExpiry(expiresAt);
  if (parsed === null) {
    return false;
  }
  return parsed - now <= leadMs;
}

export function getAuthSessionRefreshDelay(
  accessTokenExpiresAt: string,
  now = Date.now(),
  leadMs = SESSION_REFRESH_LEAD_MS,
) {
  const parsed = parseExpiry(accessTokenExpiresAt);
  if (parsed === null) {
    return null;
  }
  return Math.max(0, parsed - now - leadMs);
}
