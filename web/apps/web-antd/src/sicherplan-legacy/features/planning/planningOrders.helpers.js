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
    "errors.planning.customer_order.stale_version": "staleVersion",
    "errors.planning.customer_order.invalid_release_transition": "invalidReleaseTransition",
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
