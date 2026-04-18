// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent } from 'vue';

import CustomerNewPlanWizardView from './new-plan.vue';

const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
const routeState = {
  query: {} as Record<string, unknown>,
};
const authStoreState = {
  accessToken: 'token-1',
  effectiveAccessToken: 'token-1',
  effectiveRole: 'tenant_admin',
  effectiveTenantScopeId: 'tenant-1',
  isSessionResolving: false,
  ensureSessionReady: vi.fn().mockResolvedValue(undefined),
  syncFromPrimarySession: vi.fn(),
};
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
    emits: ['step-ui-state'],
    template: `
      <div data-testid="customer-new-plan-step-content-stub">
        stub
        <button data-testid="customer-new-plan-mark-dirty" type="button" @click="$emit('step-ui-state', 'planning', { dirty: true, error: '' })">
          dirty
        </button>
      </div>
    `,
  }),
}));

const ModuleWorkspacePageStub = defineComponent({
  name: 'ModuleWorkspacePageStub',
  template: '<div class="module-workspace-page-stub"><slot name="workspace" /></div>',
});

const SectionBlockStub = defineComponent({
  name: 'SectionBlockStub',
  template: '<section class="section-block-stub"><slot /></section>',
});

const EmptyStateStub = defineComponent({
  name: 'EmptyStateStub',
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
  },
  template: '<div class="empty-state-stub" v-bind="$attrs"><strong>{{ title }}</strong><span>{{ description }}</span></div>',
});

const ForbiddenViewStub = defineComponent({
  name: 'ForbiddenViewStub',
  template: '<div data-testid="forbidden-view">forbidden</div>',
});

function buildCustomer(overrides: Record<string, unknown> = {}) {
  return {
    id: 'customer-1',
    tenant_id: 'tenant-1',
    customer_number: 'CU-1000',
    name: 'Alpha Security',
    status: 'active',
    version_no: 1,
    legal_name: null,
    external_ref: null,
    legal_form_lookup_id: null,
    classification_lookup_id: null,
    ranking_lookup_id: null,
    customer_status_lookup_id: null,
    default_branch_id: null,
    default_mandate_id: null,
    notes: null,
    created_at: '2026-04-01T08:00:00Z',
    updated_at: '2026-04-01T08:00:00Z',
    portal_person_names_released: false,
    portal_person_names_released_at: null,
    portal_person_names_released_by_user_id: null,
    archived_at: null,
    contacts: [],
    addresses: [],
    ...overrides,
  };
}

function mountComponent() {
  return mount(CustomerNewPlanWizardView, {
    global: {
      stubs: {
        ModuleWorkspacePage: ModuleWorkspacePageStub,
        SectionBlock: SectionBlockStub,
        EmptyState: EmptyStateStub,
        ForbiddenView: ForbiddenViewStub,
      },
    },
  });
}

describe('CustomerNewPlanWizardView', () => {
  beforeEach(() => {
    vi.stubGlobal('confirm', confirmMock);
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

  it('shows the wizard shell for a valid selected customer and disables Previous on step 1', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    expect(customersApiMocks.getCustomerMock).toHaveBeenCalledWith('tenant-1', 'customer-1', 'token-1');
    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Alpha Security');
    expect(wrapper.find('[data-testid="customer-new-plan-stepper"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-previous"]').attributes('disabled')).toBeDefined();
    expect(wrapper.get('[data-testid="customer-new-plan-next"]')).toBeTruthy();
    expect(wrapper.get('[data-testid="customer-new-plan-breadcrumb"]').attributes('aria-label')).toBe(
      'sicherplan.customerPlansWizard.breadcrumbAria',
    );
  });

  it('normalizes an invalid later-step query back to the first allowed step', async () => {
    routeState.query = { customer_id: 'customer-1', step: 'series-exceptions' };
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
    expect(routerReplaceMock).toHaveBeenCalledWith({
      path: '/admin/customers/new-plan',
      query: {
        customer_id: 'customer-1',
      },
    });
  });

  it('shows a loading state while the customer context is resolving', async () => {
    routeState.query = { customer_id: 'customer-1' };
    customersApiMocks.getCustomerMock.mockImplementation(
      () => new Promise(() => undefined),
    );

    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.loadingTitle');
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.loadingBody');
  });

  it('renders a controlled state when customer_id is missing', async () => {
    const wrapper = mountComponent();
    await flushPromises();

    expect(customersApiMocks.getCustomerMock).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.missingCustomerTitle');
  });

  it('renders a controlled state when the customer is unknown', async () => {
    const { CustomerAdminApiError } = await import('#/sicherplan-legacy/api/customers');
    routeState.query = { customer_id: 'missing-customer' };
    customersApiMocks.getCustomerMock.mockRejectedValue(
      new CustomerAdminApiError(404, {
        code: 'customers.customer.not_found',
        message_key: 'errors.customers.customer.not_found',
        request_id: 'req-1',
        details: {},
      }),
    );

    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.unknownCustomerTitle');
  });

  it('blocks unauthorized access in the shell', async () => {
    authStoreState.effectiveRole = 'dispatcher';
    routeState.query = { customer_id: 'customer-1' };

    const wrapper = mountComponent();
    await flushPromises();

    expect(customersApiMocks.getCustomerMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="forbidden-view"]').exists()).toBe(true);
  });

  it('cancels back into Customer > Plans with the selected customer context', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-cancel"]').trigger('click');
    expect(routerPushMock).toHaveBeenCalledWith({
      path: '/admin/customers',
      query: {
        customer_id: 'customer-1',
        tab: 'plans',
      },
    });
  });

  it('protects breadcrumb/cancel exits when the wizard has dirty state', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-mark-dirty"]').trigger('click');
    confirmMock.mockReturnValue(false);

    await wrapper.get('[data-testid="customer-new-plan-cancel"]').trigger('click');
    expect(confirmMock).toHaveBeenCalledWith('sicherplan.customerPlansWizard.confirmDiscard');
    expect(routerPushMock).not.toHaveBeenCalled();

    await wrapper.get('[data-testid="customer-new-plan-breadcrumb"]').findAll('button')[0]!.trigger('click');
    expect(routerPushMock).not.toHaveBeenCalled();
  });
});
