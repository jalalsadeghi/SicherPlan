import { legacySessionRequest } from "./sessionRequest";

export interface EmployeeListItem {
  id: string;
  tenant_id: string;
  personnel_no: string;
  first_name: string;
  last_name: string;
  preferred_name: string | null;
  work_email: string | null;
  mobile_phone: string | null;
  default_branch_id: string | null;
  default_mandate_id: string | null;
  hire_date: string | null;
  termination_date: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeeGroupRead {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  status: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeeGroupMembershipRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  group_id: string;
  valid_from: string;
  valid_until: string | null;
  notes: string | null;
  status: string;
  archived_at: string | null;
  version_no: number;
  group: EmployeeGroupRead | null;
}

export interface EmployeeOperationalRead extends EmployeeListItem {
  work_phone: string | null;
  employment_type_code: string | null;
  target_weekly_hours: number | null;
  target_monthly_hours: number | null;
  user_id: string | null;
  notes: string | null;
  group_memberships: EmployeeGroupMembershipRead[];
}

export interface EmployeePrivateProfileRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  private_email: string | null;
  private_phone: string | null;
  birth_date: string | null;
  place_of_birth: string | null;
  nationality_country_code: string | null;
  marital_status: string | null;
  tax_id: string | null;
  social_security_no: string | null;
  bank_account_holder: string | null;
  bank_iban: string | null;
  bank_bic: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  notes: string | null;
  status: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeePrivateProfileWritePayload {
  tenant_id: string;
  employee_id: string;
  private_email?: string | null;
  private_phone?: string | null;
  birth_date?: string | null;
  place_of_birth?: string | null;
  nationality_country_code?: string | null;
  marital_status?: string | null;
  tax_id?: string | null;
  social_security_no?: string | null;
  bank_account_holder?: string | null;
  bank_iban?: string | null;
  bank_bic?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  notes?: string | null;
}

export interface EmployeePrivateProfileUpdatePayload {
  private_email?: string | null;
  private_phone?: string | null;
  birth_date?: string | null;
  place_of_birth?: string | null;
  nationality_country_code?: string | null;
  marital_status?: string | null;
  tax_id?: string | null;
  social_security_no?: string | null;
  bank_account_holder?: string | null;
  bank_iban?: string | null;
  bank_bic?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  notes?: string | null;
  status?: string | null;
  version_no?: number | null;
}

export interface EmployeeAddressHistoryRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  address_id: string;
  address_type: string;
  valid_from: string;
  valid_to: string | null;
  is_primary: boolean;
  notes: string | null;
  status: string;
  archived_at: string | null;
  version_no: number;
  address: {
    id: string;
    street_line_1: string;
    street_line_2: string | null;
    postal_code: string;
    city: string;
    state_region: string | null;
    country_code: string;
  } | null;
}

export interface EmployeeAddressWriteAddressInput {
  street_line_1: string;
  street_line_2?: string | null;
  postal_code: string;
  city: string;
  state_region?: string | null;
  country_code: string;
}

export interface EmployeeAddressHistoryCreatePayload {
  tenant_id: string;
  employee_id: string;
  address_id?: string | null;
  address?: EmployeeAddressWriteAddressInput | null;
  address_type: string;
  valid_from: string;
  valid_to?: string | null;
  is_primary: boolean;
  notes?: string | null;
}

export interface EmployeeAddressHistoryUpdatePayload {
  address_id?: string | null;
  address?: EmployeeAddressWriteAddressInput | null;
  address_type?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  is_primary?: boolean | null;
  notes?: string | null;
  status?: string | null;
  version_no?: number | null;
}

export interface EmployeeNoteRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  note_type: string;
  title: string;
  body: string | null;
  reminder_at: string | null;
  completed_at: string | null;
  completed_by_user_id: string | null;
  status: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeeDocumentListItemRead {
  document_id: string;
  relation_type: string;
  label: string | null;
  title: string;
  document_type_key: string | null;
  file_name: string | null;
  content_type: string | null;
  current_version_no: number | null;
  linked_at: string | null;
}

export interface EmployeeDocumentUploadPayload {
  title: string;
  relation_type?: string | null;
  label?: string | null;
  document_type_key?: string | null;
  file_name: string;
  content_type: string;
  content_base64: string;
  is_revision_safe_pdf?: boolean;
}

export interface EmployeeDocumentLinkPayload {
  document_id: string;
  relation_type?: string | null;
  label?: string | null;
}

export interface EmployeeDocumentVersionPayload {
  file_name: string;
  content_type: string;
  content_base64: string;
  is_revision_safe_pdf?: boolean;
}

export interface EmployeePhotoRead extends EmployeeDocumentListItemRead {}

export interface EmployeeImportRowResult {
  row_no: number;
  personnel_no: string | null;
  status: string;
  employee_id: string | null;
  messages: string[];
}

export interface EmployeeImportDryRunResult {
  tenant_id: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: EmployeeImportRowResult[];
}

export interface EmployeeImportExecuteResult {
  tenant_id: string;
  job_id: string;
  job_status: string;
  total_rows: number;
  invalid_rows: number;
  created_employees: number;
  updated_employees: number;
  linked_users: number;
  result_document_ids: string[];
  rows: EmployeeImportRowResult[];
}

export interface EmployeeExportResult {
  tenant_id: string;
  job_id: string;
  document_id: string;
  file_name: string;
  row_count: number;
}

export interface EmployeeAccessLinkRead {
  employee_id: string;
  tenant_id: string;
  user_id: string | null;
  username: string | null;
  email: string | null;
  full_name: string | null;
  app_access_enabled: boolean;
  role_assignment_active: boolean;
}

export interface EmployeeAccessUpdateUserRequest {
  tenant_id: string;
  username: string;
  email: string;
  full_name: string;
}

export interface EmployeeAccessResetPasswordRequest {
  tenant_id: string;
  password: string;
}

export interface EmployeeCatalogBootstrapRead {
  function_types_inserted: number;
  function_types_updated: number;
  qualification_types_inserted: number;
  qualification_types_updated: number;
}

export interface FunctionTypeRead {
  id: string;
  tenant_id: string;
  code: string;
  label: string;
  category: string | null;
  description: string | null;
  is_active: boolean;
  planning_relevant: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  version_no: number;
}

export interface QualificationTypeRead {
  id: string;
  tenant_id: string;
  code: string;
  label: string;
  category: string | null;
  description: string | null;
  is_active: boolean;
  planning_relevant: boolean;
  compliance_relevant: boolean;
  expiry_required: boolean;
  default_validity_days: number | null;
  proof_required: boolean;
  status: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeeQualificationRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  record_kind: string;
  function_type_id: string | null;
  qualification_type_id: string | null;
  certificate_no: string | null;
  issued_at: string | null;
  valid_until: string | null;
  issuing_authority: string | null;
  granted_internally: boolean;
  notes: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  version_no: number;
  function_type: FunctionTypeRead | null;
  qualification_type: QualificationTypeRead | null;
}

export interface EmployeeQualificationCreatePayload {
  tenant_id: string;
  employee_id: string;
  record_kind: string;
  function_type_id?: string | null;
  qualification_type_id?: string | null;
  certificate_no?: string | null;
  issued_at?: string | null;
  valid_until?: string | null;
  issuing_authority?: string | null;
  granted_internally?: boolean;
  notes?: string | null;
}

export interface EmployeeQualificationUpdatePayload {
  function_type_id?: string | null;
  qualification_type_id?: string | null;
  certificate_no?: string | null;
  issued_at?: string | null;
  valid_until?: string | null;
  issuing_authority?: string | null;
  granted_internally?: boolean | null;
  notes?: string | null;
  status?: string | null;
  archived_at?: string | null;
  version_no?: number | null;
}

export interface EmployeeQualificationProofUploadPayload {
  title?: string | null;
  file_name: string;
  content_type: string;
  content_base64: string;
}

export interface EmployeeQualificationProofRead extends EmployeeDocumentListItemRead {}

export interface EmployeeAvailabilityRuleRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  rule_kind: string;
  starts_at: string;
  ends_at: string;
  recurrence_type: string;
  weekday_mask: string | null;
  notes: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeeAvailabilityRuleCreatePayload {
  tenant_id: string;
  employee_id: string;
  rule_kind: string;
  starts_at: string;
  ends_at: string;
  recurrence_type: string;
  weekday_mask?: string | null;
  notes?: string | null;
}

export interface EmployeeAvailabilityRuleUpdatePayload {
  rule_kind?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  recurrence_type?: string | null;
  weekday_mask?: string | null;
  notes?: string | null;
  status?: string | null;
  archived_at?: string | null;
  version_no?: number | null;
}

export interface EmployeeAbsenceRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  absence_type: string;
  starts_on: string;
  ends_on: string;
  quantity_days: number;
  status: string;
  requested_at: string;
  approved_by_user_id: string | null;
  approved_at: string | null;
  decision_note: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeeAbsenceCreatePayload {
  tenant_id: string;
  employee_id: string;
  absence_type: string;
  starts_on: string;
  ends_on: string;
  notes?: string | null;
}

export interface EmployeeAbsenceUpdatePayload {
  absence_type?: string | null;
  starts_on?: string | null;
  ends_on?: string | null;
  status?: string | null;
  decision_note?: string | null;
  notes?: string | null;
  archived_at?: string | null;
  version_no?: number | null;
}

export interface EmployeeCredentialRead {
  id: string;
  tenant_id: string;
  employee_id: string;
  credential_no: string;
  credential_type: string;
  encoded_value: string;
  valid_from: string;
  valid_until: string | null;
  status: string;
  issued_at: string | null;
  revoked_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  archived_at: string | null;
  version_no: number;
}

export interface EmployeeCredentialCreatePayload {
  tenant_id: string;
  employee_id: string;
  credential_no: string;
  credential_type: string;
  encoded_value: string;
  valid_from: string;
  valid_until?: string | null;
  notes?: string | null;
}

export interface EmployeeCredentialUpdatePayload {
  status?: string | null;
  encoded_value?: string | null;
  valid_from?: string | null;
  valid_until?: string | null;
  notes?: string | null;
  archived_at?: string | null;
  version_no?: number | null;
}

export interface EmployeeCredentialBadgeIssuePayload {
  title?: string | null;
}

export interface EmployeeCredentialBadgeRead extends EmployeeDocumentListItemRead {}

export interface EmployeeListFilters {
  search?: string;
  status?: string;
  default_branch_id?: string;
  default_mandate_id?: string;
  include_archived?: boolean;
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export class EmployeeAdminApiError extends Error {
  readonly statusCode: number;
  readonly code: string;
  readonly messageKey: string;
  readonly requestId: string;
  readonly details: Record<string, unknown>;

  constructor(statusCode: number, payload: ApiErrorEnvelope["error"]) {
    super(payload.message_key);
    this.statusCode = statusCode;
    this.code = payload.code;
    this.messageKey = payload.message_key;
    this.requestId = payload.request_id;
    this.details = payload.details;
  }
}

function generateRequestId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `sp-employees-${Date.now()}`;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }

  const error = (value as Record<string, unknown>).error;
  return !!error && typeof error === "object" && typeof (error as Record<string, unknown>).message_key === "string";
}

async function request<T>(
  path: string,
  _accessToken: string,
  options?: {
    method?: string;
    body?: unknown;
  },
): Promise<T> {
  const response = await legacySessionRequest(path, {
    headers: {
      "X-Request-Id": generateRequestId(),
    },
    jsonBody: options?.body,
    method: options?.method ?? "GET",
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;

    if (isApiErrorEnvelope(payload)) {
      throw new EmployeeAdminApiError(response.status, payload.error);
    }

    throw new EmployeeAdminApiError(response.status, {
      code: response.status === 404 ? "platform.http_not_found" : "platform.internal",
      message_key: response.status === 404 ? "errors.platform.http_not_found" : "errors.platform.internal",
      request_id: response.headers.get("X-Request-ID") || "",
      details: {},
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function buildQuery(params: EmployeeListFilters) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  if (params.default_branch_id) query.set("default_branch_id", params.default_branch_id);
  if (params.default_mandate_id) query.set("default_mandate_id", params.default_mandate_id);
  if (params.include_archived) query.set("include_archived", "true");
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

function buildScopedQuery(params: Record<string, boolean | null | number | string | undefined>) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === "") {
      continue;
    }
    if (typeof value === "boolean") {
      if (value) {
        query.set(key, "true");
      }
      continue;
    }
    query.set(key, String(value));
  }
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listEmployees(tenantId: string, accessToken: string, params: EmployeeListFilters) {
  return request<EmployeeListItem[]>(`/api/employees/tenants/${tenantId}/employees${buildQuery(params)}`, accessToken);
}

export function getEmployee(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeOperationalRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}`, accessToken);
}

export function createEmployee(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeOperationalRead>(`/api/employees/tenants/${tenantId}/employees`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateEmployee(tenantId: string, employeeId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeOperationalRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}`, accessToken, {
    method: "PATCH",
    body: payload,
  });
}

export function getEmployeePrivateProfile(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeePrivateProfileRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/private-profile`, accessToken);
}

export function upsertEmployeePrivateProfile(
  tenantId: string,
  employeeId: string,
  accessToken: string,
  payload: EmployeePrivateProfileWritePayload,
) {
  return request<EmployeePrivateProfileRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/private-profile`, accessToken, {
    method: "PUT",
    body: payload,
  });
}

export function updateEmployeePrivateProfile(
  tenantId: string,
  employeeId: string,
  accessToken: string,
  payload: EmployeePrivateProfileUpdatePayload,
) {
  return request<EmployeePrivateProfileRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/private-profile`, accessToken, {
    method: "PATCH",
    body: payload,
  });
}

export function listEmployeeAddresses(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeAddressHistoryRead[]>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/addresses`, accessToken);
}

export function createEmployeeAddress(
  tenantId: string,
  employeeId: string,
  accessToken: string,
  payload: EmployeeAddressHistoryCreatePayload,
) {
  return request<EmployeeAddressHistoryRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/addresses`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function updateEmployeeAddress(
  tenantId: string,
  employeeId: string,
  historyId: string,
  accessToken: string,
  payload: EmployeeAddressHistoryUpdatePayload,
) {
  return request<EmployeeAddressHistoryRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/addresses/${historyId}`,
    accessToken,
    { method: "PATCH", body: payload },
  );
}

export function listEmployeeGroups(tenantId: string, accessToken: string) {
  return request<EmployeeGroupRead[]>(`/api/employees/tenants/${tenantId}/employees/groups/catalog`, accessToken);
}

export function bootstrapEmployeeCatalogSamples(tenantId: string, accessToken: string) {
  return request<EmployeeCatalogBootstrapRead>(
    `/api/employees/tenants/${tenantId}/employees/catalog/bootstrap-sample-data`,
    accessToken,
    { method: "POST" },
  );
}

export function listFunctionTypes(tenantId: string, accessToken: string) {
  return request<FunctionTypeRead[]>(`/api/employees/tenants/${tenantId}/employees/catalog/function-types`, accessToken);
}

export function listQualificationTypes(tenantId: string, accessToken: string) {
  return request<QualificationTypeRead[]>(`/api/employees/tenants/${tenantId}/employees/catalog/qualification-types`, accessToken);
}

export function createEmployeeGroup(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeGroupRead>(`/api/employees/tenants/${tenantId}/employees/groups/catalog`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateEmployeeGroup(tenantId: string, groupId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeGroupRead>(`/api/employees/tenants/${tenantId}/employees/groups/catalog/${groupId}`, accessToken, {
    method: "PATCH",
    body: payload,
  });
}

export function createEmployeeGroupMembership(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeGroupMembershipRead>(`/api/employees/tenants/${tenantId}/employees/groups/memberships`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateEmployeeGroupMembership(
  tenantId: string,
  memberId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<EmployeeGroupMembershipRead>(
    `/api/employees/tenants/${tenantId}/employees/groups/memberships/${memberId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listEmployeeNotes(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeNoteRead[]>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/notes`, accessToken);
}

export function listEmployeeQualifications(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeQualificationRead[]>(
    `/api/employees/tenants/${tenantId}/employees/qualifications${buildScopedQuery({ employee_id: employeeId })}`,
    accessToken,
  );
}

export function createEmployeeQualification(
  tenantId: string,
  accessToken: string,
  payload: EmployeeQualificationCreatePayload,
) {
  return request<EmployeeQualificationRead>(`/api/employees/tenants/${tenantId}/employees/qualifications`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateEmployeeQualification(
  tenantId: string,
  qualificationId: string,
  accessToken: string,
  payload: EmployeeQualificationUpdatePayload,
) {
  return request<EmployeeQualificationRead>(
    `/api/employees/tenants/${tenantId}/employees/qualifications/${qualificationId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listEmployeeQualificationProofs(
  tenantId: string,
  qualificationId: string,
  accessToken: string,
) {
  return request<EmployeeQualificationProofRead[]>(
    `/api/employees/tenants/${tenantId}/employees/qualifications/${qualificationId}/proofs`,
    accessToken,
  );
}

export function uploadEmployeeQualificationProof(
  tenantId: string,
  qualificationId: string,
  accessToken: string,
  payload: EmployeeQualificationProofUploadPayload,
) {
  return request<EmployeeQualificationProofRead>(
    `/api/employees/tenants/${tenantId}/employees/qualifications/${qualificationId}/proofs/uploads`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function listEmployeeAvailabilityRules(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeAvailabilityRuleRead[]>(
    `/api/employees/tenants/${tenantId}/employees/availability-rules${buildScopedQuery({ employee_id: employeeId })}`,
    accessToken,
  );
}

export function createEmployeeAvailabilityRule(
  tenantId: string,
  accessToken: string,
  payload: EmployeeAvailabilityRuleCreatePayload,
) {
  return request<EmployeeAvailabilityRuleRead>(
    `/api/employees/tenants/${tenantId}/employees/availability-rules`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateEmployeeAvailabilityRule(
  tenantId: string,
  ruleId: string,
  accessToken: string,
  payload: EmployeeAvailabilityRuleUpdatePayload,
) {
  return request<EmployeeAvailabilityRuleRead>(
    `/api/employees/tenants/${tenantId}/employees/availability-rules/${ruleId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listEmployeeAbsences(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeAbsenceRead[]>(
    `/api/employees/tenants/${tenantId}/employees/absences${buildScopedQuery({ employee_id: employeeId })}`,
    accessToken,
  );
}

export function createEmployeeAbsence(
  tenantId: string,
  accessToken: string,
  payload: EmployeeAbsenceCreatePayload,
) {
  return request<EmployeeAbsenceRead>(`/api/employees/tenants/${tenantId}/employees/absences`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateEmployeeAbsence(
  tenantId: string,
  absenceId: string,
  accessToken: string,
  payload: EmployeeAbsenceUpdatePayload,
) {
  return request<EmployeeAbsenceRead>(
    `/api/employees/tenants/${tenantId}/employees/absences/${absenceId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listEmployeeCredentials(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeCredentialRead[]>(
    `/api/employees/tenants/${tenantId}/employees/credentials${buildScopedQuery({ employee_id: employeeId })}`,
    accessToken,
  );
}

export function createEmployeeCredential(
  tenantId: string,
  accessToken: string,
  payload: EmployeeCredentialCreatePayload,
) {
  return request<EmployeeCredentialRead>(`/api/employees/tenants/${tenantId}/employees/credentials`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateEmployeeCredential(
  tenantId: string,
  credentialId: string,
  accessToken: string,
  payload: EmployeeCredentialUpdatePayload,
) {
  return request<EmployeeCredentialRead>(
    `/api/employees/tenants/${tenantId}/employees/credentials/${credentialId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function issueEmployeeCredentialBadgeOutput(
  tenantId: string,
  credentialId: string,
  accessToken: string,
  payload: EmployeeCredentialBadgeIssuePayload,
) {
  return request<EmployeeCredentialBadgeRead>(
    `/api/employees/tenants/${tenantId}/employees/credentials/${credentialId}/badge-output`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function createEmployeeNote(tenantId: string, employeeId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeNoteRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/notes`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateEmployeeNote(
  tenantId: string,
  employeeId: string,
  noteId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<EmployeeNoteRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/notes/${noteId}`, accessToken, {
    method: "PATCH",
    body: payload,
  });
}

export function listEmployeeDocuments(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeDocumentListItemRead[]>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/documents`, accessToken);
}

export function uploadEmployeeDocument(
  tenantId: string,
  employeeId: string,
  accessToken: string,
  payload: EmployeeDocumentUploadPayload,
) {
  return request<EmployeeDocumentListItemRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/documents/uploads`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function linkEmployeeDocument(
  tenantId: string,
  employeeId: string,
  accessToken: string,
  payload: EmployeeDocumentLinkPayload,
) {
  return request<EmployeeDocumentListItemRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/documents/links`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function addEmployeeDocumentVersion(
  tenantId: string,
  employeeId: string,
  documentId: string,
  accessToken: string,
  payload: EmployeeDocumentVersionPayload,
) {
  return request<EmployeeDocumentListItemRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/documents/${documentId}/versions`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function getEmployeePhoto(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeePhotoRead | null>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/photo`, accessToken);
}

export function uploadEmployeePhoto(tenantId: string, employeeId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeePhotoRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/photo`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function importEmployeesDryRun(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeImportDryRunResult>(`/api/employees/tenants/${tenantId}/employees/ops/import/dry-run`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function importEmployeesExecute(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeImportExecuteResult>(`/api/employees/tenants/${tenantId}/employees/ops/import/execute`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function exportEmployees(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeExportResult>(`/api/employees/tenants/${tenantId}/employees/ops/export`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function getEmployeeAccessLink(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeAccessLinkRead>(`/api/employees/tenants/${tenantId}/employees/${employeeId}/access-link`, accessToken);
}

export function createEmployeeAccessUser(tenantId: string, employeeId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeAccessLinkRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/access-link/create-user`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateEmployeeAccessUser(
  tenantId: string,
  employeeId: string,
  accessToken: string,
  payload: EmployeeAccessUpdateUserRequest,
) {
  return request<EmployeeAccessLinkRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/access-link/user`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function resetEmployeeAccessUserPassword(
  tenantId: string,
  employeeId: string,
  accessToken: string,
  payload: EmployeeAccessResetPasswordRequest,
) {
  return request<EmployeeAccessLinkRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/access-link/reset-password`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function attachEmployeeAccessUser(tenantId: string, employeeId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeAccessLinkRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/access-link/attach`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function detachEmployeeAccessUser(tenantId: string, employeeId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<EmployeeAccessLinkRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/access-link/detach`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function reconcileEmployeeAccessUser(tenantId: string, employeeId: string, accessToken: string) {
  return request<EmployeeAccessLinkRead>(
    `/api/employees/tenants/${tenantId}/employees/${employeeId}/access-link/reconcile`,
    accessToken,
    {
      method: "POST",
    },
  );
}

export async function downloadEmployeeDocument(
  tenantId: string,
  documentId: string,
  versionNo: number,
  _accessToken: string,
) {
  const response = await legacySessionRequest(
    `/api/platform/tenants/${tenantId}/documents/${documentId}/versions/${versionNo}/download`,
    {
      headers: {
        "X-Request-Id": generateRequestId(),
      },
    },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new EmployeeAdminApiError(response.status, payload.error);
    }
    throw new EmployeeAdminApiError(response.status, {
      code: response.status === 404 ? "platform.http_not_found" : "platform.internal",
      message_key: response.status === 404 ? "errors.platform.http_not_found" : "errors.platform.internal",
      request_id: response.headers.get("X-Request-ID") || "",
      details: {},
    });
  }

  return {
    blob: await response.blob(),
    fileName: response.headers.get("Content-Disposition")?.match(/filename=\"?([^\";]+)\"?/i)?.[1] ?? `document-${documentId}`,
  };
}
