// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, h, reactive } from 'vue';

const mockState = vi.hoisted(() => ({
  accessStoreState: null as any,
  legacyAuthStoreState: null as any,
  userStoreState: null as any,
  listTenantsMock: vi.fn(async () => []),
  listCustomersMock: vi.fn(async () => [
    {
      id: 'customer-1',
      legal_name: 'ACME Security',
      display_name: 'ACME',
      customer_number: 'C-1',
      status: 'active',
    },
  ]),
  listEmployeesMock: vi.fn(async () => []),
  listAdminNoticesMock: vi.fn(async () => []),
  listCustomerOrdersMock: vi.fn(async () => [
    {
      id: 'order-1',
      title: 'Order Alpha',
      order_no: 'ORD-1',
      release_state: 'draft',
      released_at: null,
      service_from: '2026-04-14',
      service_to: null,
    },
  ]),
  listShiftsMock: vi.fn(async () => []),
  listSubcontractorsMock: vi.fn(async () => []),
}));

const accessStoreState = reactive({
  accessToken: '',
});
const legacyAuthStoreState = reactive({
  effectiveAccessToken: '',
  effectiveRole: 'tenant_admin',
  tenantScopeId: '',
  sessionUser: null as null | { tenant_id?: string },
  refreshToken: 'refresh-1',
  syncFromPrimarySession: vi.fn(),
  ensureSessionReady: vi.fn(async () => true),
});
const userStoreState = reactive({
  userInfo: {
    roles: ['tenant_admin'],
  },
});

mockState.accessStoreState = accessStoreState;
mockState.legacyAuthStoreState = legacyAuthStoreState;
mockState.userStoreState = userStoreState;

const {
  listAdminNoticesMock,
  listCustomerOrdersMock,
  listCustomersMock,
  listEmployeesMock,
  listShiftsMock,
  listSubcontractorsMock,
  listTenantsMock,
} = mockState;

vi.mock('@vben/preferences', () => ({
  preferences: {
    app: {
      locale: 'en-US',
    },
  },
}));

vi.mock('@vben/stores', () => ({
  useAccessStore: () => mockState.accessStoreState,
  useUserStore: () => mockState.userStoreState,
}));

vi.mock('#/sicherplan-legacy/stores/auth', () => ({
  useAuthStore: () => mockState.legacyAuthStoreState,
}));

vi.mock('#/sicherplan-legacy/api/coreAdmin', () => ({
  listTenants: listTenantsMock,
}));

vi.mock('#/sicherplan-legacy/api/customers', () => ({
  listCustomers: listCustomersMock,
}));

vi.mock('#/sicherplan-legacy/api/employeeAdmin', () => ({
  listEmployees: listEmployeesMock,
}));

vi.mock('#/sicherplan-legacy/api/notices', () => ({
  listAdminNotices: listAdminNoticesMock,
}));

vi.mock('#/sicherplan-legacy/api/planningOrders', () => ({
  listCustomerOrders: listCustomerOrdersMock,
}));

vi.mock('#/sicherplan-legacy/api/planningShifts', () => ({
  listShifts: listShiftsMock,
}));

vi.mock('#/sicherplan-legacy/api/subcontractors', () => ({
  listSubcontractors: listSubcontractorsMock,
}));

vi.mock('#/locales', () => ({
  $t: (key: string) => key,
}));

vi.mock('@vben/icons', () => ({
  IconifyIcon: defineComponent({
    name: 'IconifyIconStub',
    setup() {
      return () => h('span', { class: 'iconify-stub' });
    },
  }),
}));

vi.mock('ant-design-vue', () => ({
  Button: defineComponent({
    name: 'AntButtonStub',
    props: { type: { type: String, default: 'default' }, block: { type: Boolean, default: false } },
    setup(_, { slots }) {
      return () => h('button', {}, slots.default?.());
    },
  }),
  Card: defineComponent({
    name: 'AntCardStub',
    setup(_, { slots }) {
      return () => h('section', { class: 'card-stub' }, slots.default?.());
    },
  }),
  Space: defineComponent({
    name: 'AntSpaceStub',
    setup(_, { slots }) {
      return () => h('div', { class: 'space-stub' }, slots.default?.());
    },
  }),
  Tag: defineComponent({
    name: 'AntTagStub',
    setup(_, { slots }) {
      return () => h('span', { class: 'tag-stub' }, slots.default?.());
    },
  }),
}));

vi.mock('#/components/sicherplan/empty-state.vue', () => ({
  default: defineComponent({
    name: 'EmptyStateStub',
    props: { title: { type: String, default: '' }, description: { type: String, default: '' } },
    setup(props) {
      return () => h('div', { class: 'empty-state-stub' }, `${props.title} ${props.description}`);
    },
  }),
}));

vi.mock('#/components/sicherplan/section-header.vue', () => ({
  default: defineComponent({
    name: 'SectionHeaderStub',
    props: { title: { type: String, default: '' }, description: { type: String, default: '' } },
    setup(props) {
      return () => h('header', { class: 'section-header-stub' }, [h('h2', props.title), h('p', props.description)]);
    },
  }),
}));

async function mountView() {
  const { default: DashboardView } = await import('./index.vue');
  return mount(DashboardView, {
    global: {
      stubs: {
        RouterLink: defineComponent({
          name: 'RouterLinkStub',
          props: { to: { type: String, required: true } },
          setup(_, { slots }) {
            return () => h('a', {}, slots.default?.());
          },
        }),
      },
    },
  });
}

describe('SicherPlan dashboard session loading', () => {
  let wrapper: null | VueWrapper<any> = null;

  beforeEach(() => {
    accessStoreState.accessToken = '';
    legacyAuthStoreState.effectiveAccessToken = '';
    legacyAuthStoreState.effectiveRole = 'tenant_admin';
    legacyAuthStoreState.tenantScopeId = '';
    legacyAuthStoreState.sessionUser = null;
    legacyAuthStoreState.refreshToken = 'refresh-1';
    legacyAuthStoreState.syncFromPrimarySession.mockClear();
    legacyAuthStoreState.ensureSessionReady.mockClear();
    legacyAuthStoreState.ensureSessionReady.mockResolvedValue(true);
    userStoreState.userInfo = { roles: ['tenant_admin'] };
    listTenantsMock.mockClear();
    listCustomersMock.mockClear();
    listEmployeesMock.mockClear();
    listAdminNoticesMock.mockClear();
    listCustomerOrdersMock.mockClear();
    listShiftsMock.mockClear();
    listSubcontractorsMock.mockClear();
  });

  afterEach(() => {
    wrapper?.unmount();
    wrapper = null;
  });

  it('loads once session state becomes available after mount', async () => {
    legacyAuthStoreState.ensureSessionReady.mockImplementationOnce(async () => {
      legacyAuthStoreState.effectiveAccessToken = 'token-1';
      legacyAuthStoreState.tenantScopeId = 'tenant-1';
      legacyAuthStoreState.sessionUser = { tenant_id: 'tenant-1' };
      return true;
    });

    wrapper = await mountView();
    await flushPromises();

    expect(legacyAuthStoreState.ensureSessionReady).toHaveBeenCalled();
    expect(listCustomersMock).toHaveBeenCalledTimes(1);
    expect(listCustomersMock).toHaveBeenCalledWith('tenant-1', 'token-1', {});
    expect(listCustomerOrdersMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('Order Alpha');
  });

  it('loads immediately on first mount when a persisted tenant session already exists', async () => {
    legacyAuthStoreState.effectiveAccessToken = 'token-1';
    legacyAuthStoreState.tenantScopeId = 'tenant-1';
    legacyAuthStoreState.sessionUser = { tenant_id: 'tenant-1' };

    wrapper = await mountView();
    await flushPromises();

    expect(listCustomersMock).toHaveBeenCalledTimes(1);
    expect(listEmployeesMock).toHaveBeenCalledTimes(1);
    expect(listSubcontractorsMock).toHaveBeenCalledTimes(1);
    expect(listCustomerOrdersMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('Order Alpha');
    expect(wrapper.text()).toContain('sicherplan.dashboardView.actions.title');
  });
});
