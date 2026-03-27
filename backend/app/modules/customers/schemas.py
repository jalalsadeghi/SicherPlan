"""Pydantic schemas for CRM customer master data and related records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.core.schemas import AddressRead


class CustomerFilter(BaseModel):
    search: str | None = None
    lifecycle_status: str | None = None
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    include_archived: bool = False


class CustomerCreate(BaseModel):
    tenant_id: str
    customer_number: str
    name: str
    status: str | None = None
    legal_name: str | None = None
    external_ref: str | None = None
    legal_form_lookup_id: str | None = None
    classification_lookup_id: str | None = None
    ranking_lookup_id: str | None = None
    customer_status_lookup_id: str | None = None
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    notes: str | None = None


class CustomerUpdate(BaseModel):
    customer_number: str | None = None
    name: str | None = None
    legal_name: str | None = None
    external_ref: str | None = None
    legal_form_lookup_id: str | None = None
    classification_lookup_id: str | None = None
    ranking_lookup_id: str | None = None
    customer_status_lookup_id: str | None = None
    default_branch_id: str | None = None
    default_mandate_id: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerContactCreate(BaseModel):
    tenant_id: str
    customer_id: str
    full_name: str
    title: str | None = None
    function_label: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    is_primary_contact: bool = False
    is_billing_contact: bool = False
    user_id: str | None = None
    notes: str | None = None


class CustomerContactUpdate(BaseModel):
    full_name: str | None = None
    title: str | None = None
    function_label: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    is_primary_contact: bool | None = None
    is_billing_contact: bool | None = None
    user_id: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerAddressCreate(BaseModel):
    tenant_id: str
    customer_id: str
    address_id: str
    address_type: str = Field(pattern="^(registered|billing|mailing|service)$")
    label: str | None = None
    is_default: bool = False


class CustomerAddressUpdate(BaseModel):
    address_id: str | None = None
    address_type: str | None = Field(default=None, pattern="^(registered|billing|mailing|service)$")
    label: str | None = None
    is_default: bool | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerContactListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    full_name: str
    email: str | None
    is_primary_contact: bool
    is_billing_contact: bool
    user_id: str | None
    status: str
    version_no: int


class CustomerContactRead(CustomerContactListItem):
    title: str | None
    function_label: str | None
    phone: str | None
    mobile: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class CustomerAddressListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    address_id: str
    address_type: str
    label: str | None
    is_default: bool
    status: str
    version_no: int


class CustomerAddressRead(CustomerAddressListItem):
    address: AddressRead | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class CustomerListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_number: str
    name: str
    status: str
    version_no: int


class CustomerRead(CustomerListItem):
    legal_name: str | None
    external_ref: str | None
    legal_form_lookup_id: str | None
    classification_lookup_id: str | None
    ranking_lookup_id: str | None
    customer_status_lookup_id: str | None
    default_branch_id: str | None
    default_mandate_id: str | None
    notes: str | None
    portal_person_names_released: bool = False
    portal_person_names_released_at: datetime | None = None
    portal_person_names_released_by_user_id: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None
    contacts: list[CustomerContactRead] = Field(default_factory=list)
    addresses: list[CustomerAddressRead] = Field(default_factory=list)


class CustomerReferenceOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    label: str
    description: str | None = None
    sort_order: int = 100


class CustomerBranchOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str


class CustomerMandateOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    branch_id: str
    code: str
    name: str


class CustomerReferenceDataRead(BaseModel):
    legal_forms: list[CustomerReferenceOptionRead] = Field(default_factory=list)
    classifications: list[CustomerReferenceOptionRead] = Field(default_factory=list)
    rankings: list[CustomerReferenceOptionRead] = Field(default_factory=list)
    customer_statuses: list[CustomerReferenceOptionRead] = Field(default_factory=list)
    branches: list[CustomerBranchOptionRead] = Field(default_factory=list)
    mandates: list[CustomerMandateOptionRead] = Field(default_factory=list)


class CustomerPortalCustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_number: str
    name: str
    status: str


class CustomerPortalContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    full_name: str
    function_label: str | None
    email: str | None
    phone: str | None
    mobile: str | None
    status: str


class CustomerPortalScopeRead(BaseModel):
    role_key: str
    scope_type: str
    customer_id: str


class CustomerPortalDatasetCapabilityRead(BaseModel):
    domain_key: str
    availability_status: str
    reason_message_key: str
    interaction_mode: str
    can_view: bool = True
    can_download_documents: bool = False
    can_write: bool = False


class CustomerPortalCapabilitiesRead(BaseModel):
    can_view_orders: bool
    can_view_schedules: bool
    can_view_watchbooks: bool
    can_add_watchbook_entries: bool
    can_view_timesheets: bool
    can_download_timesheet_documents: bool
    can_view_invoices: bool
    can_download_invoice_documents: bool
    can_view_reports: bool
    can_view_history: bool
    personal_names_visible: bool
    released_only: bool
    customer_scoped_only: bool
    datasets: list[CustomerPortalDatasetCapabilityRead] = Field(default_factory=list)


class CustomerPortalContextRead(BaseModel):
    tenant_id: str
    user_id: str
    customer_id: str
    contact_id: str
    customer: CustomerPortalCustomerRead
    contact: CustomerPortalContactRead
    scopes: list[CustomerPortalScopeRead] = Field(default_factory=list)
    capabilities: CustomerPortalCapabilitiesRead


class CustomerPortalCollectionSourceRead(BaseModel):
    domain_key: str
    source_module_key: str
    availability_status: str
    released_only: bool = True
    customer_scoped: bool = True
    docs_backed_outputs: bool = False
    message_key: str


class CustomerPortalDocumentRefRead(BaseModel):
    document_id: str
    title: str
    document_type_key: str | None = None
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None
    is_name_masked: bool = True


class CustomerPortalOrderListItemRead(BaseModel):
    id: str
    customer_id: str
    order_number: str
    title: str
    service_from: date | None = None
    service_to: date | None = None
    released_at: datetime
    status: str


class CustomerPortalScheduleListItemRead(BaseModel):
    id: str
    customer_id: str
    order_id: str
    schedule_date: date
    shift_label: str
    site_label: str | None = None
    released_at: datetime
    status: str
    documents: list[CustomerPortalDocumentRefRead] = Field(default_factory=list)


class CustomerPortalWatchbookEntryRead(BaseModel):
    id: str
    customer_id: str
    log_date: date | None = None
    occurred_at: datetime
    entry_type_code: str | None = None
    summary: str
    status: str
    personal_names_released: bool = False
    pdf_document_id: str | None = None


class CustomerPortalTimesheetRead(BaseModel):
    id: str
    customer_id: str
    period_start: date
    period_end: date
    released_at: datetime
    status: str
    total_minutes: int | None = None
    documents: list[CustomerPortalDocumentRefRead] = Field(default_factory=list)


class CustomerPortalInvoiceRead(BaseModel):
    id: str
    customer_id: str
    invoice_no: str
    issue_date: date
    due_date: date
    released_at: datetime | None = None
    status: str
    currency_code: str
    total_amount: Decimal
    documents: list[CustomerPortalDocumentRefRead] = Field(default_factory=list)


class CustomerPortalReportPackageRead(BaseModel):
    id: str
    customer_id: str
    title: str
    category_code: str | None = None
    published_at: datetime
    status: str
    documents: list[CustomerPortalDocumentRefRead] = Field(default_factory=list)


class CustomerPortalOrderCollectionRead(BaseModel):
    customer_id: str
    source: CustomerPortalCollectionSourceRead
    items: list[CustomerPortalOrderListItemRead] = Field(default_factory=list)


class CustomerPortalScheduleCollectionRead(BaseModel):
    customer_id: str
    source: CustomerPortalCollectionSourceRead
    items: list[CustomerPortalScheduleListItemRead] = Field(default_factory=list)


class CustomerPortalWatchbookCollectionRead(BaseModel):
    customer_id: str
    source: CustomerPortalCollectionSourceRead
    items: list[CustomerPortalWatchbookEntryRead] = Field(default_factory=list)


class CustomerPortalTimesheetCollectionRead(BaseModel):
    customer_id: str
    source: CustomerPortalCollectionSourceRead
    items: list[CustomerPortalTimesheetRead] = Field(default_factory=list)


class CustomerPortalInvoiceCollectionRead(BaseModel):
    customer_id: str
    source: CustomerPortalCollectionSourceRead
    items: list[CustomerPortalInvoiceRead] = Field(default_factory=list)


class CustomerPortalReportPackageCollectionRead(BaseModel):
    customer_id: str
    source: CustomerPortalCollectionSourceRead
    items: list[CustomerPortalReportPackageRead] = Field(default_factory=list)


class CustomerBillingProfileCreate(BaseModel):
    tenant_id: str
    customer_id: str
    invoice_email: str | None = None
    payment_terms_days: int | None = None
    payment_terms_note: str | None = None
    tax_number: str | None = None
    vat_id: str | None = None
    tax_exempt: bool = False
    tax_exemption_reason: str | None = None
    bank_account_holder: str | None = None
    bank_iban: str | None = None
    bank_bic: str | None = None
    bank_name: str | None = None
    contract_reference: str | None = None
    debtor_number: str | None = None
    e_invoice_enabled: bool = False
    leitweg_id: str | None = None
    invoice_layout_code: str | None = None
    shipping_method_code: str | None = None
    dunning_policy_code: str | None = None
    billing_note: str | None = None


class CustomerBillingProfileUpdate(BaseModel):
    invoice_email: str | None = None
    payment_terms_days: int | None = None
    payment_terms_note: str | None = None
    tax_number: str | None = None
    vat_id: str | None = None
    tax_exempt: bool | None = None
    tax_exemption_reason: str | None = None
    bank_account_holder: str | None = None
    bank_iban: str | None = None
    bank_bic: str | None = None
    bank_name: str | None = None
    contract_reference: str | None = None
    debtor_number: str | None = None
    e_invoice_enabled: bool | None = None
    leitweg_id: str | None = None
    invoice_layout_code: str | None = None
    shipping_method_code: str | None = None
    dunning_policy_code: str | None = None
    billing_note: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerBillingProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    invoice_email: str | None
    payment_terms_days: int | None
    payment_terms_note: str | None
    tax_number: str | None
    vat_id: str | None
    tax_exempt: bool
    tax_exemption_reason: str | None
    bank_account_holder: str | None
    bank_iban: str | None
    bank_bic: str | None
    bank_name: str | None
    contract_reference: str | None
    debtor_number: str | None
    e_invoice_enabled: bool
    leitweg_id: str | None
    invoice_layout_code: str | None
    shipping_method_code: str | None
    dunning_policy_code: str | None
    billing_note: str | None
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class CustomerInvoicePartyCreate(BaseModel):
    tenant_id: str
    customer_id: str
    company_name: str
    contact_name: str | None = None
    address_id: str
    invoice_email: str | None = None
    invoice_layout_lookup_id: str | None = None
    external_ref: str | None = None
    is_default: bool = False
    note: str | None = None


class CustomerInvoicePartyUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    address_id: str | None = None
    invoice_email: str | None = None
    invoice_layout_lookup_id: str | None = None
    external_ref: str | None = None
    is_default: bool | None = None
    note: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerInvoicePartyListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    company_name: str
    contact_name: str | None
    address_id: str
    invoice_email: str | None
    invoice_layout_lookup_id: str | None
    external_ref: str | None
    is_default: bool
    status: str
    version_no: int


class CustomerInvoicePartyRead(CustomerInvoicePartyListItem):
    address: AddressRead | None = None
    note: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class CustomerCommercialProfileRead(BaseModel):
    customer_id: str
    tenant_id: str
    billing_profile: CustomerBillingProfileRead | None = None
    invoice_parties: list[CustomerInvoicePartyRead] = Field(default_factory=list)
    rate_cards: list["CustomerRateCardRead"] = Field(default_factory=list)


class CustomerRateCardCreate(BaseModel):
    tenant_id: str
    customer_id: str
    rate_kind: str
    currency_code: str = Field(min_length=3, max_length=3)
    effective_from: date
    effective_to: date | None = None
    notes: str | None = None


class CustomerRateCardUpdate(BaseModel):
    rate_kind: str | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    effective_from: date | None = None
    effective_to: date | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerRateCardListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    rate_kind: str
    currency_code: str
    effective_from: date
    effective_to: date | None
    status: str
    version_no: int


class CustomerRateLineCreate(BaseModel):
    tenant_id: str
    rate_card_id: str
    line_kind: str
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    planning_mode_code: str | None = None
    billing_unit: str
    unit_price: Decimal
    minimum_quantity: Decimal | None = None
    sort_order: int = 100
    notes: str | None = None


class CustomerRateLineUpdate(BaseModel):
    line_kind: str | None = None
    function_type_id: str | None = None
    qualification_type_id: str | None = None
    planning_mode_code: str | None = None
    billing_unit: str | None = None
    unit_price: Decimal | None = None
    minimum_quantity: Decimal | None = None
    sort_order: int | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerRateLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    rate_card_id: str
    line_kind: str
    function_type_id: str | None
    qualification_type_id: str | None
    planning_mode_code: str | None
    billing_unit: str
    unit_price: Decimal
    minimum_quantity: Decimal | None
    sort_order: int
    notes: str | None
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class CustomerSurchargeRuleCreate(BaseModel):
    tenant_id: str
    rate_card_id: str
    surcharge_type: str
    effective_from: date
    effective_to: date | None = None
    weekday_mask: str | None = Field(default=None, min_length=7, max_length=7)
    time_from_minute: int | None = Field(default=None, ge=0, le=1439)
    time_to_minute: int | None = Field(default=None, ge=1, le=1440)
    region_code: str | None = None
    percent_value: Decimal | None = None
    fixed_amount: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    sort_order: int = 100
    notes: str | None = None


class CustomerSurchargeRuleUpdate(BaseModel):
    surcharge_type: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    weekday_mask: str | None = Field(default=None, min_length=7, max_length=7)
    time_from_minute: int | None = Field(default=None, ge=0, le=1439)
    time_to_minute: int | None = Field(default=None, ge=1, le=1440)
    region_code: str | None = None
    percent_value: Decimal | None = None
    fixed_amount: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    sort_order: int | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerSurchargeRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    rate_card_id: str
    surcharge_type: str
    effective_from: date
    effective_to: date | None
    weekday_mask: str | None
    time_from_minute: int | None
    time_to_minute: int | None
    region_code: str | None
    percent_value: Decimal | None
    fixed_amount: Decimal | None
    currency_code: str | None
    sort_order: int
    notes: str | None
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class CustomerRateCardRead(CustomerRateCardListItem):
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None
    rate_lines: list[CustomerRateLineRead] = Field(default_factory=list)
    surcharge_rules: list[CustomerSurchargeRuleRead] = Field(default_factory=list)


class CustomerPricingProfileRead(BaseModel):
    tenant_id: str
    customer_id: str
    rate_cards: list[CustomerRateCardRead] = Field(default_factory=list)


class CustomerHistoryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    entry_type: str
    title: str
    summary: str
    actor_user_id: str | None
    related_contact_id: str | None
    related_address_link_id: str | None
    integration_job_id: str | None
    sort_order: int
    before_json: dict[str, object]
    after_json: dict[str, object]
    metadata_json: dict[str, object]
    created_at: datetime
    attachments: list["CustomerHistoryAttachmentRead"] = Field(default_factory=list)


class CustomerHistoryAttachmentRead(BaseModel):
    document_id: str
    title: str
    document_type_key: str | None = None
    file_name: str | None = None
    content_type: str | None = None
    current_version_no: int | None = None


class CustomerHistoryAttachmentLinkCreate(BaseModel):
    document_id: str
    label: str | None = None


class CustomerPortalHistoryEntryRead(BaseModel):
    id: str
    entry_type: str
    title: str
    summary: str
    created_at: datetime
    attachments: list[CustomerHistoryAttachmentRead] = Field(default_factory=list)


class CustomerPortalHistoryCollectionRead(BaseModel):
    customer_id: str
    items: list[CustomerPortalHistoryEntryRead] = Field(default_factory=list)


class CustomerPortalPrivacyRead(BaseModel):
    customer_id: str
    person_names_released: bool = False
    person_names_released_at: datetime | None = None
    person_names_released_by_user_id: str | None = None


class CustomerPortalPrivacyUpdate(BaseModel):
    person_names_released: bool


class CustomerPortalAccessListItemRead(BaseModel):
    user_id: str
    contact_id: str
    contact_name: str
    username: str
    email: str
    full_name: str
    locale: str
    role_key: str
    status: str
    role_assignment_status: str
    is_password_login_enabled: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CustomerPortalAccessCreate(BaseModel):
    tenant_id: str
    customer_id: str
    contact_id: str
    username: str
    email: str
    full_name: str
    locale: str = "de"
    timezone: str = "Europe/Berlin"
    status: str = "active"
    temporary_password: str | None = None


class CustomerPortalAccessStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class CustomerPortalAccessPasswordResetRequest(BaseModel):
    temporary_password: str | None = None


class CustomerPortalAccessPasswordResetResponse(BaseModel):
    message_key: str
    temporary_password: str


class CustomerPortalAccessUnlinkResponse(BaseModel):
    message_key: str


class CustomerLoginHistoryEntryRead(BaseModel):
    id: str
    user_account_id: str | None = None
    contact_id: str | None = None
    contact_name: str | None = None
    identifier: str
    outcome: str
    failure_reason: str | None = None
    auth_method: str
    created_at: datetime


class CustomerEmployeeBlockCapabilityRead(BaseModel):
    directory_available: bool
    employee_reference_mode: str
    message_key: str


class CustomerEmployeeBlockCreate(BaseModel):
    tenant_id: str
    customer_id: str
    employee_id: str
    reason: str
    effective_from: date
    effective_to: date | None = None


class CustomerEmployeeBlockUpdate(BaseModel):
    reason: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class CustomerEmployeeBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    employee_id: str
    reason: str
    effective_from: date
    effective_to: date | None
    status: str
    version_no: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class CustomerEmployeeBlockCollectionRead(BaseModel):
    customer_id: str
    capability: CustomerEmployeeBlockCapabilityRead
    items: list[CustomerEmployeeBlockRead] = Field(default_factory=list)


class CustomerImportDryRunRequest(BaseModel):
    tenant_id: str
    csv_content_base64: str


class CustomerImportExecuteRequest(CustomerImportDryRunRequest):
    continue_on_error: bool = True


class CustomerImportRowResult(BaseModel):
    row_no: int
    customer_number: str | None = None
    status: str
    messages: list[str] = Field(default_factory=list)
    customer_id: str | None = None
    contact_id: str | None = None


class CustomerImportDryRunResult(BaseModel):
    tenant_id: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[CustomerImportRowResult]


class CustomerImportExecuteResult(BaseModel):
    tenant_id: str
    job_id: str
    job_status: str
    total_rows: int
    created_customers: int
    updated_customers: int
    created_contacts: int
    updated_contacts: int
    created_address_links: int
    updated_address_links: int
    invalid_rows: int
    result_document_ids: list[str] = Field(default_factory=list)
    rows: list[CustomerImportRowResult]


class CustomerExportRequest(BaseModel):
    tenant_id: str
    include_archived: bool = False
    search: str | None = None


class CustomerExportResult(BaseModel):
    tenant_id: str
    job_id: str
    document_id: str
    file_name: str
    row_count: int


class CustomerVCardResult(BaseModel):
    tenant_id: str
    customer_id: str
    contact_id: str
    document_id: str
    version_no: int
    file_name: str
    content_type: str
    content_base64: str
