// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, h, reactive } from 'vue';

function createDeferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, reject, resolve };
}

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
  listStaffingCoverageMock: vi.fn(async () => [
    {
      shift_id: 'shift-1',
      planning_record_id: 'planning-1',
      shift_plan_id: 'plan-1',
      order_id: 'order-1',
      order_no: 'ORD-1',
      planning_record_name: 'Planning 1',
      planning_mode_code: 'site',
      workforce_scope_code: 'internal',
      starts_at: '2026-04-14T08:00:00Z',
      ends_at: '2026-04-14T16:00:00Z',
      shift_type_code: 'site_day',
      location_text: 'Berlin',
      meeting_point: 'Gate A',
      min_required_qty: 1,
      target_required_qty: 2,
      assigned_count: 1,
      confirmed_count: 1,
      released_partner_qty: 0,
      coverage_state: 'yellow',
      demand_groups: [
        {
          demand_group_id: 'dg-1',
          function_type_id: 'func-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 2,
          assigned_count: 1,
          confirmed_count: 1,
          released_partner_qty: 0,
          coverage_state: 'yellow',
        },
      ],
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
  listStaffingCoverageMock,
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

vi.mock('#/sicherplan-legacy/api/planningStaffing', () => ({
  listStaffingCoverage: listStaffingCoverageMock,
}));

vi.mock('#/sicherplan-legacy/features/planning/planningStaffing.helpers', () => ({
  coverageTone: (state: string) => {
    if (state === 'green') return 'good';
    if (state === 'yellow') return 'warn';
    return 'bad';
  },
  resolvePlanningStaffingCoverageState: (state: string, demandGroups: unknown[]) => {
    if (!Array.isArray(demandGroups) || demandGroups.length === 0) {
      return 'setup_required';
    }
    return state;
  },
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
          setup(props, { slots }) {
            return () =>
              h('a', { 'data-to': props.to }, slots.default?.());
          },
        }),
      },
    },
  });
}

function getButtonByText(wrapper: VueWrapper<any>, text: string) {
  const button = wrapper.findAll('button').find((candidate) => candidate.text() === text);
  if (!button) {
    throw new Error(`Button not found: ${text}`);
  }
  return button;
}

function formatExpectedLocalDateTime(value: string) {
  const date = new Date(value);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
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
    listStaffingCoverageMock.mockClear();
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
    expect(listStaffingCoverageMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('Order Alpha');
    expect(wrapper.text()).not.toContain('sicherplan.dashboardView.title');
    expect(wrapper.text()).not.toContain('sicherplan.dashboardView.actions.title');
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
    expect(listStaffingCoverageMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('Order Alpha');
    expect(wrapper.text()).toContain('sicherplan.dashboardView.todayCard.label');
    expect(wrapper.text()).not.toContain('sicherplan.dashboardView.title');
    expect(wrapper.text()).not.toContain('sicherplan.dashboardView.actions.title');
  });

  it('renders count pills before rich calendar items hydrate', async () => {
    legacyAuthStoreState.effectiveAccessToken = 'token-1';
    legacyAuthStoreState.tenantScopeId = 'tenant-1';
    legacyAuthStoreState.sessionUser = { tenant_id: 'tenant-1' };
    listShiftsMock.mockResolvedValueOnce([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: null,
        occurrence_date: '2026-04-14',
        starts_at: '2026-04-14T08:00:00Z',
        ends_at: '2026-04-14T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day_shift',
        location_text: null,
        meeting_point: null,
        release_state: 'released',
        customer_visible_flag: true,
        subcontractor_visible_flag: true,
        stealth_mode_flag: false,
        source_kind_code: 'manual',
        status: 'active',
        version_no: 1,
      },
    ] as any);
    const coverageDeferred = createDeferred<any[]>();
    listStaffingCoverageMock.mockImplementationOnce(() => coverageDeferred.promise);

    wrapper = await mountView();
    await flushPromises();

    expect(wrapper.findAll('.sp-dashboard__calendar-item')).toHaveLength(0);
    expect(wrapper.text()).toContain('1 sicherplan.dashboardView.calendar.shiftShort');
    expect(listStaffingCoverageMock).toHaveBeenCalledTimes(1);

    coverageDeferred.resolve([
      {
        shift_id: 'shift-1',
        planning_record_id: 'planning-1',
        shift_plan_id: 'plan-1',
        order_id: 'order-1',
        order_no: 'ORD-1',
        planning_record_name: 'Planning 1',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-04-14T08:00:00Z',
        ends_at: '2026-04-14T16:00:00Z',
        shift_type_code: 'day_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate A',
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 1,
        confirmed_count: 1,
        released_partner_qty: 0,
        coverage_state: 'yellow',
        demand_groups: [{ demand_group_id: 'dg-1' }],
      },
    ]);
    await flushPromises();

    expect(wrapper.findAll('.sp-dashboard__calendar-item')).toHaveLength(1);
  });

  it('deduplicates in-flight month coverage requests and reuses cached month data when revisiting', async () => {
    legacyAuthStoreState.effectiveAccessToken = 'token-1';
    legacyAuthStoreState.tenantScopeId = 'tenant-1';
    legacyAuthStoreState.sessionUser = { tenant_id: 'tenant-1' };
    const firstMonthDeferred = createDeferred<any[]>();
    const nextMonthDeferred = createDeferred<any[]>();
    listStaffingCoverageMock
      .mockImplementationOnce(() => firstMonthDeferred.promise)
      .mockImplementationOnce(() => nextMonthDeferred.promise);

    wrapper = await mountView();
    await flushPromises();

    expect(listStaffingCoverageMock).toHaveBeenCalledTimes(1);
    window.dispatchEvent(new Event('focus'));
    await flushPromises();
    expect(listStaffingCoverageMock).toHaveBeenCalledTimes(1);

    firstMonthDeferred.resolve([
      {
        shift_id: 'shift-1',
        planning_record_id: 'planning-1',
        shift_plan_id: 'plan-1',
        order_id: 'order-1',
        order_no: 'ORD-1',
        planning_record_name: 'Planning 1',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-04-14T08:00:00Z',
        ends_at: '2026-04-14T16:00:00Z',
        shift_type_code: 'day_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate A',
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 1,
        confirmed_count: 1,
        released_partner_qty: 0,
        coverage_state: 'yellow',
        demand_groups: [{ demand_group_id: 'dg-1' }],
      },
    ]);
    await flushPromises();

    await getButtonByText(wrapper, 'sicherplan.dashboardView.calendar.next').trigger('click');
    await flushPromises();
    expect(listStaffingCoverageMock).toHaveBeenCalledTimes(2);

    nextMonthDeferred.resolve([
      {
        shift_id: 'shift-2',
        planning_record_id: 'planning-2',
        shift_plan_id: 'plan-2',
        order_id: 'order-2',
        order_no: 'ORD-2',
        planning_record_name: 'Planning 2',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-05-14T08:00:00Z',
        ends_at: '2026-05-14T16:00:00Z',
        shift_type_code: 'night_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate B',
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 1,
        confirmed_count: 0,
        released_partner_qty: 0,
        coverage_state: 'yellow',
        demand_groups: [{ demand_group_id: 'dg-2' }],
      },
    ]);
    await flushPromises();

    await getButtonByText(wrapper, 'sicherplan.dashboardView.calendar.previous').trigger('click');
    await flushPromises();

    expect(listStaffingCoverageMock).toHaveBeenCalledTimes(2);
  });

  it('ignores stale month coverage responses when a newer month resolves later', async () => {
    legacyAuthStoreState.effectiveAccessToken = 'token-1';
    legacyAuthStoreState.tenantScopeId = 'tenant-1';
    legacyAuthStoreState.sessionUser = { tenant_id: 'tenant-1' };
    const firstMonthDeferred = createDeferred<any[]>();
    const nextMonthDeferred = createDeferred<any[]>();
    listStaffingCoverageMock
      .mockImplementationOnce(() => firstMonthDeferred.promise)
      .mockImplementationOnce(() => nextMonthDeferred.promise);

    wrapper = await mountView();
    await flushPromises();

    await getButtonByText(wrapper, 'sicherplan.dashboardView.calendar.next').trigger('click');
    await flushPromises();

    nextMonthDeferred.resolve([
      {
        shift_id: 'shift-2',
        planning_record_id: 'planning-2',
        shift_plan_id: 'plan-2',
        order_id: 'order-2',
        order_no: 'ORD-2',
        planning_record_name: 'Planning 2',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-05-14T17:00:00Z',
        ends_at: '2026-05-14T22:00:00Z',
        shift_type_code: 'night_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate B',
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 1,
        confirmed_count: 0,
        released_partner_qty: 0,
        coverage_state: 'yellow',
        demand_groups: [{ demand_group_id: 'dg-2' }],
      },
    ]);
    await flushPromises();
    expect(wrapper.text()).toContain('Night Shift');

    firstMonthDeferred.resolve([
      {
        shift_id: 'shift-1',
        planning_record_id: 'planning-1',
        shift_plan_id: 'plan-1',
        order_id: 'order-1',
        order_no: 'ORD-1',
        planning_record_name: 'Planning 1',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-04-14T08:00:00Z',
        ends_at: '2026-04-14T16:00:00Z',
        shift_type_code: 'day_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate A',
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 1,
        confirmed_count: 1,
        released_partner_qty: 0,
        coverage_state: 'green',
        demand_groups: [{ demand_group_id: 'dg-1' }],
      },
    ]);
    await flushPromises();

    expect(wrapper.text()).toContain('Night Shift');
    expect(wrapper.text()).not.toContain('Day Shift');
  });

  it('renders real staffing coverage items with coverage tones and expands remaining items on demand', async () => {
    legacyAuthStoreState.effectiveAccessToken = 'token-1';
    legacyAuthStoreState.tenantScopeId = 'tenant-1';
    legacyAuthStoreState.sessionUser = { tenant_id: 'tenant-1' };
    listCustomerOrdersMock.mockResolvedValueOnce([
      {
        id: 'order-1',
        tenant_id: 'tenant-1',
        customer_id: 'customer-1',
        requirement_type_id: 'req-1',
        patrol_route_id: null,
        order_no: 'ORD-1',
        title: 'Objekt Süd',
        service_category_code: 'object_security',
        service_from: '2026-04-14',
        service_to: '2026-04-14',
        release_state: 'draft',
        released_at: null,
        status: 'active',
        version_no: 1,
      },
    ] as any);
    listShiftsMock.mockResolvedValueOnce([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: null,
        occurrence_date: '2026-04-14',
        starts_at: '2026-04-14T08:00:00Z',
        ends_at: '2026-04-14T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day_shift',
        location_text: null,
        meeting_point: null,
        release_state: 'released',
        customer_visible_flag: true,
        subcontractor_visible_flag: true,
        stealth_mode_flag: false,
        source_kind_code: 'manual',
        status: 'active',
        version_no: 1,
      },
    ] as any);
    listStaffingCoverageMock.mockResolvedValueOnce([
      {
        shift_id: 'shift-1',
        planning_record_id: 'planning-1',
        shift_plan_id: 'plan-1',
        order_id: 'order-1',
        order_no: 'ORD-1',
        planning_record_name: 'Objekt Süd',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-04-14T08:00:00Z',
        ends_at: '2026-04-14T16:00:00Z',
        shift_type_code: 'day_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate A',
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 2,
        confirmed_count: 2,
        released_partner_qty: 0,
        coverage_state: 'green',
        demand_groups: [{ demand_group_id: 'dg-1' }],
      },
      {
        shift_id: 'shift-2',
        planning_record_id: 'planning-1',
        shift_plan_id: 'plan-2',
        order_id: 'order-1',
        order_no: 'ORD-1',
        planning_record_name: 'Messe Nord',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-04-14T17:00:00Z',
        ends_at: '2026-04-14T22:00:00Z',
        shift_type_code: 'night_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate B',
        min_required_qty: 1,
        target_required_qty: 2,
        assigned_count: 1,
        confirmed_count: 0,
        released_partner_qty: 0,
        coverage_state: 'yellow',
        demand_groups: [{ demand_group_id: 'dg-2' }],
      },
      {
        shift_id: 'shift-3',
        planning_record_id: 'planning-1',
        shift_plan_id: 'plan-3',
        order_id: 'order-1',
        order_no: 'ORD-1',
        planning_record_name: 'Patrol West',
        planning_mode_code: 'site',
        workforce_scope_code: 'internal',
        starts_at: '2026-04-14T20:00:00Z',
        ends_at: '2026-04-14T21:00:00Z',
        shift_type_code: 'patrol_shift',
        location_text: 'Berlin',
        meeting_point: 'Gate C',
        min_required_qty: 1,
        target_required_qty: 1,
        assigned_count: 0,
        confirmed_count: 0,
        released_partner_qty: 0,
        coverage_state: 'red',
        demand_groups: [],
      },
    ] as any);

    wrapper = await mountView();
    await flushPromises();

    const initialCalendarLinks = wrapper.findAll('.sp-dashboard__calendar-item');
    expect(initialCalendarLinks).toHaveLength(2);
    expect(initialCalendarLinks[0]?.text()).toContain('Day Shift');
    expect(initialCalendarLinks[0]?.attributes('class')).toContain('sp-dashboard__calendar-item--good');
    expect(initialCalendarLinks[0]?.attributes('data-to')).toContain('/admin/planning-staffing?');
    expect(initialCalendarLinks[0]?.attributes('data-to')).toContain('shift_id=shift-1');
    const firstItemQuery = new URLSearchParams(initialCalendarLinks[0]?.attributes('data-to')?.split('?')[1] ?? '');
    expect(firstItemQuery.get('date_from')).toBe(formatExpectedLocalDateTime('2026-04-14T08:00:00Z'));
    expect(firstItemQuery.get('date_to')).toBe(formatExpectedLocalDateTime('2026-04-15T16:00:00Z'));
    expect(initialCalendarLinks[0]?.attributes('aria-label')).toContain('sicherplan.dashboardView.calendar.coverageGood:');
    expect(initialCalendarLinks[0]?.find('.sp-dashboard__calendar-item-marker').exists()).toBe(true);
    expect(initialCalendarLinks[1]?.text()).toContain('Night Shift');
    expect(initialCalendarLinks[1]?.attributes('class')).toContain('sp-dashboard__calendar-item--warn');
    expect(initialCalendarLinks[1]?.attributes('data-to')).toContain('shift_id=shift-2');
    expect(initialCalendarLinks[1]?.attributes('aria-label')).toContain('sicherplan.dashboardView.calendar.coverageWarn:');

    const moreButton = wrapper.get('.sp-dashboard__calendar-more');
    expect(moreButton.text()).toContain('+1 sicherplan.dashboardView.calendar.more');

    await moreButton.trigger('click');

    const expandedCalendarLinks = wrapper.findAll('.sp-dashboard__calendar-item');
    expect(expandedCalendarLinks).toHaveLength(3);
    expect(expandedCalendarLinks[2]?.text()).toContain('Patrol Shift');
    expect(expandedCalendarLinks[2]?.attributes('class')).toContain('sp-dashboard__calendar-item--bad');
    expect(expandedCalendarLinks[2]?.attributes('aria-label')).toContain('sicherplan.dashboardView.calendar.coverageSetupRequired:');
    expect(expandedCalendarLinks[2]?.attributes('data-to')).toContain('shift_id=shift-3');
    const thirdItemQuery = new URLSearchParams(expandedCalendarLinks[2]?.attributes('data-to')?.split('?')[1] ?? '');
    expect(thirdItemQuery.get('date_to')).toBe(formatExpectedLocalDateTime('2026-04-15T21:00:00Z'));
  });
});
