// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const authStoreState = vi.hoisted(() => ({
  ensureSessionReady: vi.fn(async () => true),
  hasRefreshToken: true,
}));

vi.mock('./auth', () => ({
  useAuthStore: () => authStoreState,
}));

import {
  initializeAuthSessionLifecycle,
  resetAuthSessionLifecycleForTests,
} from './auth-session-lifecycle';
import {
  getAuthSessionRefreshDelay,
  isAuthSessionExpiringSoon,
} from './auth-session-timing';

describe('auth session lifecycle', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    window.localStorage.clear();
    authStoreState.ensureSessionReady.mockClear();
    authStoreState.ensureSessionReady.mockResolvedValue(true);
    authStoreState.hasRefreshToken = true;
  });

  afterEach(() => {
    resetAuthSessionLifecycleForTests();
    vi.useRealTimers();
  });

  it('detects when an access token is close to expiry', () => {
    const now = Date.parse('2026-04-12T10:00:00Z');
    expect(
      isAuthSessionExpiringSoon('2026-04-12T10:00:30Z', now),
    ).toBe(true);
    expect(
      isAuthSessionExpiringSoon('2026-04-12T10:05:00Z', now),
    ).toBe(false);
  });

  it('schedules proactive refresh from the stored access-token expiry', async () => {
    window.localStorage.setItem(
      'sicherplan.auth.session.metadata',
      JSON.stringify({
        accessTokenExpiresAt: '2026-04-12T10:01:00Z',
        refreshTokenExpiresAt: '2026-04-19T10:00:00Z',
        rememberMe: true,
        sessionId: 'session-1',
      }),
    );

    vi.setSystemTime(new Date('2026-04-12T10:00:00Z'));
    await initializeAuthSessionLifecycle();

    expect(authStoreState.ensureSessionReady).toHaveBeenCalledWith({
      forceRefresh: false,
      redirectOnFailure: false,
    });

    authStoreState.ensureSessionReady.mockClear();
    await vi.advanceTimersByTimeAsync(1000);

    expect(authStoreState.ensureSessionReady).toHaveBeenCalledWith({
      forceRefresh: true,
      redirectOnFailure: true,
    });
  });

  it('refreshes again when the page becomes visible or focused', async () => {
    window.localStorage.setItem(
      'sicherplan.auth.session.metadata',
      JSON.stringify({
        accessTokenExpiresAt: '2026-04-12T10:05:00Z',
        refreshTokenExpiresAt: '2026-04-19T10:00:00Z',
        rememberMe: true,
        sessionId: 'session-1',
      }),
    );

    await initializeAuthSessionLifecycle();
    authStoreState.ensureSessionReady.mockClear();

    Object.defineProperty(document, 'visibilityState', {
      configurable: true,
      value: 'visible',
    });
    document.dispatchEvent(new Event('visibilitychange'));
    window.dispatchEvent(new Event('focus'));

    expect(authStoreState.ensureSessionReady).toHaveBeenNthCalledWith(1, {
      forceRefresh: true,
      redirectOnFailure: true,
    });
    expect(authStoreState.ensureSessionReady).toHaveBeenNthCalledWith(2, {
      forceRefresh: true,
      redirectOnFailure: true,
    });
  });

  it('computes a zero-delay refresh when expiry is already inside the lead window', () => {
    const now = Date.parse('2026-04-12T10:00:00Z');
    expect(
      getAuthSessionRefreshDelay('2026-04-12T10:00:30Z', now),
    ).toBe(0);
  });
});
