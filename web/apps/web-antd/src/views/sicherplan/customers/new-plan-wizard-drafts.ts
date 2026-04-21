import type { CustomerNewPlanWizardDraftStepId } from './new-plan-wizard.types';

const WIZARD_DRAFT_STORAGE_PREFIX = 'sicherplan.customerNewPlanWizardDraft';
const EMPTY_KEY_SEGMENT = '_';
const ORDER_DETAILS_EDIT_KEY_SEGMENT = 'order-details-edit';

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
  stepId: CustomerNewPlanWizardDraftStepId,
) {
  if (stepId === 'order-details') {
    return [
      WIZARD_DRAFT_STORAGE_PREFIX,
      normalizeKeySegment(context.tenantId),
      normalizeKeySegment(context.customerId),
      stepId,
    ].join(':');
  }
  return [
    WIZARD_DRAFT_STORAGE_PREFIX,
    normalizeKeySegment(context.tenantId),
    normalizeKeySegment(context.customerId),
    normalizeKeySegment(context.planningEntityType),
    normalizeKeySegment(context.planningEntityId),
    stepId,
  ].join(':');
}

export function buildOrderDetailsEditDraftStorageKey(
  context: CustomerNewPlanWizardDraftContext,
  orderId: string,
) {
  return [
    WIZARD_DRAFT_STORAGE_PREFIX,
    normalizeKeySegment(context.tenantId),
    normalizeKeySegment(context.customerId),
    ORDER_DETAILS_EDIT_KEY_SEGMENT,
    normalizeKeySegment(orderId),
  ].join(':');
}

export function saveWizardDraft<T>(
  context: CustomerNewPlanWizardDraftContext,
  stepId: CustomerNewPlanWizardDraftStepId,
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
  stepId: CustomerNewPlanWizardDraftStepId,
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
  stepId: CustomerNewPlanWizardDraftStepId,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(buildWizardDraftStorageKey(context, stepId));
}

export function loadWizardDraftCandidatesForCustomer<T>(
  context: Pick<CustomerNewPlanWizardDraftContext, 'customerId' | 'tenantId'>,
  stepId: CustomerNewPlanWizardDraftStepId,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return [] as T[];
  }
  const customerPrefix = [
    WIZARD_DRAFT_STORAGE_PREFIX,
    normalizeKeySegment(context.tenantId),
    normalizeKeySegment(context.customerId),
  ].join(':');
  const suffix = `:${stepId}`;
  const matches: T[] = [];
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (!key?.startsWith(customerPrefix) || !key.endsWith(suffix)) {
      continue;
    }
    const raw = storage.getItem(key);
    if (!raw) {
      continue;
    }
    try {
      matches.push(JSON.parse(raw) as T);
    } catch {
      storage.removeItem(key);
    }
  }
  return matches;
}

export function saveOrderDetailsEditDraft<T>(
  context: CustomerNewPlanWizardDraftContext,
  orderId: string,
  payload: null | T | undefined,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  const storageKey = buildOrderDetailsEditDraftStorageKey(context, orderId);
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

export function loadOrderDetailsEditDraft<T>(
  context: CustomerNewPlanWizardDraftContext,
  orderId: string,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return null as null | T;
  }
  const storageKey = buildOrderDetailsEditDraftStorageKey(context, orderId);
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

export function clearOrderDetailsEditDraft(
  context: CustomerNewPlanWizardDraftContext,
  orderId: string,
) {
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  storage.removeItem(buildOrderDetailsEditDraftStorageKey(context, orderId));
}

export function clearAllWizardDraftsForCurrentContext(context: CustomerNewPlanWizardDraftContext) {
  const storage = getSessionStorage();
  if (!storage) {
    return;
  }
  const scopedPrefix = [
    WIZARD_DRAFT_STORAGE_PREFIX,
    normalizeKeySegment(context.tenantId),
    normalizeKeySegment(context.customerId),
    normalizeKeySegment(context.planningEntityType),
    normalizeKeySegment(context.planningEntityId),
  ].join(':');
  const customerPrefix = [
    WIZARD_DRAFT_STORAGE_PREFIX,
    normalizeKeySegment(context.tenantId),
    normalizeKeySegment(context.customerId),
  ].join(':');
  const keysToDelete: string[] = [];
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (
      key?.startsWith(scopedPrefix) ||
      key === `${customerPrefix}:order-details` ||
      key?.startsWith(`${customerPrefix}:${ORDER_DETAILS_EDIT_KEY_SEGMENT}:`)
    ) {
      keysToDelete.push(key);
    }
  }
  for (const key of keysToDelete) {
    storage.removeItem(key);
  }
}
