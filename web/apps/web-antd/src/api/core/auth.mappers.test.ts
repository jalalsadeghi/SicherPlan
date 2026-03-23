import { describe, expect, it } from 'vitest';

import {
  extractRoleKeys,
  mapCurrentSessionToVbenUser,
  resolveHomePath,
} from './auth.mappers';

describe('sicherplan auth mappers', () => {
  it('deduplicates role keys', () => {
    expect(
      extractRoleKeys([
        { role_key: 'platform_admin' },
        { role_key: 'platform_admin' },
        { role_key: 'tenant_admin' },
      ]),
    ).toEqual(['platform_admin', 'tenant_admin']);
  });

  it('maps customer users to the portal home path', () => {
    expect(resolveHomePath(['customer_user'])).toBe('/portal/customer');
    expect(resolveHomePath(['subcontractor_user'])).toBe('/portal/subcontractor');
    expect(resolveHomePath(['platform_admin'])).toBe('/admin/dashboard');
  });

  it('maps current session payloads into Vben user info', () => {
    const mapped = mapCurrentSessionToVbenUser(
      {
        user: {
          id: 'user-1',
          username: 'sysadmin',
          email: 'sysadmin@example.invalid',
          full_name: 'System Administrator',
          roles: [{ role_key: 'platform_admin' }],
        },
      },
      'token-1',
    );

    expect(mapped.realName).toBe('System Administrator');
    expect(mapped.roles).toEqual(['platform_admin']);
    expect(mapped.homePath).toBe('/admin/dashboard');
    expect(mapped.token).toBe('token-1');
  });
});
