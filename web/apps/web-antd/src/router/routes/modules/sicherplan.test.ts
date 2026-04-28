// @vitest-environment happy-dom

import { describe, expect, it } from 'vitest';

import sicherplanRoutes from './sicherplan';

function findRouteByName(
  name: string,
  routes = sicherplanRoutes,
): (typeof sicherplanRoutes)[number] | undefined {
  for (const route of routes) {
    if (route.name === name) {
      return route;
    }
    if (route.children?.length) {
      const match = findRouteByName(name, route.children as typeof sicherplanRoutes);
      if (match) {
        return match;
      }
    }
  }
  return undefined;
}

describe('sicherplan route authority', () => {
  it('keeps customers hidden from platform admin and available to supported tenant-scoped roles as a direct route', () => {
    const customersRoute = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanCustomers',
    );

    expect(customersRoute?.meta?.authority).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
    expect(customersRoute?.meta?.fullPathKey).toBe(false);
    expect(customersRoute?.path).toBe('/admin/customers');
    expect(customersRoute?.children).toEqual([]);
  });

  it('adds the hidden customer order workspace route with legacy new-plan alias for tenant admins only', () => {
    const orderWorkspaceRoute = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanCustomerOrderWorkspace',
    );
    const legacyNewPlanRoute = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanCustomerNewPlan',
    );

    expect(orderWorkspaceRoute?.path).toBe('/admin/customers/order-workspace');
    expect(orderWorkspaceRoute?.alias).toBe('/admin/customers/new-plan');
    expect(legacyNewPlanRoute).toBeUndefined();
    expect(orderWorkspaceRoute?.meta?.authority).toEqual(['tenant_admin']);
    expect(orderWorkspaceRoute?.meta?.fullPathKey).toBe(false);
    expect(orderWorkspaceRoute?.meta?.hideInMenu).toBe(true);
    expect(`${orderWorkspaceRoute?.meta?.title}`).toContain('customerOrderWorkspace');
    expect(`${orderWorkspaceRoute?.meta?.title}`).not.toContain('customerNewPlan');
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

  it('marks grouped sidebar sections as non-navigating menu containers', () => {
    const sectionNames = [
      'SicherPlanAdministrationSection',
      'SicherPlanWorkforceSection',
      'SicherPlanOperationsSection',
      'SicherPlanFinanceSection',
      'SicherPlanReportingSection',
      'SicherPlanPublic',
      'SicherPlanPortal',
    ];

    for (const sectionName of sectionNames) {
      const route = sicherplanRoutes.find((item) => item.name === sectionName);
      expect(route?.children?.length).toBeGreaterThan(0);
      expect(route?.meta?.menuContainer).toBe(true);
    }
  });

  it('flattens customers into one direct sidebar route instead of a Customers -> Customers group', () => {
    const customersSection = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanCustomersSection',
    );
    const customersRoute = sicherplanRoutes.find(
      (route) => route.name === 'SicherPlanCustomers',
    );

    expect(customersSection).toBeUndefined();
    expect(customersRoute?.meta?.menuContainer).not.toBe(true);
    expect(customersRoute?.meta?.icon).toBe('lucide:users');
  });

  it('marks tabbed SicherPlan workspace routes as keepAlive and domCached', () => {
    const cachedRouteNames = [
      'SicherPlanDashboard',
      'SicherPlanCoreAdmin',
      'SicherPlanPlatformServices',
      'SicherPlanTenantUsers',
      'SicherPlanHealthDiagnostics',
      'SicherPlanCustomers',
      'SicherPlanCustomerOrderWorkspace',
      'SicherPlanRecruiting',
      'SicherPlanEmployees',
      'SicherPlanWorkforceCatalogs',
      'SicherPlanSubcontractors',
      'SicherPlanPlanning',
      'SicherPlanPlanningOrders',
      'SicherPlanPlanningShifts',
      'SicherPlanPlanningStaffing',
      'SicherPlanFinanceActuals',
      'SicherPlanFinancePayroll',
      'SicherPlanFinanceBilling',
      'SicherPlanFinanceSubcontractorChecks',
      'SicherPlanReporting',
      'SicherPlanCustomerPortalOverview',
      'SicherPlanCustomerPortalOrders',
      'SicherPlanCustomerPortalSchedules',
      'SicherPlanCustomerPortalWatchbooks',
      'SicherPlanCustomerPortalTimesheets',
      'SicherPlanCustomerPortalInvoices',
      'SicherPlanCustomerPortalReports',
      'SicherPlanCustomerPortalHistory',
      'SicherPlanSubcontractorPortal',
      'SicherPlanApplicantForm',
    ] as const;

    for (const routeName of cachedRouteNames) {
      const route = findRouteByName(routeName);
      expect(route?.meta?.keepAlive, routeName).toBe(true);
      expect(route?.meta?.domCached, routeName).toBe(true);
    }
  });

  it('does not dom-cache pure menu container routes', () => {
    const containerRouteNames = [
      'SicherPlanAdministrationSection',
      'SicherPlanWorkforceSection',
      'SicherPlanOperationsSection',
      'SicherPlanFinanceSection',
      'SicherPlanReportingSection',
      'SicherPlanPublic',
      'SicherPlanPortal',
      'SicherPlanCustomerPortalSection',
    ] as const;

    for (const routeName of containerRouteNames) {
      const route = findRouteByName(routeName);
      expect(route?.meta?.menuContainer, routeName).toBe(true);
      expect(route?.meta?.domCached, routeName).not.toBe(true);
    }
  });

  it('dom-caches AdminModuleView-powered routes because shared route names do not make KeepAlive reliable on their own', () => {
    const adminModuleRouteNames = [
      'SicherPlanCoreAdmin',
      'SicherPlanPlatformServices',
      'SicherPlanCustomers',
      'SicherPlanRecruiting',
      'SicherPlanEmployees',
      'SicherPlanWorkforceCatalogs',
      'SicherPlanSubcontractors',
      'SicherPlanPlanning',
      'SicherPlanPlanningOrders',
      'SicherPlanPlanningShifts',
      'SicherPlanPlanningStaffing',
      'SicherPlanFinanceActuals',
      'SicherPlanFinancePayroll',
      'SicherPlanFinanceBilling',
      'SicherPlanFinanceSubcontractorChecks',
      'SicherPlanReporting',
    ] as const;

    for (const routeName of adminModuleRouteNames) {
      const route = findRouteByName(routeName);
      expect(route?.component, routeName).toBeDefined();
      expect(route?.meta?.keepAlive, routeName).toBe(true);
      expect(route?.meta?.domCached, routeName).toBe(true);
    }
  });
});
