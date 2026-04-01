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

export const EMPLOYEE_CREDENTIAL_TYPE_OPTIONS = [
  { value: "company_id", labelKey: "employeeAdmin.credentialType.company_id" },
  { value: "work_badge", labelKey: "employeeAdmin.credentialType.work_badge" },
];

export const EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS = [
  { value: "availability", labelKey: "employeeAdmin.availabilityRuleKind.availability" },
  { value: "unavailable", labelKey: "employeeAdmin.availabilityRuleKind.unavailable" },
  { value: "free_wish", labelKey: "employeeAdmin.availabilityRuleKind.free_wish" },
];

export const EMPLOYEE_DOCUMENT_TYPE_OPTIONS = [
  { value: "employment_contract", labelKey: "employeeAdmin.documentType.employment_contract" },
  { value: "identity_card", labelKey: "employeeAdmin.documentType.identity_card" },
  { value: "passport_copy", labelKey: "employeeAdmin.documentType.passport_copy" },
  { value: "residence_permit", labelKey: "employeeAdmin.documentType.residence_permit" },
  { value: "driving_licence", labelKey: "employeeAdmin.documentType.driving_licence" },
  { value: "qualification_certificate", labelKey: "employeeAdmin.documentType.qualification_certificate" },
  { value: "employee_misc", labelKey: "employeeAdmin.documentType.employee_misc" },
];

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
    canManagePrivateProfile: canWrite && canReadPrivate && !!selectedEmployee,
    canManageAddresses: canWrite && canReadPrivate && !!selectedEmployee,
    canManageAbsences: canWrite && canReadPrivate && !!selectedEmployee,
    canManageQualifications: canWrite && !!selectedEmployee,
    canManageCredentials: canWrite && !!selectedEmployee,
    canManageAvailability: canWrite && !!selectedEmployee,
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
    "errors.employees.employee.invalid_target_weekly_hours": "employeeAdmin.feedback.invalidTargetWeeklyHours",
    "errors.employees.employee.invalid_target_monthly_hours": "employeeAdmin.feedback.invalidTargetMonthlyHours",
    "errors.employees.document.not_linked": "employeeAdmin.feedback.notFound",
    "errors.docs.document.not_found": "employeeAdmin.feedback.notFound",
    "errors.docs.document_link.duplicate": "employeeAdmin.feedback.documentAlreadyLinked",
    "errors.employees.group.duplicate_code": "employeeAdmin.feedback.duplicateGroupCode",
    "errors.employees.group.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.group_member.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.note.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.private_profile.not_found": "employeeAdmin.feedback.notFound",
    "errors.employees.private_profile.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.address_history.overlap": "employeeAdmin.feedback.addressOverlap",
    "errors.employees.address_history.invalid_window": "employeeAdmin.feedback.addressInvalidWindow",
    "errors.employees.address_history.address_required": "employeeAdmin.feedback.addressRequired",
    "errors.employees.note.reminder_date_required": "employeeAdmin.feedback.reminderDateRequired",
    "errors.employees.note.invalid_type": "employeeAdmin.feedback.invalidNoteType",
    "errors.employees.photo.write_failed": "employeeAdmin.feedback.photoUploadFailed",
    "errors.employees.import.invalid_csv": "employeeAdmin.feedback.invalidImportCsv",
    "errors.employees.import.invalid_headers": "employeeAdmin.feedback.invalidImportHeaders",
    "errors.employees.access.username_taken": "employeeAdmin.feedback.accessUsernameTaken",
    "errors.employees.access.email_taken": "employeeAdmin.feedback.accessEmailTaken",
    "errors.employees.access.already_linked": "employeeAdmin.feedback.accessAlreadyLinked",
    "errors.employees.access.ambiguous_match": "employeeAdmin.feedback.accessAmbiguousMatch",
    "errors.employees.access.not_linked": "employeeAdmin.feedback.accessNotLinked",
    "errors.employees.access.full_name_required": "employeeAdmin.feedback.accessFullNameRequired",
    "errors.employees.access.role_missing": "employeeAdmin.feedback.accessRoleMissing",
    "errors.employees.function_type.not_found": "employeeAdmin.feedback.functionTypeNotFound",
    "errors.employees.qualification_type.not_found": "employeeAdmin.feedback.qualificationTypeNotFound",
    "errors.employees.qualification.not_found": "employeeAdmin.feedback.notFound",
    "errors.employees.qualification.invalid_record_kind": "employeeAdmin.feedback.invalidQualificationRecordKind",
    "errors.employees.qualification.record_target_required": "employeeAdmin.feedback.qualificationTargetRequired",
    "errors.employees.qualification.invalid_window": "employeeAdmin.feedback.qualificationInvalidWindow",
    "errors.employees.qualification.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.availability_rule.not_found": "employeeAdmin.feedback.notFound",
    "errors.employees.availability_rule.invalid_kind": "employeeAdmin.feedback.invalidAvailabilityKind",
    "errors.employees.availability_rule.invalid_window": "employeeAdmin.feedback.availabilityInvalidWindow",
    "errors.employees.availability_rule.invalid_recurrence": "employeeAdmin.feedback.invalidAvailabilityRecurrence",
    "errors.employees.availability_rule.invalid_recurrence_mask": "employeeAdmin.feedback.invalidAvailabilityWeekdayMask",
    "errors.employees.availability_rule.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.absence.not_found": "employeeAdmin.feedback.notFound",
    "errors.employees.absence.invalid_type": "employeeAdmin.feedback.invalidAbsenceType",
    "errors.employees.absence.invalid_window": "employeeAdmin.feedback.absenceInvalidWindow",
    "errors.employees.absence.overlap": "employeeAdmin.feedback.absenceOverlap",
    "errors.employees.absence.stale_version": "employeeAdmin.feedback.staleVersion",
    "errors.employees.credential.not_found": "employeeAdmin.feedback.notFound",
    "errors.employees.credential.invalid_type": "employeeAdmin.feedback.invalidCredentialType",
    "errors.employees.credential.invalid_status": "employeeAdmin.feedback.invalidCredentialStatus",
    "errors.employees.credential.invalid_window": "employeeAdmin.feedback.credentialInvalidWindow",
    "errors.employees.credential.duplicate_no": "employeeAdmin.feedback.credentialDuplicateNo",
    "errors.employees.credential.duplicate_encoded_value": "employeeAdmin.feedback.credentialDuplicateEncodedValue",
    "errors.employees.credential.stale_version": "employeeAdmin.feedback.staleVersion",
  };

  return messageMap[messageKey] ?? "employeeAdmin.feedback.error";
}

export function buildEmployeeDocumentUploadPayload(draft, file, toBase64) {
  return Promise.resolve(toBase64(file)).then((contentBase64) => ({
    title: draft.title.trim(),
    relation_type: draft.relation_type,
    label: normalizeOptionalText(draft.label),
    document_type_key: normalizeOptionalText(draft.document_type_key),
    file_name: file.name,
    content_type: file.type || "application/octet-stream",
    content_base64: contentBase64,
  }));
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

/**
 * @param {Record<string, any>} draft
 * @param {{
 *   deferUserLink?: boolean,
 *   allowedBranchIds?: string[] | null,
 *   allowedMandateIds?: string[] | null,
 * } | undefined} options
 */
export function buildEmployeeOperationalPayload(
  draft,
  { deferUserLink = false, allowedBranchIds = null, allowedMandateIds = null } = {},
) {
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
    status: emptyToNull(draft.status),
    employment_type_code: emptyToNull(draft.employment_type_code),
    target_weekly_hours: emptyToNull(draft.target_weekly_hours),
    target_monthly_hours: emptyToNull(draft.target_monthly_hours),
    user_id: deferUserLink ? null : emptyToNull(draft.user_id),
    notes: emptyToNull(draft.notes),
  };
}

export function buildEmployeePrivateProfilePayload(draft, { tenantId, employeeId } = {}) {
  return {
    tenant_id: tenantId,
    employee_id: employeeId,
    birth_date: typeof draft?.birth_date === "string" && draft.birth_date.trim() ? draft.birth_date.trim() : null,
    place_of_birth: typeof draft?.place_of_birth === "string" && draft.place_of_birth.trim() ? draft.place_of_birth.trim() : null,
    nationality_country_code:
      typeof draft?.nationality_country_code === "string" && draft.nationality_country_code.trim()
        ? draft.nationality_country_code.trim().toUpperCase()
        : null,
  };
}

export function normalizeOptionalText(value, { uppercase = false } = {}) {
  if (value == null) {
    return null;
  }
  const trimmed = typeof value === "string" ? value.trim() : String(value).trim();
  if (!trimmed) {
    return null;
  }
  return uppercase ? trimmed.toUpperCase() : trimmed;
}

export function toLocalDateTimeInput(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

export function normalizeDateTimeInput(value) {
  const normalized = normalizeOptionalText(value);
  if (!normalized) {
    return null;
  }
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

export function buildWeekdayMask(selectedWeekdays) {
  const daySet = new Set((selectedWeekdays ?? []).map((value) => Number(value)).filter((value) => Number.isInteger(value) && value >= 0 && value <= 6));
  return Array.from({ length: 7 }, (_, index) => (daySet.has(index) ? "1" : "0")).join("");
}

export function parseWeekdayMask(mask) {
  if (typeof mask !== "string" || mask.length !== 7) {
    return [];
  }
  return mask
    .split("")
    .map((flag, index) => (flag === "1" ? index : null))
    .filter((value) => value != null);
}

export function buildEmployeeQualificationPayload(draft, { tenantId, employeeId } = {}) {
  return {
    tenant_id: tenantId,
    employee_id: employeeId,
    record_kind: normalizeOptionalText(draft?.record_kind) || "qualification",
    function_type_id: normalizeOptionalText(draft?.function_type_id),
    qualification_type_id: normalizeOptionalText(draft?.qualification_type_id),
    certificate_no: normalizeOptionalText(draft?.certificate_no),
    issued_at: normalizeOptionalText(draft?.issued_at),
    valid_until: normalizeOptionalText(draft?.valid_until),
    issuing_authority: normalizeOptionalText(draft?.issuing_authority),
    granted_internally: Boolean(draft?.granted_internally),
    notes: normalizeOptionalText(draft?.notes),
  };
}

export function validateEmployeeQualificationDraft(draft) {
  const recordKind = normalizeOptionalText(draft?.record_kind) || "qualification";
  const validUntil = normalizeOptionalText(draft?.valid_until);
  const issuedAt = normalizeOptionalText(draft?.issued_at);
  const hasTarget = recordKind === "function"
    ? !!normalizeOptionalText(draft?.function_type_id)
    : !!normalizeOptionalText(draft?.qualification_type_id);

  if (!hasTarget) {
    return "employeeAdmin.feedback.qualificationTargetRequired";
  }
  if (issuedAt && validUntil && validUntil < issuedAt) {
    return "employeeAdmin.feedback.qualificationInvalidWindow";
  }
  return null;
}

export function buildEmployeeCredentialPayload(draft, { tenantId, employeeId } = {}) {
  return {
    tenant_id: tenantId,
    employee_id: employeeId,
    credential_no: normalizeOptionalText(draft?.credential_no) || "",
    credential_type: normalizeOptionalText(draft?.credential_type) || "",
    encoded_value: normalizeOptionalText(draft?.encoded_value) || "",
    valid_from: normalizeOptionalText(draft?.valid_from) || "",
    valid_until: normalizeOptionalText(draft?.valid_until),
    notes: normalizeOptionalText(draft?.notes),
  };
}

export function validateEmployeeCredentialDraft(draft) {
  const credentialNo = normalizeOptionalText(draft?.credential_no);
  const credentialType = normalizeOptionalText(draft?.credential_type);
  const encodedValue = normalizeOptionalText(draft?.encoded_value);
  const validFrom = normalizeOptionalText(draft?.valid_from);
  const validUntil = normalizeOptionalText(draft?.valid_until);

  if (!credentialNo || !credentialType || !encodedValue || !validFrom) {
    return "employeeAdmin.feedback.credentialRequired";
  }
  if (!EMPLOYEE_CREDENTIAL_TYPE_OPTIONS.some((option) => option.value === credentialType)) {
    return "employeeAdmin.feedback.invalidCredentialType";
  }
  if (validUntil && validUntil < validFrom) {
    return "employeeAdmin.feedback.credentialInvalidWindow";
  }
  return null;
}

export function buildEmployeeAvailabilityPayload(draft, { tenantId, employeeId } = {}) {
  const recurrenceType = normalizeOptionalText(draft?.recurrence_type) || "none";
  return {
    tenant_id: tenantId,
    employee_id: employeeId,
    rule_kind: normalizeOptionalText(draft?.rule_kind) || "",
    starts_at: normalizeDateTimeInput(draft?.starts_at),
    ends_at: normalizeDateTimeInput(draft?.ends_at),
    recurrence_type: recurrenceType,
    weekday_mask: recurrenceType === "weekly" ? buildWeekdayMask(draft?.weekday_indexes) : null,
    notes: normalizeOptionalText(draft?.notes),
  };
}

export function validateEmployeeAvailabilityDraft(draft) {
  const ruleKind = normalizeOptionalText(draft?.rule_kind);
  const startsAt = normalizeDateTimeInput(draft?.starts_at);
  const endsAt = normalizeDateTimeInput(draft?.ends_at);
  const recurrenceType = normalizeOptionalText(draft?.recurrence_type) || "none";
  const weekdayMask = buildWeekdayMask(draft?.weekday_indexes);

  if (!ruleKind) {
    return "employeeAdmin.feedback.availabilityRuleRequired";
  }
  if (!EMPLOYEE_AVAILABILITY_RULE_KIND_OPTIONS.some((option) => option.value === ruleKind)) {
    return "employeeAdmin.feedback.invalidAvailabilityKind";
  }
  if (!startsAt || !endsAt || endsAt < startsAt) {
    return "employeeAdmin.feedback.availabilityInvalidWindow";
  }
  if (recurrenceType === "weekly" && weekdayMask === "0000000") {
    return "employeeAdmin.feedback.invalidAvailabilityWeekdayMask";
  }
  return null;
}

export function buildEmployeeAbsencePayload(draft, { tenantId, employeeId } = {}) {
  return {
    tenant_id: tenantId,
    employee_id: employeeId,
    absence_type: normalizeOptionalText(draft?.absence_type) || "",
    starts_on: normalizeOptionalText(draft?.starts_on) || "",
    ends_on: normalizeOptionalText(draft?.ends_on) || "",
    notes: normalizeOptionalText(draft?.notes),
  };
}

export function validateEmployeeAbsenceDraft(draft) {
  const absenceType = normalizeOptionalText(draft?.absence_type);
  const startsOn = normalizeOptionalText(draft?.starts_on);
  const endsOn = normalizeOptionalText(draft?.ends_on);

  if (!absenceType || !startsOn || !endsOn) {
    return "employeeAdmin.feedback.absenceRequired";
  }
  if (endsOn < startsOn) {
    return "employeeAdmin.feedback.absenceInvalidWindow";
  }
  return null;
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

export function validateEmployeeAddressDraft(addressDraft, existingRows = [], editingAddressId = "") {
  const validFrom = typeof addressDraft?.valid_from === "string" ? addressDraft.valid_from.trim() : "";
  const validTo = typeof addressDraft?.valid_to === "string" ? addressDraft.valid_to.trim() : "";
  const addressType = typeof addressDraft?.address_type === "string" ? addressDraft.address_type.trim() : "";
  const line1 = typeof addressDraft?.street_line_1 === "string" ? addressDraft.street_line_1.trim() : "";
  const postalCode = typeof addressDraft?.postal_code === "string" ? addressDraft.postal_code.trim() : "";
  const city = typeof addressDraft?.city === "string" ? addressDraft.city.trim() : "";
  const countryCode = typeof addressDraft?.country_code === "string" ? addressDraft.country_code.trim() : "";
  const nextEnd = addressDraft?.is_current ? "" : validTo;

  if (!line1 || !postalCode || !city || !countryCode || !validFrom) {
    return "employeeAdmin.feedback.addressRequired";
  }
  if (nextEnd && nextEnd < validFrom) {
    return "employeeAdmin.feedback.addressInvalidWindow";
  }

  const overlaps = (existingRows ?? []).some((row) => {
    if (!row || row.id === editingAddressId || row.archived_at || row.address_type !== addressType) {
      return false;
    }
    const rowEnd = row.valid_to || "9999-12-31";
    const draftEnd = nextEnd || "9999-12-31";
    return validFrom <= rowEnd && row.valid_from <= draftEnd;
  });

  return overlaps ? "employeeAdmin.feedback.addressOverlap" : null;
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
      "employment_type_code",
      "target_weekly_hours",
      "target_monthly_hours",
      "user_id",
      "notes",
    ].join(","),
  ].join("\n");
}
