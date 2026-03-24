export const EMPLOYEE_PERMISSION_MATRIX = {
  platform_admin: ["employees.employee.read", "employees.employee.write", "employees.private.read", "employees.private.write"],
  tenant_admin: ["employees.employee.read", "employees.employee.write", "employees.private.read", "employees.private.write"],
  dispatcher: ["employees.employee.read"],
  accounting: ["employees.employee.read"],
  controller_qm: ["employees.employee.read"],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasEmployeePermission(role, permissionKey) {
  return (EMPLOYEE_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveEmployeeActionState(role, selectedEmployee) {
  const canRead = hasEmployeePermission(role, "employees.employee.read");
  const canWrite = hasEmployeePermission(role, "employees.employee.write");
  const canReadPrivate = hasEmployeePermission(role, "employees.private.read");
  const status = selectedEmployee?.status ?? "active";
  const archivedAt = selectedEmployee?.archived_at ?? null;

  return {
    canRead,
    canWrite,
    canReadPrivate,
    canCreate: canWrite,
    canEdit: canWrite && !!selectedEmployee,
    canManageNotes: canWrite && !!selectedEmployee,
    canManageGroups: canWrite && !!selectedEmployee,
    canManagePhoto: canWrite && !!selectedEmployee,
    canImport: canWrite,
    canExport: canRead,
    canManageAccess: canWrite && !!selectedEmployee,
    canArchive: canWrite && !!selectedEmployee && !archivedAt && status !== "archived",
    canReactivate: canWrite && !!selectedEmployee && status === "inactive" && !archivedAt,
  };
}

export function mapEmployeeApiMessage(messageKey) {
  const messageMap = {
    "errors.iam.auth.invalid_access_token": "employeeAdmin.feedback.authRequired",
    "errors.iam.authorization.permission_denied": "employeeAdmin.feedback.permissionDenied",
    "errors.iam.authorization.scope_denied": "employeeAdmin.feedback.permissionDenied",
    "errors.employees.employee.not_found": "employeeAdmin.feedback.notFound",
    "errors.employees.employee.duplicate_personnel_no": "employeeAdmin.feedback.duplicatePersonnelNo",
    "errors.employees.employee.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.group.duplicate_code": "employeeAdmin.feedback.duplicateGroupCode",
    "errors.employees.group.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.group_member.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.note.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.address_history.overlap": "employeeAdmin.feedback.addressOverlap",
    "errors.employees.note.reminder_date_required": "employeeAdmin.feedback.reminderDateRequired",
    "errors.employees.note.invalid_type": "employeeAdmin.feedback.invalidNoteType",
    "errors.employees.photo.write_failed": "employeeAdmin.feedback.photoUploadFailed",
    "errors.employees.import.invalid_csv": "employeeAdmin.feedback.invalidImportCsv",
    "errors.employees.import.invalid_headers": "employeeAdmin.feedback.invalidImportHeaders",
    "errors.employees.access.username_taken": "employeeAdmin.feedback.accessUsernameTaken",
    "errors.employees.access.email_taken": "employeeAdmin.feedback.accessEmailTaken",
    "errors.employees.access.ambiguous_match": "employeeAdmin.feedback.accessAmbiguousMatch",
    "errors.employees.access.role_missing": "employeeAdmin.feedback.accessRoleMissing",
  };

  return messageMap[messageKey] ?? "employeeAdmin.feedback.error";
}

export function formatEmployeeStructureLabel(record) {
  if (!record) {
    return "";
  }

  return [record.code, record.name].filter(Boolean).join(" - ");
}

export function filterMandatesForBranch(mandates, branchId) {
  const normalizedBranchId = typeof branchId === "string" ? branchId.trim() : "";
  if (!normalizedBranchId) {
    return [...(mandates ?? [])];
  }

  return (mandates ?? []).filter((mandate) => mandate.branch_id === normalizedBranchId);
}

export function buildEmployeeOperationalPayload(draft, { deferUserLink = false, allowedBranchIds = null, allowedMandateIds = null } = {}) {
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
    personnel_no: draft.personnel_no.trim(),
    first_name: draft.first_name.trim(),
    last_name: draft.last_name.trim(),
    preferred_name: emptyToNull(draft.preferred_name),
    work_email: emptyToNull(draft.work_email),
    work_phone: emptyToNull(draft.work_phone),
    mobile_phone: emptyToNull(draft.mobile_phone),
    default_branch_id: normalizeReference(draft.default_branch_id, allowedBranchIds),
    default_mandate_id: normalizeReference(draft.default_mandate_id, allowedMandateIds),
    hire_date: emptyToNull(draft.hire_date),
    termination_date: emptyToNull(draft.termination_date),
    user_id: deferUserLink ? null : emptyToNull(draft.user_id),
    notes: emptyToNull(draft.notes),
  };
}

export function summarizeCurrentAddress(addressRows) {
  const currentPrimary = [...(addressRows ?? [])]
    .filter((row) => !row.archived_at && row.is_primary)
    .sort((left, right) => left.valid_from.localeCompare(right.valid_from))
    .at(-1);

  if (!currentPrimary?.address) {
    return "";
  }

  return [
    currentPrimary.address.street_line_1,
    currentPrimary.address.postal_code,
    currentPrimary.address.city,
  ]
    .filter(Boolean)
    .join(", ");
}

export function buildEmployeeImportTemplateRows() {
  return [
    [
      "personnel_no",
      "first_name",
      "last_name",
      "preferred_name",
      "work_email",
      "work_phone",
      "mobile_phone",
      "default_branch_id",
      "default_mandate_id",
      "hire_date",
      "termination_date",
      "status",
      "user_id",
      "notes",
    ].join(","),
  ].join("\n");
}
