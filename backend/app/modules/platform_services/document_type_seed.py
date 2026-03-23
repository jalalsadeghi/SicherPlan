"""Idempotent seed bundle for go-live document types."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.platform_services.docs_models import DocumentType


@dataclass(frozen=True, slots=True)
class DocumentTypeSeed:
    key: str
    name: str
    description: str


DOCUMENT_TYPE_SEEDS: tuple[DocumentTypeSeed, ...] = (
    DocumentTypeSeed("customer_contract", "Kundenvertrag", "Vertrags- und Stammakten fuer Kundenmigration und CRM."),
    DocumentTypeSeed("employee_personnel_file", "Personalakte", "Historische oder aktuelle Personalunterlagen."),
    DocumentTypeSeed("subcontractor_compliance", "Subunternehmer-Nachweis", "Partnerbezogene Compliance- und Vertragsnachweise."),
    DocumentTypeSeed("order_attachment", "Auftragsanlage", "Bestandsdokumente und Anlagen zu Kundenauftraegen."),
    DocumentTypeSeed("finance_supporting_document", "Finanzbeleg", "Abrechnungsnahe Belege fuer Zeiten, Kosten oder Rechnungen."),
    DocumentTypeSeed("generated_badge_output", "Badge-/Code-Ausgabe", "Generierte QR-, Barcode- oder Badge-Artefakte."),
    DocumentTypeSeed("generated_report_output", "Generierter Report", "Generierte operative oder kaufmaennische PDF-Ausgaben."),
)


def seed_document_types(session: Session, *, actor_user_id: str | None = None) -> dict[str, int]:
    inserted = 0
    updated = 0
    for seed in DOCUMENT_TYPE_SEEDS:
        existing = session.scalars(select(DocumentType).where(DocumentType.key == seed.key)).one_or_none()
        if existing is None:
            session.add(
                DocumentType(
                    key=seed.key,
                    name=seed.name,
                    description=seed.description,
                    is_system_type=True,
                    created_by_user_id=actor_user_id,
                    updated_by_user_id=actor_user_id,
                )
            )
            inserted += 1
            continue
        changed = False
        if existing.name != seed.name:
            existing.name = seed.name
            changed = True
        if existing.description != seed.description:
            existing.description = seed.description
            changed = True
        if not existing.is_system_type:
            existing.is_system_type = True
            changed = True
        if changed:
            existing.updated_by_user_id = actor_user_id
            existing.version_no = (existing.version_no or 0) + 1
            updated += 1
    return {"inserted": inserted, "updated": updated}
