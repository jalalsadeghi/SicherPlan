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

  it('splits the customer portal into explicit child routes', () => {
    const portalSection = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanPortal',
    );
    const customerPortalSection = portalSection?.children?.find(
      (route) => route.name === 'SicherPlanCustomerPortalSection',
    );

    expect(customerPortalSection?.redirect).toBe('/portal/customer/overview');
    expect(customerPortalSection?.children?.map((route) => route.path)).toEqual([
      '/portal/customer/overview',
      '/portal/customer/orders',
      '/portal/customer/schedules',
      '/portal/customer/watchbooks',
      '/portal/customer/timesheets',
      '/portal/customer/invoices',
      '/portal/customer/reports',
      '/portal/customer/history',
    ]);
  });

  it('wires planning-orders to the correct module and role set', () => {
    const operationsSection = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanOperationsSection',
    );
    const planningOrdersRoute = operationsSection?.children?.find(
      (route) => route.name === 'SicherPlanPlanningOrders',
    );

    expect(operationsSection?.meta?.authority).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
    expect(planningOrdersRoute?.path).toBe('/admin/planning-orders');
    expect(planningOrdersRoute?.meta?.moduleKey).toBe('planning-orders');
    expect(planningOrdersRoute?.meta?.authority).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
  });

  it('keeps planning-staffing aligned to the implemented staffing roles only', () => {
    const operationsSection = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanOperationsSection',
    );
    const staffingRoute = operationsSection?.children?.find(
      (route) => route.name === 'SicherPlanPlanningStaffing',
    );

    expect(staffingRoute?.path).toBe('/admin/planning-staffing');
    expect(staffingRoute?.meta?.moduleKey).toBe('planning-staffing');
    expect(staffingRoute?.meta?.authority).toEqual([
      'tenant_admin',
      'dispatcher',
    ]);
  });

  it('adds workforce catalogs as a dedicated workforce child route with employee-domain roles', () => {
    const workforceSection = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanWorkforceSection',
    );
    const catalogsRoute = workforceSection?.children?.find(
      (route) => route.name === 'SicherPlanWorkforceCatalogs',
    );

    expect(catalogsRoute?.path).toBe('/admin/workforce-catalogs');
    expect(catalogsRoute?.meta?.moduleKey).toBe('workforce-catalogs');
    expect(catalogsRoute?.meta?.authority).toEqual([
      'tenant_admin',
      'dispatcher',
      'controller_qm',
    ]);
  });
});
