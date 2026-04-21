<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter, type LocationQueryRaw } from 'vue-router';

import { $t } from '#/locales';
import EmptyState from '#/components/sicherplan/empty-state.vue';
import ModuleWorkspacePage from '#/components/sicherplan/module-workspace-page.vue';
import SectionBlock from '#/components/sicherplan/section-block.vue';
import ForbiddenView from '#/views/_core/fallback/forbidden.vue';
import { CustomerAdminApiError, getCustomer, type CustomerRead } from '#/sicherplan-legacy/api/customers';
import { useAuthStore } from '#/sicherplan-legacy/stores/auth';
import CustomerNewPlanStepContent from './new-plan-step-content.vue';
import { clearAllWizardDraftsForCurrentContext } from './new-plan-wizard-drafts';
import {
  CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID,
  CUSTOMER_NEW_PLAN_WIZARD_LAST_STEP_ID,
  isWizardStepId,
  normalizeWizardStepId,
} from './new-plan-wizard.steps';
import type {
  CustomerNewPlanStepSubmitResult,
  CustomerNewPlanWizardStepId,
} from './new-plan-wizard.types';
import { useCustomerNewPlanWizard } from './use-customer-new-plan-wizard';

type WizardContextState = 'loading' | 'ready' | 'missing' | 'not_found' | 'error';
type PersistedWizardRouteKey =
  | 'customer_id'
  | 'order_id'
  | 'planning_id'
  | 'planning_entity_id'
  | 'planning_entity_type'
  | 'planning_mode_code'
  | 'planning_record_id'
  | 'series_id'
  | 'shift_plan_id'
  | 'step';

const PERSISTED_WIZARD_ROUTE_KEYS: PersistedWizardRouteKey[] = [
  'customer_id',
  'step',
  'planning_entity_type',
  'planning_entity_id',
  'planning_mode_code',
  'order_id',
  'planning_record_id',
  'shift_plan_id',
  'series_id',
];
const PLANNING_ENTITY_TYPES = new Set(['event_venue', 'patrol_route', 'site', 'trade_fair']);
const PLANNING_MODE_CODES = new Set(['event', 'patrol', 'site', 'trade_fair']);

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const {
  state: wizardState,
  steps: wizardStepDefinitions,
  canEnterStep,
  canMoveNext,
  canMovePrevious,
  moveNext,
  movePrevious,
  resetForCustomer,
  resetWizard,
  setSavedContext,
  setCurrentStep,
  setStepCompletion,
  setStepUiState,
  applyRequestedStep,
} = useCustomerNewPlanWizard();

const customer = ref<CustomerRead | null>(null);
const contextState = ref<WizardContextState>('loading');
const bootstrapped = ref(false);
const stepContentRef = ref<InstanceType<typeof CustomerNewPlanStepContent> | null>(null);
const stepSubmitting = ref(false);
const routeRestoreWarning = ref('');
const persistDraftsOnUnmount = ref(true);
const activeInternalTransitionSeq = ref<number | null>(null);
const pendingInternalRouteSignature = ref('');
const lastCommittedInternalRouteSignature = ref('');
let resolveCustomerContextSequence = 0;
let routeTransitionSeq = 0;

const customerId = computed(() => {
  const raw = route.query.customer_id;
  if (Array.isArray(raw)) {
    return raw[0]?.trim() ?? '';
  }
  return typeof raw === 'string' ? raw.trim() : '';
});
const requestedStepId = computed(() => {
  const raw = route.query.step;
  const candidate = Array.isArray(raw) ? raw[0] : raw;
  if (candidate === 'planning') {
    return CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID;
  }
  return normalizeWizardStepId(candidate);
});

const isAuthorized = computed(() => authStore.effectiveRole === 'tenant_admin');
const tenantScopeId = computed(() => authStore.effectiveTenantScopeId);
const accessToken = computed(() => authStore.effectiveAccessToken || authStore.accessToken);
const hasStableCustomerContext = computed(
  () => contextState.value === 'ready' && customer.value?.id === customerId.value,
);
const isLoading = computed(
  () => contextState.value === 'loading' || (authStore.isSessionResolving && !hasStableCustomerContext.value),
);
const wizardSteps = computed(() =>
  wizardStepDefinitions.value.map((step) => ({
    ...step,
    label: $t(step.labelKey),
  })),
);
const currentStepIndex = computed(
  () => wizardSteps.value.findIndex((step) => step.id === wizardState.value.current_step),
);
const currentStep = computed(
  () => wizardSteps.value[currentStepIndex.value] ?? wizardSteps.value[0],
);
const currentStepLabel = computed(() => currentStep.value?.label ?? '');
const hasUnsavedChanges = computed(() =>
  Object.values(wizardState.value.step_state).some((step) => step.dirty),
);
const handledSubmitStepIds = new Set<CustomerNewPlanWizardStepId>([
  'order-details',
  'order-scope-documents',
  'planning-record-overview',
  'planning-record-documents',
  'shift-plan',
  'series-exceptions',
]);
const isFinalStep = computed(() => wizardState.value.current_step === CUSTOMER_NEW_PLAN_WIZARD_LAST_STEP_ID);
const nextActionLabel = computed(() =>
  isFinalStep.value
    ? $t('sicherplan.customerPlansWizard.actions.generateContinue')
    : $t('sicherplan.customerPlansWizard.actions.next'),
);
const canSubmitCurrentStep = computed(() => handledSubmitStepIds.has(wizardState.value.current_step));

function normalizeQueryString(value: unknown) {
  if (Array.isArray(value)) {
    return typeof value[0] === 'string' ? value[0].trim() : '';
  }
  return typeof value === 'string' ? value.trim() : '';
}

function hasQueryKey(query: typeof route.query, key: PersistedWizardRouteKey) {
  return Object.prototype.hasOwnProperty.call(query, key);
}

function addPatchIfQueryKeyPresent(
  patch: Record<string, string>,
  key: Exclude<PersistedWizardRouteKey, 'step'>,
  value: string,
) {
  if (hasQueryKey(route.query, key)) {
    patch[key] = value;
  }
}

function readWizardRouteState() {
  const planningEntityType = normalizeQueryString(route.query.planning_entity_type);
  const planningModeCode = normalizeQueryString(route.query.planning_mode_code);
  const planningEntityId = normalizeQueryString(route.query.planning_entity_id) || normalizeQueryString(route.query.planning_id);

  return {
    customer_id: customerId.value,
    order_id: normalizeQueryString(route.query.order_id),
    planning_entity_id: planningEntityId,
    planning_entity_type: PLANNING_ENTITY_TYPES.has(planningEntityType) ? planningEntityType : '',
    planning_mode_code: PLANNING_MODE_CODES.has(planningModeCode) ? planningModeCode : '',
    planning_record_id: normalizeQueryString(route.query.planning_record_id),
    series_id: normalizeQueryString(route.query.series_id),
    shift_plan_id: normalizeQueryString(route.query.shift_plan_id),
    step: requestedStepId.value,
  };
}

function buildRouteStateSignature(routeState: ReturnType<typeof readWizardRouteState>) {
  return [
    routeState.customer_id,
    routeState.order_id,
    routeState.planning_entity_id,
    routeState.planning_entity_type,
    routeState.planning_mode_code,
    routeState.planning_record_id,
    routeState.shift_plan_id,
    routeState.series_id,
    routeState.step ?? '',
  ].join('|');
}

function buildWizardStateRouteSignature() {
  return [
    wizardState.value.customer_id,
    wizardState.value.order_id,
    wizardState.value.planning_entity_id,
    wizardState.value.planning_entity_type,
    wizardState.value.planning_mode_code,
    wizardState.value.planning_record_id,
    wizardState.value.shift_plan_id,
    wizardState.value.series_id,
    wizardState.value.current_step,
  ].join('|');
}

function beginInternalWizardTransition() {
  const nextSeq = ++routeTransitionSeq;
  activeInternalTransitionSeq.value = nextSeq;
  pendingInternalRouteSignature.value = '';
  return nextSeq;
}

function endInternalWizardTransition(transitionSeq: number) {
  if (activeInternalTransitionSeq.value !== transitionSeq) {
    return;
  }
  activeInternalTransitionSeq.value = null;
  pendingInternalRouteSignature.value = '';
}

function isInternalTransitionActive() {
  return activeInternalTransitionSeq.value !== null;
}

function isSameUpstreamScope(routeState: ReturnType<typeof readWizardRouteState>) {
  return (
    routeState.customer_id === wizardState.value.customer_id &&
    routeState.order_id === wizardState.value.order_id &&
    routeState.planning_record_id === wizardState.value.planning_record_id
  );
}

function isStaleShiftPlanRollbackRoute(routeState: ReturnType<typeof readWizardRouteState>) {
  return (
    wizardState.value.current_step === 'series-exceptions' &&
    Boolean(wizardState.value.shift_plan_id) &&
    isSameUpstreamScope(routeState) &&
    (routeState.step === 'shift-plan' || !routeState.step) &&
    routeState.shift_plan_id !== wizardState.value.shift_plan_id
  );
}

function syncWizardFromRoute() {
  const routeState = readWizardRouteState();
  const contextPatch: Record<string, string> = {
    customer_id: routeState.customer_id,
  };

  addPatchIfQueryKeyPresent(contextPatch, 'order_id', routeState.order_id);
  if (hasQueryKey(route.query, 'planning_entity_id') || hasQueryKey(route.query, 'planning_id')) {
    contextPatch.planning_entity_id = routeState.planning_entity_id;
  }
  addPatchIfQueryKeyPresent(contextPatch, 'planning_entity_type', routeState.planning_entity_type);
  addPatchIfQueryKeyPresent(contextPatch, 'planning_mode_code', routeState.planning_mode_code);
  addPatchIfQueryKeyPresent(contextPatch, 'planning_record_id', routeState.planning_record_id);
  addPatchIfQueryKeyPresent(contextPatch, 'shift_plan_id', routeState.shift_plan_id);
  addPatchIfQueryKeyPresent(contextPatch, 'series_id', routeState.series_id);

  setSavedContext(contextPatch);

  const resolvedStep = applyRequestedStep(routeState.step);
  routeRestoreWarning.value =
    routeState.step && resolvedStep !== routeState.step
      ? $t('sicherplan.customerPlansWizard.restoreFallback')
      : '';
}

function buildWizardRouteQuery() {
  const keepPlanningContextInRoute = Boolean(
    wizardState.value.current_step !== CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID ||
      wizardState.value.order_id ||
      wizardState.value.planning_record_id ||
      wizardState.value.shift_plan_id ||
      wizardState.value.series_id,
  );
  const nextQuery: LocationQueryRaw = {
    ...route.query,
    customer_id: customerId.value || undefined,
    order_id: wizardState.value.order_id || undefined,
    planning_entity_id: keepPlanningContextInRoute ? wizardState.value.planning_entity_id || undefined : undefined,
    planning_entity_type: keepPlanningContextInRoute ? wizardState.value.planning_entity_type || undefined : undefined,
    planning_mode_code: keepPlanningContextInRoute ? wizardState.value.planning_mode_code || undefined : undefined,
    planning_record_id: wizardState.value.planning_record_id || undefined,
    series_id: wizardState.value.series_id || undefined,
    shift_plan_id: wizardState.value.shift_plan_id || undefined,
  };
  delete nextQuery.planning_id;

  if (wizardState.value.current_step === CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID) {
    delete nextQuery.step;
  } else {
    nextQuery.step = wizardState.value.current_step;
  }

  for (const key of PERSISTED_WIZARD_ROUTE_KEYS) {
    if (!nextQuery[key]) {
      delete nextQuery[key];
    }
  }

  return nextQuery;
}

function confirmDiscardChanges() {
  if (!hasUnsavedChanges.value) {
    return true;
  }
  return window.confirm($t('sicherplan.customerPlansWizard.confirmDiscard'));
}

function clearCurrentWizardDrafts() {
  if (!tenantScopeId.value || !customerId.value) {
    return;
  }
  clearAllWizardDraftsForCurrentContext({
    customerId: customerId.value,
    planningEntityId: wizardState.value.planning_entity_id,
    planningEntityType: wizardState.value.planning_entity_type,
    tenantId: tenantScopeId.value,
  });
}

async function resolveCustomerContext(options?: { preserveContent?: boolean }) {
  const requestSequence = ++resolveCustomerContextSequence;
  const preserveContent = Boolean(options?.preserveContent && hasStableCustomerContext.value);

  if (!isAuthorized.value) {
    contextState.value = 'error';
    customer.value = null;
    return;
  }

  if (!customerId.value) {
    contextState.value = 'missing';
    customer.value = null;
    return;
  }

  if (!tenantScopeId.value || !accessToken.value) {
    if (preserveContent) {
      return;
    }
    contextState.value = 'loading';
    customer.value = null;
    return;
  }

  if (!preserveContent) {
    contextState.value = 'loading';
  }
  try {
    const loadedCustomer = await getCustomer(tenantScopeId.value, customerId.value, accessToken.value);
    if (requestSequence !== resolveCustomerContextSequence) {
      return;
    }
    customer.value = loadedCustomer;
    contextState.value = 'ready';
  } catch (error) {
    if (requestSequence !== resolveCustomerContextSequence) {
      return;
    }
    if (preserveContent) {
      return;
    }
    customer.value = null;
    if (error instanceof CustomerAdminApiError && error.statusCode === 404) {
      contextState.value = 'not_found';
      return;
    }
    contextState.value = 'error';
  }
}

function goBackToPlans() {
  if (!confirmDiscardChanges()) {
    return;
  }
  persistDraftsOnUnmount.value = false;
  clearCurrentWizardDrafts();
  resetWizard();
  void router.push({
    path: '/admin/customers',
    query: customerId.value
      ? {
          customer_id: customerId.value,
          tab: 'plans',
        }
      : undefined,
  });
}

function goBackToCustomers() {
  if (!confirmDiscardChanges()) {
    return;
  }
  persistDraftsOnUnmount.value = false;
  clearCurrentWizardDrafts();
  void router.push('/admin/customers');
}

function goToPreviousStep() {
  if (!canMovePrevious.value) {
    return;
  }
  movePrevious();
}

function normalizeStepSubmitResult(result: CustomerNewPlanStepSubmitResult | undefined) {
  if (typeof result === 'boolean') {
    return {
      success: result,
    };
  }
  return result ?? { success: false };
}

function violatesShiftPlanSubmitInvariant(submitResult: ReturnType<typeof normalizeStepSubmitResult>) {
  if (wizardState.value.current_step !== 'shift-plan' || !submitResult.success) {
    return false;
  }
  const nextShiftPlanId = submitResult.savedContext?.shift_plan_id ?? wizardState.value.shift_plan_id;
  return !nextShiftPlanId;
}

async function goToNextStep() {
  if (stepSubmitting.value) {
    return;
  }
  if (canSubmitCurrentStep.value) {
    stepSubmitting.value = true;
    const transitionSeq = !isFinalStep.value ? beginInternalWizardTransition() : null;
    try {
      const submitResult = normalizeStepSubmitResult(
        await Promise.resolve(stepContentRef.value?.submitCurrentStep?.()),
      );
      if (submitResult.savedContext) {
        setSavedContext(submitResult.savedContext);
      }
      if (submitResult.completedStepId) {
        setStepCompletion(submitResult.completedStepId, submitResult.success);
        setStepUiState(submitResult.completedStepId, {
          ...(submitResult.dirty !== undefined ? { dirty: submitResult.dirty } : {}),
          ...(submitResult.error !== undefined ? { error: submitResult.error } : {}),
        });
      }
      if (violatesShiftPlanSubmitInvariant(submitResult)) {
        setStepCompletion('shift-plan', false);
        setStepUiState('shift-plan', {
          dirty: true,
          error: 'submit_missing_shift_plan_id',
        });
        return;
      }
      if (submitResult.success && !isFinalStep.value) {
        moveNext();
        if (wizardState.value.current_step === 'shift-plan') {
          setStepCompletion('shift-plan', false);
          setStepUiState('shift-plan', {
            dirty: true,
            error: 'transition_failed_after_shift_plan_submit',
          });
          return;
        }
        await syncWizardRouteState({
          force: true,
          source: 'internal-final',
        });
      }
    } finally {
      if (transitionSeq !== null) {
        endInternalWizardTransition(transitionSeq);
      }
      stepSubmitting.value = false;
    }
    return;
  }
  if (!canMoveNext.value) {
    return;
  }
  moveNext();
}

function selectStep(stepId: CustomerNewPlanWizardStepId) {
  setCurrentStep(stepId);
}

async function syncWizardRouteState(options?: { force?: boolean; source?: 'external' | 'internal-final' | 'repair' }) {
  if (!bootstrapped.value || !customerId.value) {
    return;
  }
  if (isInternalTransitionActive() && options?.source !== 'internal-final') {
    return;
  }
  const nextQuery = buildWizardRouteQuery();
  const nextRouteState = {
    customer_id: normalizeQueryString(nextQuery.customer_id),
    order_id: normalizeQueryString(nextQuery.order_id),
    planning_entity_id: normalizeQueryString(nextQuery.planning_entity_id),
    planning_entity_type: normalizeQueryString(nextQuery.planning_entity_type),
    planning_mode_code: normalizeQueryString(nextQuery.planning_mode_code),
    planning_record_id: normalizeQueryString(nextQuery.planning_record_id),
    shift_plan_id: normalizeQueryString(nextQuery.shift_plan_id),
    series_id: normalizeQueryString(nextQuery.series_id),
    step: (() => {
      const raw = nextQuery.step;
      if (Array.isArray(raw)) {
        return typeof raw[0] === 'string' && isWizardStepId(raw[0]) ? raw[0] : null;
      }
      return typeof raw === 'string' && isWizardStepId(raw) ? raw : null;
    })(),
  };
  const nextSignature = buildRouteStateSignature(nextRouteState);
  const queryChanged = PERSISTED_WIZARD_ROUTE_KEYS.some(
    (key) => normalizeQueryString(route.query[key]) !== normalizeQueryString(nextQuery[key]),
  );
  if (!options?.force && !queryChanged) {
    return;
  }
  if (options?.source === 'internal-final') {
    pendingInternalRouteSignature.value = nextSignature;
  }

  await router.replace({
    path: '/admin/customers/new-plan',
    query: nextQuery,
  });
  if (options?.source === 'internal-final') {
    lastCommittedInternalRouteSignature.value = nextSignature;
  }
}

onMounted(async () => {
  authStore.syncFromPrimarySession();
  await authStore.ensureSessionReady();
  bootstrapped.value = true;
  resetForCustomer(customerId.value);
  syncWizardFromRoute();
  await resolveCustomerContext();
  await syncWizardRouteState({ source: 'external' });
});

watch(
  () => [customerId.value, tenantScopeId.value, isAuthorized.value] as const,
  async ([nextCustomerId], [previousCustomerId]) => {
    if (!bootstrapped.value) {
      return;
    }
    if (nextCustomerId !== previousCustomerId) {
      resetForCustomer(nextCustomerId);
      syncWizardFromRoute();
      await syncWizardRouteState({ source: 'external' });
      await resolveCustomerContext();
      return;
    }
    await resolveCustomerContext({ preserveContent: true });
  },
);

watch(
  () => accessToken.value,
  async (nextAccessToken, previousAccessToken) => {
    if (!bootstrapped.value || nextAccessToken === previousAccessToken) {
      return;
    }
    if (!nextAccessToken || !customerId.value || !tenantScopeId.value || !isAuthorized.value) {
      return;
    }
    if (hasStableCustomerContext.value) {
      return;
    }
    await resolveCustomerContext({ preserveContent: true });
  },
);

watch(
  () => [
    route.query.step,
    route.query.planning_entity_type,
    route.query.planning_entity_id,
    route.query.planning_id,
    route.query.planning_mode_code,
    route.query.order_id,
    route.query.planning_record_id,
    route.query.shift_plan_id,
    route.query.series_id,
  ] as const,
  async () => {
    if (!bootstrapped.value) {
      return;
    }
    const routeState = readWizardRouteState();
    const routeSignature = buildRouteStateSignature(routeState);
    if (isInternalTransitionActive()) {
      return;
    }
    if (isStaleShiftPlanRollbackRoute(routeState)) {
      await syncWizardRouteState({ force: true, source: 'repair' });
      return;
    }
    if (
      lastCommittedInternalRouteSignature.value &&
      routeSignature === lastCommittedInternalRouteSignature.value &&
      routeSignature === buildWizardStateRouteSignature()
    ) {
      return;
    }
    syncWizardFromRoute();
    await syncWizardRouteState({ source: 'external' });
  },
);

watch(
  () => [
    wizardState.value.current_step,
    wizardState.value.planning_entity_type,
    wizardState.value.planning_entity_id,
    wizardState.value.planning_mode_code,
    wizardState.value.order_id,
    wizardState.value.planning_record_id,
    wizardState.value.shift_plan_id,
    wizardState.value.series_id,
  ] as const,
  async () => {
    if (!bootstrapped.value) {
      return;
    }
    await syncWizardRouteState({ source: 'external' });
  },
);
</script>

<template>
  <ForbiddenView v-if="!isAuthorized" />

  <ModuleWorkspacePage
    v-else
    :description="$t('sicherplan.customerPlansWizard.description')"
    :eyebrow="$t('sicherplan.admin.customers')"
    :show-intro="false"
    :title="$t('sicherplan.customerPlansWizard.title')"
  >
    <template #workspace>
      <SectionBlock :show-header="false" title="">
        <div class="sp-customer-plan-wizard">
          <nav
            class="sp-customer-plan-wizard__breadcrumb"
            data-testid="customer-new-plan-breadcrumb"
            :aria-label="$t('sicherplan.customerPlansWizard.breadcrumbAria')"
          >
            <button type="button" class="sp-customer-plan-wizard__crumb-action" @click="goBackToCustomers">
              {{ $t('sicherplan.customerPlansWizard.breadcrumbCustomers') }}
            </button>
            <span>/</span>
            <button type="button" class="sp-customer-plan-wizard__crumb-action" @click="goBackToPlans">
              {{ $t('sicherplan.customerPlansWizard.breadcrumbPlans') }}
            </button>
            <span>/</span>
            <span>{{ $t('sicherplan.customerPlansWizard.title') }}</span>
          </nav>

          <div v-if="isLoading" class="sp-customer-plan-wizard__state" data-testid="customer-new-plan-loading">
            <strong>{{ $t('sicherplan.customerPlansWizard.loadingTitle') }}</strong>
            <span>{{ $t('sicherplan.customerPlansWizard.loadingBody') }}</span>
          </div>

          <EmptyState
            v-else-if="contextState === 'missing'"
            data-testid="customer-new-plan-missing-customer"
            :title="$t('sicherplan.customerPlansWizard.missingCustomerTitle')"
            :description="$t('sicherplan.customerPlansWizard.missingCustomerBody')"
          />

          <EmptyState
            v-else-if="contextState === 'not_found'"
            data-testid="customer-new-plan-unknown-customer"
            :title="$t('sicherplan.customerPlansWizard.unknownCustomerTitle')"
            :description="$t('sicherplan.customerPlansWizard.unknownCustomerBody')"
          />

          <EmptyState
            v-else-if="contextState === 'error'"
            data-testid="customer-new-plan-error"
            :title="$t('sicherplan.customerPlansWizard.errorTitle')"
            :description="$t('sicherplan.customerPlansWizard.errorBody')"
          />

          <template v-else>
            <div v-if="routeRestoreWarning" class="sp-customer-plan-wizard__state" data-testid="customer-new-plan-restore-warning">
              <strong>{{ routeRestoreWarning }}</strong>
            </div>

            <header class="sp-customer-plan-wizard__summary" data-testid="customer-new-plan-customer-summary">
              <div>
                <p class="eyebrow">{{ $t('sicherplan.customerPlansWizard.customerSummaryTitle') }}</p>
                <h2>{{ customer?.name }}</h2>
              </div>
              <div class="sp-customer-plan-wizard__summary-meta">
                <span>{{ $t('sicherplan.customerPlansWizard.customerNumber') }}: {{ customer?.customer_number }}</span>
                <span>{{ $t('sicherplan.customerPlansWizard.currentStep') }}: {{ currentStepLabel }}</span>
              </div>
            </header>

            <ol class="sp-customer-plan-wizard__steps" data-testid="customer-new-plan-stepper">
              <li
                v-for="(step, index) in wizardSteps"
                :key="step.id"
                class="sp-customer-plan-wizard__step"
                :data-state="index === currentStepIndex ? 'current' : index < currentStepIndex ? 'complete' : 'upcoming'"
              >
                <button
                  type="button"
                  class="sp-customer-plan-wizard__step-button"
                  :data-testid="`customer-new-plan-step-${step.id}`"
                  :disabled="!canEnterStep(step.id)"
                  @click="selectStep(step.id)"
                >
                  <span class="sp-customer-plan-wizard__step-index">{{ index + 1 }}</span>
                  <span class="sp-customer-plan-wizard__step-label">{{ step.label }}</span>
                </button>
              </li>
            </ol>

            <section
              class="sp-customer-plan-wizard__content"
              data-testid="customer-new-plan-step-content"
              :data-step-id="wizardState.current_step"
            >
              <p class="eyebrow">{{ currentStepLabel }}</p>
              <h3>{{ $t('sicherplan.customerPlansWizard.stepContentTitle') }}</h3>
              <CustomerNewPlanStepContent
                v-if="customer"
                ref="stepContentRef"
                :access-token="accessToken || ''"
                :current-step-id="wizardState.current_step"
                :customer="customer"
                :persist-drafts-on-unmount="persistDraftsOnUnmount"
                :tenant-id="tenantScopeId || ''"
                :wizard-state="wizardState"
                @saved-context="setSavedContext"
                @step-completion="setStepCompletion"
                @step-ui-state="(stepId, patch) => setStepUiState(stepId, patch)"
              />
            </section>

            <footer class="sp-customer-plan-wizard__actions" data-testid="customer-new-plan-action-bar">
              <button
                type="button"
                class="cta-button cta-secondary"
                data-testid="customer-new-plan-cancel"
                @click="goBackToPlans"
              >
                {{ $t('sicherplan.customerPlansWizard.actions.cancel') }}
              </button>
              <div class="sp-customer-plan-wizard__actions-right">
                <button
                  type="button"
                  class="cta-button cta-secondary"
                  data-testid="customer-new-plan-previous"
                  :disabled="!canMovePrevious"
                  @click="goToPreviousStep"
                >
                  {{ $t('sicherplan.customerPlansWizard.actions.previous') }}
                </button>
                <button
                  type="button"
                  class="cta-button"
                  :data-testid="isFinalStep ? 'customer-new-plan-generate-continue' : 'customer-new-plan-next'"
                  :disabled="stepSubmitting || (!canSubmitCurrentStep && !canMoveNext)"
                  @click="goToNextStep"
                >
                  {{ nextActionLabel }}
                </button>
              </div>
            </footer>
          </template>
        </div>
      </SectionBlock>
    </template>
  </ModuleWorkspacePage>
</template>

<style scoped>
.sp-customer-plan-wizard {
  display: grid;
  gap: 1rem;
}

.sp-customer-plan-wizard__breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  color: var(--sp-color-text-secondary);
  font-size: 0.92rem;
}

.sp-customer-plan-wizard__crumb-action {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font: inherit;
}

.sp-customer-plan-wizard__crumb-action:hover,
.sp-customer-plan-wizard__crumb-action:focus-visible {
  color: var(--sp-color-text-primary);
  text-decoration: underline;
  outline: none;
}

.sp-customer-plan-wizard__state,
.sp-customer-plan-wizard__summary,
.sp-customer-plan-wizard__content,
.sp-customer-plan-wizard__actions {
  padding: 1.1rem 1.2rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-shadow-card);
}

.sp-customer-plan-wizard__state {
  display: grid;
  gap: 0.35rem;
  color: var(--sp-color-text-secondary);
}

.sp-customer-plan-wizard__summary {
  display: grid;
  gap: 0.9rem;
}

.sp-customer-plan-wizard__summary h2,
.sp-customer-plan-wizard__summary p {
  margin: 0;
}

.sp-customer-plan-wizard__summary-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1.2rem;
  color: var(--sp-color-text-secondary);
}

.sp-customer-plan-wizard__steps {
  display: grid;
  gap: 0.75rem;
  padding: 0;
  margin: 0;
  list-style: none;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
}

.sp-customer-plan-wizard__step {
  min-width: 0;
  padding: 0.95rem 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.sp-customer-plan-wizard__step[data-state='current'] {
  border-color: rgb(40 170 170 / 48%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 12%);
}

.sp-customer-plan-wizard__step[data-state='complete'] {
  border-color: color-mix(in srgb, var(--sp-color-success) 28%, var(--sp-color-border-soft));
}

.sp-customer-plan-wizard__step-button {
  display: grid;
  gap: 0.3rem;
  align-content: start;
  width: 100%;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
}

.sp-customer-plan-wizard__step-button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
}

.sp-customer-plan-wizard__step-index {
  color: var(--sp-color-text-secondary);
  font-size: 0.82rem;
}

.sp-customer-plan-wizard__step-label {
  color: var(--sp-color-text-primary);
  font-weight: 600;
}

.sp-customer-plan-wizard__content {
  display: grid;
  gap: 0.6rem;
}

.sp-customer-plan-wizard__content h3,
.sp-customer-plan-wizard__content p {
  margin: 0;
}

.sp-customer-plan-wizard__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.sp-customer-plan-wizard__actions-right {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.75rem;
}

@media (max-width: 900px) {
  .sp-customer-plan-wizard__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .sp-customer-plan-wizard__actions-right {
    justify-content: stretch;
  }
}
</style>
