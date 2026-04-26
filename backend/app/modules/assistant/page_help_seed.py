"""Seed data for verified assistant page help manifests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assistant.models import AssistantPageHelpManifest


@dataclass(frozen=True)
class AssistantPageHelpSeed:
    page_id: str
    route_name: str | None
    path_template: str | None
    module_key: str
    language_code: str | None
    manifest_version: int
    status: str
    manifest_json: dict[str, Any]
    verified_from: list[dict[str, Any]]


ASSISTANT_PAGE_HELP_SEEDS: tuple[AssistantPageHelpSeed, ...] = (
    AssistantPageHelpSeed(
        page_id="E-01",
        route_name="SicherPlanEmployees",
        path_template="/admin/employees",
        module_key="employees",
        language_code="en",
        manifest_version=1,
        status="active",
        verified_from=[
            {
                "file": "web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue",
                "evidence": "Header action button uses employeeAdmin.actions.newEmployee, startCreateEmployee, and employee-list-header-new-employee.",
            },
            {
                "file": "web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts",
                "evidence": 'employeeAdmin.actions.newEmployee = "Create employee file"; form labels and section titles verified in source.',
            },
            {
                "file": "web/apps/web-antd/src/locales/langs/en-US/sicherplan.json",
                "evidence": 'sicherplan.navigation.workforce = "Workforce & Partners" and sicherplan.admin.employees = "Employees".',
            },
        ],
        manifest_json={
            "page_id": "E-01",
            "page_title": "Employees Workspace",
            "route_name": "SicherPlanEmployees",
            "path_template": "/admin/employees",
            "module_key": "employees",
            "source_status": "verified",
            "verified_from": [
                {
                    "file": "web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue",
                    "evidence": "Top-right list header action button verified in source.",
                }
            ],
            "sidebar_path": [
                {"label": "Workforce & Partners", "verified": True},
                {"label": "Employees", "verified": True},
            ],
            "primary_actions": [
                {
                    "action_key": "employees.create.open",
                    "label": "Create employee file",
                    "label_i18n_key": "employeeAdmin.actions.newEmployee",
                    "action_type": "button",
                    "selector": "[data-assistant-action='employees.create.open']",
                    "test_id": "employee-list-header-new-employee",
                    "location": "top-right toolbar",
                    "required_permissions": ["employees.employee.write"],
                    "opens": "employee-create-form",
                    "result": "Opens the structured employee file form in create mode.",
                    "verified": True,
                }
            ],
            "form_sections": [
                {
                    "section_key": "employee.identity",
                    "title": "Identity and personnel number",
                    "title_i18n_key": "employeeAdmin.form.identityTitle",
                    "verified": True,
                    "fields": [
                        {
                            "field_key": "personnel_no",
                            "label": "Personnel number",
                            "label_i18n_key": "employeeAdmin.fields.personnelNo",
                            "required": True,
                            "verified": True,
                        },
                        {
                            "field_key": "first_name",
                            "label": "First name",
                            "label_i18n_key": "employeeAdmin.fields.firstName",
                            "required": True,
                            "verified": True,
                        },
                        {
                            "field_key": "last_name",
                            "label": "Last name",
                            "label_i18n_key": "employeeAdmin.fields.lastName",
                            "required": True,
                            "verified": True,
                        },
                    ],
                }
            ],
            "post_create_steps": [
                {"step_key": "employee.qualifications.complete", "label": "Complete qualifications", "page_id": "E-01", "verified": True},
                {"step_key": "employee.availability.complete", "label": "Complete availability", "page_id": "E-01", "verified": True},
                {"step_key": "employee.access_link.check", "label": "Check app access link", "page_id": "E-01", "verified": True},
            ],
            "fallback_policy": {
                "exact_ui_guidance_allowed": True,
                "assistant_may_guess_missing_labels": False,
            },
        },
    ),
    AssistantPageHelpSeed(
        page_id="E-01",
        route_name="SicherPlanEmployees",
        path_template="/admin/employees",
        module_key="employees",
        language_code="de",
        manifest_version=1,
        status="active",
        verified_from=[
            {
                "file": "web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue",
                "evidence": "Header action button uses employeeAdmin.actions.newEmployee and startCreateEmployee.",
            },
            {
                "file": "web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts",
                "evidence": 'employeeAdmin.actions.newEmployee = "Mitarbeiterakte anlegen"; form labels and section titles verified in source.',
            },
            {
                "file": "web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json",
                "evidence": 'sicherplan.navigation.workforce = "Belegschaft & Partner" and sicherplan.admin.employees = "Mitarbeiter".',
            },
        ],
        manifest_json={
            "page_id": "E-01",
            "page_title": "Mitarbeiter-Workspace",
            "route_name": "SicherPlanEmployees",
            "path_template": "/admin/employees",
            "module_key": "employees",
            "source_status": "verified",
            "verified_from": [
                {
                    "file": "web/apps/web-antd/src/sicherplan-legacy/views/EmployeeAdminView.vue",
                    "evidence": "Top-right list header action button verified in source.",
                }
            ],
            "sidebar_path": [
                {"label": "Belegschaft & Partner", "verified": True},
                {"label": "Mitarbeiter", "verified": True},
            ],
            "primary_actions": [
                {
                    "action_key": "employees.create.open",
                    "label": "Mitarbeiterakte anlegen",
                    "label_i18n_key": "employeeAdmin.actions.newEmployee",
                    "action_type": "button",
                    "selector": "[data-assistant-action='employees.create.open']",
                    "test_id": "employee-list-header-new-employee",
                    "location": "Toolbar oben rechts",
                    "required_permissions": ["employees.employee.write"],
                    "opens": "employee-create-form",
                    "result": "Öffnet die strukturierte Mitarbeiterakte im Anlegemodus.",
                    "verified": True,
                }
            ],
            "form_sections": [
                {
                    "section_key": "employee.identity",
                    "title": "Identität und Personalnummer",
                    "title_i18n_key": "employeeAdmin.form.identityTitle",
                    "verified": True,
                    "fields": [
                        {
                            "field_key": "personnel_no",
                            "label": "Personalnummer",
                            "label_i18n_key": "employeeAdmin.fields.personnelNo",
                            "required": True,
                            "verified": True,
                        },
                        {
                            "field_key": "first_name",
                            "label": "Vorname",
                            "label_i18n_key": "employeeAdmin.fields.firstName",
                            "required": True,
                            "verified": True,
                        },
                        {
                            "field_key": "last_name",
                            "label": "Nachname",
                            "label_i18n_key": "employeeAdmin.fields.lastName",
                            "required": True,
                            "verified": True,
                        },
                    ],
                }
            ],
            "post_create_steps": [
                {"step_key": "employee.qualifications.complete", "label": "Qualifikationen vervollständigen", "page_id": "E-01", "verified": True},
                {"step_key": "employee.availability.complete", "label": "Verfügbarkeit pflegen", "page_id": "E-01", "verified": True},
                {"step_key": "employee.access_link.check", "label": "App-Zugang prüfen", "page_id": "E-01", "verified": True},
            ],
            "fallback_policy": {
                "exact_ui_guidance_allowed": True,
                "assistant_may_guess_missing_labels": False,
            },
        },
    ),
)


def seed_assistant_page_help_manifest(session: Session) -> dict[str, int]:
    inserted = 0
    updated = 0

    for seed in ASSISTANT_PAGE_HELP_SEEDS:
        existing = session.scalars(
            select(AssistantPageHelpManifest).where(
                AssistantPageHelpManifest.page_id == seed.page_id,
                AssistantPageHelpManifest.language_code == seed.language_code,
                AssistantPageHelpManifest.manifest_version == seed.manifest_version,
            )
        ).one_or_none()
        if existing is None:
            session.add(
                AssistantPageHelpManifest(
                    page_id=seed.page_id,
                    route_name=seed.route_name,
                    path_template=seed.path_template,
                    module_key=seed.module_key,
                    language_code=seed.language_code,
                    manifest_version=seed.manifest_version,
                    status=seed.status,
                    manifest_json=seed.manifest_json,
                    verified_from=seed.verified_from,
                )
            )
            inserted += 1
            continue

        changed = False
        for field_name, value in (
            ("route_name", seed.route_name),
            ("path_template", seed.path_template),
            ("module_key", seed.module_key),
            ("status", seed.status),
            ("manifest_json", seed.manifest_json),
            ("verified_from", seed.verified_from),
        ):
            if getattr(existing, field_name) != value:
                setattr(existing, field_name, value)
                changed = True
        if changed:
            session.add(existing)
            updated += 1

    if inserted or updated:
        session.commit()
    return {"inserted": inserted, "updated": updated}
