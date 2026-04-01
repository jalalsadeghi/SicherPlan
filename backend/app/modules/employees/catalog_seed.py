"""Tenant HR catalog seed helpers for baseline and dev/test sample bootstrap."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.employees.models import FunctionType, QualificationType


@dataclass(frozen=True, slots=True)
class FunctionTypeSeed:
    code: str
    label: str
    category: str | None = None
    description: str | None = None
    planning_relevant: bool = True


@dataclass(frozen=True, slots=True)
class QualificationTypeSeed:
    code: str
    label: str
    category: str | None = None
    description: str | None = None
    planning_relevant: bool = True
    compliance_relevant: bool = False
    expiry_required: bool = False
    default_validity_days: int | None = None
    proof_required: bool = False


BASELINE_FUNCTION_TYPES: tuple[FunctionTypeSeed, ...] = (
    FunctionTypeSeed(
        code="SEC_GUARD",
        label="Security agent",
        category="operations",
        description="Default security officer function for guarded service pricing.",
    ),
    FunctionTypeSeed(
        code="SHIFT_SUP",
        label="Shift supervisor",
        category="operations",
        description="Shift-level operational lead used for supervisory coverage pricing.",
    ),
    FunctionTypeSeed(
        code="DISPATCH",
        label="Dispatch support",
        category="operations",
        description="Control-room or dispatch support function relevant for planning and pricing.",
    ),
    FunctionTypeSeed(
        code="FIRE_WATCH",
        label="Fire watch",
        category="safety",
        description="Fire-watch function for events, worksites, and temporary safety coverage.",
    ),
)


BASELINE_QUALIFICATION_TYPES: tuple[QualificationTypeSeed, ...] = (
    QualificationTypeSeed(
        code="G34A",
        label="34a certified",
        category="compliance",
        description="Sachkunde or Unterrichtung qualification under §34a GewO.",
        compliance_relevant=True,
        proof_required=True,
    ),
    QualificationTypeSeed(
        code="FIRST_AID",
        label="First aid",
        category="safety",
        description="Basic first-aid certification for field personnel.",
        compliance_relevant=True,
        expiry_required=True,
        default_validity_days=730,
        proof_required=True,
    ),
    QualificationTypeSeed(
        code="FIRE_SAFETY",
        label="Fire safety",
        category="safety",
        description="Fire-safety or evacuation-support qualification.",
        compliance_relevant=True,
        proof_required=True,
    ),
    QualificationTypeSeed(
        code="CROWD_CONTROL",
        label="Crowd control",
        category="operations",
        description="Operational crowd-management qualification for event and queue handling.",
        proof_required=False,
    ),
)


SAMPLE_FUNCTION_TYPES = BASELINE_FUNCTION_TYPES
SAMPLE_QUALIFICATION_TYPES = BASELINE_QUALIFICATION_TYPES


def seed_baseline_employee_catalogs(
    session: Session,
    *,
    tenant_id: str,
    actor_user_id: str | None = None,
) -> dict[str, int]:
    function_result = _seed_function_types(
        session,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        refresh_metadata=False,
    )
    qualification_result = _seed_qualification_types(
        session,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        refresh_metadata=False,
    )
    return {
        "function_types_inserted": function_result["inserted"],
        "function_types_updated": function_result["updated"],
        "qualification_types_inserted": qualification_result["inserted"],
        "qualification_types_updated": qualification_result["updated"],
    }


def seed_sample_employee_catalogs(
    session: Session,
    *,
    tenant_id: str,
    actor_user_id: str | None = None,
) -> dict[str, int]:
    function_result = _seed_function_types(
        session,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        refresh_metadata=True,
    )
    qualification_result = _seed_qualification_types(
        session,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        refresh_metadata=True,
    )
    return {
        "function_types_inserted": function_result["inserted"],
        "function_types_updated": function_result["updated"],
        "qualification_types_inserted": qualification_result["inserted"],
        "qualification_types_updated": qualification_result["updated"],
    }


def _seed_function_types(
    session: Session,
    *,
    tenant_id: str,
    actor_user_id: str | None,
    refresh_metadata: bool,
) -> dict[str, int]:
    inserted = 0
    updated = 0
    for seed in BASELINE_FUNCTION_TYPES:
        existing = session.scalars(
            select(FunctionType).where(
                FunctionType.tenant_id == tenant_id,
                FunctionType.code == seed.code,
            )
        ).one_or_none()
        if existing is None:
            session.add(
                FunctionType(
                    tenant_id=tenant_id,
                    code=seed.code,
                    label=seed.label,
                    category=seed.category,
                    description=seed.description,
                    is_active=True,
                    planning_relevant=seed.planning_relevant,
                    status="active",
                    archived_at=None,
                    created_by_user_id=actor_user_id,
                    updated_by_user_id=actor_user_id,
                )
            )
            inserted += 1
            continue
        changed = False
        changed |= _assign(existing, "is_active", True)
        changed |= _assign(existing, "status", "active")
        changed |= _assign(existing, "archived_at", None)
        if refresh_metadata:
            changed |= _assign(existing, "label", seed.label)
            changed |= _assign(existing, "category", seed.category)
            changed |= _assign(existing, "description", seed.description)
            changed |= _assign(existing, "planning_relevant", seed.planning_relevant)
        if changed:
            existing.updated_by_user_id = actor_user_id
            existing.version_no = (existing.version_no or 0) + 1
            updated += 1
    return {"inserted": inserted, "updated": updated}


def _seed_qualification_types(
    session: Session,
    *,
    tenant_id: str,
    actor_user_id: str | None,
    refresh_metadata: bool,
) -> dict[str, int]:
    inserted = 0
    updated = 0
    for seed in BASELINE_QUALIFICATION_TYPES:
        existing = session.scalars(
            select(QualificationType).where(
                QualificationType.tenant_id == tenant_id,
                QualificationType.code == seed.code,
            )
        ).one_or_none()
        if existing is None:
            session.add(
                QualificationType(
                    tenant_id=tenant_id,
                    code=seed.code,
                    label=seed.label,
                    category=seed.category,
                    description=seed.description,
                    is_active=True,
                    planning_relevant=seed.planning_relevant,
                    compliance_relevant=seed.compliance_relevant,
                    expiry_required=seed.expiry_required,
                    default_validity_days=seed.default_validity_days,
                    proof_required=seed.proof_required,
                    status="active",
                    archived_at=None,
                    created_by_user_id=actor_user_id,
                    updated_by_user_id=actor_user_id,
                )
            )
            inserted += 1
            continue
        changed = False
        changed |= _assign(existing, "is_active", True)
        changed |= _assign(existing, "status", "active")
        changed |= _assign(existing, "archived_at", None)
        if refresh_metadata:
            changed |= _assign(existing, "label", seed.label)
            changed |= _assign(existing, "category", seed.category)
            changed |= _assign(existing, "description", seed.description)
            changed |= _assign(existing, "planning_relevant", seed.planning_relevant)
            changed |= _assign(existing, "compliance_relevant", seed.compliance_relevant)
            changed |= _assign(existing, "expiry_required", seed.expiry_required)
            changed |= _assign(existing, "default_validity_days", seed.default_validity_days)
            changed |= _assign(existing, "proof_required", seed.proof_required)
        if changed:
            existing.updated_by_user_id = actor_user_id
            existing.version_no = (existing.version_no or 0) + 1
            updated += 1
    return {"inserted": inserted, "updated": updated}


def _assign(row: object, field: str, value: object) -> bool:
    if getattr(row, field) == value:
        return False
    setattr(row, field, value)
    return True
