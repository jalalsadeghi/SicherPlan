"""HTTP API for tenant-scoped CRM customer master maintenance."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.config import settings
from app.modules.core.schemas import AddressRead
from app.modules.platform_services.docs_repository import SqlAlchemyDocumentRepository
from app.modules.platform_services.docs_service import DocumentService
from app.modules.platform_services.integration_repository import SqlAlchemyIntegrationRepository
from app.modules.platform_services.storage import build_object_storage_adapter
from app.modules.customers.collaboration_service import CustomerCollaborationService
from app.modules.customers.commercial_service import CustomerCommercialService
from app.modules.customers.ops_service import CustomerOpsService
from app.modules.customers.repository import SqlAlchemyCustomerRepository
from app.modules.customers.schemas import (
    CustomerAddressCreate,
    CustomerAddressRead,
    CustomerAddressUpdate,
    CustomerBillingProfileCreate,
    CustomerBillingProfileRead,
    CustomerBillingProfileUpdate,
    CustomerCommercialProfileRead,
    CustomerContactCreate,
    CustomerContactRead,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerExportRequest,
    CustomerExportResult,
    CustomerFilter,
    CustomerHistoryAttachmentRead,
    CustomerHistoryAttachmentLinkCreate,
    CustomerHistoryEntryRead,
    CustomerImportDryRunRequest,
    CustomerImportDryRunResult,
    CustomerImportExecuteRequest,
    CustomerImportExecuteResult,
    CustomerInvoicePartyCreate,
    CustomerInvoicePartyRead,
    CustomerInvoicePartyUpdate,
    CustomerListItem,
    CustomerLoginHistoryEntryRead,
    CustomerPortalPrivacyRead,
    CustomerPortalPrivacyUpdate,
    CustomerPricingProfileRead,
    CustomerRead,
    CustomerRateCardCreate,
    CustomerRateCardRead,
    CustomerRateCardUpdate,
    CustomerRateLineCreate,
    CustomerRateLineRead,
    CustomerRateLineUpdate,
    CustomerSurchargeRuleCreate,
    CustomerSurchargeRuleRead,
    CustomerSurchargeRuleUpdate,
    CustomerUpdate,
    CustomerEmployeeBlockCollectionRead,
    CustomerEmployeeBlockCreate,
    CustomerEmployeeBlockRead,
    CustomerEmployeeBlockUpdate,
    CustomerReferenceDataRead,
    CustomerVCardResult,
)
from app.modules.customers.service import CustomerService
from app.modules.iam.audit_repository import SqlAlchemyAuditRepository
from app.modules.iam.audit_service import AuditService
from app.modules.iam.authz import RequestAuthorizationContext, require_authorization


router = APIRouter(prefix="/api/customers/tenants/{tenant_id}/customers", tags=["customers"])


def get_customer_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerService:
    return CustomerService(
        SqlAlchemyCustomerRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_customer_ops_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerOpsService:
    customer_repository = SqlAlchemyCustomerRepository(session)
    document_service = DocumentService(
        SqlAlchemyDocumentRepository(session),
        storage=build_object_storage_adapter(settings),
        bucket_name=settings.object_storage_bucket,
    )
    return CustomerOpsService(
        customer_service=CustomerService(
            customer_repository,
            audit_service=AuditService(SqlAlchemyAuditRepository(session)),
        ),
        customer_repository=customer_repository,
        integration_repository=SqlAlchemyIntegrationRepository(session),
        document_service=document_service,
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_customer_commercial_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerCommercialService:
    return CustomerCommercialService(
        SqlAlchemyCustomerRepository(session),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


def get_customer_collaboration_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> CustomerCollaborationService:
    return CustomerCollaborationService(
        SqlAlchemyCustomerRepository(session),
        login_audit_repository=SqlAlchemyAuditRepository(session),
        document_repository=SqlAlchemyDocumentRepository(session),
        document_service=DocumentService(
            SqlAlchemyDocumentRepository(session),
            storage=build_object_storage_adapter(settings),
            bucket_name=settings.object_storage_bucket,
        ),
        audit_service=AuditService(SqlAlchemyAuditRepository(session)),
    )


@router.get("", response_model=list[CustomerListItem])
def list_customers(
    tenant_id: UUID,
    search: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    default_branch_id: UUID | None = Query(default=None),
    default_mandate_id: UUID | None = Query(default=None),
    include_archived: bool = Query(default=False),
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ] = None,
    service: Annotated[CustomerService, Depends(get_customer_service)] = None,
) -> list[CustomerListItem]:
    filters = CustomerFilter(
        search=search,
        lifecycle_status=lifecycle_status,
        default_branch_id=str(default_branch_id) if default_branch_id else None,
        default_mandate_id=str(default_mandate_id) if default_mandate_id else None,
        include_archived=include_archived,
    )
    return service.list_customers(str(tenant_id), filters, context)


@router.get("/reference-data", response_model=CustomerReferenceDataRead)
def get_customer_reference_data(
    tenant_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerReferenceDataRead:
    return service.get_reference_data(str(tenant_id), context)


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(
    tenant_id: UUID,
    payload: CustomerCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerRead:
    return service.create_customer(str(tenant_id), payload, context)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerRead:
    return service.get_customer(str(tenant_id), str(customer_id), context)


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerRead:
    return service.update_customer(str(tenant_id), str(customer_id), payload, context)


@router.get("/{customer_id}/commercial-profile", response_model=CustomerCommercialProfileRead)
def get_customer_commercial_profile(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.read", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerCommercialProfileRead:
    return service.get_commercial_profile(str(tenant_id), str(customer_id), context)


@router.get("/{customer_id}/pricing-profile", response_model=CustomerPricingProfileRead)
def get_customer_pricing_profile(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.read", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerPricingProfileRead:
    return service.get_pricing_profile(str(tenant_id), str(customer_id), context)


@router.put("/{customer_id}/billing-profile", response_model=CustomerBillingProfileRead)
def upsert_customer_billing_profile(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerBillingProfileCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerBillingProfileRead:
    return service.upsert_billing_profile(str(tenant_id), str(customer_id), payload, context)


@router.patch("/{customer_id}/billing-profile", response_model=CustomerBillingProfileRead)
def update_customer_billing_profile(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerBillingProfileUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerBillingProfileRead:
    return service.upsert_billing_profile(str(tenant_id), str(customer_id), payload, context)


@router.get("/{customer_id}/contacts", response_model=list[CustomerContactRead])
def list_customer_contacts(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> list[CustomerContactRead]:
    return service.list_contacts(str(tenant_id), str(customer_id), context)


@router.post("/{customer_id}/contacts", response_model=CustomerContactRead, status_code=status.HTTP_201_CREATED)
def create_customer_contact(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerContactCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerContactRead:
    return service.create_contact(str(tenant_id), str(customer_id), payload, context)


@router.patch("/{customer_id}/contacts/{contact_id}", response_model=CustomerContactRead)
def update_customer_contact(
    tenant_id: UUID,
    customer_id: UUID,
    contact_id: UUID,
    payload: CustomerContactUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerContactRead:
    return service.update_contact(str(tenant_id), str(customer_id), str(contact_id), payload, context)


@router.get("/{customer_id}/invoice-parties", response_model=list[CustomerInvoicePartyRead])
def list_customer_invoice_parties(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.read", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> list[CustomerInvoicePartyRead]:
    return service.list_invoice_parties(str(tenant_id), str(customer_id), context)


@router.post("/{customer_id}/invoice-parties", response_model=CustomerInvoicePartyRead, status_code=status.HTTP_201_CREATED)
def create_customer_invoice_party(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerInvoicePartyCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerInvoicePartyRead:
    return service.create_invoice_party(str(tenant_id), str(customer_id), payload, context)


@router.patch("/{customer_id}/invoice-parties/{invoice_party_id}", response_model=CustomerInvoicePartyRead)
def update_customer_invoice_party(
    tenant_id: UUID,
    customer_id: UUID,
    invoice_party_id: UUID,
    payload: CustomerInvoicePartyUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerInvoicePartyRead:
    return service.update_invoice_party(str(tenant_id), str(customer_id), str(invoice_party_id), payload, context)


@router.get("/{customer_id}/rate-cards", response_model=list[CustomerRateCardRead])
def list_customer_rate_cards(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.read", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> list[CustomerRateCardRead]:
    return service.list_rate_cards(str(tenant_id), str(customer_id), context)


@router.post("/{customer_id}/rate-cards", response_model=CustomerRateCardRead, status_code=status.HTTP_201_CREATED)
def create_customer_rate_card(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerRateCardCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerRateCardRead:
    return service.create_rate_card(str(tenant_id), str(customer_id), payload, context)


@router.patch("/{customer_id}/rate-cards/{rate_card_id}", response_model=CustomerRateCardRead)
def update_customer_rate_card(
    tenant_id: UUID,
    customer_id: UUID,
    rate_card_id: UUID,
    payload: CustomerRateCardUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerRateCardRead:
    return service.update_rate_card(str(tenant_id), str(customer_id), str(rate_card_id), payload, context)


@router.get("/{customer_id}/rate-cards/{rate_card_id}/rate-lines", response_model=list[CustomerRateLineRead])
def list_customer_rate_lines(
    tenant_id: UUID,
    customer_id: UUID,
    rate_card_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.read", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> list[CustomerRateLineRead]:
    return service.list_rate_lines(str(tenant_id), str(customer_id), str(rate_card_id), context)


@router.post(
    "/{customer_id}/rate-cards/{rate_card_id}/rate-lines",
    response_model=CustomerRateLineRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_rate_line(
    tenant_id: UUID,
    customer_id: UUID,
    rate_card_id: UUID,
    payload: CustomerRateLineCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerRateLineRead:
    return service.create_rate_line(str(tenant_id), str(customer_id), str(rate_card_id), payload, context)


@router.patch("/{customer_id}/rate-cards/{rate_card_id}/rate-lines/{rate_line_id}", response_model=CustomerRateLineRead)
def update_customer_rate_line(
    tenant_id: UUID,
    customer_id: UUID,
    rate_card_id: UUID,
    rate_line_id: UUID,
    payload: CustomerRateLineUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerRateLineRead:
    return service.update_rate_line(str(tenant_id), str(customer_id), str(rate_card_id), str(rate_line_id), payload, context)


@router.get(
    "/{customer_id}/rate-cards/{rate_card_id}/surcharge-rules",
    response_model=list[CustomerSurchargeRuleRead],
)
def list_customer_surcharge_rules(
    tenant_id: UUID,
    customer_id: UUID,
    rate_card_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.read", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> list[CustomerSurchargeRuleRead]:
    return service.list_surcharge_rules(str(tenant_id), str(customer_id), str(rate_card_id), context)


@router.post(
    "/{customer_id}/rate-cards/{rate_card_id}/surcharge-rules",
    response_model=CustomerSurchargeRuleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_surcharge_rule(
    tenant_id: UUID,
    customer_id: UUID,
    rate_card_id: UUID,
    payload: CustomerSurchargeRuleCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerSurchargeRuleRead:
    return service.create_surcharge_rule(str(tenant_id), str(customer_id), str(rate_card_id), payload, context)


@router.patch(
    "/{customer_id}/rate-cards/{rate_card_id}/surcharge-rules/{surcharge_rule_id}",
    response_model=CustomerSurchargeRuleRead,
)
def update_customer_surcharge_rule(
    tenant_id: UUID,
    customer_id: UUID,
    rate_card_id: UUID,
    surcharge_rule_id: UUID,
    payload: CustomerSurchargeRuleUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.billing.write", scope="tenant")),
    ],
    service: Annotated[CustomerCommercialService, Depends(get_customer_commercial_service)],
) -> CustomerSurchargeRuleRead:
    return service.update_surcharge_rule(
        str(tenant_id),
        str(customer_id),
        str(rate_card_id),
        str(surcharge_rule_id),
        payload,
        context,
    )


@router.get("/{customer_id}/addresses", response_model=list[CustomerAddressRead])
def list_customer_addresses(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> list[CustomerAddressRead]:
    return service.list_customer_addresses(str(tenant_id), str(customer_id), context)


@router.get("/{customer_id}/address-options", response_model=list[AddressRead])
def list_customer_available_addresses(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
    search: str = Query(default="", max_length=120),
    limit: int = Query(default=25, ge=1, le=50),
) -> list[AddressRead]:
    return service.list_available_addresses(
        str(tenant_id),
        str(customer_id),
        context,
        search=search,
        limit=limit,
    )


@router.post("/{customer_id}/addresses", response_model=CustomerAddressRead, status_code=status.HTTP_201_CREATED)
def create_customer_address(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerAddressCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerAddressRead:
    return service.create_customer_address(str(tenant_id), str(customer_id), payload, context)


@router.patch("/{customer_id}/addresses/{link_id}", response_model=CustomerAddressRead)
def update_customer_address(
    tenant_id: UUID,
    customer_id: UUID,
    link_id: UUID,
    payload: CustomerAddressUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerAddressRead:
    return service.update_customer_address(str(tenant_id), str(customer_id), str(link_id), payload, context)


@router.get("/{customer_id}/history", response_model=list[CustomerHistoryEntryRead])
def list_customer_history(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> list[CustomerHistoryEntryRead]:
    return service.list_history(str(tenant_id), str(customer_id), context)


@router.post("/{customer_id}/history/{history_entry_id}/attachments", response_model=list[CustomerHistoryAttachmentRead])
def link_customer_history_attachment(
    tenant_id: UUID,
    customer_id: UUID,
    history_entry_id: UUID,
    payload: CustomerHistoryAttachmentLinkCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> list[CustomerHistoryAttachmentRead]:
    return service.link_history_attachment(str(tenant_id), str(customer_id), str(history_entry_id), payload, context)


@router.get("/{customer_id}/portal-login-history", response_model=list[CustomerLoginHistoryEntryRead])
def list_customer_portal_login_history(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> list[CustomerLoginHistoryEntryRead]:
    return service.list_login_history(str(tenant_id), str(customer_id), context)


@router.get("/{customer_id}/portal-privacy", response_model=CustomerPortalPrivacyRead)
def get_customer_portal_privacy(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> CustomerPortalPrivacyRead:
    return service.get_portal_privacy(str(tenant_id), str(customer_id), context)


@router.put("/{customer_id}/portal-privacy", response_model=CustomerPortalPrivacyRead)
def update_customer_portal_privacy(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerPortalPrivacyUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> CustomerPortalPrivacyRead:
    return service.update_portal_privacy(str(tenant_id), str(customer_id), payload, context)


@router.get("/{customer_id}/employee-blocks", response_model=CustomerEmployeeBlockCollectionRead)
def list_customer_employee_blocks(
    tenant_id: UUID,
    customer_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> CustomerEmployeeBlockCollectionRead:
    return service.list_employee_blocks(str(tenant_id), str(customer_id), context)


@router.post("/{customer_id}/employee-blocks", response_model=CustomerEmployeeBlockRead, status_code=status.HTTP_201_CREATED)
def create_customer_employee_block(
    tenant_id: UUID,
    customer_id: UUID,
    payload: CustomerEmployeeBlockCreate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> CustomerEmployeeBlockRead:
    return service.create_employee_block(str(tenant_id), str(customer_id), payload, context)


@router.patch("/{customer_id}/employee-blocks/{block_id}", response_model=CustomerEmployeeBlockRead)
def update_customer_employee_block(
    tenant_id: UUID,
    customer_id: UUID,
    block_id: UUID,
    payload: CustomerEmployeeBlockUpdate,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerCollaborationService, Depends(get_customer_collaboration_service)],
) -> CustomerEmployeeBlockRead:
    return service.update_employee_block(str(tenant_id), str(customer_id), str(block_id), payload, context)


@router.post("/imports/dry-run", response_model=CustomerImportDryRunResult)
def import_customers_dry_run(
    tenant_id: UUID,
    payload: CustomerImportDryRunRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerOpsService, Depends(get_customer_ops_service)],
) -> CustomerImportDryRunResult:
    return service.import_dry_run(str(tenant_id), payload, context)


@router.post("/imports/execute", response_model=CustomerImportExecuteResult, status_code=status.HTTP_201_CREATED)
def import_customers_execute(
    tenant_id: UUID,
    payload: CustomerImportExecuteRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.write", scope="tenant")),
    ],
    service: Annotated[CustomerOpsService, Depends(get_customer_ops_service)],
) -> CustomerImportExecuteResult:
    return service.execute_import(str(tenant_id), payload, context)


@router.post("/exports", response_model=CustomerExportResult, status_code=status.HTTP_201_CREATED)
def export_customers(
    tenant_id: UUID,
    payload: CustomerExportRequest,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerOpsService, Depends(get_customer_ops_service)],
) -> CustomerExportResult:
    return service.export_customers(str(tenant_id), payload, context)


@router.post("/{customer_id}/contacts/{contact_id}/vcard", response_model=CustomerVCardResult, status_code=status.HTTP_201_CREATED)
def export_contact_vcard(
    tenant_id: UUID,
    customer_id: UUID,
    contact_id: UUID,
    context: Annotated[
        RequestAuthorizationContext,
        Depends(require_authorization("customers.customer.read", scope="tenant")),
    ],
    service: Annotated[CustomerOpsService, Depends(get_customer_ops_service)],
) -> CustomerVCardResult:
    return service.export_vcard(str(tenant_id), str(customer_id), str(contact_id), context)
