export const CUSTOMER_PERMISSION_MATRIX = {
  platform_admin: ["customers.customer.read", "customers.customer.write"],
  tenant_admin: [
    "customers.customer.read",
    "customers.customer.write",
    "customers.portal_access.read",
    "customers.portal_access.write",
  ],
  dispatcher: ["customers.customer.read"],
  accounting: ["customers.customer.read"],
  controller_qm: ["customers.customer.read"],
  customer_user: [],
  subcontractor_user: [],
};

export const CUSTOMER_DETAIL_TAB_ORDER = [
  "overview",
  "contacts",
  "addresses",
  "commercial",
  "portal",
  "history",
  "employee_blocks",
];

export const CUSTOMER_COMMERCIAL_TAB_ORDER = [
  "billing_profile",
  "invoice_parties",
  "pricing_rules",
];

export function hasCustomerPermission(role, permissionKey) {
  return (CUSTOMER_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function resolveCustomerAdminSectionVisibility({ effectiveRole, embedded = false }) {
  const isTenantAdminEmbedded = embedded && effectiveRole === "tenant_admin";

  return {
    showGovernanceHero: !isTenantAdminEmbedded,
  };
}

export function resolveCustomerAdminSessionScope({
  effectiveAccessToken,
  effectiveRole,
  effectiveTenantScopeId,
  storedAccessToken,
}) {
  if (effectiveRole === "tenant_admin") {
    return {
      accessToken: typeof effectiveAccessToken === "string" ? effectiveAccessToken.trim() : "",
      tenantScopeId: typeof effectiveTenantScopeId === "string" ? effectiveTenantScopeId.trim() : "",
    };
  }

  return {
    accessToken: typeof storedAccessToken === "string" ? storedAccessToken.trim() : "",
    tenantScopeId: typeof effectiveTenantScopeId === "string" ? effectiveTenantScopeId.trim() : "",
  };
}

export function deriveCustomerActionState(role, selectedCustomer) {
  const canRead = hasCustomerPermission(role, "customers.customer.read");
  const canWrite = hasCustomerPermission(role, "customers.customer.write");
  const customerStatus = selectedCustomer?.status ?? "active";
  const archivedAt = selectedCustomer?.archived_at ?? null;

  return {
    canRead,
    canCreate: canWrite,
    canEdit: canWrite && !!selectedCustomer,
    canManageContacts: canWrite && !!selectedCustomer,
    canManageAddresses: canWrite && !!selectedCustomer,
    canDeactivate: canWrite && customerStatus === "active" && !archivedAt,
    canReactivate: canWrite && customerStatus === "inactive" && !archivedAt,
    canArchive: canWrite && !!selectedCustomer && !archivedAt,
  };
}

export function buildLifecyclePayload(customer, nextStatus) {
  const archivedAt = nextStatus === "archived" ? new Date().toISOString() : null;

  return {
    status: nextStatus,
    archived_at: archivedAt,
    version_no: customer.version_no,
  };
}

export function formatPrimaryContactSummary(customer) {
  const primaryContact = customer?.contacts?.find((contact) => contact.is_primary_contact);
  if (!primaryContact) {
    return "";
  }

  return [primaryContact.full_name, primaryContact.email].filter(Boolean).join(" · ");
}

export function formatCustomerReferenceLabel(record) {
  if (!record) {
    return "";
  }

  if ("name" in record && record.name) {
    return [record.code, record.name].filter(Boolean).join(" - ");
  }

  return [record.code, record.label].filter(Boolean).join(" - ");
}

export function filterCustomerMandatesByBranch(mandates, branchId) {
  const normalizedBranchId = typeof branchId === "string" ? branchId.trim() : "";
  if (!normalizedBranchId) {
    return [...(mandates ?? [])];
  }
  return (mandates ?? []).filter((mandate) => mandate.branch_id === normalizedBranchId);
}

export function buildCustomerReferenceMaps(referenceData) {
  const buildMap = (items) => new Map((items ?? []).map((item) => [item.id, formatCustomerReferenceLabel(item)]));

  return {
    legalForms: buildMap(referenceData?.legal_forms),
    classifications: buildMap(referenceData?.classifications),
    rankings: buildMap(referenceData?.rankings),
    customerStatuses: buildMap(referenceData?.customer_statuses),
    branches: buildMap(referenceData?.branches),
    mandates: buildMap(referenceData?.mandates),
  };
}

export function buildCustomerDraftPayload(draft, { allowedBranchIds = null, allowedMandateIds = null } = {}) {
  const emptyToNull = (value) => {
    if (typeof value !== "string") {
      return value ?? null;
    }
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  };
  const normalizeReference = (value, allowedIds) => {
    const normalized = emptyToNull(value);
    if (normalized == null) {
      return null;
    }
    if (Array.isArray(allowedIds)) {
      return allowedIds.includes(normalized) ? normalized : null;
    }
    return normalized;
  };

  return {
    tenant_id: draft.tenant_id,
    customer_number: draft.customer_number.trim(),
    name: draft.name.trim(),
    status: emptyToNull(draft.status) ?? "active",
    legal_name: emptyToNull(draft.legal_name),
    external_ref: emptyToNull(draft.external_ref),
    legal_form_lookup_id: emptyToNull(draft.legal_form_lookup_id),
    classification_lookup_id: emptyToNull(draft.classification_lookup_id),
    ranking_lookup_id: emptyToNull(draft.ranking_lookup_id),
    customer_status_lookup_id: emptyToNull(draft.customer_status_lookup_id),
    default_branch_id: normalizeReference(draft.default_branch_id, allowedBranchIds),
    default_mandate_id: normalizeReference(draft.default_mandate_id, allowedMandateIds),
    notes: emptyToNull(draft.notes),
  };
}

export function resolveCustomerCancelSelection(previousSelectedCustomer) {
  return previousSelectedCustomer
    ? { isCreatingCustomer: false, selectedCustomerId: previousSelectedCustomer.id, selectedCustomer: previousSelectedCustomer }
    : { isCreatingCustomer: false, selectedCustomerId: "", selectedCustomer: null };
}

export function buildCustomerDetailTabs({ canReadCommercial, hasSelectedCustomer, isCreatingCustomer }) {
  if (isCreatingCustomer) {
    return ["overview"];
  }

  if (!hasSelectedCustomer) {
    return [];
  }

  return CUSTOMER_DETAIL_TAB_ORDER.filter((tabId) => tabId !== "commercial" || !!canReadCommercial);
}

export function normalizeCustomerDetailTab(activeTab, options) {
  const tabs = buildCustomerDetailTabs(options);
  if (!tabs.length) {
    return "";
  }

  return tabs.includes(activeTab) ? activeTab : "overview";
}

export function normalizeCustomerCommercialTab(activeTab) {
  return CUSTOMER_COMMERCIAL_TAB_ORDER.includes(activeTab) ? activeTab : "billing_profile";
}

export function mapCustomerApiMessage(messageKey) {
  const messageMap = {
    "errors.iam.auth.invalid_access_token": "customerAdmin.feedback.authRequired",
    "errors.iam.authorization.permission_denied": "customerAdmin.feedback.permissionDenied",
    "errors.iam.authorization.scope_denied": "customerAdmin.feedback.permissionDenied",
    "errors.customers.customer.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.contact.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.customer_address.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.history_entry.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.employee_block.not_found": "customerAdmin.feedback.notFound",
    "errors.customers.customer.duplicate_number": "customerAdmin.feedback.duplicateNumber",
    "errors.customers.customer.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.customer.invalid_initial_status": "customerAdmin.feedback.invalidInitialStatus",
    "errors.customers.customer.invalid_branch_scope": "customerAdmin.feedback.invalidBranchScope",
    "errors.customers.customer.invalid_mandate_scope": "customerAdmin.feedback.invalidMandateScope",
    "errors.customers.customer.mandate_branch_mismatch": "customerAdmin.feedback.mandateBranchMismatch",
    "errors.customers.contact.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.address_link.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.employee_block.stale_version": "customerAdmin.feedback.staleVersion",
    "errors.customers.contact.duplicate_email": "customerAdmin.feedback.duplicateEmail",
    "errors.customers.contact.primary_conflict": "customerAdmin.feedback.primaryConflict",
    "errors.customers.customer_address.default_conflict": "customerAdmin.feedback.defaultAddressConflict",
    "errors.customers.contact.invalid_user_id_format": "customerAdmin.feedback.invalidPortalUserFormat",
    "errors.customers.contact.invalid_user_scope": "customerAdmin.feedback.invalidPortalUser",
    "errors.customers.portal_access.contact_already_linked": "customerAdmin.feedback.portalAccessAlreadyLinked",
    "errors.customers.portal_access.contact_customer_mismatch": "customerAdmin.feedback.portalAccessContactMismatch",
    "errors.customers.portal.contact_inactive": "customerAdmin.feedback.portalAccessContactInactive",
    "errors.customers.portal.customer_inactive": "customerAdmin.feedback.portalAccessCustomerInactive",
  };

  return messageMap[messageKey] ?? "customerAdmin.feedback.error";
}
