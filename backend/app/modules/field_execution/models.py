"""Watchbook and field-evidence models."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin
from app.modules.customers.models import Customer
from app.modules.iam.models import UserAccount
from app.modules.employees.models import Employee
from app.modules.planning.models import Assignment, CustomerOrder, PatrolCheckpoint, PatrolRoute, PlanningRecord, Shift, Site
from app.modules.subcontractors.models import Subcontractor, SubcontractorWorker


class Watchbook(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "watchbook"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_field_watchbook_tenant_customer",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_field_watchbook_tenant_site",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["ops.customer_order.tenant_id", "ops.customer_order.id"],
            name="fk_field_watchbook_tenant_order",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_field_watchbook_tenant_planning_record",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_watchbook_tenant_shift",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_field_watchbook_tenant_subcontractor",
            ondelete="SET NULL",
        ),
        CheckConstraint(
            "(CASE WHEN site_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN order_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN planning_record_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="watchbook_context_exactly_one",
        ),
        CheckConstraint(
            "context_type IN ('site','order','planning_record')",
            name="watchbook_context_type_valid",
        ),
        CheckConstraint(
            "review_status_code IN ('pending','reviewed')",
            name="watchbook_review_status_valid",
        ),
        CheckConstraint(
            "closure_state_code IN ('open','closed')",
            name="watchbook_closure_state_valid",
        ),
        Index(
            "uq_field_watchbook_open_context_date",
            "tenant_id",
            "log_date",
            "context_type",
            "site_id",
            "order_id",
            "planning_record_id",
            unique=True,
            postgresql_where=text("closure_state_code = 'open' AND archived_at IS NULL"),
        ),
        Index("ix_field_watchbook_context_lookup", "tenant_id", "customer_id", "log_date"),
        UniqueConstraint("tenant_id", "id", name="uq_field_watchbook_tenant_id_id"),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    context_type: Mapped[str] = mapped_column(String(40), nullable=False)
    log_date: Mapped[date] = mapped_column(Date(), nullable=False)
    site_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    order_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    shift_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    review_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="pending", server_default="pending")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supervisor_user_id: Mapped[str | None] = mapped_column(ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True)
    supervisor_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    closure_state_code: Mapped[str] = mapped_column(String(40), nullable=False, default="open", server_default="open")
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True)
    pdf_document_id: Mapped[str | None] = mapped_column(ForeignKey("docs.document.id", ondelete="SET NULL"), nullable=True)
    customer_visibility_released: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    subcontractor_visibility_released: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    customer_participation_enabled: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    subcontractor_participation_enabled: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    customer_personal_names_released: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("false"))
    subcontractor_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    customer: Mapped[Customer] = relationship(lazy="selectin", overlaps="site,order,planning_record,shift,subcontractor")
    site: Mapped[Site | None] = relationship(lazy="selectin", overlaps="customer,order,planning_record,shift,subcontractor")
    order: Mapped[CustomerOrder | None] = relationship(lazy="selectin", overlaps="customer,site,planning_record,shift,subcontractor")
    planning_record: Mapped[PlanningRecord | None] = relationship(lazy="selectin", overlaps="customer,site,order,shift,subcontractor")
    shift: Mapped[Shift | None] = relationship(lazy="selectin", overlaps="customer,site,order,planning_record,subcontractor")
    supervisor_user: Mapped[UserAccount | None] = relationship(
        UserAccount,
        foreign_keys=[supervisor_user_id],
        lazy="selectin",
    )
    closed_by_user: Mapped[UserAccount | None] = relationship(
        UserAccount,
        foreign_keys=[closed_by_user_id],
        lazy="selectin",
    )
    subcontractor: Mapped[Subcontractor | None] = relationship(lazy="selectin", overlaps="customer,site,order,planning_record,shift")
    entries: Mapped[list["WatchbookEntry"]] = relationship(
        back_populates="watchbook",
        order_by="WatchbookEntry.occurred_at",
        lazy="selectin",
    )


class WatchbookEntry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "watchbook_entry"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "watchbook_id"],
            ["field.watchbook.tenant_id", "field.watchbook.id"],
            name="fk_field_watchbook_entry_tenant_watchbook",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_field_watchbook_entry_tenant_assignment",
            ondelete="SET NULL",
        ),
        CheckConstraint(
            "entry_type_code IN ('remark','incident','handover','status','customer_note','subcontractor_note','employee_note')",
            name="watchbook_entry_type_valid",
        ),
        CheckConstraint(
            "author_actor_type IN ('internal','employee','customer','subcontractor')",
            name="watchbook_entry_author_actor_valid",
        ),
        CheckConstraint(
            "traffic_light_code IS NULL OR traffic_light_code IN ('green','yellow','red')",
            name="watchbook_entry_traffic_light_valid",
        ),
        Index("ix_field_watchbook_entry_watchbook_occurred_at", "watchbook_id", "occurred_at"),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    watchbook_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    assignment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    entry_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    narrative: Mapped[str] = mapped_column(Text(), nullable=False)
    traffic_light_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    author_user_id: Mapped[str] = mapped_column(ForeignKey("iam.user_account.id", ondelete="RESTRICT"), nullable=False)
    author_actor_type: Mapped[str] = mapped_column(String(40), nullable=False, default="internal", server_default="internal")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    created_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    watchbook: Mapped[Watchbook] = relationship(back_populates="entries", lazy="selectin")
    assignment: Mapped[object | None] = relationship("Assignment", lazy="selectin", overlaps="entries,watchbook")
    author_user: Mapped[UserAccount] = relationship(UserAccount, lazy="selectin")


class PatrolRound(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "patrol_round"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_field_patrol_round_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_patrol_round_tenant_shift",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_field_patrol_round_tenant_planning_record",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_field_patrol_round_tenant_route",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "watchbook_id"],
            ["field.watchbook.tenant_id", "field.watchbook.id"],
            name="fk_field_patrol_round_tenant_watchbook",
            ondelete="SET NULL",
        ),
        CheckConstraint(
            "round_status_code IN ('active','completed','aborted')",
            name="patrol_round_status_valid",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_field_patrol_round_tenant_id_id"),
        UniqueConstraint("tenant_id", "offline_sync_token", name="uq_field_patrol_round_sync_token"),
        Index(
            "uq_field_patrol_round_employee_active",
            "tenant_id",
            "employee_id",
            unique=True,
            postgresql_where=text("round_status_code = 'active' AND archived_at IS NULL"),
        ),
        Index("ix_field_patrol_round_route_started_at", "tenant_id", "patrol_route_id", "started_at"),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    employee_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    shift_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    patrol_route_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    watchbook_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    summary_document_id: Mapped[str | None] = mapped_column(ForeignKey("docs.document.id", ondelete="SET NULL"), nullable=True)
    offline_sync_token: Mapped[str | None] = mapped_column(String(120), nullable=True)
    round_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="active", server_default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), server_default=text("CURRENT_TIMESTAMP"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aborted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    abort_reason_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    completion_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    total_checkpoint_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    completed_checkpoint_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    employee: Mapped[Employee] = relationship(lazy="selectin", overlaps="shift,planning_record,patrol_route,watchbook")
    shift: Mapped[Shift] = relationship(lazy="selectin", overlaps="employee,planning_record,patrol_route,watchbook")
    planning_record: Mapped[PlanningRecord | None] = relationship(lazy="selectin", overlaps="employee,shift,patrol_route,watchbook")
    patrol_route: Mapped[PatrolRoute] = relationship(lazy="selectin", overlaps="employee,shift,planning_record,watchbook")
    watchbook: Mapped[Watchbook | None] = relationship(lazy="selectin", overlaps="employee,shift,planning_record,patrol_route")
    events: Mapped[list["PatrolRoundEvent"]] = relationship(
        back_populates="patrol_round",
        lazy="selectin",
        order_by="PatrolRoundEvent.sequence_no",
    )


class PatrolRoundEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "patrol_round_event"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "patrol_round_id"],
            ["field.patrol_round.tenant_id", "field.patrol_round.id"],
            name="fk_field_patrol_round_event_tenant_round",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "checkpoint_id"],
            ["ops.patrol_checkpoint.tenant_id", "ops.patrol_checkpoint.id"],
            name="fk_field_patrol_round_event_tenant_checkpoint",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "patrol_round_id", "sequence_no", name="uq_field_patrol_round_event_round_sequence"),
        UniqueConstraint("tenant_id", "patrol_round_id", "client_event_id", name="uq_field_patrol_round_event_client_event"),
        CheckConstraint(
            "event_type_code IN ('round_started','checkpoint_scanned','checkpoint_exception','round_completed','round_aborted')",
            name="patrol_round_event_type_valid",
        ),
        CheckConstraint(
            "scan_method_code IS NULL OR scan_method_code IN ('system','qr','barcode','nfc','manual')",
            name="patrol_round_event_scan_method_valid",
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="patrol_round_event_coordinates_valid",
        ),
        Index("ix_field_patrol_round_event_round_occurred_at", "tenant_id", "patrol_round_id", "occurred_at"),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    patrol_round_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    checkpoint_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), server_default=text("CURRENT_TIMESTAMP"))
    event_type_code: Mapped[str] = mapped_column(String(60), nullable=False)
    scan_method_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    token_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    client_event_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("iam.user_account.id", ondelete="RESTRICT"), nullable=False)
    is_policy_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), server_default=text("CURRENT_TIMESTAMP"))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    patrol_round: Mapped[PatrolRound] = relationship(back_populates="events", lazy="selectin")
    checkpoint: Mapped[PatrolCheckpoint | None] = relationship(lazy="selectin", overlaps="events,patrol_round")
    actor_user: Mapped[UserAccount] = relationship(UserAccount, lazy="selectin")


class TimeCaptureDevice(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "time_capture_device"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_field_time_capture_device_tenant_site",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "device_code", name="uq_field_time_capture_device_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_field_time_capture_device_tenant_id_id"),
        CheckConstraint(
            "device_type_code IN ('shared_terminal','browser_station','scanner_station','mobile_shared')",
            name="time_capture_device_type_valid",
        ),
        CheckConstraint(
            "status IN ('active','inactive')",
            name="time_capture_device_status_valid",
        ),
        Index("ix_field_time_capture_device_site_status", "tenant_id", "site_id", "status"),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    device_code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type_code: Mapped[str] = mapped_column(String(40), nullable=False, default="shared_terminal", server_default="shared_terminal")
    site_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    access_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fixed_ip_cidr: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    site: Mapped[Site | None] = relationship(lazy="selectin")
    policies: Mapped[list["TimeCapturePolicy"]] = relationship(back_populates="allowed_device", lazy="selectin")


class TimeCapturePolicy(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "time_capture_policy"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_field_time_capture_policy_tenant_site",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_time_capture_policy_tenant_shift",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_field_time_capture_policy_tenant_planning_record",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_field_time_capture_policy_tenant_route",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "allowed_device_id"],
            ["field.time_capture_device.tenant_id", "field.time_capture_device.id"],
            name="fk_field_time_capture_policy_tenant_device",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "policy_code", name="uq_field_time_capture_policy_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_field_time_capture_policy_tenant_id_id"),
        CheckConstraint(
            "context_type_code IN ('site','shift','planning_record','patrol_route')",
            name="time_capture_policy_context_type_valid",
        ),
        CheckConstraint(
            "(CASE WHEN site_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN shift_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN planning_record_id IS NULL THEN 0 ELSE 1 END + "
            "CASE WHEN patrol_route_id IS NULL THEN 0 ELSE 1 END) = 1",
            name="time_capture_policy_context_exactly_one",
        ),
        CheckConstraint(
            "enforce_mode_code IN ('flag','reject')",
            name="time_capture_policy_enforce_mode_valid",
        ),
        CheckConstraint(
            "status IN ('active','inactive')",
            name="time_capture_policy_status_valid",
        ),
        CheckConstraint(
            "(geofence_latitude IS NULL AND geofence_longitude IS NULL AND geofence_radius_meters IS NULL) OR "
            "(geofence_latitude BETWEEN -90 AND 90 AND geofence_longitude BETWEEN -180 AND 180 AND geofence_radius_meters > 0)",
            name="time_capture_policy_geofence_valid",
        ),
        Index(
            "uq_field_time_capture_policy_active_context",
            "tenant_id",
            "context_type_code",
            "site_id",
            "shift_id",
            "planning_record_id",
            "patrol_route_id",
            unique=True,
            postgresql_where=text("archived_at IS NULL AND status = 'active'"),
        ),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    policy_code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    context_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    site_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    shift_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    patrol_route_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    allowed_device_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    allowed_device_type_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    allow_browser_capture: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    allow_mobile_capture: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    allow_terminal_capture: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    allowed_ip_cidr: Mapped[str | None] = mapped_column(String(80), nullable=True)
    geofence_latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    geofence_longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    geofence_radius_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enforce_mode_code: Mapped[str] = mapped_column(String(20), nullable=False, default="reject", server_default="reject")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    site: Mapped[Site | None] = relationship(lazy="selectin", overlaps="shift,planning_record,patrol_route,allowed_device,policies")
    shift: Mapped[Shift | None] = relationship(lazy="selectin", overlaps="site,planning_record,patrol_route,allowed_device,policies")
    planning_record: Mapped[PlanningRecord | None] = relationship(lazy="selectin", overlaps="site,shift,patrol_route,allowed_device,policies")
    patrol_route: Mapped[PatrolRoute | None] = relationship(lazy="selectin", overlaps="site,shift,planning_record,allowed_device,policies")
    allowed_device: Mapped[TimeCaptureDevice | None] = relationship(back_populates="policies", lazy="selectin")


class TimeEvent(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "time_event"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_field_time_event_tenant_employee",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_field_time_event_tenant_worker",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_time_event_tenant_shift",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_field_time_event_tenant_assignment",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_field_time_event_tenant_site",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_field_time_event_tenant_planning_record",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_field_time_event_tenant_route",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "device_id"],
            ["field.time_capture_device.tenant_id", "field.time_capture_device.id"],
            name="fk_field_time_event_tenant_device",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "policy_id"],
            ["field.time_capture_policy.tenant_id", "field.time_capture_policy.id"],
            name="fk_field_time_event_tenant_policy",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_field_time_event_tenant_id_id"),
        UniqueConstraint("tenant_id", "client_event_id", name="uq_field_time_event_tenant_client_event"),
        CheckConstraint(
            "actor_type_code IN ('employee','subcontractor_worker','unresolved')",
            name="time_event_actor_type_valid",
        ),
        CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'employee') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL AND actor_type_code = 'subcontractor_worker') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'unresolved')",
            name="time_event_actor_reference_valid",
        ),
        CheckConstraint(
            "source_channel_code IN ('browser','mobile','terminal')",
            name="time_event_source_channel_valid",
        ),
        CheckConstraint(
            "event_code IN ('clock_in','clock_out','break_start','break_end')",
            name="time_event_event_code_valid",
        ),
        CheckConstraint(
            "validation_status_code IN ('accepted','flagged','rejected')",
            name="time_event_validation_status_valid",
        ),
        CheckConstraint(
            "scan_medium_code IS NULL OR scan_medium_code IN ('manual','qr','barcode','rfid','nfc','app_badge')",
            name="time_event_scan_medium_valid",
        ),
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="time_event_coordinates_valid",
        ),
        Index("ix_field_time_event_tenant_occurred_at", "tenant_id", "occurred_at"),
        Index("ix_field_time_event_tenant_shift_occurred_at", "tenant_id", "shift_id", "occurred_at"),
        Index("ix_field_time_event_tenant_validation_status", "tenant_id", "validation_status_code", "occurred_at"),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    actor_type_code: Mapped[str] = mapped_column(String(40), nullable=False, default="unresolved", server_default="unresolved")
    employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_worker_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    shift_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    assignment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    site_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    patrol_route_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    device_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    policy_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    source_channel_code: Mapped[str] = mapped_column(String(20), nullable=False)
    event_code: Mapped[str] = mapped_column(String(20), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), server_default=text("CURRENT_TIMESTAMP"))
    source_ip: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    scan_medium_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    raw_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_token_suffix: Mapped[str | None] = mapped_column(String(12), nullable=True)
    client_event_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    validation_status_code: Mapped[str] = mapped_column(String(20), nullable=False, default="accepted", server_default="accepted")
    validation_message_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    validation_details_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    employee: Mapped[Employee | None] = relationship(lazy="selectin", overlaps="subcontractor_worker,shift,assignment,site,planning_record,patrol_route,device,policy")
    subcontractor_worker: Mapped[SubcontractorWorker | None] = relationship(
        lazy="selectin",
        overlaps="employee,shift,assignment,site,planning_record,patrol_route,device,policy",
    )
    shift: Mapped[Shift | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,assignment,site,planning_record,patrol_route,device,policy")
    assignment: Mapped[Assignment | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,shift,site,planning_record,patrol_route,device,policy")
    site: Mapped[Site | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,shift,assignment,planning_record,patrol_route,device,policy")
    planning_record: Mapped[PlanningRecord | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,shift,assignment,site,patrol_route,device,policy")
    patrol_route: Mapped[PatrolRoute | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,shift,assignment,site,planning_record,device,policy")
    device: Mapped[TimeCaptureDevice | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,shift,assignment,site,planning_record,patrol_route,policy")
    policy: Mapped[TimeCapturePolicy | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,shift,assignment,site,planning_record,patrol_route,device")


class AttendanceRecord(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "attendance_record"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_field_attendance_record_tenant_employee",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_field_attendance_record_tenant_worker",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_field_attendance_record_tenant_shift",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_field_attendance_record_tenant_assignment",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "first_time_event_id"],
            ["field.time_event.tenant_id", "field.time_event.id"],
            name="fk_field_attendance_record_tenant_first_event",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "last_time_event_id"],
            ["field.time_event.tenant_id", "field.time_event.id"],
            name="fk_field_attendance_record_tenant_last_event",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "superseded_by_attendance_id"],
            ["field.attendance_record.tenant_id", "field.attendance_record.id"],
            name="fk_field_attendance_record_tenant_superseded_by",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_field_attendance_record_tenant_id_id"),
        CheckConstraint(
            "actor_type_code IN ('employee','subcontractor_worker')",
            name="attendance_record_actor_type_valid",
        ),
        CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL AND actor_type_code = 'employee') OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL AND actor_type_code = 'subcontractor_worker')",
            name="attendance_record_actor_reference_valid",
        ),
        CheckConstraint(
            "discrepancy_state_code IN ('clean','warning','needs_review')",
            name="attendance_record_discrepancy_state_valid",
        ),
        CheckConstraint(
            "derivation_status_code IN ('derived','needs_review','superseded')",
            name="attendance_record_derivation_status_valid",
        ),
        CheckConstraint("source_event_count >= 0", name="attendance_record_source_event_count_nonnegative"),
        CheckConstraint("break_minutes >= 0", name="attendance_record_break_minutes_nonnegative"),
        CheckConstraint("worked_minutes >= 0", name="attendance_record_worked_minutes_nonnegative"),
        Index("ix_field_attendance_record_shift_derived", "tenant_id", "shift_id", "derived_at"),
        Index("ix_field_attendance_record_assignment_current", "tenant_id", "assignment_id", "is_current"),
        Index(
            "uq_field_attendance_record_employee_current",
            "tenant_id",
            "shift_id",
            "employee_id",
            unique=True,
            postgresql_where=text("employee_id IS NOT NULL AND is_current = true AND archived_at IS NULL"),
        ),
        Index(
            "uq_field_attendance_record_worker_current",
            "tenant_id",
            "shift_id",
            "subcontractor_worker_id",
            unique=True,
            postgresql_where=text("subcontractor_worker_id IS NOT NULL AND is_current = true AND archived_at IS NULL"),
        ),
        {"schema": "field"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    actor_type_code: Mapped[str] = mapped_column(String(40), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_worker_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    shift_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    assignment_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    worked_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    source_event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    first_time_event_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    last_time_event_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    source_event_ids_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    discrepancy_state_code: Mapped[str] = mapped_column(String(40), nullable=False, default="clean", server_default="clean")
    discrepancy_codes_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    discrepancy_details_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    derivation_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="derived", server_default="derived")
    derived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), server_default=text("CURRENT_TIMESTAMP"))
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by_attendance_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)

    employee: Mapped[Employee | None] = relationship(lazy="selectin", overlaps="subcontractor_worker,shift,assignment")
    subcontractor_worker: Mapped[SubcontractorWorker | None] = relationship(lazy="selectin", overlaps="employee,shift,assignment")
    shift: Mapped[Shift] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,assignment")
    assignment: Mapped[Assignment | None] = relationship(lazy="selectin", overlaps="employee,subcontractor_worker,shift")
    first_time_event: Mapped[TimeEvent | None] = relationship(
        TimeEvent,
        foreign_keys=[first_time_event_id],
        lazy="selectin",
    )
    last_time_event: Mapped[TimeEvent | None] = relationship(
        TimeEvent,
        foreign_keys=[last_time_event_id],
        lazy="selectin",
    )
