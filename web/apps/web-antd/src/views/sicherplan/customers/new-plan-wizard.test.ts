import { describe, expect, it } from 'vitest';

import { useCustomerNewPlanWizard } from './use-customer-new-plan-wizard';

describe('useCustomerNewPlanWizard', () => {
  it('initializes from customer context with order-details as the safe first step', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');

    expect(wizard.state.value.customer_id).toBe('customer-1');
    expect(wizard.state.value.current_step).toBe('order-details');
    expect(wizard.hasMinimumContext.value).toBe(true);
    expect(wizard.canEnterStep('order-details')).toBe(true);
    expect(wizard.canEnterStep('equipment-lines')).toBe(false);
  });

  it('blocks direct entry into later steps when prerequisites are missing', () => {
    const wizard = useCustomerNewPlanWizard();

    const resolvedStep = wizard.resetForCustomer('customer-1', 'series-exceptions');

    expect(resolvedStep).toBe('order-details');
    expect(wizard.state.value.current_step).toBe('order-details');
  });

  it('moves forward only after the required saved ids exist', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    expect(wizard.canMoveNext.value).toBe(false);

    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setStepCompletion('order-details', true);

    expect(wizard.canMoveNext.value).toBe(true);
    wizard.moveNext();
    expect(wizard.state.value.current_step).toBe('equipment-lines');
  });

  it('allows the planning-record step to be entered once order context exists', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({ order_id: 'order-1' });

    const resolvedStep = wizard.applyRequestedStep('planning-record-overview');

    expect(resolvedStep).toBe('planning-record-overview');
    expect(wizard.state.value.current_step).toBe('planning-record-overview');
  });

  it('resets all transient ids when the customer context changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
    });
    wizard.setStepCompletion('series-exceptions', true);

    wizard.resetForCustomer('customer-2', 'order-details');

    expect(wizard.state.value.customer_id).toBe('customer-2');
    expect(wizard.state.value.order_id).toBe('');
    expect(wizard.state.value.planning_entity_id).toBe('');
    expect(wizard.state.value.planning_record_id).toBe('');
    expect(wizard.state.value.shift_plan_id).toBe('');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.state.value.step_state['series-exceptions'].completed).toBe(false);
  });

  it('keeps the customer id stable when a saved-context patch tries to change it', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      customer_id: 'customer-2',
      order_id: 'order-1',
    });

    expect(wizard.state.value.customer_id).toBe('customer-1');
    expect(wizard.state.value.order_id).toBe('order-1');
  });

  it('clears wizard state on cancel/reset', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
    });
    wizard.setStepUiState('order-details', { dirty: true, error: 'problem' });

    wizard.resetWizard();

    expect(wizard.state.value.customer_id).toBe('');
    expect(wizard.state.value.order_id).toBe('');
    expect(wizard.state.value.current_step).toBe('order-details');
    expect(wizard.state.value.step_state['order-details'].dirty).toBe(false);
  });

  it('invalidates downstream ids when the order changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
    });
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
    expect(wizard.state.value.current_step).toBe('order-details');
  });

  it('invalidates shift-plan and series ids when the planning record changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
    });
    wizard.setStepCompletion('planning-record-documents', true);
    wizard.setStepCompletion('shift-plan', true);
    wizard.setStepCompletion('series-exceptions', true);
    wizard.setCurrentStep('series-exceptions');

    wizard.setSavedContext({ planning_record_id: 'record-2' });

    expect(wizard.state.value.planning_record_id).toBe('record-2');
    expect(wizard.state.value.shift_plan_id).toBe('');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.state.value.current_step).toBe('order-details');
  });

  it('does not report handoff readiness before the full persisted chain exists', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      customer_id: 'customer-1',
      order_id: 'order-1',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
    });

    expect(wizard.isWizardCompleteEnoughForHandoff.value).toBe(false);

    wizard.setStepCompletion('series-exceptions', true);

    expect(wizard.isWizardCompleteEnoughForHandoff.value).toBe(false);
  });
});
