import { webAppConfig } from "@/config/env";

export interface PlanningListItem {
  id: string;
  tenant_id: string;
  customer_id: string;
  status: string;
  version_no: number;
  code?: string;
  label?: string;
  site_no?: string;
  venue_no?: string;
  fair_no?: string;
  route_no?: string;
  name?: string;
}

export interface TradeFairZoneRead {
  id: string;
  tenant_id: string;
  trade_fair_id: string;
  zone_type_code: string;
  zone_code: string;
  label: string;
  notes: string | null;
  status: string;
  version_no: number;
  archived_at: string | null;
}

export interface PatrolCheckpointRead {
  id: string;
  tenant_id: string;
  patrol_route_id: string;
  sequence_no: number;
  checkpoint_code: string;
  label: string;
  latitude: string | number;
  longitude: string | number;
  scan_type_code: string;
  expected_token_value: string | null;
  minimum_dwell_seconds: number;
  notes: string | null;
  status: string;
  version_no: number;
  archived_at: string | null;
}

export interface PlanningDetailRead extends PlanningListItem {
  default_planning_mode_code?: string;
  unit_of_measure_code?: string;
  address_id?: string | null;
  timezone?: string | null;
  latitude?: string | number | null;
  longitude?: string | number | null;
  watchbook_enabled?: boolean;
  notes?: string | null;
  venue_id?: string | null;
  start_date?: string;
  end_date?: string;
  site_id?: string | null;
  meeting_address_id?: string | null;
  start_point_text?: string | null;
  end_point_text?: string | null;
  travel_policy_code?: string | null;
  archived_at?: string | null;
  zones?: TradeFairZoneRead[];
  checkpoints?: PatrolCheckpointRead[];
}

export interface PlanningImportRowResult {
  row_no: number;
  entity_ref: string | null;
  status: string;
  messages: string[];
  entity_id: string | null;
}

export interface PlanningImportDryRunResult {
  tenant_id: string;
  entity_key: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: PlanningImportRowResult[];
}

export interface PlanningImportExecuteResult extends PlanningImportDryRunResult {
  job_id: string;
  job_status: string;
  created_rows: number;
  updated_rows: number;
  result_document_ids: string[];
}

export interface PlanningReferenceOptionRead {
  id?: string | null;
  code: string;
  label: string;
  description?: string | null;
  sort_order?: number;
}

export class PlanningAdminApiError extends Error {
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
  return `planning-${Math.random().toString(36).slice(2, 10)}`;
}

function isApiErrorEnvelope(payload) {
  return payload && typeof payload === "object" && payload.error && typeof payload.error.message_key === "string";
}

async function request(
  path: string,
  accessToken: string,
  options: { method?: string; body?: unknown } = {},
) {
  const response = await fetch(`${webAppConfig.apiBaseUrl}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "X-Request-Id": generateRequestId(),
    },
    body: options.body == null ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    if (isApiErrorEnvelope(payload)) {
      throw new PlanningAdminApiError(response.status, payload.error);
    }
    throw new PlanningAdminApiError(response.status, { message_key: "errors.platform.internal", details: {} });
  }

  return response.status === 204 ? undefined : response.json();
}

function buildQuery(params) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.customer_id) query.set("customer_id", params.customer_id);
  if (params.lifecycle_status) query.set("lifecycle_status", params.lifecycle_status);
  if (params.include_archived) query.set("include_archived", "true");
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

const ENTITY_PATHS = {
  requirement_type: "requirement-types",
  equipment_item: "equipment-items",
  site: "sites",
  event_venue: "event-venues",
  trade_fair: "trade-fairs",
  patrol_route: "patrol-routes",
};

export function listPlanningRecords(entityKey, tenantId, accessToken, filters) {
  return request(`/api/planning/tenants/${tenantId}/ops/${ENTITY_PATHS[entityKey]}${buildQuery(filters)}`, accessToken);
}

export function getPlanningRecord(entityKey, tenantId, recordId, accessToken) {
  return request(`/api/planning/tenants/${tenantId}/ops/${ENTITY_PATHS[entityKey]}/${recordId}`, accessToken);
}

export function listEquipmentUnitOptions(tenantId, accessToken) {
  return request(`/api/planning/tenants/${tenantId}/ops/equipment-unit-options`, accessToken);
}

export function createPlanningRecord(entityKey, tenantId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/${ENTITY_PATHS[entityKey]}`, accessToken, { method: "POST", body: payload });
}

export function updatePlanningRecord(entityKey, tenantId, recordId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/${ENTITY_PATHS[entityKey]}/${recordId}`, accessToken, { method: "PATCH", body: payload });
}

export function listTradeFairZones(tenantId, tradeFairId, accessToken) {
  return request(`/api/planning/tenants/${tenantId}/ops/trade-fairs/${tradeFairId}/zones`, accessToken);
}

export function createTradeFairZone(tenantId, tradeFairId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/trade-fairs/${tradeFairId}/zones`, accessToken, { method: "POST", body: payload });
}

export function updateTradeFairZone(tenantId, tradeFairId, zoneId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/trade-fairs/${tradeFairId}/zones/${zoneId}`, accessToken, { method: "PATCH", body: payload });
}

export function listPatrolCheckpoints(tenantId, patrolRouteId, accessToken) {
  return request(`/api/planning/tenants/${tenantId}/ops/patrol-routes/${patrolRouteId}/checkpoints`, accessToken);
}

export function createPatrolCheckpoint(tenantId, patrolRouteId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/patrol-routes/${patrolRouteId}/checkpoints`, accessToken, { method: "POST", body: payload });
}

export function updatePatrolCheckpoint(tenantId, patrolRouteId, checkpointId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/patrol-routes/${patrolRouteId}/checkpoints/${checkpointId}`, accessToken, { method: "PATCH", body: payload });
}

export function importPlanningDryRun(tenantId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/import/dry-run`, accessToken, { method: "POST", body: payload });
}

export function importPlanningExecute(tenantId, accessToken, payload) {
  return request(`/api/planning/tenants/${tenantId}/ops/import/execute`, accessToken, { method: "POST", body: payload });
}
