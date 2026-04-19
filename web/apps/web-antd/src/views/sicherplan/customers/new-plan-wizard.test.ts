import { describe, expect, it } from 'vitest';

import { useCustomerNewPlanWizard } from './use-customer-new-plan-wizard';

describe('useCustomerNewPlanWizard', () => {
  it('initializes from customer context and keeps the first step as the safe default', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');

    expect(wizard.state.value.customer_id).toBe('customer-1');
    expect(wizard.state.value.current_step).toBe('planning');
    expect(wizard.hasMinimumContext.value).toBe(true);
    expect(wizard.canEnterStep('planning')).toBe(true);
    expect(wizard.canEnterStep('order-details')).toBe(false);
  });

  it('blocks direct entry into a later step when prerequisites are missing', () => {
    const wizard = useCustomerNewPlanWizard();

    const resolvedStep = wizard.resetForCustomer('customer-1', 'series-exceptions');

    expect(resolvedStep).toBe('planning');
    expect(wizard.state.value.current_step).toBe('planning');
  });

  it('falls back to the furthest valid step when a requested later step is still too deep', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      order_id: 'order-1',
    });

    const resolvedStep = wizard.applyRequestedStep('series-exceptions');

    expect(resolvedStep).toBe('planning-record-overview');
    expect(wizard.state.value.current_step).toBe('planning-record-overview');
  });

  it('moves through steps only after the required saved ids exist', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    expect(wizard.canMoveNext.value).toBe(false);

    wizard.setSavedContext({
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
    });
    wizard.setStepCompletion('planning', true);

    expect(wizard.canMoveNext.value).toBe(true);
    wizard.moveNext();
    expect(wizard.state.value.current_step).toBe('order-details');

    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setStepCompletion('order-details', true);
    wizard.moveNext();
    expect(wizard.state.value.current_step).toBe('equipment-lines');
  });

  it('resets all transient ids when the customer context changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({ planning_entity_type: 'site', planning_entity_id: 'site-1', planning_mode_code: 'site' });
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({ planning_record_id: 'record-1' });
    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });
    wizard.setSavedContext({ series_id: 'series-1' });
    wizard.setStepCompletion('series-exceptions', true);

    wizard.resetForCustomer('customer-2', 'planning');

    expect(wizard.state.value.customer_id).toBe('customer-2');
    expect(wizard.state.value.order_id).toBe('');
    expect(wizard.state.value.planning_record_id).toBe('');
    expect(wizard.state.value.shift_plan_id).toBe('');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.state.value.step_state['series-exceptions'].completed).toBe(false);
  });

  it('keeps the customer id stable when a saved-context patch tries to change it', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({
      customer_id: 'customer-2',
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
    });

    expect(wizard.state.value.customer_id).toBe('customer-1');
    expect(wizard.state.value.planning_entity_id).toBe('site-1');
  });

  it('clears wizard state on cancel/reset', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      order_id: 'order-1',
    });
    wizard.setStepUiState('planning', { dirty: true, error: 'problem' });

    wizard.resetWizard();

    expect(wizard.state.value.customer_id).toBe('');
    expect(wizard.state.value.order_id).toBe('');
    expect(wizard.state.value.step_state.planning.dirty).toBe(false);
    expect(wizard.state.value.step_state.planning.error).toBe('');
  });

  it('retains saved ids when revisiting earlier steps', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({ planning_entity_type: 'site', planning_entity_id: 'site-1', planning_mode_code: 'site' });
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({ planning_record_id: 'record-1' });
    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });
    wizard.setCurrentStep('shift-plan');

    wizard.movePrevious();

    expect(wizard.state.value.current_step).toBe('planning-record-documents');
    expect(wizard.state.value.order_id).toBe('order-1');
    expect(wizard.state.value.planning_record_id).toBe('record-1');
    expect(wizard.state.value.shift_plan_id).toBe('shift-plan-1');
  });

  it('invalidates downstream ids and step state when the planning context changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({ planning_entity_type: 'site', planning_entity_id: 'site-1', planning_mode_code: 'site' });
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({ planning_record_id: 'record-1' });
    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });
    wizard.setSavedContext({ series_id: 'series-1' });
    wizard.setStepCompletion('planning-record-overview', true);
    wizard.setStepCompletion('planning-record-documents', true);
    wizard.setStepCompletion('shift-plan', true);
    wizard.setStepCompletion('series-exceptions', true);
    wizard.setCurrentStep('series-exceptions');

    wizard.setSavedContext({
      planning_entity_type: 'event_venue',
      planning_entity_id: 'venue-1',
      planning_mode_code: 'event',
    });

    expect(wizard.state.value.planning_entity_type).toBe('event_venue');
    expect(wizard.state.value.planning_entity_id).toBe('venue-1');
    expect(wizard.state.value.planning_mode_code).toBe('event');
    expect(wizard.state.value.order_id).toBe('order-1');
    expect(wizard.state.value.planning_record_id).toBe('');
    expect(wizard.state.value.shift_plan_id).toBe('');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.state.value.step_state['planning-record-overview'].completed).toBe(false);
    expect(wizard.state.value.step_state['planning-record-documents'].completed).toBe(false);
    expect(wizard.state.value.step_state['shift-plan'].completed).toBe(false);
    expect(wizard.state.value.step_state['series-exceptions'].completed).toBe(false);
    expect(wizard.state.value.current_step).toBe('planning-record-overview');
  });

  it('invalidates downstream ids and completion when the order changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({ planning_entity_type: 'site', planning_entity_id: 'site-1', planning_mode_code: 'site' });
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({ planning_record_id: 'record-1' });
    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });
    wizard.setSavedContext({ series_id: 'series-1' });
    wizard.setStepCompletion('equipment-lines', true);
    wizard.setStepCompletion('requirement-lines', true);
    wizard.setStepCompletion('order-documents', true);
    wizard.setStepCompletion('planning-record-overview', true);
    wizard.setStepCompletion('planning-record-documents', true);
    wizard.setStepCompletion('shift-plan', true);
    wizard.setStepCompletion('series-exceptions', true);
    wizard.setCurrentStep('series-exceptions');

    wizard.setSavedContext({ order_id: 'order-2' });

    expect(wizard.state.value.order_id).toBe('order-2');
    expect(wizard.state.value.planning_record_id).toBe('');
    expect(wizard.state.value.shift_plan_id).toBe('');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.state.value.step_state['equipment-lines'].completed).toBe(false);
    expect(wizard.state.value.step_state['requirement-lines'].completed).toBe(false);
    expect(wizard.state.value.step_state['order-documents'].completed).toBe(false);
    expect(wizard.state.value.step_state['planning-record-overview'].completed).toBe(false);
    expect(wizard.state.value.step_state['planning-record-documents'].completed).toBe(false);
    expect(wizard.state.value.step_state['shift-plan'].completed).toBe(false);
    expect(wizard.state.value.step_state['series-exceptions'].completed).toBe(false);
    expect(wizard.state.value.current_step).toBe('planning-record-overview');
  });

  it('invalidates shift-plan and series ids when the planning record changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({ planning_entity_type: 'site', planning_entity_id: 'site-1', planning_mode_code: 'site' });
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({ planning_record_id: 'record-1' });
    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });
    wizard.setSavedContext({ series_id: 'series-1' });
    wizard.setStepCompletion('planning-record-documents', true);
    wizard.setStepCompletion('shift-plan', true);
    wizard.setStepCompletion('series-exceptions', true);
    wizard.setCurrentStep('series-exceptions');

    wizard.setSavedContext({ planning_record_id: 'record-2' });

    expect(wizard.state.value.planning_record_id).toBe('record-2');
    expect(wizard.state.value.shift_plan_id).toBe('');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.state.value.step_state['planning-record-documents'].completed).toBe(false);
    expect(wizard.state.value.step_state['shift-plan'].completed).toBe(false);
    expect(wizard.state.value.step_state['series-exceptions'].completed).toBe(false);
    expect(wizard.state.value.current_step).toBe('shift-plan');
  });

  it('invalidates only the series state when the shift plan changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({ planning_entity_type: 'site', planning_entity_id: 'site-1', planning_mode_code: 'site' });
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({ planning_record_id: 'record-1' });
    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });
    wizard.setSavedContext({ series_id: 'series-1' });
    wizard.setStepCompletion('shift-plan', true);
    wizard.setStepCompletion('series-exceptions', true);
    wizard.setCurrentStep('series-exceptions');

    wizard.setSavedContext({ shift_plan_id: 'shift-plan-2' });

    expect(wizard.state.value.shift_plan_id).toBe('shift-plan-2');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.state.value.step_state['shift-plan'].completed).toBe(true);
    expect(wizard.state.value.step_state['series-exceptions'].completed).toBe(false);
    expect(wizard.state.value.current_step).toBe('series-exceptions');
  });

  it('only reports handoff readiness when all required ids exist and the final step is completed', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning');
    wizard.setSavedContext({ planning_entity_type: 'site', planning_entity_id: 'site-1', planning_mode_code: 'site' });
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({ planning_record_id: 'record-1' });
    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });
    wizard.setSavedContext({ series_id: 'series-1' });

    expect(wizard.isWizardCompleteEnoughForHandoff.value).toBe(false);

    wizard.setStepCompletion('series-exceptions', true);

    expect(wizard.isWizardCompleteEnoughForHandoff.value).toBe(true);
  });
});
