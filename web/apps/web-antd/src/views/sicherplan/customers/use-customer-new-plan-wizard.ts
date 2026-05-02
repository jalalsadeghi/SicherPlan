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
  normalizeWizardStepId,
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

function logWizardContextDiagnostic(
  message: string,
  payload: Record<string, unknown>,
) {
  if (!import.meta.env.DEV) {
    return;
  }
  console.debug(`[customer-new-plan-wizard] ${message}`, payload);
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
    return syncCurrentStep(normalizeWizardStepId(stepId));
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
    const previousState = state.value;
    const explicitOrderId = normalizeScalar(patch.order_id);
    const explicitPlanningRecordId = normalizeScalar(patch.planning_record_id);
    const explicitShiftPlanId = normalizeScalar(patch.shift_plan_id);
    const explicitSeriesId = normalizeScalar(patch.series_id);
    const hasExplicitPlanningContext =
      Object.prototype.hasOwnProperty.call(patch, 'planning_entity_id') ||
      Object.prototype.hasOwnProperty.call(patch, 'planning_entity_type') ||
      Object.prototype.hasOwnProperty.call(patch, 'planning_mode_code');
    const hasExplicitOrderId = Object.prototype.hasOwnProperty.call(patch, 'order_id');
    const hasExplicitPlanningRecordId = Object.prototype.hasOwnProperty.call(patch, 'planning_record_id');
    const hasExplicitShiftPlanId = Object.prototype.hasOwnProperty.call(patch, 'shift_plan_id');
    const hasExplicitSeriesId = Object.prototype.hasOwnProperty.call(patch, 'series_id');
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
    const seriesChanged = nextState.series_id !== state.value.series_id;
    const shouldPreservePlanningRecordForPlanningContextChange =
      Boolean(explicitPlanningRecordId && hasExplicitPlanningContext);
    const shouldPreservePlanningRecordForOrderChange =
      Boolean(explicitOrderId && explicitPlanningRecordId && hasExplicitOrderId && hasExplicitPlanningRecordId);
    const shouldPreserveShiftPlanForPlanningContextChange =
      Boolean(
        shouldPreservePlanningRecordForPlanningContextChange &&
          explicitShiftPlanId &&
          hasExplicitPlanningRecordId &&
          hasExplicitShiftPlanId,
      );
    const shouldPreserveShiftPlanForOrderChange =
      Boolean(
        shouldPreservePlanningRecordForOrderChange &&
          explicitShiftPlanId &&
          hasExplicitPlanningRecordId &&
          hasExplicitShiftPlanId,
      );
    const shouldPreserveShiftPlanForPlanningRecordChange =
      Boolean(explicitPlanningRecordId && explicitShiftPlanId && hasExplicitPlanningRecordId && hasExplicitShiftPlanId);
    const shouldPreserveSeriesForShiftPlanChange =
      Boolean(explicitShiftPlanId && explicitSeriesId && hasExplicitShiftPlanId && hasExplicitSeriesId);

    let shiftPlanClearReason = '';

    if (planningContextChanged) {
      nextState.planning_record_id = shouldPreservePlanningRecordForPlanningContextChange ? explicitPlanningRecordId : '';
      if (shouldPreserveShiftPlanForPlanningContextChange) {
        nextState.shift_plan_id = explicitShiftPlanId;
      } else {
        nextState.shift_plan_id = '';
        shiftPlanClearReason = hasExplicitShiftPlanId
          ? 'explicit_clear'
          : 'planningContextChanged without explicit shift_plan_id';
      }
      nextState.series_id = '';
      invalidateSteps(nextState, [
        'planning-record-documents',
        'shift-plan',
        'series-exceptions',
        'demand-groups',
      ]);
      if (!shouldPreservePlanningRecordForPlanningContextChange) {
        invalidateSteps(nextState, ['planning-record-overview']);
      }
    }

    if (orderChanged) {
      nextState.planning_record_id = shouldPreservePlanningRecordForOrderChange ? explicitPlanningRecordId : '';
      if (shouldPreserveShiftPlanForOrderChange) {
        nextState.shift_plan_id = explicitShiftPlanId;
      } else {
        nextState.shift_plan_id = '';
        shiftPlanClearReason = hasExplicitShiftPlanId
          ? 'explicit_clear'
          : 'orderChanged without explicit shift_plan_id';
      }
      nextState.series_id = '';
      invalidateSteps(nextState, [
        'order-scope-documents',
        'planning-record-documents',
        'shift-plan',
        'series-exceptions',
        'demand-groups',
      ]);
      if (!shouldPreservePlanningRecordForOrderChange) {
        invalidateSteps(nextState, ['planning-record-overview']);
      }
    }

    if (planningRecordChanged) {
      if (shouldPreserveShiftPlanForPlanningRecordChange) {
        nextState.shift_plan_id = explicitShiftPlanId;
      } else {
        nextState.shift_plan_id = '';
        shiftPlanClearReason = hasExplicitShiftPlanId
          ? 'explicit_clear'
          : 'planningRecordChanged without explicit shift_plan_id';
      }
      nextState.series_id = '';
      invalidateSteps(nextState, [
        'planning-record-documents',
        'shift-plan',
        'series-exceptions',
        'demand-groups',
      ]);
    }

    if (shiftPlanChanged) {
      nextState.series_id = shouldPreserveSeriesForShiftPlanChange ? explicitSeriesId : '';
      invalidateSteps(nextState, ['series-exceptions', 'demand-groups']);
    }

    if (seriesChanged) {
      invalidateSteps(nextState, ['demand-groups']);
    }

    state.value = nextState;

    if (previousState.shift_plan_id && !nextState.shift_plan_id) {
      logWizardContextDiagnostic('cleared shift_plan_id', {
        patch,
        previousState,
        nextState,
        planningContextChanged,
        orderChanged,
        planningRecordChanged,
        shiftPlanChanged,
        reason: shiftPlanClearReason || (hasExplicitShiftPlanId ? 'explicit_clear' : 'unknown'),
      });
    }
    if (previousState.current_step === 'series-exceptions' && !nextState.shift_plan_id) {
      logWizardContextDiagnostic('series-exceptions lost shift_plan_id', {
        patch,
        previousState,
        nextState,
        planningContextChanged,
        orderChanged,
        planningRecordChanged,
        shiftPlanChanged,
        reason: shiftPlanClearReason || (hasExplicitShiftPlanId ? 'explicit_clear' : 'unknown'),
      });
    }

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
