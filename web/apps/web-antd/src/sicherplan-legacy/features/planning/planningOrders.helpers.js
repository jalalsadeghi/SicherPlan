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
  // The product wording expects an account-manager/commercial role on P-02.
  // The current repo role model does not expose one yet, so `accounting` is
  // the nearest implemented commercial role and keeps full page capability.
  accounting: [
    "planning.order.read",
    "planning.order.write",
    "planning.record.read",
    "planning.record.write",
  ],
  controller_qm: [
    "planning.order.read",
    "planning.record.read",
  ],
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
    "errors.planning.planning_record.invalid_window": "planningInvalidWindow",
    "errors.planning.planning_record.order_window_mismatch": "planningOrderWindowMismatch",
    "errors.planning.planning_record.detail_mismatch": "planningDetailMismatch",
    "errors.planning.planning_record.detail_customer_mismatch": "planningDetailCustomerMismatch",
    "errors.planning.planning_record.parent_mismatch": "planningParentMismatch",
    "errors.planning.planning_record.parent_not_allowed": "planningParentNotAllowed",
    "errors.planning.planning_record.parent_window_mismatch": "planningParentWindowMismatch",
    "errors.planning.planning_record_attachment.scope_mismatch": "attachmentScopeMismatch",
    "errors.planning.dispatcher_user.not_found": "dispatcherNotFound",
    "errors.planning.event_venue.not_found": "eventVenueNotFound",
    "errors.planning.site.not_found": "siteNotFound",
    "errors.planning.trade_fair.not_found": "tradeFairNotFound",
    "errors.planning.trade_fair_zone.not_found": "tradeFairZoneNotFound",
    "errors.planning.patrol_route.not_found": "patrolRouteNotFound",
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

  if (entityKey === "event_venue") {
    const venueNo = typeof record.venue_no === "string" ? record.venue_no.trim() : "";
    const name = typeof record.name === "string" ? record.name.trim() : "";
    return [venueNo, name].filter(Boolean).join(" — ") || record.id || "";
  }

  if (entityKey === "site") {
    const siteNo = typeof record.site_no === "string" ? record.site_no.trim() : "";
    const name = typeof record.name === "string" ? record.name.trim() : "";
    return [siteNo, name].filter(Boolean).join(" — ") || record.id || "";
  }

  if (entityKey === "equipment_item") {
    const code = typeof record.code === "string" ? record.code.trim() : "";
    const label = typeof record.label === "string" ? record.label.trim() : "";
    return [code, label].filter(Boolean).join(" — ") || record.id || "";
  }

  if (entityKey === "trade_fair") {
    const fairNo = typeof record.fair_no === "string" ? record.fair_no.trim() : "";
    const name = typeof record.name === "string" ? record.name.trim() : "";
    return [fairNo, name].filter(Boolean).join(" — ") || record.id || "";
  }

  if (entityKey === "trade_fair_zone") {
    const zoneCode = typeof record.zone_code === "string" ? record.zone_code.trim() : "";
    const label = typeof record.label === "string" ? record.label.trim() : "";
    return [zoneCode, label].filter(Boolean).join(" — ") || record.id || "";
  }

  if (entityKey === "planning_record") {
    const name = typeof record.name === "string" ? record.name.trim() : "";
    const planningFrom = typeof record.planning_from === "string" ? record.planning_from.trim() : "";
    const planningTo = typeof record.planning_to === "string" ? record.planning_to.trim() : "";
    const windowLabel = [planningFrom, planningTo].filter(Boolean).join(" - ");
    return [name, windowLabel].filter(Boolean).join(" · ") || record.id || "";
  }

  if (entityKey === "dispatcher_user") {
    const fullName = typeof record.full_name === "string" ? record.full_name.trim() : "";
    const username = typeof record.username === "string" ? record.username.trim() : "";
    const email = typeof record.email === "string" ? record.email.trim() : "";
    return [fullName, username || email].filter(Boolean).join(" · ") || record.id || "";
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

export function filterPlanningOrderOptionsByScope(entityKey, records, customerId) {
  if (entityKey === "requirement_type" || entityKey === "equipment_item") {
    return records;
  }
  return filterPlanningOrderOptionsByCustomer(records, customerId);
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

export function validatePlanningRecordDraft(
  planningDraft,
  {
    orderServiceFrom = "",
    orderServiceTo = "",
    eventVenueOptions = [],
    siteOptions = [],
    tradeFairOptions = [],
    patrolRouteOptions = [],
  } = {},
) {
  const planningFrom = typeof planningDraft?.planning_from === "string" ? planningDraft.planning_from.trim() : "";
  const planningTo = typeof planningDraft?.planning_to === "string" ? planningDraft.planning_to.trim() : "";
  const planningMode = typeof planningDraft?.planning_mode_code === "string" ? planningDraft.planning_mode_code.trim() : "";
  const eventVenueId = normalizePlanningOrderUuidValue(planningDraft?.event_detail?.event_venue_id);
  const siteId = normalizePlanningOrderUuidValue(planningDraft?.site_detail?.site_id);
  const tradeFairId = normalizePlanningOrderUuidValue(planningDraft?.trade_fair_detail?.trade_fair_id);
  const patrolRouteId = normalizePlanningOrderUuidValue(planningDraft?.patrol_detail?.patrol_route_id);
  const orderWindowStart = typeof orderServiceFrom === "string" ? orderServiceFrom.trim() : "";
  const orderWindowEnd = typeof orderServiceTo === "string" ? orderServiceTo.trim() : "";

  const result = {
    planning_from: false,
    planning_to: false,
    planning_window: false,
    mode_detail: false,
    messageKey: null,
  };

  if (!planningFrom) {
    result.planning_from = true;
    result.messageKey = "planningFromRequired";
    return result;
  }
  if (!planningTo) {
    result.planning_to = true;
    result.messageKey = "planningToRequired";
    return result;
  }
  if (planningTo < planningFrom) {
    result.planning_from = true;
    result.planning_to = true;
    result.planning_window = true;
    result.messageKey = "planningInvalidWindow";
    return result;
  }
  if (orderWindowStart && orderWindowEnd && (planningFrom < orderWindowStart || planningTo > orderWindowEnd)) {
    result.planning_from = true;
    result.planning_to = true;
    result.planning_window = true;
    result.messageKey = "planningOrderWindowMismatch";
    return result;
  }

  if (planningMode === "event") {
    if (!Array.isArray(eventVenueOptions) || eventVenueOptions.length === 0) {
      result.mode_detail = true;
      result.messageKey = "eventVenueSetupBlocked";
      return result;
    }
    if (!eventVenueId) {
      result.mode_detail = true;
      result.messageKey = "eventVenueRequired";
      return result;
    }
  }

  if (planningMode === "site") {
    if (!Array.isArray(siteOptions) || siteOptions.length === 0) {
      result.mode_detail = true;
      result.messageKey = "siteSetupBlocked";
      return result;
    }
    if (!siteId) {
      result.mode_detail = true;
      result.messageKey = "siteRequired";
      return result;
    }
  }

  if (planningMode === "trade_fair") {
    if (!Array.isArray(tradeFairOptions) || tradeFairOptions.length === 0) {
      result.mode_detail = true;
      result.messageKey = "tradeFairSetupBlocked";
      return result;
    }
    if (!tradeFairId) {
      result.mode_detail = true;
      result.messageKey = "tradeFairRequired";
      return result;
    }
  }

  if (planningMode === "patrol") {
    if (!Array.isArray(patrolRouteOptions) || patrolRouteOptions.length === 0) {
      result.mode_detail = true;
      result.messageKey = "patrolRouteSetupBlocked";
      return result;
    }
    if (!patrolRouteId) {
      result.mode_detail = true;
      result.messageKey = "patrolRouteRequired";
      return result;
    }
  }

  return result;
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
