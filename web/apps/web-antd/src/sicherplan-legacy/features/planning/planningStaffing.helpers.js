export const PLANNING_STAFFING_PERMISSION_MATRIX = {
  platform_admin: ["planning.staffing.read", "planning.staffing.write", "planning.staffing.override"],
  tenant_admin: ["planning.staffing.read", "planning.staffing.write", "planning.staffing.override"],
  dispatcher: ["planning.staffing.read", "planning.staffing.write", "planning.staffing.override"],
  accounting: [],
  controller_qm: [],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasPlanningStaffingPermission(role, permissionKey) {
  return (PLANNING_STAFFING_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function derivePlanningStaffingActionState(role, selectedShift, selectedAssignment, selectedIssue) {
  const canReadCoverage = hasPlanningStaffingPermission(role, "planning.staffing.read");
  const canWriteStaffing = hasPlanningStaffingPermission(role, "planning.staffing.write");
  const canOverrideValidation = hasPlanningStaffingPermission(role, "planning.staffing.override");
  return {
    canReadCoverage,
    canWriteStaffing,
    canOverrideValidation,
    canRefresh: canReadCoverage,
    canInspectDetails: canReadCoverage && !!selectedShift,
    canInspectAssignments: canReadCoverage && !!selectedAssignment,
    canRecordOverride: canOverrideValidation && !!selectedAssignment && !!selectedIssue && selectedIssue.override_allowed === true,
    canManageRelease: canWriteStaffing && !!selectedShift,
    canDispatch: canWriteStaffing && !!selectedShift,
  };
}

export function mapPlanningStaffingApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.planning.staffing.scope_mismatch": "scopeMismatch",
    "errors.planning.assignment.blocked_by_validation": "assignmentBlocked",
    "errors.planning.assignment_validation.override_not_allowed": "overrideNotAllowed",
    "errors.planning.assignment_validation.rule_not_found": "ruleNotFound",
    "errors.planning.shift.blocked_by_validation": "releaseBlocked",
    "errors.planning.shift.visibility_requires_release": "visibilityRequiresRelease",
    "errors.planning.output.release_required": "outputReleaseRequired",
    "errors.planning.communication.release_required": "dispatchReleaseRequired",
    "errors.planning.communication.no_recipients": "dispatchNoRecipients",
  };
  return map[messageKey] ?? "error";
}

export function coverageTone(coverageState) {
  switch (coverageState) {
    case "green":
      return "good";
    case "yellow":
      return "warn";
    default:
      return "bad";
  }
}

export function validationTone(severity) {
  switch (severity) {
    case "block":
      return "bad";
    case "warn":
      return "warn";
    default:
      return "neutral";
  }
}

export function summarizeCoverage(rows) {
  return rows.reduce(
    (summary, row) => {
      summary.total += 1;
      if (row.coverage_state === "green") {
        summary.green += 1;
      } else if (row.coverage_state === "yellow") {
        summary.yellow += 1;
      } else {
        summary.red += 1;
      }
      return summary;
    },
    { green: 0, red: 0, total: 0, yellow: 0 },
  );
}

export function summarizeValidations(result) {
  const summary = { blocking: 0, warnings: 0, infos: 0, overrideable: 0 };
  if (!result?.issues) {
    return summary;
  }
  for (const issue of result.issues) {
    if (issue.severity === "block") {
      summary.blocking += 1;
    } else if (issue.severity === "warn") {
      summary.warnings += 1;
    } else {
      summary.infos += 1;
    }
    if (issue.override_allowed) {
      summary.overrideable += 1;
    }
  }
  return summary;
}

export function actorLabel(assignment) {
  if (!assignment) {
    return "";
  }
  if (assignment.employee_id) {
    return `employee:${assignment.employee_id}`;
  }
  if (assignment.subcontractor_worker_id) {
    return `worker:${assignment.subcontractor_worker_id}`;
  }
  return "unassigned";
}

export function releaseTone(releaseState) {
  if (releaseState === "released") {
    return "good";
  }
  if (releaseState === "release_ready") {
    return "warn";
  }
  return "neutral";
}

export function dispatchAudienceLabel(audienceCode) {
  const map = {
    assigned_employees: "employees",
    teams: "teams",
    subcontractor_release: "subcontractors",
  };
  return map[audienceCode] ?? audienceCode;
}
