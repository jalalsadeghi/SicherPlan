import { legacySessionRequest } from "./sessionRequest";

export type LifecycleStatus = "active" | "inactive" | "archived";

export interface CustomerListItem {
  id: string;
  tenant_id: string;
  customer_number: string;
  name: string;
  status: LifecycleStatus | string;
  version_no: number;
  classification_lookup_id?: string | null;
  customer_status_lookup_id?: string | null;
  default_branch_id?: string | null;
}

export interface CustomerContactRead {
  id: string;
  tenant_id: string;
  customer_id: string;
  full_name: string;
  title: string | null;
  function_label: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  is_primary_contact: boolean;
  is_billing_contact: boolean;
  user_id: string | null;
  notes: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface CustomerAddressRead {
  id: string;
  tenant_id: string;
  customer_id: string;
  address_id: string;
  address_type: "registered" | "billing" | "mailing" | "service";
  label: string | null;
  is_default: boolean;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
  address: {
    id: string;
    street_line_1: string;
    street_line_2: string | null;
    postal_code: string;
    city: string;
    state: string | null;
    country_code: string;
  } | null;
}

export interface CustomerAvailableAddressRead {
  id: string;
  street_line_1: string;
  street_line_2: string | null;
  postal_code: string;
  city: string;
  state: string | null;
  country_code: string;
}

export interface CustomerAvailableAddressCreatePayload {
  street_line_1: string;
  street_line_2?: null | string;
  postal_code: string;
  city: string;
  state?: null | string;
  country_code: string;
}

export interface CustomerRead extends CustomerListItem {
  legal_name: string | null;
  external_ref: string | null;
  legal_form_lookup_id: string | null;
  classification_lookup_id: string | null;
  ranking_lookup_id: string | null;
  customer_status_lookup_id: string | null;
  default_branch_id: string | null;
  default_mandate_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  portal_person_names_released: boolean;
  portal_person_names_released_at: string | null;
  portal_person_names_released_by_user_id: string | null;
  archived_at: string | null;
  contacts: CustomerContactRead[];
  addresses: CustomerAddressRead[];
}

export interface CustomerDashboardPlanItemRead {
  id: string;
  order_id: string;
  order_no: string;
  label: string;
  status: string;
  planning_mode_code: string;
  planning_from: string;
  planning_to: string;
  released_at: string | null;
}

export interface CustomerDashboardPlanningSummaryRead {
  total_plans_count: number;
  latest_plans: CustomerDashboardPlanItemRead[];
}

export interface CustomerDashboardFinanceSummaryRead {
  visibility: "available" | "restricted" | "unavailable";
  total_received_amount: string | null;
  currency_code: string | null;
  semantic_label: string | null;
}

export interface CustomerDashboardCalendarItemRead {
  id: string;
  source_type: string;
  source_ref_id: string;
  order_id: string | null;
  planning_record_id: string | null;
  title: string;
  starts_at: string | null;
  ends_at: string | null;
  status: string;
}

export interface CustomerDashboardRead {
  customer_id: string;
  planning_summary: CustomerDashboardPlanningSummaryRead;
  finance_summary: CustomerDashboardFinanceSummaryRead;
  calendar_items: CustomerDashboardCalendarItemRead[];
}

export interface CustomerHistoryEntryRead {
  id: string;
  tenant_id: string;
  customer_id: string;
  entry_type: string;
  title: string;
  summary: string;
  actor_user_id: string | null;
  related_contact_id: string | null;
  related_address_link_id: string | null;
  integration_job_id: string | null;
  sort_order: number;
  before_json: Record<string, unknown>;
  after_json: Record<string, unknown>;
  metadata_json: Record<string, unknown>;
  created_at: string;
  attachments: CustomerHistoryAttachmentRead[];
}

export interface CustomerHistoryAttachmentRead {
  document_id: string;
  title: string;
  document_type_key: string | null;
  file_name: string | null;
  content_type: string | null;
  current_version_no: number | null;
}

export interface CustomerLoginHistoryEntryRead {
  id: string;
  user_account_id: string | null;
  contact_id: string | null;
  contact_name: string | null;
  identifier: string;
  outcome: string;
  failure_reason: string | null;
  auth_method: string;
  created_at: string;
}

export interface CustomerEmployeeBlockRead {
  id: string;
  tenant_id: string;
  customer_id: string;
  employee_id: string;
  reason: string;
  effective_from: string;
  effective_to: string | null;
  status: string;
  version_no: number;
  created_at: string;
  updated_at: string;
  created_by_user_id: string | null;
  updated_by_user_id: string | null;
  archived_at: string | null;
}

export interface CustomerEmployeeBlockCollectionRead {
  customer_id: string;
  capability: {
    directory_available: boolean;
    employee_reference_mode: string;
    message_key: string;
  };
  items: CustomerEmployeeBlockRead[];
}

export interface CustomerPortalPrivacyRead {
  customer_id: string;
  person_names_released: boolean;
  person_names_released_at: string | null;
  person_names_released_by_user_id: string | null;
}

export interface CustomerPortalPrivacyUpdatePayload {
  person_names_released: boolean;
}

export interface CustomerBillingProfileRead {
  id: string;
  tenant_id: string;
  customer_id: string;
  invoice_email: string | null;
  payment_terms_days: number | null;
  payment_terms_note: string | null;
  tax_number: string | null;
  vat_id: string | null;
  tax_exempt: boolean;
  tax_exemption_reason: string | null;
  bank_account_holder: string | null;
  bank_iban: string | null;
  bank_bic: string | null;
  bank_name: string | null;
  contract_reference: string | null;
  debtor_number: string | null;
  e_invoice_enabled: boolean;
  leitweg_id: string | null;
  invoice_layout_code: string | null;
  shipping_method_code: string | null;
  dunning_policy_code: string | null;
  billing_note: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface CustomerBillingProfilePayload {
  tenant_id: string;
  customer_id: string;
  invoice_email?: string | null;
  payment_terms_days?: number | null;
  payment_terms_note?: string | null;
  tax_number?: string | null;
  vat_id?: string | null;
  tax_exempt?: boolean;
  tax_exemption_reason?: string | null;
  bank_account_holder?: string | null;
  bank_iban?: string | null;
  bank_bic?: string | null;
  bank_name?: string | null;
  contract_reference?: string | null;
  debtor_number?: string | null;
  e_invoice_enabled?: boolean;
  leitweg_id?: string | null;
  invoice_layout_code?: string | null;
  shipping_method_code?: string | null;
  dunning_policy_code?: string | null;
  billing_note?: string | null;
}

export interface CustomerBillingProfileUpdatePayload
  extends Partial<CustomerBillingProfilePayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerInvoicePartyRead {
  id: string;
  tenant_id: string;
  customer_id: string;
  company_name: string;
  contact_name: string | null;
  address_id: string;
  invoice_email: string | null;
  invoice_layout_lookup_id: string | null;
  external_ref: string | null;
  is_default: boolean;
  note: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
  address: CustomerAddressRead["address"] | null;
}

export interface CustomerInvoicePartyPayload {
  tenant_id: string;
  customer_id: string;
  company_name: string;
  contact_name?: string | null;
  address_id: string;
  invoice_email?: string | null;
  invoice_layout_lookup_id?: string | null;
  external_ref?: string | null;
  is_default?: boolean;
  note?: string | null;
}

export interface CustomerInvoicePartyUpdatePayload
  extends Partial<CustomerInvoicePartyPayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerRateLineRead {
  id: string;
  tenant_id: string;
  rate_card_id: string;
  line_kind: string;
  function_type_id: string | null;
  qualification_type_id: string | null;
  function_type: CustomerCatalogOptionRead | null;
  qualification_type: CustomerCatalogOptionRead | null;
  planning_mode_code: string | null;
  billing_unit: string;
  unit_price: string;
  minimum_quantity: string | null;
  sort_order: number;
  notes: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface CustomerSurchargeRuleRead {
  id: string;
  tenant_id: string;
  rate_card_id: string;
  surcharge_type: string;
  effective_from: string;
  effective_to: string | null;
  weekday_mask: string | null;
  time_from_minute: number | null;
  time_to_minute: number | null;
  region_code: string | null;
  percent_value: string | null;
  fixed_amount: string | null;
  currency_code: string | null;
  sort_order: number;
  notes: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
}

export interface CustomerRateCardRead {
  id: string;
  tenant_id: string;
  customer_id: string;
  rate_kind: string;
  currency_code: string;
  effective_from: string;
  effective_to: string | null;
  notes: string | null;
  status: LifecycleStatus | string;
  version_no: number;
  archived_at: string | null;
  rate_lines: CustomerRateLineRead[];
  surcharge_rules: CustomerSurchargeRuleRead[];
}

export interface CustomerRateCardPayload {
  tenant_id: string;
  customer_id: string;
  rate_kind: string;
  currency_code: string;
  effective_from: string;
  effective_to?: string | null;
  notes?: string | null;
}

export interface CustomerRateCardUpdatePayload extends Partial<CustomerRateCardPayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerRateLinePayload {
  tenant_id: string;
  rate_card_id: string;
  line_kind: string;
  function_type_id?: string | null;
  qualification_type_id?: string | null;
  planning_mode_code?: string | null;
  billing_unit: string;
  unit_price: string;
  minimum_quantity?: string | null;
  sort_order?: number;
  notes?: string | null;
}

export interface CustomerRateLineUpdatePayload extends Partial<CustomerRateLinePayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerSurchargeRulePayload {
  tenant_id: string;
  rate_card_id: string;
  surcharge_type: string;
  effective_from: string;
  effective_to?: string | null;
  weekday_mask?: string | null;
  time_from_minute?: number | null;
  time_to_minute?: number | null;
  region_code?: string | null;
  percent_value?: string | null;
  fixed_amount?: string | null;
  currency_code?: string | null;
  sort_order?: number;
  notes?: string | null;
}

export interface CustomerSurchargeRuleUpdatePayload
  extends Partial<CustomerSurchargeRulePayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerCommercialProfileRead {
  customer_id: string;
  tenant_id: string;
  billing_profile: CustomerBillingProfileRead | null;
  invoice_parties: CustomerInvoicePartyRead[];
  rate_cards: CustomerRateCardRead[];
}

export interface CustomerPricingProfileRead {
  tenant_id: string;
  customer_id: string;
  rate_cards: CustomerRateCardRead[];
}

export interface CustomerFilterParams {
  search?: string;
  lifecycle_status?: string;
  default_branch_id?: string;
  default_mandate_id?: string;
  include_archived?: boolean;
}

export interface CustomerCreatePayload {
  tenant_id: string;
  customer_number: string;
  name: string;
  status?: LifecycleStatus | string | null;
  legal_name?: string | null;
  external_ref?: string | null;
  legal_form_lookup_id?: string | null;
  classification_lookup_id?: string | null;
  ranking_lookup_id?: string | null;
  customer_status_lookup_id?: string | null;
  default_branch_id?: string | null;
  default_mandate_id?: string | null;
  notes?: string | null;
}

export interface CustomerUpdatePayload extends Partial<CustomerCreatePayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerContactPayload {
  tenant_id: string;
  customer_id: string;
  full_name: string;
  title?: string | null;
  function_label?: string | null;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  is_primary_contact?: boolean;
  is_billing_contact?: boolean;
  user_id?: string | null;
  notes?: string | null;
}

export interface CustomerContactUpdatePayload extends Partial<CustomerContactPayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerAddressPayload {
  tenant_id: string;
  customer_id: string;
  address_id: string;
  address_type: "registered" | "billing" | "mailing" | "service";
  label?: string | null;
  is_default?: boolean;
}

export interface CustomerAddressUpdatePayload extends Partial<CustomerAddressPayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerReferenceOptionRead {
  id: string;
  code: string;
  label: string;
  description: string | null;
  sort_order: number;
}

export interface CustomerBranchOptionRead {
  id: string;
  code: string;
  name: string;
}

export interface CustomerMandateOptionRead {
  id: string;
  branch_id: string;
  code: string;
  name: string;
}

export interface CustomerCatalogOptionRead {
  id: string;
  code: string;
  label: string;
  description: string | null;
  is_active: boolean;
  status: string;
  archived_at: string | null;
}

export interface CustomerReferenceDataRead {
  legal_forms: CustomerReferenceOptionRead[];
  classifications: CustomerReferenceOptionRead[];
  rankings: CustomerReferenceOptionRead[];
  customer_statuses: CustomerReferenceOptionRead[];
  invoice_layouts: CustomerReferenceOptionRead[];
  shipping_methods: CustomerReferenceOptionRead[];
  dunning_policies: CustomerReferenceOptionRead[];
  function_types: CustomerCatalogOptionRead[];
  qualification_types: CustomerCatalogOptionRead[];
  branches: CustomerBranchOptionRead[];
  mandates: CustomerMandateOptionRead[];
}

export interface CustomerHistoryAttachmentLinkPayload {
  document_id: string;
  label?: string | null;
}

export interface CustomerEmployeeBlockPayload {
  tenant_id: string;
  customer_id: string;
  employee_id: string;
  reason: string;
  effective_from: string;
  effective_to?: string | null;
}

export interface CustomerEmployeeBlockUpdatePayload extends Partial<CustomerEmployeeBlockPayload> {
  status?: LifecycleStatus | string | null;
  archived_at?: string | null;
  version_no: number;
}

export interface CustomerExportPayload {
  tenant_id: string;
  include_archived?: boolean;
  search?: string | null;
}

export interface CustomerExportResult {
  tenant_id: string;
  job_id: string;
  document_id: string;
  version_no: number;
  file_name: string;
  row_count: number;
}

export interface CustomerVCardResult {
  tenant_id: string;
  customer_id: string;
  contact_id: string;
  document_id: string;
  version_no: number;
  file_name: string;
  content_type: string;
  content_base64: string;
}

interface ApiErrorEnvelope {
  error: {
    code: string;
    message_key: string;
    request_id: string;
    details: Record<string, unknown>;
  };
}

export class CustomerAdminApiError extends Error {
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

  return `sp-${Date.now()}`;
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
  _accessToken?: string,
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
      throw new CustomerAdminApiError(response.status, payload.error);
    }

    throw new CustomerAdminApiError(response.status, {
      code: "platform.internal",
      message_key: "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  return (await response.json()) as T;
}

function buildQuery(params: CustomerFilterParams) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.lifecycle_status) query.set("lifecycle_status", params.lifecycle_status);
  if (params.default_branch_id) query.set("default_branch_id", params.default_branch_id);
  if (params.default_mandate_id) query.set("default_mandate_id", params.default_mandate_id);
  if (params.include_archived) query.set("include_archived", "true");
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function listCustomers(tenantId: string, accessToken: string, params: CustomerFilterParams) {
  return request<CustomerListItem[]>(
    `/api/customers/tenants/${tenantId}/customers${buildQuery(params)}`,
    accessToken,
  );
}

export function getCustomer(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerRead>(`/api/customers/tenants/${tenantId}/customers/${customerId}`, accessToken);
}

export function getCustomerDashboard(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerDashboardRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/dashboard`,
    accessToken,
  );
}

export function getCustomerReferenceData(tenantId: string, accessToken: string) {
  return request<CustomerReferenceDataRead>(
    `/api/customers/tenants/${tenantId}/customers/reference-data`,
    accessToken,
  );
}

export function createCustomer(tenantId: string, accessToken: string, payload: CustomerCreatePayload) {
  return request<CustomerRead>(`/api/customers/tenants/${tenantId}/customers`, accessToken, {
    method: "POST",
    body: payload,
  });
}

export function updateCustomer(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerUpdatePayload,
) {
  return request<CustomerRead>(`/api/customers/tenants/${tenantId}/customers/${customerId}`, accessToken, {
    method: "PATCH",
    body: payload,
  });
}

export function createCustomerContact(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerContactPayload,
) {
  return request<CustomerContactRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/contacts`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateCustomerContact(
  tenantId: string,
  customerId: string,
  contactId: string,
  accessToken: string,
  payload: CustomerContactUpdatePayload,
) {
  return request<CustomerContactRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/contacts/${contactId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function createCustomerAddress(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerAddressPayload,
) {
  return request<CustomerAddressRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/addresses`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function listCustomerAddresses(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerAddressRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/addresses`,
    accessToken,
  );
}

export function listCustomerAvailableAddresses(
  tenantId: string,
  customerId: string,
  accessToken: string,
  params: { search?: string; limit?: number } = {},
) {
  const query = new URLSearchParams();
  if (params.search?.trim()) {
    query.set("search", params.search.trim());
  }
  if (params.limit) {
    query.set("limit", String(params.limit));
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<CustomerAvailableAddressRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/address-options${suffix}`,
    accessToken,
  );
}

export function createCustomerAvailableAddress(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerAvailableAddressCreatePayload,
) {
  return request<CustomerAvailableAddressRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/address-options`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateCustomerAddress(
  tenantId: string,
  customerId: string,
  addressLinkId: string,
  accessToken: string,
  payload: CustomerAddressUpdatePayload,
) {
  return request<CustomerAddressRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/addresses/${addressLinkId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listCustomerHistory(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerHistoryEntryRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/history`,
    accessToken,
  );
}

export function linkCustomerHistoryAttachment(
  tenantId: string,
  customerId: string,
  historyEntryId: string,
  accessToken: string,
  payload: CustomerHistoryAttachmentLinkPayload,
) {
  return request<CustomerHistoryAttachmentRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/history/${historyEntryId}/attachments`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function listCustomerPortalLoginHistory(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerLoginHistoryEntryRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-login-history`,
    accessToken,
  );
}

export function getCustomerPortalPrivacy(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerPortalPrivacyRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-privacy`,
    accessToken,
  );
}

export function updateCustomerPortalPrivacy(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerPortalPrivacyUpdatePayload,
) {
  return request<CustomerPortalPrivacyRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/portal-privacy`,
    accessToken,
    {
      method: "PUT",
      body: payload,
    },
  );
}

export function listCustomerEmployeeBlocks(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerEmployeeBlockCollectionRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/employee-blocks`,
    accessToken,
  );
}

export function createCustomerEmployeeBlock(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerEmployeeBlockPayload,
) {
  return request<CustomerEmployeeBlockRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/employee-blocks`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateCustomerEmployeeBlock(
  tenantId: string,
  customerId: string,
  blockId: string,
  accessToken: string,
  payload: CustomerEmployeeBlockUpdatePayload,
) {
  return request<CustomerEmployeeBlockRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/employee-blocks/${blockId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function exportCustomers(tenantId: string, accessToken: string, payload: CustomerExportPayload) {
  return request<CustomerExportResult>(`/api/customers/tenants/${tenantId}/customers/exports`, accessToken, {
    method: "POST",
    body: payload,
  });
}

function extractDownloadFileName(contentDisposition: string | null, fallback: string) {
  if (!contentDisposition) {
    return fallback;
  }
  const match = contentDisposition.match(/filename=\"?([^\";]+)\"?/i);
  return match?.[1] ?? fallback;
}

export async function downloadCustomerDocument(
  tenantId: string,
  documentId: string,
  versionNo: number,
  accessToken: string,
  fallbackFileName = `document-${documentId}`,
) {
  const response = await legacySessionRequest(
    `/api/platform/tenants/${tenantId}/documents/${documentId}/versions/${versionNo}/download`,
    { accessToken },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as unknown;

    if (isApiErrorEnvelope(payload)) {
      throw new CustomerAdminApiError(response.status, payload.error);
    }

    throw new CustomerAdminApiError(response.status, {
      code: "platform.internal",
      message_key: response.status === 404 ? "errors.platform.http_not_found" : "errors.platform.internal",
      request_id: "",
      details: {},
    });
  }

  const blob = await response.blob();
  return {
    blob,
    fileName: extractDownloadFileName(response.headers.get("content-disposition"), fallbackFileName),
  };
}

export function exportCustomerVCard(
  tenantId: string,
  customerId: string,
  contactId: string,
  accessToken: string,
) {
  return request<CustomerVCardResult>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/contacts/${contactId}/vcard`,
    accessToken,
    {
      method: "POST",
    },
  );
}

export function getCustomerCommercialProfile(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerCommercialProfileRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/commercial-profile`,
    accessToken,
  );
}

export function getCustomerPricingProfile(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerPricingProfileRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/pricing-profile`,
    accessToken,
  );
}

export function upsertCustomerBillingProfile(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerBillingProfilePayload,
) {
  return request<CustomerBillingProfileRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/billing-profile`,
    accessToken,
    {
      method: "PUT",
      body: payload,
    },
  );
}

export function updateCustomerBillingProfile(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerBillingProfileUpdatePayload,
) {
  return request<CustomerBillingProfileRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/billing-profile`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listCustomerInvoiceParties(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerInvoicePartyRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/invoice-parties`,
    accessToken,
  );
}

export function createCustomerInvoiceParty(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerInvoicePartyPayload,
) {
  return request<CustomerInvoicePartyRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/invoice-parties`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateCustomerInvoiceParty(
  tenantId: string,
  customerId: string,
  invoicePartyId: string,
  accessToken: string,
  payload: CustomerInvoicePartyUpdatePayload,
) {
  return request<CustomerInvoicePartyRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/invoice-parties/${invoicePartyId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listCustomerRateCards(tenantId: string, customerId: string, accessToken: string) {
  return request<CustomerRateCardRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards`,
    accessToken,
  );
}

export function createCustomerRateCard(
  tenantId: string,
  customerId: string,
  accessToken: string,
  payload: CustomerRateCardPayload,
) {
  return request<CustomerRateCardRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateCustomerRateCard(
  tenantId: string,
  customerId: string,
  rateCardId: string,
  accessToken: string,
  payload: CustomerRateCardUpdatePayload,
) {
  return request<CustomerRateCardRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards/${rateCardId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listCustomerRateLines(
  tenantId: string,
  customerId: string,
  rateCardId: string,
  accessToken: string,
) {
  return request<CustomerRateLineRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards/${rateCardId}/rate-lines`,
    accessToken,
  );
}

export function createCustomerRateLine(
  tenantId: string,
  customerId: string,
  rateCardId: string,
  accessToken: string,
  payload: CustomerRateLinePayload,
) {
  return request<CustomerRateLineRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards/${rateCardId}/rate-lines`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateCustomerRateLine(
  tenantId: string,
  customerId: string,
  rateCardId: string,
  rateLineId: string,
  accessToken: string,
  payload: CustomerRateLineUpdatePayload,
) {
  return request<CustomerRateLineRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards/${rateCardId}/rate-lines/${rateLineId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export function listCustomerSurchargeRules(
  tenantId: string,
  customerId: string,
  rateCardId: string,
  accessToken: string,
) {
  return request<CustomerSurchargeRuleRead[]>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards/${rateCardId}/surcharge-rules`,
    accessToken,
  );
}

export function createCustomerSurchargeRule(
  tenantId: string,
  customerId: string,
  rateCardId: string,
  accessToken: string,
  payload: CustomerSurchargeRulePayload,
) {
  return request<CustomerSurchargeRuleRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards/${rateCardId}/surcharge-rules`,
    accessToken,
    {
      method: "POST",
      body: payload,
    },
  );
}

export function updateCustomerSurchargeRule(
  tenantId: string,
  customerId: string,
  rateCardId: string,
  surchargeRuleId: string,
  accessToken: string,
  payload: CustomerSurchargeRuleUpdatePayload,
) {
  return request<CustomerSurchargeRuleRead>(
    `/api/customers/tenants/${tenantId}/customers/${customerId}/rate-cards/${rateCardId}/surcharge-rules/${surchargeRuleId}`,
    accessToken,
    {
      method: "PATCH",
      body: payload,
    },
  );
}
