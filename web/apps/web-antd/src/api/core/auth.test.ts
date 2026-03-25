// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';

const accessStoreState = {
  accessToken: null as null | string,
  refreshToken: null as null | string,
  setAccessToken(token: null | string) {
    this.accessToken = token;
  },
  setRefreshToken(token: null | string) {
    this.refreshToken = token;
  },
};

vi.mock('@vben/stores', () => ({
  useAccessStore: () => accessStoreState,
}));

import {
  AuthApiError,
  getCurrentSessionApi,
  loginApi,
  refreshTokenApi,
  resolveLoginErrorMessageKey,
} from './auth';

describe('login error message mapping', () => {
  beforeEach(() => {
    accessStoreState.accessToken = null;
    accessStoreState.refreshToken = null;
    vi.restoreAllMocks();
  });

  it('maps invalid-credential responses to the auth-specific message', () => {
    expect(
      resolveLoginErrorMessageKey(
        new AuthApiError(
          401,
          'iam.auth.invalid_credentials',
          'errors.iam.auth.invalid_credentials',
        ),
      ),
    ).toBe('sicherplan.auth.loginErrors.invalidCredentials');
  });

  it('maps rate limits separately from invalid credentials', () => {
    expect(
      resolveLoginErrorMessageKey(
        new AuthApiError(
          429,
          'iam.auth.rate_limited',
          'errors.iam.auth.rate_limited',
        ),
      ),
    ).toBe('sicherplan.auth.loginErrors.rateLimited');
  });

  it('maps network and server failures to the availability message', () => {
    expect(resolveLoginErrorMessageKey(new TypeError('fetch failed'))).toBe(
      'sicherplan.auth.loginErrors.serverUnavailable',
    );
    expect(
      resolveLoginErrorMessageKey(
        new AuthApiError(
          503,
          'platform.database_unavailable',
          'errors.platform.database_unavailable',
        ),
      ),
    ).toBe('sicherplan.auth.loginErrors.serverUnavailable');
  });

  it('falls back to the generic login failure message', () => {
    expect(resolveLoginErrorMessageKey(new Error('unexpected'))).toBe(
      'sicherplan.auth.loginErrors.generic',
    );
  });

  it('sends remember_me on login and maps the full token payload', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            session: {
              access_token: 'access-1',
              access_token_expires_at: '2026-03-23T10:00:00Z',
              refresh_token: 'refresh-1',
              refresh_token_expires_at: '2026-03-30T10:00:00Z',
              session_id: 'session-1',
            },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      );

    await expect(
      loginApi({
        identifier: 'sysadmin',
        password: 'secret',
        rememberMe: true,
        tenantCode: 'system',
      }),
    ).resolves.toEqual({
      accessToken: 'access-1',
      accessTokenExpiresAt: '2026-03-23T10:00:00Z',
      refreshToken: 'refresh-1',
      refreshTokenExpiresAt: '2026-03-30T10:00:00Z',
      sessionId: 'session-1',
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/auth/login'),
      expect.objectContaining({
        body: JSON.stringify({
          device_id: undefined,
          device_label: undefined,
          identifier: 'sysadmin',
          password: 'secret',
          remember_me: true,
          tenant_code: 'system',
        }),
        method: 'POST',
      }),
    );
  });

  it('refreshes with the stored refresh token and maps the rotated pair', async () => {
    accessStoreState.refreshToken = 'refresh-current';
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          session: {
            access_token: 'access-2',
            access_token_expires_at: '2026-03-23T10:15:00Z',
            refresh_token: 'refresh-2',
            refresh_token_expires_at: '2026-03-30T10:15:00Z',
            session_id: 'session-1',
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    );

    await expect(refreshTokenApi()).resolves.toEqual({
      accessToken: 'access-2',
      accessTokenExpiresAt: '2026-03-23T10:15:00Z',
      refreshToken: 'refresh-2',
      refreshTokenExpiresAt: '2026-03-30T10:15:00Z',
      sessionId: 'session-1',
    });
  });

  it('fails refresh immediately when no refresh token is stored', async () => {
    await expect(refreshTokenApi()).rejects.toMatchObject({
      code: 'iam.auth.invalid_refresh_token',
      messageKey: 'errors.iam.auth.invalid_refresh_token',
      status: 401,
    });
  });

  it('restores the current session by refreshing once when startup hits an expired access token', async () => {
    accessStoreState.accessToken = 'expired-access';
    accessStoreState.refreshToken = 'refresh-current';

    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: 'iam.auth.access_token_expired',
              message_key: 'errors.iam.auth.access_token_expired',
            },
          }),
          {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            session: {
              access_token: 'access-2',
              access_token_expires_at: '2026-03-23T10:15:00Z',
              refresh_token: 'refresh-2',
              refresh_token_expires_at: '2026-03-30T10:15:00Z',
              session_id: 'session-1',
            },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            session_id: 'session-1',
            tenant_id: 'tenant-1',
            tenant_code: 'system',
            user: {
              id: 'user-1',
              username: 'sysadmin',
              email: 'sysadmin@example.invalid',
              display_name: 'System Admin',
              locale: 'de',
              timezone: 'Europe/Berlin',
              status: 'active',
            },
            roles: [],
            permissions: ['core.admin.access'],
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      );

    await expect(getCurrentSessionApi()).resolves.toMatchObject({
      session_id: 'session-1',
      tenant_code: 'system',
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining('/auth/me'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer expired-access',
        }),
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      expect.stringContaining('/auth/refresh'),
      expect.objectContaining({
        body: JSON.stringify({
          refresh_token: 'refresh-current',
        }),
        method: 'POST',
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      expect.stringContaining('/auth/me'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer access-2',
        }),
      }),
    );
    expect(accessStoreState.accessToken).toBe('access-2');
    expect(accessStoreState.refreshToken).toBe('refresh-2');
  });

  it('fails cleanly when the remembered refresh session is no longer valid', async () => {
    accessStoreState.accessToken = 'expired-access';
    accessStoreState.refreshToken = 'refresh-current';

    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: 'iam.auth.access_token_expired',
              message_key: 'errors.iam.auth.access_token_expired',
            },
          }),
          {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            error: {
              code: 'iam.auth.invalid_refresh_token',
              message_key: 'errors.iam.auth.invalid_refresh_token',
            },
          }),
          {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      );

    await expect(getCurrentSessionApi()).rejects.toMatchObject({
      code: 'iam.auth.invalid_refresh_token',
      messageKey: 'errors.iam.auth.invalid_refresh_token',
      status: 401,
    });
  });
});
