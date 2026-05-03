<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue';

import { $t } from '#/locales';
import LocalLoadingIndicator from '#/components/sicherplan/local-loading-indicator.vue';
import {
  listEmployeeGroups,
  listFunctionTypes,
  listQualificationTypes,
  type EmployeeGroupRead,
  type FunctionTypeRead,
  type QualificationTypeRead,
} from '#/sicherplan-legacy/api/employeeAdmin';
import {
  applyAssignmentStep,
  getAssignmentStepSnapshot,
  listAssignmentStepCandidates,
  listTeams,
  previewAssignmentStepApply,
  type AssignmentStepApplyRequest,
  type AssignmentStepCandidateRead,
  type AssignmentStepCellRead,
  type AssignmentStepDemandGroupMatch,
  type AssignmentStepDemandGroupSummaryRead,
  type AssignmentStepDaySummaryRead,
  type AssignmentStepSnapshotRead,
  type TeamRead,
} from '#/sicherplan-legacy/api/planningStaffing';
import type {
  CustomerNewPlanStepSubmitResult,
  CustomerNewPlanWizardState,
} from './new-plan-wizard.types';

type CandidateActorKind = '' | 'employee' | 'subcontractor_worker';

interface CalendarDayCell {
  active: boolean;
  date: Date;
  dateKey: string;
  inCurrentMonth: boolean;
}

interface DayAggregate {
  assignedCount: number;
  blockedCount: number;
  cellCount: number;
  editableCount: number;
  existingAssignments: string[];
  openCount: number;
  state: string;
  targetCount: number;
}

interface AssignmentReferenceData {
  employeeGroups: EmployeeGroupRead[];
  functionTypes: FunctionTypeRead[];
  qualificationTypes: QualificationTypeRead[];
  teams: TeamRead[];
}

const assignmentReferenceCache = new Map<string, AssignmentReferenceData>();
const assignmentReferenceCacheInFlight = new Map<string, Promise<AssignmentReferenceData>>();

const props = defineProps<{
  accessToken: string;
  tenantId: string;
  wizardState: CustomerNewPlanWizardState;
}>();

const emit = defineEmits<{
  (event: 'step-completion', stepId: 'assignments', completed: boolean): void;
  (event: 'step-ui-state', stepId: 'assignments', patch: { dirty?: boolean; error?: string; loading?: boolean }): void;
}>();

const referenceLoading = ref(false);
const snapshotLoading = ref(false);
const assignmentRunning = ref(false);
const loadError = ref('');
const inlineError = ref('');
const summaryMessage = ref('');
const snapshot = ref<AssignmentStepSnapshotRead | null>(null);
const candidates = ref<AssignmentStepCandidateRead[]>([]);
const teamRows = ref<TeamRead[]>([]);
const employeeGroupRows = ref<EmployeeGroupRead[]>([]);
const functionTypeRows = ref<FunctionTypeRead[]>([]);
const qualificationTypeRows = ref<QualificationTypeRead[]>([]);
const selectedDemandGroupSignature = ref('');
const activeMonth = ref('');
const selectedCandidateId = ref('');
const dragCandidateId = ref('');
const calendarDropActive = ref(false);
const snapshotReloadSequence = ref(0);
const candidateReloadSequence = ref(0);
const snapshotRequestInFlight = new Map<string, Promise<AssignmentStepSnapshotRead>>();
const candidateRequestInFlight = new Map<string, Promise<Awaited<ReturnType<typeof listAssignmentStepCandidates>>>>();
let searchReloadTimer: ReturnType<typeof setTimeout> | null = null;

const filters = reactive<{
  actor_kind: CandidateActorKind;
  employee_group_id: string;
  search: string;
  team_id: string;
  unfilled_only: boolean;
}>({
  actor_kind: '',
  employee_group_id: '',
  search: '',
  team_id: '',
  unfilled_only: true,
});

const controlIds = {
  actorKind: 'customer-new-plan-assignments-actor-kind-input',
  demandGroup: 'customer-new-plan-assignments-demand-group-input',
  employeeGroup: 'customer-new-plan-assignments-group-input',
  search: 'customer-new-plan-assignments-search-input',
  team: 'customer-new-plan-assignments-team-input',
  unfilledOnly: 'customer-new-plan-assignments-unfilled-only-input',
} as const;

function normalizeDateKey(value: Date | string) {
  if (value instanceof Date) {
    return value.toISOString().slice(0, 10);
  }
  return value.slice(0, 10);
}

function parseDateOnly(value: string) {
  return new Date(`${normalizeDateKey(value)}T00:00:00Z`);
}

function addDays(date: Date, amount: number) {
  const result = new Date(date);
  result.setUTCDate(result.getUTCDate() + amount);
  return result;
}

function monthStart(value: string) {
  const date = parseDateOnly(value);
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
}

function monthEnd(value: string) {
  const start = monthStart(value);
  return new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 0));
}

function formatMonthKey(date: Date) {
  return date.toISOString().slice(0, 10);
}

function beginLoad() {
  emit('step-ui-state', 'assignments', { loading: true, error: '' });
}

function endLoad() {
  emit('step-ui-state', 'assignments', { loading: false });
}

function setStepError(code: string, message: string) {
  inlineError.value = message;
  emit('step-ui-state', 'assignments', { error: code });
}

function clearStepMessages() {
  inlineError.value = '';
  loadError.value = '';
  summaryMessage.value = '';
  emit('step-ui-state', 'assignments', { error: '' });
}

function buildDemandGroupMatch(row: AssignmentStepDemandGroupSummaryRead): AssignmentStepDemandGroupMatch {
  return {
    function_type_id: row.function_type_id,
    mandatory_flag: row.mandatory_flag,
    min_qty: row.min_qty,
    qualification_type_id: row.qualification_type_id || null,
    remark: row.remark || null,
    sort_order: row.sort_order,
    target_qty: row.target_qty,
  };
}

const selectedDemandGroupSummary = computed(() =>
  snapshot.value?.demand_group_summaries.find((row) => row.signature_key === selectedDemandGroupSignature.value) ?? null,
);

const demandGroupOptions = computed(() =>
  (snapshot.value?.demand_group_summaries ?? []).map((row) => ({
    coverage_state: row.coverage_state,
    label: [
      resolveFunctionLabel(row.function_type_id),
      resolveQualificationLabel(row.qualification_type_id),
    ].filter(Boolean).join(' · ') || row.signature_key,
    value: row.signature_key,
  })),
);

const currentDemandGroupMatch = computed(() =>
  selectedDemandGroupSummary.value ? buildDemandGroupMatch(selectedDemandGroupSummary.value) : null,
);

const hasPersistedAssignments = computed(() =>
  (snapshot.value?.demand_group_summaries ?? []).some((row) => row.assigned_count > 0 || row.confirmed_count > 0),
);

const assignmentStepEditable = computed(() => snapshot.value?.editable_flag !== false);
const snapshotBusy = computed(() => snapshotLoading.value || referenceLoading.value);
const currentMonthValue = computed(() => activeMonth.value || snapshot.value?.shift_plan.default_month || '');
const projectStart = computed(() => snapshot.value?.shift_plan.project_start ?? '');
const projectEnd = computed(() => snapshot.value?.shift_plan.project_end ?? '');
const activeMonths = computed(() => snapshot.value?.shift_plan.active_months ?? []);
const monthIndex = computed(() => activeMonths.value.indexOf(currentMonthValue.value));
const hasPreviousMonth = computed(() => monthIndex.value > 0);
const hasNextMonth = computed(() => monthIndex.value >= 0 && monthIndex.value < activeMonths.value.length - 1);

const calendarCellsForSelection = computed(() => {
  const selected = selectedDemandGroupSummary.value;
  if (!selected) {
    return [] as AssignmentStepCellRead[];
  }
  return (snapshot.value?.calendar_cells ?? []).filter((cell) =>
    cell.function_type_id === selected.function_type_id &&
    (cell.qualification_type_id || '') === (selected.qualification_type_id || '') &&
    cell.min_qty === selected.min_qty &&
    cell.target_qty === selected.target_qty &&
    cell.shift_id,
  );
});

const editableTargetShiftIds = computed(() => {
  const ids = new Set<string>();
  for (const cell of calendarCellsForSelection.value) {
    if (!cell.editable_flag) {
      continue;
    }
    if (filters.unfilled_only && cell.remaining_open_qty <= 0) {
      continue;
    }
    ids.add(cell.shift_id);
  }
  return [...ids];
});

const selectedCandidate = computed(() =>
  candidates.value.find((row) => row.actor_id === selectedCandidateId.value) ?? null,
);

const candidateStatusByDate = computed(() => {
  const map = new Map<string, { eligible: boolean; warning: boolean; reasons: Set<string>; warnings: Set<string> }>();
  for (const dayStatus of selectedCandidate.value?.day_statuses ?? []) {
    const key = dayStatus.occurrence_date;
    const entry = map.get(key) ?? {
      eligible: false,
      warning: false,
      reasons: new Set<string>(),
      warnings: new Set<string>(),
    };
    entry.eligible = entry.eligible || dayStatus.eligible_flag;
    entry.warning = entry.warning || dayStatus.warning_flag;
    dayStatus.reason_codes.forEach((code) => entry.reasons.add(code));
    dayStatus.warning_codes.forEach((code) => entry.warnings.add(code));
    map.set(key, entry);
  }
  return map;
});

const daySummaryByDate = computed(() => {
  const map = new Map<string, AssignmentStepDaySummaryRead>();
  for (const row of snapshot.value?.day_summaries ?? []) {
    map.set(row.occurrence_date, row);
  }
  return map;
});

const cellAggregateByDate = computed(() => {
  const map = new Map<string, DayAggregate>();
  for (const cell of calendarCellsForSelection.value) {
    const key = cell.occurrence_date;
    const entry = map.get(key) ?? {
      assignedCount: 0,
      blockedCount: 0,
      cellCount: 0,
      editableCount: 0,
      existingAssignments: [],
      openCount: 0,
      state: cell.coverage_state,
      targetCount: 0,
    };
    entry.assignedCount += cell.assigned_count;
    entry.targetCount += cell.target_qty;
    entry.openCount += Math.max(cell.remaining_open_qty, 0);
    entry.cellCount += 1;
    entry.editableCount += cell.editable_flag ? 1 : 0;
    if (!cell.editable_flag) {
      entry.blockedCount += 1;
    }
    entry.state = resolveWorseCoverageState(entry.state, cell.coverage_state);
    if (cell.existing_assignments.length) {
      entry.existingAssignments.push(...cell.existing_assignments.map((row) => row.display_name));
    }
    map.set(key, entry);
  }
  return map;
});

const summaryRibbon = computed(() => {
  return (snapshot.value?.day_summaries ?? []).reduce(
    (summary, row) => {
      summary.total += row.total_shifts;
      summary.covered += row.fully_covered_count;
      summary.warning += row.warning_count;
      summary.blocked += row.blocked_count;
      return summary;
    },
    { blocked: 0, covered: 0, total: 0, warning: 0 },
  );
});

const calendarDays = computed(() => {
  if (!currentMonthValue.value) {
    return [] as CalendarDayCell[];
  }
  const start = monthStart(currentMonthValue.value);
  const monthStartWeekday = (start.getUTCDay() + 6) % 7;
  const gridStart = addDays(start, -monthStartWeekday);
  return Array.from({ length: 42 }, (_, index) => {
    const date = addDays(gridStart, index);
    return {
      active: isDateWithinProjectRange(date),
      date,
      dateKey: normalizeDateKey(date),
      inCurrentMonth: date.getUTCMonth() === start.getUTCMonth(),
    };
  });
});

const demandGroupEmpty = computed(() => snapshot.value && snapshot.value.generated_shift_count > 0 && !snapshot.value.demand_group_summaries.length);
const noGeneratedShifts = computed(() => snapshot.value?.generated_shift_count === 0);
const noCandidates = computed(() => !snapshotBusy.value && !!selectedDemandGroupSummary.value && !candidates.value.length);

function resolveCoverageTone(state: string) {
  if (state === 'green') {
    return 'good';
  }
  if (state === 'yellow') {
    return 'warn';
  }
  return 'bad';
}

function resolveWorseCoverageState(current: string, next: string) {
  const rank = (value: string) => {
    if (value === 'green') {
      return 0;
    }
    if (value === 'yellow') {
      return 1;
    }
    return 2;
  };
  return rank(next) > rank(current) ? next : current;
}

function resolveFunctionLabel(functionTypeId: null | string) {
  if (!functionTypeId) {
    return '';
  }
  return functionTypeRows.value.find((row) => row.id === functionTypeId)?.label
    ?? functionTypeRows.value.find((row) => row.id === functionTypeId)?.code
    ?? functionTypeId;
}

function resolveQualificationLabel(qualificationTypeId: null | string) {
  if (!qualificationTypeId) {
    return '';
  }
  return qualificationTypeRows.value.find((row) => row.id === qualificationTypeId)?.label
    ?? qualificationTypeRows.value.find((row) => row.id === qualificationTypeId)?.code
    ?? qualificationTypeId;
}

function resolveTeamLabels(candidate: AssignmentStepCandidateRead) {
  return candidate.team_ids
    .map((teamId) => teamRows.value.find((row) => row.id === teamId)?.name ?? teamId)
    .filter(Boolean);
}

function resolveEmployeeGroupLabels(candidate: AssignmentStepCandidateRead) {
  return candidate.employee_group_ids
    .map((groupId) => employeeGroupRows.value.find((row) => row.id === groupId)?.name ?? groupId)
    .filter(Boolean);
}

function resolveActorKindLabel(actorKind: string) {
  return actorKind === 'subcontractor_worker'
    ? $t('sicherplan.customerPlansWizard.assignments.actorSubcontractor')
    : $t('sicherplan.customerPlansWizard.assignments.actorEmployee');
}

function isDateWithinProjectRange(date: Date) {
  if (!projectStart.value || !projectEnd.value) {
    return false;
  }
  const key = normalizeDateKey(date);
  return key >= projectStart.value && key <= projectEnd.value;
}

function buildScopePayload(includeSelectedDemandGroup = true) {
  return {
    active_month: currentMonthValue.value || null,
    actor_kind: filters.actor_kind || null,
    demand_group_match: includeSelectedDemandGroup ? currentDemandGroupMatch.value : null,
    employee_group_id: filters.employee_group_id || null,
    search: filters.search.trim() || null,
    shift_plan_id: props.wizardState.shift_plan_id,
    shift_series_id: props.wizardState.series_id || null,
    team_id: filters.team_id || null,
    tenant_id: props.tenantId,
    unfilled_only: filters.unfilled_only,
  };
}

async function loadReferenceData() {
  if (referenceLoading.value || !props.tenantId || !props.accessToken) {
    return;
  }
  referenceLoading.value = true;
  try {
    const cacheKey = props.tenantId;
    let cached = assignmentReferenceCache.get(cacheKey);
    if (!cached) {
      let inFlight = assignmentReferenceCacheInFlight.get(cacheKey);
      if (!inFlight) {
        inFlight = Promise.all([
          listTeams(props.tenantId, props.accessToken, {}),
          listEmployeeGroups(props.tenantId, props.accessToken),
          listFunctionTypes(props.tenantId, props.accessToken),
          listQualificationTypes(props.tenantId, props.accessToken),
        ]).then(([teams, employeeGroups, functionTypes, qualificationTypes]) => {
          const nextValue = {
            employeeGroups: employeeGroups.filter((row) => row.status === 'active' && !row.archived_at),
            functionTypes: functionTypes.filter((row) => row.status === 'active' && !row.archived_at),
            qualificationTypes: qualificationTypes.filter((row) => row.status === 'active' && !row.archived_at),
            teams: teams.filter((row) => row.status === 'active'),
          };
          assignmentReferenceCache.set(cacheKey, nextValue);
          return nextValue;
        }).finally(() => {
          assignmentReferenceCacheInFlight.delete(cacheKey);
        });
        assignmentReferenceCacheInFlight.set(cacheKey, inFlight);
      }
      cached = await inFlight;
    }
    teamRows.value = cached.teams;
    employeeGroupRows.value = cached.employeeGroups;
    functionTypeRows.value = cached.functionTypes;
    qualificationTypeRows.value = cached.qualificationTypes;
  } finally {
    referenceLoading.value = false;
  }
}

function syncStepCompletion() {
  emit('step-completion', 'assignments', hasPersistedAssignments.value);
  emit('step-ui-state', 'assignments', { dirty: false, error: '' });
}

async function loadSnapshot(options: { preserveSummaryMessage?: boolean } = {}) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id) {
    setStepError('missing_shift_plan', $t('sicherplan.customerPlansWizard.errors.assignmentsMissingShiftPlan'));
    return;
  }
  const requestId = ++snapshotReloadSequence.value;
  snapshotLoading.value = true;
  beginLoad();
  if (options.preserveSummaryMessage) {
    inlineError.value = '';
    loadError.value = '';
    emit('step-ui-state', 'assignments', { error: '' });
  } else {
    clearStepMessages();
  }
  try {
    const requestedWithDemandGroup = Boolean(selectedDemandGroupSignature.value);
    const payload = buildScopePayload(requestedWithDemandGroup);
    const requestKey = JSON.stringify(payload);
    let inFlight = snapshotRequestInFlight.get(requestKey);
    if (!inFlight) {
      inFlight = getAssignmentStepSnapshot(props.tenantId, props.accessToken, payload).finally(() => {
        snapshotRequestInFlight.delete(requestKey);
      });
      snapshotRequestInFlight.set(requestKey, inFlight);
    }
    const nextSnapshot = await inFlight;
    if (!activeMonth.value) {
      activeMonth.value = nextSnapshot.shift_plan.default_month;
    }
    let nextSelection = selectedDemandGroupSignature.value;
    if (!nextSelection && nextSnapshot.demand_group_summaries.length) {
      nextSelection = nextSnapshot.demand_group_summaries[0]!.signature_key;
    } else if (
      selectedDemandGroupSignature.value &&
      !nextSnapshot.demand_group_summaries.some((row) => row.signature_key === selectedDemandGroupSignature.value)
    ) {
      nextSelection = nextSnapshot.demand_group_summaries[0]?.signature_key ?? '';
    }
    if (requestId !== snapshotReloadSequence.value) {
      return;
    }
    selectedDemandGroupSignature.value = nextSelection;
    snapshot.value = nextSnapshot;
    if (requestedWithDemandGroup && nextSnapshot.candidates.length) {
      candidates.value = nextSnapshot.candidates;
    } else if (!nextSelection) {
      candidates.value = [];
    } else if (!requestedWithDemandGroup && nextSnapshot.candidates.length) {
      candidates.value = nextSnapshot.candidates;
    } else {
      await reloadCandidates({ preserveSummaryMessage: true });
    }
    if (!activeMonth.value) {
      activeMonth.value = nextSnapshot.shift_plan.default_month;
    }
    syncStepCompletion();
  } catch {
    if (requestId !== snapshotReloadSequence.value) {
      return;
    }
    loadError.value = $t('sicherplan.customerPlansWizard.errors.assignmentsLoadFailed');
    emit('step-ui-state', 'assignments', { error: 'load_failed' });
  } finally {
    if (requestId === snapshotReloadSequence.value) {
      snapshotLoading.value = false;
      endLoad();
    }
  }
}

async function reloadCandidates(options: { preserveSummaryMessage?: boolean } = {}) {
  if (!props.tenantId || !props.accessToken || !props.wizardState.shift_plan_id || !currentDemandGroupMatch.value) {
    candidates.value = [];
    return;
  }
  const requestId = ++candidateReloadSequence.value;
  snapshotLoading.value = true;
  beginLoad();
  if (options.preserveSummaryMessage) {
    inlineError.value = '';
    loadError.value = '';
    emit('step-ui-state', 'assignments', { error: '' });
  } else {
    clearStepMessages();
  }
  try {
    const payload = buildScopePayload(true);
    const requestKey = JSON.stringify(payload);
    let inFlight = candidateRequestInFlight.get(requestKey);
    if (!inFlight) {
      inFlight = listAssignmentStepCandidates(props.tenantId, props.accessToken, payload).finally(() => {
        candidateRequestInFlight.delete(requestKey);
      });
      candidateRequestInFlight.set(requestKey, inFlight);
    }
    const result = await inFlight;
    if (requestId !== candidateReloadSequence.value) {
      return;
    }
    candidates.value = result.candidates;
  } catch {
    if (requestId !== candidateReloadSequence.value) {
      return;
    }
    loadError.value = $t('sicherplan.customerPlansWizard.errors.assignmentsCandidatesFailed');
    emit('step-ui-state', 'assignments', { error: 'load_failed' });
  } finally {
    if (requestId === candidateReloadSequence.value) {
      snapshotLoading.value = false;
      endLoad();
    }
  }
}

function findCandidateByActorId(actorId: string) {
  return candidates.value.find((row) => row.actor_id === actorId) ?? null;
}

function buildAssignmentPayload(candidate: AssignmentStepCandidateRead): AssignmentStepApplyRequest | null {
  if (!currentDemandGroupMatch.value) {
    setStepError('missing_demand_group', $t('sicherplan.customerPlansWizard.errors.assignmentsMissingDemandGroup'));
    return null;
  }
  if (!editableTargetShiftIds.value.length) {
    setStepError('no_targets', $t('sicherplan.customerPlansWizard.errors.assignmentsNoEligibleDays'));
    return null;
  }
  return {
    assignment_source_code: 'dispatcher',
    demand_group_match: currentDemandGroupMatch.value,
    employee_id: candidate.actor_kind === 'employee' ? candidate.actor_id : null,
    remarks: null,
    shift_plan_id: props.wizardState.shift_plan_id,
    shift_series_id: props.wizardState.series_id || null,
    stop_on_first_rejection: false,
    subcontractor_worker_id: candidate.actor_kind === 'subcontractor_worker' ? candidate.actor_id : null,
    target_shift_ids: editableTargetShiftIds.value,
    team_id: filters.team_id || null,
    tenant_id: props.tenantId,
  };
}

async function applyForCandidate(candidate: AssignmentStepCandidateRead) {
  const payload = buildAssignmentPayload(candidate);
  if (!payload || assignmentRunning.value || !assignmentStepEditable.value) {
    return;
  }
  assignmentRunning.value = true;
  beginLoad();
  clearStepMessages();
  selectedCandidateId.value = candidate.actor_id;
  try {
    const preview = await previewAssignmentStepApply(props.tenantId, props.accessToken, payload);
    if (preview.accepted_count <= 0) {
      setStepError(
        'preview_rejected',
        $t('sicherplan.customerPlansWizard.errors.assignmentsPreviewRejected', {
          rejected: preview.rejected_count,
        } as never),
      );
      summaryMessage.value = $t('sicherplan.customerPlansWizard.messages.assignmentsPreviewSummary', {
        accepted: preview.accepted_count,
        rejected: preview.rejected_count,
      } as never);
      return;
    }
    const result = await applyAssignmentStep(props.tenantId, props.accessToken, payload);
    await loadSnapshot({ preserveSummaryMessage: true });
    summaryMessage.value = $t('sicherplan.customerPlansWizard.messages.assignmentsAppliedSummary', {
      accepted: result.accepted_count,
      rejected: result.rejected_count,
      requested: result.requested_count,
    } as never);
    await nextTick();
  } catch {
    setStepError('apply_failed', $t('sicherplan.customerPlansWizard.errors.assignmentsApplyFailed'));
  } finally {
    assignmentRunning.value = false;
    endLoad();
  }
}

function handleDemandGroupSelection(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  selectedDemandGroupSignature.value = value;
  selectedCandidateId.value = '';
  void reloadCandidates();
}

function handleMonthSelection(value: string) {
  activeMonth.value = value;
  void loadSnapshot({ preserveSummaryMessage: true });
}

function moveMonth(direction: -1 | 1) {
  const nextIndex = monthIndex.value + direction;
  const nextMonth = activeMonths.value[nextIndex];
  if (!nextMonth) {
    return;
  }
  activeMonth.value = nextMonth;
}

function selectCandidate(candidate: AssignmentStepCandidateRead) {
  selectedCandidateId.value = candidate.actor_id;
  inlineError.value = '';
}

function handleCandidateDragStart(candidate: AssignmentStepCandidateRead) {
  dragCandidateId.value = candidate.actor_id;
  selectedCandidateId.value = candidate.actor_id;
}

function handleCandidateDragEnd() {
  dragCandidateId.value = '';
  calendarDropActive.value = false;
}

function handleCalendarDrop() {
  calendarDropActive.value = false;
  const candidate = findCandidateByActorId(dragCandidateId.value || selectedCandidateId.value);
  if (!candidate) {
    return;
  }
  void applyForCandidate(candidate);
}

function handleCalendarDragOver() {
  if (!dragCandidateId.value || !assignmentStepEditable.value) {
    return;
  }
  calendarDropActive.value = true;
}

function handleCalendarDragLeave() {
  calendarDropActive.value = false;
}

function resolveCandidateInitials(candidate: AssignmentStepCandidateRead) {
  return [candidate.first_name, candidate.last_name]
    .filter(Boolean)
    .map((value) => value[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2);
}

function resolveDayTitle(day: CalendarDayCell) {
  if (!day.active) {
    return $t('sicherplan.customerPlansWizard.assignments.outsideProjectRange');
  }
  const candidateStatus = candidateStatusByDate.value.get(day.dateKey);
  if (candidateStatus) {
    const details = [
      ...candidateStatus.warnings,
      ...candidateStatus.reasons,
    ];
    return details.length ? details.join(', ') : '';
  }
  return '';
}

function resolveDayAggregate(dayKey: string) {
  return cellAggregateByDate.value.get(dayKey) ?? null;
}

function resolveDayState(dayKey: string) {
  const cellAggregate = resolveDayAggregate(dayKey);
  if (cellAggregate) {
    return cellAggregate.state;
  }
  return daySummaryByDate.value.get(dayKey)?.overall_state ?? 'setup_required';
}

function resolveCandidateDayState(dayKey: string) {
  const candidateStatus = candidateStatusByDate.value.get(dayKey);
  if (!candidateStatus) {
    return '';
  }
  if (candidateStatus.eligible) {
    return candidateStatus.warning ? 'warn' : 'eligible';
  }
  return 'blocked';
}

async function submitCurrentStep(): Promise<CustomerNewPlanStepSubmitResult> {
  if (!props.wizardState.shift_plan_id) {
    setStepError('missing_shift_plan', $t('sicherplan.customerPlansWizard.errors.assignmentsMissingShiftPlan'));
    return false;
  }
  if (hasPersistedAssignments.value) {
    emit('step-completion', 'assignments', true);
    emit('step-ui-state', 'assignments', { dirty: false, error: '' });
    return {
      completedStepId: 'assignments',
      dirty: false,
      error: '',
      success: true,
    };
  }
  setStepError('missing_assignments', $t('sicherplan.customerPlansWizard.errors.assignmentsRequired'));
  return false;
}

function scheduleSearchCandidateReload() {
  if (searchReloadTimer) {
    clearTimeout(searchReloadTimer);
  }
  searchReloadTimer = setTimeout(() => {
    searchReloadTimer = null;
    void reloadCandidates({ preserveSummaryMessage: true });
  }, 250);
}

function handleSearchCommit() {
  if (searchReloadTimer) {
    clearTimeout(searchReloadTimer);
    searchReloadTimer = null;
  }
  void reloadCandidates({ preserveSummaryMessage: true });
}

watch(
  () => [
    props.tenantId,
    props.accessToken,
    props.wizardState.shift_plan_id,
    props.wizardState.series_id,
  ].join('|'),
  async () => {
    selectedCandidateId.value = '';
    selectedDemandGroupSignature.value = '';
    activeMonth.value = '';
    await Promise.all([
      loadReferenceData(),
      loadSnapshot(),
    ]);
  },
  { immediate: true },
);

watch(
  () => filters.search,
  () => {
    if (!currentDemandGroupMatch.value) {
      return;
    }
    scheduleSearchCandidateReload();
  },
);

onBeforeUnmount(() => {
  if (searchReloadTimer) {
    clearTimeout(searchReloadTimer);
    searchReloadTimer = null;
  }
});

defineExpose({
  submitCurrentStep,
});
</script>

<template>
  <section
    class="sp-customer-plan-wizard-step__panel sp-customer-plan-assignments"
    data-testid="customer-new-plan-step-panel-assignments"
  >
    <LocalLoadingIndicator
      v-if="snapshotBusy"
      :label="$t('sicherplan.customerPlansWizard.loading.savedData')"
      test-id="customer-new-plan-assignments-loading"
    />
    <p v-if="loadError" class="field-help" data-testid="customer-new-plan-assignments-load-error">{{ loadError }}</p>

    <div
      v-if="snapshot"
      class="sp-customer-plan-assignments__summary"
      data-testid="customer-new-plan-assignments-summary"
    >
      <div class="sp-customer-plan-assignments__summary-block">
        <strong>{{ snapshot.order.order_no }}</strong>
        <span>{{ snapshot.order.planning_record_name }}</span>
      </div>
      <div class="sp-customer-plan-assignments__summary-block">
        <strong>{{ snapshot.shift_plan.shift_plan_name }}</strong>
        <span>{{ snapshot.shift_plan.project_start }} - {{ snapshot.shift_plan.project_end }}</span>
      </div>
      <div class="sp-customer-plan-assignments__summary-cards">
        <article class="sp-customer-plan-assignments__metric">
          <strong>{{ summaryRibbon.total }}</strong>
          <span>{{ $t('sicherplan.customerPlansWizard.assignments.summaryTotal') }}</span>
        </article>
        <article class="sp-customer-plan-assignments__metric" data-tone="good">
          <strong>{{ summaryRibbon.covered }}</strong>
          <span>{{ $t('sicherplan.customerPlansWizard.assignments.summaryCovered') }}</span>
        </article>
        <article class="sp-customer-plan-assignments__metric" data-tone="warn">
          <strong>{{ summaryRibbon.warning }}</strong>
          <span>{{ $t('sicherplan.customerPlansWizard.assignments.summaryWarning') }}</span>
        </article>
        <article class="sp-customer-plan-assignments__metric" data-tone="bad">
          <strong>{{ summaryRibbon.blocked }}</strong>
          <span>{{ $t('sicherplan.customerPlansWizard.assignments.summaryBlocked') }}</span>
        </article>
      </div>
    </div>

    <div
      v-if="snapshot && !assignmentStepEditable"
      class="sp-customer-plan-assignments__banner sp-customer-plan-assignments__banner--warn"
      data-testid="customer-new-plan-assignments-locked"
    >
      <strong>{{ $t('sicherplan.customerPlansWizard.assignments.lockedTitle') }}</strong>
      <span>{{ snapshot.lock_reason_codes.join(', ') || $t('sicherplan.customerPlansWizard.assignments.lockedBody') }}</span>
    </div>

    <div
      v-if="summaryMessage"
      class="sp-customer-plan-assignments__banner"
      data-testid="customer-new-plan-assignments-message"
    >
      {{ summaryMessage }}
    </div>
    <div
      v-if="inlineError"
      class="sp-customer-plan-assignments__banner sp-customer-plan-assignments__banner--error"
      data-testid="customer-new-plan-assignments-error"
    >
      {{ inlineError }}
    </div>

    <div
      v-if="snapshot"
      class="sp-customer-plan-assignments__filters"
      data-testid="customer-new-plan-assignments-filters"
    >
      <label class="field-stack sp-customer-plan-assignments__control sp-customer-plan-assignments__control--demand-group">
        <span class="sp-customer-plan-assignments__control-label">{{ $t('sicherplan.customerPlansWizard.assignments.demandGroup') }}</span>
        <select
          :id="controlIds.demandGroup"
          :value="selectedDemandGroupSignature"
          data-testid="customer-new-plan-assignments-demand-group"
          @change="handleDemandGroupSelection"
        >
          <option
            v-for="option in demandGroupOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </label>
      <label
        v-if="snapshot.shift_plan.workforce_scope_code === 'mixed'"
        class="field-stack sp-customer-plan-assignments__control sp-customer-plan-assignments__control--actor-kind"
      >
        <span class="sp-customer-plan-assignments__control-label">{{ $t('sicherplan.customerPlansWizard.assignments.actorKind') }}</span>
        <select
          :id="controlIds.actorKind"
          v-model="filters.actor_kind"
          data-testid="customer-new-plan-assignments-actor-kind"
          @change="reloadCandidates"
        >
          <option value="">{{ $t('sicherplan.customerPlansWizard.assignments.actorAll') }}</option>
          <option value="employee">{{ $t('sicherplan.customerPlansWizard.assignments.actorEmployee') }}</option>
          <option value="subcontractor_worker">{{ $t('sicherplan.customerPlansWizard.assignments.actorSubcontractor') }}</option>
        </select>
      </label>
      <label class="field-stack sp-customer-plan-assignments__control sp-customer-plan-assignments__control--team">
        <span class="sp-customer-plan-assignments__control-label">{{ $t('sicherplan.customerPlansWizard.assignments.teamFilter') }}</span>
        <select
          :id="controlIds.team"
          v-model="filters.team_id"
          data-testid="customer-new-plan-assignments-team"
          @change="reloadCandidates"
        >
          <option value="">{{ $t('sicherplan.customerPlansWizard.assignments.teamAll') }}</option>
          <option v-for="team in teamRows" :key="team.id" :value="team.id">{{ team.name }}</option>
        </select>
      </label>
      <label class="field-stack sp-customer-plan-assignments__control sp-customer-plan-assignments__control--employee-group">
        <span class="sp-customer-plan-assignments__control-label">{{ $t('sicherplan.customerPlansWizard.assignments.employeeGroupFilter') }}</span>
        <select
          :id="controlIds.employeeGroup"
          v-model="filters.employee_group_id"
          data-testid="customer-new-plan-assignments-group"
          @change="reloadCandidates"
        >
          <option value="">{{ $t('sicherplan.customerPlansWizard.assignments.employeeGroupAll') }}</option>
          <option v-for="group in employeeGroupRows" :key="group.id" :value="group.id">{{ group.name }}</option>
        </select>
      </label>
      <label class="field-stack sp-customer-plan-assignments__control sp-customer-plan-assignments__control--search">
        <span class="sp-customer-plan-assignments__control-label">{{ $t('sicherplan.customerPlansWizard.assignments.search') }}</span>
        <input
          :id="controlIds.search"
          v-model="filters.search"
          class="sp-customer-plan-assignments__search-input"
          data-testid="customer-new-plan-assignments-search"
          type="search"
          @keydown.enter.prevent="handleSearchCommit"
        />
      </label>
      <div class="sp-customer-plan-assignments__control sp-customer-plan-assignments__control--toggle">
        <label class="planning-admin-checkbox planning-admin-checkbox--centered sp-customer-plan-assignments__checkbox">
          <input
            :id="controlIds.unfilledOnly"
            v-model="filters.unfilled_only"
            data-testid="customer-new-plan-assignments-unfilled-only"
            type="checkbox"
            @change="reloadCandidates"
          />
          <span>{{ $t('sicherplan.customerPlansWizard.assignments.unfilledOnly') }}</span>
        </label>
      </div>
    </div>

    <div
      v-if="snapshot"
      class="sp-customer-plan-assignments__workspace"
      data-testid="customer-new-plan-assignments-workspace"
    >
      <aside class="sp-customer-plan-assignments__rail" data-testid="customer-new-plan-assignments-candidate-rail">
        <header class="sp-customer-plan-assignments__rail-header">
          <div>
            <strong>{{ $t('sicherplan.customerPlansWizard.assignments.candidatesTitle') }}</strong>
            <p class="field-help">
              {{
                $t('sicherplan.customerPlansWizard.assignments.candidatesSummary', {
                  count: candidates.length,
                } as never)
              }}
            </p>
          </div>
        </header>
        <div v-if="noGeneratedShifts" class="sp-customer-plan-assignments__empty" data-testid="customer-new-plan-assignments-no-shifts">
          <strong>{{ $t('sicherplan.customerPlansWizard.assignments.emptyNoShiftsTitle') }}</strong>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.assignments.emptyNoShiftsBody') }}</p>
        </div>
        <div v-else-if="demandGroupEmpty" class="sp-customer-plan-assignments__empty" data-testid="customer-new-plan-assignments-no-demand-groups">
          <strong>{{ $t('sicherplan.customerPlansWizard.assignments.emptyNoDemandGroupsTitle') }}</strong>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.assignments.emptyNoDemandGroupsBody') }}</p>
        </div>
        <div v-else-if="noCandidates" class="sp-customer-plan-assignments__empty" data-testid="customer-new-plan-assignments-no-candidates">
          <strong>{{ $t('sicherplan.customerPlansWizard.assignments.emptyNoCandidatesTitle') }}</strong>
          <p class="field-help">{{ $t('sicherplan.customerPlansWizard.assignments.emptyNoCandidatesBody') }}</p>
        </div>
        <div v-else class="sp-customer-plan-assignments__candidate-list">
          <article
            v-for="candidate in candidates"
            :key="candidate.actor_id"
            :class="[
              'sp-customer-plan-assignments__candidate',
              { 'sp-customer-plan-assignments__candidate--selected': selectedCandidateId === candidate.actor_id },
            ]"
            :data-testid="`customer-new-plan-assignments-candidate-${candidate.actor_id}`"
            draggable="true"
            @click="selectCandidate(candidate)"
            @dragend="handleCandidateDragEnd"
            @dragstart="handleCandidateDragStart(candidate)"
          >
            <div class="sp-customer-plan-assignments__candidate-avatar">{{ resolveCandidateInitials(candidate) }}</div>
            <div class="sp-customer-plan-assignments__candidate-body">
              <header class="sp-customer-plan-assignments__candidate-header">
                <strong>{{ candidate.display_name }}</strong>
                <span class="sp-customer-plan-assignments__candidate-score">{{ candidate.suitability_score }}</span>
              </header>
              <p class="field-help">{{ candidate.personnel_ref }}</p>
              <div class="sp-customer-plan-assignments__candidate-tags">
                <span class="sp-customer-plan-assignments__tag">{{ resolveActorKindLabel(candidate.actor_kind) }}</span>
                <span v-if="resolveTeamLabels(candidate)[0]" class="sp-customer-plan-assignments__tag">
                  {{ resolveTeamLabels(candidate)[0] }}
                </span>
                <span v-if="resolveEmployeeGroupLabels(candidate)[0]" class="sp-customer-plan-assignments__tag">
                  {{ resolveEmployeeGroupLabels(candidate)[0] }}
                </span>
              </div>
              <div class="sp-customer-plan-assignments__candidate-stats">
                <span>{{ $t('sicherplan.customerPlansWizard.assignments.eligibleDays', { count: candidate.eligible_day_count } as never) }}</span>
                <span>{{ $t('sicherplan.customerPlansWizard.assignments.blockedDays', { count: candidate.blocked_day_count } as never) }}</span>
              </div>
              <button
                type="button"
                class="cta-button cta-secondary"
                :disabled="assignmentRunning || !assignmentStepEditable"
                :data-testid="`customer-new-plan-assignments-assign-${candidate.actor_id}`"
                @click.stop="applyForCandidate(candidate)"
              >
                {{ $t('sicherplan.customerPlansWizard.assignments.assignAction') }}
              </button>
            </div>
          </article>
        </div>
      </aside>

      <section
        :class="[
          'sp-customer-plan-assignments__calendar',
          { 'sp-customer-plan-assignments__calendar--droppable': calendarDropActive },
        ]"
        data-testid="customer-new-plan-assignments-calendar"
        @dragenter.prevent="handleCalendarDragOver"
        @dragleave.prevent="handleCalendarDragLeave"
        @dragover.prevent="handleCalendarDragOver"
        @drop.prevent="handleCalendarDrop"
      >
        <header class="sp-customer-plan-assignments__calendar-header">
          <div>
            <strong>{{ $t('sicherplan.customerPlansWizard.assignments.calendarTitle') }}</strong>
            <p class="field-help">{{ $t('sicherplan.customerPlansWizard.assignments.calendarHelp') }}</p>
          </div>
          <div class="sp-customer-plan-assignments__calendar-toolbar">
            <button
              type="button"
              class="cta-button cta-secondary"
              data-testid="customer-new-plan-assignments-month-prev"
              :disabled="!hasPreviousMonth"
              @click="moveMonth(-1)"
            >
              {{ $t('sicherplan.customerPlansWizard.assignments.previousMonth') }}
            </button>
            <select
              :value="currentMonthValue"
              data-testid="customer-new-plan-assignments-month"
              @change="handleMonthSelection(($event.target as HTMLSelectElement).value)"
            >
              <option v-for="month in activeMonths" :key="month" :value="month">{{ month }}</option>
            </select>
            <button
              type="button"
              class="cta-button cta-secondary"
              data-testid="customer-new-plan-assignments-month-next"
              :disabled="!hasNextMonth"
              @click="moveMonth(1)"
            >
              {{ $t('sicherplan.customerPlansWizard.assignments.nextMonth') }}
            </button>
          </div>
        </header>

        <div class="sp-customer-plan-assignments__legend">
          <span class="sp-customer-plan-assignments__legend-chip sp-customer-plan-assignments__legend-chip--green">
            {{ $t('sicherplan.customerPlansWizard.assignments.legendCovered') }}
          </span>
          <span class="sp-customer-plan-assignments__legend-chip sp-customer-plan-assignments__legend-chip--yellow">
            {{ $t('sicherplan.customerPlansWizard.assignments.legendWarning') }}
          </span>
          <span class="sp-customer-plan-assignments__legend-chip sp-customer-plan-assignments__legend-chip--red">
            {{ $t('sicherplan.customerPlansWizard.assignments.legendBlocked') }}
          </span>
        </div>

        <div class="sp-customer-plan-assignments__weekday-row">
          <span v-for="weekday in ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']" :key="weekday">{{ weekday }}</span>
        </div>
        <div class="sp-customer-plan-assignments__calendar-grid">
          <article
            v-for="day in calendarDays"
            :key="day.dateKey"
            :class="[
              'sp-customer-plan-assignments__day',
              `sp-customer-plan-assignments__day--${resolveCoverageTone(resolveDayState(day.dateKey))}`,
              {
                'sp-customer-plan-assignments__day--inactive': !day.active,
                'sp-customer-plan-assignments__day--outside': !day.inCurrentMonth,
                'sp-customer-plan-assignments__day--candidate-eligible': resolveCandidateDayState(day.dateKey) === 'eligible',
                'sp-customer-plan-assignments__day--candidate-warn': resolveCandidateDayState(day.dateKey) === 'warn',
                'sp-customer-plan-assignments__day--candidate-blocked': resolveCandidateDayState(day.dateKey) === 'blocked',
              },
            ]"
            :data-testid="`customer-new-plan-assignments-day-${day.dateKey}`"
            :title="resolveDayTitle(day)"
          >
            <header class="sp-customer-plan-assignments__day-header">
              <strong>{{ day.date.getUTCDate() }}</strong>
              <span v-if="resolveDayAggregate(day.dateKey)?.openCount">
                {{ resolveDayAggregate(day.dateKey)?.openCount }}
              </span>
            </header>
            <div class="sp-customer-plan-assignments__day-body">
              <span v-if="resolveDayAggregate(day.dateKey)">
                {{ resolveDayAggregate(day.dateKey)?.assignedCount }}/{{ resolveDayAggregate(day.dateKey)?.targetCount }}
              </span>
              <span v-else-if="daySummaryByDate.get(day.dateKey)">
                {{ daySummaryByDate.get(day.dateKey)?.total_shifts }}
              </span>
              <span
                v-if="resolveCandidateDayState(day.dateKey) === 'blocked'"
                class="sp-customer-plan-assignments__day-indicator sp-customer-plan-assignments__day-indicator--blocked"
              >
                {{ $t('sicherplan.customerPlansWizard.assignments.dayBlocked') }}
              </span>
              <span
                v-else-if="resolveCandidateDayState(day.dateKey) === 'warn'"
                class="sp-customer-plan-assignments__day-indicator sp-customer-plan-assignments__day-indicator--warn"
              >
                {{ $t('sicherplan.customerPlansWizard.assignments.dayWarn') }}
              </span>
              <span
                v-else-if="resolveCandidateDayState(day.dateKey) === 'eligible'"
                class="sp-customer-plan-assignments__day-indicator sp-customer-plan-assignments__day-indicator--eligible"
              >
                {{ $t('sicherplan.customerPlansWizard.assignments.dayEligible') }}
              </span>
            </div>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.sp-customer-plan-assignments {
  display: grid;
  gap: 1rem;
}

.sp-customer-plan-assignments__summary,
.sp-customer-plan-assignments__filters,
.sp-customer-plan-assignments__workspace,
.sp-customer-plan-assignments__banner {
  border: 1px solid var(--vp-c-divider, #d7deea);
  border-radius: 8px;
  background: var(--vp-c-bg-soft, #fff);
}

.sp-customer-plan-assignments__summary,
.sp-customer-plan-assignments__filters,
.sp-customer-plan-assignments__banner {
  padding: 0.875rem 1rem;
}

.sp-customer-plan-assignments__summary {
  display: grid;
  gap: 0.875rem;
  grid-template-columns: repeat(2, minmax(0, 1fr)) minmax(16rem, 1.2fr);
}

.sp-customer-plan-assignments__summary-block,
.sp-customer-plan-assignments__metric {
  display: grid;
  gap: 0.25rem;
}

.sp-customer-plan-assignments__summary-cards {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.sp-customer-plan-assignments__metric {
  border-radius: 8px;
  padding: 0.75rem;
  background: #f6f8fb;
}

.sp-customer-plan-assignments__metric[data-tone='good'] {
  background: rgba(46, 160, 67, 0.12);
}

.sp-customer-plan-assignments__metric[data-tone='warn'] {
  background: rgba(251, 188, 5, 0.16);
}

.sp-customer-plan-assignments__metric[data-tone='bad'] {
  background: rgba(217, 48, 37, 0.12);
}

.sp-customer-plan-assignments__banner {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.sp-customer-plan-assignments__banner--warn {
  border-color: rgba(251, 188, 5, 0.4);
  background: rgba(251, 188, 5, 0.1);
}

.sp-customer-plan-assignments__banner--error {
  border-color: rgba(217, 48, 37, 0.4);
  background: rgba(217, 48, 37, 0.08);
}

.sp-customer-plan-assignments__filters {
  display: grid;
  gap: 0.875rem 0.75rem;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  align-items: stretch;
}

.sp-customer-plan-assignments__control {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}

.sp-customer-plan-assignments__control-label {
  color: #516074;
  font-size: 0.8125rem;
  font-weight: 600;
}

.sp-customer-plan-assignments__control--demand-group {
  grid-column: span 3;
}

.sp-customer-plan-assignments__control--actor-kind,
.sp-customer-plan-assignments__control--team,
.sp-customer-plan-assignments__control--employee-group {
  grid-column: span 2;
}

.sp-customer-plan-assignments__control--search {
  grid-column: span 2;
}

.sp-customer-plan-assignments__control--toggle {
  grid-column: span 1;
  align-content: end;
}

.sp-customer-plan-assignments__search-input {
  width: 100%;
}

.sp-customer-plan-assignments__checkbox {
  min-height: 2.5rem;
  height: 100%;
  padding: 0.55rem 0.75rem;
  border: 1px solid #d7deea;
  border-radius: 8px;
  background: #f8fafc;
}

.sp-customer-plan-assignments__workspace {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(18rem, 20rem) minmax(0, 1fr);
  padding: 1rem;
  min-height: 42rem;
}

.sp-customer-plan-assignments__rail,
.sp-customer-plan-assignments__calendar {
  display: grid;
  gap: 0.875rem;
  min-height: 0;
}

.sp-customer-plan-assignments__rail {
  grid-template-rows: auto 1fr;
}

.sp-customer-plan-assignments__candidate-list {
  display: grid;
  gap: 0.75rem;
  overflow: auto;
  padding-right: 0.25rem;
}

.sp-customer-plan-assignments__candidate {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: auto minmax(0, 1fr);
  padding: 0.875rem;
  border: 1px solid #d7deea;
  border-radius: 8px;
  background: #f8fafc;
  cursor: pointer;
}

.sp-customer-plan-assignments__candidate--selected {
  border-color: rgb(40, 170, 170);
  box-shadow: 0 0 0 1px rgba(40, 170, 170, 0.12);
}

.sp-customer-plan-assignments__candidate-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(40, 170, 170, 0.14);
  color: rgb(26, 102, 102);
  font-weight: 700;
}

.sp-customer-plan-assignments__candidate-body,
.sp-customer-plan-assignments__candidate-header,
.sp-customer-plan-assignments__candidate-stats,
.sp-customer-plan-assignments__candidate-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.sp-customer-plan-assignments__candidate-body {
  flex-direction: column;
}

.sp-customer-plan-assignments__candidate-header {
  justify-content: space-between;
  align-items: center;
}

.sp-customer-plan-assignments__candidate-score {
  font-size: 0.8125rem;
  color: #516074;
}

.sp-customer-plan-assignments__tag {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.45rem;
  border-radius: 999px;
  background: #edf2f7;
  font-size: 0.75rem;
}

.sp-customer-plan-assignments__calendar {
  grid-template-rows: auto auto auto 1fr;
}

.sp-customer-plan-assignments__calendar--droppable {
  box-shadow: 0 0 0 2px rgba(40, 170, 170, 0.18);
}

.sp-customer-plan-assignments__calendar-header,
.sp-customer-plan-assignments__calendar-toolbar,
.sp-customer-plan-assignments__legend,
.sp-customer-plan-assignments__weekday-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
}

.sp-customer-plan-assignments__legend {
  justify-content: flex-start;
}

.sp-customer-plan-assignments__legend-chip,
.sp-customer-plan-assignments__day-indicator {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.15rem 0.45rem;
  font-size: 0.75rem;
}

.sp-customer-plan-assignments__legend-chip--green,
.sp-customer-plan-assignments__day--good {
  background: rgba(46, 160, 67, 0.12);
}

.sp-customer-plan-assignments__legend-chip--yellow,
.sp-customer-plan-assignments__day--warn {
  background: rgba(251, 188, 5, 0.16);
}

.sp-customer-plan-assignments__legend-chip--red,
.sp-customer-plan-assignments__day--bad {
  background: rgba(217, 48, 37, 0.12);
}

.sp-customer-plan-assignments__weekday-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  color: #516074;
  font-size: 0.8125rem;
}

.sp-customer-plan-assignments__calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.65rem;
}

.sp-customer-plan-assignments__day {
  display: grid;
  gap: 0.5rem;
  align-content: start;
  min-height: 7rem;
  padding: 0.65rem;
  border-radius: 8px;
  border: 1px solid transparent;
}

.sp-customer-plan-assignments__day--inactive {
  opacity: 0.45;
}

.sp-customer-plan-assignments__day--outside {
  background: #f2f5f9;
}

.sp-customer-plan-assignments__day--candidate-eligible {
  border-color: rgba(46, 160, 67, 0.45);
}

.sp-customer-plan-assignments__day--candidate-warn {
  border-color: rgba(251, 188, 5, 0.6);
}

.sp-customer-plan-assignments__day--candidate-blocked {
  border-color: rgba(217, 48, 37, 0.55);
}

.sp-customer-plan-assignments__day-header {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
}

.sp-customer-plan-assignments__day-body {
  display: grid;
  gap: 0.35rem;
  font-size: 0.8125rem;
}

.sp-customer-plan-assignments__day-indicator--eligible {
  background: rgba(46, 160, 67, 0.14);
}

.sp-customer-plan-assignments__day-indicator--warn {
  background: rgba(251, 188, 5, 0.2);
}

.sp-customer-plan-assignments__day-indicator--blocked {
  background: rgba(217, 48, 37, 0.14);
}

.sp-customer-plan-assignments__empty {
  display: grid;
  gap: 0.35rem;
  border: 1px dashed #d7deea;
  border-radius: 8px;
  padding: 1rem;
  background: #f9fbfd;
}

@media (max-width: 1200px) {
  .sp-customer-plan-assignments__summary,
  .sp-customer-plan-assignments__workspace {
    grid-template-columns: 1fr;
  }

  .sp-customer-plan-assignments__summary-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sp-customer-plan-assignments__filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sp-customer-plan-assignments__control,
  .sp-customer-plan-assignments__control--demand-group,
  .sp-customer-plan-assignments__control--actor-kind,
  .sp-customer-plan-assignments__control--team,
  .sp-customer-plan-assignments__control--employee-group,
  .sp-customer-plan-assignments__control--search,
  .sp-customer-plan-assignments__control--toggle {
    grid-column: auto;
  }
}

@media (max-width: 720px) {
  .sp-customer-plan-assignments__filters,
  .sp-customer-plan-assignments__summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>
