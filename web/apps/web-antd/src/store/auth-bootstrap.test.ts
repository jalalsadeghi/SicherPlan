import { describe, expect, it } from 'vitest';

import { buildLoginLocation } from './auth-bootstrap';

describe('buildLoginLocation', () => {
  it('includes redirect for non-home authenticated routes', () => {
    expect(buildLoginLocation('/auth/login', '/admin/core', '/admin/customers'))
      .toEqual({
        path: '/auth/login',
        query: { redirect: encodeURIComponent('/admin/customers') },
      });
  });

  it('omits redirect for the default home path', () => {
    expect(buildLoginLocation('/auth/login', '/admin/core', '/admin/core')).toEqual({
      path: '/auth/login',
      query: {},
    });
  });

  it('omits redirect query when explicitly disabled', () => {
    expect(buildLoginLocation('/auth/login', '/admin/core', '/admin/customers', false)).toEqual({
      path: '/auth/login',
      query: {},
    });
  });
});
