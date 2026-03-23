import { webAppConfig } from "@/config/env";

import { AuthApiError } from "@/api/auth";

export interface SubcontractorPortalCollectionSourceRead {
  domain_key: string;
  source_module_key: string;
  availability_status: string;
  released_only: boolean;
  subcontractor_scoped: boolean;
  docs_backed_outputs: boolean;
  message_key: string;
}

export interface SubcontractorPortalPositionRead {
  id: string;
  subcontractor_id: string;
  reference_no: string;
  title: string;
  branch_label: string | null;
  mandate_label: string | null;
  work_start: string;
  work_end: string;
  location_label: string | null;
  readiness_status: string;
  confirmation_status: string;
}

export interface SubcontractorPortalScheduleRead {
  id: string;
  subcontractor_id: string;
  position_id: string;
  shift_label: string;
  schedule_date: string;
  work_start: string;
  work_end: string;
  location_label: string | null;
  confirmation_status: string;
}

export interface SubcontractorPortalActualSummaryRead {
  id: string;
  subcontractor_id: string;
  period_start: string;
  period_end: string;
  confirmed_minutes: number;
  open_minutes: number;
  status: string;
  attendance_status: string;
}

export interface SubcontractorPortalAttendanceRead {
  id: string;
  subcontractor_id: string;
  schedule_id: string;
  work_date: string;
  status: string;
  confirmed_at: string | null;
  location_label: string | null;
  document_count: number;
}

export interface SubcontractorPortalInvoiceCheckRead {
  id: string;
  subcontractor_id: string;
  period_label: string;
  status: string;
  submitted_invoice_ref: string | null;
  approved_minutes: number;
  approved_amount: string | null;
  submitted_invoice_amount: string | null;
  last_checked_at: string | null;
  variance_minutes: number | null;
  variance_amount: string | null;
}

export interface SubcontractorPortalInvoiceCheckLineRead {
  id: string;
  service_date: string;
  label: string;
  billing_unit_code: string;
  approved_quantity: string;
  unit_price: string | null;
  approved_amount: string;
  variance_amount: string;
  variance_reason_codes_json: string[];
}

export interface SubcontractorPortalInvoiceCheckDetailRead extends SubcontractorPortalInvoiceCheckRead {
  period_start: string;
  period_end: string;
  released_at: string | null;
  lines: SubcontractorPortalInvoiceCheckLineRead[];
}

export interface SubcontractorPortalPositionCollectionRead {
  subcontractor_id: string;
  source: SubcontractorPortalCollectionSourceRead;
  items: SubcontractorPortalPositionRead[];
}

export interface SubcontractorPortalScheduleCollectionRead {
  subcontractor_id: string;
  source: SubcontractorPortalCollectionSourceRead;
  items: SubcontractorPortalScheduleRead[];
}

export interface SubcontractorPortalActualSummaryCollectionRead {
  subcontractor_id: string;
  source: SubcontractorPortalCollectionSourceRead;
  items: SubcontractorPortalActualSummaryRead[];
}

export interface SubcontractorPortalAttendanceCollectionRead {
  subcontractor_id: string;
  source: SubcontractorPortalCollectionSourceRead;
  items: SubcontractorPortalAttendanceRead[];
}

export interface SubcontractorPortalInvoiceCheckCollectionRead {
  subcontractor_id: string;
  source: SubcontractorPortalCollectionSourceRead;
  items: SubcontractorPortalInvoiceCheckRead[];
}

export interface SubcontractorPortalWatchbookEntryRead {
  id: string;
  subcontractor_id: string;
  log_date: string;
  occurred_at: string;
  entry_type_code: string;
  summary: string;
  status: string;
  pdf_document_id: null | string;
}

export interface SubcontractorPortalWatchbookCollectionRead {
  subcontractor_id: string;
  source: SubcontractorPortalCollectionSourceRead;
  items: SubcontractorPortalWatchbookEntryRead[];
}

export interface SubcontractorPortalWatchbookEntryCreate {
  entry_type_code: "subcontractor_note";
  narrative: string;
}

export interface SubcontractorWorkerReadinessIssueRead {
  issue_code: string;
  message_key: string;
  severity: string;
  category: string;
  reference_type: string;
  reference_id: null | string;
  title: string;
  due_on: null | string;
  metadata_json: Record<string, unknown>;
}

export interface SubcontractorPortalAllocationCandidateRead {
  worker_id: string;
  worker_no: string;
  display_name: string;
  readiness_status: string;
  is_ready: boolean;
  blocking_issue_count: number;
  warning_issue_count: number;
  issues: SubcontractorWorkerReadinessIssueRead[];
}

export interface SubcontractorPortalAllocationCandidateCollectionRead {
  subcontractor_id: string;
  items: SubcontractorPortalAllocationCandidateRead[];
}

export type SubcontractorPortalAllocationAction = "assign" | "confirm" | "reassign" | "unassign";

export interface SubcontractorPortalAllocationRequest {
  position_id: string;
  worker_id: string;
  action: SubcontractorPortalAllocationAction;
}

export interface SubcontractorPortalAllocationPreviewRead {
  subcontractor_id: string;
  position_id: string;
  worker_id: string;
  action: SubcontractorPortalAllocationAction;
  command_status: string;
  validation_scope: string;
  can_submit: boolean;
  issues: SubcontractorWorkerReadinessIssueRead[];
}

export interface SubcontractorPortalAllocationResultRead {
  subcontractor_id: string;
  position_id: string;
  worker_id: string;
  action: SubcontractorPortalAllocationAction;
  command_status: string;
  message_key: string;
  acted_by_user_id: string;
  confirmed_at: null | string;
  issues: SubcontractorWorkerReadinessIssueRead[];
}

export interface SubcontractorPortalQualificationTypeOptionRead {
  id: string;
  code: string;
  label: string;
  expiry_required: boolean;
  default_validity_days: null | number;
  proof_required: boolean;
  compliance_relevant: boolean;
}

export interface SubcontractorWorkerListItem {
  id: string;
  tenant_id: string;
  subcontractor_id: string;
  worker_no: string;
  first_name: string;
  last_name: string;
  preferred_name: null | string;
  email: null | string;
  mobile: null | string;
  status: string;
  archived_at: null | string;
  version_no: number;
}

export interface SubcontractorPortalWorkerCreate {
  worker_no: string;
  first_name: string;
  last_name: string;
  preferred_name?: null | string;
  birth_date?: null | string;
  email?: null | string;
  phone?: null | string;
  mobile?: null | string;
}

export interface SubcontractorPortalWorkerUpdate {
  worker_no?: string;
  first_name?: string;
  last_name?: string;
  preferred_name?: null | string;
  birth_date?: null | string;
  email?: null | string;
  phone?: null | string;
  mobile?: null | string;
  version_no: number;
}

export interface SubcontractorPortalWorkerQualificationCreate {
  qualification_type_id: string;
  certificate_no?: null | string;
  issued_at?: null | string;
  valid_until?: null | string;
  issuing_authority?: null | string;
  notes?: null | string;
}

export interface SubcontractorPortalWorkerQualificationUpdate {
  certificate_no?: null | string;
  issued_at?: null | string;
  valid_until?: null | string;
  issuing_authority?: null | string;
  notes?: null | string;
  version_no: number;
}

export interface SubcontractorWorkerQualificationProofUpload {
  title?: null | string;
  file_name: string;
  content_type: string;
  content_base64: string;
}

export interface SubcontractorWorkerQualificationProofLinkCreate {
  document_id: string;
  label?: null | string;
}

export interface SubcontractorWorkerQualificationProofRead {
  document_id: string;
  title: string;
  document_type_key: null | string;
  file_name: null | string;
  content_type: null | string;
  current_version_no: null | number;
  relation_type: string;
}

export interface SubcontractorWorkerQualificationRead {
  id: string;
  tenant_id: string;
  worker_id: string;
  qualification_type_id: string;
  qualification_type_code: null | string;
  qualification_type_label: null | string;
  certificate_no: null | string;
  issued_at: null | string;
  valid_until: null | string;
  issuing_authority: null | string;
  notes: null | string;
  status: string;
  archived_at: null | string;
  version_no: number;
  proofs: SubcontractorWorkerQualificationProofRead[];
}

export interface SubcontractorPortalWorkerRead {
  id: string;
  tenant_id: string;
  subcontractor_id: string;
  worker_no: string;
  first_name: string;
  last_name: string;
  preferred_name: null | string;
  email: null | string;
  mobile: null | string;
  status: string;
  archived_at: null | string;
  version_no: number;
  birth_date: null | string;
  phone: null | string;
  qualifications: SubcontractorWorkerQualificationRead[];
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

function generateRequestId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `sp-subcontractor-portal-${Date.now()}`;
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }

  const error = (value as Record<string, unknown>).error;
  return !!error && typeof error === "object" && typeof (error as Record<string, unknown>).message_key === "string";
}

async function request<T>(path: string, accessToken: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: init?.method ?? "GET",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      "X-Request-Id": generateRequestId(),
      ...(init?.headers ?? {}),
    },
    body: init?.body,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;
    if (isApiErrorEnvelope(payload)) {
      throw new AuthApiError(response.status, payload.error);
    }
    throw new AuthApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  return (await response.json()) as T;
}

export function getSubcontractorPortalPositions(accessToken: string) {
  return request<SubcontractorPortalPositionCollectionRead>("/api/portal/subcontractor/positions", accessToken);
}

export function getSubcontractorPortalSchedules(accessToken: string) {
  return request<SubcontractorPortalScheduleCollectionRead>("/api/portal/subcontractor/schedules", accessToken);
}

export function getSubcontractorPortalActuals(accessToken: string) {
  return request<SubcontractorPortalActualSummaryCollectionRead>("/api/portal/subcontractor/actuals", accessToken);
}

export function getSubcontractorPortalAttendance(accessToken: string) {
  return request<SubcontractorPortalAttendanceCollectionRead>("/api/portal/subcontractor/attendance", accessToken);
}

export function getSubcontractorPortalInvoiceChecks(accessToken: string) {
  return request<SubcontractorPortalInvoiceCheckCollectionRead>("/api/portal/subcontractor/invoice-checks", accessToken);
}

export function getSubcontractorPortalInvoiceCheckDetail(accessToken: string, invoiceCheckId: string) {
  return request<SubcontractorPortalInvoiceCheckDetailRead>(`/api/portal/subcontractor/invoice-checks/${invoiceCheckId}`, accessToken);
}

export function getSubcontractorPortalWatchbooks(accessToken: string) {
  return request<SubcontractorPortalWatchbookCollectionRead>("/api/portal/subcontractor/watchbooks", accessToken);
}

export function createSubcontractorPortalWatchbookEntry(
  accessToken: string,
  watchbookId: string,
  payload: SubcontractorPortalWatchbookEntryCreate,
) {
  return request(`/api/portal/subcontractor/watchbooks/${watchbookId}/entries`, accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getSubcontractorPortalAllocationCandidates(accessToken: string) {
  return request<SubcontractorPortalAllocationCandidateCollectionRead>(
    "/api/portal/subcontractor/allocation/candidates",
    accessToken,
  );
}

export function previewSubcontractorPortalAllocation(
  accessToken: string,
  payload: SubcontractorPortalAllocationRequest,
) {
  return request<SubcontractorPortalAllocationPreviewRead>(
    "/api/portal/subcontractor/allocation/preview",
    accessToken,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function submitSubcontractorPortalAllocation(
  accessToken: string,
  payload: SubcontractorPortalAllocationRequest,
) {
  return request<SubcontractorPortalAllocationResultRead>(
    "/api/portal/subcontractor/allocation/submit",
    accessToken,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function getSubcontractorPortalWorkerQualificationTypes(accessToken: string) {
  return request<SubcontractorPortalQualificationTypeOptionRead[]>(
    "/api/portal/subcontractor/worker-qualification-types",
    accessToken,
  );
}

export function getSubcontractorPortalWorkers(accessToken: string) {
  return request<SubcontractorWorkerListItem[]>("/api/portal/subcontractor/workers", accessToken);
}

export function createSubcontractorPortalWorker(accessToken: string, payload: SubcontractorPortalWorkerCreate) {
  return request<SubcontractorPortalWorkerRead>("/api/portal/subcontractor/workers", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getSubcontractorPortalWorker(accessToken: string, workerId: string) {
  return request<SubcontractorPortalWorkerRead>(`/api/portal/subcontractor/workers/${workerId}`, accessToken);
}

export function updateSubcontractorPortalWorker(
  accessToken: string,
  workerId: string,
  payload: SubcontractorPortalWorkerUpdate,
) {
  return request<SubcontractorPortalWorkerRead>(`/api/portal/subcontractor/workers/${workerId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getSubcontractorPortalWorkerQualifications(accessToken: string, workerId: string) {
  return request<SubcontractorWorkerQualificationRead[]>(
    `/api/portal/subcontractor/workers/${workerId}/qualifications`,
    accessToken,
  );
}

export function createSubcontractorPortalWorkerQualification(
  accessToken: string,
  workerId: string,
  payload: SubcontractorPortalWorkerQualificationCreate,
) {
  return request<SubcontractorWorkerQualificationRead>(
    `/api/portal/subcontractor/workers/${workerId}/qualifications`,
    accessToken,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function updateSubcontractorPortalWorkerQualification(
  accessToken: string,
  workerId: string,
  qualificationId: string,
  payload: SubcontractorPortalWorkerQualificationUpdate,
) {
  return request<SubcontractorWorkerQualificationRead>(
    `/api/portal/subcontractor/workers/${workerId}/qualifications/${qualificationId}`,
    accessToken,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export function uploadSubcontractorPortalWorkerQualificationProof(
  accessToken: string,
  workerId: string,
  qualificationId: string,
  payload: SubcontractorWorkerQualificationProofUpload,
) {
  return request<SubcontractorWorkerQualificationProofRead>(
    `/api/portal/subcontractor/workers/${workerId}/qualifications/${qualificationId}/proofs/upload`,
    accessToken,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
