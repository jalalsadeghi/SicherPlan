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

function buildCustomer() {
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

    await wrapper.get('[data-testid="customer-new-plan-planning-entity"]').setValue('site-1');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');

    await wrapper.get('[data-testid="customer-new-plan-order-no"]').setValue('ORD-2000');
    await wrapper.get('[data-testid="customer-new-plan-order-title"]').setValue('Werkschutz Nord');
    await wrapper.get('[data-testid="customer-new-plan-order-requirement-type"]').setValue('requirement-type-1');
    await wrapper.get('[data-testid="customer-new-plan-order-service-category"]').setValue('guarding');
    await wrapper.get('[data-testid="customer-new-plan-order-service-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-order-service-to"]').setValue('2026-06-10');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();

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
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenCalledWith('equipment_item', 'tenant-1', 'token-1', expect.any(Object));
    expect(apiMocks.createPlanningSetupRecordMock.mock.calls.find((call) => call[0] === 'equipment_item')?.[3]).not.toHaveProperty('customer_id');
    expect(apiMocks.createOrderEquipmentLineMock).toHaveBeenCalledTimes(1);

    await wrapper.get('[data-testid="customer-new-plan-new-requirement"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-new-requirement-code"]').setValue('REQ-2');
    await wrapper.get('[data-testid="customer-new-plan-new-requirement-label"]').setValue('Werkschutz');
    await wrapper.get('[data-testid="modal-ok"]').trigger('click');
    await nextTickFlush();
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenCalledWith('requirement_type', 'tenant-1', 'token-1', expect.any(Object));
    expect(apiMocks.createPlanningSetupRecordMock.mock.calls.find((call) => call[0] === 'requirement_type')?.[3]).not.toHaveProperty('customer_id');
    expect(apiMocks.createOrderRequirementLineMock).toHaveBeenCalledTimes(1);

    await wrapper.get('[data-testid="customer-new-plan-order-document-id"]').setValue('document-1');
    await wrapper.get('[data-testid="customer-new-plan-next"]').trigger('click');
    await nextTickFlush();
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(1);
    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('planning-record-overview');
  });

  it('supports create-new planning behavior in step 1 and derives the planning mode from the chosen family', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-family"]').setValue('event_venue');
    await nextTickFlush();
    const radios = wrapper.findAll('input[type="radio"]');
    await radios[1]!.setValue(true);
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
    await nextTickFlush();

    authStoreState.effectiveAccessToken = 'token-2';
    authStoreState.accessToken = 'token-2';
    await nextTickFlush();

    expect(wrapper.get('[data-testid="customer-new-plan-step-content"]').attributes('data-step-id')).toBe('order-details');
    expect((wrapper.get('[data-testid="customer-new-plan-order-no"]').element as HTMLInputElement).value).toBe('ORD-REFRESH');
    expect((wrapper.get('[data-testid="customer-new-plan-order-title"]').element as HTMLInputElement).value).toBe('Auth Refresh Draft');
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
    const radios = wrapper.findAll('input[type="radio"]');
    await radios[1]!.setValue(true);
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

    const radios = wrapper.findAll('input[type="radio"]');
    await radios[1]!.setValue(true);
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
      const radios = wrapper.findAll('input[type="radio"]');
      await radios[1]!.setValue(true);
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

    const radios = wrapper.findAll('input[type="radio"]');
    await radios[1]!.setValue(true);

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
    const patrolRadios = wrapper.findAll('input[type="radio"]');
    await patrolRadios[1]!.setValue(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-address-action"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-pick-on-map"]').exists()).toBe(false);
  });

  it('keeps coordinates unchanged when the map picker is canceled and wires the localized load error text', async () => {
    const wrapper = mountComponent();
    await nextTickFlush();

    const radios = wrapper.findAll('input[type="radio"]');
    await radios[1]!.setValue(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-create"]').trigger('click');
    await nextTickFlush();

    await wrapper.get('[data-testid="customer-new-plan-planning-create-latitude"]').setValue('50.111111');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-longitude"]').setValue('7.222222');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-pick-on-map"]').trigger('click');
    await nextTickFlush();

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
        const radios = wrapper.findAll('input[type="radio"]');
        await radios[1]!.setValue(true);
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
        const radios = wrapper.findAll('input[type="radio"]');
        await radios[1]!.setValue(true);
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
        const radios = wrapper.findAll('input[type="radio"]');
        await radios[1]!.setValue(true);
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

    const radios = wrapper.findAll('input[type="radio"]');
    await radios[1]!.setValue(true);
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
    expect((wrapper.findAll('input[type="radio"]')[1]!.element as HTMLInputElement).checked).toBe(true);
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
