import { describe, expect, it } from 'vitest';

import { moduleRegistry } from './module-registry';

describe('module registry wrapper flags', () => {
  it('removes the page intro and workspace section header for the core module', () => {
    expect(moduleRegistry.core.showPageIntro).toBe(false);
    expect(moduleRegistry.core.showWorkspaceSectionHeader).toBe(false);
  });

  it('keeps wrapper intro and workspace section header defaults for other modules', () => {
    expect(moduleRegistry['platform-services'].showPageIntro).toBeUndefined();
  });

  it('hides the customers workspace section header only for tenant admin', () => {
    expect(moduleRegistry.customers.hideWorkspaceSectionHeaderForRoles).toEqual(['tenant_admin']);
  });

  it('removes the platform-services workspace section header while keeping the hero', () => {
    expect(moduleRegistry['platform-services'].showPageIntro).toBeUndefined();
    expect(moduleRegistry['platform-services'].showWorkspaceSectionHeader).toBe(false);
  });

  it('keeps customers unavailable to platform admin in the shared module registry', () => {
    expect(moduleRegistry.customers.allowedRoles).toEqual([
      'tenant_admin',
      'dispatcher',
      'accounting',
      'controller_qm',
    ]);
  });
});
