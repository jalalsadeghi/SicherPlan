"""Migration template package and preflight validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.modules.platform_services.migration_schemas import (
    MigrationFieldDictionaryItem,
    MigrationPreflightRequest,
    MigrationPreflightResult,
    MigrationPreflightRowIssue,
    MigrationPreflightRowResult,
    MigrationPreflightSummary,
    MigrationTemplatePackageRead,
    MigrationTemplateSheetRead,
)


@dataclass(frozen=True, slots=True)
class _FieldSpec:
    name: str
    description: str
    required: bool = False
    business_key: bool = False
    lookup_domain: str | None = None
    foreign_sheet: str | None = None


@dataclass(frozen=True, slots=True)
class _SheetSpec:
    sheet_key: str
    business_key_field: str
    match_actions: tuple[str, ...]
    load_order: int
    fields: tuple[_FieldSpec, ...]
    example_rows: tuple[dict[str, object], ...]


class MigrationPackageRepository(Protocol):
    def customer_exists_by_number(self, tenant_id: str, customer_number: str) -> bool: ...
    def employee_exists_by_personnel_no(self, tenant_id: str, personnel_no: str) -> bool: ...
    def subcontractor_exists_by_number(self, tenant_id: str, subcontractor_number: str) -> bool: ...
    def order_exists_by_number(self, tenant_id: str, order_no: str) -> bool: ...
    def lookup_value_exists(self, tenant_id: str, domain: str, code: str) -> bool: ...
    def requirement_type_exists(self, tenant_id: str, code: str) -> bool: ...
    def document_type_exists(self, key: str) -> bool: ...


_SHEETS: tuple[_SheetSpec, ...] = (
    _SheetSpec(
        sheet_key="customers",
        business_key_field="customer_number",
        match_actions=("upsert", "create_only", "update_only"),
        load_order=10,
        fields=(
            _FieldSpec("match_action", "Explizite Matching-Regel fuer Create/Update.", required=True),
            _FieldSpec("customer_number", "Mandantenbezogene Kundennummer.", required=True, business_key=True),
            _FieldSpec("name", "Anzeigename des Kunden.", required=True),
            _FieldSpec("legal_name", "Rechtlicher Name des Kunden."),
            _FieldSpec("legal_form_code", "Lookup-Code fuer Rechtsform.", lookup_domain="legal_form"),
            _FieldSpec("default_branch_id", "Default-Niederlassung fuer operative Scopes."),
            _FieldSpec("default_mandate_id", "Default-Mandat fuer operative Scopes."),
            _FieldSpec("status", "Lifecycle-Status; Standard ist active."),
            _FieldSpec("notes", "Freitext fuer Migrationsteams."),
        ),
        example_rows=(
            {
                "match_action": "upsert",
                "customer_number": "K-1001",
                "name": "Messe Berlin",
                "legal_name": "Messe Berlin GmbH",
                "legal_form_code": "gmbh",
                "default_branch_id": "branch-berlin",
                "default_mandate_id": "mandate-ops",
                "status": "active",
            },
        ),
    ),
    _SheetSpec(
        sheet_key="employees",
        business_key_field="personnel_no",
        match_actions=("upsert", "create_only", "update_only"),
        load_order=20,
        fields=(
            _FieldSpec("match_action", "Explizite Matching-Regel fuer Create/Update.", required=True),
            _FieldSpec("personnel_no", "Mandantenbezogene Personalnummer.", required=True, business_key=True),
            _FieldSpec("first_name", "Vorname.", required=True),
            _FieldSpec("last_name", "Nachname.", required=True),
            _FieldSpec("preferred_name", "Rufname."),
            _FieldSpec("work_email", "Dienstliche E-Mail."),
            _FieldSpec("mobile_phone", "Mobilnummer."),
            _FieldSpec("default_branch_id", "Default-Niederlassung."),
            _FieldSpec("default_mandate_id", "Default-Mandat."),
            _FieldSpec("hire_date", "Eintrittsdatum ISO-8601."),
            _FieldSpec("status", "Lifecycle-Status; Standard ist active."),
        ),
        example_rows=(
            {
                "match_action": "upsert",
                "personnel_no": "P-2001",
                "first_name": "Anna",
                "last_name": "Schmidt",
                "preferred_name": "Anni",
                "work_email": "anna.schmidt@example.test",
                "default_branch_id": "branch-berlin",
                "status": "active",
            },
        ),
    ),
    _SheetSpec(
        sheet_key="subcontractors",
        business_key_field="subcontractor_number",
        match_actions=("upsert", "create_only", "update_only"),
        load_order=30,
        fields=(
            _FieldSpec("match_action", "Explizite Matching-Regel fuer Create/Update.", required=True),
            _FieldSpec("subcontractor_number", "Mandantenbezogene Partnernummer.", required=True, business_key=True),
            _FieldSpec("legal_name", "Rechtlicher Name.", required=True),
            _FieldSpec("display_name", "Anzeigename."),
            _FieldSpec("legal_form_code", "Lookup-Code fuer Rechtsform.", lookup_domain="legal_form"),
            _FieldSpec(
                "subcontractor_status_code",
                "Lookup-Code fuer Partnerstatus.",
                lookup_domain="subcontractor_status",
            ),
            _FieldSpec("managing_director_name", "Geschaeftsfuehrer."),
            _FieldSpec("status", "Lifecycle-Status; Standard ist active."),
        ),
        example_rows=(
            {
                "match_action": "upsert",
                "subcontractor_number": "SU-3001",
                "legal_name": "Nord Security Service GmbH",
                "display_name": "Nord Security",
                "legal_form_code": "gmbh",
                "subcontractor_status_code": "active",
                "status": "active",
            },
        ),
    ),
    _SheetSpec(
        sheet_key="orders",
        business_key_field="order_no",
        match_actions=("upsert", "create_only", "update_only"),
        load_order=40,
        fields=(
            _FieldSpec("match_action", "Explizite Matching-Regel fuer Create/Update.", required=True),
            _FieldSpec("order_no", "Mandantenbezogene Auftragsnummer.", required=True, business_key=True),
            _FieldSpec("customer_number", "Referenz auf customers.customer_number.", required=True, foreign_sheet="customers"),
            _FieldSpec("requirement_type_code", "Requirement-Type-Code aus ops.requirement_type.", required=True),
            _FieldSpec("title", "Auftragstitel.", required=True),
            _FieldSpec("service_category_code", "Servicekategorie laut Quellsystem.", required=True),
            _FieldSpec("service_from", "Leistungsbeginn ISO-8601.", required=True),
            _FieldSpec("service_to", "Leistungsende ISO-8601.", required=True),
            _FieldSpec("status", "Lifecycle-Status; Standard ist active."),
        ),
        example_rows=(
            {
                "match_action": "upsert",
                "order_no": "A-4001",
                "customer_number": "K-1001",
                "requirement_type_code": "event_security",
                "title": "Fruehjahrsmesse Eingang Nord",
                "service_category_code": "event",
                "service_from": "2026-04-15",
                "service_to": "2026-04-20",
                "status": "active",
            },
        ),
    ),
    _SheetSpec(
        sheet_key="documents",
        business_key_field="manifest_row_key",
        match_actions=("import_only",),
        load_order=50,
        fields=(
            _FieldSpec("manifest_row_key", "Eindeutiger Manifestschluessel.", required=True, business_key=True),
            _FieldSpec("source_system", "Quellsystembezeichner.", required=True),
            _FieldSpec("legacy_document_id", "Legacy-Dokument-ID.", required=True),
            _FieldSpec("source_file_name", "Dateiname aus dem Quellsystem.", required=True),
            _FieldSpec("title", "Dokumenttitel.", required=True),
            _FieldSpec("owner_sheet", "Referenzierter Business-Sheet-Key.", required=True, foreign_sheet="*package*"),
            _FieldSpec("owner_business_key", "Business-Key des referenzierten Owners.", required=True),
            _FieldSpec("document_type_key", "Zentraler Dokumenttyp.", required=False),
            _FieldSpec("relation_type", "Link-Relation, z. B. attachment oder generated_output.", required=True),
            _FieldSpec("checksum_sha256", "Erwartete SHA-256 Checksumme.", required=True),
            _FieldSpec("content_base64", "Pilot-Dateiinhalt Base64-kodiert.", required=True),
        ),
        example_rows=(
            {
                "manifest_row_key": "DOC-1",
                "source_system": "legacy_dms",
                "legacy_document_id": "4711",
                "source_file_name": "vertrag.pdf",
                "title": "Rahmenvertrag 2025",
                "owner_sheet": "customers",
                "owner_business_key": "K-1001",
                "document_type_key": "customer_contract",
                "relation_type": "attachment",
                "checksum_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "content_base64": "UERG",
            },
        ),
    ),
)

_SHEET_BY_KEY = {sheet.sheet_key: sheet for sheet in _SHEETS}


class MigrationPackageService:
    def __init__(self, repository: MigrationPackageRepository) -> None:
        self.repository = repository

    def describe_package(self) -> MigrationTemplatePackageRead:
        return MigrationTemplatePackageRead(
            package_version="v1",
            sheets=[
                MigrationTemplateSheetRead(
                    sheet_key=sheet.sheet_key,
                    business_key_field=sheet.business_key_field,
                    match_actions=sheet.match_actions,
                    load_order=sheet.load_order,
                    field_dictionary=[
                        MigrationFieldDictionaryItem(
                            field_name=field.name,
                            required=field.required,
                            description=field.description,
                            business_key=field.business_key,
                            lookup_domain=field.lookup_domain,
                            foreign_sheet=field.foreign_sheet,
                        )
                        for field in sheet.fields
                    ],
                    example_rows=list(sheet.example_rows),
                )
                for sheet in _SHEETS
            ],
            load_order=[sheet.sheet_key for sheet in sorted(_SHEETS, key=lambda row: row.load_order)],
            document_manifest_notes=[
                "Dokumentimporte bleiben manifestbasiert und laufen ueber docs.document/docs.document_version/docs.document_link.",
                "Dateinamen, Checksumme und Legacy-Provenienz werden explizit gespeichert; Dateipfade werden nie als Owner-Semantik interpretiert.",
            ],
        )

    def preflight(self, payload: MigrationPreflightRequest) -> MigrationPreflightResult:
        row_results: list[MigrationPreflightRowResult] = []
        package_business_keys: dict[str, set[str]] = {}
        for sheet in payload.sheets:
            spec = _SHEET_BY_KEY.get(sheet.sheet_key)
            if spec is None:
                for row_no, _row in enumerate(sheet.rows, start=2):
                    row_results.append(
                        MigrationPreflightRowResult(
                            sheet_key=sheet.sheet_key,
                            row_no=row_no,
                            status="invalid",
                            issues=[MigrationPreflightRowIssue(code="unknown_sheet", message="Unbekannter Sheet-Key.")],
                        )
                    )
                continue
            seen_keys = package_business_keys.setdefault(sheet.sheet_key, set())
            for row_no, raw_row in enumerate(sheet.rows, start=2):
                row = {key: "" if value is None else str(value).strip() for key, value in raw_row.items()}
                row_results.append(self._validate_row(payload.tenant_id, spec, row_no, row, seen_keys, package_business_keys))
        summary = MigrationPreflightSummary(
            total_rows=len(row_results),
            valid_rows=sum(1 for row in row_results if row.status == "valid"),
            invalid_rows=sum(1 for row in row_results if row.status == "invalid"),
            create_rows=sum(1 for row in row_results if row.match_result == "create"),
            update_rows=sum(1 for row in row_results if row.match_result == "update"),
            conflict_rows=sum(1 for row in row_results if row.match_result == "conflict"),
        )
        return MigrationPreflightResult(
            tenant_id=payload.tenant_id,
            package_version=payload.package_version,
            summary=summary,
            rows=row_results,
        )

    def _validate_row(
        self,
        tenant_id: str,
        spec: _SheetSpec,
        row_no: int,
        row: dict[str, str],
        seen_keys: set[str],
        package_business_keys: dict[str, set[str]],
    ) -> MigrationPreflightRowResult:
        issues: list[MigrationPreflightRowIssue] = []
        business_key = row.get(spec.business_key_field) or None
        if business_key:
            if business_key in seen_keys:
                issues.append(MigrationPreflightRowIssue(code="duplicate_business_key", message="Business-Key ist im Paket doppelt."))
            else:
                seen_keys.add(business_key)
        for field in spec.fields:
            value = row.get(field.name, "")
            if field.required and not value:
                issues.append(
                    MigrationPreflightRowIssue(
                        code="missing_required_field",
                        message=f"Pflichtfeld '{field.name}' fehlt.",
                    )
                )
            if value and field.lookup_domain and not self.repository.lookup_value_exists(tenant_id, field.lookup_domain, value):
                issues.append(
                    MigrationPreflightRowIssue(
                        code="unknown_lookup_value",
                        message=f"Lookup-Wert '{value}' fuer Domain '{field.lookup_domain}' ist unbekannt.",
                    )
                )
        if row.get("status") in {"draft", "pending"}:
            issues.append(
                MigrationPreflightRowIssue(
                    code="unsafe_status_combination",
                    message="Migrationspakete duerfen keine instabilen Workflow-Zwischenstatus laden.",
                )
            )
        if spec.sheet_key == "orders":
            customer_number = row.get("customer_number") or ""
            if customer_number and customer_number not in package_business_keys.get("customers", set()) and not self.repository.customer_exists_by_number(tenant_id, customer_number):
                issues.append(
                    MigrationPreflightRowIssue(
                        code="unknown_customer_reference",
                        message="Kundenreferenz ist weder im Paket noch im Zielsystem vorhanden.",
                    )
                )
            requirement_type_code = row.get("requirement_type_code") or ""
            if requirement_type_code and not self.repository.requirement_type_exists(tenant_id, requirement_type_code):
                issues.append(
                    MigrationPreflightRowIssue(
                        code="unknown_requirement_type",
                        message="Requirement-Type-Code ist im Zielsystem nicht vorhanden.",
                    )
                )
        if spec.sheet_key == "documents":
            owner_sheet = row.get("owner_sheet") or ""
            owner_business_key = row.get("owner_business_key") or ""
            if owner_sheet not in _SHEET_BY_KEY or owner_sheet == "documents":
                issues.append(MigrationPreflightRowIssue(code="invalid_owner_sheet", message="Owner-Sheet ist ungueltig."))
            elif owner_business_key and owner_business_key not in package_business_keys.get(owner_sheet, set()) and not self._owner_exists_in_system(tenant_id, owner_sheet, owner_business_key):
                issues.append(
                    MigrationPreflightRowIssue(
                        code="orphan_document_link",
                        message="Dokument verweist auf keinen bekannten Owner.",
                    )
                )
            document_type_key = row.get("document_type_key") or ""
            if document_type_key and not self.repository.document_type_exists(document_type_key):
                issues.append(MigrationPreflightRowIssue(code="unknown_document_type", message="Dokumenttyp ist unbekannt."))
        match_result = self._resolve_match_result(tenant_id, spec, row, issues)
        status = "invalid" if issues else "valid"
        return MigrationPreflightRowResult(
            sheet_key=spec.sheet_key,
            row_no=row_no,
            business_key=business_key,
            status=status,
            match_result=match_result,
            issues=issues,
        )

    def _resolve_match_result(
        self,
        tenant_id: str,
        spec: _SheetSpec,
        row: dict[str, str],
        issues: list[MigrationPreflightRowIssue],
    ) -> str | None:
        action = row.get("match_action") or ("import_only" if spec.sheet_key == "documents" else "")
        if action not in spec.match_actions:
            issues.append(MigrationPreflightRowIssue(code="invalid_match_action", message="Match-Aktion ist ungueltig."))
            return "conflict"
        if spec.sheet_key == "documents":
            return "create"
        business_key = row.get(spec.business_key_field) or ""
        exists = self._owner_exists_in_system(tenant_id, spec.sheet_key, business_key)
        if exists and action == "create_only":
            issues.append(MigrationPreflightRowIssue(code="match_conflict_existing", message="Zielobjekt existiert bereits, Row ist aber create_only."))
            return "conflict"
        if not exists and action == "update_only":
            issues.append(MigrationPreflightRowIssue(code="match_conflict_missing", message="Zielobjekt fehlt, Row ist aber update_only."))
            return "conflict"
        return "update" if exists else "create"

    def _owner_exists_in_system(self, tenant_id: str, sheet_key: str, business_key: str) -> bool:
        if not business_key:
            return False
        if sheet_key == "customers":
            return self.repository.customer_exists_by_number(tenant_id, business_key)
        if sheet_key == "employees":
            return self.repository.employee_exists_by_personnel_no(tenant_id, business_key)
        if sheet_key == "subcontractors":
            return self.repository.subcontractor_exists_by_number(tenant_id, business_key)
        if sheet_key == "orders":
            return self.repository.order_exists_by_number(tenant_id, business_key)
        return False
