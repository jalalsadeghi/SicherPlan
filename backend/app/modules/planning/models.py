"""Operational planning master-data and shift-planning models."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin
from app.modules.core.models import Address
from app.modules.customers.models import Customer
from app.modules.employees.models import Employee, FunctionType, QualificationType
from app.modules.iam.models import UserAccount
from app.modules.subcontractors.models import Subcontractor, SubcontractorWorker


def _coordinate_table_args(*constraints: object) -> tuple[object, ...]:
    return (
        *constraints,
        CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR "
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="coordinates_valid",
        ),
    )


class RequirementType(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "requirement_type"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_ops_requirement_type_tenant_customer",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "code", name="uq_ops_requirement_type_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_ops_requirement_type_tenant_id_id"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    default_planning_mode_code: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer | None] = relationship(lazy="selectin")

    @property
    def notes(self) -> str | None:
        return self.description

    @notes.setter
    def notes(self, value: str | None) -> None:
        self.description = value


class EquipmentItem(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "equipment_item"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_ops_equipment_item_tenant_customer",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "code", name="uq_ops_equipment_item_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_ops_equipment_item_tenant_id_id"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_of_measure_code: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer | None] = relationship(lazy="selectin")


class Site(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "site"
    __table_args__ = (
        *_coordinate_table_args(
            ForeignKeyConstraint(
                ["tenant_id", "customer_id"],
                ["crm.customer.tenant_id", "crm.customer.id"],
                name="fk_ops_site_tenant_customer",
                ondelete="RESTRICT",
            ),
            UniqueConstraint("tenant_id", "site_no", name="uq_ops_site_tenant_site_no"),
            UniqueConstraint("tenant_id", "id", name="uq_ops_site_tenant_id_id"),
        ),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    site_no: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_id: Mapped[str | None] = mapped_column(ForeignKey("common.address.id", ondelete="SET NULL"), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    watchbook_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(lazy="selectin")
    address: Mapped[Address | None] = relationship(lazy="selectin")
    patrol_routes: Mapped[list["PatrolRoute"]] = relationship(
        back_populates="site",
        lazy="selectin",
        order_by="PatrolRoute.route_no",
    )


class EventVenue(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "event_venue"
    __table_args__ = (
        *_coordinate_table_args(
            ForeignKeyConstraint(
                ["tenant_id", "customer_id"],
                ["crm.customer.tenant_id", "crm.customer.id"],
                name="fk_ops_event_venue_tenant_customer",
                ondelete="RESTRICT",
            ),
            UniqueConstraint("tenant_id", "venue_no", name="uq_ops_event_venue_tenant_venue_no"),
            UniqueConstraint("tenant_id", "id", name="uq_ops_event_venue_tenant_id_id"),
        ),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    venue_no: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_id: Mapped[str | None] = mapped_column(ForeignKey("common.address.id", ondelete="SET NULL"), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(lazy="selectin")
    address: Mapped[Address | None] = relationship(lazy="selectin")
    trade_fairs: Mapped[list["TradeFair"]] = relationship(
        back_populates="venue",
        lazy="selectin",
        order_by="TradeFair.start_date",
    )


class TradeFair(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "trade_fair"
    __table_args__ = (
        *_coordinate_table_args(
            ForeignKeyConstraint(
                ["tenant_id", "customer_id"],
                ["crm.customer.tenant_id", "crm.customer.id"],
                name="fk_ops_trade_fair_tenant_customer",
                ondelete="RESTRICT",
            ),
            ForeignKeyConstraint(
                ["tenant_id", "venue_id"],
                ["ops.event_venue.tenant_id", "ops.event_venue.id"],
                name="fk_ops_trade_fair_tenant_venue",
                ondelete="SET NULL",
            ),
            UniqueConstraint("tenant_id", "fair_no", name="uq_ops_trade_fair_tenant_fair_no"),
            UniqueConstraint("tenant_id", "id", name="uq_ops_trade_fair_tenant_id_id"),
            CheckConstraint("end_date >= start_date", name="trade_fair_date_window_valid"),
        ),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    venue_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    fair_no: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address_id: Mapped[str | None] = mapped_column(ForeignKey("common.address.id", ondelete="SET NULL"), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(nullable=True)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(lazy="selectin", overlaps="trade_fairs,venue")
    venue: Mapped[EventVenue | None] = relationship(back_populates="trade_fairs", lazy="selectin", overlaps="customer")
    address: Mapped[Address | None] = relationship(lazy="selectin")
    zones: Mapped[list["TradeFairZone"]] = relationship(
        back_populates="trade_fair",
        lazy="selectin",
        order_by="TradeFairZone.zone_code",
    )


class PatrolRoute(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "patrol_route"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_ops_patrol_route_tenant_customer",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_ops_patrol_route_tenant_site",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "route_no", name="uq_ops_patrol_route_tenant_route_no"),
        UniqueConstraint("tenant_id", "id", name="uq_ops_patrol_route_tenant_id_id"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    site_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    meeting_address_id: Mapped[str | None] = mapped_column(
        ForeignKey("common.address.id", ondelete="SET NULL"),
        nullable=True,
    )
    route_no: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_point_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_point_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    travel_policy_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(lazy="selectin", overlaps="patrol_routes,site")
    site: Mapped[Site | None] = relationship(back_populates="patrol_routes", lazy="selectin", overlaps="customer")
    meeting_address: Mapped[Address | None] = relationship(lazy="selectin")
    checkpoints: Mapped[list["PatrolCheckpoint"]] = relationship(
        back_populates="patrol_route",
        lazy="selectin",
        order_by="PatrolCheckpoint.sequence_no",
    )
    customer_orders: Mapped[list["CustomerOrder"]] = relationship(
        back_populates="patrol_route",
        lazy="selectin",
        order_by="CustomerOrder.order_no",
    )


class TradeFairZone(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "trade_fair_zone"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "trade_fair_id"],
            ["ops.trade_fair.tenant_id", "ops.trade_fair.id"],
            name="fk_ops_trade_fair_zone_tenant_fair",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "trade_fair_id",
            "zone_type_code",
            "zone_code",
            name="uq_ops_trade_fair_zone_tuple",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_trade_fair_zone_tenant_id_id"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    trade_fair_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    zone_type_code: Mapped[str] = mapped_column(String(80), nullable=False)
    zone_code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    trade_fair: Mapped[TradeFair] = relationship(back_populates="zones", lazy="selectin")


class PatrolCheckpoint(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "patrol_checkpoint"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_ops_patrol_checkpoint_tenant_route",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "patrol_route_id",
            "sequence_no",
            name="uq_ops_patrol_checkpoint_route_sequence",
        ),
        UniqueConstraint(
            "tenant_id",
            "patrol_route_id",
            "checkpoint_code",
            name="uq_ops_patrol_checkpoint_route_code",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_patrol_checkpoint_tenant_id_id"),
        CheckConstraint(
            "(latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)",
            name="patrol_checkpoint_coordinates_valid",
        ),
        CheckConstraint("minimum_dwell_seconds >= 0", name="patrol_checkpoint_dwell_non_negative"),
        Index("ix_ops_patrol_checkpoint_route_sequence", "tenant_id", "patrol_route_id", "sequence_no"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    patrol_route_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    sequence_no: Mapped[int] = mapped_column(nullable=False)
    checkpoint_code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(nullable=False)
    longitude: Mapped[Decimal] = mapped_column(nullable=False)
    scan_type_code: Mapped[str] = mapped_column(String(80), nullable=False)
    expected_token_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    minimum_dwell_seconds: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    patrol_route: Mapped[PatrolRoute] = relationship(back_populates="checkpoints", lazy="selectin")


class CustomerOrder(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "customer_order"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "customer_id"],
            ["crm.customer.tenant_id", "crm.customer.id"],
            name="fk_ops_customer_order_tenant_customer",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "requirement_type_id"],
            ["ops.requirement_type.tenant_id", "ops.requirement_type.id"],
            name="fk_ops_customer_order_tenant_requirement_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_ops_customer_order_tenant_patrol_route",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "order_no", name="uq_ops_customer_order_tenant_order_no"),
        UniqueConstraint("tenant_id", "id", name="uq_ops_customer_order_tenant_id_id"),
        CheckConstraint("service_to >= service_from", name="customer_order_service_window_valid"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    customer_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    requirement_type_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    patrol_route_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    order_no: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    service_category_code: Mapped[str] = mapped_column(String(80), nullable=False)
    security_concept_text: Mapped[str | None] = mapped_column(Text(), nullable=True)
    service_from: Mapped[date] = mapped_column(nullable=False)
    service_to: Mapped[date] = mapped_column(nullable=False)
    release_state: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    customer: Mapped[Customer] = relationship(lazy="selectin", overlaps="customer_orders")
    requirement_type: Mapped[RequirementType] = relationship(lazy="selectin", overlaps="customer,customer_orders")
    patrol_route: Mapped[PatrolRoute | None] = relationship(back_populates="customer_orders", lazy="selectin", overlaps="customer,requirement_type")
    equipment_lines: Mapped[list["OrderEquipmentLine"]] = relationship(
        back_populates="order",
        lazy="selectin",
        order_by="OrderEquipmentLine.created_at",
    )
    requirement_lines: Mapped[list["OrderRequirementLine"]] = relationship(
        back_populates="order",
        lazy="selectin",
        order_by="OrderRequirementLine.created_at",
    )
    planning_records: Mapped[list["PlanningRecord"]] = relationship(
        back_populates="order",
        lazy="selectin",
        order_by="PlanningRecord.planning_from",
    )


class OrderEquipmentLine(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "order_equipment"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["ops.customer_order.tenant_id", "ops.customer_order.id"],
            name="fk_ops_order_equipment_tenant_order",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "equipment_item_id"],
            ["ops.equipment_item.tenant_id", "ops.equipment_item.id"],
            name="fk_ops_order_equipment_tenant_item",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "order_id", "equipment_item_id", name="uq_ops_order_equipment_order_item"),
        CheckConstraint("required_qty >= 1", name="order_equipment_required_qty_positive"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    equipment_item_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    required_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    order: Mapped[CustomerOrder] = relationship(back_populates="equipment_lines", lazy="selectin")
    equipment_item: Mapped[EquipmentItem] = relationship(lazy="selectin", overlaps="equipment_lines,order")


class OrderRequirementLine(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "order_requirement_line"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["ops.customer_order.tenant_id", "ops.customer_order.id"],
            name="fk_ops_order_requirement_line_tenant_order",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "requirement_type_id"],
            ["ops.requirement_type.tenant_id", "ops.requirement_type.id"],
            name="fk_ops_order_requirement_line_tenant_requirement_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_ops_order_requirement_line_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_ops_order_requirement_line_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        CheckConstraint("min_qty >= 0", name="order_requirement_line_min_qty_nonnegative"),
        CheckConstraint("target_qty >= min_qty", name="order_requirement_line_target_ge_min"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    requirement_type_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    function_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    min_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    target_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    order: Mapped[CustomerOrder] = relationship(back_populates="requirement_lines", lazy="selectin")
    requirement_type: Mapped[RequirementType] = relationship(lazy="selectin", overlaps="order,requirement_lines")
    function_type: Mapped[FunctionType | None] = relationship(lazy="selectin", overlaps="order,requirement_lines,requirement_type")
    qualification_type: Mapped[QualificationType | None] = relationship(lazy="selectin", overlaps="function_type,order,requirement_lines,requirement_type")


class PlanningRecord(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "planning_record"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "order_id"],
            ["ops.customer_order.tenant_id", "ops.customer_order.id"],
            name="fk_ops_planning_record_tenant_order",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "parent_planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_planning_record_tenant_parent",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_planning_record_tenant_id_id"),
        UniqueConstraint("tenant_id", "order_id", "name", name="uq_ops_planning_record_order_name"),
        CheckConstraint("planning_to >= planning_from", name="planning_record_window_valid"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    order_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    parent_planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    dispatcher_user_id: Mapped[str | None] = mapped_column(ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True)
    planning_mode_code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    planning_from: Mapped[date] = mapped_column(nullable=False)
    planning_to: Mapped[date] = mapped_column(nullable=False)
    release_state: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    order: Mapped[CustomerOrder] = relationship(back_populates="planning_records", lazy="selectin")
    parent_planning_record: Mapped["PlanningRecord | None"] = relationship(
        remote_side="PlanningRecord.id",
        lazy="selectin",
        overlaps="child_planning_records,order,planning_records",
    )
    child_planning_records: Mapped[list["PlanningRecord"]] = relationship(
        lazy="selectin",
        order_by="PlanningRecord.planning_from",
        overlaps="parent_planning_record,order,planning_records",
    )
    dispatcher_user: Mapped[UserAccount | None] = relationship(lazy="selectin")
    event_detail: Mapped["EventPlanDetail | None"] = relationship(back_populates="planning_record", lazy="selectin", uselist=False)
    site_detail: Mapped["SitePlanDetail | None"] = relationship(back_populates="planning_record", lazy="selectin", uselist=False)
    trade_fair_detail: Mapped["TradeFairPlanDetail | None"] = relationship(back_populates="planning_record", lazy="selectin", uselist=False)
    patrol_detail: Mapped["PatrolPlanDetail | None"] = relationship(back_populates="planning_record", lazy="selectin", uselist=False)


class EventPlanDetail(Base):
    __tablename__ = "event_plan_detail"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_event_plan_detail_tenant_record",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "event_venue_id"],
            ["ops.event_venue.tenant_id", "ops.event_venue.id"],
            name="fk_ops_event_plan_detail_tenant_venue",
            ondelete="RESTRICT",
        ),
        {"schema": "ops"},
    )

    planning_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    event_venue_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    setup_note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    planning_record: Mapped[PlanningRecord] = relationship(back_populates="event_detail", lazy="selectin")
    event_venue: Mapped[EventVenue] = relationship(lazy="selectin", overlaps="event_detail,planning_record")


class SitePlanDetail(Base):
    __tablename__ = "site_plan_detail"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_site_plan_detail_tenant_record",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "site_id"],
            ["ops.site.tenant_id", "ops.site.id"],
            name="fk_ops_site_plan_detail_tenant_site",
            ondelete="RESTRICT",
        ),
        {"schema": "ops"},
    )

    planning_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    site_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    watchbook_scope_note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    planning_record: Mapped[PlanningRecord] = relationship(back_populates="site_detail", lazy="selectin")
    site: Mapped[Site] = relationship(lazy="selectin", overlaps="planning_record,site_detail")


class TradeFairPlanDetail(Base):
    __tablename__ = "trade_fair_plan_detail"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_trade_fair_plan_detail_tenant_record",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "trade_fair_id"],
            ["ops.trade_fair.tenant_id", "ops.trade_fair.id"],
            name="fk_ops_trade_fair_plan_detail_tenant_fair",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "trade_fair_zone_id"],
            ["ops.trade_fair_zone.tenant_id", "ops.trade_fair_zone.id"],
            name="fk_ops_trade_fair_plan_detail_tenant_zone",
            ondelete="SET NULL",
        ),
        {"schema": "ops"},
    )

    planning_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    trade_fair_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    trade_fair_zone_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    stand_note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    planning_record: Mapped[PlanningRecord] = relationship(back_populates="trade_fair_detail", lazy="selectin")
    trade_fair: Mapped[TradeFair] = relationship(lazy="selectin", overlaps="planning_record,trade_fair_detail")
    trade_fair_zone: Mapped[TradeFairZone | None] = relationship(
        lazy="selectin",
        overlaps="planning_record,trade_fair,trade_fair_detail",
    )


class PatrolPlanDetail(Base):
    __tablename__ = "patrol_plan_detail"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_patrol_plan_detail_tenant_record",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "patrol_route_id"],
            ["ops.patrol_route.tenant_id", "ops.patrol_route.id"],
            name="fk_ops_patrol_plan_detail_tenant_route",
            ondelete="RESTRICT",
        ),
        {"schema": "ops"},
    )

    planning_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    patrol_route_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    execution_note: Mapped[str | None] = mapped_column(Text(), nullable=True)

    planning_record: Mapped[PlanningRecord] = relationship(back_populates="patrol_detail", lazy="selectin")
    patrol_route: Mapped[PatrolRoute] = relationship(lazy="selectin", overlaps="patrol_detail,planning_record")


class ShiftPlan(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "shift_plan"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_shift_plan_tenant_record",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_shift_plan_tenant_id_id"),
        UniqueConstraint("tenant_id", "planning_record_id", "name", name="uq_ops_shift_plan_record_name"),
        CheckConstraint("planning_to >= planning_from", name="shift_plan_window_valid"),
        CheckConstraint(
            "workforce_scope_code IN ('internal', 'subcontractor', 'mixed')",
            name="shift_plan_workforce_scope_valid",
        ),
        Index("ix_ops_shift_plan_tenant_record_window", "tenant_id", "planning_record_id", "planning_from", "planning_to"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    planning_record_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    workforce_scope_code: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="internal",
        server_default="internal",
    )
    planning_from: Mapped[date] = mapped_column(nullable=False)
    planning_to: Mapped[date] = mapped_column(nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text(), nullable=True)

    planning_record: Mapped[PlanningRecord] = relationship(lazy="selectin")
    series_rows: Mapped[list["ShiftSeries"]] = relationship(
        back_populates="shift_plan",
        lazy="selectin",
        order_by="ShiftSeries.date_from",
    )
    shifts: Mapped[list["Shift"]] = relationship(
        back_populates="shift_plan",
        lazy="selectin",
        order_by="Shift.starts_at",
        overlaps="shift_series",
    )


class ShiftTemplate(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "shift_template"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ops_shift_template_tenant_code"),
        UniqueConstraint("tenant_id", "id", name="uq_ops_shift_template_tenant_id_id"),
        CheckConstraint("default_break_minutes >= 0", name="shift_template_break_nonnegative"),
        Index("ix_ops_shift_template_tenant_status", "tenant_id", "status"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    local_start_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    local_end_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    default_break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    shift_type_code: Mapped[str] = mapped_column(String(80), nullable=False)
    meeting_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    series_rows: Mapped[list["ShiftSeries"]] = relationship(
        back_populates="shift_template",
        lazy="selectin",
        order_by="ShiftSeries.date_from",
        overlaps="shift_plan,series_rows",
    )


class ShiftSeries(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "shift_series"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "shift_plan_id"],
            ["ops.shift_plan.tenant_id", "ops.shift_plan.id"],
            name="fk_ops_shift_series_tenant_plan",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_template_id"],
            ["ops.shift_template.tenant_id", "ops.shift_template.id"],
            name="fk_ops_shift_series_tenant_template",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_shift_series_tenant_id_id"),
        CheckConstraint("date_to >= date_from", name="shift_series_window_valid"),
        CheckConstraint("interval_count >= 1", name="shift_series_interval_positive"),
        CheckConstraint("recurrence_code IN ('daily', 'weekly')", name="shift_series_recurrence_code_valid"),
        CheckConstraint("default_break_minutes IS NULL OR default_break_minutes >= 0", name="shift_series_break_nonnegative"),
        Index("ix_ops_shift_series_tenant_plan_window", "tenant_id", "shift_plan_id", "date_from", "date_to"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    shift_plan_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    shift_template_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    recurrence_code: Mapped[str] = mapped_column(String(40), nullable=False, default="daily", server_default="daily")
    interval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    weekday_mask: Mapped[str | None] = mapped_column(String(7), nullable=True)
    timezone: Mapped[str] = mapped_column(String(80), nullable=False)
    date_from: Mapped[date] = mapped_column(nullable=False)
    date_to: Mapped[date] = mapped_column(nullable=False)
    default_break_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shift_type_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    meeting_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_visible_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    subcontractor_visible_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    stealth_mode_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    release_state: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    shift_plan: Mapped[ShiftPlan] = relationship(back_populates="series_rows", lazy="selectin", overlaps="series_rows")
    shift_template: Mapped[ShiftTemplate] = relationship(
        back_populates="series_rows",
        lazy="selectin",
        overlaps="shift_plan,series_rows",
    )
    exceptions: Mapped[list["ShiftSeriesException"]] = relationship(
        back_populates="shift_series",
        lazy="selectin",
        order_by="ShiftSeriesException.exception_date",
        overlaps="shifts",
    )
    shifts: Mapped[list["Shift"]] = relationship(
        back_populates="shift_series",
        lazy="selectin",
        order_by="Shift.starts_at",
        overlaps="exceptions,shift_plan,shifts",
    )


class ShiftSeriesException(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "shift_series_exception"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "shift_series_id"],
            ["ops.shift_series.tenant_id", "ops.shift_series.id"],
            name="fk_ops_shift_series_exception_tenant_series",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "shift_series_id", "exception_date", name="uq_ops_shift_series_exception_date"),
        CheckConstraint("action_code IN ('skip', 'override')", name="shift_series_exception_action_valid"),
        CheckConstraint(
            "(override_local_start_time IS NULL AND override_local_end_time IS NULL) OR "
            "(override_local_start_time IS NOT NULL AND override_local_end_time IS NOT NULL)",
            name="shift_series_exception_override_time_pair",
        ),
        CheckConstraint(
            "override_break_minutes IS NULL OR override_break_minutes >= 0",
            name="shift_series_exception_break_nonnegative",
        ),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    shift_series_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    exception_date: Mapped[date] = mapped_column(nullable=False)
    action_code: Mapped[str] = mapped_column(String(40), nullable=False)
    override_local_start_time: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    override_local_end_time: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    override_break_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    override_shift_type_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    override_meeting_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    override_location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_visible_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    subcontractor_visible_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    stealth_mode_flag: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    shift_series: Mapped[ShiftSeries] = relationship(back_populates="exceptions", lazy="selectin", overlaps="shifts")


class Shift(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "shift"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "shift_plan_id"],
            ["ops.shift_plan.tenant_id", "ops.shift_plan.id"],
            name="fk_ops_shift_tenant_plan",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_series_id"],
            ["ops.shift_series.tenant_id", "ops.shift_series.id"],
            name="fk_ops_shift_tenant_series",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_shift_tenant_id_id"),
        UniqueConstraint("tenant_id", "shift_series_id", "occurrence_date", name="uq_ops_shift_series_occurrence"),
        CheckConstraint("ends_at > starts_at", name="shift_window_valid"),
        CheckConstraint("break_minutes >= 0", name="shift_break_nonnegative"),
        Index("ix_ops_shift_tenant_plan_starts_at", "tenant_id", "shift_plan_id", "starts_at"),
        Index("ix_ops_shift_tenant_starts_at", "tenant_id", "starts_at"),
        Index("ix_ops_shift_tenant_status_starts_at", "tenant_id", "status", "starts_at"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    shift_plan_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    shift_series_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    occurrence_date: Mapped[date | None] = mapped_column(nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    shift_type_code: Mapped[str] = mapped_column(String(80), nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_point: Mapped[str | None] = mapped_column(String(255), nullable=True)
    release_state: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    customer_visible_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    subcontractor_visible_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    stealth_mode_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    source_kind_code: Mapped[str] = mapped_column(String(40), nullable=False, default="generated", server_default="generated")
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    shift_plan: Mapped[ShiftPlan] = relationship(back_populates="shifts", lazy="selectin", overlaps="series_rows")
    shift_series: Mapped[ShiftSeries | None] = relationship(
        back_populates="shifts",
        lazy="selectin",
        overlaps="shift_plan,exceptions",
    )
    demand_groups: Mapped[list["DemandGroup"]] = relationship(
        back_populates="shift",
        lazy="selectin",
        order_by="DemandGroup.sort_order",
        overlaps="assignments,teams",
    )
    teams: Mapped[list["Team"]] = relationship(
        back_populates="shift",
        lazy="selectin",
        order_by="Team.name",
        overlaps="planning_record,demand_groups",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="shift",
        lazy="selectin",
        order_by="Assignment.created_at",
        overlaps="demand_group,team",
    )


class DemandGroup(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "demand_group"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_ops_demand_group_tenant_shift",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "function_type_id"],
            ["hr.function_type.tenant_id", "hr.function_type.id"],
            name="fk_ops_demand_group_tenant_function_type",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "qualification_type_id"],
            ["hr.qualification_type.tenant_id", "hr.qualification_type.id"],
            name="fk_ops_demand_group_tenant_qualification_type",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_demand_group_tenant_id_id"),
        UniqueConstraint("tenant_id", "shift_id", "sort_order", name="uq_ops_demand_group_shift_sort_order"),
        CheckConstraint("min_qty >= 0", name="demand_group_min_qty_nonnegative"),
        CheckConstraint("target_qty >= min_qty", name="demand_group_target_qty_ge_min"),
        Index("ix_ops_demand_group_tenant_shift", "tenant_id", "shift_id", "sort_order"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    shift_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    function_type_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    qualification_type_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    min_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    target_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    mandatory_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    remark: Mapped[str | None] = mapped_column(Text(), nullable=True)

    shift: Mapped[Shift] = relationship(back_populates="demand_groups", lazy="selectin", overlaps="teams,assignments")
    function_type: Mapped[FunctionType] = relationship(lazy="selectin", overlaps="shift,demand_groups")
    qualification_type: Mapped[QualificationType | None] = relationship(
        lazy="selectin",
        overlaps="shift,demand_groups,function_type",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="demand_group",
        lazy="selectin",
        order_by="Assignment.created_at",
        overlaps="shift,team,assignments",
    )
    subcontractor_releases: Mapped[list["SubcontractorRelease"]] = relationship(
        back_populates="demand_group",
        lazy="selectin",
        order_by="SubcontractorRelease.created_at",
        overlaps="shift",
    )


class Team(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "team"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "planning_record_id"],
            ["ops.planning_record.tenant_id", "ops.planning_record.id"],
            name="fk_ops_team_tenant_record",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_ops_team_tenant_shift",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_team_tenant_id_id"),
        CheckConstraint(
            "planning_record_id IS NOT NULL OR shift_id IS NOT NULL",
            name="team_requires_record_or_shift",
        ),
        Index("ix_ops_team_tenant_record", "tenant_id", "planning_record_id"),
        Index("ix_ops_team_tenant_shift", "tenant_id", "shift_id"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    planning_record_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    shift_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    planning_record: Mapped[PlanningRecord | None] = relationship(lazy="selectin", overlaps="shift,teams")
    shift: Mapped[Shift | None] = relationship(back_populates="teams", lazy="selectin", overlaps="planning_record,demand_groups")
    members: Mapped[list["TeamMember"]] = relationship(
        back_populates="team",
        lazy="selectin",
        order_by="TeamMember.valid_from",
        overlaps="assignments",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="team",
        lazy="selectin",
        order_by="Assignment.created_at",
        overlaps="shift,demand_group,assignments",
    )


class TeamMember(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "team_member"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "team_id"],
            ["ops.team.tenant_id", "ops.team.id"],
            name="fk_ops_team_member_tenant_team",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_ops_team_member_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_ops_team_member_tenant_subcontractor_worker",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_team_member_tenant_id_id"),
        CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL) OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL)",
            name="team_member_exactly_one_actor",
        ),
        CheckConstraint("valid_to IS NULL OR valid_to >= valid_from", name="team_member_window_valid"),
        Index("ix_ops_team_member_tenant_team", "tenant_id", "team_id", "valid_from"),
        Index(
            "uq_ops_team_member_single_lead",
            "tenant_id",
            "team_id",
            unique=True,
            postgresql_where=text("is_team_lead = true AND archived_at IS NULL"),
        ),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    team_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_worker_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    role_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_team_lead: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    team: Mapped[Team] = relationship(back_populates="members", lazy="selectin", overlaps="assignments")
    employee: Mapped[Employee | None] = relationship(lazy="selectin", overlaps="team,members")
    subcontractor_worker: Mapped[SubcontractorWorker | None] = relationship(
        lazy="selectin",
        overlaps="employee,team,members",
    )


class Assignment(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "assignment"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_ops_assignment_tenant_shift",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "demand_group_id"],
            ["ops.demand_group.tenant_id", "ops.demand_group.id"],
            name="fk_ops_assignment_tenant_demand_group",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "team_id"],
            ["ops.team.tenant_id", "ops.team.id"],
            name="fk_ops_assignment_tenant_team",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_ops_assignment_tenant_employee",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_worker_id"],
            ["partner.subcontractor_worker.tenant_id", "partner.subcontractor_worker.id"],
            name="fk_ops_assignment_tenant_subcontractor_worker",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_assignment_tenant_id_id"),
        CheckConstraint(
            "(employee_id IS NOT NULL AND subcontractor_worker_id IS NULL) OR "
            "(employee_id IS NULL AND subcontractor_worker_id IS NOT NULL)",
            name="assignment_exactly_one_actor",
        ),
        CheckConstraint(
            "assignment_status_code IN ('offered', 'assigned', 'confirmed', 'removed')",
            name="assignment_status_code_valid",
        ),
        CheckConstraint(
            "assignment_source_code IN ('dispatcher', 'subcontractor_release', 'portal_allocation', 'manual')",
            name="assignment_source_code_valid",
        ),
        Index("ix_ops_assignment_tenant_shift", "tenant_id", "shift_id", "created_at"),
        Index(
            "uq_ops_assignment_employee_active_per_shift",
            "tenant_id",
            "shift_id",
            "employee_id",
            unique=True,
            postgresql_where=text("employee_id IS NOT NULL AND assignment_status_code != 'removed' AND archived_at IS NULL"),
        ),
        Index(
            "uq_ops_assignment_worker_active_per_shift",
            "tenant_id",
            "shift_id",
            "subcontractor_worker_id",
            unique=True,
            postgresql_where=text("subcontractor_worker_id IS NOT NULL AND assignment_status_code != 'removed' AND archived_at IS NULL"),
        ),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    shift_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    demand_group_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    team_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_worker_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    assignment_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="assigned", server_default="assigned")
    assignment_source_code: Mapped[str] = mapped_column(String(40), nullable=False, default="dispatcher", server_default="dispatcher")
    offered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text(), nullable=True)

    shift: Mapped[Shift] = relationship(back_populates="assignments", lazy="selectin", overlaps="demand_groups,team")
    demand_group: Mapped[DemandGroup] = relationship(back_populates="assignments", lazy="selectin", overlaps="shift,team")
    team: Mapped[Team | None] = relationship(back_populates="assignments", lazy="selectin", overlaps="shift,demand_group")
    employee: Mapped[Employee | None] = relationship(
        lazy="selectin",
        overlaps="shift,team,demand_group,assignments",
    )
    subcontractor_worker: Mapped[SubcontractorWorker | None] = relationship(
        lazy="selectin",
        overlaps="employee,shift,team,demand_group,assignments",
    )
    validation_overrides: Mapped[list["AssignmentValidationOverride"]] = relationship(
        back_populates="assignment",
        lazy="selectin",
        order_by="AssignmentValidationOverride.created_at",
    )


class AssignmentValidationOverride(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "assignment_validation_override"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "assignment_id"],
            ["ops.assignment.tenant_id", "ops.assignment.id"],
            name="fk_ops_assignment_validation_override_tenant_assignment",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["created_by_user_id"],
            ["iam.user_account.id"],
            name="fk_ops_assignment_validation_override_actor_user",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_assignment_validation_override_tenant_id_id"),
        Index("ix_ops_assignment_validation_override_assignment_created", "tenant_id", "assignment_id", "created_at"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    assignment_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(120), nullable=False)
    reason_text: Mapped[str] = mapped_column(Text(), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    assignment: Mapped[Assignment] = relationship(back_populates="validation_overrides", lazy="selectin")
    created_by_user: Mapped[UserAccount | None] = relationship(foreign_keys=[created_by_user_id], lazy="selectin")


class SubcontractorRelease(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "subcontractor_release"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["ops.shift.tenant_id", "ops.shift.id"],
            name="fk_ops_subcontractor_release_tenant_shift",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "demand_group_id"],
            ["ops.demand_group.tenant_id", "ops.demand_group.id"],
            name="fk_ops_subcontractor_release_tenant_demand_group",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subcontractor_id"],
            ["partner.subcontractor.tenant_id", "partner.subcontractor.id"],
            name="fk_ops_subcontractor_release_tenant_subcontractor",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_ops_subcontractor_release_tenant_id_id"),
        CheckConstraint("released_qty >= 1", name="subcontractor_release_qty_positive"),
        CheckConstraint(
            "release_status_code IN ('draft', 'released', 'revoked')",
            name="subcontractor_release_status_code_valid",
        ),
        Index(
            "uq_ops_subcontractor_release_active_tuple",
            "tenant_id",
            "shift_id",
            "demand_group_id",
            "subcontractor_id",
            unique=True,
            postgresql_where=text("release_status_code != 'revoked' AND archived_at IS NULL"),
        ),
        Index("ix_ops_subcontractor_release_tenant_shift", "tenant_id", "shift_id", "created_at"),
        {"schema": "ops"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    shift_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    demand_group_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    subcontractor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    released_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    release_status_code: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", server_default="draft")
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text(), nullable=True)

    shift: Mapped[Shift] = relationship(lazy="selectin", overlaps="demand_groups,subcontractor_releases")
    demand_group: Mapped[DemandGroup | None] = relationship(
        back_populates="subcontractor_releases",
        lazy="selectin",
        overlaps="shift",
    )
    subcontractor: Mapped[Subcontractor] = relationship(
        lazy="selectin",
        overlaps="shift,demand_group,subcontractor_releases",
    )
