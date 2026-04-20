// @vitest-environment happy-dom

import { readFileSync } from 'node:fs';

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent } from 'vue';

import CustomerNewPlanStepContent from './new-plan-step-content.vue';
import { buildWizardDraftStorageKey } from './new-plan-wizard-drafts';
import type { CustomerNewPlanWizardState, CustomerNewPlanWizardStepId } from './new-plan-wizard.types';

const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
const planningShiftsApiErrorExports = vi.hoisted(() => {
  class PlanningShiftsApiError extends Error {
    status: number;
    messageKey: string;
    details: Record<string, unknown>;

    constructor(status: number, payload: { message_key: string; details: Record<string, unknown> }) {
      super(payload.message_key);
      this.status = status;
      this.messageKey = payload.message_key;
      this.details = payload.details;
    }
  }

  return { PlanningShiftsApiError };
});

const apiMocks = vi.hoisted(() => ({
  createPlanningSetupRecordMock: vi.fn(),
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
  getShiftTemplateMock: vi.fn(),
  linkPlanningRecordAttachmentMock: vi.fn(),
  listOrderAttachmentsMock: vi.fn(),
  listOrderEquipmentLinesMock: vi.fn(),
  listOrderRequirementLinesMock: vi.fn(),
  listPlanningRecordsMock: vi.fn(),
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
    replace: routerReplaceMock,
  }),
}));

vi.mock('#/sicherplan-legacy/api/planningAdmin', () => ({
  createPlanningRecord: apiMocks.createPlanningSetupRecordMock,
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
  listPlanningRecords: apiMocks.listPlanningRecordsMock,
  listPlanningRecordAttachments: apiMocks.listPlanningRecordAttachmentsMock,
  listServiceCategoryOptions: vi.fn().mockResolvedValue([]),
  updatePlanningRecord: apiMocks.updatePlanningRecordMock,
  updateCustomerOrder: vi.fn(),
  updateOrderEquipmentLine: vi.fn(),
  updateOrderRequirementLine: vi.fn(),
}));

vi.mock('#/sicherplan-legacy/api/planningShifts', () => ({
  PlanningShiftsApiError: planningShiftsApiErrorExports.PlanningShiftsApiError,
  createShiftPlan: apiMocks.createShiftPlanMock,
  createShiftSeries: apiMocks.createShiftSeriesMock,
  createShiftSeriesException: apiMocks.createShiftSeriesExceptionMock,
  createShiftTemplate: apiMocks.createShiftTemplateMock,
  generateShiftSeries: apiMocks.generateShiftSeriesMock,
  getShiftPlan: apiMocks.getShiftPlanMock,
  getShiftSeries: apiMocks.getShiftSeriesMock,
  getShiftTemplate: apiMocks.getShiftTemplateMock,
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

function buildPlanningRecordDraftKey(planningEntityId: string, planningEntityType: string) {
  return buildWizardDraftStorageKey(
    {
      customerId: 'customer-1',
      planningEntityId,
      planningEntityType,
      tenantId: 'tenant-1',
    },
    'planning-record-overview',
  );
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

function countWeeklyOccurrences(dateFrom: string, dateTo: string, weekdayMask: string) {
  const start = new Date(`${dateFrom}T00:00:00Z`);
  const end = new Date(`${dateTo}T00:00:00Z`);
  const included: string[] = [];
  const cursor = new Date(start);
  while (cursor <= end) {
    const weekdayIndex = (cursor.getUTCDay() + 6) % 7;
    if (weekdayMask[weekdayIndex] === '1') {
      included.push(cursor.toISOString().slice(0, 10));
    }
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return included;
}

const SERIES_WEEKDAY_IDS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

async function setSeriesWeeklyMask(wrapper: ReturnType<typeof mount>, weekdayMask: string) {
  const recurrenceSelect = wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]');
  if ((recurrenceSelect.element as HTMLSelectElement).value !== 'weekly') {
    await recurrenceSelect.setValue('weekly');
    await flushPromises();
  }
  for (const [index, weekdayId] of SERIES_WEEKDAY_IDS.entries()) {
    const chip = wrapper.get(`[data-testid="customer-new-plan-series-weekday-chip-${weekdayId}"]`);
    const isSelected = chip.attributes('aria-pressed') === 'true';
    const shouldBeSelected = weekdayMask[index] === '1';
    if (isSelected !== shouldBeSelected) {
      await chip.trigger('click');
    }
  }
  await flushPromises();
}

function seriesWeekdayChip(wrapper: ReturnType<typeof mount>, weekdayId: (typeof SERIES_WEEKDAY_IDS)[number]) {
  return wrapper.get(`[data-testid="customer-new-plan-series-weekday-chip-${weekdayId}"]`);
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
    routerReplaceMock.mockReset();
    apiMocks.createPlanningRecordMock.mockReset();
    apiMocks.createPlanningSetupRecordMock.mockReset();
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
    apiMocks.getShiftTemplateMock.mockReset();
    apiMocks.linkPlanningRecordAttachmentMock.mockReset();
    apiMocks.listOrderAttachmentsMock.mockReset();
    apiMocks.listOrderEquipmentLinesMock.mockReset();
    apiMocks.listOrderRequirementLinesMock.mockReset();
    apiMocks.listPlanningRecordsMock.mockReset();
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
    apiMocks.listPlanningRecordsMock.mockResolvedValue([]);
    apiMocks.listShiftPlansMock.mockResolvedValue([]);
    apiMocks.listShiftTemplatesMock.mockResolvedValue([{ id: 'template-1', tenant_id: 'tenant-1', code: 'TPL-1', label: 'Tagdienst Vorlage', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'day', status: 'active', version_no: 1 }]);
    apiMocks.listShiftTypeOptionsMock.mockResolvedValue([{ code: 'day', label: 'Day shift' }]);
    apiMocks.listShiftSeriesMock.mockResolvedValue([]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.getPlanningRecordMock.mockResolvedValue(buildPlanningRecord());
    apiMocks.getShiftPlanMock.mockResolvedValue(buildShiftPlan());
    apiMocks.getShiftSeriesMock.mockResolvedValue(buildSeries());
    apiMocks.getShiftTemplateMock.mockImplementation((_, templateId: string) =>
      Promise.resolve({
        id: templateId,
        tenant_id: 'tenant-1',
        code: templateId === 'template-2' ? 'ST_RFK_NORTH_DAY_0800_1600' : 'TPL-1',
        label: templateId === 'template-2' ? 'Nordtor Tagdienst 08:00-16:00' : 'Tagdienst Vorlage',
        local_start_time: '08:00',
        local_end_time: '16:00',
        default_break_minutes: templateId === 'template-2' ? 30 : 30,
        shift_type_code: templateId === 'template-2' ? 'site_day' : 'day',
        meeting_point: templateId === 'template-2' ? 'Nordtor Sicherheitsloge' : null,
        location_text: templateId === 'template-2' ? 'RheinForum Köln – Nordtor & Ladehof' : null,
        notes: null,
        status: 'active',
        version_no: 1,
      }),
    );
    apiMocks.createPlanningSetupRecordMock.mockResolvedValue({
      id: 'site-created-1',
      customer_id: 'customer-1',
      site_no: 'SITE-NEW',
      name: 'Neuer Standort',
      tenant_id: 'tenant-1',
      status: 'active',
      version_no: 1,
    });
  });

  it('renders a planning context selector instead of a dead-end when planning context is missing', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-blocked"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-context-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-details"]').exists()).toBe(false);
  });

  it('renders planning context mode options with the standard toggle styling', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-planning-context-existing-label"]').classes()).toContain('planning-admin-checkbox');
    expect(wrapper.get('[data-testid="customer-new-plan-planning-context-create-label"]').classes()).toContain('planning-admin-checkbox');
    expect(wrapper.find('[data-testid="customer-new-plan-planning-context-existing-label"].field-stack').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-context-create-label"].field-stack').exists()).toBe(false);
  });

  it('selects an existing site planning entry locally without committing wizard context', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();
    apiMocks.getCustomerOrderMock.mockClear();
    apiMocks.listOrderAttachmentsMock.mockClear();
    apiMocks.listOrderEquipmentLinesMock.mockClear();
    apiMocks.listOrderRequirementLinesMock.mockClear();
    apiMocks.listPlanningSetupRecordsMock.mockClear();
    routerReplaceMock.mockClear();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();

    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listOrderAttachmentsMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listOrderEquipmentLinesMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listOrderRequirementLinesMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listPlanningSetupRecordsMock).toHaveBeenCalledTimes(0);
    expect(wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').classes()).toContain(
      'sp-customer-plan-wizard-step__list-row--selected',
    );
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-details"]').exists()).toBe(true);
  });

  it('selects existing event venue, trade fair, and patrol route contexts locally with the correct derived mode', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('event_venue');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();
    const setupState = (wrapper.vm as any).$?.setupState;
    expect(setupState.planningEntityId).toBe('venue-1');
    expect(setupState.planningRecordDraft.planning_mode_code).toBe('event');
    expect(wrapper.emitted('saved-context')).toBeUndefined();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('trade_fair');
    await flushPromises();
    apiMocks.listTradeFairZonesMock.mockClear();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();
    expect(setupState.planningEntityId).toBe('fair-1');
    expect(setupState.planningRecordDraft.planning_mode_code).toBe('trade_fair');
    expect(apiMocks.listTradeFairZonesMock).toHaveBeenCalledTimes(1);
    expect(wrapper.emitted('saved-context')).toBeUndefined();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('patrol_route');
    await flushPromises();
    apiMocks.listTradeFairZonesMock.mockClear();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();
    expect(setupState.planningEntityId).toBe('route-1');
    expect(setupState.planningRecordDraft.planning_mode_code).toBe('patrol');
    expect(apiMocks.listTradeFairZonesMock).toHaveBeenCalledTimes(0);
    expect(wrapper.emitted('saved-context')).toBeUndefined();
  });

  it('loads existing operational planning records for the selected order and planning context', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    apiMocks.listPlanningRecordsMock.mockClear();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();

    expect(apiMocks.listPlanningRecordsMock).toHaveBeenCalledWith('tenant-1', 'token-1', {
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
    });
    expect(wrapper.find('[data-testid="customer-new-plan-existing-planning-records"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(1);
  });

  it('loads an existing operational planning record locally without committing wizard context early', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();
    routerReplaceMock.mockClear();
    apiMocks.getPlanningRecordMock.mockClear();

    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledWith('tenant-1', 'record-1', 'token-1');
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );
  });

  it('auto-selects the single saved planning record when there is no contentful unsaved draft', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const contextOnlyDraftKey = buildPlanningRecordDraftKey('site-1', 'site');
    window.sessionStorage.setItem(
      contextOnlyDraftKey,
      JSON.stringify({
        form: {
          dispatcher_user_id: '',
          event_detail_event_venue_id: '',
          event_detail_setup_note: '',
          name: '',
          notes: '',
          parent_planning_record_id: '',
          patrol_detail_execution_note: '',
          patrol_detail_patrol_route_id: '',
          planning_from: '',
          planning_mode_code: 'site',
          planning_to: '',
          site_detail_site_id: '',
          site_detail_watchbook_scope_note: '',
          status: 'active',
          trade_fair_detail_stand_note: '',
          trade_fair_detail_trade_fair_id: '',
          trade_fair_detail_trade_fair_zone_id: '',
        },
        order_id: 'order-1',
        planning_context: {
          planning_entity_id: 'site-1',
          planning_entity_type: 'site',
          planning_mode_code: 'site',
        },
        selection_mode: 'use_existing',
      }),
    );

    const wrapper = mountStep('planning-record-overview');
    await flushPromises();
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledWith('tenant-1', 'record-1', 'token-1');
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toEqual({
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
    });
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );
  });

  it('does not auto-select a saved planning record over a contentful unsaved draft', async () => {
    const draftKey = buildPlanningRecordDraftKey('site-1', 'site');
    window.sessionStorage.setItem(
      draftKey,
      JSON.stringify({
        form: {
          dispatcher_user_id: '',
          event_detail_event_venue_id: '',
          event_detail_setup_note: '',
          name: 'Draft Planning Record',
          notes: '',
          parent_planning_record_id: '',
          patrol_detail_execution_note: '',
          patrol_detail_patrol_route_id: '',
          planning_from: '2026-06-03',
          planning_mode_code: 'site',
          planning_to: '2026-06-12',
          site_detail_site_id: '',
          site_detail_watchbook_scope_note: '',
          status: 'active',
          trade_fair_detail_stand_note: '',
          trade_fair_detail_trade_fair_id: '',
          trade_fair_detail_trade_fair_zone_id: '',
        },
        order_id: 'order-1',
        planning_context: {
          planning_entity_id: 'site-1',
          planning_entity_type: 'site',
          planning_mode_code: 'site',
        },
        selection_mode: 'use_existing',
      }),
    );

    const wrapper = mountStep('planning-record-overview');
    await flushPromises();
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).not.toHaveBeenCalledWith('tenant-1', 'record-1', 'token-1');
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(wrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Draft Planning Record',
    );
  });

  it('shows multiple matching planning records without auto-selecting one', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlanningRecord({ id: 'record-1', name: 'Objektschutz RheinForum Köln – Nordtor Juli 2026' }),
      buildPlanningRecord({
        id: 'record-2',
        name: 'Objektschutz RheinForum Köln – Nordtor August 2026',
        planning_from: '2026-08-01',
        planning_to: '2026-08-31',
      }),
    ]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();

    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(2);
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe('Werk Nord');
    expect(apiMocks.getPlanningRecordMock).not.toHaveBeenCalledWith('tenant-1', 'record-1', 'token-1');
    expect(apiMocks.getPlanningRecordMock).not.toHaveBeenCalledWith('tenant-1', 'record-2', 'token-1');
  });

  it('creates or updates the planning record and keeps step-5 mode alignment', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
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
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toEqual({
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
    });
    expect(apiMocks.listPlanningRecordsMock).toHaveBeenCalledWith('tenant-1', 'token-1', {
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
    });

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

  it('keeps wizard planning-record filters aligned with planning-orders admin expectations', () => {
    const adminViewSource = readFileSync(
      '/home/jey/Projects/SicherPlan/web/apps/web-antd/src/sicherplan-legacy/views/PlanningOrdersAdminView.vue',
      'utf8',
    );

    expect(adminViewSource).toContain('listPlanningRecords');
    expect(adminViewSource).toContain('order_id');
    expect(adminViewSource).toContain('planning_mode_code');
  });

  it('creates a new planning entry inside Planning Record and selects it locally', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    await wrapper.get('[data-testid="customer-new-plan-planning-context-create-new"]').setValue(true);
    await flushPromises();
    setupState.openPlanningCreateModal();
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').setValue('SITE-NEW');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Neuer Standort');
    await wrapper.get('[data-testid="modal-ok"]').trigger('click');
    await flushPromises();

    expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenCalledTimes(1);
    expect(setupState.planningEntityId).toBe('site-created-1');
    expect(setupState.planningSelectionMode).toBe('use_existing');
    expect(wrapper.emitted('saved-context')).toBeUndefined();
  });

  it('blocks Planning Record submit when planning context is missing', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.selectOrCreatePlanningContextBeforeContinue');
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

  it('loads planning-record overview data once per stable context and does not emit saved-context during hydration', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: 'fair-1',
      planning_entity_type: 'trade_fair',
      planning_mode_code: 'trade_fair',
      planning_record_id: '',
    });
    await flushPromises();
    await flushPromises();

    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listOrderAttachmentsMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listOrderEquipmentLinesMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listOrderRequirementLinesMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listPlanningSetupRecordsMock).toHaveBeenCalledTimes(4);
    expect(apiMocks.listTradeFairZonesMock).toHaveBeenCalledTimes(1);
    expect(wrapper.emitted('saved-context')).toBeUndefined();
  });

  it('reloads planning-entry options once when the user changes planning family', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
      planning_record_id: '',
    });
    await flushPromises();
    apiMocks.listPlanningSetupRecordsMock.mockClear();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('trade_fair');
    await flushPromises();

    expect(apiMocks.listPlanningSetupRecordsMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listPlanningSetupRecordsMock).toHaveBeenCalledWith(
      'trade_fair',
      'tenant-1',
      'token-1',
      { customer_id: 'customer-1' },
    );
  });

  it('persists the planning-record draft payload and restores the selected planning context after remount', async () => {
    const wrapper = mountStep('planning-record-overview', {
      current_step: 'planning-record-overview',
      order_id: 'order-1',
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
      planning_record_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('trade_fair');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-row"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Draft Planning Record');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').setValue('2026-06-03');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').setValue('2026-06-12');
    await flushPromises();

    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'fair-1',
        planningEntityType: 'trade_fair',
        tenantId: 'tenant-1',
      },
      'planning-record-overview',
    );
    const persistedDraft = window.sessionStorage.getItem(draftKey);
    expect(persistedDraft).toContain('Draft Planning Record');

    wrapper.unmount();
    window.sessionStorage.setItem(draftKey, persistedDraft || '');

    const restoredWrapper = mountStep('planning-record-overview', {
      current_step: 'planning-record-overview',
      order_id: 'order-1',
      planning_entity_id: 'fair-1',
      planning_entity_type: 'trade_fair',
      planning_mode_code: 'trade_fair',
      planning_record_id: '',
    });
    await flushPromises();
    await flushPromises();
    const restoredSetupState = (restoredWrapper.vm as any).$?.setupState;
    await restoredSetupState.loadPlanningRecordState();
    await flushPromises();

    expect(persistedDraft).toContain('Draft Planning Record');
    expect((restoredWrapper.get('[data-testid="customer-new-plan-planning-context-family"]').element as HTMLSelectElement).value).toBe('trade_fair');
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

    expect(saved).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
    expect(apiMocks.createShiftPlanMock).toHaveBeenCalledWith(
      'tenant-1',
      'token-1',
      expect.objectContaining({
        planning_record_id: 'record-1',
        name: 'Werk Nord / Schichtplan',
      }),
    );
    expect(wrapper.emitted('saved-context')).toBeUndefined();
  });

  it('selects an existing shift plan row locally and shows the selected summary without committing wizard context immediately', async () => {
    apiMocks.listShiftPlansMock.mockResolvedValue([
      buildShiftPlan(),
      buildShiftPlan({ id: 'plan-2', name: 'Werk Süd / Schichtplan', planning_from: '2026-06-02', planning_to: '2026-06-09' }),
    ]);
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: '',
    });
    await flushPromises();

    const rows = wrapper.findAll('[data-testid="customer-new-plan-existing-shift-plan-row"]');
    expect(rows).toHaveLength(2);

    await rows[0]!.trigger('click');
    await flushPromises();

    expect(apiMocks.getShiftPlanMock).toHaveBeenCalledWith('tenant-1', 'plan-1', 'token-1');
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(wrapper.emitted('step-completion')).toBeUndefined();
    expect(wrapper.emitted('step-ui-state')?.at(-1)?.[0]).toBe('shift-plan');
    expect(wrapper.get('[data-testid="customer-new-plan-selected-shift-plan-summary"]').text()).toContain('plan');
    expect(rows[0]!.classes()).toContain('sp-customer-plan-wizard-step__list-row--selected');
  });

  it('continues with a selected existing shift plan without creating a duplicate', async () => {
    apiMocks.listShiftPlansMock.mockResolvedValue([
      buildShiftPlan(),
      buildShiftPlan({ id: 'plan-2', name: 'Werk Süd / Schichtplan' }),
    ]);
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: '',
    });
    await flushPromises();

    await wrapper.findAll('[data-testid="customer-new-plan-existing-shift-plan-row"]')[0]!.trigger('click');
    await flushPromises();

    const continued = await (wrapper.vm as any).submitCurrentStep();

    expect(continued).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
    expect(apiMocks.createShiftPlanMock).not.toHaveBeenCalled();
    expect(apiMocks.updateShiftPlanMock).not.toHaveBeenCalled();
    expect(wrapper.emitted('saved-context')).toBeUndefined();
  });

  it('auto-selects a single existing shift plan when there is no real unsaved draft', async () => {
    apiMocks.listShiftPlansMock.mockResolvedValue([buildShiftPlan()]);
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: '',
    });
    await flushPromises();

    expect(apiMocks.getShiftPlanMock).toHaveBeenCalledWith('tenant-1', 'plan-1', 'token-1');
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(wrapper.emitted('step-completion')).toBeUndefined();
    expect(wrapper.find('[data-testid="customer-new-plan-selected-shift-plan-summary"]').exists()).toBe(true);
  });

  it('continues with the single auto-selected shift plan without creating a duplicate', async () => {
    apiMocks.listShiftPlansMock.mockResolvedValue([buildShiftPlan()]);
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: '',
    });
    await flushPromises();

    const continued = await (wrapper.vm as any).submitCurrentStep();

    expect(continued).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
    expect(apiMocks.createShiftPlanMock).not.toHaveBeenCalled();
    expect(apiMocks.updateShiftPlanMock).not.toHaveBeenCalled();
    expect(wrapper.emitted('saved-context')).toBeUndefined();
  });

  it('does not auto-select when multiple existing shift plans are available', async () => {
    apiMocks.listShiftPlansMock.mockResolvedValue([
      buildShiftPlan(),
      buildShiftPlan({ id: 'plan-2', name: 'Werk Süd / Schichtplan' }),
    ]);
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: '',
    });
    await flushPromises();

    expect(apiMocks.getShiftPlanMock).not.toHaveBeenCalled();
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(wrapper.find('[data-testid="customer-new-plan-selected-shift-plan-summary"]').exists()).toBe(false);
  });

  it('lets the user clear selected shift plan context and start a new one explicitly', async () => {
    apiMocks.listShiftPlansMock.mockResolvedValue([buildShiftPlan()]);
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: 'plan-1',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-create-new-shift-plan"]').trigger('click');
    await flushPromises();

    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toEqual({ shift_plan_id: '' });
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer / sicherplan.customerPlansWizard.forms.shiftPlanDefaultNameSuffix',
    );
  });

  it('validates the shift plan window against the selected planning record window and applies min/max input bounds', async () => {
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: '',
    });
    await flushPromises();

    const fromInput = wrapper.get('[data-testid="customer-new-plan-shift-plan-from"]');
    const toInput = wrapper.get('[data-testid="customer-new-plan-shift-plan-to"]');
    expect(fromInput.attributes('min')).toBe('2026-06-01');
    expect(fromInput.attributes('max')).toBe('2026-06-10');
    expect(toInput.attributes('min')).toBe('2026-06-01');
    expect(toInput.attributes('max')).toBe('2026-06-10');

    await wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').setValue('Werk Nord / Schichtplan');
    await fromInput.setValue('2026-05-31');
    await toInput.setValue('2026-06-10');

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.shiftPlanPlanningRecordWindowMismatch');
    expect(apiMocks.createShiftPlanMock).not.toHaveBeenCalled();
  });

  it('accepts shift plan dates inside the planning record window and saves successfully', async () => {
    apiMocks.getPlanningRecordMock.mockResolvedValue(
      buildPlanningRecord({ planning_from: '2026-07-01', planning_to: '2026-07-31' }),
    );
    const wrapper = mountStep('shift-plan', {
      planning_record_id: 'record-1',
      current_step: 'shift-plan',
      shift_plan_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').setValue('Werk Nord / Fenster ok');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').setValue('2026-07-10');
    apiMocks.createShiftPlanMock.mockResolvedValue(
      buildShiftPlan({ name: 'Werk Nord / Fenster ok', planning_from: '2026-07-01', planning_to: '2026-07-10' }),
    );

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
    expect(apiMocks.createShiftPlanMock).toHaveBeenCalledOnce();
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
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').setValue('2026-06-10');
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
    expect((restoredWrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').element as HTMLInputElement).value).toBe('2026-06-10');
    expect(restoredWrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');
  });

  it('does not restore a generic persisted shift-plan draft over a saved selected shift plan', async () => {
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
        draft: {
          name: 'Generic Draft',
          planning_from: '2026-06-03',
          planning_to: '2026-06-04',
          planning_record_id: 'record-1',
          remarks: 'draft',
          workforce_scope_code: 'mixed',
        },
        selected_shift_plan_id: '',
      }),
    );

    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
    });
    await flushPromises();

    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toBe('Werk Nord / Schichtplan');
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-from"]').element as HTMLInputElement).value).toBe('2026-06-01');
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').element as HTMLInputElement).value).toBe('2026-06-10');
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
    expect(apiMocks.createShiftPlanMock).not.toHaveBeenCalled();
    expect(apiMocks.updateShiftPlanMock).not.toHaveBeenCalled();
  });

  it('applies a contentful matching shift-plan draft, updates the saved plan, and returns committed context', async () => {
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
        draft: {
          name: 'Werk Nord / Angepasst',
          planning_from: '2026-06-01',
          planning_to: '2026-06-10',
          planning_record_id: 'record-1',
          remarks: 'drafted change',
          workforce_scope_code: 'internal',
        },
        selected_shift_plan_id: 'plan-1',
      }),
    );

    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
    });
    await flushPromises();

    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toBe('Werk Nord / Angepasst');
    expect(wrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe('sicherplan.customerPlansWizard.draftRestored');

    apiMocks.updateShiftPlanMock.mockResolvedValue(
      buildShiftPlan({ id: 'plan-1', name: 'Werk Nord / Angepasst', remarks: 'drafted change', version_no: 2 }),
    );

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
    expect(apiMocks.updateShiftPlanMock).toHaveBeenCalledWith(
      'tenant-1',
      'plan-1',
      'token-1',
      expect.objectContaining({
        name: 'Werk Nord / Angepasst',
        remarks: 'drafted change',
        version_no: 1,
      }),
    );
    expect(apiMocks.createShiftPlanMock).not.toHaveBeenCalled();
  });

  it('ignores and clears a blank/default persisted shift-plan draft instead of showing draft restored', async () => {
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
        draft: {
          name: 'Werk Nord Sommer / sicherplan.customerPlansWizard.forms.shiftPlanDefaultNameSuffix',
          planning_from: '2026-06-01',
          planning_to: '2026-06-10',
          planning_record_id: 'record-1',
          remarks: '',
          workforce_scope_code: 'internal',
        },
        selected_shift_plan_id: '',
      }),
    );

    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: '',
    });
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);
    expect(window.sessionStorage.getItem(draftKey)).toBeNull();
  });

  it('clears a real shift-plan draft after successful save', async () => {
    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').setValue('Draft Shift Plan');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-from"]').setValue('2026-06-02');
    await wrapper.get('[data-testid="customer-new-plan-shift-plan-to"]').setValue('2026-06-10');
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

    apiMocks.createShiftPlanMock.mockResolvedValue(
      buildShiftPlan({ name: 'Draft Shift Plan', planning_from: '2026-06-02', planning_to: '2026-06-10' }),
    );
    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
    expect(window.sessionStorage.getItem(draftKey)).toBeNull();
    expect(wrapper.emitted('saved-context')).toBeUndefined();
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

    expect(shiftPlanSaved).toEqual({
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: 'plan-1' },
    });
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
    expect(apiMocks.generateShiftSeriesMock).toHaveBeenCalledWith('tenant-1', 'series-1', 'token-1', {
      from_date: '2026-06-01',
      regenerate_existing: false,
      to_date: '2026-06-10',
    });
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

  it('loads the Series step with read-only upstream hydration and keeps the series form visible after all loaders finish', async () => {
    apiMocks.getPlanningRecordMock.mockResolvedValue(
      buildPlanningRecord({
        id: 'record-1',
        name: 'Werk Nord Sommer',
        planning_from: '2026-06-01',
        planning_to: '2026-06-10',
      }),
    );
    apiMocks.getShiftPlanMock.mockResolvedValue(
      buildShiftPlan({
        id: 'plan-1',
        name: 'Werk Nord / Schichtplan',
        planning_from: '2026-06-01',
        planning_to: '2026-06-10',
      }),
    );
    apiMocks.listShiftSeriesMock.mockResolvedValue([]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledWith('tenant-1', 'record-1', 'token-1');
    expect(apiMocks.getShiftPlanMock).toHaveBeenCalledWith('tenant-1', 'plan-1', 'token-1');
    expect(apiMocks.listPlanningRecordAttachmentsMock).not.toHaveBeenCalled();
    expect(apiMocks.listShiftPlansMock).not.toHaveBeenCalled();
    expect(apiMocks.listShiftTemplatesMock).toHaveBeenCalled();
    expect(apiMocks.listShiftTypeOptionsMock).toHaveBeenCalled();
    expect(apiMocks.listShiftSeriesMock).toHaveBeenCalledWith('tenant-1', 'plan-1', 'token-1');
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-shift-plan"]').exists()).toBe(false);
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-series-shift-plan-summary"]').text()).toContain(
      'Werk Nord / Schichtplan',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-series-shift-plan-summary"]').text()).toContain(
      'sicherplan.customerPlansWizard.forms.workforceScope',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-label"]').element as HTMLInputElement).value).toBe(
      'Werk Nord / Schichtplan',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-from"]').element as HTMLInputElement).value).toBe(
      '2026-06-01',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-to"]').element as HTMLInputElement).value).toBe(
      '2026-06-10',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-generation-from"]').element as HTMLInputElement).value).toBe(
      '2026-06-01',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-generation-to"]').element as HTMLInputElement).value).toBe(
      '2026-06-10',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-timezone"]').element as HTMLSelectElement).value).toBe(
      'Europe/Berlin',
    );
    expect(((wrapper.vm as any).$?.setupState.seriesDraft.weekday_mask as string)).toBe('');
  });

  it('shows code and label for shift templates, applies template defaults, and submits explicit generation controls', async () => {
    apiMocks.listShiftTemplatesMock.mockResolvedValue([
      { id: 'template-1', tenant_id: 'tenant-1', code: 'TPL-1', label: 'Tagdienst Vorlage', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'day', status: 'active', version_no: 1 },
      { id: 'template-2', tenant_id: 'tenant-1', code: 'ST_RFK_NORTH_DAY_0800_1600', label: 'Nordtor Tagdienst 08:00-16:00', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'site_day', status: 'active', version_no: 1 },
    ]);
    apiMocks.getShiftPlanMock.mockResolvedValue(
      buildShiftPlan({
        planning_from: '2026-07-01',
        planning_to: '2026-07-31',
      }),
    );
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      shift_plan_id: 'plan-1',
      planning_record_id: '',
      series_id: '',
    });
    await flushPromises();

    const templateSelect = wrapper.get('[data-testid="customer-new-plan-series-template"]');
    expect(templateSelect.text()).toContain('ST_RFK_NORTH_DAY_0800_1600');
    expect(templateSelect.text()).toContain('Nordtor Tagdienst 08:00-16:00');

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await templateSelect.setValue('template-2');
    await flushPromises();
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    expect(apiMocks.getShiftTemplateMock).toHaveBeenCalledWith('tenant-1', 'template-2', 'token-1');
    expect(setupState.seriesDraft.default_break_minutes).toBe(30);
    expect(setupState.seriesDraft.shift_type_code).toBe('site_day');
    expect(setupState.seriesDraft.meeting_point).toBe('Nordtor Sicherheitsloge');
    expect(setupState.seriesDraft.location_text).toBe('RheinForum Köln – Nordtor & Ladehof');

    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-regenerate-existing"]').setValue(false);
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(
      buildSeries({
        date_from: '2026-07-01',
        date_to: '2026-07-31',
        label: 'Werktage Tagschicht Nordtor',
        shift_template_id: 'template-2',
        shift_type_code: 'site_day',
      }),
    );
    apiMocks.listShiftSeriesMock.mockResolvedValue([
      buildSeries({
        date_from: '2026-07-01',
        date_to: '2026-07-31',
        label: 'Werktage Tagschicht Nordtor',
        shift_template_id: 'template-2',
        shift_type_code: 'site_day',
      }),
    ]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-01',
        starts_at: '2026-07-01T08:00:00Z',
        ends_at: '2026-07-01T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'site_day',
        location_text: 'RheinForum Köln – Nordtor & Ladehof',
        meeting_point: 'Nordtor Sicherheitsloge',
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
        date_from: '2026-07-01',
        date_to: '2026-07-31',
        default_break_minutes: 30,
        label: 'Werktage Tagschicht Nordtor',
        location_text: 'RheinForum Köln – Nordtor & Ladehof',
        meeting_point: 'Nordtor Sicherheitsloge',
        shift_type_code: 'site_day',
        shift_template_id: 'template-2',
      }),
    );
    expect(apiMocks.generateShiftSeriesMock).toHaveBeenCalledWith('tenant-1', 'series-1', 'token-1', {
      from_date: '2026-07-01',
      regenerate_existing: false,
      to_date: '2026-07-31',
    });
    expect(routerPushMock).toHaveBeenCalledWith(
      '/admin/planning-staffing?date_from=2026-07-01T00%3A00&date_to=2026-07-02T00%3A00&shift_id=shift-1',
    );
  });

  it('accepts the full RheinForum Nordtor weekly series data and reflects the exact form state', async () => {
    apiMocks.listShiftTemplatesMock.mockResolvedValue([
      { id: 'template-2', tenant_id: 'tenant-1', code: 'ST_RFK_NORTH_DAY_0800_1600', label: 'RheinForum Nordtor Day 08:00-16:00', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'site_day', status: 'active', version_no: 1 },
    ]);
    apiMocks.getShiftPlanMock.mockResolvedValue(
      buildShiftPlan({
        planning_from: '2026-07-01',
        planning_to: '2026-07-31',
      }),
    );

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      order_id: 'order-1',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-2');
    await setSeriesWeeklyMask(wrapper, '1111100');
    await wrapper.get('[data-testid="customer-new-plan-series-timezone"]').setValue('Europe/Berlin');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-07-31');
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    setupState.seriesDraft.default_break_minutes = 30;
    setupState.seriesDraft.shift_type_code = 'site_day';
    setupState.seriesDraft.meeting_point = 'Nordtor Sicherheitsloge';
    setupState.seriesDraft.location_text = 'RheinForum Köln – Nordtor & Ladehof';
    setupState.seriesDraft.customer_visible_flag = false;
    setupState.seriesDraft.subcontractor_visible_flag = false;
    setupState.seriesDraft.stealth_mode_flag = false;
    setupState.seriesDraft.release_state = 'draft';
    setupState.seriesDraft.notes = 'Standard weekday recurring day-shift pattern for RheinForum Köln – Nordtor & Ladehof.';
    await flushPromises();

    expect(setupState.seriesDraft).toMatchObject({
      label: 'Werktage Tagschicht Nordtor',
      recurrence_code: 'weekly',
      interval_count: 1,
      weekday_mask: '1111100',
      timezone: 'Europe/Berlin',
      date_from: '2026-07-01',
      date_to: '2026-07-31',
      default_break_minutes: 30,
      shift_type_code: 'site_day',
      meeting_point: 'Nordtor Sicherheitsloge',
      location_text: 'RheinForum Köln – Nordtor & Ladehof',
      customer_visible_flag: false,
      subcontractor_visible_flag: false,
      stealth_mode_flag: false,
      release_state: 'draft',
      notes: 'Standard weekday recurring day-shift pattern for RheinForum Köln – Nordtor & Ladehof.',
    });
  });

  it('keeps Series active and ignores a stale shift-plan draft when shift_plan_id is already committed', async () => {
    const shiftPlanDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'shift-plan',
    );
    window.sessionStorage.setItem(
      shiftPlanDraftKey,
      JSON.stringify({
        draft: {
          name: 'Stale Shift Draft',
          planning_from: '2026-06-03',
          planning_to: '2026-06-04',
          planning_record_id: 'record-1',
          remarks: 'stale',
          workforce_scope_code: 'mixed',
        },
        selected_shift_plan_id: '',
      }),
    );

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-shift-plan"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-series-shift-plan-summary"]').text()).toContain(
      'Werk Nord / Schichtplan',
    );
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);
    expect(window.sessionStorage.getItem(shiftPlanDraftKey)).toContain('Stale Shift Draft');
  });

  it('restores a contentful series draft for the committed shift plan without activating upstream steps', async () => {
    const seriesDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'series-exceptions',
    );
    window.sessionStorage.setItem(
      seriesDraftKey,
      JSON.stringify({
        exception: {
          action_code: 'skip',
          customer_visible_flag: null,
          exception_date: '',
          notes: '',
          override_break_minutes: '',
          override_local_end_time: '',
          override_local_start_time: '',
          override_location_text: '',
          override_meeting_point: '',
          override_shift_type_code: '',
          stealth_mode_flag: null,
          subcontractor_visible_flag: null,
        },
        series: {
          customer_visible_flag: false,
          date_from: '2026-06-02',
          date_to: '2026-06-09',
          default_break_minutes: 45,
          interval_count: 2,
          label: 'Restored Series Draft',
          location_text: 'Nordtor',
          meeting_point: '',
          notes: 'draft notes',
          recurrence_code: 'weekly',
          release_state: 'draft',
          shift_template_id: 'template-1',
          shift_type_code: 'day',
          stealth_mode_flag: false,
          subcontractor_visible_flag: false,
          timezone: 'Europe/Berlin',
          weekday_mask: '1010100',
        },
      }),
    );

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-shift-plan"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-series-label"]').element as HTMLInputElement).value).toBe(
      'Restored Series Draft',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-from"]').element as HTMLInputElement).value).toBe(
      '2026-06-02',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-to"]').element as HTMLInputElement).value).toBe(
      '2026-06-09',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-draft-restored"]').text()).toBe(
      'sicherplan.customerPlansWizard.draftRestored',
    );
    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(seriesWeekdayChip(wrapper, 'mon').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'tue').attributes('aria-pressed')).toBe('false');
    expect(seriesWeekdayChip(wrapper, 'wed').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'thu').attributes('aria-pressed')).toBe('false');
    expect(seriesWeekdayChip(wrapper, 'fri').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'sat').attributes('aria-pressed')).toBe('false');
    expect(seriesWeekdayChip(wrapper, 'sun').attributes('aria-pressed')).toBe('false');
  });

  it('displays existing series rows and keeps the wizard on Series when one row is selected', async () => {
    apiMocks.listShiftSeriesMock.mockResolvedValue([
      buildSeries({ id: 'series-1', label: 'Tagdienst' }),
      buildSeries({ id: 'series-2', label: 'Nachtdienst', date_from: '2026-06-05', date_to: '2026-06-20' }),
    ]);
    apiMocks.getShiftSeriesMock.mockResolvedValue(
      buildSeries({ id: 'series-2', label: 'Nachtdienst', date_from: '2026-06-05', date_to: '2026-06-20' }),
    );
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([
      {
        id: 'exception-1',
        tenant_id: 'tenant-1',
        shift_series_id: 'series-2',
        exception_date: '2026-06-07',
        action_code: 'skip',
        version_no: 1,
      },
    ]);

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    const rows = wrapper.findAll('.sp-customer-plan-wizard-step__list-row');
    expect(rows.some((row) => row.text().includes('Tagdienst'))).toBe(true);
    expect(rows.some((row) => row.text().includes('Nachtdienst'))).toBe(true);

    const targetRow = rows.find((row) => row.text().includes('Nachtdienst'));
    expect(targetRow).toBeDefined();
    await targetRow!.trigger('click');
    await flushPromises();

    expect(apiMocks.getShiftSeriesMock).toHaveBeenCalledWith('tenant-1', 'series-2', 'token-1');
    expect(apiMocks.listShiftSeriesExceptionsMock).toHaveBeenCalledWith('tenant-1', 'series-2', 'token-1');
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-series-label"]').element as HTMLInputElement).value).toBe(
      'Nachtdienst',
    );
  });

  it('restores saved weekly series masks into active weekday chips when an existing series is selected', async () => {
    apiMocks.listShiftSeriesMock.mockResolvedValue([
      buildSeries({ id: 'series-1', label: 'Werktage', recurrence_code: 'weekly', weekday_mask: '1010100' }),
    ]);
    apiMocks.getShiftSeriesMock.mockResolvedValue(
      buildSeries({ id: 'series-1', label: 'Werktage', recurrence_code: 'weekly', weekday_mask: '1010100' }),
    );
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    const rows = wrapper.findAll('.sp-customer-plan-wizard-step__list-row');
    const targetRow = rows.find((row) => row.text().includes('Werktage'));
    expect(targetRow).toBeDefined();
    await targetRow!.trigger('click');
    await flushPromises();

    expect((wrapper.vm as any).$?.setupState.seriesDraft.weekday_mask).toBe('1010100');
    expect(seriesWeekdayChip(wrapper, 'mon').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'tue').attributes('aria-pressed')).toBe('false');
    expect(seriesWeekdayChip(wrapper, 'wed').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'thu').attributes('aria-pressed')).toBe('false');
    expect(seriesWeekdayChip(wrapper, 'fri').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'sat').attributes('aria-pressed')).toBe('false');
    expect(seriesWeekdayChip(wrapper, 'sun').attributes('aria-pressed')).toBe('false');
  });

  it('blocks Series submit when the date range exceeds the selected shift-plan window', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Nachtdienst Juni');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-05-31');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    await flushPromises();

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.seriesShiftPlanWindowMismatch');
    expect(apiMocks.createShiftSeriesMock).not.toHaveBeenCalled();
  });

  it('shows the weekday picker for weekly recurrence with seven chips and no raw weekday mask input', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('weekly');
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-series-weekday-picker"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="customer-new-plan-series-weekday-chip"]')).toHaveLength(7);
    for (const weekdayId of SERIES_WEEKDAY_IDS) {
      expect(wrapper.find(`[data-testid="customer-new-plan-series-weekday-chip-${weekdayId}"]`).exists()).toBe(true);
    }
    expect(wrapper.find('[data-testid="customer-new-plan-series-weekday-mask"]').exists()).toBe(false);
  });

  it('toggles weekday chips into the correct mask with matching aria and active classes', async () => {
    const seriesDraftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'series-exceptions',
    );
    window.sessionStorage.setItem(
      seriesDraftKey,
      JSON.stringify({
        exception: {
          action_code: 'skip',
          customer_visible_flag: null,
          exception_date: '',
          notes: '',
          override_break_minutes: '',
          override_local_end_time: '',
          override_local_start_time: '',
          override_location_text: '',
          override_meeting_point: '',
          override_shift_type_code: '',
          stealth_mode_flag: null,
          subcontractor_visible_flag: null,
        },
        series: {
          customer_visible_flag: false,
          date_from: '2026-06-01',
          date_to: '2026-06-10',
          default_break_minutes: 30,
          interval_count: 1,
          label: 'Weekly Draft',
          location_text: '',
          meeting_point: '',
          notes: '',
          recurrence_code: 'weekly',
          release_state: 'draft',
          shift_template_id: 'template-1',
          shift_type_code: 'day',
          stealth_mode_flag: false,
          subcontractor_visible_flag: false,
          timezone: 'Europe/Berlin',
          weekday_mask: '1111100',
        },
      }),
    );

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    expect(setupState.seriesDraft.weekday_mask).toBe('1111100');

    const saturdayChip = seriesWeekdayChip(wrapper, 'sat');
    setupState.toggleSeriesWeekday(5);
    await flushPromises();
    expect(setupState.seriesDraft.weekday_mask).toBe('1111110');
    expect(saturdayChip.attributes('aria-pressed')).toBe('true');
    expect(saturdayChip.classes()).toContain('sp-customer-plan-wizard-step__weekday-chip--active');

    const mondayChip = seriesWeekdayChip(wrapper, 'mon');
    setupState.toggleSeriesWeekday(0);
    await flushPromises();
    expect(setupState.seriesDraft.weekday_mask).toBe('0111110');
    expect(mondayChip.attributes('aria-pressed')).toBe('false');
    expect(mondayChip.classes()).not.toContain('sp-customer-plan-wizard-step__weekday-chip--active');
    expect(seriesWeekdayChip(wrapper, 'fri').attributes('aria-pressed')).toBe('true');
  });

  it('validates weekly weekday mask, clears it for daily recurrence, and supports tri-state override visibility', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    await wrapper.get('[data-testid="customer-new-plan-series-timezone"]').setValue('Europe/Berlin');
    await setSeriesWeeklyMask(wrapper, '0000000');
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    let saved = await (wrapper.vm as any).submitCurrentStep();
    expect(saved).toBe(false);
    expect(setupState.stepFeedback.message).toBe('sicherplan.customerPlansWizard.errors.seriesWeekdayMaskInvalid');
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.forms.weekdayMaskHelp');

    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('daily');
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-series-weekday-picker"]').exists()).toBe(false);
    expect(setupState.seriesDraft.weekday_mask).toBe('');

    await setSeriesWeeklyMask(wrapper, '1111100');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('override');
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-series-exception-override-start"]').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-customer-visible"]').setValue('false');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-subcontractor-visible"]').setValue('true');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-stealth-mode"]').setValue('');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-06-03');
    await flushPromises();

    saved = await (wrapper.vm as any).submitCurrentStep();
    expect(saved).toBe(false);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.seriesExceptionOverrideTimesRequired');

    await wrapper.get('[data-testid="customer-new-plan-series-exception-override-start"]').setValue('08:30');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-override-end"]').setValue('16:30');
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(
      buildSeries({
        date_from: '2026-06-01',
        date_to: '2026-06-10',
        recurrence_code: 'weekly',
        weekday_mask: '1111100',
      }),
    );
    apiMocks.createShiftSeriesExceptionMock.mockResolvedValue({
      id: 'exception-1',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-06-03',
      action_code: 'override',
      customer_visible_flag: false,
      subcontractor_visible_flag: true,
      stealth_mode_flag: null,
      override_local_start_time: '08:30',
      override_local_end_time: '16:30',
      version_no: 1,
    });
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ recurrence_code: 'weekly', weekday_mask: '1111100' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockResolvedValue([]);

    saved = await (wrapper.vm as any).submitCurrentStep();
    expect(saved).toBe(true);
    expect(apiMocks.createShiftSeriesMock).toHaveBeenCalledWith(
      'tenant-1',
      'plan-1',
      'token-1',
      expect.objectContaining({
        recurrence_code: 'weekly',
        weekday_mask: '1111100',
        timezone: 'Europe/Berlin',
      }),
    );
    expect(apiMocks.createShiftSeriesExceptionMock).toHaveBeenCalledWith(
      'tenant-1',
      'series-1',
      'token-1',
      expect.objectContaining({
        action_code: 'override',
        customer_visible_flag: false,
        subcontractor_visible_flag: true,
        stealth_mode_flag: null,
        override_local_start_time: '08:30',
        override_local_end_time: '16:30',
      }),
    );
  });

  it('submits daily recurrence without a weekly mask and keeps the picker hidden', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Tagesdienst');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('daily');
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-series-weekday-picker"]').exists()).toBe(false);
    expect((wrapper.vm as any).$?.setupState.seriesDraft.weekday_mask).toBe('');

    apiMocks.createShiftSeriesMock.mockResolvedValue(
      buildSeries({
        recurrence_code: 'daily',
        weekday_mask: null,
      }),
    );
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ recurrence_code: 'daily', weekday_mask: null })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockResolvedValue([
      {
        id: 'shift-daily-1',
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
    expect(apiMocks.createShiftSeriesMock).toHaveBeenLastCalledWith(
      'tenant-1',
      'plan-1',
      'token-1',
      expect.objectContaining({
        recurrence_code: 'daily',
        weekday_mask: null,
      }),
    );
  });

  it('submits skip exceptions with null override payload fields', async () => {
    apiMocks.getShiftPlanMock.mockResolvedValue(
      buildShiftPlan({
        planning_from: '2026-07-01',
        planning_to: '2026-07-31',
      }),
    );
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      order_id: 'order-1',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('weekly');
    await setSeriesWeeklyMask(wrapper, '1111100');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    setupState.exceptionDraft.notes = 'Interne Logistik-Sperrung am Nordtor; kein regulärer Objektschutzdienst an diesem Tag.';
    apiMocks.createShiftSeriesMock.mockResolvedValue(
      buildSeries({
        date_from: '2026-07-01',
        date_to: '2026-07-31',
        recurrence_code: 'weekly',
        weekday_mask: '1111100',
      }),
    );
    apiMocks.createShiftSeriesExceptionMock.mockResolvedValue({
      id: 'exception-1',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-07-03',
      action_code: 'skip',
      customer_visible_flag: null,
      subcontractor_visible_flag: null,
      stealth_mode_flag: null,
      version_no: 1,
    });
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', recurrence_code: 'weekly', weekday_mask: '1111100' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockResolvedValue([]);

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(true);
    expect(apiMocks.createShiftSeriesExceptionMock).toHaveBeenCalledWith(
      'tenant-1',
      'series-1',
      'token-1',
      expect.objectContaining({
        action_code: 'skip',
        override_local_start_time: null,
        override_local_end_time: null,
        override_break_minutes: null,
        override_shift_type_code: null,
        override_meeting_point: null,
        override_location_text: null,
        customer_visible_flag: null,
        subcontractor_visible_flag: null,
        stealth_mode_flag: null,
      }),
    );
  });

  it('defaults empty weekly weekday mask to monday-friday and does not overwrite manually edited template-derived fields', async () => {
    apiMocks.listShiftTemplatesMock.mockResolvedValue([
      { id: 'template-1', tenant_id: 'tenant-1', code: 'TPL-1', label: 'Tagdienst Vorlage', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'day', status: 'active', version_no: 1 },
      { id: 'template-2', tenant_id: 'tenant-1', code: 'ST_RFK_NORTH_DAY_0800_1600', label: 'Nordtor Tagdienst 08:00-16:00', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'site_day', status: 'active', version_no: 1 },
    ]);
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('weekly');
    await flushPromises();
    expect((wrapper.vm as any).$?.setupState.seriesDraft.weekday_mask).toBe('1111100');
    expect(seriesWeekdayChip(wrapper, 'mon').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'tue').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'wed').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'thu').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'fri').attributes('aria-pressed')).toBe('true');
    expect(seriesWeekdayChip(wrapper, 'sat').attributes('aria-pressed')).toBe('false');
    expect(seriesWeekdayChip(wrapper, 'sun').attributes('aria-pressed')).toBe('false');

    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-2');
    await flushPromises();
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    setupState.seriesDraft.default_break_minutes = 45;
    setupState.seriesDraft.shift_type_code = 'custom_day';
    setupState.seriesDraft.meeting_point = 'Custom meeting';
    setupState.seriesDraft.location_text = 'Custom location';
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await flushPromises();
    await flushPromises();

    expect(setupState.seriesDraft.default_break_minutes).toBe(45);
    expect(setupState.seriesDraft.shift_type_code).toBe('custom_day');
    expect(setupState.seriesDraft.meeting_point).toBe('Custom meeting');
    expect(setupState.seriesDraft.location_text).toBe('Custom location');
  });

  it('maps known backend series errors to specific user-facing messages', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries());
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries()]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockRejectedValue(
      new planningShiftsApiErrorExports.PlanningShiftsApiError(400, {
        message_key: 'errors.planning.shift_series.invalid_generation_window',
        details: {},
      }),
    );

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.seriesGenerationWindowInvalid');
  });

  it('runs full submit in order and clears the series draft only after successful generation', async () => {
    apiMocks.getShiftPlanMock.mockResolvedValue(
      buildShiftPlan({
        planning_from: '2026-07-01',
        planning_to: '2026-07-31',
      }),
    );
    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'series-exceptions',
    );
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('weekly');
    await setSeriesWeeklyMask(wrapper, '1111100');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    await flushPromises();

    const generated = Array.from({ length: 22 }, (_, index) => ({
      id: `shift-${index + 1}`,
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      occurrence_date: `2026-07-${String(index + 1).padStart(2, '0')}`,
      starts_at: `2026-07-${String(index + 1).padStart(2, '0')}T08:00:00Z`,
      ends_at: `2026-07-${String(index + 1).padStart(2, '0')}T16:00:00Z`,
      break_minutes: 30,
      shift_type_code: 'site_day',
      location_text: 'RheinForum Köln – Nordtor & Ladehof',
      meeting_point: 'Nordtor Sicherheitsloge',
      release_state: 'draft',
      customer_visible_flag: false,
      subcontractor_visible_flag: false,
      stealth_mode_flag: false,
      source_kind_code: 'series',
      status: 'active',
      version_no: 1,
    }));
    apiMocks.createShiftSeriesMock.mockResolvedValue(
      buildSeries({
        date_from: '2026-07-01',
        date_to: '2026-07-31',
        recurrence_code: 'weekly',
        weekday_mask: '1111100',
      }),
    );
    apiMocks.createShiftSeriesExceptionMock.mockResolvedValue({
      id: 'exception-1',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-07-03',
      action_code: 'skip',
      version_no: 1,
    });
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', recurrence_code: 'weekly', weekday_mask: '1111100' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockResolvedValue(generated);

    expect(window.sessionStorage.getItem(draftKey)).toContain('Werktage Tagschicht Nordtor');

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(true);
    const createOrder = apiMocks.createShiftSeriesMock.mock.invocationCallOrder[0];
    const exceptionOrder = apiMocks.createShiftSeriesExceptionMock.mock.invocationCallOrder[0];
    const generateOrder = apiMocks.generateShiftSeriesMock.mock.invocationCallOrder[0];
    expect(createOrder).toBeDefined();
    expect(exceptionOrder).toBeDefined();
    expect(generateOrder).toBeDefined();
    expect(createOrder!).toBeLessThan(exceptionOrder!);
    expect(exceptionOrder!).toBeLessThan(generateOrder!);
    expect(apiMocks.generateShiftSeriesMock).toHaveBeenCalledWith('tenant-1', 'series-1', 'token-1', {
      from_date: '2026-07-01',
      to_date: '2026-07-31',
      regenerate_existing: false,
    });
    expect(apiMocks.generateShiftSeriesMock.mock.results[0]?.type).toBe('return');
    expect(window.sessionStorage.getItem(draftKey)).toBeNull();
    expect(routerPushMock).toHaveBeenCalled();
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

  it('does not clear drafts and keeps entered fields visible when generation fails after series and exception save', async () => {
    const draftKey = buildWizardDraftStorageKey(
      {
        customerId: 'customer-1',
        planningEntityId: 'site-1',
        planningEntityType: 'site',
        tenantId: 'tenant-1',
      },
      'series-exceptions',
    );
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('weekly');
    await setSeriesWeeklyMask(wrapper, '1111100');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', recurrence_code: 'weekly', weekday_mask: '1111100' }));
    apiMocks.createShiftSeriesExceptionMock.mockResolvedValue({
      id: 'exception-1',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-07-03',
      action_code: 'skip',
      version_no: 1,
    });
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', recurrence_code: 'weekly', weekday_mask: '1111100' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockRejectedValue(new Error('generate failed'));

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(window.sessionStorage.getItem(draftKey)).toContain('Werktage Tagschicht Nordtor');
    expect((wrapper.get('[data-testid="customer-new-plan-series-label"]').element as HTMLInputElement).value).toBe('Werktage Tagschicht Nordtor');
    expect((wrapper.vm as any).$?.setupState.seriesDraft.weekday_mask).toBe('1111100');
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
  });

  it('does not generate shifts when exception save fails and shows a useful mapped error', async () => {
    apiMocks.getShiftPlanMock.mockResolvedValue(
      buildShiftPlan({
        planning_from: '2026-07-01',
        planning_to: '2026-07-31',
      }),
    );
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Werktage Tagschicht Nordtor');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('weekly');
    await setSeriesWeeklyMask(wrapper, '1111100');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', recurrence_code: 'weekly', weekday_mask: '1111100' }));
    apiMocks.createShiftSeriesExceptionMock.mockRejectedValue(
      new planningShiftsApiErrorExports.PlanningShiftsApiError(409, {
        message_key: 'errors.planning.shift_series_exception.duplicate_date',
        details: {},
      }),
    );

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(apiMocks.generateShiftSeriesMock).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.seriesExceptionDuplicateDate');
  });

  it('treats weekday_mask 1111100 as monday-friday and a skip on 2026-07-03 reduces 23 weekday occurrences to 22', () => {
    const occurrences = countWeeklyOccurrences('2026-07-01', '2026-07-31', '1111100');
    expect(occurrences).toHaveLength(23);
    expect(occurrences.every((date) => {
      const weekday = (new Date(`${date}T00:00:00Z`).getUTCDay() + 6) % 7;
      return weekday >= 0 && weekday <= 4;
    })).toBe(true);
    const afterSkip = occurrences.filter((date) => date !== '2026-07-03');
    expect(afterSkip).toHaveLength(22);
    expect(afterSkip).not.toContain('2026-07-03');
  });
});
