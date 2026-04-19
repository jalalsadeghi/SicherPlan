export type CustomerNewPlanWizardStepId =
  | 'order-details'
  | 'equipment-lines'
  | 'requirement-lines'
  | 'order-documents'
  | 'planning-record-overview'
  | 'planning-record-documents'
  | 'shift-plan'
  | 'series-exceptions';

export interface CustomerNewPlanWizardStepUiState {
  completed: boolean;
  dirty: boolean;
  error: string;
  loading: boolean;
}

export interface CustomerNewPlanWizardState {
  current_step: CustomerNewPlanWizardStepId;
  customer_id: string;
  order_id: string;
  planning_entity_id: string;
  planning_entity_type: string;
  planning_mode_code: string;
  planning_record_id: string;
  series_id: string;
  shift_plan_id: string;
  step_state: Record<CustomerNewPlanWizardStepId, CustomerNewPlanWizardStepUiState>;
}

export type CustomerNewPlanWizardStatePatch = Partial<
  Pick<
    CustomerNewPlanWizardState,
    | 'customer_id'
    | 'order_id'
    | 'planning_entity_id'
    | 'planning_entity_type'
    | 'planning_mode_code'
    | 'planning_record_id'
    | 'series_id'
    | 'shift_plan_id'
  >
>;

export interface CustomerNewPlanWizardStepDefinition {
  id: CustomerNewPlanWizardStepId;
  labelKey: string;
  loadHandlerKey: string;
  nextStepResolverKey: string;
  requiredContextFields: Array<
    | 'customer_id'
    | 'order_id'
    | 'planning_entity_id'
    | 'planning_entity_type'
    | 'planning_mode_code'
    | 'planning_record_id'
    | 'series_id'
    | 'shift_plan_id'
  >;
  saveHandlerKey: string;
  validateHandlerKey: string;
}
