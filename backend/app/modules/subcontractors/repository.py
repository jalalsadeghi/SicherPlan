"""SQLAlchemy repository for subcontractor aggregate maintenance."""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import ApiException
from app.modules.core.models import Address, Branch, LookupValue, Mandate
from app.modules.employees.models import QualificationType
from app.modules.iam.models import UserAccount
from app.modules.platform_services.integration_models import ImportExportJob
from app.modules.subcontractors.models import (
    Subcontractor,
    SubcontractorContact,
    SubcontractorFinanceProfile,
    SubcontractorHistoryEntry,
    SubcontractorRateCard,
    SubcontractorRateLine,
    SubcontractorScope,
    SubcontractorWorker,
    SubcontractorWorkerCredential,
    SubcontractorWorkerQualification,
)
from app.modules.subcontractors.schemas import (
    SubcontractorContactCreate,
    SubcontractorContactUpdate,
    SubcontractorCreate,
    SubcontractorFilter,
    SubcontractorFinanceProfileCreate,
    SubcontractorFinanceProfileUpdate,
    SubcontractorScopeCreate,
    SubcontractorScopeUpdate,
    SubcontractorUpdate,
    SubcontractorWorkerFilter,
)


class SqlAlchemySubcontractorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_subcontractors(self, tenant_id: str, filters: SubcontractorFilter) -> list[Subcontractor]:
        statement = (
            select(Subcontractor)
            .where(Subcontractor.tenant_id == tenant_id)
            .options(
                selectinload(Subcontractor.address),
                selectinload(Subcontractor.contacts),
                selectinload(Subcontractor.scopes),
                selectinload(Subcontractor.finance_profile),
            )
            .order_by(Subcontractor.subcontractor_number)
        )
        if not filters.include_archived:
            statement = statement.where(Subcontractor.archived_at.is_(None))
        if filters.status is not None:
            statement = statement.where(Subcontractor.status == filters.status)
        if filters.branch_id is not None:
            statement = statement.join(Subcontractor.scopes).where(SubcontractorScope.branch_id == filters.branch_id)
        if filters.mandate_id is not None:
            statement = statement.join(Subcontractor.scopes).where(SubcontractorScope.mandate_id == filters.mandate_id)
        if filters.search:
            like_term = f"%{filters.search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(Subcontractor.subcontractor_number).like(like_term),
                    func.lower(Subcontractor.legal_name).like(like_term),
                    func.lower(func.coalesce(Subcontractor.display_name, "")).like(like_term),
                )
            )
        return list(self.session.scalars(statement).unique().all())

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None:
        statement = (
            select(Subcontractor)
            .where(Subcontractor.tenant_id == tenant_id, Subcontractor.id == subcontractor_id)
            .options(
                selectinload(Subcontractor.address),
                selectinload(Subcontractor.contacts),
                selectinload(Subcontractor.scopes),
                selectinload(Subcontractor.finance_profile),
            )
        )
        return self.session.scalars(statement).one_or_none()

    def create_subcontractor(self, tenant_id: str, payload: SubcontractorCreate, actor_user_id: str | None) -> Subcontractor:
        row = Subcontractor(
            tenant_id=tenant_id,
            subcontractor_number=payload.subcontractor_number,
            legal_name=payload.legal_name,
            display_name=payload.display_name,
            legal_form_lookup_id=payload.legal_form_lookup_id,
            subcontractor_status_lookup_id=payload.subcontractor_status_lookup_id,
            managing_director_name=payload.managing_director_name,
            address_id=payload.address_id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_subcontractor(tenant_id, row.id) or row

    def update_subcontractor(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorUpdate,
        actor_user_id: str | None,
    ) -> Subcontractor | None:
        row = self._tenant_scoped_get(Subcontractor, tenant_id, subcontractor_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "subcontractor")
        self._apply_update(row, payload.model_dump(exclude_unset=True, exclude={"version_no"}), actor_user_id)
        self._commit_or_raise()
        return self.get_subcontractor(tenant_id, row.id)

    def save_subcontractor(self, row: Subcontractor) -> Subcontractor:
        self.session.add(row)
        self._commit_or_raise()
        return self.get_subcontractor(row.tenant_id, row.id) or row

    def list_contacts(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorContact]:
        statement = (
            select(SubcontractorContact)
            .where(SubcontractorContact.tenant_id == tenant_id, SubcontractorContact.subcontractor_id == subcontractor_id)
            .order_by(SubcontractorContact.full_name)
        )
        return list(self.session.scalars(statement).all())

    def get_contact(self, tenant_id: str, subcontractor_id: str, contact_id: str) -> SubcontractorContact | None:
        statement = select(SubcontractorContact).where(
            SubcontractorContact.tenant_id == tenant_id,
            SubcontractorContact.subcontractor_id == subcontractor_id,
            SubcontractorContact.id == contact_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_contact(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorContactCreate,
        actor_user_id: str | None,
    ) -> SubcontractorContact:
        row = SubcontractorContact(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            full_name=payload.full_name,
            title=payload.title,
            function_label=payload.function_label,
            email=payload.email,
            phone=payload.phone,
            mobile=payload.mobile,
            is_primary_contact=payload.is_primary_contact,
            portal_enabled=payload.portal_enabled,
            user_id=payload.user_id,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_contact(tenant_id, subcontractor_id, row.id) or row

    def update_contact(
        self,
        tenant_id: str,
        subcontractor_id: str,
        contact_id: str,
        payload: SubcontractorContactUpdate,
        actor_user_id: str | None,
    ) -> SubcontractorContact | None:
        row = self.get_contact(tenant_id, subcontractor_id, contact_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "subcontractor_contact")
        self._apply_update(row, payload.model_dump(exclude_unset=True, exclude={"version_no"}), actor_user_id)
        self._commit_or_raise()
        return self.get_contact(tenant_id, subcontractor_id, contact_id)

    def list_scopes(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorScope]:
        statement = (
            select(SubcontractorScope)
            .where(SubcontractorScope.tenant_id == tenant_id, SubcontractorScope.subcontractor_id == subcontractor_id)
            .order_by(SubcontractorScope.valid_from)
        )
        return list(self.session.scalars(statement).all())

    def get_scope(self, tenant_id: str, subcontractor_id: str, scope_id: str) -> SubcontractorScope | None:
        statement = select(SubcontractorScope).where(
            SubcontractorScope.tenant_id == tenant_id,
            SubcontractorScope.subcontractor_id == subcontractor_id,
            SubcontractorScope.id == scope_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorScopeCreate,
        actor_user_id: str | None,
    ) -> SubcontractorScope:
        row = SubcontractorScope(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            branch_id=payload.branch_id,
            mandate_id=payload.mandate_id,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
            notes=payload.notes,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_scope(tenant_id, subcontractor_id, row.id) or row

    def update_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        scope_id: str,
        payload: SubcontractorScopeUpdate,
        actor_user_id: str | None,
    ) -> SubcontractorScope | None:
        row = self.get_scope(tenant_id, subcontractor_id, scope_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "subcontractor_scope")
        self._apply_update(row, payload.model_dump(exclude_unset=True, exclude={"version_no"}), actor_user_id)
        self._commit_or_raise()
        return self.get_scope(tenant_id, subcontractor_id, scope_id)

    def get_finance_profile(self, tenant_id: str, subcontractor_id: str) -> SubcontractorFinanceProfile | None:
        statement = select(SubcontractorFinanceProfile).where(
            SubcontractorFinanceProfile.tenant_id == tenant_id,
            SubcontractorFinanceProfile.subcontractor_id == subcontractor_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_active_rate_cards(self, tenant_id: str, subcontractor_id: str, on_date: date) -> list[SubcontractorRateCard]:
        statement = (
            select(SubcontractorRateCard)
            .options(selectinload(SubcontractorRateCard.rate_lines))
            .where(
                SubcontractorRateCard.tenant_id == tenant_id,
                SubcontractorRateCard.subcontractor_id == subcontractor_id,
                SubcontractorRateCard.status_code == "active",
                SubcontractorRateCard.effective_from <= on_date,
                or_(SubcontractorRateCard.effective_until.is_(None), SubcontractorRateCard.effective_until >= on_date),
            )
            .order_by(SubcontractorRateCard.effective_from.desc(), SubcontractorRateCard.created_at.desc())
        )
        return list(self.session.scalars(statement).unique().all())

    def list_history_entries(self, tenant_id: str, subcontractor_id: str) -> list[SubcontractorHistoryEntry]:
        statement = (
            select(SubcontractorHistoryEntry)
            .where(
                SubcontractorHistoryEntry.tenant_id == tenant_id,
                SubcontractorHistoryEntry.subcontractor_id == subcontractor_id,
            )
            .order_by(SubcontractorHistoryEntry.occurred_at.desc(), SubcontractorHistoryEntry.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def get_history_entry(
        self,
        tenant_id: str,
        subcontractor_id: str,
        history_entry_id: str,
    ) -> SubcontractorHistoryEntry | None:
        statement = select(SubcontractorHistoryEntry).where(
            SubcontractorHistoryEntry.tenant_id == tenant_id,
            SubcontractorHistoryEntry.subcontractor_id == subcontractor_id,
            SubcontractorHistoryEntry.id == history_entry_id,
        )
        return self.session.scalars(statement).one_or_none()

    def create_history_entry(self, row: SubcontractorHistoryEntry) -> SubcontractorHistoryEntry:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def create_finance_profile(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorFinanceProfileCreate,
        actor_user_id: str | None,
    ) -> SubcontractorFinanceProfile:
        row = SubcontractorFinanceProfile(
            tenant_id=tenant_id,
            subcontractor_id=subcontractor_id,
            invoice_email=payload.invoice_email,
            payment_terms_days=payload.payment_terms_days,
            payment_terms_note=payload.payment_terms_note,
            tax_number=payload.tax_number,
            vat_id=payload.vat_id,
            bank_account_holder=payload.bank_account_holder,
            bank_iban=payload.bank_iban,
            bank_bic=payload.bank_bic,
            bank_name=payload.bank_name,
            invoice_delivery_method_lookup_id=payload.invoice_delivery_method_lookup_id,
            invoice_status_mode_lookup_id=payload.invoice_status_mode_lookup_id,
            billing_note=payload.billing_note,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        self.session.add(row)
        self._commit_or_raise()
        return self.get_finance_profile(tenant_id, subcontractor_id) or row

    def update_finance_profile(
        self,
        tenant_id: str,
        subcontractor_id: str,
        payload: SubcontractorFinanceProfileUpdate,
        actor_user_id: str | None,
    ) -> SubcontractorFinanceProfile | None:
        row = self.get_finance_profile(tenant_id, subcontractor_id)
        if row is None:
            return None
        self._assert_version(row.version_no, payload.version_no, "subcontractor_finance_profile")
        self._apply_update(row, payload.model_dump(exclude_unset=True, exclude={"version_no"}), actor_user_id)
        self._commit_or_raise()
        return self.get_finance_profile(tenant_id, subcontractor_id)

    def find_subcontractor_by_number(
        self,
        tenant_id: str,
        subcontractor_number: str,
        *,
        exclude_id: str | None = None,
    ) -> Subcontractor | None:
        statement = select(Subcontractor).where(
            Subcontractor.tenant_id == tenant_id,
            func.lower(Subcontractor.subcontractor_number) == subcontractor_number.strip().lower(),
        )
        if exclude_id is not None:
            statement = statement.where(Subcontractor.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def has_primary_contact(self, tenant_id: str, subcontractor_id: str, *, exclude_id: str | None = None) -> bool:
        statement = select(SubcontractorContact.id).where(
            SubcontractorContact.tenant_id == tenant_id,
            SubcontractorContact.subcontractor_id == subcontractor_id,
            SubcontractorContact.is_primary_contact.is_(True),
            SubcontractorContact.archived_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(SubcontractorContact.id != exclude_id)
        return self.session.scalar(statement.limit(1)) is not None

    def find_contact_by_user_id(
        self,
        tenant_id: str,
        user_id: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorContact | None:
        statement = select(SubcontractorContact).where(
            SubcontractorContact.tenant_id == tenant_id,
            SubcontractorContact.user_id == user_id,
        )
        if exclude_id is not None:
            statement = statement.where(SubcontractorContact.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def get_portal_contact_for_user(self, tenant_id: str, user_id: str) -> tuple[Subcontractor, SubcontractorContact] | None:
        statement = (
            select(Subcontractor, SubcontractorContact)
            .join(
                SubcontractorContact,
                and_(
                    SubcontractorContact.tenant_id == Subcontractor.tenant_id,
                    SubcontractorContact.subcontractor_id == Subcontractor.id,
                ),
            )
            .where(
                Subcontractor.tenant_id == tenant_id,
                SubcontractorContact.user_id == user_id,
            )
            .options(
                selectinload(Subcontractor.contacts),
                selectinload(Subcontractor.scopes),
            )
        )
        return self.session.execute(statement).one_or_none()

    def get_portal_subcontractor_scope_match(
        self,
        tenant_id: str,
        user_id: str,
        allowed_subcontractor_ids: list[str],
    ) -> tuple[Subcontractor, SubcontractorContact] | None:
        if not allowed_subcontractor_ids:
            return None
        statement = (
            select(Subcontractor, SubcontractorContact)
            .join(
                SubcontractorContact,
                and_(
                    SubcontractorContact.tenant_id == Subcontractor.tenant_id,
                    SubcontractorContact.subcontractor_id == Subcontractor.id,
                ),
            )
            .where(
                Subcontractor.tenant_id == tenant_id,
                Subcontractor.id.in_(allowed_subcontractor_ids),
                SubcontractorContact.user_id == user_id,
            )
            .options(
                selectinload(Subcontractor.contacts),
                selectinload(Subcontractor.scopes),
            )
        )
        return self.session.execute(statement).one_or_none()

    def find_overlapping_scope(
        self,
        tenant_id: str,
        subcontractor_id: str,
        branch_id: str,
        mandate_id: str | None,
        valid_from: date,
        valid_to: date | None,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorScope | None:
        end_value = valid_to or date.max
        statement = select(SubcontractorScope).where(
            SubcontractorScope.tenant_id == tenant_id,
            SubcontractorScope.subcontractor_id == subcontractor_id,
            SubcontractorScope.branch_id == branch_id,
            SubcontractorScope.archived_at.is_(None),
            SubcontractorScope.mandate_id.is_(None) if mandate_id is None else SubcontractorScope.mandate_id == mandate_id,
        )
        if exclude_id is not None:
            statement = statement.where(SubcontractorScope.id != exclude_id)
        rows = list(self.session.scalars(statement).all())
        for row in rows:
            row_end = row.valid_to or date.max
            if row.valid_from <= end_value and valid_from <= row_end:
                return row
        return None

    def get_lookup_value(self, lookup_id: str) -> LookupValue | None:
        return self.session.get(LookupValue, lookup_id)

    def get_branch(self, tenant_id: str, branch_id: str) -> Branch | None:
        statement = select(Branch).where(Branch.tenant_id == tenant_id, Branch.id == branch_id)
        return self.session.scalars(statement).one_or_none()

    def get_mandate(self, tenant_id: str, mandate_id: str) -> Mandate | None:
        statement = select(Mandate).where(Mandate.tenant_id == tenant_id, Mandate.id == mandate_id)
        return self.session.scalars(statement).one_or_none()

    def get_user_account(self, tenant_id: str, user_id: str) -> UserAccount | None:
        statement = select(UserAccount).where(UserAccount.tenant_id == tenant_id, UserAccount.id == user_id)
        return self.session.scalars(statement).one_or_none()

    def list_contact_user_options(self, tenant_id: str, search: str = "", limit: int = 25) -> list[UserAccount]:
        statement = (
            select(UserAccount)
            .where(
                UserAccount.tenant_id == tenant_id,
                UserAccount.archived_at.is_(None),
                UserAccount.status == "active",
            )
            .order_by(UserAccount.username)
            .limit(limit)
        )
        if search.strip():
            like_term = f"%{search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(UserAccount.username).like(like_term),
                    func.lower(func.coalesce(UserAccount.email, "")).like(like_term),
                    func.lower(func.coalesce(UserAccount.full_name, "")).like(like_term),
                )
            )
        return list(self.session.scalars(statement).all())

    def get_address(self, address_id: str) -> Address | None:
        return self.session.get(Address, address_id)

    def create_address(self, row: Address) -> Address:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def list_workers(self, tenant_id: str, subcontractor_id: str, filters: SubcontractorWorkerFilter) -> list[SubcontractorWorker]:
        statement = (
            select(SubcontractorWorker)
            .where(
                SubcontractorWorker.tenant_id == tenant_id,
                SubcontractorWorker.subcontractor_id == subcontractor_id,
            )
            .options(
                selectinload(SubcontractorWorker.qualifications).selectinload(SubcontractorWorkerQualification.qualification_type),
                selectinload(SubcontractorWorker.credentials),
            )
            .order_by(SubcontractorWorker.worker_no)
        )
        if not filters.include_archived:
            statement = statement.where(SubcontractorWorker.archived_at.is_(None))
        if filters.status is not None:
            statement = statement.where(SubcontractorWorker.status == filters.status)
        if filters.search:
            like_term = f"%{filters.search.strip().lower()}%"
            statement = statement.where(
                or_(
                    func.lower(SubcontractorWorker.worker_no).like(like_term),
                    func.lower(SubcontractorWorker.first_name).like(like_term),
                    func.lower(SubcontractorWorker.last_name).like(like_term),
                    func.lower(func.coalesce(SubcontractorWorker.preferred_name, "")).like(like_term),
                )
            )
        return list(self.session.scalars(statement).unique().all())

    def get_worker(self, tenant_id: str, subcontractor_id: str, worker_id: str) -> SubcontractorWorker | None:
        statement = (
            select(SubcontractorWorker)
            .where(
                SubcontractorWorker.tenant_id == tenant_id,
                SubcontractorWorker.subcontractor_id == subcontractor_id,
                SubcontractorWorker.id == worker_id,
            )
            .options(
                selectinload(SubcontractorWorker.qualifications).selectinload(SubcontractorWorkerQualification.qualification_type),
                selectinload(SubcontractorWorker.credentials),
            )
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_worker(self, row: SubcontractorWorker) -> SubcontractorWorker:
        self.session.add(row)
        self._commit_or_raise()
        return self.get_worker(row.tenant_id, row.subcontractor_id, row.id) or row

    def update_worker(self, row: SubcontractorWorker) -> SubcontractorWorker:
        self.session.add(row)
        self._commit_or_raise()
        return self.get_worker(row.tenant_id, row.subcontractor_id, row.id) or row

    def find_worker_by_number(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_no: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorker | None:
        statement = select(SubcontractorWorker).where(
            SubcontractorWorker.tenant_id == tenant_id,
            SubcontractorWorker.subcontractor_id == subcontractor_id,
            func.lower(SubcontractorWorker.worker_no) == worker_no.strip().lower(),
        )
        if exclude_id is not None:
            statement = statement.where(SubcontractorWorker.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def list_worker_qualifications(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
    ) -> list[SubcontractorWorkerQualification]:
        statement = (
            select(SubcontractorWorkerQualification)
            .join(
                SubcontractorWorker,
                and_(
                    SubcontractorWorker.tenant_id == SubcontractorWorkerQualification.tenant_id,
                    SubcontractorWorker.id == SubcontractorWorkerQualification.worker_id,
                ),
            )
            .where(
                SubcontractorWorkerQualification.tenant_id == tenant_id,
                SubcontractorWorkerQualification.worker_id == worker_id,
                SubcontractorWorker.subcontractor_id == subcontractor_id,
            )
            .options(selectinload(SubcontractorWorkerQualification.qualification_type))
            .order_by(SubcontractorWorkerQualification.valid_until, SubcontractorWorkerQualification.created_at)
        )
        return list(self.session.scalars(statement).unique().all())

    def get_worker_qualification(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        qualification_id: str,
    ) -> SubcontractorWorkerQualification | None:
        statement = (
            select(SubcontractorWorkerQualification)
            .join(
                SubcontractorWorker,
                and_(
                    SubcontractorWorker.tenant_id == SubcontractorWorkerQualification.tenant_id,
                    SubcontractorWorker.id == SubcontractorWorkerQualification.worker_id,
                ),
            )
            .where(
                SubcontractorWorkerQualification.tenant_id == tenant_id,
                SubcontractorWorkerQualification.id == qualification_id,
                SubcontractorWorkerQualification.worker_id == worker_id,
                SubcontractorWorker.subcontractor_id == subcontractor_id,
            )
            .options(selectinload(SubcontractorWorkerQualification.qualification_type))
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_worker_qualification(self, row: SubcontractorWorkerQualification) -> SubcontractorWorkerQualification:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def update_worker_qualification(self, row: SubcontractorWorkerQualification) -> SubcontractorWorkerQualification:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def get_qualification_type(self, tenant_id: str, qualification_type_id: str) -> QualificationType | None:
        statement = select(QualificationType).where(
            QualificationType.tenant_id == tenant_id,
            QualificationType.id == qualification_type_id,
        )
        return self.session.scalars(statement).one_or_none()

    def list_qualification_types(self, tenant_id: str) -> list[QualificationType]:
        statement = (
            select(QualificationType)
            .where(
                QualificationType.tenant_id == tenant_id,
                QualificationType.is_active.is_(True),
                QualificationType.status == "active",
                QualificationType.archived_at.is_(None),
            )
            .order_by(QualificationType.label, QualificationType.code)
        )
        return list(self.session.scalars(statement).all())

    def list_worker_credentials(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
    ) -> list[SubcontractorWorkerCredential]:
        statement = (
            select(SubcontractorWorkerCredential)
            .join(
                SubcontractorWorker,
                and_(
                    SubcontractorWorker.tenant_id == SubcontractorWorkerCredential.tenant_id,
                    SubcontractorWorker.id == SubcontractorWorkerCredential.worker_id,
                ),
            )
            .where(
                SubcontractorWorkerCredential.tenant_id == tenant_id,
                SubcontractorWorkerCredential.worker_id == worker_id,
                SubcontractorWorker.subcontractor_id == subcontractor_id,
            )
            .order_by(SubcontractorWorkerCredential.valid_from, SubcontractorWorkerCredential.created_at)
        )
        return list(self.session.scalars(statement).all())

    def get_worker_credential(
        self,
        tenant_id: str,
        subcontractor_id: str,
        worker_id: str,
        credential_id: str,
    ) -> SubcontractorWorkerCredential | None:
        statement = (
            select(SubcontractorWorkerCredential)
            .join(
                SubcontractorWorker,
                and_(
                    SubcontractorWorker.tenant_id == SubcontractorWorkerCredential.tenant_id,
                    SubcontractorWorker.id == SubcontractorWorkerCredential.worker_id,
                ),
            )
            .where(
                SubcontractorWorkerCredential.tenant_id == tenant_id,
                SubcontractorWorkerCredential.worker_id == worker_id,
                SubcontractorWorkerCredential.id == credential_id,
                SubcontractorWorker.subcontractor_id == subcontractor_id,
            )
        )
        return self.session.scalars(statement).one_or_none()

    def create_worker_credential(self, row: SubcontractorWorkerCredential) -> SubcontractorWorkerCredential:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def update_worker_credential(self, row: SubcontractorWorkerCredential) -> SubcontractorWorkerCredential:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def find_worker_credential_by_no(
        self,
        tenant_id: str,
        credential_no: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorkerCredential | None:
        statement = select(SubcontractorWorkerCredential).where(
            SubcontractorWorkerCredential.tenant_id == tenant_id,
            SubcontractorWorkerCredential.credential_no == credential_no,
        )
        if exclude_id is not None:
            statement = statement.where(SubcontractorWorkerCredential.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def find_worker_credential_by_encoded_value(
        self,
        tenant_id: str,
        encoded_value: str,
        *,
        exclude_id: str | None = None,
    ) -> SubcontractorWorkerCredential | None:
        statement = select(SubcontractorWorkerCredential).where(
            SubcontractorWorkerCredential.tenant_id == tenant_id,
            SubcontractorWorkerCredential.encoded_value == encoded_value,
        )
        if exclude_id is not None:
            statement = statement.where(SubcontractorWorkerCredential.id != exclude_id)
        return self.session.scalars(statement).one_or_none()

    def create_job(self, row: ImportExportJob) -> ImportExportJob:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def save_job(self, row: ImportExportJob) -> ImportExportJob:
        self.session.add(row)
        self._commit_or_raise()
        self.session.refresh(row)
        return row

    def _tenant_scoped_get(self, model, tenant_id: str, entity_id: str):  # noqa: ANN001
        statement = select(model).where(model.tenant_id == tenant_id, model.id == entity_id)
        return self.session.scalars(statement).one_or_none()

    def _apply_update(self, row, values: dict[str, object], actor_user_id: str | None) -> None:  # noqa: ANN001
        for key, value in values.items():
            setattr(row, key, value)
        row.updated_by_user_id = actor_user_id
        row.version_no += 1

    @staticmethod
    def _assert_version(current_version: int, next_version: int | None, entity_name: str) -> None:
        if next_version is None or current_version != next_version:
            raise ApiException(
                409,
                f"subcontractors.conflict.{entity_name}.stale_version",
                f"errors.subcontractors.{entity_name}.stale_version",
            )

    def _commit_or_raise(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ApiException(
                409,
                "subcontractors.conflict.integrity",
                "errors.subcontractors.integrity",
                {"detail": str(exc.orig)},
            ) from exc
