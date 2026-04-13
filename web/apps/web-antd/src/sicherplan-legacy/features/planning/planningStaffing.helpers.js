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
    canAssign: canWriteStaffing && !!selectedShift,
    canUnassign: canWriteStaffing && !!selectedAssignment,
    canSubstitute: canWriteStaffing && !!selectedAssignment,
    canInspectTeams: canReadCoverage && !!selectedShift,
    canInspectSubcontractorReleases: canReadCoverage && !!selectedShift,
  };
}

export function mapPlanningStaffingApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.planning.staffing.scope_mismatch": "scopeMismatch",
    "errors.planning.assignment.blocked_by_validation": "assignmentBlocked",
    "errors.planning.assignment.stale_version": "assignmentStaleVersion",
    "errors.planning.team_member.invalid_actor_choice": "error",
    "errors.planning.team_member.duplicate_lead": "error",
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
    case "setup_required":
      return "bad";
    default:
      return "bad";
  }
}

export function resolvePlanningStaffingCoverageState(coverageState, demandGroups) {
  if (!Array.isArray(demandGroups) || demandGroups.length === 0) {
    return "setup_required";
  }
  return coverageState;
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
      const resolvedState = resolvePlanningStaffingCoverageState(row.coverage_state, row.demand_groups);
      summary.total += 1;
      if (resolvedState === "green") {
        summary.green += 1;
      } else if (resolvedState === "yellow") {
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

export function buildStaffingMemberOptions(teamMembers, teamId) {
  return (teamMembers || []).filter((member) => !teamId || member.team_id === teamId);
}

export function resolvePlanningStaffingCatalogLabel(options, id) {
  if (!id) {
    return "";
  }
  const option = (options || []).find((row) => row?.id === id);
  return option?.label || option?.code || id;
}

export function formatPlanningStaffingDemandGroupLabel(group, functionTypeOptions, qualificationTypeOptions) {
  if (!group) {
    return "";
  }
  const functionLabel = resolvePlanningStaffingCatalogLabel(functionTypeOptions, group.function_type_id);
  const qualificationLabel = resolvePlanningStaffingCatalogLabel(qualificationTypeOptions, group.qualification_type_id);
  return [functionLabel, qualificationLabel].filter(Boolean).join(" · ");
}

export function resolveSelectedDemandGroupId(shift, selectedDemandGroupId) {
  const demandGroups = shift?.demand_groups ?? [];
  if (!demandGroups.length) {
    return "";
  }
  return demandGroups.some((row) => row.id === selectedDemandGroupId || row.demand_group_id === selectedDemandGroupId)
    ? selectedDemandGroupId
    : (demandGroups[0].id ?? demandGroups[0].demand_group_id ?? "");
}

export function normalizePlanningStaffingLookupDate(value) {
  if (typeof value !== "string") {
    return undefined;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  const match = trimmed.match(/^(\d{4}-\d{2}-\d{2})/);
  return match ? match[1] : undefined;
}

export function buildPlanningStaffingPlanningRecordLookupFilters(filters, search = "") {
  const normalizedSearch = typeof search === "string" ? search.trim() : "";
  const lookupFilters = {
    planning_mode_code: filters?.planning_mode_code || undefined,
    planning_from: normalizePlanningStaffingLookupDate(filters?.date_from),
    planning_to: normalizePlanningStaffingLookupDate(filters?.date_to),
    search: normalizedSearch || undefined,
  };
  return Object.fromEntries(Object.entries(lookupFilters).filter(([, value]) => value !== undefined && value !== ""));
}

export function formatPlanningStaffingPlanningRecordOption(record) {
  if (!record) {
    return "";
  }
  const timeWindow = [record.planning_from, record.planning_to].filter(Boolean).join(" -> ");
  return [
    record.name || record.id,
    record.planning_mode_code,
    timeWindow,
    record.release_state,
    record.status,
  ]
    .filter(Boolean)
    .join(" | ");
}
