// @vitest-environment happy-dom

import { readFileSync } from 'node:fs';

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';

import CustomerNewPlanStepContent from './new-plan-step-content.vue';
import { buildWizardDraftStorageKey } from './new-plan-wizard-drafts';
import type { CustomerNewPlanWizardState, CustomerNewPlanWizardStepId } from './new-plan-wizard.types';

const routerPushMock = vi.fn();
const routerReplaceMock = vi.fn();
const confirmMock = vi.fn();
const notificationMocks = vi.hoisted(() => ({
  error: vi.fn(),
  info: vi.fn(),
  success: vi.fn(),
  warning: vi.fn(),
}));
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
  applyAssignmentStepMock: vi.fn(),
  getAssignmentStepSnapshotMock: vi.fn(),
  createPlanningSetupRecordMock: vi.fn(),
  createPlanningRecordAttachmentMock: vi.fn(),
  createPlanningRecordMock: vi.fn(),
  createShiftPlanMock: vi.fn(),
  createShiftSeriesExceptionMock: vi.fn(),
  createShiftSeriesMock: vi.fn(),
  createShiftTemplateMock: vi.fn(),
  deleteShiftSeriesExceptionMock: vi.fn(),
  generateShiftSeriesMock: vi.fn(),
  bulkApplyDemandGroupsMock: vi.fn(),
  bulkUpdateDemandGroupsMock: vi.fn(),
  getCustomerOrderMock: vi.fn(),
  getPlanningRecordMock: vi.fn(),
  getShiftPlanMock: vi.fn(),
  getShiftSeriesMock: vi.fn(),
  getShiftTemplateMock: vi.fn(),
  listAssignmentStepCandidatesMock: vi.fn(),
  listDemandGroupsMock: vi.fn(),
  listTeamsMock: vi.fn(),
  linkOrderAttachmentMock: vi.fn(),
  linkPlanningRecordAttachmentMock: vi.fn(),
  listCustomerOrdersMock: vi.fn(),
  listDocumentsMock: vi.fn(),
  listOrderAttachmentsMock: vi.fn(),
  listOrderEquipmentLinesMock: vi.fn(),
  listOrderRequirementLinesMock: vi.fn(),
  listPlanningRecordsMock: vi.fn(),
  listPlanningRecordAttachmentsMock: vi.fn(),
  listPlanningSetupRecordsMock: vi.fn(),
  listServiceCategoryOptionsMock: vi.fn(),
  listTradeFairZonesMock: vi.fn(),
  listShiftPlansMock: vi.fn(),
  listShiftsMock: vi.fn(),
  listShiftSeriesExceptionsMock: vi.fn(),
  listShiftSeriesMock: vi.fn(),
  listShiftTemplatesMock: vi.fn(),
  listShiftTypeOptionsMock: vi.fn(),
  previewAssignmentStepApplyMock: vi.fn(),
  updateDemandGroupMock: vi.fn(),
  updatePlanningRecordMock: vi.fn(),
  updateShiftPlanMock: vi.fn(),
  updateShiftSeriesExceptionMock: vi.fn(),
  updateShiftSeriesMock: vi.fn(),
  unlinkPlanningRecordAttachmentMock: vi.fn(),
}));
const employeeAdminMocks = vi.hoisted(() => ({
  listEmployeeGroupsMock: vi.fn(),
  listFunctionTypesMock: vi.fn(),
  listQualificationTypesMock: vi.fn(),
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
  listEmployeeGroups: employeeAdminMocks.listEmployeeGroupsMock,
  listFunctionTypes: employeeAdminMocks.listFunctionTypesMock,
  listQualificationTypes: employeeAdminMocks.listQualificationTypesMock,
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
  linkOrderAttachment: apiMocks.linkOrderAttachmentMock,
  listDocuments: apiMocks.listDocumentsMock,
  listCustomerOrders: apiMocks.listCustomerOrdersMock,
  listOrderAttachments: apiMocks.listOrderAttachmentsMock,
  listOrderEquipmentLines: apiMocks.listOrderEquipmentLinesMock,
  listOrderRequirementLines: apiMocks.listOrderRequirementLinesMock,
  listPlanningRecords: apiMocks.listPlanningRecordsMock,
  listPlanningRecordAttachments: apiMocks.listPlanningRecordAttachmentsMock,
  listServiceCategoryOptions: apiMocks.listServiceCategoryOptionsMock,
  updatePlanningRecord: apiMocks.updatePlanningRecordMock,
  updateCustomerOrder: vi.fn(),
  updateOrderEquipmentLine: vi.fn(),
  updateOrderRequirementLine: vi.fn(),
  unlinkPlanningRecordAttachment: apiMocks.unlinkPlanningRecordAttachmentMock,
}));

vi.mock('#/sicherplan-legacy/api/planningShifts', () => ({
  PlanningShiftsApiError: planningShiftsApiErrorExports.PlanningShiftsApiError,
  createShiftPlan: apiMocks.createShiftPlanMock,
  createShiftSeries: apiMocks.createShiftSeriesMock,
  createShiftSeriesException: apiMocks.createShiftSeriesExceptionMock,
  createShiftTemplate: apiMocks.createShiftTemplateMock,
  deleteShiftSeriesException: apiMocks.deleteShiftSeriesExceptionMock,
  generateShiftSeries: apiMocks.generateShiftSeriesMock,
  getShiftPlan: apiMocks.getShiftPlanMock,
  getShiftSeries: apiMocks.getShiftSeriesMock,
  getShiftTemplate: apiMocks.getShiftTemplateMock,
  listShiftPlans: apiMocks.listShiftPlansMock,
  listShifts: apiMocks.listShiftsMock,
  listShiftSeries: apiMocks.listShiftSeriesMock,
  listShiftSeriesExceptions: apiMocks.listShiftSeriesExceptionsMock,
  listShiftTemplates: apiMocks.listShiftTemplatesMock,
  listShiftTypeOptions: apiMocks.listShiftTypeOptionsMock,
  updateShiftPlan: apiMocks.updateShiftPlanMock,
  updateShiftSeries: apiMocks.updateShiftSeriesMock,
  updateShiftSeriesException: apiMocks.updateShiftSeriesExceptionMock,
}));

vi.mock('#/sicherplan-legacy/api/planningStaffing', () => ({
  applyAssignmentStep: apiMocks.applyAssignmentStepMock,
  bulkApplyDemandGroups: apiMocks.bulkApplyDemandGroupsMock,
  bulkUpdateDemandGroups: apiMocks.bulkUpdateDemandGroupsMock,
  getAssignmentStepSnapshot: apiMocks.getAssignmentStepSnapshotMock,
  listAssignmentStepCandidates: apiMocks.listAssignmentStepCandidatesMock,
  listDemandGroups: apiMocks.listDemandGroupsMock,
  listTeams: apiMocks.listTeamsMock,
  previewAssignmentStepApply: apiMocks.previewAssignmentStepApplyMock,
  updateDemandGroup: apiMocks.updateDemandGroupMock,
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
  notification: notificationMocks,
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

function buildDemandGroupsDraftKey(planningEntityId = 'site-1', planningEntityType = 'site') {
  return buildWizardDraftStorageKey(
    {
      customerId: 'customer-1',
      planningEntityId,
      planningEntityType,
      tenantId: 'tenant-1',
    },
    'demand-groups',
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

async function saveCurrentSeries(wrapper: ReturnType<typeof mount>) {
  await wrapper.get('[data-testid="customer-new-plan-save-series"]').trigger('click');
  await flushPromises();
  await settleLoadingRender();
}

async function openNewExceptionDialog(wrapper: ReturnType<typeof mount>) {
  await wrapper.get('[data-testid="customer-new-plan-new-exception"]').trigger('click');
  await flushPromises();
  await nextTick();
}

async function saveCurrentException(wrapper: ReturnType<typeof mount>) {
  await wrapper.get('[data-testid="customer-new-plan-save-exception"]').trigger('click');
  await flushPromises();
}

function deferred<T>() {
  let reject!: (reason?: unknown) => void;
  let resolve!: (value: T | PromiseLike<T>) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, reject, resolve };
}

async function settleLoadingRender() {
  for (let index = 0; index < 6; index += 1) {
    await Promise.resolve();
    await nextTick();
  }
}

async function waitForCondition(assertion: () => void | boolean, attempts = 20) {
  let lastError: unknown;
  for (let index = 0; index < attempts; index += 1) {
    try {
      const result = assertion();
      if (result !== false) {
        return;
      }
    } catch (error) {
      lastError = error;
    }
    await flushPromises();
    await settleLoadingRender();
  }
  if (lastError) {
    throw lastError;
  }
  throw new Error('Condition not met within retry budget');
}

async function waitForDemandGroupsStepReady(
  wrapper: ReturnType<typeof mount>,
  expectedGeneratedShiftCount?: number,
) {
  await waitForCondition(() => {
    if (wrapper.find('[data-testid="customer-new-plan-demand-groups-loading"]').exists()) {
      return false;
    }
    if (typeof expectedGeneratedShiftCount === 'number') {
      const countText = wrapper.get('[data-testid="customer-new-plan-demand-groups-generated-count"]').text();
      if (countText !== String(expectedGeneratedShiftCount)) {
        return false;
      }
    }
    return true;
  });
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
      'order-scope-documents': { completed: true, dirty: false, error: '', loading: false },
      'planning-record-overview': { completed: false, dirty: false, error: '', loading: false },
      'planning-record-documents': { completed: false, dirty: false, error: '', loading: false },
      'shift-plan': { completed: false, dirty: false, error: '', loading: false },
      'series-exceptions': { completed: false, dirty: false, error: '', loading: false },
      'demand-groups': { completed: false, dirty: false, error: '', loading: false },
      'assignments': { completed: false, dirty: false, error: '', loading: false },
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
    vi.stubGlobal('confirm', confirmMock);
    routerPushMock.mockReset();
    routerReplaceMock.mockReset();
    confirmMock.mockReset();
    confirmMock.mockReturnValue(true);
    apiMocks.createPlanningRecordMock.mockReset();
    apiMocks.createPlanningSetupRecordMock.mockReset();
    apiMocks.createPlanningRecordAttachmentMock.mockReset();
    apiMocks.createShiftPlanMock.mockReset();
    apiMocks.createShiftSeriesExceptionMock.mockReset();
    apiMocks.createShiftSeriesMock.mockReset();
    apiMocks.createShiftTemplateMock.mockReset();
    apiMocks.deleteShiftSeriesExceptionMock.mockReset();
    apiMocks.generateShiftSeriesMock.mockReset();
    apiMocks.bulkApplyDemandGroupsMock.mockReset();
    apiMocks.bulkUpdateDemandGroupsMock.mockReset();
    apiMocks.applyAssignmentStepMock.mockReset();
    apiMocks.getAssignmentStepSnapshotMock.mockReset();
    apiMocks.getCustomerOrderMock.mockReset();
    apiMocks.getPlanningRecordMock.mockReset();
    apiMocks.getShiftPlanMock.mockReset();
    apiMocks.getShiftSeriesMock.mockReset();
    apiMocks.getShiftTemplateMock.mockReset();
    apiMocks.listAssignmentStepCandidatesMock.mockReset();
    apiMocks.listDemandGroupsMock.mockReset();
    apiMocks.listTeamsMock.mockReset();
    apiMocks.linkOrderAttachmentMock.mockReset();
    apiMocks.linkPlanningRecordAttachmentMock.mockReset();
    apiMocks.listCustomerOrdersMock.mockReset();
    apiMocks.listDocumentsMock.mockReset();
    apiMocks.listOrderAttachmentsMock.mockReset();
    apiMocks.listOrderEquipmentLinesMock.mockReset();
    apiMocks.listOrderRequirementLinesMock.mockReset();
    apiMocks.listPlanningRecordsMock.mockReset();
    apiMocks.listPlanningRecordAttachmentsMock.mockReset();
    apiMocks.listPlanningSetupRecordsMock.mockReset();
    apiMocks.listServiceCategoryOptionsMock.mockReset();
    apiMocks.listTradeFairZonesMock.mockReset();
    apiMocks.listShiftPlansMock.mockReset();
    apiMocks.listShiftsMock.mockReset();
    apiMocks.listShiftSeriesExceptionsMock.mockReset();
    apiMocks.listShiftSeriesMock.mockReset();
    apiMocks.listShiftTemplatesMock.mockReset();
    apiMocks.listShiftTypeOptionsMock.mockReset();
    apiMocks.previewAssignmentStepApplyMock.mockReset();
    apiMocks.updateDemandGroupMock.mockReset();
    employeeAdminMocks.listEmployeeGroupsMock.mockReset();
    employeeAdminMocks.listFunctionTypesMock.mockReset();
    employeeAdminMocks.listQualificationTypesMock.mockReset();
    apiMocks.updatePlanningRecordMock.mockReset();
    apiMocks.updateShiftPlanMock.mockReset();
    apiMocks.updateShiftSeriesExceptionMock.mockReset();
    apiMocks.updateShiftSeriesMock.mockReset();
    apiMocks.unlinkPlanningRecordAttachmentMock.mockReset();
    notificationMocks.error.mockReset();
    notificationMocks.info.mockReset();
    notificationMocks.success.mockReset();
    notificationMocks.warning.mockReset();

    apiMocks.getCustomerOrderMock.mockResolvedValue(buildOrder());
    apiMocks.listCustomerOrdersMock.mockResolvedValue([buildOrder()]);
    apiMocks.listOrderEquipmentLinesMock.mockResolvedValue([]);
    apiMocks.listOrderRequirementLinesMock.mockResolvedValue([]);
    apiMocks.listOrderAttachmentsMock.mockResolvedValue([]);
    apiMocks.listDocumentsMock.mockResolvedValue([
      { id: 'document-1', tenant_id: 'tenant-1', title: 'Safety concept', current_version_no: 1, status: 'active' },
    ]);
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
    apiMocks.listServiceCategoryOptionsMock.mockResolvedValue([]);
    apiMocks.listShiftPlansMock.mockResolvedValue([]);
    apiMocks.listShiftsMock.mockResolvedValue([]);
    apiMocks.listShiftTemplatesMock.mockResolvedValue([{ id: 'template-1', tenant_id: 'tenant-1', code: 'TPL-1', label: 'Tagdienst Vorlage', local_start_time: '08:00', local_end_time: '16:00', default_break_minutes: 30, shift_type_code: 'day', status: 'active', version_no: 1 }]);
    apiMocks.listShiftTypeOptionsMock.mockResolvedValue([{ code: 'day', label: 'Day shift' }]);
    apiMocks.listTeamsMock.mockResolvedValue([]);
    employeeAdminMocks.listEmployeeGroupsMock.mockResolvedValue([]);
    employeeAdminMocks.listFunctionTypesMock.mockResolvedValue([]);
    employeeAdminMocks.listQualificationTypesMock.mockResolvedValue([]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([]);
    apiMocks.getAssignmentStepSnapshotMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      order: {
        order_id: 'order-1',
        order_no: 'ORD-1000',
        customer_id: 'customer-1',
        planning_record_id: 'record-1',
        planning_record_name: 'Werk Nord Sommer',
        planning_mode_code: 'site',
      },
      shift_plan: {
        shift_plan_id: 'plan-1',
        shift_plan_name: 'Werk Nord / Schichtplan',
        shift_series_id: 'series-1',
        shift_series_label: 'Tagdienst',
        workforce_scope_code: 'internal',
        planning_from: '2026-06-01',
        planning_to: '2026-06-10',
        project_start: '2026-06-01',
        project_end: '2026-06-10',
        default_month: '2026-06-01',
        active_months: ['2026-06-01'],
      },
      generated_shift_count: 0,
      demand_group_summary_count: 0,
      editable_flag: true,
      lock_reason_codes: [],
      demand_group_summaries: [],
      day_summaries: [],
      calendar_cells: [],
      candidates: [],
    });
    apiMocks.listAssignmentStepCandidatesMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      generated_shift_count: 0,
      candidates: [],
    });
    apiMocks.previewAssignmentStepApplyMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      actor_kind: 'employee',
      actor_id: 'employee-1',
      requested_count: 0,
      accepted_count: 0,
      rejected_count: 0,
      created_assignment_ids: [],
      results: [],
    });
    apiMocks.applyAssignmentStepMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      actor_kind: 'employee',
      actor_id: 'employee-1',
      requested_count: 0,
      accepted_count: 0,
      rejected_count: 0,
      created_assignment_ids: [],
      results: [],
    });
    apiMocks.listShiftSeriesMock.mockResolvedValue([]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.getPlanningRecordMock.mockResolvedValue(buildPlanningRecord());
    apiMocks.getShiftPlanMock.mockResolvedValue(buildShiftPlan());
    apiMocks.getShiftSeriesMock.mockResolvedValue(buildSeries());
    apiMocks.bulkApplyDemandGroupsMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      apply_mode: 'upsert_matching',
      target_shift_count: 2,
      template_count: 1,
      created_count: 1,
      updated_count: 1,
      skipped_count: 0,
      affected_demand_group_ids: ['dg-1'],
      results: [],
    });
    apiMocks.bulkUpdateDemandGroupsMock.mockResolvedValue({
      tenant_id: 'tenant-1',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      matched_count: 2,
      updated_count: 2,
      skipped_count: 0,
      conflict_count: 0,
      updated_demand_group_ids: ['dg-1', 'dg-2'],
      results: [],
    });
    apiMocks.updateDemandGroupMock.mockResolvedValue({
      id: 'dg-1',
      tenant_id: 'tenant-1',
      shift_id: 'shift-1',
      function_type_id: 'function-1',
      qualification_type_id: null,
      min_qty: 1,
      target_qty: 2,
      mandatory_flag: true,
      sort_order: 1,
      remark: null,
      status: 'active',
      version_no: 2,
      created_at: '2026-07-01T08:00:00Z',
      updated_at: '2026-07-01T08:00:00Z',
      archived_at: null,
    });
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

  it('keeps the step shell visible while order details load locally', async () => {
    const orders = deferred<any[]>();
    apiMocks.listCustomerOrdersMock.mockReturnValueOnce(orders.promise);

    const wrapper = mountStep('order-details', {
      current_step: 'order-details',
      order_id: 'order-1',
    });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-order-details"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-mode-existing-label"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-order-list"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-loading"]').exists()).toBe(true);
    expect(wrapper.find('.ant-spin').exists()).toBe(false);

    orders.resolve([buildOrder({ title: 'Werk Nord geladen' })]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-order-loading"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-existing-order-row"]').text()).toContain('Werk Nord geladen');
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-order-details"]').exists()).toBe(true);
  });

  it('shows a local equipment-lines indicator without replacing the editor', async () => {
    const equipmentLines = deferred<any[]>();
    apiMocks.listOrderEquipmentLinesMock.mockReturnValueOnce(equipmentLines.promise);

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-equipment-lines"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-item"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(true);

    equipmentLines.resolve([{ id: 'equipment-line-1', equipment_item_id: 'equipment-1', required_qty: 3, notes: null }]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('3');
  });

  it('renders the combined order-scope step with all three subsection cards and controls', async () => {
    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-documents-step"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-equipment-card"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-requirements-card"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-documents-card"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-item"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-type"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-upload-title"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.forms.linkExistingDocument');
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-picker-open"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-link-id"]').exists()).toBe(false);
  });

  it('opens the order document picker with local loading, keeps the step visible, and renders search results', async () => {
    const documents = deferred<any[]>();
    apiMocks.listDocumentsMock.mockReturnValue(documents.promise);

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-order-document-picker-open"]').trigger('click');
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-order-document-picker-modal"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-documents-step"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-loading"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.forms.documentPickerLoading');
    await wrapper.get('[data-testid="customer-new-plan-order-document-search"]').setValue('contract');
    await wrapper.get('[data-testid="customer-new-plan-order-document-search"]').trigger('keyup.enter');

    documents.resolve([
      {
        id: 'doc-1',
        tenant_id: 'tenant-1',
        title: 'Customer contract RheinForum with an intentionally long descriptive title for wrapping checks',
        current_version_no: 1,
        status: 'active',
        document_type: { id: 'doc-type-1', key: 'contract', name: 'Contract document type with a long label' },
        source_label: 'rheinforum-contract-attachment-final-version-signed.pdf',
      },
      { id: 'doc-2', tenant_id: 'tenant-1', title: 'Security concept attachment', current_version_no: 2, status: 'active' },
    ]);
    await flushPromises();

    expect(wrapper.findAll('[data-testid="customer-new-plan-order-document-result-row"]')).toHaveLength(2);
    expect(wrapper.find('.sp-customer-plan-wizard-step__document-picker-modal').exists()).toBe(true);
    expect(wrapper.find('.sp-customer-plan-wizard-step__document-picker-results').exists()).toBe(true);
    expect(wrapper.find('.sp-customer-plan-wizard-step__document-picker-row').exists()).toBe(true);
    expect(wrapper.find('.sp-customer-plan-wizard-step__document-picker-meta').exists()).toBe(true);
    expect(wrapper.text()).toContain('Customer contract RheinForum with an intentionally long descriptive title for wrapping checks');
    expect(wrapper.text()).toContain('rheinforum-contract-attachment-final-version-signed.pdf');
    expect(wrapper.text()).toContain('Security concept attachment');
  });

  it('clears stale order document picker results and shows the empty state', async () => {
    apiMocks.listDocumentsMock
      .mockResolvedValueOnce([
        { id: 'doc-1', tenant_id: 'tenant-1', title: 'Customer contract RheinForum', current_version_no: 1, status: 'active' },
      ])
      .mockResolvedValueOnce([]);

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-order-document-picker-open"]').trigger('click');
    await flushPromises();
    expect(wrapper.findAll('[data-testid="customer-new-plan-order-document-result-row"]')).toHaveLength(1);

    await wrapper.get('[data-testid="customer-new-plan-order-document-search"]').setValue('unknown');
    await wrapper.get('[data-testid="customer-new-plan-order-document-search"]').trigger('keyup.enter');
    await flushPromises();

    expect(wrapper.findAll('[data-testid="customer-new-plan-order-document-result-row"]')).toHaveLength(0);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.forms.documentPickerEmpty');
  });

  it('clears a selected order document and blocks linking until another document is selected', async () => {
    apiMocks.listDocumentsMock.mockResolvedValueOnce([
      { id: 'doc-1', tenant_id: 'tenant-1', title: 'Customer contract RheinForum', current_version_no: 1, status: 'active' },
    ]);
    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-order-document-picker-open"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-order-document-result-row"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-selected"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-order-document-clear"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-selected"]').exists()).toBe(false);

    await wrapper.get('[data-testid="customer-new-plan-link-order-document"]').trigger('click');
    await flushPromises();
    expect(apiMocks.linkOrderAttachmentMock).toHaveBeenCalledTimes(0);
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.orderDocumentLinkIncomplete',
    }));
  });

  it('restores an order document link draft selection state and label', async () => {
    window.sessionStorage.setItem(
      buildWizardDraftStorageKey(
        { customerId: 'customer-1', planningEntityId: 'site-1', planningEntityType: 'site', tenantId: 'tenant-1' },
        'order-documents',
      ),
      JSON.stringify({
        link: {
          document_id: 'doc-draft-1',
          label: 'Draft link label',
        },
      }),
    );

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-order-document-selected"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-order-document-link-label"]').element as HTMLInputElement).value).toBe(
      'Draft link label',
    );
  });

  it('shows independent local loading indicators for all order-scope cards and keeps the combined step mounted', async () => {
    const equipmentLines = deferred<any[]>();
    const requirementLines = deferred<any[]>();
    const attachments = deferred<any[]>();
    apiMocks.listOrderEquipmentLinesMock.mockReturnValueOnce(equipmentLines.promise);
    apiMocks.listOrderRequirementLinesMock.mockReturnValueOnce(requirementLines.promise);
    apiMocks.listOrderAttachmentsMock.mockReturnValueOnce(attachments.promise);

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-documents-step"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-lines-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-documents-loading"]').exists()).toBe(true);

    equipmentLines.resolve([{ id: 'equipment-line-1', equipment_item_id: 'equipment-1', required_qty: 4, notes: null }]);
    requirementLines.resolve([{ id: 'requirement-line-1', requirement_type_id: 'requirement-type-1', function_type_id: null, qualification_type_id: null, min_qty: 1, target_qty: 2, notes: null }]);
    attachments.resolve([{ id: 'doc-1', tenant_id: 'tenant-1', title: 'Dienstanweisung', current_version_no: 1, status: 'active' }]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-order-scope-documents-step"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-lines-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-order-documents-loading"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('4');
    expect(wrapper.text()).toContain('1 / 2');
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-list"]').text()).toContain('Dienstanweisung');
  });

  it('clears order-scope section loading when an in-flight load becomes stale before settling', async () => {
    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();

    apiMocks.listOrderEquipmentLinesMock.mockReset();
    apiMocks.listOrderRequirementLinesMock.mockReset();
    apiMocks.listOrderAttachmentsMock.mockReset();

    const equipmentLines = deferred<any[]>();
    const requirementLines = deferred<any[]>();
    const attachments = deferred<any[]>();
    apiMocks.listOrderEquipmentLinesMock.mockReturnValueOnce(equipmentLines.promise);
    apiMocks.listOrderRequirementLinesMock.mockReturnValueOnce(requirementLines.promise);
    apiMocks.listOrderAttachmentsMock.mockReturnValueOnce(attachments.promise);

    let requestCurrent = true;
    const loadPromise = (wrapper.vm as any).$?.setupState.loadOrderState(() => requestCurrent);
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-lines-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-documents-loading"]').exists()).toBe(true);

    requestCurrent = false;
    equipmentLines.resolve([]);
    requirementLines.resolve([]);
    attachments.resolve([]);
    await loadPromise;
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-lines-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-order-documents-loading"]').exists()).toBe(false);
  });

  it('shows a local requirement-lines indicator without replacing the editor', async () => {
    const requirementLines = deferred<any[]>();
    apiMocks.listOrderRequirementLinesMock.mockReturnValueOnce(requirementLines.promise);

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-requirement-lines"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-type"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-requirement-lines-loading"]').exists()).toBe(true);

    requirementLines.resolve([{ id: 'requirement-line-1', requirement_type_id: 'requirement-type-1', function_type_id: null, qualification_type_id: null, min_qty: 1, target_qty: 2, notes: null }]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-requirement-lines-loading"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('1 / 2');
  });

  it('shows local order-document loading and then renders loaded documents', async () => {
    const attachments = deferred<any[]>();
    apiMocks.listOrderAttachmentsMock.mockReturnValueOnce(attachments.promise);

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-order-documents"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-document-upload-title"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-order-documents-loading"]').exists()).toBe(true);

    attachments.resolve([{ id: 'doc-1', tenant_id: 'tenant-1', title: 'Dienstanweisung', current_version_no: 1, status: 'active' }]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-order-documents-loading"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-order-document-list"]').text()).toContain('Dienstanweisung');
  });

  it('shows planning-record list and detail loading locally', async () => {
    const records = deferred<any[]>();
    const detail = deferred<any>();
    apiMocks.listPlanningRecordsMock.mockReturnValueOnce(records.promise);
    apiMocks.getPlanningRecordMock.mockReturnValueOnce(detail.promise);

    const wrapper = mountStep('planning-record-overview', {
      current_step: 'planning-record-overview',
      planning_record_id: 'record-1',
    });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-planning-record-overview"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-loading"]').exists()).toBe(true);

    records.resolve([{ id: 'record-1', name: 'Werk Nord Sommer', planning_from: '2026-06-01', planning_to: '2026-06-10' }]);
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-detail-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-details"]').exists()).toBe(true);
    expect(
      wrapper
        .get('[data-testid="customer-new-plan-planning-record-detail-loading"]')
        .element.closest('[data-testid="customer-new-plan-planning-record-details"]'),
    ).toBeNull();

    detail.resolve(buildPlanningRecord({ name: 'Detail geladen' }));
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-detail-loading"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe('Detail geladen');
  });

  it('shows planning-document loading locally', async () => {
    const attachments = deferred<any[]>();
    apiMocks.listPlanningRecordAttachmentsMock.mockReturnValueOnce(attachments.promise);

    const wrapper = mountStep('planning-record-documents', {
      current_step: 'planning-record-documents',
      planning_record_id: 'record-1',
    });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-planning-record-documents"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-document-title"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-documents-loading"]').exists()).toBe(true);

    attachments.resolve([{ id: 'planning-doc-1', tenant_id: 'tenant-1', title: 'Wachbuch', current_version_no: 1, status: 'active' }]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-documents-loading"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('Wachbuch');
  });

  it('shows shift-plan list and detail loading locally', async () => {
    const plans = deferred<any[]>();
    const detail = deferred<any>();
    apiMocks.listShiftPlansMock.mockReturnValueOnce(plans.promise);
    apiMocks.getShiftPlanMock.mockReturnValueOnce(detail.promise);

    const wrapper = mountStep('shift-plan', {
      current_step: 'shift-plan',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
    });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-shift-plan"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-shift-plan-loading"]').exists()).toBe(true);

    plans.resolve([{ id: 'plan-1', name: 'Werk Nord / Plan', planning_from: '2026-06-01', planning_to: '2026-06-10' }]);
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-shift-plan-detail-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-shift-plan-name"]').exists()).toBe(true);

    detail.resolve(buildShiftPlan({ name: 'Schichtplan geladen' }));
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-shift-plan-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-shift-plan-detail-loading"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toBe('Schichtplan geladen');
  });

  it('shows series and exceptions loading locally', async () => {
    const seriesRows = deferred<any[]>();
    apiMocks.listShiftSeriesMock.mockReturnValueOnce(seriesRows.promise);

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
    });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-series-loading"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-series-label"]').exists()).toBe(true);

    seriesRows.resolve([buildSeries({ label: 'Tagdienst geladen' })]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-series-loading"]').exists()).toBe(false);
    expect(wrapper.text()).toContain('Tagdienst geladen');
  });

  it('keeps dirty equipment drafts visible while saved data reloads', async () => {
    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').setValue(7);
    const reload = deferred<any[]>();
    apiMocks.listOrderEquipmentLinesMock.mockReturnValueOnce(reload.promise);

    void (wrapper.vm as any).$?.setupState.loadOrderState();
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').element as HTMLInputElement).value).toBe('7');

    reload.resolve([]);
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-equipment-lines-loading"]').exists()).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').element as HTMLInputElement).value).toBe('7');
  });

  it('restores old subsection draft keys inside the combined order-scope step', async () => {
    window.sessionStorage.setItem(
      buildWizardDraftStorageKey(
        {
          customerId: 'customer-1',
          planningEntityId: 'site-1',
          planningEntityType: 'site',
          tenantId: 'tenant-1',
        },
        'equipment-lines',
      ),
      JSON.stringify({
        equipment_item_id: 'equipment-1',
        notes: 'Restored equipment draft',
        required_qty: 5,
      }),
    );
    window.sessionStorage.setItem(
      buildWizardDraftStorageKey(
        {
          customerId: 'customer-1',
          planningEntityId: 'site-1',
          planningEntityType: 'site',
          tenantId: 'tenant-1',
        },
        'requirement-lines',
      ),
      JSON.stringify({
        function_type_id: '',
        min_qty: 1,
        notes: 'Restored requirement draft',
        qualification_type_id: '',
        requirement_type_id: 'requirement-type-1',
        target_qty: 2,
      }),
    );

    const wrapper = mountStep('order-scope-documents', { current_step: 'order-scope-documents' });
    await flushPromises();

    expect((wrapper.get('[data-testid="customer-new-plan-equipment-required-qty"]').element as HTMLInputElement).value).toBe('5');
    expect((wrapper.get('[data-testid="customer-new-plan-equipment-notes"]').element as HTMLTextAreaElement).value).toBe('Restored equipment draft');
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-min-qty"]').element as HTMLInputElement).value).toBe('1');
    expect((wrapper.get('[data-testid="customer-new-plan-requirement-notes"]').element as HTMLTextAreaElement).value).toBe('Restored requirement draft');
  });

  it('keeps stale order-list requests from hiding newer loading or overwriting current data', async () => {
    const wrapper = mountStep('order-details', { current_step: 'order-details' });
    await flushPromises();
    apiMocks.listCustomerOrdersMock.mockReset();
    const first = deferred<any[]>();
    const second = deferred<any[]>();
    apiMocks.listCustomerOrdersMock
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);

    let firstCurrent = true;
    const setupState = (wrapper.vm as any).$?.setupState;
    void setupState.loadCustomerOrderRows(() => firstCurrent);
    await settleLoadingRender();
    expect(wrapper.find('[data-testid="customer-new-plan-order-loading"]').exists()).toBe(true);

    void setupState.loadCustomerOrderRows(() => true);
    await settleLoadingRender();
    expect(wrapper.find('[data-testid="customer-new-plan-order-loading"]').exists()).toBe(true);

    second.resolve([buildOrder({ id: 'order-latest', order_no: 'ORD-LATEST', title: 'Latest order' })]);
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-order-loading"]').exists()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-existing-order-list"]').text()).toContain('Latest order');

    firstCurrent = false;
    first.resolve([buildOrder({ id: 'order-stale', order_no: 'ORD-STALE', title: 'Stale order' })]);
    await flushPromises();
    expect(wrapper.get('[data-testid="customer-new-plan-existing-order-list"]').text()).toContain('Latest order');
    expect(wrapper.get('[data-testid="customer-new-plan-existing-order-list"]').text()).not.toContain('Stale order');
  });

  it('renders loader failures as local errors without replacing the step shell', async () => {
    const failure = deferred<any[]>();
    apiMocks.listPlanningRecordsMock.mockReturnValueOnce(failure.promise);

    const wrapper = mountStep('planning-record-overview', {
      current_step: 'planning-record-overview',
      planning_record_id: '',
    });
    await settleLoadingRender();
    failure.reject(new Error('network failed'));
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-planning-record-overview"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-planning-records"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.errors.planningRecordLoad');
    expect(routerReplaceMock).not.toHaveBeenCalled();
  });

  it('renders a planning context selector instead of a dead-end when planning context is missing', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-blocked"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-context-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-planning-records"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-details"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-context-family"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-context-entry"]').exists()).toBe(true);
  });

  it('renders planning context controls inside the planning-record editor', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-context-panel"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-card"]').exists()).toBe(true);
    const stepPanel = wrapper.get('[data-testid="customer-new-plan-step-panel-planning-record-overview"]');
    expect(stepPanel.classes()).toContain('sp-customer-plan-wizard-step__panel');
    expect(stepPanel.findAll('.sp-customer-plan-wizard-step__panel')).toHaveLength(0);
    expect(wrapper.get('[data-testid="customer-new-plan-planning-record-card"]').classes()).not.toContain(
      'sp-customer-plan-wizard-step__panel',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-existing-planning-records"]').classes()).toContain(
      'sp-customer-plan-wizard-step__planning-record-subsection',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-planning-record-editor"]').classes()).toContain(
      'sp-customer-plan-wizard-step__planning-record-subsection',
    );
    expect(wrapper.find('.sp-customer-plan-wizard-step__planning-record-divider').exists()).toBe(true);
    const modeSelect = wrapper.get('[data-testid="customer-new-plan-planning-context-family"]');
    const entrySelect = wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]');
    expect(modeSelect.element.tagName).toBe('SELECT');
    expect(entrySelect.element.tagName).toBe('SELECT');
    expect(modeSelect.attributes('readonly')).toBeUndefined();
    expect(entrySelect.attributes('readonly')).toBeUndefined();
    expect(modeSelect.element.closest('[data-testid="customer-new-plan-planning-record-editor"]')).toBeTruthy();
    expect(entrySelect.element.closest('[data-testid="customer-new-plan-planning-record-editor"]')).toBeTruthy();
    const createEntryButton = wrapper.get('[data-testid="customer-new-plan-planning-record-create-entry"]');
    expect(createEntryButton.element.closest('[data-testid="customer-new-plan-planning-record-editor"]')).toBeTruthy();
    expect(createEntryButton.element.closest('[data-testid="customer-new-plan-existing-planning-records"]')).toBeNull();
    expect(createEntryButton.element.closest('.sp-customer-plan-wizard-step__planning-record-subsection-header--with-action')).toBeTruthy();
    expect(wrapper.find('[data-testid="customer-new-plan-save-planning-record"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-clear-planning-record-draft"]').exists()).toBe(true);
    expect(
      wrapper.get('[data-testid="customer-new-plan-existing-planning-records"]').element.closest('[data-testid="customer-new-plan-planning-record-card"]'),
    ).toBe(
      wrapper.get('[data-testid="customer-new-plan-planning-record-editor"]').element.closest('[data-testid="customer-new-plan-planning-record-card"]'),
    );

    expect(entrySelect.text()).toContain('Werk Nord');
    expect(entrySelect.text()).not.toContain('Arena');
    await modeSelect.setValue('event_venue');
    await flushPromises();
    expect(wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').text()).toContain('Arena');
    expect(wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').text()).not.toContain('Werk Nord');
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

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    expect(wrapper.emitted('saved-context')).toBeUndefined();
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(apiMocks.getCustomerOrderMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listOrderAttachmentsMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listOrderEquipmentLinesMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listOrderRequirementLinesMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.listPlanningSetupRecordsMock).toHaveBeenCalledTimes(0);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').element as HTMLSelectElement).value).toBe('site-1');
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
    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('venue-1');
    await flushPromises();
    const setupState = (wrapper.vm as any).$?.setupState;
    expect(setupState.planningEntityId).toBe('venue-1');
    expect(setupState.planningRecordDraft.planning_mode_code).toBe('event');
    expect(wrapper.emitted('saved-context')).toBeUndefined();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('trade_fair');
    await flushPromises();
    expect(setupState.planningEntityId).toBe('');
    apiMocks.listTradeFairZonesMock.mockClear();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('fair-1');
    await flushPromises();
    expect(setupState.planningEntityId).toBe('fair-1');
    expect(setupState.planningRecordDraft.planning_mode_code).toBe('trade_fair');
    expect(apiMocks.listTradeFairZonesMock).toHaveBeenCalledTimes(1);
    expect(wrapper.emitted('saved-context')).toBeUndefined();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('patrol_route');
    await flushPromises();
    apiMocks.listTradeFairZonesMock.mockClear();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('route-1');
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
    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    expect(apiMocks.listPlanningRecordsMock).toHaveBeenCalledWith('tenant-1', 'token-1', {
      order_id: 'order-1',
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
    });
    expect(wrapper.find('[data-testid="customer-new-plan-existing-planning-records"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(1);
    expect(wrapper.findAll('[data-testid="customer-new-plan-edit-planning-record"]')).toHaveLength(0);
  });

  it('keeps the existing planning record list visible after repeated async flushes for the same site context', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlanningRecord({ id: 'record-1', name: 'RFK Nordtor Sommer' }),
    ]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await settleLoadingRender();

    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-existing-planning-records"]').text()).toContain('RFK Nordtor Sommer');
  });

  it('selects an existing operational planning record for the wizard when the row is clicked', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    routerReplaceMock.mockClear();
    apiMocks.getPlanningRecordMock.mockClear();

    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledWith('tenant-1', 'record-1', 'token-1');
    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').classes()).toContain(
      'sp-customer-plan-wizard-step__list-row--selected',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Sommer',
    );
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toEqual({
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
    });
    expect((wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').element as HTMLSelectElement).value).toBe('site');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').element as HTMLSelectElement).value).toBe('site-1');
    expect(wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').text()).toContain('SITE-1');
    expect(wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').text()).toContain('Werk Nord');
    expect(wrapper.text()).not.toContain('sicherplan.customerPlansWizard.forms.noPlanningEntriesFoundForCustomer');
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(true);
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(wrapper.emitted('step-ui-state')?.some((event) => event[0] === 'planning-record-overview' && (event[1] as Record<string, unknown>).dirty === false && (event[1] as Record<string, unknown>).error === '')).toBe(true);
  });

  it('treats a second click on the same selected planning record row as a strict no-op', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    const row = wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]');
    await row.trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledTimes(1);
    const savedContextCountAfterFirstClick = wrapper.emitted('saved-context')?.length ?? 0;
    const successToastCountAfterFirstClick = notificationMocks.success.mock.calls.length;
    const nameAfterFirstClick = (wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value;

    await row.trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listPlanningRecordsMock).toHaveBeenCalledTimes(1);
    expect(wrapper.emitted('saved-context')?.length ?? 0).toBe(savedContextCountAfterFirstClick);
    expect(notificationMocks.success.mock.calls.length).toBe(successToastCountAfterFirstClick);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      nameAfterFirstClick,
    );
    expect(wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').classes()).toContain(
      'sp-customer-plan-wizard-step__list-row--selected',
    );
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(routerPushMock).not.toHaveBeenCalled();
  });

  it('switches to a different existing planning record when a different row is clicked', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlanningRecord({ id: 'record-1', name: 'Werk Nord Sommer' }),
      buildPlanningRecord({ id: 'record-2', name: 'Werk Nord Nacht' }),
    ]);
    apiMocks.getPlanningRecordMock.mockImplementation((_tenantId, recordId: string) =>
      Promise.resolve(
        buildPlanningRecord({
          id: recordId,
          name: recordId === 'record-2' ? 'Werk Nord Nacht' : 'Werk Nord Sommer',
        }),
      ),
    );

    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    const rows = wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]');
    await rows[0]!.trigger('click');
    await flushPromises();
    await rows[1]!.trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledTimes(2);
    expect(apiMocks.getPlanningRecordMock).toHaveBeenLastCalledWith('tenant-1', 'record-2', 'token-1');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Nacht',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Nacht',
    );
  });

  it('keeps the newer selected planning record when an older detail response resolves late', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlanningRecord({ id: 'record-1', name: 'Werk Nord Sommer' }),
      buildPlanningRecord({ id: 'record-2', name: 'Werk Nord Nacht' }),
    ]);
    const firstDetail = deferred<ReturnType<typeof buildPlanningRecord>>();
    const secondDetail = deferred<ReturnType<typeof buildPlanningRecord>>();
    apiMocks.getPlanningRecordMock.mockImplementation((_tenantId, recordId: string) => {
      if (recordId === 'record-1') {
        return firstDetail.promise;
      }
      if (recordId === 'record-2') {
        return secondDetail.promise;
      }
      return Promise.resolve(buildPlanningRecord({ id: recordId }));
    });

    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    const rows = wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]');
    await rows[0]!.trigger('click');
    await flushPromises();
    await rows[1]!.trigger('click');
    await flushPromises();

    secondDetail.resolve(buildPlanningRecord({
      id: 'record-2',
      name: 'Werk Nord Nacht',
      notes: 'Nachtnotiz',
      planning_from: '2026-07-01',
      planning_to: '2026-07-10',
      site_detail: { site_id: 'site-1', watchbook_scope_note: 'Nacht-Wachbuch' },
    }));
    await flushPromises();

    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Nacht',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Nacht',
    );
    expect(rows[1]!.classes()).toContain('sp-customer-plan-wizard-step__list-row--selected');

    firstDetail.resolve(buildPlanningRecord({
      id: 'record-1',
      name: 'Werk Nord Sommer',
      notes: 'Sommernotiz',
      site_detail: { site_id: 'site-1', watchbook_scope_note: 'Sommer-Wachbuch' },
    }));
    await flushPromises();
    await settleLoadingRender();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledTimes(2);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Nacht',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').element as HTMLInputElement).value).toBe(
      '2026-07-01',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').element as HTMLInputElement).value).toBe(
      '2026-07-10',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Nacht',
    );
    expect(rows[1]!.classes()).toContain('sp-customer-plan-wizard-step__list-row--selected');
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toEqual({
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-2',
    });
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(routerPushMock).not.toHaveBeenCalled();
  });

  it('recovers safely when the selected row id matches but the hydrated planning record is missing', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    setupState.selectedPlanningRecord = null;
    setupState.editingExistingPlanningRecordId = '';
    setupState.planningRecordDraft.name = '';
    apiMocks.getPlanningRecordMock.mockClear();
    const savedContextCountBeforeRecovery = wrapper.emitted('saved-context')?.length ?? 0;

    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledTimes(1);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Sommer',
    );
    expect(wrapper.emitted('saved-context')?.length ?? 0).toBe(savedContextCountBeforeRecovery + 1);
    expect(routerReplaceMock).not.toHaveBeenCalled();
    expect(routerPushMock).not.toHaveBeenCalled();
  });

  it('does not re-bootstrap the planning-record step when parent route state catches up after local record selection', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlanningRecord({ id: 'record-1', name: 'Werk Nord Sommer' }),
      buildPlanningRecord({ id: 'record-2', name: 'Werk Nord Nacht' }),
    ]);
    apiMocks.getPlanningRecordMock.mockImplementation((_tenantId, recordId: string) =>
      Promise.resolve(
        buildPlanningRecord({
          id: recordId,
          name: recordId === 'record-2' ? 'Werk Nord Nacht' : 'Werk Nord Sommer',
        }),
      ),
    );

    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    apiMocks.getPlanningRecordMock.mockClear();
    await wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')[0]!.trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledTimes(1);

    await wrapper.setProps({
      wizardState: {
        ...(wrapper.props('wizardState') as CustomerNewPlanWizardState),
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'record-1',
      },
    });
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-loading"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-detail-loading"]').exists()).toBe(false);
  });

  it('keeps the selected planning record stable when a late planning-context sync arrives without planning_record_id', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord({ id: 'record-1', name: 'Werk Nord Sommer' })]);

    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
      planning_record_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Sommer',
    );

    await wrapper.setProps({
      wizardState: {
        ...(wrapper.props('wizardState') as CustomerNewPlanWizardState),
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: '',
      },
    });
    await flushPromises();
    await flushPromises();

    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').classes()).toContain(
      'sp-customer-plan-wizard-step__list-row--selected',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Sommer',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );
    expect(routerReplaceMock).not.toHaveBeenCalled();
  });

  it('ignores a stale empty planning-record list response after a newer selection has already populated the editor', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
      planning_record_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    const first = deferred<any[]>();
    const second = deferred<any[]>();
    apiMocks.listPlanningRecordsMock.mockReset();
    apiMocks.listPlanningRecordsMock
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);

    let firstCurrent = true;
    const setupState = (wrapper.vm as any).$?.setupState;
    void setupState.loadExistingPlanningRecordRows(() => firstCurrent);
    await settleLoadingRender();

    void setupState.loadExistingPlanningRecordRows(() => true);
    await settleLoadingRender();

    second.resolve([buildPlanningRecord({ id: 'record-1', name: 'Werk Nord Sommer' })]);
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Sommer',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );

    firstCurrent = false;
    first.resolve([]);
    await flushPromises();
    await settleLoadingRender();

    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(1);
    expect(wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').classes()).toContain(
      'sp-customer-plan-wizard-step__list-row--selected',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-selected-planning-record-summary"]').text()).toContain(
      'Werk Nord Sommer',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );
    expect(routerReplaceMock).not.toHaveBeenCalled();
  });

  it('clears selected existing record state when Planning entry changes', async () => {
    apiMocks.listPlanningSetupRecordsMock.mockImplementation((entityKey: string) => {
      const map: Record<string, unknown[]> = {
        site: [
          { id: 'site-1', customer_id: 'customer-1', site_no: 'SITE-1', name: 'Werk Nord', tenant_id: 'tenant-1', status: 'active', version_no: 1 },
          { id: 'site-2', customer_id: 'customer-1', site_no: 'SITE-2', name: 'Werk Süd', tenant_id: 'tenant-1', status: 'active', version_no: 1 },
        ],
      };
      return Promise.resolve(map[entityKey] ?? []);
    });
    apiMocks.listPlanningRecordsMock.mockImplementation((_tenantId, _token, params) =>
      Promise.resolve(params?.planning_entity_id === 'site-1' ? [buildPlanningRecord()] : []),
    );
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-2');
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    expect(setupState.selectedPlanningRecord).toBeNull();
    expect(setupState.selectedExistingPlanningRecordId).toBe('');
    expect(setupState.planningEntityId).toBe('site-2');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe('');
    expect(notificationMocks.info).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.messages.planningEntryChangedForNewRecord',
    }));
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-name-error"]').exists()).toBe(true);
  });

  it('shows inline Planning Record validation errors on Next', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-planning-entry-error"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').setValue('2026-06-10');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').setValue('2026-06-01');
    await flushPromises();

    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-name-error"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-from-error"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-record-to-error"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').attributes('aria-invalid'))).toBe('true');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').attributes('aria-invalid'))).toBe('true');
  });

  it.each([
    {
      family: 'event_venue',
      mode: 'event',
      record: buildPlanningRecord({
        event_detail: { event_venue_id: 'venue-1', setup_note: null },
        planning_mode_code: 'event',
        site_detail: null,
      }),
      value: 'venue-1',
    },
    {
      family: 'trade_fair',
      mode: 'trade_fair',
      record: buildPlanningRecord({
        planning_mode_code: 'trade_fair',
        site_detail: null,
        trade_fair_detail: { trade_fair_id: 'fair-1', trade_fair_zone_id: null, stand_note: null },
      }),
      value: 'fair-1',
    },
    {
      family: 'patrol_route',
      mode: 'patrol',
      record: buildPlanningRecord({
        patrol_detail: { patrol_route_id: 'route-1', execution_note: null },
        planning_mode_code: 'patrol',
        site_detail: null,
      }),
      value: 'route-1',
    },
  ])('hydrates the planning entry from an existing $family planning record', async ({ family, mode, record, value }) => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([record]);
    apiMocks.getPlanningRecordMock.mockResolvedValue(record);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue(family);
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue(value);
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    expect((wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').element as HTMLSelectElement).value).toBe(family);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').element as HTMLSelectElement).value).toBe(value);
    expect((wrapper.vm as any).$?.setupState.planningRecordDraft.planning_mode_code).toBe(mode);
    expect(wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]')).toHaveLength(1);
    expect(wrapper.text()).not.toContain('sicherplan.customerPlansWizard.forms.noPlanningEntriesFoundForCustomer');
  });

  it('uses the selected card as the edit entry point and blocks Next when dirty', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    expect(apiMocks.getPlanningRecordMock).toHaveBeenCalledWith('tenant-1', 'record-1', 'token-1');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );

    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Werk Nord Sommer geandert');
    await flushPromises();

    expect(wrapper.emitted('step-ui-state')?.at(-1)?.[1]).toMatchObject({ dirty: true, error: '' });
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    expect(apiMocks.createPlanningRecordMock).not.toHaveBeenCalled();
    expect(apiMocks.updatePlanningRecordMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.saveOrCancelPlanningRecordEditBeforeContinue',
    }));
  });

  it('blocks Next when a clean selected planning record conflicts with wizard context', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
      planning_record_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();
    await wrapper.setProps({
      wizardState: {
        ...baseWizardState(),
        order_id: 'order-1',
        planning_entity_id: 'site-1',
        planning_entity_type: 'site',
        planning_mode_code: 'site',
        planning_record_id: 'other-record',
      },
    });
    await flushPromises();

    expect((wrapper.vm as any).$?.setupState.selectedPlanningRecord.id).toBe('record-1');
    expect((wrapper.vm as any).$?.setupState.planningRecordDirty).toBe(false);
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    expect(apiMocks.createPlanningRecordMock).not.toHaveBeenCalled();
    expect(apiMocks.updatePlanningRecordMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.savePlanningRecordBeforeContinue',
    }));
  });

  it('fully replaces planning-record editor values when switching existing records', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([
      buildPlanningRecord({
        id: 'record-1',
        name: 'Werk Nord Sommer',
        notes: 'Sommernotiz',
        site_detail: { site_id: 'site-1', watchbook_scope_note: 'Sommer-Wachbuch' },
      }),
      buildPlanningRecord({
        id: 'record-2',
        name: 'Werk Nord Herbst',
        notes: null,
        planning_from: '2026-09-01',
        planning_to: '2026-09-10',
        site_detail: { site_id: 'site-1', watchbook_scope_note: null },
      }),
    ]);
    apiMocks.getPlanningRecordMock
      .mockResolvedValueOnce(buildPlanningRecord({
        id: 'record-1',
        name: 'Werk Nord Sommer',
        notes: 'Sommernotiz',
        site_detail: { site_id: 'site-1', watchbook_scope_note: 'Sommer-Wachbuch' },
      }))
      .mockResolvedValueOnce(buildPlanningRecord({
        id: 'record-2',
        name: 'Werk Nord Herbst',
        notes: null,
        planning_from: '2026-09-01',
        planning_to: '2026-09-10',
        site_detail: { site_id: 'site-1', watchbook_scope_note: null },
      }));
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    const recordRows = wrapper.findAll('[data-testid="customer-new-plan-existing-planning-record-row"]');
    await recordRows[0]!.trigger('click');
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    expect(setupState.planningRecordDraft.name).toBe('Werk Nord Sommer');
    expect(setupState.planningRecordDraft.notes).toBe('Sommernotiz');
    expect(setupState.planningRecordDraft.site_detail_watchbook_scope_note).toBe('Sommer-Wachbuch');

    await recordRows[1]!.trigger('click');
    await flushPromises();

    expect(setupState.planningRecordDraft.name).toBe('Werk Nord Herbst');
    expect(setupState.planningRecordDraft.notes).toBe('');
    expect(setupState.planningRecordDraft.site_detail_watchbook_scope_note).toBe('');
    expect(setupState.planningRecordDirty).toBe(false);
    expect((wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').element as HTMLSelectElement).value).toBe('site-1');
  });

  it('clears selected planning-record editor values when the planning context changes', async () => {
    apiMocks.listPlanningSetupRecordsMock.mockImplementation((entityKey: string) => {
      const map: Record<string, unknown[]> = {
        event_venue: [{ id: 'venue-1', customer_id: 'customer-1', venue_no: 'VEN-1', name: 'Arena', tenant_id: 'tenant-1', status: 'active', version_no: 1 }],
        patrol_route: [{ id: 'route-1', customer_id: 'customer-1', route_no: 'ROU-1', name: 'Innenstadt', tenant_id: 'tenant-1', status: 'active', version_no: 1 }],
        site: [
          { id: 'site-1', customer_id: 'customer-1', site_no: 'SITE-1', name: 'Werk Nord', tenant_id: 'tenant-1', status: 'active', version_no: 1 },
          { id: 'site-2', customer_id: 'customer-1', site_no: 'SITE-2', name: 'Werk Süd', tenant_id: 'tenant-1', status: 'active', version_no: 1 },
        ],
        trade_fair: [{ id: 'fair-1', customer_id: 'customer-1', fair_no: 'FAIR-1', name: 'Expo', tenant_id: 'tenant-1', status: 'active', version_no: 1 }],
      };
      return Promise.resolve(map[entityKey] ?? []);
    });
    apiMocks.listPlanningRecordsMock.mockImplementation((_tenantId, _token, params) =>
      Promise.resolve(
        params?.planning_entity_id === 'site-2'
          ? []
          : [
              buildPlanningRecord({
                id: 'record-1',
                name: 'Werk Nord Sommer',
                notes: 'Sommernotiz',
                site_detail: { site_id: 'site-1', watchbook_scope_note: 'Sommer-Wachbuch' },
              }),
            ],
      ),
    );
    apiMocks.getPlanningRecordMock.mockResolvedValue(buildPlanningRecord({
      id: 'record-1',
      name: 'Werk Nord Sommer',
      notes: 'Sommernotiz',
      site_detail: { site_id: 'site-1', watchbook_scope_note: 'Sommer-Wachbuch' },
    }));
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
    expect(setupState.selectedPlanningRecord.id).toBe('record-1');
    expect(setupState.planningRecordDraft.name).toBe('Werk Nord Sommer');
    expect(setupState.planningRecordDraft.notes).toBe('Sommernotiz');
    expect(setupState.planningRecordDraft.site_detail_watchbook_scope_note).toBe('Sommer-Wachbuch');

    apiMocks.listPlanningRecordsMock.mockClear();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-2');
    await flushPromises();

    expect(apiMocks.listPlanningRecordsMock).toHaveBeenCalledWith('tenant-1', 'token-1', {
      order_id: 'order-1',
      planning_entity_id: 'site-2',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
    });
    expect(setupState.selectedPlanningRecord).toBeNull();
    expect(setupState.planningEntityId).toBe('site-2');
    expect(setupState.planningRecordDraft.name).toBe('');
    expect(setupState.planningRecordDraft.notes).toBe('');
    expect(setupState.planningRecordDraft.site_detail_watchbook_scope_note).toBe('');
    expect(setupState.planningRecordDraft.planning_from).toBe('2026-06-01');
    expect(setupState.planningRecordDraft.planning_to).toBe('2026-06-10');
    expect(setupState.planningRecordDirty).toBe(false);
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toMatchObject({
      planning_entity_id: 'site-2',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: '',
    });
    expect(wrapper.emitted('step-completion')?.at(-1)).toEqual(['planning-record-overview', false]);

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-context-family"]').setValue('event_venue');
    await flushPromises();

    expect(setupState.selectedPlanningRecord).toBeNull();
    expect(setupState.planningFamily).toBe('event_venue');
    expect(setupState.planningEntityId).toBe('');
    expect(setupState.planningRecordDraft.name).toBe('');
    expect(setupState.planningRecordDraft.notes).toBe('');
    expect(setupState.planningRecordDraft.site_detail_watchbook_scope_note).toBe('');
    expect(wrapper.emitted('saved-context')?.at(-1)?.[0]).toMatchObject({
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
      planning_record_id: '',
    });
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

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
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

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-clear-planning-record-draft"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Werk Nord Sommer');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').setValue('2026-06-10');

    apiMocks.createPlanningRecordMock.mockResolvedValue(buildPlanningRecord());

    await wrapper.get('[data-testid="customer-new-plan-save-planning-record"]').trigger('click');
    await flushPromises();

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
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(true);
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

    await wrapper.get('[data-testid="customer-new-plan-save-planning-record"]').trigger('click');
    await flushPromises();

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
    expect(wrapper.emitted('step-ui-state')?.some((event) => event[0] === 'planning-record-overview' && (event[1] as Record<string, unknown>).dirty === false && (event[1] as Record<string, unknown>).error === '')).toBe(true);
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(true);
  });

  it('clears planning-record editor drafts without saving or changing the planning context', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Werk Nord Sommer');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').setValue('2026-06-10');

    await wrapper.get('[data-testid="customer-new-plan-clear-planning-record-draft"]').trigger('click');
    await flushPromises();

    expect(apiMocks.createPlanningRecordMock).not.toHaveBeenCalled();
    expect(apiMocks.updatePlanningRecordMock).not.toHaveBeenCalled();
    expect((wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').element as HTMLSelectElement).value).toBe('site-1');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe('');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').element as HTMLInputElement).value).toBe('');
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').element as HTMLInputElement).value).toBe('');
    expect(wrapper.emitted('step-completion')?.at(-1)).toEqual(['planning-record-overview', false]);
    expect(wrapper.emitted('step-ui-state')?.at(-1)?.[1]).toMatchObject({ dirty: false, error: '' });
  });

  it('reverts an edited existing planning record when the editor is cleared', async () => {
    apiMocks.listPlanningRecordsMock.mockResolvedValue([buildPlanningRecord()]);
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-existing-planning-record-row"]').trigger('click');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Werk Nord Herbst');
    await flushPromises();

    expect(wrapper.emitted('step-ui-state')?.at(-1)?.[1]).toMatchObject({ dirty: true, error: '' });

    await wrapper.get('[data-testid="customer-new-plan-clear-planning-record-draft"]').trigger('click');
    await flushPromises();
    await waitForCondition(
      () => (wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value === 'Werk Nord Sommer',
    );

    expect(apiMocks.updatePlanningRecordMock).not.toHaveBeenCalled();
    expect((wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord Sommer',
    );
    expect(wrapper.emitted('step-completion')?.at(-1)).toEqual(['planning-record-overview', true]);
    expect(wrapper.emitted('step-ui-state')?.at(-1)?.[1]).toMatchObject({ dirty: false, error: '' });
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(true);
  });

  it('blocks Next from silently saving an unsaved planning record draft', async () => {
    const wrapper = mountStep('planning-record-overview', {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('site-1');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-record-name"]').setValue('Werk Nord Sommer');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-planning-record-to"]').setValue('2026-06-10');

    const continued = await (wrapper.vm as any).submitCurrentStep();

    expect(continued).toBe(false);
    expect(apiMocks.createPlanningRecordMock).not.toHaveBeenCalled();
    expect(apiMocks.updatePlanningRecordMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.savePlanningRecordBeforeContinue',
    }));

    apiMocks.createPlanningRecordMock.mockResolvedValue(buildPlanningRecord());
    await wrapper.get('[data-testid="customer-new-plan-save-planning-record"]').trigger('click');
    await flushPromises();

    expect(apiMocks.createPlanningRecordMock).toHaveBeenCalledTimes(1);
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(true);
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
    apiMocks.listPlanningSetupRecordsMock.mockImplementation((entityKey: string) => {
      const map: Record<string, unknown[]> = {
        site: [
          { id: 'site-1', customer_id: 'customer-1', site_no: 'SITE-1', name: 'Werk Nord', tenant_id: 'tenant-1', status: 'active', version_no: 1 },
          { id: 'site-created-1', customer_id: 'customer-1', site_no: 'SITE-NEW', name: 'Neuer Standort', tenant_id: 'tenant-1', status: 'active', version_no: 1 },
        ],
      };
      return Promise.resolve(map[entityKey] ?? []);
    });
    await wrapper.get('[data-testid="customer-new-plan-planning-record-create-entry"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-site-no"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-planning-create-name"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-planning-create-site-no"]').setValue('SITE-NEW');
    await wrapper.get('[data-testid="customer-new-plan-planning-create-name"]').setValue('Neuer Standort');
    await wrapper.get('[data-testid="modal-ok"]').trigger('click');
    await flushPromises();

    expect(apiMocks.createPlanningSetupRecordMock).toHaveBeenCalledTimes(1);
    expect(setupState.planningEntityId).toBe('site-created-1');
    expect(setupState.planningSelectionMode).toBe('use_existing');
    const entrySelect = wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]');
    expect(entrySelect.text()).toContain('Neuer Standort');
    expect((entrySelect.element as HTMLSelectElement).value).toBe('site-created-1');
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
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.selectOrCreatePlanningContextBeforeContinue',
    }));
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
    await wrapper.get('[data-testid="customer-new-plan-planning-context-entry"]').setValue('fair-1');
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

    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-planning-document-upload-title"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-attach-planning-document"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.forms.linkExistingDocument');
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-link-planning-document"]').exists()).toBe(true);

    await wrapper.get('[data-testid="customer-new-plan-planning-document-picker-open"]').trigger('click');
    await flushPromises();
    expect(wrapper.find('.sp-customer-plan-wizard-step__document-picker-modal').exists()).toBe(true);
    expect(wrapper.find('.sp-customer-plan-wizard-step__document-picker-results').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-planning-document-search"]').setValue('Safety');
    await wrapper.get('[data-testid="customer-new-plan-planning-document-search"]').trigger('keyup.enter');
    await flushPromises();
    await wrapper.get('[data-testid="customer-new-plan-planning-document-result-row"]').trigger('click');
    await flushPromises();
    await settleLoadingRender();
    expect(wrapper.get('[data-testid="customer-new-plan-planning-document-selected"]').text()).toContain('Safety concept');
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

    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-link-planning-document"]').trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-planning-record-documents"]').exists()).toBe(true);
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledWith(
      'tenant-1',
      'record-1',
      'token-1',
      expect.objectContaining({
        document_id: 'document-1',
      }),
    );
    expect(wrapper.find('[data-testid="customer-new-plan-planning-document-selected"]').exists()).toBe(false);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-planning-document-list"]').exists()).toBe(true);

    const continued = await (wrapper.vm as any).submitCurrentStep();

    expect(continued).toBe(true);
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledTimes(1);
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
      {
        id: '11111111-1111-4111-8111-111111111111',
        tenant_id: 'tenant-1',
        title: '1663202370369.jpg',
        source_label: 'camera-upload',
        relation_label: 'Image for test',
        current_version_no: 1,
        status: 'active',
      },
    ]);
    const existingWrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    const documentList = existingWrapper.get('[data-order-workspace-testid="customer-order-workspace-planning-document-list"]');
    expect(documentList.text()).toContain('Image for test');
    expect(documentList.text()).not.toContain('11111111-1111-4111-8111-111111111111');
    expect(existingWrapper.get('[data-order-workspace-testid="customer-order-workspace-planning-document-primary-label"]').text()).toBe('Image for test');
    expect(existingWrapper.get('[data-order-workspace-testid="customer-order-workspace-planning-document-secondary-label"]').text()).toContain('v1');
    expect(existingWrapper.find('[data-testid="customer-new-plan-planning-record-document-id"]').exists()).toBe(false);
    expect(existingWrapper.find('[data-order-workspace-testid="customer-order-workspace-planning-document-picker"]').exists()).toBe(true);
    expect(existingWrapper.find('[data-order-workspace-testid="customer-order-workspace-planning-document-remove"]').exists()).toBe(true);

    const existingSaved = await (existingWrapper.vm as any).submitCurrentStep();

    expect(existingSaved).toBe(true);
    expect(apiMocks.createPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);

    apiMocks.unlinkPlanningRecordAttachmentMock.mockResolvedValue(undefined);
    apiMocks.listPlanningRecordAttachmentsMock.mockResolvedValueOnce([]);

    await existingWrapper.get('[data-order-workspace-testid="customer-order-workspace-planning-document-remove"]').trigger('click');
    await flushPromises();

    expect(confirmMock).toHaveBeenCalledWith('sicherplan.customerPlansWizard.confirmUnlinkPlanningDocument');
    expect(apiMocks.unlinkPlanningRecordAttachmentMock).toHaveBeenCalledWith(
      'tenant-1',
      'record-1',
      '11111111-1111-4111-8111-111111111111',
      'token-1',
    );
    expect(existingWrapper.find('[data-order-workspace-testid="customer-order-workspace-planning-document-list"]').exists()).toBe(false);
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
    apiMocks.createPlanningRecordAttachmentMock.mockResolvedValue({
      id: 'doc-row-upload',
      tenant_id: 'tenant-1',
      title: 'Planning brief',
      current_version_no: 1,
      status: 'active',
    });
    apiMocks.listPlanningRecordAttachmentsMock.mockResolvedValue([
      { id: 'doc-row-upload', tenant_id: 'tenant-1', title: 'Planning brief', current_version_no: 1, status: 'active' },
    ]);
    await flushPromises();

    await uploadWrapper.get('[data-order-workspace-testid="customer-order-workspace-attach-planning-document"]').trigger('click');
    await flushPromises();

    expect(uploadWrapper.find('[data-testid="customer-new-plan-step-panel-planning-record-documents"]').exists()).toBe(true);
    expect(apiMocks.createPlanningRecordAttachmentMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.createPlanningRecordAttachmentMock).toHaveBeenCalledWith(
      'tenant-1',
      'record-1',
      'token-1',
      expect.objectContaining({
        content_base64: 'base64-planning',
        file_name: 'brief.pdf',
        title: 'Planning brief',
      }),
    );
    expect(apiMocks.linkPlanningRecordAttachmentMock).toHaveBeenCalledTimes(0);
    expect((uploadWrapper.get('[data-order-workspace-testid="customer-order-workspace-planning-document-upload-title"]').element as HTMLInputElement).value).toBe('');
    expect(uploadWrapper.find('[data-order-workspace-testid="customer-order-workspace-planning-document-list"]').exists()).toBe(true);

    const completeDraftWrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    const completeDraftState = (completeDraftWrapper.vm as any).$?.setupState;
    completeDraftState.planningRecordAttachmentDraft.title = 'Complete draft via Next';
    completeDraftState.planningRecordAttachmentDraft.file_name = 'complete.pdf';
    completeDraftState.planningRecordAttachmentDraft.content_type = 'application/pdf';
    completeDraftState.planningRecordAttachmentDraft.content_base64 = 'base64-complete';
    await flushPromises();

    const completeDraftContinued = await (completeDraftWrapper.vm as any).submitCurrentStep();

    expect(completeDraftContinued).toBe(false);
    expect(apiMocks.createPlanningRecordAttachmentMock).toHaveBeenCalledTimes(1);
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.completeCurrentPlanningDocumentDraftBeforeContinue',
    }));

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
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.completeCurrentPlanningDocumentDraftBeforeContinue',
    }));
    expect(partialWrapper.find('[data-testid="customer-new-plan-clear-planning-document-draft"]').exists()).toBe(true);

    await partialWrapper.get('[data-testid="customer-new-plan-clear-planning-document-draft"]').trigger('click');
    await flushPromises();

    const cleared = await (partialWrapper.vm as any).submitCurrentStep();
    expect(cleared).toBe(true);

    const partialLinkWrapper = mountStep('planning-record-documents', {
      planning_record_id: 'record-1',
      current_step: 'planning-record-documents',
    });
    await flushPromises();

    const partialLinkState = (partialLinkWrapper.vm as any).$?.setupState;
    partialLinkState.planningRecordAttachmentLink.label = 'Missing document ID';
    await flushPromises();

    const blockedLink = await (partialLinkWrapper.vm as any).submitCurrentStep();

    expect(blockedLink).toBe(false);
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.completeCurrentPlanningDocumentDraftBeforeContinue',
    }));

    await partialLinkWrapper.get('[data-order-workspace-testid="customer-order-workspace-clear-planning-document-draft"]').trigger('click');
    await flushPromises();

    const clearedLink = await (partialLinkWrapper.vm as any).submitCurrentStep();
    expect(clearedLink).toBe(true);
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

  it('selects an existing shift plan row locally without committing wizard context immediately', async () => {
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
    expect(wrapper.find('[data-testid="customer-new-plan-selected-shift-plan-summary"]').exists()).toBe(false);
    expect(rows[0]!.classes()).toContain('sp-customer-plan-wizard-step__list-row--selected');
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord / Schichtplan',
    );
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
    expect(wrapper.find('[data-testid="customer-new-plan-selected-shift-plan-summary"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-existing-shift-plan-row"]').classes()).toContain(
      'sp-customer-plan-wizard-step__list-row--selected',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-shift-plan-name"]').element as HTMLInputElement).value).toBe(
      'Werk Nord / Schichtplan',
    );
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
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.shiftPlanPlanningRecordWindowMismatch',
    }));
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

    await saveCurrentSeries(wrapper);

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
    await saveCurrentSeries(wrapper);
    await openNewExceptionDialog(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-06-03');
    await saveCurrentException(wrapper);

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

    expect(saved).toMatchObject({
      completedStepId: 'series-exceptions',
      success: true,
    });
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
    expect(routerPushMock).not.toHaveBeenCalled();
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
    expect(wrapper.find('[data-testid="customer-new-plan-series-generation-from"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="customer-new-plan-series-generation-to"]').exists()).toBe(false);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-exceptions-section"]').exists()).toBe(false);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-generation-options-section"]').exists()).toBe(false);
    expect(wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-gating-helper"]').text()).toBe(
      'sicherplan.customerPlansWizard.forms.seriesDependentSectionsHelper',
    );
    expect((wrapper.get('[data-testid="customer-new-plan-series-timezone"]').element as HTMLSelectElement).value).toBe(
      'Europe/Berlin',
    );
    expect(((wrapper.vm as any).$?.setupState.seriesDraft.weekday_mask as string)).toBe('');
  });

  it('renders Series and Exceptions sections, saves series independently, and blocks dirty generation', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-section"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-save"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-template-helper"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-start-time"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-end-time"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-shift-type"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-default-break"]').exists()).toBe(true);
    expect(wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-save"]').text()).toBe(
      'sicherplan.customerPlansWizard.actions.saveSeries',
    );
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-selected-shift-plan-summary"]').exists()).toBe(true);
    expect(wrapper.get('[data-order-workspace-testid="customer-order-workspace-selected-shift-plan-summary"]').classes()).toContain(
      'sp-customer-plan-wizard-step__info-summary',
    );
    expect(wrapper.get('[data-order-workspace-testid="customer-order-workspace-selected-shift-plan-summary"]').classes()).not.toContain(
      'sp-customer-plan-wizard-step__list-row',
    );
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-exceptions-section"]').exists()).toBe(false);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-generation-options-section"]').exists()).toBe(false);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-gating-helper"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-series-exception-date"]').exists()).toBe(false);
    const checkboxRows = wrapper.findAll('.planning-admin-checkbox--centered');
    expect(checkboxRows.length).toBeGreaterThanOrEqual(3);

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Tagdienst Juni');
    await wrapper.get('[data-testid="customer-new-plan-series-template"]').setValue('template-1');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    await flushPromises();
    await settleLoadingRender();

    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    expect(apiMocks.createShiftSeriesMock).not.toHaveBeenCalled();
    expect(apiMocks.generateShiftSeriesMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.saveCurrentSeriesBeforeContinue',
    }));

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries({ label: 'Tagdienst Juni' }));
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ label: 'Tagdienst Juni' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    await saveCurrentSeries(wrapper);

    expect(apiMocks.createShiftSeriesMock).toHaveBeenCalledWith(
      'tenant-1',
      'plan-1',
      'token-1',
      expect.objectContaining({ label: 'Tagdienst Juni' }),
    );
    expect(apiMocks.generateShiftSeriesMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-update"]').exists()).toBe(true);
    expect(wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-update"]').text()).toBe(
      'sicherplan.customerPlansWizard.actions.updateSeries',
    );
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-series-gating-helper"]').exists()).toBe(false);
    const exceptionsSection = wrapper.get('[data-order-workspace-testid="customer-order-workspace-exceptions-section"]');
    const generationSection = wrapper.get('[data-order-workspace-testid="customer-order-workspace-generation-options-section"]');
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-new-exception"]').exists()).toBe(true);
    expect(exceptionsSection.element.compareDocumentPosition(generationSection.element) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const generationControls = generationSection.findAll('.sp-customer-plan-wizard-step__generation-grid > *');
    expect(generationControls).toHaveLength(3);
    expect(generationControls[0]!.find('[data-order-workspace-testid="customer-order-workspace-generate-from"]').exists()).toBe(true);
    expect(generationControls[1]!.find('[data-order-workspace-testid="customer-order-workspace-generate-to"]').exists()).toBe(true);
    expect(generationControls[2]!.find('[data-order-workspace-testid="customer-order-workspace-regenerate-existing"]').exists()).toBe(true);
  });

  it('saves manual time-first series input by reusing a compatible generated template', async () => {
    apiMocks.listShiftTemplatesMock.mockResolvedValue([
      { id: 'manual-template-1', tenant_id: 'tenant-1', code: 'OW_0900_1700_day_45', label: 'Manual 09:00-17:00', local_start_time: '09:00', local_end_time: '17:00', default_break_minutes: 45, shift_type_code: 'day', status: 'active', version_no: 1 },
    ]);
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Manuelle Tagschicht');
    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-start-time"]').setValue('09:00');
    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-end-time"]').setValue('17:00');
    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-shift-type"]').setValue('day');
    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-default-break"]').setValue(45);
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries({ label: 'Manuelle Tagschicht', shift_template_id: 'manual-template-1' }));
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ label: 'Manuelle Tagschicht', shift_template_id: 'manual-template-1' })]);

    await saveCurrentSeries(wrapper);

    expect(apiMocks.createShiftTemplateMock).not.toHaveBeenCalled();
    expect(apiMocks.createShiftSeriesMock).toHaveBeenCalledWith(
      'tenant-1',
      'plan-1',
      'token-1',
      expect.objectContaining({
        label: 'Manuelle Tagschicht',
        shift_template_id: 'manual-template-1',
        shift_type_code: 'day',
        default_break_minutes: 45,
      }),
    );
  });

  it('blocks time-first series save when required time fields or weekly weekdays are invalid', async () => {
    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: '',
    });
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-label"]').setValue('Fehlerhafte Serie');
    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-shift-type"]').setValue('day');
    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-06-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-06-10');
    await saveCurrentSeries(wrapper);
    expect(apiMocks.createShiftSeriesMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesStartTimeRequired',
    }));

    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-start-time"]').setValue('17:00');
    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-end-time"]').setValue('09:00');
    await flushPromises();
    await saveCurrentSeries(wrapper);
    expect(apiMocks.createShiftSeriesMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesEndTimeAfterStart',
    }));

    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-end-time"]').setValue('18:00');
    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('weekly');
    await flushPromises();
    for (const weekdayId of SERIES_WEEKDAY_IDS) {
      if (seriesWeekdayChip(wrapper, weekdayId).attributes('aria-pressed') === 'true') {
        await seriesWeekdayChip(wrapper, weekdayId).trigger('click');
      }
    }
    await saveCurrentSeries(wrapper);
    expect(apiMocks.createShiftSeriesMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesWeekdayMaskInvalid',
    }));
  });

  it('renders saved-series loading above the Series form fields without replacing the label field', async () => {
    const seriesDetail = deferred<ReturnType<typeof buildSeries>>();
    apiMocks.getShiftSeriesMock.mockReturnValue(seriesDetail.promise);

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await settleLoadingRender();

    const loading = wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-loading"]');
    const label = wrapper.get('[data-testid="customer-new-plan-series-label"]');
    expect(loading.text()).toContain('sicherplan.customerPlansWizard.forms.loadingSavedSeries');
    expect(wrapper.find('[data-testid="customer-new-plan-series-label"]').exists()).toBe(true);
    expect(loading.element.closest('.sp-customer-plan-wizard-step__grid')).toBeNull();
    expect(loading.element.compareDocumentPosition(label.element) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    seriesDetail.resolve(buildSeries());
    await flushPromises();
  });

  it('manages multiple series exceptions through the dialog with create, edit, and delete', async () => {
    const exceptionOne = {
      id: 'exception-1',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-06-03',
      action_code: 'skip',
      version_no: 1,
    };
    const exceptionTwo = {
      id: 'exception-2',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-06-04',
      action_code: 'skip',
      version_no: 1,
    };
    const exceptionThree = {
      id: 'exception-3',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-06-05',
      action_code: 'skip',
      version_no: 1,
    };
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries()]);
    apiMocks.getShiftSeriesMock.mockResolvedValue(buildSeries());
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValueOnce([exceptionOne, exceptionTwo]);

    const wrapper = mountStep('series-exceptions', {
      current_step: 'series-exceptions',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await flushPromises();

    expect(wrapper.findAll('[data-order-workspace-testid="customer-order-workspace-exception-row"]')).toHaveLength(2);
    expect(wrapper.find('.sp-customer-plan-wizard-step__exception-action-row').exists()).toBe(true);
    expect(wrapper.find('.sp-customer-plan-wizard-step__exception-list').exists()).toBe(true);

    apiMocks.createShiftSeriesExceptionMock.mockResolvedValue(exceptionThree);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValueOnce([exceptionOne, exceptionTwo, exceptionThree]);
    await openNewExceptionDialog(wrapper);
    expect(wrapper.find('[data-order-workspace-testid="customer-order-workspace-exception-dialog"]').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-06-05');
    await saveCurrentException(wrapper);
    expect(apiMocks.createShiftSeriesExceptionMock).toHaveBeenCalledWith(
      'tenant-1',
      'series-1',
      'token-1',
      expect.objectContaining({ exception_date: '2026-06-05', action_code: 'skip' }),
    );
    expect(wrapper.findAll('[data-order-workspace-testid="customer-order-workspace-exception-row"]')).toHaveLength(3);

    apiMocks.updateShiftSeriesExceptionMock.mockResolvedValue({ ...exceptionTwo, action_code: 'override', version_no: 2 });
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValueOnce([
      exceptionOne,
      { ...exceptionTwo, action_code: 'override', version_no: 2 },
      exceptionThree,
    ]);
    await wrapper.findAll('[data-order-workspace-testid="customer-order-workspace-edit-exception"]')[1]!.trigger('click');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('override');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-override-start"]').setValue('09:00');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-override-end"]').setValue('17:00');
    await saveCurrentException(wrapper);
    expect(apiMocks.updateShiftSeriesExceptionMock).toHaveBeenCalledWith(
      'tenant-1',
      'exception-2',
      'token-1',
      expect.objectContaining({
        action_code: 'override',
        override_local_start_time: '09:00',
        override_local_end_time: '17:00',
      }),
    );

    apiMocks.deleteShiftSeriesExceptionMock.mockResolvedValue(undefined);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValueOnce([
      { ...exceptionTwo, action_code: 'override', version_no: 2 },
      exceptionThree,
    ]);
    await wrapper.findAll('[data-order-workspace-testid="customer-order-workspace-delete-exception"]')[0]!.trigger('click');
    await flushPromises();
    expect(apiMocks.deleteShiftSeriesExceptionMock).toHaveBeenCalledWith('tenant-1', 'exception-1', 'token-1');
    expect(wrapper.findAll('[data-order-workspace-testid="customer-order-workspace-exception-row"]')).toHaveLength(2);
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
    expect(apiMocks.getShiftTemplateMock).not.toHaveBeenCalledWith('tenant-1', 'template-2', 'token-1');
    expect(setupState.seriesDraft.shift_type_code).toBe('');

    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-apply-template"]').trigger('click');
    await flushPromises();

    expect(apiMocks.getShiftTemplateMock).toHaveBeenCalledWith('tenant-1', 'template-2', 'token-1');
    expect(setupState.seriesDraft.local_start_time).toBe('08:00');
    expect(setupState.seriesDraft.local_end_time).toBe('16:00');
    expect(setupState.seriesDraft.default_break_minutes).toBe(30);
    expect(setupState.seriesDraft.shift_type_code).toBe('site_day');
    expect(setupState.seriesDraft.meeting_point).toBe('Nordtor Sicherheitsloge');
    expect(setupState.seriesDraft.location_text).toBe('RheinForum Köln – Nordtor & Ladehof');

    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-start-time"]').setValue('09:15');
    await templateSelect.setValue('template-1');
    await flushPromises();
    expect(setupState.seriesDraft.local_start_time).toBe('09:15');
    await templateSelect.setValue('template-2');
    await wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-apply-template"]').trigger('click');
    await flushPromises();

    await wrapper.get('[data-testid="customer-new-plan-series-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-to"]').setValue('2026-07-31');
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

    await saveCurrentSeries(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-generation-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-to"]').setValue('2026-07-31');
    await wrapper.get('[data-testid="customer-new-plan-series-regenerate-existing"]').setValue(false);
    await flushPromises();
    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toMatchObject({
      completedStepId: 'series-exceptions',
      success: true,
    });
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
    expect(routerPushMock).not.toHaveBeenCalled();
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
          local_end_time: '17:00',
          local_start_time: '09:00',
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
    expect((wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-start-time"]').element as HTMLInputElement).value).toBe(
      '09:00',
    );
    expect((wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-end-time"]').element as HTMLInputElement).value).toBe(
      '17:00',
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
    expect((wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-start-time"]').element as HTMLInputElement).value).toBe(
      '08:00',
    );
    expect((wrapper.get('[data-order-workspace-testid="customer-order-workspace-series-end-time"]').element as HTMLInputElement).value).toBe(
      '16:00',
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

    await saveCurrentSeries(wrapper);

    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesShiftPlanWindowMismatch',
    }));
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
    await saveCurrentSeries(wrapper);
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesWeekdayMaskInvalid',
    }));
    expect(wrapper.text()).toContain('sicherplan.customerPlansWizard.forms.weekdayMaskHelp');

    await wrapper.get('[data-testid="customer-new-plan-series-recurrence-code"]').setValue('daily');
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-series-weekday-picker"]').exists()).toBe(false);
    expect(setupState.seriesDraft.weekday_mask).toBe('');

    await setSeriesWeeklyMask(wrapper, '1111100');
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(
      buildSeries({
        date_from: '2026-06-01',
        date_to: '2026-06-10',
        recurrence_code: 'weekly',
        weekday_mask: '1111100',
      }),
    );
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ recurrence_code: 'weekly', weekday_mask: '1111100' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    await saveCurrentSeries(wrapper);
    await openNewExceptionDialog(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('override');
    await flushPromises();
    expect(wrapper.find('[data-testid="customer-new-plan-series-exception-override-start"]').exists()).toBe(true);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-customer-visible"]').setValue('false');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-subcontractor-visible"]').setValue('true');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-stealth-mode"]').setValue('');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-06-03');
    await flushPromises();

    await saveCurrentException(wrapper);
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesExceptionOverrideTimesRequired',
    }));

    await wrapper.get('[data-testid="customer-new-plan-series-exception-override-start"]').setValue('08:30');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-override-end"]').setValue('16:30');
    await flushPromises();

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

    await saveCurrentException(wrapper);
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

    await saveCurrentSeries(wrapper);
    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toMatchObject({
      completedStepId: 'series-exceptions',
      success: true,
    });
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
    await flushPromises();

    const setupState = (wrapper.vm as any).$?.setupState;
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

    await saveCurrentSeries(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-generation-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-to"]').setValue('2026-07-31');
    await flushPromises();
    await openNewExceptionDialog(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    setupState.exceptionDraft.notes = 'Interne Logistik-Sperrung am Nordtor; kein regulärer Objektschutzdienst an diesem Tag.';
    await saveCurrentException(wrapper);

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

    await saveCurrentSeries(wrapper);
    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesGenerationWindowInvalid',
    }));
  });

  it('saves series and exception before final generation and clears the series draft', async () => {
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

    await saveCurrentSeries(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-generation-from"]').setValue('2026-07-01');
    await wrapper.get('[data-testid="customer-new-plan-series-generation-to"]').setValue('2026-07-31');
    await flushPromises();
    await openNewExceptionDialog(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    await saveCurrentException(wrapper);

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toMatchObject({
      completedStepId: 'series-exceptions',
      success: true,
    });
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
    expect(routerPushMock).not.toHaveBeenCalled();
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

    await saveCurrentSeries(wrapper);
    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(routerPushMock).not.toHaveBeenCalled();
    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-series-exceptions"]').exists()).toBe(true);
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesGenerateFailed',
    }));
  });

  it('keeps saved series fields visible when generation fails after series and exception save', async () => {
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
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', label: 'Werktage Tagschicht Nordtor', recurrence_code: 'weekly', weekday_mask: '1111100' }));
    apiMocks.createShiftSeriesExceptionMock.mockResolvedValue({
      id: 'exception-1',
      tenant_id: 'tenant-1',
      shift_series_id: 'series-1',
      exception_date: '2026-07-03',
      action_code: 'skip',
      version_no: 1,
    });
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', label: 'Werktage Tagschicht Nordtor', recurrence_code: 'weekly', weekday_mask: '1111100' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.generateShiftSeriesMock.mockRejectedValue(new Error('generate failed'));

    await saveCurrentSeries(wrapper);
    await openNewExceptionDialog(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    await saveCurrentException(wrapper);

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toBe(false);
    expect(window.sessionStorage.getItem(draftKey)).toBeNull();
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
    await flushPromises();

    apiMocks.createShiftSeriesMock.mockResolvedValue(buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', recurrence_code: 'weekly', weekday_mask: '1111100' }));
    apiMocks.listShiftSeriesMock.mockResolvedValue([buildSeries({ date_from: '2026-07-01', date_to: '2026-07-31', recurrence_code: 'weekly', weekday_mask: '1111100' })]);
    apiMocks.listShiftSeriesExceptionsMock.mockResolvedValue([]);
    apiMocks.createShiftSeriesExceptionMock.mockRejectedValue(
      new planningShiftsApiErrorExports.PlanningShiftsApiError(409, {
        message_key: 'errors.planning.shift_series_exception.duplicate_date',
        details: {},
      }),
    );

    await saveCurrentSeries(wrapper);
    await openNewExceptionDialog(wrapper);
    await wrapper.get('[data-testid="customer-new-plan-series-exception-date"]').setValue('2026-07-03');
    await wrapper.get('[data-testid="customer-new-plan-series-exception-action-code"]').setValue('skip');
    await saveCurrentException(wrapper);

    expect(apiMocks.generateShiftSeriesMock).not.toHaveBeenCalled();
    expect(notificationMocks.error).toHaveBeenCalledWith(expect.objectContaining({
      message: 'sicherplan.customerPlansWizard.errors.seriesExceptionDuplicateDate',
    }));
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

  it('shows a demand-groups empty state when no generated shifts exist yet', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await settleLoadingRender();

    expect(wrapper.find('[data-testid="customer-new-plan-step-panel-demand-groups"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-demand-groups-empty"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-demand-group-new"]').exists()).toBe(true);
    expect((wrapper.get('[data-testid="customer-new-plan-demand-groups-generated-count"]').element as HTMLElement).textContent).toContain('0');

    await wrapper.get('[data-testid="customer-new-plan-demand-group-new"]').trigger('click');
    await flushPromises();
    const demandGroupDialog = (wrapper.vm as any).$?.setupState.demandGroupDialog;
    demandGroupDialog.function_type_id = 'function-1';
    (wrapper.vm as any).$?.setupState.submitDemandGroupDialog();
    await flushPromises();

    expect(wrapper.findAll('[data-testid="customer-new-plan-demand-group-row"]')).toHaveLength(1);
    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    expect(wrapper.get('[data-testid="customer-new-plan-demand-groups-validation"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.demandGroupsNoGeneratedShifts',
    );
  });

  it('loads active function and qualification options for the demand-group modal', async () => {
    employeeAdminMocks.listFunctionTypesMock.mockResolvedValue([
      { id: 'function-1', tenant_id: 'tenant-1', label: 'Dispatch support', status: 'active', version_no: 1, archived_at: null },
      { id: 'function-archived', tenant_id: 'tenant-1', label: 'Archived function', status: 'active', version_no: 1, archived_at: '2026-01-01T00:00:00Z' },
      { id: 'function-inactive', tenant_id: 'tenant-1', label: 'Inactive function', status: 'inactive', version_no: 1, archived_at: null },
    ]);
    employeeAdminMocks.listQualificationTypesMock.mockResolvedValue([
      { id: 'qualification-1', tenant_id: 'tenant-1', label: 'Crowd control', status: 'active', version_no: 1, archived_at: null },
      { id: 'qualification-archived', tenant_id: 'tenant-1', label: 'Archived qualification', status: 'active', version_no: 1, archived_at: '2026-01-01T00:00:00Z' },
      { id: 'qualification-inactive', tenant_id: 'tenant-1', label: 'Inactive qualification', status: 'inactive', version_no: 1, archived_at: null },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await settleLoadingRender();

    expect(employeeAdminMocks.listFunctionTypesMock).toHaveBeenCalledWith('tenant-1', 'token-1');
    expect(employeeAdminMocks.listQualificationTypesMock).toHaveBeenCalledWith('tenant-1', 'token-1');

    (wrapper.vm as any).$?.setupState.openNewDemandGroupDialog();
    await nextTick();
    await flushPromises();

    const functionOptions = wrapper
      .get('[data-testid="customer-new-plan-demand-group-modal-function-type"]')
      .findAll('option')
      .map((option) => option.text());
    const qualificationOptions = wrapper
      .get('[data-testid="customer-new-plan-demand-group-modal-qualification-type"]')
      .findAll('option')
      .map((option) => option.text());

    expect(functionOptions).toContain('Dispatch support');
    expect(functionOptions).not.toContain('Archived function');
    expect(functionOptions).not.toContain('Inactive function');
    expect(qualificationOptions).toContain('Crowd control');
    expect(qualificationOptions).not.toContain('Archived qualification');
    expect(qualificationOptions).not.toContain('Inactive qualification');
  });

  it('opens a demand-group modal from the demand-groups step', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await settleLoadingRender();

    (wrapper.vm as any).$?.setupState.openNewDemandGroupDialog();
    await nextTick();
    await flushPromises();
    expect((wrapper.vm as any).$?.setupState.demandGroupDialog.open).toBe(true);
    expect(wrapper.find('[data-testid="customer-new-plan-demand-group-modal"]').exists()).toBe(true);
  });

  it('blocks demand-group modal save when function type is missing', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await settleLoadingRender();

    await wrapper.get('[data-testid="customer-new-plan-demand-group-new"]').trigger('click');
    await flushPromises();
    (wrapper.vm as any).$?.setupState.submitDemandGroupDialog();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-demand-groups-validation"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.demandGroupsFunctionTypeRequired',
    );
  });

  it('blocks demand-group modal save when target_qty is below min_qty', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await settleLoadingRender();

    await wrapper.get('[data-testid="customer-new-plan-demand-group-new"]').trigger('click');
    await flushPromises();
    const invalidDialog = (wrapper.vm as any).$?.setupState.demandGroupDialog;
    invalidDialog.function_type_id = 'function-1';
    invalidDialog.min_qty = 3;
    invalidDialog.target_qty = 2;
    (wrapper.vm as any).$?.setupState.submitDemandGroupDialog();
    await flushPromises();

    expect(wrapper.get('[data-testid="customer-new-plan-demand-groups-validation"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.demandGroupsMinExceedsTarget',
    );
  });

  it('adds, edits, and removes a demand-group template row', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await settleLoadingRender();

    await wrapper.get('[data-testid="customer-new-plan-demand-group-new"]').trigger('click');
    await flushPromises();
    const createDialog = (wrapper.vm as any).$?.setupState.demandGroupDialog;
    createDialog.function_type_id = 'function-1';
    createDialog.target_qty = 2;
    (wrapper.vm as any).$?.setupState.submitDemandGroupDialog();
    await flushPromises();

    expect(wrapper.findAll('[data-testid="customer-new-plan-demand-group-row"]')).toHaveLength(1);

    await wrapper.get('[data-testid="customer-new-plan-demand-group-edit-0"]').trigger('click');
    await flushPromises();
    const editDialog = (wrapper.vm as any).$?.setupState.demandGroupDialog;
    editDialog.remark = 'night gate';
    (wrapper.vm as any).$?.setupState.submitDemandGroupDialog();
    await flushPromises();

    expect(wrapper.text()).toContain('night gate');

    await wrapper.get('[data-testid="customer-new-plan-demand-group-remove-0"]').trigger('click');
    await flushPromises();

    expect(wrapper.findAll('[data-testid="customer-new-plan-demand-group-row"]')).toHaveLength(0);
  });

  it('shows persisted applied demand-group summaries when local draft rows are empty', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
      {
        id: 'shift-2',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-03',
        starts_at: '2026-07-03T08:00:00Z',
        ends_at: '2026-07-03T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    employeeAdminMocks.listFunctionTypesMock.mockResolvedValue([
      { id: 'function-1', tenant_id: 'tenant-1', label: 'Dispatch support', status: 'active', version_no: 1, archived_at: null },
      { id: 'function-2', tenant_id: 'tenant-1', label: 'Fire watch', status: 'active', version_no: 1, archived_at: null },
    ]);
    employeeAdminMocks.listQualificationTypesMock.mockResolvedValue([
      { id: 'qualification-1', tenant_id: 'tenant-1', label: 'Crowd control', status: 'active', version_no: 1, archived_at: null },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([
      {
        id: 'dg-1',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-1',
        qualification_type_id: 'qualification-1',
        min_qty: 1,
        target_qty: 2,
        mandatory_flag: true,
        sort_order: 1,
        remark: 'Front gate',
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
      {
        id: 'dg-2',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-2',
        qualification_type_id: null,
        min_qty: 1,
        target_qty: 1,
        mandatory_flag: false,
        sort_order: 2,
        remark: null,
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
      {
        id: 'dg-3',
        tenant_id: 'tenant-1',
        shift_id: 'shift-2',
        function_type_id: 'function-1',
        qualification_type_id: 'qualification-1',
        min_qty: 1,
        target_qty: 2,
        mandatory_flag: true,
        sort_order: 1,
        remark: 'Front gate',
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
      {
        id: 'dg-4',
        tenant_id: 'tenant-1',
        shift_id: 'shift-2',
        function_type_id: 'function-2',
        qualification_type_id: null,
        min_qty: 1,
        target_qty: 1,
        mandatory_flag: false,
        sort_order: 2,
        remark: null,
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 2);

    expect(wrapper.findAll('[data-testid="customer-new-plan-demand-group-row"]')).toHaveLength(0);
    expect(wrapper.get('[data-testid="customer-new-plan-demand-group-persisted-list"]').findAll('[data-testid="customer-new-plan-demand-group-persisted-row"]')).toHaveLength(2);
    expect(wrapper.text()).toContain('Dispatch support');
    expect(wrapper.text()).toContain('Fire watch');
    expect(apiMocks.listDemandGroupsMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listDemandGroupsMock).toHaveBeenCalledWith('tenant-1', 'token-1', {
      include_archived: false,
      shift_plan_id: 'plan-1',
    });
    expect((wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          applied_shift_count: 2,
          function_type_label: 'Dispatch support',
          total_shift_count: 2,
        }),
        expect.objectContaining({
          applied_shift_count: 2,
          function_type_label: 'Fire watch',
          total_shift_count: 2,
        }),
      ]),
    );
    expect(wrapper.emitted('step-completion')).toContainEqual(['demand-groups', true]);
  });

  it('loads demand-groups with one scoped demand-group request and without unrelated reference calls', async () => {
    apiMocks.listShiftsMock.mockResolvedValue(
      Array.from({ length: 23 }, (_, index) => ({
        id: `shift-${index + 1}`,
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: `2026-07-${String(index + 1).padStart(2, '0')}`,
        starts_at: `2026-07-${String(index + 1).padStart(2, '0')}T08:00:00Z`,
        ends_at: `2026-07-${String(index + 1).padStart(2, '0')}T16:00:00Z`,
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      })),
    );
    employeeAdminMocks.listFunctionTypesMock.mockResolvedValue([
      { id: 'function-1', tenant_id: 'tenant-1', label: 'Dispatch support', status: 'active', version_no: 1, archived_at: null },
    ]);
    employeeAdminMocks.listQualificationTypesMock.mockResolvedValue([
      { id: 'qualification-1', tenant_id: 'tenant-1', label: 'Crowd control', status: 'active', version_no: 1, archived_at: null },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([
      {
        id: 'dg-1',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-1',
        qualification_type_id: 'qualification-1',
        min_qty: 1,
        target_qty: 2,
        mandatory_flag: true,
        sort_order: 1,
        remark: 'Front gate',
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 23);

    expect(apiMocks.listDemandGroupsMock).toHaveBeenCalledTimes(1);
    expect(apiMocks.listDemandGroupsMock).toHaveBeenCalledWith('tenant-1', 'token-1', {
      include_archived: false,
      shift_plan_id: 'plan-1',
    });
    expect(apiMocks.listPlanningSetupRecordsMock).not.toHaveBeenCalled();
    expect(apiMocks.listServiceCategoryOptionsMock).not.toHaveBeenCalled();
    expect(apiMocks.listTradeFairZonesMock).not.toHaveBeenCalled();
    expect(apiMocks.listShiftTemplatesMock).not.toHaveBeenCalled();
    expect(apiMocks.listShiftTypeOptionsMock).not.toHaveBeenCalled();
    expect(apiMocks.listShiftSeriesExceptionsMock).not.toHaveBeenCalled();
    expect(apiMocks.getPlanningRecordMock).not.toHaveBeenCalled();
    expect(wrapper.get('[data-testid="customer-new-plan-demand-groups-generated-count"]').text()).toBe('23');
  });

  it('does not refetch demand-groups for the same step context', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 1);

    expect(apiMocks.listDemandGroupsMock).toHaveBeenCalledTimes(1);

    await wrapper.setProps({
      wizardState: {
        ...baseWizardState(),
        current_step: 'demand-groups',
        planning_record_id: 'record-1',
        shift_plan_id: 'plan-1',
        series_id: 'series-1',
      },
    });
    await flushPromises();
    await settleLoadingRender();

    expect(apiMocks.listDemandGroupsMock).toHaveBeenCalledTimes(1);
  });

  it('ignores and clears a persisted demand-groups draft from a different plan context', async () => {
    window.sessionStorage.setItem(
      buildDemandGroupsDraftKey(),
      JSON.stringify({
        context: {
          order_id: 'order-1',
          planning_record_id: 'record-1',
          shift_plan_id: 'plan-other',
          series_id: 'series-other',
        },
        rows: [
          {
            function_type_id: 'function-1',
            qualification_type_id: '',
            min_qty: 1,
            target_qty: 2,
            mandatory_flag: true,
            sort_order: 1,
            remark: 'stale',
          },
        ],
      }),
    );
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 1);

    expect((wrapper.vm as any).$?.setupState.demandGroupDraftRows).toHaveLength(0);
    expect(wrapper.find('[data-testid="customer-new-plan-draft-restored"]').exists()).toBe(false);
    expect(window.sessionStorage.getItem(buildDemandGroupsDraftKey())).toBeNull();
  });

  it('renders applied demand-group actions and prefills the aggregate edit dialog', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: 'North gate',
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    employeeAdminMocks.listFunctionTypesMock.mockResolvedValue([
      { id: 'function-1', tenant_id: 'tenant-1', label: 'Dispatch support', status: 'active', version_no: 1, archived_at: null },
    ]);
    employeeAdminMocks.listQualificationTypesMock.mockResolvedValue([
      { id: 'qualification-1', tenant_id: 'tenant-1', label: 'Crowd control', status: 'active', version_no: 1, archived_at: null },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([
      {
        id: 'dg-1',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-1',
        qualification_type_id: 'qualification-1',
        min_qty: 1,
        target_qty: 2,
        mandatory_flag: true,
        sort_order: 1,
        remark: 'Front gate',
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 1);

    const rowVm = (wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows[0];
    expect(wrapper.find(`[data-testid="customer-new-plan-demand-group-persisted-days-${rowVm.signature_key}"]`).exists()).toBe(true);
    expect(wrapper.find(`[data-testid="customer-new-plan-demand-group-persisted-edit-${rowVm.signature_key}"]`).exists()).toBe(true);
    const header = wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-header-${rowVm.signature_key}"]`);
    const headerButtons = header.findAll('button');
    expect(headerButtons).toHaveLength(2);
    expect(headerButtons[0]?.attributes('data-testid')).toBe(`customer-new-plan-demand-group-persisted-days-${rowVm.signature_key}`);
    expect(headerButtons[1]?.attributes('data-testid')).toBe(`customer-new-plan-demand-group-persisted-edit-${rowVm.signature_key}`);
    expect(wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-status-${rowVm.signature_key}"]`).exists()).toBe(true);

    await wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-edit-${rowVm.signature_key}"]`).trigger('click');
    await flushPromises();

    expect(wrapper.find('[data-testid="customer-new-plan-demand-group-aggregate-modal"]').exists()).toBe(true);
    const aggregateDraft = (wrapper.vm as any).$?.setupState.aggregateDemandGroupDialog;
    expect(aggregateDraft.function_type_id).toBe('function-1');
    expect(aggregateDraft.qualification_type_id).toBe('qualification-1');
    expect(aggregateDraft.min_qty).toBe(1);
    expect(aggregateDraft.target_qty).toBe(2);
    expect(aggregateDraft.sort_order).toBe(1);
    expect(aggregateDraft.remark).toBe('Front gate');
  });

  it('saves aggregate demand-group edits through the bulk update API and reloads the summary', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
      {
        id: 'shift-2',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-03',
        starts_at: '2026-07-03T08:00:00Z',
        ends_at: '2026-07-03T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    employeeAdminMocks.listFunctionTypesMock.mockResolvedValue([
      { id: 'function-1', tenant_id: 'tenant-1', label: 'Dispatch support', status: 'active', version_no: 1, archived_at: null },
      { id: 'function-2', tenant_id: 'tenant-1', label: 'Fire watch', status: 'active', version_no: 1, archived_at: null },
    ]);
    apiMocks.listDemandGroupsMock
      .mockResolvedValueOnce([
        {
          id: 'dg-1',
          tenant_id: 'tenant-1',
          shift_id: 'shift-1',
          function_type_id: 'function-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 2,
          mandatory_flag: true,
          sort_order: 1,
          remark: null,
          status: 'active',
          version_no: 1,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
        {
          id: 'dg-2',
          tenant_id: 'tenant-1',
          shift_id: 'shift-2',
          function_type_id: 'function-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 2,
          mandatory_flag: true,
          sort_order: 1,
          remark: null,
          status: 'active',
          version_no: 1,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          id: 'dg-1',
          tenant_id: 'tenant-1',
          shift_id: 'shift-1',
          function_type_id: 'function-2',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 4,
          mandatory_flag: true,
          sort_order: 1,
          remark: 'Updated',
          status: 'active',
          version_no: 2,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
        {
          id: 'dg-2',
          tenant_id: 'tenant-1',
          shift_id: 'shift-2',
          function_type_id: 'function-2',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 4,
          mandatory_flag: true,
          sort_order: 1,
          remark: 'Updated',
          status: 'active',
          version_no: 2,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
      ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 2);

    const rowVm = (wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows[0];
    await wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-edit-${rowVm.signature_key}"]`).trigger('click');
    await flushPromises();
    const aggregateDraft = (wrapper.vm as any).$?.setupState.aggregateDemandGroupDialog;
    aggregateDraft.function_type_id = 'function-2';
    aggregateDraft.target_qty = 4;
    aggregateDraft.remark = 'Updated';
    await (wrapper.vm as any).$?.setupState.submitAggregateDemandGroupDialog();
    await flushPromises();

    expect(apiMocks.bulkUpdateDemandGroupsMock).toHaveBeenCalledWith('tenant-1', 'token-1', expect.objectContaining({
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
      expected_target_shift_count: 2,
    }));
    expect((wrapper.vm as any).$?.setupState.demandGroupSummaryMessage).toContain(
      'sicherplan.customerPlansWizard.messages.demandGroupsBulkUpdatedSummary',
    );
    expect((wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows[0].target_qty).toBe(4);
  });

  it('opens a sorted per-shift edit list and updates one persisted demand-group row', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-2',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-03',
        starts_at: '2026-07-03T08:00:00Z',
        ends_at: '2026-07-03T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: 'South gate',
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: 'North gate',
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    employeeAdminMocks.listFunctionTypesMock.mockResolvedValue([
      { id: 'function-1', tenant_id: 'tenant-1', label: 'Dispatch support', status: 'active', version_no: 1, archived_at: null },
    ]);
    apiMocks.listDemandGroupsMock
      .mockResolvedValueOnce([
        {
          id: 'dg-1',
          tenant_id: 'tenant-1',
          shift_id: 'shift-1',
          function_type_id: 'function-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 2,
          mandatory_flag: true,
          sort_order: 1,
          remark: 'Shared',
          status: 'active',
          version_no: 1,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
        {
          id: 'dg-2',
          tenant_id: 'tenant-1',
          shift_id: 'shift-2',
          function_type_id: 'function-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 2,
          mandatory_flag: true,
          sort_order: 1,
          remark: 'Shared',
          status: 'active',
          version_no: 1,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          id: 'dg-1',
          tenant_id: 'tenant-1',
          shift_id: 'shift-1',
          function_type_id: 'function-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 2,
          mandatory_flag: true,
          sort_order: 1,
          remark: 'Shared',
          status: 'active',
          version_no: 1,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
        {
          id: 'dg-2',
          tenant_id: 'tenant-1',
          shift_id: 'shift-2',
          function_type_id: 'function-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 2,
          mandatory_flag: true,
          sort_order: 1,
          remark: 'Shared',
          status: 'active',
          version_no: 1,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
        {
          id: 'dg-1',
          tenant_id: 'tenant-1',
          shift_id: 'shift-1',
          function_type_id: 'function-1',
          qualification_type_id: null,
          min_qty: 1,
          target_qty: 3,
          mandatory_flag: true,
          sort_order: 1,
          remark: 'North updated',
          status: 'active',
          version_no: 2,
          created_at: '2026-07-01T08:00:00Z',
          updated_at: '2026-07-01T08:00:00Z',
          archived_at: null,
        },
      ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 2);

    const rowVm = (wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows[0];
    await wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-days-${rowVm.signature_key}"]`).trigger('click');
    await flushPromises();

    const shiftButtons = wrapper.findAll('[data-testid^="customer-new-plan-demand-group-shift-row-"]');
    expect(shiftButtons[0]?.text()).toContain('2026-07-02');
    expect(shiftButtons[1]?.text()).toContain('2026-07-03');

    await wrapper.get('[data-testid="customer-new-plan-demand-group-shift-row-dg-1"]').trigger('click');
    await flushPromises();
    const rowDraft = (wrapper.vm as any).$?.setupState.shiftDemandGroupDialogDraft;
    rowDraft.target_qty = 3;
    rowDraft.remark = 'North updated';
    await (wrapper.vm as any).$?.setupState.submitShiftDemandGroupDialog();
    await flushPromises();

    expect(apiMocks.updateDemandGroupMock).toHaveBeenCalledWith('tenant-1', 'token-1', 'dg-1', expect.objectContaining({
      target_qty: 3,
      remark: 'North updated',
      version_no: 1,
    }));
    expect((wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          target_qty: 3,
          remark: 'North updated',
        }),
      ]),
    );
  });

  it('disables applied edit actions when the visible shift state is already locked', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'released',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([
      {
        id: 'dg-1',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-1',
        qualification_type_id: null,
        min_qty: 1,
        target_qty: 1,
        mandatory_flag: true,
        sort_order: 1,
        remark: null,
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 1);

    const rowVm = (wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows[0];
    expect(wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-edit-${rowVm.signature_key}"]`).attributes('disabled')).toBeDefined();
    expect(wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-days-${rowVm.signature_key}"]`).attributes('disabled')).toBeDefined();
  });

  it('disables applied edit actions when the backend marks persisted demand groups as blocked', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([
      {
        id: 'dg-1',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-1',
        qualification_type_id: null,
        min_qty: 1,
        target_qty: 1,
        mandatory_flag: true,
        sort_order: 1,
        remark: null,
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
        editable_flag: false,
        edit_block_reason_codes: ['assignments_exist'],
        active_assignment_count: 2,
        active_subcontractor_release_count: 0,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 1);

    const rowVm = (wrapper.vm as any).$?.setupState.persistedDemandGroupSummaryRows[0];
    expect(rowVm.has_locked_rows).toBe(true);
    expect(rowVm.shift_rows[0].edit_block_reason_codes).toEqual(['assignments_exist']);
    expect(rowVm.shift_rows[0].active_assignment_count).toBe(2);
    expect(wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-edit-${rowVm.signature_key}"]`).attributes('disabled')).toBeDefined();
    expect(wrapper.get(`[data-testid="customer-new-plan-demand-group-persisted-days-${rowVm.signature_key}"]`).attributes('disabled')).toBeDefined();
  });

  it('does not bulk apply again when persisted demand groups exist but there are no pending templates', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([
      {
        id: 'dg-1',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-1',
        qualification_type_id: null,
        min_qty: 1,
        target_qty: 1,
        mandatory_flag: true,
        sort_order: 1,
        remark: null,
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 1);

    expect(await (wrapper.vm as any).submitCurrentStep()).toBe(false);
    await flushPromises();
    expect(apiMocks.bulkApplyDemandGroupsMock).not.toHaveBeenCalled();
    expect(wrapper.get('[data-testid="customer-new-plan-demand-groups-validation"]').text()).toContain(
      'sicherplan.customerPlansWizard.errors.demandGroupsNoPendingTemplates',
    );
  });

  it('applies demand groups successfully and marks the step complete', async () => {
    apiMocks.listShiftsMock.mockResolvedValue([
      {
        id: 'shift-1',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-02',
        starts_at: '2026-07-02T08:00:00Z',
        ends_at: '2026-07-02T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
      {
        id: 'shift-2',
        tenant_id: 'tenant-1',
        shift_plan_id: 'plan-1',
        shift_series_id: 'series-1',
        occurrence_date: '2026-07-03',
        starts_at: '2026-07-03T08:00:00Z',
        ends_at: '2026-07-03T16:00:00Z',
        break_minutes: 30,
        shift_type_code: 'day',
        location_text: null,
        meeting_point: null,
        release_state: 'draft',
        customer_visible_flag: false,
        subcontractor_visible_flag: false,
        stealth_mode_flag: false,
        source_kind_code: 'generated',
        status: 'active',
        version_no: 1,
      },
    ]);
    apiMocks.listDemandGroupsMock.mockResolvedValue([
      {
        id: 'dg-1',
        tenant_id: 'tenant-1',
        shift_id: 'shift-1',
        function_type_id: 'function-1',
        qualification_type_id: null,
        min_qty: 1,
        target_qty: 2,
        mandatory_flag: true,
        sort_order: 1,
        remark: null,
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
      {
        id: 'dg-2',
        tenant_id: 'tenant-1',
        shift_id: 'shift-2',
        function_type_id: 'function-1',
        qualification_type_id: null,
        min_qty: 1,
        target_qty: 2,
        mandatory_flag: true,
        sort_order: 1,
        remark: null,
        status: 'active',
        version_no: 1,
        created_at: '2026-07-01T08:00:00Z',
        updated_at: '2026-07-01T08:00:00Z',
        archived_at: null,
      },
    ]);

    const wrapper = mountStep('demand-groups', {
      current_step: 'demand-groups',
      planning_record_id: 'record-1',
      shift_plan_id: 'plan-1',
      series_id: 'series-1',
    });
    await waitForDemandGroupsStepReady(wrapper, 2);

    await wrapper.get('[data-testid="customer-new-plan-demand-group-new"]').trigger('click');
    await flushPromises();
    const applyDialog = (wrapper.vm as any).$?.setupState.demandGroupDialog;
    applyDialog.function_type_id = 'function-1';
    applyDialog.target_qty = 2;
    applyDialog.sort_order = 1;
    (wrapper.vm as any).$?.setupState.submitDemandGroupDialog();
    await flushPromises();

    const saved = await (wrapper.vm as any).submitCurrentStep();

    expect(saved).toMatchObject({
      completedStepId: 'demand-groups',
      success: true,
    });
    expect(apiMocks.bulkApplyDemandGroupsMock).toHaveBeenCalledWith('tenant-1', 'token-1', expect.objectContaining({
      apply_mode: 'upsert_matching',
      shift_plan_id: 'plan-1',
      shift_series_id: 'series-1',
    }));
    expect(wrapper.emitted('step-completion')).toContainEqual(['demand-groups', true]);
    await nextTick();
    await waitForCondition(() => wrapper.findAll('[data-testid="customer-new-plan-demand-group-persisted-row"]').length === 1);
    expect((wrapper.vm as any).$?.setupState.demandGroupSummaryMessage).toContain(
      'sicherplan.customerPlansWizard.messages.demandGroupsAppliedSummary',
    );
    expect(wrapper.get('[data-testid="customer-new-plan-demand-group-persisted-list"]').findAll('[data-testid="customer-new-plan-demand-group-persisted-row"]')).toHaveLength(1);
  });
});
