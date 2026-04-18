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
import {
  CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID,
  CUSTOMER_NEW_PLAN_WIZARD_LAST_STEP_ID,
  isWizardStepId,
} from './new-plan-wizard.steps';
import type { CustomerNewPlanWizardStepId } from './new-plan-wizard.types';
import { useCustomerNewPlanWizard } from './use-customer-new-plan-wizard';

type WizardContextState = 'loading' | 'ready' | 'missing' | 'not_found' | 'error';

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
  return isWizardStepId(candidate) ? candidate : null;
});

const isAuthorized = computed(() => authStore.effectiveRole === 'tenant_admin');
const tenantScopeId = computed(() => authStore.effectiveTenantScopeId);
const accessToken = computed(() => authStore.effectiveAccessToken || authStore.accessToken);
const isLoading = computed(
  () => authStore.isSessionResolving || contextState.value === 'loading',
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
  'planning',
  'order-details',
  'equipment-lines',
  'requirement-lines',
  'order-documents',
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

function confirmDiscardChanges() {
  if (!hasUnsavedChanges.value) {
    return true;
  }
  return window.confirm($t('sicherplan.customerPlansWizard.confirmDiscard'));
}

async function resolveCustomerContext() {
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
    contextState.value = 'loading';
    customer.value = null;
    return;
  }

  contextState.value = 'loading';
  try {
    customer.value = await getCustomer(tenantScopeId.value, customerId.value, accessToken.value);
    contextState.value = 'ready';
  } catch (error) {
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
  void router.push('/admin/customers');
}

function goToPreviousStep() {
  if (!canMovePrevious.value) {
    return;
  }
  movePrevious();
}

function goToNextStep() {
  if (stepSubmitting.value) {
    return;
  }
  if (canSubmitCurrentStep.value) {
    stepSubmitting.value = true;
    Promise.resolve(stepContentRef.value?.submitCurrentStep?.())
      .then((success) => {
        if (success && !isFinalStep.value) {
          moveNext();
        }
      })
      .finally(() => {
        stepSubmitting.value = false;
      });
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

async function syncWizardRouteStep() {
  if (!bootstrapped.value || !customerId.value) {
    return;
  }
  const nextQuery: LocationQueryRaw = {
    ...route.query,
    customer_id: customerId.value,
  };

  if (wizardState.value.current_step === CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID) {
    delete nextQuery.step;
  } else {
    nextQuery.step = wizardState.value.current_step;
  }

  const currentQueryStep = Array.isArray(route.query.step) ? route.query.step[0] : route.query.step;
  if (currentQueryStep === nextQuery.step) {
    return;
  }

  await router.replace({
    path: '/admin/customers/new-plan',
    query: nextQuery,
  });
}

onMounted(async () => {
  authStore.syncFromPrimarySession();
  await authStore.ensureSessionReady();
  bootstrapped.value = true;
  resetForCustomer(customerId.value, requestedStepId.value);
  await resolveCustomerContext();
  await syncWizardRouteStep();
});

watch(
  () => [customerId.value, tenantScopeId.value, accessToken.value, isAuthorized.value] as const,
  async ([nextCustomerId], [previousCustomerId]) => {
    if (!bootstrapped.value) {
      return;
    }
    if (nextCustomerId !== previousCustomerId) {
      resetForCustomer(nextCustomerId, requestedStepId.value);
      await syncWizardRouteStep();
    }
    await resolveCustomerContext();
  },
);

watch(
  () => requestedStepId.value,
  async (nextStepId) => {
    if (!bootstrapped.value) {
      return;
    }
    applyRequestedStep(nextStepId);
    await syncWizardRouteStep();
  },
);

watch(
  () => wizardState.value.current_step,
  async () => {
    if (!bootstrapped.value) {
      return;
    }
    await syncWizardRouteStep();
  },
);
</script>

<template>
  <ForbiddenView v-if="!isAuthorized" />

  <ModuleWorkspacePage
    v-else
    :description="$t('sicherplan.customerPlansWizard.description')"
    :eyebrow="$t('sicherplan.admin.customers')"
    :show-intro="true"
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
