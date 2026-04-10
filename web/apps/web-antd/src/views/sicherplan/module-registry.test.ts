import { describe, expect, it } from 'vitest';

import { moduleRegistry } from './module-registry';

describe('module registry wrapper flags', () => {
  it('removes the page intro and workspace section header for the core module', () => {
    const core = moduleRegistry.core!;
    expect(core.showPageIntro).toBe(false);
    expect(core.showWorkspaceSectionHeader).toBe(false);
  });

  it('keeps wrapper intro and workspace section header defaults for other modules', () => {
    const platformServices = moduleRegistry['platform-services']!;
    expect(platformServices.showPageIntro).toBeUndefined();
  });

  it('hides the customers workspace section header only for tenant admin', () => {
    const customers = moduleRegistry.customers!;
    expect(customers.hideWorkspaceSectionHeaderForRoles).toEqual(['tenant_admin']);
  });

  it('removes the platform-services workspace section header while keeping the hero', () => {
    const platformServices = moduleRegistry['platform-services']!;
    expect(platformServices.showPageIntro).toBeUndefined();
    expect(platformServices.showWorkspaceSectionHeader).toBe(false);
  });

  it('removes both shared wrapper blocks for planning setup', () => {
    const planning = moduleRegistry.planning!;
    expect(planning.showPageIntro).toBeUndefined();
    expect(planning.showWorkspaceSectionHeader).toBe(false);
  });

  it('keeps the planning-orders page intro while removing the workspace section header', () => {
    const planningOrders = moduleRegistry['planning-orders']!;
    expect(planningOrders.showPageIntro).toBeUndefined();
    expect(planningOrders.showWorkspaceSectionHeader).toBe(false);
  });

  it('keeps planning-orders available to the implemented commercial role and controller read-only route audience', () => {
    const planningOrders = moduleRegistry['planning-orders']!;
    expect(planningOrders.allowedRoles).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
  });

  it('keeps the planning-shifts page intro while removing the workspace section header', () => {
    const planningShifts = moduleRegistry['planning-shifts']!;
    expect(planningShifts.showPageIntro).toBeUndefined();
    expect(planningShifts.showWorkspaceSectionHeader).toBe(false);
  });

  it('limits planning-staffing to the implemented staffing roles', () => {
    const staffing = moduleRegistry['planning-staffing']!;
    expect(staffing.allowedRoles).toEqual(['tenant_admin', 'dispatcher']);
    expect(staffing.showWorkspaceSectionHeader).toBe(false);
  });

  it('keeps customers unavailable to platform admin in the shared module registry', () => {
    const customers = moduleRegistry.customers!;
    expect(customers.allowedRoles).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
  });
});
