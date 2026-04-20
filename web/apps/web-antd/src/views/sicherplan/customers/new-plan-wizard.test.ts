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
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
    });
    wizard.setSavedContext({
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
    expect(wizard.state.value.current_step).toBe('planning-record-overview');
  });

  it('invalidates shift-plan and series ids when the planning record changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setSavedContext({
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
    });
    wizard.setSavedContext({
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
    expect(wizard.state.value.current_step).toBe('shift-plan');
  });

  it('stores shift_plan_id, unlocks series-exceptions, and clears series_id when the shift plan changes', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'shift-plan');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_record_id: 'record-1',
      series_id: 'series-1',
    });
    wizard.setCurrentStep('shift-plan');
    wizard.setStepCompletion('shift-plan', true);

    wizard.setSavedContext({ shift_plan_id: 'shift-plan-1' });

    expect(wizard.state.value.shift_plan_id).toBe('shift-plan-1');
    expect(wizard.state.value.series_id).toBe('');
    expect(wizard.canEnterStep('series-exceptions')).toBe(true);
    expect(wizard.moveNext()).toBe('series-exceptions');
    expect(wizard.state.value.current_step).toBe('series-exceptions');
  });

  it('preserves a newly saved planning_record_id when the planning context changes in the same patch', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning-record-overview');
    wizard.setSavedContext({ order_id: 'order-1' });
    wizard.setCurrentStep('planning-record-overview');
    wizard.setStepCompletion('planning-record-overview', true);

    wizard.setSavedContext({
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
    });

    expect(wizard.state.value.planning_entity_type).toBe('site');
    expect(wizard.state.value.planning_entity_id).toBe('site-1');
    expect(wizard.state.value.planning_mode_code).toBe('site');
    expect(wizard.state.value.planning_record_id).toBe('record-1');
    expect(wizard.canEnterStep('planning-record-documents')).toBe(true);
    expect(wizard.moveNext()).toBe('planning-record-documents');
    expect(wizard.state.value.current_step).toBe('planning-record-documents');
  });

  it('preserves planning_record_id when order_id and planning_record_id are restored together', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_record_id: 'record-1',
    });

    expect(wizard.state.value.order_id).toBe('order-1');
    expect(wizard.state.value.planning_record_id).toBe('record-1');
    expect(wizard.canEnterStep('planning-record-documents')).toBe(true);
  });

  it('preserves shift_plan_id when planning_record_id and shift_plan_id are restored together', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning-record-documents');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_record_id: 'record-1',
    });

    wizard.setSavedContext({
      planning_record_id: 'record-2',
      shift_plan_id: 'shift-plan-1',
    });

    expect(wizard.state.value.planning_record_id).toBe('record-2');
    expect(wizard.state.value.shift_plan_id).toBe('shift-plan-1');
    expect(wizard.canEnterStep('series-exceptions')).toBe(true);
  });

  it('preserves series_id when shift_plan_id and series_id are restored together', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'shift-plan');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_record_id: 'record-1',
    });

    wizard.setSavedContext({
      shift_plan_id: 'shift-plan-1',
      series_id: 'series-1',
    });

    expect(wizard.state.value.shift_plan_id).toBe('shift-plan-1');
    expect(wizard.state.value.series_id).toBe('series-1');
    expect(wizard.canEnterStep('series-exceptions')).toBe(true);
    expect(wizard.applyRequestedStep('series-exceptions')).toBe('series-exceptions');
    expect(wizard.state.value.current_step).toBe('series-exceptions');
  });

  it('preserves planning_record_id and shift_plan_id when order_id, planning_record_id, and shift_plan_id are restored together', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');

    wizard.setSavedContext({
      order_id: 'order-1',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
    });

    expect(wizard.state.value.order_id).toBe('order-1');
    expect(wizard.state.value.planning_record_id).toBe('record-1');
    expect(wizard.state.value.shift_plan_id).toBe('shift-plan-1');
    expect(wizard.canEnterStep('series-exceptions')).toBe(true);
  });

  it('preserves planning context, planning_record_id, and shift_plan_id when restored atomically', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'planning-record-overview');
    wizard.setSavedContext({ order_id: 'order-1' });

    wizard.setSavedContext({
      planning_entity_id: 'site-1',
      planning_entity_type: 'site',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
      shift_plan_id: 'shift-plan-1',
    });

    expect(wizard.state.value.planning_entity_id).toBe('site-1');
    expect(wizard.state.value.planning_entity_type).toBe('site');
    expect(wizard.state.value.planning_mode_code).toBe('site');
    expect(wizard.state.value.planning_record_id).toBe('record-1');
    expect(wizard.state.value.shift_plan_id).toBe('shift-plan-1');
    expect(wizard.canEnterStep('series-exceptions')).toBe(true);
    expect(wizard.applyRequestedStep('series-exceptions')).toBe('series-exceptions');
    expect(wizard.state.value.current_step).toBe('series-exceptions');
  });

  it('clears planning_record_id when only planning context changes without a new planning record id', () => {
    const wizard = useCustomerNewPlanWizard();

    wizard.resetForCustomer('customer-1', 'order-details');
    wizard.setSavedContext({
      order_id: 'order-1',
      planning_entity_type: 'site',
      planning_entity_id: 'site-1',
      planning_mode_code: 'site',
      planning_record_id: 'record-1',
    });

    wizard.setSavedContext({
      planning_entity_type: 'trade_fair',
      planning_entity_id: 'fair-1',
      planning_mode_code: 'trade_fair',
    });

    expect(wizard.state.value.planning_entity_type).toBe('trade_fair');
    expect(wizard.state.value.planning_entity_id).toBe('fair-1');
    expect(wizard.state.value.planning_mode_code).toBe('trade_fair');
    expect(wizard.state.value.planning_record_id).toBe('');
    expect(wizard.state.value.shift_plan_id).toBe('');
    expect(wizard.state.value.series_id).toBe('');
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

    expect(wizard.isWizardCompleteEnoughForHandoff.value).toBe(true);
  });
});
