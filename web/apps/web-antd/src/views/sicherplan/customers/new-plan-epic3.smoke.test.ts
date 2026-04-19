// @vitest-environment happy-dom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils';
import { defineComponent, reactive } from 'vue';

import CustomerNewPlanWizardView from './new-plan.vue';
import { buildWizardDraftStorageKey } from './new-plan-wizard-drafts';

const routeState = reactive({
  query: { customer_id: 'customer-1' } as Record<string, unknown>,
});
const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
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
  attachmentsByOrder: {} as Record<string, Array<{ current_version_no: number; id: string; status: string; tenant_id: string; title: string }>>,
  equipmentItems: [{ id: 'equipment-item-1', customer_id: 'customer-1', code: 'EQ-1', label: 'Funkgerät', tenant_id: 'tenant-1' }],
  equipmentLinesByOrder: {} as Record<string, Array<{ id: string; equipment_item_id: string; required_qty: number; notes: string | null; order_id: string; tenant_id: string; status: string; version_no: number; archived_at: null }>>,
  eventVenues: [{ id: 'venue-1', customer_id: 'customer-1', venue_no: 'VEN-1', name: 'Arena', tenant_id: 'tenant-1' }],
  functionTypes: [{ id: 'function-1', code: 'SUP', label: 'Supervisor' }],
  orders: {} as Record<string, any>,
  patrolRoutes: [{ id: 'route-1', customer_id: 'customer-1', route_no: 'ROU-1', name: 'Innenstadt', tenant_id: 'tenant-1' }],
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
  getCustomerMock: vi.fn(),
  getCustomerOrderMock: vi.fn(),
  linkOrderAttachmentMock: vi.fn(),
  listCustomerOrdersMock: vi.fn(),
  listCustomerAddressesMock: vi.fn(),
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
}));

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
  getCustomerOrder: apiMocks.getCustomerOrderMock,
  linkOrderAttachment: apiMocks.linkOrderAttachmentMock,
  listCustomerOrders: apiMocks.listCustomerOrdersMock,
  listOrderAttachments: apiMocks.listOrderAttachmentsMock,
  listOrderEquipmentLines: apiMocks.listOrderEquipmentLinesMock,
  listOrderRequirementLines: apiMocks.listOrderRequirementLinesMock,
  listServiceCategoryOptions: apiMocks.listServiceCategoryOptionsMock,
  updateCustomerOrder: apiMocks.updateCustomerOrderMock,
  updateOrderEquipmentLine: apiMocks.updateOrderEquipmentLineMock,
  updateOrderRequirementLine: apiMocks.updateOrderRequirementLineMock,
}));

vi.mock('#/sicherplan-legacy/api/employeeAdmin', () => ({
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
  await wrapper.get('[data-testid="customer-new-plan-planning-entity"]').setValue('site-1');
  await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
  await nextTickFlush();

  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
}

async function advanceToEquipmentLines(wrapper: VueWrapper) {
  await advanceToOrderDetails(wrapper);
  await wrapper.get('[data-testid="customer-new-plan-order-mode-create-label"]').trigger('click');
  await nextTickFlush();
  await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-2000');
  await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Werkschutz Nord');
  await wrapper.get('[data-testid="customer-new-plan-order-requirement-type"]').setValue('requirement-type-1');
  await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
  await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
  await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
  await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
  await nextTickFlush();

  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
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
  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');
}

async function advanceToOrderDocuments(wrapper: VueWrapper) {
  await advanceToRequirementLines(wrapper);
  await saveRequirementLine(wrapper);
  await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
  await nextTickFlush();
  expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-documents');
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

describe('CustomerNewPlanWizardView EPIC 3', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
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
    stores.equipmentLinesByOrder = {};
    stores.requirementLinesByOrder = {};
    stores.attachmentsByOrder = {};
    stores.sites = [{ id: 'site-1', customer_id: 'customer-1', site_no: 'SITE-1', name: 'Werk Nord', tenant_id: 'tenant-1' }];
    stores.eventVenues = [{ id: 'venue-1', customer_id: 'customer-1', venue_no: 'VEN-1', name: 'Arena', tenant_id: 'tenant-1' }];
    stores.tradeFairs = [{ id: 'fair-1', customer_id: 'customer-1', fair_no: 'FAIR-1', name: 'Expo', tenant_id: 'tenant-1' }];
    stores.patrolRoutes = [{ id: 'route-1', customer_id: 'customer-1', route_no: 'ROU-1', name: 'Innenstadt', tenant_id: 'tenant-1' }];
    stores.requirementTypes = [{ id: 'requirement-type-1', customer_id: 'customer-1', code: 'REQ-1', label: 'Objektschutz', tenant_id: 'tenant-1' }];
    stores.equipmentItems = [{ id: 'equipment-item-1', customer_id: 'customer-1', code: 'EQ-1', label: 'Funkgerät', tenant_id: 'tenant-1' }];

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
    apiMocks.listServiceCategoryOptionsMock.mockResolvedValue(stores.serviceCategories);
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
          (row: any) => !filters?.customer_id || row.customer_id === filters.customer_id,
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

    apiMocks.listOrderAttachmentsMock.mockReset();
    apiMocks.listOrderAttachmentsMock.mockImplementation((_tenantId: string, orderId: string) => Promise.resolve(stores.attachmentsByOrder[orderId] ?? []));
    apiMocks.linkOrderAttachmentMock.mockReset();
    apiMocks.linkOrderAttachmentMock.mockImplementation((_tenantId: string, orderId: string, _token: string, payload: any) => {
      const doc = { id: payload.document_id, current_version_no: 1, status: 'active', tenant_id: 'tenant-1', title: payload.label || payload.document_id };
      stores.attachmentsByOrder[orderId] = [...(stores.attachmentsByOrder[orderId] ?? []), doc];
      return Promise.resolve(doc);
    });
    apiMocks.createOrderAttachmentMock.mockReset();
    apiMocks.createOrderAttachmentMock.mockImplementation((_tenantId: string, orderId: string, _token: string, payload: any) => {
      const doc = { id: 'uploaded-doc-1', current_version_no: 1, status: 'active', tenant_id: 'tenant-1', title: payload.title };
      stores.attachmentsByOrder[orderId] = [...(stores.attachmentsByOrder[orderId] ?? []), doc];
      return Promise.resolve(doc);
    });
  });

  afterEach(() => {
    while (mountedWrappers.length) {
      mountedWrappers.pop()?.unmount();
    }
    window.sessionStorage.clear();
  });

  it('runs through steps 1-5, persists canonical records, and updates earlier order data instead of creating duplicates', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    await advanceToEquipmentLines(wrapper);
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createCustomerOrderMock.mock.calls[0]?.[2]).toMatchObject({ customer_id: 'customer-1', order_no: 'ORD-2000' });
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');

    await wrapper.get('[data-testid="customer-new-plan-previous"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.updateCustomerOrderMock).toHaveBeenCalledTimes(1);

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
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');

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
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-order-document-id"]').setValue('document-1');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
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
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    stores.attachmentsByOrder['order-1'] = [
      { id: 'doc-1', current_version_no: 1, status: 'active', tenant_id: 'tenant-1', title: 'Bestandsdokument' },
    ];
    await wrapper.get('[data-testid="customer-new-plan-previous"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('uploads order documents on Next and refreshes attachments before continuing', async () => {
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

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(stores.attachmentsByOrder['order-1']).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('links existing order documents on Next and keeps attachments visible', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-document-id"]').setValue('document-42');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(stores.attachmentsByOrder['order-1']).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');

    await wrapper.get('[data-testid="customer-new-plan-previous"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-documents');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(stores.attachmentsByOrder['order-1']).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('blocks partial order-document drafts until cleared, then allows skipping', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDocuments(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-order-document-title"]').setValue('Unvollstandiger Entwurf');

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-documents');
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue');
    expect(wrapper.find('[data-testid="customer-new-plan-clear-order-document-draft"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-clear-order-document-draft"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('saves and updates equipment lines inline, blocks next for unsaved drafts, and clears persisted draft state', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToEquipmentLines(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(0);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.equipmentLineRequiredBeforeContinue');

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
    await wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').setValue('3');
    await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue('Primary radios');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.saveCurrentEquipmentLineBeforeContinue');
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(0);

    const equipmentDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'equipment-lines',
    );
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toContain('Primary radios');

    await wrapper.get('[data-testid="customer-new-plan-save-equipment-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.messages.equipmentLineSaved');
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toBeNull();
    expect(stores.equipmentLinesByOrder['order-1']).toHaveLength(1);
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-item"]').element as HTMLSelectElement).value).toBe('');
    expect(wrapper.find('[data-testid="customer-new-plan-save-equipment-line"]').exists()).toBe(true);

    await wrapper.get('.sp-customer-plan-wizard-step__list-row').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-editing"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-update-equipment-line"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').setValue('Updated radios');
    await wrapper.get('[data-testid="customer-new-plan-update-equipment-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.updateOrderEquipmentLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.messages.equipmentLineUpdated');
    expect(stores.equipmentLinesByOrder['order-1']?.[0]?.notes).toBe('Updated radios');
    expect(wrapper.find('[data-testid="customer-new-plan-save-equipment-line"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-equipment-item"]').setValue('equipment-item-1');
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
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');
  });

  it('saves and updates requirement lines inline, blocks next for unsaved drafts, and clears persisted draft state', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToRequirementLines(wrapper);

    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(0);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue');

    await wrapper.get('[data-testid="customer-new-plan-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-function-type"]').setValue('function-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-qualification-type"]').setValue('qualification-1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-min-qty"]').setValue('1');
    await wrapper.get('[data-testid="customer-new-plan-requirement-target-qty"]').setValue('2');
    await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue('Need supervisor');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.saveCurrentRequirementLineBeforeContinue');
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(0);

    const requirementDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'requirement-lines',
    );
    expect(window.sessionStorage.getItem(requirementDraftKey)).toContain('Need supervisor');

    await wrapper.get('[data-testid="customer-new-plan-save-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.messages.requirementLineSaved');
    expect(window.sessionStorage.getItem(requirementDraftKey)).toBeNull();
    expect(stores.requirementLinesByOrder['order-1']).toHaveLength(1);
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-type"]').element as HTMLSelectElement).value).toBe('');

    await wrapper.get('.sp-customer-plan-wizard-step__list-row').trigger('click');
    await nextTickFlush();
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-editing"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-update-requirement-line"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').setValue('Updated requirement');
    await wrapper.get('[data-testid="customer-new-plan-update-requirement-line"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.updateOrderRequirementLineMock).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.messages.requirementLineUpdated');
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
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-documents');
  });

  it('loads existing customer orders, hydrates a selected order, and persists order_id into route state', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Objektschutz RheinForum Koln - Nordtor Juli',
      notes: 'Existing order notes',
      security_concept_text: 'Existing concept',
    });
    const wrapper = mountComponent();
    await nextTickFlush();
    await advanceToOrderDetails(wrapper);

    expect(apiMocks.listCustomerOrdersMock).toHaveBeenCalledWith('tenant-1', 'token-1', expect.objectContaining({
      customer_id: 'customer-1',
      include_archived: false,
    }));
    expect(wrapper.find('[data-testid="customer-new-plan-order-mode-existing"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-order-row"]')).toHaveLength(1);

    await wrapper.get('[data-testid="customer-new-plan-existing-order-row"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledWith('tenant-1', 'order-existing-1', 'token-1');
    expect((wrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-EX-1');
    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Objektschutz RheinForum Koln - Nordtor Juli');
    expect((wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Existing concept');
    expect(wrapper.get('[data-testid="customer-new-plan-selected-order-summary"]').text()).toContain('ORD-EX-1');
    expect(routerReplaceMock).toHaveBeenCalledWith(expect.objectContaining({
      path: '/admin/customers/new-plan',
      query: expect.objectContaining({
        customer_id: 'customer-1',
        order_id: 'order-existing-1',
        step: 'order-details',
      }),
    }));
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.messages.existingOrderLoaded');
  });

  it('updates a selected existing order on Next without creating a duplicate and then reuses its downstream data', async () => {
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
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Existing title updated');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.updateCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.updateCustomerOrderMock.mock.calls[0]?.[1]).toBe('order-existing-1');
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
    expect(apiMocks.listOrderEquipmentLinesMock).toHaveBeenCalledWith('tenant-1', 'order-existing-1', 'token-1');
    expect(wrapper.text()).toContain('Funkgerät');
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
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.orderSelectionRequired');
    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(0);

    wrapper.unmount();

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

    await createWrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-NEW-2');
    await createWrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Create after existing mode');
    await createWrapper.get('[data-testid="customer-new-plan-order-requirement-type"]').setValue('requirement-type-1');
    await createWrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await createWrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
    await createWrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
    await createWrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

    expect(apiMocks.createCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(createWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
  });

  it('restores a selected existing order from route order_id and ignores stale create-new draft content', async () => {
    stores.orders['order-existing-1'] = makeOrder('order-existing-1', {
      order_no: 'ORD-EX-1',
      title: 'Hydrated existing order',
      security_concept_text: 'Hydrated concept',
    });
    routeState.query = {
      customer_id: 'customer-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      order_id: 'order-existing-1',
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
    expect((wrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-EX-1');
    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Hydrated existing order');
    expect((wrapper.get('[data-testid="customer-new-plan-order-security-concept"]').element as HTMLTextAreaElement).value).toBe('Hydrated concept');
    expect(wrapper.get('[data-testid="customer-new-plan-selected-order-summary"]').text()).toContain('ORD-EX-1');
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

    expect(restoredWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('equipment-lines');
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

    expect(restoredWrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('requirement-lines');
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
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'equipment-lines',
    );
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toContain('Customer one equipment draft');

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
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'requirement-lines',
    );
    expect(window.sessionStorage.getItem(requirementDraftKey)).toContain('Customer one requirement draft');

    routeState.query = {
      customer_id: 'customer-2',
    };
    await nextTickFlush();
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning');
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-item"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-type"]').exists()).toBe(false);
    expect(window.sessionStorage.getItem(equipmentDraftKey)).toContain('Customer one equipment draft');
    expect(window.sessionStorage.getItem(requirementDraftKey)).toContain('Customer one requirement draft');
  });

  it('supports create-new planning behavior in step 1 and derives the planning mode from the chosen family', async () => {
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

    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-REAL-KEY');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Real key draft');
    await nextTickFlush();

    const storageKeys = Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) || '');
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:_:_:order-details'))).toBe(false);
    expect(storageKeys.some((key) => key.includes('sicherplan.customerNewPlanWizardDraft:tenant-1:customer-1:site:site-1:order-details'))).toBe(true);
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
        path: '/admin/customers/new-plan',
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

  it('creates a new address inside the planning modal, refreshes options, and selects it', async () => {
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

  it('validates required address fields and keeps the planning modal state stable when address creation is canceled', async () => {
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
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.addressCreateValidation');
    expect(wrapper.find('[data-testid="customer-new-plan-planning-address-dialog"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-planning-address-street-line-1"]').setValue('Should be discarded');
    await wrapper.get('[data-testid="customer-new-plan-planning-address-cancel"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-address-dialog"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').element as HTMLInputElement).value).toBe('SITE-99');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').element as HTMLInputElement).value).toBe('Stable Modal Site');
  });

  it('writes the created address into the correct family-specific target field', async () => {
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

  it('shows map picking only for coordinate-backed families and applies the selected coordinates', async () => {
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

  it('keeps coordinates unchanged when the map picker is canceled and wires the localized load error text', async () => {
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

    expect(wrapper.find('[data-testid="customer-new-plan-location-picker-dialog"]').exists()).toBe(true);
    expect(wrapper.get('[data-testid="customer-new-plan-location-picker-load-error"]').text()).toBe(
      'sicherplan.customerPlansWizard.mapPicker.loadError',
    );
    await wrapper.get('[data-testid="customer-new-plan-location-picker-cancel"]').trigger('click');
    await nextTickFlush();

    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').element as HTMLInputElement).value)).toBe(50.111111);
    expect(Number((wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').element as HTMLInputElement).value)).toBe(7.222222);
  });

  it('submits only the canonical family-specific payload fields for site, trade fair, and patrol route', async () => {
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

  it('keeps the real planning create modal and typed values stable across focus-driven session refresh', async () => {
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
