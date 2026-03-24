// @vitest-environment happy-dom

import { beforeEach, describe, expect, it } from 'vitest';

import {
  persistRememberedLoginValues,
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
});
