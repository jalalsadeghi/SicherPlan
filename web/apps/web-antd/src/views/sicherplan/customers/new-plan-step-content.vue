<script setup lang="ts">
import { IconifyIcon } from '@vben/icons';
import type { CSSProperties } from 'vue';
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { Modal } from 'ant-design-vue';

import { $t } from '#/locales';
import LocalLoadingIndicator from '#/components/sicherplan/local-loading-indicator.vue';
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
  deleteOrderEquipmentLine,
  deleteOrderRequirementLine,
  getCustomerOrder,
  listCustomerOrders,
  getPlanningRecord,
  linkPlanningRecordAttachment,
  linkOrderAttachment,
  listDocuments,
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
  unlinkOrderAttachment,
  unlinkPlanningRecordAttachment,
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
import { useSicherPlanFeedback } from '#/sicherplan-legacy/composables/useSicherPlanFeedback';
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
  deleteShiftSeriesException,
  generateShiftSeries,
  getShiftPlan,
  getShiftSeries,
  getShiftTemplate,
  listShiftPlans,
  listShifts,
  listShiftSeries,
  listShiftSeriesExceptions,
  listShiftTemplates,
  listShiftTypeOptions,
  PlanningShiftsApiError,
  updateShiftPlan,
  updateShiftSeries,
  updateShiftSeriesException,
  type ShiftPlanListItem,
  type ShiftPlanRead,
  type ShiftListItem,
  type ShiftSeriesExceptionRead,
  type ShiftSeriesRead,
  type ShiftTemplateListItem,
  type ShiftTemplateRead,
  type ShiftTypeOption,
} from '#/sicherplan-legacy/api/planningShifts';
import {
  bulkUpdateDemandGroups,
  listDemandGroups,
  bulkApplyDemandGroups,
  type DemandGroupRead,
  type DemandGroupBulkApplyResult,
  type DemandGroupBulkTemplate,
  updateDemandGroup,
} from '#/sicherplan-legacy/api/planningStaffing';
import type {
  CustomerNewPlanStepSubmitResult,
  CustomerNewPlanWizardDraftStepId,
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
import CustomerNewPlanAssignmentsStep from './customer-new-plan-assignments-step.vue';

type PlanningEntityType = 'event_venue' | 'patrol_route' | 'site' | 'trade_fair';
type PlanningSelectionMode = 'create_new' | 'use_existing';
type OrderSelectionMode = 'create_new' | 'use_existing';
type OrderScopeSectionId = 'documents' | 'equipment' | 'requirements';
type OrderScopeValidationFieldKey =
  | 'documentsLinkAction'
  | 'documentsLinkSelection'
  | 'documentsUploadAction'
  | 'documentsUploadFile'
  | 'documentsUploadTitle'
  | 'equipmentAction'
  | 'equipmentItem'
  | 'requirementsAction'
  | 'requirementsType';
type DocumentPickerTarget = 'order' | 'planning-record';

interface OrderScopeSectionValidationResult {
  fieldErrors?: Partial<Record<OrderScopeValidationFieldKey, string>>;
  focusSelector?: string;
  message: string;
  sectionId: OrderScopeSectionId;
}
interface ShiftPlanDraftPersistence {
  draft: Partial<typeof shiftPlanDraft>;
  selected_shift_plan_id: string;
}

interface DemandGroupDraftRow {
  function_type_id: string;
  id: string;
  mandatory_flag: boolean;
  min_qty: number;
  qualification_type_id: string;
  remark: string;
  sort_order: number;
  target_qty: number;
}

type DemandGroupsDraftPersistence = {
  rows: Array<Omit<DemandGroupDraftRow, 'id'>>;
};

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
const planningEntityOptionsRequestSeq = ref(0);
const planningRecordDetailRequestSeq = ref(0);
const orderSelectionMode = ref<OrderSelectionMode>('use_existing');
const customerOrderRows = ref<CustomerOrderListItem[]>([]);
const customerOrderRowsLoading = ref(false);
const customerOrderRowsError = ref('');
const selectedExistingOrderId = ref('');
const editingExistingOrderId = ref('');
const pendingExistingOrderEditId = ref('');
const existingOrderEditFormOpen = ref(false);
const activeOrderScopeSection = ref<OrderScopeSectionId>('equipment');
const orderScopeOnePageRef = ref<HTMLElement | null>(null);
const orderScopeNavShellRef = ref<HTMLElement | null>(null);
const orderScopeNavFloatingMode = ref<'fixed' | 'pinned' | 'static'>('static');
const orderScopeNavFloatingStyle = ref<CSSProperties>({});

let orderScopeSectionObserver: IntersectionObserver | null = null;
let suppressOrderScopeScrollSpyUntil = 0;
let orderScopeNavScrollTargets: Array<HTMLElement | Window> = [];
let orderScopeNavFloatingRaf: number | null = null;
const orderScopeVisibleEntries = new Map<OrderScopeSectionId, IntersectionObserverEntry>();
const EXTRA_SECTION_NAV_TOP_OFFSET = 25;
const ORDER_SCOPE_NAV_FLOATING_MIN_WIDTH = 1081;

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
const orderScopeSectionErrors = reactive<Record<OrderScopeSectionId, string>>({
  documents: '',
  equipment: '',
  requirements: '',
});
const orderScopeFieldErrors = reactive<Record<OrderScopeValidationFieldKey, string>>({
  documentsLinkAction: '',
  documentsLinkSelection: '',
  documentsUploadAction: '',
  documentsUploadFile: '',
  documentsUploadTitle: '',
  equipmentAction: '',
  equipmentItem: '',
  requirementsAction: '',
  requirementsType: '',
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

const documentPicker = reactive({
  error: '',
  loading: false,
  open: false,
  results: [] as PlanningDocumentRead[],
  search: '',
  target: 'order' as DocumentPickerTarget,
});
const selectedOrderLinkDocument = ref<PlanningDocumentRead | null>(null);
const selectedPlanningRecordLinkDocument = ref<PlanningDocumentRead | null>(null);

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
  local_end_time: '',
  local_start_time: '',
  meeting_point: '',
  notes: '',
  recurrence_code: 'daily',
  release_state: 'draft',
  shift_template_id: '',
  shift_type_code: '',
  stealth_mode_flag: false,
  subcontractor_visible_flag: false,
  timezone: 'Europe/Berlin',
  weekday_mask: '',
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

const seriesGenerationDraft = reactive({
  from_date: '',
  regenerate_existing: false,
  to_date: '',
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

const exceptionModal = reactive({
  open: false,
  saving: false,
});

const selectedEquipmentLineId = ref('');
const selectedRequirementLineId = ref('');
const selectedExceptionId = ref('');
const selectedOrder = ref<CustomerOrderRead | null>(null);
const selectedPlanningRecord = ref<PlanningRecordRead | null>(null);
const selectedExistingPlanningRecordId = ref('');
const editingExistingPlanningRecordId = ref('');
const committedPlanningRecordId = ref('');
const planningRecordDirty = ref(false);
const planningRecordFieldErrors = reactive({
  dateRange: '',
  name: '',
  planningEntity: '',
  planningFrom: '',
  planningMode: '',
  planningTo: '',
});
const selectedShiftPlan = ref<ShiftPlanRead | null>(null);
const selectedSeries = ref<ShiftSeriesRead | null>(null);
const seriesDependentSectionsVisible = computed(() => Boolean(selectedSeries.value?.id || props.wizardState.series_id));
const seriesEditMode = computed(() => Boolean(selectedSeries.value?.id));
const planningRecordRows = ref<PlanningRecordListItem[]>([]);
const planningRecordRowsLoading = ref(false);
const planningRecordRowsError = ref('');
const selectedPlanningRecordRow = computed(() =>
  planningRecordRows.value.find((row) => row.id === selectedExistingPlanningRecordId.value),
);
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
const shiftTemplateDetailCache = reactive<Record<string, ShiftTemplateRead>>({});
const demandGroupsScopedRequestCache = new Map<string, Promise<unknown>>();
const demandGroupsFunctionTypeCache = new Map<string, FunctionTypeRead[]>();
const demandGroupsQualificationTypeCache = new Map<string, QualificationTypeRead[]>();
const demandGroupsShiftPlanCache = new Map<string, null | ShiftPlanRead>();
const demandGroupsSeriesCache = new Map<string, null | ShiftSeriesRead>();
const demandGroupsGeneratedShiftCache = new Map<string, ShiftListItem[]>();
const demandGroupsPersistedCache = new Map<string, DemandGroupRead[]>();
const seriesTemplateFieldTouched = reactive({
  default_break_minutes: false,
  location_text: false,
  local_end_time: false,
  local_start_time: false,
  meeting_point: false,
  shift_type_code: false,
});
const seriesTemplateDefaultsApplying = ref(false);
const seriesFieldErrors = reactive({
  dateRange: '',
  defaultBreak: '',
  endTime: '',
  shiftType: '',
  startTime: '',
  weekdayMask: '',
});
const demandGroupDraftRows = ref<DemandGroupDraftRow[]>([]);
const demandGroupGeneratedShifts = ref<ShiftListItem[]>([]);
const persistedDemandGroups = ref<DemandGroupRead[]>([]);
const demandGroupApplyResult = ref<DemandGroupBulkApplyResult | null>(null);
const demandGroupValidationError = ref('');
const demandGroupSummaryMessage = ref('');
const demandGroupDraftWatchMuted = ref(false);
const demandGroupDialog = reactive({
  function_type_id: '',
  mandatory_flag: true,
  min_qty: 1,
  open: false,
  qualification_type_id: '',
  remark: '',
  sort_order: 1,
  target_qty: 1,
});
const editingDemandGroupDraftId = ref('');
const aggregateDemandGroupDialog = reactive({
  function_type_id: '',
  mandatory_flag: true,
  min_qty: 1,
  open: false,
  qualification_type_id: '',
  remark: '',
  sort_order: 1,
  target_qty: 1,
});
const shiftDemandGroupDialog = reactive({
  open: false,
});
const selectedAggregateDemandGroupSignature = ref('');
const selectedShiftDemandGroupId = ref('');
const aggregateDemandGroupSaving = ref(false);
const shiftDemandGroupSaving = ref(false);
const aggregateDemandGroupValidationError = ref('');
const shiftDemandGroupValidationError = ref('');
const shiftDemandGroupDialogDraft = reactive({
  function_type_id: '',
  mandatory_flag: true,
  min_qty: 1,
  qualification_type_id: '',
  remark: '',
  sort_order: 1,
  target_qty: 1,
});
let demandGroupDraftRowSequence = 0;

const { showFeedbackToast } = useSicherPlanFeedback();

type StepLoadKey =
  | 'demandGroups'
  | 'equipmentLines'
  | 'orderDetails'
  | 'orderDocuments'
  | 'orderReferenceOptions'
  | 'planningDocuments'
  | 'planningRecordDetail'
  | 'planningRecords'
  | 'planningReferenceOptions'
  | 'requirementLines'
  | 'seriesContext'
  | 'seriesDetail'
  | 'seriesExceptions'
  | 'seriesReferenceOptions'
  | 'seriesRows'
  | 'shiftPlanDetail'
  | 'shiftPlans'
  | 'shiftReferenceOptions';

const stepLoadState = reactive<Record<StepLoadKey, boolean>>({
  demandGroups: false,
  equipmentLines: false,
  orderDetails: false,
  orderDocuments: false,
  orderReferenceOptions: false,
  planningDocuments: false,
  planningRecordDetail: false,
  planningRecords: false,
  planningReferenceOptions: false,
  requirementLines: false,
  seriesContext: false,
  seriesDetail: false,
  seriesExceptions: false,
  seriesReferenceOptions: false,
  seriesRows: false,
  shiftPlanDetail: false,
  shiftPlans: false,
  shiftReferenceOptions: false,
});

const stepLoadError = reactive({
  demandGroups: '',
  equipmentLines: '',
  orderDetails: '',
  orderDocuments: '',
  planningDocuments: '',
  planningRecords: '',
  planningRecordDetail: '',
  requirementLines: '',
  series: '',
  shiftPlan: '',
});

const stepLoadRequestVersion = reactive<Record<StepLoadKey, number>>({
  demandGroups: 0,
  equipmentLines: 0,
  orderDetails: 0,
  orderDocuments: 0,
  orderReferenceOptions: 0,
  planningDocuments: 0,
  planningRecordDetail: 0,
  planningRecords: 0,
  planningReferenceOptions: 0,
  requirementLines: 0,
  seriesContext: 0,
  seriesDetail: 0,
  seriesExceptions: 0,
  seriesReferenceOptions: 0,
  seriesRows: 0,
  shiftPlanDetail: 0,
  shiftPlans: 0,
  shiftReferenceOptions: 0,
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
  selected_planning_record_id?: string;
  selection_mode?: PlanningSelectionMode;
};

type SeriesExceptionsDraftPersistence = {
  exception: typeof exceptionDraft;
  generation?: typeof seriesGenerationDraft;
  series: typeof seriesDraft;
};

type PersistedDemandGroupSummaryRow = {
  applied_shift_count: number;
  demand_group_ids: string[];
  function_type_id: string;
  function_type_label: string;
  has_locked_rows: boolean;
  all_rows_locked: boolean;
  missing_shift_count: number;
  missing_shift_labels: string[];
  mandatory_flag: boolean;
  qualification_type_id: string;
  qualification_type_label: string;
  remark: string;
  shift_labels: string[];
  signature_key: string;
  sort_order: number;
  status: 'complete' | 'mixed' | 'partial';
  target_qty: number;
  total_shift_count: number;
  variant_count: number;
  min_qty: number;
  shift_rows: PersistedDemandGroupShiftRow[];
};

type PersistedDemandGroupShiftRow = {
  customer_visible_flag: boolean;
  demand_group_id: string;
  function_type_id: string;
  function_type_label: string;
  location_text: string;
  locked: boolean;
  lock_reason: string;
  mandatory_flag: boolean;
  meeting_point: string;
  min_qty: number;
  qualification_type_id: string;
  qualification_type_label: string;
  release_state: string;
  remark: string;
  shift_id: string;
  shift_label: string;
  shift_type_code: string;
  sort_order: number;
  starts_at: string;
  subcontractor_visible_flag: boolean;
  target_qty: number;
  version_no: number;
};

const planningFamilyOptions = computed(() => [
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.site'), value: 'site' },
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.eventVenue'), value: 'event_venue' },
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.tradeFair'), value: 'trade_fair' },
  { label: $t('sicherplan.customerPlansWizard.forms.planningFamilies.patrolRoute'), value: 'patrol_route' },
]);
const savedDataLoadingLabel = computed(() => $t('sicherplan.customerPlansWizard.loading.savedData'));
const referenceDataLoadingLabel = computed(() => $t('sicherplan.customerPlansWizard.loading.referenceData'));

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
const availableEquipmentItemSelectOptions = computed(() => {
  const usedEquipmentItemIds = new Set(
    orderEquipmentLines.value
      .filter((line) => line.id !== selectedEquipmentLineId.value && line.archived_at == null && line.status === 'active')
      .map((line) => line.equipment_item_id),
  );
  return equipmentItemSelectOptions.value.filter((option) => !usedEquipmentItemIds.has(option.value));
});
const equipmentLineDuplicateActive = computed(
  () =>
    !!equipmentLineDraft.equipment_item_id &&
    orderEquipmentLines.value.some(
      (line) =>
        line.id !== selectedEquipmentLineId.value &&
        line.archived_at == null &&
        line.status === 'active' &&
        line.equipment_item_id === equipmentLineDraft.equipment_item_id,
    ),
);
const equipmentItemsExhausted = computed(
  () =>
    equipmentItemSelectOptions.value.length > 0 &&
    availableEquipmentItemSelectOptions.value.length === 0 &&
    !selectedEquipmentLineId.value,
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
const demandGroupDraftRowsDisplay = computed(() =>
  demandGroupDraftRows.value.map((row, index) => ({
    ...row,
    function_type_label:
      functionTypeSelectOptions.value.find((option) => option.value === row.function_type_id)?.label || row.function_type_id,
    index,
    qualification_type_label:
      qualificationTypeSelectOptions.value.find((option) => option.value === row.qualification_type_id)?.label ||
      row.qualification_type_id ||
      $t('sicherplan.customerPlansWizard.forms.none'),
  })),
);
const generatedDemandGroupShiftMeta = computed(() =>
  demandGroupGeneratedShifts.value.map((shift) => ({
    customer_visible_flag: shift.customer_visible_flag,
    id: shift.id,
    label: shift.occurrence_date || shift.starts_at,
    location_text: shift.location_text || '',
    meeting_point: shift.meeting_point || '',
    release_state: shift.release_state,
    shift_type_code: shift.shift_type_code,
    starts_at: shift.starts_at,
    subcontractor_visible_flag: shift.subcontractor_visible_flag,
  })),
);
const persistedDemandGroupSummaryRows = computed<PersistedDemandGroupSummaryRow[]>(() => {
  if (!persistedDemandGroups.value.length || !generatedDemandGroupShiftMeta.value.length) {
    return [];
  }
  const shiftMetaById = new Map(generatedDemandGroupShiftMeta.value.map((entry) => [entry.id, entry]));
  const targetShiftIds = new Set(generatedDemandGroupShiftMeta.value.map((entry) => entry.id));
  const normalizeRemark = (value: null | string | undefined) => value?.trim() || '';
  const buildBaseKey = (row: Pick<DemandGroupRead, 'function_type_id' | 'qualification_type_id'>) =>
    [row.function_type_id, row.qualification_type_id || ''].join('|');
  const buildSignatureKey = (row: Pick<DemandGroupRead, 'function_type_id' | 'qualification_type_id' | 'min_qty' | 'target_qty' | 'mandatory_flag' | 'sort_order' | 'remark'>) =>
    [
      row.function_type_id,
      row.qualification_type_id || '',
      String(row.min_qty),
      String(row.target_qty),
      row.mandatory_flag ? '1' : '0',
      String(row.sort_order),
      normalizeRemark(row.remark),
    ].join('|');

  const baseVariantCounts = new Map<string, number>();
  const signatures = new Map<string, { row: DemandGroupRead; shiftIds: Set<string>; rows: DemandGroupRead[] }>();

  for (const row of persistedDemandGroups.value) {
    if (!targetShiftIds.has(row.shift_id) || row.archived_at != null || row.status !== 'active') {
      continue;
    }
    const signatureKey = buildSignatureKey(row);
    const baseKey = buildBaseKey(row);
    const existing = signatures.get(signatureKey);
    if (existing) {
      existing.shiftIds.add(row.shift_id);
      existing.rows.push(row);
    } else {
      signatures.set(signatureKey, { row, shiftIds: new Set([row.shift_id]), rows: [row] });
      baseVariantCounts.set(baseKey, (baseVariantCounts.get(baseKey) || 0) + 1);
    }
  }

  return Array.from(signatures.entries())
    .map(([signatureKey, entry]) => {
      const functionTypeLabel = functionTypeSelectOptions.value.find((option) => option.value === entry.row.function_type_id)?.label || entry.row.function_type_id;
      const qualificationTypeLabel = qualificationTypeSelectOptions.value.find((option) => option.value === (entry.row.qualification_type_id || ''))?.label
        || (entry.row.qualification_type_id || '')
        || $t('sicherplan.customerPlansWizard.forms.none');
      const shiftIds = Array.from(entry.shiftIds);
      const shiftRows = entry.rows
        .map((row) => {
          const shiftMeta = shiftMetaById.get(row.shift_id);
          const rowLocked = !shiftMeta || shiftMeta.release_state !== 'draft' || shiftMeta.customer_visible_flag || shiftMeta.subcontractor_visible_flag;
          return {
            customer_visible_flag: shiftMeta?.customer_visible_flag ?? false,
            demand_group_id: row.id,
            function_type_id: row.function_type_id,
            function_type_label: functionTypeLabel,
            location_text: shiftMeta?.location_text ?? '',
            locked: rowLocked,
            lock_reason: rowLocked ? $t('sicherplan.customerPlansWizard.messages.demandGroupsRowLocked') : '',
            mandatory_flag: row.mandatory_flag,
            meeting_point: shiftMeta?.meeting_point ?? '',
            min_qty: row.min_qty,
            qualification_type_id: row.qualification_type_id || '',
            qualification_type_label: qualificationTypeLabel,
            release_state: shiftMeta?.release_state ?? '',
            remark: normalizeRemark(row.remark),
            shift_id: row.shift_id,
            shift_label: shiftMeta?.label || row.shift_id,
            shift_type_code: shiftMeta?.shift_type_code ?? '',
            sort_order: row.sort_order,
            starts_at: shiftMeta?.starts_at || '',
            subcontractor_visible_flag: shiftMeta?.subcontractor_visible_flag ?? false,
            target_qty: row.target_qty,
            version_no: row.version_no,
          } satisfies PersistedDemandGroupShiftRow;
        })
        .sort((left, right) => left.starts_at.localeCompare(right.starts_at) || left.shift_label.localeCompare(right.shift_label));
      const missingShiftLabels = generatedDemandGroupShiftMeta.value
        .filter((shift) => !entry.shiftIds.has(shift.id))
        .map((shift) => shift.label);
      const baseKey = buildBaseKey(entry.row);
      const variantCount = baseVariantCounts.get(baseKey) || 1;
      const appliedShiftCount = shiftIds.length;
      const totalShiftCount = generatedDemandGroupShiftMeta.value.length;
      return {
        applied_shift_count: appliedShiftCount,
        all_rows_locked: shiftRows.length > 0 && shiftRows.every((row) => row.locked),
        demand_group_ids: entry.rows.map((row) => row.id),
        function_type_id: entry.row.function_type_id,
        function_type_label: functionTypeLabel,
        has_locked_rows: shiftRows.some((row) => row.locked),
        min_qty: entry.row.min_qty,
        missing_shift_count: missingShiftLabels.length,
        missing_shift_labels: missingShiftLabels,
        mandatory_flag: entry.row.mandatory_flag,
        qualification_type_id: entry.row.qualification_type_id || '',
        qualification_type_label: qualificationTypeLabel,
        remark: normalizeRemark(entry.row.remark),
        shift_rows: shiftRows,
        shift_labels: shiftIds.map((shiftId) => shiftMetaById.get(shiftId)?.label || shiftId),
        signature_key: signatureKey,
        sort_order: entry.row.sort_order,
        status: variantCount > 1 ? 'mixed' : appliedShiftCount === totalShiftCount ? 'complete' : 'partial',
        target_qty: entry.row.target_qty,
        total_shift_count: totalShiftCount,
        variant_count: variantCount,
      } satisfies PersistedDemandGroupSummaryRow;
    })
    .sort((left, right) => left.sort_order - right.sort_order || left.function_type_label.localeCompare(right.function_type_label));
});
const persistedDemandGroupsCoverageComplete = computed(
  () =>
    generatedDemandGroupShiftMeta.value.length > 0
    && generatedDemandGroupShiftMeta.value.every((shift) => persistedDemandGroups.value.some((row) => row.shift_id === shift.id && row.archived_at == null && row.status === 'active')),
);
const persistedDemandGroupsSummaryMessage = computed(() => {
  if (!persistedDemandGroupSummaryRows.value.length) {
    return '';
  }
  return $t('sicherplan.customerPlansWizard.messages.demandGroupsPersistedSummary', {
    groups: persistedDemandGroupSummaryRows.value.length,
    shifts: generatedDemandGroupShiftMeta.value.length,
  } as never);
});
const selectedAggregateDemandGroupRow = computed(
  () => persistedDemandGroupSummaryRows.value.find((row) => row.signature_key === selectedAggregateDemandGroupSignature.value) || null,
);
const selectedShiftDemandGroupRows = computed(() => selectedAggregateDemandGroupRow.value?.shift_rows || []);
const selectedShiftDemandGroupRow = computed(
  () => selectedShiftDemandGroupRows.value.find((row) => row.demand_group_id === selectedShiftDemandGroupId.value) || null,
);
const requirementLineDuplicateActive = computed(() =>
  hasDuplicateActiveRequirementLine(
    orderRequirementLines.value,
    requirementLineDraft.requirement_type_id,
    requirementLineDraft.function_type_id,
    requirementLineDraft.qualification_type_id,
    selectedRequirementLineId.value,
  ),
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
    label: [row.code, row.label].filter(Boolean).join(' — ') || row.id,
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
const seriesWeekdayOptions = computed(() => [
  { id: 'mon', index: 0, label: $t('sicherplan.customerPlansWizard.forms.weekdayMon') },
  { id: 'tue', index: 1, label: $t('sicherplan.customerPlansWizard.forms.weekdayTue') },
  { id: 'wed', index: 2, label: $t('sicherplan.customerPlansWizard.forms.weekdayWed') },
  { id: 'thu', index: 3, label: $t('sicherplan.customerPlansWizard.forms.weekdayThu') },
  { id: 'fri', index: 4, label: $t('sicherplan.customerPlansWizard.forms.weekdayFri') },
  { id: 'sat', index: 5, label: $t('sicherplan.customerPlansWizard.forms.weekdaySat') },
  { id: 'sun', index: 6, label: $t('sicherplan.customerPlansWizard.forms.weekdaySun') },
]);

const orderStepActive = computed(() => props.currentStepId === 'order-details');
const orderScopeDocumentsStepActive = computed(() => props.currentStepId === 'order-scope-documents');
const planningRecordStepActive = computed(() => props.currentStepId === 'planning-record-overview');
const planningRecordDocumentsStepActive = computed(() => props.currentStepId === 'planning-record-documents');
const shiftPlanStepActive = computed(() => props.currentStepId === 'shift-plan');
const seriesStepActive = computed(() => props.currentStepId === 'series-exceptions');
const demandGroupsStepActive = computed(() => props.currentStepId === 'demand-groups');
const assignmentsStepActive = computed(() => props.currentStepId === 'assignments');
const assignmentsStepRef = ref<InstanceType<typeof CustomerNewPlanAssignmentsStep> | null>(null);
const orderScopeSections = computed(() => [
  {
    id: 'equipment' as const,
    icon: 'lucide:package',
    label: $t('sicherplan.customerPlansWizard.orderScope.equipmentTitle'),
    testId: 'customer-order-scope-nav-link-equipment',
  },
  {
    id: 'requirements' as const,
    icon: 'lucide:list-checks',
    label: $t('sicherplan.customerPlansWizard.orderScope.requirementsTitle'),
    testId: 'customer-order-scope-nav-link-requirements',
  },
  {
    id: 'documents' as const,
    icon: 'lucide:file-text',
    label: $t('sicherplan.customerPlansWizard.orderScope.documentsTitle'),
    testId: 'customer-order-scope-nav-link-documents',
  },
]);
const ORDER_SCOPE_FIELD_KEYS_BY_SECTION: Record<OrderScopeSectionId, OrderScopeValidationFieldKey[]> = {
  documents: ['documentsUploadTitle', 'documentsUploadFile', 'documentsUploadAction', 'documentsLinkSelection', 'documentsLinkAction'],
  equipment: ['equipmentItem', 'equipmentAction'],
  requirements: ['requirementsType', 'requirementsAction'],
};
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
    orderScopeDocumentsStepActive.value ||
    planningRecordStepActive.value ||
    planningRecordDocumentsStepActive.value ||
    shiftPlanStepActive.value ||
    seriesStepActive.value ||
    demandGroupsStepActive.value ||
    assignmentsStepActive.value,
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
const selectedShiftPlanSummary = computed(
  () => selectedShiftPlan.value ?? shiftPlanRows.value.find((row) => row.id === props.wizardState.shift_plan_id) ?? null,
);
const selectedSeriesSummary = computed(
  () => selectedSeries.value ?? seriesRows.value.find((row) => row.id === props.wizardState.series_id) ?? null,
);
const generatedDemandGroupShiftCount = computed(() => demandGroupGeneratedShifts.value.length);
const demandGroupsCanApply = computed(
  () => Boolean(props.tenantId && props.accessToken && props.wizardState.shift_plan_id) && generatedDemandGroupShiftCount.value > 0,
);
const seriesWeekdayMaskRequired = computed(() => seriesDraft.recurrence_code === 'weekly');
const exceptionOverrideActive = computed(() => exceptionDraft.action_code === 'override');
const selectedShiftTemplate = computed(
  () => shiftTemplateOptions.value.find((row) => row.id === seriesDraft.shift_template_id) ?? null,
);

function normalizeOrderScopeSectionId(sectionId: string): OrderScopeSectionId {
  return orderScopeSections.value.some((section) => section.id === sectionId)
    ? (sectionId as OrderScopeSectionId)
    : 'equipment';
}

function resolveOrderScopeSectionElementId(sectionId: OrderScopeSectionId) {
  return `customer-order-scope-section-${sectionId}`;
}

function resolveOrderScopeSectionIdFromElement(element: Element): OrderScopeSectionId | null {
  const sectionId = element.id.replace(/^customer-order-scope-section-/, '');
  return orderScopeSections.value.some((section) => section.id === sectionId)
    ? (sectionId as OrderScopeSectionId)
    : null;
}

function suppressOrderScopeScrollSpy() {
  if (typeof window === 'undefined') {
    return;
  }
  suppressOrderScopeScrollSpyUntil = window.performance.now() + 650;
}

function scrollToOrderScopeSection(sectionId: OrderScopeSectionId) {
  void nextTick(() => {
    const sectionElement = orderScopeOnePageRef.value?.querySelector<HTMLElement>(`#${resolveOrderScopeSectionElementId(sectionId)}`)
      ?? document.getElementById(resolveOrderScopeSectionElementId(sectionId));
    sectionElement?.scrollIntoView({
      behavior: 'smooth',
      block: 'start',
    });
  });
}

function clearOrderScopeValidationSection(sectionId: OrderScopeSectionId) {
  orderScopeSectionErrors[sectionId] = '';
  ORDER_SCOPE_FIELD_KEYS_BY_SECTION[sectionId].forEach((key) => {
    orderScopeFieldErrors[key] = '';
  });
}

function clearOrderScopeValidationState() {
  clearOrderScopeValidationSection('equipment');
  clearOrderScopeValidationSection('requirements');
  clearOrderScopeValidationSection('documents');
}

function orderScopeSectionTitle(sectionId: OrderScopeSectionId) {
  switch (sectionId) {
    case 'equipment':
      return $t('sicherplan.customerPlansWizard.orderScope.equipmentTitle');
    case 'requirements':
      return $t('sicherplan.customerPlansWizard.orderScope.requirementsTitle');
    case 'documents':
      return $t('sicherplan.customerPlansWizard.orderScope.documentsTitle');
  }
}

function formatOrderScopeSectionMessage(sectionId: OrderScopeSectionId, errorKey: string) {
  return `${orderScopeSectionTitle(sectionId)}: ${$t(errorKey as never)}`;
}

function resolveOrderScopeValidationTarget(selector?: string) {
  if (!selector) {
    return null;
  }
  return orderScopeOnePageRef.value?.querySelector<HTMLElement>(selector) ?? document.querySelector<HTMLElement>(selector);
}

function focusOrderScopeValidationTarget(selector?: string) {
  void nextTick(() => {
    resolveOrderScopeValidationTarget(selector)?.focus?.();
  });
}

function revealOrderScopeValidationResult(result: OrderScopeSectionValidationResult) {
  activeOrderScopeSection.value = result.sectionId;
  suppressOrderScopeScrollSpy();
  scrollToOrderScopeSection(result.sectionId);
  focusOrderScopeValidationTarget(result.focusSelector);
}

function applyOrderScopeValidationResults(results: OrderScopeSectionValidationResult[]) {
  clearOrderScopeValidationState();
  results.forEach((result) => {
    orderScopeSectionErrors[result.sectionId] = result.message;
    Object.entries(result.fieldErrors ?? {}).forEach(([key, value]) => {
      orderScopeFieldErrors[key as OrderScopeValidationFieldKey] = value;
    });
  });
}

function selectOrderScopeSection(sectionId: string) {
  activeOrderScopeSection.value = normalizeOrderScopeSectionId(sectionId);
  suppressOrderScopeScrollSpy();
  scrollToOrderScopeSection(activeOrderScopeSection.value);
}

function disconnectOrderScopeSectionObserver() {
  orderScopeSectionObserver?.disconnect();
  orderScopeSectionObserver = null;
  orderScopeVisibleEntries.clear();
}

function resolveOrderScopeStickyTop() {
  const navShell = orderScopeNavShellRef.value;
  if (navShell && typeof window !== 'undefined') {
    const top = Number.parseFloat(window.getComputedStyle(navShell).top);
    if (Number.isFinite(top)) {
      return top;
    }
  }

  if (typeof window === 'undefined') {
    return 104 + EXTRA_SECTION_NAV_TOP_OFFSET;
  }

  const rootFontSize = Number.parseFloat(window.getComputedStyle(document.documentElement).fontSize);
  const baseTop = (Number.isFinite(rootFontSize) ? rootFontSize : 16) * 6.5;
  return baseTop + EXTRA_SECTION_NAV_TOP_OFFSET;
}

function isScrollableAncestor(element: HTMLElement) {
  const overflowY = window.getComputedStyle(element).overflowY;
  return /(auto|scroll|overlay)/.test(overflowY) && element.scrollHeight > element.clientHeight;
}

function findOrderScopeScrollContainers() {
  const containers: HTMLElement[] = [];
  let parent = orderScopeOnePageRef.value?.parentElement ?? null;

  while (parent && parent !== document.body) {
    if (isScrollableAncestor(parent)) {
      containers.push(parent);
    }
    parent = parent.parentElement;
  }

  return containers;
}

function resolveOrderScopeIntersectionRoot() {
  return findOrderScopeScrollContainers()[0] ?? null;
}

function resolveActiveOrderScopeSection(sectionElements: HTMLElement[]) {
  const stickyTop = resolveOrderScopeStickyTop();
  const activeLineTolerance = 32;
  const visibleSections = sectionElements
    .map((element) => {
      const sectionId = resolveOrderScopeSectionIdFromElement(element);
      if (!sectionId || !orderScopeVisibleEntries.has(sectionId)) {
        return null;
      }
      const rect = element.getBoundingClientRect();
      return {
        distance: Math.abs(rect.top - stickyTop),
        isCurrentOrNear: rect.top <= stickyTop + activeLineTolerance,
        rectTop: rect.top,
        sectionId,
      };
    })
    .filter((entry): entry is Exclude<typeof entry, null> => !!entry);

  const currentSections = visibleSections.filter((section) => section.isCurrentOrNear);
  const [bestSection] = (currentSections.length ? currentSections : visibleSections).sort((left, right) => {
    if (left.distance !== right.distance) {
      return left.distance - right.distance;
    }
    return left.rectTop - right.rectTop;
  });

  return bestSection?.sectionId ?? null;
}

function resetOrderScopeNavFloating() {
  orderScopeNavFloatingMode.value = 'static';
  orderScopeNavFloatingStyle.value = {};
}

function cancelOrderScopeNavFloatingFrame() {
  if (orderScopeNavFloatingRaf !== null) {
    window.cancelAnimationFrame(orderScopeNavFloatingRaf);
    orderScopeNavFloatingRaf = null;
  }
}

function updateOrderScopeNavFloating() {
  orderScopeNavFloatingRaf = null;

  const onePageElement = orderScopeOnePageRef.value;
  const navShell = orderScopeNavShellRef.value;
  if (
    !orderScopeDocumentsStepActive.value ||
    !onePageElement ||
    !navShell ||
    typeof window === 'undefined' ||
    !window.matchMedia(`(min-width: ${ORDER_SCOPE_NAV_FLOATING_MIN_WIDTH}px)`).matches
  ) {
    resetOrderScopeNavFloating();
    return;
  }

  const stickyTop = resolveOrderScopeStickyTop();
  const onePageRect = onePageElement.getBoundingClientRect();
  const navWidth = navShell.offsetWidth;
  const navHeight = navShell.offsetHeight;

  if (!navWidth || !navHeight || onePageRect.top > stickyTop || onePageRect.height <= navHeight) {
    resetOrderScopeNavFloating();
    return;
  }

  const maxHeight = `calc(100vh - ${Math.round(stickyTop)}px - 1rem)`;
  if (onePageRect.bottom <= stickyTop + navHeight) {
    orderScopeNavFloatingMode.value = 'pinned';
    orderScopeNavFloatingStyle.value = {
      left: '0px',
      maxHeight,
      top: `${Math.max(0, onePageElement.offsetHeight - navHeight)}px`,
      width: `${navWidth}px`,
    };
    return;
  }

  orderScopeNavFloatingMode.value = 'fixed';
  orderScopeNavFloatingStyle.value = {
    left: `${onePageRect.left}px`,
    maxHeight,
    top: `${stickyTop}px`,
    width: `${navWidth}px`,
  };
}

function scheduleOrderScopeNavFloatingUpdate() {
  if (orderScopeNavFloatingRaf !== null || typeof window === 'undefined') {
    return;
  }
  orderScopeNavFloatingRaf = window.requestAnimationFrame(updateOrderScopeNavFloating);
}

function teardownOrderScopeNavFloating() {
  if (typeof window === 'undefined') {
    return;
  }
  cancelOrderScopeNavFloatingFrame();
  orderScopeNavScrollTargets.forEach((target) => target.removeEventListener('scroll', scheduleOrderScopeNavFloatingUpdate));
  window.removeEventListener('resize', scheduleOrderScopeNavFloatingUpdate);
  orderScopeNavScrollTargets = [];
  resetOrderScopeNavFloating();
}

function setupOrderScopeNavFloating() {
  teardownOrderScopeNavFloating();

  if (!orderScopeDocumentsStepActive.value || !orderScopeOnePageRef.value || !orderScopeNavShellRef.value || typeof window === 'undefined') {
    return;
  }

  orderScopeNavScrollTargets = [window, ...findOrderScopeScrollContainers()];
  orderScopeNavScrollTargets.forEach((target) =>
    target.addEventListener('scroll', scheduleOrderScopeNavFloatingUpdate, { passive: true }),
  );
  window.addEventListener('resize', scheduleOrderScopeNavFloatingUpdate, { passive: true });
  scheduleOrderScopeNavFloatingUpdate();
}

function setupOrderScopeSectionObserver() {
  disconnectOrderScopeSectionObserver();

  if (!orderScopeDocumentsStepActive.value || typeof window === 'undefined' || typeof window.IntersectionObserver === 'undefined') {
    return;
  }

  const sectionElements = orderScopeSections.value
    .map(
      (section) =>
        orderScopeOnePageRef.value?.querySelector<HTMLElement>(`#${resolveOrderScopeSectionElementId(section.id)}`)
        ?? document.getElementById(resolveOrderScopeSectionElementId(section.id)),
    )
    .filter((element): element is HTMLElement => !!element);

  if (!sectionElements.length) {
    return;
  }

  const stickyTop = resolveOrderScopeStickyTop();
  orderScopeSectionObserver = new IntersectionObserver(
    (entries) => {
      if (window.performance.now() < suppressOrderScopeScrollSpyUntil) {
        return;
      }

      entries.forEach((entry) => {
        const sectionId = resolveOrderScopeSectionIdFromElement(entry.target);
        if (!sectionId) {
          return;
        }
        if (entry.isIntersecting) {
          orderScopeVisibleEntries.set(sectionId, entry);
          return;
        }
        orderScopeVisibleEntries.delete(sectionId);
      });

      const sectionId = resolveActiveOrderScopeSection(sectionElements);
      if (sectionId) {
        activeOrderScopeSection.value = sectionId;
      }
    },
    {
      root: resolveOrderScopeIntersectionRoot(),
      rootMargin: `-${Math.round(stickyTop)}px 0px -55% 0px`,
      threshold: [0, 0.1, 0.25, 0.5, 0.75, 1],
    },
  );

  sectionElements.forEach((element) => orderScopeSectionObserver?.observe(element));
}

function setupOrderScopeOnePageNavigation() {
  void nextTick(() => {
    if (!orderScopeDocumentsStepActive.value) {
      disconnectOrderScopeSectionObserver();
      teardownOrderScopeNavFloating();
      activeOrderScopeSection.value = 'equipment';
      return;
    }

    activeOrderScopeSection.value = normalizeOrderScopeSectionId(activeOrderScopeSection.value);
    setupOrderScopeSectionObserver();
    setupOrderScopeNavFloating();
  });
}

const exceptionCustomerVisibleModel = computed({
  get: () => nullableBooleanToSelectValue(exceptionDraft.customer_visible_flag),
  set: (value: string) => {
    exceptionDraft.customer_visible_flag = selectValueToNullableBoolean(value);
  },
});
const exceptionSubcontractorVisibleModel = computed({
  get: () => nullableBooleanToSelectValue(exceptionDraft.subcontractor_visible_flag),
  set: (value: string) => {
    exceptionDraft.subcontractor_visible_flag = selectValueToNullableBoolean(value);
  },
});
const exceptionStealthModeModel = computed({
  get: () => nullableBooleanToSelectValue(exceptionDraft.stealth_mode_flag),
  set: (value: string) => {
    exceptionDraft.stealth_mode_flag = selectValueToNullableBoolean(value);
  },
});
const existingOrderEditActive = computed(
  () => orderModeUsesExisting.value && Boolean(existingOrderEditFormOpen.value && editingExistingOrderId.value),
);
const externalOrderEditRequested = computed(() => {
  const rawOrderMode = route.query.order_mode;
  const rawIntent = route.query.intent;
  const orderMode = Array.isArray(rawOrderMode) ? rawOrderMode[0] : rawOrderMode;
  const intent = Array.isArray(rawIntent) ? rawIntent[0] : rawIntent;
  return orderMode === 'edit' || intent === 'edit-order';
});
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
  if (!message.trim()) {
    return;
  }
  showFeedbackToast({
    key: 'customer-new-plan-step-feedback',
    message,
    tone,
  });
}

function resetSeriesTemplateTouchedState() {
  Object.assign(seriesTemplateFieldTouched, {
    default_break_minutes: false,
    location_text: false,
    local_end_time: false,
    local_start_time: false,
    meeting_point: false,
    shift_type_code: false,
  });
}

function clearSeriesFieldErrors() {
  Object.assign(seriesFieldErrors, {
    dateRange: '',
    defaultBreak: '',
    endTime: '',
    shiftType: '',
    startTime: '',
    weekdayMask: '',
  });
}

function nullableBooleanToSelectValue(value: boolean | null) {
  if (value === true) {
    return 'true';
  }
  if (value === false) {
    return 'false';
  }
  return '';
}

function selectValueToNullableBoolean(value: string) {
  if (value === 'true') {
    return true;
  }
  if (value === 'false') {
    return false;
  }
  return null;
}

function isOrderDetailsDraftPersistence(value: unknown): value is OrderDetailsDraftPersistence {
  return Boolean(value && typeof value === 'object' && 'form' in (value as Record<string, unknown>));
}

function normalizeUuid(value: string | null | undefined) {
  const normalized = typeof value === 'string' ? value.trim() : '';
  return normalized || null;
}

function normalizeSeriesWeekdayMask(value: null | string | undefined) {
  const candidate = (value ?? '').trim();
  return /^[01]{7}$/.test(candidate) ? candidate : '1111100';
}

function normalizeSeriesTimeValue(value: null | string | undefined) {
  const normalized = (value ?? '').trim();
  const match = normalized.match(/^(\d{2}:\d{2})/);
  return match?.[1] ?? normalized;
}

function isSeriesWeekdaySelected(index: number) {
  return normalizeSeriesWeekdayMask(seriesDraft.weekday_mask)[index] === '1';
}

function toggleSeriesWeekday(index: number) {
  if (!seriesWeekdayMaskRequired.value) {
    return;
  }
  const mask = normalizeSeriesWeekdayMask(seriesDraft.weekday_mask).split('');
  mask[index] = mask[index] === '1' ? '0' : '1';
  seriesDraft.weekday_mask = mask.join('');
}

function ensureSeriesWeeklyMask() {
  if (!seriesWeekdayMaskRequired.value) {
    return;
  }
  seriesDraft.weekday_mask = normalizeSeriesWeekdayMask(seriesDraft.weekday_mask);
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

function buildStepExternalContextKey(
  overrides: Partial<{
    currentStepId: CustomerNewPlanWizardStepId;
    customerId: string;
    orderId: string;
    planningEntityId: string;
    planningEntityType: string;
    planningModeCode: string;
    planningRecordId: string;
    shiftPlanId: string;
    seriesId: string;
    tenantId: string;
  }> = {},
) {
  return JSON.stringify({
    currentStepId: overrides.currentStepId ?? props.currentStepId,
    customerId: overrides.customerId ?? props.customer.id,
    orderId: overrides.orderId ?? props.wizardState.order_id,
    planningEntityId: overrides.planningEntityId ?? props.wizardState.planning_entity_id,
    planningEntityType: overrides.planningEntityType ?? props.wizardState.planning_entity_type,
    planningModeCode: overrides.planningModeCode ?? props.wizardState.planning_mode_code,
    planningRecordId: overrides.planningRecordId ?? props.wizardState.planning_record_id,
    shiftPlanId: overrides.shiftPlanId ?? props.wizardState.shift_plan_id,
    seriesId: overrides.seriesId ?? props.wizardState.series_id,
    tenantId: overrides.tenantId ?? props.tenantId,
  });
}

function buildDemandGroupsStepContextKey(
  overrides: Partial<{
    currentStepId: CustomerNewPlanWizardStepId;
    customerId: string;
    orderId: string;
    planningRecordId: string;
    shiftPlanId: string;
    seriesId: string;
    tenantId: string;
  }> = {},
) {
  return JSON.stringify({
    currentStepId: overrides.currentStepId ?? 'demand-groups',
    customerId: overrides.customerId ?? props.customer.id,
    orderId: overrides.orderId ?? props.wizardState.order_id,
    planningRecordId: overrides.planningRecordId ?? props.wizardState.planning_record_id,
    shiftPlanId: overrides.shiftPlanId ?? props.wizardState.shift_plan_id,
    seriesId: overrides.seriesId ?? props.wizardState.series_id,
    tenantId: overrides.tenantId ?? props.tenantId,
  });
}

function clearDemandGroupsRequestCaches() {
  demandGroupsScopedRequestCache.clear();
  demandGroupsFunctionTypeCache.clear();
  demandGroupsQualificationTypeCache.clear();
  demandGroupsShiftPlanCache.clear();
  demandGroupsSeriesCache.clear();
  demandGroupsGeneratedShiftCache.clear();
  demandGroupsPersistedCache.clear();
}

async function resolveDemandGroupsScopedRequest<T>(cacheKey: string, loader: () => Promise<T>) {
  if (demandGroupsScopedRequestCache.has(cacheKey)) {
    return demandGroupsScopedRequestCache.get(cacheKey) as Promise<T>;
  }
  const request = loader()
    .finally(() => {
      demandGroupsScopedRequestCache.delete(cacheKey);
    });
  demandGroupsScopedRequestCache.set(cacheKey, request);
  return request;
}

function invalidateDemandGroupsScopedCache(prefix: 'persisted' | 'shifts', contextKey: string) {
  if (prefix === 'persisted') {
    demandGroupsPersistedCache.delete(contextKey);
    demandGroupsScopedRequestCache.delete(`persisted:${contextKey}`);
    return;
  }
  demandGroupsGeneratedShiftCache.delete(contextKey);
  demandGroupsScopedRequestCache.delete(`shifts:${contextKey}`);
}

function loadStepDraft<T>(stepId: CustomerNewPlanWizardDraftStepId) {
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

function saveStepDraft<T>(stepId: CustomerNewPlanWizardDraftStepId, payload: null | T | undefined) {
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

function clearStepDraft(stepId: CustomerNewPlanWizardDraftStepId) {
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
    selected_planning_record_id: selectedPlanningRecord.value?.id,
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

function hasPlanningRecordDocumentUploadDraftInput() {
  return Boolean(
    planningRecordAttachmentDraft.title ||
      planningRecordAttachmentDraft.label ||
      planningRecordAttachmentDraft.file_name ||
      planningRecordAttachmentDraft.content_type ||
      planningRecordAttachmentDraft.content_base64,
  );
}

function hasCompletePlanningRecordDocumentUploadDraft() {
  return Boolean(
    planningRecordAttachmentDraft.content_base64 &&
      planningRecordAttachmentDraft.file_name &&
      planningRecordAttachmentDraft.title.trim(),
  );
}

function hasPlanningRecordDocumentLinkDraftInput() {
  return Boolean(planningRecordAttachmentLink.document_id.trim() || planningRecordAttachmentLink.label.trim());
}

function hasCompletePlanningRecordDocumentLinkDraft() {
  return Boolean(planningRecordAttachmentLink.document_id.trim());
}

function hasAnyPlanningRecordDocumentDraftInput() {
  return hasPlanningRecordDocumentUploadDraftInput() || hasPlanningRecordDocumentLinkDraftInput();
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

function buildSeriesDefaultDraft() {
  return {
    customer_visible_flag: false,
    date_from: selectedShiftPlan.value?.planning_from || '',
    date_to: selectedShiftPlan.value?.planning_to || '',
    default_break_minutes: 30,
    interval_count: 1,
    label: selectedShiftPlan.value?.name || '',
    location_text: '',
    local_end_time: '',
    local_start_time: '',
    meeting_point: '',
    notes: '',
    recurrence_code: 'daily',
    release_state: 'draft',
    shift_template_id: '',
    shift_type_code: '',
    stealth_mode_flag: false,
    subcontractor_visible_flag: false,
    timezone: 'Europe/Berlin',
    weekday_mask: '',
  };
}

function buildSeriesGenerationDefaultDraft(
  source: Pick<typeof seriesDraft, 'date_from' | 'date_to'> = seriesDraft,
) {
  return {
    from_date: source.date_from || selectedShiftPlan.value?.planning_from || '',
    regenerate_existing: false,
    to_date: source.date_to || selectedShiftPlan.value?.planning_to || '',
  };
}

function formatWorkforceScopeLabel(workforceScopeCode: string | null | undefined) {
  switch (workforceScopeCode) {
    case 'subcontractor':
      return $t('sicherplan.customerPlansWizard.forms.workforceSubcontractor');
    case 'mixed':
      return $t('sicherplan.customerPlansWizard.forms.workforceMixed');
    case 'internal':
    default:
      return $t('sicherplan.customerPlansWizard.forms.workforceInternal');
  }
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

function hasContentfulShiftPlanDraftPersistence(
  payload: ShiftPlanDraftPersistence | null,
  baseline: Partial<typeof shiftPlanDraft>,
) {
  if (!payload) {
    return false;
  }
  const draft = payload.draft;
  return Boolean(
    (draft.name ?? '') !== (baseline.name ?? '') ||
      (draft.planning_from ?? '') !== (baseline.planning_from ?? '') ||
      (draft.planning_record_id ?? '') !== (baseline.planning_record_id ?? '') ||
      (draft.planning_to ?? '') !== (baseline.planning_to ?? '') ||
      (draft.remarks ?? '') !== (baseline.remarks ?? '') ||
      (draft.workforce_scope_code ?? 'internal') !== (baseline.workforce_scope_code ?? 'internal'),
  );
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
  const generationDefaults = buildSeriesGenerationDefaultDraft();
  return Boolean(
    seriesDraft.label ||
      seriesDraft.shift_template_id ||
      seriesDraft.date_from ||
      seriesDraft.date_to ||
      seriesDraft.interval_count !== 1 ||
      seriesDraft.default_break_minutes !== 30 ||
      seriesDraft.local_start_time ||
      seriesDraft.local_end_time ||
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
      seriesDraft.weekday_mask !== '' ||
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
      exceptionDraft.stealth_mode_flag !== null ||
      (seriesGenerationDraft.from_date && seriesGenerationDraft.from_date !== generationDefaults.from_date) ||
      (seriesGenerationDraft.to_date && seriesGenerationDraft.to_date !== generationDefaults.to_date) ||
      seriesGenerationDraft.regenerate_existing,
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

function planningRecordDraftMatchesRecord(
  draft: null | PlanningRecordOverviewDraftPersistence | undefined,
  record: PlanningRecordRead,
) {
  if (!draft || !draft.selected_planning_record_id || draft.selected_planning_record_id !== record.id) {
    return false;
  }
  const context = draft.planning_context;
  if (!context) {
    return false;
  }
  return (
    context.planning_entity_id === planningEntityIdForRecord(record) &&
    context.planning_entity_type === planningFamilyForRecord(record) &&
    context.planning_mode_code === record.planning_mode_code
  );
}

function hasCommittedPlanningRecordSelection() {
  const selectedId = selectedPlanningRecord.value?.id || selectedExistingPlanningRecordId.value;
  if (
    !selectedId ||
    planningRecordDirty.value ||
    (props.wizardState.planning_record_id || committedPlanningRecordId.value) !== selectedId
  ) {
    return false;
  }
  if (selectedPlanningRecord.value?.id === selectedId) {
    return (
      currentPlanningEntityScope.value?.planningEntityId === planningEntityIdForRecord(selectedPlanningRecord.value) &&
      currentPlanningEntityScope.value?.planningEntityType === planningFamilyForRecord(selectedPlanningRecord.value) &&
      currentPlanningModeCode.value === selectedPlanningRecord.value.planning_mode_code
    );
  }
  return Boolean(
    currentPlanningEntityScope.value?.planningEntityId &&
      currentPlanningEntityScope.value?.planningEntityType &&
      currentPlanningModeCode.value,
  );
}

function hasStableLocalPlanningRecordSelectionForCurrentContext() {
  const selectedRecord = selectedPlanningRecord.value;
  const selectedId = selectedRecord?.id || selectedExistingPlanningRecordId.value || committedPlanningRecordId.value;
  if (!selectedRecord || !selectedId || planningRecordDirty.value) {
    return false;
  }
  return (
    selectedRecord.id === selectedId &&
    committedPlanningRecordId.value === selectedId &&
    currentPlanningEntityScope.value?.planningEntityId === planningEntityIdForRecord(selectedRecord) &&
    currentPlanningEntityScope.value?.planningEntityType === planningFamilyForRecord(selectedRecord) &&
    currentPlanningModeCode.value === selectedRecord.planning_mode_code
  );
}

function hasHydratedSelectedPlanningRecord(planningRecordId: string) {
  const selectedRecord = selectedPlanningRecord.value;
  if (!planningRecordId || !selectedRecord || planningRecordDirty.value) {
    return false;
  }
  return (
    selectedRecord.id === planningRecordId &&
    selectedExistingPlanningRecordId.value === planningRecordId &&
    editingExistingPlanningRecordId.value === planningRecordId &&
    committedPlanningRecordId.value === planningRecordId &&
    currentPlanningEntityScope.value?.planningEntityId === planningEntityIdForRecord(selectedRecord) &&
    currentPlanningEntityScope.value?.planningEntityType === planningFamilyForRecord(selectedRecord) &&
    currentPlanningModeCode.value === selectedRecord.planning_mode_code
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
    Object.assign(seriesGenerationDraft, payload.generation || {});
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
          generation: { ...seriesGenerationDraft },
          series: { ...seriesDraft },
        }
      : null,
  );
}

function hasDemandGroupDraftContent() {
  return demandGroupDraftRows.value.some((row) =>
    Boolean(
      row.function_type_id.trim() ||
        row.qualification_type_id.trim() ||
        row.min_qty !== 1 ||
        row.target_qty !== 1 ||
        row.sort_order !== 1 ||
        !row.mandatory_flag ||
        row.remark.trim(),
    ),
  );
}

function persistDemandGroupsDraft() {
  saveStepDraft<DemandGroupsDraftPersistence>(
    'demand-groups',
    hasDemandGroupDraftContent()
      ? {
          rows: demandGroupDraftRows.value.map(({ id: _id, ...row }) => ({
            ...row,
            function_type_id: row.function_type_id.trim(),
            qualification_type_id: row.qualification_type_id.trim(),
            remark: row.remark.trim(),
          })),
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
  persistDemandGroupsDraft();
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
  selectedOrderLinkDocument.value = null;
}

function resetPlanningRecordDraft() {
  selectedPlanningRecord.value = null;
  selectedExistingPlanningRecordId.value = '';
  editingExistingPlanningRecordId.value = '';
  committedPlanningRecordId.value = '';
  planningRecordDirty.value = false;
  clearPlanningRecordFieldErrors();
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

function resetPlanningRecordDraftForNewContext() {
  withDraftSyncPaused(() => {
    resetPlanningRecordDraft();
    planningRecordDraft.planning_mode_code = planningModeCode.value;
    planningRecordDraft.planning_from = selectedOrder.value?.service_from || orderDraft.service_from || '';
    planningRecordDraft.planning_to = selectedOrder.value?.service_to || orderDraft.service_to || '';
  });
  clearStepDraft('planning-record-overview');
  clearDraftRestoreMessage();
}

function invalidateSelectedPlanningRecordForCurrentContext() {
  resetPlanningRecordDraftForNewContext();
  selectedPlanningRecord.value = null;
  selectedExistingPlanningRecordId.value = '';
  editingExistingPlanningRecordId.value = '';
  committedPlanningRecordId.value = '';
  setFeedback('neutral', $t('sicherplan.customerPlansWizard.messages.planningEntryChangedForNewRecord'));
  emit('saved-context', {
    ...buildPlanningContextPatch(),
    planning_record_id: '',
  });
  emit('step-completion', 'planning-record-overview', false);
  emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
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
  selectedPlanningRecordLinkDocument.value = null;
}

function resetShiftPlanDraft() {
  Object.assign(shiftPlanDraft, buildShiftPlanDefaultDraft());
}

function resetSeriesDraft() {
  Object.assign(seriesDraft, buildSeriesDefaultDraft());
  resetSeriesTemplateTouchedState();
}

function resetSeriesGenerationDraft(source: Pick<typeof seriesDraft, 'date_from' | 'date_to'> = seriesDraft) {
  Object.assign(seriesGenerationDraft, buildSeriesGenerationDefaultDraft(source));
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

function openNewExceptionModal() {
  if (!selectedSeries.value?.id) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.saveCurrentSeriesBeforeContinue'));
    return;
  }
  withDraftSyncPaused(() => {
    resetExceptionDraft();
  });
  exceptionModal.open = true;
}

function openEditExceptionModal(row: ShiftSeriesExceptionRead) {
  syncExceptionDraft(row);
  exceptionModal.open = true;
}

function closeExceptionModal() {
  exceptionModal.open = false;
  withDraftSyncPaused(() => {
    resetExceptionDraft();
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

function planningFamilyForRecord(record: PlanningRecordRead): PlanningEntityType {
  if (record.planning_mode_code === 'event') {
    return 'event_venue';
  }
  if (record.planning_mode_code === 'trade_fair') {
    return 'trade_fair';
  }
  if (record.planning_mode_code === 'patrol') {
    return 'patrol_route';
  }
  return 'site';
}

function planningEntityIdForRecord(record: PlanningRecordRead) {
  if (record.planning_mode_code === 'event') {
    return record.event_detail?.event_venue_id ?? '';
  }
  if (record.planning_mode_code === 'trade_fair') {
    return record.trade_fair_detail?.trade_fair_id ?? '';
  }
  if (record.planning_mode_code === 'patrol') {
    return record.patrol_detail?.patrol_route_id ?? '';
  }
  return record.site_detail?.site_id ?? '';
}

function planningEntityOptionLabel(option: PlanningListItem) {
  const code = option.site_no || option.venue_no || option.fair_no || option.route_no || option.code || '';
  const name = option.name || option.label || '';
  if (code && name) {
    return `${code} - ${name}`;
  }
  return name || code || option.id;
}

function planningRecordContextIsValid(record: PlanningRecordRead) {
  return Boolean(planningEntityIdForRecord(record));
}

function linkedPlanningEntityFallbackOption(record: PlanningRecordRead): PlanningListItem | null {
  const entityId = planningEntityIdForRecord(record);
  if (!entityId) {
    return null;
  }
  return {
    customer_id: props.customer.id,
    id: entityId,
    label: `${entityId} / ${$t('sicherplan.customerPlansWizard.forms.linkedPlanningEntry')}`,
    name: `${entityId} / ${$t('sicherplan.customerPlansWizard.forms.linkedPlanningEntry')}`,
    status: 'active',
    tenant_id: props.tenantId,
    version_no: 0,
  };
}

function ensureSelectedPlanningEntityOption(record = selectedPlanningRecord.value) {
  if (!record) {
    return;
  }
  const fallback = linkedPlanningEntityFallbackOption(record);
  if (!fallback || planningEntityOptions.value.some((option) => option.id === fallback.id)) {
    return;
  }
  planningEntityOptions.value = [fallback, ...planningEntityOptions.value];
}

function clearPlanningRecordFieldErrors() {
  Object.assign(planningRecordFieldErrors, {
    dateRange: '',
    name: '',
    planningEntity: '',
    planningFrom: '',
    planningMode: '',
    planningTo: '',
  });
}

function setPlanningRecordFieldError(field: keyof typeof planningRecordFieldErrors, messageKey: string) {
  planningRecordFieldErrors[field] = $t(`sicherplan.customerPlansWizard.errors.${messageKey}` as never);
}

function validatePlanningRecordFields() {
  clearPlanningRecordFieldErrors();
  if (!planningEntityId.value.trim()) {
    setPlanningRecordFieldError('planningEntity', 'planningEntryRequired');
  }
  if (!planningRecordDraft.name.trim()) {
    setPlanningRecordFieldError('name', 'planningRecordNameRequired');
  }
  if (!planningRecordDraft.planning_from) {
    setPlanningRecordFieldError('planningFrom', 'planningRecordStartRequired');
  }
  if (!planningRecordDraft.planning_to) {
    setPlanningRecordFieldError('planningTo', 'planningRecordEndRequired');
  }
  if (
    planningRecordDraft.planning_from &&
    planningRecordDraft.planning_to &&
    planningRecordDraft.planning_to < planningRecordDraft.planning_from
  ) {
    setPlanningRecordFieldError('dateRange', 'planningRecordDateRangeInvalid');
  }
  const modeMatchesEntity = planningRecordDraft.planning_mode_code === planningModeCode.value;
  if (!modeMatchesEntity) {
    setPlanningRecordFieldError('planningMode', 'planningRecordModeMismatch');
  }
  return !Object.values(planningRecordFieldErrors).some(Boolean);
}

function syncPlanningRecordDraft(record: PlanningRecordRead) {
  withPlanningContextHydrationPaused(() =>
    withDraftSyncPaused(() => {
      resetPlanningRecordDraft();
      selectedPlanningRecord.value = record;
      selectedExistingPlanningRecordId.value = record.id;
      committedPlanningRecordId.value = record.id;
      planningSelectionMode.value = 'use_existing';
      planningFamily.value = planningFamilyForRecord(record);
      planningEntityId.value = planningEntityIdForRecord(record);
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
    }),
  );
  ensureSelectedPlanningEntityOption(record);
  planningRecordDirty.value = false;
  clearPlanningRecordFieldErrors();
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
      local_end_time: normalizeSeriesTimeValue(
        shiftTemplateOptions.value.find((row) => row.id === series.shift_template_id)?.local_end_time,
      ),
      local_start_time: normalizeSeriesTimeValue(
        shiftTemplateOptions.value.find((row) => row.id === series.shift_template_id)?.local_start_time,
      ),
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
    Object.assign(seriesGenerationDraft, buildSeriesGenerationDefaultDraft({
      date_from: series.date_from,
      date_to: series.date_to,
    }));
  });
  resetSeriesTemplateTouchedState();
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

async function resolveShiftTemplate(templateId: string) {
  if (!props.tenantId || !props.accessToken || !templateId) {
    return null;
  }
  const cached = shiftTemplateDetailCache[templateId];
  if (cached) {
    return cached;
  }
  const detail = await getShiftTemplate(props.tenantId, templateId, props.accessToken);
  shiftTemplateDetailCache[templateId] = detail;
  return detail;
}

function applyTemplateDefaultsToSeriesDraft(
  template: Pick<ShiftTemplateRead, 'default_break_minutes' | 'local_end_time' | 'local_start_time' | 'location_text' | 'meeting_point' | 'shift_type_code'>,
  options: { force?: boolean; onlyIfEmpty?: boolean } = {},
) {
  const onlyIfEmpty = options.onlyIfEmpty ?? false;
  const force = options.force ?? false;
  if ((force || !seriesTemplateFieldTouched.local_start_time) && template.local_start_time) {
    if (!onlyIfEmpty || !seriesDraft.local_start_time) {
      seriesDraft.local_start_time = normalizeSeriesTimeValue(template.local_start_time);
    }
  }
  if ((force || !seriesTemplateFieldTouched.local_end_time) && template.local_end_time) {
    if (!onlyIfEmpty || !seriesDraft.local_end_time) {
      seriesDraft.local_end_time = normalizeSeriesTimeValue(template.local_end_time);
    }
  }
  if ((force || !seriesTemplateFieldTouched.default_break_minutes) && template.default_break_minutes != null) {
    if (!onlyIfEmpty || seriesDraft.default_break_minutes === 0 || seriesDraft.default_break_minutes === 30) {
      seriesDraft.default_break_minutes = template.default_break_minutes;
    }
  }
  if ((force || !seriesTemplateFieldTouched.shift_type_code) && template.shift_type_code) {
    if (!onlyIfEmpty || !seriesDraft.shift_type_code) {
      seriesDraft.shift_type_code = template.shift_type_code;
    }
  }
  if ((force || !seriesTemplateFieldTouched.meeting_point) && template.meeting_point) {
    if (!onlyIfEmpty || !seriesDraft.meeting_point) {
      seriesDraft.meeting_point = template.meeting_point;
    }
  }
  if ((force || !seriesTemplateFieldTouched.location_text) && template.location_text) {
    if (!onlyIfEmpty || !seriesDraft.location_text) {
      seriesDraft.location_text = template.location_text;
    }
  }
}

async function applySelectedShiftTemplatePreset() {
  if (!seriesDraft.shift_template_id) {
    return;
  }
  const listItem = shiftTemplateOptions.value.find((row) => row.id === seriesDraft.shift_template_id) ?? null;
  const detail = await resolveShiftTemplate(seriesDraft.shift_template_id);
  seriesTemplateDefaultsApplying.value = true;
  try {
    withDraftSyncPaused(() => {
      if (detail) {
        applyTemplateDefaultsToSeriesDraft(detail, { force: true });
      } else if (listItem) {
        applyTemplateDefaultsToSeriesDraft({
          default_break_minutes: listItem.default_break_minutes,
          local_end_time: listItem.local_end_time,
          local_start_time: listItem.local_start_time,
          shift_type_code: listItem.shift_type_code,
          meeting_point: null,
          location_text: null,
        }, { force: true });
      }
    });
  } finally {
    seriesTemplateDefaultsApplying.value = false;
  }
}

async function hydrateSeriesTimeFieldsFromTemplate() {
  if (!seriesDraft.shift_template_id || (seriesDraft.local_start_time && seriesDraft.local_end_time)) {
    return;
  }
  await applySelectedShiftTemplatePreset();
}

function resolveSeriesErrorMessage(error: unknown) {
  if (!(error instanceof PlanningShiftsApiError)) {
    return 'sicherplan.customerPlansWizard.errors.seriesGenerateFailed';
  }
  switch (error.messageKey) {
    case 'errors.planning.shift_series.invalid_weekday_mask':
      return 'sicherplan.customerPlansWizard.errors.seriesWeekdayMaskInvalid';
    case 'errors.planning.shift_series.invalid_generation_window':
      return 'sicherplan.customerPlansWizard.errors.seriesGenerationWindowInvalid';
    case 'errors.planning.shift_series.plan_window_mismatch':
      return 'sicherplan.customerPlansWizard.errors.seriesShiftPlanWindowMismatch';
    case 'errors.planning.shift_series_exception.duplicate_date':
      return 'sicherplan.customerPlansWizard.errors.seriesExceptionDuplicateDate';
    case 'errors.planning.shift_series.invalid_shift_type_code':
      return 'sicherplan.customerPlansWizard.errors.seriesInvalidShiftTypeCode';
    case 'errors.planning.shift_series.invalid_timezone':
      return 'sicherplan.customerPlansWizard.errors.seriesInvalidTimezone';
    case 'errors.planning.shift_series_exception.override_times_required':
      return 'sicherplan.customerPlansWizard.errors.seriesExceptionOverrideTimesRequired';
    case 'errors.planning.shift_series_exception.outside_window':
      return 'sicherplan.customerPlansWizard.errors.seriesExceptionOutsideWindow';
    default:
      return 'sicherplan.customerPlansWizard.errors.seriesGenerateFailed';
  }
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
  const hadSelectedPlanningRecord = Boolean(selectedPlanningRecord.value || selectedExistingPlanningRecordId.value);
  withDraftSyncPaused(() => {
    planningFamily.value = family;
    planningEntityId.value = '';
    planningSelectionMode.value = 'use_existing';
  });
  planningRecordRows.value = [];
  planningRecordRowsError.value = '';
  if (hadSelectedPlanningRecord) {
    invalidateSelectedPlanningRecordForCurrentContext();
  } else {
    withDraftSyncPaused(() => {
      planningRecordDraft.planning_mode_code = planningModeCode.value;
      planningRecordDraft.trade_fair_detail_trade_fair_zone_id = '';
    });
  }
}

async function selectExistingPlanningEntity(entityId: string) {
  if (!entityId) {
    return;
  }
  const hadSelectedPlanningRecord = Boolean(selectedPlanningRecord.value || selectedExistingPlanningRecordId.value);
  const contextChanged = planningEntityId.value !== entityId;
  const invalidatedSelectedPlanningRecord = hadSelectedPlanningRecord && contextChanged;
  withDraftSyncPaused(() => {
    planningSelectionMode.value = 'use_existing';
    planningEntityId.value = entityId;
  });
  if (invalidatedSelectedPlanningRecord) {
    invalidateSelectedPlanningRecordForCurrentContext();
  } else {
    selectedPlanningRecord.value = null;
    selectedExistingPlanningRecordId.value = '';
    editingExistingPlanningRecordId.value = '';
    committedPlanningRecordId.value = '';
    planningRecordDraft.planning_mode_code = planningModeCode.value;
  }
  if (planningModeCode.value === 'trade_fair') {
    await refreshTradeFairZoneOptions(entityId);
  } else {
    await refreshTradeFairZoneOptions('');
  }
  await loadExistingPlanningRecordRows();
  setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningEntrySelected'));
  emit('step-ui-state', 'planning-record-overview', {
    dirty: invalidatedSelectedPlanningRecord ? false : hasPlanningRecordDraftContent(),
    error: '',
  });
}

async function onPlanningEntityChange(event: Event) {
  const entityId = (event.target as HTMLSelectElement).value;
  if (!entityId) {
    const hadSelectedPlanningRecord = Boolean(selectedPlanningRecord.value || selectedExistingPlanningRecordId.value);
    withDraftSyncPaused(() => {
      planningEntityId.value = '';
    });
    planningRecordRows.value = [];
    planningRecordRowsError.value = '';
    if (hadSelectedPlanningRecord) {
      invalidateSelectedPlanningRecordForCurrentContext();
    } else {
      selectedPlanningRecord.value = null;
      selectedExistingPlanningRecordId.value = '';
      editingExistingPlanningRecordId.value = '';
      committedPlanningRecordId.value = '';
    }
    await refreshTradeFairZoneOptions('');
    emit('step-ui-state', 'planning-record-overview', {
      dirty: hadSelectedPlanningRecord ? false : hasPlanningRecordDraftContent(),
      error: '',
    });
    return;
  }
  await selectExistingPlanningEntity(entityId);
}

async function hydrateExistingPlanningRecordSelection(planningRecordId: string) {
  if (!props.tenantId || !props.accessToken || !planningRecordId) {
    return;
  }
  if (hasHydratedSelectedPlanningRecord(planningRecordId)) {
    return;
  }
  const requestSeq = planningRecordDetailRequestSeq.value + 1;
  planningRecordDetailRequestSeq.value = requestSeq;
  selectedExistingPlanningRecordId.value = planningRecordId;
  committedPlanningRecordId.value = planningRecordId;
  const loadVersions = beginStepLoads('planningRecordDetail');
  stepLoadError.planningRecordDetail = '';
  try {
    const record = await getPlanningRecord(props.tenantId, planningRecordId, props.accessToken);
    if (
      requestSeq !== planningRecordDetailRequestSeq.value ||
      selectedExistingPlanningRecordId.value !== planningRecordId
    ) {
      return;
    }
    if (!planningRecordContextIsValid(record)) {
      stepLoadError.planningRecordDetail = $t('sicherplan.customerPlansWizard.errors.invalidPlanningRecordDetail');
      setFeedback('error', stepLoadError.planningRecordDetail);
      emit('step-ui-state', 'planning-record-overview', { error: 'invalid_record_detail' });
      return;
    }
    syncPlanningRecordDraft(record);
    selectedExistingPlanningRecordId.value = record.id;
    editingExistingPlanningRecordId.value = record.id;
    clearStepDraft('planning-record-overview');
    clearDraftRestoreMessage();
    await loadPlanningEntityOptions();
    if (
      requestSeq !== planningRecordDetailRequestSeq.value ||
      selectedExistingPlanningRecordId.value !== planningRecordId
    ) {
      return;
    }
    planningEntityId.value = planningEntityIdForRecord(record);
    ensureSelectedPlanningEntityOption(record);
    if (record.planning_mode_code === 'trade_fair') {
      await refreshTradeFairZoneOptions(record.trade_fair_detail?.trade_fair_id ?? '');
    } else {
      await refreshTradeFairZoneOptions('');
    }
    if (
      requestSeq !== planningRecordDetailRequestSeq.value ||
      selectedExistingPlanningRecordId.value !== planningRecordId
    ) {
      return;
    }
    lastLoadedStepContextKey = buildStepExternalContextKey({
      planningEntityId: planningEntityIdForRecord(record),
      planningEntityType: planningFamilyForRecord(record),
      planningModeCode: record.planning_mode_code,
      planningRecordId: record.id,
      shiftPlanId: '',
      seriesId: '',
    });
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningRecordSelected'));
    committedPlanningRecordId.value = record.id;
    emit('saved-context', {
      ...buildPlanningContextPatch(),
      planning_record_id: record.id,
    });
    emit('step-completion', 'planning-record-overview', true);
    emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
  } catch {
    stepLoadError.planningRecordDetail = $t('sicherplan.customerPlansWizard.errors.planningRecordLoad');
    setFeedback('error', stepLoadError.planningRecordDetail);
    emit('step-ui-state', 'planning-record-overview', { error: 'load_failed' });
  } finally {
    finishStepLoads(loadVersions);
  }
}

async function selectExistingPlanningRecordRow(planningRecordId: string) {
  await hydrateExistingPlanningRecordSelection(planningRecordId);
}

function openPlanningCreateModal() {
  setPlanningSelectionMode('create_new');
  planningCreateModal.open = true;
  void loadPlanningCreateReferenceOptions();
}

function onPlanningFamilyChange(event: Event) {
  setPlanningFamilySelection((event.target as HTMLSelectElement).value as PlanningEntityType);
}

async function selectShiftPlanRow(planId: string) {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  const loadVersions = beginStepLoads('shiftPlanDetail');
  try {
    const plan = await getShiftPlan(props.tenantId, planId, props.accessToken);
    syncShiftPlanDraft(plan);
    const persistedShiftPlanDraft = normalizeShiftPlanDraftPersistence(
      loadStepDraft<ShiftPlanDraftPersistence | Partial<typeof shiftPlanDraft>>('shift-plan'),
    );
    if (
      persistedShiftPlanDraft &&
      (!persistedShiftPlanDraft.selected_shift_plan_id || persistedShiftPlanDraft.selected_shift_plan_id !== plan.id)
    ) {
      clearStepDraft('shift-plan');
    }
    clearDraftRestoreMessage();
    emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
    setFeedback('neutral', '');
  } finally {
    finishStepLoads(loadVersions);
  }
}

function startNewShiftPlan() {
  selectedShiftPlan.value = null;
  clearStepDraft('shift-plan');
  clearDraftRestoreMessage();
  withDraftSyncPaused(() => {
    resetShiftPlanDraft();
  });
  if (props.wizardState.shift_plan_id) {
    emit('saved-context', { shift_plan_id: '' });
  }
  emit('step-completion', 'shift-plan', false);
  emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
}

async function selectSeriesRow(seriesId: string) {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  const loadVersions = beginStepLoads('seriesDetail', 'seriesExceptions');
  try {
    const [series, exceptions] = await Promise.all([
      getShiftSeries(props.tenantId, seriesId, props.accessToken),
      listShiftSeriesExceptions(props.tenantId, seriesId, props.accessToken),
    ]);
    syncSeriesDraft(series);
    await hydrateSeriesTimeFieldsFromTemplate();
    seriesExceptions.value = exceptions;
  } finally {
    finishStepLoads(loadVersions);
  }
}

async function loadPlanningEntityOptions() {
  if (!props.tenantId || !props.accessToken) {
    return;
  }
  const requestSeq = planningEntityOptionsRequestSeq.value + 1;
  planningEntityOptionsRequestSeq.value = requestSeq;
  const requestedFamily = planningFamily.value;
  const requestedPlanningEntityId = planningEntityId.value;
  const loadVersions = beginStepLoads('planningReferenceOptions');
  planningEntityLoading.value = true;
  planningEntityError.value = '';
  try {
    const options = await listPlanningSetupRecords(
      requestedFamily,
      props.tenantId,
      props.accessToken,
      { customer_id: props.customer.id },
    );
    if (requestSeq !== planningEntityOptionsRequestSeq.value || requestedFamily !== planningFamily.value) {
      return;
    }
    planningEntityOptions.value = options as PlanningListItem[];
    ensureSelectedPlanningEntityOption();
    const activePlanningEntityId = planningEntityId.value || requestedPlanningEntityId;
    if (activePlanningEntityId && planningEntityOptions.value.some((option) => option.id === activePlanningEntityId)) {
      planningEntityId.value = activePlanningEntityId;
    } else if (!activePlanningEntityId && !selectedPlanningRecord.value) {
      planningEntityId.value = '';
    }
  } catch {
    ensureSelectedPlanningEntityOption();
    planningEntityError.value = $t('sicherplan.customerPlansWizard.errors.planningEntityLoad');
  } finally {
    finishStepLoads(loadVersions);
    if (requestSeq === planningEntityOptionsRequestSeq.value) {
      planningEntityLoading.value = false;
    }
  }
}

async function loadExistingPlanningRecordRows(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id || !hasPlanningContext.value) {
    planningRecordRows.value = [];
    planningRecordRowsError.value = '';
    planningRecordRowsLoading.value = false;
    return;
  }
  const loadVersions = beginStepLoads('planningRecords');
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
    if (selectedExistingPlanningRecordId.value && !rows.some((row) => row.id === selectedExistingPlanningRecordId.value)) {
      selectedExistingPlanningRecordId.value = '';
      editingExistingPlanningRecordId.value = '';
      committedPlanningRecordId.value = '';
    }
  } catch {
    if (!isCurrent()) {
      return;
    }
    planningRecordRows.value = [];
    planningRecordRowsError.value = $t('sicherplan.customerPlansWizard.errors.planningRecordLoad');
  } finally {
    finishStepLoads(loadVersions, isCurrent);
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
  const loadVersions = beginStepLoads('orderReferenceOptions');
  try {
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
    const activeFunctionTypes = functionTypes.filter((row) => row.status === 'active' && row.archived_at == null);
    const activeQualificationTypes = qualificationTypes.filter((row) => row.status === 'active' && row.archived_at == null);
    serviceCategoryOptions.value = serviceCategories;
    requirementTypeOptions.value = requirementTypes as PlanningListItem[];
    patrolRouteOptions.value = patrolRoutes as PlanningListItem[];
    equipmentItemOptions.value = equipmentItems as PlanningCatalogRecordRead[];
    functionTypeOptions.value = activeFunctionTypes;
    qualificationTypeOptions.value = activeQualificationTypes;
  } finally {
    finishStepLoads(loadVersions, isCurrent);
  }
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
  const loadVersions = beginStepLoads('orderDetails');
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
    finishStepLoads(loadVersions, isCurrent);
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
  const loadVersions = beginStepLoads('orderDetails');
  stepLoadError.orderDetails = '';
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
    finishStepLoads(loadVersions);
    stepLoading.value = false;
    emit('step-ui-state', 'order-details', { loading: false });
  }
}

function clearStepLoadErrors() {
  Object.assign(stepLoadError, {
    demandGroups: '',
    equipmentLines: '',
    orderDetails: '',
    orderDocuments: '',
    planningDocuments: '',
    planningRecordDetail: '',
    planningRecords: '',
    requirementLines: '',
    series: '',
    shiftPlan: '',
  });
}

function beginStepLoads(...keys: StepLoadKey[]) {
  const versions = new Map<StepLoadKey, number>();
  for (const key of keys) {
    stepLoadRequestVersion[key] += 1;
    versions.set(key, stepLoadRequestVersion[key]);
    stepLoadState[key] = true;
  }
  return versions;
}

function finishStepLoads(versions: Map<StepLoadKey, number>, _isCurrent = () => true) {
  for (const [key, version] of versions) {
    if (stepLoadRequestVersion[key] === version) {
      stepLoadState[key] = false;
    }
  }
}

function markActiveStepLoadError(message: string) {
  if (orderStepActive.value) {
    stepLoadError.orderDetails = message;
  } else if (orderScopeDocumentsStepActive.value) {
    stepLoadError.equipmentLines = message;
    stepLoadError.requirementLines = message;
    stepLoadError.orderDocuments = message;
  } else if (planningRecordStepActive.value) {
    stepLoadError.planningRecords = message;
    stepLoadError.planningRecordDetail = message;
  } else if (planningRecordDocumentsStepActive.value) {
    stepLoadError.planningDocuments = message;
  } else if (shiftPlanStepActive.value) {
    stepLoadError.shiftPlan = message;
  } else if (seriesStepActive.value) {
    stepLoadError.series = message;
  } else if (demandGroupsStepActive.value) {
    stepLoadError.demandGroups = message;
  }
}

function createDemandGroupDraftRow(overrides: Partial<DemandGroupDraftRow> = {}): DemandGroupDraftRow {
  demandGroupDraftRowSequence += 1;
  return {
    function_type_id: '',
    id: `demand-group-draft-${demandGroupDraftRowSequence}`,
    mandatory_flag: true,
    min_qty: 1,
    qualification_type_id: '',
    remark: '',
    sort_order: demandGroupDraftRowSequence,
    target_qty: 1,
    ...overrides,
  };
}

function resetDemandGroupDialogDraft() {
  demandGroupDialog.function_type_id = '';
  demandGroupDialog.mandatory_flag = true;
  demandGroupDialog.min_qty = 1;
  demandGroupDialog.qualification_type_id = '';
  demandGroupDialog.remark = '';
  demandGroupDialog.sort_order = Math.max(1, demandGroupDraftRows.value.length + 1);
  demandGroupDialog.target_qty = 1;
}

function openNewDemandGroupDialog() {
  editingDemandGroupDraftId.value = '';
  resetDemandGroupDialogDraft();
  demandGroupValidationError.value = '';
  demandGroupDialog.open = true;
}

function openEditDemandGroupDialog(rowId: string) {
  const row = demandGroupDraftRows.value.find((entry) => entry.id === rowId);
  if (!row) {
    return;
  }
  editingDemandGroupDraftId.value = row.id;
  demandGroupDialog.function_type_id = row.function_type_id;
  demandGroupDialog.mandatory_flag = row.mandatory_flag;
  demandGroupDialog.min_qty = row.min_qty;
  demandGroupDialog.qualification_type_id = row.qualification_type_id;
  demandGroupDialog.remark = row.remark;
  demandGroupDialog.sort_order = row.sort_order;
  demandGroupDialog.target_qty = row.target_qty;
  demandGroupValidationError.value = '';
  demandGroupDialog.open = true;
}

function closeDemandGroupDialog() {
  demandGroupDialog.open = false;
  editingDemandGroupDraftId.value = '';
  resetDemandGroupDialogDraft();
}

function resetAggregateDemandGroupDialogDraft() {
  aggregateDemandGroupDialog.function_type_id = '';
  aggregateDemandGroupDialog.mandatory_flag = true;
  aggregateDemandGroupDialog.min_qty = 1;
  aggregateDemandGroupDialog.qualification_type_id = '';
  aggregateDemandGroupDialog.remark = '';
  aggregateDemandGroupDialog.sort_order = 1;
  aggregateDemandGroupDialog.target_qty = 1;
}

function resetShiftDemandGroupDialogDraft() {
  shiftDemandGroupDialogDraft.function_type_id = '';
  shiftDemandGroupDialogDraft.mandatory_flag = true;
  shiftDemandGroupDialogDraft.min_qty = 1;
  shiftDemandGroupDialogDraft.qualification_type_id = '';
  shiftDemandGroupDialogDraft.remark = '';
  shiftDemandGroupDialogDraft.sort_order = 1;
  shiftDemandGroupDialogDraft.target_qty = 1;
}

function openAggregateDemandGroupEditDialog(signatureKey: string) {
  const row = persistedDemandGroupSummaryRows.value.find((entry) => entry.signature_key === signatureKey);
  if (!row || row.has_locked_rows) {
    return;
  }
  selectedAggregateDemandGroupSignature.value = signatureKey;
  aggregateDemandGroupDialog.function_type_id = row.function_type_id;
  aggregateDemandGroupDialog.mandatory_flag = row.mandatory_flag;
  aggregateDemandGroupDialog.min_qty = row.min_qty;
  aggregateDemandGroupDialog.qualification_type_id = row.qualification_type_id;
  aggregateDemandGroupDialog.remark = row.remark;
  aggregateDemandGroupDialog.sort_order = row.sort_order;
  aggregateDemandGroupDialog.target_qty = row.target_qty;
  aggregateDemandGroupValidationError.value = '';
  aggregateDemandGroupDialog.open = true;
}

function closeAggregateDemandGroupEditDialog() {
  aggregateDemandGroupDialog.open = false;
  selectedAggregateDemandGroupSignature.value = '';
  aggregateDemandGroupValidationError.value = '';
  resetAggregateDemandGroupDialogDraft();
}

function openShiftDemandGroupEditDialog(signatureKey: string) {
  const row = persistedDemandGroupSummaryRows.value.find((entry) => entry.signature_key === signatureKey);
  if (!row) {
    return;
  }
  selectedAggregateDemandGroupSignature.value = signatureKey;
  selectedShiftDemandGroupId.value = row.shift_rows[0]?.demand_group_id || '';
  hydrateShiftDemandGroupDialogDraft();
  shiftDemandGroupValidationError.value = '';
  shiftDemandGroupDialog.open = true;
}

function closeShiftDemandGroupEditDialog() {
  shiftDemandGroupDialog.open = false;
  selectedShiftDemandGroupId.value = '';
  shiftDemandGroupValidationError.value = '';
  resetShiftDemandGroupDialogDraft();
  selectedAggregateDemandGroupSignature.value = '';
}

function hydrateShiftDemandGroupDialogDraft() {
  const row = selectedShiftDemandGroupRow.value;
  if (!row) {
    resetShiftDemandGroupDialogDraft();
    return;
  }
  shiftDemandGroupDialogDraft.function_type_id = row.function_type_id;
  shiftDemandGroupDialogDraft.mandatory_flag = row.mandatory_flag;
  shiftDemandGroupDialogDraft.min_qty = row.min_qty;
  shiftDemandGroupDialogDraft.qualification_type_id = row.qualification_type_id;
  shiftDemandGroupDialogDraft.remark = row.remark;
  shiftDemandGroupDialogDraft.sort_order = row.sort_order;
  shiftDemandGroupDialogDraft.target_qty = row.target_qty;
}

function buildDemandGroupCompositeKey(row: Pick<DemandGroupDraftRow, 'function_type_id' | 'qualification_type_id' | 'sort_order'>) {
  return [
    row.function_type_id.trim(),
    row.qualification_type_id.trim(),
    String(row.sort_order),
  ].join('|');
}

function submitDemandGroupDialog() {
  const candidate = {
    function_type_id: demandGroupDialog.function_type_id.trim(),
    mandatory_flag: demandGroupDialog.mandatory_flag,
    min_qty: Number(demandGroupDialog.min_qty),
    qualification_type_id: demandGroupDialog.qualification_type_id.trim(),
    remark: demandGroupDialog.remark.trim(),
    sort_order: Number(demandGroupDialog.sort_order),
    target_qty: Number(demandGroupDialog.target_qty),
  };
  if (!candidate.function_type_id) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsFunctionTypeRequired');
    return;
  }
  if (
    !Number.isInteger(candidate.sort_order) ||
    candidate.sort_order < 1 ||
    candidate.min_qty < 0 ||
    candidate.target_qty < 0
  ) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsInvalid');
    return;
  }
  if (candidate.target_qty < candidate.min_qty) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsMinExceedsTarget');
    return;
  }
  const candidateKey = buildDemandGroupCompositeKey(candidate);
  const duplicate = demandGroupDraftRows.value.some(
    (row) => row.id !== editingDemandGroupDraftId.value && buildDemandGroupCompositeKey(row) === candidateKey,
  );
  if (duplicate) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsDuplicateTemplate');
    return;
  }
  if (editingDemandGroupDraftId.value) {
    demandGroupDraftRows.value = demandGroupDraftRows.value.map((row) =>
      row.id === editingDemandGroupDraftId.value ? { ...row, ...candidate } : row,
    );
  } else {
    demandGroupDraftRows.value = [
      ...demandGroupDraftRows.value,
      createDemandGroupDraftRow(candidate),
    ];
  }
  closeDemandGroupDialog();
  demandGroupValidationError.value = '';
}

function removeDemandGroupDraftRow(rowId: string) {
  demandGroupDraftRows.value = demandGroupDraftRows.value.filter((row) => row.id !== rowId);
}

function buildDemandGroupTemplates(): DemandGroupBulkTemplate[] | null {
  const normalizedRows = demandGroupDraftRows.value.map((row) => ({
    ...row,
    function_type_id: row.function_type_id.trim(),
    qualification_type_id: row.qualification_type_id.trim(),
    remark: row.remark.trim(),
  }));
  if (!normalizedRows.length) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsEmpty');
    return null;
  }
  const duplicateSortOrders = new Set<number>();
  const seenSortOrders = new Set<number>();
  const compositeKeys = new Set<string>();
  for (const row of normalizedRows) {
    if (!row.function_type_id || row.min_qty < 0 || row.target_qty < 0 || row.sort_order < 1) {
      demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsInvalid');
      return null;
    }
    if (row.min_qty > row.target_qty) {
      demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsMinExceedsTarget');
      return null;
    }
    if (seenSortOrders.has(row.sort_order)) {
      duplicateSortOrders.add(row.sort_order);
    }
    seenSortOrders.add(row.sort_order);
    const compositeKey = buildDemandGroupCompositeKey(row);
    if (compositeKeys.has(compositeKey)) {
      demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsDuplicateTemplate');
      return null;
    }
    compositeKeys.add(compositeKey);
  }
  if (duplicateSortOrders.size) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsDuplicateSortOrder');
    return null;
  }
  demandGroupValidationError.value = '';
  return normalizedRows.map((row) => ({
    function_type_id: row.function_type_id,
    mandatory_flag: row.mandatory_flag,
    min_qty: row.min_qty,
    qualification_type_id: row.qualification_type_id || null,
    remark: row.remark || null,
    sort_order: row.sort_order,
    target_qty: row.target_qty,
  }));
}

function validateDemandGroupValues(
  candidate: {
    function_type_id: string;
    min_qty: number;
    sort_order: number;
    target_qty: number;
  },
  errorTarget: 'aggregate' | 'row',
) {
  const setError = (message: string) => {
    if (errorTarget === 'aggregate') {
      aggregateDemandGroupValidationError.value = message;
    } else {
      shiftDemandGroupValidationError.value = message;
    }
  };
  if (!candidate.function_type_id.trim()) {
    setError($t('sicherplan.customerPlansWizard.errors.demandGroupsFunctionTypeRequired'));
    return false;
  }
  if (!Number.isInteger(candidate.sort_order) || candidate.sort_order < 1 || candidate.min_qty < 0 || candidate.target_qty < 0) {
    setError($t('sicherplan.customerPlansWizard.errors.demandGroupsInvalid'));
    return false;
  }
  if (candidate.target_qty < candidate.min_qty) {
    setError($t('sicherplan.customerPlansWizard.errors.demandGroupsMinExceedsTarget'));
    return false;
  }
  setError('');
  return true;
}

async function reloadPersistedDemandGroups() {
  persistedDemandGroups.value = await loadPersistedDemandGroupsForCurrentScope({ forceReload: true });
}

async function loadDemandGroupFunctionTypeOptions() {
  if (!props.tenantId || !props.accessToken) {
    return [] as FunctionTypeRead[];
  }
  const cacheKey = props.tenantId;
  const cached = demandGroupsFunctionTypeCache.get(cacheKey);
  if (cached) {
    return cached;
  }
  const rows = await resolveDemandGroupsScopedRequest(`function-types:${cacheKey}`, async () => {
    const functionTypes = await listFunctionTypes(props.tenantId, props.accessToken);
    return functionTypes.filter((row) => row.status === 'active' && row.archived_at == null);
  });
  demandGroupsFunctionTypeCache.set(cacheKey, rows);
  return rows;
}

async function loadDemandGroupQualificationTypeOptions() {
  if (!props.tenantId || !props.accessToken) {
    return [] as QualificationTypeRead[];
  }
  const cacheKey = props.tenantId;
  const cached = demandGroupsQualificationTypeCache.get(cacheKey);
  if (cached) {
    return cached;
  }
  const rows = await resolveDemandGroupsScopedRequest(`qualification-types:${cacheKey}`, async () => {
    const qualificationTypes = await listQualificationTypes(props.tenantId, props.accessToken);
    return qualificationTypes.filter((row) => row.status === 'active' && row.archived_at == null);
  });
  demandGroupsQualificationTypeCache.set(cacheKey, rows);
  return rows;
}

async function loadDemandGroupShiftPlanSummary() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    return null;
  }
  const cacheKey = `${props.tenantId}:${props.wizardState.shift_plan_id}`;
  if (demandGroupsShiftPlanCache.has(cacheKey)) {
    return demandGroupsShiftPlanCache.get(cacheKey) ?? null;
  }
  const detail = await resolveDemandGroupsScopedRequest(
    `shift-plan:${cacheKey}`,
    () => getShiftPlan(props.tenantId, props.wizardState.shift_plan_id, props.accessToken),
  );
  demandGroupsShiftPlanCache.set(cacheKey, detail);
  return detail;
}

async function loadDemandGroupSeriesSummary() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.series_id) {
    return null;
  }
  const cacheKey = `${props.tenantId}:${props.wizardState.series_id}`;
  if (demandGroupsSeriesCache.has(cacheKey)) {
    return demandGroupsSeriesCache.get(cacheKey) ?? null;
  }
  const detail = await resolveDemandGroupsScopedRequest(
    `series:${cacheKey}`,
    () => getShiftSeries(props.tenantId, props.wizardState.series_id, props.accessToken),
  );
  demandGroupsSeriesCache.set(cacheKey, detail);
  return detail;
}

async function loadDemandGroupGeneratedShifts(contextKey: string) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    return [] as ShiftListItem[];
  }
  const cached = demandGroupsGeneratedShiftCache.get(contextKey);
  if (cached) {
    return cached;
  }
  const rows = await resolveDemandGroupsScopedRequest(`shifts:${contextKey}`, async () => {
    const shifts = await listShifts(props.tenantId, props.accessToken, {
      shift_plan_id: props.wizardState.shift_plan_id,
      shift_series_id: props.wizardState.series_id || undefined,
    });
    return shifts.filter((row) => row.source_kind_code === 'generated');
  });
  demandGroupsGeneratedShiftCache.set(contextKey, rows);
  return rows;
}

async function loadPersistedDemandGroupsForCurrentScope(options: { forceReload?: boolean } = {}) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id || !demandGroupGeneratedShifts.value.length) {
    return [] as DemandGroupRead[];
  }
  const contextKey = buildDemandGroupsStepContextKey();
  if (options.forceReload) {
    invalidateDemandGroupsScopedCache('persisted', contextKey);
  }
  const cached = demandGroupsPersistedCache.get(contextKey);
  if (cached) {
    return cached;
  }
  const rows = await resolveDemandGroupsScopedRequest(`persisted:${contextKey}`, async () => {
    const targetShiftIds = new Set(demandGroupGeneratedShifts.value.map((shift) => shift.id));
    const persistedRows = await listDemandGroups(props.tenantId, props.accessToken, {
      include_archived: false,
      shift_plan_id: props.wizardState.shift_plan_id,
    });
    return persistedRows.filter((row) => targetShiftIds.has(row.shift_id));
  });
  demandGroupsPersistedCache.set(contextKey, rows);
  return rows;
}

async function submitAggregateDemandGroupDialog() {
  const summaryRow = selectedAggregateDemandGroupRow.value;
  if (!summaryRow || !props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id || summaryRow.has_locked_rows) {
    return;
  }
  const candidate = {
    function_type_id: aggregateDemandGroupDialog.function_type_id.trim(),
    min_qty: Number(aggregateDemandGroupDialog.min_qty),
    sort_order: Number(aggregateDemandGroupDialog.sort_order),
    target_qty: Number(aggregateDemandGroupDialog.target_qty),
  };
  if (!validateDemandGroupValues(candidate, 'aggregate')) {
    return;
  }
  aggregateDemandGroupSaving.value = true;
  try {
    const result = await bulkUpdateDemandGroups(props.tenantId, props.accessToken, {
      tenant_id: props.tenantId,
      shift_plan_id: props.wizardState.shift_plan_id,
      shift_series_id: props.wizardState.series_id || null,
      match: {
        function_type_id: summaryRow.function_type_id,
        qualification_type_id: summaryRow.qualification_type_id || null,
        min_qty: summaryRow.min_qty,
        target_qty: summaryRow.target_qty,
        mandatory_flag: summaryRow.mandatory_flag,
        sort_order: summaryRow.sort_order,
        remark: summaryRow.remark || null,
      },
      patch: {
        function_type_id: candidate.function_type_id,
        qualification_type_id: aggregateDemandGroupDialog.qualification_type_id.trim() || null,
        mandatory_flag: aggregateDemandGroupDialog.mandatory_flag,
        min_qty: candidate.min_qty,
        remark: aggregateDemandGroupDialog.remark.trim() || null,
        sort_order: candidate.sort_order,
        target_qty: candidate.target_qty,
      },
      expected_demand_group_ids: summaryRow.demand_group_ids,
      expected_target_shift_count: summaryRow.total_shift_count,
    });
    demandGroupSummaryMessage.value = $t('sicherplan.customerPlansWizard.messages.demandGroupsBulkUpdatedSummary', {
      conflicts: result.conflict_count,
      matched: result.matched_count,
      updated: result.updated_count,
    } as never);
    invalidateDemandGroupsScopedCache('persisted', buildDemandGroupsStepContextKey());
    await reloadPersistedDemandGroups();
    emit('step-completion', 'demand-groups', persistedDemandGroupsCoverageComplete.value && demandGroupDraftRows.value.length === 0);
    closeAggregateDemandGroupEditDialog();
  } catch (error) {
    aggregateDemandGroupValidationError.value = error instanceof Error ? error.message : String(error);
  } finally {
    aggregateDemandGroupSaving.value = false;
  }
}

async function submitShiftDemandGroupDialog() {
  const row = selectedShiftDemandGroupRow.value;
  if (!row || row.locked || !props.tenantId || !props.accessToken) {
    return;
  }
  const candidate = {
    function_type_id: shiftDemandGroupDialogDraft.function_type_id.trim(),
    min_qty: Number(shiftDemandGroupDialogDraft.min_qty),
    sort_order: Number(shiftDemandGroupDialogDraft.sort_order),
    target_qty: Number(shiftDemandGroupDialogDraft.target_qty),
  };
  if (!validateDemandGroupValues(candidate, 'row')) {
    return;
  }
  shiftDemandGroupSaving.value = true;
  try {
    await updateDemandGroup(props.tenantId, props.accessToken, row.demand_group_id, {
      function_type_id: candidate.function_type_id,
      qualification_type_id: shiftDemandGroupDialogDraft.qualification_type_id.trim() || null,
      mandatory_flag: shiftDemandGroupDialogDraft.mandatory_flag,
      min_qty: candidate.min_qty,
      remark: shiftDemandGroupDialogDraft.remark.trim() || null,
      sort_order: candidate.sort_order,
      target_qty: candidate.target_qty,
      version_no: row.version_no,
    });
    demandGroupSummaryMessage.value = $t('sicherplan.customerPlansWizard.messages.demandGroupsShiftUpdatedSummary', {
      shift: row.shift_label,
    } as never);
    invalidateDemandGroupsScopedCache('persisted', buildDemandGroupsStepContextKey());
    await reloadPersistedDemandGroups();
    emit('step-completion', 'demand-groups', persistedDemandGroupsCoverageComplete.value && demandGroupDraftRows.value.length === 0);
    closeShiftDemandGroupEditDialog();
  } catch (error) {
    shiftDemandGroupValidationError.value = error instanceof Error ? error.message : String(error);
  } finally {
    shiftDemandGroupSaving.value = false;
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
    if (externalOrderEditRequested.value || persistedExistingEditDraft?.form) {
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
  const orderDetailVersions = beginStepLoads('orderDetails');
  const orderSectionVersions = beginStepLoads('equipmentLines', 'requirementLines', 'orderDocuments');
  stepLoadError.orderDetails = '';
  stepLoadError.equipmentLines = '';
  stepLoadError.requirementLines = '';
  stepLoadError.orderDocuments = '';
  let order: CustomerOrderRead | null = null;
  try {
    order = await getCustomerOrder(props.tenantId, props.wizardState.order_id, props.accessToken);
    if (!isCurrent()) {
      return;
    }
    orderSelectionMode.value = 'use_existing';
    selectedExistingOrderId.value = order.id;
    syncOrderDraft(order);
    finishStepLoads(orderDetailVersions, isCurrent);
    const [equipmentLinesResult, requirementLinesResult, attachmentsResult] = await Promise.allSettled([
      listOrderEquipmentLines(props.tenantId, props.wizardState.order_id, props.accessToken),
      listOrderRequirementLines(props.tenantId, props.wizardState.order_id, props.accessToken),
      listOrderAttachments(props.tenantId, props.wizardState.order_id, props.accessToken),
    ]);
    if (!isCurrent()) {
      return;
    }
    if (equipmentLinesResult.status === 'fulfilled') {
      orderEquipmentLines.value = equipmentLinesResult.value;
      stepLoadError.equipmentLines = '';
    } else {
      stepLoadError.equipmentLines = $t('sicherplan.customerPlansWizard.errors.stepLoad');
    }
    if (requirementLinesResult.status === 'fulfilled') {
      orderRequirementLines.value = requirementLinesResult.value;
      stepLoadError.requirementLines = '';
    } else {
      stepLoadError.requirementLines = $t('sicherplan.customerPlansWizard.errors.stepLoad');
    }
    if (attachmentsResult.status === 'fulfilled') {
      orderAttachments.value = attachmentsResult.value;
      stepLoadError.orderDocuments = '';
    } else {
      stepLoadError.orderDocuments = $t('sicherplan.customerPlansWizard.errors.stepLoad');
    }
  } finally {
    finishStepLoads(orderDetailVersions, isCurrent);
    finishStepLoads(orderSectionVersions, isCurrent);
  }
  if (persistedOrderDraft && order) {
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
  } else if (hasEquipmentLineDraftContent()) {
    // Keep the active unsaved draft while saved server rows refresh.
  } else {
    withDraftSyncPaused(() => {
      resetEquipmentLineDraft();
    });
  }
  if (persistedRequirementDraft) {
    applyRequirementLineDraftPersistence(persistedRequirementDraft);
  } else if (hasRequirementLineDraftContent()) {
    // Keep the active unsaved draft while saved server rows refresh.
  } else {
    withDraftSyncPaused(() => {
      resetRequirementLineDraft();
    });
  }
  if (persistedDocumentsDraft) {
    applyOrderDocumentsDraftPersistence(persistedDocumentsDraft);
  } else if (hasOrderAttachmentDraftContent()) {
    // Keep the active unsaved document draft while saved attachments refresh.
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
  const loadVersions = beginStepLoads('planningReferenceOptions');
  try {
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
  } finally {
    finishStepLoads(loadVersions, isCurrent);
  }
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
  ensureSelectedPlanningEntityOption();
  if (!selectedPlanningRecord.value && !planningEntityOptions.value.some((option) => option.id === planningEntityId.value)) {
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
  stepLoadError.planningRecords = '';
  stepLoadError.planningRecordDetail = '';
  stepLoadError.planningDocuments = '';
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
    if (hasStableLocalPlanningRecordSelectionForCurrentContext()) {
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
    const shouldAutoSelectSingleSavedRecord =
      planningRecordRows.value.length === 1 &&
      !hasContentfulPersistedPlanningRecordDraft &&
      !hasPlanningRecordDraftContent();
    if (shouldAutoSelectSingleSavedRecord) {
      const matchingRow = planningRecordRows.value[0];
      if (!matchingRow) {
        return;
      }
      const detailVersions = beginStepLoads('planningRecordDetail');
      try {
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
      } finally {
        finishStepLoads(detailVersions, isCurrent);
      }
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
  const detailVersions = beginStepLoads('planningRecordDetail', 'planningDocuments');
  let loadedPlanningRecord: PlanningRecordRead | null = null;
  try {
    const [record, attachments] = await Promise.all([
      getPlanningRecord(props.tenantId, props.wizardState.planning_record_id, props.accessToken),
      listPlanningRecordAttachments(props.tenantId, props.wizardState.planning_record_id, props.accessToken),
    ]);
    if (!isCurrent()) {
      return;
    }
    loadedPlanningRecord = record;
    syncPlanningRecordDraft(record);
    planningRecordAttachments.value = attachments;
  } finally {
    finishStepLoads(detailVersions, isCurrent);
  }
  if (
    loadedPlanningRecord &&
    persistedPlanningRecordDraft &&
    (!persistedPlanningRecordDraft.order_id || persistedPlanningRecordDraft.order_id === props.wizardState.order_id) &&
    planningRecordDraftMatchesRecord(persistedPlanningRecordDraft, loadedPlanningRecord)
  ) {
    applyPlanningRecordOverviewDraftPersistence(persistedPlanningRecordDraft);
    restoreDraftMessage();
  } else {
    clearStepDraft('planning-record-overview');
    clearDraftRestoreMessage();
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
  const loadVersions = beginStepLoads('shiftPlans', 'shiftReferenceOptions');
  try {
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
  } finally {
    finishStepLoads(loadVersions, isCurrent);
  }
}

async function loadSeriesReferenceOptions(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken) {
    shiftTemplateOptions.value = [];
    shiftTypeOptions.value = [];
    return;
  }
  const loadVersions = beginStepLoads('seriesReferenceOptions');
  try {
    const [templates, shiftTypes] = await Promise.all([
      listShiftTemplates(props.tenantId, props.accessToken, {}),
      listShiftTypeOptions(props.tenantId, props.accessToken),
    ]);
    if (!isCurrent()) {
      return;
    }
    shiftTemplateOptions.value = templates;
    shiftTypeOptions.value = shiftTypes;
  } finally {
    finishStepLoads(loadVersions, isCurrent);
  }
}

async function hydrateSeriesStepContext(isCurrent = () => true) {
  if (!props.tenantId || !props.accessToken) {
    selectedPlanningRecord.value = null;
    selectedShiftPlan.value = null;
    return;
  }
  const loadVersions = beginStepLoads('seriesContext');
  try {
    const planningRecordPromise = props.wizardState.planning_record_id
      ? getPlanningRecord(props.tenantId, props.wizardState.planning_record_id, props.accessToken)
      : Promise.resolve(null);
    const shiftPlanPromise = props.wizardState.shift_plan_id
      ? getShiftPlan(props.tenantId, props.wizardState.shift_plan_id, props.accessToken)
      : Promise.resolve(null);
    const [record, plan] = await Promise.all([planningRecordPromise, shiftPlanPromise]);
    if (!isCurrent()) {
      return;
    }
    if (record) {
      syncPlanningRecordDraft(record);
    } else {
      selectedPlanningRecord.value = null;
    }
    if (plan) {
      syncShiftPlanDraft(plan);
    } else {
      selectedShiftPlan.value = null;
    }
  } finally {
    finishStepLoads(loadVersions, isCurrent);
  }
}

async function loadShiftPlanState(isCurrent = () => true) {
  const persistedShiftPlanDraft = normalizeShiftPlanDraftPersistence(
    loadStepDraft<ShiftPlanDraftPersistence | Partial<typeof shiftPlanDraft>>('shift-plan'),
  );
  stepLoadError.shiftPlan = '';
  await loadShiftPlanningReferenceOptions(isCurrent);
  if (!isCurrent()) {
    return;
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    if (!isCurrent()) {
      return;
    }
    selectedShiftPlan.value = null;
    const defaultDraft = buildShiftPlanDefaultDraft();
    const hasContentfulPersistedShiftPlanDraft = hasContentfulShiftPlanDraftPersistence(
      persistedShiftPlanDraft,
      defaultDraft,
    );
    if (persistedShiftPlanDraft && hasContentfulPersistedShiftPlanDraft) {
      applyShiftPlanDraftPersistence(persistedShiftPlanDraft.draft);
      restoreDraftMessage();
    } else if (persistedShiftPlanDraft && !hasContentfulPersistedShiftPlanDraft) {
      clearStepDraft('shift-plan');
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
  const detailVersions = beginStepLoads('shiftPlanDetail');
  let plan: ShiftPlanRead | null = null;
  try {
    plan = await getShiftPlan(props.tenantId, props.wizardState.shift_plan_id, props.accessToken);
    if (!isCurrent()) {
      return;
    }
    syncShiftPlanDraft(plan);
  } finally {
    finishStepLoads(detailVersions, isCurrent);
  }
  if (!plan) {
    return;
  }
  const selectedPlanBaseline = buildSelectedShiftPlanBaseline(plan);
  if (
    persistedShiftPlanDraft &&
    persistedShiftPlanDraft.selected_shift_plan_id === props.wizardState.shift_plan_id &&
    hasContentfulShiftPlanDraftPersistence(persistedShiftPlanDraft, selectedPlanBaseline)
  ) {
    applyShiftPlanDraftPersistence(persistedShiftPlanDraft.draft);
    restoreDraftMessage();
  } else if (
    persistedShiftPlanDraft &&
    persistedShiftPlanDraft.selected_shift_plan_id === props.wizardState.shift_plan_id &&
    !hasContentfulShiftPlanDraftPersistence(persistedShiftPlanDraft, selectedPlanBaseline)
  ) {
    clearStepDraft('shift-plan');
  }
}

async function loadSeriesState(isCurrent = () => true) {
  const persistedSeriesDraft = loadStepDraft<SeriesExceptionsDraftPersistence>('series-exceptions');
  stepLoadError.series = '';
  await loadSeriesReferenceOptions(isCurrent);
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
        resetSeriesGenerationDraft();
        resetExceptionDraft();
      });
    }
    return;
  }
  const rowVersions = beginStepLoads('seriesRows');
  try {
    const listedSeries = await listShiftSeries(props.tenantId, props.wizardState.shift_plan_id, props.accessToken);
    if (!isCurrent()) {
      return;
    }
    seriesRows.value = listedSeries;
  } finally {
    finishStepLoads(rowVersions, isCurrent);
  }
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
        resetSeriesGenerationDraft();
        resetExceptionDraft();
      });
    }
    return;
  }
  const detailVersions = beginStepLoads('seriesDetail', 'seriesExceptions');
  try {
    const [series, exceptions] = await Promise.all([
      getShiftSeries(props.tenantId, props.wizardState.series_id, props.accessToken),
      listShiftSeriesExceptions(props.tenantId, props.wizardState.series_id, props.accessToken),
    ]);
    if (!isCurrent()) {
      return;
    }
    syncSeriesDraft(series);
    await hydrateSeriesTimeFieldsFromTemplate();
    seriesExceptions.value = exceptions;
  } finally {
    finishStepLoads(detailVersions, isCurrent);
  }
  if (persistedSeriesDraft) {
    applySeriesDraftPersistence(persistedSeriesDraft);
    restoreDraftMessage();
  }
}

async function loadDemandGroupsState(isCurrent = () => true) {
  stepLoadError.demandGroups = '';
  demandGroupValidationError.value = '';
  const persistedDemandGroupsDraft = loadStepDraft<DemandGroupsDraftPersistence>('demand-groups');
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    selectedShiftPlan.value = null;
    selectedSeries.value = null;
    demandGroupGeneratedShifts.value = [];
    persistedDemandGroups.value = [];
    demandGroupApplyResult.value = null;
    demandGroupSummaryMessage.value = '';
    demandGroupDraftRows.value = persistedDemandGroupsDraft?.rows?.length
      ? persistedDemandGroupsDraft.rows.map((row) => createDemandGroupDraftRow(row))
      : [];
    if (persistedDemandGroupsDraft?.rows?.length) {
      restoreDraftMessage();
    }
    emit('step-completion', 'demand-groups', false);
    return;
  }
  const loadVersions = beginStepLoads('demandGroups');
  try {
    const contextKey = buildDemandGroupsStepContextKey();
    const [functionTypes, qualificationTypes, shiftPlan, series, generatedShifts] = await Promise.all([
      loadDemandGroupFunctionTypeOptions(),
      loadDemandGroupQualificationTypeOptions(),
      loadDemandGroupShiftPlanSummary(),
      loadDemandGroupSeriesSummary(),
      loadDemandGroupGeneratedShifts(contextKey),
    ]);
    if (!isCurrent()) {
      return;
    }
    functionTypeOptions.value = functionTypes;
    qualificationTypeOptions.value = qualificationTypes;
    selectedShiftPlan.value = shiftPlan;
    selectedSeries.value = series;
    demandGroupGeneratedShifts.value = generatedShifts;
    if (demandGroupGeneratedShifts.value.length) {
      persistedDemandGroups.value = await loadPersistedDemandGroupsForCurrentScope();
      if (!isCurrent()) {
        return;
      }
    } else {
      persistedDemandGroups.value = [];
    }
    demandGroupApplyResult.value = null;
    demandGroupSummaryMessage.value = '';
    demandGroupDraftRows.value = persistedDemandGroupsDraft?.rows?.length
      ? persistedDemandGroupsDraft.rows.map((row) => createDemandGroupDraftRow(row))
      : [];
    if (persistedDemandGroupsDraft?.rows?.length) {
      restoreDraftMessage();
    }
    emit(
      'step-completion',
      'demand-groups',
      persistedDemandGroupsCoverageComplete.value && demandGroupDraftRows.value.length === 0,
    );
  } finally {
    finishStepLoads(loadVersions, isCurrent);
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
  clearStepLoadErrors();
  emit('step-ui-state', props.currentStepId, { loading: true, error: '' });
  stepLoading.value = true;
  try {
    if (orderStepActive.value) {
      await loadOrderReferenceOptions(isCurrent);
      await loadCustomerOrderRows(isCurrent);
      await loadOrderState(isCurrent);
    } else if (orderScopeDocumentsStepActive.value) {
      await loadOrderReferenceOptions(isCurrent);
      await loadOrderState(isCurrent);
    } else if (planningRecordStepActive.value || planningRecordDocumentsStepActive.value) {
      await loadOrderState(isCurrent);
      await loadPlanningRecordState(isCurrent);
    } else if (shiftPlanStepActive.value) {
      await loadPlanningRecordState(isCurrent);
      await loadShiftPlanState(isCurrent);
    } else if (seriesStepActive.value) {
      await hydrateSeriesStepContext(isCurrent);
      await loadSeriesState(isCurrent);
    } else if (demandGroupsStepActive.value) {
      await loadDemandGroupsState(isCurrent);
    }
  } catch {
    if (!isCurrent()) {
      return;
    }
    lastLoadedStepContextKey = '';
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.stepLoad'));
    markActiveStepLoadError($t('sicherplan.customerPlansWizard.errors.stepLoad'));
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

function validateEquipmentStep(): OrderScopeSectionValidationResult | null {
  if (hasEquipmentLineDraftInput()) {
    return {
      fieldErrors: {
        equipmentAction: formatOrderScopeSectionMessage('equipment', 'sicherplan.customerPlansWizard.errors.saveCurrentEquipmentLineBeforeContinue'),
      },
      focusSelector: selectedEquipmentLineId.value
        ? '[data-testid="customer-new-plan-update-equipment-line"]'
        : '[data-testid="customer-new-plan-save-equipment-line"]',
      message: formatOrderScopeSectionMessage('equipment', 'sicherplan.customerPlansWizard.errors.saveCurrentEquipmentLineBeforeContinue'),
      sectionId: 'equipment',
    };
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return null;
  }
  if (!orderEquipmentLines.value.length) {
    return {
      fieldErrors: {
        equipmentItem: $t('sicherplan.customerPlansWizard.errors.equipmentLineRequiredBeforeContinue'),
      },
      focusSelector: '[data-testid="customer-new-plan-equipment-item"]',
      message: formatOrderScopeSectionMessage('equipment', 'sicherplan.customerPlansWizard.errors.equipmentLineRequiredBeforeContinue'),
      sectionId: 'equipment',
    };
  }
  return null;
}

function validateRequirementStep(): OrderScopeSectionValidationResult | null {
  if (hasRequirementLineDraftInput()) {
    return {
      fieldErrors: {
        requirementsAction: formatOrderScopeSectionMessage('requirements', 'sicherplan.customerPlansWizard.errors.saveCurrentRequirementLineBeforeContinue'),
      },
      focusSelector: selectedRequirementLineId.value
        ? '[data-testid="customer-new-plan-update-requirement-line"]'
        : '[data-testid="customer-new-plan-save-requirement-line"]',
      message: formatOrderScopeSectionMessage('requirements', 'sicherplan.customerPlansWizard.errors.saveCurrentRequirementLineBeforeContinue'),
      sectionId: 'requirements',
    };
  }
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return null;
  }
  if (!orderRequirementLines.value.length) {
    return {
      fieldErrors: {
        requirementsType: $t('sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue'),
      },
      focusSelector: '[data-testid="customer-new-plan-requirement-type"]',
      message: formatOrderScopeSectionMessage('requirements', 'sicherplan.customerPlansWizard.errors.requirementLineRequiredBeforeContinue'),
      sectionId: 'requirements',
    };
  }
  return null;
}

function clearEquipmentLineDraftState() {
  clearOrderScopeValidationSection('equipment');
  withDraftSyncPaused(() => {
    resetEquipmentLineDraft();
  });
  clearStepDraft('equipment-lines');
  clearDraftRestoreMessage();
  emit('step-completion', 'order-scope-documents', orderEquipmentLines.value.length > 0);
  emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
}

function clearRequirementLineDraftState() {
  clearOrderScopeValidationSection('requirements');
  withDraftSyncPaused(() => {
    resetRequirementLineDraft();
  });
  clearStepDraft('requirement-lines');
  clearDraftRestoreMessage();
  emit('step-completion', 'order-scope-documents', orderRequirementLines.value.length > 0);
  emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
}

function clearOrderDocumentDraftState() {
  clearOrderScopeValidationSection('documents');
  withDraftSyncPaused(() => {
    resetOrderAttachmentDraft();
  });
  clearStepDraft('order-documents');
  clearDraftRestoreMessage();
  setFeedback('success', $t('sicherplan.customerPlansWizard.messages.orderDocumentDraftCleared'));
  emit('step-completion', 'order-scope-documents', orderAttachments.value.length > 0);
  emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
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

function clearPlanningRecordDraftState() {
  withDraftSyncPaused(() => {
    if (selectedPlanningRecord.value) {
      syncPlanningRecordDraft(selectedPlanningRecord.value);
    } else {
      resetPlanningRecordDraft();
    }
  });
  clearStepDraft('planning-record-overview');
  clearDraftRestoreMessage();
  setFeedback('neutral', '');
  const completed = Boolean(selectedPlanningRecord.value?.id || props.wizardState.planning_record_id);
  emit('step-completion', 'planning-record-overview', completed);
  emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
}

function validateDocumentsStep(): OrderScopeSectionValidationResult | null {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id || !hasAnyOrderDocumentDraftInput()) {
    return null;
  }

  const uploadDraftActive = hasOrderDocumentUploadDraftInput();
  const uploadDraftComplete = hasCompleteOrderDocumentUploadDraft();
  const linkDraftActive = hasOrderDocumentLinkDraftInput();
  const linkDraftComplete = hasCompleteOrderDocumentLinkDraft();
  const fieldErrors: Partial<Record<OrderScopeValidationFieldKey, string>> = {};
  let focusSelector = '';
  let messageKey = '';

  if (uploadDraftActive && !orderAttachmentDraft.title.trim()) {
    fieldErrors.documentsUploadTitle = $t('sicherplan.customerPlansWizard.errors.documentTitleRequired');
    focusSelector = '[data-testid="customer-new-plan-order-document-upload-title"]';
    messageKey ||= 'sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue';
  }

  if (uploadDraftActive && !(orderAttachmentDraft.content_base64 && orderAttachmentDraft.file_name)) {
    fieldErrors.documentsUploadFile = $t('sicherplan.customerPlansWizard.errors.documentFileRequired');
    focusSelector ||= '[data-testid="customer-new-plan-order-document-file"]';
    messageKey ||= 'sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue';
  }

  if (linkDraftActive && !orderAttachmentLink.document_id.trim()) {
    fieldErrors.documentsLinkSelection = $t('sicherplan.customerPlansWizard.errors.existingDocumentSelectionRequired');
    focusSelector ||= '[data-testid="customer-new-plan-order-document-picker-open"]';
    messageKey ||= 'sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue';
  }

  if (uploadDraftActive && uploadDraftComplete) {
    fieldErrors.documentsUploadAction = formatOrderScopeSectionMessage(
      'documents',
      'sicherplan.customerPlansWizard.errors.attachOrClearCurrentOrderDocumentBeforeContinue',
    );
    focusSelector ||= '[data-testid="customer-new-plan-attach-order-document"]';
    messageKey ||= 'sicherplan.customerPlansWizard.errors.attachOrClearCurrentOrderDocumentBeforeContinue';
  }

  if (linkDraftActive && linkDraftComplete) {
    fieldErrors.documentsLinkAction = formatOrderScopeSectionMessage(
      'documents',
      'sicherplan.customerPlansWizard.errors.linkOrClearCurrentOrderDocumentBeforeContinue',
    );
    focusSelector ||= '[data-testid="customer-new-plan-link-order-document"]';
    messageKey ||= 'sicherplan.customerPlansWizard.errors.linkOrClearCurrentOrderDocumentBeforeContinue';
  }

  if (uploadDraftActive && linkDraftActive) {
    messageKey = 'sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue';
  }

  if (!messageKey) {
    return null;
  }

  return {
    fieldErrors,
    focusSelector,
    message: formatOrderScopeSectionMessage('documents', messageKey),
    sectionId: 'documents',
  };
}

async function saveEquipmentLineDraft() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!equipmentLineDraft.equipment_item_id || equipmentLineDraft.required_qty < 1 || equipmentLineDuplicateActive.value) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.equipmentLineInvalid'));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-scope-documents', { loading: true, error: '' });
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
    clearOrderScopeValidationSection('equipment');
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
    emit('step-ui-state', 'order-scope-documents', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-scope-documents', { loading: false });
  }
}

function confirmRemove(messageKey: string) {
  return window.confirm($t(messageKey));
}

async function deleteEquipmentLine(line: OrderEquipmentLineRead) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!confirmRemove('sicherplan.customerPlansWizard.confirmRemoveEquipmentLine')) {
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-scope-documents', { loading: true, error: '' });
  try {
    await deleteOrderEquipmentLine(props.tenantId, props.wizardState.order_id, line.id, props.accessToken);
    orderEquipmentLines.value = await listOrderEquipmentLines(props.tenantId, props.wizardState.order_id, props.accessToken);
    clearOrderScopeValidationSection('equipment');
    if (selectedEquipmentLineId.value === line.id) {
      clearEquipmentLineDraftState();
    } else {
      emit('step-completion', 'order-scope-documents', orderEquipmentLines.value.length > 0);
    }
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.equipmentLineDeleted'));
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.equipmentLineDeleteFailed'));
    emit('step-ui-state', 'order-scope-documents', { error: 'delete_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-scope-documents', { loading: false });
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
    requirementLineDuplicateActive.value
  ) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.requirementLineInvalid'));
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-scope-documents', { loading: true, error: '' });
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
    clearOrderScopeValidationSection('requirements');
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
    emit('step-ui-state', 'order-scope-documents', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-scope-documents', { loading: false });
  }
}

async function deleteRequirementLine(line: OrderRequirementLineRead) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!confirmRemove('sicherplan.customerPlansWizard.confirmRemoveRequirementLine')) {
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-scope-documents', { loading: true, error: '' });
  try {
    await deleteOrderRequirementLine(props.tenantId, props.wizardState.order_id, line.id, props.accessToken);
    orderRequirementLines.value = await listOrderRequirementLines(props.tenantId, props.wizardState.order_id, props.accessToken);
    clearOrderScopeValidationSection('requirements');
    if (selectedRequirementLineId.value === line.id) {
      clearRequirementLineDraftState();
    } else {
      emit('step-completion', 'order-scope-documents', orderRequirementLines.value.length > 0);
    }
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.requirementLineDeleted'));
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.requirementLineDeleteFailed'));
    emit('step-ui-state', 'order-scope-documents', { error: 'delete_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-scope-documents', { loading: false });
  }
}

async function submitDocumentsStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasAnyOrderDocumentDraftInput()) {
    setFeedback('neutral', '');
    emit('step-completion', 'order-scope-documents', true);
    emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
    return true;
  }
  if (hasOrderAttachmentPartialDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.completeCurrentOrderDocumentDraftBeforeContinue'));
    emit('step-completion', 'order-scope-documents', false);
    emit('step-ui-state', 'order-scope-documents', { error: 'draft_incomplete' });
    return false;
  }
  if (hasCompleteOrderDocumentUploadDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.attachOrClearCurrentOrderDocumentBeforeContinue'));
    emit('step-completion', 'order-scope-documents', false);
    emit('step-ui-state', 'order-scope-documents', { error: 'draft_incomplete' });
    return false;
  }
  if (hasCompleteOrderDocumentLinkDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.linkOrClearCurrentOrderDocumentBeforeContinue'));
    emit('step-completion', 'order-scope-documents', false);
    emit('step-ui-state', 'order-scope-documents', { error: 'draft_incomplete' });
    return false;
  }
  setFeedback('neutral', '');
  emit('step-completion', 'order-scope-documents', true);
  emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
  return true;
}

async function submitOrderScopeDocumentsStep(): Promise<CustomerNewPlanStepSubmitResult> {
  const validationResults = [
    validateEquipmentStep(),
    validateRequirementStep(),
    validateDocumentsStep(),
  ].filter((result): result is OrderScopeSectionValidationResult => !!result);

  if (validationResults.length) {
    applyOrderScopeValidationResults(validationResults);
    revealOrderScopeValidationResult(validationResults[0]);
    setFeedback('error', validationResults[0].message);
    emit('step-completion', 'order-scope-documents', false);
    emit('step-ui-state', 'order-scope-documents', { dirty: true, error: 'validation_failed' });
    return {
      success: false,
      completedStepId: 'order-scope-documents',
      dirty: true,
      error: 'validation_failed',
    };
  }

  clearOrderScopeValidationState();
  const documentsValid = await submitDocumentsStep();
  if (!documentsValid) {
    return {
      success: false,
      completedStepId: 'order-scope-documents',
      dirty: true,
    };
  }
  emit('step-completion', 'order-scope-documents', true);
  emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
  return {
    success: true,
    completedStepId: 'order-scope-documents',
    dirty: false,
    error: '',
    savedContext: { order_id: props.wizardState.order_id },
  };
}

function documentPickerTestId(suffix: string) {
  const prefix = documentPicker.target === 'order' ? 'customer-new-plan-order-document' : 'customer-new-plan-planning-document';
  return `${prefix}-${suffix}`;
}

function documentTypeLabel(document: PlanningDocumentRead) {
  const documentType = (document as PlanningDocumentRead & { document_type?: { key?: string; name?: string }; document_type_id?: string | null }).document_type;
  return documentType?.name || documentType?.key || (document as PlanningDocumentRead & { document_type_id?: string | null }).document_type_id || '';
}

function latestFileName(document: PlanningDocumentRead) {
  const versions = (document as PlanningDocumentRead & { versions?: Array<{ file_name?: string; version_no?: number }> }).versions || [];
  return versions[versions.length - 1]?.file_name || document.source_label || '';
}

function documentPickerTitle(document: PlanningDocumentRead) {
  return document.title || latestFileName(document) || document.id;
}

function documentCustomerSummary(document: PlanningDocumentRead | null) {
  if (!document) {
    return '';
  }
  const sourceLabel = document.source_label?.trim() || '';
  return [
    document.title,
    sourceLabel && sourceLabel !== document.title ? sourceLabel : '',
    document.current_version_no ? `v${document.current_version_no}` : '',
    document.status,
  ]
    .filter(Boolean)
    .join(' · ');
}

function documentPickerMetadata(document: PlanningDocumentRead) {
  const typeLabel = documentTypeLabel(document);
  const fileName = latestFileName(document);
  const title = documentPickerTitle(document);
  return [
    typeLabel,
    fileName && fileName !== title ? fileName : '',
    document.id,
    document.current_version_no ? `v${document.current_version_no}` : '',
    document.status,
  ].filter(Boolean);
}

function orderAttachmentDisplayTitle(document: PlanningDocumentRead) {
  return document.relation_label?.trim() || document.title;
}

function planningRecordAttachmentDisplayTitle(document: PlanningDocumentRead) {
  return document.relation_label?.trim() || document.title || document.source_label || document.id;
}

function documentRowMetadata(document: PlanningDocumentRead) {
  const sourceLabel = document.source_label?.trim() || '';
  return [
    sourceLabel && sourceLabel !== document.title ? sourceLabel : '',
    document.current_version_no ? `v${document.current_version_no}` : '',
    document.status,
  ]
    .filter(Boolean)
    .join(' · ');
}

function openDocumentPicker(target: DocumentPickerTarget) {
  documentPicker.target = target;
  documentPicker.open = true;
  documentPicker.error = '';
  documentPicker.search =
    target === 'order' ? orderAttachmentLink.document_id.trim() : planningRecordAttachmentLink.document_id.trim();
  void searchDocumentPicker();
}

function closeDocumentPicker() {
  documentPicker.open = false;
}

async function searchDocumentPicker() {
  if (!props.tenantId || !props.accessToken) {
    documentPicker.results = [];
    return;
  }
  documentPicker.loading = true;
  documentPicker.error = '';
  try {
    documentPicker.results = await listDocuments(props.tenantId, props.accessToken, {
      limit: 20,
      search: documentPicker.search.trim(),
    });
  } catch {
    documentPicker.results = [];
    documentPicker.error = $t('sicherplan.customerPlansWizard.forms.documentPickerLoadFailed');
  } finally {
    documentPicker.loading = false;
  }
}

function selectDocumentForLink(document: PlanningDocumentRead) {
  if (documentPicker.target === 'order') {
    orderAttachmentLink.document_id = document.id;
    if (!orderAttachmentLink.label.trim()) {
      orderAttachmentLink.label = document.title;
    }
    selectedOrderLinkDocument.value = document;
  } else {
    planningRecordAttachmentLink.document_id = document.id;
    if (!planningRecordAttachmentLink.label.trim()) {
      planningRecordAttachmentLink.label = document.title;
    }
    selectedPlanningRecordLinkDocument.value = document;
  }
  closeDocumentPicker();
}

function clearSelectedOrderLinkDocument() {
  clearOrderScopeValidationSection('documents');
  orderAttachmentLink.document_id = '';
  selectedOrderLinkDocument.value = null;
}

function clearSelectedPlanningRecordLinkDocument() {
  planningRecordAttachmentLink.document_id = '';
  selectedPlanningRecordLinkDocument.value = null;
}

async function attachUploadedOrderDocument() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasCompleteOrderDocumentUploadDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentUploadIncomplete'));
    emit('step-ui-state', 'order-scope-documents', { error: 'draft_incomplete' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-scope-documents', { loading: true, error: '' });
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
    clearOrderScopeValidationSection('documents');
    withDraftSyncPaused(() => {
      resetOrderAttachmentDraft();
    });
    clearStepDraft('order-documents');
    clearDraftRestoreMessage();
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.orderDocumentAttached'));
    emit('step-completion', 'order-scope-documents', true);
    emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentSaveFailed'));
    emit('step-ui-state', 'order-scope-documents', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-scope-documents', { loading: false });
  }
}

async function linkExistingOrderDocument() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasCompleteOrderDocumentLinkDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentLinkIncomplete'));
    emit('step-ui-state', 'order-scope-documents', { error: 'draft_incomplete' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-scope-documents', { loading: true, error: '' });
  try {
    await linkOrderAttachment(props.tenantId, props.wizardState.order_id, props.accessToken, {
      document_id: orderAttachmentLink.document_id.trim(),
      label: orderAttachmentLink.label || null,
      tenant_id: props.tenantId,
    });
    orderAttachments.value = await listOrderAttachments(props.tenantId, props.wizardState.order_id, props.accessToken);
    clearOrderScopeValidationSection('documents');
    withDraftSyncPaused(() => {
      resetOrderAttachmentDraft();
    });
    clearStepDraft('order-documents');
    clearDraftRestoreMessage();
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.orderDocumentLinked'));
    emit('step-completion', 'order-scope-documents', true);
    emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentSaveFailed'));
    emit('step-ui-state', 'order-scope-documents', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-scope-documents', { loading: false });
  }
}

async function attachUploadedPlanningRecordDocument() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.planning_record_id) {
    return false;
  }
  if (!hasCompletePlanningRecordDocumentUploadDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningRecordDocumentUploadIncomplete'));
    emit('step-ui-state', 'planning-record-documents', { error: 'draft_incomplete' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'planning-record-documents', { loading: true, error: '' });
  try {
    await createPlanningRecordAttachment(props.tenantId, props.wizardState.planning_record_id, props.accessToken, {
      content_base64: planningRecordAttachmentDraft.content_base64,
      content_type: planningRecordAttachmentDraft.content_type,
      file_name: planningRecordAttachmentDraft.file_name,
      label: planningRecordAttachmentDraft.label || null,
      tenant_id: props.tenantId,
      title: planningRecordAttachmentDraft.title.trim(),
    });
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
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningRecordDocumentAttached'));
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

async function linkExistingPlanningRecordDocument() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.planning_record_id) {
    return false;
  }
  if (!hasCompletePlanningRecordDocumentLinkDraft()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningRecordDocumentLinkIncomplete'));
    emit('step-ui-state', 'planning-record-documents', { error: 'draft_incomplete' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'planning-record-documents', { loading: true, error: '' });
  try {
    await linkPlanningRecordAttachment(props.tenantId, props.wizardState.planning_record_id, props.accessToken, {
      document_id: planningRecordAttachmentLink.document_id.trim(),
      label: planningRecordAttachmentLink.label || null,
      tenant_id: props.tenantId,
    });
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
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningRecordDocumentLinked'));
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

async function unlinkOrderDocument(documentId: string) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!confirmRemove('sicherplan.customerPlansWizard.confirmUnlinkOrderDocument')) {
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'order-scope-documents', { loading: true, error: '' });
  try {
    await unlinkOrderAttachment(props.tenantId, props.wizardState.order_id, documentId, props.accessToken);
    orderAttachments.value = await listOrderAttachments(props.tenantId, props.wizardState.order_id, props.accessToken);
    clearOrderScopeValidationSection('documents');
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.orderDocumentUnlinked'));
    emit('step-ui-state', 'order-scope-documents', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.orderDocumentUnlinkFailed'));
    emit('step-ui-state', 'order-scope-documents', { error: 'delete_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'order-scope-documents', { loading: false });
  }
}

async function unlinkPlanningRecordDocument(documentId: string) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.planning_record_id) {
    return false;
  }
  if (!confirmRemove('sicherplan.customerPlansWizard.confirmUnlinkPlanningDocument')) {
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'planning-record-documents', { loading: true, error: '' });
  try {
    await unlinkPlanningRecordAttachment(props.tenantId, props.wizardState.planning_record_id, documentId, props.accessToken);
    planningRecordAttachments.value = await listPlanningRecordAttachments(
      props.tenantId,
      props.wizardState.planning_record_id,
      props.accessToken,
    );
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.planningRecordDocumentUnlinked'));
    emit('step-ui-state', 'planning-record-documents', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningRecordDocumentUnlinkFailed'));
    emit('step-ui-state', 'planning-record-documents', { error: 'delete_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'planning-record-documents', { loading: false });
  }
}

async function savePlanningRecordDraftOrSelection() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.order_id) {
    return false;
  }
  if (!hasPlanningContext.value) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.selectOrCreatePlanningContextBeforeContinue'));
    validatePlanningRecordFields();
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { error: 'planning_context_required' });
    return false;
  }
  planningRecordDraft.planning_mode_code = planningModeCode.value;
  if (!validatePlanningRecordFields()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.planningRecordValidationFailed'));
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { error: 'validation_failed' });
    return false;
  }
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
    const existingPlanningRecord = selectedPlanningRecord.value;
    const saved = existingPlanningRecord
      ? await updatePlanningRecord(props.tenantId, existingPlanningRecord.id, props.accessToken, payload)
      : await createPlanningRecord(props.tenantId, props.accessToken, payload);
    syncPlanningRecordDraft(saved);
    planningRecordDirty.value = false;
    clearPlanningRecordFieldErrors();
    clearStepDraft('planning-record-overview');
    clearDraftRestoreMessage();
    selectedExistingPlanningRecordId.value = saved.id;
    editingExistingPlanningRecordId.value = saved.id;
    committedPlanningRecordId.value = saved.id;
    emit('saved-context', {
      ...buildPlanningContextPatch(),
      planning_record_id: saved.id,
    });
    setFeedback(
      'success',
      $t(
        existingPlanningRecord
          ? 'sicherplan.customerPlansWizard.messages.planningRecordUpdated'
          : 'sicherplan.customerPlansWizard.messages.planningRecordSelected',
      ),
    );
    emit('step-completion', 'planning-record-overview', true);
    emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
    await loadExistingPlanningRecordRows();
    selectedExistingPlanningRecordId.value = saved.id;
    editingExistingPlanningRecordId.value = saved.id;
    committedPlanningRecordId.value = saved.id;
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

async function submitPlanningRecordStep() {
  if (!hasPlanningContext.value) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.selectOrCreatePlanningContextBeforeContinue'));
    validatePlanningRecordFields();
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { error: 'planning_context_required' });
    return false;
  }
  if (planningRecordDirty.value) {
    validatePlanningRecordFields();
    const messageKey = editingExistingPlanningRecordId.value
      ? 'saveOrCancelPlanningRecordEditBeforeContinue'
      : 'savePlanningRecordBeforeContinue';
    setFeedback('error', $t(`sicherplan.customerPlansWizard.errors.${messageKey}` as never));
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { dirty: true, error: 'save_required' });
    return false;
  }
  if (!hasCommittedPlanningRecordSelection() && !props.wizardState.planning_record_id) {
    validatePlanningRecordFields();
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.savePlanningRecordBeforeContinue'));
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { error: 'save_required' });
    return false;
  }
  if (selectedPlanningRecord.value?.id && !hasCommittedPlanningRecordSelection()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.savePlanningRecordBeforeContinue'));
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { error: 'save_required' });
    return false;
  }
  if (selectedExistingPlanningRecordId.value && !hasCommittedPlanningRecordSelection()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.savePlanningRecordBeforeContinue'));
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { error: 'save_required' });
    return false;
  }
  emit('step-completion', 'planning-record-overview', true);
  clearPlanningRecordFieldErrors();
  emit('step-ui-state', 'planning-record-overview', { dirty: false, error: '' });
  return true;
}

async function submitPlanningRecordDocumentsStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.planning_record_id) {
    return false;
  }
  if (hasAnyPlanningRecordDocumentDraftInput()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.completeCurrentPlanningDocumentDraftBeforeContinue'));
    emit('step-completion', 'planning-record-documents', false);
    emit('step-ui-state', 'planning-record-documents', { error: 'draft_incomplete' });
    return false;
  }
  setFeedback('neutral', '');
  emit('step-completion', 'planning-record-documents', true);
  emit('step-ui-state', 'planning-record-documents', { dirty: false, error: '' });
  return true;
}

async function submitShiftPlanStep(): Promise<CustomerNewPlanStepSubmitResult> {
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
    emit('step-completion', 'shift-plan', true);
    emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
    return {
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: selectedShiftPlan.value.id },
    };
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
    clearDemandGroupsRequestCaches();
    clearStepDraft('shift-plan');
    clearDraftRestoreMessage();
    shiftPlanRows.value = await listShiftPlans(props.tenantId, props.accessToken, { planning_record_id: props.wizardState.planning_record_id });
    emit('step-completion', 'shift-plan', true);
    emit('step-ui-state', 'shift-plan', { dirty: false, error: '' });
    return {
      success: true,
      completedStepId: 'shift-plan',
      dirty: false,
      error: '',
      savedContext: { shift_plan_id: saved.id },
    };
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

function buildSeriesCompatibilityTemplateCode() {
  const start = normalizeSeriesTimeValue(seriesDraft.local_start_time).replace(':', '');
  const end = normalizeSeriesTimeValue(seriesDraft.local_end_time).replace(':', '');
  const shiftType = seriesDraft.shift_type_code.trim() || 'shift';
  return `OW_${start}_${end}_${shiftType}_${seriesDraft.default_break_minutes}`.replace(/[^A-Za-z0-9_]/g, '_').slice(0, 80);
}

function findCompatibleShiftTemplate() {
  const start = normalizeSeriesTimeValue(seriesDraft.local_start_time);
  const end = normalizeSeriesTimeValue(seriesDraft.local_end_time);
  const shiftType = seriesDraft.shift_type_code.trim();
  return shiftTemplateOptions.value.find((row) =>
    row.code === buildSeriesCompatibilityTemplateCode() ||
    (
      normalizeSeriesTimeValue(row.local_start_time) === start &&
      normalizeSeriesTimeValue(row.local_end_time) === end &&
      row.default_break_minutes === seriesDraft.default_break_minutes &&
      row.shift_type_code === shiftType
    ),
  ) ?? null;
}

function selectedTemplateMatchesSeriesTiming() {
  const template = shiftTemplateOptions.value.find((row) => row.id === seriesDraft.shift_template_id);
  if (!template) {
    return false;
  }
  return (
    normalizeSeriesTimeValue(template.local_start_time) === normalizeSeriesTimeValue(seriesDraft.local_start_time) &&
    normalizeSeriesTimeValue(template.local_end_time) === normalizeSeriesTimeValue(seriesDraft.local_end_time) &&
    template.default_break_minutes === seriesDraft.default_break_minutes &&
    template.shift_type_code === seriesDraft.shift_type_code
  );
}

async function ensureSeriesCompatibilityTemplate() {
  if (seriesDraft.shift_template_id && selectedTemplateMatchesSeriesTiming()) {
    return seriesDraft.shift_template_id;
  }
  const reusableTemplate = findCompatibleShiftTemplate();
  if (reusableTemplate) {
    seriesDraft.shift_template_id = reusableTemplate.id;
    return reusableTemplate.id;
  }
  const code = buildSeriesCompatibilityTemplateCode();
  const created = await createShiftTemplate(props.tenantId, props.accessToken, {
    tenant_id: props.tenantId,
    code,
    label: `${$t('sicherplan.customerPlansWizard.forms.seriesTemplateGeneratedLabel')} ${seriesDraft.local_start_time}-${seriesDraft.local_end_time}`,
    local_start_time: seriesDraft.local_start_time,
    local_end_time: seriesDraft.local_end_time,
    default_break_minutes: seriesDraft.default_break_minutes,
    shift_type_code: seriesDraft.shift_type_code,
    meeting_point: null,
    location_text: null,
    notes: $t('sicherplan.customerPlansWizard.forms.seriesTemplateGeneratedNote'),
  });
  shiftTemplateDetailCache[created.id] = created;
  shiftTemplateOptions.value = await listShiftTemplates(props.tenantId, props.accessToken, {});
  seriesDraft.shift_template_id = created.id;
  return created.id;
}

function validateSeriesDraft() {
  clearSeriesFieldErrors();
  if (!seriesDraft.label.trim() || !seriesDraft.date_from || !seriesDraft.date_to || seriesDraft.date_to < seriesDraft.date_from) {
    seriesFieldErrors.dateRange = $t('sicherplan.customerPlansWizard.errors.seriesDateRangeInvalid');
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.seriesInvalid'));
    return false;
  }
  if (!seriesDraft.local_start_time.trim()) {
    seriesFieldErrors.startTime = $t('sicherplan.customerPlansWizard.errors.seriesStartTimeRequired');
    setFeedback('error', seriesFieldErrors.startTime);
    return false;
  }
  if (!seriesDraft.local_end_time.trim()) {
    seriesFieldErrors.endTime = $t('sicherplan.customerPlansWizard.errors.seriesEndTimeRequired');
    setFeedback('error', seriesFieldErrors.endTime);
    return false;
  }
  if (seriesDraft.local_end_time <= seriesDraft.local_start_time) {
    seriesFieldErrors.endTime = $t('sicherplan.customerPlansWizard.errors.seriesEndTimeAfterStart');
    setFeedback('error', seriesFieldErrors.endTime);
    return false;
  }
  if (!seriesDraft.shift_type_code.trim()) {
    seriesFieldErrors.shiftType = $t('sicherplan.customerPlansWizard.errors.seriesShiftTypeRequired');
    setFeedback('error', seriesFieldErrors.shiftType);
    return false;
  }
  if (seriesDraft.default_break_minutes < 0) {
    seriesFieldErrors.defaultBreak = $t('sicherplan.customerPlansWizard.errors.seriesDefaultBreakInvalid');
    setFeedback('error', seriesFieldErrors.defaultBreak);
    return false;
  }
  if (seriesWeekdayMaskRequired.value && (!/^[01]{7}$/.test(seriesDraft.weekday_mask) || !seriesDraft.weekday_mask.includes('1'))) {
    seriesFieldErrors.weekdayMask = $t('sicherplan.customerPlansWizard.errors.seriesWeekdaySelectionRequired');
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.seriesWeekdayMaskInvalid'));
    return false;
  }
  if (
    selectedShiftPlanSummary.value &&
    (seriesDraft.date_from < selectedShiftPlanSummary.value.planning_from ||
      seriesDraft.date_to > selectedShiftPlanSummary.value.planning_to)
  ) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.seriesShiftPlanWindowMismatch'));
    return false;
  }
  return true;
}

function validateExceptionDraft() {
  if (!exceptionDraft.exception_date) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.exceptionDateRequired'));
    return false;
  }
  if (!exceptionDraft.action_code.trim()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.exceptionActionRequired'));
    return false;
  }
  if (
    exceptionOverrideActive.value &&
    (!exceptionDraft.override_local_start_time.trim() || !exceptionDraft.override_local_end_time.trim())
  ) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.seriesExceptionOverrideTimesRequired'));
    return false;
  }
  return true;
}

function buildSeriesPayload() {
  return {
    tenant_id: props.tenantId,
    shift_plan_id: props.wizardState.shift_plan_id,
    shift_template_id: seriesDraft.shift_template_id,
    label: seriesDraft.label.trim(),
    recurrence_code: seriesDraft.recurrence_code,
    interval_count: seriesDraft.interval_count,
    weekday_mask: seriesWeekdayMaskRequired.value ? seriesDraft.weekday_mask : null,
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
}

function buildExceptionPayload() {
  return {
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
    ...(selectedExceptionId.value
      ? { version_no: seriesExceptions.value.find((row) => row.id === selectedExceptionId.value)?.version_no }
      : {}),
  };
}

async function saveSeriesDraft() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    return false;
  }
  if (seriesDraft.shift_template_id && (!seriesDraft.local_start_time || !seriesDraft.local_end_time || !seriesDraft.shift_type_code)) {
    await applySelectedShiftTemplatePreset();
  }
  if (!validateSeriesDraft()) {
    emit('step-completion', 'series-exceptions', false);
    emit('step-ui-state', 'series-exceptions', { error: 'validation_failed' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'series-exceptions', { loading: true, error: '' });
  try {
    await ensureSeriesCompatibilityTemplate();
    const updatingExistingSeries = Boolean(selectedSeries.value);
    const savedSeries = updatingExistingSeries
      ? await updateShiftSeries(props.tenantId, selectedSeries.value!.id, props.accessToken, buildSeriesPayload())
      : await createShiftSeries(props.tenantId, props.wizardState.shift_plan_id, props.accessToken, buildSeriesPayload());
    syncSeriesDraft(savedSeries);
    clearDemandGroupsRequestCaches();
    emit('saved-context', { series_id: savedSeries.id });
    seriesRows.value = await listShiftSeries(props.tenantId, props.wizardState.shift_plan_id, props.accessToken);
    seriesExceptions.value = await listShiftSeriesExceptions(props.tenantId, savedSeries.id, props.accessToken);
    clearStepDraft('series-exceptions');
    clearDraftRestoreMessage();
    setFeedback('success', $t(updatingExistingSeries ? 'sicherplan.customerPlansWizard.messages.seriesUpdated' : 'sicherplan.customerPlansWizard.messages.seriesSaved'));
    emit('step-completion', 'series-exceptions', true);
    emit('step-ui-state', 'series-exceptions', { dirty: false, error: '' });
    return true;
  } catch (error) {
    setFeedback('error', $t(resolveSeriesErrorMessage(error)));
    emit('step-ui-state', 'series-exceptions', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'series-exceptions', { loading: false });
  }
}

async function saveExceptionDraft() {
  if (!props.tenantId || !props.accessToken || !selectedSeries.value?.id) {
    return false;
  }
  if (!validateExceptionDraft()) {
    emit('step-ui-state', 'series-exceptions', { error: 'validation_failed' });
    return false;
  }
  exceptionModal.saving = true;
  emit('step-ui-state', 'series-exceptions', { loading: true, error: '' });
  try {
    const savedException = selectedExceptionId.value
      ? await updateShiftSeriesException(props.tenantId, selectedExceptionId.value, props.accessToken, buildExceptionPayload())
      : await createShiftSeriesException(props.tenantId, selectedSeries.value.id, props.accessToken, buildExceptionPayload());
    clearDemandGroupsRequestCaches();
    seriesExceptions.value = await listShiftSeriesExceptions(props.tenantId, savedException.shift_series_id, props.accessToken);
    closeExceptionModal();
    clearStepDraft('series-exceptions');
    clearDraftRestoreMessage();
    setFeedback(
      'success',
      $t(
        selectedExceptionId.value
          ? 'sicherplan.customerPlansWizard.messages.exceptionSaved'
          : 'sicherplan.customerPlansWizard.messages.exceptionSaved',
      ),
    );
    emit('step-ui-state', 'series-exceptions', { dirty: false, error: '' });
    return true;
  } catch (error) {
    setFeedback('error', $t(resolveSeriesErrorMessage(error)));
    emit('step-ui-state', 'series-exceptions', { error: 'save_failed' });
    return false;
  } finally {
    exceptionModal.saving = false;
    emit('step-ui-state', 'series-exceptions', { loading: false });
  }
}

async function deleteExceptionRow(row: ShiftSeriesExceptionRead) {
  if (!props.tenantId || !props.accessToken) {
    return false;
  }
  if (!confirmRemove('sicherplan.customerPlansWizard.confirmDeleteException')) {
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'series-exceptions', { loading: true, error: '' });
  try {
    await deleteShiftSeriesException(props.tenantId, row.id, props.accessToken);
    clearDemandGroupsRequestCaches();
    seriesExceptions.value = await listShiftSeriesExceptions(props.tenantId, row.shift_series_id, props.accessToken);
    if (selectedExceptionId.value === row.id) {
      closeExceptionModal();
    }
    setFeedback('success', $t('sicherplan.customerPlansWizard.messages.exceptionDeleted'));
    emit('step-ui-state', 'series-exceptions', { dirty: false, error: '' });
    return true;
  } catch {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.exceptionDeleteFailed'));
    emit('step-ui-state', 'series-exceptions', { error: 'delete_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'series-exceptions', { loading: false });
  }
}

function hasUnsavedSeriesChanges() {
  if (!selectedSeries.value) {
    return hasSeriesDraftContent();
  }
  return (
    seriesDraft.label !== selectedSeries.value.label ||
    seriesDraft.shift_template_id !== selectedSeries.value.shift_template_id ||
    seriesDraft.recurrence_code !== selectedSeries.value.recurrence_code ||
    seriesDraft.interval_count !== selectedSeries.value.interval_count ||
    seriesDraft.weekday_mask !== (selectedSeries.value.weekday_mask ?? '1111100') ||
    seriesDraft.timezone !== selectedSeries.value.timezone ||
    seriesDraft.date_from !== selectedSeries.value.date_from ||
    seriesDraft.date_to !== selectedSeries.value.date_to ||
    seriesDraft.default_break_minutes !== (selectedSeries.value.default_break_minutes ?? 30) ||
    seriesDraft.shift_type_code !== (selectedSeries.value.shift_type_code ?? '') ||
    !selectedTemplateMatchesSeriesTiming() ||
    seriesDraft.meeting_point !== (selectedSeries.value.meeting_point ?? '') ||
    seriesDraft.location_text !== (selectedSeries.value.location_text ?? '') ||
    seriesDraft.notes !== (selectedSeries.value.notes ?? '') ||
    seriesDraft.customer_visible_flag !== selectedSeries.value.customer_visible_flag ||
    seriesDraft.subcontractor_visible_flag !== selectedSeries.value.subcontractor_visible_flag ||
    seriesDraft.stealth_mode_flag !== selectedSeries.value.stealth_mode_flag ||
    seriesDraft.release_state !== selectedSeries.value.release_state
  );
}

async function submitSeriesStep() {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    return false;
  }
  if (hasUnsavedSeriesChanges()) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.saveCurrentSeriesBeforeContinue'));
    emit('step-ui-state', 'series-exceptions', { dirty: true, error: 'save_required' });
    return false;
  }
  if (!selectedSeries.value?.id) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.saveCurrentSeriesBeforeContinue'));
    emit('step-ui-state', 'series-exceptions', { error: 'save_required' });
    return false;
  }
  if (exceptionModal.open) {
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.saveOrCancelCurrentExceptionBeforeContinue'));
    emit('step-ui-state', 'series-exceptions', { error: 'save_required' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'series-exceptions', { loading: true, error: '' });
  try {
    const generationFrom = seriesGenerationDraft.from_date || selectedSeries.value.date_from;
    const generationTo = seriesGenerationDraft.to_date || selectedSeries.value.date_to;
    if (
      !generationFrom ||
      !generationTo ||
      generationTo < generationFrom ||
      generationFrom < selectedSeries.value.date_from ||
      generationTo > selectedSeries.value.date_to
    ) {
      setFeedback('error', $t('sicherplan.customerPlansWizard.errors.seriesGenerationWindowInvalid'));
      emit('step-ui-state', 'series-exceptions', { error: 'generation_window_invalid' });
      return false;
    }
    clearStepDraft('series-exceptions');
    clearDraftRestoreMessage();
    await generateShiftSeries(props.tenantId, selectedSeries.value.id, props.accessToken, {
      from_date: generationFrom,
      regenerate_existing: seriesGenerationDraft.regenerate_existing,
      to_date: generationTo,
    });
    clearDemandGroupsRequestCaches();
    emit('step-completion', 'series-exceptions', true);
    emit('step-ui-state', 'series-exceptions', { dirty: false, error: '' });
    return {
      completedStepId: 'series-exceptions',
      dirty: false,
      error: '',
      success: true,
    };
  } catch (error) {
    setFeedback('error', $t(resolveSeriesErrorMessage(error)));
    emit('step-ui-state', 'series-exceptions', { error: 'save_failed' });
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'series-exceptions', { loading: false });
  }
}

async function submitDemandGroupsStep(): Promise<CustomerNewPlanStepSubmitResult> {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsMissingShiftPlan');
    emit('step-ui-state', 'demand-groups', { error: 'missing_shift_plan' });
    return false;
  }
  if (!demandGroupDraftRows.value.length) {
    demandGroupValidationError.value = persistedDemandGroupSummaryRows.value.length
      ? $t('sicherplan.customerPlansWizard.errors.demandGroupsNoPendingTemplates')
      : $t('sicherplan.customerPlansWizard.errors.demandGroupsEmpty');
    emit('step-ui-state', 'demand-groups', { error: 'validation_failed' });
    return false;
  }
  if (!demandGroupsCanApply.value) {
    demandGroupValidationError.value = $t('sicherplan.customerPlansWizard.errors.demandGroupsNoGeneratedShifts');
    emit('step-ui-state', 'demand-groups', { error: 'no_generated_shifts' });
    return false;
  }
  const templates = buildDemandGroupTemplates();
  if (!templates) {
    emit('step-ui-state', 'demand-groups', { error: 'validation_failed' });
    return false;
  }
  stepLoading.value = true;
  emit('step-ui-state', 'demand-groups', { loading: true, error: '' });
  try {
    const result = await bulkApplyDemandGroups(props.tenantId, props.accessToken, {
      apply_mode: 'upsert_matching',
      demand_groups: templates,
      shift_plan_id: props.wizardState.shift_plan_id,
      shift_series_id: props.wizardState.series_id || null,
      tenant_id: props.tenantId,
    });
    demandGroupApplyResult.value = result;
    demandGroupSummaryMessage.value = $t('sicherplan.customerPlansWizard.messages.demandGroupsAppliedSummary', {
      created: result.created_count,
      skipped: result.skipped_count,
      updated: result.updated_count,
    } as never);
    demandGroupDraftWatchMuted.value = true;
    demandGroupDraftRows.value = [];
    clearStepDraft('demand-groups');
    clearDraftRestoreMessage();
    invalidateDemandGroupsScopedCache('persisted', buildDemandGroupsStepContextKey());
    await reloadPersistedDemandGroups();
    emit('step-completion', 'demand-groups', true);
    emit('step-ui-state', 'demand-groups', { dirty: false, error: '' });
    return {
      completedStepId: 'demand-groups',
      dirty: false,
      error: '',
      success: true,
    };
  } catch {
    demandGroupSummaryMessage.value = '';
    emit('step-ui-state', 'demand-groups', { error: 'save_failed' });
    setFeedback('error', $t('sicherplan.customerPlansWizard.errors.demandGroupsApplyFailed'));
    return false;
  } finally {
    stepLoading.value = false;
    emit('step-ui-state', 'demand-groups', { loading: false });
  }
}

async function submitCurrentStep(): Promise<CustomerNewPlanStepSubmitResult> {
  if (orderStepActive.value) {
    return submitOrderStep();
  }
  if (orderScopeDocumentsStepActive.value) {
    return submitOrderScopeDocumentsStep();
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
  if (demandGroupsStepActive.value) {
    return submitDemandGroupsStep();
  }
  if (assignmentsStepActive.value) {
    return assignmentsStepRef.value?.submitCurrentStep?.() ?? false;
  }
  return true;
}

defineExpose({
  editingExistingOrderId,
  existingOrderEditFormOpen,
  selectedExistingOrderId,
  submitCurrentStep,
});

watch(
  () => [equipmentLineDraft.equipment_item_id, equipmentLineDraft.required_qty, selectedEquipmentLineId.value, orderEquipmentLines.value.length],
  () => {
    clearOrderScopeValidationSection('equipment');
  },
);

watch(
  () => [
    requirementLineDraft.requirement_type_id,
    requirementLineDraft.min_qty,
    requirementLineDraft.target_qty,
    selectedRequirementLineId.value,
    orderRequirementLines.value.length,
  ],
  () => {
    clearOrderScopeValidationSection('requirements');
  },
);

watch(
  () => [
    orderAttachmentDraft.title,
    orderAttachmentDraft.file_name,
    orderAttachmentDraft.content_base64,
    orderAttachmentLink.document_id,
    orderAttachmentLink.label,
    orderAttachments.value.length,
  ],
  () => {
    clearOrderScopeValidationSection('documents');
  },
);

watch(planningFamily, async () => {
  if (draftSyncPaused.value || planningContextHydrationPaused.value || stepLoading.value) {
    return;
  }
  if (selectedPlanningRecord.value && planningFamily.value === planningFamilyForRecord(selectedPlanningRecord.value)) {
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
  () => [orderAttachmentLink.document_id, planningRecordAttachmentLink.document_id] as const,
  ([orderDocumentId, planningDocumentId]) => {
    if (selectedOrderLinkDocument.value && selectedOrderLinkDocument.value.id !== orderDocumentId) {
      selectedOrderLinkDocument.value = null;
    }
    if (selectedPlanningRecordLinkDocument.value && selectedPlanningRecordLinkDocument.value.id !== planningDocumentId) {
      selectedPlanningRecordLinkDocument.value = null;
    }
  },
);

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
    emit('step-completion', 'order-scope-documents', false);
    emit('step-ui-state', 'order-scope-documents', { dirty: true, error: '' });
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
    emit('step-completion', 'order-scope-documents', false);
    emit('step-ui-state', 'order-scope-documents', { dirty: true, error: '' });
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
    emit('step-completion', 'order-scope-documents', false);
    emit('step-ui-state', 'order-scope-documents', { dirty: true, error: '' });
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
    planningRecordDirty.value = true;
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
    if (!hasPlanningRecordDraftContent() && planningSelectionMode.value === 'use_existing') {
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
    planningRecordDirty.value = true;
    emit('step-completion', 'planning-record-overview', false);
    emit('step-ui-state', 'planning-record-overview', { dirty: true, error: '' });
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
    seriesDraft.local_start_time,
    seriesDraft.local_end_time,
    seriesDraft.default_break_minutes,
    seriesDraft.shift_type_code,
    seriesDraft.meeting_point,
    seriesDraft.location_text,
    seriesDraft.notes,
    seriesDraft.customer_visible_flag,
    seriesDraft.subcontractor_visible_flag,
    seriesDraft.stealth_mode_flag,
    seriesDraft.release_state,
    seriesGenerationDraft.from_date,
    seriesGenerationDraft.to_date,
    seriesGenerationDraft.regenerate_existing,
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
  demandGroupDraftRows,
  () => {
    if (!demandGroupsStepActive.value || stepLoading.value) {
      return;
    }
    if (demandGroupDraftWatchMuted.value) {
      demandGroupDraftWatchMuted.value = false;
      return;
    }
    demandGroupApplyResult.value = null;
    demandGroupSummaryMessage.value = '';
    demandGroupValidationError.value = '';
    emit('step-completion', 'demand-groups', false);
    emit('step-ui-state', 'demand-groups', { dirty: true, error: '' });
    persistDemandGroupsDraft();
  },
  { deep: true },
);

watch(selectedShiftDemandGroupId, () => {
  if (shiftDemandGroupDialog.open) {
    hydrateShiftDemandGroupDialogDraft();
  }
});

watch(
  () => seriesDraft.recurrence_code,
  () => {
    if (draftSyncPaused.value) {
      return;
    }
    if (seriesDraft.recurrence_code === 'daily' && seriesDraft.weekday_mask) {
      seriesDraft.weekday_mask = '';
    } else if (seriesDraft.recurrence_code === 'weekly') {
      ensureSeriesWeeklyMask();
    }
  },
);

watch(
  () => [
    seriesDraft.default_break_minutes,
    seriesDraft.local_start_time,
    seriesDraft.local_end_time,
    seriesDraft.shift_type_code,
    seriesDraft.meeting_point,
    seriesDraft.location_text,
  ] as const,
  ([nextBreak, nextStart, nextEnd, nextShiftType, nextMeetingPoint, nextLocationText], [previousBreak, previousStart, previousEnd, previousShiftType, previousMeetingPoint, previousLocationText]) => {
    if (draftSyncPaused.value || seriesTemplateDefaultsApplying.value) {
      return;
    }
    if (nextBreak !== previousBreak) {
      seriesTemplateFieldTouched.default_break_minutes = true;
    }
    if (nextStart !== previousStart) {
      seriesTemplateFieldTouched.local_start_time = true;
    }
    if (nextEnd !== previousEnd) {
      seriesTemplateFieldTouched.local_end_time = true;
    }
    if (nextShiftType !== previousShiftType) {
      seriesTemplateFieldTouched.shift_type_code = true;
    }
    if (nextMeetingPoint !== previousMeetingPoint) {
      seriesTemplateFieldTouched.meeting_point = true;
    }
    if (nextLocationText !== previousLocationText) {
      seriesTemplateFieldTouched.location_text = true;
    }
  },
);

watch(
  () => exceptionDraft.action_code,
  () => {
    if (draftSyncPaused.value || exceptionDraft.action_code === 'override') {
      return;
    }
    withDraftSyncPaused(() => {
      exceptionDraft.override_local_start_time = '';
      exceptionDraft.override_local_end_time = '';
      exceptionDraft.override_break_minutes = '';
      exceptionDraft.override_shift_type_code = '';
      exceptionDraft.override_meeting_point = '';
      exceptionDraft.override_location_text = '';
      exceptionDraft.customer_visible_flag = null;
      exceptionDraft.subcontractor_visible_flag = null;
      exceptionDraft.stealth_mode_flag = null;
    });
  },
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
    clearDemandGroupsRequestCaches();
    planningCreateStagedAddresses.value = [];
    closePlanningAddressCreateModal();
    planningLocationPickerOpen.value = false;
    clearDraftRestoreMessage();
    existingOrderEditFormOpen.value = false;
    selectedOrder.value = null;
    selectedPlanningRecord.value = null;
    selectedExistingPlanningRecordId.value = '';
    editingExistingPlanningRecordId.value = '';
    committedPlanningRecordId.value = '';
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
        committedPlanningRecordId.value = props.wizardState.planning_record_id || committedPlanningRecordId.value;
        shiftPlanDraft.planning_record_id = props.wizardState.planning_record_id || '';
        resetRequirementModal();
      }),
    );
    await refreshStepData();
  },
  { immediate: true },
);

watch(orderScopeDocumentsStepActive, () => {
  setupOrderScopeOnePageNavigation();
}, { immediate: true });

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
  disconnectOrderScopeSectionObserver();
  teardownOrderScopeNavFloating();
  if (props.persistDraftsOnUnmount === false) {
    return;
  }
  persistAllUnsavedDrafts();
});
</script>

<template>
  <div class="sp-customer-plan-wizard-step">
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
          <LocalLoadingIndicator
            v-if="customerOrderRowsLoading || stepLoadState.orderDetails"
            :label="savedDataLoadingLabel"
            test-id="customer-new-plan-order-loading"
          />
          <p v-if="stepLoadError.orderDetails || customerOrderRowsError" class="field-help">
            {{ stepLoadError.orderDetails || customerOrderRowsError }}
          </p>
          <p v-else-if="!customerOrderRowsLoading && !stepLoadState.orderDetails && !customerOrderRows.length" class="field-help">
            {{ $t('sicherplan.customerPlansWizard.forms.noExistingOrdersFound') }}
          </p>
          <div
            v-for="row in customerOrderRows"
            :key="row.id"
            class="sp-customer-plan-wizard-step__list-row"
            :class="{ 'sp-customer-plan-wizard-step__list-row--selected': row.id === selectedExistingOrderId }"
            :aria-pressed="row.id === selectedExistingOrderId ? 'true' : 'false'"
            data-testid="customer-new-plan-existing-order-row"
            role="button"
            tabindex="0"
            @click="selectExistingOrder(row.id)"
            @keydown.enter.prevent="selectExistingOrder(row.id)"
            @keydown.space.prevent="selectExistingOrder(row.id)"
          >
            <div class="sp-customer-order-row-label">
              <span class="sp-customer-order-row__primary">{{ row.order_no }} · {{ row.title }}</span>
              <span class="sp-customer-order-row__secondary">
                · {{ row.service_from }} - {{ row.service_to }} · {{ row.release_state }} · {{ row.status }}
              </span>
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
        <LocalLoadingIndicator
          v-if="stepLoadState.orderDetails"
          :label="savedDataLoadingLabel"
          test-id="customer-new-plan-step-local-loading"
        />
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

    <section
      v-else-if="orderScopeDocumentsStepActive"
      class="sp-customer-plan-wizard-step__scope-documents"
      data-testid="customer-new-plan-order-scope-documents-step"
    >
      <section
        ref="orderScopeOnePageRef"
        class="sp-customer-order-scope-onepage"
        data-testid="customer-order-scope-onepage"
      >
        <aside
          ref="orderScopeNavShellRef"
          class="sp-customer-order-scope-nav-shell"
          :class="{
            'sp-customer-order-scope-nav-shell--fixed': orderScopeNavFloatingMode === 'fixed',
            'sp-customer-order-scope-nav-shell--pinned': orderScopeNavFloatingMode === 'pinned',
          }"
          :style="orderScopeNavFloatingStyle"
          data-testid="customer-order-scope-nav"
        >
          <nav class="sp-customer-order-scope-nav" aria-label="Order scope sections">
            <button
              v-for="section in orderScopeSections"
              :key="section.id"
              type="button"
              :aria-current="section.id === activeOrderScopeSection ? 'true' : undefined"
              class="sp-customer-order-scope-nav__link"
              :class="{ 'sp-customer-order-scope-nav__link--active': section.id === activeOrderScopeSection }"
              :data-testid="section.testId"
              @click="selectOrderScopeSection(section.id)"
            >
              <IconifyIcon class="sp-customer-order-scope-nav__icon" :icon="section.icon" aria-hidden="true" />
              <span>{{ section.label }}</span>
            </button>
          </nav>
        </aside>

        <div class="sp-customer-order-scope-content">
      <section
        id="customer-order-scope-section-equipment"
        class="sp-customer-plan-wizard-step__scope-card"
        :class="{ 'sp-customer-plan-wizard-step__scope-card--invalid': Boolean(orderScopeSectionErrors.equipment) }"
        data-testid="customer-new-plan-order-scope-equipment-card"
      >
        <div data-testid="customer-new-plan-step-panel-equipment-lines">
          <header class="sp-customer-plan-wizard-step__scope-card-header">
            <h4>{{ $t('sicherplan.customerPlansWizard.orderScope.equipmentTitle') }}</h4>
          </header>
      <p
        v-if="orderScopeSectionErrors.equipment"
        class="field-error sp-customer-plan-wizard-step__section-error"
        data-testid="customer-new-plan-order-scope-equipment-error"
      >
        {{ orderScopeSectionErrors.equipment }}
      </p>
      <div class="sp-customer-plan-wizard-step__scope-subsection">
        <div class="cta-row sp-customer-plan-wizard-step__scope-action-row">
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-new-equipment"
            @click="equipmentModal.open = true"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.newEquipment') }}
          </button>
        </div>
      </div>
      <LocalLoadingIndicator
        v-if="stepLoadState.equipmentLines"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-equipment-lines-loading"
      />
      <LocalLoadingIndicator
        v-if="stepLoadState.orderReferenceOptions"
        :label="referenceDataLoadingLabel"
        test-id="customer-new-plan-equipment-options-loading"
      />
      <p v-if="stepLoadError.equipmentLines" class="field-help">{{ stepLoadError.equipmentLines }}</p>
      <div v-if="orderEquipmentLines.length" class="sp-customer-plan-wizard-step__scope-saved-list">
        <div class="sp-customer-plan-wizard-step__list">
          <div
            v-for="line in orderEquipmentLines"
            :key="line.id"
            class="sp-customer-plan-wizard-step__list-row"
            :class="{ 'sp-customer-plan-wizard-step__list-row--selected': line.id === selectedEquipmentLineId }"
          >
            <button
              type="button"
              class="sp-customer-plan-wizard-step__list-row-main"
              data-testid="customer-new-plan-equipment-line-select"
              @click="syncEquipmentLineDraft(line)"
            >
              <strong>{{ equipmentItemSelectOptions.find((option) => option.value === line.equipment_item_id)?.label || line.equipment_item_id }}</strong>
              <span>{{ line.required_qty }}</span>
            </button>
            <button
              type="button"
              class="cta-button cta-secondary sp-customer-plan-wizard-step__row-action"
              data-testid="customer-new-plan-delete-equipment-line"
              :disabled="stepLoading"
              @click.stop="void deleteEquipmentLine(line)"
            >
              {{ $t('sicherplan.customerPlansWizard.actions.deleteEquipmentLine') }}
            </button>
          </div>
        </div>
      </div>
      <div
        class="sp-customer-plan-wizard-step__scope-editor"
        :class="{ 'sp-customer-plan-wizard-step__scope-editor--invalid': Boolean(orderScopeSectionErrors.equipment) }"
      >
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack" :class="{ 'field-stack--invalid': Boolean(orderScopeFieldErrors.equipmentItem) }">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.equipmentItem') }}</span>
            <select
              v-model="equipmentLineDraft.equipment_item_id"
              data-testid="customer-new-plan-equipment-item"
              :disabled="equipmentItemsExhausted"
              :aria-invalid="Boolean(orderScopeFieldErrors.equipmentItem)"
            >
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.equipmentItemPlaceholder') }}</option>
              <option v-for="option in availableEquipmentItemSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <span
              v-if="equipmentItemsExhausted"
              class="field-help"
              data-testid="customer-new-plan-equipment-all-assigned"
            >
              {{ $t('sicherplan.customerPlansWizard.forms.allEquipmentItemsAssigned') }}
            </span>
            <span
              v-else-if="equipmentLineDuplicateActive"
              class="field-help"
              data-testid="customer-new-plan-equipment-duplicate"
            >
              {{ $t('sicherplan.customerPlansWizard.errors.equipmentLineDuplicate') }}
            </span>
            <p v-if="orderScopeFieldErrors.equipmentItem" class="field-error" data-testid="customer-new-plan-equipment-item-error">
              {{ orderScopeFieldErrors.equipmentItem }}
            </p>
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
        <p v-if="orderScopeFieldErrors.equipmentAction" class="field-error" data-testid="customer-new-plan-equipment-action-error">
          {{ orderScopeFieldErrors.equipmentAction }}
        </p>
        <div class="cta-row">
          <button
            v-if="selectedEquipmentLineId"
            type="button"
            class="cta-button"
            :class="{ 'cta-button--invalid': Boolean(orderScopeFieldErrors.equipmentAction) }"
            data-testid="customer-new-plan-update-equipment-line"
            :disabled="stepLoading || equipmentLineDuplicateActive"
            @click="void saveEquipmentLineDraft()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.updateEquipmentLine') }}
          </button>
          <button
            v-else
            type="button"
            class="cta-button"
            :class="{ 'cta-button--invalid': Boolean(orderScopeFieldErrors.equipmentAction) }"
            data-testid="customer-new-plan-save-equipment-line"
            :disabled="stepLoading || equipmentLineDuplicateActive"
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
      </div>
        </div>
    </section>

      <section
        id="customer-order-scope-section-requirements"
        class="sp-customer-plan-wizard-step__scope-card"
        :class="{ 'sp-customer-plan-wizard-step__scope-card--invalid': Boolean(orderScopeSectionErrors.requirements) }"
        data-testid="customer-new-plan-order-scope-requirements-card"
      >
        <div data-testid="customer-new-plan-step-panel-requirement-lines">
          <header class="sp-customer-plan-wizard-step__scope-card-header">
            <h4>{{ $t('sicherplan.customerPlansWizard.orderScope.requirementsTitle') }}</h4>
          </header>
      <p
        v-if="orderScopeSectionErrors.requirements"
        class="field-error sp-customer-plan-wizard-step__section-error"
        data-testid="customer-new-plan-order-scope-requirements-error"
      >
        {{ orderScopeSectionErrors.requirements }}
      </p>
      <div class="sp-customer-plan-wizard-step__scope-subsection">
        <div class="cta-row sp-customer-plan-wizard-step__scope-action-row">
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-new-requirement"
            @click="requirementModal.open = true"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.newRequirement') }}
          </button>
        </div>
      </div>
      <LocalLoadingIndicator
        v-if="stepLoadState.requirementLines"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-requirement-lines-loading"
      />
      <LocalLoadingIndicator
        v-if="stepLoadState.orderReferenceOptions"
        :label="referenceDataLoadingLabel"
        test-id="customer-new-plan-requirement-options-loading"
      />
      <p v-if="stepLoadError.requirementLines" class="field-help">{{ stepLoadError.requirementLines }}</p>
      <div v-if="orderRequirementLines.length" class="sp-customer-plan-wizard-step__scope-saved-list">
        <div class="sp-customer-plan-wizard-step__list">
          <div
            v-for="line in orderRequirementLines"
            :key="line.id"
            class="sp-customer-plan-wizard-step__list-row"
            :class="{ 'sp-customer-plan-wizard-step__list-row--selected': line.id === selectedRequirementLineId }"
          >
            <button
              type="button"
              class="sp-customer-plan-wizard-step__list-row-main"
              data-testid="customer-new-plan-requirement-line-select"
              @click="syncRequirementLineDraft(line)"
            >
              <strong>{{ requirementTypeSelectOptions.find((option) => option.value === line.requirement_type_id)?.label || line.requirement_type_id }}</strong>
              <span>{{ line.min_qty }} / {{ line.target_qty }}</span>
            </button>
            <button
              type="button"
              class="cta-button cta-secondary sp-customer-plan-wizard-step__row-action"
              data-testid="customer-new-plan-delete-requirement-line"
              :disabled="stepLoading"
              @click.stop="void deleteRequirementLine(line)"
            >
              {{ $t('sicherplan.customerPlansWizard.actions.deleteRequirementLine') }}
            </button>
          </div>
        </div>
      </div>
      <div
        class="sp-customer-plan-wizard-step__scope-editor"
        :class="{ 'sp-customer-plan-wizard-step__scope-editor--invalid': Boolean(orderScopeSectionErrors.requirements) }"
      >
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack" :class="{ 'field-stack--invalid': Boolean(orderScopeFieldErrors.requirementsType) }">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.requirementType') }}</span>
            <select
              v-model="requirementLineDraft.requirement_type_id"
              data-testid="customer-new-plan-requirement-type"
              :aria-invalid="Boolean(orderScopeFieldErrors.requirementsType)"
            >
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.requirementTypePlaceholder') }}</option>
              <option v-for="option in requirementTypeSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <p v-if="orderScopeFieldErrors.requirementsType" class="field-error" data-testid="customer-new-plan-requirement-type-error">
              {{ orderScopeFieldErrors.requirementsType }}
            </p>
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
        <p
          v-if="requirementLineDuplicateActive"
          class="field-help"
          data-testid="customer-new-plan-requirement-duplicate"
        >
          {{ $t('sicherplan.customerPlansWizard.errors.requirementLineDuplicate') }}
        </p>
        <p v-if="orderScopeFieldErrors.requirementsAction" class="field-error" data-testid="customer-new-plan-requirement-action-error">
          {{ orderScopeFieldErrors.requirementsAction }}
        </p>
        <div class="cta-row">
          <button
            v-if="selectedRequirementLineId"
            type="button"
            class="cta-button"
            :class="{ 'cta-button--invalid': Boolean(orderScopeFieldErrors.requirementsAction) }"
            data-testid="customer-new-plan-update-requirement-line"
            :disabled="stepLoading || requirementLineDuplicateActive"
            @click="void saveRequirementLineDraft()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.updateRequirementLine') }}
          </button>
          <button
            v-else
            type="button"
            class="cta-button"
            :class="{ 'cta-button--invalid': Boolean(orderScopeFieldErrors.requirementsAction) }"
            data-testid="customer-new-plan-save-requirement-line"
            :disabled="stepLoading || requirementLineDuplicateActive"
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
      </div>
        </div>
    </section>

      <section
        id="customer-order-scope-section-documents"
        class="sp-customer-plan-wizard-step__scope-card"
        :class="{ 'sp-customer-plan-wizard-step__scope-card--invalid': Boolean(orderScopeSectionErrors.documents) }"
        data-testid="customer-new-plan-order-scope-documents-card"
      >
        <div class="sp-customer-plan-wizard-step__documents-panel" data-testid="customer-new-plan-step-panel-order-documents">
      <header class="sp-customer-plan-wizard-step__scope-card-header">
        <h4>{{ $t('sicherplan.customerPlansWizard.orderScope.documentsTitle') }}</h4>
      </header>
      <p
        v-if="orderScopeSectionErrors.documents"
        class="field-error sp-customer-plan-wizard-step__section-error"
        data-testid="customer-new-plan-order-scope-documents-error"
      >
        {{ orderScopeSectionErrors.documents }}
      </p>
      <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.orderDocumentsOptional') }}</p>
      <LocalLoadingIndicator
        v-if="stepLoadState.orderDocuments"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-order-documents-loading"
      />
      <p v-if="stepLoadError.orderDocuments" class="field-help">{{ stepLoadError.orderDocuments }}</p>
      <div v-if="orderAttachments.length" class="sp-customer-plan-wizard-step__list sp-customer-plan-wizard-step__document-list" data-testid="customer-new-plan-order-document-list">
        <div
          v-for="document in orderAttachments"
          :key="document.id"
          class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static sp-customer-plan-wizard-step__list-row--document"
        >
          <div class="sp-customer-plan-wizard-step__document-row-copy">
            <strong>{{ orderAttachmentDisplayTitle(document) }}</strong>
            <span v-if="documentRowMetadata(document)">{{ documentRowMetadata(document) }}</span>
          </div>
          <button
            type="button"
            class="sp-customer-plan-wizard-step__list-action sp-customer-plan-wizard-step__list-action--compact sp-customer-plan-wizard-step__list-action--document-remove"
            data-testid="customer-new-plan-unlink-order-document"
            :disabled="stepLoading"
            @click.stop="void unlinkOrderDocument(document.id)"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.unlinkOrderDocument') }}
          </button>
        </div>
      </div>
      <p v-else-if="!stepLoadState.planningDocuments" class="field-help">
        {{ $t('sicherplan.customerPlansWizard.forms.noPlanningDocumentsYet') }}
      </p>
      <section
        class="sp-customer-plan-wizard-step__document-subsection"
        :class="{ 'sp-customer-plan-wizard-step__document-subsection--invalid': Boolean(orderScopeFieldErrors.documentsUploadTitle || orderScopeFieldErrors.documentsUploadFile || orderScopeFieldErrors.documentsUploadAction) }"
      >
        <header class="sp-customer-plan-wizard-step__document-subsection-header">
          <h5>{{ $t('sicherplan.customerPlansWizard.forms.uploadNewDocument') }}</h5>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.uploadNewDocumentHelp') }}</p>
        </header>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack" :class="{ 'field-stack--invalid': Boolean(orderScopeFieldErrors.documentsUploadTitle) }">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.documentTitle') }}</span>
            <input
              v-model="orderAttachmentDraft.title"
              data-testid="customer-new-plan-order-document-upload-title"
              :aria-invalid="Boolean(orderScopeFieldErrors.documentsUploadTitle)"
            />
            <p v-if="orderScopeFieldErrors.documentsUploadTitle" class="field-error" data-testid="customer-new-plan-order-document-upload-title-error">
              {{ orderScopeFieldErrors.documentsUploadTitle }}
            </p>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.uploadLabel') }}</span>
            <input v-model="orderAttachmentDraft.label" data-testid="customer-new-plan-order-document-upload-label" />
          </label>
          <label class="field-stack field-stack--wide" :class="{ 'field-stack--invalid': Boolean(orderScopeFieldErrors.documentsUploadFile) }">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.documentFile') }}</span>
            <input
              data-testid="customer-new-plan-order-document-file"
              type="file"
              :aria-invalid="Boolean(orderScopeFieldErrors.documentsUploadFile)"
              @change="onOrderAttachmentSelected"
            />
            <p v-if="orderScopeFieldErrors.documentsUploadFile" class="field-error" data-testid="customer-new-plan-order-document-file-error">
              {{ orderScopeFieldErrors.documentsUploadFile }}
            </p>
          </label>
        </div>
        <p v-if="orderScopeFieldErrors.documentsUploadAction" class="field-error" data-testid="customer-new-plan-order-document-upload-action-error">
          {{ orderScopeFieldErrors.documentsUploadAction }}
        </p>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            :class="{ 'cta-button--invalid': Boolean(orderScopeFieldErrors.documentsUploadAction) }"
            data-testid="customer-new-plan-attach-order-document"
            :disabled="stepLoading"
            @click="void attachUploadedOrderDocument()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.attachUploadedDocument') }}
          </button>
          <button
            v-if="hasOrderDocumentUploadDraftInput()"
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
      <div class="sp-customer-plan-wizard-step__document-divider" aria-hidden="true"></div>
      <section
        class="sp-customer-plan-wizard-step__document-subsection"
        :class="{ 'sp-customer-plan-wizard-step__document-subsection--invalid': Boolean(orderScopeFieldErrors.documentsLinkSelection || orderScopeFieldErrors.documentsLinkAction) }"
      >
        <header class="sp-customer-plan-wizard-step__document-subsection-header">
          <h5>{{ $t('sicherplan.customerPlansWizard.forms.linkExistingDocument') }}</h5>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.linkExistingDocumentHelp') }}</p>
        </header>
        <div
          v-if="orderAttachmentLink.document_id"
          class="sp-customer-plan-wizard-step__document-selection"
          data-testid="customer-new-plan-order-document-selected"
        >
          <strong>{{ $t('sicherplan.customerPlansWizard.forms.documentPickerSelected') }}</strong>
          <span>{{ documentCustomerSummary(selectedOrderLinkDocument) }}</span>
        </div>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button cta-secondary"
            :class="{ 'cta-button--invalid': Boolean(orderScopeFieldErrors.documentsLinkSelection) }"
            data-testid="customer-new-plan-order-document-picker-open"
            :disabled="stepLoading"
            @click="openDocumentPicker('order')"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.documentPickerOpen') }}
          </button>
          <button
            v-if="orderAttachmentLink.document_id"
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-order-document-clear"
            :disabled="stepLoading"
            @click="clearSelectedOrderLinkDocument"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.documentPickerClear') }}
          </button>
        </div>
        <p v-if="orderScopeFieldErrors.documentsLinkSelection" class="field-error" data-testid="customer-new-plan-order-document-selection-error">
          {{ orderScopeFieldErrors.documentsLinkSelection }}
        </p>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.linkLabel') }}</span>
            <input v-model="orderAttachmentLink.label" data-testid="customer-new-plan-order-document-link-label" />
          </label>
        </div>
        <p v-if="orderScopeFieldErrors.documentsLinkAction" class="field-error" data-testid="customer-new-plan-order-document-link-action-error">
          {{ orderScopeFieldErrors.documentsLinkAction }}
        </p>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            :class="{ 'cta-button--invalid': Boolean(orderScopeFieldErrors.documentsLinkAction) }"
            data-testid="customer-new-plan-link-order-document"
            :disabled="stepLoading"
            @click="void linkExistingOrderDocument()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.linkExistingDocument') }}
          </button>
          <button
            v-if="hasOrderDocumentLinkDraftInput()"
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
        </div>
      </section>
        </div>
      </section>
    </section>

    <section
      v-else-if="planningRecordStepActive"
      class="sp-customer-plan-wizard-step__panel"
      data-testid="customer-new-plan-step-panel-planning-record-overview"
    >
      <section
        class="sp-customer-plan-wizard-step__planning-record-card"
        data-testid="customer-new-plan-planning-record-card"
      >
        <section
          class="sp-customer-plan-wizard-step__planning-record-subsection"
          data-testid="customer-new-plan-existing-planning-records"
        >
          <div class="sp-customer-plan-wizard-step__planning-record-subsection-header">
            <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.existingPlanningRecords') }}</strong></p>
            <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.existingPlanningRecordsHelp') }}</p>
          </div>
          <LocalLoadingIndicator
            v-if="planningRecordRowsLoading || stepLoadState.planningRecords"
            :label="savedDataLoadingLabel"
            test-id="customer-new-plan-planning-record-loading"
          />
          <p v-if="stepLoadError.planningRecords || planningRecordRowsError" class="field-help">
            {{ stepLoadError.planningRecords || planningRecordRowsError }}
          </p>
          <div v-if="planningRecordRows.length" class="sp-customer-plan-wizard-step__list">
            <div
              v-for="row in planningRecordRows"
              :key="row.id"
              class="sp-customer-plan-wizard-step__list-row"
              :class="{ 'sp-customer-plan-wizard-step__list-row--selected': row.id === selectedExistingPlanningRecordId }"
              data-testid="customer-new-plan-existing-planning-record-row"
              data-order-workspace-testid="customer-order-workspace-existing-planning-record-row"
              role="button"
              tabindex="0"
              @click="void selectExistingPlanningRecordRow(row.id)"
              @keydown.enter.prevent="void selectExistingPlanningRecordRow(row.id)"
              @keydown.space.prevent="void selectExistingPlanningRecordRow(row.id)"
            >
              <div class="sp-customer-plan-wizard-step__planning-record-row-copy">
                <strong>{{ row.name }}</strong>
                <span>{{ row.planning_from }} - {{ row.planning_to }}</span>
              </div>
            </div>
          </div>
          <p
            v-if="selectedPlanningRecordRow"
            class="field-help"
            data-testid="customer-new-plan-selected-planning-record-summary"
            data-order-workspace-testid="customer-order-workspace-selected-planning-record-summary"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.selectedPlanningRecord') }}:
            {{ selectedPlanningRecordRow.name }}
          </p>
          <p v-else-if="!planningRecordRowsLoading && !stepLoadState.planningRecords" class="field-help" data-testid="customer-new-plan-existing-planning-records-empty">
            {{ $t('sicherplan.customerPlansWizard.forms.noPlanningRecordsFoundForContext') }}
          </p>
        </section>

        <div class="sp-customer-plan-wizard-step__planning-record-divider" aria-hidden="true"></div>

        <section
          class="sp-customer-plan-wizard-step__planning-record-subsection"
          data-testid="customer-new-plan-planning-record-editor"
          data-order-workspace-testid="customer-order-workspace-planning-record-editor"
        >
          <header
            class="sp-customer-plan-wizard-step__planning-record-subsection-header sp-customer-plan-wizard-step__planning-record-subsection-header--with-action"
          >
            <div class="sp-customer-plan-wizard-step__planning-record-subsection-title">
              <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.planningRecordDetails') }}</strong></p>
              <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.selectPlanningContext') }}</p>
            </div>
            <button
              type="button"
              class="cta-button cta-secondary"
              data-testid="customer-new-plan-planning-record-create-entry"
              :disabled="stepLoading"
              @click="openPlanningCreateModal()"
            >
              {{ $t('sicherplan.customerPlansWizard.forms.createNewPlanningEntry') }}
            </button>
          </header>
          <LocalLoadingIndicator
            v-if="stepLoadState.planningRecordDetail"
            :label="savedDataLoadingLabel"
            test-id="customer-new-plan-planning-record-detail-loading"
          />
          <LocalLoadingIndicator
            v-if="planningEntityLoading || stepLoadState.planningReferenceOptions"
            :label="referenceDataLoadingLabel"
            test-id="customer-new-plan-planning-reference-loading"
          />
          <p v-if="stepLoadError.planningRecordDetail" class="field-help">{{ stepLoadError.planningRecordDetail }}</p>
          <p v-if="planningEntityError" class="field-help">{{ planningEntityError }}</p>
          <div class="sp-customer-plan-wizard-step__grid" data-testid="customer-new-plan-planning-record-details">
            <label class="field-stack">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.orderTitle') }}</span>
              <input :value="selectedOrder?.title || orderDraft.title" readonly />
            </label>
            <label class="field-stack" :class="{ 'field-stack--invalid': planningRecordFieldErrors.planningMode }">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.planningModeCode') }}</span>
              <select
                :value="planningFamily"
                data-testid="customer-new-plan-planning-context-family"
                :aria-invalid="Boolean(planningRecordFieldErrors.planningMode)"
                @change="onPlanningFamilyChange"
              >
                <option v-for="option in planningFamilyOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <p v-if="planningRecordFieldErrors.planningMode" class="field-error" data-testid="customer-new-plan-planning-mode-error">
                {{ planningRecordFieldErrors.planningMode }}
              </p>
            </label>
            <label class="field-stack" :class="{ 'field-stack--invalid': planningRecordFieldErrors.planningEntity }">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.planningEntity') }}</span>
              <select
                :value="planningEntityId"
                data-testid="customer-new-plan-planning-context-entry"
                :disabled="planningEntityLoading || stepLoadState.planningReferenceOptions"
                :aria-invalid="Boolean(planningRecordFieldErrors.planningEntity)"
                @change="void onPlanningEntityChange($event)"
              >
                <option value="">{{ $t('sicherplan.customerPlansWizard.forms.planningEntityPlaceholder') }}</option>
                <option v-for="option in planningEntityOptions" :key="option.id" :value="option.id">
                  {{ planningEntityOptionLabel(option) }}
                </option>
              </select>
              <p v-if="planningRecordFieldErrors.planningEntity" class="field-error" data-testid="customer-new-plan-planning-entry-error">
                {{ planningRecordFieldErrors.planningEntity }}
              </p>
              <p
                v-if="!planningEntityOptions.length && !planningEntityLoading && !stepLoadState.planningReferenceOptions && !selectedPlanningRecord"
                class="field-help"
              >
                {{ $t('sicherplan.customerPlansWizard.forms.noPlanningEntriesFoundForCustomer') }}
              </p>
            </label>
            <label class="field-stack" :class="{ 'field-stack--invalid': planningRecordFieldErrors.name }">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.name') }}</span>
              <input
                v-model="planningRecordDraft.name"
                data-testid="customer-new-plan-planning-record-name"
                :aria-invalid="Boolean(planningRecordFieldErrors.name)"
              />
              <p v-if="planningRecordFieldErrors.name" class="field-error" data-testid="customer-new-plan-planning-record-name-error">
                {{ planningRecordFieldErrors.name }}
              </p>
            </label>
            <label class="field-stack" :class="{ 'field-stack--invalid': planningRecordFieldErrors.planningFrom || planningRecordFieldErrors.dateRange }">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.startDate') }}</span>
              <input
                v-model="planningRecordDraft.planning_from"
                data-testid="customer-new-plan-planning-record-from"
                type="date"
                :aria-invalid="Boolean(planningRecordFieldErrors.planningFrom || planningRecordFieldErrors.dateRange)"
              />
              <p v-if="planningRecordFieldErrors.planningFrom || planningRecordFieldErrors.dateRange" class="field-error" data-testid="customer-new-plan-planning-record-from-error">
                {{ planningRecordFieldErrors.planningFrom || planningRecordFieldErrors.dateRange }}
              </p>
            </label>
            <label class="field-stack" :class="{ 'field-stack--invalid': planningRecordFieldErrors.planningTo || planningRecordFieldErrors.dateRange }">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.endDate') }}</span>
              <input
                v-model="planningRecordDraft.planning_to"
                data-testid="customer-new-plan-planning-record-to"
                type="date"
                :aria-invalid="Boolean(planningRecordFieldErrors.planningTo || planningRecordFieldErrors.dateRange)"
              />
              <p v-if="planningRecordFieldErrors.planningTo || planningRecordFieldErrors.dateRange" class="field-error" data-testid="customer-new-plan-planning-record-to-error">
                {{ planningRecordFieldErrors.planningTo || planningRecordFieldErrors.dateRange }}
              </p>
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
          <div class="cta-row">
            <button
              type="button"
              class="cta-button"
              data-testid="customer-new-plan-save-planning-record"
              data-order-workspace-testid="customer-order-workspace-update-planning-record"
              :disabled="stepLoading || !hasPlanningContext"
              @click="void savePlanningRecordDraftOrSelection()"
            >
              {{
                selectedPlanningRecord
                  ? $t('sicherplan.customerPlansWizard.actions.updatePlanningRecord')
                  : $t('sicherplan.customerPlansWizard.actions.savePlanningRecord')
              }}
            </button>
            <button
              type="button"
              class="cta-button cta-secondary"
              data-testid="customer-new-plan-clear-planning-record-draft"
              data-order-workspace-testid="customer-order-workspace-cancel-planning-record-edit"
              :disabled="stepLoading"
              @click="clearPlanningRecordDraftState"
            >
              {{ $t('sicherplan.customerPlansWizard.actions.clearPlanningRecordDraft') }}
            </button>
          </div>
        </section>
      </section>
    </section>

    <section
      v-else-if="planningRecordDocumentsStepActive"
      class="sp-customer-plan-wizard-step__panel"
      data-testid="customer-new-plan-step-panel-planning-record-documents"
    >
      <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.planningDocumentsOptional') }}</p>
      <LocalLoadingIndicator
        v-if="stepLoadState.planningDocuments"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-planning-documents-loading"
      />
      <p v-if="stepLoadError.planningDocuments" class="field-help">{{ stepLoadError.planningDocuments }}</p>
      <div
        v-if="planningRecordAttachments.length"
        class="sp-customer-plan-wizard-step__list sp-customer-plan-wizard-step__document-list"
        data-testid="customer-new-plan-planning-document-list"
        data-order-workspace-testid="customer-order-workspace-planning-document-list"
      >
        <div
          v-for="document in planningRecordAttachments"
          :key="document.id"
          class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static"
          data-order-workspace-testid="customer-order-workspace-planning-document-row"
        >
          <div class="sp-customer-plan-wizard-step__document-row-copy">
            <strong data-order-workspace-testid="customer-order-workspace-planning-document-primary-label">
              {{ planningRecordAttachmentDisplayTitle(document) }}
            </strong>
            <span
              v-if="documentRowMetadata(document)"
              data-order-workspace-testid="customer-order-workspace-planning-document-secondary-label"
            >
              {{ documentRowMetadata(document) }}
            </span>
          </div>
          <button
            type="button"
            class="sp-customer-plan-wizard-step__list-action sp-customer-plan-wizard-step__list-action--compact"
            data-testid="customer-new-plan-unlink-planning-record-document"
            data-order-workspace-testid="customer-order-workspace-planning-document-remove"
            :disabled="stepLoading"
            @click.stop="void unlinkPlanningRecordDocument(document.id)"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.unlinkPlanningDocument') }}
          </button>
        </div>
      </div>
      <section class="sp-customer-plan-wizard-step__document-subsection">
        <header class="sp-customer-plan-wizard-step__document-subsection-header">
          <h5>{{ $t('sicherplan.customerPlansWizard.forms.uploadNewDocument') }}</h5>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.uploadNewDocumentHelp') }}</p>
        </header>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.documentTitle') }}</span>
            <input
              v-model="planningRecordAttachmentDraft.title"
              data-testid="customer-new-plan-planning-record-document-title"
              data-order-workspace-testid="customer-order-workspace-planning-document-upload-title"
            />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.uploadLabel') }}</span>
            <input
              v-model="planningRecordAttachmentDraft.label"
              data-testid="customer-new-plan-planning-record-document-label"
              data-order-workspace-testid="customer-order-workspace-planning-document-upload-label"
            />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.documentFile') }}</span>
            <input
              data-testid="customer-new-plan-planning-record-document-file"
              data-order-workspace-testid="customer-order-workspace-planning-document-file"
              type="file"
              @change="onPlanningRecordAttachmentSelected"
            />
          </label>
        </div>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-attach-planning-record-document"
            data-order-workspace-testid="customer-order-workspace-attach-planning-document"
            :disabled="stepLoading"
            @click="void attachUploadedPlanningRecordDocument()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.attachUploadedDocument') }}
          </button>
        </div>
      </section>
      <div class="sp-customer-plan-wizard-step__document-divider" aria-hidden="true"></div>
      <section class="sp-customer-plan-wizard-step__document-subsection">
        <header class="sp-customer-plan-wizard-step__document-subsection-header">
          <h5>{{ $t('sicherplan.customerPlansWizard.forms.linkExistingDocument') }}</h5>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.linkExistingDocumentHelp') }}</p>
        </header>
        <div
          v-if="planningRecordAttachmentLink.document_id"
          class="sp-customer-plan-wizard-step__document-selection"
          data-testid="customer-new-plan-planning-document-selected"
        >
          <strong>{{ $t('sicherplan.customerPlansWizard.forms.documentPickerSelected') }}</strong>
          <span>{{ documentCustomerSummary(selectedPlanningRecordLinkDocument) }}</span>
        </div>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-planning-document-picker-open"
            data-order-workspace-testid="customer-order-workspace-planning-document-picker"
            :disabled="stepLoading"
            @click="openDocumentPicker('planning-record')"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.documentPickerOpen') }}
          </button>
          <button
            v-if="planningRecordAttachmentLink.document_id"
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-planning-document-clear"
            :disabled="stepLoading"
            @click="clearSelectedPlanningRecordLinkDocument"
          >
            {{ $t('sicherplan.customerPlansWizard.forms.documentPickerClear') }}
          </button>
        </div>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.linkLabel') }}</span>
            <input
              v-model="planningRecordAttachmentLink.label"
              data-testid="customer-new-plan-planning-record-document-link-label"
              data-order-workspace-testid="customer-order-workspace-planning-document-link-label"
            />
          </label>
        </div>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-link-planning-record-document"
            data-order-workspace-testid="customer-order-workspace-link-planning-document"
            :disabled="stepLoading"
            @click="void linkExistingPlanningRecordDocument()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.linkExistingDocument') }}
          </button>
          <button
            v-if="hasAnyPlanningRecordDocumentDraftInput()"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-clear-planning-document-draft"
            data-order-workspace-testid="customer-order-workspace-clear-planning-document-draft"
            type="button"
            :disabled="stepLoading"
            @click="clearPlanningRecordDocumentDraftState"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.clearPlanningDocumentDraft') }}
          </button>
        </div>
      </section>
    </section>

    <section v-else-if="shiftPlanStepActive" class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-shift-plan">
      <LocalLoadingIndicator
        v-if="stepLoadState.shiftPlans"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-shift-plan-loading"
      />
      <LocalLoadingIndicator
        v-if="stepLoadState.shiftReferenceOptions"
        :label="referenceDataLoadingLabel"
        test-id="customer-new-plan-shift-options-loading"
      />
      <p v-if="stepLoadError.shiftPlan" class="field-help">{{ stepLoadError.shiftPlan }}</p>
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
      <LocalLoadingIndicator
        v-if="stepLoadState.shiftPlanDetail"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-shift-plan-detail-loading"
      />
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
      <LocalLoadingIndicator
        v-if="stepLoadState.seriesContext"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-series-context-loading"
      />
      <LocalLoadingIndicator
        v-if="stepLoadState.seriesRows"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-series-loading"
      />
      <LocalLoadingIndicator
        v-if="stepLoadState.seriesReferenceOptions"
        :label="referenceDataLoadingLabel"
        test-id="customer-new-plan-series-options-loading"
      />
      <p v-if="stepLoadError.series" class="field-help">{{ stepLoadError.series }}</p>
      <div
        v-if="selectedShiftPlanSummary"
        class="sp-customer-plan-wizard-step__info-summary"
        data-testid="customer-new-plan-series-shift-plan-summary"
        data-order-workspace-testid="customer-order-workspace-selected-shift-plan-summary"
      >
        <strong>{{ $t('sicherplan.customerPlansWizard.forms.selectedShiftPlan') }}: {{ selectedShiftPlanSummary.name }}</strong>
        <span>{{ selectedShiftPlanSummary.planning_from }} - {{ selectedShiftPlanSummary.planning_to }}</span>
        <span>
          {{ $t('sicherplan.customerPlansWizard.forms.workforceScope') }}:
          {{ formatWorkforceScopeLabel(selectedShiftPlanSummary.workforce_scope_code) }}
        </span>
      </div>
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
      <section
        class="sp-customer-plan-wizard-step__document-subsection"
        data-testid="customer-new-plan-series-section"
        data-order-workspace-testid="customer-order-workspace-series-section"
      >
        <header class="sp-customer-plan-wizard-step__document-subsection-header">
          <h5>{{ $t('sicherplan.customerPlansWizard.forms.series') }}</h5>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.seriesHelp') }}</p>
        </header>
        <div
          v-if="stepLoadState.seriesDetail"
          class="sp-customer-plan-wizard-step__series-loading-row"
          data-testid="customer-new-plan-series-detail-loading"
          data-order-workspace-testid="customer-order-workspace-series-loading"
        >
          <LocalLoadingIndicator :label="$t('sicherplan.customerPlansWizard.forms.loadingSavedSeries')" />
        </div>
        <div
          class="sp-customer-plan-wizard-step__template-helper"
          data-testid="customer-new-plan-series-template-helper"
          data-order-workspace-testid="customer-order-workspace-series-template-helper"
        >
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.useTemplateOptional') }}</span>
            <select v-model="seriesDraft.shift_template_id" data-testid="customer-new-plan-series-template">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.shiftTemplatePlaceholder') }}</option>
              <option v-for="option in shiftTemplateSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-apply-template"
            data-order-workspace-testid="customer-order-workspace-series-apply-template"
            :disabled="stepLoading || !seriesDraft.shift_template_id"
            @click="void applySelectedShiftTemplatePreset()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.applyTemplate') }}
          </button>
        </div>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.label') }}</span>
            <input v-model="seriesDraft.label" data-testid="customer-new-plan-series-label" />
          </label>
          <label :class="['field-stack', { 'field-stack--invalid': seriesFieldErrors.startTime }]">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.startTime') }}</span>
            <input
              v-model="seriesDraft.local_start_time"
              data-testid="customer-new-plan-series-start-time"
              data-order-workspace-testid="customer-order-workspace-series-start-time"
              type="time"
            />
            <p v-if="seriesFieldErrors.startTime" class="field-error">{{ seriesFieldErrors.startTime }}</p>
          </label>
          <label :class="['field-stack', { 'field-stack--invalid': seriesFieldErrors.endTime }]">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.endTime') }}</span>
            <input
              v-model="seriesDraft.local_end_time"
              data-testid="customer-new-plan-series-end-time"
              data-order-workspace-testid="customer-order-workspace-series-end-time"
              type="time"
            />
            <p v-if="seriesFieldErrors.endTime" class="field-error">{{ seriesFieldErrors.endTime }}</p>
          </label>
          <label :class="['field-stack', { 'field-stack--invalid': seriesFieldErrors.shiftType }]">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.shiftType') }}</span>
            <select
              v-model="seriesDraft.shift_type_code"
              data-testid="customer-new-plan-series-shift-type"
              data-order-workspace-testid="customer-order-workspace-series-shift-type"
            >
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.shiftTypePlaceholder') }}</option>
              <option v-for="option in shiftTypeSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
            <p v-if="seriesFieldErrors.shiftType" class="field-error">{{ seriesFieldErrors.shiftType }}</p>
          </label>
          <label :class="['field-stack', { 'field-stack--invalid': seriesFieldErrors.defaultBreak }]">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.defaultBreakMinutes') }}</span>
            <input
              v-model.number="seriesDraft.default_break_minutes"
              data-testid="customer-new-plan-series-default-break"
              data-order-workspace-testid="customer-order-workspace-series-default-break"
              min="0"
              type="number"
            />
            <p v-if="seriesFieldErrors.defaultBreak" class="field-error">{{ seriesFieldErrors.defaultBreak }}</p>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.recurrenceCode') }}</span>
            <select v-model="seriesDraft.recurrence_code" data-testid="customer-new-plan-series-recurrence-code">
              <option value="daily">{{ $t('sicherplan.customerPlansWizard.forms.recurrenceDaily') }}</option>
              <option value="weekly">{{ $t('sicherplan.customerPlansWizard.forms.recurrenceWeekly') }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.intervalCount') }}</span>
            <input v-model.number="seriesDraft.interval_count" min="1" type="number" />
          </label>
          <label v-if="seriesWeekdayMaskRequired" class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.weekdayMask') }}</span>
            <div
              class="sp-customer-plan-wizard-step__weekday-picker"
              data-testid="customer-new-plan-series-weekday-picker"
            >
              <div
                v-for="option in seriesWeekdayOptions"
                :key="option.id"
                data-testid="customer-new-plan-series-weekday-chip"
              >
                <button
                  :aria-pressed="isSeriesWeekdaySelected(option.index) ? 'true' : 'false'"
                  :class="[
                    'sp-customer-plan-wizard-step__weekday-chip',
                    {
                      'sp-customer-plan-wizard-step__weekday-chip--active': isSeriesWeekdaySelected(option.index),
                    },
                  ]"
                  :data-testid="`customer-new-plan-series-weekday-chip-${option.id}`"
                  type="button"
                  @click="toggleSeriesWeekday(option.index)"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
            <span class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.weekdayMaskHelp') }}</span>
            <p v-if="seriesFieldErrors.weekdayMask" class="field-error">{{ seriesFieldErrors.weekdayMask }}</p>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.timezone') }}</span>
            <select v-model="seriesDraft.timezone" data-testid="customer-new-plan-series-timezone">
              <option v-for="option in timezoneOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label :class="['field-stack', { 'field-stack--invalid': seriesFieldErrors.dateRange }]">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.startDate') }}</span>
            <input
              v-model="seriesDraft.date_from"
              :max="selectedShiftPlanSummary?.planning_to || undefined"
              :min="selectedShiftPlanSummary?.planning_from || undefined"
              data-testid="customer-new-plan-series-from"
              type="date"
            />
          </label>
          <label :class="['field-stack', { 'field-stack--invalid': seriesFieldErrors.dateRange }]">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.endDate') }}</span>
            <input
              v-model="seriesDraft.date_to"
              :max="selectedShiftPlanSummary?.planning_to || undefined"
              :min="selectedShiftPlanSummary?.planning_from || undefined"
              data-testid="customer-new-plan-series-to"
              type="date"
            />
            <p v-if="seriesFieldErrors.dateRange" class="field-error">{{ seriesFieldErrors.dateRange }}</p>
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
          <label class="planning-admin-checkbox planning-admin-checkbox--centered">
            <input v-model="seriesDraft.customer_visible_flag" type="checkbox" />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.customerVisible') }}</span>
          </label>
          <label class="planning-admin-checkbox planning-admin-checkbox--centered">
            <input v-model="seriesDraft.subcontractor_visible_flag" type="checkbox" />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.subcontractorVisible') }}</span>
          </label>
          <label class="planning-admin-checkbox planning-admin-checkbox--centered">
            <input v-model="seriesDraft.stealth_mode_flag" type="checkbox" />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.stealthMode') }}</span>
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
            <textarea v-model="seriesDraft.notes" rows="2" />
          </label>
        </div>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-save-series"
            :data-order-workspace-testid="seriesEditMode ? 'customer-order-workspace-series-update' : 'customer-order-workspace-series-save'"
            :disabled="stepLoading"
            @click="void saveSeriesDraft()"
          >
            {{
              seriesEditMode
                ? $t('sicherplan.customerPlansWizard.actions.updateSeries')
                : $t('sicherplan.customerPlansWizard.actions.saveSeries')
            }}
          </button>
        </div>
      </section>
      <p
        v-if="!seriesDependentSectionsVisible"
        class="sp-customer-plan-wizard-step__gating-helper field-help"
        data-testid="customer-new-plan-series-gating-helper"
        data-order-workspace-testid="customer-order-workspace-series-gating-helper"
      >
        {{ $t('sicherplan.customerPlansWizard.forms.seriesDependentSectionsHelper') }}
      </p>
      <section
        v-if="seriesDependentSectionsVisible"
        class="sp-customer-plan-wizard-step__dependent-section"
        data-testid="customer-new-plan-exceptions-section"
        data-order-workspace-testid="customer-order-workspace-exceptions-section"
      >
        <LocalLoadingIndicator
          v-if="stepLoadState.seriesExceptions"
          :label="savedDataLoadingLabel"
          test-id="customer-new-plan-series-exceptions-loading"
        />
        <div class="sp-customer-plan-wizard-step__section-intro">
          <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.exceptions') }}</strong></p>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.exceptionsHelp') }}</p>
        </div>
        <div class="cta-row sp-customer-plan-wizard-step__exception-action-row">
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-new-exception"
            data-order-workspace-testid="customer-order-workspace-new-exception"
            :disabled="stepLoading"
            @click="openNewExceptionModal"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.newException') }}
          </button>
        </div>
        <div v-if="seriesExceptions.length" class="sp-customer-plan-wizard-step__list sp-customer-plan-wizard-step__exception-list">
          <div
            v-for="row in seriesExceptions"
            :key="row.id"
            class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__list-row--static"
            data-testid="customer-new-plan-series-exception-row"
            data-order-workspace-testid="customer-order-workspace-exception-row"
          >
            <div class="sp-customer-plan-wizard-step__document-row-copy">
              <strong>{{ row.exception_date }}</strong>
              <span>{{ row.action_code }}</span>
            </div>
            <div class="cta-row">
              <button
                type="button"
                class="sp-customer-plan-wizard-step__list-action sp-customer-plan-wizard-step__list-action--compact"
                data-testid="customer-new-plan-edit-exception"
                data-order-workspace-testid="customer-order-workspace-edit-exception"
                :disabled="stepLoading"
                @click="openEditExceptionModal(row)"
              >
                {{ $t('sicherplan.customerPlansWizard.actions.editException') }}
              </button>
              <button
                type="button"
                class="sp-customer-plan-wizard-step__list-action sp-customer-plan-wizard-step__list-action--compact"
                data-testid="customer-new-plan-delete-exception"
                data-order-workspace-testid="customer-order-workspace-delete-exception"
                :disabled="stepLoading"
                @click="void deleteExceptionRow(row)"
              >
                {{ $t('sicherplan.customerPlansWizard.actions.deleteException') }}
              </button>
            </div>
          </div>
        </div>
      </section>
      <section
        v-if="seriesDependentSectionsVisible"
        class="sp-customer-plan-wizard-step__dependent-section"
        data-testid="customer-new-plan-generation-options-section"
        data-order-workspace-testid="customer-order-workspace-generation-options-section"
      >
        <div class="sp-customer-plan-wizard-step__section-intro">
          <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.generationOptions') }}</strong></p>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.generationOptionsHelp') }}</p>
        </div>
        <div
          class="sp-customer-plan-wizard-step__generation-grid"
          data-testid="customer-new-plan-generation-options"
          data-order-workspace-testid="customer-order-workspace-generation-options"
        >
          <label class="field-stack sp-customer-plan-wizard-step__generation-date-field">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.generateFromDate') }}</span>
            <input
              v-model="seriesGenerationDraft.from_date"
              :max="seriesDraft.date_to || selectedShiftPlanSummary?.planning_to || undefined"
              :min="seriesDraft.date_from || selectedShiftPlanSummary?.planning_from || undefined"
              data-testid="customer-new-plan-series-generation-from"
              data-order-workspace-testid="customer-order-workspace-generate-from"
              type="date"
            />
          </label>
          <label class="field-stack sp-customer-plan-wizard-step__generation-date-field">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.generateToDate') }}</span>
            <input
              v-model="seriesGenerationDraft.to_date"
              :max="seriesDraft.date_to || selectedShiftPlanSummary?.planning_to || undefined"
              :min="seriesDraft.date_from || selectedShiftPlanSummary?.planning_from || undefined"
              data-testid="customer-new-plan-series-generation-to"
              data-order-workspace-testid="customer-order-workspace-generate-to"
              type="date"
            />
          </label>
          <label class="planning-admin-checkbox planning-admin-checkbox--centered sp-customer-plan-wizard-step__generation-checkbox">
            <input
              v-model="seriesGenerationDraft.regenerate_existing"
              data-testid="customer-new-plan-series-regenerate-existing"
              data-order-workspace-testid="customer-order-workspace-regenerate-existing"
              type="checkbox"
            />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.regenerateExisting') }}</span>
          </label>
        </div>
      </section>
    </section>

    <section
      v-else-if="demandGroupsStepActive"
      class="sp-customer-plan-wizard-step__panel"
      data-testid="customer-new-plan-step-panel-demand-groups"
    >
      <LocalLoadingIndicator
        v-if="stepLoadState.demandGroups"
        :label="savedDataLoadingLabel"
        test-id="customer-new-plan-demand-groups-loading"
      />
      <p v-if="stepLoadError.demandGroups" class="field-help">{{ stepLoadError.demandGroups }}</p>
      <div
        v-if="selectedShiftPlanSummary"
        class="sp-customer-plan-wizard-step__info-summary"
        data-testid="customer-new-plan-demand-groups-shift-plan-summary"
      >
        <strong>{{ $t('sicherplan.customerPlansWizard.forms.selectedShiftPlan') }}: {{ selectedShiftPlanSummary.name }}</strong>
        <span>{{ selectedShiftPlanSummary.planning_from }} - {{ selectedShiftPlanSummary.planning_to }}</span>
        <span>
          {{ $t('sicherplan.customerPlansWizard.forms.workforceScope') }}:
          {{ formatWorkforceScopeLabel(selectedShiftPlanSummary.workforce_scope_code) }}
        </span>
      </div>
      <div
        v-if="selectedSeriesSummary"
        class="sp-customer-plan-wizard-step__info-summary"
        data-testid="customer-new-plan-demand-groups-series-summary"
      >
        <strong>{{ $t('sicherplan.customerPlansWizard.forms.series') }}: {{ selectedSeriesSummary.label }}</strong>
        <span>{{ selectedSeriesSummary.date_from }} - {{ selectedSeriesSummary.date_to }}</span>
      </div>
      <div
        class="sp-customer-plan-wizard-step__section-intro"
        data-testid="customer-new-plan-demand-groups-context"
      >
        <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.demandGroups') }}</strong></p>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsHelp') }}</p>
        <p class="field-help">
          {{ $t('sicherplan.customerPlansWizard.forms.generatedShiftCount') }}:
          <strong data-testid="customer-new-plan-demand-groups-generated-count">{{ generatedDemandGroupShiftCount }}</strong>
        </p>
      </div>
      <div class="cta-row">
        <button
          type="button"
          class="cta-button cta-secondary"
          data-testid="customer-new-plan-demand-group-new"
          :disabled="stepLoading || !props.wizardState.shift_plan_id"
          @click="openNewDemandGroupDialog"
        >
          {{ $t('sicherplan.customerPlansWizard.actions.newDemandGroup') }}
        </button>
      </div>
      <div
        v-if="!generatedDemandGroupShiftCount"
        class="sp-customer-plan-wizard-step__empty-state"
        data-testid="customer-new-plan-demand-groups-empty"
      >
        <p><strong>{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsEmptyTitle') }}</strong></p>
        <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsEmptyBody') }}</p>
      </div>
      <p
        v-if="demandGroupValidationError"
        class="field-error"
        data-testid="customer-new-plan-demand-groups-validation"
      >
        {{ demandGroupValidationError }}
      </p>
      <p
        v-if="demandGroupSummaryMessage"
        class="field-help"
        data-testid="customer-new-plan-demand-groups-summary"
      >
        {{ demandGroupSummaryMessage }}
      </p>
      <section class="sp-customer-plan-wizard-step__document-subsection" data-testid="customer-new-plan-demand-group-persisted-section">
        <header class="sp-customer-plan-wizard-step__document-subsection-header">
          <h5>{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsAppliedTitle') }}</h5>
          <p class="field-help">{{ persistedDemandGroupsSummaryMessage || $t('sicherplan.customerPlansWizard.forms.demandGroupsAppliedEmpty') }}</p>
        </header>
        <div
          v-if="persistedDemandGroupSummaryRows.length"
          class="sp-customer-plan-wizard-step__list sp-customer-plan-wizard-step__list--compact"
          data-testid="customer-new-plan-demand-group-persisted-list"
        >
          <article
            v-for="row in persistedDemandGroupSummaryRows"
            :key="row.signature_key"
            class="sp-customer-plan-wizard-step__document-subsection sp-customer-plan-wizard-step__document-subsection--compact"
            data-testid="customer-new-plan-demand-group-persisted-row"
          >
            <div class="sp-customer-plan-wizard-step__demand-group-card">
              <div class="sp-customer-plan-wizard-step__demand-group-card-body">
                <header
                  class="sp-customer-plan-wizard-step__document-subsection-header sp-customer-plan-wizard-step__document-subsection-header--compact sp-customer-plan-wizard-step__demand-group-card-header"
                  :data-testid="`customer-new-plan-demand-group-persisted-header-${row.signature_key}`"
                >
                  <div class="sp-customer-plan-wizard-step__demand-group-card-title">
                    <h5>{{ row.function_type_label }}</h5>
                    <p class="field-help">{{ row.qualification_type_label }}</p>
                  </div>
                  <div class="sp-customer-plan-wizard-step__demand-group-card-actions">
                    <button
                      type="button"
                      class="cta-button cta-secondary"
                      :data-testid="`customer-new-plan-demand-group-persisted-days-${row.signature_key}`"
                      :disabled="stepLoading || row.all_rows_locked"
                      @click="openShiftDemandGroupEditDialog(row.signature_key)"
                    >
                      {{ $t('sicherplan.customerPlansWizard.actions.editDemandGroupDays') }}
                    </button>
                    <button
                      type="button"
                      class="cta-button cta-secondary"
                      :data-testid="`customer-new-plan-demand-group-persisted-edit-${row.signature_key}`"
                      :disabled="stepLoading || row.has_locked_rows"
                      @click="openAggregateDemandGroupEditDialog(row.signature_key)"
                    >
                      {{ $t('sicherplan.customerPlansWizard.actions.editDemandGroupAggregate') }}
                    </button>
                  </div>
                </header>
                <div class="sp-customer-plan-wizard-step__demand-group-card-status-row">
                  <span
                    class="sp-customer-plan-wizard-step__status-badge"
                    :class="`sp-customer-plan-wizard-step__status-badge--${row.status}`"
                    :data-testid="`customer-new-plan-demand-group-persisted-status-${row.signature_key}`"
                  >
                    {{
                      row.status === 'complete'
                        ? $t('sicherplan.customerPlansWizard.forms.demandGroupsStatusComplete')
                        : row.status === 'mixed'
                          ? $t('sicherplan.customerPlansWizard.forms.demandGroupsStatusMixed')
                        : $t('sicherplan.customerPlansWizard.forms.demandGroupsStatusPartial')
                    }}
                  </span>
                </div>
                <div>
                  <div class="sp-customer-plan-wizard-step__info-summary sp-customer-plan-wizard-step__info-summary--compact">
                    <span><b>{{ $t('sicherplan.customerPlansWizard.forms.minQty') }}:</b> {{ row.min_qty }}</span>
                    <span><b>{{ $t('sicherplan.customerPlansWizard.forms.targetQty') }}:</b> {{ row.target_qty }}</span>
                    <span><b>{{ $t('sicherplan.customerPlansWizard.forms.sortOrder') }}:</b> {{ row.sort_order }}</span>
                    <span><b>{{ row.mandatory_flag ? $t('sicherplan.customerPlansWizard.forms.mandatoryFlag') : $t('sicherplan.customerPlansWizard.forms.optionalFlag') }}</b></span>
                    <span>{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsAppliedShiftCount', { applied: row.applied_shift_count, total: row.total_shift_count }) }}</span>
                    <span v-if="row.missing_shift_count">{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsMissingShiftCount', { count: row.missing_shift_count }) }}</span>
                    <span v-if="row.variant_count > 1">{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsVariantCount', { count: row.variant_count }) }}</span>
                    <span v-if="row.remark">{{ row.remark }}</span>
                    <span v-if="row.has_locked_rows" class="sp-customer-plan-wizard-step__lock-chip">
                      {{ $t('sicherplan.customerPlansWizard.messages.demandGroupsLockedHint') }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>
      <section class="sp-customer-plan-wizard-step__document-subsection" data-testid="customer-new-plan-demand-group-draft-section">
        <header class="sp-customer-plan-wizard-step__document-subsection-header">
          <h5>{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsDraftTitle') }}</h5>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.demandGroupsDraftHelp') }}</p>
        </header>
      <div
        v-if="demandGroupDraftRowsDisplay.length"
        class="sp-customer-plan-wizard-step__list"
        data-testid="customer-new-plan-demand-group-list"
      >
        <article
          v-for="row in demandGroupDraftRowsDisplay"
          :key="row.id"
          class="sp-customer-plan-wizard-step__document-subsection"
          data-testid="customer-new-plan-demand-group-row"
        >
          <header class="sp-customer-plan-wizard-step__document-subsection-header">
            <h5>{{ $t('sicherplan.customerPlansWizard.forms.demandGroupRowLabel', { index: row.index + 1 }) }}</h5>
          </header>
          <div class="sp-customer-plan-wizard-step__info-summary">
            <strong>{{ row.function_type_label }}</strong>
            <span>{{ row.qualification_type_label }}</span>
            <span>{{ $t('sicherplan.customerPlansWizard.forms.minQty') }}: {{ row.min_qty }}</span>
            <span>{{ $t('sicherplan.customerPlansWizard.forms.targetQty') }}: {{ row.target_qty }}</span>
            <span>{{ $t('sicherplan.customerPlansWizard.forms.sortOrder') }}: {{ row.sort_order }}</span>
            <span>{{ row.mandatory_flag ? $t('sicherplan.customerPlansWizard.forms.mandatoryFlag') : $t('sicherplan.customerPlansWizard.forms.optionalFlag') }}</span>
            <span v-if="row.remark">{{ row.remark }}</span>
          </div>
          <div class="cta-row">
            <button
              type="button"
              class="cta-button cta-secondary"
              :data-testid="`customer-new-plan-demand-group-edit-${row.index}`"
              :disabled="stepLoading"
              @click="openEditDemandGroupDialog(row.id)"
            >
              {{ $t('sicherplan.customerPlansWizard.actions.editDemandGroup') }}
            </button>
            <button
              type="button"
              class="cta-button cta-secondary"
              :data-testid="`customer-new-plan-demand-group-remove-${row.index}`"
              :disabled="stepLoading"
              @click="removeDemandGroupDraftRow(row.id)"
            >
              {{ $t('sicherplan.customerPlansWizard.actions.removeDemandGroup') }}
            </button>
          </div>
        </article>
      </div>
      <p
        v-else
        class="field-help"
        data-testid="customer-new-plan-demand-group-list-empty"
      >
        {{ $t('sicherplan.customerPlansWizard.forms.demandGroupsDraftEmpty') }}
      </p>
      </section>
    </section>

    <CustomerNewPlanAssignmentsStep
      v-else-if="assignmentsStepActive"
      ref="assignmentsStepRef"
      :access-token="props.accessToken"
      :tenant-id="props.tenantId"
      :wizard-state="props.wizardState"
      @step-completion="(stepId, completed) => emit('step-completion', stepId, completed)"
      @step-ui-state="(stepId, patch) => emit('step-ui-state', stepId, patch)"
    />

    <section v-else class="sp-customer-plan-wizard-step__panel" data-testid="customer-new-plan-step-panel-placeholder">
      <p>{{ $t('sicherplan.customerPlansWizard.stepLead') }}</p>
      <p>{{ $t('sicherplan.customerPlansWizard.stepContentBody') }}</p>
    </section>

    <Modal
      v-model:open="demandGroupDialog.open"
      :footer="null"
      :title="
        editingDemandGroupDraftId
          ? $t('sicherplan.customerPlansWizard.dialogs.demandGroupEditTitle')
          : $t('sicherplan.customerPlansWizard.dialogs.demandGroupCreateTitle')
      "
      wrap-class-name="sp-customer-plan-wizard-modal"
      @cancel="closeDemandGroupDialog"
    >
      <form
        class="sp-customer-plan-wizard-step__modal"
        data-testid="customer-new-plan-demand-group-modal"
        @submit.prevent="submitDemandGroupDialog"
      >
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.functionType') }}</span>
            <select v-model="demandGroupDialog.function_type_id" data-testid="customer-new-plan-demand-group-modal-function-type">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.functionTypePlaceholder') }}</option>
              <option v-for="option in functionTypeSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.qualificationType') }}</span>
            <select v-model="demandGroupDialog.qualification_type_id" data-testid="customer-new-plan-demand-group-modal-qualification-type">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.qualificationTypePlaceholder') }}</option>
              <option v-for="option in qualificationTypeSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.minQty') }}</span>
            <input v-model.number="demandGroupDialog.min_qty" data-testid="customer-new-plan-demand-group-modal-min-qty" min="0" type="number" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.targetQty') }}</span>
            <input v-model.number="demandGroupDialog.target_qty" data-testid="customer-new-plan-demand-group-modal-target-qty" min="0" type="number" />
          </label>
          <label class="planning-admin-checkbox planning-admin-checkbox--centered">
            <input v-model="demandGroupDialog.mandatory_flag" data-testid="customer-new-plan-demand-group-modal-mandatory" type="checkbox" />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.mandatoryFlag') }}</span>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.sortOrder') }}</span>
            <input v-model.number="demandGroupDialog.sort_order" data-testid="customer-new-plan-demand-group-modal-sort-order" min="1" type="number" />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.remark') }}</span>
            <textarea v-model="demandGroupDialog.remark" data-testid="customer-new-plan-demand-group-modal-remark" rows="2" />
          </label>
        </div>
        <div class="cta-row">
          <button class="cta-button" data-testid="customer-new-plan-demand-group-modal-save" type="submit">
            {{
              editingDemandGroupDraftId
                ? $t('sicherplan.customerPlansWizard.actions.updateDemandGroup')
                : $t('sicherplan.customerPlansWizard.actions.saveDemandGroup')
            }}
          </button>
          <button
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-demand-group-modal-cancel"
            type="button"
            @click="closeDemandGroupDialog"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.cancelDemandGroup') }}
          </button>
        </div>
      </form>
    </Modal>

    <Modal
      v-model:open="aggregateDemandGroupDialog.open"
      :footer="null"
      :title="$t('sicherplan.customerPlansWizard.dialogs.demandGroupAggregateEditTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @cancel="closeAggregateDemandGroupEditDialog"
    >
      <form
        class="sp-customer-plan-wizard-step__modal"
        data-testid="customer-new-plan-demand-group-aggregate-modal"
        @submit.prevent="submitAggregateDemandGroupDialog"
      >
        <p
          v-if="selectedAggregateDemandGroupRow?.status === 'mixed'"
          class="field-help"
          data-testid="customer-new-plan-demand-group-aggregate-warning"
        >
          {{ $t('sicherplan.customerPlansWizard.messages.demandGroupsMixedWarning') }}
        </p>
        <div class="sp-customer-plan-wizard-step__grid">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.functionType') }}</span>
            <select v-model="aggregateDemandGroupDialog.function_type_id" data-testid="customer-new-plan-demand-group-aggregate-function-type">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.functionTypePlaceholder') }}</option>
              <option v-for="option in functionTypeSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.qualificationType') }}</span>
            <select v-model="aggregateDemandGroupDialog.qualification_type_id" data-testid="customer-new-plan-demand-group-aggregate-qualification-type">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.qualificationTypePlaceholder') }}</option>
              <option v-for="option in qualificationTypeSelectOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.minQty') }}</span>
            <input v-model.number="aggregateDemandGroupDialog.min_qty" data-testid="customer-new-plan-demand-group-aggregate-min-qty" min="0" type="number" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.targetQty') }}</span>
            <input v-model.number="aggregateDemandGroupDialog.target_qty" data-testid="customer-new-plan-demand-group-aggregate-target-qty" min="0" type="number" />
          </label>
          <label class="planning-admin-checkbox planning-admin-checkbox--centered">
            <input v-model="aggregateDemandGroupDialog.mandatory_flag" data-testid="customer-new-plan-demand-group-aggregate-mandatory" type="checkbox" />
            <span>{{ $t('sicherplan.customerPlansWizard.forms.mandatoryFlag') }}</span>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.sortOrder') }}</span>
            <input v-model.number="aggregateDemandGroupDialog.sort_order" data-testid="customer-new-plan-demand-group-aggregate-sort-order" min="1" type="number" />
          </label>
          <label class="field-stack field-stack--wide">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.remark') }}</span>
            <textarea v-model="aggregateDemandGroupDialog.remark" data-testid="customer-new-plan-demand-group-aggregate-remark" rows="2" />
          </label>
        </div>
        <p v-if="aggregateDemandGroupValidationError" class="field-help" data-testid="customer-new-plan-demand-group-aggregate-validation">
          {{ aggregateDemandGroupValidationError }}
        </p>
        <div class="cta-row">
          <button class="cta-button" data-testid="customer-new-plan-demand-group-aggregate-save" :disabled="aggregateDemandGroupSaving" type="submit">
            {{ $t('sicherplan.customerPlansWizard.actions.saveDemandGroupAggregate') }}
          </button>
          <button
            class="cta-button cta-secondary"
            data-testid="customer-new-plan-demand-group-aggregate-cancel"
            :disabled="aggregateDemandGroupSaving"
            type="button"
            @click="closeAggregateDemandGroupEditDialog"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.cancelDemandGroup') }}
          </button>
        </div>
      </form>
    </Modal>

    <Modal
      v-model:open="shiftDemandGroupDialog.open"
      :footer="null"
      :title="$t('sicherplan.customerPlansWizard.dialogs.demandGroupShiftEditTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @cancel="closeShiftDemandGroupEditDialog"
    >
      <div class="sp-customer-plan-wizard-step__modal" data-testid="customer-new-plan-demand-group-shift-modal">
        <div class="sp-customer-plan-wizard-step__demand-group-shift-list">
          <button
            v-for="row in selectedShiftDemandGroupRows"
            :key="row.demand_group_id"
            type="button"
            class="sp-customer-plan-wizard-step__demand-group-shift-list-row"
            :class="{ 'is-selected': row.demand_group_id === selectedShiftDemandGroupId }"
            :data-testid="`customer-new-plan-demand-group-shift-row-${row.demand_group_id}`"
            @click="selectedShiftDemandGroupId = row.demand_group_id"
          >
            <strong>{{ row.shift_label }}</strong>
            <span>{{ row.shift_type_code }}</span>
            <span v-if="row.location_text">{{ row.location_text }}</span>
            <span v-if="row.locked" class="sp-customer-plan-wizard-step__lock-chip">{{ row.lock_reason }}</span>
          </button>
        </div>
        <form class="sp-customer-plan-wizard-step__modal" @submit.prevent="submitShiftDemandGroupDialog">
          <div class="sp-customer-plan-wizard-step__grid">
            <label class="field-stack">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.functionType') }}</span>
              <select v-model="shiftDemandGroupDialogDraft.function_type_id" data-testid="customer-new-plan-demand-group-shift-function-type" :disabled="selectedShiftDemandGroupRow?.locked || shiftDemandGroupSaving">
                <option value="">{{ $t('sicherplan.customerPlansWizard.forms.functionTypePlaceholder') }}</option>
                <option v-for="option in functionTypeSelectOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
            <label class="field-stack">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.qualificationType') }}</span>
              <select v-model="shiftDemandGroupDialogDraft.qualification_type_id" data-testid="customer-new-plan-demand-group-shift-qualification-type" :disabled="selectedShiftDemandGroupRow?.locked || shiftDemandGroupSaving">
                <option value="">{{ $t('sicherplan.customerPlansWizard.forms.qualificationTypePlaceholder') }}</option>
                <option v-for="option in qualificationTypeSelectOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
            <label class="field-stack">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.minQty') }}</span>
              <input v-model.number="shiftDemandGroupDialogDraft.min_qty" data-testid="customer-new-plan-demand-group-shift-min-qty" min="0" type="number" :disabled="selectedShiftDemandGroupRow?.locked || shiftDemandGroupSaving" />
            </label>
            <label class="field-stack">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.targetQty') }}</span>
              <input v-model.number="shiftDemandGroupDialogDraft.target_qty" data-testid="customer-new-plan-demand-group-shift-target-qty" min="0" type="number" :disabled="selectedShiftDemandGroupRow?.locked || shiftDemandGroupSaving" />
            </label>
            <label class="planning-admin-checkbox planning-admin-checkbox--centered">
              <input v-model="shiftDemandGroupDialogDraft.mandatory_flag" data-testid="customer-new-plan-demand-group-shift-mandatory" type="checkbox" :disabled="selectedShiftDemandGroupRow?.locked || shiftDemandGroupSaving" />
              <span>{{ $t('sicherplan.customerPlansWizard.forms.mandatoryFlag') }}</span>
            </label>
            <label class="field-stack">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.sortOrder') }}</span>
              <input v-model.number="shiftDemandGroupDialogDraft.sort_order" data-testid="customer-new-plan-demand-group-shift-sort-order" min="1" type="number" :disabled="selectedShiftDemandGroupRow?.locked || shiftDemandGroupSaving" />
            </label>
            <label class="field-stack field-stack--wide">
              <span>{{ $t('sicherplan.customerPlansWizard.forms.remark') }}</span>
              <textarea v-model="shiftDemandGroupDialogDraft.remark" data-testid="customer-new-plan-demand-group-shift-remark" rows="2" :disabled="selectedShiftDemandGroupRow?.locked || shiftDemandGroupSaving" />
            </label>
          </div>
          <p v-if="shiftDemandGroupValidationError" class="field-help" data-testid="customer-new-plan-demand-group-shift-validation">
            {{ shiftDemandGroupValidationError }}
          </p>
          <div class="cta-row">
            <button class="cta-button" data-testid="customer-new-plan-demand-group-shift-save" :disabled="!selectedShiftDemandGroupRow || selectedShiftDemandGroupRow.locked || shiftDemandGroupSaving" type="submit">
              {{ $t('sicherplan.customerPlansWizard.actions.saveDemandGroupShift') }}
            </button>
            <button
              class="cta-button cta-secondary"
              data-testid="customer-new-plan-demand-group-shift-cancel"
              :disabled="shiftDemandGroupSaving"
              type="button"
              @click="closeShiftDemandGroupEditDialog"
            >
              {{ $t('sicherplan.customerPlansWizard.actions.cancelDemandGroup') }}
            </button>
          </div>
        </form>
      </div>
    </Modal>

    <Modal
      v-model:open="documentPicker.open"
      :footer="null"
      :title="$t('sicherplan.customerPlansWizard.forms.documentPickerTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal sp-customer-plan-wizard-modal--document-picker"
      @cancel="closeDocumentPicker"
    >
      <div
        class="sp-customer-plan-wizard-step__modal sp-customer-plan-wizard-step__document-picker-modal"
        :data-testid="documentPickerTestId('picker-modal')"
      >
        <label class="field-stack sp-customer-plan-wizard-step__document-picker-search">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.documentPickerSearch') }}</span>
          <input
            v-model="documentPicker.search"
            :placeholder="$t('sicherplan.customerPlansWizard.forms.documentPickerSearchPlaceholder')"
            :data-testid="documentPickerTestId('search')"
            @keyup.enter="void searchDocumentPicker()"
          />
        </label>
        <div class="cta-row">
          <button class="cta-button" type="button" :disabled="documentPicker.loading" @click="void searchDocumentPicker()">
            {{ $t('sicherplan.customerPlansWizard.forms.documentPickerSearchAction') }}
          </button>
          <span v-if="documentPicker.loading" class="field-help">{{ $t('sicherplan.customerPlansWizard.forms.documentPickerLoading') }}</span>
        </div>
        <p v-if="documentPicker.error" class="field-help">{{ documentPicker.error }}</p>
        <div
          v-if="documentPicker.results.length"
          class="sp-customer-plan-wizard-step__list sp-customer-plan-wizard-step__document-picker-results"
        >
          <button
            v-for="document in documentPicker.results"
            :key="document.id"
            type="button"
            class="sp-customer-plan-wizard-step__list-row sp-customer-plan-wizard-step__document-picker-row"
            :data-testid="documentPickerTestId('result-row')"
            @click="selectDocumentForLink(document)"
          >
            <div class="sp-customer-plan-wizard-step__document-picker-copy">
              <strong class="sp-customer-plan-wizard-step__document-picker-title">{{ documentPickerTitle(document) }}</strong>
              <div class="sp-customer-plan-wizard-step__document-picker-meta">
                <span
                  v-for="entry in documentPickerMetadata(document)"
                  :key="`${document.id}-${entry}`"
                  class="sp-customer-plan-wizard-step__document-picker-meta-item"
                >
                  {{ entry }}
                </span>
              </div>
            </div>
          </button>
        </div>
        <p v-else-if="!documentPicker.loading" class="field-help">
          {{ $t('sicherplan.customerPlansWizard.forms.documentPickerEmpty') }}
        </p>
      </div>
    </Modal>

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
      v-model:open="exceptionModal.open"
      :confirm-loading="exceptionModal.saving"
      :footer="null"
      :title="$t('sicherplan.customerPlansWizard.dialogs.exceptionTitle')"
      wrap-class-name="sp-customer-plan-wizard-modal"
      @cancel="closeExceptionModal"
    >
      <div
        class="sp-customer-plan-wizard-step__modal"
        data-testid="customer-new-plan-exception-dialog"
        data-order-workspace-testid="customer-order-workspace-exception-dialog"
      >
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.exceptionDate') }}</span>
          <input v-model="exceptionDraft.exception_date" data-testid="customer-new-plan-series-exception-date" type="date" />
        </label>
        <label class="field-stack">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.actionCode') }}</span>
          <select v-model="exceptionDraft.action_code" data-testid="customer-new-plan-series-exception-action-code">
            <option value="skip">{{ $t('sicherplan.customerPlansWizard.forms.exceptionActionSkip') }}</option>
            <option value="override">{{ $t('sicherplan.customerPlansWizard.forms.exceptionActionOverride') }}</option>
          </select>
        </label>
        <template v-if="exceptionOverrideActive">
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideStartTime') }}</span>
            <input v-model="exceptionDraft.override_local_start_time" data-testid="customer-new-plan-series-exception-override-start" type="time" />
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.overrideEndTime') }}</span>
            <input v-model="exceptionDraft.override_local_end_time" data-testid="customer-new-plan-series-exception-override-end" type="time" />
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
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.customerVisible') }}</span>
            <select v-model="exceptionCustomerVisibleModel" data-testid="customer-new-plan-series-exception-customer-visible">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.inheritValue') }}</option>
              <option value="true">{{ $t('sicherplan.customerPlansWizard.forms.yesValue') }}</option>
              <option value="false">{{ $t('sicherplan.customerPlansWizard.forms.noValue') }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.subcontractorVisible') }}</span>
            <select v-model="exceptionSubcontractorVisibleModel" data-testid="customer-new-plan-series-exception-subcontractor-visible">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.inheritValue') }}</option>
              <option value="true">{{ $t('sicherplan.customerPlansWizard.forms.yesValue') }}</option>
              <option value="false">{{ $t('sicherplan.customerPlansWizard.forms.noValue') }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ $t('sicherplan.customerPlansWizard.forms.stealthMode') }}</span>
            <select v-model="exceptionStealthModeModel" data-testid="customer-new-plan-series-exception-stealth-mode">
              <option value="">{{ $t('sicherplan.customerPlansWizard.forms.inheritValue') }}</option>
              <option value="true">{{ $t('sicherplan.customerPlansWizard.forms.yesValue') }}</option>
              <option value="false">{{ $t('sicherplan.customerPlansWizard.forms.noValue') }}</option>
            </select>
          </label>
        </template>
        <label class="field-stack field-stack--wide">
          <span>{{ $t('sicherplan.customerPlansWizard.forms.notes') }}</span>
          <textarea v-model="exceptionDraft.notes" rows="2" />
        </label>
        <div class="cta-row">
          <button
            type="button"
            class="cta-button"
            data-testid="customer-new-plan-save-exception"
            data-order-workspace-testid="customer-order-workspace-save-exception"
            :disabled="exceptionModal.saving"
            @click="void saveExceptionDraft()"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.saveException') }}
          </button>
          <button
            type="button"
            class="cta-button cta-secondary"
            :disabled="exceptionModal.saving"
            @click="closeExceptionModal"
          >
            {{ $t('sicherplan.customerPlansWizard.actions.cancel') }}
          </button>
        </div>
      </div>
    </Modal>

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

.sp-customer-plan-wizard-step__scope-documents {
  display: grid;
  gap: 1rem;
  width: 100%;
  min-width: 0;
}

.sp-customer-order-scope-onepage {
  --customer-order-scope-sticky-top: calc(var(--sp-sticky-offset, 6.5rem) + 25px);
  position: relative;
  display: grid;
  grid-template-columns: minmax(190px, 240px) minmax(0, 1fr);
  gap: 1.25rem;
  align-items: start;
  min-width: 0;
}

.sp-customer-order-scope-content {
  grid-column: 2;
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.sp-customer-order-scope-nav-shell {
  grid-column: 1;
  position: sticky;
  top: var(--customer-order-scope-sticky-top, 6.5rem);
  align-self: start;
  z-index: 2;
  min-width: 0;
  max-height: calc(100vh - var(--customer-order-scope-sticky-top, 6.5rem) - 1rem);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.sp-customer-order-scope-nav-shell--fixed {
  position: fixed;
}

.sp-customer-order-scope-nav-shell--pinned {
  position: absolute;
}

.sp-customer-order-scope-nav {
  display: grid;
  gap: 0.25rem;
  padding: 0.25rem 0;
  border: 0;
  background: transparent;
}

.sp-customer-order-scope-nav__link {
  display: grid;
  grid-template-columns: 1.25rem minmax(0, 1fr);
  align-items: center;
  gap: 0.55rem;
  width: 100%;
  padding: 0.55rem 0.35rem 0.55rem 0.75rem;
  border: 0;
  border-left: 2px solid transparent;
  border-radius: 0.35rem;
  background: transparent;
  color: var(--sp-color-text-secondary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.sp-customer-order-scope-nav__link:hover,
.sp-customer-order-scope-nav__link:focus-visible {
  color: var(--sp-color-primary-strong);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 36%, transparent);
  outline: none;
}

.sp-customer-order-scope-nav__link:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--sp-color-primary) 38%, transparent);
  outline-offset: 2px;
}

.sp-customer-order-scope-nav__link--active {
  border-left-color: var(--sp-color-primary);
  color: var(--sp-color-primary-strong);
  font-weight: 700;
}

.sp-customer-order-scope-nav__icon {
  width: 1.08rem;
  height: 1.08rem;
  color: currentColor;
}

.sp-customer-plan-wizard-step__scope-card {
  display: grid;
  gap: 1rem;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-elevation-sm, 0 10px 30px rgb(15 23 42 / 0.06));
  overflow: hidden;
  scroll-margin-top: var(--customer-order-scope-sticky-top, 6.5rem);
}

.sp-customer-plan-wizard-step__scope-card--invalid {
  border-color: rgb(210 40 40 / 42%);
  box-shadow:
    0 0 0 3px rgb(210 40 40 / 10%),
    var(--sp-elevation-sm, 0 10px 30px rgb(15 23 42 / 0.06));
}

.sp-customer-plan-wizard-step__scope-card-header {
  display: grid;
  gap: 0.25rem;
}

.sp-customer-plan-wizard-step__scope-card-header h4 {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: 1rem;
  font-weight: 700;
}

.sp-customer-plan-wizard-step__editor-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.sp-customer-plan-wizard-step__editor-header p {
  margin: 0;
}

.sp-customer-plan-wizard-step__scope-action-row {
  margin-bottom: 0;
}

.sp-customer-plan-wizard-step__scope-subsection {
  display: grid;
  gap: 0.65rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__scope-saved-list {
  display: grid;
  gap: 0.65rem;
  min-width: 0;
  margin: 0.15rem 0 0.35rem;
}

.sp-customer-plan-wizard-step__scope-editor {
  display: grid;
  gap: 0.85rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__scope-editor--invalid {
  padding: 0.1rem 0;
}

.sp-customer-plan-wizard-step__documents-panel {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__document-list {
  margin: 0.7rem 0 1rem;
}

.sp-customer-plan-wizard-step__document-row-copy {
  display: grid;
  gap: 0.18rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__planning-record-row-copy {
  display: grid;
  gap: 0.18rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__document-subsection {
  display: grid;
  gap: 1rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__document-subsection--invalid {
  padding: 0.15rem 0;
}

.sp-customer-plan-wizard-step__document-subsection-header {
  display: grid;
  gap: 0.25rem;
}

.sp-customer-plan-wizard-step__document-subsection-header h5 {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: 0.96rem;
  font-weight: 700;
}

.sp-customer-plan-wizard-step__document-divider {
  height: 1px;
  margin: 0.85rem 0 0.45rem;
  background: var(--sp-color-border-soft);
}

.sp-customer-plan-wizard-step__planning-record-card {
  display: grid;
  gap: 1.05rem;
}

.sp-customer-plan-wizard-step__planning-record-subsection {
  display: grid;
  gap: 0.85rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__planning-record-subsection-header {
  display: grid;
  gap: 0.25rem;
}

.sp-customer-plan-wizard-step__planning-record-subsection-header--with-action {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.sp-customer-plan-wizard-step__planning-record-subsection-header p {
  margin: 0;
}

.sp-customer-plan-wizard-step__planning-record-subsection-title {
  display: grid;
  gap: 0.25rem;
  min-width: min(100%, 16rem);
}

.sp-customer-plan-wizard-step__planning-record-divider {
  height: 1px;
  margin: 0.35rem 0;
  background: var(--sp-color-border-soft);
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

.field-stack--invalid input,
.field-stack--invalid select,
.field-stack--invalid textarea {
  border-color: rgb(210 40 40 / 72%);
  box-shadow: 0 0 0 3px rgb(210 40 40 / 10%);
}

.field-error {
  margin: -0.15rem 0 0;
  color: rgb(190 30 30);
  font-size: 0.78rem;
  font-weight: 650;
}

.sp-customer-plan-wizard-step__section-error {
  margin-top: -0.1rem;
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

.sp-customer-plan-wizard-step__weekday-picker {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.sp-customer-plan-wizard-step__weekday-chip {
  min-width: 2.5rem;
  padding: 0.45rem 0.72rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 999px;
  background: var(--sp-color-surface-page);
  color: var(--sp-color-text-secondary);
  font-size: 0.82rem;
  font-weight: 600;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease,
    transform 0.18s ease;
}

.sp-customer-plan-wizard-step__weekday-chip:hover,
.sp-customer-plan-wizard-step__weekday-chip:focus-visible {
  border-color: rgb(40 170 170 / 48%);
  color: var(--sp-color-text-primary);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 10%);
  outline: none;
}

.sp-customer-plan-wizard-step__weekday-chip--active {
  border-color: rgb(40 170 170 / 65%);
  background: rgb(40 170 170 / 14%);
  color: rgb(18 112 112);
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

.sp-customer-plan-wizard-step__list-row-main {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
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

.sp-customer-order-row-label {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.55rem;
  align-items: baseline;
  min-width: 0;
}

.sp-customer-order-row-label span {
  text-align: left;
}

.sp-customer-order-row__primary {
  color: var(--sp-color-text-primary);
  font-weight: 700;
}

.sp-customer-order-row__secondary {
  color: var(--sp-color-text-secondary);
}

.sp-customer-plan-wizard-step__list-row:not(.sp-customer-plan-wizard-step__list-row--static):hover,
.sp-customer-plan-wizard-step__list-row:has(.sp-customer-plan-wizard-step__list-row-main:focus-visible) {
  border-color: rgb(40 170 170 / 38%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 10%);
  transform: translateY(-1px);
}

.sp-customer-plan-wizard-step__list-row-main:focus-visible {
  outline: none;
}

.sp-customer-plan-wizard-step__list-row--selected {
  border-color: rgb(40 170 170 / 48%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 12%);
}

.sp-customer-plan-wizard-step__list-row--static {
  align-items: center;
}

.sp-customer-plan-wizard-step__list-row--document {
  align-items: flex-start;
}

.sp-customer-plan-wizard-step__info-summary {
  display: flex;
  gap: 0.3rem;
  padding: 0.95rem 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: color-mix(in srgb, var(--sp-color-surface-page) 82%, rgb(40 170 170));
  color: var(--sp-color-text-secondary);
  cursor: default;
}

.sp-customer-plan-wizard-step__info-summary strong {
  color: var(--sp-color-text-primary);
}

.sp-customer-plan-wizard-step__dependent-section {
  display: grid;
  gap: 0.9rem;
  padding-top: 1rem;
  border-top: 1px solid var(--sp-color-border-soft);
}

.sp-customer-plan-wizard-step__gating-helper {
  margin: 0;
  padding: 0.8rem 0.9rem;
  border: 1px dashed var(--sp-color-border-soft);
  border-radius: 0.85rem;
  background: color-mix(in srgb, var(--sp-color-surface-page) 92%, rgb(40 170 170));
}

.sp-customer-plan-wizard-step__series-loading-row {
  display: flex;
  align-items: center;
  min-height: 2.6rem;
}

.sp-customer-plan-wizard-step__template-helper {
  display: grid;
  grid-template-columns: minmax(14rem, 22rem) max-content;
  gap: 0.75rem;
  align-items: end;
  padding: 0.8rem 0.9rem;
  border: 1px dashed var(--sp-color-border-soft);
  border-radius: 0.9rem;
  background: color-mix(in srgb, var(--sp-color-surface-page) 90%, rgb(40 170 170));
}

.sp-customer-plan-wizard-step__generation-grid {
  display: grid;
  grid-template-columns: minmax(10rem, 14rem) minmax(10rem, 14rem) minmax(12rem, max-content);
  gap: 0.9rem;
  align-items: end;
}

.sp-customer-plan-wizard-step__generation-date-field {
  max-width: 14rem;
}

.sp-customer-plan-wizard-step__generation-checkbox {
  padding-top: 0;
}

.sp-customer-plan-wizard-step__exception-action-row {
  margin-bottom: 0.15rem;
}

.sp-customer-plan-wizard-step__exception-list {
  margin-top: 0.45rem;
}

.sp-customer-plan-wizard-step__row-action {
  flex: 0 0 auto;
}

.sp-customer-plan-wizard-step__row-link-action {
  flex: 0 0 auto;
  padding: 0.25rem 0.35rem;
  border: 0;
  border-radius: 0.45rem;
  background: transparent;
  color: rgb(18 112 112);
  font: inherit;
  font-size: 0.84rem;
  font-weight: 700;
  cursor: pointer;
}

.sp-customer-plan-wizard-step__row-link-action:hover,
.sp-customer-plan-wizard-step__row-link-action:focus-visible {
  outline: none;
  background: rgb(40 170 170 / 10%);
  color: rgb(12 92 92);
}

.sp-customer-plan-wizard-step__list-action {
  flex: 0 0 auto;
  min-height: 2.25rem;
  padding: 0.42rem 0.72rem;
  border: 1px solid color-mix(in srgb, var(--sp-color-border-soft) 72%, var(--sp-color-danger));
  border-radius: 999px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 88%, var(--sp-color-danger));
  color: var(--sp-color-danger);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease,
    transform 0.18s ease;
}

.sp-customer-plan-wizard-step__list-action--compact {
  font-size: 0.78rem;
  line-height: 1.15;
}

.sp-customer-plan-wizard-step__list-action--document-remove {
  min-height: 1.85rem;
  padding: 0.32rem 0.6rem;
}

.sp-customer-plan-wizard-step__list-action:hover,
.sp-customer-plan-wizard-step__list-action:focus-visible {
  border-color: color-mix(in srgb, var(--sp-color-danger) 54%, var(--sp-color-border-soft));
  background: color-mix(in srgb, var(--sp-color-surface-page) 78%, var(--sp-color-danger));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--sp-color-danger) 13%, transparent);
  outline: none;
}

.sp-customer-plan-wizard-step__list-action:disabled {
  opacity: 0.62;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
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

.sp-customer-plan-wizard-step__document-selection {
  display: grid;
  gap: 0.25rem;
  padding: 0.8rem 0.9rem;
  border: 1px solid rgb(40 170 170 / 28%);
  border-radius: 1rem;
  background: rgb(40 170 170 / 8%);
}

.sp-customer-plan-wizard-step__document-selection span {
  color: var(--sp-color-text-secondary);
  overflow-wrap: anywhere;
}

.planning-admin-checkbox {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  min-height: 2.6rem;
  min-width: 0;
  color: var(--sp-color-text-secondary);
}

.planning-admin-checkbox--centered {
  align-self: center;
  padding-top: 1.4rem;
}

.planning-admin-checkbox input[type='checkbox'],
.planning-admin-checkbox input[type='radio'] {
  flex: 0 0 auto;
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--sp-color-primary);
  cursor: pointer;
}

.planning-admin-checkbox span {
  font-weight: 500;
}

@media (max-width: 720px) {
  .sp-customer-plan-wizard-step__template-helper {
    grid-template-columns: minmax(0, 1fr);
  }

  .sp-customer-plan-wizard-step__generation-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .sp-customer-plan-wizard-step__generation-date-field {
    max-width: none;
  }
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

.cta-button--invalid {
  border: 1px solid rgb(210 40 40 / 58%);
  box-shadow: 0 0 0 3px rgb(210 40 40 / 10%);
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
  width: 100%;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.sp-customer-plan-wizard-step__document-picker-modal {
  overflow: hidden;
}

.sp-customer-plan-wizard-step__document-picker-search {
  width: 100%;
  min-width: 0;
  max-width: 100%;
}

.sp-customer-plan-wizard-step__document-picker-results {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  max-height: min(24rem, 60vh);
  overflow-x: hidden;
  overflow-y: auto;
  padding-right: 0.1rem;
}

.sp-customer-plan-wizard-step__document-picker-row {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  align-items: flex-start;
  justify-content: flex-start;
}

.sp-customer-plan-wizard-step__document-picker-copy {
  display: grid;
  gap: 0.35rem;
  width: 100%;
  min-width: 0;
}

.sp-customer-plan-wizard-step__document-picker-title {
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.sp-customer-plan-wizard-step__document-picker-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.5rem;
  width: 100%;
  min-width: 0;
  max-width: 100%;
}

.sp-customer-plan-wizard-step__document-picker-meta-item {
  min-width: 0;
  max-width: 100%;
  color: var(--sp-color-text-secondary);
  overflow-wrap: anywhere;
  word-break: break-word;
}

.sp-customer-plan-wizard-step__list--compact {
  gap: 0.75rem;
}

.sp-customer-plan-wizard-step__document-subsection--compact {
  padding: 0.85rem 1rem;
  border: 1px solid var(--sp-color-border-soft);
  background: color-mix(in srgb, var(--sp-color-surface-page) 84%, white);
}

.sp-customer-plan-wizard-step__document-subsection-header--compact {
  gap: 0.5rem;
  align-items: flex-start;
}

.sp-customer-plan-wizard-step__demand-group-card {
  display: grid;
  gap: 0.7rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__demand-group-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.85rem;
}

.sp-customer-plan-wizard-step__demand-group-card-title {
  min-width: 0;
}

.sp-customer-plan-wizard-step__demand-group-card-actions {
  display: flex;
  flex: 0 0 auto;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: flex-end;
}

.sp-customer-plan-wizard-step__demand-group-card-body {
  display: grid;
  gap: 0.6rem;
  min-width: 0;
}

.sp-customer-plan-wizard-step__demand-group-card-status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sp-customer-plan-wizard-step__info-summary--compact {
  gap: 0.35rem 0.6rem;
}

.sp-customer-plan-wizard-step__status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 1.6rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid var(--sp-color-border-soft);
}

.sp-customer-plan-wizard-step__status-badge--complete {
  background: rgb(40 170 170 / 10%);
  color: rgb(22 118 118);
}

.sp-customer-plan-wizard-step__status-badge--partial {
  background: rgb(210 140 40 / 12%);
  color: rgb(145 96 21);
}

.sp-customer-plan-wizard-step__status-badge--mixed {
  background: rgb(114 93 198 / 10%);
  color: rgb(82 63 158);
}

.sp-customer-plan-wizard-step__lock-chip {
  color: rgb(145 96 21);
}

.sp-customer-plan-wizard-step__demand-group-shift-list {
  display: grid;
  gap: 0.5rem;
  max-height: 16rem;
  overflow: auto;
}

.sp-customer-plan-wizard-step__demand-group-shift-list-row {
  display: grid;
  gap: 0.2rem;
  padding: 0.75rem 0.85rem;
  border-radius: 12px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  text-align: left;
  color: var(--sp-color-text-primary);
}

.sp-customer-plan-wizard-step__demand-group-shift-list-row.is-selected {
  border-color: rgb(40 170 170 / 45%);
  box-shadow: 0 0 0 2px rgb(40 170 170 / 12%);
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

:deep(.sp-customer-plan-wizard-modal--document-picker .ant-modal) {
  width: min(42rem, calc(100vw - 2rem)) !important;
  max-width: calc(100vw - 2rem);
}

:deep(.sp-customer-plan-wizard-modal--document-picker .ant-modal-content),
:deep(.sp-customer-plan-wizard-modal--document-picker .ant-modal-body) {
  overflow: hidden;
}

@media (max-width: 960px) {
  .sp-customer-order-scope-onepage {
    grid-template-columns: 1fr;
  }

  .sp-customer-order-scope-nav-shell,
  .sp-customer-order-scope-content {
    grid-column: 1;
  }

  .sp-customer-order-scope-nav-shell {
    position: static;
    max-height: none;
    overflow: visible;
  }

  .sp-customer-order-scope-nav-shell--fixed,
  .sp-customer-order-scope-nav-shell--pinned {
    position: static;
  }

  .sp-customer-order-scope-nav {
    display: flex;
    overflow-x: auto;
    padding: 0.25rem 0 0.5rem;
  }

  .sp-customer-order-scope-nav__link {
    min-width: max-content;
    border-left: 0;
    border-bottom: 2px solid transparent;
    padding: 0.55rem 0.75rem;
  }

  .sp-customer-order-scope-nav__link--active {
    border-bottom-color: var(--sp-color-primary);
  }

  .sp-customer-plan-wizard-step__grid {
    grid-template-columns: 1fr;
  }

  .sp-customer-plan-wizard-step__demand-group-card {
    gap: 0.75rem;
  }

  .sp-customer-plan-wizard-step__demand-group-card-header {
    flex-direction: column;
  }

  .sp-customer-plan-wizard-step__demand-group-card-actions {
    justify-content: flex-start;
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
