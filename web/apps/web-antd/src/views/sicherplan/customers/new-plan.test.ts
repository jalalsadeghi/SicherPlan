// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, reactive } from 'vue';

import CustomerNewPlanWizardView from './new-plan.vue';
import { buildWizardDraftStorageKey } from './new-plan-wizard-drafts';

const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
const routeState = reactive({
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
  $t: (key: string) => key,
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
    methods: {
      async submitCurrentStep() {
        if (this.currentStepId === 'order-details') {
          this.$emit('saved-context', { order_id: 'order-1' });
          this.$emit('step-completion', 'order-details', true);
          this.$emit('step-ui-state', 'order-details', { dirty: false, error: '' });
          return true;
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
          this.$emit('saved-context', { shift_plan_id: 'shift-plan-1' });
          this.$emit('step-completion', 'shift-plan', true);
          this.$emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
          return true;
        }
        return true;
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
  template: '<div><slot name="workspace" /></div>',
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
    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Alpha Security');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.findAll('.sp-customer-plan-wizard__step')).toHaveLength(8);
    expect(wrapper.get('[data-testid="customer-new-plan-previous"]').attributes('disabled')).toBeDefined();
  });

  it('normalizes an invalid later-step query back to order-details', async () => {
    routeState.query = { customer_id: 'customer-1', step: 'series-exceptions' };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(routerReplaceMock).toHaveBeenCalledWith({
      path: '/admin/customers/new-plan',
      query: {
        customer_id: 'customer-1',
      },
    });
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
      path: '/admin/customers/new-plan',
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
      path: '/admin/customers/new-plan',
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

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/new-plan',
      query: {
        customer_id: 'customer-1',
        order_id: 'order-1',
        step: 'equipment-lines',
      },
    });
  });

  it('hydrates a later step from route state when required ids exist', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'equipment-lines',
    };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
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
      path: '/admin/customers/new-plan',
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

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await flushPromises();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('series-exceptions');
    expect(
      routerReplaceMock.mock.calls.some(
        ([payload]) =>
          payload?.path === '/admin/customers/new-plan' &&
          payload?.query?.step === 'shift-plan' &&
          payload?.query?.shift_plan_id === 'shift-plan-1',
      ),
    ).toBe(false);
    expect(routerReplaceMock).toHaveBeenLastCalledWith({
      path: '/admin/customers/new-plan',
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

  it('does not reset from order-details when only the access token changes for the same customer', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
  });

  it('returns to order-details when Previous is clicked from equipment-lines', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-1',
      step: 'equipment-lines',
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
      step: 'equipment-lines',
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

  it('cancels back to customer plans after discard confirmation', async () => {
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
        tab: 'plans',
      },
    });
  });
});
