// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { reactive } from 'vue';

const routeState = reactive({
  meta: {
    moduleKey: 'employees',
  } as Record<string, unknown>,
});

const authStoreState = reactive({
  effectiveRole: 'tenant_admin',
});

const moduleWorkspacePageProps: Array<Record<string, unknown>> = [];

vi.mock('vue-router', () => ({
  useRoute: () => routeState,
}));

vi.mock('#/locales', () => ({
  $t: (key: string) => {
    const translations: Record<string, string> = {
      'sicherplan.admin.employees': 'Employees',
      'sicherplan.ui.moduleEyebrow': 'MODULE CONTROL',
      'sicherplan.ui.modules.employees.description': 'Employee administration separates private HR data.',
      'sicherplan.ui.modules.employees.workspace': 'Employee workspace',
      'sicherplan.ui.workspaceTitle': 'Workspace',
    };
    return translations[key] ?? key;
  },
}));

vi.mock('#/sicherplan-legacy/stores/auth', () => ({
  useAuthStore: () => authStoreState,
}));

vi.mock('#/components/sicherplan/empty-state.vue', () => ({
  default: {
    name: 'EmptyStateStub',
    template: '<div data-testid="empty-state" />',
  },
}));

vi.mock('#/views/_core/fallback/forbidden.vue', () => ({
  default: {
    name: 'ForbiddenViewStub',
    template: '<div data-testid="forbidden-view" />',
  },
}));

vi.mock('#/components/sicherplan/module-workspace-page.vue', () => ({
  default: {
    name: 'ModuleWorkspacePageStub',
    props: ['badges', 'description', 'eyebrow', 'showIntro', 'title'],
    setup(props: Record<string, unknown>) {
      moduleWorkspacePageProps.push(props);
      return {};
    },
    template: `
      <section data-testid="module-workspace-page">
        <div v-if="showIntro !== false" data-testid="page-intro">
          {{ eyebrow }} {{ title }} {{ description }}
          <span v-for="badge in badges" :key="badge.key">{{ badge.key }}</span>
        </div>
        <slot name="workspace" />
      </section>
    `,
  },
}));

vi.mock('#/components/sicherplan/section-block.vue', () => ({
  default: {
    name: 'SectionBlockStub',
    props: ['description', 'showHeader', 'title'],
    template: `
      <section data-testid="section-block">
        <header v-if="showHeader" data-testid="section-block-header">{{ title }} {{ description }}</header>
        <slot />
      </section>
    `,
  },
}));

vi.mock('./module-registry', () => ({
  moduleRegistry: {
    employees: {
      badges: [
        { key: 'HR Split', tone: 'success' },
        { key: 'Private Data', tone: 'warning' },
        { key: 'Import Ready', tone: 'default' },
      ],
      component: {
        name: 'EmployeeAdminStub',
        template: `
          <section>
            <div data-testid="employee-list-section">Employee List</div>
            <div data-testid="employee-detail-workspace">Employee Detail</div>
          </section>
        `,
      },
      descriptionKey: 'sicherplan.ui.modules.employees.description',
      highlightKeys: [],
      quickLinks: [],
      showPageIntro: false,
      showWorkspaceSectionHeader: false,
      stats: [],
      titleKey: 'sicherplan.admin.employees',
      workspaceDescriptionKey: 'sicherplan.ui.modules.employees.workspace',
    },
  },
}));

describe('AdminModuleView employees wrapper', () => {
  beforeEach(() => {
    routeState.meta = { moduleKey: 'employees' };
    authStoreState.effectiveRole = 'tenant_admin';
    moduleWorkspacePageProps.length = 0;
  });

  it('does not render the ModuleWorkspacePage intro for employees while keeping the workspace visible', async () => {
    const { default: AdminModuleView } = await import('./admin-module-view.vue');
    const wrapper = mount(AdminModuleView);

    expect(moduleWorkspacePageProps.at(-1)?.showIntro).toBe(false);
    expect(wrapper.find('[data-testid="page-intro"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('MODULE CONTROL');
    expect(wrapper.text()).not.toContain('Employee administration separates private HR data.');
    expect(wrapper.text()).not.toContain('HR Split');
    expect(wrapper.text()).not.toContain('Private Data');
    expect(wrapper.text()).not.toContain('Import Ready');
    expect(wrapper.find('[data-testid="employee-list-section"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="employee-detail-workspace"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="section-block-header"]').exists()).toBe(false);
  });
});
