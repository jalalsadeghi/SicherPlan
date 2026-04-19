import type { CustomerNewPlanWizardStepId } from './new-plan-wizard.types';

const WIZARD_DRAFT_STORAGE_PREFIX = 'sicherplan.customerNewPlanWizardDraft';
const EMPTY_KEY_SEGMENT = '_';

export interface CustomerNewPlanWizardDraftContext {
  customerId: string;
  planningEntityId?: null | string;
  planningEntityType?: null | string;
  tenantId: string;
}

function getSessionStorage() {
  if (typeof window === 'undefined') {
    return null;
  }
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

function normalizeKeySegment(value: null | string | undefined) {
  const normalized = typeof value === 'string' ? value.trim() : '';
  return normalized || EMPTY_KEY_SEGMENT;
}

export function buildWizardDraftStorageKey(
  context: CustomerNewPlanWizardDraftContext,
  stepId: CustomerNewPlanWizardStepId,
) {
  return [
    WIZARD_DRAFT_STORAGE_PREFIX,
    normalizeKeySegment(context.tenantId),
    normalizeKeySegment(context.customerId),
    normalizeKeySegment(context.planningEntityType),
    normalizeKeySegment(context.planningEntityId),
    stepId,
  ].join(':');
}

export function saveWizardDraft<T>(
  context: CustomerNewPlanWizardDraftContext,
  stepId: CustomerNewPlanWizardStepId,
  payload: null | T | undefined,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  const storageKey = buildWizardDraftStorageKey(context, stepId);
  if (payload == null) {
    storage.removeItem(storageKey);
    return;
  }
  try {
    const serialized = JSON.stringify(payload);
    if (!serialized || serialized === '{}' || serialized === '[]' || serialized === 'null') {
      storage.removeItem(storageKey);
      return;
    }
    storage.setItem(storageKey, serialized);
  } catch {
    storage.removeItem(storageKey);
  }
}

export function loadWizardDraft<T>(
  context: CustomerNewPlanWizardDraftContext,
  stepId: CustomerNewPlanWizardStepId,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return null as null | T;
  }
  const storageKey = buildWizardDraftStorageKey(context, stepId);
  const raw = storage.getItem(storageKey);
  if (!raw) {
    return null as null | T;
  }
  try {
    return JSON.parse(raw) as T;
  } catch {
    storage.removeItem(storageKey);
    return null as null | T;
  }
}

export function clearWizardDraft(
  context: CustomerNewPlanWizardDraftContext,
  stepId: CustomerNewPlanWizardStepId,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(buildWizardDraftStorageKey(context, stepId));
}

export function clearAllWizardDraftsForCurrentContext(context: CustomerNewPlanWizardDraftContext) {
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  const prefix = [
    WIZARD_DRAFT_STORAGE_PREFIX,
    normalizeKeySegment(context.tenantId),
    normalizeKeySegment(context.customerId),
    normalizeKeySegment(context.planningEntityType),
    normalizeKeySegment(context.planningEntityId),
  ].join(':');
  const keysToDelete: string[] = [];
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (key?.startsWith(prefix)) {
      keysToDelete.push(key);
    }
  }
  for (const key of keysToDelete) {
    storage.removeItem(key);
  }
}
