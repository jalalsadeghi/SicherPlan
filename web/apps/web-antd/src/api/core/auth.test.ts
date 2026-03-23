// @vitest-environment happy-dom

import { describe, expect, it } from 'vitest';

import { AuthApiError, resolveLoginErrorMessageKey } from './auth';

describe('login error message mapping', () => {
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
});
