"""Seed canonical employee document types for the employee admin upload flow.

Revision ID: 0060_seed_employee_document_types
Revises: 0059_employee_file_operational_fields
Create Date: 2026-04-01 00:00:00
"""

from __future__ import annotations

from alembic import op


revision = "0060_seed_employee_document_types"
down_revision = "0059_employee_file_operational_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO docs.document_type (key, name, description, is_system_type)
        VALUES
          ('employment_contract', 'Arbeitsvertrag', 'Unterzeichnete Arbeitsvertraege und Vertragsnachtraege.', true),
          ('identity_card', 'Personalausweis', 'Ausweis- oder Identitaetsnachweise fuer Mitarbeitende.', true),
          ('passport_copy', 'Passkopie', 'Passkopien fuer Identitaets- oder Reisepruefungen.', true),
          ('residence_permit', 'Aufenthaltstitel', 'Nachweise ueber gueltige Aufenthalts- und Arbeitsberechtigungen.', true),
          ('driving_licence', 'Fuehrerschein', 'Fuehrerscheinkopien fuer fahrzeugbezogene Einsaetze.', true),
          ('qualification_certificate', 'Qualifikationsnachweis', 'Zertifikate, Befaehigungsnachweise und Schulungsbelege.', true),
          ('employee_misc', 'Mitarbeitendenanlage', 'Sonstige mitarbeitendenbezogene Dokumente ausserhalb der Standardkategorien.', true)
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM docs.document_type
        WHERE key IN (
          'employment_contract',
          'identity_card',
          'passport_copy',
          'residence_permit',
          'driving_licence',
          'qualification_certificate',
          'employee_misc'
        )
        AND NOT EXISTS (
          SELECT 1
          FROM docs.document AS d
          WHERE d.document_type_id = docs.document_type.id
        )
        """
    )
