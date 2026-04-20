<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { Modal } from 'ant-design-vue';

import { $t } from '#/locales';
import {
  createCustomerAvailableAddress,
  listCustomerAddresses,
  type CustomerAvailableAddressRead,
  type CustomerAddressRead,
} from '#/sicherplan-legacy/api/customers';
import {
  listFunctionTypes,
  listQualificationTypes,
  type FunctionTypeRead,
  type QualificationTypeRead,
} from '#/sicherplan-legacy/api/employeeAdmin';
import {
  createPlanningRecord as createPlanningSetupRecord,
  listPlanningRecords as listPlanningSetupRecords,
  listTradeFairZones,
  type PlanningListItem,
  type TradeFairZoneRead,
} from '#/sicherplan-legacy/api/planningAdmin';
import {
  createPlanningRecord,
  createPlanningRecordAttachment,
  createCustomerOrder,
  createOrderAttachment,
  createOrderEquipmentLine,
  createOrderRequirementLine,
  getCustomerOrder,
  listCustomerOrders,
  getPlanningRecord,
  linkPlanningRecordAttachment,
  linkOrderAttachment,
  listOrderAttachments,
  listOrderEquipmentLines,
  listOrderRequirementLines,
  listPlanningRecords as listOperationalPlanningRecords,
  listPlanningRecordAttachments,
  listServiceCategoryOptions,
  updatePlanningRecord,
  updateCustomerOrder,
  updateOrderEquipmentLine,
  updateOrderRequirementLine,
  type CustomerOrderRead,
  type OrderEquipmentLineRead,
  type OrderRequirementLineRead,
  type PlanningCatalogRecordRead,
  type PlanningDocumentRead,
  type PlanningRecordListItem,
  type PlanningRecordRead,
  type PlanningReferenceOptionRead,
  type CustomerOrderListItem,
} from '#/sicherplan-legacy/api/planningOrders';
import {
  derivePlanningOrderSubmitBlockReason,
  filterPlanningOrderOptionsByScope,
  hasDuplicateActiveRequirementLine,
  validatePlanningRecordDraft,
} from '#/sicherplan-legacy/features/planning/planningOrders.helpers';
import PlanningLocationPickerModal from '#/sicherplan-legacy/components/planning/PlanningLocationPickerModal.vue';
import {
  formatPlanningAddressOption,
  resolveInitialMapCenter,
} from '#/sicherplan-legacy/features/planning/planningAdmin.helpers';
import {
  createShiftPlan,
  createShiftSeries,
  createShiftSeriesException,
  createShiftTemplate,
  generateShiftSeries,
  getShiftPlan,
  getShiftSeries,
  listShiftPlans,
  listShiftSeries,
  listShiftSeriesExceptions,
  listShiftTemplates,
  listShiftTypeOptions,
  updateShiftPlan,
  updateShiftSeries,
  updateShiftSeriesException,
  type ShiftPlanListItem,
  type ShiftPlanRead,
  type ShiftSeriesExceptionRead,
  type ShiftSeriesRead,
  type ShiftTemplateListItem,
  type ShiftTypeOption,
} from '#/sicherplan-legacy/api/planningShifts';
import type {
  CustomerNewPlanWizardState,
  CustomerNewPlanWizardStatePatch,
  CustomerNewPlanWizardStepId,
} from './new-plan-wizard.types';
import {
  clearWizardDraft,
  clearOrderDetailsEditDraft,
  loadWizardDraftCandidatesForCustomer,
  loadOrderDetailsEditDraft,
  loadWizardDraft,
  saveOrderDetailsEditDraft,
  saveWizardDraft,
  type CustomerNewPlanWizardDraftContext,
} from './new-plan-wizard-drafts';

type PlanningEntityType = 'event_venue' | 'patrol_route' | 'site' | 'trade_fair';
type PlanningSelectionMode = 'create_new' | 'use_existing';
type OrderSelectionMode = 'create_new' | 'use_existing';
interface ShiftPlanDraftPersistence {
  draft: Partial<typeof shiftPlanDraft>;
  selected_shift_plan_id: string;
}

const router = useRouter();
const route = useRoute();

const props = defineProps<{
  accessToken: string;
  currentStepId: CustomerNewPlanWizardStepId;
  customer: {
    customer_number?: string | null;
    id: string;
    name?: string | null;
  };
  persistDraftsOnUnmount?: boolean;
  tenantId: string;
  wizardState: CustomerNewPlanWizardState;
}>();

const emit = defineEmits<{
  (event: 'saved-context', patch: CustomerNewPlanWizardStatePatch): void;
  (event: 'step-completion', stepId: CustomerNewPlanWizardStepId, completed: boolean): void;
  (event: 'step-ui-state', stepId: CustomerNewPlanWizardStepId, patch: { dirty?: boolean; error?: string; loading?: boolean }): void;
}>();

const planningFamily = ref<PlanningEntityType>('site');
const planningSelectionMode = ref<PlanningSelectionMode>('use_existing');
const planningEntityOptions = ref<PlanningListItem[]>([]);
const planningEntityId = ref('');
const planningEntityLoading = ref(false);
const planningEntityError = ref('');
const orderSelectionMode = ref<OrderSelectionMode>('use_existing');
const customerOrderRows = ref<CustomerOrderListItem[]>([]);
const customerOrderRowsLoading = ref(false);
const customerOrderRowsError = ref('');
const selectedExistingOrderId = ref('');
const editingExistingOrderId = ref('');
const pendingExistingOrderEditId = ref('');
const existingOrderEditFormOpen = ref(false);

const orderDraft = reactive({
  customer_id: '',
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
});

const equipmentLineDraft = reactive({
  equipment_item_id: '',
  notes: '',
  required_qty: 1,
});

const requirementLineDraft = reactive({
  function_type_id: '',
  min_qty: 0,
  notes: '',
  qualification_type_id: '',
  requirement_type_id: '',
  target_qty: 1,
});

const orderAttachmentDraft = reactive({
  content_base64: '',
  content_type: '',
  file_name: '',
  label: '',
  title: '',
});

const orderAttachmentLink = reactive({
  document_id: '',
  label: '',
});

const planningRecordDraft = reactive({
  dispatcher_user_id: '',
  event_detail_event_venue_id: '',
  event_detail_setup_note: '',
  name: '',
  notes: '',
  parent_planning_record_id: '',
  patrol_detail_execution_note: '',
  patrol_detail_patrol_route_id: '',
  planning_from: '',
  planning_mode_code: '',
  planning_to: '',
  site_detail_site_id: '',
  site_detail_watchbook_scope_note: '',
  status: 'active',
  trade_fair_detail_stand_note: '',
  trade_fair_detail_trade_fair_id: '',
  trade_fair_detail_trade_fair_zone_id: '',
});

const planningRecordAttachmentDraft = reactive({
  content_base64: '',
  content_type: '',
  file_name: '',
  label: '',
  title: '',
});

const planningRecordAttachmentLink = reactive({
  document_id: '',
  label: '',
});

const shiftPlanDraft = reactive({
  name: '',
  planning_from: '',
  planning_record_id: '',
  planning_to: '',
  remarks: '',
  workforce_scope_code: 'internal',
});

const seriesDraft = reactive({
  customer_visible_flag: false,
  date_from: '',
  date_to: '',
  default_break_minutes: 30,
  interval_count: 1,
  label: '',
  location_text: '',
  meeting_point: '',
  notes: '',
  recurrence_code: 'daily',
  release_state: 'draft',
  shift_template_id: '',
  shift_type_code: '',
  stealth_mode_flag: false,
  subcontractor_visible_flag: false,
  timezone: 'Europe/Berlin',
  weekday_mask: '1111100',
});

const exceptionDraft = reactive({
  action_code: 'skip',
  customer_visible_flag: null as boolean | null,
  exception_date: '',
  notes: '',
  override_break_minutes: '',
  override_local_end_time: '',
  override_local_start_time: '',
  override_location_text: '',
  override_meeting_point: '',
  override_shift_type_code: '',
  stealth_mode_flag: null as boolean | null,
  subcontractor_visible_flag: null as boolean | null,
});

const planningCreateModal = reactive({
  address_id: '',
  end_date: '',
  fair_no: '',
  latitude: '',
  longitude: '',
  meeting_address_id: '',
  name: '',
  notes: '',
  open: false,
  route_no: '',
  saving: false,
  site_id: '',
  site_no: '',
  start_date: '',
  start_point_text: '',
  status: 'active',
  timezone: 'Europe/Berlin',
  travel_policy_code: '',
  venue_id: '',
  venue_no: '',
  watchbook_enabled: false,
  end_point_text: '',
});

const planningAddressCreateModal = reactive({
  city: '',
  country_code: 'DE',
  error: '',
  open: false,
  postal_code: '',
  saving: false,
  state: '',
  street_line_1: '',
  street_line_2: '',
});

const requirementModal = reactive({
  code: '',
  default_planning_mode_code: 'site',
  label: '',
  notes: '',
  open: false,
  saving: false,
});

const equipmentModal = reactive({
  code: '',
  label: '',
  notes: '',
  open: false,
  saving: false,
  unit_of_measure_code: 'piece',
});

const templateModal = reactive({
  code: '',
  default_break_minutes: 30,
  label: '',
  local_end_time: '16:00',
  local_start_time: '08:00',
  location_text: '',
  meeting_point: '',
  notes: '',
  open: false,
  saving: false,
  shift_type_code: '',
});

const selectedEquipmentLineId = ref('');
const selectedRequirementLineId = ref('');
const selectedExceptionId = ref('');
const selectedOrder = ref<CustomerOrderRead | null>(null);
const selectedPlanningRecord = ref<PlanningRecordRead | null>(null);
const selectedShiftPlan = ref<ShiftPlanRead | null>(null);
const selectedSeries = ref<ShiftSeriesRead | null>(null);
const planningRecordRows = ref<PlanningRecordListItem[]>([]);
const planningRecordRowsLoading = ref(false);
const planningRecordRowsError = ref('');
const orderEquipmentLines = ref<OrderEquipmentLineRead[]>([]);
const orderRequirementLines = ref<OrderRequirementLineRead[]>([]);
const orderAttachments = ref<PlanningDocumentRead[]>([]);
const planningRecordAttachments = ref<PlanningDocumentRead[]>([]);
const requirementTypeOptions = ref<PlanningListItem[]>([]);
const patrolRouteOptions = ref<PlanningListItem[]>([]);
const eventVenueOptions = ref<PlanningListItem[]>([]);
const siteOptions = ref<PlanningListItem[]>([]);
const tradeFairOptions = ref<PlanningListItem[]>([]);
const equipmentItemOptions = ref<PlanningCatalogRecordRead[]>([]);
const serviceCategoryOptions = ref<PlanningReferenceOptionRead[]>([]);
const functionTypeOptions = ref<FunctionTypeRead[]>([]);
const qualificationTypeOptions = ref<QualificationTypeRead[]>([]);
const shiftPlanRows = ref<ShiftPlanListItem[]>([]);
const shiftTemplateOptions = ref<ShiftTemplateListItem[]>([]);
const shiftTypeOptions = ref<ShiftTypeOption[]>([]);
const seriesRows = ref<any[]>([]);
const seriesExceptions = ref<ShiftSeriesExceptionRead[]>([]);
const planningCreateAddressOptions = ref<CustomerAddressRead[]>([]);
const planningCreateStagedAddresses = ref<CustomerAvailableAddressRead[]>([]);
const planningCreateAddressLookupLoading = ref(false);
const planningCreateAddressLookupError = ref('');
const planningLocationPickerOpen = ref(false);
const planningLocationPickerStartPoint = ref({
  label: '',
  lat: 51.662973,
  lng: 8.174013,
  zoom: 11,
});
const tradeFairZoneOptions = ref<TradeFairZoneRead[]>([]);
const tradeFairZoneLookupLoading = ref(false);
const tradeFairZoneLookupError = ref('');

const stepFeedback = reactive({
  message: '',
  tone: 'neutral' as 'error' | 'neutral' | 'success',
});

const draftRestoreMessage = ref('');
const draftSyncPaused = ref(false);
const stepLoading = ref(false);
const planningContextHydrationPaused = ref(false);
let stepRefreshSequence = 0;
let lastLoadedStepContextKey = '';

type AttachmentDraftPersistence = {
  content_type: string;
  file_name: string;
  file_needs_reselect?: boolean;
  label: string;
  title: string;
};

type OrderDetailsDraftPersistence = {
  form: typeof orderDraft;
  mode?: OrderSelectionMode;
  selected_order_id?: string;
};

type OrderDetailsEditDraftPersistence = {
  form: typeof orderDraft;
};

type OrderDocumentsDraftPersistence = {
  attachment: AttachmentDraftPersistence;
  link: {
    document_id: string;
    label: string;
  };
};

type PlanningRecordOverviewDraftPersistence = {
  form: Partial<typeof planningRecordDraft>;
  order_id?: string;
  planning_context?: {
    planning_entity_id: string;
    planning_entity_type: PlanningEntityType;
    planning_mode_code: string;
  };
  selection_mode?: PlanningSelectionMode;
};

type SeriesExceptionsDraftPersistence = {
  exception: typeof exceptionDraft;
  series: typeof seriesDraft;
};

const planningFamilyOptions = computed(() => [
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.site'), value: 'site' },
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.eventVenue'), value: 'event_venue' },
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.tradeFair'), value: 'trade_fair' },
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.patrolRoute'), value: 'patrol_route' },
]);

function mapPlanningEntityTypeToModeCode(entityType: PlanningEntityType | '' | null | undefined) {
  const mapping: Record<PlanningEntityType, string> = {
    event_venue: 'event',
    patrol_route: 'patrol',
    site: 'site',
    trade_fair: 'trade_fair',
  };
  return entityType ? mapping[entityType] : '';
}

const planningModeCode = computed(() => mapPlanningEntityTypeToModeCode(planningFamily.value));

const planningModeLabel = computed(() => {
  const mode = props.wizardState.planning_mode_code || planningModeCode.value;
  if (mode === 'event') {
    return $t('sicherplan.customerPlansWizard.forms.planningModeEvent');
  }
  if (mode === 'trade_fair') {
    return $t('sicherplan.customerPlansWizard.forms.planningModeTradeFair');
  }
  if (mode === 'patrol') {
    return $t('sicherplan.customerPlansWizard.forms.planningModePatrol');
  }
  return $t('sicherplan.customerPlansWizard.forms.planningModeSite');
});

const planningEntityLabel = computed(() => {
  const row = planningEntityOptions.value.find((option) => option.id === planningEntityId.value);
  return row?.name || row?.label || row?.code || row?.id || '';
});

const requirementTypeSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope('requirement_type', requirementTypeOptions.value, props.customer.id).map((row) => ({
    label: row.label || row.code || row.name || row.id,
    value: row.id,
  })),
);

const patrolRouteSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope('patrol_route', patrolRouteOptions.value, props.customer.id).map((row) => ({
    label: row.name || row.code || row.label || row.id,
    value: row.id,
  })),
);

const equipmentItemSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope('equipment_item', equipmentItemOptions.value, props.customer.id).map((row) => ({
    label: row.label || row.code || row.name || row.id,
    value: row.id,
  })),
);

const functionTypeSelectOptions = computed(() =>
  functionTypeOptions.value.map((row) => ({
    label: row.label,
    value: row.id,
  })),
);

const qualificationTypeSelectOptions = computed(() =>
  qualificationTypeOptions.value.map((row) => ({
    label: row.label,
    value: row.id,
  })),
);

const serviceCategorySelectOptions = computed(() =>
  serviceCategoryOptions.value.map((row) => ({
    label: row.label,
    value: row.code,
  })),
);

const eventVenueSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope('event_venue', eventVenueOptions.value, props.customer.id).map((row) => ({
    label: row.name || row.label || row.code || row.id,
    value: row.id,
  })),
);

const siteSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope('site', siteOptions.value, props.customer.id).map((row) => ({
    label: row.name || row.label || row.code || row.id,
    value: row.id,
  })),
);

const tradeFairSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope('trade_fair', tradeFairOptions.value, props.customer.id).map((row) => ({
    label: row.name || row.label || row.code || row.id,
    value: row.id,
  })),
);

const shiftPlanSelectOptions = computed(() =>
  shiftPlanRows.value.map((row) => ({
    label: `${row.name} · ${row.planning_from} - ${row.planning_to}`,
    value: row.id,
  })),
);

const shiftTemplateSelectOptions = computed(() =>
  shiftTemplateOptions.value.map((row) => ({
    label: row.label || row.code,
    value: row.id,
  })),
);

const shiftTypeSelectOptions = computed(() =>
  shiftTypeOptions.value.map((row) => ({
    label: row.label,
    value: row.code,
  })),
);

const planningCreateAddressSelectOptions = computed(() =>
  mergePlanningCreateAddressOptions().map((row) => ({
    label: formatPlanningAddressOption(row),
    value: row.address_id,
  })),
);

const planningCreateAddressFieldKey = computed(() => {
  if (planningFamily.value === 'patrol_route') {
    return 'meeting_address_id';
  }
  if (planningFamily.value === 'site' || planningFamily.value === 'event_venue' || planningFamily.value === 'trade_fair') {
    return 'address_id';
  }
  return '';
});

const planningCreateHasAddressField = computed(() => !!planningCreateAddressFieldKey.value);
const planningCreateSupportsLocationPicker = computed(
  () => planningFamily.value === 'site' || planningFamily.value === 'event_venue' || planningFamily.value === 'trade_fair',
);
const planningLocationPickerLatitude = computed(() => planningCreateModal.latitude);
const planningLocationPickerLongitude = computed(() => planningCreateModal.longitude);

const tradeFairZoneSelectOptions = computed(() =>
  tradeFairZoneOptions.value.map((row) => ({
    label: [row.zone_code, row.label].filter(Boolean).join(' — ') || row.id,
    value: row.id,
  })),
);

const timezoneOptions = computed(() =>
  getSupportedTimezones().map((timezone) => ({
    label: timezone,
    value: timezone,
  })),
);

const orderStepActive = computed(() => props.currentStepId === 'order-details');
const equipmentStepActive = computed(() => props.currentStepId === 'equipment-lines');
const requirementStepActive = computed(() => props.currentStepId === 'requirement-lines');
const documentsStepActive = computed(() => props.currentStepId === 'order-documents');
const planningRecordStepActive = computed(() => props.currentStepId === 'planning-record-overview');
const planningRecordDocumentsStepActive = computed(() => props.currentStepId === 'planning-record-documents');
const shiftPlanStepActive = computed(() => props.currentStepId === 'shift-plan');
const seriesStepActive = computed(() => props.currentStepId === 'series-exceptions');
const stepRefreshContextKey = computed(() =>
  JSON.stringify({
    currentStepId: props.currentStepId,
    customerId: props.customer.id,
    orderId: props.wizardState.order_id,
    planningEntityId: props.wizardState.planning_entity_id,
    planningEntityType: props.wizardState.planning_entity_type,
    planningModeCode: props.wizardState.planning_mode_code,
    planningRecordId: props.wizardState.planning_record_id,
    seriesId: props.wizardState.series_id,
    shiftPlanId: props.wizardState.shift_plan_id,
    tenantId: props.tenantId,
  }),
);
const handledStepActive = computed(
  () =>
    orderStepActive.value ||
    equipmentStepActive.value ||
    requirementStepActive.value ||
    documentsStepActive.value ||
    planningRecordStepActive.value ||
    planningRecordDocumentsStepActive.value ||
    shiftPlanStepActive.value ||
    seriesStepActive.value,
);
const orderModeUsesExisting = computed(() => orderSelectionMode.value === 'use_existing');
const planningModeUsesExisting = computed(() => planningSelectionMode.value === 'use_existing');
const orderSelectionModeModel = computed<OrderSelectionMode>({
  get: () => orderSelectionMode.value,
  set: (value) => setOrderSelectionMode(value),
});
const planningSelectionModeModel = computed<PlanningSelectionMode>({
  get: () => planningSelectionMode.value,
  set: (value) => setPlanningSelectionMode(value),
});
const selectedExistingOrderSummary = computed(
  () => customerOrderRows.value.find((row) => row.id === selectedExistingOrderId.value) ?? null,
);
const selectedShiftPlanSummary = computed(
  () => selectedShiftPlan.value ?? shiftPlanRows.value.find((row) => row.id === props.wizardState.shift_plan_id) ?? null,
);
const existingOrderEditActive = computed(
  () => orderModeUsesExisting.value && Boolean(existingOrderEditFormOpen.value && editingExistingOrderId.value),
);
const currentPlanningEntityScope = computed(() => {
  const routePlanningEntityId = typeof route.query.planning_entity_id === 'string' ? route.query.planning_entity_id.trim() : '';
  const routePlanningEntityType = typeof route.query.planning_entity_type === 'string' ? route.query.planning_entity_type.trim() : '';
  const localPlanningEntityId = planningRecordStepActive.value ? planningEntityId.value.trim() : '';
  const localPlanningEntityType = planningRecordStepActive.value && localPlanningEntityId ? planningFamily.value : '';
  const resolvedPlanningEntityId = localPlanningEntityId || props.wizardState.planning_entity_id || routePlanningEntityId;
  const resolvedPlanningEntityType =
    localPlanningEntityType ||
    (props.wizardState.planning_entity_type as PlanningEntityType) ||
    (routePlanningEntityType as PlanningEntityType);
  if (!resolvedPlanningEntityId || !resolvedPlanningEntityType) {
    return null;
  }
  return {
    planningEntityId: resolvedPlanningEntityId,
    planningEntityType: resolvedPlanningEntityType,
  };
});
const currentPlanningModeCode = computed(() => {
  if (planningRecordStepActive.value && planningEntityId.value.trim()) {
    return planningModeCode.value;
  }
  return (
    props.wizardState.planning_mode_code ||
    mapPlanningEntityTypeToModeCode(currentPlanningEntityScope.value?.planningEntityType) ||
    ''
  );
});
const hasPlanningContext = computed(
  () =>
    Boolean(
      currentPlanningEntityScope.value?.planningEntityId &&
        currentPlanningEntityScope.value?.planningEntityType &&
        currentPlanningModeCode.value,
    ),
);

function setFeedback(tone: 'error' | 'neutral' | 'success', message = '') {
  stepFeedback.tone = tone;
  stepFeedback.message = message;
}

function isOrderDetailsDraftPersistence(value: unknown): value is OrderDetailsDraftPersistence {
  return Boolean(value && typeof value === 'object' && 'form' in (value as Record<string, unknown>));
}

function normalizeUuid(value: string | null | undefined) {
  const normalized = typeof value === 'string' ? value.trim() : '';
  return normalized || null;
}

function withDraftSyncPaused(callback: () => void) {
  draftSyncPaused.value = true;
  try {
    callback();
  } finally {
    draftSyncPaused.value = false;
  }
}

function withPlanningContextHydrationPaused<T>(callback: () => T) {
  planningContextHydrationPaused.value = true;
  try {
    return callback();
  } finally {
    planningContextHydrationPaused.value = false;
  }
}

function buildDraftContext(): CustomerNewPlanWizardDraftContext | null {
  if (!props.tenantId || !props.customer.id) {
    return null;
  }
  const planningEntityId = currentPlanningEntityScope.value?.planningEntityId ?? '';
  const planningEntityType = currentPlanningEntityScope.value?.planningEntityType ?? '';
  return {
    customerId: props.customer.id,
    planningEntityId,
    planningEntityType,
    tenantId: props.tenantId,
  };
}

function buildStepExternalContextKey() {
  return JSON.stringify({
    currentStepId: props.currentStepId,
    customerId: props.customer.id,
    orderId: props.wizardState.order_id,
    planningEntityId: props.wizardState.planning_entity_id,
    planningEntityType: props.wizardState.planning_entity_type,
    planningModeCode: props.wizardState.planning_mode_code,
    planningRecordId: props.wizardState.planning_record_id,
    shiftPlanId: props.wizardState.shift_plan_id,
    seriesId: props.wizardState.series_id,
    tenantId: props.tenantId,
  });
}

function loadStepDraft<T>(stepId: CustomerNewPlanWizardStepId) {
  const context = buildDraftContext();
  if (!context) {
    return null as null | T;
  }
  return loadWizardDraft<T>(context, stepId);
}

function loadExistingOrderEditDraft<T>(orderId: string) {
  const context = buildDraftContext();
  if (!context || !orderId) {
    return null as null | T;
  }
  return loadOrderDetailsEditDraft<T>(context, orderId);
}

function saveStepDraft<T>(stepId: CustomerNewPlanWizardStepId, payload: null | T | undefined) {
  const context = buildDraftContext();
  if (!context) {
    return;
  }
  saveWizardDraft(context, stepId, payload);
}

function saveExistingOrderEditDraft<T>(orderId: string, payload: null | T | undefined) {
  const context = buildDraftContext();
  if (!context || !orderId) {
    return;
  }
  saveOrderDetailsEditDraft(context, orderId, payload);
}

function clearStepDraft(stepId: CustomerNewPlanWizardStepId) {
  const context = buildDraftContext();
  if (!context) {
    return;
  }
  clearWizardDraft(context, stepId);
}

function clearExistingOrderEditDraftState(orderId: string) {
  const context = buildDraftContext();
  if (!context || !orderId) {
    return;
  }
  clearOrderDetailsEditDraft(context, orderId);
}

function restoreDraftMessage(messageKey = 'sicherplan.customerPlansWizard.draftRestored') {
  draftRestoreMessage.value = $t(messageKey);
}

function clearDraftRestoreMessage() {
  draftRestoreMessage.value = '';
}

function buildPlanningContextPatch() {
  if (!planningEntityId.value) {
    return {
      planning_entity_id: '',
      planning_entity_type: '',
      planning_mode_code: '',
    } as CustomerNewPlanWizardStatePatch;
  }
  return {
    planning_entity_id: planningEntityId.value,
    planning_entity_type: planningFamily.value,
    planning_mode_code: planningModeCode.value,
  } as CustomerNewPlanWizardStatePatch;
}

function buildOrderDetailsDraftPersistence(): OrderDetailsDraftPersistence | null {
  if (orderSelectionMode.value !== 'create_new') {
    return null;
  }
  return {
    form: {
      ...orderDraft,
      customer_id: props.customer.id,
    },
    mode: orderSelectionMode.value,
    selected_order_id: selectedExistingOrderId.value || '',
  };
}

function buildPlanningRecordOverviewDraftPersistence(): PlanningRecordOverviewDraftPersistence | null {
  if (!hasPlanningRecordDraftContent()) {
    return null;
  }
  return {
    form: { ...planningRecordDraft },
    order_id: props.wizardState.order_id,
    planning_context: hasPlanningContext.value
      ? {
          planning_entity_id: currentPlanningEntityScope.value?.planningEntityId || planningEntityId.value,
          planning_entity_type:
            currentPlanningEntityScope.value?.planningEntityType || planningFamily.value,
          planning_mode_code: currentPlanningModeCode.value,
        }
      : undefined,
    selection_mode: planningSelectionMode.value,
  };
}

function buildOrderDetailsEditDraftPersistence(): null | OrderDetailsEditDraftPersistence {
  if (!existingOrderEditActive.value || !editingExistingOrderId.value || !hasExistingOrderEditDirtyState()) {
    return null;
  }
  return {
    form: {
      ...orderDraft,
      customer_id: props.customer.id,
    },
  };
}

function buildStepLoadGuard() {
  const refreshSequence = ++stepRefreshSequence;
  const refreshContextKey = stepRefreshContextKey.value;
  return () => refreshSequence === stepRefreshSequence && refreshContextKey === stepRefreshContextKey.value;
}

function hasOrderDraftContent() {
  return Boolean(
    orderDraft.order_no ||
      orderDraft.title ||
      orderDraft.requirement_type_id ||
      orderDraft.service_category_code ||
      orderDraft.service_from ||
      orderDraft.service_to ||
      orderDraft.notes ||
      orderDraft.security_concept_text ||
      orderDraft.patrol_route_id,
  );
}

function matchesSelectedOrderDraft() {
  return Boolean(
    selectedOrder.value &&
      existingOrderEditActive.value &&
      orderDraft.customer_id === selectedOrder.value.customer_id &&
      orderDraft.notes === (selectedOrder.value.notes ?? '') &&
      orderDraft.order_no === selectedOrder.value.order_no &&
      orderDraft.patrol_route_id === (selectedOrder.value.patrol_route_id ?? '') &&
      orderDraft.release_state === selectedOrder.value.release_state &&
      orderDraft.requirement_type_id === selectedOrder.value.requirement_type_id &&
      orderDraft.security_concept_text === (selectedOrder.value.security_concept_text ?? '') &&
      orderDraft.service_category_code === selectedOrder.value.service_category_code &&
      orderDraft.service_from === selectedOrder.value.service_from &&
      orderDraft.service_to === selectedOrder.value.service_to &&
      orderDraft.title === selectedOrder.value.title,
  );
}

function hasExistingOrderEditDirtyState() {
  return Boolean(existingOrderEditActive.value && !matchesSelectedOrderDraft());
}

function hasEquipmentLineDraftContent() {
  return Boolean(
    equipmentLineDraft.equipment_item_id || equipmentLineDraft.notes || equipmentLineDraft.required_qty !== 1,
  );
}

function hasRequirementLineDraftContent() {
  return Boolean(
    requirementLineDraft.requirement_type_id ||
      requirementLineDraft.function_type_id ||
      requirementLineDraft.qualification_type_id ||
      requirementLineDraft.notes ||
      requirementLineDraft.min_qty !== 0 ||
      requirementLineDraft.target_qty !== 1,
  );
}

function hasEquipmentLineDraftInput() {
  return hasEquipmentLineDraftContent();
}

function hasRequirementLineDraftInput() {
  return hasRequirementLineDraftContent();
}

function hasOrderAttachmentDraftContent() {
  return Boolean(
    orderAttachmentDraft.title ||
      orderAttachmentDraft.label ||
      orderAttachmentDraft.file_name ||
      orderAttachmentDraft.content_type ||
      orderAttachmentDraft.content_base64 ||
      orderAttachmentLink.document_id ||
      orderAttachmentLink.label,
  );
}

function hasOrderDocumentUploadDraftInput() {
  return Boolean(
    orderAttachmentDraft.title ||
      orderAttachmentDraft.label ||
      orderAttachmentDraft.file_name ||
      orderAttachmentDraft.content_type ||
      orderAttachmentDraft.content_base64,
  );
}

function hasCompleteOrderDocumentUploadDraft() {
  return Boolean(
    orderAttachmentDraft.content_base64 && orderAttachmentDraft.file_name && orderAttachmentDraft.title.trim(),
  );
}

function hasOrderDocumentLinkDraftInput() {
  return Boolean(orderAttachmentLink.document_id.trim() || orderAttachmentLink.label.trim());
}

function hasCompleteOrderDocumentLinkDraft() {
  return Boolean(orderAttachmentLink.document_id.trim());
}

function hasAnyOrderDocumentDraftInput() {
  return hasOrderDocumentUploadDraftInput() || hasOrderDocumentLinkDraftInput();
}

function hasOrderAttachmentPartialDraft() {
  return (
    (hasOrderDocumentUploadDraftInput() && !hasCompleteOrderDocumentUploadDraft()) ||
    (hasOrderDocumentLinkDraftInput() && !hasCompleteOrderDocumentLinkDraft()) ||
    (hasOrderDocumentUploadDraftInput() && hasOrderDocumentLinkDraftInput())
  );
}

function hasPlanningRecordDraftContent() {
  return Boolean(
    planningRecordDraft.name ||
      planningRecordDraft.notes ||
      planningRecordDraft.parent_planning_record_id ||
      planningRecordDraft.dispatcher_user_id ||
      planningRecordDraft.planning_from ||
      planningRecordDraft.planning_to ||
      planningRecordDraft.event_detail_event_venue_id ||
      planningRecordDraft.event_detail_setup_note ||
      planningRecordDraft.site_detail_site_id ||
      planningRecordDraft.site_detail_watchbook_scope_note ||
      planningRecordDraft.trade_fair_detail_trade_fair_id ||
      planningRecordDraft.trade_fair_detail_trade_fair_zone_id ||
      planningRecordDraft.trade_fair_detail_stand_note ||
      planningRecordDraft.patrol_detail_patrol_route_id ||
      planningRecordDraft.patrol_detail_execution_note ||
      planningRecordDraft.status !== 'active',
  );
}

function hasPlanningRecordAttachmentDraftContent() {
  return Boolean(
    planningRecordAttachmentDraft.title ||
      planningRecordAttachmentDraft.label ||
      planningRecordAttachmentDraft.file_name ||
      planningRecordAttachmentDraft.content_type ||
      planningRecordAttachmentDraft.content_base64 ||
      planningRecordAttachmentLink.document_id ||
      planningRecordAttachmentLink.label,
  );
}

function hasPlanningRecordAttachmentSubmission() {
  return Boolean(planningRecordAttachmentDraft.content_base64 || planningRecordAttachmentLink.document_id.trim());
}

function hasPlanningRecordAttachmentPartialDraft() {
  return hasPlanningRecordAttachmentDraftContent() && !hasPlanningRecordAttachmentSubmission();
}

function buildShiftPlanDefaultDraft() {
  return {
    name: selectedPlanningRecord.value
      ? `${selectedPlanningRecord.value.name} / ${$t('sicherplan.customerPlansWizard.forms.shiftPlanDefaultNameSuffix')}`
      : '',
    planning_from: selectedPlanningRecord.value?.planning_from || '',
    planning_record_id: props.wizardState.planning_record_id || '',
    planning_to: selectedPlanningRecord.value?.planning_to || '',
    remarks: '',
    workforce_scope_code: 'internal',
  };
}

function buildSelectedShiftPlanBaseline(plan: ShiftPlanRead) {
  return {
    name: plan.name,
    planning_from: plan.planning_from,
    planning_record_id: plan.planning_record_id,
    planning_to: plan.planning_to,
    remarks: plan.remarks ?? '',
    workforce_scope_code: plan.workforce_scope_code,
  };
}

function hasShiftPlanDraftContent() {
  if (selectedShiftPlan.value) {
    const baseline = buildSelectedShiftPlanBaseline(selectedShiftPlan.value);
    return Boolean(
      shiftPlanDraft.name !== baseline.name ||
        shiftPlanDraft.planning_from !== baseline.planning_from ||
        shiftPlanDraft.planning_record_id !== baseline.planning_record_id ||
        shiftPlanDraft.planning_to !== baseline.planning_to ||
        shiftPlanDraft.remarks !== baseline.remarks ||
        shiftPlanDraft.workforce_scope_code !== baseline.workforce_scope_code,
    );
  }
  if (selectedPlanningRecord.value) {
    const defaultDraft = buildShiftPlanDefaultDraft();
    return Boolean(
      shiftPlanDraft.name && shiftPlanDraft.name !== defaultDraft.name ||
        shiftPlanDraft.planning_from && shiftPlanDraft.planning_from !== defaultDraft.planning_from ||
        shiftPlanDraft.planning_record_id && shiftPlanDraft.planning_record_id !== defaultDraft.planning_record_id ||
        shiftPlanDraft.planning_to && shiftPlanDraft.planning_to !== defaultDraft.planning_to ||
        shiftPlanDraft.remarks ||
        shiftPlanDraft.workforce_scope_code !== defaultDraft.workforce_scope_code,
    );
  }
  return Boolean(
    shiftPlanDraft.name ||
      shiftPlanDraft.planning_from ||
      shiftPlanDraft.planning_to ||
      shiftPlanDraft.planning_record_id ||
      shiftPlanDraft.remarks ||
      shiftPlanDraft.workforce_scope_code !== 'internal',
  );
}

function hasSeriesDraftContent() {
  return Boolean(
    seriesDraft.label ||
      seriesDraft.shift_template_id ||
      seriesDraft.date_from ||
      seriesDraft.date_to ||
      seriesDraft.interval_count !== 1 ||
      seriesDraft.default_break_minutes !== 30 ||
      seriesDraft.meeting_point ||
      seriesDraft.location_text ||
      seriesDraft.notes ||
      seriesDraft.shift_type_code ||
      seriesDraft.customer_visible_flag ||
      seriesDraft.subcontractor_visible_flag ||
      seriesDraft.stealth_mode_flag ||
      seriesDraft.release_state !== 'draft' ||
      seriesDraft.timezone !== 'Europe/Berlin' ||
      seriesDraft.recurrence_code !== 'daily' ||
      seriesDraft.weekday_mask !== '1111100' ||
      exceptionDraft.exception_date ||
      exceptionDraft.action_code !== 'skip' ||
      exceptionDraft.override_local_start_time ||
      exceptionDraft.override_local_end_time ||
      exceptionDraft.override_break_minutes ||
      exceptionDraft.override_shift_type_code ||
      exceptionDraft.override_meeting_point ||
      exceptionDraft.override_location_text ||
      exceptionDraft.notes ||
      exceptionDraft.customer_visible_flag !== null ||
      exceptionDraft.subcontractor_visible_flag !== null ||
      exceptionDraft.stealth_mode_flag !== null,
  );
}

function buildAttachmentDraftPersistence(
  attachmentDraft: typeof orderAttachmentDraft | typeof planningRecordAttachmentDraft,
): AttachmentDraftPersistence {
  return {
    content_type: attachmentDraft.content_type,
    file_name: attachmentDraft.file_name,
    file_needs_reselect: Boolean(attachmentDraft.content_base64),
    label: attachmentDraft.label,
    title: attachmentDraft.title,
  };
}

function applyOrderDraftPersistence(payload: Partial<typeof orderDraft>) {
  withDraftSyncPaused(() => {
    Object.assign(orderDraft, {
      ...payload,
      customer_id: props.customer.id,
    });
  });
}

function resetOrderSelection() {
  existingOrderEditFormOpen.value = false;
  selectedOrder.value = null;
  editingExistingOrderId.value = '';
  selectedExistingOrderId.value = '';
}

function closeExistingOrderEdit(options?: { clearDraft?: boolean; preserveSelection?: boolean }) {
  const editingOrderId = editingExistingOrderId.value;
  existingOrderEditFormOpen.value = false;
  selectedOrder.value = null;
  editingExistingOrderId.value = '';
  if (options?.preserveSelection === false) {
    selectedExistingOrderId.value = '';
  }
  withDraftSyncPaused(() => {
    resetOrderDraft();
  });
  if (options?.clearDraft !== false && editingOrderId) {
    clearExistingOrderEditDraftState(editingOrderId);
  }
}

function setOrderSelectionMode(mode: OrderSelectionMode) {
  if (orderSelectionMode.value === mode) {
    return;
  }
  const previousEditingOrderId = editingExistingOrderId.value;
  orderSelectionMode.value = mode;
  setFeedback('neutral', '');
  if (mode === 'create_new') {
    const persistedCreateDraft = loadStepDraft<OrderDetailsDraftPersistence | Partial<typeof orderDraft>>('order-details');
    clearDraftRestoreMessage();
    resetOrderSelection();
    if (previousEditingOrderId) {
      clearExistingOrderEditDraftState(previousEditingOrderId);
    }
    if (isOrderDetailsDraftPersistence(persistedCreateDraft) && persistedCreateDraft.mode === 'create_new') {
      applyOrderDraftPersistence(persistedCreateDraft.form);
      if (hasOrderDraftContent()) {
        restoreDraftMessage();
      }
    } else {
      withDraftSyncPaused(() => {
        resetOrderDraft();
      });
    }
    saveStepDraft('order-details', buildOrderDetailsDraftPersistence());
    emit('saved-context', { order_id: '' });
    return;
  }
  clearDraftRestoreMessage();
  resetOrderSelection();
  if (previousEditingOrderId) {
    clearExistingOrderEditDraftState(previousEditingOrderId);
  }
  emit('saved-context', { order_id: '' });
  emit('step-completion', 'order-details', false);
  emit('step-ui-state', 'order-details', { dirty: false, error: '' });
  if (!customerOrderRows.value.length) {
    withDraftSyncPaused(() => {
      resetOrderDraft();
    });
  }
}

function applyEquipmentLineDraftPersistence(
  payload: Partial<typeof equipmentLineDraft> & { selected_equipment_line_id?: string },
) {
  withDraftSyncPaused(() => {
    selectedEquipmentLineId.value = payload.selected_equipment_line_id || '';
    Object.assign(equipmentLineDraft, payload);
  });
}

function applyRequirementLineDraftPersistence(
  payload: Partial<typeof requirementLineDraft> & { selected_requirement_line_id?: string },
) {
  withDraftSyncPaused(() => {
    selectedRequirementLineId.value = payload.selected_requirement_line_id || '';
    Object.assign(requirementLineDraft, payload);
  });
}

function applyOrderDocumentsDraftPersistence(payload: Partial<OrderDocumentsDraftPersistence>) {
  withDraftSyncPaused(() => {
    Object.assign(orderAttachmentDraft, {
      content_base64: '',
      content_type: payload.attachment?.content_type || '',
      file_name: payload.attachment?.file_name || '',
      label: payload.attachment?.label || '',
      title: payload.attachment?.title || '',
    });
    Object.assign(orderAttachmentLink, {
      document_id: payload.link?.document_id || '',
      label: payload.link?.label || '',
    });
  });
  if (payload.attachment?.file_needs_reselect) {
    restoreDraftMessage('sicherplan.customerPlansWizard.draftRestoredFileReset');
  }
}

function applyPlanningRecordDraftPersistence(payload: Partial<typeof planningRecordDraft>) {
  withDraftSyncPaused(() => {
    Object.assign(planningRecordDraft, payload);
  });
}

function applyPlanningRecordOverviewDraftPersistence(payload: PlanningRecordOverviewDraftPersistence) {
  withPlanningContextHydrationPaused(() =>
    withDraftSyncPaused(() => {
      planningSelectionMode.value = payload.selection_mode || 'use_existing';
      if (payload.planning_context?.planning_entity_type) {
        planningFamily.value = payload.planning_context.planning_entity_type;
      }
      planningEntityId.value = payload.planning_context?.planning_entity_id || '';
      planningRecordDraft.planning_mode_code =
        payload.planning_context?.planning_mode_code || planningModeCode.value;
      Object.assign(planningRecordDraft, payload.form || {});
    }),
  );
}

function hasContentfulPlanningRecordDraftPayload(payload: null | PlanningRecordOverviewDraftPersistence | undefined) {
  if (!payload) {
    return false;
  }
  const form = payload.form || {};
  return Boolean(
    form.name ||
      form.notes ||
      form.parent_planning_record_id ||
      form.dispatcher_user_id ||
      form.planning_from ||
      form.planning_to ||
      form.event_detail_event_venue_id ||
      form.event_detail_setup_note ||
      form.site_detail_site_id ||
      form.site_detail_watchbook_scope_note ||
      form.trade_fair_detail_trade_fair_id ||
      form.trade_fair_detail_trade_fair_zone_id ||
      form.trade_fair_detail_stand_note ||
      form.patrol_detail_patrol_route_id ||
      form.patrol_detail_execution_note ||
      (typeof form.status === 'string' && form.status !== 'active'),
  );
}

function applyPlanningRecordDocumentsDraftPersistence(payload: Partial<OrderDocumentsDraftPersistence>) {
  withDraftSyncPaused(() => {
    Object.assign(planningRecordAttachmentDraft, {
      content_base64: '',
      content_type: payload.attachment?.content_type || '',
      file_name: payload.attachment?.file_name || '',
      label: payload.attachment?.label || '',
      title: payload.attachment?.title || '',
    });
    Object.assign(planningRecordAttachmentLink, {
      document_id: payload.link?.document_id || '',
      label: payload.link?.label || '',
    });
  });
  if (payload.attachment?.file_needs_reselect) {
    restoreDraftMessage('sicherplan.customerPlansWizard.draftRestoredFileReset');
  }
}

function normalizeShiftPlanDraftPersistence(
  payload: ShiftPlanDraftPersistence | Partial<typeof shiftPlanDraft> | null | undefined,
): ShiftPlanDraftPersistence | null {
  if (!payload || typeof payload !== 'object') {
    return null;
  }
  if ('draft' in payload && payload.draft && typeof payload.draft === 'object') {
    return {
      draft: payload.draft,
      selected_shift_plan_id: typeof payload.selected_shift_plan_id === 'string' ? payload.selected_shift_plan_id : '',
    };
  }
  return {
    draft: payload as Partial<typeof shiftPlanDraft>,
    selected_shift_plan_id: '',
  };
}

function applyShiftPlanDraftPersistence(payload: Partial<typeof shiftPlanDraft>) {
  withDraftSyncPaused(() => {
    Object.assign(shiftPlanDraft, {
      name: payload.name ?? shiftPlanDraft.name,
      planning_from: payload.planning_from ?? shiftPlanDraft.planning_from,
      planning_record_id: payload.planning_record_id ?? shiftPlanDraft.planning_record_id,
      planning_to: payload.planning_to ?? shiftPlanDraft.planning_to,
      remarks: payload.remarks ?? shiftPlanDraft.remarks,
      workforce_scope_code: payload.workforce_scope_code ?? shiftPlanDraft.workforce_scope_code,
    });
  });
}

function applySeriesDraftPersistence(payload: Partial<SeriesExceptionsDraftPersistence>) {
  withDraftSyncPaused(() => {
    Object.assign(seriesDraft, payload.series || {});
    selectedExceptionId.value = '';
    Object.assign(exceptionDraft, payload.exception || {});
  });
}

function persistOrderDraft() {
  if (existingOrderEditActive.value) {
    saveExistingOrderEditDraft(editingExistingOrderId.value, buildOrderDetailsEditDraftPersistence());
    return;
  }
  if (orderSelectionMode.value === 'use_existing') {
    return;
  }
  saveStepDraft('order-details', buildOrderDetailsDraftPersistence());
}

function persistEquipmentLineDraft() {
  saveStepDraft(
    'equipment-lines',
    hasEquipmentLineDraftContent()
      ? {
          ...equipmentLineDraft,
          selected_equipment_line_id: selectedEquipmentLineId.value,
        }
      : null,
  );
}

function persistRequirementLineDraft() {
  saveStepDraft(
    'requirement-lines',
    hasRequirementLineDraftContent()
      ? {
          ...requirementLineDraft,
          selected_requirement_line_id: selectedRequirementLineId.value,
        }
      : null,
  );
}

function persistOrderDocumentsDraft() {
  saveStepDraft(
    'order-documents',
    hasOrderAttachmentDraftContent()
      ? {
          attachment: buildAttachmentDraftPersistence(orderAttachmentDraft),
          link: {
            document_id: orderAttachmentLink.document_id,
            label: orderAttachmentLink.label,
          },
        }
      : null,
  );
}

function persistPlanningRecordDraft() {
  saveStepDraft(
    'planning-record-overview',
    buildPlanningRecordOverviewDraftPersistence(),
  );
}

function persistPlanningRecordDocumentsDraft() {
  saveStepDraft(
    'planning-record-documents',
    hasPlanningRecordAttachmentDraftContent()
      ? {
          attachment: buildAttachmentDraftPersistence(planningRecordAttachmentDraft),
          link: {
            document_id: planningRecordAttachmentLink.document_id,
            label: planningRecordAttachmentLink.label,
          },
        }
      : null,
  );
}

function persistShiftPlanDraft() {
  saveStepDraft(
    'shift-plan',
    hasShiftPlanDraftContent()
      ? {
          draft: { ...shiftPlanDraft },
          selected_shift_plan_id: selectedShiftPlan.value?.id || '',
        }
      : null,
  );
}

function persistSeriesDraft() {
  saveStepDraft(
    'series-exceptions',
    hasSeriesDraftContent()
      ? {
          exception: { ...exceptionDraft },
          series: { ...seriesDraft },
        }
      : null,
  );
}

function persistAllUnsavedDrafts() {
  if (draftSyncPaused.value) {
    return;
  }
  persistOrderDraft();
  persistEquipmentLineDraft();
  persistRequirementLineDraft();
  persistOrderDocumentsDraft();
  persistPlanningRecordDraft();
  persistPlanningRecordDocumentsDraft();
  persistShiftPlanDraft();
  persistSeriesDraft();
}

function handleBeforeUnload() {
  if (props.persistDraftsOnUnmount === false) {
    return;
  }
  persistAllUnsavedDrafts();
}

function resetPlanningCreateModal() {
  Object.assign(planningCreateModal, {
    address_id: '',
    end_date: '',
    fair_no: '',
    latitude: '',
    longitude: '',
    meeting_address_id: '',
    name: '',
    notes: '',
    open: false,
    route_no: '',
    saving: false,
    site_id: '',
    site_no: '',
    start_date: '',
    start_point_text: '',
    status: 'active',
    timezone: 'Europe/Berlin',
    travel_policy_code: '',
    venue_id: '',
    venue_no: '',
    watchbook_enabled: false,
    end_point_text: '',
  });
  closePlanningAddressCreateModal();
  planningLocationPickerOpen.value = false;
}

function resetPlanningAddressCreateModal() {
  Object.assign(planningAddressCreateModal, {
    city: '',
    country_code: 'DE',
    error: '',
    open: false,
    postal_code: '',
    saving: false,
    state: '',
    street_line_1: '',
    street_line_2: '',
  });
}

function buildPlanningCreateAddressOption(address: CustomerAvailableAddressRead): CustomerAddressRead {
  return {
    address: {
      city: address.city,
      country_code: address.country_code,
      id: address.id,
      postal_code: address.postal_code,
      state: address.state ?? null,
      street_line_1: address.street_line_1,
      street_line_2: address.street_line_2 ?? null,
    },
    address_id: address.id,
    address_type: 'service',
    archived_at: null,
    customer_id: props.customer.id,
    id: `staged-${address.id}`,
    is_default: false,
    label: null,
    status: 'active',
    tenant_id: props.tenantId,
    version_no: 1,
  };
}

function mergePlanningCreateAddressOptions(addressLinks = planningCreateAddressOptions.value, stagedAddresses = planningCreateStagedAddresses.value) {
  const merged = new Map<string, CustomerAddressRead>();
  for (const entry of addressLinks) {
    if (entry?.address_id) {
      merged.set(entry.address_id, entry);
    }
  }
  for (const address of stagedAddresses) {
    merged.set(address.id, buildPlanningCreateAddressOption(address));
  }
  return [...merged.values()];
}

function syncPlanningCreateAddressSelections() {
  const validAddressIds = new Set(mergePlanningCreateAddressOptions().map((entry) => entry.address_id));
  if (planningCreateModal.address_id && !validAddressIds.has(planningCreateModal.address_id)) {
    planningCreateModal.address_id = '';
  }
  if (planningCreateModal.meeting_address_id && !validAddressIds.has(planningCreateModal.meeting_address_id)) {
    planningCreateModal.meeting_address_id = '';
  }
}

function openPlanningAddressCreateModal() {
  if (!planningCreateHasAddressField.value || planningCreateAddressLookupLoading.value || !props.customer.id) {
    return;
  }
  resetPlanningAddressCreateModal();
  planningAddressCreateModal.open = true;
}

function closePlanningAddressCreateModal() {
  resetPlanningAddressCreateModal();
}

function normalizePlanningAddressCreatePayload() {
  return {
    city: planningAddressCreateModal.city.trim(),
    country_code: planningAddressCreateModal.country_code.trim().toUpperCase(),
    postal_code: planningAddressCreateModal.postal_code.trim(),
    state: planningAddressCreateModal.state.trim() || null,
    street_line_1: planningAddressCreateModal.street_line_1.trim(),
    street_line_2: planningAddressCreateModal.street_line_2.trim() || null,
  };
}

function openPlanningLocationPicker() {
  if (!planningCreateSupportsLocationPicker.value) {
    return;
  }
  const fallback = {
    label: $t('sicherplan.customerPlansWizard.mapPicker.startDefault'),
    lat: 51.662973,
    lng: 8.174013,
    zoom: 11,
  };
  const resolvedCenter = resolveInitialMapCenter({
    currentLatitude: planningCreateModal.latitude,
    currentLongitude: planningCreateModal.longitude,
    fallback,
  });
  planningLocationPickerStartPoint.value = {
    label:
      resolvedCenter.source === 'existing-record'
        ? $t('sicherplan.customerPlansWizard.mapPicker.startExisting')
        : fallback.label,
    lat: resolvedCenter.lat,
    lng: resolvedCenter.lng,
    zoom: resolvedCenter.source === 'existing-record' ? 14 : fallback.zoom,
  };
  planningLocationPickerOpen.value = true;
}

function applyPlanningLocationSelection(payload: { latitude: string; longitude: string }) {
  planningCreateModal.latitude = payload.latitude;
  planningCreateModal.longitude = payload.longitude;
}

function resetRequirementModal() {
  Object.assign(requirementModal, {
    code: '',
    default_planning_mode_code: planningModeCode.value,
    label: '',
    notes: '',
    open: false,
    saving: false,
  });
}

function resetEquipmentModal() {
  Object.assign(equipmentModal, {
    code: '',
    label: '',
    notes: '',
    open: false,
    saving: false,
    unit_of_measure_code: 'piece',
  });
}

function resetOrderDraft() {
  Object.assign(orderDraft, {
    customer_id: props.customer.id,
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
  });
}

function resetEquipmentLineDraft() {
  selectedEquipmentLineId.value = '';
  Object.assign(equipmentLineDraft, {
    equipment_item_id: '',
    notes: '',
    required_qty: 1,
  });
}

function resetRequirementLineDraft() {
  selectedRequirementLineId.value = '';
  Object.assign(requirementLineDraft, {
    function_type_id: '',
    min_qty: 0,
    notes: '',
    qualification_type_id: '',
    requirement_type_id: '',
    target_qty: 1,
  });
}

function resetOrderAttachmentDraft() {
  Object.assign(orderAttachmentDraft, {
    content_base64: '',
    content_type: '',
    file_name: '',
    label: '',
    title: '',
  });
  Object.assign(orderAttachmentLink, {
    document_id: '',
    label: '',
  });
}

function resetPlanningRecordDraft() {
  Object.assign(planningRecordDraft, {
    dispatcher_user_id: '',
    event_detail_event_venue_id: '',
    event_detail_setup_note: '',
    name: '',
    notes: '',
    parent_planning_record_id: '',
    patrol_detail_execution_note: '',
    patrol_detail_patrol_route_id: '',
    planning_from: '',
    planning_mode_code: props.wizardState.planning_mode_code || planningModeCode.value,
    planning_to: '',
    site_detail_site_id: '',
    site_detail_watchbook_scope_note: '',
    status: 'active',
    trade_fair_detail_stand_note: '',
    trade_fair_detail_trade_fair_id: '',
    trade_fair_detail_trade_fair_zone_id: '',
  });
}

function resetPlanningRecordAttachmentDraft() {
  Object.assign(planningRecordAttachmentDraft, {
    content_base64: '',
    content_type: '',
    file_name: '',
    label: '',
    title: '',
  });
  Object.assign(planningRecordAttachmentLink, {
    document_id: '',
    label: '',
  });
}

function resetShiftPlanDraft() {
  Object.assign(shiftPlanDraft, buildShiftPlanDefaultDraft());
}

function resetSeriesDraft() {
  Object.assign(seriesDraft, {
    customer_visible_flag: false,
    date_from: '',
    date_to: '',
    default_break_minutes: 30,
    interval_count: 1,
    label: '',
    location_text: '',
    meeting_point: '',
    notes: '',
    recurrence_code: 'daily',
    release_state: 'draft',
    shift_template_id: '',
    shift_type_code: '',
    stealth_mode_flag: false,
    subcontractor_visible_flag: false,
    timezone: 'Europe/Berlin',
    weekday_mask: '1111100',
  });
}

function resetExceptionDraft() {
  selectedExceptionId.value = '';
  Object.assign(exceptionDraft, {
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
  });
}

function resetTemplateModal() {
  Object.assign(templateModal, {
    code: '',
    default_break_minutes: 30,
    label: '',
    local_end_time: '16:00',
    local_start_time: '08:00',
    location_text: '',
    meeting_point: '',
    notes: '',
    open: false,
    saving: false,
    shift_type_code: shiftTypeOptions.value[0]?.code || '',
  });
}

function syncOrderDraft(order: CustomerOrderRead) {
  selectedOrder.value = order;
  withDraftSyncPaused(() => {
    Object.assign(orderDraft, {
      customer_id: order.customer_id,
      notes: order.notes ?? '',
      order_no: order.order_no,
      patrol_route_id: order.patrol_route_id ?? '',
      release_state: order.release_state,
      requirement_type_id: order.requirement_type_id,
      security_concept_text: order.security_concept_text ?? '',
      service_category_code: order.service_category_code,
      service_from: order.service_from,
      service_to: order.service_to,
      title: order.title,
    });
  });
}

function syncPlanningRecordDraft(record: PlanningRecordRead) {
  selectedPlanningRecord.value = record;
  withDraftSyncPaused(() => {
    Object.assign(planningRecordDraft, {
      dispatcher_user_id: record.dispatcher_user_id ?? '',
      event_detail_event_venue_id: record.event_detail?.event_venue_id ?? '',
      event_detail_setup_note: record.event_detail?.setup_note ?? '',
      name: record.name,
      notes: record.notes ?? '',
      parent_planning_record_id: record.parent_planning_record_id ?? '',
      patrol_detail_execution_note: record.patrol_detail?.execution_note ?? '',
      patrol_detail_patrol_route_id: record.patrol_detail?.patrol_route_id ?? '',
      planning_from: record.planning_from,
      planning_mode_code: record.planning_mode_code,
      planning_to: record.planning_to,
      site_detail_site_id: record.site_detail?.site_id ?? '',
      site_detail_watchbook_scope_note: record.site_detail?.watchbook_scope_note ?? '',
      status: record.status,
      trade_fair_detail_stand_note: record.trade_fair_detail?.stand_note ?? '',
      trade_fair_detail_trade_fair_id: record.trade_fair_detail?.trade_fair_id ?? '',
      trade_fair_detail_trade_fair_zone_id: record.trade_fair_detail?.trade_fair_zone_id ?? '',
    });
  });
}

function syncShiftPlanDraft(plan: ShiftPlanRead) {
  selectedShiftPlan.value = plan;
  withDraftSyncPaused(() => {
    Object.assign(shiftPlanDraft, {
      name: plan.name,
      planning_from: plan.planning_from,
      planning_record_id: plan.planning_record_id,
      planning_to: plan.planning_to,
      remarks: plan.remarks ?? '',
      workforce_scope_code: plan.workforce_scope_code,
    });
  });
}

function syncSeriesDraft(series: ShiftSeriesRead) {
  selectedSeries.value = series;
  withDraftSyncPaused(() => {
    Object.assign(seriesDraft, {
      customer_visible_flag: series.customer_visible_flag,
      date_from: series.date_from,
      date_to: series.date_to,
      default_break_minutes: series.default_break_minutes ?? 30,
      interval_count: series.interval_count,
      label: series.label,
      location_text: series.location_text ?? '',
      meeting_point: series.meeting_point ?? '',
      notes: series.notes ?? '',
      recurrence_code: series.recurrence_code,
      release_state: series.release_state,
      shift_template_id: series.shift_template_id,
      shift_type_code: series.shift_type_code ?? '',
      stealth_mode_flag: series.stealth_mode_flag,
      subcontractor_visible_flag: series.subcontractor_visible_flag,
      timezone: series.timezone,
      weekday_mask: series.weekday_mask ?? '1111100',
    });
  });
}

function syncExceptionDraft(row: ShiftSeriesExceptionRead) {
  withDraftSyncPaused(() => {
    selectedExceptionId.value = row.id;
    Object.assign(exceptionDraft, {
      action_code: row.action_code,
      customer_visible_flag: row.customer_visible_flag ?? null,
      exception_date: row.exception_date,
      notes: row.notes ?? '',
      override_break_minutes: row.override_break_minutes == null ? '' : String(row.override_break_minutes),
      override_local_end_time: row.override_local_end_time ?? '',
      override_local_start_time: row.override_local_start_time ?? '',
      override_location_text: row.override_location_text ?? '',
      override_meeting_point: row.override_meeting_point ?? '',
      override_shift_type_code: row.override_shift_type_code ?? '',
      stealth_mode_flag: row.stealth_mode_flag ?? null,
      subcontractor_visible_flag: row.subcontractor_visible_flag ?? null,
    });
  });
}

function syncEquipmentLineDraft(line: OrderEquipmentLineRead) {
  withDraftSyncPaused(() => {
    selectedEquipmentLineId.value = line.id;
    Object.assign(equipmentLineDraft, {
      equipment_item_id: line.equipment_item_id,
      notes: line.notes ?? '',
      required_qty: line.required_qty,
    });
  });
}

function syncRequirementLineDraft(line: OrderRequirementLineRead) {
  withDraftSyncPaused(() => {
    selectedRequirementLineId.value = line.id;
    Object.assign(requirementLineDraft, {
      function_type_id: line.function_type_id ?? '',
      min_qty: line.min_qty,
      notes: line.notes ?? '',
      qualification_type_id: line.qualification_type_id ?? '',
      requirement_type_id: line.requirement_type_id,
      target_qty: line.target_qty,
    });
  });
}

async function fileToBase64(file: File) {
  const bytes = await file.arrayBuffer();
  let binary = '';
  new Uint8Array(bytes).forEach((value) => {
    binary += String.fromCharCode(value);
  });
  return window.btoa(binary);
}

function formatDateTimeLocalValue(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  const hours = String(value.getHours()).padStart(2, '0');
  const minutes = String(value.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function getSupportedTimezones() {
  const supportedValuesOf = (Intl as typeof Intl & {
    supportedValuesOf?: (key: 'timeZone') => string[];
  }).supportedValuesOf;
  if (typeof supportedValuesOf === 'function') {
    return supportedValuesOf('timeZone');
  }
  return ['Europe/Berlin'];
}

function buildCanonicalStaffingWindowFromDates(start: string, end: string) {
  const startDate = new Date(`${start}T00:00:00`);
  const endDate = new Date(`${end}T00:00:00`);
  const dateFrom = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate(), 0, 0, 0, 0);
  const dateTo = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate() + 1, 0, 0, 0, 0);
  return {
    date_from: formatDateTimeLocalValue(dateFrom),
    date_to: formatDateTimeLocalValue(dateTo),
  };
}

function buildCanonicalStaffingWindowFromShiftRange(startsAt: string, endsAt: string) {
  const start = new Date(startsAt);
  const end = new Date(endsAt);
  const dateFrom = new Date(start.getFullYear(), start.getMonth(), start.getDate(), 0, 0, 0, 0);
  const dateTo = new Date(end.getFullYear(), end.getMonth(), end.getDate() + 1, 0, 0, 0, 0);
  return {
    date_from: formatDateTimeLocalValue(dateFrom),
    date_to: formatDateTimeLocalValue(dateTo),
  };
}

function buildPlanningRecordModePayload() {
  const planningMode = planningModeCode.value;
  const activePlanningEntityId = currentPlanningEntityScope.value?.planningEntityId || planningEntityId.value;
  if (planningMode === 'event') {
    return {
      event_detail: {
        event_venue_id: activePlanningEntityId,
        setup_note: planningRecordDraft.event_detail_setup_note || null,
      },
      patrol_detail: null,
      site_detail: null,
      trade_fair_detail: null,
    };
  }
  if (planningMode === 'trade_fair') {
    return {
      event_detail: null,
      patrol_detail: null,
      site_detail: null,
      trade_fair_detail: {
        stand_note: planningRecordDraft.trade_fair_detail_stand_note || null,
        trade_fair_id: activePlanningEntityId,
        trade_fair_zone_id: normalizeUuid(planningRecordDraft.trade_fair_detail_trade_fair_zone_id),
      },
    };
  }
  if (planningMode === 'patrol') {
    return {
      event_detail: null,
      patrol_detail: {
        execution_note: planningRecordDraft.patrol_detail_execution_note || null,
        patrol_route_id: activePlanningEntityId,
      },
      site_detail: null,
      trade_fair_detail: null,
    };
  }
  return {
    event_detail: null,
    patrol_detail: null,
    site_detail: {
      site_id: activePlanningEntityId,
      watchbook_scope_note: planningRecordDraft.site_detail_watchbook_scope_note || null,
    },
    trade_fair_detail: null,
  };
}

function buildPlanningRecordDraftForValidation() {
  const modePayload = buildPlanningRecordModePayload();
  return {
    planning_from: planningRecordDraft.planning_from,
    planning_to: planningRecordDraft.planning_to,
    planning_mode_code: currentPlanningModeCode.value,
    event_detail: modePayload.event_detail,
    site_detail: modePayload.site_detail,
    trade_fair_detail: modePayload.trade_fair_detail,
    patrol_detail: modePayload.patrol_detail,
  };
}

function planningEntitySummaryLabel() {
  const entityId = currentPlanningEntityScope.value?.planningEntityId || planningEntityId.value;
  if (!entityId) {
    return '';
  }
  if (currentPlanningModeCode.value === 'event') {
    return eventVenueSelectOptions.value.find((row) => row.value === entityId)?.label || entityId;
  }
  if (currentPlanningModeCode.value === 'trade_fair') {
    return tradeFairSelectOptions.value.find((row) => row.value === entityId)?.label || entityId;
  }
  if (currentPlanningModeCode.value === 'patrol') {
    return patrolRouteSelectOptions.value.find((row) => row.value === entityId)?.label || entityId;
  }
  return siteSelectOptions.value.find((row) => row.value === entityId)?.label || entityId;
}

function setPlanningSelectionMode(mode: PlanningSelectionMode) {
  if (planningSelectionMode.value === mode) {
    return;
  }
  planningSelectionMode.value = mode;
  setFeedback('neutral', '');
  if (mode === 'create_new') {
    planningEntityId.value = '';
  }
}

function setPlanningFamilySelection(family: PlanningEntityType) {
  if (planningFamily.value === family) {
    return;
  }
  planningFamily.value = family;
  planningEntityId.value = '';
  planningSelectionMode.value = 'use_existing';
  selectedPlanningRecord.value = null;
  planningRecordRows.value = [];
  planningRecordRowsError.value = '';
  withDraftSyncPaused(() => {
    planningRecordDraft.planning_mode_code = planningModeCode.value;
    planningRecordDraft.trade_fair_detail_trade_fair_zone_id = '';
  });
}

async function selectExistingPlanningEntity(entityId: string) {
  if (!entityId) {
    return;
  }
  planningSelectionMode.value = 'use_existing';
  planningEntityId.value = entityId;
  selectedPlanningRecord.value = null;
  planningRecordDraft.planning_mode_code = planningModeCode.value;
  if (planningModeCode.value === 'trade_fair') {
    await refreshTradeFairZoneOptions(entityId);
  } else {
    await refreshTradeFairZoneOptions('');
  }
  await loadExistingPlanningRecordRows();
  setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningEntrySelected'));
  emit('step-ui-state', 'planning-record-overview', { dirty: hasPlanningRecordDraftContent(), error: '' });
}

async function selectExistingPlanningRecordRow(planningRecordId: string) {
  if (!props.tenantId || !props.accessToken || !planningRecordId) {
    return;
  }
  const record = await getPlanningRecord(props.tenantId, planningRecordId, props.accessToken);
  syncPlanningRecordDraft(record);
  setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningRecordSelected'));
  emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
}

function openPlanningCreateModal() {
  setPlanningSelectionMode('create_new');
  planningCreateModal.open = true;
  void loadPlanningCreateReferenceOptions();
}

function onPlanningFamilyChange(event: Event) {
  setPlanningFamilySelection((event.target as HTMLSelectElement).value as PlanningEntityType);
}

function sortShiftRange<T extends { ends_at: string; starts_at: string }>(shifts: T[]) {
  return [...shifts].sort((left, right) => left.starts_at.localeCompare(right.starts_at));
}

async function selectShiftPlanRow(planId: string) {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  const plan = await getShiftPlan(props.tenantId, planId, props.accessToken);
  syncShiftPlanDraft(plan);
  clearStepDraft('shift-plan');
  clearDraftRestoreMessage();
  emit('step-completion', 'shift-plan', true);
  emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
}

function startNewShiftPlan() {
  selectedShiftPlan.value = null;
  clearStepDraft('shift-plan');
  clearDraftRestoreMessage();
  withDraftSyncPaused(() => {
    resetShiftPlanDraft();
  });
  emit('saved-context', { shift_plan_id: '' });
  emit('step-completion', 'shift-plan', false);
  emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
}

async function selectSeriesRow(seriesId: string) {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  const [series, exceptions] = await Promise.all([
    getShiftSeries(props.tenantId, seriesId, props.accessToken),
    listShiftSeriesExceptions(props.tenantId, seriesId, props.accessToken),
  ]);
  syncSeriesDraft(series);
  seriesExceptions.value = exceptions;
}

function setExceptionCustomerVisible(event: Event) {
  exceptionDraft.customer_visible_flag = (event.target as HTMLInputElement)?.checked ?? false;
}

function setExceptionSubcontractorVisible(event: Event) {
  exceptionDraft.subcontractor_visible_flag = (event.target as HTMLInputElement)?.checked ?? false;
}

function setExceptionStealthMode(event: Event) {
  exceptionDraft.stealth_mode_flag = (event.target as HTMLInputElement)?.checked ?? false;
}

async function loadPlanningEntityOptions() {
  if (!props.tenantId || !props.accessToken) {
    planningEntityOptions.value = [];
    return;
  }
  planningEntityLoading.value = true;
  planningEntityError.value = '';
  try {
    planningEntityOptions.value = await listPlanningSetupRecords(
      planningFamily.value,
      props.tenantId,
      props.accessToken,
      { customer_id: props.customer.id },
    );
    if (!planningEntityOptions.value.some((option) => option.id === planningEntityId.value)) {
      planningEntityId.value = '';
    }
  } catch {
    planningEntityOptions.value = [];
    planningEntityError.value = $t('sicherplan.customerPlansWizard.errors.planningEntityLoad');
  } finally {
    planningEntityLoading.value = false;
  }
}

async function loadExistingPlanningRecordRows(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id || !hasPlanningContext.value) {
    planningRecordRows.value = [];
    planningRecordRowsError.value = '';
    planningRecordRowsLoading.value = false;
    return;
  }
  planningRecordRowsLoading.value = true;
  planningRecordRowsError.value = '';
  try {
    const rows = await listOperationalPlanningRecords(props.tenantId, props.accessToken, {
      order_id: props.wizardState.order_id,
      planning_entity_id: currentPlanningEntityScope.value?.planningEntityId,
      planning_entity_type: currentPlanningEntityScope.value?.planningEntityType,
      planning_mode_code: currentPlanningModeCode.value,
    });
    if (!isCurrent()) {
      return;
    }
    planningRecordRows.value = rows;
    if (selectedPlanningRecord.value && !rows.some((row) => row.id === selectedPlanningRecord.value?.id)) {
      selectedPlanningRecord.value = null;
    }
  } catch {
    if (!isCurrent()) {
      return;
    }
    planningRecordRows.value = [];
    planningRecordRowsError.value = $t('sicherplan.customerPlansWizard.errors.planningRecordLoad');
  } finally {
    if (isCurrent()) {
      planningRecordRowsLoading.value = false;
    }
  }
}

async function loadPlanningCreateReferenceOptions() {
  if (!props.tenantId || !props.accessToken || !props.customer.id) {
    planningCreateAddressOptions.value = [];
    planningCreateStagedAddresses.value = [];
    planningCreateAddressLookupError.value = '';
    planningCreateAddressLookupLoading.value = false;
    return;
  }
  planningCreateAddressLookupLoading.value = true;
  planningCreateAddressLookupError.value = '';
  try {
    planningCreateAddressOptions.value = await listCustomerAddresses(props.tenantId, props.customer.id, props.accessToken);
    syncPlanningCreateAddressSelections();
  } catch {
    planningCreateAddressOptions.value = [];
    planningCreateAddressLookupError.value = $t('sicherplan.customerPlansWizard.errors.addressLoad');
    planningCreateModal.address_id = '';
    planningCreateModal.meeting_address_id = '';
  } finally {
    planningCreateAddressLookupLoading.value = false;
  }
}

async function submitPlanningAddressCreateModal() {
  if (!props.tenantId || !props.accessToken || !props.customer.id || !planningCreateAddressFieldKey.value) {
    return;
  }

  const payload = normalizePlanningAddressCreatePayload();
  if (!payload.street_line_1 || !payload.postal_code || !payload.city || !payload.country_code) {
    planningAddressCreateModal.error = $t('sicherplan.customerPlansWizard.errors.addressCreateValidation');
    setFeedback('error', planningAddressCreateModal.error);
    return;
  }

  planningAddressCreateModal.saving = true;
  planningAddressCreateModal.error = '';
  try {
    const created = await createCustomerAvailableAddress(props.tenantId, props.customer.id, props.accessToken, payload);
    planningCreateStagedAddresses.value = [
      ...planningCreateStagedAddresses.value.filter((entry) => entry.id !== created.id),
      created,
    ];
    await loadPlanningCreateReferenceOptions();
    if (planningCreateAddressFieldKey.value === 'meeting_address_id') {
      planningCreateModal.meeting_address_id = created.id;
    } else {
      planningCreateModal.address_id = created.id;
    }
    closePlanningAddressCreateModal();
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.addressCreateSuccess'));
  } catch {
    planningAddressCreateModal.error = $t('sicherplan.customerPlansWizard.errors.addressCreateFailed');
    setFeedback('error', planningAddressCreateModal.error);
  } finally {
    planningAddressCreateModal.saving = false;
  }
}

async function refreshTradeFairZoneOptions(tradeFairId: string, isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken || !tradeFairId) {
    if (!isCurrent()) {
      return;
    }
    tradeFairZoneOptions.value = [];
    tradeFairZoneLookupError.value = '';
    tradeFairZoneLookupLoading.value = false;
    planningRecordDraft.trade_fair_detail_trade_fair_zone_id = '';
    return;
  }
  tradeFairZoneLookupLoading.value = true;
  tradeFairZoneLookupError.value = '';
  try {
    const zones = await listTradeFairZones(props.tenantId, tradeFairId, props.accessToken);
    if (!isCurrent()) {
      return;
    }
    tradeFairZoneOptions.value = zones;
    if (!tradeFairZoneOptions.value.some((row) => row.id === planningRecordDraft.trade_fair_detail_trade_fair_zone_id)) {
      planningRecordDraft.trade_fair_detail_trade_fair_zone_id = '';
    }
  } catch {
    if (!isCurrent()) {
      return;
    }
    tradeFairZoneOptions.value = [];
    tradeFairZoneLookupError.value = $t('sicherplan.customerPlansWizard.errors.tradeFairZoneLoad');
    planningRecordDraft.trade_fair_detail_trade_fair_zone_id = '';
  } finally {
    if (!isCurrent()) {
      return;
    }
    tradeFairZoneLookupLoading.value = false;
  }
}

async function loadOrderReferenceOptions(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  const [serviceCategories, requirementTypes, patrolRoutes, equipmentItems, functionTypes, qualificationTypes] =
    await Promise.all([
      listServiceCategoryOptions(props.tenantId, props.accessToken),
      listPlanningSetupRecords('requirement_type', props.tenantId, props.accessToken, { customer_id: props.customer.id }),
      listPlanningSetupRecords('patrol_route', props.tenantId, props.accessToken, { customer_id: props.customer.id }),
      listPlanningSetupRecords('equipment_item', props.tenantId, props.accessToken, { customer_id: props.customer.id }),
      listFunctionTypes(props.tenantId, props.accessToken),
      listQualificationTypes(props.tenantId, props.accessToken),
    ]);

  if (!isCurrent()) {
    return;
  }
  serviceCategoryOptions.value = serviceCategories;
  requirementTypeOptions.value = requirementTypes as PlanningListItem[];
  patrolRouteOptions.value = patrolRoutes as PlanningListItem[];
  equipmentItemOptions.value = equipmentItems as PlanningCatalogRecordRead[];
  functionTypeOptions.value = functionTypes;
  qualificationTypeOptions.value = qualificationTypes;
}

async function loadCustomerOrderRows(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken || !props.customer.id) {
    if (!isCurrent()) {
      return;
    }
    customerOrderRows.value = [];
    customerOrderRowsError.value = '';
    customerOrderRowsLoading.value = false;
    return;
  }
  customerOrderRowsLoading.value = true;
  customerOrderRowsError.value = '';
  try {
    const rows = await listCustomerOrders(props.tenantId, props.accessToken, {
      customer_id: props.customer.id,
      include_archived: false,
    });
    if (!isCurrent()) {
      return;
    }
    customerOrderRows.value = rows;
  } catch {
    if (!isCurrent()) {
      return;
    }
    customerOrderRows.value = [];
    customerOrderRowsError.value = $t('sicherplan.customerPlansWizard.errors.orderListLoadFailed');
  } finally {
    if (!isCurrent()) {
      return;
    }
    customerOrderRowsLoading.value = false;
  }
}

function selectExistingOrder(orderId: string) {
  if (!orderId) {
    return false;
  }
  if (existingOrderEditActive.value && editingExistingOrderId.value === orderId) {
    return true;
  }
  if (existingOrderEditActive.value && editingExistingOrderId.value !== orderId && hasExistingOrderEditDirtyState()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.completeCurrentOrderEditBeforeContinue'));
    emit('step-ui-state', 'order-details', { error: 'edit_incomplete' });
    return false;
  }
  if (existingOrderEditActive.value && editingExistingOrderId.value !== orderId) {
    closeExistingOrderEdit();
  }
  selectedExistingOrderId.value = orderId;
  orderSelectionMode.value = 'use_existing';
  clearDraftRestoreMessage();
  emit('step-completion', 'order-details', true);
  emit('step-ui-state', 'order-details', { dirty: false, error: '' });
  setFeedback('neutral', '');
  return true;
}

async function editExistingOrder(orderId: string) {
  if (!selectExistingOrder(orderId)) {
    return;
  }
  await openExistingOrderEdit(orderId);
}

async function openExistingOrderEdit(orderId: string, options?: { applyPersistedDraft?: boolean; showLoadedMessage?: boolean }) {
  if (!props.tenantId || !props.accessToken || !orderId) {
    return;
  }
  if (existingOrderEditActive.value && editingExistingOrderId.value === orderId) {
    return;
  }
  if (existingOrderEditActive.value && editingExistingOrderId.value !== orderId && hasExistingOrderEditDirtyState()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.completeCurrentOrderEditBeforeContinue'));
    emit('step-ui-state', 'order-details', { error: 'edit_incomplete' });
    return;
  }
  const shouldApplyDraft = options?.applyPersistedDraft !== false;
  pendingExistingOrderEditId.value = orderId;
  stepLoading.value = true;
  emit('step-ui-state', 'order-details', { loading: true, error: '' });
  try {
    const order = await getCustomerOrder(props.tenantId, orderId, props.accessToken);
    syncOrderDraft(order);
    selectedExistingOrderId.value = order.id;
    editingExistingOrderId.value = order.id;
    existingOrderEditFormOpen.value = true;
    orderSelectionMode.value = 'use_existing';
    clearDraftRestoreMessage();
    const persistedDraft = shouldApplyDraft
      ? loadExistingOrderEditDraft<OrderDetailsEditDraftPersistence>(order.id)
      : null;
    if (persistedDraft?.form) {
      applyOrderDraftPersistence(persistedDraft.form);
      restoreDraftMessage();
    }
    const editDirty = Boolean(persistedDraft?.form) && hasExistingOrderEditDirtyState();
    emit('step-completion', 'order-details', true);
    emit('step-ui-state', 'order-details', { dirty: editDirty, error: '' });
    if (options?.showLoadedMessage !== false) {
      setFeedback('success', $t('sicherplan.customerPlansWizard.messages.existingOrderLoaded'));
    }
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderLoadFailed'));
    emit('step-ui-state', 'order-details', { error: 'load_failed' });
  } finally {
    pendingExistingOrderEditId.value = '';
    stepLoading.value = false;
    emit('step-ui-state', 'order-details', { loading: false });
  }
}

function cancelExistingOrderEdit() {
  closeExistingOrderEdit();
  emit('step-completion', 'order-details', Boolean(selectedExistingOrderId.value));
  emit('step-ui-state', 'order-details', { dirty: false, error: '' });
  setFeedback('neutral', '');
}

async function loadOrderState(isCurrent = () => true) {
  const persistedOrderDraft = loadStepDraft<OrderDetailsDraftPersistence | Partial<typeof orderDraft>>('order-details');
  const persistedEquipmentDraft = loadStepDraft<
    Partial<typeof equipmentLineDraft> & { selected_equipment_line_id?: string }
  >('equipment-lines');
  const persistedRequirementDraft = loadStepDraft<
    Partial<typeof requirementLineDraft> & { selected_requirement_line_id?: string }
  >('requirement-lines');
  const persistedDocumentsDraft = loadStepDraft<OrderDocumentsDraftPersistence>('order-documents');

  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    if (!isCurrent()) {
      return;
    }
    resetOrderSelection();
    orderEquipmentLines.value = [];
    orderRequirementLines.value = [];
    orderAttachments.value = [];
    if (customerOrderRows.value.length) {
      if (
        persistedOrderDraft &&
        isOrderDetailsDraftPersistence(persistedOrderDraft) &&
        persistedOrderDraft.mode === 'create_new'
      ) {
        orderSelectionMode.value = 'create_new';
        applyOrderDraftPersistence(persistedOrderDraft.form);
        if (hasOrderDraftContent()) {
          restoreDraftMessage();
        }
      } else {
        orderSelectionMode.value = 'use_existing';
        selectedExistingOrderId.value =
          persistedOrderDraft &&
          isOrderDetailsDraftPersistence(persistedOrderDraft) &&
          persistedOrderDraft.mode === 'use_existing'
            ? persistedOrderDraft.selected_order_id || ''
            : '';
        withDraftSyncPaused(() => {
          resetOrderDraft();
        });
      }
    } else if (hasOrderDraftContent()) {
      orderSelectionMode.value = 'create_new';
      return;
    } else if (persistedOrderDraft) {
      orderSelectionMode.value =
        isOrderDetailsDraftPersistence(persistedOrderDraft) && persistedOrderDraft.mode === 'use_existing' && customerOrderRows.value.length
          ? 'use_existing'
          : 'create_new';
      selectedExistingOrderId.value =
        isOrderDetailsDraftPersistence(persistedOrderDraft) && persistedOrderDraft.mode === 'use_existing'
          ? persistedOrderDraft.selected_order_id || ''
          : '';
      if (isOrderDetailsDraftPersistence(persistedOrderDraft)) {
        applyOrderDraftPersistence(persistedOrderDraft.form);
      } else {
        applyOrderDraftPersistence(persistedOrderDraft);
      }
      restoreDraftMessage();
    } else {
      orderSelectionMode.value = customerOrderRows.value.length ? 'use_existing' : 'create_new';
      withDraftSyncPaused(() => {
        resetOrderDraft();
      });
    }
    if (persistedEquipmentDraft) {
      applyEquipmentLineDraftPersistence(persistedEquipmentDraft);
    } else if (hasEquipmentLineDraftContent()) {
      // Keep the active unsaved draft through reference reloads.
    } else {
      withDraftSyncPaused(() => {
        resetEquipmentLineDraft();
      });
    }
    if (persistedRequirementDraft) {
      applyRequirementLineDraftPersistence(persistedRequirementDraft);
    } else if (hasRequirementLineDraftContent()) {
      // Keep the active unsaved draft through reference reloads.
    } else {
      withDraftSyncPaused(() => {
        resetRequirementLineDraft();
      });
    }
    if (persistedDocumentsDraft) {
      applyOrderDocumentsDraftPersistence(persistedDocumentsDraft);
    } else if (hasOrderAttachmentDraftContent()) {
      // Keep the active unsaved draft through reference reloads.
    } else {
      withDraftSyncPaused(() => {
        resetOrderAttachmentDraft();
      });
    }
    return;
  }
  if (orderStepActive.value) {
    if (!isCurrent()) {
      return;
    }
    if (
      pendingExistingOrderEditId.value === props.wizardState.order_id ||
      (existingOrderEditActive.value && editingExistingOrderId.value === props.wizardState.order_id)
    ) {
      emit('step-completion', 'order-details', true);
      emit('step-ui-state', 'order-details', { dirty: hasExistingOrderEditDirtyState(), error: '' });
      return;
    }
    orderSelectionMode.value = 'use_existing';
    selectedExistingOrderId.value = props.wizardState.order_id;
    const persistedExistingEditDraft = loadExistingOrderEditDraft<OrderDetailsEditDraftPersistence>(
      props.wizardState.order_id,
    );
    if (persistedExistingEditDraft?.form) {
      await openExistingOrderEdit(props.wizardState.order_id, {
        applyPersistedDraft: true,
        showLoadedMessage: false,
      });
      if (!isCurrent()) {
        return;
      }
    } else {
      closeExistingOrderEdit({ clearDraft: false });
      clearDraftRestoreMessage();
      emit('step-completion', 'order-details', true);
      emit('step-ui-state', 'order-details', { dirty: false, error: '' });
    }
    return;
  }
  const order = await getCustomerOrder(props.tenantId, props.wizardState.order_id, props.accessToken);
  if (!isCurrent()) {
    return;
  }
  orderSelectionMode.value = 'use_existing';
  selectedExistingOrderId.value = order.id;
  syncOrderDraft(order);
  const [equipmentLines, requirementLines, attachments] = await Promise.all([
    listOrderEquipmentLines(props.tenantId, props.wizardState.order_id, props.accessToken),
    listOrderRequirementLines(props.tenantId, props.wizardState.order_id, props.accessToken),
    listOrderAttachments(props.tenantId, props.wizardState.order_id, props.accessToken),
  ]);
  if (!isCurrent()) {
    return;
  }
  orderEquipmentLines.value = equipmentLines;
  orderRequirementLines.value = requirementLines;
  orderAttachments.value = attachments;
  if (persistedOrderDraft) {
    if (
      isOrderDetailsDraftPersistence(persistedOrderDraft) &&
      persistedOrderDraft.mode === 'use_existing' &&
      persistedOrderDraft.selected_order_id === order.id
    ) {
      applyOrderDraftPersistence(persistedOrderDraft.form);
      restoreDraftMessage();
    }
  }
  if (persistedEquipmentDraft) {
    applyEquipmentLineDraftPersistence(persistedEquipmentDraft);
  } else {
    withDraftSyncPaused(() => {
      resetEquipmentLineDraft();
    });
  }
  if (persistedRequirementDraft) {
    applyRequirementLineDraftPersistence(persistedRequirementDraft);
  } else {
    withDraftSyncPaused(() => {
      resetRequirementLineDraft();
    });
  }
  if (persistedDocumentsDraft) {
    applyOrderDocumentsDraftPersistence(persistedDocumentsDraft);
  } else {
    withDraftSyncPaused(() => {
      resetOrderAttachmentDraft();
    });
  }
}

async function loadPlanningRecordReferenceOptions(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken) {
    eventVenueOptions.value = [];
    siteOptions.value = [];
    tradeFairOptions.value = [];
    patrolRouteOptions.value = [];
    return;
  }
  const [eventVenues, sites, tradeFairs, patrolRoutes] = await Promise.all([
    listPlanningSetupRecords('event_venue', props.tenantId, props.accessToken, { customer_id: props.customer.id }),
    listPlanningSetupRecords('site', props.tenantId, props.accessToken, { customer_id: props.customer.id }),
    listPlanningSetupRecords('trade_fair', props.tenantId, props.accessToken, { customer_id: props.customer.id }),
    listPlanningSetupRecords('patrol_route', props.tenantId, props.accessToken, { customer_id: props.customer.id }),
  ]);
  if (!isCurrent()) {
    return;
  }
  eventVenueOptions.value = eventVenues as PlanningListItem[];
  siteOptions.value = sites as PlanningListItem[];
  tradeFairOptions.value = tradeFairs as PlanningListItem[];
  patrolRouteOptions.value = patrolRoutes as PlanningListItem[];
}

function syncPlanningEntityOptionsFromReferenceOptions() {
  if (planningFamily.value === 'event_venue') {
    planningEntityOptions.value = eventVenueOptions.value;
  } else if (planningFamily.value === 'trade_fair') {
    planningEntityOptions.value = tradeFairOptions.value;
  } else if (planningFamily.value === 'patrol_route') {
    planningEntityOptions.value = patrolRouteOptions.value;
  } else {
    planningEntityOptions.value = siteOptions.value;
  }
  if (!planningEntityOptions.value.some((option) => option.id === planningEntityId.value)) {
    planningEntityId.value = '';
  }
}

async function loadPlanningRecordState(isCurrent = () => true) {
  const directPlanningRecordDraft = loadStepDraft<PlanningRecordOverviewDraftPersistence>('planning-record-overview');
  const planningRecordDraftCandidates = loadWizardDraftCandidatesForCustomer<PlanningRecordOverviewDraftPersistence>(
    {
      customerId: props.customer.id,
      tenantId: props.tenantId,
    },
    'planning-record-overview',
  ).filter((candidate) => !candidate.order_id || candidate.order_id === props.wizardState.order_id);
  const persistedPlanningRecordDraft =
    directPlanningRecordDraft ||
    planningRecordDraftCandidates.find((candidate) => Boolean(candidate.planning_context?.planning_entity_id)) ||
    planningRecordDraftCandidates[0] ||
    null;
  const hasContentfulPersistedPlanningRecordDraft = hasContentfulPlanningRecordDraftPayload(persistedPlanningRecordDraft);
  const persistedDocumentsDraft =
    loadStepDraft<OrderDocumentsDraftPersistence>('planning-record-documents');
  if (
    hasContentfulPersistedPlanningRecordDraft &&
    persistedPlanningRecordDraft &&
    (!persistedPlanningRecordDraft.order_id || persistedPlanningRecordDraft.order_id === props.wizardState.order_id)
  ) {
    applyPlanningRecordOverviewDraftPersistence(persistedPlanningRecordDraft);
  }
  await loadPlanningRecordReferenceOptions(isCurrent);
  if (!isCurrent()) {
    return;
  }
  syncPlanningEntityOptionsFromReferenceOptions();
  await loadExistingPlanningRecordRows(isCurrent);
  if (!isCurrent()) {
    return;
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.planning_record_id) {
    if (!isCurrent()) {
      return;
    }
    const shouldAutoSelectSingleSavedRecord =
      planningRecordRows.value.length === 1 &&
      !hasContentfulPersistedPlanningRecordDraft &&
      !hasPlanningRecordDraftContent();
    if (shouldAutoSelectSingleSavedRecord) {
      const matchingRow = planningRecordRows.value[0];
      if (!matchingRow) {
        return;
      }
      const record = await getPlanningRecord(props.tenantId, matchingRow.id, props.accessToken);
      if (!isCurrent()) {
        return;
      }
      syncPlanningRecordDraft(record);
      planningRecordAttachments.value = [];
      emit('saved-context', {
        ...buildPlanningContextPatch(),
        planning_record_id: record.id,
      });
      clearStepDraft('planning-record-overview');
      clearDraftRestoreMessage();
      return;
    }
    selectedPlanningRecord.value = null;
    planningRecordAttachments.value = [];
    if (
      hasContentfulPersistedPlanningRecordDraft &&
      persistedPlanningRecordDraft &&
      (!persistedPlanningRecordDraft.order_id || persistedPlanningRecordDraft.order_id === props.wizardState.order_id)
    ) {
      applyPlanningRecordOverviewDraftPersistence(persistedPlanningRecordDraft);
      restoreDraftMessage();
    } else if (!hasPlanningRecordDraftContent()) {
      withDraftSyncPaused(() => {
        resetPlanningRecordDraft();
        if (selectedOrder.value) {
          planningRecordDraft.name = selectedOrder.value.title;
          planningRecordDraft.planning_from = selectedOrder.value.service_from;
          planningRecordDraft.planning_to = selectedOrder.value.service_to;
        }
      });
    }
    if (persistedDocumentsDraft) {
      applyPlanningRecordDocumentsDraftPersistence(persistedDocumentsDraft);
    } else if (!hasPlanningRecordAttachmentDraftContent()) {
      withDraftSyncPaused(() => {
        resetPlanningRecordAttachmentDraft();
      });
    }
    const activePlanningEntityId = currentPlanningEntityScope.value?.planningEntityId || planningEntityId.value;
    if (currentPlanningModeCode.value === 'trade_fair') {
      await refreshTradeFairZoneOptions(activePlanningEntityId, isCurrent);
    } else {
      await refreshTradeFairZoneOptions('', isCurrent);
    }
    return;
  }
  const [record, attachments] = await Promise.all([
    getPlanningRecord(props.tenantId, props.wizardState.planning_record_id, props.accessToken),
    listPlanningRecordAttachments(props.tenantId, props.wizardState.planning_record_id, props.accessToken),
  ]);
  if (!isCurrent()) {
    return;
  }
  syncPlanningRecordDraft(record);
  planningRecordAttachments.value = attachments;
  if (persistedPlanningRecordDraft && (!persistedPlanningRecordDraft.order_id || persistedPlanningRecordDraft.order_id === props.wizardState.order_id)) {
    applyPlanningRecordOverviewDraftPersistence(persistedPlanningRecordDraft);
    restoreDraftMessage();
  }
  if (persistedDocumentsDraft) {
    applyPlanningRecordDocumentsDraftPersistence(persistedDocumentsDraft);
  } else if (!hasPlanningRecordAttachmentDraftContent()) {
    withDraftSyncPaused(() => {
      resetPlanningRecordAttachmentDraft();
    });
  }
  const activePlanningEntityId = currentPlanningEntityScope.value?.planningEntityId || planningEntityId.value;
  if (currentPlanningModeCode.value === 'trade_fair') {
    await refreshTradeFairZoneOptions(activePlanningEntityId, isCurrent);
  } else {
    await refreshTradeFairZoneOptions('', isCurrent);
  }
}

async function loadShiftPlanningReferenceOptions(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken) {
    shiftPlanRows.value = [];
    shiftTemplateOptions.value = [];
    shiftTypeOptions.value = [];
    return;
  }
  const [plans, templates, shiftTypes] = await Promise.all([
    props.wizardState.planning_record_id
      ? listShiftPlans(props.tenantId, props.accessToken, { planning_record_id: props.wizardState.planning_record_id })
      : Promise.resolve([]),
    listShiftTemplates(props.tenantId, props.accessToken, {}),
    listShiftTypeOptions(props.tenantId, props.accessToken),
  ]);
  if (!isCurrent()) {
    return;
  }
  shiftPlanRows.value = plans;
  shiftTemplateOptions.value = templates;
  shiftTypeOptions.value = shiftTypes;
}

async function loadShiftPlanState(isCurrent = () => true) {
  const persistedShiftPlanDraft = normalizeShiftPlanDraftPersistence(
    loadStepDraft<ShiftPlanDraftPersistence | Partial<typeof shiftPlanDraft>>('shift-plan'),
  );
  await loadShiftPlanningReferenceOptions(isCurrent);
  if (!isCurrent()) {
    return;
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    if (!isCurrent()) {
      return;
    }
    selectedShiftPlan.value = null;
    if (persistedShiftPlanDraft) {
      applyShiftPlanDraftPersistence(persistedShiftPlanDraft.draft);
      restoreDraftMessage();
    } else if (shiftPlanRows.value.length === 1 && !hasShiftPlanDraftContent()) {
      const matchingRow = shiftPlanRows.value[0];
      if (!matchingRow) {
        return;
      }
      await selectShiftPlanRow(matchingRow.id);
    } else if (!hasShiftPlanDraftContent()) {
      withDraftSyncPaused(() => {
        resetShiftPlanDraft();
      });
    }
    return;
  }
  const plan = await getShiftPlan(props.tenantId, props.wizardState.shift_plan_id, props.accessToken);
  if (!isCurrent()) {
    return;
  }
  syncShiftPlanDraft(plan);
  if (
    persistedShiftPlanDraft &&
    persistedShiftPlanDraft.selected_shift_plan_id === props.wizardState.shift_plan_id
  ) {
    applyShiftPlanDraftPersistence(persistedShiftPlanDraft.draft);
    restoreDraftMessage();
  }
}

async function loadSeriesState(isCurrent = () => true) {
  const persistedSeriesDraft = loadStepDraft<SeriesExceptionsDraftPersistence>('series-exceptions');
  await loadShiftPlanningReferenceOptions(isCurrent);
  if (!isCurrent()) {
    return;
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    if (!isCurrent()) {
      return;
    }
    selectedSeries.value = null;
    seriesRows.value = [];
    seriesExceptions.value = [];
    if (persistedSeriesDraft) {
      applySeriesDraftPersistence(persistedSeriesDraft);
      restoreDraftMessage();
    } else if (!hasSeriesDraftContent()) {
      withDraftSyncPaused(() => {
        resetSeriesDraft();
        resetExceptionDraft();
      });
    }
    return;
  }
  const listedSeries = await listShiftSeries(props.tenantId, props.wizardState.shift_plan_id, props.accessToken);
  if (!isCurrent()) {
    return;
  }
  seriesRows.value = listedSeries;
  if (!props.wizardState.series_id) {
    if (!isCurrent()) {
      return;
    }
    selectedSeries.value = null;
    seriesExceptions.value = [];
    if (persistedSeriesDraft) {
      applySeriesDraftPersistence(persistedSeriesDraft);
      restoreDraftMessage();
    } else if (!hasSeriesDraftContent()) {
      withDraftSyncPaused(() => {
        resetSeriesDraft();
        resetExceptionDraft();
      });
    }
    return;
  }
  const [series, exceptions] = await Promise.all([
    getShiftSeries(props.tenantId, props.wizardState.series_id, props.accessToken),
    listShiftSeriesExceptions(props.tenantId, props.wizardState.series_id, props.accessToken),
  ]);
  if (!isCurrent()) {
    return;
  }
  syncSeriesDraft(series);
  seriesExceptions.value = exceptions;
  if (persistedSeriesDraft) {
    applySeriesDraftPersistence(persistedSeriesDraft);
    restoreDraftMessage();
  }
}

async function refreshStepData() {
  if (!handledStepActive.value) {
    return;
  }
  const externalContextKey = buildStepExternalContextKey();
  if (externalContextKey === lastLoadedStepContextKey) {
    return;
  }
  lastLoadedStepContextKey = externalContextKey;
  const isCurrent = buildStepLoadGuard();
  clearDraftRestoreMessage();
  emit('step-ui-state', props.currentStepId, { loading: true, error: '' });
  stepLoading.value = true;
  try {
    if (orderStepActive.value) {
      await loadOrderReferenceOptions(isCurrent);
      await loadCustomerOrderRows(isCurrent);
      await loadOrderState(isCurrent);
    } else if (equipmentStepActive.value || requirementStepActive.value || documentsStepActive.value) {
      await loadOrderReferenceOptions(isCurrent);
      await loadOrderState(isCurrent);
    } else if (planningRecordStepActive.value || planningRecordDocumentsStepActive.value) {
      await loadOrderState(isCurrent);
      await loadPlanningRecordState(isCurrent);
    } else if (shiftPlanStepActive.value) {
      await loadPlanningRecordState(isCurrent);
      await loadShiftPlanState(isCurrent);
    } else if (seriesStepActive.value) {
      await loadPlanningRecordState(isCurrent);
      await loadShiftPlanState(isCurrent);
      await loadSeriesState(isCurrent);
    }
  } catch {
    if (!isCurrent()) {
      return;
    }
    lastLoadedStepContextKey = '';
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.stepLoad'));
    emit('step-ui-state', props.currentStepId, { error: 'load_failed' });
  } finally {
    if (!isCurrent()) {
      return;
    }
    stepLoading.value = false;
    emit('step-ui-state', props.currentStepId, { loading: false });
  }
}

async function submitPlanningCreateModal() {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  const payloadBase = {
    customer_id: props.customer.id,
    notes: planningCreateModal.notes.trim() || null,
    tenant_id: props.tenantId,
  };
  let payload: Record<string, unknown>;

  if (planningFamily.value === 'site') {
    if (!planningCreateModal.site_no.trim() || !planningCreateModal.name.trim()) {
      setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningCreateInvalid'));
      return;
    }
    payload = {
      ...payloadBase,
      address_id: planningCreateModal.address_id || null,
      latitude: planningCreateModal.latitude || null,
      name: planningCreateModal.name.trim(),
      site_no: planningCreateModal.site_no.trim(),
      longitude: planningCreateModal.longitude || null,
      status: planningCreateModal.status || undefined,
      timezone: planningCreateModal.timezone || null,
      watchbook_enabled: planningCreateModal.watchbook_enabled,
    };
  } else if (planningFamily.value === 'event_venue') {
    if (!planningCreateModal.venue_no.trim() || !planningCreateModal.name.trim()) {
      setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningCreateInvalid'));
      return;
    }
    payload = {
      ...payloadBase,
      address_id: planningCreateModal.address_id || null,
      latitude: planningCreateModal.latitude || null,
      name: planningCreateModal.name.trim(),
      venue_no: planningCreateModal.venue_no.trim(),
      longitude: planningCreateModal.longitude || null,
      status: planningCreateModal.status || undefined,
      timezone: planningCreateModal.timezone || null,
    };
  } else if (planningFamily.value === 'trade_fair') {
    if (
      !planningCreateModal.fair_no.trim() ||
      !planningCreateModal.name.trim() ||
      !planningCreateModal.start_date ||
      !planningCreateModal.end_date ||
      planningCreateModal.end_date < planningCreateModal.start_date
    ) {
      setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningCreateInvalid'));
      return;
    }
    payload = {
      ...payloadBase,
      address_id: planningCreateModal.address_id || null,
      end_date: planningCreateModal.end_date,
      fair_no: planningCreateModal.fair_no.trim(),
      latitude: planningCreateModal.latitude || null,
      name: planningCreateModal.name.trim(),
      longitude: planningCreateModal.longitude || null,
      start_date: planningCreateModal.start_date,
      status: planningCreateModal.status || undefined,
      timezone: planningCreateModal.timezone || null,
      venue_id: planningCreateModal.venue_id || null,
    };
  } else {
    if (!planningCreateModal.route_no.trim() || !planningCreateModal.name.trim()) {
      setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningCreateInvalid'));
      return;
    }
    payload = {
      ...payloadBase,
      end_point_text: planningCreateModal.end_point_text.trim() || null,
      meeting_address_id: planningCreateModal.meeting_address_id || null,
      name: planningCreateModal.name.trim(),
      route_no: planningCreateModal.route_no.trim(),
      site_id: planningCreateModal.site_id || null,
      start_point_text: planningCreateModal.start_point_text.trim() || null,
      status: planningCreateModal.status || undefined,
      travel_policy_code: planningCreateModal.travel_policy_code.trim() || null,
    };
  }

  planningCreateModal.saving = true;
  try {
    const created = await createPlanningSetupRecord(planningFamily.value, props.tenantId, props.accessToken, payload);
    await loadPlanningEntityOptions();
    planningEntityId.value = created.id;
    planningSelectionMode.value = 'use_existing';
    selectedPlanningRecord.value = null;
    planningRecordDraft.planning_mode_code = planningModeCode.value;
    if (planningModeCode.value === 'trade_fair') {
      await refreshTradeFairZoneOptions(created.id);
    } else {
      await refreshTradeFairZoneOptions('');
    }
    await loadExistingPlanningRecordRows();
    resetPlanningCreateModal();
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningEntryCreated'));
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningCreateFailed'));
  } finally {
    planningCreateModal.saving = false;
  }
}

async function submitRequirementModal() {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  if (
    !requirementModal.code.trim() ||
    !requirementModal.label.trim() ||
    !requirementModal.default_planning_mode_code.trim()
  ) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.requirementCreateInvalid'));
    return;
  }
  requirementModal.saving = true;
  try {
    const created = await createPlanningSetupRecord('requirement_type', props.tenantId, props.accessToken, {
      code: requirementModal.code.trim(),
      default_planning_mode_code: requirementModal.default_planning_mode_code.trim(),
      label: requirementModal.label.trim(),
      notes: requirementModal.notes.trim() || null,
      tenant_id: props.tenantId,
    });
    await loadOrderReferenceOptions();
    requirementLineDraft.requirement_type_id = created.id;
    resetRequirementModal();
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.requirementCreateFailed'));
  } finally {
    requirementModal.saving = false;
  }
}

async function submitEquipmentModal() {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  if (!equipmentModal.code.trim() || !equipmentModal.label.trim() || !equipmentModal.unit_of_measure_code.trim()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.equipmentCreateInvalid'));
    return;
  }
  equipmentModal.saving = true;
  try {
    const created = await createPlanningSetupRecord('equipment_item', props.tenantId, props.accessToken, {
      code: equipmentModal.code.trim(),
      label: equipmentModal.label.trim(),
      notes: equipmentModal.notes.trim() || null,
      tenant_id: props.tenantId,
      unit_of_measure_code: equipmentModal.unit_of_measure_code.trim(),
    });
    await loadOrderReferenceOptions();
    equipmentLineDraft.equipment_item_id = created.id;
    resetEquipmentModal();
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.equipmentCreateFailed'));
  } finally {
    equipmentModal.saving = false;
  }
}

async function onOrderAttachmentSelected(event: Event) {
  const file = (event.target as HTMLInputElement)?.files?.[0];
  if (!file) {
    return;
  }
  orderAttachmentDraft.file_name = file.name;
  orderAttachmentDraft.content_type = file.type || 'application/octet-stream';
  orderAttachmentDraft.content_base64 = await fileToBase64(file);
  if (!orderAttachmentDraft.title) {
    orderAttachmentDraft.title = file.name;
  }
}

async function onPlanningRecordAttachmentSelected(event: Event) {
  const file = (event.target as HTMLInputElement)?.files?.[0];
  if (!file) {
    return;
  }
  planningRecordAttachmentDraft.file_name = file.name;
  planningRecordAttachmentDraft.content_type = file.type || 'application/octet-stream';
  planningRecordAttachmentDraft.content_base64 = await fileToBase64(file);
  if (!planningRecordAttachmentDraft.title) {
    planningRecordAttachmentDraft.title = file.name;
  }
}

async function submitOrderStep() {
  if (!props.tenantId || !props.accessToken) {
    return false;
  }
  if (orderModeUsesExisting.value && !selectedExistingOrderId.value) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderSelectionRequired'));
    emit('step-completion', 'order-details', false);
    return false;
  }
  if (orderModeUsesExisting.value) {
    if (hasExistingOrderEditDirtyState()) {
      setFeedback('error', $t('sicherplan.customerPlansWizard.errors.completeCurrentOrderEditBeforeContinue'));
      emit('step-completion', 'order-details', false);
      emit('step-ui-state', 'order-details', { error: 'edit_incomplete' });
      return false;
    }
    emit('saved-context', { order_id: selectedExistingOrderId.value });
    clearStepDraft('order-details');
    emit('step-completion', 'order-details', true);
    emit('step-ui-state', 'order-details', { dirty: false, error: '' });
    return true;
  }
  const blockReason = derivePlanningOrderSubmitBlockReason(orderDraft);
  if (blockReason) {
    setFeedback('error', $t(`sicherplan.customerPlansWizard.errors.${blockReason}`));
    return false;
  }
  if (!orderDraft.service_from || !orderDraft.service_to || orderDraft.service_to < orderDraft.service_from) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderWindowInvalid'));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-details', { loading: true, error: '' });
  try {
    const payload = {
      customer_id: props.customer.id,
      notes: orderDraft.notes || null,
      order_no: orderDraft.order_no,
      patrol_route_id: normalizeUuid(orderDraft.patrol_route_id),
      release_state: orderDraft.release_state || 'draft',
      requirement_type_id: normalizeUuid(orderDraft.requirement_type_id),
      security_concept_text: orderDraft.security_concept_text || null,
      service_category_code: orderDraft.service_category_code,
      service_from: orderDraft.service_from,
      service_to: orderDraft.service_to,
      tenant_id: props.tenantId,
      title: orderDraft.title,
    };
    const saved = await createCustomerOrder(props.tenantId, props.accessToken, payload);
    orderSelectionMode.value = 'use_existing';
    selectedExistingOrderId.value = saved.id;
    closeExistingOrderEdit({ clearDraft: false });
    clearStepDraft('order-details');
    clearDraftRestoreMessage();
    emit('saved-context', { order_id: saved.id });
    emit('step-completion', 'order-details', true);
    emit('step-ui-state', 'order-details', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderSaveFailed'));
    emit('step-ui-state', 'order-details', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-details', { loading: false });
  }
}

async function updateExistingOrder() {
  if (!props.tenantId || !props.accessToken || !existingOrderEditActive.value || !selectedOrder.value) {
    return false;
  }
  const blockReason = derivePlanningOrderSubmitBlockReason(orderDraft);
  if (blockReason) {
    setFeedback('error', $t(`sicherplan.customerPlansWizard.errors.${blockReason}`));
    return false;
  }
  if (!orderDraft.service_from || !orderDraft.service_to || orderDraft.service_to < orderDraft.service_from) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderWindowInvalid'));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-details', { loading: true, error: '' });
  try {
    const saved = await updateCustomerOrder(props.tenantId, selectedOrder.value.id, props.accessToken, {
      customer_id: props.customer.id,
      notes: orderDraft.notes || null,
      order_no: orderDraft.order_no,
      patrol_route_id: normalizeUuid(orderDraft.patrol_route_id),
      release_state: orderDraft.release_state || 'draft',
      requirement_type_id: normalizeUuid(orderDraft.requirement_type_id),
      security_concept_text: orderDraft.security_concept_text || null,
      service_category_code: orderDraft.service_category_code,
      service_from: orderDraft.service_from,
      service_to: orderDraft.service_to,
      tenant_id: props.tenantId,
      title: orderDraft.title,
      version_no: selectedOrder.value.version_no,
    });
    await loadCustomerOrderRows(() => true);
    selectedExistingOrderId.value = saved.id;
    emit('saved-context', { order_id: saved.id });
    closeExistingOrderEdit();
    emit('step-completion', 'order-details', true);
    emit('step-ui-state', 'order-details', { dirty: false, error: '' });
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.existingOrderUpdated'));
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderSaveFailed'));
    emit('step-ui-state', 'order-details', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-details', { loading: false });
  }
}

async function submitEquipmentStep() {
  if (hasEquipmentLineDraftInput()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.saveCurrentEquipmentLineBeforeContinue'));
    emit('step-completion', 'equipment-lines', false);
    return false;
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!orderEquipmentLines.value.length) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.equipmentLineRequiredBeforeContinue'));
    emit('step-completion', 'equipment-lines', false);
    return false;
  }
  emit('step-completion', 'equipment-lines', true);
  return true;
}

async function submitRequirementStep() {
  if (hasRequirementLineDraftInput()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.saveCurrentRequirementLineBeforeContinue'));
    emit('step-completion', 'requirement-lines', false);
    return false;
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!orderRequirementLines.value.length) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue'));
    emit('step-completion', 'requirement-lines', false);
    return false;
  }
  emit('step-completion', 'requirement-lines', true);
  return true;
}

function clearEquipmentLineDraftState() {
  withDraftSyncPaused(() => {
    resetEquipmentLineDraft();
  });
  clearStepDraft('equipment-lines');
  clearDraftRestoreMessage();
  emit('step-completion', 'equipment-lines', orderEquipmentLines.value.length > 0);
  emit('step-ui-state', 'equipment-lines', { dirty: false, error: '' });
}

function clearRequirementLineDraftState() {
  withDraftSyncPaused(() => {
    resetRequirementLineDraft();
  });
  clearStepDraft('requirement-lines');
  clearDraftRestoreMessage();
  emit('step-completion', 'requirement-lines', orderRequirementLines.value.length > 0);
  emit('step-ui-state', 'requirement-lines', { dirty: false, error: '' });
}

function clearOrderDocumentDraftState() {
  withDraftSyncPaused(() => {
    resetOrderAttachmentDraft();
  });
  clearStepDraft('order-documents');
  clearDraftRestoreMessage();
  setFeedback('success', $t('sicherplan.customerPlansWizard.messages.orderDocumentDraftCleared'));
  emit('step-completion', 'order-documents', orderAttachments.value.length > 0);
  emit('step-ui-state', 'order-documents', { dirty: false, error: '' });
}

function clearPlanningRecordDocumentDraftState() {
  withDraftSyncPaused(() => {
    resetPlanningRecordAttachmentDraft();
  });
  clearStepDraft('planning-record-documents');
  clearDraftRestoreMessage();
  setFeedback('neutral', '');
  emit('step-completion', 'planning-record-documents', planningRecordAttachments.value.length > 0);
  emit('step-ui-state', 'planning-record-documents', { dirty: false, error: '' });
}

async function saveEquipmentLineDraft() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!equipmentLineDraft.equipment_item_id || equipmentLineDraft.required_qty < 1) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.equipmentLineInvalid'));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'equipment-lines', { loading: true, error: '' });
  try {
    const isUpdate = Boolean(selectedEquipmentLineId.value);
    if (selectedEquipmentLineId.value) {
      await updateOrderEquipmentLine(props.tenantId, props.wizardState.order_id, selectedEquipmentLineId.value, props.accessToken, {
        equipment_item_id: equipmentLineDraft.equipment_item_id,
        notes: equipmentLineDraft.notes || null,
        required_qty: equipmentLineDraft.required_qty,
        version_no: orderEquipmentLines.value.find((line) => line.id === selectedEquipmentLineId.value)?.version_no,
      });
    } else {
      await createOrderEquipmentLine(props.tenantId, props.wizardState.order_id, props.accessToken, {
        equipment_item_id: equipmentLineDraft.equipment_item_id,
        notes: equipmentLineDraft.notes || null,
        order_id: props.wizardState.order_id,
        required_qty: equipmentLineDraft.required_qty,
        tenant_id: props.tenantId,
      });
    }
    orderEquipmentLines.value = await listOrderEquipmentLines(props.tenantId, props.wizardState.order_id, props.accessToken);
    clearEquipmentLineDraftState();
    setFeedback(
      'success',
      $t(
        isUpdate
          ? 'sicherplan.customerPlansWizard.messages.equipmentLineUpdated'
          : 'sicherplan.customerPlansWizard.messages.equipmentLineSaved',
      ),
    );
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.equipmentLineSaveFailed'));
    emit('step-ui-state', 'equipment-lines', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'equipment-lines', { loading: false });
  }
}

async function saveRequirementLineDraft() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (
    !requirementLineDraft.requirement_type_id ||
    requirementLineDraft.min_qty < 0 ||
    requirementLineDraft.target_qty < requirementLineDraft.min_qty ||
    hasDuplicateActiveRequirementLine(
      orderRequirementLines.value,
      requirementLineDraft.requirement_type_id,
      requirementLineDraft.function_type_id,
      requirementLineDraft.qualification_type_id,
      selectedRequirementLineId.value,
    )
  ) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.requirementLineInvalid'));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'requirement-lines', { loading: true, error: '' });
  try {
    const isUpdate = Boolean(selectedRequirementLineId.value);
    if (selectedRequirementLineId.value) {
      await updateOrderRequirementLine(props.tenantId, props.wizardState.order_id, selectedRequirementLineId.value, props.accessToken, {
        function_type_id: normalizeUuid(requirementLineDraft.function_type_id),
        min_qty: requirementLineDraft.min_qty,
        notes: requirementLineDraft.notes || null,
        qualification_type_id: normalizeUuid(requirementLineDraft.qualification_type_id),
        requirement_type_id: requirementLineDraft.requirement_type_id,
        target_qty: requirementLineDraft.target_qty,
        version_no: orderRequirementLines.value.find((line) => line.id === selectedRequirementLineId.value)?.version_no,
      });
    } else {
      await createOrderRequirementLine(props.tenantId, props.wizardState.order_id, props.accessToken, {
        function_type_id: normalizeUuid(requirementLineDraft.function_type_id),
        min_qty: requirementLineDraft.min_qty,
        notes: requirementLineDraft.notes || null,
        order_id: props.wizardState.order_id,
        qualification_type_id: normalizeUuid(requirementLineDraft.qualification_type_id),
        requirement_type_id: requirementLineDraft.requirement_type_id,
        target_qty: requirementLineDraft.target_qty,
        tenant_id: props.tenantId,
      });
    }
    orderRequirementLines.value = await listOrderRequirementLines(props.tenantId, props.wizardState.order_id, props.accessToken);
    clearRequirementLineDraftState();
    setFeedback(
      'success',
      $t(
        isUpdate
          ? 'sicherplan.customerPlansWizard.messages.requirementLineUpdated'
          : 'sicherplan.customerPlansWizard.messages.requirementLineSaved',
      ),
    );
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.requirementLineSaveFailed'));
    emit('step-ui-state', 'requirement-lines', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'requirement-lines', { loading: false });
  }
}

async function submitDocumentsStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasAnyOrderDocumentDraftInput()) {
    setFeedback('neutral', '');
    emit('step-completion', 'order-documents', true);
    emit('step-ui-state', 'order-documents', { dirty: false, error: '' });
    return true;
  }
  if (hasOrderAttachmentPartialDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue'));
    emit('step-completion', 'order-documents', false);
    emit('step-ui-state', 'order-documents', { error: 'draft_incomplete' });
    return false;
  }
  if (hasCompleteOrderDocumentUploadDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.attachOrClearCurrentOrderDocumentBeforeContinue'));
    emit('step-completion', 'order-documents', false);
    emit('step-ui-state', 'order-documents', { error: 'draft_incomplete' });
    return false;
  }
  if (hasCompleteOrderDocumentLinkDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.linkOrClearCurrentOrderDocumentBeforeContinue'));
    emit('step-completion', 'order-documents', false);
    emit('step-ui-state', 'order-documents', { error: 'draft_incomplete' });
    return false;
  }
  setFeedback('neutral', '');
  emit('step-completion', 'order-documents', true);
  emit('step-ui-state', 'order-documents', { dirty: false, error: '' });
  return true;
}

async function attachUploadedOrderDocument() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasCompleteOrderDocumentUploadDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentUploadIncomplete'));
    emit('step-ui-state', 'order-documents', { error: 'draft_incomplete' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-documents', { loading: true, error: '' });
  try {
    await createOrderAttachment(props.tenantId, props.wizardState.order_id, props.accessToken, {
      content_base64: orderAttachmentDraft.content_base64,
      content_type: orderAttachmentDraft.content_type,
      file_name: orderAttachmentDraft.file_name,
      label: orderAttachmentDraft.label || null,
      tenant_id: props.tenantId,
      title: orderAttachmentDraft.title.trim(),
    });
    orderAttachments.value = await listOrderAttachments(props.tenantId, props.wizardState.order_id, props.accessToken);
    withDraftSyncPaused(() => {
      resetOrderAttachmentDraft();
    });
    clearStepDraft('order-documents');
    clearDraftRestoreMessage();
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.orderDocumentAttached'));
    emit('step-completion', 'order-documents', true);
    emit('step-ui-state', 'order-documents', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentSaveFailed'));
    emit('step-ui-state', 'order-documents', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-documents', { loading: false });
  }
}

async function linkExistingOrderDocument() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasCompleteOrderDocumentLinkDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentLinkIncomplete'));
    emit('step-ui-state', 'order-documents', { error: 'draft_incomplete' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-documents', { loading: true, error: '' });
  try {
    await linkOrderAttachment(props.tenantId, props.wizardState.order_id, props.accessToken, {
      document_id: orderAttachmentLink.document_id.trim(),
      label: orderAttachmentLink.label || null,
      tenant_id: props.tenantId,
    });
    orderAttachments.value = await listOrderAttachments(props.tenantId, props.wizardState.order_id, props.accessToken);
    withDraftSyncPaused(() => {
      resetOrderAttachmentDraft();
    });
    clearStepDraft('order-documents');
    clearDraftRestoreMessage();
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.orderDocumentLinked'));
    emit('step-completion', 'order-documents', true);
    emit('step-ui-state', 'order-documents', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentSaveFailed'));
    emit('step-ui-state', 'order-documents', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-documents', { loading: false });
  }
}

async function submitPlanningRecordStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasPlanningContext.value) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.selectOrCreatePlanningContextBeforeContinue'));
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { error: 'planning_context_required' });
    return false;
  }
  planningRecordDraft.planning_mode_code = planningModeCode.value;
  const validation = validatePlanningRecordDraft(buildPlanningRecordDraftForValidation(), {
    eventVenueOptions: eventVenueOptions.value as never[],
    orderServiceFrom: selectedOrder.value?.service_from || orderDraft.service_from,
    orderServiceTo: selectedOrder.value?.service_to || orderDraft.service_to,
    patrolRouteOptions: patrolRouteOptions.value as never[],
    siteOptions: siteOptions.value as never[],
    tradeFairOptions: tradeFairOptions.value as never[],
  });
  if (!planningRecordDraft.name.trim()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningRecordNameRequired'));
    return false;
  }
  if (validation.messageKey) {
    setFeedback('error', $t(`sicherplan.customerPlansWizard.errors.${validation.messageKey}` as never));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'planning-record-overview', { loading: true, error: '' });
  try {
    const modePayload = buildPlanningRecordModePayload();
    const payload = {
      tenant_id: props.tenantId,
      order_id: props.wizardState.order_id,
      parent_planning_record_id: normalizeUuid(planningRecordDraft.parent_planning_record_id),
      dispatcher_user_id: normalizeUuid(planningRecordDraft.dispatcher_user_id),
      planning_mode_code: planningModeCode.value,
      name: planningRecordDraft.name.trim(),
      planning_from: planningRecordDraft.planning_from,
      planning_to: planningRecordDraft.planning_to,
      notes: planningRecordDraft.notes.trim() || null,
      status: planningRecordDraft.status || 'active',
      ...modePayload,
      ...(selectedPlanningRecord.value ? { version_no: selectedPlanningRecord.value.version_no } : {}),
    };
    const saved = selectedPlanningRecord.value
      ? await updatePlanningRecord(props.tenantId, selectedPlanningRecord.value.id, props.accessToken, payload)
      : await createPlanningRecord(props.tenantId, props.accessToken, payload);
    syncPlanningRecordDraft(saved);
    clearStepDraft('planning-record-overview');
    clearDraftRestoreMessage();
    emit('saved-context', {
      ...buildPlanningContextPatch(),
      planning_record_id: saved.id,
    });
    emit('step-completion', 'planning-record-overview', true);
    emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningRecordSaveFailed'));
    emit('step-ui-state', 'planning-record-overview', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'planning-record-overview', { loading: false });
  }
}

async function submitPlanningRecordDocumentsStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.planning_record_id) {
    return false;
  }
  if (hasPlanningRecordAttachmentPartialDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.completeCurrentPlanningDocumentDraftBeforeContinue'));
    emit('step-completion', 'planning-record-documents', false);
    emit('step-ui-state', 'planning-record-documents', { error: 'draft_incomplete' });
    return false;
  }
  if (!hasPlanningRecordAttachmentSubmission()) {
    setFeedback('neutral', '');
    emit('step-completion', 'planning-record-documents', true);
    emit('step-ui-state', 'planning-record-documents', { dirty: false, error: '' });
    return true;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'planning-record-documents', { loading: true, error: '' });
  try {
    if (planningRecordAttachmentDraft.content_base64) {
      await createPlanningRecordAttachment(props.tenantId, props.wizardState.planning_record_id, props.accessToken, {
        content_base64: planningRecordAttachmentDraft.content_base64,
        content_type: planningRecordAttachmentDraft.content_type,
        file_name: planningRecordAttachmentDraft.file_name,
        label: planningRecordAttachmentDraft.label || null,
        tenant_id: props.tenantId,
        title: planningRecordAttachmentDraft.title,
      });
    } else {
      await linkPlanningRecordAttachment(props.tenantId, props.wizardState.planning_record_id, props.accessToken, {
        document_id: planningRecordAttachmentLink.document_id.trim(),
        label: planningRecordAttachmentLink.label || null,
        tenant_id: props.tenantId,
      });
    }
    planningRecordAttachments.value = await listPlanningRecordAttachments(
      props.tenantId,
      props.wizardState.planning_record_id,
      props.accessToken,
    );
    withDraftSyncPaused(() => {
      resetPlanningRecordAttachmentDraft();
    });
    clearStepDraft('planning-record-documents');
    clearDraftRestoreMessage();
    emit('step-completion', 'planning-record-documents', true);
    emit('step-ui-state', 'planning-record-documents', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningRecordDocumentSaveFailed'));
    emit('step-ui-state', 'planning-record-documents', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'planning-record-documents', { loading: false });
  }
}

async function submitShiftPlanStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.planning_record_id) {
    return false;
  }
  if (!shiftPlanDraft.name.trim() || !shiftPlanDraft.planning_from || !shiftPlanDraft.planning_to || shiftPlanDraft.planning_to < shiftPlanDraft.planning_from) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.shiftPlanInvalid'));
    return false;
  }
  if (
    selectedPlanningRecord.value &&
    (shiftPlanDraft.planning_from < selectedPlanningRecord.value.planning_from ||
      shiftPlanDraft.planning_to > selectedPlanningRecord.value.planning_to)
  ) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.shiftPlanPlanningRecordWindowMismatch'));
    return false;
  }
  if (selectedShiftPlan.value && !hasShiftPlanDraftContent()) {
    clearStepDraft('shift-plan');
    clearDraftRestoreMessage();
    emit('saved-context', { shift_plan_id: selectedShiftPlan.value.id });
    emit('step-completion', 'shift-plan', true);
    emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
    return true;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'shift-plan', { loading: true, error: '' });
  try {
    const payload = {
      tenant_id: props.tenantId,
      planning_record_id: props.wizardState.planning_record_id,
      name: shiftPlanDraft.name.trim(),
      workforce_scope_code: shiftPlanDraft.workforce_scope_code,
      planning_from: shiftPlanDraft.planning_from,
      planning_to: shiftPlanDraft.planning_to,
      remarks: shiftPlanDraft.remarks.trim() || null,
      ...(selectedShiftPlan.value ? { version_no: selectedShiftPlan.value.version_no } : {}),
    };
    const saved = selectedShiftPlan.value
      ? await updateShiftPlan(props.tenantId, selectedShiftPlan.value.id, props.accessToken, payload)
      : await createShiftPlan(props.tenantId, props.accessToken, payload);
    syncShiftPlanDraft(saved);
    clearStepDraft('shift-plan');
    clearDraftRestoreMessage();
    emit('saved-context', { shift_plan_id: saved.id });
    shiftPlanRows.value = await listShiftPlans(props.tenantId, props.accessToken, { planning_record_id: props.wizardState.planning_record_id });
    emit('step-completion', 'shift-plan', true);
    emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.shiftPlanSaveFailed'));
    emit('step-ui-state', 'shift-plan', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'shift-plan', { loading: false });
  }
}

async function submitTemplateModal() {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  if (!templateModal.code.trim() || !templateModal.label.trim() || !templateModal.shift_type_code.trim()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.templateCreateInvalid'));
    return;
  }
  templateModal.saving = true;
  try {
    const created = await createShiftTemplate(props.tenantId, props.accessToken, {
      tenant_id: props.tenantId,
      code: templateModal.code.trim(),
      label: templateModal.label.trim(),
      local_start_time: templateModal.local_start_time,
      local_end_time: templateModal.local_end_time,
      default_break_minutes: templateModal.default_break_minutes,
      shift_type_code: templateModal.shift_type_code,
      meeting_point: templateModal.meeting_point.trim() || null,
      location_text: templateModal.location_text.trim() || null,
      notes: templateModal.notes.trim() || null,
    });
    shiftTemplateOptions.value = await listShiftTemplates(props.tenantId, props.accessToken, {});
    seriesDraft.shift_template_id = created.id;
    templateModal.open = false;
    resetTemplateModal();
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.templateCreateFailed'));
  } finally {
    templateModal.saving = false;
  }
}

function closeTemplateModal() {
  templateModal.open = false;
  resetTemplateModal();
}

function buildStaffingHandoffRoute(generatedShifts: Array<{ ends_at: string; id: string; starts_at: string }>) {
  const sortedShifts = sortShiftRange(generatedShifts);
  const firstShift = sortedShifts[0];
  const lastShift = sortedShifts[sortedShifts.length - 1];
  const canonicalWindow =
    firstShift && lastShift
      ? buildCanonicalStaffingWindowFromShiftRange(firstShift.starts_at, lastShift.ends_at)
      : buildCanonicalStaffingWindowFromDates(seriesDraft.date_from, seriesDraft.date_to);
  const query = new URLSearchParams({
    date_from: canonicalWindow.date_from,
    date_to: canonicalWindow.date_to,
    planning_record_id: props.wizardState.planning_record_id,
  });
  if (firstShift?.id) {
    query.set('shift_id', firstShift.id);
  }
  return `/admin/planning-staffing?${query.toString()}`;
}

async function submitSeriesStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id || !props.wizardState.planning_record_id) {
    return false;
  }
  if (!seriesDraft.label.trim() || !seriesDraft.shift_template_id || !seriesDraft.date_from || !seriesDraft.date_to || seriesDraft.date_to < seriesDraft.date_from) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.seriesInvalid'));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'series-exceptions', { loading: true, error: '' });
  try {
    const seriesPayload = {
      tenant_id: props.tenantId,
      shift_plan_id: props.wizardState.shift_plan_id,
      shift_template_id: seriesDraft.shift_template_id,
      label: seriesDraft.label.trim(),
      recurrence_code: seriesDraft.recurrence_code,
      interval_count: seriesDraft.interval_count,
      weekday_mask: seriesDraft.weekday_mask,
      timezone: seriesDraft.timezone,
      date_from: seriesDraft.date_from,
      date_to: seriesDraft.date_to,
      default_break_minutes: seriesDraft.default_break_minutes,
      shift_type_code: seriesDraft.shift_type_code || null,
      meeting_point: seriesDraft.meeting_point.trim() || null,
      location_text: seriesDraft.location_text.trim() || null,
      notes: seriesDraft.notes.trim() || null,
      customer_visible_flag: seriesDraft.customer_visible_flag,
      subcontractor_visible_flag: seriesDraft.subcontractor_visible_flag,
      stealth_mode_flag: seriesDraft.stealth_mode_flag,
      release_state: seriesDraft.release_state,
      ...(selectedSeries.value ? { version_no: selectedSeries.value.version_no } : {}),
    };
    const savedSeries = selectedSeries.value
      ? await updateShiftSeries(props.tenantId, selectedSeries.value.id, props.accessToken, seriesPayload)
      : await createShiftSeries(props.tenantId, props.wizardState.shift_plan_id, props.accessToken, seriesPayload);
    syncSeriesDraft(savedSeries);
    emit('saved-context', { series_id: savedSeries.id });
    seriesRows.value = await listShiftSeries(props.tenantId, props.wizardState.shift_plan_id, props.accessToken);

    if (exceptionDraft.exception_date) {
      const exceptionPayload = {
        tenant_id: props.tenantId,
        exception_date: exceptionDraft.exception_date,
        action_code: exceptionDraft.action_code,
        override_local_start_time: exceptionDraft.override_local_start_time.trim() || null,
        override_local_end_time: exceptionDraft.override_local_end_time.trim() || null,
        override_break_minutes: exceptionDraft.override_break_minutes === '' ? null : Number(exceptionDraft.override_break_minutes),
        override_shift_type_code: exceptionDraft.override_shift_type_code.trim() || null,
        override_meeting_point: exceptionDraft.override_meeting_point.trim() || null,
        override_location_text: exceptionDraft.override_location_text.trim() || null,
        customer_visible_flag: exceptionDraft.customer_visible_flag,
        subcontractor_visible_flag: exceptionDraft.subcontractor_visible_flag,
        stealth_mode_flag: exceptionDraft.stealth_mode_flag,
        notes: exceptionDraft.notes.trim() || null,
      };
      const savedException = selectedExceptionId.value
        ? await updateShiftSeriesException(props.tenantId, selectedExceptionId.value, props.accessToken, exceptionPayload)
        : await createShiftSeriesException(props.tenantId, savedSeries.id, props.accessToken, exceptionPayload);
      syncExceptionDraft(savedException);
    }

    seriesExceptions.value = await listShiftSeriesExceptions(props.tenantId, savedSeries.id, props.accessToken);
    clearStepDraft('series-exceptions');
    clearDraftRestoreMessage();
    const generatedShifts = await generateShiftSeries(props.tenantId, savedSeries.id, props.accessToken, {});
    emit('step-completion', 'series-exceptions', true);
    emit('step-ui-state', 'series-exceptions', { dirty: false, error: '' });
    await router.push(buildStaffingHandoffRoute(generatedShifts));
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.seriesGenerateFailed'));
    emit('step-ui-state', 'series-exceptions', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'series-exceptions', { loading: false });
  }
}

async function submitCurrentStep() {
  if (orderStepActive.value) {
    return submitOrderStep();
  }
  if (equipmentStepActive.value) {
    return submitEquipmentStep();
  }
  if (requirementStepActive.value) {
    return submitRequirementStep();
  }
  if (documentsStepActive.value) {
    return submitDocumentsStep();
  }
  if (planningRecordStepActive.value) {
    return submitPlanningRecordStep();
  }
  if (planningRecordDocumentsStepActive.value) {
    return submitPlanningRecordDocumentsStep();
  }
  if (shiftPlanStepActive.value) {
    return submitShiftPlanStep();
  }
  if (seriesStepActive.value) {
    return submitSeriesStep();
  }
  return true;
}

defineExpose({
  submitCurrentStep,
});

watch(planningFamily, async () => {
  if (draftSyncPaused.value || planningContextHydrationPaused.value || stepLoading.value) {
    return;
  }
  planningEntityId.value = '';
  await loadPlanningEntityOptions();
});

watch(planningEntityId, () => {
  if (draftSyncPaused.value) {
    return;
  }
});

watch(
  () => [
    orderDraft.order_no,
    orderDraft.title,
    orderDraft.requirement_type_id,
    orderDraft.service_category_code,
    orderDraft.service_from,
    orderDraft.service_to,
    orderDraft.notes,
    orderDraft.security_concept_text,
    orderDraft.patrol_route_id,
  ] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    if (existingOrderEditActive.value) {
      emit('step-completion', 'order-details', true);
      emit('step-ui-state', 'order-details', { dirty: hasExistingOrderEditDirtyState(), error: '' });
    } else {
      emit('step-completion', 'order-details', false);
      emit('step-ui-state', 'order-details', { dirty: true, error: '' });
    }
    persistOrderDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [equipmentLineDraft.equipment_item_id, equipmentLineDraft.required_qty, equipmentLineDraft.notes] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    emit('step-completion', 'equipment-lines', false);
    emit('step-ui-state', 'equipment-lines', { dirty: true, error: '' });
    persistEquipmentLineDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [
    requirementLineDraft.requirement_type_id,
    requirementLineDraft.function_type_id,
    requirementLineDraft.qualification_type_id,
    requirementLineDraft.min_qty,
    requirementLineDraft.target_qty,
    requirementLineDraft.notes,
  ] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    emit('step-completion', 'requirement-lines', false);
    emit('step-ui-state', 'requirement-lines', { dirty: true, error: '' });
    persistRequirementLineDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [
    orderAttachmentDraft.title,
    orderAttachmentDraft.label,
    orderAttachmentDraft.file_name,
    orderAttachmentDraft.content_base64,
    orderAttachmentLink.document_id,
    orderAttachmentLink.label,
  ] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    emit('step-completion', 'order-documents', false);
    emit('step-ui-state', 'order-documents', { dirty: true, error: '' });
    persistOrderDocumentsDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [
    planningRecordDraft.name,
    planningRecordDraft.planning_from,
    planningRecordDraft.planning_to,
    planningRecordDraft.notes,
    planningRecordDraft.event_detail_setup_note,
    planningRecordDraft.site_detail_watchbook_scope_note,
    planningRecordDraft.trade_fair_detail_stand_note,
    planningRecordDraft.trade_fair_detail_trade_fair_zone_id,
    planningRecordDraft.patrol_detail_execution_note,
  ] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { dirty: true, error: '' });
    persistPlanningRecordDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [planningFamily.value, planningSelectionMode.value, planningEntityId.value] as const,
  () => {
    if (draftSyncPaused.value || planningContextHydrationPaused.value || !planningRecordStepActive.value) {
      return;
    }
    if (
      !hasPlanningRecordDraftContent() &&
      planningSelectionMode.value === 'use_existing' &&
      planningEntityId.value === props.wizardState.planning_entity_id &&
      planningFamily.value === ((props.wizardState.planning_entity_type as PlanningEntityType) || planningFamily.value)
    ) {
      return;
    }
    persistPlanningRecordDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [
    planningRecordAttachmentDraft.title,
    planningRecordAttachmentDraft.label,
    planningRecordAttachmentDraft.file_name,
    planningRecordAttachmentDraft.content_base64,
    planningRecordAttachmentLink.document_id,
    planningRecordAttachmentLink.label,
  ] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    emit('step-completion', 'planning-record-documents', false);
    emit('step-ui-state', 'planning-record-documents', { dirty: true, error: '' });
    persistPlanningRecordDocumentsDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [
    shiftPlanDraft.name,
    shiftPlanDraft.planning_from,
    shiftPlanDraft.planning_to,
    shiftPlanDraft.workforce_scope_code,
    shiftPlanDraft.remarks,
  ] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    emit('step-completion', 'shift-plan', false);
    emit('step-ui-state', 'shift-plan', { dirty: true, error: '' });
    persistShiftPlanDraft();
  },
  { flush: 'sync' },
);

watch(
  () => [
    seriesDraft.label,
    seriesDraft.shift_template_id,
    seriesDraft.date_from,
    seriesDraft.date_to,
    seriesDraft.recurrence_code,
    seriesDraft.interval_count,
    seriesDraft.weekday_mask,
    seriesDraft.default_break_minutes,
    seriesDraft.shift_type_code,
    seriesDraft.meeting_point,
    seriesDraft.location_text,
    seriesDraft.notes,
    seriesDraft.customer_visible_flag,
    seriesDraft.subcontractor_visible_flag,
    seriesDraft.stealth_mode_flag,
    seriesDraft.release_state,
    exceptionDraft.exception_date,
    exceptionDraft.action_code,
    exceptionDraft.override_local_start_time,
    exceptionDraft.override_local_end_time,
    exceptionDraft.override_break_minutes,
    exceptionDraft.override_shift_type_code,
    exceptionDraft.override_meeting_point,
    exceptionDraft.override_location_text,
    exceptionDraft.notes,
  ] as const,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    emit('step-completion', 'series-exceptions', false);
    emit('step-ui-state', 'series-exceptions', { dirty: true, error: '' });
    persistSeriesDraft();
  },
  { flush: 'sync' },
);

watch(
  () => selectedEquipmentLineId.value,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    persistEquipmentLineDraft();
  },
);

watch(
  () => selectedRequirementLineId.value,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    persistRequirementLineDraft();
  },
);

watch(
  () => selectedExceptionId.value,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    persistSeriesDraft();
  },
);

watch(
  () => planningCreateModal.open,
  async (isOpen) => {
    if (!isOpen) {
      return;
    }
    await loadPlanningCreateReferenceOptions();
  },
);

watch(
  () => [props.customer.id, props.wizardState.customer_id] as const,
  () => {
    planningCreateStagedAddresses.value = [];
    closePlanningAddressCreateModal();
    planningLocationPickerOpen.value = false;
    clearDraftRestoreMessage();
    existingOrderEditFormOpen.value = false;
    selectedOrder.value = null;
    selectedPlanningRecord.value = null;
    selectedShiftPlan.value = null;
    selectedSeries.value = null;
    planningRecordRows.value = [];
    planningRecordRowsError.value = '';
    planningRecordRowsLoading.value = false;
    orderEquipmentLines.value = [];
    orderRequirementLines.value = [];
    orderAttachments.value = [];
    planningRecordAttachments.value = [];
    seriesRows.value = [];
    seriesExceptions.value = [];
    withDraftSyncPaused(() => {
      resetOrderDraft();
      resetEquipmentLineDraft();
      resetRequirementLineDraft();
      resetOrderAttachmentDraft();
      resetPlanningRecordDraft();
      resetPlanningRecordAttachmentDraft();
      resetShiftPlanDraft();
      resetSeriesDraft();
      resetExceptionDraft();
    });
  },
);

watch(
  () => [
    props.customer.id,
    props.currentStepId,
    props.wizardState.order_id,
    props.wizardState.planning_entity_type,
    props.wizardState.planning_entity_id,
    props.wizardState.planning_mode_code,
    props.wizardState.planning_record_id,
    props.wizardState.shift_plan_id,
    props.wizardState.series_id,
  ] as const,
  async () => {
    withPlanningContextHydrationPaused(() =>
      withDraftSyncPaused(() => {
        if (props.wizardState.planning_entity_type) {
          planningFamily.value = props.wizardState.planning_entity_type as PlanningEntityType;
        }
        planningEntityId.value = props.wizardState.planning_entity_id || '';
        planningRecordDraft.planning_mode_code = props.wizardState.planning_mode_code || planningModeCode.value;
        shiftPlanDraft.planning_record_id = props.wizardState.planning_record_id || '';
        resetRequirementModal();
      }),
    );
    await refreshStepData();
  },
  { immediate: true },
);

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload);
  withPlanningContextHydrationPaused(() =>
    withDraftSyncPaused(() => {
      resetTemplateModal();
      if (props.wizardState.planning_entity_type) {
        planningFamily.value = props.wizardState.planning_entity_type as PlanningEntityType;
      }
      planningEntityId.value = props.wizardState.planning_entity_id || '';
    }),
  );
});

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload);
  if (props.persistDraftsOnUnmount === false) {
    return;
  }
  persistAllUnsavedDrafts();
});
</script>

<template>
  <div class="sp-customer-plan-wizard-step">
    <p v-if="stepFeedback.message" class="sp-customer-plan-wizard-step__feedback" :data-tone="stepFeedback.tone">
      {{ stepFeedback.message }}
    </p>
    <p
      v-if="draftRestoreMessage"
      class="sp-customer-plan-wizard-step__feedback"
      data-testid="customer-new-plan-draft-restored"
      data-tone="neutral"
    >
      {{ draftRestoreMessage }}
    </p>

    <section v-if="orderStepActive" class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-order-details">
      <div class="sp-customer-plan-wizard-step__toggle-row">
        <label
          class="planning-admin-checkbox"
          data-testid="customer-new-plan-order-mode-existing-label"
          @click="setOrderSelectionMode('use_existing')"
        >
          <input
            v-model="orderSelectionModeModel"
            data-testid="customer-new-plan-order-mode-existing"
            name="customer-new-plan-order-mode"
            type="radio"
            value="use_existing"
          />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.useExistingOrder') }}</span>
        </label>
        <label
          class="planning-admin-checkbox"
          data-testid="customer-new-plan-order-mode-create-label"
          @click="setOrderSelectionMode('create_new')"
        >
          <input
            v-model="orderSelectionModeModel"
            data-testid="customer-new-plan-order-mode-create"
            name="customer-new-plan-order-mode"
            type="radio"
            value="create_new"
          />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.createNewOrder') }}</span>
        </label>
      </div>

      <template v-if="orderModeUsesExisting">
        <div data-testid="customer-new-plan-existing-order-select"></div>
        <p class="eyebrow">
          {{ $t('sicherplan.customerPlansWizard.forms.existingCustomerOrders') }}
        </p>
        <div class="sp-customer-plan-wizard-step__list" data-testid="customer-new-plan-existing-order-list">
          <p v-if="customerOrderRowsLoading" class="field-help">{{ $t('sicherplan.customerPlansWizard.loadingBody') }}</p>
          <p v-else-if="customerOrderRowsError" class="field-help">{{ customerOrderRowsError }}</p>
          <p v-else-if="!customerOrderRows.length" class="field-help">
            {{ $t('sicherplan.customerPlansWizard.forms.noExistingOrdersFound') }}
          </p>
          <div
            v-for="row in customerOrderRows"
            :key="row.id"
            class="sp-customer-plan-wizard-step__list-row"
            :class="{ 'sp-customer-plan-wizard-step__list-row--selected': row.id === selectedExistingOrderId }"
            data-testid="customer-new-plan-existing-order-row"
            @click="selectExistingOrder(row.id)"
          >
            <div>
              <strong>{{ row.order_no }} · {{ row.title }}</strong>
              <span>{{ row.service_from }} - {{ row.service_to }} · {{ row.release_state }} · {{ row.status }}</span>
            </div>
            <button
              type="button"
              class="cta-button cta-secondary"
              data-testid="customer-new-plan-existing-order-edit"
              @click.stop="void editExistingOrder(row.id)"
            >
              {{ $t('sicherplan.customerPlansWizard.actions.edit') }}
            </button>
          </div>
        </div>

        <div v-if="selectedExistingOrderSummary" class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static" data-testid="customer-new-plan-selected-order-summary">
          <strong>{{ $t('sicherplan.customerPlansWizard.forms.selectedOrder') }}: {{ selectedExistingOrderSummary.order_no }} · {{ selectedExistingOrderSummary.title }}</strong>
          <span>{{ selectedExistingOrderSummary.service_from }} - {{ selectedExistingOrderSummary.service_to }}</span>
        </div>
      </template>

      <p
        v-if="orderModeUsesExisting && !selectedExistingOrderId && !customerOrderRowsLoading && !customerOrderRowsError"
        class="field-help"
      >
        {{ $t('sicherplan.customerPlansWizard.forms.selectExistingOrder') }}
      </p>

      <div
        v-if="orderSelectionMode === 'create_new' || existingOrderEditActive"
        :data-testid="existingOrderEditActive ? 'customer-new-plan-existing-order-edit-form' : undefined"
      >
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.customer') }}</span>
            <input :value="props.customer.name || props.customer.id" readonly />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.orderNo') }}</span>
            <input v-model="orderDraft.order_no" data-testid="customer-new-plan-order-no" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.orderTitle') }}</span>
            <input v-model="orderDraft.title" data-testid="customer-new-plan-order-title" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.requirementType') }}</span>
            <select v-model="orderDraft.requirement_type_id" data-testid="customer-new-plan-order-requirement-type">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.requirementTypePlaceholder') }}</option>
              <option v-for="option in requirementTypeSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.patrolRoute') }}</span>
            <select v-model="orderDraft.patrol_route_id">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.patrolRoutePlaceholder') }}</option>
              <option v-for="option in patrolRouteSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.serviceCategory') }}</span>
            <select v-model="orderDraft.service_category_code" data-testid="customer-new-plan-order-service-category">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.serviceCategoryPlaceholder') }}</option>
              <option v-for="option in serviceCategorySelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.serviceFrom') }}</span>
            <input v-model="orderDraft.service_from" data-testid="customer-new-plan-order-service-from" type="date" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.serviceTo') }}</span>
            <input v-model="orderDraft.service_to" data-testid="customer-new-plan-order-service-to" type="date" />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.securityConcept') }}</span>
            <textarea
              v-model="orderDraft.security_concept_text"
              data-testid="customer-new-plan-order-security-concept"
              rows="3"
            />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
            <textarea v-model="orderDraft.notes" data-testid="customer-new-plan-order-notes" rows="3" />
          </label>
        </div>
        <div v-if="existingOrderEditActive" class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-existing-order-update"
            :disabled="stepLoading"
            @click="void updateExistingOrder()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.updateOrder') }}
          </button>
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-existing-order-cancel-edit"
            :disabled="stepLoading"
            @click="cancelExistingOrderEdit()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.cancelEdit') }}
          </button>
        </div>
      </div>
    </section>

    <section v-else-if="equipmentStepActive" class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-equipment-lines">
      <div class="cta-row">
        <button
          type="button"
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-new-equipment"
          @click="equipmentModal.open = true"
        >
          {{ $t('sicherplan.customerPlansWizard.forms.newEquipment') }}
        </button>
      </div>
      <div v-if="orderEquipmentLines.length" class="sp-customer-plan-wizard-step__list">
        <button
          v-for="line in orderEquipmentLines"
          :key="line.id"
          type="button"
          class="sp-customer-plan-wizard-step__list-row"
          :class="{ 'sp-customer-plan-wizard-step__list-row--selected': line.id === selectedEquipmentLineId }"
          @click="syncEquipmentLineDraft(line)"
        >
          <strong>{{ equipmentItemSelectOptions.find((option) => option.value === line.equipment_item_id)?.label || line.equipment_item_id }}</strong>
          <span>{{ line.required_qty }}</span>
        </button>
      </div>
      <div class="sp-customer-plan-wizard-step__grid">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.equipmentItem') }}</span>
          <select v-model="equipmentLineDraft.equipment_item_id" data-testid="customer-new-plan-equipment-item">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.equipmentItemPlaceholder') }}</option>
            <option v-for="option in equipmentItemSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.requiredQty') }}</span>
          <input v-model.number="equipmentLineDraft.required_qty" data-testid="customer-new-plan-equipment-required-qty" min="1" type="number" />
        </label>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="equipmentLineDraft.notes" data-testid="customer-new-plan-equipment-notes" rows="2" />
        </label>
      </div>
      <p v-if="selectedEquipmentLineId" class="field-help" data-testid="customer-new-plan-equipment-editing">
        {{ $t('sicherplan.customerPlansWizard.forms.editingEquipmentLine') }}
      </p>
      <div class="cta-row">
        <button
          v-if="selectedEquipmentLineId"
          type="button"
          class="cta-button"
          data-testid="customer-new-plan-update-equipment-line"
          :disabled="stepLoading"
          @click="void saveEquipmentLineDraft()"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.updateEquipmentLine') }}
        </button>
        <button
          v-else
          type="button"
          class="cta-button"
          data-testid="customer-new-plan-save-equipment-line"
          :disabled="stepLoading"
          @click="void saveEquipmentLineDraft()"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.saveEquipmentLine') }}
        </button>
        <button
          type="button"
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-clear-equipment-line"
          :disabled="stepLoading"
          @click="clearEquipmentLineDraftState"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.clearEquipmentLine') }}
        </button>
      </div>
    </section>

    <section v-else-if="requirementStepActive" class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-requirement-lines">
      <div class="cta-row">
        <button
          type="button"
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-new-requirement"
          @click="requirementModal.open = true"
        >
          {{ $t('sicherplan.customerPlansWizard.forms.newRequirement') }}
        </button>
      </div>
      <div v-if="orderRequirementLines.length" class="sp-customer-plan-wizard-step__list">
        <button
          v-for="line in orderRequirementLines"
          :key="line.id"
          type="button"
          class="sp-customer-plan-wizard-step__list-row"
          :class="{ 'sp-customer-plan-wizard-step__list-row--selected': line.id === selectedRequirementLineId }"
          @click="syncRequirementLineDraft(line)"
        >
          <strong>{{ requirementTypeSelectOptions.find((option) => option.value === line.requirement_type_id)?.label || line.requirement_type_id }}</strong>
          <span>{{ line.min_qty }} / {{ line.target_qty }}</span>
        </button>
      </div>
      <div class="sp-customer-plan-wizard-step__grid">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.requirementType') }}</span>
          <select v-model="requirementLineDraft.requirement_type_id" data-testid="customer-new-plan-requirement-type">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.requirementTypePlaceholder') }}</option>
            <option v-for="option in requirementTypeSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.functionType') }}</span>
          <select v-model="requirementLineDraft.function_type_id" data-testid="customer-new-plan-requirement-function-type">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.functionTypePlaceholder') }}</option>
            <option v-for="option in functionTypeSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.qualificationType') }}</span>
          <select v-model="requirementLineDraft.qualification_type_id" data-testid="customer-new-plan-requirement-qualification-type">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.qualificationTypePlaceholder') }}</option>
            <option v-for="option in qualificationTypeSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.minQty') }}</span>
          <input v-model.number="requirementLineDraft.min_qty" data-testid="customer-new-plan-requirement-min-qty" min="0" type="number" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.targetQty') }}</span>
          <input v-model.number="requirementLineDraft.target_qty" data-testid="customer-new-plan-requirement-target-qty" min="0" type="number" />
        </label>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="requirementLineDraft.notes" data-testid="customer-new-plan-requirement-notes" rows="2" />
        </label>
      </div>
      <p v-if="selectedRequirementLineId" class="field-help" data-testid="customer-new-plan-requirement-editing">
        {{ $t('sicherplan.customerPlansWizard.forms.editingRequirementLine') }}
      </p>
      <div class="cta-row">
        <button
          v-if="selectedRequirementLineId"
          type="button"
          class="cta-button"
          data-testid="customer-new-plan-update-requirement-line"
          :disabled="stepLoading"
          @click="void saveRequirementLineDraft()"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.updateRequirementLine') }}
        </button>
        <button
          v-else
          type="button"
          class="cta-button"
          data-testid="customer-new-plan-save-requirement-line"
          :disabled="stepLoading"
          @click="void saveRequirementLineDraft()"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.saveRequirementLine') }}
        </button>
        <button
          type="button"
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-clear-requirement-line"
          :disabled="stepLoading"
          @click="clearRequirementLineDraftState"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.clearRequirementLine') }}
        </button>
      </div>
    </section>

    <section v-else-if="documentsStepActive" class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-order-documents">
      <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.orderDocumentsOptional') }}</p>
      <div v-if="orderAttachments.length" class="sp-customer-plan-wizard-step__list" data-testid="customer-new-plan-order-document-list">
        <div v-for="document in orderAttachments" :key="document.id" class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static">
          <strong>{{ document.title }}</strong>
          <span>{{ document.id }}<template v-if="document.status"> · {{ document.status }}</template><template v-if="document.current_version_no"> · v{{ document.current_version_no }}</template></span>
        </div>
      </div>
      <section class="sp-customer-plan-wizard-step__panel">
        <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.uploadNewDocument') }}</strong></p>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.uploadNewDocumentHelp') }}</p>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.documentTitle') }}</span>
            <input v-model="orderAttachmentDraft.title" data-testid="customer-new-plan-order-document-upload-title" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.uploadLabel') }}</span>
            <input v-model="orderAttachmentDraft.label" data-testid="customer-new-plan-order-document-upload-label" />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.documentFile') }}</span>
            <input data-testid="customer-new-plan-order-document-file" type="file" @change="onOrderAttachmentSelected" />
          </label>
        </div>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-attach-order-document"
            :disabled="stepLoading"
            @click="void attachUploadedOrderDocument()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.attachUploadedDocument') }}
          </button>
        </div>
      </section>
      <section class="sp-customer-plan-wizard-step__panel">
        <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.linkExistingDocument') }}</strong></p>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.linkExistingDocumentHelp') }}</p>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.existingDocumentId') }}</span>
            <input v-model="orderAttachmentLink.document_id" data-testid="customer-new-plan-order-document-link-id" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.linkLabel') }}</span>
            <input v-model="orderAttachmentLink.label" data-testid="customer-new-plan-order-document-link-label" />
          </label>
        </div>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-link-order-document"
            :disabled="stepLoading"
            @click="void linkExistingOrderDocument()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.linkExistingDocument') }}
          </button>
        </div>
      </section>
      <div v-if="hasAnyOrderDocumentDraftInput()" class="cta-row">
        <button
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-clear-order-document-draft"
          type="button"
          :disabled="stepLoading"
          @click="clearOrderDocumentDraftState"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.clearOrderDocumentDraft') }}
        </button>
      </div>
    </section>

    <section
      v-else-if="planningRecordStepActive"
      class="sp-customer-plan-wizard-step__panel"
      data-testid="customer-new-plan-step-panel-planning-record-overview"
    >
      <section class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-planning-context-panel">
        <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.planningContext') }}</strong></p>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.selectPlanningContext') }}</p>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.planningModeCode') }}</span>
            <select
              :value="planningFamily"
              data-testid="customer-new-plan-planning-context-family"
              @change="onPlanningFamilyChange"
            >
              <option v-for="option in planningFamilyOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
        </div>
        <div class="sp-customer-plan-wizard-step__toggle-row">
          <label class="planning-admin-checkbox" data-testid="customer-new-plan-planning-context-existing-label">
            <input
              v-model="planningSelectionModeModel"
              data-testid="customer-new-plan-planning-context-use-existing"
              type="radio"
              value="use_existing"
            />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.useExistingPlanningEntry') }}</span>
          </label>
          <label class="planning-admin-checkbox" data-testid="customer-new-plan-planning-context-create-label">
            <input
              v-model="planningSelectionModeModel"
              data-testid="customer-new-plan-planning-context-create-new"
              type="radio"
              value="create_new"
            />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.createNewPlanningEntry') }}</span>
          </label>
        </div>
        <template v-if="planningModeUsesExisting">
          <p v-if="planningEntityLoading" class="field-help">{{ $t('sicherplan.customerPlansWizard.loadingBody') }}</p>
          <p v-else-if="planningEntityError" class="field-help">{{ planningEntityError }}</p>
          <template v-else-if="planningEntityOptions.length">
            <div class="sp-customer-plan-wizard-step__list" data-testid="customer-new-plan-planning-context-list">
              <button
                v-for="row in planningEntityOptions"
                :key="row.id"
                type="button"
                class="sp-customer-plan-wizard-step__list-row"
                :class="{ 'sp-customer-plan-wizard-step__list-row--selected': row.id === planningEntityId }"
                data-testid="customer-new-plan-planning-context-row"
                @click="void selectExistingPlanningEntity(row.id)"
              >
                <strong>{{ row.name || row.label || row.code || row.id }}</strong>
                <span>{{ row.code || row.id }}</span>
              </button>
            </div>
          </template>
          <div v-else data-testid="customer-new-plan-planning-context-empty">
            <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.noPlanningEntriesFoundForCustomer') }}</p>
            <div class="cta-row">
              <button
                type="button"
                class="cta-button"
                data-testid="customer-new-plan-planning-context-create-button"
                @click="openPlanningCreateModal()"
              >
                {{ $t('sicherplan.customerPlansWizard.forms.createNewPlanningEntry') }}
              </button>
            </div>
          </div>
        </template>
        <div v-else class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-planning-context-create-button"
            @click="openPlanningCreateModal()"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.createNewPlanningEntry') }}
          </button>
        </div>
      </section>
      <section
        v-if="hasPlanningContext"
        class="sp-customer-plan-wizard-step__panel"
        data-testid="customer-new-plan-existing-planning-records"
      >
        <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.existingPlanningRecords') }}</strong></p>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.existingPlanningRecordsHelp') }}</p>
        <p v-if="planningRecordRowsLoading" class="field-help">{{ $t('sicherplan.customerPlansWizard.loadingBody') }}</p>
        <p v-else-if="planningRecordRowsError" class="field-help">{{ planningRecordRowsError }}</p>
        <div v-else-if="planningRecordRows.length" class="sp-customer-plan-wizard-step__list">
          <button
            v-for="row in planningRecordRows"
            :key="row.id"
            type="button"
            class="sp-customer-plan-wizard-step__list-row"
            :class="{ 'sp-customer-plan-wizard-step__list-row--selected': row.id === selectedPlanningRecord?.id }"
            data-testid="customer-new-plan-existing-planning-record-row"
            @click="void selectExistingPlanningRecordRow(row.id)"
          >
            <strong>{{ row.name }}</strong>
            <span>{{ row.planning_from }} - {{ row.planning_to }}</span>
          </button>
        </div>
        <p v-else class="field-help" data-testid="customer-new-plan-existing-planning-records-empty">
          {{ $t('sicherplan.customerPlansWizard.forms.noPlanningRecordsFoundForContext') }}
        </p>
      </section>
      <div v-if="hasPlanningContext" class="sp-customer-plan-wizard-step__grid" data-testid="customer-new-plan-planning-record-details">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.orderTitle') }}</span>
          <input :value="selectedOrder?.title || orderDraft.title" readonly />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.planningModeCode') }}</span>
          <input :value="planningModeLabel" readonly />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.planningEntity') }}</span>
          <input :value="planningEntitySummaryLabel()" readonly />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.name') }}</span>
          <input v-model="planningRecordDraft.name" data-testid="customer-new-plan-planning-record-name" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.startDate') }}</span>
          <input v-model="planningRecordDraft.planning_from" data-testid="customer-new-plan-planning-record-from" type="date" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.endDate') }}</span>
          <input v-model="planningRecordDraft.planning_to" data-testid="customer-new-plan-planning-record-to" type="date" />
        </label>
        <label v-if="planningModeCode === 'event'" class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.setupNote') }}</span>
          <textarea v-model="planningRecordDraft.event_detail_setup_note" rows="2" />
        </label>
        <label v-else-if="planningModeCode === 'site'" class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.watchbookScopeNote') }}</span>
          <textarea v-model="planningRecordDraft.site_detail_watchbook_scope_note" rows="2" />
        </label>
        <label v-else-if="planningModeCode === 'trade_fair'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.tradeFairZoneId') }}</span>
          <select v-model="planningRecordDraft.trade_fair_detail_trade_fair_zone_id" data-testid="customer-new-plan-trade-fair-zone">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.tradeFairZonePlaceholder') }}</option>
            <option v-for="option in tradeFairZoneSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <p v-if="tradeFairZoneLookupError" class="field-help">{{ tradeFairZoneLookupError }}</p>
          <p v-else-if="tradeFairZoneLookupLoading" class="field-help">{{ $t('sicherplan.customerPlansWizard.loadingBody') }}</p>
        </label>
        <label v-if="planningModeCode === 'trade_fair'" class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.standNote') }}</span>
          <textarea v-model="planningRecordDraft.trade_fair_detail_stand_note" rows="2" />
        </label>
        <label v-if="planningModeCode === 'patrol'" class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.executionNote') }}</span>
          <textarea v-model="planningRecordDraft.patrol_detail_execution_note" rows="2" />
        </label>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="planningRecordDraft.notes" rows="3" />
        </label>
      </div>
    </section>

    <section
      v-else-if="planningRecordDocumentsStepActive"
      class="sp-customer-plan-wizard-step__panel"
      data-testid="customer-new-plan-step-panel-planning-record-documents"
    >
      <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.planningDocumentsOptional') }}</p>
      <div v-if="planningRecordAttachments.length" class="sp-customer-plan-wizard-step__list">
        <div
          v-for="document in planningRecordAttachments"
          :key="document.id"
          class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static"
        >
          <strong>{{ document.title }}</strong>
          <span>{{ document.id }}</span>
        </div>
      </div>
      <div class="sp-customer-plan-wizard-step__grid">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.documentTitle') }}</span>
          <input v-model="planningRecordAttachmentDraft.title" data-testid="customer-new-plan-planning-record-document-title" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.documentLabel') }}</span>
          <input v-model="planningRecordAttachmentDraft.label" data-testid="customer-new-plan-planning-record-document-label" />
        </label>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.documentFile') }}</span>
          <input data-testid="customer-new-plan-planning-record-document-file" type="file" @change="onPlanningRecordAttachmentSelected" />
        </label>
      </div>
      <div class="sp-customer-plan-wizard-step__divider"></div>
      <div class="sp-customer-plan-wizard-step__grid">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.documentId') }}</span>
          <input v-model="planningRecordAttachmentLink.document_id" data-testid="customer-new-plan-planning-record-document-id" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.documentLabel') }}</span>
          <input v-model="planningRecordAttachmentLink.label" data-testid="customer-new-plan-planning-record-document-link-label" />
        </label>
      </div>
      <div v-if="hasPlanningRecordAttachmentDraftContent()" class="cta-row">
        <button
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-clear-planning-document-draft"
          type="button"
          :disabled="stepLoading"
          @click="clearPlanningRecordDocumentDraftState"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.clearPlanningDocumentDraft') }}
        </button>
      </div>
    </section>

    <section v-else-if="shiftPlanStepActive" class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-shift-plan">
      <div v-if="shiftPlanRows.length" class="cta-row">
        <button
          type="button"
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-create-new-shift-plan"
          @click="startNewShiftPlan"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.createNewShiftPlan') }}
        </button>
      </div>
      <div
        v-if="shiftPlanRows.length"
        class="sp-customer-plan-wizard-step__list"
        data-testid="customer-new-plan-existing-shift-plan-list"
      >
        <button
          v-for="row in shiftPlanRows"
          :key="row.id"
          type="button"
          class="sp-customer-plan-wizard-step__list-row"
          :class="{ 'sp-customer-plan-wizard-step__list-row--selected': row.id === selectedShiftPlan?.id }"
          data-testid="customer-new-plan-existing-shift-plan-row"
          @click="selectShiftPlanRow(row.id)"
        >
          <strong>{{ row.name }}</strong>
          <span>{{ row.planning_from }} - {{ row.planning_to }}</span>
        </button>
      </div>
      <div
        v-if="selectedShiftPlanSummary"
        class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static"
        data-testid="customer-new-plan-selected-shift-plan-summary"
      >
        <strong>{{ $t('sicherplan.customerPlansWizard.forms.selectedShiftPlan') }}: {{ selectedShiftPlanSummary.name }}</strong>
        <span>{{ selectedShiftPlanSummary.planning_from }} - {{ selectedShiftPlanSummary.planning_to }}</span>
      </div>
      <div class="sp-customer-plan-wizard-step__grid">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.planningRecord') }}</span>
          <input :value="selectedPlanningRecord?.name || props.wizardState.planning_record_id" readonly />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.name') }}</span>
          <input v-model="shiftPlanDraft.name" data-testid="customer-new-plan-shift-plan-name" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.workforceScope') }}</span>
          <select v-model="shiftPlanDraft.workforce_scope_code">
            <option value="internal">{{ $t('sicherplan.customerPlansWizard.forms.workforceInternal') }}</option>
            <option value="subcontractor">{{ $t('sicherplan.customerPlansWizard.forms.workforceSubcontractor') }}</option>
            <option value="mixed">{{ $t('sicherplan.customerPlansWizard.forms.workforceMixed') }}</option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.startDate') }}</span>
          <input
            v-model="shiftPlanDraft.planning_from"
            :max="selectedPlanningRecord?.planning_to || undefined"
            :min="selectedPlanningRecord?.planning_from || undefined"
            data-testid="customer-new-plan-shift-plan-from"
            type="date"
          />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.endDate') }}</span>
          <input
            v-model="shiftPlanDraft.planning_to"
            :max="selectedPlanningRecord?.planning_to || undefined"
            :min="selectedPlanningRecord?.planning_from || undefined"
            data-testid="customer-new-plan-shift-plan-to"
            type="date"
          />
        </label>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="shiftPlanDraft.remarks" rows="2" />
        </label>
      </div>
    </section>

    <section v-else-if="seriesStepActive" class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-series-exceptions">
      <div class="cta-row">
        <button
          type="button"
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-new-template"
          @click="templateModal.open = true"
        >
          {{ $t('sicherplan.customerPlansWizard.forms.newTemplate') }}
        </button>
      </div>
      <div v-if="seriesRows.length" class="sp-customer-plan-wizard-step__list">
        <button
          v-for="row in seriesRows"
          :key="row.id"
          type="button"
          class="sp-customer-plan-wizard-step__list-row"
          @click="selectSeriesRow(row.id)"
        >
          <strong>{{ row.label }}</strong>
          <span>{{ row.date_from }} - {{ row.date_to }}</span>
        </button>
      </div>
      <div class="sp-customer-plan-wizard-step__grid">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.label') }}</span>
          <input v-model="seriesDraft.label" data-testid="customer-new-plan-series-label" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.shiftTemplate') }}</span>
          <select v-model="seriesDraft.shift_template_id" data-testid="customer-new-plan-series-template">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.shiftTemplatePlaceholder') }}</option>
            <option v-for="option in shiftTemplateSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.shiftType') }}</span>
          <select v-model="seriesDraft.shift_type_code">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.shiftTypePlaceholder') }}</option>
            <option v-for="option in shiftTypeSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.recurrenceCode') }}</span>
          <select v-model="seriesDraft.recurrence_code">
            <option value="daily">{{ $t('sicherplan.customerPlansWizard.forms.recurrenceDaily') }}</option>
            <option value="weekly">{{ $t('sicherplan.customerPlansWizard.forms.recurrenceWeekly') }}</option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.intervalCount') }}</span>
          <input v-model.number="seriesDraft.interval_count" min="1" type="number" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.weekdayMask') }}</span>
          <input v-model="seriesDraft.weekday_mask" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.startDate') }}</span>
          <input v-model="seriesDraft.date_from" data-testid="customer-new-plan-series-from" type="date" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.endDate') }}</span>
          <input v-model="seriesDraft.date_to" data-testid="customer-new-plan-series-to" type="date" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.defaultBreakMinutes') }}</span>
          <input v-model.number="seriesDraft.default_break_minutes" min="0" type="number" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.meetingPoint') }}</span>
          <input v-model="seriesDraft.meeting_point" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.locationText') }}</span>
          <input v-model="seriesDraft.location_text" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.releaseState') }}</span>
          <select v-model="seriesDraft.release_state">
            <option value="draft">{{ $t('sicherplan.customerPlansWizard.forms.releaseStateDraft') }}</option>
            <option value="release_ready">{{ $t('sicherplan.customerPlansWizard.forms.releaseStateReady') }}</option>
            <option value="released">{{ $t('sicherplan.customerPlansWizard.forms.releaseStateReleased') }}</option>
          </select>
        </label>
        <label class="planning-admin-checkbox">
          <input v-model="seriesDraft.customer_visible_flag" type="checkbox" />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.customerVisible') }}</span>
        </label>
        <label class="planning-admin-checkbox">
          <input v-model="seriesDraft.subcontractor_visible_flag" type="checkbox" />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.subcontractorVisible') }}</span>
        </label>
        <label class="planning-admin-checkbox">
          <input v-model="seriesDraft.stealth_mode_flag" type="checkbox" />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.stealthMode') }}</span>
        </label>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="seriesDraft.notes" rows="2" />
        </label>
      </div>
      <div class="sp-customer-plan-wizard-step__divider"></div>
      <div v-if="seriesExceptions.length" class="sp-customer-plan-wizard-step__list">
        <button
          v-for="row in seriesExceptions"
          :key="row.id"
          type="button"
          class="sp-customer-plan-wizard-step__list-row"
          @click="syncExceptionDraft(row)"
        >
          <strong>{{ row.exception_date }}</strong>
          <span>{{ row.action_code }}</span>
        </button>
      </div>
      <div class="sp-customer-plan-wizard-step__grid">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.exceptionDate') }}</span>
          <input v-model="exceptionDraft.exception_date" data-testid="customer-new-plan-series-exception-date" type="date" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.actionCode') }}</span>
          <select v-model="exceptionDraft.action_code">
            <option value="skip">{{ $t('sicherplan.customerPlansWizard.forms.exceptionActionSkip') }}</option>
            <option value="override">{{ $t('sicherplan.customerPlansWizard.forms.exceptionActionOverride') }}</option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideStartTime') }}</span>
          <input v-model="exceptionDraft.override_local_start_time" type="time" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideEndTime') }}</span>
          <input v-model="exceptionDraft.override_local_end_time" type="time" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideBreakMinutes') }}</span>
          <input v-model="exceptionDraft.override_break_minutes" min="0" type="number" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideShiftType') }}</span>
          <select v-model="exceptionDraft.override_shift_type_code">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.shiftTypePlaceholder') }}</option>
            <option v-for="option in shiftTypeSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideMeetingPoint') }}</span>
          <input v-model="exceptionDraft.override_meeting_point" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideLocationText') }}</span>
          <input v-model="exceptionDraft.override_location_text" />
        </label>
        <label class="planning-admin-checkbox">
          <input
            :checked="Boolean(exceptionDraft.customer_visible_flag)"
            type="checkbox"
            @change="setExceptionCustomerVisible"
          />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.customerVisible') }}</span>
        </label>
        <label class="planning-admin-checkbox">
          <input
            :checked="Boolean(exceptionDraft.subcontractor_visible_flag)"
            type="checkbox"
            @change="setExceptionSubcontractorVisible"
          />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.subcontractorVisible') }}</span>
        </label>
        <label class="planning-admin-checkbox">
          <input
            :checked="Boolean(exceptionDraft.stealth_mode_flag)"
            type="checkbox"
            @change="setExceptionStealthMode"
          />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.stealthMode') }}</span>
        </label>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="exceptionDraft.notes" rows="2" />
        </label>
      </div>
    </section>

    <section v-else class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-placeholder">
      <p>{{ $t('sicherplan.customerPlansWizard.stepLead') }}</p>
      <p>{{ $t('sicherplan.customerPlansWizard.stepContentBody') }}</p>
    </section>

    <Modal
      v-model:open="planningCreateModal.open"
      :confirm-loading="planningCreateModal.saving"
      :title="$t('sicherplan.customerPlansWizard.dialogs.planningCreateTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @ok="submitPlanningCreateModal"
      @cancel="resetPlanningCreateModal"
    >
      <div class="sp-customer-plan-wizard-step__modal">
        <label v-if="planningFamily === 'site'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.siteNo') }}</span>
          <input v-model="planningCreateModal.site_no" data-testid="customer-new-plan-planning-create-site-no" />
        </label>
        <label v-if="planningFamily === 'event_venue'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.venueNo') }}</span>
          <input v-model="planningCreateModal.venue_no" data-testid="customer-new-plan-planning-create-venue-no" />
        </label>
        <label v-if="planningFamily === 'trade_fair'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.fairNo') }}</span>
          <input v-model="planningCreateModal.fair_no" data-testid="customer-new-plan-planning-create-fair-no" />
        </label>
        <label v-if="planningFamily === 'patrol_route'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.routeNo') }}</span>
          <input v-model="planningCreateModal.route_no" data-testid="customer-new-plan-planning-create-route-no" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.name') }}</span>
          <input v-model="planningCreateModal.name" data-testid="customer-new-plan-planning-create-name" />
        </label>
        <label v-if="planningFamily === 'trade_fair'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.venueId') }}</span>
          <select v-model="planningCreateModal.venue_id" data-testid="customer-new-plan-planning-create-venue-id">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.none') }}</option>
            <option v-for="option in eventVenueSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label v-if="planningFamily === 'patrol_route'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.siteId') }}</span>
          <select v-model="planningCreateModal.site_id" data-testid="customer-new-plan-planning-create-site-id">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.none') }}</option>
            <option v-for="option in siteSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label v-if="planningFamily === 'site' || planningFamily === 'event_venue' || planningFamily === 'trade_fair'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.addressId') }}</span>
          <select v-model="planningCreateModal.address_id" data-testid="customer-new-plan-planning-create-address-id">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.none') }}</option>
            <option v-for="option in planningCreateAddressSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label v-if="planningFamily === 'patrol_route'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.meetingAddressId') }}</span>
          <select v-model="planningCreateModal.meeting_address_id" data-testid="customer-new-plan-planning-create-meeting-address-id">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.none') }}</option>
            <option v-for="option in planningCreateAddressSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <div v-if="planningCreateHasAddressField" class="cta-row">
          <button
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-planning-create-address-action"
            type="button"
            :disabled="planningCreateAddressLookupLoading"
            @click="openPlanningAddressCreateModal"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.createAddress') }}
          </button>
          <span class="field-help">{{ $t('sicherplan.customerPlansWizard.addressModal.helper') }}</span>
        </div>
        <label v-if="planningFamily === 'site' || planningFamily === 'event_venue' || planningFamily === 'trade_fair'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.timezone') }}</span>
          <select v-model="planningCreateModal.timezone" data-testid="customer-new-plan-planning-create-timezone">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.none') }}</option>
            <option v-for="option in timezoneOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label v-if="planningFamily === 'site' || planningFamily === 'event_venue' || planningFamily === 'trade_fair'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.latitude') }}</span>
          <input v-model="planningCreateModal.latitude" data-testid="customer-new-plan-planning-create-latitude" type="number" step="0.000001" />
        </label>
        <label v-if="planningFamily === 'site' || planningFamily === 'event_venue' || planningFamily === 'trade_fair'" class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.longitude') }}</span>
          <input v-model="planningCreateModal.longitude" data-testid="customer-new-plan-planning-create-longitude" type="number" step="0.000001" />
        </label>
        <div v-if="planningCreateSupportsLocationPicker" class="cta-row">
          <button
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-planning-create-pick-on-map"
            type="button"
            @click="openPlanningLocationPicker"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.pickOnMap') }}
          </button>
          <span class="field-help">{{ $t('sicherplan.customerPlansWizard.mapPicker.helper') }}</span>
        </div>
        <label v-if="planningFamily === 'site'" class="planning-admin-checkbox">
          <input v-model="planningCreateModal.watchbook_enabled" data-testid="customer-new-plan-planning-create-watchbook-enabled" type="checkbox" />
          <span>{{ $t('sicherplan.customerPlansWizard.forms.watchbookEnabled') }}</span>
        </label>
        <template v-if="planningFamily === 'trade_fair'">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.startDate') }}</span>
            <input v-model="planningCreateModal.start_date" data-testid="customer-new-plan-planning-create-start-date" type="date" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.endDate') }}</span>
            <input v-model="planningCreateModal.end_date" data-testid="customer-new-plan-planning-create-end-date" type="date" />
          </label>
        </template>
        <template v-if="planningFamily === 'patrol_route'">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.startPointText') }}</span>
            <input v-model="planningCreateModal.start_point_text" data-testid="customer-new-plan-planning-create-start-point" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.endPointText') }}</span>
            <input v-model="planningCreateModal.end_point_text" data-testid="customer-new-plan-planning-create-end-point" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.travelPolicyCode') }}</span>
            <input v-model="planningCreateModal.travel_policy_code" data-testid="customer-new-plan-planning-create-travel-policy-code" />
          </label>
        </template>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.status') }}</span>
          <select v-model="planningCreateModal.status" data-testid="customer-new-plan-planning-create-status">
            <option value="active">{{ $t('sicherplan.customerPlansWizard.forms.statusActive') }}</option>
            <option value="inactive">{{ $t('sicherplan.customerPlansWizard.forms.statusInactive') }}</option>
            <option value="archived">{{ $t('sicherplan.customerPlansWizard.forms.statusArchived') }}</option>
          </select>
        </label>
        <p v-if="planningCreateAddressLookupError" class="field-help">{{ planningCreateAddressLookupError }}</p>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="planningCreateModal.notes" data-testid="customer-new-plan-planning-create-notes" rows="3" />
        </label>
      </div>
    </Modal>

    <Modal
      v-model:open="planningAddressCreateModal.open"
      :footer="null"
      :title="$t('sicherplan.customerPlansWizard.addressModal.title')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @cancel="closePlanningAddressCreateModal"
    >
      <div class="sp-customer-plan-wizard-step__modal" data-testid="customer-new-plan-planning-address-dialog">
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.addressModal.helper') }}</p>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.addressModal.streetLine1') }}</span>
          <input v-model="planningAddressCreateModal.street_line_1" data-testid="customer-new-plan-planning-address-street-line-1" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.addressModal.streetLine2') }}</span>
          <input v-model="planningAddressCreateModal.street_line_2" data-testid="customer-new-plan-planning-address-street-line-2" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.addressModal.postalCode') }}</span>
          <input v-model="planningAddressCreateModal.postal_code" data-testid="customer-new-plan-planning-address-postal-code" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.addressModal.city') }}</span>
          <input v-model="planningAddressCreateModal.city" data-testid="customer-new-plan-planning-address-city" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.addressModal.state') }}</span>
          <input v-model="planningAddressCreateModal.state" data-testid="customer-new-plan-planning-address-state" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.addressModal.countryCode') }}</span>
          <input v-model="planningAddressCreateModal.country_code" data-testid="customer-new-plan-planning-address-country-code" maxlength="2" />
        </label>
        <p v-if="planningAddressCreateModal.error" class="field-help">{{ planningAddressCreateModal.error }}</p>
        <div class="cta-row">
          <button
            class="cta-button"
            data-testid="customer-new-plan-planning-address-save"
            type="button"
            :disabled="planningAddressCreateModal.saving"
            @click="submitPlanningAddressCreateModal"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.saveAddress') }}
          </button>
          <button
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-planning-address-cancel"
            type="button"
            :disabled="planningAddressCreateModal.saving"
            @click="closePlanningAddressCreateModal"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.cancelAddress') }}
          </button>
        </div>
      </div>
    </Modal>

    <PlanningLocationPickerModal
      v-model:open="planningLocationPickerOpen"
      :latitude="planningLocationPickerLatitude"
      :longitude="planningLocationPickerLongitude"
      :initial-center="planningLocationPickerStartPoint"
      :start-point-label="planningLocationPickerStartPoint.label"
      :title="$t('sicherplan.customerPlansWizard.mapPicker.title')"
      :confirm-text="$t('sicherplan.customerPlansWizard.mapPicker.apply')"
      :cancel-text="$t('sicherplan.customerPlansWizard.mapPicker.cancel')"
      :helper-text="$t('sicherplan.customerPlansWizard.mapPicker.helper')"
      :latitude-label="$t('sicherplan.customerPlansWizard.forms.latitude')"
      :longitude-label="$t('sicherplan.customerPlansWizard.forms.longitude')"
      :load-error-text="$t('sicherplan.customerPlansWizard.mapPicker.loadError')"
      @confirm="applyPlanningLocationSelection"
    />

    <Modal
      v-model:open="templateModal.open"
      :confirm-loading="templateModal.saving"
      :title="$t('sicherplan.customerPlansWizard.dialogs.templateTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @ok="submitTemplateModal"
      @cancel="closeTemplateModal"
    >
      <div class="sp-customer-plan-wizard-step__modal" data-testid="customer-new-plan-new-template-dialog">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.code') }}</span>
          <input v-model="templateModal.code" data-testid="customer-new-plan-new-template-code" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.label') }}</span>
          <input v-model="templateModal.label" data-testid="customer-new-plan-new-template-label" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.shiftType') }}</span>
          <select v-model="templateModal.shift_type_code">
            <option value="">{{ $t('sicherplan.customerPlansWizard.forms.shiftTypePlaceholder') }}</option>
            <option v-for="option in shiftTypeSelectOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.startTime') }}</span>
          <input v-model="templateModal.local_start_time" type="time" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.endTime') }}</span>
          <input v-model="templateModal.local_end_time" type="time" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.defaultBreakMinutes') }}</span>
          <input v-model.number="templateModal.default_break_minutes" min="0" type="number" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.meetingPoint') }}</span>
          <input v-model="templateModal.meeting_point" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.locationText') }}</span>
          <input v-model="templateModal.location_text" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="templateModal.notes" rows="3" />
        </label>
      </div>
    </Modal>

    <Modal
      v-model:open="equipmentModal.open"
      :confirm-loading="equipmentModal.saving"
      :title="$t('sicherplan.customerPlansWizard.dialogs.equipmentTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @ok="submitEquipmentModal"
      @cancel="resetEquipmentModal"
    >
      <div class="sp-customer-plan-wizard-step__modal" data-testid="customer-new-plan-new-equipment-dialog">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.code') }}</span>
          <input v-model="equipmentModal.code" data-testid="customer-new-plan-new-equipment-code" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.label') }}</span>
          <input v-model="equipmentModal.label" data-testid="customer-new-plan-new-equipment-label" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.unitOfMeasureCode') }}</span>
          <input v-model="equipmentModal.unit_of_measure_code" data-testid="customer-new-plan-new-equipment-unit" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="equipmentModal.notes" rows="3" />
        </label>
      </div>
    </Modal>

    <Modal
      v-model:open="requirementModal.open"
      :confirm-loading="requirementModal.saving"
      :title="$t('sicherplan.customerPlansWizard.dialogs.requirementTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @ok="submitRequirementModal"
      @cancel="resetRequirementModal"
    >
      <div class="sp-customer-plan-wizard-step__modal" data-testid="customer-new-plan-new-requirement-dialog">
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.code') }}</span>
          <input v-model="requirementModal.code" data-testid="customer-new-plan-new-requirement-code" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.label') }}</span>
          <input v-model="requirementModal.label" data-testid="customer-new-plan-new-requirement-label" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.defaultPlanningModeCode') }}</span>
          <select v-model="requirementModal.default_planning_mode_code">
            <option value="event">{{ $t('sicherplan.customerPlansWizard.forms.planningModeEvent') }}</option>
            <option value="site">{{ $t('sicherplan.customerPlansWizard.forms.planningModeSite') }}</option>
            <option value="trade_fair">{{ $t('sicherplan.customerPlansWizard.forms.planningModeTradeFair') }}</option>
            <option value="patrol">{{ $t('sicherplan.customerPlansWizard.forms.planningModePatrol') }}</option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="requirementModal.notes" rows="3" />
        </label>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.sp-customer-plan-wizard-step {
  display: grid;
  gap: 0.9rem;
}

.sp-customer-plan-wizard-step__panel {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-elevation-sm, 0 10px 30px rgb(15 23 42 / 0.06));
}

.sp-customer-plan-wizard-step__grid {
  display: grid;
  gap: 0.9rem;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  align-items: start;
}

.sp-customer-plan-wizard-step__toggle-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
}

.field-stack {
  display: grid;
  gap: 0.42rem;
  min-width: 0;
  font-size: 0.92rem;
}

.field-stack span {
  color: var(--sp-color-text-secondary);
  font-size: 0.84rem;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.field-stack input,
.field-stack select,
.field-stack textarea {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 0.78rem 0.9rem;
  border-radius: 14px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  color: var(--sp-color-text-primary);
  font: inherit;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease;
}

.field-stack input[type='file'] {
  padding: 0.68rem 0.9rem;
  cursor: pointer;
}

.field-stack textarea {
  min-height: 6.5rem;
  resize: vertical;
}

.field-stack input:focus,
.field-stack select:focus,
.field-stack textarea:focus {
  outline: none;
  border-color: rgb(40 170 170 / 55%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

.field-stack input:disabled,
.field-stack select:disabled,
.field-stack textarea:disabled {
  opacity: 0.72;
  cursor: not-allowed;
  background: color-mix(in srgb, var(--sp-color-surface-page) 72%, var(--sp-color-border-soft));
}

.field-stack--wide {
  grid-column: 1 / -1;
}

.field-help {
  margin: 0;
  color: var(--sp-color-text-secondary);
  font-size: 0.82rem;
  line-height: 1.45;
}

.sp-customer-plan-wizard-step__list {
  display: grid;
  gap: 0.65rem;
}

.sp-customer-plan-wizard-step__list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.8rem 0.9rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-page);
  text-align: left;
  color: var(--sp-color-text-primary);
  transition:
    border-color 0.18s ease,
    transform 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.sp-customer-plan-wizard-step__list-row strong,
.sp-customer-plan-wizard-step__list-row span {
  min-width: 0;
}

.sp-customer-plan-wizard-step__list-row strong {
  font-weight: 700;
}

.sp-customer-plan-wizard-step__list-row span {
  color: var(--sp-color-text-secondary);
  text-align: right;
}

.sp-customer-plan-wizard-step__list-row:not(.sp-customer-plan-wizard-step__list-row--static) {
  cursor: pointer;
}

.sp-customer-plan-wizard-step__list-row:not(.sp-customer-plan-wizard-step__list-row--static):hover,
.sp-customer-plan-wizard-step__list-row:not(.sp-customer-plan-wizard-step__list-row--static):focus-visible {
  border-color: rgb(40 170 170 / 38%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 10%);
  transform: translateY(-1px);
}

.sp-customer-plan-wizard-step__list-row--selected {
  border-color: rgb(40 170 170 / 48%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 12%);
}

.sp-customer-plan-wizard-step__list-row--static {
  align-items: center;
}

.sp-customer-plan-wizard-step__feedback {
  margin: 0;
  padding: 0.8rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--sp-color-border-soft);
}

.sp-customer-plan-wizard-step__feedback[data-tone='error'] {
  border-color: color-mix(in srgb, var(--sp-color-danger) 36%, var(--sp-color-border-soft));
  color: var(--sp-color-danger);
}

.sp-customer-plan-wizard-step__feedback[data-tone='success'] {
  border-color: color-mix(in srgb, var(--sp-color-success) 36%, var(--sp-color-border-soft));
  color: var(--sp-color-success);
}

.sp-customer-plan-wizard-step__divider {
  height: 1px;
  background: var(--sp-color-border-soft);
}

.planning-admin-checkbox {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-width: 0;
  color: var(--sp-color-text-secondary);
}

.planning-admin-checkbox input[type='checkbox'],
.planning-admin-checkbox input[type='radio'] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--sp-color-primary);
  cursor: pointer;
}

.planning-admin-checkbox span {
  font-weight: 500;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
}

.cta-button {
  padding: 0.7rem 1rem;
  border: 0;
  border-radius: 999px;
  background: var(--sp-color-primary);
  color: white;
  cursor: pointer;
  font: inherit;
  transition:
    opacity 0.18s ease,
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease;
}

.cta-button:hover,
.cta-button:focus-visible {
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
  transform: translateY(-1px);
}

.cta-button.cta-secondary {
  border: 1px solid var(--sp-color-border-soft);
  background: transparent;
  color: var(--sp-color-text-primary);
}

.cta-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.sp-customer-plan-wizard-step__modal {
  display: grid;
  gap: 0.85rem;
}

:deep(.sp-customer-plan-wizard-modal .field-stack) {
  display: grid;
  gap: 0.42rem;
  min-width: 0;
  font-size: 0.92rem;
}

:deep(.sp-customer-plan-wizard-modal .field-stack span) {
  color: var(--sp-color-text-secondary);
  font-size: 0.84rem;
  font-weight: 600;
  letter-spacing: 0.01em;
}

:deep(.sp-customer-plan-wizard-modal .field-stack input),
:deep(.sp-customer-plan-wizard-modal .field-stack select),
:deep(.sp-customer-plan-wizard-modal .field-stack textarea) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 0.78rem 0.9rem;
  border-radius: 14px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  color: var(--sp-color-text-primary);
  font: inherit;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease;
}

:deep(.sp-customer-plan-wizard-modal .field-stack textarea) {
  min-height: 6.5rem;
  resize: vertical;
}

:deep(.sp-customer-plan-wizard-modal .field-stack input:focus),
:deep(.sp-customer-plan-wizard-modal .field-stack select:focus),
:deep(.sp-customer-plan-wizard-modal .field-stack textarea:focus) {
  outline: none;
  border-color: rgb(40 170 170 / 55%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

:deep(.sp-customer-plan-wizard-modal .field-stack input:disabled),
:deep(.sp-customer-plan-wizard-modal .field-stack select:disabled),
:deep(.sp-customer-plan-wizard-modal .field-stack textarea:disabled) {
  opacity: 0.72;
  cursor: not-allowed;
  background: color-mix(in srgb, var(--sp-color-surface-page) 72%, var(--sp-color-border-soft));
}

@media (max-width: 960px) {
  .sp-customer-plan-wizard-step__grid {
    grid-template-columns: 1fr;
  }

  .field-stack--wide {
    grid-column: auto;
  }

  .sp-customer-plan-wizard-step__list-row {
    flex-direction: column;
    align-items: start;
  }

  .sp-customer-plan-wizard-step__list-row span {
    text-align: left;
  }
}
</style>
