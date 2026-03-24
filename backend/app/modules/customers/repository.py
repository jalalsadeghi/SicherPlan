"""SQLAlchemy repository for CRM customer master maintenance."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import ApiException
from app.modules.core.models import Address, Branch, LookupValue, Mandate
from app.modules.customers.models import (
    Customer,
    CustomerAddressLink,
    CustomerBillingProfile,
    CustomerContact,
    CustomerEmployeeBlock,
    CustomerHistoryEntry,
    CustomerInvoiceParty,
    CustomerRateCard,
    CustomerRateLine,
    CustomerSurchargeRule,
)
from app.modules.customers.schemas import (
    CustomerAddressCreate,
    CustomerAddressUpdate,
    CustomerBillingProfileCreate,
    CustomerBillingProfileUpdate,
    CustomerContactCreate,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerFilter,
    CustomerInvoicePartyCreate,
    CustomerInvoicePartyUpdate,
    CustomerRateCardCreate,
    CustomerRateCardUpdate,
    CustomerRateLineCreate,
    CustomerRateLineUpdate,
    CustomerSurchargeRuleCreate,
    CustomerSurchargeRuleUpdate,
    CustomerUpdate,
)
from app.modules.iam.models import UserAccount


class SqlAlchemyCustomerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_customers(self, tenant_id: str, filters: CustomerFilter) -> list[Customer]:
        statement = (
            select(Customer)
            .where(Customer.tenant_id == tenant_id)
            .options(
                selectinload(Customer.contacts),
                selectinload(Customer.billing_profile),
                selectinload(Customer.invoice_parties).selectinload(CustomerInvoiceParty.address),
                selectinload(Customer.rate_cards).selectinload(CustomerRateCard.rate_lines),
                selectinload(Customer.rate_cards).selectinload(CustomerRateCard.surcharge_rules),
                selectinload(Customer.addresses).selectinload(CustomerAddressLink.address),
            )
            .order_by(Customer.customer_number)
        )
        if not filters.include_archived:
            statement = statement.where(Customer.archived_at.is_(None))
        if filters.lifecycle_status is not None:
            statement = statement.where(Customer.status == filters.lifecycle_status)
        if filters.default_branch_id is not None:
            statement = statement.where(Customer.default_branch_id == filters.default_branch_id)
        if filters.default_mandate_id is not None:
            statement = statement.where(Customer.default_mandate_id == filters.default_mandate_id)
        if filters.search:
            like_term = f"%{filters.search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Customer.customer_number).like(like_term),
                    func.lower(Customer.name).like(like_term),
                    func.lower(func.coalesce(Customer.legal_name, "")).like(like_term),
                )
            )
        return list(self.session.scalars(statement).all())

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        statement = (
            select(Customer)
            .where(Customer.tenant_id == tenant_id, Customer.id == customer_id)
            .options(
                selectinload(Customer.contacts),
                selectinload(Customer.billing_profile),
                selectinload(Customer.invoice_parties).selectinload(CustomerInvoiceParty.address),
                selectinload(Customer.rate_cards).selectinload(CustomerRateCard.rate_lines),
                selectinload(Customer.rate_cards).selectinload(CustomerRateCard.surcharge_rules),
                selectinload(Customer.addresses).selectinload(CustomerAddressLink.address),
                selectinload(Customer.history_entries),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def get_portal_contact_for_user(self, tenant_id: str, user_id: str) -> tuple[Customer, CustomerContact] | None:
        statement = (
            select(Customer, CustomerContact)
            .join(
                CustomerContact,
                (CustomerContact.tenant_id == Customer.tenant_id) & (CustomerContact.customer_id == Customer.id),
            )
            .where(
                Customer.tenant_id == tenant_id,
                CustomerContact.tenant_id == tenant_id,
                CustomerContact.user_id == user_id,
                CustomerContact.archived_at.is_(None),
            )
            .options(selectinload(Customer.contacts))
            .order_by(CustomerContact.created_at.asc())
        )
        row = self.session.execute(statement).first()
        if row is None:
            return None
        customer, contact = row
        return customer, contact

    def get_billing_profile(self, tenant_id: str, customer_id: str) -> CustomerBillingProfile | None:
        statement = select(CustomerBillingProfile).where(
            CustomerBillingProfile.tenant_id == tenant_id,
            CustomerBillingProfile.customer_id == customer_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_billing_profile(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerBillingProfileCreate,
        actor_user_id: str | None,
    ) -> CustomerBillingProfile:
        row = CustomerBillingProfile(
            tenant_id=tenant_id,
            customer_id=customer_id,
            invoice_email=payload.invoice_email,
            payment_terms_days=payload.payment_terms_days,
            payment_terms_note=payload.payment_terms_note,
            tax_number=payload.tax_number,
            vat_id=payload.vat_id,
            tax_exempt=payload.tax_exempt,
            tax_exemption_reason=payload.tax_exemption_reason,
            bank_account_holder=payload.bank_account_holder,
            bank_iban=payload.bank_iban,
            bank_bic=payload.bank_bic,
            bank_name=payload.bank_name,
            contract_reference=payload.contract_reference,
            debtor_number=payload.debtor_number,
            e_invoice_enabled=payload.e_invoice_enabled,
            leitweg_id=payload.leitweg_id,
            invoice_layout_code=payload.invoice_layout_code,
            shipping_method_code=payload.shipping_method_code,
            dunning_policy_code=payload.dunning_policy_code,
            billing_note=payload.billing_note,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_billing_profile(tenant_id, customer_id) or row

    def update_billing_profile(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerBillingProfileUpdate,
        actor_user_id: str | None,
    ) -> CustomerBillingProfile | None:
        row = self.get_billing_profile(tenant_id, customer_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "billing_profile")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_billing_profile(tenant_id, customer_id)

    def create_customer(self, tenant_id: str, payload: CustomerCreate, actor_user_id: str | None) -> Customer:
        row = Customer(
            tenant_id=tenant_id,
            customer_number=payload.customer_number,
            name=payload.name,
            status=payload.status or "active",
            legal_name=payload.legal_name,
            external_ref=payload.external_ref,
            legal_form_lookup_id=payload.legal_form_lookup_id,
            classification_lookup_id=payload.classification_lookup_id,
            ranking_lookup_id=payload.ranking_lookup_id,
            customer_status_lookup_id=payload.customer_status_lookup_id,
            default_branch_id=payload.default_branch_id,
            default_mandate_id=payload.default_mandate_id,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_customer(tenant_id, row.id) or row

    def update_customer(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerUpdate,
        actor_user_id: str | None,
    ) -> Customer | None:
        row = self._tenant_scoped_get(Customer, tenant_id, customer_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "customer")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_customer(tenant_id, row.id)

    def list_contacts(self, tenant_id: str, customer_id: str) -> list[CustomerContact]:
        statement = (
            select(CustomerContact)
            .where(CustomerContact.tenant_id == tenant_id, CustomerContact.customer_id == customer_id)
            .order_by(CustomerContact.full_name)
        )
        return list(self.session.scalars(statement).all())

    def get_contact(self, tenant_id: str, customer_id: str, contact_id: str) -> CustomerContact | None:
        statement = select(CustomerContact).where(
            CustomerContact.tenant_id == tenant_id,
            CustomerContact.customer_id == customer_id,
            CustomerContact.id == contact_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_contact(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerContactCreate,
        actor_user_id: str | None,
    ) -> CustomerContact:
        row = CustomerContact(
            tenant_id=tenant_id,
            customer_id=customer_id,
            full_name=payload.full_name,
            title=payload.title,
            function_label=payload.function_label,
            email=payload.email,
            phone=payload.phone,
            mobile=payload.mobile,
            is_primary_contact=payload.is_primary_contact,
            is_billing_contact=payload.is_billing_contact,
            user_id=payload.user_id,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_contact(tenant_id, customer_id, row.id) or row

    def update_contact(
        self,
        tenant_id: str,
        customer_id: str,
        contact_id: str,
        payload: CustomerContactUpdate,
        actor_user_id: str | None,
    ) -> CustomerContact | None:
        row = self.get_contact(tenant_id, customer_id, contact_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "contact")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_contact(tenant_id, customer_id, contact_id)

    def list_invoice_parties(self, tenant_id: str, customer_id: str) -> list[CustomerInvoiceParty]:
        statement = (
            select(CustomerInvoiceParty)
            .where(CustomerInvoiceParty.tenant_id == tenant_id, CustomerInvoiceParty.customer_id == customer_id)
            .options(selectinload(CustomerInvoiceParty.address))
            .order_by(CustomerInvoiceParty.company_name)
        )
        return list(self.session.scalars(statement).all())

    def get_invoice_party(self, tenant_id: str, customer_id: str, invoice_party_id: str) -> CustomerInvoiceParty | None:
        statement = (
            select(CustomerInvoiceParty)
            .where(
                CustomerInvoiceParty.tenant_id == tenant_id,
                CustomerInvoiceParty.customer_id == customer_id,
                CustomerInvoiceParty.id == invoice_party_id,
            )
            .options(selectinload(CustomerInvoiceParty.address))
        )
        return self.session.scalars(statement).one_or_none()

    def create_invoice_party(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerInvoicePartyCreate,
        actor_user_id: str | None,
    ) -> CustomerInvoiceParty:
        row = CustomerInvoiceParty(
            tenant_id=tenant_id,
            customer_id=customer_id,
            company_name=payload.company_name,
            contact_name=payload.contact_name,
            address_id=payload.address_id,
            invoice_email=payload.invoice_email,
            invoice_layout_lookup_id=payload.invoice_layout_lookup_id,
            external_ref=payload.external_ref,
            is_default=payload.is_default,
            note=payload.note,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_invoice_party(tenant_id, customer_id, row.id) or row

    def update_invoice_party(
        self,
        tenant_id: str,
        customer_id: str,
        invoice_party_id: str,
        payload: CustomerInvoicePartyUpdate,
        actor_user_id: str | None,
    ) -> CustomerInvoiceParty | None:
        row = self.get_invoice_party(tenant_id, customer_id, invoice_party_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "invoice_party")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_invoice_party(tenant_id, customer_id, invoice_party_id)

    def list_customer_addresses(self, tenant_id: str, customer_id: str) -> list[CustomerAddressLink]:
        statement = (
            select(CustomerAddressLink)
            .where(CustomerAddressLink.tenant_id == tenant_id, CustomerAddressLink.customer_id == customer_id)
            .options(selectinload(CustomerAddressLink.address))
            .order_by(CustomerAddressLink.address_type, CustomerAddressLink.id)
        )
        return list(self.session.scalars(statement).all())

    def list_rate_cards(self, tenant_id: str, customer_id: str) -> list[CustomerRateCard]:
        statement = (
            select(CustomerRateCard)
            .where(CustomerRateCard.tenant_id == tenant_id, CustomerRateCard.customer_id == customer_id)
            .options(
                selectinload(CustomerRateCard.rate_lines),
                selectinload(CustomerRateCard.surcharge_rules),
            )
            .order_by(CustomerRateCard.effective_from, CustomerRateCard.id)
        )
        return list(self.session.scalars(statement).all())

    def get_rate_card(self, tenant_id: str, customer_id: str, rate_card_id: str) -> CustomerRateCard | None:
        statement = (
            select(CustomerRateCard)
            .where(
                CustomerRateCard.tenant_id == tenant_id,
                CustomerRateCard.customer_id == customer_id,
                CustomerRateCard.id == rate_card_id,
            )
            .options(
                selectinload(CustomerRateCard.rate_lines),
                selectinload(CustomerRateCard.surcharge_rules),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def create_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerRateCardCreate,
        actor_user_id: str | None,
    ) -> CustomerRateCard:
        row = CustomerRateCard(
            tenant_id=tenant_id,
            customer_id=customer_id,
            rate_kind=payload.rate_kind.strip().lower(),
            currency_code=payload.currency_code.strip().upper(),
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_rate_card(tenant_id, customer_id, row.id) or row

    def update_rate_card(
        self,
        tenant_id: str,
        customer_id: str,
        rate_card_id: str,
        payload: CustomerRateCardUpdate,
        actor_user_id: str | None,
    ) -> CustomerRateCard | None:
        row = self.get_rate_card(tenant_id, customer_id, rate_card_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "rate_card")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_rate_card(tenant_id, customer_id, rate_card_id)

    def list_overlapping_rate_cards(
        self,
        tenant_id: str,
        customer_id: str,
        *,
        rate_kind: str,
        effective_from,
        effective_to,
        exclude_id: str | None = None,
    ) -> list[CustomerRateCard]:
        statement = select(CustomerRateCard).where(
            CustomerRateCard.tenant_id == tenant_id,
            CustomerRateCard.customer_id == customer_id,
            CustomerRateCard.rate_kind == rate_kind,
            CustomerRateCard.archived_at.is_(None),
            CustomerRateCard.effective_from <= (effective_to or effective_from),
            or_(CustomerRateCard.effective_to.is_(None), CustomerRateCard.effective_to >= effective_from),
        )
        if effective_to is None:
            statement = select(CustomerRateCard).where(
                CustomerRateCard.tenant_id == tenant_id,
                CustomerRateCard.customer_id == customer_id,
                CustomerRateCard.rate_kind == rate_kind,
                CustomerRateCard.archived_at.is_(None),
                or_(CustomerRateCard.effective_to.is_(None), CustomerRateCard.effective_to >= effective_from),
            )
        if exclude_id is not None:
            statement = statement.where(CustomerRateCard.id != exclude_id)
        return list(self.session.scalars(statement).all())

    def get_rate_line(self, tenant_id: str, rate_card_id: str, rate_line_id: str) -> CustomerRateLine | None:
        statement = select(CustomerRateLine).where(
            CustomerRateLine.tenant_id == tenant_id,
            CustomerRateLine.rate_card_id == rate_card_id,
            CustomerRateLine.id == rate_line_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_rate_lines(self, tenant_id: str, rate_card_id: str) -> list[CustomerRateLine]:
        statement = (
            select(CustomerRateLine)
            .where(CustomerRateLine.tenant_id == tenant_id, CustomerRateLine.rate_card_id == rate_card_id)
            .order_by(CustomerRateLine.sort_order, CustomerRateLine.id)
        )
        return list(self.session.scalars(statement).all())

    def create_rate_line(
        self,
        tenant_id: str,
        rate_card_id: str,
        payload: CustomerRateLineCreate,
        actor_user_id: str | None,
    ) -> CustomerRateLine:
        row = CustomerRateLine(
            tenant_id=tenant_id,
            rate_card_id=rate_card_id,
            line_kind=payload.line_kind.strip().lower(),
            function_type_id=payload.function_type_id.strip() if payload.function_type_id else None,
            qualification_type_id=payload.qualification_type_id.strip() if payload.qualification_type_id else None,
            planning_mode_code=payload.planning_mode_code.strip().lower() if payload.planning_mode_code else None,
            billing_unit=payload.billing_unit.strip().lower(),
            unit_price=payload.unit_price,
            minimum_quantity=payload.minimum_quantity,
            sort_order=payload.sort_order,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_rate_line(tenant_id, rate_card_id, row.id) or row

    def update_rate_line(
        self,
        tenant_id: str,
        rate_card_id: str,
        rate_line_id: str,
        payload: CustomerRateLineUpdate,
        actor_user_id: str | None,
    ) -> CustomerRateLine | None:
        row = self.get_rate_line(tenant_id, rate_card_id, rate_line_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "rate_line")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_rate_line(tenant_id, rate_card_id, rate_line_id)

    def find_duplicate_rate_line(
        self,
        tenant_id: str,
        rate_card_id: str,
        *,
        line_kind: str,
        function_type_id: str | None,
        qualification_type_id: str | None,
        planning_mode_code: str | None,
        billing_unit: str,
        exclude_id: str | None = None,
    ) -> CustomerRateLine | None:
        statement = select(CustomerRateLine).where(
            CustomerRateLine.tenant_id == tenant_id,
            CustomerRateLine.rate_card_id == rate_card_id,
            CustomerRateLine.line_kind == line_kind.strip().lower(),
            CustomerRateLine.function_type_id == function_type_id,
            CustomerRateLine.qualification_type_id == qualification_type_id,
            CustomerRateLine.planning_mode_code == (planning_mode_code.strip().lower() if planning_mode_code else None),
            CustomerRateLine.billing_unit == billing_unit.strip().lower(),
            CustomerRateLine.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerRateLine.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def get_surcharge_rule(
        self,
        tenant_id: str,
        rate_card_id: str,
        surcharge_rule_id: str,
    ) -> CustomerSurchargeRule | None:
        statement = select(CustomerSurchargeRule).where(
            CustomerSurchargeRule.tenant_id == tenant_id,
            CustomerSurchargeRule.rate_card_id == rate_card_id,
            CustomerSurchargeRule.id == surcharge_rule_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_surcharge_rules(self, tenant_id: str, rate_card_id: str) -> list[CustomerSurchargeRule]:
        statement = (
            select(CustomerSurchargeRule)
            .where(CustomerSurchargeRule.tenant_id == tenant_id, CustomerSurchargeRule.rate_card_id == rate_card_id)
            .order_by(CustomerSurchargeRule.sort_order, CustomerSurchargeRule.id)
        )
        return list(self.session.scalars(statement).all())

    def create_surcharge_rule(
        self,
        tenant_id: str,
        rate_card_id: str,
        payload: CustomerSurchargeRuleCreate,
        actor_user_id: str | None,
    ) -> CustomerSurchargeRule:
        row = CustomerSurchargeRule(
            tenant_id=tenant_id,
            rate_card_id=rate_card_id,
            surcharge_type=payload.surcharge_type.strip().lower(),
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            weekday_mask=payload.weekday_mask,
            time_from_minute=payload.time_from_minute,
            time_to_minute=payload.time_to_minute,
            region_code=payload.region_code.strip().upper() if payload.region_code else None,
            percent_value=payload.percent_value,
            fixed_amount=payload.fixed_amount,
            currency_code=payload.currency_code.strip().upper() if payload.currency_code else None,
            sort_order=payload.sort_order,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_surcharge_rule(tenant_id, rate_card_id, row.id) or row

    def update_surcharge_rule(
        self,
        tenant_id: str,
        rate_card_id: str,
        surcharge_rule_id: str,
        payload: CustomerSurchargeRuleUpdate,
        actor_user_id: str | None,
    ) -> CustomerSurchargeRule | None:
        row = self.get_surcharge_rule(tenant_id, rate_card_id, surcharge_rule_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "surcharge_rule")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_surcharge_rule(tenant_id, rate_card_id, surcharge_rule_id)

    def get_customer_address(self, tenant_id: str, customer_id: str, link_id: str) -> CustomerAddressLink | None:
        statement = (
            select(CustomerAddressLink)
            .where(
                CustomerAddressLink.tenant_id == tenant_id,
                CustomerAddressLink.customer_id == customer_id,
                CustomerAddressLink.id == link_id,
            )
            .options(selectinload(CustomerAddressLink.address))
        )
        return self.session.scalars(statement).one_or_none()

    def create_customer_address(
        self,
        tenant_id: str,
        customer_id: str,
        payload: CustomerAddressCreate,
        actor_user_id: str | None,
    ) -> CustomerAddressLink:
        row = CustomerAddressLink(
            tenant_id=tenant_id,
            customer_id=customer_id,
            address_id=payload.address_id,
            address_type=payload.address_type,
            label=payload.label,
            is_default=payload.is_default,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_customer_address(tenant_id, customer_id, row.id) or row

    def update_customer_address(
        self,
        tenant_id: str,
        customer_id: str,
        link_id: str,
        payload: CustomerAddressUpdate,
        actor_user_id: str | None,
    ) -> CustomerAddressLink | None:
        row = self.get_customer_address(tenant_id, customer_id, link_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "address_link")
        self._apply_update(
            row,
            payload.model_dump(exclude_unset=True, exclude={"version_no"}),
            actor_user_id,
        )
        self._commit_or_raise()
        return self.get_customer_address(tenant_id, customer_id, link_id)

    def find_customer_by_number(
        self,
        tenant_id: str,
        customer_number: str,
        *,
        exclude_id: str | None = None,
    ) -> Customer | None:
        statement = select(Customer).where(
            Customer.tenant_id == tenant_id,
            Customer.customer_number == customer_number,
        )
        if exclude_id is not None:
            statement = statement.where(Customer.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_contact_by_email(
        self,
        tenant_id: str,
        customer_id: str,
        email: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerContact | None:
        statement = select(CustomerContact).where(
            CustomerContact.tenant_id == tenant_id,
            CustomerContact.customer_id == customer_id,
            CustomerContact.archived_at.is_(None),
            func.lower(CustomerContact.email) == email.lower(),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerContact.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_contact_by_name(
        self,
        tenant_id: str,
        customer_id: str,
        full_name: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerContact | None:
        statement = select(CustomerContact).where(
            CustomerContact.tenant_id == tenant_id,
            CustomerContact.customer_id == customer_id,
            CustomerContact.archived_at.is_(None),
            func.lower(CustomerContact.full_name) == full_name.lower(),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerContact.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def has_primary_contact(self, tenant_id: str, customer_id: str, *, exclude_id: str | None = None) -> bool:
        statement = select(CustomerContact.id).where(
            CustomerContact.tenant_id == tenant_id,
            CustomerContact.customer_id == customer_id,
            CustomerContact.is_primary_contact.is_(True),
            CustomerContact.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerContact.id != exclude_id)
        return self.session.scalars(statement).first() is not None

    def has_default_invoice_party(self, tenant_id: str, customer_id: str, *, exclude_id: str | None = None) -> bool:
        statement = select(CustomerInvoiceParty.id).where(
            CustomerInvoiceParty.tenant_id == tenant_id,
            CustomerInvoiceParty.customer_id == customer_id,
            CustomerInvoiceParty.is_default.is_(True),
            CustomerInvoiceParty.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerInvoiceParty.id != exclude_id)
        return self.session.scalars(statement).first() is not None

    def has_default_address(
        self,
        tenant_id: str,
        customer_id: str,
        address_type: str,
        *,
        exclude_id: str | None = None,
    ) -> bool:
        statement = select(CustomerAddressLink.id).where(
            CustomerAddressLink.tenant_id == tenant_id,
            CustomerAddressLink.customer_id == customer_id,
            CustomerAddressLink.address_type == address_type,
            CustomerAddressLink.is_default.is_(True),
            CustomerAddressLink.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerAddressLink.id != exclude_id)
        return self.session.scalars(statement).first() is not None

    def find_duplicate_address_link(
        self,
        tenant_id: str,
        customer_id: str,
        address_id: str,
        address_type: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerAddressLink | None:
        statement = select(CustomerAddressLink).where(
            CustomerAddressLink.tenant_id == tenant_id,
            CustomerAddressLink.customer_id == customer_id,
            CustomerAddressLink.address_id == address_id,
            CustomerAddressLink.address_type == address_type,
        )
        if exclude_id is not None:
            statement = statement.where(CustomerAddressLink.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_address_link_by_type(
        self,
        tenant_id: str,
        customer_id: str,
        address_type: str,
        *,
        exclude_id: str | None = None,
    ) -> CustomerAddressLink | None:
        statement = select(CustomerAddressLink).where(
            CustomerAddressLink.tenant_id == tenant_id,
            CustomerAddressLink.customer_id == customer_id,
            CustomerAddressLink.address_type == address_type,
            CustomerAddressLink.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerAddressLink.id != exclude_id)
        return self.session.scalars(statement).first()

    def list_history_entries(self, tenant_id: str, customer_id: str) -> list[CustomerHistoryEntry]:
        statement = (
            select(CustomerHistoryEntry)
            .where(CustomerHistoryEntry.tenant_id == tenant_id, CustomerHistoryEntry.customer_id == customer_id)
            .order_by(CustomerHistoryEntry.created_at.desc(), CustomerHistoryEntry.sort_order.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_history_entry(self, tenant_id: str, customer_id: str, history_entry_id: str) -> CustomerHistoryEntry | None:
        statement = select(CustomerHistoryEntry).where(
            CustomerHistoryEntry.tenant_id == tenant_id,
            CustomerHistoryEntry.customer_id == customer_id,
            CustomerHistoryEntry.id == history_entry_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_history_entry(self, row: CustomerHistoryEntry) -> CustomerHistoryEntry:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_employee_blocks(self, tenant_id: str, customer_id: str) -> list[CustomerEmployeeBlock]:
        statement = (
            select(CustomerEmployeeBlock)
            .where(
                CustomerEmployeeBlock.tenant_id == tenant_id,
                CustomerEmployeeBlock.customer_id == customer_id,
            )
            .order_by(CustomerEmployeeBlock.effective_from.desc(), CustomerEmployeeBlock.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def get_employee_block(
        self,
        tenant_id: str,
        customer_id: str,
        block_id: str,
    ) -> CustomerEmployeeBlock | None:
        statement = select(CustomerEmployeeBlock).where(
            CustomerEmployeeBlock.tenant_id == tenant_id,
            CustomerEmployeeBlock.customer_id == customer_id,
            CustomerEmployeeBlock.id == block_id,
        )
        return self.session.scalars(statement).one_or_none()

    def find_overlapping_employee_block(
        self,
        tenant_id: str,
        customer_id: str,
        employee_id: str,
        effective_from,
        effective_to,
        *,
        exclude_id: str | None = None,
    ) -> CustomerEmployeeBlock | None:
        statement = select(CustomerEmployeeBlock).where(
            CustomerEmployeeBlock.tenant_id == tenant_id,
            CustomerEmployeeBlock.customer_id == customer_id,
            CustomerEmployeeBlock.employee_id == employee_id,
            CustomerEmployeeBlock.archived_at.is_(None),
            CustomerEmployeeBlock.effective_from <= (effective_to or effective_from),
            or_(CustomerEmployeeBlock.effective_to.is_(None), CustomerEmployeeBlock.effective_to >= effective_from),
        )
        if exclude_id is not None:
            statement = statement.where(CustomerEmployeeBlock.id != exclude_id)
        return self.session.scalars(statement).first()

    def create_employee_block(self, row: CustomerEmployeeBlock) -> CustomerEmployeeBlock:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def update_employee_block(
        self,
        tenant_id: str,
        customer_id: str,
        block_id: str,
        payload,
        actor_user_id: str | None,
    ) -> CustomerEmployeeBlock | None:
        row = self.get_employee_block(tenant_id, customer_id, block_id)
        if row is None:
            return None
        updates = payload.model_dump(exclude_unset=True, exclude={"version_no"})
        for field_name, value in updates.items():
            setattr(row, field_name, value)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def get_lookup_value(self, lookup_id: str) -> LookupValue | None:
        return self.session.get(LookupValue, lookup_id)

    def list_lookup_values(self, tenant_id: str, domain: str) -> list[LookupValue]:
        statement = (
            select(LookupValue)
            .where(
                LookupValue.domain == domain,
                LookupValue.archived_at.is_(None),
                or_(LookupValue.tenant_id.is_(None), LookupValue.tenant_id == tenant_id),
            )
            .order_by(LookupValue.sort_order.asc(), LookupValue.label.asc())
        )
        return list(self.session.scalars(statement).all())

    def find_lookup_by_domain_code(
        self,
        tenant_id: str | None,
        domain: str,
        code: str,
    ) -> LookupValue | None:
        tenant_scope = (
            or_(LookupValue.tenant_id.is_(None), LookupValue.tenant_id == tenant_id)
            if tenant_id is not None
            else LookupValue.tenant_id.is_(None)
        )
        statement = (
            select(LookupValue)
            .where(
                LookupValue.domain == domain,
                LookupValue.code == code,
                tenant_scope,
            )
            .order_by(LookupValue.tenant_id.desc().nulls_last())
        )
        return self.session.scalars(statement).first()

    def get_branch(self, tenant_id: str, branch_id: str) -> Branch | None:
        statement = select(Branch).where(Branch.tenant_id == tenant_id, Branch.id == branch_id)
        return self.session.scalars(statement).one_or_none()

    def list_branches(self, tenant_id: str) -> list[Branch]:
        statement = (
            select(Branch)
            .where(Branch.tenant_id == tenant_id, Branch.archived_at.is_(None), Branch.status == "active")
            .order_by(Branch.code.asc(), Branch.name.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_mandate(self, tenant_id: str, mandate_id: str) -> Mandate | None:
        statement = select(Mandate).where(Mandate.tenant_id == tenant_id, Mandate.id == mandate_id)
        return self.session.scalars(statement).one_or_none()

    def list_mandates(self, tenant_id: str) -> list[Mandate]:
        statement = (
            select(Mandate)
            .where(Mandate.tenant_id == tenant_id, Mandate.archived_at.is_(None), Mandate.status == "active")
            .order_by(Mandate.code.asc(), Mandate.name.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None:
        statement = select(UserAccount).where(UserAccount.tenant_id == tenant_id, UserAccount.id == user_id)
        return self.session.scalars(statement).one_or_none()

    def get_address(self, address_id: str) -> Address | None:
        return self.session.get(Address, address_id)

    def get_portal_customer_scope_match(
        self,
        tenant_id: str,
        user_id: str,
        allowed_customer_ids: Sequence[str],
    ) -> tuple[Customer, CustomerContact] | None:
        if not allowed_customer_ids:
            return None

        statement = (
            select(Customer, CustomerContact)
            .join(
                CustomerContact,
                (CustomerContact.tenant_id == Customer.tenant_id) & (CustomerContact.customer_id == Customer.id),
            )
            .where(
                Customer.tenant_id == tenant_id,
                CustomerContact.tenant_id == tenant_id,
                CustomerContact.user_id == user_id,
                CustomerContact.archived_at.is_(None),
                Customer.id.in_(list(allowed_customer_ids)),
            )
            .order_by(CustomerContact.created_at.asc())
        )
        row = self.session.execute(statement).first()
        if row is None:
            return None
        customer, contact = row
        return customer, contact

    @staticmethod
    def _apply_update(row: object, data: dict[str, object], actor_user_id: str | None) -> None:
        for field, value in data.items():
            setattr(row, field, value)
        setattr(row, "updated_by_user_id", actor_user_id)
        setattr(row, "version_no", getattr(row, "version_no") + 1)

    @staticmethod
    def _assert_version(expected: int, actual: int | None, entity: str) -> None:
        if actual is None or actual != expected:
            raise ApiException(
                409,
                f"customers.conflict.stale_{entity}_version",
                f"errors.customers.{entity}.stale_version",
                {"expected_version_no": expected},
            )

    def _tenant_scoped_get(self, model: type[Customer], tenant_id: str, row_id: str):
        statement = select(model).where(model.tenant_id == tenant_id, model.id == row_id)
        return self.session.scalars(statement).one_or_none()

    def _commit_or_raise(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise self._translate_integrity_error(exc) from exc

    @staticmethod
    def _translate_integrity_error(exc: IntegrityError) -> ApiException:
        message = str(exc.orig)
        if "uq_crm_customer_tenant_customer_number" in message:
            return ApiException(409, "customers.conflict.customer_number", "errors.customers.customer.duplicate_number")
        if "uq_crm_customer_billing_profile_customer" in message:
            return ApiException(
                409,
                "customers.conflict.billing_profile_exists",
                "errors.customers.billing_profile.duplicate_customer",
            )
        if "uq_crm_customer_contact_primary_per_customer" in message:
            return ApiException(409, "customers.conflict.primary_contact", "errors.customers.contact.primary_conflict")
        if "uq_crm_customer_contact_tenant_user_id" in message:
            return ApiException(409, "customers.conflict.portal_user", "errors.customers.contact.duplicate_user_link")
        if "uq_crm_customer_invoice_party_default_per_customer" in message:
            return ApiException(
                409,
                "customers.conflict.default_invoice_party",
                "errors.customers.invoice_party.default_conflict",
            )
        if "uq_crm_customer_address_default_per_type" in message:
            return ApiException(
                409,
                "customers.conflict.default_address",
                "errors.customers.customer_address.default_conflict",
            )
        if "uq_crm_customer_address_customer_address_type" in message:
            return ApiException(
                409,
                "customers.conflict.customer_address_duplicate",
                "errors.customers.customer_address.duplicate_link",
            )
        return ApiException(409, "customers.conflict.integrity", "errors.customers.conflict.integrity")
