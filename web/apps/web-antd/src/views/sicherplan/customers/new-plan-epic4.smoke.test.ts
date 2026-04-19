// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent } from 'vue';

import CustomerNewPlanStepContent from './new-plan-step-content.vue';
import { buildWizardDraftStorageKey } from './new-plan-wizard-drafts';
import type { CustomerNewPlanWizardState, CustomerNewPlanWizardStepId } from './new-plan-wizard.types';

const routerPushMock = vi.fn();

const apiMocks = vi.hoisted(() => ({
  createPlanningRecordAttachmentMock: vi.fn(),
  createPlanningRecordMock: vi.fn(),
  createShiftPlanMock: vi.fn(),
  createShiftSeriesExceptionMock: vi.fn(),
  createShiftSeriesMock: vi.fn(),
  createShiftTemplateMock: vi.fn(),
  generateShiftSeriesMock: vi.fn(),
  getCustomerOrderMock: vi.fn(),
  getPlanningRecordMock: vi.fn(),
  getShiftPlanMock: vi.fn(),
  getShiftSeriesMock: vi.fn(),
  linkPlanningRecordAttachmentMock: vi.fn(),
  listOrderAttachmentsMock: vi.fn(),
  listOrderEquipmentLinesMock: vi.fn(),
  listOrderRequirementLinesMock: vi.fn(),
  listPlanningRecordAttachmentsMock: vi.fn(),
  listPlanningSetupRecordsMock: vi.fn(),
  listTradeFairZonesMock: vi.fn(),
  listShiftPlansMock: vi.fn(),
  listShiftSeriesExceptionsMock: vi.fn(),
  listShiftSeriesMock: vi.fn(),
  listShiftTemplatesMock: vi.fn(),
  listShiftTypeOptionsMock: vi.fn(),
  updatePlanningRecordMock: vi.fn(),
  updateShiftPlanMock: vi.fn(),
  updateShiftSeriesExceptionMock: vi.fn(),
  updateShiftSeriesMock: vi.fn(),
}));

vi.mock('#/locales', () => ({
  $t: (key: string) => key,
}));

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: {},
  }),
  useRouter: () => ({
    push: routerPushMock,
  }),
}));

vi.mock('#/sicherplan-legacy/api/planningAdmin', () => ({
  createPlanningRecord: vi.fn(),
  listPlanningRecords: apiMocks.listPlanningSetupRecordsMock,
  listTradeFairZones: apiMocks.listTradeFairZonesMock,
}));

vi.mock('#/sicherplan-legacy/api/employeeAdmin', () => ({
  listFunctionTypes: vi.fn().mockResolvedValue([]),
  listQualificationTypes: vi.fn().mockResolvedValue([]),
}));

vi.mock('#/sicherplan-legacy/api/planningOrders', () => ({
  createPlanningRecord: apiMocks.createPlanningRecordMock,
  createPlanningRecordAttachment: apiMocks.createPlanningRecordAttachmentMock,
  createCustomerOrder: vi.fn(),
  createOrderAttachment: vi.fn(),
  createOrderEquipmentLine: vi.fn(),
  createOrderRequirementLine: vi.fn(),
  getCustomerOrder: apiMocks.getCustomerOrderMock,
  getPlanningRecord: apiMocks.getPlanningRecordMock,
  linkPlanningRecordAttachment: apiMocks.linkPlanningRecordAttachmentMock,
  linkOrderAttachment: vi.fn(),
  listOrderAttachments: apiMocks.listOrderAttachmentsMock,
  listOrderEquipmentLines: apiMocks.listOrderEquipmentLinesMock,
  listOrderRequirementLines: apiMocks.listOrderRequirementLinesMock,
  listPlanningRecordAttachments: apiMocks.listPlanningRecordAttachmentsMock,
  listServiceCategoryOptions: vi.fn().mockResolvedValue([]),
  updatePlanningRecord: apiMocks.updatePlanningRecordMock,
  updateCustomerOrder: vi.fn(),
  updateOrderEquipmentLine: vi.fn(),
  updateOrderRequirementLine: vi.fn(),
}));

vi.mock('#/sicherplan-legacy/api/planningShifts', () => ({
  createShiftPlan: apiMocks.createShiftPlanMock,
  createShiftSeries: apiMocks.createShiftSeriesMock,
  createShiftSeriesException: apiMocks.createShiftSeriesExceptionMock,
  createShiftTemplate: apiMocks.createShiftTemplateMock,
  generateShiftSeries: apiMocks.generateShiftSeriesMock,
  getShiftPlan: apiMocks.getShiftPlanMock,
  getShiftSeries: apiMocks.getShiftSeriesMock,
  listShiftPlans: apiMocks.listShiftPlansMock,
  listShiftSeries: apiMocks.listShiftSeriesMock,
  listShiftSeriesExceptions: apiMocks.listShiftSeriesExceptionsMock,
  listShiftTemplates: apiMocks.listShiftTemplatesMock,
  listShiftTypeOptions: apiMocks.listShiftTypeOptionsMock,
  updateShiftPlan: apiMocks.updateShiftPlanMock,
  updateShiftSeries: apiMocks.updateShiftSeriesMock,
  updateShiftSeriesException: apiMocks.updateShiftSeriesExceptionMock,
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

function buildOrder(overrides: Record<string, unknown> = {}) {
  return {
    id: 'order-1',
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

function buildPlanningRecord(overrides: Record<string, unknown> = {}) {
  return {
    id: 'record-1',
    tenant_id: 'tenant-1',
    order_id: 'order-1',
    parent_planning_record_id: null,
    dispatcher_user_id: null,
    planning_mode_code: 'site',
    name: 'Werk Nord Sommer',
    planning_from: '2026-06-01',
    planning_to: '2026-06-10',
    release_state: 'draft',
    released_at: null,
    created_at: '2026-04-01T08:00:00Z',
    status: 'active',
    version_no: 1,
    released_by_user_id: null,
    notes: null,
    site_detail: { site_id: 'site-1', watchbook_scope_note: null },
    attachments: [],
    updated_at: '2026-04-01T08:00:00Z',
    archived_at: null,
    ...overrides,
  };
}

function buildShiftPlan(overrides: Record<string, unknown> = {}) {
  return {
    id: 'plan-1',
    tenant_id: 'tenant-1',
    planning_record_id: 'record-1',
    name: 'Werk Nord / Schichtplan',
    workforce_scope_code: 'internal',
    planning_from: '2026-06-01',
    planning_to: '2026-06-10',
    status: 'active',
    version_no: 1,
    remarks: null,
    ...overrides,
  };
}

function buildSeries(overrides: Record<string, unknown> = {}) {
  return {
    id: 'series-1',
    tenant_id: 'tenant-1',
    shift_plan_id: 'plan-1',
    shift_template_id: 'template-1',
    label: 'Tagdienst',
    recurrence_code: 'daily',
    interval_count: 1,
    weekday_mask: '1111100',
    timezone: 'Europe/Berlin',
    date_from: '2026-06-01',
    date_to: '2026-06-10',
    release_state: 'draft',
    customer_visible_flag: false,
    subcontractor_visible_flag: false,
    stealth_mode_flag: false,
    status: 'active',
    version_no: 1,
    default_break_minutes: 30,
    shift_type_code: 'day',
    meeting_point: null,
    location_text: null,
    notes: null,
    exceptions: [],
    ...overrides,
  };
}

function baseWizardState(): CustomerNewPlanWizardState {
  return {
    current_step: 'planning-record-overview',
    customer_id: 'customer-1',
    order_id: 'order-1',
    planning_entity_id: 'site-1',
    planning_entity_type: 'site',
    planning_mode_code: 'site',
    planning_record_id: '',
    shift_plan_id: '',
    series_id: '',
    step_state: {
      'order-details': { completed: true, dirty: false, error: '', loading: false },
      'equipment-lines': { completed: true, dirty: false, error: '', loading: false },
      'requirement-lines': { completed: true, dirty: false, error: '', loading: false },
      'order-documents': { completed: true, dirty: false, error: '', loading: false },
      'planning-record-overview': { completed: false, dirty: false, error: '', loading: false },
      'planning-record-documents': { completed: false, dirty: false, error: '', loading: false },
      'shift-plan': { completed: false, dirty: false, error: '', loading: false },
      'series-exceptions': { completed: false, dirty: false, error: '', loading: false },
    },
  };
}

function mountStep(stepId: CustomerNewPlanWizardStepId, wizardOverrides: Partial<CustomerNewPlanWizardState> = {}) {
  return mount(CustomerNewPlanStepContent, {
    props: {
      accessToken: 'token-1',
      currentStepId: stepId,
      customer: {
        id: 'customer-1',
        name: 'Alpha Security',
        customer_number: 'CU-1000',
      },
      tenantId: 'tenant-1',
      wizardState: {
        ...baseWizardState(),
        ...wizardOverrides,
      },
    },
  });
}

function mountStepWithProps(
  stepId: CustomerNewPlanWizardStepId,
  options: {
    accessToken?: string;
    tenantId?: string;
    wizardOverrides?: Partial<CustomerNewPlanWizardState>;
  } = {},
) {
  return mount(CustomerNewPlanStepContent, {
    props: {
      accessToken: options.accessToken ?? 'token-1',
      currentStepId: stepId,
      customer: {
        id: 'customer-1',
        name: 'Alpha Security',
        customer_number: 'CU-1000',
      },
      tenantId: options.tenantId ?? 'tenant-1',
      wizardState: {
        ...baseWizardState(),
        ...(options.wizardOverrides ?? {}),
      },
    },
  });
}

describe('CustomerNewPlanStepContent EPIC 4', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    routerPushMock.mockReset();
    apiMocks.createPlanningRecordMock.mockReset();
    apiMocks.createPlanningRecordAttachmentMock.mockReset();
    apiMocks.createShiftPlanMock.mockReset();
    apiMocks.createShiftSeriesExceptionMock.mockReset();
    apiMocks.createShiftSeriesMock.mockReset();
    apiMocks.createShiftTemplateMock.mockReset();
    apiMocks.generateShiftSeriesMock.mockReset();
    apiMocks.getCustomerOrderMock.mockReset();
    apiMocks.getPlanningRecordMock.mockReset();
    apiMocks.getShiftPlanMock.mockReset();
    apiMocks.getShiftSeriesMock.mockReset();
    apiMocks.linkPlanningRecordAttachmentMock.mockReset();
    apiMocks.listOrderAttachmentsMock.mockReset();
    apiMocks.listOrderEquipmentLinesMock.mockReset();
    apiMocks.listOrderRequirementLinesMock.mockReset();
    apiMocks.listPlanningRecordAttachmentsMock.mockReset();
    apiMocks.listPlanningSetupRecordsMock.mockReset();
    apiMocks.listTradeFairZonesMock.mockReset();
    apiMocks.listShiftPlansMock.mockReset();
    apiMocks.listShiftSeriesExceptionsMock.mockReset();
    apiMocks.listShiftSeriesMock.mockReset();
    apiMocks.listShiftTemplatesMock.mockReset();
    apiMocks.listShiftTypeOptionsMock.mockReset();
    apiMocks.updatePlanningRecordMock.mockReset();
    apiMocks.updateShiftPlanMock.mockReset();
    apiMocks.updateShiftSeriesExceptionMock.mockReset();
    apiMocks.updateShiftSeriesMock.mockReset();

    apiMocks.getCustomerOrderMock.mockResolvedValue(buildOrder());
    apiMocks.listOrderEquipmentLinesMock.mockResolvedValue([]);
    apiMocks.listOrderRequirementLinesMock.mockResolvedValue([]);
    apiMocks.listOrderAttachmentsMock.mockResolvedValue([]);
    apiMocks.listPlanningSetupRecordsMock.mockImplementation((entityKey: string) => {
      const map: Record<string, unknown[]> = {
        event_venue: [{ id: 'venue-1', customer_id: 'customer-1', venue_no: 'VEN-1', name: 'Arena', tenant_id: 'tenant-1', status: 'active', version_no: 1 }],
        patrol_route: [{ id: 'route-1', customer_id: 'customer-1', route_no: 'ROU-1', name: 'Innenstadt', tenant_id: 'tenant-1', status: 'active', version_no: 1 }],
        site: [{ id: 'site-1', customer_id: 'customer-1', site_no: 'SITE-1', name: 'Werk Nord', tenant_id: 'tenant-1', status: 'active', version_no: 1 }],
        trade_fair: [{ id: 'fair-1', customer_id: 'customer-1', fair_no: 'FAIR-1', name: 'Expo', tenant_id: 'tenant-1', status: 'active', version_no: 1 }],
      };
      return Promise.resolve(map[entityKey] ?? []);
    });
    apiMocks.listTradeFairZonesMock.mockResolvedValue([
      {
        id: 'zone-1',
        tenant_id: 'tenant-1',
        trade_fair_id: 'fair-1',
        zone_type_code: 'hall',
        zone_code: 'H2-A',
        label: 'Halle 2 A',
        notes: null,
        status: 'active',
        version_no: 1,
        archived_at: null,
      },
    ]);
    apiMocks.listPlanningRecordAttachmentsMock.mockResolvedValue([]);
    apiMocks.listShiftPlansMock.mockResolvedValue([]);
    apiMocks.listShiftTemplatesMock.mockResolvedValue([{ id: 'template-1', tenant_id: 'tenant-1', code: 'TPL-1', label: 'Tagdienst Vorlage', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'day', status: 'active', version_no: 1 }]);
    apiMocks.listShiftTypeOptionsMock.mockResolvedValue([{ code: 'day', label: 'Day shift' }]);
    apiMocks.listShiftSeriesMock.mockResolvedValue([]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.getPlanningRecordMock.mockResolvedValue(buildPlanningRecord());
    apiMocks.getShiftPlanMock.mockResolvedValue(buildShiftPlan());
    apiMocks.getShiftSeriesMock.mockResolvedValue(buildSeries());
  });

  it('creates or updates the planning record and keeps step-1 mode alignment', async () => {
    const wrapper = mountStep('planning-record-overview');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Werk Nord Sommer');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').setValue('2026-06-10');

    apiMocks.createPlanningRecordMock.mockResolvedValue(buildPlanningRecord());

    const created = await (wrapper.vm as any).submitCurrentStep();

    expect(created).toBe(true);
    expect(apiMocks.createPlanningRecordMock).toHaveBeenCalledWith(
      'tenant-1',
      'token-1',
      expect.objectContaining({
        order_id: 'order-1',
        planning_mode_code: 'site',
        site_detail: {
          site_id: 'site-1',
          watchbook_scope_note: null,
        },
      }),
    );
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toEqual({ planning_record_id: 'record-1' });

    await wrapper.setProps({
      wizardState: {
        ...baseWizardState(),
        planning_record_id: 'record-1',
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
      },
    });
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Werk Nord Herbst');
    apiMocks.updatePlanningRecordMock.mockResolvedValue(buildPlanningRecord({ name: 'Werk Nord Herbst', version_no: 2 }));

    const updated = await (wrapper.vm as any).submitCurrentStep();

    expect(updated).toBe(true);
    expect(apiMocks.updatePlanningRecordMock).toHaveBeenCalledWith(
      'tenant-1',
      'record-1',
      'token-1',
      expect.objectContaining({
        planning_mode_code: 'site',
        site_detail: {
          site_id: 'site-1',
          watchbook_scope_note: null,
        },
      }),
    );
  });

  it('loads trade fair zones into a selector instead of a raw UUID field', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: 'fair-1',
      planning_entity_type: 'trade_fair',
      planning_mode_code: 'trade_fair',
    });
    await flushPromises();

    expect(apiMocks.listTradeFairZonesMock).toHaveBeenCalledWith('tenant-1', 'fair-1', 'token-1');
    const zoneSelect = wrapper.get('[data-testid="customer-new-plan-trade-fair-zone"]');
    expect(zoneSelect.findAll('option')).toHaveLength(2);
    expect(zoneSelect.text()).toContain('H2-A');
  });

  it('restores an unsaved planning-record draft after remount', async () => {
    const wrapper = mountStep('planning-record-overview', {
      current_step: 'planning-record-overview',
      order_id: 'order-1',
      planning_record_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Draft Planning Record');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').setValue('2026-06-03');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').setValue('2026-06-12');
    await flushPromises();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'planning-record-overview',
    );
    expect(window.sessionStorage.getItem(draftKey)).toContain('Draft Planning Record');

    wrapper.unmount();

    const restoredWrapper = mountStep('planning-record-overview', {
      current_step: 'planning-record-overview',
      order_id: 'order-1',
      planning_record_id: '',
    });
    await flushPromises();

    expect((restoredWrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe('Draft Planning Record');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-planning-record-from"]').element as HTMLInputElement).value).toBe('2026-06-03');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-planning-record-to"]').element as HTMLInputElement).value).toBe('2026-06-12');
    expect(restoredWrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');
  });

  it('links planning-record documents through the canonical planning-record document path', async () => {
    const wrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-record-document-id"]').setValue('document-1');
    apiMocks.linkPlanningRecordAttachmentMock.mockResolvedValue({
      id: 'doc-row-1',
      tenant_id: 'tenant-1',
      title: 'Safety concept',
      current_version_no: 1,
      status: 'active',
    });
    apiMocks.listPlanningRecordAttachmentsMock.mockResolvedValue([
      { id: 'doc-row-1', tenant_id: 'tenant-1', title: 'Safety concept', current_version_no: 1, status: 'active' },
    ]);

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(true);
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledWith(
      'tenant-1',
      'record-1',
      'token-1',
      expect.objectContaining({
        document_id: 'document-1',
      }),
    );
  });

  it('allows skipping Planning Record Documents when the draft is empty or attachments already exist', async () => {
    const emptyWrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    const emptySaved = await (emptyWrapper.vm as any).submitCurrentStep();

    expect(emptySaved).toBe(true);
    expect(apiMocks.createPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);

    apiMocks.listPlanningRecordAttachmentsMock.mockResolvedValueOnce([
      { id: 'doc-row-existing', tenant_id: 'tenant-1', title: 'Existing planning doc', current_version_no: 1, status: 'active' },
    ]);
    const existingWrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    const existingSaved = await (existingWrapper.vm as any).submitCurrentStep();

    expect(existingSaved).toBe(true);
    expect(apiMocks.createPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);
  });

  it('uploads planning-record documents and blocks partial planning document drafts until cleared', async () => {
    const uploadWrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    const uploadState = (uploadWrapper.vm as any).$?.setupState;
    uploadState.planningRecordAttachmentDraft.title = 'Planning brief';
    uploadState.planningRecordAttachmentDraft.file_name = 'brief.pdf';
    uploadState.planningRecordAttachmentDraft.content_type = 'application/pdf';
    uploadState.planningRecordAttachmentDraft.content_base64 = 'base64-planning';
    await flushPromises();

    const uploaded = await (uploadWrapper.vm as any).submitCurrentStep();

    expect(uploaded).toBe(true);
    expect(apiMocks.createPlanningRecordAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);

    const partialWrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    const partialState = (partialWrapper.vm as any).$?.setupState;
    partialState.planningRecordAttachmentDraft.title = 'Incomplete planning draft';
    await flushPromises();

    const blocked = await (partialWrapper.vm as any).submitCurrentStep();

    expect(blocked).toBe(false);
    expect(partialWrapper.text()).toContain(
      'sicherplan.customerPlansWizard.errors.completeCurrentPlanningDocumentDraftBeforeContinue',
    );
    expect(partialWrapper.find('[data-testid="customer-new-plan-clear-planning-document-draft"]').exists()).toBe(true);

    await partialWrapper.get('[data-testid="customer-new-plan-clear-planning-document-draft"]').trigger('click');
    await flushPromises();

    const cleared = await (partialWrapper.vm as any).submitCurrentStep();
    expect(cleared).toBe(true);
  });

  it('creates the shift plan and emits the canonical shift_plan_id', async () => {
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').setValue('Werk Nord / Schichtplan');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').setValue('2026-06-10');
    apiMocks.createShiftPlanMock.mockResolvedValue(buildShiftPlan());

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(true);
    expect(apiMocks.createShiftPlanMock).toHaveBeenCalledWith(
      'tenant-1',
      'token-1',
      expect.objectContaining({
        planning_record_id: 'record-1',
        name: 'Werk Nord / Schichtplan',
      }),
    );
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toEqual({ shift_plan_id: 'plan-1' });
  });

  it('restores an unsaved shift-plan draft after remount', async () => {
    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').setValue('Draft Shift Plan');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-from"]').setValue('2026-06-02');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').setValue('2026-06-11');
    await flushPromises();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'shift-plan',
    );
    expect(window.sessionStorage.getItem(draftKey)).toContain('Draft Shift Plan');

    wrapper.unmount();

    const restoredWrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: '',
    });
    await flushPromises();

    expect((restoredWrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toBe('Draft Shift Plan');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-shift-plan-from"]').element as HTMLInputElement).value).toBe('2026-06-02');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').element as HTMLInputElement).value).toBe('2026-06-11');
    expect(restoredWrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');
  });

  it('ignores malformed session storage draft values safely', async () => {
    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'shift-plan',
    );
    window.sessionStorage.setItem(draftKey, '{bad-json');

    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: '',
    });
    await flushPromises();

    const persisted = window.sessionStorage.getItem(draftKey);
    expect(persisted === null || !persisted.includes('{bad-json')).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).not.toBe('{bad-json');
  });

  it('does not hydrate a draft stored under another tenant context', async () => {
    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'shift-plan',
    );
    window.sessionStorage.setItem(
      draftKey,
      JSON.stringify({
        name: 'Tenant One Draft',
        planning_from: '2026-06-01',
        planning_to: '2026-06-10',
        remarks: '',
        workforce_scope_code: 'internal',
      }),
    );

    const wrapper = mountStepWithProps('shift-plan', {
      tenantId: 'tenant-2',
      wizardOverrides: {
        current_step: 'shift-plan',
        planning_record_id: 'record-1',
        shift_plan_id: '',
      },
    });
    await flushPromises();

    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).not.toBe('Tenant One Draft');
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);
  });

  it('does not persist raw attachment base64 in session storage', async () => {
    const wrapper = mountStep('planning-record-documents', {
      current_step: 'planning-record-documents',
      planning_record_id: 'record-1',
    });
    await flushPromises();

    const setupState = (wrapper.vm as any).$.setupState;
    setupState.planningRecordAttachmentDraft.title = 'Safety concept';
    setupState.planningRecordAttachmentDraft.file_name = 'safety.pdf';
    setupState.planningRecordAttachmentDraft.content_type = 'application/pdf';
    setupState.planningRecordAttachmentDraft.content_base64 = 'very-large-base64';
    await flushPromises();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'planning-record-documents',
    );
    const persisted = JSON.parse(window.sessionStorage.getItem(draftKey) || '{}');

    expect(persisted).toMatchObject({
      attachment: {
        content_type: 'application/pdf',
        file_name: 'safety.pdf',
        file_needs_reselect: true,
        title: 'Safety concept',
      },
    });
    expect(JSON.stringify(persisted)).not.toContain('very-large-base64');
  });

  it('updates existing shift-plan and series records instead of creating duplicates on revisit', async () => {
    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').setValue('Werk Nord / Aktualisiert');
    apiMocks.updateShiftPlanMock.mockResolvedValue(buildShiftPlan({ name: 'Werk Nord / Aktualisiert', version_no: 2 }));

    const shiftPlanSaved = await (wrapper.vm as any).submitCurrentStep();

    expect(shiftPlanSaved).toBe(true);
    expect(apiMocks.updateShiftPlanMock).toHaveBeenCalledWith(
      'tenant-1',
      'plan-1',
      'token-1',
      expect.objectContaining({
        name: 'Werk Nord / Aktualisiert',
      }),
    );
    expect(apiMocks.createShiftPlanMock).not.toHaveBeenCalled();

    await wrapper.setProps({
      currentStepId: 'series-exceptions',
      wizardState: {
        ...baseWizardState(),
        current_step: 'series-exceptions',
        planning_record_id: 'record-1',
        shift_plan_id: 'plan-1',
        series_id: 'series-1',
      },
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Tagdienst aktualisiert');
    apiMocks.updateShiftSeriesMock.mockResolvedValue(buildSeries({ label: 'Tagdienst aktualisiert', version_no: 2 }));
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ label: 'Tagdienst aktualisiert', version_no: 2 })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-06-01',
        starts_at: '2026-06-01T08:00:00Z',
        ends_at: '2026-06-01T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'series',
        status: 'active',
        version_no: 1,
      },
    ]);

    const seriesSaved = await (wrapper.vm as any).submitCurrentStep();

    expect(seriesSaved).toBe(true);
    expect(apiMocks.updateShiftSeriesMock).toHaveBeenCalledWith(
      'tenant-1',
      'series-1',
      'token-1',
      expect.objectContaining({
        label: 'Tagdienst aktualisiert',
      }),
    );
    expect(apiMocks.createShiftSeriesMock).not.toHaveBeenCalled();
  });

  it('creates a new template, generates the series, and redirects into canonical staffing coverage', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-new-template"]').trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-new-template-code"]').setValue('TPL-2');
    await wrapper.get('[data-testid="customer-new-plan-new-template-label"]').setValue('Nachtdienst');
    await wrapper.find('.modal-stub select').setValue('day');
    apiMocks.createShiftTemplateMock.mockResolvedValue({
      id: 'template-2',
      tenant_id: 'tenant-1',
      code: 'TPL-2',
      label: 'Nachtdienst',
      local_start_time: '08:00',
      local_end_time: '16:00',
      default_break_minutes: 30,
      shift_type_code: 'day',
      meeting_point: null,
      location_text: null,
      notes: null,
      status: 'active',
      version_no: 1,
    });
    apiMocks.listShiftTemplatesMock.mockResolvedValue([
      { id: 'template-1', tenant_id: 'tenant-1', code: 'TPL-1', label: 'Tagdienst Vorlage', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'day', status: 'active', version_no: 1 },
      { id: 'template-2', tenant_id: 'tenant-1', code: 'TPL-2', label: 'Nachtdienst', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'day', status: 'active', version_no: 1 },
    ]);
    await wrapper.get('[data-testid="modal-ok"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Nachtdienst Juni');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-2');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-06-03');

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries({ shift_template_id: 'template-2', label: 'Nachtdienst Juni' }));
    apiMocks.createShiftSeriesExceptionMock.mockResolvedValue({
      id: 'exception-1',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-06-03',
      action_code: 'skip',
      version_no: 1,
    });
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ shift_template_id: 'template-2', label: 'Nachtdienst Juni' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([
      { id: 'exception-1', tenant_id: 'tenant-1', shift_series_id: 'series-1', exception_date: '2026-06-03', action_code: 'skip', version_no: 1 },
    ]);
    apiMocks.generateShiftSeriesMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-06-01',
        starts_at: '2026-06-01T08:00:00Z',
        ends_at: '2026-06-01T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'series',
        status: 'active',
        version_no: 1,
      },
    ]);

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(true);
    expect(apiMocks.createShiftSeriesMock).toHaveBeenCalledWith(
      'tenant-1',
      'plan-1',
      'token-1',
      expect.objectContaining({
        label: 'Nachtdienst Juni',
        shift_template_id: 'template-2',
      }),
    );
    expect(apiMocks.createShiftSeriesExceptionMock).toHaveBeenCalled();
    expect(apiMocks.generateShiftSeriesMock).toHaveBeenCalledWith('tenant-1', 'series-1', 'token-1', {});
    expect(routerPushMock).toHaveBeenCalledWith(
      '/admin/planning-staffing?date_from=2026-06-01T00%3A00&date_to=2026-06-02T00%3A00&planning_record_id=record-1&shift_id=shift-1',
    );
    const redirectTarget = routerPushMock.mock.calls.at(-1)?.[0];
    const redirectUrl = new URL(`https://example.test${redirectTarget}`);
    expect(redirectUrl.pathname).toBe('/admin/planning-staffing');
    expect(redirectUrl.searchParams.get('planning_record_id')).toBe('record-1');
    expect(redirectUrl.searchParams.get('date_from')).toBe('2026-06-01T00:00');
    expect(redirectUrl.searchParams.get('date_to')).toBe('2026-06-02T00:00');
    expect(redirectUrl.searchParams.get('shift_id')).toBe('shift-1');
    expect(redirectUrl.searchParams.get('planning_mode_code')).toBeNull();
    expect([...redirectUrl.searchParams.keys()].sort()).toEqual([
      'date_from',
      'date_to',
      'planning_record_id',
      'shift_id',
    ]);
  });

  it('keeps the user on the final step with clear feedback when series generation fails', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Nachtdienst Juni');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries());
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries()]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockRejectedValue(new Error('generate failed'));

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(routerPushMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.seriesGenerateFailed');
  });
});
