// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, reactive } from 'vue';

import CustomerNewPlanWizardView from './new-plan.vue';
import CustomerNewPlanStepContent from './new-plan-step-content.vue';
import { buildOrderDetailsEditDraftStorageKey, buildWizardDraftStorageKey } from './new-plan-wizard-drafts';

const routeState = reactive({
  query: { customer_id: 'customer-1' } as Record<string, unknown>,
});
const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
const scrollIntoViewMock = vi.fn();
const focusMock = vi.fn();
const confirmMock = vi.fn();
const showFeedbackToastMock = vi.fn();
const intersectionObserverInstances: Array<{
  callback: IntersectionObserverCallback;
  disconnect: ReturnType<typeof vi.fn>;
  observe: ReturnType<typeof vi.fn>;
  unobserve: ReturnType<typeof vi.fn>;
}> = [];
const authStoreState = reactive({
  accessToken: 'token-1',
  effectiveAccessToken: 'token-1',
  effectiveRole: 'tenant_admin',
  effectiveTenantScopeId: 'tenant-1',
  ensureSessionReady: vi.fn().mockResolvedValue(undefined),
  isSessionResolving: false,
  syncFromPrimarySession: vi.fn(),
});

const stores = vi.hoisted(() => ({
  attachmentsByOrder: {} as Record<string, Array<{ current_version_no: number; id: string; relation_label?: string | null; source_label?: string | null; status: string; tenant_id: string; title: string }>>,
  equipmentItems: [
    { id: 'equipment-item-1', customer_id: 'customer-1', code: 'EQ-1', label: 'Funkgerät', tenant_id: 'tenant-1' },
    { id: 'equipment-item-2', customer_id: 'customer-1', code: 'EQ-2', label: 'Taschenlampe', tenant_id: 'tenant-1' },
  ],
  equipmentLinesByOrder: {} as Record<string, Array<{ id: string; equipment_item_id: string; required_qty: number; notes: string | null; order_id: string; tenant_id: string; status: string; version_no: number; archived_at: null }>>,
  eventVenues: [{ id: 'venue-1', customer_id: 'customer-1', venue_no: 'VEN-1', name: 'Arena', tenant_id: 'tenant-1' }],
  functionTypes: [{ id: 'function-1', code: 'SUP', label: 'Supervisor' }],
  orders: {} as Record<string, any>,
  patrolRoutes: [{ id: 'route-1', customer_id: 'customer-1', route_no: 'ROU-1', name: 'Innenstadt', tenant_id: 'tenant-1' }],
  orderPlanningScopesByOrder: {} as Record<string, Array<{ planning_entity_id: string; planning_entity_type: string }>>,
  qualificationTypes: [{ id: 'qualification-1', code: '34A', label: '34a' }],
  requirementLinesByOrder: {} as Record<string, Array<{ id: string; requirement_type_id: string; function_type_id: string | null; qualification_type_id: string | null; min_qty: number; target_qty: number; notes: string | null; order_id: string; tenant_id: string; status: string; version_no: number; archived_at: null }>>,
  requirementTypes: [{ id: 'requirement-type-1', customer_id: 'customer-1', code: 'REQ-1', label: 'Objektschutz', tenant_id: 'tenant-1' }],
  serviceCategories: [{ code: 'guarding', label: 'Bewachung' }],
  sites: [{ id: 'site-1', customer_id: 'customer-1', site_no: 'SITE-1', name: 'Werk Nord', tenant_id: 'tenant-1' }],
  tradeFairs: [{ id: 'fair-1', customer_id: 'customer-1', fair_no: 'FAIR-1', name: 'Expo', tenant_id: 'tenant-1' }],
}));

const apiMocks = vi.hoisted(() => ({
  createCustomerAvailableAddressMock: vi.fn(),
  createCustomerOrderMock: vi.fn(),
  createOrderAttachmentMock: vi.fn(),
  createOrderEquipmentLineMock: vi.fn(),
  createOrderRequirementLineMock: vi.fn(),
  createPlanningSetupRecordMock: vi.fn(),
  deleteOrderEquipmentLineMock: vi.fn(),
  deleteOrderRequirementLineMock: vi.fn(),
  getCustomerMock: vi.fn(),
  getCustomerOrderMock: vi.fn(),
  linkOrderAttachmentMock: vi.fn(),
  listCustomerOrdersMock: vi.fn(),
  listCustomerAddressesMock: vi.fn(),
  listDocumentsMock: vi.fn(),
  listEmployeeGroupsMock: vi.fn(),
  listFunctionTypesMock: vi.fn(),
  listOrderAttachmentsMock: vi.fn(),
  listOrderEquipmentLinesMock: vi.fn(),
  listOrderRequirementLinesMock: vi.fn(),
  listPlanningSetupRecordsMock: vi.fn(),
  listQualificationTypesMock: vi.fn(),
  listServiceCategoryOptionsMock: vi.fn(),
  updateCustomerOrderMock: vi.fn(),
  updateOrderEquipmentLineMock: vi.fn(),
  updateOrderRequirementLineMock: vi.fn(),
  unlinkOrderAttachmentMock: vi.fn(),
}));

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

vi.mock('#/sicherplan-legacy/composables/useSicherPlanFeedback', () => ({
  useSicherPlanFeedback: () => ({
    showFeedbackToast: showFeedbackToastMock,
  }),
}));

vi.mock('#/sicherplan-legacy/stores/auth', () => ({
  useAuthStore: () => authStoreState,
}));

vi.mock('#/sicherplan-legacy/api/customers', async () => {
  const actual = await vi.importActual<typeof import('#/sicherplan-legacy/api/customers')>('#/sicherplan-legacy/api/customers');
  return {
    ...actual,
    createCustomerAvailableAddress: apiMocks.createCustomerAvailableAddressMock,
    getCustomer: apiMocks.getCustomerMock,
    listCustomerAddresses: apiMocks.listCustomerAddressesMock,
  };
});

vi.mock('#/sicherplan-legacy/components/planning/PlanningLocationPickerModal.vue', () => ({
  default: defineComponent({
    name: 'PlanningLocationPickerModalStub',
    props: {
      loadErrorText: { type: String, default: '' },
      open: { type: Boolean, default: false },
    },
    emits: ['confirm', 'update:open'],
    template: `
      <div v-if="open" data-testid="customer-new-plan-location-picker-dialog">
        <div data-testid="customer-new-plan-location-picker-load-error">{{ loadErrorText }}</div>
        <button
          data-testid="customer-new-plan-location-picker-apply"
          type="button"
          @click="$emit('confirm', { latitude: '51.111111', longitude: '8.222222' }); $emit('update:open', false)"
        >
          apply
        </button>
        <button
          data-testid="customer-new-plan-location-picker-cancel"
          type="button"
          @click="$emit('update:open', false)"
        >
          cancel
        </button>
      </div>
    `,
  }),
}));

vi.mock('#/sicherplan-legacy/api/planningAdmin', () => ({
  createPlanningRecord: apiMocks.createPlanningSetupRecordMock,
  listPlanningRecords: apiMocks.listPlanningSetupRecordsMock,
  listTradeFairZones: vi.fn().mockResolvedValue([]),
}));

vi.mock('#/sicherplan-legacy/api/planningOrders', () => ({
  createCustomerOrder: apiMocks.createCustomerOrderMock,
  createOrderAttachment: apiMocks.createOrderAttachmentMock,
  createOrderEquipmentLine: apiMocks.createOrderEquipmentLineMock,
  createOrderRequirementLine: apiMocks.createOrderRequirementLineMock,
  deleteOrderEquipmentLine: apiMocks.deleteOrderEquipmentLineMock,
  deleteOrderRequirementLine: apiMocks.deleteOrderRequirementLineMock,
  getCustomerOrder: apiMocks.getCustomerOrderMock,
  linkOrderAttachment: apiMocks.linkOrderAttachmentMock,
  listDocuments: apiMocks.listDocumentsMock,
  listCustomerOrders: apiMocks.listCustomerOrdersMock,
  listOrderAttachments: apiMocks.listOrderAttachmentsMock,
  listOrderEquipmentLines: apiMocks.listOrderEquipmentLinesMock,
  listOrderRequirementLines: apiMocks.listOrderRequirementLinesMock,
  listServiceCategoryOptions: apiMocks.listServiceCategoryOptionsMock,
  updateCustomerOrder: apiMocks.updateCustomerOrderMock,
  updateOrderEquipmentLine: apiMocks.updateOrderEquipmentLineMock,
  updateOrderRequirementLine: apiMocks.updateOrderRequirementLineMock,
  unlinkOrderAttachment: apiMocks.unlinkOrderAttachmentMock,
}));

vi.mock('#/sicherplan-legacy/api/employeeAdmin', () => ({
  listEmployeeGroups: apiMocks.listEmployeeGroupsMock,
  listFunctionTypes: apiMocks.listFunctionTypesMock,
  listQualificationTypes: apiMocks.listQualificationTypesMock,
}));

vi.mock('ant-design-vue', () => ({
  Modal: defineComponent({
    name: 'ModalStub',
    props: {
      open: { type: Boolean, default: false },
      confirmLoading: { type: Boolean, default: false },
      title: { type: String, default: '' },
    },
    emits: ['cancel', 'ok', 'update:open'],
    template: `
      <div v-if="open" class="modal-stub">
        <header>{{ title }}</header>
        <slot />
        <button data-testid="modal-ok" type="button" @click="$emit('ok')">ok</button>
        <button data-testid="modal-cancel" type="button" @click="$emit('cancel'); $emit('update:open', false)">cancel</button>
      </div>
    `,
  }),
}));

const ModuleWorkspacePageStub = defineComponent({
  name: 'ModuleWorkspacePageStub',
  template: '<div><slot name="workspace" /></div>',
});

const SectionBlockStub = defineComponent({
  name: 'SectionBlockStub',
  template: '<section><slot /></section>',
});

const EmptyStateStub = defineComponent({
  name: 'EmptyStateStub',
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
  },
  template: '<div><strong>{{ title }}</strong><span>{{ description }}</span></div>',
});

const ForbiddenViewStub = defineComponent({
  name: 'ForbiddenViewStub',
  template: '<div>forbidden</div>',
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

function makeOrder(id: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 'tenant-1',
    customer_id: 'customer-1',
    requirement_type_id: 'requirement-type-1',
    patrol_route_id: null,
    order_no: 'ORD-1000',
    title: 'Werk Nord',
    service_category_code: 'guarding',
    service_from: '2026-06-01',
    service_to: '2026-06-10',
    release_state: 'draft',
    released_at: null,
    status: 'active',
    version_no: 1,
    security_concept_text: null,
    notes: null,
    released_by_user_id: null,
    attachments: [],
    created_at: '2026-04-01T08:00:00Z',
    updated_at: '2026-04-01T08:00:00Z',
    archived_at: null,
    ...overrides,
  };
}

function nextTickFlush() {
  return flushPromises();
}

function expectFeedback(tone: 'error' | 'neutral' | 'success', message: string) {
  expect(showFeedbackToastMock).toHaveBeenCalledWith(expect.objectContaining({ message, tone }));
}

function expectOrderScopeValidationFeedback(sectionKey: string, errorKey: string) {
  expectFeedback('error', `${sectionKey}: ${errorKey}`);
}

const mountedWrappers: VueWrapper[] = [];

function mountComponent() {
  const wrapper = mount(CustomerNewPlanWizardView, {
    global: {
      stubs: {
        EmptyState: EmptyStateStub,
        ForbiddenView: ForbiddenViewStub,
        ModuleWorkspacePage: ModuleWorkspacePageStub,
        SectionBlock: SectionBlockStub,
      },
    },
  });
  mountedWrappers.push(wrapper);
  return wrapper;
}

async function advanceToOrderDetails(wrapper: VueWrapper) {
  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
}

function getOrderStepContentState(wrapper: VueWrapper) {
  return wrapper.getComponent(CustomerNewPlanStepContent).vm as unknown as {
    editingExistingOrderId: string;
    existingOrderEditFormOpen: boolean;
    selectedExistingOrderId: string;
  };
}

async function ensureCreateNewOrderMode(wrapper: VueWrapper) {
  if (!wrapper.find('[data-testid="customer-new-plan-order-no"]').exists()) {
    await wrapper.get('[data-testid="customer-new-plan-order-mode-create"]').setValue(true);
    await nextTickFlush();
  }
}

async function advanceToEquipmentLines(wrapper: VueWrapper) {
  await advanceToOrderDetails(wrapper);
  await ensureCreateNewOrderMode(wrapper);
  await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-2000');
  await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Werkschutz Nord');
  await wrapper.get('[data-testid="customer-new-plan-order-requirement-type"]').setValue('requirement-type-1');
  await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
  await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
  await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
  await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
  await nextTickFlush();

  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
}

async function saveEquipmentLine(wrapper: VueWrapper, overrides?: { notes?: string; qty?: string | number }) {
  await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
  await wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').setValue(String(overrides?.qty ?? 2));
  await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue(overrides?.notes ?? 'Night radios');
  await wrapper.get('[data-testid="customer-new-plan-save-equipment-line"]').trigger('click');
  await nextTickFlush();
}

async function advanceToRequirementLines(wrapper: VueWrapper) {
  await advanceToEquipmentLines(wrapper);
  await saveEquipmentLine(wrapper);
  await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
  await nextTickFlush();
  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
}

async function advanceToOrderDocuments(wrapper: VueWrapper) {
  await advanceToRequirementLines(wrapper);
  await saveRequirementLine(wrapper);
  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
}

async function saveRequirementLine(
  wrapper: VueWrapper,
  overrides?: { minQty?: string | number; notes?: string; targetQty?: string | number },
) {
  await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
  await wrapper.get('[data-testid="customer-new-plan-requirement-function-type"]').setValue('function-1');
  await wrapper.get('[data-testid="customer-new-plan-requirement-qualification-type"]').setValue('qualification-1');
  await wrapper.get('[data-testid="customer-new-plan-requirement-min-qty"]').setValue(String(overrides?.minQty ?? 1));
  await wrapper.get('[data-testid="customer-new-plan-requirement-target-qty"]').setValue(String(overrides?.targetQty ?? 2));
  await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue(overrides?.notes ?? 'One supervisor');
  await wrapper.get('[data-testid="customer-new-plan-save-requirement-line"]').trigger('click');
  await nextTickFlush();
}

function mountExistingOrderScope(overrides: Partial<typeof routeState.query> = {}) {
  routeState.query = {
    customer_id: 'customer-1',
    order_id: 'order-1',
    step: 'order-scope-documents',
    ...overrides,
  };
  stores.orders['order-1'] = makeOrder('order-1');
  return mountComponent();
}

function orderDocumentRows(wrapper: VueWrapper) {
  return wrapper.findAll('[data-testid="customer-new-plan-order-document-list"] .sp-customer-plan-wizard-step__list-row');
}

function orderDocumentPrimaryTitle(wrapper: VueWrapper, index = 0) {
  return orderDocumentRows(wrapper)[index]!.get('strong').text();
}

describe('CustomerNewPlanWizardView EPIC 3', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.stubGlobal('confirm', confirmMock);
    confirmMock.mockReset();
    confirmMock.mockReturnValue(true);
    scrollIntoViewMock.mockReset();
    focusMock.mockReset();
    showFeedbackToastMock.mockReset();
    intersectionObserverInstances.length = 0;
    Object.defineProperty(window.Element.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoViewMock,
    });
    Object.defineProperty(window.HTMLElement.prototype, 'focus', {
      configurable: true,
      value: focusMock,
    });
    Object.defineProperty(window, 'IntersectionObserver', {
      configurable: true,
      value: class MockIntersectionObserver {
        callback: IntersectionObserverCallback;
        disconnect = vi.fn();
        observe = vi.fn();
        unobserve = vi.fn();

        constructor(callback: IntersectionObserverCallback) {
          this.callback = callback;
          intersectionObserverInstances.push(this);
        }
      },
    });
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      value: vi.fn().mockReturnValue({
        addEventListener: vi.fn(),
        matches: false,
        removeEventListener: vi.fn(),
      }),
    });
    routeState.query = { customer_id: 'customer-1' };
    routerPushMock.mockReset();
    routerReplaceMock.mockReset();
    authStoreState.accessToken = 'token-1';
    authStoreState.effectiveAccessToken = 'token-1';
    authStoreState.effectiveRole = 'tenant_admin';
    authStoreState.effectiveTenantScopeId = 'tenant-1';
    authStoreState.isSessionResolving = false;
    authStoreState.syncFromPrimarySession.mockReset();
    authStoreState.ensureSessionReady.mockReset();
    authStoreState.ensureSessionReady.mockResolvedValue(undefined);

    stores.orders = {};
    stores.orderPlanningScopesByOrder = {};
    stores.equipmentLinesByOrder = {};
    stores.requirementLinesByOrder = {};
    stores.attachmentsByOrder = {};
    stores.sites = [{ id: 'site-1', customer_id: 'customer-1', site_no: 'SITE-1', name: 'Werk Nord', tenant_id: 'tenant-1' }];
    stores.eventVenues = [{ id: 'venue-1', customer_id: 'customer-1', venue_no: 'VEN-1', name: 'Arena', tenant_id: 'tenant-1' }];
    stores.tradeFairs = [{ id: 'fair-1', customer_id: 'customer-1', fair_no: 'FAIR-1', name: 'Expo', tenant_id: 'tenant-1' }];
    stores.patrolRoutes = [{ id: 'route-1', customer_id: 'customer-1', route_no: 'ROU-1', name: 'Innenstadt', tenant_id: 'tenant-1' }];
    stores.requirementTypes = [{ id: 'requirement-type-1', customer_id: 'customer-1', code: 'REQ-1', label: 'Objektschutz', tenant_id: 'tenant-1' }];
    stores.serviceCategories = [{ code: 'guarding', label: 'Bewachung' }];
    stores.equipmentItems = [
      { id: 'equipment-item-1', customer_id: 'customer-1', code: 'EQ-1', label: 'Funkgerät', tenant_id: 'tenant-1' },
      { id: 'equipment-item-2', customer_id: 'customer-1', code: 'EQ-2', label: 'Taschenlampe', tenant_id: 'tenant-1' },
    ];

    apiMocks.getCustomerMock.mockReset();
    apiMocks.getCustomerMock.mockResolvedValue(buildCustomer());
    apiMocks.createCustomerAvailableAddressMock.mockReset();
    apiMocks.createCustomerAvailableAddressMock.mockImplementation((_tenantId: string, _customerId: string, _token: string, payload: any) =>
      Promise.resolve({
        id: 'available-address-1',
        city: payload.city,
        country_code: payload.country_code,
        postal_code: payload.postal_code,
        state: payload.state ?? null,
        street_line_1: payload.street_line_1,
        street_line_2: payload.street_line_2 ?? null,
      }),
    );
    apiMocks.listCustomerAddressesMock.mockReset();
    apiMocks.listCustomerAddressesMock.mockResolvedValue([
      {
        id: 'customer-address-link-1',
        tenant_id: 'tenant-1',
        customer_id: 'customer-1',
        address_id: 'address-1',
        address_type: 'service',
        label: null,
        is_default: true,
        status: 'active',
        version_no: 1,
        archived_at: null,
        address: {
          id: 'address-1',
          street_line_1: 'Werkstraße 1',
          street_line_2: null,
          postal_code: '10115',
          city: 'Berlin',
          state: null,
          country_code: 'DE',
        },
      },
    ]);

    apiMocks.listPlanningSetupRecordsMock.mockReset();
    apiMocks.listPlanningSetupRecordsMock.mockImplementation((entityKey: string) => {
      const map: Record<string, unknown[]> = {
        equipment_item: stores.equipmentItems,
        event_venue: stores.eventVenues,
        patrol_route: stores.patrolRoutes,
        requirement_type: stores.requirementTypes,
        site: stores.sites,
        trade_fair: stores.tradeFairs,
      };
      return Promise.resolve(map[entityKey] ?? []);
    });

    apiMocks.createPlanningSetupRecordMock.mockReset();
    apiMocks.createPlanningSetupRecordMock.mockImplementation((entityKey: string, _tenantId: string, _token: string, payload: any) => {
      const created = { id: `${entityKey}-new-1`, tenant_id: 'tenant-1', ...payload };
      if (entityKey === 'equipment_item') stores.equipmentItems.push(created);
      if (entityKey === 'requirement_type') stores.requirementTypes.push(created);
      if (entityKey === 'event_venue') stores.eventVenues.push(created);
      if (entityKey === 'site') stores.sites.push(created);
      if (entityKey === 'trade_fair') stores.tradeFairs.push(created);
      if (entityKey === 'patrol_route') stores.patrolRoutes.push(created);
      return Promise.resolve(created);
    });

    apiMocks.listServiceCategoryOptionsMock.mockReset();
    apiMocks.listServiceCategoryOptionsMock.mockImplementation(() => Promise.resolve(stores.serviceCategories));
    apiMocks.listEmployeeGroupsMock.mockReset();
    apiMocks.listEmployeeGroupsMock.mockResolvedValue([]);
    apiMocks.listFunctionTypesMock.mockReset();
    apiMocks.listFunctionTypesMock.mockResolvedValue(stores.functionTypes);
    apiMocks.listQualificationTypesMock.mockReset();
    apiMocks.listQualificationTypesMock.mockResolvedValue(stores.qualificationTypes);

    apiMocks.createCustomerOrderMock.mockReset();
    apiMocks.createCustomerOrderMock.mockImplementation((_tenantId: string, _token: string, payload: any) => {
      const created = makeOrder('order-1', payload);
      stores.orders[created.id] = created;
      return Promise.resolve(created);
    });
    apiMocks.updateCustomerOrderMock.mockReset();
    apiMocks.updateCustomerOrderMock.mockImplementation((_tenantId: string, orderId: string, _token: string, payload: any) => {
      const updated = makeOrder(orderId, { ...stores.orders[orderId], ...payload, version_no: (stores.orders[orderId]?.version_no ?? 1) + 1 });
      stores.orders[orderId] = updated;
      return Promise.resolve(updated);
    });
    apiMocks.getCustomerOrderMock.mockReset();
    apiMocks.getCustomerOrderMock.mockImplementation((_tenantId: string, orderId: string) => Promise.resolve(stores.orders[orderId]));
    apiMocks.listCustomerOrdersMock.mockReset();
    apiMocks.listCustomerOrdersMock.mockImplementation((_tenantId: string, _token: string, filters: Record<string, unknown>) =>
      Promise.resolve(
        Object.values(stores.orders).filter(
          (row: any) =>
            (!filters?.customer_id || row.customer_id === filters.customer_id)
            && (
              !filters?.planning_entity_type
              || !filters?.planning_entity_id
              || (stores.orderPlanningScopesByOrder[row.id] ?? []).some(
                (scope) =>
                  scope.planning_entity_type === filters.planning_entity_type
                  && scope.planning_entity_id === filters.planning_entity_id,
              )
            ),
        ),
      ),
    );

    apiMocks.listOrderEquipmentLinesMock.mockReset();
    apiMocks.listOrderEquipmentLinesMock.mockImplementation((_tenantId: string, orderId: string) => Promise.resolve(stores.equipmentLinesByOrder[orderId] ?? []));
    apiMocks.createOrderEquipmentLineMock.mockReset();
    apiMocks.createOrderEquipmentLineMock.mockImplementation((_tenantId: string, orderId: string, _token: string, payload: any) => {
      const row = { id: `equipment-line-${(stores.equipmentLinesByOrder[orderId] ?? []).length + 1}`, archived_at: null, status: 'active', tenant_id: 'tenant-1', version_no: 1, ...payload };
      stores.equipmentLinesByOrder[orderId] = [...(stores.equipmentLinesByOrder[orderId] ?? []), row];
      return Promise.resolve(row);
    });
    apiMocks.updateOrderEquipmentLineMock.mockReset();
    apiMocks.updateOrderEquipmentLineMock.mockImplementation((_tenantId: string, orderId: string, rowId: string, _token: string, payload: any) => {
      stores.equipmentLinesByOrder[orderId] = (stores.equipmentLinesByOrder[orderId] ?? []).map((row) => row.id === rowId ? { ...row, ...payload, version_no: row.version_no + 1 } : row);
      return Promise.resolve(stores.equipmentLinesByOrder[orderId].find((row) => row.id === rowId));
    });
    apiMocks.deleteOrderEquipmentLineMock.mockReset();
    apiMocks.deleteOrderEquipmentLineMock.mockImplementation((_tenantId: string, orderId: string, rowId: string) => {
      stores.equipmentLinesByOrder[orderId] = (stores.equipmentLinesByOrder[orderId] ?? []).filter((row) => row.id !== rowId);
      return Promise.resolve();
    });

    apiMocks.listOrderRequirementLinesMock.mockReset();
    apiMocks.listOrderRequirementLinesMock.mockImplementation((_tenantId: string, orderId: string) => Promise.resolve(stores.requirementLinesByOrder[orderId] ?? []));
    apiMocks.createOrderRequirementLineMock.mockReset();
    apiMocks.createOrderRequirementLineMock.mockImplementation((_tenantId: string, orderId: string, _token: string, payload: any) => {
      const row = { id: `requirement-line-${(stores.requirementLinesByOrder[orderId] ?? []).length + 1}`, archived_at: null, status: 'active', tenant_id: 'tenant-1', version_no: 1, ...payload };
      stores.requirementLinesByOrder[orderId] = [...(stores.requirementLinesByOrder[orderId] ?? []), row];
      return Promise.resolve(row);
    });
    apiMocks.updateOrderRequirementLineMock.mockReset();
    apiMocks.updateOrderRequirementLineMock.mockImplementation((_tenantId: string, orderId: string, rowId: string, _token: string, payload: any) => {
      stores.requirementLinesByOrder[orderId] = (stores.requirementLinesByOrder[orderId] ?? []).map((row) => row.id === rowId ? { ...row, ...payload, version_no: row.version_no + 1 } : row);
      return Promise.resolve(stores.requirementLinesByOrder[orderId].find((row) => row.id === rowId));
    });
    apiMocks.deleteOrderRequirementLineMock.mockReset();
    apiMocks.deleteOrderRequirementLineMock.mockImplementation((_tenantId: string, orderId: string, rowId: string) => {
      stores.requirementLinesByOrder[orderId] = (stores.requirementLinesByOrder[orderId] ?? []).filter((row) => row.id !== rowId);
      return Promise.resolve();
    });

    apiMocks.listOrderAttachmentsMock.mockReset();
    apiMocks.listOrderAttachmentsMock.mockImplementation((_tenantId: string, orderId: string) => Promise.resolve(stores.attachmentsByOrder[orderId] ?? []));
    apiMocks.listDocumentsMock.mockReset();
    apiMocks.listDocumentsMock.mockResolvedValue([
      { id: 'document-42', current_version_no: 2, status: 'active', tenant_id: 'tenant-1', title: 'Sicherheitskonzept' },
    ]);
    apiMocks.linkOrderAttachmentMock.mockReset();
    apiMocks.linkOrderAttachmentMock.mockImplementation((_tenantId: string, orderId: string, _token: string, payload: any) => {
      const doc = {
        id: payload.document_id,
        current_version_no: 1,
        relation_label: payload.label || null,
        status: 'active',
        tenant_id: 'tenant-1',
        title: '1663202370369.jpg',
      };
      stores.attachmentsByOrder[orderId] = [...(stores.attachmentsByOrder[orderId] ?? []), doc];
      return Promise.resolve(doc);
    });
    apiMocks.createOrderAttachmentMock.mockReset();
    apiMocks.createOrderAttachmentMock.mockImplementation((_tenantId: string, orderId: string, _token: string, payload: any) => {
      const doc = { id: 'uploaded-doc-1', current_version_no: 1, status: 'active', tenant_id: 'tenant-1', title: payload.title };
      stores.attachmentsByOrder[orderId] = [...(stores.attachmentsByOrder[orderId] ?? []), doc];
      return Promise.resolve(doc);
    });
    apiMocks.unlinkOrderAttachmentMock.mockReset();
    apiMocks.unlinkOrderAttachmentMock.mockImplementation((_tenantId: string, orderId: string, documentId: string) => {
      stores.attachmentsByOrder[orderId] = (stores.attachmentsByOrder[orderId] ?? []).filter((doc) => doc.id !== documentId);
      return Promise.resolve();
    });
  });

  afterEach(() => {
    while (mountedWrappers.length) {
      mountedWrappers.pop()?.unmount();
    }
    window.sessionStorage.clear();
  });

  it('runs through steps 1-5, persists canonical records, and reuses the previously created order without creating duplicates', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    await advanceToEquipmentLines(wrapper);
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createCustomerOrderMock.mock.calls[0]?.[2]).toMatchObject({ customer_id: 'customer-1', order_no: 'ORD-2000' });
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');

    await wrapper.get('[data-testid="customer-new-plan-previous"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.updateCustomerOrderMock).toHaveBeenCalledTimes(0);

    await wrapper.get('[data-testid="customer-new-plan-new-equipment"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-new-equipment-code"]').setValue('EQ-2');
    await wrapper.get('[data-testid="customer-new-plan-new-equipment-label"]').setValue('Ersatzfunkgerät');
    await wrapper.get('[data-testid="customer-new-plan-new-equipment-unit"]').setValue('piece');
    await wrapper.get('[data-testid="modal-ok"]').trigger('click');
    await nextTickFlush();
    await saveEquipmentLine(wrapper);
    await nextTickFlush();
    expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenCalledWith('equipment_item', 'tenant-1', 'token-1', expect.any(Object));
    expect(apiMocks.createPlanningSetupRecordMock.mock.calls.find((call) => call[0] === 'equipment_item')?.[3]).not.toHaveProperty('customer_id');
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');

    await wrapper.get('[data-testid="customer-new-plan-new-requirement"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-new-requirement-code"]').setValue('REQ-2');
    await wrapper.get('[data-testid="customer-new-plan-new-requirement-label"]').setValue('Werkschutz');
    await wrapper.get('[data-testid="modal-ok"]').trigger('click');
    await nextTickFlush();
    await saveRequirementLine(wrapper);
    await nextTickFlush();
    expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenCalledWith('requirement_type', 'tenant-1', 'token-1', expect.any(Object));
    expect(apiMocks.createPlanningSetupRecordMock.mock.calls.find((call) => call[0] === 'requirement_type')?.[3]).not.toHaveProperty('customer_id');
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');

    await wrapper.get('[data-testid="customer-new-plan-order-document-picker-open"]').trigger('click');
    await nextTickFlush();
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-order-document-result-row"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-link-order-document"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('loads Order workspace service-category choices from the shared service-category options endpoint', async () => {
    stores.serviceCategories = [
      { code: 'tenant_object', label: 'Tenant Objektschutz' },
      { code: 'tenant_event', label: 'Tenant Veranstaltungsschutz' },
    ];

    const wrapper = mountComponent();
    await nextTickFlush();
    await ensureCreateNewOrderMode(wrapper);

    const serviceCategorySelect = wrapper.get('[data-testid="customer-new-plan-order-service-category"]').element as HTMLSelectElement;
    expect(apiMocks.listServiceCategoryOptionsMock).toHaveBeenCalledWith('tenant-1', 'token-1');
    expect(Array.from(serviceCategorySelect.options).map((option) => option.value)).toContain('tenant_object');
    expect(Array.from(serviceCategorySelect.options).map((option) => option.textContent)).toContain('Tenant Objektschutz');
  });

  it('shows sticky order-scope section navigation only in the scope documents step and scrolls to sections', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.find('[data-testid="customer-order-scope-nav"]').exists()).toBe(false);

    await advanceToOrderDocuments(wrapper);

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(wrapper.find('[data-testid="customer-order-scope-onepage"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-order-scope-nav"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-order-scope-nav-link-equipment"]').text()).toContain('sicherplan.customerPlansWizard.orderScope.equipmentTitle');
    expect(wrapper.get('[data-testid="customer-order-scope-nav-link-requirements"]').text()).toContain('sicherplan.customerPlansWizard.orderScope.requirementsTitle');
    expect(wrapper.get('[data-testid="customer-order-scope-nav-link-documents"]').text()).toContain('sicherplan.customerPlansWizard.orderScope.documentsTitle');
    expect(wrapper.find('#customer-order-scope-section-equipment').exists()).toBe(true);
    expect(wrapper.find('#customer-order-scope-section-requirements').exists()).toBe(true);
    expect(wrapper.find('#customer-order-scope-section-documents').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-item"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-save-equipment-line"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-type"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-save-requirement-line"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-picker-open"]').exists()).toBe(true);

    const requirementsSection = wrapper.get('#customer-order-scope-section-requirements').element;
    await wrapper.get('[data-testid="customer-order-scope-nav-link-requirements"]').trigger('click');
    await nextTickFlush();

    expect(scrollIntoViewMock).toHaveBeenLastCalledWith({ behavior: 'smooth', block: 'start' });
    expect(scrollIntoViewMock.mock.contexts.at(-1)).toBe(requirementsSection);

    const documentsSection = wrapper.get('#customer-order-scope-section-documents').element;
    await wrapper.get('[data-testid="customer-order-scope-nav-link-documents"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-order-scope-nav-link-documents"]').classes()).toContain('sp-customer-order-scope-nav__link--active');
    expect(scrollIntoViewMock).toHaveBeenLastCalledWith({ behavior: 'smooth', block: 'start' });
    expect(scrollIntoViewMock.mock.contexts.at(-1)).toBe(documentsSection);
  });

  it('updates the order-scope active nav link from IntersectionObserver scroll-spy events', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);

    const observer = intersectionObserverInstances.at(-1);
    expect(observer).toBeTruthy();

    const equipmentSection = wrapper.get('#customer-order-scope-section-equipment').element;
    const requirementsSection = wrapper.get('#customer-order-scope-section-requirements').element;
    const documentsSection = wrapper.get('#customer-order-scope-section-documents').element;
    const sectionTops = { documents: 640, equipment: 129, requirements: 420 };
    const mockRect = (top: number) => ({ bottom: top + 320, height: 320, left: 0, right: 0, top, width: 800, x: 0, y: top, toJSON: () => ({}) });
    vi.spyOn(equipmentSection, 'getBoundingClientRect').mockImplementation(() => mockRect(sectionTops.equipment) as DOMRect);
    vi.spyOn(requirementsSection, 'getBoundingClientRect').mockImplementation(() => mockRect(sectionTops.requirements) as DOMRect);
    vi.spyOn(documentsSection, 'getBoundingClientRect').mockImplementation(() => mockRect(sectionTops.documents) as DOMRect);

    observer?.callback(
      [{ isIntersecting: true, intersectionRatio: 0.8, boundingClientRect: { top: 0 }, target: equipmentSection } as IntersectionObserverEntry],
      observer as unknown as IntersectionObserver,
    );
    await nextTickFlush();
    sectionTops.equipment = -260;
    sectionTops.requirements = 129;
    sectionTops.documents = 420;
    observer?.callback(
      [{ isIntersecting: true, intersectionRatio: 0.85, boundingClientRect: { top: 0 }, target: requirementsSection } as IntersectionObserverEntry],
      observer as unknown as IntersectionObserver,
    );
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-order-scope-nav-link-requirements"]').classes()).toContain('sp-customer-order-scope-nav__link--active');

  });

  it('allows skipping Order Documents when the draft is empty and no existing attachments exist', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('allows skipping Order Documents when existing attachments already exist', async () => {
    stores.attachmentsByOrder['order-1'] = [
      { id: 'doc-1', current_version_no: 1, status: 'active', tenant_id: 'tenant-1', title: 'Bestandsdokument' },
    ];
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('displays linked order documents with a custom relation label as the primary title', async () => {
    stores.attachmentsByOrder['order-1'] = [
      {
        id: 'document-badge-photo',
        current_version_no: 1,
        relation_label: 'Employee badge photo',
        status: 'active',
        tenant_id: 'tenant-1',
        title: '1663202370369.jpg',
      },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    expect(orderDocumentPrimaryTitle(wrapper)).toBe('Employee badge photo');
    expect(orderDocumentPrimaryTitle(wrapper)).not.toBe('1663202370369.jpg');
  });

  it('falls back to the document title when a linked order document has no custom relation label', async () => {
    stores.attachmentsByOrder['order-1'] = [
      {
        id: 'document-badge-title',
        current_version_no: 1,
        relation_label: null,
        status: 'active',
        tenant_id: 'tenant-1',
        title: 'WB-P2002-badge',
      },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    expect(orderDocumentPrimaryTitle(wrapper)).toBe('WB-P2002-badge');
  });

  it('attaches uploaded order documents inline, stays on the step, and allows continuing afterward', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    const uploadFile = new File(['order document'], 'konzept.pdf', { type: 'application/pdf' });
    const uploadInput = wrapper.get('[data-testid="customer-new-plan-order-document-file"]');
    Object.defineProperty(uploadInput.element, 'files', {
      configurable: true,
      value: [uploadFile],
    });
    await uploadInput.trigger('change');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-order-document-upload-title"]').setValue('Sicherheitskonzept');

    await wrapper.get('[data-testid="customer-new-plan-attach-order-document"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(stores.attachmentsByOrder['order-1']).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-list"]').text()).toContain('Sicherheitskonzept');
    expect(orderDocumentPrimaryTitle(wrapper)).toBe('Sicherheitskonzept');
    expect((wrapper.get('[data-testid="customer-new-plan-order-document-upload-title"]').element as HTMLInputElement).value).toBe('');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('links existing order documents inline, stays on the step, and allows continuing afterward', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-document-picker-open"]').trigger('click');
    await nextTickFlush();
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-picker-modal"]').exists()).toBe(true);
    expect(wrapper.find('.sp-customer-plan-wizard-step__document-picker-modal').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-order-document-search"]').setValue('Sicherheitskonzept');
    await wrapper.get('[data-testid="customer-new-plan-order-document-search"]').trigger('keyup.enter');
    await flushPromises();
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-result-row"]').text()).toContain('Sicherheitskonzept');
    await wrapper.get('[data-testid="customer-new-plan-order-document-result-row"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-picker-modal"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-selected"]').text()).toContain('Sicherheitskonzept');
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-selected"]').text()).toContain('Sicherheitskonzept');
    await wrapper.get('[data-testid="customer-new-plan-order-document-link-label"]').setValue('Bestehendes Dokument');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-link-order-document"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledWith(
      'tenant-1',
      'order-1',
      'token-1',
      expect.objectContaining({ document_id: 'document-42', label: 'Bestehendes Dokument' }),
    );
    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(stores.attachmentsByOrder['order-1']).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-list"]').text()).toContain('Bestehendes Dokument');
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-list"]').text()).not.toContain('1663202370369.jpg');

    await wrapper.get('[data-testid="customer-new-plan-unlink-order-document"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.unlinkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(stores.attachmentsByOrder['order-1']).toHaveLength(0);
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.orderDocumentUnlinked');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(stores.attachmentsByOrder['order-1']).toHaveLength(0);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('keeps linked document title and relation label as separate UI assumptions', async () => {
    stores.attachmentsByOrder['order-1'] = [
      {
        id: 'document-title-and-label',
        current_version_no: 3,
        relation_label: 'Employee badge photo',
        source_label: 'source file: 1663202370369.jpg',
        status: 'active',
        tenant_id: 'tenant-1',
        title: '1663202370369.jpg',
      },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    const row = orderDocumentRows(wrapper)[0]!;
    expect(row.get('strong').text()).toBe('Employee badge photo');
    expect(row.text()).toContain('source file: 1663202370369.jpg');
    expect(row.text()).toContain('v3');
    expect(row.text()).toContain('active');
  });

  it('blocks partial order-document drafts until cleared, then allows skipping', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-document-upload-title"]').setValue('Unvollstandiger Entwurf');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expectOrderScopeValidationFeedback(
      'sicherplan.customerPlansWizard.orderScope.documentsTitle',
      'sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-order-scope-documents-card"]').classes()).toContain(
      'sp-customer-plan-wizard-step__scope-card--invalid',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-order-scope-documents-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.orderScope.documentsTitle: sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-file-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.documentFileRequired',
    );
    expect(scrollIntoViewMock).toHaveBeenLastCalledWith({ behavior: 'smooth', block: 'start' });
    expect(scrollIntoViewMock.mock.contexts.at(-1)).toBe(wrapper.get('#customer-order-scope-section-documents').element);
    expect((focusMock.mock.contexts.at(-1) as HTMLElement | undefined)?.getAttribute('data-testid')).toBe(
      'customer-new-plan-order-document-file',
    );
    expect(wrapper.find('[data-testid="customer-new-plan-clear-order-document-draft"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-clear-order-document-draft"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('blocks incomplete upload attach attempts and allows continuing after clearing the draft', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-document-upload-title"]').setValue('Nur Titel');

    await wrapper.get('[data-testid="customer-new-plan-attach-order-document"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expectFeedback('error', 'sicherplan.customerPlansWizard.errors.orderDocumentUploadIncomplete');

    await wrapper.get('[data-testid="customer-new-plan-clear-order-document-draft"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('blocks incomplete link drafts until cleared, then allows continuing', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-document-link-label"]').setValue('Nur Label');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expectOrderScopeValidationFeedback(
      'sicherplan.customerPlansWizard.orderScope.documentsTitle',
      'sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-selection-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.existingDocumentSelectionRequired',
    );
    expect((focusMock.mock.contexts.at(-1) as HTMLElement | undefined)?.getAttribute('data-testid')).toBe(
      'customer-new-plan-order-document-picker-open',
    );

    await wrapper.get('[data-testid="customer-new-plan-clear-order-document-draft"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('marks all blocking order-scope sections and keeps scrolling to the first unresolved one', async () => {
    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
    await wrapper.get('[data-testid="customer-new-plan-order-document-upload-title"]').setValue('Needs file');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-order-scope-equipment-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.orderScope.equipmentTitle: sicherplan.customerPlansWizard.errors.saveCurrentEquipmentLineBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-order-scope-requirements-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.orderScope.requirementsTitle: sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-order-scope-documents-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.orderScope.documentsTitle: sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue',
    );
    expect(scrollIntoViewMock.mock.contexts.at(-1)).toBe(wrapper.get('#customer-order-scope-section-equipment').element);

    await wrapper.get('[data-testid="customer-new-plan-save-equipment-line"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(scrollIntoViewMock.mock.contexts.at(-1)).toBe(wrapper.get('#customer-order-scope-section-requirements').element);
    expect((focusMock.mock.contexts.at(-1) as HTMLElement | undefined)?.getAttribute('data-testid')).toBe(
      'customer-new-plan-requirement-type',
    );
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-equipment-error"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-documents-error"]').exists()).toBe(true);
  });

  it('removes existing equipment rows, refreshes the list, and clears the selected edit draft', async () => {
    stores.equipmentLinesByOrder['order-1'] = [
      {
        id: 'equipment-line-existing-1',
        archived_at: null,
        equipment_item_id: 'equipment-item-1',
        notes: 'Selected row',
        order_id: 'order-1',
        required_qty: 2,
        status: 'active',
        tenant_id: 'tenant-1',
        version_no: 1,
      },
      {
        id: 'equipment-line-existing-2',
        archived_at: null,
        equipment_item_id: 'equipment-item-2',
        notes: 'Other row',
        order_id: 'order-1',
        required_qty: 1,
        status: 'active',
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    const removeActions = wrapper.findAll('[data-testid="customer-new-plan-delete-equipment-line"]');
    expect(removeActions).toHaveLength(2);

    await wrapper.findAll('[data-testid="customer-new-plan-equipment-line-select"]')[0]!.trigger('click');
    await nextTickFlush();
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').element as HTMLTextAreaElement).value).toBe('Selected row');

    await removeActions[0]!.trigger('click');
    await nextTickFlush();

    expect(confirmMock).toHaveBeenCalledWith('sicherplan.customerPlansWizard.confirmRemoveEquipmentLine');
    expect(apiMocks.deleteOrderEquipmentLineMock).toHaveBeenCalledWith(
      'tenant-1',
      'order-1',
      'equipment-line-existing-1',
      'token-1',
    );
    expect(apiMocks.listOrderEquipmentLinesMock).toHaveBeenCalledWith('tenant-1', 'order-1', 'token-1');
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-line-select"]').text()).toContain('Taschenlampe');
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-line-select"]').text()).not.toContain('Funkgerät');
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-item"]').element as HTMLSelectElement).value).toBe('');
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').element as HTMLTextAreaElement).value).toBe('');
  });

  it('removes existing requirement rows, refreshes the list, and clears the selected edit draft', async () => {
    stores.requirementLinesByOrder['order-1'] = [
      {
        id: 'requirement-line-existing-1',
        archived_at: null,
        function_type_id: 'function-1',
        min_qty: 1,
        notes: 'Selected requirement',
        order_id: 'order-1',
        qualification_type_id: 'qualification-1',
        requirement_type_id: 'requirement-type-1',
        status: 'active',
        target_qty: 2,
        tenant_id: 'tenant-1',
        version_no: 1,
      },
      {
        id: 'requirement-line-existing-2',
        archived_at: null,
        function_type_id: null,
        min_qty: 0,
        notes: 'Other requirement',
        order_id: 'order-1',
        qualification_type_id: null,
        requirement_type_id: 'requirement-type-1',
        status: 'active',
        target_qty: 1,
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    const removeActions = wrapper.findAll('[data-testid="customer-new-plan-delete-requirement-line"]');
    expect(removeActions).toHaveLength(2);

    await wrapper.findAll('[data-testid="customer-new-plan-requirement-line-select"]')[0]!.trigger('click');
    await nextTickFlush();
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').element as HTMLTextAreaElement).value).toBe('Selected requirement');

    await removeActions[0]!.trigger('click');
    await nextTickFlush();

    expect(confirmMock).toHaveBeenCalledWith('sicherplan.customerPlansWizard.confirmRemoveRequirementLine');
    expect(apiMocks.deleteOrderRequirementLineMock).toHaveBeenCalledWith(
      'tenant-1',
      'order-1',
      'requirement-line-existing-1',
      'token-1',
    );
    expect(apiMocks.listOrderRequirementLinesMock).toHaveBeenCalledWith('tenant-1', 'order-1', 'token-1');
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-line-select"]').text()).toContain('0 / 1');
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-line-select"]').text()).not.toContain('1 / 2');
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-type"]').element as HTMLSelectElement).value).toBe('');
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').element as HTMLTextAreaElement).value).toBe('');
  });

  it('unlinks existing order documents and refreshes the attachment list without deleting document metadata', async () => {
    stores.attachmentsByOrder['order-1'] = [
      { id: 'document-existing-1', current_version_no: 1, status: 'active', tenant_id: 'tenant-1', title: 'Wachbuch' },
      { id: 'document-existing-2', current_version_no: 2, status: 'active', tenant_id: 'tenant-1', title: 'Sicherheitskonzept' },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    const removeActions = wrapper.findAll('[data-testid="customer-new-plan-unlink-order-document"]');
    expect(removeActions).toHaveLength(2);
    expect(removeActions[0]?.classes()).toContain('sp-customer-plan-wizard-step__list-action--compact');
    expect(removeActions[0]?.classes()).toContain('sp-customer-plan-wizard-step__list-action--document-remove');
    const documentList = wrapper.get('[data-testid="customer-new-plan-order-document-list"]');
    expect(documentList.classes()).toContain('sp-customer-plan-wizard-step__document-list');
    expect(documentList.text()).toContain('Wachbuch');
    expect(documentList.text()).toContain('v1');
    expect(documentList.text()).toContain('active');
    expect(documentList.text()).not.toContain('document-existing-1');
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-link-id"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('sicherplan.customerPlansWizard.forms.manualDocumentId');

    await removeActions[0]!.trigger('click');
    await nextTickFlush();

    expect(confirmMock).toHaveBeenCalledWith('sicherplan.customerPlansWizard.confirmUnlinkOrderDocument');
    expect(apiMocks.unlinkOrderAttachmentMock).toHaveBeenCalledWith(
      'tenant-1',
      'order-1',
      'document-existing-1',
      'token-1',
    );
    expect(apiMocks.listOrderAttachmentsMock).toHaveBeenCalledWith('tenant-1', 'order-1', 'token-1');
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-list"]').text()).not.toContain('Wachbuch');
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-list"]').text()).toContain('Sicherheitskonzept');
  });

  it('places clear document draft next to the active upload or link action and keeps cleanup spacing structure', async () => {
    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-order-document-upload-title"]').setValue('Upload draft');
    await nextTickFlush();

    const attachButton = wrapper.get('[data-testid="customer-new-plan-attach-order-document"]');
    const uploadClearButton = wrapper.get('[data-testid="customer-new-plan-clear-order-document-draft"]');
    expect(attachButton.element.closest('.cta-row')).toBe(uploadClearButton.element.closest('.cta-row'));

    await uploadClearButton.trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-order-document-link-label"]').setValue('Draft label');
    await nextTickFlush();

    const linkButton = wrapper.get('[data-testid="customer-new-plan-link-order-document"]');
    const clearButton = wrapper.get('[data-testid="customer-new-plan-clear-order-document-draft"]');
    expect(linkButton.element.closest('.cta-row')).toBe(clearButton.element.closest('.cta-row'));
    expect(clearButton.element.closest('.sp-customer-plan-wizard-step__documents-panel')).toBeTruthy();

    const documentsCard = wrapper.get('[data-testid="customer-new-plan-order-scope-documents-card"]');
    expect(documentsCard.findAll('.sp-customer-plan-wizard-step__document-subsection')).toHaveLength(2);
    expect(documentsCard.find('.sp-customer-plan-wizard-step__document-divider').exists()).toBe(true);
    expect(documentsCard.find('.sp-customer-plan-wizard-step__document-list').exists()).toBe(false);
  });

  it('renders scoped spacing wrappers for equipment and requirement saved-row areas', async () => {
    stores.equipmentLinesByOrder['order-1'] = [
      {
        id: 'equipment-line-existing-1',
        archived_at: null,
        equipment_item_id: 'equipment-item-1',
        notes: 'Equipment row',
        order_id: 'order-1',
        required_qty: 2,
        status: 'active',
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];
    stores.requirementLinesByOrder['order-1'] = [
      {
        id: 'requirement-line-existing-1',
        archived_at: null,
        function_type_id: 'function-1',
        min_qty: 1,
        notes: 'Requirement row',
        order_id: 'order-1',
        qualification_type_id: 'qualification-1',
        requirement_type_id: 'requirement-type-1',
        status: 'active',
        target_qty: 2,
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    const equipmentCard = wrapper.get('[data-testid="customer-new-plan-order-scope-equipment-card"]');
    expect(equipmentCard.find('.sp-customer-plan-wizard-step__scope-subsection').exists()).toBe(true);
    expect(equipmentCard.find('.sp-customer-plan-wizard-step__scope-saved-list').exists()).toBe(true);
    expect(equipmentCard.find('.sp-customer-plan-wizard-step__scope-editor').exists()).toBe(true);

    const requirementsCard = wrapper.get('[data-testid="customer-new-plan-order-scope-requirements-card"]');
    expect(requirementsCard.find('.sp-customer-plan-wizard-step__scope-subsection').exists()).toBe(true);
    expect(requirementsCard.find('.sp-customer-plan-wizard-step__scope-saved-list').exists()).toBe(true);
    expect(requirementsCard.find('.sp-customer-plan-wizard-step__scope-editor').exists()).toBe(true);
  });

  it('keeps row edit/select behavior isolated from remove button clicks', async () => {
    stores.equipmentLinesByOrder['order-1'] = [
      {
        id: 'equipment-line-existing-1',
        archived_at: null,
        equipment_item_id: 'equipment-item-1',
        notes: 'Selectable equipment',
        order_id: 'order-1',
        required_qty: 2,
        status: 'active',
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];
    stores.requirementLinesByOrder['order-1'] = [
      {
        id: 'requirement-line-existing-1',
        archived_at: null,
        function_type_id: 'function-1',
        min_qty: 1,
        notes: 'Selectable requirement',
        order_id: 'order-1',
        qualification_type_id: 'qualification-1',
        requirement_type_id: 'requirement-type-1',
        status: 'active',
        target_qty: 2,
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];

    const wrapper = mountExistingOrderScope();
    await nextTickFlush();

    confirmMock.mockReturnValueOnce(false);
    await wrapper.get('[data-testid="customer-new-plan-delete-equipment-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.deleteOrderEquipmentLineMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-editing"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').element as HTMLTextAreaElement).value).toBe('');

    await wrapper.get('[data-testid="customer-new-plan-equipment-line-select"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-editing"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').element as HTMLTextAreaElement).value).toBe('Selectable equipment');

    confirmMock.mockReturnValueOnce(false);
    await wrapper.get('[data-testid="customer-new-plan-delete-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.deleteOrderRequirementLineMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-editing"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').element as HTMLTextAreaElement).value).toBe('');

    await wrapper.get('[data-testid="customer-new-plan-requirement-line-select"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-editing"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').element as HTMLTextAreaElement).value).toBe('Selectable requirement');
  });

  it('saves and updates equipment lines inline, blocks next for unsaved drafts, and clears persisted draft state', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToEquipmentLines(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(0);
    expectOrderScopeValidationFeedback(
      'sicherplan.customerPlansWizard.orderScope.equipmentTitle',
      'sicherplan.customerPlansWizard.errors.equipmentLineRequiredBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-order-scope-equipment-card"]').classes()).toContain(
      'sp-customer-plan-wizard-step__scope-card--invalid',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-equipment-item-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.equipmentLineRequiredBeforeContinue',
    );
    expect(scrollIntoViewMock.mock.contexts.at(-1)).toBe(wrapper.get('#customer-order-scope-section-equipment').element);
    expect((focusMock.mock.contexts.at(-1) as HTMLElement | undefined)?.getAttribute('data-testid')).toBe(
      'customer-new-plan-equipment-item',
    );

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
    await wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').setValue('3');
    await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue('Primary radios');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expectOrderScopeValidationFeedback(
      'sicherplan.customerPlansWizard.orderScope.equipmentTitle',
      'sicherplan.customerPlansWizard.errors.saveCurrentEquipmentLineBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-equipment-action-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.orderScope.equipmentTitle: sicherplan.customerPlansWizard.errors.saveCurrentEquipmentLineBeforeContinue',
    );
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(0);

    const equipmentDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'equipment-lines',
    );
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toContain('Primary radios');

    await wrapper.get('[data-testid="customer-new-plan-save-equipment-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.equipmentLineSaved');
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toBeNull();
    expect(stores.equipmentLinesByOrder['order-1']).toHaveLength(1);
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-item"]').element as HTMLSelectElement).value).toBe('');
    expect(wrapper.find('[data-testid="customer-new-plan-save-equipment-line"]').exists()).toBe(true);
    const equipmentOptionsAfterSave = wrapper
      .get('[data-testid="customer-new-plan-equipment-item"]')
      .findAll('option')
      .map((option) => option.attributes('value'));
    expect(equipmentOptionsAfterSave).not.toContain('equipment-item-1');
    expect(equipmentOptionsAfterSave).toContain('equipment-item-2');

    await wrapper.get('[data-testid="customer-new-plan-equipment-line-select"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-editing"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-update-equipment-line"]').exists()).toBe(true);
    const equipmentOptionsWhileEditing = wrapper
      .get('[data-testid="customer-new-plan-equipment-item"]')
      .findAll('option')
      .map((option) => option.attributes('value'));
    expect(equipmentOptionsWhileEditing).toContain('equipment-item-1');

    await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue('Updated radios');
    await wrapper.get('[data-testid="customer-new-plan-update-equipment-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.updateOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.equipmentLineUpdated');
    expect(stores.equipmentLinesByOrder['order-1']?.[0]?.notes).toBe('Updated radios');
    expect(wrapper.find('[data-testid="customer-new-plan-save-equipment-line"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-equipment-line-select"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-delete-equipment-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.deleteOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(stores.equipmentLinesByOrder['order-1']).toHaveLength(0);
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.equipmentLineDeleted');
    expect(wrapper.find('[data-testid="customer-new-plan-save-equipment-line"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-2');
    await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue('Discard me');
    await nextTickFlush();
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toContain('Discard me');
    await wrapper.get('[data-testid="customer-new-plan-clear-equipment-line"]').trigger('click');
    await nextTickFlush();
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toBeNull();
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-item"]').element as HTMLSelectElement).value).toBe('');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.updateOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.deleteOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
  });

  it('shows equipment save failures as toast feedback without restoring the old top banner', async () => {
    apiMocks.createOrderEquipmentLineMock.mockRejectedValueOnce(new Error('save failed'));
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToEquipmentLines(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
    await wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').setValue('3');
    await wrapper.get('[data-testid="customer-new-plan-save-equipment-line"]').trigger('click');
    await nextTickFlush();

    expectFeedback('error', 'sicherplan.customerPlansWizard.errors.equipmentLineSaveFailed');
    expect(wrapper.text()).not.toContain('sicherplan.customerPlansWizard.errors.equipmentLineSaveFailed');
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
  });

  it('saves and updates requirement lines inline, blocks next for unsaved drafts, and clears persisted draft state', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToRequirementLines(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(0);
    expectOrderScopeValidationFeedback(
      'sicherplan.customerPlansWizard.orderScope.requirementsTitle',
      'sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-requirement-type-error"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue',
    );
    expect(scrollIntoViewMock.mock.contexts.at(-1)).toBe(wrapper.get('#customer-order-scope-section-requirements').element);
    expect((focusMock.mock.contexts.at(-1) as HTMLElement | undefined)?.getAttribute('data-testid')).toBe(
      'customer-new-plan-requirement-type',
    );

    await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-function-type"]').setValue('function-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-qualification-type"]').setValue('qualification-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-min-qty"]').setValue('1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-target-qty"]').setValue('2');
    await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue('Need supervisor');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expectOrderScopeValidationFeedback(
      'sicherplan.customerPlansWizard.orderScope.requirementsTitle',
      'sicherplan.customerPlansWizard.errors.saveCurrentRequirementLineBeforeContinue',
    );
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(0);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-equipment-card"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-requirements-card"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-documents-card"]').exists()).toBe(true);
    const documentsCard = wrapper.get('[data-testid="customer-new-plan-order-scope-documents-card"]');
    expect(documentsCard.findAll('.sp-customer-plan-wizard-step__document-subsection')).toHaveLength(2);
    expect(documentsCard.find('.sp-customer-plan-wizard-step__document-divider').exists()).toBe(true);
    expect(documentsCard.find('[data-testid="customer-new-plan-order-document-upload-title"]').exists()).toBe(true);
    expect(documentsCard.find('[data-testid="customer-new-plan-order-document-link-id"]').exists()).toBe(false);
    expect(documentsCard.find('.sp-customer-plan-wizard-step__panel').exists()).toBe(false);

    const requirementDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'requirement-lines',
    );
    expect(window.sessionStorage.getItem(requirementDraftKey)).toContain('Need supervisor');

    await wrapper.get('[data-testid="customer-new-plan-save-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.requirementLineSaved');
    expect(window.sessionStorage.getItem(requirementDraftKey)).toBeNull();
    expect(stores.requirementLinesByOrder['order-1']).toHaveLength(1);
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-type"]').element as HTMLSelectElement).value).toBe('');

    await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-function-type"]').setValue('function-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-qualification-type"]').setValue('qualification-1');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-duplicate"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-save-requirement-line"]').attributes('disabled')).toBeDefined();
    await wrapper.get('[data-testid="customer-new-plan-save-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(1);

    await wrapper.get('[data-testid="customer-new-plan-requirement-line-select"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-editing"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-update-requirement-line"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-duplicate"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-update-requirement-line"]').attributes('disabled')).toBeUndefined();

    await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue('Updated requirement');
    await wrapper.get('[data-testid="customer-new-plan-update-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.updateOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.requirementLineUpdated');
    expect(stores.requirementLinesByOrder['order-1']?.[0]?.notes).toBe('Updated requirement');

    await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue('Discard requirement draft');
    await nextTickFlush();
    expect(window.sessionStorage.getItem(requirementDraftKey)).toContain('Discard requirement draft');
    await wrapper.get('[data-testid="customer-new-plan-clear-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(window.sessionStorage.getItem(requirementDraftKey)).toBeNull();
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-type"]').element as HTMLSelectElement).value).toBe('');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.updateOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('removes selected requirement lines inline and blocks continuing until a requirement line exists again', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToRequirementLines(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-target-qty"]').setValue('2');
    await wrapper.get('[data-testid="customer-new-plan-save-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(stores.requirementLinesByOrder['order-1']).toHaveLength(1);

    await wrapper.get('[data-testid="customer-new-plan-requirement-line-select"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-delete-requirement-line"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.deleteOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expect(stores.requirementLinesByOrder['order-1']).toHaveLength(0);
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.requirementLineDeleted');
    expect(wrapper.find('[data-testid="customer-new-plan-save-requirement-line"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expectOrderScopeValidationFeedback(
      'sicherplan.customerPlansWizard.orderScope.requirementsTitle',
      'sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue',
    );
  });

  it('selects an existing order on row click without opening the edit form or leaving order-details', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Objektschutz RheinForum Koln - Nordtor Juli',
      notes: 'Existing order notes',
      security_concept_text: 'Existing concept',
    });
    stores.orders['order-unrelated-1'] = makeOrder('order-unrelated-1', {
      order_no: 'OBJECT_GUARD',
      title: 'Objektschutz RheinForum Koln - Mai 2026',
    });
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    expect(apiMocks.listCustomerOrdersMock).toHaveBeenCalledWith('tenant-1', 'token-1', expect.objectContaining({
      customer_id: 'customer-1',
      include_archived: false,
    }));
    expect(wrapper.find('[data-testid="customer-new-plan-order-mode-existing"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-order-row"]')).toHaveLength(2);
    expect(wrapper.text()).toContain('Objektschutz RheinForum Koln - Nordtor Juli');
    expect(wrapper.text()).toContain('Objektschutz RheinForum Koln - Mai 2026');
    const firstOrderRow = wrapper.get('[data-testid="customer-new-plan-existing-order-row"]');
    expect(firstOrderRow.get('.sp-customer-order-row__primary').text()).toBe('ORD-EX-1 · Objektschutz RheinForum Koln - Nordtor Juli');
    expect(firstOrderRow.get('.sp-customer-order-row__secondary').text()).toBe('· 2026-06-01 - 2026-06-10 · draft · active');
    expect(firstOrderRow.text()).not.toContain('Juli2026-06-01');
    const orderListCallsBeforeSelect = apiMocks.listCustomerOrdersMock.mock.calls.length;
    const routerReplaceCallsBeforeSelect = routerReplaceMock.mock.calls.length;

    await firstOrderRow.trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listCustomerOrdersMock.mock.calls.length).toBe(orderListCallsBeforeSelect);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-order-title"]').exists()).toBe(false);
    const selectedRow = wrapper.get('[data-testid="customer-new-plan-existing-order-row"]');
    expect(selectedRow.classes()).toContain('sp-customer-plan-wizard-step__list-row--selected');
    expect(selectedRow.attributes('aria-pressed')).toBe('true');
    expect(wrapper.find('[data-testid="customer-new-plan-selected-order-summary"]').exists()).toBe(false);
    expect(routerReplaceMock.mock.calls.length).toBe(routerReplaceCallsBeforeSelect);
  });

  it('keeps create-new mode selected through reference reload even when the order form is still empty', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Existing title',
    });
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    await ensureCreateNewOrderMode(wrapper);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-list"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-order-no"]').exists()).toBe(true);

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    await nextTickFlush();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-list"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-order-no"]').exists()).toBe(true);
  });

  it('opens the edit form only from the edit action and updates an existing order inline without leaving order-details', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Existing title',
      notes: 'Existing order notes',
    });
    stores.equipmentLinesByOrder['order-existing-1'] = [
      {
        archived_at: null,
        equipment_item_id: 'equipment-item-1',
        id: 'equipment-line-existing-1',
        notes: 'Existing equipment line',
        order_id: 'order-existing-1',
        required_qty: 3,
        status: 'active',
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-existing-order-row"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(false);

    await wrapper.get('[data-testid="customer-new-plan-existing-order-edit"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledWith('tenant-1', 'order-existing-1', 'token-1');
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Existing title updated');
    await wrapper.get('[data-testid="customer-new-plan-existing-order-update"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.updateCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.updateCustomerOrderMock.mock.calls[0]?.[1]).toBe('order-existing-1');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(false);
    expectFeedback('success', 'sicherplan.customerPlansWizard.messages.existingOrderUpdated');
    expect(wrapper.get('[data-testid="customer-new-plan-existing-order-list"]').text()).toContain('Existing title updated');
    expect(stores.orders['order-existing-1']?.title).toBe('Existing title updated');
  });

  it('moves to equipment-lines only when Next is clicked for a selected existing order', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Existing title',
    });
    stores.equipmentLinesByOrder['order-existing-1'] = [
      {
        archived_at: null,
        equipment_item_id: 'equipment-item-1',
        id: 'equipment-line-existing-1',
        notes: 'Existing equipment line',
        order_id: 'order-existing-1',
        required_qty: 3,
        status: 'active',
        tenant_id: 'tenant-1',
        version_no: 1,
      },
    ];
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-existing-order-row"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(apiMocks.updateCustomerOrderMock).toHaveBeenCalledTimes(0);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.updateCustomerOrderMock).toHaveBeenCalledTimes(0);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect(routerReplaceMock).toHaveBeenCalledWith(expect.objectContaining({
      path: '/admin/customers/order-workspace',
      query: expect.objectContaining({
        customer_id: 'customer-1',
        order_id: 'order-existing-1',
      }),
    }));
    expect(apiMocks.listOrderEquipmentLinesMock).toHaveBeenCalledWith('tenant-1', 'order-existing-1', 'token-1');
    expect(wrapper.text()).toContain('Funkgerät');
  });

  it('blocks Next when an existing-order edit form is dirty and keeps the selected order after cancel edit', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Existing title',
      notes: 'Existing order notes',
    });
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-existing-order-edit"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Dirty edit title');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(apiMocks.updateCustomerOrderMock).toHaveBeenCalledTimes(0);
    expectFeedback('error', 'sicherplan.customerPlansWizard.errors.completeCurrentOrderEditBeforeContinue');

    await wrapper.get('[data-testid="customer-new-plan-existing-order-cancel-edit"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(false);
    const selectedRow = wrapper.get('[data-testid="customer-new-plan-existing-order-row"]');
    expect(selectedRow.classes()).toContain('sp-customer-plan-wizard-step__list-row--selected');
    expect(selectedRow.attributes('aria-pressed')).toBe('true');
    expect(wrapper.find('[data-testid="customer-new-plan-selected-order-summary"]').exists()).toBe(false);
  });

  it('blocks Next in existing-order mode when no order is selected and keeps create-new mode working', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Existing title',
    });
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expectFeedback('error', 'sicherplan.customerPlansWizard.errors.orderSelectionRequired');
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(0);

    wrapper.unmount();

    routeState.query = {
      customer_id: 'customer-1',
      step: 'order-details',
    };
    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'order-details',
    );
    window.sessionStorage.setItem(
      draftKey,
      JSON.stringify({
        form: {
          customer_id: 'customer-1',
          notes: '',
          order_no: '',
          patrol_route_id: '',
          release_state: 'draft',
          requirement_type_id: '',
          security_concept_text: '',
          service_category_code: '',
          service_from: '',
          service_to: '',
          title: '',
        },
        mode: 'create_new',
        selected_order_id: '',
      }),
    );

    const createWrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(createWrapper);
    await createWrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-NEW-2');
    await createWrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Create after existing mode');
    await createWrapper.get('[data-testid="customer-new-plan-order-requirement-type"]').setValue('requirement-type-1');
    await createWrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await createWrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
    await createWrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
    await createWrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(createWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
  });

  it('restores a selected existing order from route order_id and ignores stale create-new draft content', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Hydrated existing order',
      security_concept_text: 'Hydrated concept',
    });
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-existing-1',
      step: 'order-details',
    };
    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'order-details',
    );
    window.sessionStorage.setItem(
      draftKey,
      JSON.stringify({
        mode: 'create_new',
        selected_order_id: '',
        form: {
          customer_id: 'customer-1',
          notes: 'stale create draft',
          order_no: 'ORD-STALE',
          patrol_route_id: '',
          release_state: 'draft',
          requirement_type_id: 'requirement-type-1',
          security_concept_text: '',
          service_category_code: 'guarding',
          service_from: '2026-07-01',
          service_to: '2026-07-02',
          title: 'stale draft title',
        },
      }),
    );

    const wrapper = mountComponent();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.text()).toContain('Order workspace');
    expect(wrapper.text()).not.toContain('New plan');
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(false);
    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledTimes(0);
    const selectedRow = wrapper.get('[data-testid="customer-new-plan-existing-order-row"]');
    expect(selectedRow.classes()).toContain('sp-customer-plan-wizard-step__list-row--selected');
    expect(selectedRow.attributes('aria-pressed')).toBe('true');
    expect(selectedRow.text()).toContain('ORD-EX-1');
    expect(selectedRow.text()).toContain('Hydrated existing order');
    expect(wrapper.find('[data-testid="customer-new-plan-selected-order-summary"]').exists()).toBe(false);
    expect((wrapper.vm as any).wizardState.order_id).toBe('order-existing-1');
    expect(getOrderStepContentState(wrapper).selectedExistingOrderId).toBe('order-existing-1');
    expect(getOrderStepContentState(wrapper).editingExistingOrderId).toBe('');
    expect(getOrderStepContentState(wrapper).existingOrderEditFormOpen).toBe(false);
  });

  it('opens an existing-order edit form from external order_mode=edit navigation without a persisted edit draft', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      notes: 'Saved notes',
      order_no: 'ORD-EX-1',
      security_concept_text: 'Saved concept',
      title: 'Hydrated existing order',
    });
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-existing-1',
      order_mode: 'edit',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledWith('tenant-1', 'order-existing-1', 'token-1');
    expect(getOrderStepContentState(wrapper).selectedExistingOrderId).toBe('order-existing-1');
    expect(getOrderStepContentState(wrapper).editingExistingOrderId).toBe('order-existing-1');
    expect(getOrderStepContentState(wrapper).existingOrderEditFormOpen).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Hydrated existing order');
    expect((wrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Saved notes');
  });

  it('restores an existing-order edit draft when external order_mode=edit opens the editor', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      notes: 'Saved notes',
      order_no: 'ORD-EX-1',
      security_concept_text: 'Saved concept',
      title: 'Hydrated existing order',
    });
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-existing-1',
      order_mode: 'edit',
      step: 'order-details',
    };
    window.sessionStorage.setItem(
      buildOrderDetailsEditDraftStorageKey(
        {
          customerId: 'customer-1',
          tenantId: 'tenant-1',
        },
        'order-existing-1',
      ),
      JSON.stringify({
        form: {
          customer_id: 'customer-1',
          notes: 'Draft notes override',
          order_no: 'ORD-DRAFT-EDIT',
          patrol_route_id: '',
          release_state: 'draft',
          requirement_type_id: 'requirement-type-1',
          security_concept_text: 'Draft concept override',
          service_category_code: 'guarding',
          service_from: '2026-06-01',
          service_to: '2026-06-10',
          title: 'Draft title override',
        },
        order_id: 'order-existing-1',
      }),
    );

    const wrapper = mountComponent();
    await nextTickFlush();

    expect(getOrderStepContentState(wrapper).selectedExistingOrderId).toBe('order-existing-1');
    expect(getOrderStepContentState(wrapper).editingExistingOrderId).toBe('order-existing-1');
    expect(getOrderStepContentState(wrapper).existingOrderEditFormOpen).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Draft title override');
    expect((wrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Draft notes override');
    expect(wrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');
  });

  it('persists an existing-order edit draft separately from create-new drafts and restores the edit form on remount', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Hydrated existing order',
    });
    routeState.query = {
      customer_id: 'customer-1',
      order_id: 'order-existing-1',
      step: 'order-details',
    };
    const createDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'order-details',
    );
    window.sessionStorage.setItem(
      createDraftKey,
      JSON.stringify({
        mode: 'create_new',
        selected_order_id: '',
        form: {
          customer_id: 'customer-1',
          notes: 'create draft notes',
          order_no: 'ORD-CREATE',
          patrol_route_id: '',
          release_state: 'draft',
          requirement_type_id: 'requirement-type-1',
          security_concept_text: '',
          service_category_code: 'guarding',
          service_from: '2026-07-01',
          service_to: '2026-07-02',
          title: 'create draft title',
        },
      }),
    );

    const wrapper = mountComponent();
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-existing-order-edit"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Edited before remount');
    await nextTickFlush();

    const editDraftKey = buildOrderDetailsEditDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'order-existing-1',
    );
    expect(window.sessionStorage.getItem(editDraftKey)).toContain('Edited before remount');
    expect(window.sessionStorage.getItem(createDraftKey)).toContain('create draft title');

    wrapper.unmount();

    const restoredWrapper = mountComponent();
    await nextTickFlush();

    expect(restoredWrapper.find('[data-testid="customer-new-plan-existing-order-edit-form"]').exists()).toBe(true);
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Edited before remount');
    expect(window.sessionStorage.getItem(createDraftKey)).toContain('create draft title');
  });

  it('shows the generic empty-state help when the customer has no existing orders', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-order-row"]')).toHaveLength(0);
    expect(wrapper.find('[data-testid="customer-new-plan-order-no"]').exists()).toBe(true);
  });

  it('keeps an unsaved equipment draft during same-customer auth refresh and remount', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      order_id: 'order-1',
      step: 'equipment-lines',
    };
    stores.orders['order-1'] = makeOrder('order-1');

    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
    await wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').setValue('4');
    await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue('Keep after auth refresh');
    await nextTickFlush();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'equipment-lines',
    );
    expect(window.sessionStorage.getItem(draftKey)).toContain('Keep after auth refresh');

    authStoreState.effectiveAccessToken = 'token-2';
    await nextTickFlush();
    await nextTickFlush();

    expect((wrapper.get('[data-testid="customer-new-plan-equipment-item"]').element as HTMLSelectElement).value).toBe('equipment-item-1');
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').element as HTMLInputElement).value).toBe('4');
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').element as HTMLTextAreaElement).value).toBe('Keep after auth refresh');

    wrapper.unmount();
    mountedWrappers.pop();

    const restoredWrapper = mountComponent();
    await nextTickFlush();

    expect(restoredWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-equipment-item"]').element as HTMLSelectElement).value).toBe('equipment-item-1');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').element as HTMLInputElement).value).toBe('4');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-equipment-notes"]').element as HTMLTextAreaElement).value).toBe('Keep after auth refresh');
    expect(window.sessionStorage.getItem(draftKey)).toContain('Keep after auth refresh');
  });

  it('keeps an unsaved requirement draft during same-customer auth refresh and remount', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      order_id: 'order-1',
      step: 'requirement-lines',
    };
    stores.orders['order-1'] = makeOrder('order-1');

    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-function-type"]').setValue('function-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-qualification-type"]').setValue('qualification-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-min-qty"]').setValue('2');
    await wrapper.get('[data-testid="customer-new-plan-requirement-target-qty"]').setValue('3');
    await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue('Keep requirement draft');
    await nextTickFlush();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'requirement-lines',
    );
    expect(window.sessionStorage.getItem(draftKey)).toContain('Keep requirement draft');

    authStoreState.effectiveAccessToken = 'token-2';
    await nextTickFlush();
    await nextTickFlush();

    expect((wrapper.get('[data-testid="customer-new-plan-requirement-type"]').element as HTMLSelectElement).value).toBe('requirement-type-1');
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-min-qty"]').element as HTMLInputElement).value).toBe('2');
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-target-qty"]').element as HTMLInputElement).value).toBe('3');
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').element as HTMLTextAreaElement).value).toBe('Keep requirement draft');

    wrapper.unmount();
    mountedWrappers.pop();

    const restoredWrapper = mountComponent();
    await nextTickFlush();

    expect(restoredWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-scope-documents');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-requirement-type"]').element as HTMLSelectElement).value).toBe('requirement-type-1');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-requirement-min-qty"]').element as HTMLInputElement).value).toBe('2');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-requirement-target-qty"]').element as HTMLInputElement).value).toBe('3');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-requirement-notes"]').element as HTMLTextAreaElement).value).toBe('Keep requirement draft');
    expect(window.sessionStorage.getItem(draftKey)).toContain('Keep requirement draft');
  });

  it('does not leak equipment or requirement drafts across customer switch', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      order_id: 'order-1',
      step: 'equipment-lines',
    };
    stores.orders['order-1'] = makeOrder('order-1');
    apiMocks.getCustomerMock.mockImplementation((_tenantId: string, customerId: string) =>
      Promise.resolve(buildCustomer({ customer_number: customerId === 'customer-2' ? 'CU-2000' : 'CU-1000', id: customerId, name: customerId === 'customer-2' ? 'Beta Security' : 'Alpha Security' })),
    );

    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
    await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue('Customer one equipment draft');
    await nextTickFlush();

    const equipmentDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'equipment-lines',
    );

    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      order_id: 'order-1',
      step: 'requirement-lines',
    };
    await nextTickFlush();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue('Customer one requirement draft');
    await nextTickFlush();

    const requirementDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        tenantId: 'tenant-1',
      },
      'requirement-lines',
    );

    routeState.query = {
      customer_id: 'customer-2',
    };
    await nextTickFlush();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-item"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-type"]').exists()).toBe(false);
    expect(window.sessionStorage.getItem(equipmentDraftKey) ?? '').not.toContain('customer-2');
    expect(window.sessionStorage.getItem(requirementDraftKey) ?? '').not.toContain('customer-2');
  });

  it.skip('supports create-new planning behavior in step 1 and derives the planning mode from the chosen family', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-family"]').setValue('event_venue');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-venue-no"]').setValue('VEN-2');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Messehalle');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-address-id"]').setValue('address-1');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').setValue('Europe/Berlin');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').setValue('52.520008');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').setValue('13.404954');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-status"]').setValue('inactive');
    await wrapper.get('[data-testid="modal-ok"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenCalledWith(
      'event_venue',
      'tenant-1',
      'token-1',
      expect.objectContaining({
        address_id: 'address-1',
        customer_id: 'customer-1',
        latitude: 52.520008,
        longitude: 13.404954,
        status: 'inactive',
        timezone: 'Europe/Berlin',
        venue_no: 'VEN-2',
      }),
    );

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
  });

  it('restores an unsaved order-details draft after remount and stays on order-details', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-DRAFT');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Ungespeicherter Auftrag');
    await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-12');
    await nextTickFlush();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'order-details',
    );
    expect(window.sessionStorage.getItem(draftKey)).toContain('ORD-DRAFT');

    wrapper.unmount();
    mountedWrappers.pop();

    const restoredWrapper = mountComponent();
    await nextTickFlush();

    expect(restoredWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-DRAFT');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Ungespeicherter Auftrag');
    expect(restoredWrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');
  });

  it('keeps the unsaved order-details draft during same-customer auth refresh', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-REFRESH');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Auth Refresh Draft');
    await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
    await wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').setValue('Security concept survives refresh');
    await wrapper.get('[data-testid="customer-new-plan-order-notes"]').setValue('Notes survive refresh');
    await nextTickFlush();

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect((wrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-REFRESH');
    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Auth Refresh Draft');
    expect((wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Security concept survives refresh');
    expect((wrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Notes survive refresh');
  });

  it('restores a preexisting order-details draft after auth-driven remount and repeated reference reloads without overwriting it with defaults', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'order-details',
    );
    window.sessionStorage.setItem(
      draftKey,
      JSON.stringify({
        customer_id: 'customer-1',
        notes: 'Keep this note',
        order_no: 'ORD-STORED',
        patrol_route_id: '',
        release_state: 'draft',
        requirement_type_id: '',
        security_concept_text: 'Do not overwrite me',
        service_category_code: 'guarding',
        service_from: '2026-06-01',
        service_to: '2026-06-12',
        title: 'Persisted before mount',
      }),
    );

    const firstWrapper = mountComponent();
    await nextTickFlush();

    expect((firstWrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-STORED');
    expect((firstWrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Persisted before mount');
    expect((firstWrapper.get('[data-testid="customer-new-plan-order-service-category"]').element as HTMLSelectElement).value).toBe('guarding');
    expect((firstWrapper.get('[data-testid="customer-new-plan-order-service-from"]').element as HTMLInputElement).value).toBe('2026-06-01');
    expect((firstWrapper.get('[data-testid="customer-new-plan-order-service-to"]').element as HTMLInputElement).value).toBe('2026-06-12');
    expect((firstWrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Do not overwrite me');
    expect((firstWrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Keep this note');

    const firstServiceCategoryLoadCount = apiMocks.listServiceCategoryOptionsMock.mock.calls.length;
    const firstRequirementTypeLoadCount = apiMocks.listPlanningSetupRecordsMock.mock.calls.filter(
      ([entityKey]) => entityKey === 'requirement_type',
    ).length;
    const firstPatrolRouteLoadCount = apiMocks.listPlanningSetupRecordsMock.mock.calls.filter(
      ([entityKey]) => entityKey === 'patrol_route',
    ).length;
    const firstEquipmentItemLoadCount = apiMocks.listPlanningSetupRecordsMock.mock.calls.filter(
      ([entityKey]) => entityKey === 'equipment_item',
    ).length;
    const firstFunctionTypeLoadCount = apiMocks.listFunctionTypesMock.mock.calls.length;
    const firstQualificationTypeLoadCount = apiMocks.listQualificationTypesMock.mock.calls.length;

    firstWrapper.unmount();
    mountedWrappers.pop();

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';

    const secondWrapper = mountComponent();
    await nextTickFlush();

    expect(secondWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect((secondWrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-STORED');
    expect((secondWrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Persisted before mount');
    expect((secondWrapper.get('[data-testid="customer-new-plan-order-service-category"]').element as HTMLSelectElement).value).toBe('guarding');
    expect((secondWrapper.get('[data-testid="customer-new-plan-order-service-from"]').element as HTMLInputElement).value).toBe('2026-06-01');
    expect((secondWrapper.get('[data-testid="customer-new-plan-order-service-to"]').element as HTMLInputElement).value).toBe('2026-06-12');
    expect((secondWrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Do not overwrite me');
    expect((secondWrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Keep this note');
    expect(secondWrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');
    expect(window.sessionStorage.getItem(draftKey)).toContain('ORD-STORED');
    expect(window.sessionStorage.getItem(draftKey)).toContain('Persisted before mount');

    expect(apiMocks.listServiceCategoryOptionsMock.mock.calls.length).toBeGreaterThan(firstServiceCategoryLoadCount);
    expect(
      apiMocks.listPlanningSetupRecordsMock.mock.calls.filter(([entityKey]) => entityKey === 'requirement_type').length,
    ).toBeGreaterThan(firstRequirementTypeLoadCount);
    expect(
      apiMocks.listPlanningSetupRecordsMock.mock.calls.filter(([entityKey]) => entityKey === 'patrol_route').length,
    ).toBeGreaterThan(firstPatrolRouteLoadCount);
    expect(
      apiMocks.listPlanningSetupRecordsMock.mock.calls.filter(([entityKey]) => entityKey === 'equipment_item').length,
    ).toBeGreaterThan(firstEquipmentItemLoadCount);
    expect(apiMocks.listFunctionTypesMock.mock.calls.length).toBeGreaterThan(firstFunctionTypeLoadCount);
    expect(apiMocks.listQualificationTypesMock.mock.calls.length).toBeGreaterThan(firstQualificationTypeLoadCount);
  });

  it('keeps a typed order-details draft across auth churn and same-route remount when no order_id exists', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-REMOUNT');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Remount after auth refresh');
    await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-03');
    await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-14');
    await wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').setValue('Security concept remount');
    await wrapper.get('[data-testid="customer-new-plan-order-notes"]').setValue('Notes remount');
    await nextTickFlush();

    authStoreState.effectiveAccessToken = '';
    authStoreState.accessToken = '';
    authStoreState.isSessionResolving = true;
    await nextTickFlush();

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    authStoreState.isSessionResolving = false;

    wrapper.unmount();
    mountedWrappers.pop();

    const restoredWrapper = mountComponent();
    await nextTickFlush();

    expect(restoredWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-REMOUNT');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Remount after auth refresh');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-service-category"]').element as HTMLSelectElement).value).toBe('guarding');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-service-from"]').element as HTMLInputElement).value).toBe('2026-06-03');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-service-to"]').element as HTMLInputElement).value).toBe('2026-06-14');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Security concept remount');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Notes remount');
  });

  it('persists the latest typed order-details values even if remount happens before watcher-flush settles', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    const orderNoInput = wrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement;
    const titleInput = wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement;
    const serviceCategorySelect = wrapper.get('[data-testid="customer-new-plan-order-service-category"]').element as HTMLSelectElement;
    const serviceFromInput = wrapper.get('[data-testid="customer-new-plan-order-service-from"]').element as HTMLInputElement;
    const serviceToInput = wrapper.get('[data-testid="customer-new-plan-order-service-to"]').element as HTMLInputElement;
    const securityConceptTextarea = wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement;
    const notesTextarea = wrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement;

    orderNoInput.value = 'ORD-RACE';
    orderNoInput.dispatchEvent(new Event('input'));
    titleInput.value = 'Watcher race draft';
    titleInput.dispatchEvent(new Event('input'));
    serviceCategorySelect.value = 'guarding';
    serviceCategorySelect.dispatchEvent(new Event('change'));
    serviceFromInput.value = '2026-06-05';
    serviceFromInput.dispatchEvent(new Event('input'));
    serviceToInput.value = '2026-06-15';
    serviceToInput.dispatchEvent(new Event('input'));
    securityConceptTextarea.value = 'Security concept race';
    securityConceptTextarea.dispatchEvent(new Event('input'));
    notesTextarea.value = 'Notes race';
    notesTextarea.dispatchEvent(new Event('input'));

    wrapper.unmount();
    mountedWrappers.pop();

    const restoredWrapper = mountComponent();
    await nextTickFlush();

    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-RACE');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Watcher race draft');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-service-category"]').element as HTMLSelectElement).value).toBe('guarding');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-service-from"]').element as HTMLInputElement).value).toBe('2026-06-05');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-service-to"]').element as HTMLInputElement).value).toBe('2026-06-15');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Security concept race');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Notes race');
  });

  it('does not save or clear order-details draft under an incomplete planning key when route context already has planning_entity_id', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-REAL-KEY');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Real key draft');
    await nextTickFlush();

    const storageKeys = Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) || '');
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:_:_:order-details'))).toBe(false);
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:site:site-1:order-details'))).toBe(false);
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:order-details'))).toBe(true);
  });

  it('keeps the real order-details draft through rapid same-context token churn without creating a second draft key', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-DOUBLE-REFRESH');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Double refresh draft');
    await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-06');
    await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-16');
    await wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').setValue('Double refresh security concept');
    await wrapper.get('[data-testid="customer-new-plan-order-notes"]').setValue('Double refresh notes');
    await nextTickFlush();

    authStoreState.effectiveAccessToken = '';
    authStoreState.accessToken = '';
    await nextTickFlush();
    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    await nextTickFlush();
    authStoreState.effectiveAccessToken = 'token-3';
    authStoreState.accessToken = 'token-3';
    await nextTickFlush();

    const storageKeys = Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) || '');
    expect(storageKeys.filter((key) => key.includes('customerNewPlanWizardDraft')).length).toBe(1);
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:_:_:order-details'))).toBe(false);
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:site:site-1:order-details'))).toBe(false);
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:order-details'))).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-DOUBLE-REFRESH');
    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Double refresh draft');
    expect((wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Double refresh security concept');
    expect((wrapper.get('[data-testid="customer-new-plan-order-notes"]').element as HTMLTextAreaElement).value).toBe('Double refresh notes');
  });

  it('clears the unsaved order draft after successful save and persists order_id into the route update', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-SAVE');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Gespeicherter Auftrag');
    await wrapper.get('[data-testid="customer-new-plan-order-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
    await nextTickFlush();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'order-details',
    );
    expect(window.sessionStorage.getItem(draftKey)).toContain('ORD-SAVE');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(window.sessionStorage.getItem(draftKey)).toBeNull();
    expect(routerReplaceMock).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/admin/customers/order-workspace',
        query: expect.objectContaining({
          order_id: 'order-1',
        }),
      }),
    );
  });

  it('does not leak a previous customer order draft after customer switch', async () => {
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };

    const wrapper = mountComponent();
    await nextTickFlush();

    await ensureCreateNewOrderMode(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Customer One Draft');
    await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
    await nextTickFlush();

    apiMocks.getCustomerMock.mockResolvedValueOnce(
      buildCustomer({
        customer_number: 'CU-2000',
        id: 'customer-2',
        name: 'Beta Security',
        tenant_id: 'tenant-1',
      }),
    );
    routeState.query = {
      customer_id: 'customer-2',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      step: 'order-details',
    };
    await nextTickFlush();

    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('');
    expect((wrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('');
  });

  it.skip('creates a new address inside the planning modal, refreshes options, and selects it', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    const initialAddressLoads = apiMocks.listCustomerAddressesMock.mock.calls.length;
    await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-address-action"]').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-create-address-action"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-address-street-line-1"]').setValue('Neue Straße 5');
    await wrapper.get('[data-testid="customer-new-plan-planning-address-postal-code"]').setValue('50667');
    await wrapper.get('[data-testid="customer-new-plan-planning-address-city"]').setValue('Köln');
    await wrapper.get('[data-testid="customer-new-plan-planning-address-country-code"]').setValue('DE');
    await wrapper.get('[data-testid="customer-new-plan-planning-address-save"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createCustomerAvailableAddressMock).toHaveBeenCalledWith(
      'tenant-1',
      'customer-1',
      'token-1',
      {
        city: 'Köln',
        country_code: 'DE',
        postal_code: '50667',
        state: null,
        street_line_1: 'Neue Straße 5',
        street_line_2: null,
      },
    );
    expect(apiMocks.listCustomerAddressesMock.mock.calls.length).toBeGreaterThan(initialAddressLoads);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-address-id"]').element as HTMLSelectElement).value).toBe('available-address-1');
    expect(wrapper.find('[data-testid="customer-new-plan-planning-address-dialog"]').exists()).toBe(false);
  });

  it.skip('validates required address fields and keeps the planning modal state stable when address creation is canceled', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').setValue('SITE-99');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Stable Modal Site');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-address-action"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-address-save"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createCustomerAvailableAddressMock).not.toHaveBeenCalled();
    expectFeedback('error', 'sicherplan.customerPlansWizard.errors.addressCreateValidation');
    expect(wrapper.find('[data-testid="customer-new-plan-planning-address-dialog"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-planning-address-street-line-1"]').setValue('Should be discarded');
    await wrapper.get('[data-testid="customer-new-plan-planning-address-cancel"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-address-dialog"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').element as HTMLInputElement).value).toBe('SITE-99');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').element as HTMLInputElement).value).toBe('Stable Modal Site');
  });

  it.skip('writes the created address into the correct family-specific target field', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    const cases = [
      {
        addressFieldTestId: 'customer-new-plan-planning-create-address-id',
        family: 'trade_fair',
      },
      {
        addressFieldTestId: 'customer-new-plan-planning-create-meeting-address-id',
        family: 'patrol_route',
      },
    ];

    for (const testCase of cases) {
      await wrapper.get('[data-testid="customer-new-plan-planning-family"]').setValue(testCase.family);
      await nextTickFlush();
      await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
      await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
      await nextTickFlush();

      await wrapper.get('[data-testid="customer-new-plan-planning-create-address-action"]').trigger('click');
      await nextTickFlush();
      await wrapper.get('[data-testid="customer-new-plan-planning-address-street-line-1"]').setValue('Neue Straße 5');
      await wrapper.get('[data-testid="customer-new-plan-planning-address-postal-code"]').setValue('50667');
      await wrapper.get('[data-testid="customer-new-plan-planning-address-city"]').setValue('Köln');
      await wrapper.get('[data-testid="customer-new-plan-planning-address-country-code"]').setValue('DE');
      await wrapper.get('[data-testid="customer-new-plan-planning-address-save"]').trigger('click');
      await nextTickFlush();

      expect((wrapper.get(`[data-testid="${testCase.addressFieldTestId}"]`).element as HTMLSelectElement).value).toBe('available-address-1');
      await wrapper.get('[data-testid="modal-cancel"]').trigger('click');
      await nextTickFlush();
    }
  });

  it.skip('shows map picking only for coordinate-backed families and applies the selected coordinates', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');

    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-pick-on-map"]').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-create-pick-on-map"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-location-picker-apply"]').trigger('click');
    await nextTickFlush();

    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').element as HTMLInputElement).value)).toBe(51.111111);
    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').element as HTMLInputElement).value)).toBe(8.222222);

    await wrapper.get('[data-testid="modal-cancel"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-family"]').setValue('patrol_route');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-address-action"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-pick-on-map"]').exists()).toBe(false);
  });

  it.skip('keeps coordinates unchanged when the map picker is canceled and wires the localized load error text', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').setValue('50.111111');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').setValue('7.222222');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-pick-on-map"]').trigger('click');
    await nextTickFlush();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-location-picker-load-error"]').text()).toBe(
      'sicherplan.customerPlansWizard.mapPicker.loadError',
    );
    await wrapper.get('[data-testid="customer-new-plan-location-picker-cancel"]').trigger('click');
    await nextTickFlush();

    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').element as HTMLInputElement).value)).toBe(50.111111);
    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').element as HTMLInputElement).value)).toBe(7.222222);
  });

  it.skip('submits only the canonical family-specific payload fields for site, trade fair, and patrol route', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    const scenarios = [
      async () => {
        await wrapper.get('[data-testid="customer-new-plan-planning-family"]').setValue('site');
        await nextTickFlush();
        await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
        await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
        await nextTickFlush();
        await wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').setValue('SITE-2');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Werk Süd');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-address-id"]').setValue('address-1');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').setValue('Europe/Berlin');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').setValue('50.123456');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').setValue('8.123456');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-watchbook-enabled"]').setValue(true);
        await wrapper.get('[data-testid="customer-new-plan-planning-create-status"]').setValue('inactive');
        await wrapper.get('[data-testid="modal-ok"]').trigger('click');
        await nextTickFlush();
        expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenLastCalledWith(
          'site',
          'tenant-1',
          'token-1',
          expect.objectContaining({
            address_id: 'address-1',
            latitude: 50.123456,
            longitude: 8.123456,
            timezone: 'Europe/Berlin',
            watchbook_enabled: true,
            status: 'inactive',
          }),
        );
      },
      async () => {
        await wrapper.get('[data-testid="customer-new-plan-planning-family"]').setValue('trade_fair');
        await nextTickFlush();
        await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
        await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
        await nextTickFlush();
        await wrapper.get('[data-testid="customer-new-plan-planning-create-fair-no"]').setValue('FAIR-2');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Sommermesse');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-venue-id"]').setValue('venue-1');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-address-id"]').setValue('address-1');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').setValue('Europe/Berlin');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').setValue('51.333333');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').setValue('9.444444');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-start-date"]').setValue('2026-07-01');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-end-date"]').setValue('2026-07-03');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-status"]').setValue('active');
        await wrapper.get('[data-testid="modal-ok"]').trigger('click');
        await nextTickFlush();
        expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenLastCalledWith(
          'trade_fair',
          'tenant-1',
          'token-1',
          expect.objectContaining({
            venue_id: 'venue-1',
            address_id: 'address-1',
            latitude: 51.333333,
            longitude: 9.444444,
            timezone: 'Europe/Berlin',
            start_date: '2026-07-01',
            end_date: '2026-07-03',
            status: 'active',
          }),
        );
      },
      async () => {
        await wrapper.get('[data-testid="customer-new-plan-planning-family"]').setValue('patrol_route');
        await nextTickFlush();
        await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
        await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
        await nextTickFlush();
        await wrapper.get('[data-testid="customer-new-plan-planning-create-route-no"]').setValue('ROUTE-2');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Innenstadt Süd');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-site-id"]').setValue('site-1');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-meeting-address-id"]').setValue('address-1');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-start-point"]').setValue('Start A');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-end-point"]').setValue('Ende B');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-travel-policy-code"]').setValue('city');
        await wrapper.get('[data-testid="customer-new-plan-planning-create-status"]').setValue('inactive');
        await wrapper.get('[data-testid="modal-ok"]').trigger('click');
        await nextTickFlush();
        expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenLastCalledWith(
          'patrol_route',
          'tenant-1',
          'token-1',
          expect.objectContaining({
            site_id: 'site-1',
            meeting_address_id: 'address-1',
            start_point_text: 'Start A',
            end_point_text: 'Ende B',
            travel_policy_code: 'city',
            status: 'inactive',
          }),
        );
        expect(apiMocks.createPlanningSetupRecordMock.mock.calls.at(-1)?.[3]).not.toHaveProperty('latitude');
        expect(apiMocks.createPlanningSetupRecordMock.mock.calls.at(-1)?.[3]).not.toHaveProperty('longitude');
      },
    ];

    for (const run of scenarios) {
      await run();
    }
  });

  it.skip('keeps the real planning create modal and typed values stable across focus-driven session refresh', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-customer-summary"]').text()).toContain('Alpha Security');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');

    await wrapper.get('[data-testid="customer-new-plan-planning-mode-create"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').setValue('TEST-SITE-FOCUS');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Focus Persistence Test Site');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').setValue('Europe/Berlin');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').setValue('50.950000');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').setValue('6.980000');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-watchbook-enabled"]').setValue(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-create-notes"]').setValue('Focus regression test');
    await nextTickFlush();

    apiMocks.getCustomerMock.mockResolvedValue(buildCustomer());
    window.dispatchEvent(new Event('blur'));
    authStoreState.isSessionResolving = true;
    authStoreState.effectiveAccessToken = '';
    authStoreState.accessToken = '';
    document.dispatchEvent(new Event('visibilitychange'));
    window.dispatchEvent(new Event('focus'));
    await nextTickFlush();

    expect(wrapper.find('[data-testid="customer-new-plan-loading"]').exists()).toBe(false);
    expect(wrapper.find('.modal-stub').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').element as HTMLInputElement).value).toBe('TEST-SITE-FOCUS');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').element as HTMLInputElement).value).toBe('Focus Persistence Test Site');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').element as HTMLSelectElement).value).toBe('Europe/Berlin');
    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').element as HTMLInputElement).value)).toBe(50.95);
    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').element as HTMLInputElement).value)).toBe(6.98);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-watchbook-enabled"]').element as HTMLInputElement).checked).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-notes"]').element as HTMLTextAreaElement).value).toBe('Focus regression test');
    expect(wrapper.find('[data-testid="customer-new-plan-planning-create"]').exists()).toBe(true);
    expect(routerPushMock).not.toHaveBeenCalled();

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    authStoreState.isSessionResolving = false;
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-timezone"]').setValue('Europe/Berlin');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').trigger('focus');
    await nextTickFlush();

    expect(wrapper.find('.modal-stub').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
    expect(routerPushMock).not.toHaveBeenCalled();

    await wrapper.get('[data-testid="modal-cancel"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.find('.modal-stub').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
  });
});
