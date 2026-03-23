"""SQLAlchemy-backed watchbook and patrol repository."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.modules.core.models import TenantSetting
from app.modules.customers.models import Customer
from app.modules.employees.models import Employee
from app.modules.field_execution.models import PatrolRound, PatrolRoundEvent, Watchbook, WatchbookEntry
from app.modules.platform_services.docs_models import Document, DocumentLink
from app.modules.planning.models import Assignment, CustomerOrder, PatrolCheckpoint, PatrolRoute, PlanningRecord, Shift, ShiftPlan, Site
from app.modules.subcontractors.models import Subcontractor, SubcontractorWorker


class SqlAlchemyWatchbookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_watchbooks(self, tenant_id: str, filters) -> list[Watchbook]:  # noqa: ANN001
        statement = self._watchbook_query().where(Watchbook.tenant_id == tenant_id, Watchbook.archived_at.is_(None))
        if filters.context_type is not None:
            statement = statement.where(Watchbook.context_type == filters.context_type)
        if filters.site_id is not None:
            statement = statement.where(Watchbook.site_id == filters.site_id)
        if filters.order_id is not None:
            statement = statement.where(Watchbook.order_id == filters.order_id)
        if filters.planning_record_id is not None:
            statement = statement.where(Watchbook.planning_record_id == filters.planning_record_id)
        if filters.shift_id is not None:
            statement = statement.where(Watchbook.shift_id == filters.shift_id)
        if filters.log_date_from is not None:
            statement = statement.where(Watchbook.log_date >= filters.log_date_from)
        if filters.log_date_to is not None:
            statement = statement.where(Watchbook.log_date <= filters.log_date_to)
        if filters.closure_state_code is not None:
            statement = statement.where(Watchbook.closure_state_code == filters.closure_state_code)
        if filters.review_status_code is not None:
            statement = statement.where(Watchbook.review_status_code == filters.review_status_code)
        if filters.released_to_customer is not None:
            statement = statement.where(Watchbook.customer_visibility_released.is_(filters.released_to_customer))
        if filters.released_to_subcontractor is not None:
            statement = statement.where(Watchbook.subcontractor_visibility_released.is_(filters.released_to_subcontractor))
        statement = statement.order_by(Watchbook.log_date.desc(), Watchbook.updated_at.desc())
        return list(self.session.scalars(statement).unique().all())

    def get_watchbook(self, tenant_id: str, watchbook_id: str) -> Watchbook | None:
        statement = self._watchbook_query().where(Watchbook.tenant_id == tenant_id, Watchbook.id == watchbook_id)
        return self.session.scalars(statement).unique().one_or_none()

    def find_open_watchbook(
        self,
        tenant_id: str,
        *,
        context_type: str,
        log_date: date,
        site_id: str | None,
        order_id: str | None,
        planning_record_id: str | None,
    ) -> Watchbook | None:
        statement = self._watchbook_query().where(
            Watchbook.tenant_id == tenant_id,
            Watchbook.context_type == context_type,
            Watchbook.log_date == log_date,
            Watchbook.closure_state_code == "open",
            Watchbook.archived_at.is_(None),
            Watchbook.site_id.is_(site_id) if site_id is None else Watchbook.site_id == site_id,
            Watchbook.order_id.is_(order_id) if order_id is None else Watchbook.order_id == order_id,
            Watchbook.planning_record_id.is_(planning_record_id)
            if planning_record_id is None
            else Watchbook.planning_record_id == planning_record_id,
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_watchbook(self, row: Watchbook) -> Watchbook:
        self.session.add(row)
        self.session.commit()
        return self.get_watchbook(row.tenant_id, row.id) or row

    def save_watchbook(self, row: Watchbook) -> Watchbook:
        self.session.add(row)
        self.session.commit()
        return self.get_watchbook(row.tenant_id, row.id) or row

    def create_entry(self, row: WatchbookEntry) -> WatchbookEntry:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_documents_for_owner(self, tenant_id: str, owner_type: str, owner_id: str) -> list[Document]:
        statement = (
            select(Document)
            .options(joinedload(Document.document_type))
            .options(joinedload(Document.versions))
            .join(DocumentLink, DocumentLink.document_id == Document.id)
            .where(
                Document.tenant_id == tenant_id,
                DocumentLink.tenant_id == tenant_id,
                DocumentLink.owner_type == owner_type,
                DocumentLink.owner_id == owner_id,
            )
            .order_by(Document.created_at)
        )
        return list(self.session.scalars(statement).unique().all())

    def get_document(self, tenant_id: str, document_id: str) -> Document | None:
        statement = (
            select(Document)
            .options(joinedload(Document.document_type))
            .options(joinedload(Document.versions))
            .where(Document.tenant_id == tenant_id, Document.id == document_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_customer(self, tenant_id: str, customer_id: str) -> Customer | None:
        return self.session.scalars(select(Customer).where(Customer.tenant_id == tenant_id, Customer.id == customer_id)).one_or_none()

    def get_site(self, tenant_id: str, row_id: str) -> Site | None:
        return self.session.scalars(select(Site).where(Site.tenant_id == tenant_id, Site.id == row_id)).one_or_none()

    def get_order(self, tenant_id: str, row_id: str) -> CustomerOrder | None:
        return self.session.scalars(select(CustomerOrder).where(CustomerOrder.tenant_id == tenant_id, CustomerOrder.id == row_id)).one_or_none()

    def get_planning_record(self, tenant_id: str, row_id: str) -> PlanningRecord | None:
        statement = (
            select(PlanningRecord)
            .options(joinedload(PlanningRecord.order))
            .where(PlanningRecord.tenant_id == tenant_id, PlanningRecord.id == row_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_shift(self, tenant_id: str, row_id: str) -> Shift | None:
        statement = (
            select(Shift)
            .options(joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record))
            .where(Shift.tenant_id == tenant_id, Shift.id == row_id)
        )
        return self.session.scalars(statement).unique().one_or_none()

    def get_subcontractor_worker(self, tenant_id: str, worker_id: str) -> SubcontractorWorker | None:
        return self.session.scalars(
            select(SubcontractorWorker).where(SubcontractorWorker.tenant_id == tenant_id, SubcontractorWorker.id == worker_id)
        ).one_or_none()

    def get_subcontractor(self, tenant_id: str, subcontractor_id: str) -> Subcontractor | None:
        return self.session.scalars(
            select(Subcontractor).where(Subcontractor.tenant_id == tenant_id, Subcontractor.id == subcontractor_id)
        ).one_or_none()

    def get_tenant_setting(self, tenant_id: str, key: str) -> TenantSetting | None:
        return self.session.scalars(
            select(TenantSetting).where(TenantSetting.tenant_id == tenant_id, TenantSetting.key == key)
        ).one_or_none()

    def find_employee_by_user_id(self, tenant_id: str, user_id: str) -> Employee | None:
        return self.session.scalars(
            select(Employee).where(Employee.tenant_id == tenant_id, Employee.user_id == user_id, Employee.archived_at.is_(None))
        ).one_or_none()

    def list_released_employee_patrol_shifts(self, tenant_id: str, employee_id: str) -> list[Shift]:
        statement = (
            select(Shift)
            .options(joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record).joinedload(PlanningRecord.patrol_detail))
            .options(joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record).joinedload(PlanningRecord.order).joinedload(CustomerOrder.patrol_route))
            .options(joinedload(Shift.assignments))
            .join(Assignment, and_(Assignment.tenant_id == Shift.tenant_id, Assignment.shift_id == Shift.id))
            .where(
                Shift.tenant_id == tenant_id,
                Shift.release_state == "released",
                Assignment.employee_id == employee_id,
                Assignment.assignment_status_code.in_(("assigned", "confirmed")),
                Shift.archived_at.is_(None),
            )
            .order_by(Shift.starts_at)
        )
        return list(self.session.scalars(statement).unique().all())

    def get_patrol_route(self, tenant_id: str, patrol_route_id: str) -> PatrolRoute | None:
        statement = (
            select(PatrolRoute)
            .options(joinedload(PatrolRoute.checkpoints))
            .where(PatrolRoute.tenant_id == tenant_id, PatrolRoute.id == patrol_route_id, PatrolRoute.archived_at.is_(None))
        )
        return self.session.scalars(statement).unique().one_or_none()

    def list_patrol_checkpoints(self, tenant_id: str, patrol_route_id: str) -> list[PatrolCheckpoint]:
        statement = (
            select(PatrolCheckpoint)
            .where(PatrolCheckpoint.tenant_id == tenant_id, PatrolCheckpoint.patrol_route_id == patrol_route_id, PatrolCheckpoint.archived_at.is_(None))
            .order_by(PatrolCheckpoint.sequence_no)
        )
        return list(self.session.scalars(statement).all())

    def find_active_patrol_round(self, tenant_id: str, employee_id: str) -> PatrolRound | None:
        statement = self._patrol_round_query().where(
            PatrolRound.tenant_id == tenant_id,
            PatrolRound.employee_id == employee_id,
            PatrolRound.round_status_code == "active",
            PatrolRound.archived_at.is_(None),
        )
        return self.session.scalars(statement).unique().one_or_none()

    def find_patrol_round_by_sync_token(self, tenant_id: str, offline_sync_token: str) -> PatrolRound | None:
        statement = self._patrol_round_query().where(
            PatrolRound.tenant_id == tenant_id,
            PatrolRound.offline_sync_token == offline_sync_token,
        )
        return self.session.scalars(statement).unique().one_or_none()

    def create_patrol_round(self, row: PatrolRound) -> PatrolRound:
        self.session.add(row)
        self.session.commit()
        return self.get_patrol_round(row.tenant_id, row.id) or row

    def save_patrol_round(self, row: PatrolRound) -> PatrolRound:
        self.session.add(row)
        self.session.commit()
        return self.get_patrol_round(row.tenant_id, row.id) or row

    def get_patrol_round(self, tenant_id: str, patrol_round_id: str) -> PatrolRound | None:
        statement = self._patrol_round_query().where(PatrolRound.tenant_id == tenant_id, PatrolRound.id == patrol_round_id)
        return self.session.scalars(statement).unique().one_or_none()

    def list_patrol_round_events(self, tenant_id: str, patrol_round_id: str) -> list[PatrolRoundEvent]:
        statement = (
            select(PatrolRoundEvent)
            .where(PatrolRoundEvent.tenant_id == tenant_id, PatrolRoundEvent.patrol_round_id == patrol_round_id)
            .order_by(PatrolRoundEvent.sequence_no)
        )
        return list(self.session.scalars(statement).all())

    def get_patrol_event_by_client_id(self, tenant_id: str, patrol_round_id: str, client_event_id: str) -> PatrolRoundEvent | None:
        statement = select(PatrolRoundEvent).where(
            PatrolRoundEvent.tenant_id == tenant_id,
            PatrolRoundEvent.patrol_round_id == patrol_round_id,
            PatrolRoundEvent.client_event_id == client_event_id,
        )
        return self.session.scalars(statement).one_or_none()

    def next_patrol_event_sequence(self, tenant_id: str, patrol_round_id: str) -> int:
        statement = select(func.max(PatrolRoundEvent.sequence_no)).where(
            PatrolRoundEvent.tenant_id == tenant_id,
            PatrolRoundEvent.patrol_round_id == patrol_round_id,
        )
        current = self.session.scalar(statement)
        return int(current or 0) + 1

    def create_patrol_event(self, row: PatrolRoundEvent) -> PatrolRoundEvent:
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_customer_released_watchbooks(self, tenant_id: str, customer_id: str) -> list[Watchbook]:
        statement = (
            self._watchbook_query()
            .where(
                Watchbook.tenant_id == tenant_id,
                Watchbook.customer_id == customer_id,
                Watchbook.customer_visibility_released.is_(True),
                Watchbook.review_status_code == "reviewed",
                Watchbook.archived_at.is_(None),
            )
            .order_by(Watchbook.log_date.desc(), Watchbook.updated_at.desc())
        )
        return list(self.session.scalars(statement).unique().all())

    def list_subcontractor_released_watchbooks(self, tenant_id: str, subcontractor_id: str) -> list[Watchbook]:
        statement = (
            self._watchbook_query()
            .where(
                Watchbook.tenant_id == tenant_id,
                Watchbook.subcontractor_id == subcontractor_id,
                Watchbook.subcontractor_visibility_released.is_(True),
                Watchbook.review_status_code == "reviewed",
                Watchbook.archived_at.is_(None),
            )
            .order_by(Watchbook.log_date.desc(), Watchbook.updated_at.desc())
        )
        return list(self.session.scalars(statement).unique().all())

    def list_employee_watchbooks_for_planning_records(self, tenant_id: str, planning_record_ids: list[str]) -> list[Watchbook]:
        if not planning_record_ids:
            return []
        statement = (
            self._watchbook_query()
            .where(
                Watchbook.tenant_id == tenant_id,
                or_(
                    Watchbook.planning_record_id.in_(planning_record_ids),
                    and_(Watchbook.order_id.is_not(None), Watchbook.order_id.in_(select(CustomerOrder.id).where(CustomerOrder.tenant_id == tenant_id))),
                ),
                Watchbook.archived_at.is_(None),
            )
            .order_by(Watchbook.log_date.desc(), Watchbook.updated_at.desc())
        )
        return list(self.session.scalars(statement).unique().all())

    @staticmethod
    def _watchbook_query() -> Select[tuple[Watchbook]]:
        return (
            select(Watchbook)
            .options(joinedload(Watchbook.entries))
            .options(joinedload(Watchbook.customer))
            .options(joinedload(Watchbook.site))
            .options(joinedload(Watchbook.order))
            .options(joinedload(Watchbook.planning_record).joinedload(PlanningRecord.order))
            .options(joinedload(Watchbook.shift))
            .options(joinedload(Watchbook.subcontractor))
        )

    @staticmethod
    def _patrol_round_query() -> Select[tuple[PatrolRound]]:
        return (
            select(PatrolRound)
            .options(joinedload(PatrolRound.events).joinedload(PatrolRoundEvent.checkpoint))
            .options(joinedload(PatrolRound.patrol_route).joinedload(PatrolRoute.checkpoints))
            .options(joinedload(PatrolRound.watchbook))
            .options(joinedload(PatrolRound.shift).joinedload(Shift.shift_plan).joinedload(ShiftPlan.planning_record).joinedload(PlanningRecord.patrol_detail))
        )
