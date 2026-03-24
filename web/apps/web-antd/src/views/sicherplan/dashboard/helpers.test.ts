import { describe, expect, it } from 'vitest';

import { buildDashboardQuickActions } from './helpers';

describe('dashboard quick actions', () => {
  const t = (key: string) => key;

  it('does not expose customers to platform admin', () => {
    const actions = buildDashboardQuickActions({
      isPlatformAdmin: true,
      t,
    });

    expect(actions.map((action) => action.to)).toEqual([
      '/admin/core',
      '/admin/iam/users',
      '/admin/health',
    ]);
  });

  it('keeps customers for tenant-scoped dashboard roles', () => {
    const actions = buildDashboardQuickActions({
      isPlatformAdmin: false,
      t,
    });

    expect(actions.map((action) => action.to)).toContain('/admin/customers');
  });
});
