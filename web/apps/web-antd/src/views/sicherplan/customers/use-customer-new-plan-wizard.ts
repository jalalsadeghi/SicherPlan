import { computed, ref } from 'vue';

import {
  createInitialWizardState,
  CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID,
  CUSTOMER_NEW_PLAN_WIZARD_LAST_STEP_ID,
  CUSTOMER_NEW_PLAN_WIZARD_STEPS,
  getNextWizardStepId,
  getPreviousWizardStepId,
  getWizardStepDefinition,
  hasRequiredContextForStep,
  isWizardStepId,
  resolveAllowedWizardStep,
} from './new-plan-wizard.steps';
import type {
  CustomerNewPlanWizardState,
  CustomerNewPlanWizardStatePatch,
  CustomerNewPlanWizardStepId,
  CustomerNewPlanWizardStepUiState,
} from './new-plan-wizard.types';

function normalizeScalar(value: null | string | undefined) {
  return typeof value === 'string' ? value.trim() : '';
}

function resolveStableCustomerId(
  currentCustomerId: string,
  patchCustomerId: null | string | undefined,
) {
  const normalizedPatchCustomerId = normalizeScalar(patchCustomerId);
  if (!currentCustomerId) {
    return normalizedPatchCustomerId;
  }
  if (!normalizedPatchCustomerId || normalizedPatchCustomerId === currentCustomerId) {
    return currentCustomerId;
  }
  return currentCustomerId;
}

function resetStepUiState(): CustomerNewPlanWizardStepUiState {
  return {
    completed: false,
    dirty: false,
    error: '',
    loading: false,
  };
}

function invalidateSteps(
  state: CustomerNewPlanWizardState,
  stepIds: CustomerNewPlanWizardStepId[],
) {
  for (const stepId of stepIds) {
    state.step_state[stepId] = resetStepUiState();
  }
}

export function useCustomerNewPlanWizard() {
  const state = ref(createInitialWizardState());

  const steps = computed(() => CUSTOMER_NEW_PLAN_WIZARD_STEPS);
  const currentStep = computed(() => getWizardStepDefinition(state.value.current_step));
  const hasMinimumContext = computed(() => Boolean(state.value.customer_id));
  const canMovePrevious = computed(() => state.value.current_step !== CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID);
  const canMoveNext = computed(() => {
    const nextStepId = getNextWizardStepId(state.value.current_step);
    if (!nextStepId) {
      return false;
    }
    return state.value.step_state[state.value.current_step].completed && hasRequiredContextForStep(state.value, nextStepId);
  });
  const isWizardCompleteEnoughForHandoff = computed(
    () =>
      Boolean(
        state.value.customer_id &&
          state.value.order_id &&
          state.value.planning_record_id &&
          state.value.shift_plan_id &&
          state.value.series_id &&
          state.value.step_state[CUSTOMER_NEW_PLAN_WIZARD_LAST_STEP_ID].completed,
      ),
  );

  function canEnterStep(stepId: CustomerNewPlanWizardStepId) {
    return hasRequiredContextForStep(state.value, stepId);
  }

  function syncCurrentStep(requestedStepId?: CustomerNewPlanWizardStepId | null) {
    state.value.current_step = resolveAllowedWizardStep(state.value, requestedStepId);
    return state.value.current_step;
  }

  function resetForCustomer(customerId: string, requestedStepId?: CustomerNewPlanWizardStepId | null) {
    state.value = createInitialWizardState(normalizeScalar(customerId));
    return syncCurrentStep(requestedStepId);
  }

  function resetWizard() {
    return resetForCustomer('', null);
  }

  function setCurrentStep(stepId: CustomerNewPlanWizardStepId) {
    if (!canEnterStep(stepId)) {
      return syncCurrentStep(null);
    }
    state.value.current_step = stepId;
    return state.value.current_step;
  }

  function applyRequestedStep(stepId: string | null | undefined) {
    return syncCurrentStep(isWizardStepId(stepId) ? stepId : null);
  }

  function moveNext() {
    const nextStepId = getNextWizardStepId(state.value.current_step);
    if (!nextStepId) {
      return state.value.current_step;
    }
    return setCurrentStep(nextStepId);
  }

  function movePrevious() {
    const previousStepId = getPreviousWizardStepId(state.value.current_step);
    if (!previousStepId) {
      return state.value.current_step;
    }
    state.value.current_step = previousStepId;
    return state.value.current_step;
  }

  function setSavedContext(patch: CustomerNewPlanWizardStatePatch) {
    const nextState: CustomerNewPlanWizardState = {
      ...state.value,
      customer_id: resolveStableCustomerId(state.value.customer_id, patch.customer_id),
      order_id: normalizeScalar(patch.order_id ?? state.value.order_id),
      planning_entity_id: normalizeScalar(patch.planning_entity_id ?? state.value.planning_entity_id),
      planning_entity_type: normalizeScalar(patch.planning_entity_type ?? state.value.planning_entity_type),
      planning_mode_code: normalizeScalar(patch.planning_mode_code ?? state.value.planning_mode_code),
      planning_record_id: normalizeScalar(patch.planning_record_id ?? state.value.planning_record_id),
      series_id: normalizeScalar(patch.series_id ?? state.value.series_id),
      shift_plan_id: normalizeScalar(patch.shift_plan_id ?? state.value.shift_plan_id),
      step_state: {
        ...state.value.step_state,
      },
    };

    const planningContextChanged =
      nextState.planning_entity_id !== state.value.planning_entity_id ||
      nextState.planning_entity_type !== state.value.planning_entity_type ||
      nextState.planning_mode_code !== state.value.planning_mode_code;
    const orderChanged = nextState.order_id !== state.value.order_id;
    const planningRecordChanged = nextState.planning_record_id !== state.value.planning_record_id;
    const shiftPlanChanged = nextState.shift_plan_id !== state.value.shift_plan_id;

    if (planningContextChanged) {
      nextState.planning_record_id = '';
      nextState.shift_plan_id = '';
      nextState.series_id = '';
      invalidateSteps(nextState, [
        'planning-record-overview',
        'planning-record-documents',
        'shift-plan',
        'series-exceptions',
      ]);
    }

    if (orderChanged) {
      nextState.planning_record_id = '';
      nextState.shift_plan_id = '';
      nextState.series_id = '';
      invalidateSteps(nextState, [
        'equipment-lines',
        'requirement-lines',
        'order-documents',
        'planning-record-overview',
        'planning-record-documents',
        'shift-plan',
        'series-exceptions',
      ]);
    }

    if (planningRecordChanged) {
      nextState.shift_plan_id = '';
      nextState.series_id = '';
      invalidateSteps(nextState, [
        'planning-record-documents',
        'shift-plan',
        'series-exceptions',
      ]);
    }

    if (shiftPlanChanged) {
      nextState.series_id = '';
      invalidateSteps(nextState, ['series-exceptions']);
    }

    state.value = nextState;
    return syncCurrentStep(state.value.current_step);
  }

  function setStepCompletion(stepId: CustomerNewPlanWizardStepId, completed: boolean) {
    state.value.step_state[stepId] = {
      ...state.value.step_state[stepId],
      completed,
    };
  }

  function setStepUiState(stepId: CustomerNewPlanWizardStepId, patch: Partial<CustomerNewPlanWizardStepUiState>) {
    state.value.step_state[stepId] = {
      ...state.value.step_state[stepId],
      ...patch,
    };
  }

  return {
    state,
    steps,
    currentStep,
    hasMinimumContext,
    canMoveNext,
    canMovePrevious,
    isWizardCompleteEnoughForHandoff,
    applyRequestedStep,
    canEnterStep,
    moveNext,
    movePrevious,
    resetForCustomer,
    resetWizard,
    setCurrentStep,
    setSavedContext,
    setStepCompletion,
    setStepUiState,
  };
}
