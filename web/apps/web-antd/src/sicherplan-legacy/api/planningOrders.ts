import { webAppConfig } from "@/config/env";

export interface PlanningDocumentRead {
  id: string;
  tenant_id: string;
  title: string;
  current_version_no: number;
  status: string;
  created_at?: string;
  document_type?: { id: string; key: string; name: string } | null;
  document_type_id?: string | null;
  source_label?: string | null;
  metadata_json?: Record<string, unknown>;
}

export interface PlanningCatalogRecordRead {
  id: string;
  tenant_id: string;
  customer_id?: string | null;
  code?: string | null;
  label?: string | null;
  name?: string | null;
  status?: string | null;
}

export interface PlanningReferenceOptionRead {
  id?: string | null;
  code: string;
  label: string;
  description?: string | null;
  sort_order?: number;
}

export interface OrderEquipmentLineRead {
  id: string;
  tenant_id: string;
  order_id: string;
  equipment_item_id: string;
  required_qty: number;
  notes: string | null;
  status: string;
  version_no: number;
  archived_at: string | null;
}

export interface OrderRequirementLineRead {
  id: string;
  tenant_id: string;
  order_id: string;
  requirement_type_id: string;
  function_type_id: string | null;
  qualification_type_id: string | null;
  min_qty: number;
  target_qty: number;
  notes: string | null;
  status: string;
  version_no: number;
  archived_at: string | null;
}

export interface CustomerOrderListItem {
  id: string;
  tenant_id: string;
  customer_id: string;
  requirement_type_id: string;
  patrol_route_id: string | null;
  order_no: string;
  title: string;
  service_category_code: string;
  service_from: string;
  service_to: string;
  release_state: string;
  released_at: string | null;
  status: string;
  version_no: number;
}

export interface CustomerOrderRead extends CustomerOrderListItem {
  security_concept_text: string | null;
  notes: string | null;
  released_by_user_id: string | null;
  attachments: PlanningDocumentRead[];
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

export type CustomerOrderPlanningEntityType = 'site' | 'event_venue' | 'trade_fair' | 'patrol_route';

export interface CustomerOrderListFilters {
  customer_id?: string;
  include_archived?: boolean;
  lifecycle_status?: string;
  planning_entity_id?: string;
  planning_entity_type?: CustomerOrderPlanningEntityType;
  release_state?: string;
  search?: string;
  service_from?: string;
  service_to?: string;
}

export interface PlanningRecordListItem {
  id: string;
  tenant_id: string;
  order_id: string;
  parent_planning_record_id: string | null;
  dispatcher_user_id: string | null;
  planning_mode_code: string;
  name: string;
  planning_from: string;
  planning_to: string;
  release_state: string;
  released_at: string | null;
  created_at: string;
  status: string;
  version_no: number;
}

export interface PlanningRecordListFilters {
  customer_id?: string;
  dispatcher_user_id?: string;
  include_archived?: boolean;
  lifecycle_status?: string;
  order_id?: string;
  planning_entity_id?: string;
  planning_entity_type?: CustomerOrderPlanningEntityType;
  planning_from?: string;
  planning_mode_code?: string;
  planning_to?: string;
  release_state?: string;
  search?: string;
}

export interface PlanningRecordRead extends PlanningRecordListItem {
  released_by_user_id: string | null;
  notes: string | null;
  event_detail?: { event_venue_id: string; setup_note: string | null } | null;
  site_detail?: { site_id: string; watchbook_scope_note: string | null } | null;
  trade_fair_detail?: { trade_fair_id: string; trade_fair_zone_id: string | null; stand_note: string | null } | null;
  patrol_detail?: { patrol_route_id: string; execution_note: string | null } | null;
  attachments: PlanningDocumentRead[];
  created_at: string;
  updated_at: string;
  archived_at: string | null;
}

export interface PlanningDispatcherCandidateRead {
  id: string;
  tenant_id: string;
  username: string;
  email: string | null;
  full_name: string;
  status: string;
  role_keys: string[];
  archived_at?: string | null;
}

export interface PlanningCommercialIssueRead {
  code: string;
  severity: string;
  message_key: string;
}

export interface PlanningCommercialLinkRead {
  tenant_id: string;
  customer_id: string;
  order_id: string;
  planning_record_id: string | null;
  billing_profile_id: string | null;
  default_invoice_party_id: string | null;
  shipping_method_code: string | null;
  invoice_layout_code: string | null;
  dunning_policy_code: string | null;
  e_invoice_enabled: boolean;
  rate_card_ids: string[];
  is_release_ready: boolean;
  blocking_issues: PlanningCommercialIssueRead[];
  warning_issues: PlanningCommercialIssueRead[];
}

export class PlanningOrdersApiError extends Error {
  status: number;
  messageKey: string;
  details: Record<string, unknown>;

  constructor(status: number, payload: { message_key: string; details: Record<string, unknown> }) {
    super(payload.message_key);
    this.status = status;
    this.messageKey = payload.message_key;
    this.details = payload.details;
  }
}

function generateRequestId() {
  return `planning-orders-${Math.random().toString(36).slice(2, 10)}`;
}

function isApiErrorEnvelope(payload: unknown): payload is { error: { message_key: string; details: Record<string, unknown> } } {
  if (!payload || typeof payload !== "object" || !("error" in payload)) {
    return false;
  }
  const { error } = payload as { error?: unknown };
  return Boolean(
    error &&
      typeof error === "object" &&
      "message_key" in error &&
      typeof (error as { message_key?: unknown }).message_key === "string",
  );
}

type JsonRequestOptions = Omit<RequestInit, "body"> & { body?: unknown };

async function request<T>(path: string, accessToken: string, options: JsonRequestOptions = {}): Promise<T> {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": generateRequestId(),
      ...(options.headers ?? {}),
    },
    body: options.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new PlanningOrdersApiError(response.status, payload.error);
    }
    throw new PlanningOrdersApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }

  return (response.status === 204 ? undefined : response.json()) as T;
}

function queryString(params: object) {
  const query = new URLSearchParams();
  Object.entries(params as Record<string, unknown>).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "" || value === false) {
      return;
    }
    query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listCustomerOrders(tenantId: string, accessToken: string, filters: CustomerOrderListFilters) {
  return request<CustomerOrderListItem[]>(
    `/api/planning/tenants/${tenantId}/ops/orders${queryString(filters)}`,
    accessToken,
  );
}

export function listServiceCategoryOptions(tenantId: string, accessToken: string) {
  return request<PlanningReferenceOptionRead[]>(
    `/api/planning/tenants/${tenantId}/ops/service-category-options`,
    accessToken,
  );
}

export function getCustomerOrder(tenantId: string, orderId: string, accessToken: string) {
  return request<CustomerOrderRead>(`/api/planning/tenants/${tenantId}/ops/orders/${orderId}`, accessToken);
}

export function createCustomerOrder(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<CustomerOrderRead>(`/api/planning/tenants/${tenantId}/ops/orders`, accessToken, { method: "POST", body: payload });
}

export function updateCustomerOrder(tenantId: string, orderId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<CustomerOrderRead>(`/api/planning/tenants/${tenantId}/ops/orders/${orderId}`, accessToken, { method: "PATCH", body: payload });
}

export function setCustomerOrderReleaseState(tenantId: string, orderId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<CustomerOrderRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/release-state`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function listOrderEquipmentLines(tenantId: string, orderId: string, accessToken: string) {
  return request<OrderEquipmentLineRead[]>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/equipment-lines`,
    accessToken,
  );
}

export function createOrderEquipmentLine(tenantId: string, orderId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<OrderEquipmentLineRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/equipment-lines`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function updateOrderEquipmentLine(tenantId: string, orderId: string, rowId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<OrderEquipmentLineRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/equipment-lines/${rowId}`,
    accessToken,
    { method: "PATCH", body: payload },
  );
}

export function listOrderRequirementLines(tenantId: string, orderId: string, accessToken: string) {
  return request<OrderRequirementLineRead[]>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/requirement-lines`,
    accessToken,
  );
}

export function createOrderRequirementLine(tenantId: string, orderId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<OrderRequirementLineRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/requirement-lines`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function updateOrderRequirementLine(tenantId: string, orderId: string, rowId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<OrderRequirementLineRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/requirement-lines/${rowId}`,
    accessToken,
    { method: "PATCH", body: payload },
  );
}

export function listOrderAttachments(tenantId: string, orderId: string, accessToken: string) {
  return request<PlanningDocumentRead[]>(`/api/planning/tenants/${tenantId}/ops/orders/${orderId}/attachments`, accessToken);
}

export function createOrderAttachment(tenantId: string, orderId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PlanningDocumentRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/attachments`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function linkOrderAttachment(tenantId: string, orderId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PlanningDocumentRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/attachments/link`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function getOrderCommercialLink(tenantId: string, orderId: string, accessToken: string) {
  return request<PlanningCommercialLinkRead>(
    `/api/planning/tenants/${tenantId}/ops/orders/${orderId}/commercial-link`,
    accessToken,
  );
}

export function listPlanningRecords(tenantId: string, accessToken: string, filters: PlanningRecordListFilters) {
  return request<PlanningRecordListItem[]>(
    `/api/planning/tenants/${tenantId}/ops/planning-records${queryString(filters)}`,
    accessToken,
  );
}

export function getPlanningRecord(tenantId: string, planningRecordId: string, accessToken: string) {
  return request<PlanningRecordRead>(`/api/planning/tenants/${tenantId}/ops/planning-records/${planningRecordId}`, accessToken);
}

export function listPlanningDispatcherCandidates(tenantId: string, accessToken: string) {
  return request<PlanningDispatcherCandidateRead[]>(
    `/api/planning/tenants/${tenantId}/ops/planning-records/dispatcher-candidates`,
    accessToken,
  );
}

export function createPlanningRecord(tenantId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PlanningRecordRead>(
    `/api/planning/tenants/${tenantId}/ops/planning-records`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function updatePlanningRecord(tenantId: string, planningRecordId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PlanningRecordRead>(
    `/api/planning/tenants/${tenantId}/ops/planning-records/${planningRecordId}`,
    accessToken,
    { method: "PATCH", body: payload },
  );
}

export function setPlanningRecordReleaseState(tenantId: string, planningRecordId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PlanningRecordRead>(
    `/api/planning/tenants/${tenantId}/ops/planning-records/${planningRecordId}/release-state`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function listPlanningRecordAttachments(tenantId: string, planningRecordId: string, accessToken: string) {
  return request<PlanningDocumentRead[]>(
    `/api/planning/tenants/${tenantId}/ops/planning-records/${planningRecordId}/attachments`,
    accessToken,
  );
}

export function createPlanningRecordAttachment(tenantId: string, planningRecordId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PlanningDocumentRead>(
    `/api/planning/tenants/${tenantId}/ops/planning-records/${planningRecordId}/attachments`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function linkPlanningRecordAttachment(tenantId: string, planningRecordId: string, accessToken: string, payload: Record<string, unknown>) {
  return request<PlanningDocumentRead>(
    `/api/planning/tenants/${tenantId}/ops/planning-records/${planningRecordId}/attachments/link`,
    accessToken,
    { method: "POST", body: payload },
  );
}

export function listDocuments(
  tenantId: string,
  accessToken: string,
  filters: { document_type_code?: string; linked_entity?: string; limit?: number; search?: string } = {},
) {
  return request<PlanningDocumentRead[]>(
    `/api/platform/tenants/${tenantId}/documents${queryString(filters)}`,
    accessToken,
  );
}

export function getPlanningRecordCommercialLink(tenantId: string, planningRecordId: string, accessToken: string) {
  return request<PlanningCommercialLinkRead>(
    `/api/planning/tenants/${tenantId}/ops/planning-records/${planningRecordId}/commercial-link`,
    accessToken,
  );
}

export async function downloadPlanningDocument(
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
      throw new PlanningOrdersApiError(response.status, payload.error);
    }
    throw new PlanningOrdersApiError(response.status, {
      message_key: response.status === 404 ? "errors.platform.http_not_found" : "errors.platform.internal",
      details: {},
    });
  }

  return {
    blob: await response.blob(),
    fileName: response.headers.get("Content-Disposition")?.match(/filename=\"?([^\";]+)\"?/i)?.[1] ?? `document-${documentId}`,
  };
}
