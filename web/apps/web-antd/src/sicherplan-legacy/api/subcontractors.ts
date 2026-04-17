import { webAppConfig } from "@/config/env";

export type LifecycleStatus = "active" | "inactive" | "archived";

export interface SubcontractorListItem {
  id: string;
  tenant_id: string;
  subcontractor_number: string;
  legal_name: string;
  display_name: string | null;
  managing_director_name: string | null;
  latitude: string | number | null;
  longitude: string | number | null;
  status: LifecycleStatus | string;
  archived_at: string | null;
  version_no: number;
}

export interface SubcontractorContactRead {
  id: string;
  tenant_id: string;
  subcontractor_id: string;
  full_name: string;
  title: string | null;
  function_label: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  is_primary_contact: boolean;
  portal_enabled: boolean;
  user_id: string | null;
  notes: string | null;
  status: LifecycleStatus | string;
  archived_at: string | null;
  version_no: number;
}

export interface SubcontractorScopeRead {
  id: string;
  tenant_id: string;
  subcontractor_id: string;
  branch_id: string;
  mandate_id: string | null;
  valid_from: string;
  valid_to: string | null;
  notes: string | null;
  status: LifecycleStatus | string;
  archived_at: string | null;
  version_no: number;
}

export interface SubcontractorFinanceProfileRead {
  id: string;
  tenant_id: string;
  subcontractor_id: string;
  invoice_email: string | null;
  payment_terms_days: number | null;
  payment_terms_note: string | null;
  tax_number: string | null;
  vat_id: string | null;
  bank_account_holder: string | null;
  bank_iban: string | null;
  bank_bic: string | null;
  bank_name: string | null;
  invoice_delivery_method_lookup_id: string | null;
  invoice_status_mode_lookup_id: string | null;
  billing_note: string | null;
  status: LifecycleStatus | string;
  archived_at: string | null;
  version_no: number;
}

export interface SubcontractorContactUserOptionRead {
  id: string;
  username: string;
  email: string | null;
  full_name: string | null;
  status: LifecycleStatus | string;
}

export interface SubcontractorReferenceOptionRead {
  id: string;
  code: string;
  label: string;
  description: string | null;
  is_active: boolean;
  status: string;
  archived_at: string | null;
}

export interface SubcontractorReferenceDataRead {
  legal_forms: SubcontractorReferenceOptionRead[];
}

export interface SubcontractorHistoryAttachmentRead {
  document_id: string;
  title: string;
  document_type_key: string | null;
  file_name: string | null;
  content_type: string | null;
  current_version_no: number | null;
}

export interface SubcontractorHistoryEntryRead {
  id: string;
  tenant_id: string;
  subcontractor_id: string;
  entry_type: string;
  title: string;
  body: string;
  occurred_at: string;
  actor_user_id: string | null;
  related_contact_id: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  attachments: SubcontractorHistoryAttachmentRead[];
}

export interface SubcontractorWorkerListItem {
  id: string;
  tenant_id: string;
  subcontractor_id: string;
  worker_no: string;
  first_name: string;
  last_name: string;
  preferred_name: string | null;
  email: string | null;
  mobile: string | null;
  status: LifecycleStatus | string;
  archived_at: string | null;
  version_no: number;
}

export interface SubcontractorWorkerQualificationProofRead {
  document_id: string;
  title: string;
  document_type_key: string | null;
  file_name: string | null;
  content_type: string | null;
  current_version_no: number | null;
  relation_type: string;
}

export interface SubcontractorWorkerQualificationRead {
  id: string;
  tenant_id: string;
  worker_id: string;
  qualification_type_id: string;
  qualification_type_code: string | null;
  qualification_type_label: string | null;
  certificate_no: string | null;
  issued_at: string | null;
  valid_until: string | null;
  issuing_authority: string | null;
  notes: string | null;
  status: LifecycleStatus | string;
  archived_at: string | null;
  version_no: number;
  proofs: SubcontractorWorkerQualificationProofRead[];
}

export interface SubcontractorWorkerCredentialRead {
  id: string;
  tenant_id: string;
  worker_id: string;
  credential_no: string;
  credential_type: string;
  encoded_value: string;
  valid_from: string;
  valid_until: string | null;
  issued_at: string | null;
  revoked_at: string | null;
  notes: string | null;
  status: LifecycleStatus | string;
  archived_at: string | null;
  version_no: number;
}

export interface SubcontractorWorkerRead extends SubcontractorWorkerListItem {
  birth_date: string | null;
  phone: string | null;
  notes: string | null;
  qualifications: SubcontractorWorkerQualificationRead[];
  credentials: SubcontractorWorkerCredentialRead[];
}

export interface SubcontractorWorkerReadinessIssueRead {
  issue_code: string;
  message_key: string;
  severity: string;
  category: string;
  reference_type: string;
  reference_id: string | null;
  title: string;
  due_on: string | null;
  metadata_json: Record<string, unknown>;
}

export interface SubcontractorWorkerReadinessListItem {
  worker_id: string;
  tenant_id: string;
  subcontractor_id: string;
  worker_no: string;
  first_name: string;
  last_name: string;
  preferred_name: string | null;
  status: string;
  archived_at: string | null;
  readiness_status: string;
  is_ready: boolean;
  blocking_issue_count: number;
  warning_issue_count: number;
  missing_proof_count: number;
  expired_qualification_count: number;
  expiring_qualification_count: number;
  missing_credential_count: number;
  issues: SubcontractorWorkerReadinessIssueRead[];
}

export interface SubcontractorWorkerReadinessRead extends SubcontractorWorkerReadinessListItem {
  qualification_count: number;
  credential_count: number;
  checked_at: string;
}

export interface SubcontractorWorkforceReadinessSummaryRead {
  tenant_id: string;
  subcontractor_id: string;
  total_workers: number;
  ready_workers: number;
  warning_only_workers: number;
  not_ready_workers: number;
  missing_proof_workers: number;
  expired_qualification_workers: number;
  expiring_qualification_workers: number;
  missing_credential_workers: number;
  checked_at: string;
}

export interface SubcontractorWorkerImportRowResult {
  row_no: number;
  worker_no: string | null;
  status: string;
  messages: string[];
  worker_id: string | null;
}

export interface SubcontractorWorkerImportDryRunResult {
  tenant_id: string;
  subcontractor_id: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: SubcontractorWorkerImportRowResult[];
}

export interface SubcontractorWorkerImportExecuteResult {
  tenant_id: string;
  subcontractor_id: string;
  job_id: string;
  job_status: string;
  total_rows: number;
  invalid_rows: number;
  created_workers: number;
  updated_workers: number;
  result_document_ids: string[];
  rows: SubcontractorWorkerImportRowResult[];
}

export interface SubcontractorWorkerExportResult {
  tenant_id: string;
  subcontractor_id: string;
  job_id: string;
  document_id: string;
  file_name: string;
  row_count: number;
}

export interface SubcontractorRead extends SubcontractorListItem {
  legal_form_lookup_id: string | null;
  subcontractor_status_lookup_id: string | null;
  address_id: string | null;
  notes: string | null;
  address: {
    id: string;
    street_line_1: string;
    street_line_2: string | null;
    postal_code: string;
    city: string;
    state: string | null;
    country_code: string;
  } | null;
  contacts: SubcontractorContactRead[];
  scopes: SubcontractorScopeRead[];
  finance_profile: SubcontractorFinanceProfileRead | null;
}

export interface SubcontractorListFilters {
  search?: string;
  lifecycle_status?: string;
  branch_id?: string;
  mandate_id?: string;
  include_archived?: boolean;
}

export interface SubcontractorWorkerListFilters {
  search?: string;
  status?: string;
  include_archived?: boolean;
}

export interface SubcontractorWorkerReadinessFilters extends SubcontractorWorkerListFilters {
  readiness_status?: string;
  issue_severity?: string;
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export class SubcontractorAdminApiError extends Error {
  readonly statusCode: number;
  readonly code: string;
  readonly messageKey: string;
  readonly details: Record<string, unknown>;

  constructor(statusCode: number, payload: ApiErrorEnvelope["error"]) {
    super(payload.message_key);
    this.statusCode = statusCode;
    this.code = payload.code;
    this.messageKey = payload.message_key;
    this.details = payload.details;
  }
}

function generateRequestId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `sp-subcontractors-${Date.now()}`;
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
  accessToken: string,
  options?: {
    method?: string;
    body?: unknown;
  },
): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: options?.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": generateRequestId(),
    },
    body: options?.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;

    if (isApiErrorEnvelope(payload)) {
      throw new SubcontractorAdminApiError(response.status, payload.error);
    }

    throw new SubcontractorAdminApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function buildQuery(params: SubcontractorListFilters) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.lifecycle_status) query.set("lifecycle_status", params.lifecycle_status);
  if (params.branch_id) query.set("branch_id", params.branch_id);
  if (params.mandate_id) query.set("mandate_id", params.mandate_id);
  if (params.include_archived) query.set("include_archived", "true");
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

function buildWorkerQuery(params: SubcontractorWorkerListFilters) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  if (params.include_archived) query.set("include_archived", "true");
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

function buildWorkerReadinessQuery(params: SubcontractorWorkerReadinessFilters) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  if (params.include_archived) query.set("include_archived", "true");
  if (params.readiness_status) query.set("readiness_status", params.readiness_status);
  if (params.issue_severity) query.set("issue_severity", params.issue_severity);
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listSubcontractors(tenantId: string, accessToken: string, params: SubcontractorListFilters) {
  return request<SubcontractorListItem[]>(`/api/subcontractors/tenants/${tenantId}/subcontractors${buildQuery(params)}`, accessToken);
}

export function getSubcontractor(tenantId: string, subcontractorId: string, accessToken: string) {
  return request<SubcontractorRead>(`/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}`, accessToken);
}

export function getSubcontractorReferenceData(tenantId: string, accessToken: string) {
  return request<SubcontractorReferenceDataRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/reference-data`,
    accessToken,
  );
}

export function createSubcontractor(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<SubcontractorRead>(`/api/subcontractors/tenants/${tenantId}/subcontractors`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateSubcontractor(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorRead>(`/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}`, accessToken, {
    method: "PATCH",
    body: payload,
  });
}

export function archiveSubcontractor(tenantId: string, subcontractorId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<SubcontractorRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/archive`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function reactivateSubcontractor(tenantId: string, subcontractorId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<SubcontractorRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/reactivate`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function listSubcontractorContacts(tenantId: string, subcontractorId: string, accessToken: string) {
  return request<SubcontractorContactRead[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/contacts`,
    accessToken,
  );
}

export function createSubcontractorContact(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorContactRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/contacts`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function listSubcontractorContactUserOptions(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  params: { search?: string; limit?: number } = {},
) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.limit != null) query.set("limit", String(params.limit));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<SubcontractorContactUserOptionRead[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/contact-user-options${suffix}`,
    accessToken,
  );
}

export function listSubcontractorAddressOptions(tenantId: string, subcontractorId: string, accessToken: string) {
  return request<SubcontractorRead["address"][]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/address-options`,
    accessToken,
  );
}

export function createSubcontractorAddressOption(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<NonNullable<SubcontractorRead["address"]>>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/address-options`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateSubcontractorContact(
  tenantId: string,
  subcontractorId: string,
  contactId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorContactRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/contacts/${contactId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listSubcontractorScopes(tenantId: string, subcontractorId: string, accessToken: string) {
  return request<SubcontractorScopeRead[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/scopes`,
    accessToken,
  );
}

export function listSubcontractorHistory(tenantId: string, subcontractorId: string, accessToken: string) {
  return request<SubcontractorHistoryEntryRead[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/history`,
    accessToken,
  );
}

export function listSubcontractorWorkers(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  params: SubcontractorWorkerListFilters,
) {
  return request<SubcontractorWorkerListItem[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers${buildWorkerQuery(params)}`,
    accessToken,
  );
}

export function listSubcontractorWorkerReadiness(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  params: SubcontractorWorkerReadinessFilters,
) {
  return request<SubcontractorWorkerReadinessListItem[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/readiness${buildWorkerReadinessQuery(params)}`,
    accessToken,
  );
}

export function getSubcontractorWorkerReadinessSummary(tenantId: string, subcontractorId: string, accessToken: string) {
  return request<SubcontractorWorkforceReadinessSummaryRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/readiness-summary`,
    accessToken,
  );
}

export function getSubcontractorWorkerReadiness(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  accessToken: string,
) {
  return request<SubcontractorWorkerReadinessRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}/readiness`,
    accessToken,
  );
}

export function getSubcontractorWorker(tenantId: string, subcontractorId: string, workerId: string, accessToken: string) {
  return request<SubcontractorWorkerRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}`,
    accessToken,
  );
}

export function createSubcontractorWorker(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateSubcontractorWorker(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function createSubcontractorWorkerQualification(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerQualificationRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}/qualifications`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateSubcontractorWorkerQualification(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  qualificationId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerQualificationRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}/qualifications/${qualificationId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function uploadSubcontractorQualificationProof(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  qualificationId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerQualificationProofRead[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}/qualifications/${qualificationId}/proofs/upload`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function linkSubcontractorQualificationProof(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  qualificationId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerQualificationProofRead[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}/qualifications/${qualificationId}/proofs/link`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function createSubcontractorWorkerCredential(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerCredentialRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}/credentials`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateSubcontractorWorkerCredential(
  tenantId: string,
  subcontractorId: string,
  workerId: string,
  credentialId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerCredentialRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/${workerId}/credentials/${credentialId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function importSubcontractorWorkersDryRun(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerImportDryRunResult>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/ops/import/dry-run`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function importSubcontractorWorkersExecute(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerImportExecuteResult>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/ops/import/execute`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function exportSubcontractorWorkers(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorWorkerExportResult>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/workers/ops/export`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function createSubcontractorHistoryEntry(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorHistoryEntryRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/history`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function linkSubcontractorHistoryAttachment(
  tenantId: string,
  subcontractorId: string,
  historyEntryId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorHistoryAttachmentRead[]>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/history/${historyEntryId}/attachments`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function createSubcontractorScope(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorScopeRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/scopes`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateSubcontractorScope(
  tenantId: string,
  subcontractorId: string,
  scopeId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorScopeRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/scopes/${scopeId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function getSubcontractorFinanceProfile(tenantId: string, subcontractorId: string, accessToken: string) {
  return request<SubcontractorFinanceProfileRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/finance-profile`,
    accessToken,
  );
}

export function putSubcontractorFinanceProfile(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorFinanceProfileRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/finance-profile`,
    accessToken,
    {
      method: "PUT",
      body: payload,
    },
  );
}

export function patchSubcontractorFinanceProfile(
  tenantId: string,
  subcontractorId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<SubcontractorFinanceProfileRead>(
    `/api/subcontractors/tenants/${tenantId}/subcontractors/${subcontractorId}/finance-profile`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function createPlatformDocument(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<{ id: string }>(`/api/platform/tenants/${tenantId}/documents`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function addPlatformDocumentVersion(
  tenantId: string,
  documentId: string,
  accessToken: string,
  payload: Record<string, unknown>,
) {
  return request<{ version_no: number }>(
    `/api/platform/tenants/${tenantId}/documents/${documentId}/versions`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export async function downloadSubcontractorDocument(
  tenantId: string,
  documentId: string,
  versionNo: number,
  accessToken: string,
) {
  const response = await fetch(
    `${webAppConfig.apiBaseUrl}/api/platform/tenants/${tenantId}/documents/${documentId}/versions/${versionNo}/download`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-Request-Id": generateRequestId(),
      },
    },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new SubcontractorAdminApiError(response.status, payload.error);
    }
    throw new SubcontractorAdminApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  return {
    blob: await response.blob(),
    fileName: response.headers.get("Content-Disposition")?.match(/filename=\"?([^\";]+)\"?/i)?.[1] ?? `document-${documentId}`,
  };
}
