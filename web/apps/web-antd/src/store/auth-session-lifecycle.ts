import { useAuthStore } from './auth';
import { subscribeAuthSessionStateChanged } from './auth-session-events';
import { readStoredAuthSessionMetadata } from './auth-session';
import { getAuthSessionRefreshDelay } from './auth-session-timing';

let lifecycleInitialized = false;
let refreshTimer: null | ReturnType<typeof setTimeout> = null;
let unsubscribeSessionListener: null | (() => void) = null;

function clearRefreshTimer() {
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

async function refreshSessionForLifecycle(
  reason: 'bootstrap' | 'focus' | 'proactive' | 'visibility',
) {
  const authStore = useAuthStore();
  const refreshed = await authStore.ensureSessionReady({
    forceRefresh: reason !== 'bootstrap',
    redirectOnFailure: reason !== 'bootstrap',
  });
  scheduleNextSessionRefresh();
  return refreshed;
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
