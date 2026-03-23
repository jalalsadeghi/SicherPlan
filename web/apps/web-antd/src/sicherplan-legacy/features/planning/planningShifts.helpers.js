export const PLANNING_SHIFT_PERMISSION_MATRIX = {
  platform_admin: ["planning.shift.read", "planning.shift.write"],
  tenant_admin: ["planning.shift.read", "planning.shift.write"],
  dispatcher: ["planning.shift.read", "planning.shift.write"],
  accounting: [],
  controller_qm: [],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasPlanningShiftPermission(role, permissionKey) {
  return (PLANNING_SHIFT_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function derivePlanningShiftActionState(role, selectedShiftPlan, selectedSeries, selectedShift) {
  const canRead = hasPlanningShiftPermission(role, "planning.shift.read");
  const canWrite = hasPlanningShiftPermission(role, "planning.shift.write");
  return {
    canRead,
    canWrite,
    canCreateTemplate: canWrite,
    canCreatePlan: canWrite,
    canEditPlan: canWrite && !!selectedShiftPlan,
    canCreateSeries: canWrite && !!selectedShiftPlan,
    canEditSeries: canWrite && !!selectedSeries,
    canGenerateSeries: canWrite && !!selectedSeries,
    canManageExceptions: canWrite && !!selectedSeries,
    canCreateShift: canWrite && !!selectedShiftPlan,
    canEditShift: canWrite && !!selectedShift,
    canCopy: canWrite && !!selectedShiftPlan,
  };
}

export function mapPlanningShiftApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.planning.shift_template.duplicate_code": "templateDuplicateCode",
    "errors.planning.shift_template.invalid_time_range": "templateInvalidTimeRange",
    "errors.planning.shift_plan.invalid_workforce_scope": "invalidWorkforceScope",
    "errors.planning.shift_plan.record_window_mismatch": "planWindowMismatch",
    "errors.planning.shift_series.invalid_weekday_mask": "invalidWeekdayMask",
    "errors.planning.shift_series.invalid_timezone": "invalidTimezone",
    "errors.planning.shift_series_exception.override_times_required": "exceptionOverrideRequired",
    "errors.planning.shift.duplicate_window": "shiftDuplicateWindow",
    "errors.planning.shift.copy.duplicate_conflict": "copyDuplicateConflict",
    "errors.planning.shift_board.invalid_window": "invalidBoardWindow",
  };
  return map[messageKey] ?? "error";
}

export function visibilitySummary(shift) {
  return {
    customer: Boolean(shift.customer_visible_flag),
    subcontractor: Boolean(shift.subcontractor_visible_flag),
    stealth: Boolean(shift.stealth_mode_flag),
  };
}

export function recurrenceLabel(code) {
  switch (code) {
    case "daily":
      return "daily";
    case "weekly":
      return "weekly";
    default:
      return "unknown";
  }
}
