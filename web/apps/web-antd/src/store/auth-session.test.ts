// @vitest-environment happy-dom

import { beforeEach, describe, expect, it } from 'vitest';

import {
  clearStoredAuthSessionMetadata,
  persistAuthSessionMetadata,
  persistRememberedLoginValues,
  readStoredAuthSessionMetadata,
  readRememberedLoginValues,
} from './auth-session';

describe('auth remembered login storage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('stores tenant and identifier when remember me is enabled', () => {
    persistRememberedLoginValues({
      identifier: 'sysadmin',
      rememberMe: true,
      tenantCode: 'system',
    });

    expect(readRememberedLoginValues()).toEqual({
      identifier: 'sysadmin',
      rememberMe: true,
      tenantCode: 'system',
    });
  });

  it('clears remembered login values when remember me is disabled', () => {
    persistRememberedLoginValues({
      identifier: 'sysadmin',
      rememberMe: true,
      tenantCode: 'system',
    });

    persistRememberedLoginValues({
      rememberMe: false,
    });

    expect(readRememberedLoginValues()).toEqual({
      identifier: '',
      rememberMe: false,
      tenantCode: '',
    });
  });

  it('stores and reads auth session metadata', () => {
    persistAuthSessionMetadata({
      accessTokenExpiresAt: '2026-04-12T10:15:00Z',
      refreshTokenExpiresAt: '2026-04-19T10:00:00Z',
      rememberMe: true,
      sessionId: 'session-1',
    });

    expect(readStoredAuthSessionMetadata()).toEqual({
      accessTokenExpiresAt: '2026-04-12T10:15:00Z',
      refreshTokenExpiresAt: '2026-04-19T10:00:00Z',
      rememberMe: true,
      sessionId: 'session-1',
    });
  });

  it('clears auth session metadata explicitly', () => {
    persistAuthSessionMetadata({
      accessTokenExpiresAt: '2026-04-12T10:15:00Z',
      refreshTokenExpiresAt: '2026-04-19T10:00:00Z',
      rememberMe: true,
      sessionId: 'session-1',
    });

    clearStoredAuthSessionMetadata();

    expect(readStoredAuthSessionMetadata()).toEqual({
      accessTokenExpiresAt: '',
      refreshTokenExpiresAt: '',
      rememberMe: false,
      sessionId: '',
    });
  });
});
