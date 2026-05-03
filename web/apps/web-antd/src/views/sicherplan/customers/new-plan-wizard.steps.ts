import type {
  CustomerNewPlanWizardState,
  CustomerNewPlanWizardStepDefinition,
  CustomerNewPlanWizardStepId,
  CustomerNewPlanWizardStepUiState,
} from './new-plan-wizard.types';

export const CUSTOMER_NEW_PLAN_STEP_ALIASES: Record<string, CustomerNewPlanWizardStepId> = {
  'equipment-lines': 'order-scope-documents',
  'requirement-lines': 'order-scope-documents',
  'order-documents': 'order-scope-documents',
};

export const CUSTOMER_NEW_PLAN_WIZARD_STEPS: CustomerNewPlanWizardStepDefinition[] = [
  {
    id: 'order-details',
    labelKey: 'sicherplan.customerPlansWizard.steps.orderDetails',
    requiredContextFields: ['customer_id'],
    loadHandlerKey: 'loadOrderDetailsStep',
    validateHandlerKey: 'validateOrderDetailsStep',
    saveHandlerKey: 'saveOrderDetailsStep',
    nextStepResolverKey: 'resolveOrderDetailsStepNext',
  },
  {
    id: 'order-scope-documents',
    labelKey: 'sicherplan.customerPlansWizard.steps.orderScopeDocuments',
    requiredContextFields: ['customer_id', 'order_id'],
    loadHandlerKey: 'loadOrderScopeDocumentsStep',
    validateHandlerKey: 'validateOrderScopeDocumentsStep',
    saveHandlerKey: 'saveOrderScopeDocumentsStep',
    nextStepResolverKey: 'resolveOrderScopeDocumentsStepNext',
  },
  {
    id: 'planning-record-overview',
    labelKey: 'sicherplan.customerPlansWizard.steps.planningRecordOverview',
    requiredContextFields: ['customer_id', 'order_id'],
    loadHandlerKey: 'loadPlanningRecordOverviewStep',
    validateHandlerKey: 'validatePlanningRecordOverviewStep',
    saveHandlerKey: 'savePlanningRecordOverviewStep',
    nextStepResolverKey: 'resolvePlanningRecordOverviewStepNext',
  },
  {
    id: 'planning-record-documents',
    labelKey: 'sicherplan.customerPlansWizard.steps.planningRecordDocuments',
    requiredContextFields: ['customer_id', 'planning_record_id'],
    loadHandlerKey: 'loadPlanningRecordDocumentsStep',
    validateHandlerKey: 'validatePlanningRecordDocumentsStep',
    saveHandlerKey: 'savePlanningRecordDocumentsStep',
    nextStepResolverKey: 'resolvePlanningRecordDocumentsStepNext',
  },
  {
    id: 'shift-plan',
    labelKey: 'sicherplan.customerPlansWizard.steps.shiftPlan',
    requiredContextFields: ['customer_id', 'planning_record_id'],
    loadHandlerKey: 'loadShiftPlanStep',
    validateHandlerKey: 'validateShiftPlanStep',
    saveHandlerKey: 'saveShiftPlanStep',
    nextStepResolverKey: 'resolveShiftPlanStepNext',
  },
  {
    id: 'series-exceptions',
    labelKey: 'sicherplan.customerPlansWizard.steps.seriesExceptions',
    requiredContextFields: ['customer_id', 'shift_plan_id'],
    loadHandlerKey: 'loadSeriesExceptionsStep',
    validateHandlerKey: 'validateSeriesExceptionsStep',
    saveHandlerKey: 'saveSeriesExceptionsStep',
    nextStepResolverKey: 'resolveSeriesExceptionsStepNext',
  },
  {
    id: 'demand-groups',
    labelKey: 'sicherplan.customerPlansWizard.steps.demandGroups',
    requiredContextFields: ['customer_id', 'shift_plan_id'],
    loadHandlerKey: 'loadDemandGroupsStep',
    validateHandlerKey: 'validateDemandGroupsStep',
    saveHandlerKey: 'saveDemandGroupsStep',
    nextStepResolverKey: 'resolveDemandGroupsStepNext',
  },
  {
    id: 'assignments',
    labelKey: 'sicherplan.customerPlansWizard.steps.assignments',
    requiredContextFields: ['customer_id', 'shift_plan_id'],
    loadHandlerKey: 'loadAssignmentsStep',
    validateHandlerKey: 'validateAssignmentsStep',
    saveHandlerKey: 'saveAssignmentsStep',
    nextStepResolverKey: 'resolveAssignmentsStepNext',
  },
];

export const CUSTOMER_NEW_PLAN_WIZARD_STEP_IDS = CUSTOMER_NEW_PLAN_WIZARD_STEPS.map((step) => step.id);

export const CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID = CUSTOMER_NEW_PLAN_WIZARD_STEPS[0]!.id;
export const CUSTOMER_NEW_PLAN_WIZARD_LAST_STEP_ID =
  CUSTOMER_NEW_PLAN_WIZARD_STEPS[CUSTOMER_NEW_PLAN_WIZARD_STEPS.length - 1]!.id;

export function createInitialStepUiState(): CustomerNewPlanWizardStepUiState {
  return {
    completed: false,
    dirty: false,
    error: '',
    loading: false,
  };
}

export function createInitialStepState() {
  return CUSTOMER_NEW_PLAN_WIZARD_STEPS.reduce<Record<CustomerNewPlanWizardStepId, CustomerNewPlanWizardStepUiState>>(
    (accumulator, step) => {
      accumulator[step.id] = createInitialStepUiState();
      return accumulator;
    },
    {} as Record<CustomerNewPlanWizardStepId, CustomerNewPlanWizardStepUiState>,
  );
}

export function createInitialWizardState(customerId = ''): CustomerNewPlanWizardState {
  return {
    current_step: CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID,
    customer_id: customerId,
    order_id: '',
    planning_entity_id: '',
    planning_entity_type: '',
    planning_mode_code: '',
    planning_record_id: '',
    series_id: '',
    shift_plan_id: '',
    step_state: createInitialStepState(),
  };
}

export function getWizardStepDefinition(stepId: CustomerNewPlanWizardStepId) {
  return CUSTOMER_NEW_PLAN_WIZARD_STEPS.find((step) => step.id === stepId) ?? CUSTOMER_NEW_PLAN_WIZARD_STEPS[0]!;
}

export function getWizardStepIndex(stepId: CustomerNewPlanWizardStepId) {
  return CUSTOMER_NEW_PLAN_WIZARD_STEP_IDS.indexOf(stepId);
}

export function getPreviousWizardStepId(stepId: CustomerNewPlanWizardStepId) {
  const currentIndex = getWizardStepIndex(stepId);
  if (currentIndex <= 0) {
    return null;
  }
  return CUSTOMER_NEW_PLAN_WIZARD_STEP_IDS[currentIndex - 1] ?? null;
}

export function getNextWizardStepId(stepId: CustomerNewPlanWizardStepId) {
  const currentIndex = getWizardStepIndex(stepId);
  if (currentIndex < 0 || currentIndex >= CUSTOMER_NEW_PLAN_WIZARD_STEP_IDS.length - 1) {
    return null;
  }
  return CUSTOMER_NEW_PLAN_WIZARD_STEP_IDS[currentIndex + 1] ?? null;
}

export function isWizardStepId(value: string | null | undefined): value is CustomerNewPlanWizardStepId {
  return typeof value === 'string' && CUSTOMER_NEW_PLAN_WIZARD_STEP_IDS.includes(value as CustomerNewPlanWizardStepId);
}

export function normalizeWizardStepId(value: string | null | undefined): CustomerNewPlanWizardStepId | null {
  if (isWizardStepId(value)) {
    return value;
  }
  if (typeof value === 'string') {
    return CUSTOMER_NEW_PLAN_STEP_ALIASES[value] ?? null;
  }
  return null;
}

export function hasRequiredContextForStep(state: CustomerNewPlanWizardState, stepId: CustomerNewPlanWizardStepId) {
  const step = getWizardStepDefinition(stepId);
  return step.requiredContextFields.every((fieldName) => Boolean(state[fieldName]));
}

export function resolveFurthestEnterableWizardStep(state: CustomerNewPlanWizardState) {
  const lastEnterableStep = [...CUSTOMER_NEW_PLAN_WIZARD_STEPS]
    .reverse()
    .find((step) => hasRequiredContextForStep(state, step.id));
  return lastEnterableStep?.id ?? CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID;
}

export function resolveAllowedWizardStep(
  state: CustomerNewPlanWizardState,
  requestedStepId: CustomerNewPlanWizardStepId | null | undefined,
) {
  if (!requestedStepId) {
    return hasRequiredContextForStep(state, state.current_step)
      ? state.current_step
      : CUSTOMER_NEW_PLAN_WIZARD_FIRST_STEP_ID;
  }
  if (requestedStepId && hasRequiredContextForStep(state, requestedStepId)) {
    return requestedStepId;
  }
  return resolveFurthestEnterableWizardStep(state);
}
