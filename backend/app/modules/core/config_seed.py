"""Idempotent tenant configuration seeding for numbering rules and print templates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import TenantSetting


NUMBERING_RULES_SETTING_KEY = "numbering.rules"
PRINT_TEMPLATES_SETTING_KEY = "print_templates.catalog"
CUSTOMER_PORTAL_POLICY_SETTING_KEY = "customer_portal.policy"


@dataclass(frozen=True, slots=True)
class TenantSettingSeed:
    key: str
    value_json: dict[str, object]


DEFAULT_NUMBERING_RULES: dict[str, dict[str, object]] = {
    "customer_number": {"prefix": "K-", "next_counter": 1000, "pad_length": 4, "reset_policy": "never"},
    "personnel_no": {"prefix": "P-", "next_counter": 2000, "pad_length": 4, "reset_policy": "never"},
    "subcontractor_number": {"prefix": "SU-", "next_counter": 3000, "pad_length": 4, "reset_policy": "never"},
    "order_no": {"prefix": "A-", "next_counter": 4000, "pad_length": 4, "reset_policy": "yearly"},
    "invoice_no": {"prefix": "RE-", "next_counter": 5000, "pad_length": 5, "reset_policy": "yearly"},
    "timesheet_no": {"prefix": "LS-", "next_counter": 6000, "pad_length": 5, "reset_policy": "yearly"},
}

DEFAULT_PRINT_TEMPLATES: list[dict[str, object]] = [
    {
        "template_key": "watchbook_pdf",
        "name_de": "Wachbuch PDF",
        "name_en": "Watchbook PDF",
        "owner_type": "field.watchbook",
        "output_kind": "pdf",
    },
    {
        "template_key": "patrol_report_pdf",
        "name_de": "Patrouillenbericht PDF",
        "name_en": "Patrol Report PDF",
        "owner_type": "field.patrol_round",
        "output_kind": "pdf",
    },
    {
        "template_key": "timesheet_pdf",
        "name_de": "Leistungsnachweis PDF",
        "name_en": "Timesheet PDF",
        "owner_type": "finance.timesheet",
        "output_kind": "pdf",
    },
    {
        "template_key": "invoice_pdf",
        "name_de": "Rechnung PDF",
        "name_en": "Invoice PDF",
        "owner_type": "finance.customer_invoice",
        "output_kind": "pdf",
    },
    {
        "template_key": "employee_badge_code",
        "name_de": "Mitarbeiterausweis Code",
        "name_en": "Employee Badge Code",
        "owner_type": "hr.employee",
        "output_kind": "badge_output",
        "supports_qr": True,
        "supports_barcode": True,
    },
    {
        "template_key": "order_badge_code",
        "name_de": "Auftragsbadge Code",
        "name_en": "Order Badge Code",
        "owner_type": "ops.customer_order",
        "output_kind": "badge_output",
        "supports_qr": True,
        "supports_barcode": True,
    },
]


DEFAULT_TENANT_SETTINGS: tuple[TenantSettingSeed, ...] = (
    TenantSettingSeed(
        key=NUMBERING_RULES_SETTING_KEY,
        value_json={"version": "v1", "rules": DEFAULT_NUMBERING_RULES},
    ),
    TenantSettingSeed(
        key=PRINT_TEMPLATES_SETTING_KEY,
        value_json={"version": "v1", "templates": DEFAULT_PRINT_TEMPLATES},
    ),
    TenantSettingSeed(
        key=CUSTOMER_PORTAL_POLICY_SETTING_KEY,
        value_json={
            "version": "v1",
            "customer_watchbook_entries_enabled": False,
        },
    ),
)


def preview_number(rule: dict[str, object], counter: int | None = None, *, at_date: date | None = None) -> str:
    next_counter = int(counter if counter is not None else rule.get("next_counter", 1))
    prefix = str(rule.get("prefix", ""))
    pad_length = int(rule.get("pad_length", 0))
    reset_policy = str(rule.get("reset_policy", "never"))
    year_segment = f"{(at_date or date.today()).year}-" if reset_policy == "yearly" else ""
    return f"{prefix}{year_segment}{next_counter:0{pad_length}d}"


def seed_default_tenant_settings(
    session: Session,
    *,
    tenant_id: str,
    actor_user_id: str | None = None,
) -> dict[str, int]:
    inserted = 0
    updated = 0
    for seed in DEFAULT_TENANT_SETTINGS:
        existing = session.scalars(
            select(TenantSetting).where(TenantSetting.tenant_id == tenant_id, TenantSetting.key == seed.key)
        ).one_or_none()
        if existing is None:
            session.add(
                TenantSetting(
                    tenant_id=tenant_id,
                    key=seed.key,
                    value_json=seed.value_json,
                    created_by_user_id=actor_user_id,
                    updated_by_user_id=actor_user_id,
                )
            )
            inserted += 1
            continue
        if existing.value_json != seed.value_json:
            existing.value_json = seed.value_json
            existing.updated_by_user_id = actor_user_id
            existing.version_no = (existing.version_no or 0) + 1
            updated += 1
    return {"inserted": inserted, "updated": updated}
