// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, reactive } from 'vue';

import CustomerNewPlanWizardView from './new-plan.vue';
import { buildWizardDraftStorageKey } from './new-plan-wizard-drafts';

const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
const routeState = reactive({
  fullPath: '/admin/customers/order-workspace',
  path: '/admin/customers/order-workspace',
  query: {} as Record<string, unknown>,
});
const authStoreState = reactive({
  accessToken: 'token-1',
  effectiveAccessToken: 'token-1',
  effectiveRole: 'tenant_admin',
  effectiveTenantScopeId: 'tenant-1',
  isSessionResolving: false,
  ensureSessionReady: vi.fn().mockResolvedValue(undefined),
  syncFromPrimarySession: vi.fn(),
});
const customersApiMocks = vi.hoisted(() => ({
  getCustomerMock: vi.fn(),
}));
const confirmMock = vi.fn();

vi.mock('#/locales', () => ({
  $t: (key: string) => ({
    'sicherplan.customerPlansWizard.breadcrumbCustomers': 'Customers',
    'sicherplan.customerPlansWizard.breadcrumbPlans': 'Orders',
    'sicherplan.customerPlansWizard.title': 'Order workspace',
  } as Record<string, string>)[key] ?? key,
}));

vi.mock('vue-router', () => ({
  useRoute: () => routeState,
  useRouter: () => ({
    push: routerPushMock,
    replace: routerReplaceMock,
  }),
}));

vi.mock('#/sicherplan-legacy/stores/auth', () => ({
  useAuthStore: () => authStoreState,
}));

vi.mock('#/sicherplan-legacy/api/customers', async () => {
  const actual = await vi.importActual<typeof import('#/sicherplan-legacy/api/customers')>('#/sicherplan-legacy/api/customers');
  return {
    ...actual,
    getCustomer: customersApiMocks.getCustomerMock,
  };
});

vi.mock('./new-plan-step-content.vue', () => ({
  default: defineComponent({
    name: 'CustomerNewPlanStepContentStub',
    props: {
      currentStepId: { type: String, required: true },
      wizardState: { type: Object, required: true },
    },
    emits: ['saved-context', 'step-completion', 'step-ui-state'],
    data() {
      return {
        returnShiftPlanWithoutSavedContext: false,
        selectedShiftPlanId: '',
        shiftPlanName: '',
        shiftPlanFrom: '',
        shiftPlanTo: '',
      };
    },
    methods: {
      async submitCurrentStep() {
        if (this.currentStepId === 'order-details') {
          this.$emit('saved-context', { order_id: 'order-1' });
          this.$emit('step-completion', 'order-details', true);
          this.$emit('step-ui-state', 'order-details', { dirty: false, error: '' });
          return true;
        }
        if (this.currentStepId === 'order-scope-documents') {
          return {
            success: true,
            completedStepId: 'order-scope-documents',
            dirty: false,
            error: '',
            savedContext: { order_id: this.wizardState.order_id },
          };
        }
        if (this.currentStepId === 'planning-record-overview') {
          this.$emit('saved-context', {
            planning_entity_id: 'site-1',
            planning_entity_type: 'site',
            planning_mode_code: 'site',
            planning_record_id: 'record-1',
          });
          this.$emit('step-completion', 'planning-record-overview', true);
          this.$emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
          return true;
        }
        if (this.currentStepId === 'shift-plan') {
          if (!this.selectedShiftPlanId) {
            return false;
          }
          if (this.returnShiftPlanWithoutSavedContext) {
            return {
              success: true,
              completedStepId: 'shift-plan',
              dirty: false,
              error: '',
            };
          }
          return {
            success: true,
            savedContext: { shift_plan_id: this.selectedShiftPlanId },
            completedStepId: 'shift-plan',
            dirty: false,
            error: '',
          };
        }
        if (this.currentStepId === 'series-exceptions') {
          return {
            success: true,
            completedStepId: 'series-exceptions',
            dirty: false,
            error: '',
            savedContext: {
              order_id: this.wizardState.order_id,
              shift_plan_id: this.wizardState.shift_plan_id,
              series_id: this.wizardState.series_id || 'series-1',
            },
          };
        }
        if (this.currentStepId === 'demand-groups') {
          return {
            success: true,
            completedStepId: 'demand-groups',
            dirty: false,
            error: '',
            savedContext: {
              order_id: this.wizardState.order_id,
              shift_plan_id: this.wizardState.shift_plan_id,
              series_id: this.wizardState.series_id || 'series-1',
            },
          };
        }
        return true;
      },
      selectExistingShiftPlan() {
        this.selectedShiftPlanId = 'shift-plan-1';
        this.shiftPlanName = 'Objektschutz RheinForum Koln - Nordtor Juli 2026 / Shift plan';
        this.shiftPlanFrom = '2026-07-01';
        this.shiftPlanTo = '2026-07-31';
        this.$emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
      },
      simulateMissingShiftPlanCommit() {
        this.returnShiftPlanWithoutSavedContext = true;
      },
    },
    template: `
      <div data-testid="customer-new-plan-step-content-stub">
        <div data-testid="customer-new-plan-step-panel-order-details" v-if="currentStepId === 'order-details'">
          <button
            data-testid="customer-new-plan-mark-order-dirty"
            type="button"
            @click="$emit('step-ui-state', 'order-details', { dirty: true, error: '' })"
          >
            dirty
          </button>
        </div>
        <div data-testid="customer-new-plan-step-panel-order-scope-documents" v-else-if="currentStepId === 'order-scope-documents'">
          order scope
        </div>
        <div data-testid="customer-new-plan-step-panel-shift-plan" v-else-if="currentStepId === 'shift-plan'">
          <button
            data-testid="customer-new-plan-existing-shift-plan-row"
            type="button"
            @click="selectExistingShiftPlan"
          >
            select shift plan
          </button>
          <button
            data-testid="customer-new-plan-simulate-missing-shift-plan-commit"
            type="button"
            @click="simulateMissingShiftPlanCommit"
          >
            simulate missing commit
          </button>
          <input data-testid="customer-new-plan-shift-plan-name" :value="shiftPlanName" />
          <input data-testid="customer-new-plan-shift-plan-from" :value="shiftPlanFrom" />
          <input data-testid="customer-new-plan-shift-plan-to" :value="shiftPlanTo" />
        </div>
      </div>
    `,
  }),
}));

const ModuleWorkspacePageStub = defineComponent({
  name: 'ModuleWorkspacePageStub',
  props: {
    title: { type: String, default: '' },
    eyebrow: { type: String, default: '' },
    description: { type: String, default: '' },
    showIntro: { type: Boolean, default: false },
  },
  template: `
    <div data-testid="module-workspace-page" :data-show-intro="String(showIntro)">
      <div v-if="showIntro" data-testid="module-workspace-intro">{{ eyebrow }} {{ title }} {{ description }}</div>
      <slot name="workspace" />
    </div>
  `,
});

const SectionBlockStub = defineComponent({
  name: 'SectionBlockStub',
  props: {
    title: { type: String, default: '' },
    showHeader: { type: Boolean, default: true },
  },
  template: '<section><slot /></section>',
});

const EmptyStateStub = defineComponent({
  name: 'EmptyStateStub',
  props: {
    title: { type: String, default: '' },
    description: { type: String, default: '' },
  },
  template: '<div data-testid="empty-state">{{ title }} {{ description }}</div>',
});

const ForbiddenViewStub = defineComponent({
  name: 'ForbiddenViewStub',
  template: '<div data-testid="forbidden">forbidden</div>',
});

function buildCustomer(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: 'customer-1',
    tenant_id: 'tenant-1',
    customer_number: 'CU-1000',
    name: 'Alpha Security',
    status: 'active',
    archived_at: null,
    contacts: [],
    addresses: [],
    created_at: '2026-04-01T08:00:00Z',
    updated_at: '2026-04-01T08:00:00Z',
    ...overrides,
  };
}

const mountedWrappers: VueWrapper[] = [];

function mountComponent() {
  const wrapper = mount(CustomerNewPlanWizardView, {
    global: {
      stubs: {
        ModuleWorkspacePage: ModuleWorkspacePageStub,
        SectionBlock: SectionBlockStub,
        EmptyState: EmptyStateStub,
        ForbiddenView: ForbiddenViewStub,
      },
    },
  });
  mountedWrappers.push(wrapper);
  return wrapper;
}

describe('CustomerNewPlanWizardView', () => {
  beforeEach(() => {
    vi.stubGlobal('confirm', confirmMock);
    window.sessionStorage.clear();
    routeState.fullPath = '/admin/customers/order-workspace';
    routeState.path = '/admin/customers/order-workspace';
    routeState.query = {};
    routerPushMock.mockReset();
    routerReplaceMock.mockReset();
    confirmMock.mockReset();
    confirmMock.mockReturnValue(true);
    authStoreState.effectiveRole = 'tenant_admin';
    authStoreState.effectiveTenantScopeId = 'tenant-1';
    authStoreState.effectiveAccessToken = 'token-1';
    authStoreState.accessToken = 'token-1';
    authStoreState.isSessionResolving = false;
    authStoreState.syncFromPrimarySession.mockReset();
    authStoreState.ensureSessionReady.mockReset();
    authStoreState.ensureSessionReady.mockResolvedValue(undefined);
    customersApiMocks.getCustomerMock.mockReset();
    customersApiMocks.getCustomerMock.mockResolvedValue(buildCustomer());
  });

  afterEach(() => {
    while (mountedWrappers.length) {
      mountedWrappers.pop()?.unmount();
    }
    document.body.innerHTML = '';
    window.sessionStorage.clear();
  });

  it('shows the wizard shell for a valid selected customer and starts on order-details', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    expect(customersApiMocks.getCustomerMock).toHaveBeenCalledWith('tenant-1', 'customer-1', 'token-1');
    expect(wrapper.get('[data-testid="module-workspace-page"]').attributes('data-show-intro')).toBe('false');
    expect(wrapper.find('[data-testid="module-workspace-intro"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-breadcrumb"]').text()).toContain(
      'Customers',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-breadcrumb"]').text()).toContain('Orders');
    expect(wrapper.get('[data-testid="customer-new-plan-breadcrumb"]').text()).toContain('Order workspace');
    expect(wrapper.text()).not.toContain('New plan');
    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Alpha Security');
    expect(wrapper.find('[data-testid="customer-new-plan-stepper"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.find('[data-testid="customer-new-plan-step-content-stub"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-action-bar"]').exists()).toBe(true);
    expect(wrapper.findAll('.sp-customer-plan-wizard__step')).toHaveLength(8);
    expect(wrapper.find('[data-testid="customer-new-plan-step-equipment-lines"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-step-requirement-lines"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-step-order-documents"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-step-order-scope-documents"]').text()).toContain(
      'sicherplan.customerPlansWizard.steps.orderScopeDocuments',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-previous"]').attributes('disabled')).toBeDefined();
  });

  it('opens from the old new-plan alias with query params preserved and visible Order workspace naming', async () => {
    routeState.path = '/admin/customers/new-plan';
    routeState.fullPath = '/admin/customers/new-plan?customer_id=customer-1';
    routeState.query = { customer_id: 'customer-1' };

    const wrapper = mountComponent();
    await flushPromises();

    expect(customersApiMocks.getCustomerMock).toHaveBeenCalledWith('tenant-1', 'customer-1', 'token-1');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.get('[data-testid="customer-new-plan-breadcrumb"]').text()).toContain('Order workspace');
    expect(routeState.query).toEqual({ customer_id: 'customer-1' });
    expect(routerReplaceMock).not.toHaveBeenCalled();
  });

  it('opens from the canonical order workspace path with Orders breadcrumb naming', async () => {
    routeState.path = '/admin/customers/order-workspace';
    routeState.fullPath = '/admin/customers/order-workspace?customer_id=customer-1';
    routeState.query = { customer_id: 'customer-1' };

    const wrapper = mountComponent();
    await flushPromises();

    const breadcrumbText = wrapper.get('[data-testid="customer-new-plan-breadcrumb"]').text();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(breadcrumbText).toContain('Customers');
    expect(breadcrumbText).toContain('Orders');
    expect(breadcrumbText).toContain('Order workspace');
    expect(breadcrumbText).not.toContain('New plan');
  });

  it('normalizes an invalid later-step query back to order-details', async () => {
    routeState.query = { customer_id: 'customer-1', step: 'series-exceptions' };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(routerReplaceMock).toHaveBeenCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
      },
    });
  });

  it('falls back from a direct series-exceptions URL without shift_plan_id to shift-plan', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'series-exceptions',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('shift-plan');
    expect(routerReplaceMock).toHaveBeenCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        step: 'shift-plan',
      },
    });
  });

  it('restores a direct valid series-exceptions URL when shift_plan_id is present', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      step: 'series-exceptions',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('shift-plan-1');
  });

  it('falls back from a direct demand-groups URL without shift_plan_id to shift-plan', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'demand-groups',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('shift-plan');
  });

  it('restores a direct valid demand-groups URL when shift_plan_id is present', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
      step: 'demand-groups',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('demand-groups');
    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('shift-plan-1');
  });

  it('normalizes old step=planning links back to order-details and clears stale planning query on the first step', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      step: 'planning',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(routerReplaceMock).toHaveBeenCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
      },
    });
  });

  it('normalizes legacy planning_id to planning_entity_id once and drops the stale key', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'planning-record-overview',
      planning_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
    expect(routerReplaceMock).toHaveBeenCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        step: 'planning-record-overview',
      },
    });
  });

  it('persists order_id into the route after order-details succeeds', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        step: 'order-scope-documents',
      },
    });
  });

  it.each(['equipment-lines', 'requirement-lines', 'order-documents'])(
    'normalizes legacy route step %s when required ids exist',
    async (legacyStepId) => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: legacyStepId,
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        step: 'order-scope-documents',
      },
    });
    },
  );

  it('keeps legacy requirement-lines routes compatible across remounts', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'requirement-lines',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');

    wrapper.unmount();
    const restoredWrapper = mountComponent();
    await flushPromises();

    expect(restoredWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        step: 'order-scope-documents',
      },
    });
  });

  it('falls back to order-details when order-scope-documents is requested without order_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      step: 'order-scope-documents',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
      },
    });
  });

  it('falls back to order-details when planning-record-overview is requested without order_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      step: 'planning-record-overview',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
      },
    });
  });

  it('moves from order-scope-documents to planning-record-overview on Next', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'order-scope-documents',
    };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        step: 'planning-record-overview',
      },
    });
  });

  it('does not auto-jump away from order-details when order_id exists but the route has no explicit step', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
  });

  it('keeps planning-record-overview reachable and lets the step handle planning-context setup itself', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'planning-record-overview',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
    expect(wrapper.find('[data-testid="customer-new-plan-restore-warning"]').exists()).toBe(false);
  });

  it('advances to planning-record-documents after a successful planning-record save and persists planning_record_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'planning-record-overview',
    };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-documents');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        step: 'planning-record-documents',
      },
    });
  });

  it('returns to planning-record-overview from planning-record-documents without dropping planning_record_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'planning-record-documents',
    };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-previous"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        step: 'planning-record-overview',
      },
    });
  });

  it('advances to series-exceptions after a successful shift-plan save even when router.replace mutates the route immediately', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'shift-plan',
    };
    routerReplaceMock.mockImplementation(async ({ query }: { query: Record<string, unknown> }) => {
      routeState.query = { ...query };
    });
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-existing-shift-plan-row"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();
    await flushPromises();

    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('shift-plan-1');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    expect(
      routerReplaceMock.mock.calls.some(
        ([payload]) =>
          payload?.path === '/admin/customers/order-workspace' &&
          payload?.query?.step === 'shift-plan' &&
          payload?.query?.shift_plan_id === 'shift-plan-1',
      ),
    ).toBe(false);
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        shift_plan_id: 'shift-plan-1',
        step: 'series-exceptions',
      },
    });
  });

  it('keeps shift-plan row selection local without immediate route mutation, then commits on Next', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'shift-plan',
    };
    routerReplaceMock.mockImplementation(async ({ query }: { query: Record<string, unknown> }) => {
      routeState.query = { ...query };
    });
    const wrapper = mountComponent();
    await flushPromises();
    routerReplaceMock.mockClear();

    await wrapper.get('[data-testid="customer-new-plan-existing-shift-plan-row"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('shift-plan');
    expect(wrapper.find('[data-testid="customer-new-plan-selected-shift-plan-summary"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toContain('RheinForum');
    expect(routeState.query.shift_plan_id).toBeUndefined();
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('shift-plan-1');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        shift_plan_id: 'shift-plan-1',
        step: 'series-exceptions',
      },
    });
  });

  it('sets a shift-plan diagnostic and does not silently advance when submit reports success without shift_plan_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'shift-plan',
    };
    routerReplaceMock.mockImplementation(async ({ query }: { query: Record<string, unknown> }) => {
      routeState.query = { ...query };
    });
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-existing-shift-plan-row"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-simulate-missing-shift-plan-commit"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('shift-plan');
    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('');
    expect((wrapper.vm as any).wizardState.step_state['shift-plan'].error).toBe('submit_missing_shift_plan_id');
    expect(routeState.query.step).toBe('shift-plan');
  });

  it('repairs a stale shift-plan route snapshot after Step 7 already advanced to series-exceptions', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'shift-plan',
    };
    routerReplaceMock.mockImplementation(async ({ query }: { query: Record<string, unknown> }) => {
      routeState.query = { ...query };
    });
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-existing-shift-plan-row"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    routerReplaceMock.mockClear();

    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'shift-plan',
    };
    await flushPromises();
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('shift-plan-1');
    expect(routerReplaceMock).toHaveBeenCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        shift_plan_id: 'shift-plan-1',
        step: 'series-exceptions',
      },
    });
  });

  it('stays on series-exceptions after repeated watcher flushes once Step 8 has been entered', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'shift-plan',
    };
    routerReplaceMock.mockImplementation(async ({ query }: { query: Record<string, unknown> }) => {
      routeState.query = { ...query };
    });
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-existing-shift-plan-row"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    expect((wrapper.vm as any).wizardState.current_step).toBe('series-exceptions');
    expect(routeState.query.step).toBe('series-exceptions');
    expect(routeState.query.shift_plan_id).toBe('shift-plan-1');
  });

  it('does not clear committed shift_plan_id when the same-scope route later omits shift_plan_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      step: 'series-exceptions',
    };
    routerReplaceMock.mockImplementation(async ({ query }: { query: Record<string, unknown> }) => {
      routeState.query = { ...query };
    });
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');

    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'series-exceptions',
    };
    await flushPromises();
    await flushPromises();

    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('shift-plan-1');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        shift_plan_id: 'shift-plan-1',
        step: 'series-exceptions',
      },
    });
  });

  it('allows explicit user navigation back to shift-plan from series-exceptions without losing the saved shift_plan_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      step: 'shift-plan',
    };
    routerReplaceMock.mockImplementation(async ({ query }: { query: Record<string, unknown> }) => {
      routeState.query = { ...query };
    });
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-existing-shift-plan-row"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');

    await wrapper.get('[data-testid="customer-new-plan-step-shift-plan"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('shift-plan');
    expect((wrapper.vm as any).wizardState.shift_plan_id).toBe('shift-plan-1');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        shift_plan_id: 'shift-plan-1',
        step: 'shift-plan',
      },
    });
  });

  it('does not rewrite the route when route.replace keeps the same wizard context', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();
    routerReplaceMock.mockClear();

    routeState.query = { customer_id: 'customer-1' };
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(routerReplaceMock).not.toHaveBeenCalled();
  });

  it('advances from series-exceptions to demand-groups after a successful series submission', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
      step: 'series-exceptions',
    };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-generate-continue"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('demand-groups');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/order-workspace',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
        shift_plan_id: 'shift-plan-1',
        series_id: 'series-1',
        step: 'demand-groups',
      },
    });
  });

  it('advances from demand-groups to assignments after a successful apply', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
      step: 'demand-groups',
    };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('assignments');
    expect(routerReplaceMock).toHaveBeenLastCalledWith(expect.objectContaining({
      query: expect.objectContaining({
        step: 'assignments',
      }),
    }));
  });

  it('does not reset from order-details when only the access token changes for the same customer', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
  });

  it('returns to order-details when Previous is clicked from order-scope-documents', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'order-scope-documents',
    };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-previous"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
  });

  it('resets wizard context when the customer id changes', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'order-scope-documents',
    };
    const wrapper = mountComponent();
    await flushPromises();

    routeState.query = { customer_id: 'customer-2' };
    customersApiMocks.getCustomerMock.mockResolvedValue(buildCustomer({ customer_number: 'CU-2000', id: 'customer-2', name: 'Beta Security' }));
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Beta Security');
  });

  it('uses a customer-scoped order-details draft key without planning context segments', async () => {
    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'order-details',
    );

    expect(draftKey).toBe('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:order-details');
  });

  it('cancels back to customer orders after discard confirmation', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-mark-order-dirty"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-cancel"]').trigger('click');

    expect(confirmMock).toHaveBeenCalledTimes(1);
    expect(routerPushMock).toHaveBeenCalledWith({
      path: '/admin/customers',
      query: {
        customer_id: 'customer-1',
        tab: 'orders',
      },
    });
  });
});
