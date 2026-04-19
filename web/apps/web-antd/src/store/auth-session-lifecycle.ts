import { useAuthStore } from './auth';
import { subscribeAuthSessionStateChanged } from './auth-session-events';
import { readStoredAuthSessionMetadata } from './auth-session';
import { getAuthSessionRefreshDelay, isAuthSessionExpiringSoon } from './auth-session-timing';

let lifecycleInitialized = false;
let refreshTimer: null | ReturnType<typeof setTimeout> = null;
let unsubscribeSessionListener: null | (() => void) = null;
let lifecycleRefreshPromise: null | Promise<boolean> = null;
let lastInteractiveRefreshStartedAt = 0;

const FOCUS_VISIBILITY_REFRESH_COOLDOWN_MS = 1500;

function clearRefreshTimer() {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

async function refreshSessionForLifecycle(
  reason: 'bootstrap' | 'focus' | 'proactive' | 'visibility',
) {
  const metadata = readStoredAuthSessionMetadata();
  const now = Date.now();
  const authStore = useAuthStore();
  const sessionExpiringSoon = isAuthSessionExpiringSoon(metadata.accessTokenExpiresAt, now);
  const shouldForceRefresh = reason === 'proactive' || ((reason === 'focus' || reason === 'visibility') && sessionExpiringSoon);

  if (lifecycleRefreshPromise) {
    return lifecycleRefreshPromise;
  }

  if (
    (reason === 'focus' || reason === 'visibility')
    && !shouldForceRefresh
    && now - lastInteractiveRefreshStartedAt < FOCUS_VISIBILITY_REFRESH_COOLDOWN_MS
  ) {
    scheduleNextSessionRefresh();
    return true;
  }

  if (reason === 'focus' || reason === 'visibility') {
    lastInteractiveRefreshStartedAt = now;
  }
  lifecycleRefreshPromise = authStore.ensureSessionReady({
    forceRefresh: reason === 'bootstrap' ? false : shouldForceRefresh,
    redirectOnFailure: reason !== 'bootstrap',
  })
    .then((refreshed) => {
      scheduleNextSessionRefresh();
      return refreshed;
    })
    .finally(() => {
      lifecycleRefreshPromise = null;
    });

  return lifecycleRefreshPromise;
}

function scheduleNextSessionRefresh() {
  clearRefreshTimer();

  const authStore = useAuthStore();
  if (!authStore.hasRefreshToken) {
    return;
  }

  const metadata = readStoredAuthSessionMetadata();
  const delay = getAuthSessionRefreshDelay(metadata.accessTokenExpiresAt);
  if (delay === null) {
    return;
  }

  refreshTimer = setTimeout(() => {
    void refreshSessionForLifecycle('proactive');
  }, delay);
}

function handleVisibilityChange() {
  if (typeof document === 'undefined' || document.visibilityState !== 'visible') {
    return;
  }
  void refreshSessionForLifecycle('visibility');
}

function handleWindowFocus() {
  void refreshSessionForLifecycle('focus');
}

export async function initializeAuthSessionLifecycle() {
  if (!lifecycleInitialized) {
    if (typeof document !== 'undefined') {
      document.addEventListener('visibilitychange', handleVisibilityChange);
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('focus', handleWindowFocus);
    }
    unsubscribeSessionListener = subscribeAuthSessionStateChanged(() => {
      scheduleNextSessionRefresh();
    });
    lifecycleInitialized = true;
  }

  await refreshSessionForLifecycle('bootstrap');
}

export function resetAuthSessionLifecycleForTests() {
  clearRefreshTimer();
  lifecycleRefreshPromise = null;
  lastInteractiveRefreshStartedAt = 0;
  unsubscribeSessionListener?.();
  unsubscribeSessionListener = null;
  if (lifecycleInitialized) {
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('focus', handleWindowFocus);
    }
  }
  lifecycleInitialized = false;
}
