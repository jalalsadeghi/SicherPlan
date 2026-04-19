// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, reactive } from 'vue';

import CustomerNewPlanWizardView from './new-plan.vue';

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
    },
    emits: ['step-ui-state'],
    data() {
      return {
        modalOpen: false,
        modalNotes: '',
        modalLatitude: '',
        modalLongitude: '',
        modalName: '',
        modalSiteNo: '',
        modalTimezone: '',
        planningSelectionMode: 'use_existing',
        watchbookEnabled: false,
      };
    },
    template: `
      <div data-testid="customer-new-plan-step-content-stub">
        <div data-testid="customer-new-plan-step-panel-planning" v-if="currentStepId === 'planning'">
          <label>
            <input
              data-testid="customer-new-plan-use-existing-radio"
              v-model="planningSelectionMode"
              type="radio"
              value="use_existing"
            />
            use-existing
          </label>
          <label>
            <input
              data-testid="customer-new-plan-create-new-radio"
              v-model="planningSelectionMode"
              type="radio"
              value="create_new"
            />
            create-new
          </label>
          <button
            data-testid="customer-new-plan-planning-create"
            type="button"
            @click="modalOpen = true"
          >
            open-modal
          </button>
          <div v-if="modalOpen" data-testid="customer-new-plan-planning-create-modal">
            <input data-testid="customer-new-plan-planning-create-site-no" v-model="modalSiteNo" />
            <input data-testid="customer-new-plan-planning-create-name" v-model="modalName" />
            <select data-testid="customer-new-plan-planning-create-timezone" v-model="modalTimezone">
              <option value=""></option>
              <option value="Europe/Berlin">Europe/Berlin</option>
            </select>
            <input data-testid="customer-new-plan-planning-create-latitude" v-model="modalLatitude" />
            <input data-testid="customer-new-plan-planning-create-longitude" v-model="modalLongitude" />
            <label>
              <input
                data-testid="customer-new-plan-planning-create-watchbook-enabled"
                v-model="watchbookEnabled"
                type="checkbox"
              />
              watchbook
            </label>
            <textarea data-testid="customer-new-plan-planning-create-notes" v-model="modalNotes"></textarea>
            <input data-testid="customer-new-plan-planning-create-second-focus-field" />
            <button data-testid="customer-new-plan-planning-create-cancel" type="button" @click="modalOpen = false">
              cancel
            </button>
          </div>
        </div>
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

  it('preserves the mounted wizard content during same-customer session refresh churn', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const wrapper = mountComponent();
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-mark-dirty"]').trigger('click');

    customersApiMocks.getCustomerMock.mockResolvedValue(buildCustomer({ name: 'Alpha Security Reloaded' }));
    authStoreState.isSessionResolving = true;
    authStoreState.effectiveAccessToken = '';
    authStoreState.accessToken = '';
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-step-content-stub"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-customer-summary"]').exists()).toBe(true);

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    authStoreState.isSessionResolving = false;
    await flushPromises();

    expect(customersApiMocks.getCustomerMock).toHaveBeenLastCalledWith('tenant-1', 'customer-1', 'token-2');
    expect(wrapper.find('[data-testid="customer-new-plan-step-content-stub"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Alpha Security Reloaded');
  });

  it('keeps the planning create-new modal and typed values stable across focus-driven session refresh', async () => {
    routeState.query = { customer_id: 'customer-1' };
    const initialUrl = '/admin/customers/new-plan?customer_id=customer-1';
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Alpha Security');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');

    await wrapper.get('[data-testid="customer-new-plan-create-new-radio"]').setValue(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').setValue('TEST-SITE-FOCUS');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Focus Persistence Test Site');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').setValue('Europe/Berlin');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').setValue('50.950000');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').setValue('6.980000');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-watchbook-enabled"]').setValue(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-create-notes"]').setValue('Focus regression test');
    await flushPromises();

    customersApiMocks.getCustomerMock.mockResolvedValue(buildCustomer({ name: 'Alpha Security Refreshed' }));
    window.dispatchEvent(new Event('blur'));
    authStoreState.isSessionResolving = true;
    authStoreState.effectiveAccessToken = '';
    authStoreState.accessToken = '';
    document.dispatchEvent(new Event('visibilitychange'));
    window.dispatchEvent(new Event('focus'));
    await flushPromises();

    expect(routerPushMock).not.toHaveBeenCalled();
    expect(routerReplaceMock).not.toHaveBeenCalledWith(expect.objectContaining({ path: initialUrl }));
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
    expect(wrapper.find('[data-testid="customer-new-plan-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-modal"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').element as HTMLInputElement).value).toBe('TEST-SITE-FOCUS');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').element as HTMLInputElement).value).toBe('Focus Persistence Test Site');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').element as HTMLSelectElement).value).toBe('Europe/Berlin');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').element as HTMLInputElement).value).toBe('50.950000');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').element as HTMLInputElement).value).toBe('6.980000');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-watchbook-enabled"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-notes"]').element as HTMLTextAreaElement).value).toBe('Focus regression test');
    expect((wrapper.get('[data-testid="customer-new-plan-create-new-radio"]').element as HTMLInputElement).checked).toBe(true);

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    authStoreState.isSessionResolving = false;
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-second-focus-field"]').trigger('focus');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').setValue('Europe/Berlin');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-modal"]').exists()).toBe(true);
    expect(routerPushMock).not.toHaveBeenCalled();
    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Alpha Security Refreshed');

    await wrapper.get('[data-testid="customer-new-plan-planning-create-cancel"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-modal"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
  });
});
