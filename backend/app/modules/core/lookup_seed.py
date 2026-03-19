"""Lookup domain catalog and idempotent seeding helpers."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.core.models import LookupValue


@dataclass(frozen=True, slots=True)
class LookupSeedValue:
    code: str
    label: str
    description: str | None = None
    sort_order: int = 100


@dataclass(frozen=True, slots=True)
class LookupSeedDomain:
    name: str
    ownership: str
    description: str
    values: tuple[LookupSeedValue, ...]


SYSTEM_LOOKUP_DOMAINS: tuple[LookupSeedDomain, ...] = (
    LookupSeedDomain(
        name="legal_form",
        ownership="system",
        description="Cross-module legal form dictionary for CRM, partner, and company master data.",
        values=(
            LookupSeedValue("gmbh", "GmbH", "Gesellschaft mit beschraenkter Haftung", 10),
            LookupSeedValue("ug", "UG (haftungsbeschraenkt)", "Unternehmergesellschaft", 20),
            LookupSeedValue("ag", "AG", "Aktiengesellschaft", 30),
            LookupSeedValue("ek", "e.K.", "Eingetragener Kaufmann", 40),
            LookupSeedValue("sole_proprietorship", "Einzelunternehmen", "Natuerliche Person als Unternehmen", 50),
            LookupSeedValue("public_authority", "Behoerde", "Oeffentliche Stelle oder Behoerde", 60),
        ),
    ),
    LookupSeedDomain(
        name="invoice_layout",
        ownership="system",
        description="Finance-facing invoice layout options approved for downstream billing tasks.",
        values=(
            LookupSeedValue("standard", "Standard", "Regulaeres Rechnungslayout", 10),
            LookupSeedValue("compact", "Kompakt", "Verdichtetes Layout fuer einfache Leistungsnachweise", 20),
            LookupSeedValue("detailed_timesheet", "Mit Leistungsnachweis", "Layout mit Leistungs- und Zeilendetails", 30),
        ),
    ),
    LookupSeedDomain(
        name="invoice_delivery_method",
        ownership="system",
        description="Customer billing delivery channels used by invoice dispatch and portal release flows.",
        values=(
            LookupSeedValue("email_pdf", "E-Mail PDF", "Rechnungsversand per E-Mail mit PDF", 10),
            LookupSeedValue("portal_download", "Portal Download", "Bereitstellung im Kundenportal", 20),
            LookupSeedValue("postal_print", "Postversand", "Physischer Druck- und Postversand", 30),
            LookupSeedValue("e_invoice", "E-Rechnung", "Strukturierte elektronische Rechnung", 40),
        ),
    ),
    LookupSeedDomain(
        name="dunning_stage",
        ownership="system",
        description="Stable finance dunning stages for reminder and collections workflows.",
        values=(
            LookupSeedValue("none", "Keine Mahnung", "Noch keine Mahnstufe erreicht", 10),
            LookupSeedValue("reminder_1", "Mahnstufe 1", "Erste Zahlungserinnerung", 20),
            LookupSeedValue("reminder_2", "Mahnstufe 2", "Zweite Mahnung", 30),
            LookupSeedValue("final_notice", "Letzte Mahnung", "Letzte Zahlungsaufforderung", 40),
        ),
    ),
    LookupSeedDomain(
        name="dunning_policy",
        ownership="system",
        description="Customer-facing dunning policy profiles used by CRM commercial configuration.",
        values=(
            LookupSeedValue("disabled", "Deaktiviert", "Keine Mahnlogik fuer diesen Kunden anwenden", 10),
            LookupSeedValue("standard", "Standard", "Standardisierte Mahnlogik mit regulaerer Eskalation", 20),
            LookupSeedValue("strict", "Streng", "Verkuerzte Fristen mit frueher Eskalation", 30),
        ),
    ),
    LookupSeedDomain(
        name="report_category",
        ownership="system",
        description="Shared reporting categories for operational, finance, and compliance output grouping.",
        values=(
            LookupSeedValue("operations", "Operativ", "Operative Steuerungs- und Einsatzberichte", 10),
            LookupSeedValue("finance", "Finanzen", "Kaufmaennische und abrechnungsbezogene Reports", 20),
            LookupSeedValue("compliance", "Compliance", "Qualitaets- und Nachweisberichte", 30),
            LookupSeedValue("management", "Management", "Mandanten- und Bereichsuebersichten", 40),
        ),
    ),
    LookupSeedDomain(
        name="notice_category",
        ownership="system",
        description="Shared info/notice categories for employee, customer, and subcontractor communications.",
        values=(
            LookupSeedValue("operations", "Einsatzhinweis", "Operative Mitteilung zum Tagesgeschaeft", 10),
            LookupSeedValue("safety", "Sicherheit", "Sicherheitsrelevante Information", 20),
            LookupSeedValue("hr", "Personal", "Personal- oder organisationsbezogene Mitteilung", 30),
            LookupSeedValue("compliance", "Compliance", "Pflichtinformation mit Nachweisbezug", 40),
        ),
    ),
)


TENANT_EXTENSIBLE_LOOKUP_DOMAINS: tuple[LookupSeedDomain, ...] = (
    LookupSeedDomain(
        name="customer_category",
        ownership="tenant_extensible",
        description="Tenant-maintained CRM categorization for customer portfolio segmentation.",
        values=(),
    ),
    LookupSeedDomain(
        name="employee_group",
        ownership="tenant_extensible",
        description="Tenant-maintained HR grouping for workforce segmentation and filtering.",
        values=(),
    ),
    LookupSeedDomain(
        name="subcontractor_category",
        ownership="tenant_extensible",
        description="Tenant-maintained partner segmentation for subcontractor management.",
        values=(),
    ),
    LookupSeedDomain(
        name="site_category",
        ownership="tenant_extensible",
        description="Tenant-maintained site grouping for planning and reporting.",
        values=(),
    ),
)


ALL_LOOKUP_DOMAINS: tuple[LookupSeedDomain, ...] = SYSTEM_LOOKUP_DOMAINS + TENANT_EXTENSIBLE_LOOKUP_DOMAINS


def seed_lookup_values(
    session: Session,
    *,
    tenant_id: str | None = None,
    actor_user_id: str | None = None,
) -> dict[str, int]:
    """Insert missing lookup rows without creating duplicates."""

    inserted = 0
    updated = 0
    domains = SYSTEM_LOOKUP_DOMAINS if tenant_id is None else TENANT_EXTENSIBLE_LOOKUP_DOMAINS

    for domain in domains:
        for value in domain.values:
            existing = session.scalars(
                select(LookupValue).where(
                    LookupValue.tenant_id == tenant_id,
                    LookupValue.domain == domain.name,
                    LookupValue.code == value.code,
                )
            ).one_or_none()

            if existing is None:
                session.add(
                    LookupValue(
                        tenant_id=tenant_id,
                        domain=domain.name,
                        code=value.code,
                        label=value.label,
                        description=value.description,
                        sort_order=value.sort_order,
                        created_by_user_id=actor_user_id,
                        updated_by_user_id=actor_user_id,
                    )
                )
                inserted += 1
                continue

            changed = False
            if existing.label != value.label:
                existing.label = value.label
                changed = True
            if existing.description != value.description:
                existing.description = value.description
                changed = True
            if existing.sort_order != value.sort_order:
                existing.sort_order = value.sort_order
                changed = True

            if changed:
                existing.updated_by_user_id = actor_user_id
                existing.version_no = (existing.version_no or 0) + 1
                updated += 1

    return {"inserted": inserted, "updated": updated}
