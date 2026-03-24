// @vitest-environment happy-dom

import { describe, expect, it } from 'vitest';

import sicherplanRoutes from './sicherplan';

describe('sicherplan route authority', () => {
  it('keeps customers hidden from platform admin and available to supported tenant-scoped roles', () => {
    const customersSection = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanCustomersSection',
    );
    const customersRoute = customersSection?.children?.find(
      (route) => route.name === 'SicherPlanCustomers',
    );

    expect(customersSection?.meta?.authority).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
    expect(customersRoute?.meta?.authority).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
  });
});
