"""Recruiting-owned applicant intake and workflow models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import AuditLifecycleMixin, Base, UUIDPrimaryKeyMixin


class Applicant(UUIDPrimaryKeyMixin, AuditLifecycleMixin, Base):
    __tablename__ = "applicant"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "converted_employee_id"],
            ["hr.employee.tenant_id", "hr.employee.id"],
            name="fk_hr_applicant_tenant_converted_employee",
            ondelete="SET NULL",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_hr_applicant_tenant_id_id"),
        UniqueConstraint("tenant_id", "application_no", name="uq_hr_applicant_tenant_application_no"),
        UniqueConstraint("tenant_id", "submission_key", name="uq_hr_applicant_tenant_submission_key"),
        Index("ix_hr_applicant_tenant_status", "tenant_id", "status"),
        Index("ix_hr_applicant_tenant_email", "tenant_id", "email"),
        Index(
            "uq_hr_applicant_tenant_converted_employee_id",
            "tenant_id",
            "converted_employee_id",
            unique=True,
            postgresql_where=text("converted_employee_id IS NOT NULL"),
        ),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    application_no: Mapped[str] = mapped_column(String(40), nullable=False)
    submission_key: Mapped[str] = mapped_column(String(80), nullable=False)
    source_channel: Mapped[str] = mapped_column(String(80), nullable=False, default="public_form", server_default="public_form")
    source_detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="de", server_default="de")
    converted_employee_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    desired_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    availability_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    gdpr_consent_granted: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))
    gdpr_consent_at: Mapped[datetime] = mapped_column(nullable=False)
    gdpr_policy_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    gdpr_policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    custom_fields_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    submitted_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_user_agent: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="submitted", server_default="submitted")


class ApplicantStatusEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "applicant_status_event"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "applicant_id"],
            ["hr.applicant.tenant_id", "hr.applicant.id"],
            name="fk_hr_applicant_status_event_tenant_applicant",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_hr_applicant_status_event_tenant_applicant_created",
            "tenant_id",
            "applicant_id",
            "created_at",
        ),
        Index("ix_hr_applicant_status_event_tenant_to_status", "tenant_id", "to_status"),
        {"schema": "hr"},
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("core.tenant.id", ondelete="RESTRICT"), nullable=False)
    applicant_id: Mapped[str] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    interview_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hiring_target_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("iam.user_account.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
