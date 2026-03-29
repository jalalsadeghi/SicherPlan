export const PLANNING_ORDER_PERMISSION_MATRIX = {
  platform_admin: [
    "planning.order.read",
    "planning.order.write",
    "planning.record.read",
    "planning.record.write",
  ],
  tenant_admin: [
    "planning.order.read",
    "planning.order.write",
    "planning.record.read",
    "planning.record.write",
  ],
  dispatcher: [
    "planning.order.read",
    "planning.order.write",
    "planning.record.read",
    "planning.record.write",
  ],
  accounting: [],
  controller_qm: [],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasPlanningOrderPermission(role, permissionKey) {
  return (PLANNING_ORDER_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function derivePlanningOrderActionState(role, selectedOrder, selectedPlanningRecord) {
  const canReadOrders = hasPlanningOrderPermission(role, "planning.order.read");
  const canWriteOrders = hasPlanningOrderPermission(role, "planning.order.write");
  const canReadPlanning = hasPlanningOrderPermission(role, "planning.record.read");
  const canWritePlanning = hasPlanningOrderPermission(role, "planning.record.write");
  return {
    canReadOrders,
    canWriteOrders,
    canReadPlanning,
    canWritePlanning,
    canCreateOrder: canWriteOrders,
    canEditOrder: canWriteOrders && !!selectedOrder,
    canTransitionOrder: canWriteOrders && !!selectedOrder,
    canManageOrderDocs: canWriteOrders && !!selectedOrder,
    canCreatePlanning: canWritePlanning && !!selectedOrder,
    canEditPlanning: canWritePlanning && !!selectedPlanningRecord,
    canTransitionPlanning: canWritePlanning && !!selectedPlanningRecord,
    canManagePlanningDocs: canWritePlanning && !!selectedPlanningRecord,
  };
}

export function mapPlanningOrderApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.planning.customer_order.not_found": "orderNotFound",
    "errors.planning.customer_order.duplicate_number": "orderDuplicateNumber",
    "errors.planning.customer_order.invalid_customer_id": "customerRequired",
    "errors.planning.customer_order.invalid_requirement_type_id": "requirementTypeRequired",
    "errors.planning.customer_order.stale_version": "staleVersion",
    "errors.planning.customer_order.invalid_release_transition": "invalidReleaseTransition",
    "errors.planning.requirement_type.duplicate_code": "planningSetupDuplicateCode",
    "errors.planning.patrol_route.duplicate_code": "planningSetupDuplicateCode",
    "errors.planning.order_attachment.scope_mismatch": "attachmentScopeMismatch",
    "errors.planning.planning_record.not_found": "planningNotFound",
    "errors.planning.planning_record.duplicate_name": "planningDuplicateName",
    "errors.planning.planning_record.stale_version": "staleVersion",
    "errors.planning.planning_record.invalid_release_transition": "invalidReleaseTransition",
    "errors.planning.planning_record.detail_mismatch": "planningDetailMismatch",
    "errors.planning.planning_record.detail_customer_mismatch": "planningDetailCustomerMismatch",
    "errors.planning.planning_record.parent_not_allowed": "planningParentNotAllowed",
    "errors.planning.planning_record.parent_window_mismatch": "planningParentWindowMismatch",
    "errors.planning.planning_record_attachment.scope_mismatch": "attachmentScopeMismatch",
    "errors.planning.dispatcher_user.not_found": "dispatcherNotFound",
    "errors.planning.commercial_link.prerequisites_missing": "commercialPrerequisitesMissing",
  };
  return map[messageKey] ?? "error";
}

export function planningModeLabel(modeCode) {
  switch (modeCode) {
    case "event":
      return "event";
    case "site":
      return "site";
    case "trade_fair":
      return "tradeFair";
    case "patrol":
      return "patrol";
    default:
      return "unknown";
  }
}

export function formatPlanningOrderReferenceOption(entityKey, record) {
  if (!record || typeof record !== "object") {
    return "";
  }

  if (entityKey === "requirement_type") {
    const code = typeof record.code === "string" ? record.code.trim() : "";
    const label = typeof record.label === "string" ? record.label.trim() : "";
    return [code, label].filter(Boolean).join(" — ") || record.id || "";
  }

  if (entityKey === "patrol_route") {
    const routeNo = typeof record.route_no === "string" ? record.route_no.trim() : "";
    const name = typeof record.name === "string" ? record.name.trim() : "";
    return [routeNo, name].filter(Boolean).join(" — ") || record.id || "";
  }

  return typeof record.name === "string" && record.name.trim()
    ? record.name.trim()
    : record.id || "";
}

export function filterPlanningOrderOptionsByCustomer(records, customerId) {
  if (!customerId) {
    return records;
  }
  return records.filter((record) => record?.customer_id === customerId);
}

export function normalizePlanningOrderUuidValue(value) {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized ? normalized : null;
}

export function validatePlanningOrderDraft(orderDraft) {
  return {
    customer_id: !normalizePlanningOrderUuidValue(orderDraft?.customer_id),
    requirement_type_id: !normalizePlanningOrderUuidValue(orderDraft?.requirement_type_id),
  };
}

export function hasPlanningOrderSetupGap({ customerId, options, loading, error }) {
  return Boolean(customerId) && !loading && !error && Array.isArray(options) && options.length === 0;
}

export function derivePlanningOrderSubmitBlockReason(orderDraft, { requirementTypeSetupMissing = false } = {}) {
  const validation = validatePlanningOrderDraft(orderDraft);
  if (validation.customer_id) {
    return "customerRequired";
  }
  if (requirementTypeSetupMissing) {
    return "requirementTypeSetupBlocked";
  }
  if (validation.requirement_type_id) {
    return "requirementTypeRequired";
  }
  return null;
}

export function buildPlanningSetupLocation(entityKey, customerId = "") {
  const query = { entity: entityKey };
  if (customerId) {
    query.customer_id = customerId;
  }
  return {
    path: "/admin/planning",
    query,
  };
}

export function mapPlanningCommercialIssueCode(code) {
  const normalizedCode = typeof code === "string" ? code.trim() : "";
  const issueMap = {
    missing_billing_profile: "commercialIssueMissingBillingProfile",
    missing_default_invoice_party: "commercialIssueMissingDefaultInvoiceParty",
    missing_shipping_method: "commercialIssueMissingShippingMethod",
    missing_invoice_layout: "commercialIssueMissingInvoiceLayout",
    missing_active_rate_card: "commercialIssueMissingActiveRateCard",
  };
  if (issueMap[normalizedCode]) {
    return issueMap[normalizedCode];
  }
  if (!normalizedCode) {
    return "commercialIssueFallback";
  }
  return null;
}

export function formatPlanningCommercialIssueFallback(code) {
  const normalizedCode = typeof code === "string" ? code.trim() : "";
  if (!normalizedCode) {
    return "";
  }
  return normalizedCode
    .split("_")
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}

export function buildCustomerCommercialLocation(customerId = "") {
  const query = { tab: "commercial" };
  if (customerId) {
    query.customer_id = customerId;
  }
  return {
    path: "/admin/customers",
    query,
  };
}
