"""Workflow-intent detection and verified grounding facts."""

from __future__ import annotations

from dataclasses import dataclass
import re


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
ALIAS_STOPWORDS = {
    "a", "an", "and", "create", "do", "for", "how", "i", "it", "new", "the", "to",
    "anlegen", "den", "der", "die", "einen", "eine", "einer", "eines", "einem", "erstellen", "für", "ich", "neuen", "und", "wie",
}


@dataclass(frozen=True)
class AssistantWorkflowIntent:
    intent: str


@dataclass(frozen=True)
class AssistantWorkflowSourceBasisSeed:
    source_type: str
    source_name: str
    page_id: str | None
    module_key: str | None
    evidence: str


@dataclass(frozen=True)
class AssistantWorkflowStepSeed:
    step_key: str
    sequence: int
    page_id: str | None
    module_key: str | None
    purpose_en: str
    purpose_de: str
    required_permissions: tuple[str, ...] = ()
    source_basis: tuple[AssistantWorkflowSourceBasisSeed, ...] = ()


@dataclass(frozen=True)
class AssistantWorkflowSeed:
    workflow_key: str
    title_en: str
    title_de: str
    summary_en: str
    summary_de: str
    intent_aliases_en: tuple[str, ...]
    intent_aliases_de: tuple[str, ...]
    steps: tuple[AssistantWorkflowStepSeed, ...]
    linked_page_ids: tuple[str, ...]
    api_families: tuple[str, ...]
    ambiguity_notes: tuple[str, ...] = ()
    legacy_keys: tuple[str, ...] = ()

    @property
    def title(self) -> str:
        return self.title_en


def detect_workflow_intent(message: str) -> AssistantWorkflowIntent | None:
    lowered = message.strip().casefold()
    if not lowered:
        return None

    if _is_customer_plan_create(lowered):
        return AssistantWorkflowIntent(intent="customer_plan_create")
    if _is_customer_order_create(lowered):
        return AssistantWorkflowIntent(intent="customer_order_create")
    if _is_customer_create(lowered):
        return AssistantWorkflowIntent(intent="customer_create")
    if _is_contract_registration(lowered):
        return AssistantWorkflowIntent(intent="contract_or_document_register")
    if _is_employee_assign_to_shift(lowered):
        return AssistantWorkflowIntent(intent="employee_assign_to_shift")
    if _is_shift_release_to_employee_app(lowered):
        return AssistantWorkflowIntent(intent="shift_release_to_employee_app")
    if _is_actuals_billing_payroll_chain(lowered):
        return AssistantWorkflowIntent(intent="actuals_billing_payroll_chain")
    if _is_employee_create(lowered):
        return AssistantWorkflowIntent(intent="employee_create")

    alias_match = _detect_by_alias_match(lowered)
    if alias_match is not None:
        return AssistantWorkflowIntent(intent=alias_match)
    return None


def resolve_workflow_key(value: str | None) -> str | None:
    cleaned = str(value or "").strip()
    if not cleaned:
        return None
    if cleaned in WORKFLOW_HELP_SEEDS:
        return WORKFLOW_HELP_SEEDS[cleaned].workflow_key
    return None


def search_workflow_seeds(
    *,
    query: str | None,
    language_code: str | None,
    workflow_key: str | None,
    limit: int,
) -> list[AssistantWorkflowSeed]:
    resolved_key = resolve_workflow_key(workflow_key)
    if resolved_key is not None:
        return [WORKFLOW_HELP_SEEDS[resolved_key]]

    cleaned_query = str(query or "").strip()
    if not cleaned_query:
        return []

    normalized_query = cleaned_query.casefold()
    query_tokens = set(_tokenize(normalized_query))
    scores: list[tuple[float, AssistantWorkflowSeed]] = []
    direct_intent = _detect_by_heuristics(normalized_query)

    for workflow in CANONICAL_WORKFLOW_SEEDS:
        score = 0.0
        if direct_intent == workflow.workflow_key:
            score += 200.0
        alias_pool = list(workflow.intent_aliases_en) + list(workflow.intent_aliases_de)
        title_pool = [workflow.title_en, workflow.title_de, workflow.summary_en, workflow.summary_de]
        for alias in alias_pool:
            alias_norm = alias.casefold()
            if alias_norm and alias_norm in normalized_query:
                score += 50.0
            alias_tokens = set(_tokenize(alias_norm))
            score += len(query_tokens.intersection(alias_tokens)) * 8.0
        for title in title_pool:
            title_tokens = set(_tokenize(title.casefold()))
            score += len(query_tokens.intersection(title_tokens)) * 2.0
        for page_id in workflow.linked_page_ids:
            if page_id.casefold() in normalized_query:
                score += 12.0
        if language_code == "de":
            score += len(workflow.intent_aliases_de) * 0.2
        elif language_code == "en":
            score += len(workflow.intent_aliases_en) * 0.2
        if score > 0:
            scores.append((score, workflow))

    scores.sort(key=lambda item: (-item[0], item[1].workflow_key))
    return [item[1] for item in scores[: max(limit, 1)]]


def _basis(
    *,
    source_type: str,
    source_name: str,
    page_id: str | None,
    module_key: str | None,
    evidence: str,
) -> AssistantWorkflowSourceBasisSeed:
    return AssistantWorkflowSourceBasisSeed(
        source_type=source_type,
        source_name=source_name,
        page_id=page_id,
        module_key=module_key,
        evidence=evidence,
    )


def _step(
    *,
    step_key: str,
    sequence: int,
    page_id: str | None,
    module_key: str | None,
    purpose_en: str,
    purpose_de: str,
    required_permissions: tuple[str, ...] = (),
    source_basis: tuple[AssistantWorkflowSourceBasisSeed, ...] = (),
) -> AssistantWorkflowStepSeed:
    return AssistantWorkflowStepSeed(
        step_key=step_key,
        sequence=sequence,
        page_id=page_id,
        module_key=module_key,
        purpose_en=purpose_en,
        purpose_de=purpose_de,
        required_permissions=required_permissions,
        source_basis=source_basis,
    )


CUSTOMER_CREATE = AssistantWorkflowSeed(
    workflow_key="customer_create",
    title_en="Create a customer master record",
    title_de="Kundenstammdatensatz anlegen",
    summary_en="Customer setup starts in the Customers workspace and usually covers the customer master, contacts, addresses, billing profile, invoice parties, rate cards, portal privacy, and employee visibility blocks.",
    summary_de="Die Kundenanlage startet im Kunden-Workspace und umfasst in der Regel Kundenstamm, Kontakte, Adressen, Abrechnungsprofil, Rechnungsempfänger, Preisregeln, Portal-Datenschutz und Mitarbeitersperren.",
    intent_aliases_en=("create customer", "new customer", "customer master", "create a new customer"),
    intent_aliases_de=("kunde anlegen", "neuen kunden anlegen", "kundenstamm anlegen", "kunden erstellen"),
    linked_page_ids=("C-01",),
    api_families=("customers",),
    steps=(
        _step(
            step_key="customer_master",
            sequence=1,
            page_id="C-01",
            module_key="customers",
            purpose_en="Create or verify the customer master record before any order, planning, or billing workflow continues.",
            purpose_de="Kundenstammdaten anlegen oder prüfen, bevor Auftrags-, Planungs- oder Abrechnungsprozesse fortgesetzt werden.",
            required_permissions=("customers.customer.read", "customers.customer.write"),
            source_basis=(
                _basis(
                    source_type="role_page_coverage",
                    source_name="Assistant Role Page Coverage Map",
                    page_id="C-01",
                    module_key="customers",
                    evidence="Inferred from the verified role/page coverage and route catalog: C-01 is the tenant-scoped Customers workspace for customer master access.",
                ),
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The generated user manual states that customer master work starts in C-01.",
                ),
            ),
        ),
        _step(
            step_key="commercial_and_billing",
            sequence=2,
            page_id="C-01",
            module_key="customers",
            purpose_en="Maintain contacts, addresses, billing profile, invoice parties, and commercial/rate-card data inside the customer workspace.",
            purpose_de="Kontakte, Adressen, Abrechnungsprofil, Rechnungsempfänger und kaufmännische bzw. Preisregeldaten im Kunden-Workspace pflegen.",
            required_permissions=("customers.billing.read", "customers.billing.write"),
            source_basis=(
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The implementation data model assigns customer master and customer-history ownership to the Customers context.",
                ),
            ),
        ),
        _step(
            step_key="portal_privacy_and_blocks",
            sequence=3,
            page_id="C-01",
            module_key="customers",
            purpose_en="Review portal privacy defaults and any employee visibility restrictions before exposing customer-facing data.",
            purpose_de="Portal-Datenschutzvorgaben und eventuelle Mitarbeitersichtbarkeits-Sperren prüfen, bevor kundenseitige Daten freigegeben werden.",
            required_permissions=("customers.portal_access.read",),
            source_basis=(
                _basis(
                    source_type="security_doc",
                    source_name="AI Assistant Security",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The assistant security guidance requires least-privilege customer visibility and customer-facing name protection by default.",
                ),
            ),
        ),
    ),
)

CONTRACT_OR_DOCUMENT_REGISTER = AssistantWorkflowSeed(
    workflow_key="contract_or_document_register",
    title_en="Register a contract or document in the correct business context",
    title_de="Vertrag oder Dokument im richtigen Fachkontext registrieren",
    summary_en="Contract registration is document-centered and context-dependent. The assistant must distinguish customer contract, order attachment, subcontractor agreement, or generic document handling instead of inventing a standalone contract workspace.",
    summary_de="Die Vertragsregistrierung ist dokumentenzentriert und kontextabhängig. Der Assistent muss zwischen Kundenvertrag, Auftragsanhang, Subunternehmervereinbarung oder generischer Dokumentablage unterscheiden, statt einen eigenständigen Vertrags-Workspace zu erfinden.",
    intent_aliases_en=("register contract", "new contract", "register document", "upload agreement", "attach document"),
    intent_aliases_de=("vertrag registrieren", "neuen vertrag anlegen", "dokument registrieren", "vereinbarung hochladen", "anhang hinzufügen"),
    linked_page_ids=("PS-01", "C-01", "P-02", "S-01"),
    api_families=("platform_services", "customers", "planning", "subcontractors"),
    ambiguity_notes=(
        "If the user does not specify whether the document belongs to a customer relationship, an order/planning package, a subcontractor agreement, or a generic document workflow, ask that targeted clarifying question before suggesting a page.",
    ),
    steps=(
        _step(
            step_key="clarify_business_context",
            sequence=1,
            page_id="PS-01",
            module_key="platform_services",
            purpose_en="Clarify whether the item is a customer contract, order attachment, subcontractor agreement, or generic document before routing the user.",
            purpose_de="Klären, ob es sich um einen Kundenvertrag, einen Auftragsanhang, eine Subunternehmervereinbarung oder ein generisches Dokument handelt, bevor eine Seite empfohlen wird.",
            required_permissions=(),
            source_basis=(
                _basis(
                    source_type="operational_handbook",
                    source_name="Generated Operational Handbook",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="The operational handbook states that contract-like artifacts are handled as documents or attachments linked to the owning business entity.",
                ),
                _basis(
                    source_type="workflow_help",
                    source_name="Workflow Manifest",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="This workflow intentionally treats contract registration as ambiguous and requires targeted clarification before page guidance.",
                ),
            ),
        ),
        _step(
            step_key="generic_document_reference",
            sequence=2,
            page_id="PS-01",
            module_key="platform_services",
            purpose_en="Use Platform Services as the safe shared document reference when the exact subtype is still unclear and the user needs document create, version, upload, or linking guidance.",
            purpose_de="Platform Services als sicheren gemeinsamen Dokumentbezug verwenden, wenn der genaue Untertyp noch unklar ist und der Nutzer Anleitung für Anlegen, Versionieren, Hochladen oder Verknüpfen benötigt.",
            required_permissions=(),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="PS-01 is the verified Platform Services workspace.",
                ),
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="The generated user manual identifies PS-01 as the safe shared reference for document-centered workflows when the subtype is unclear.",
                ),
            ),
        ),
        _step(
            step_key="customer_or_order_attachment",
            sequence=3,
            page_id="C-01",
            module_key="customers",
            purpose_en="If the document belongs to a customer relationship or customer history, keep the workflow in Customers; if it belongs to an order or planning package, continue in Orders & Planning Records.",
            purpose_de="Wenn das Dokument zu einer Kundenbeziehung oder Kundenhistorie gehört, bleibt der Ablauf im Kunden-Workspace; gehört es zu einem Auftrag oder Planungspaket, geht es in Aufträge & Planungsdatensätze weiter.",
            required_permissions=("customers.customer.read", "planning.order.read", "planning.record.read"),
            source_basis=(
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The implementation data model places customer truth in Customers and planning packages in Planning.",
                ),
                _basis(
                    source_type="operational_handbook",
                    source_name="Generated Operational Handbook",
                    page_id="P-02",
                    module_key="planning",
                    evidence="The operational handbook says planning orders and planning records include documented planning packages and attachments.",
                ),
            ),
        ),
        _step(
            step_key="subcontractor_agreement",
            sequence=4,
            page_id="S-01",
            module_key="subcontractors",
            purpose_en="If the user means a subcontractor agreement, route the context into the Subcontractors workspace instead of treating it as a generic document only.",
            purpose_de="Wenn der Nutzer eine Subunternehmervereinbarung meint, muss der Kontext in den Subunternehmer-Workspace geleitet werden, statt ihn nur als generisches Dokument zu behandeln.",
            required_permissions=("subcontractors.company.read",),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="S-01",
                    module_key="subcontractors",
                    evidence="S-01 is the verified subcontractors workspace for tenant-scoped partner records.",
                ),
            ),
        ),
    ),
)

CUSTOMER_ORDER_CREATE = AssistantWorkflowSeed(
    workflow_key="customer_order_create",
    title_en="Create a customer order and planning record",
    title_de="Kundenauftrag und Planungsdatensatz anlegen",
    summary_en="A customer order belongs to an existing customer and continues into a planning record with attachments, commercial linkage, and operational preparation.",
    summary_de="Ein Kundenauftrag gehört zu einem bestehenden Kunden und wird mit Anhängen, kaufmännischer Verknüpfung und operativer Vorbereitung in einen Planungsdatensatz überführt.",
    intent_aliases_en=("create order", "new customer order", "create plan for customer", "create customer order"),
    intent_aliases_de=("auftrag erstellen", "neuen auftrag anlegen", "planung für kunden erstellen", "kundenauftrag anlegen"),
    linked_page_ids=("C-01", "P-02"),
    api_families=("customers", "planning"),
    steps=(
        _step(
            step_key="customer_context",
            sequence=1,
            page_id="C-01",
            module_key="customers",
            purpose_en="Create or verify the customer record before creating the order or project context.",
            purpose_de="Kundendatensatz anlegen oder prüfen, bevor Auftrag oder Projektkontext erstellt werden.",
            required_permissions=("customers.customer.read",),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Workflow Manifest",
                    page_id="C-01",
                    module_key="customers",
                    evidence="This workflow requires customer context before order creation.",
                ),
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The generated user manual states that order and planning flows depend on an existing customer context.",
                ),
            ),
        ),
        _step(
            step_key="order_and_planning_record",
            sequence=2,
            page_id="P-02",
            module_key="planning",
            purpose_en="Create the customer order, project or planning record, including attachments, commercial linkage, and requirement lines.",
            purpose_de="Kundenauftrag, Projekt oder Planungsdatensatz inklusive Anhängen, kaufmännischer Verknüpfung und Anforderungszeilen anlegen.",
            required_permissions=("planning.order.read", "planning.order.write", "planning.record.read", "planning.record.write"),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="P-02",
                    module_key="planning",
                    evidence="P-02 is the verified Orders & Planning Records workspace.",
                ),
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="P-02",
                    module_key="planning",
                    evidence="The generated user manual states that P-02 manages customer orders, planning records, and document packages.",
                ),
            ),
        ),
    ),
)

CUSTOMER_PLAN_CREATE = AssistantWorkflowSeed(
    workflow_key="customer_plan_create",
    title_en="Create a customer planning record and concrete shifts",
    title_de="Planungsdatensatz und konkrete Schichten für Kunden anlegen",
    summary_en="Planning starts with customer and order context, then continues from planning record setup into concrete shift planning.",
    summary_de="Die Planung startet mit Kunden- und Auftragskontext und geht dann vom Planungsdatensatz in die konkrete Schichtplanung über.",
    intent_aliases_en=("create customer plan", "new plan for customer", "create planning record", "plan customer shifts"),
    intent_aliases_de=("kundenplanung anlegen", "neuen plan für kunden erstellen", "planungsdatensatz anlegen", "kundenschichten planen"),
    linked_page_ids=("C-01", "P-02", "P-03"),
    api_families=("customers", "planning"),
    steps=(
        _step(
            step_key="customer_context",
            sequence=1,
            page_id="C-01",
            module_key="customers",
            purpose_en="Confirm the customer context first.",
            purpose_de="Zuerst den Kundenkontext bestätigen.",
            required_permissions=("customers.customer.read",),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Workflow Manifest",
                    page_id="C-01",
                    module_key="customers",
                    evidence="Customer context is the first prerequisite in this workflow.",
                ),
            ),
        ),
        _step(
            step_key="planning_record",
            sequence=2,
            page_id="P-02",
            module_key="planning",
            purpose_en="Create the planning record or order package that owns the operational planning context.",
            purpose_de="Den Planungsdatensatz oder das Auftragspaket anlegen, das den operativen Planungskontext trägt.",
            required_permissions=("planning.order.read", "planning.record.read", "planning.record.write"),
            source_basis=(
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="P-02",
                    module_key="planning",
                    evidence="The generated user manual places planning records and order setup in P-02.",
                ),
            ),
        ),
        _step(
            step_key="concrete_shifts",
            sequence=3,
            page_id="P-03",
            module_key="planning",
            purpose_en="Continue into Shift Planning for concrete shifts once the planning record exists.",
            purpose_de="Nach dem Planungsdatensatz in die Schichtplanung wechseln, um konkrete Schichten anzulegen.",
            required_permissions=("planning.shift.read", "planning.shift.write"),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Workflow Manifest",
                    page_id="P-03",
                    module_key="planning",
                    evidence="This workflow moves from the planning record into concrete shift planning in P-03.",
                ),
            ),
        ),
    ),
)

EMPLOYEE_CREATE = AssistantWorkflowSeed(
    workflow_key="employee_create",
    title_en="Create an employee file and operational readiness",
    title_de="Mitarbeiterakte und operative Einsatzfähigkeit anlegen",
    summary_en="Employee creation starts in the Employees workspace, then continues with qualifications, availability, and app-access readiness.",
    summary_de="Die Mitarbeiteranlage startet im Mitarbeiter-Workspace und wird mit Qualifikationen, Verfügbarkeit und App-Zugangsbereitschaft fortgesetzt.",
    intent_aliases_en=("create employee", "new employee", "employee file", "create employee file"),
    intent_aliases_de=("mitarbeiter anlegen", "neuen mitarbeiter anlegen", "mitarbeiterakte anlegen"),
    linked_page_ids=("E-01",),
    api_families=("employees",),
    steps=(
        _step(
            step_key="employee_file",
            sequence=1,
            page_id="E-01",
            module_key="employees",
            purpose_en="Open the employee create flow in the Employees workspace and create the operational employee file.",
            purpose_de="Den Anlegevorgang im Mitarbeiter-Workspace öffnen und die operative Mitarbeiterakte anlegen.",
            required_permissions=("employees.employee.read", "employees.employee.write"),
            source_basis=(
                _basis(
                    source_type="page_help_manifest",
                    source_name="Assistant Page Help Manifest",
                    page_id="E-01",
                    module_key="employees",
                    evidence="The verified E-01 page-help manifest includes the employees.create.open action and confirms that it opens the structured employee create form.",
                ),
            ),
        ),
        _step(
            step_key="qualifications_and_availability",
            sequence=2,
            page_id="E-01",
            module_key="employees",
            purpose_en="Complete qualifications and availability so planning can safely use the employee later.",
            purpose_de="Qualifikationen und Verfügbarkeit pflegen, damit die Planung den Mitarbeiter später sicher einsetzen kann.",
            required_permissions=("employees.employee.read",),
            source_basis=(
                _basis(
                    source_type="page_help_manifest",
                    source_name="Assistant Page Help Manifest",
                    page_id="E-01",
                    module_key="employees",
                    evidence="The verified E-01 manifest lists follow-up steps for qualifications and availability after employee creation.",
                ),
            ),
        ),
        _step(
            step_key="access_link",
            sequence=3,
            page_id="E-01",
            module_key="employees",
            purpose_en="Check the access link or employee self-service readiness if the employee must later receive released schedules in the app.",
            purpose_de="Zugangsverknüpfung oder Self-Service-Bereitschaft prüfen, wenn der Mitarbeiter später freigegebene Schichten in der App erhalten soll.",
            required_permissions=("employees.employee.write",),
            source_basis=(
                _basis(
                    source_type="page_help_manifest",
                    source_name="Assistant Page Help Manifest",
                    page_id="E-01",
                    module_key="employees",
                    evidence="The verified E-01 manifest includes a post-create step to check the app access link.",
                ),
            ),
        ),
    ),
)

EMPLOYEE_ASSIGN_TO_SHIFT = AssistantWorkflowSeed(
    workflow_key="employee_assign_to_shift",
    title_en="Assign an employee to a shift",
    title_de="Mitarbeiter einer Schicht zuweisen",
    summary_en="Employee assignment requires an existing employee, a concrete shift, and staffing-board validations before release and dispatch follow-up.",
    summary_de="Die Mitarbeiterzuweisung erfordert einen bestehenden Mitarbeiter, eine konkrete Schicht und Prüfungen im Staffing Board, bevor Freigabe und Disposition folgen.",
    intent_aliases_en=("assign employee to shift", "staff a shift", "put employee on shift"),
    intent_aliases_de=("mitarbeiter einer schicht zuweisen", "schicht besetzen", "mitarbeiter in schicht einplanen"),
    linked_page_ids=("E-01", "P-03", "P-04", "P-05"),
    api_families=("employees", "planning"),
    legacy_keys=("employee_assign_to_shift_workflow",),
    steps=(
        _step(
            step_key="employee_readiness",
            sequence=1,
            page_id="E-01",
            module_key="employees",
            purpose_en="Verify that the employee exists and is operationally ready before staffing the shift.",
            purpose_de="Vor der Besetzung der Schicht prüfen, ob der Mitarbeiter existiert und operativ einsatzbereit ist.",
            required_permissions=("employees.employee.read",),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Workflow Manifest",
                    page_id="E-01",
                    module_key="employees",
                    evidence="This workflow requires employee readiness before staffing.",
                ),
            ),
        ),
        _step(
            step_key="concrete_shift",
            sequence=2,
            page_id="P-03",
            module_key="planning",
            purpose_en="Verify that the concrete shift exists in Shift Planning and that the planning context is ready for staffing.",
            purpose_de="Prüfen, dass die konkrete Schicht in der Schichtplanung existiert und der Planungskontext für die Besetzung bereit ist.",
            required_permissions=("planning.shift.read",),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="P-03",
                    module_key="planning",
                    evidence="P-03 is the verified Shift Planning workspace.",
                ),
            ),
        ),
        _step(
            step_key="staffing_board_assignment",
            sequence=3,
            page_id="P-04",
            module_key="planning",
            purpose_en="Assign the employee in the Staffing Board and review assignment validations.",
            purpose_de="Den Mitarbeiter im Staffing Board zuweisen und die Zuordnungsprüfungen kontrollieren.",
            required_permissions=("planning.staffing.read", "planning.staffing.write"),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="P-04",
                    module_key="planning",
                    evidence="P-04 is the verified Staffing Board & Coverage workspace.",
                ),
            ),
        ),
        _step(
            step_key="dispatch_followup",
            sequence=4,
            page_id="P-05",
            module_key="planning",
            purpose_en="If app visibility or downstream release matters, continue into dispatch, outputs, and subcontractor-release follow-up.",
            purpose_de="Wenn App-Sichtbarkeit oder nachgelagerte Freigaben relevant sind, in Disposition, Outputs und Freigabe-Nachlauf wechseln.",
            required_permissions=("planning.staffing.read",),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Workflow Manifest",
                    page_id="P-05",
                    module_key="planning",
                    evidence="This workflow explicitly places release and dispatch follow-up after the staffing step.",
                ),
            ),
        ),
    ),
)

SHIFT_RELEASE_TO_EMPLOYEE_APP = AssistantWorkflowSeed(
    workflow_key="shift_release_to_employee_app",
    title_en="Release a shift to the employee app",
    title_de="Schicht für die Mitarbeiter-App freigeben",
    summary_en="Employee-app visibility depends on shift release state, staffing state, downstream dispatch checks, and employee self-service readiness.",
    summary_de="Die Sichtbarkeit in der Mitarbeiter-App hängt von Schichtfreigabe, Besetzungsstatus, Dispositionsprüfungen und der Self-Service-Bereitschaft des Mitarbeiters ab.",
    intent_aliases_en=("release shift to employee app", "make shift visible in app", "employee app shift visibility"),
    intent_aliases_de=("schicht für mitarbeiter-app freigeben", "schicht in app sichtbar machen", "mitarbeiter-app sichtbarkeit"),
    linked_page_ids=("P-03", "P-04", "P-05", "ES-01"),
    api_families=("planning", "employees", "employee_self_service"),
    legacy_keys=("shift_create_or_release",),
    steps=(
        _step(
            step_key="shift_release_state",
            sequence=1,
            page_id="P-03",
            module_key="planning",
            purpose_en="Verify the shift exists and is in a releaseable state.",
            purpose_de="Prüfen, dass die Schicht existiert und sich in einem freigabefähigen Zustand befindet.",
            required_permissions=("planning.shift.read",),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="P-03",
                    module_key="planning",
                    evidence="P-03 is the verified Shift Planning workspace for concrete shifts.",
                ),
            ),
        ),
        _step(
            step_key="assignment_visibility_state",
            sequence=2,
            page_id="P-04",
            module_key="planning",
            purpose_en="Verify that the assignment and staffing state allow employee visibility.",
            purpose_de="Prüfen, dass Zuordnung und Besetzungsstatus die Mitarbeitersichtbarkeit zulassen.",
            required_permissions=("planning.staffing.read",),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Workflow Manifest",
                    page_id="P-04",
                    module_key="planning",
                    evidence="The workflow places visibility dependency on staffing state before app release.",
                ),
            ),
        ),
        _step(
            step_key="dispatch_and_output_checks",
            sequence=3,
            page_id="P-05",
            module_key="planning",
            purpose_en="Review downstream dispatch and release follow-up when visibility still fails.",
            purpose_de="Nachgelagerte Dispositions- und Freigabeprüfungen kontrollieren, wenn die Sichtbarkeit weiterhin fehlschlägt.",
            required_permissions=("planning.staffing.read",),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="P-05",
                    module_key="planning",
                    evidence="P-05 is the verified dispatch, outputs, and subcontractor-release workspace.",
                ),
            ),
        ),
        _step(
            step_key="employee_self_service_ready",
            sequence=4,
            page_id="ES-01",
            module_key="employee_self_service",
            purpose_en="Verify that employee self-service or mobile access is ready, because a released shift is still not visible without employee access readiness.",
            purpose_de="Prüfen, dass Self-Service bzw. Mobile-Zugang des Mitarbeiters bereit ist, denn eine freigegebene Schicht bleibt ohne Zugangsbereitschaft unsichtbar.",
            required_permissions=("portal.employee.access",),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="ES-01",
                    module_key="employee_self_service",
                    evidence="ES-01 is the verified employee self-service portal reference used for employee access context.",
                ),
            ),
        ),
    ),
)

ACTUALS_BILLING_PAYROLL_CHAIN = AssistantWorkflowSeed(
    workflow_key="actuals_billing_payroll_chain",
    title_en="Move from field actuals into billing and payroll",
    title_de="Von Feldevidence zu Abrechnung und Payroll überleiten",
    summary_en="Field attendance and time evidence flow into finance actual records, approvals, customer billing, and payroll export without bypassing the finance actual bridge.",
    summary_de="Feldbezogene Anwesenheits- und Zeitevidence fließt in Finance-Actual-Records, Freigaben, Kundenabrechnung und Payroll-Export, ohne die Finance-Actual-Bridge zu umgehen.",
    intent_aliases_en=("billing and payroll chain", "actuals to billing", "timesheet to payroll", "invoice and payroll workflow"),
    intent_aliases_de=("abrechnung und payroll", "actuals zu abrechnung", "timesheet zu payroll", "feldevidence abrechnung payroll"),
    linked_page_ids=("FD-01", "FI-01", "FI-02", "FI-03"),
    api_families=("field_execution", "finance"),
    steps=(
        _step(
            step_key="field_evidence",
            sequence=1,
            page_id="FD-01",
            module_key="field_execution",
            purpose_en="Capture or review attendance and field evidence before finance derivation starts.",
            purpose_de="Anwesenheit und Feldevidence erfassen oder prüfen, bevor die finanzielle Ableitung beginnt.",
            required_permissions=("field.attendance.read", "field.time_capture.read"),
            source_basis=(
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="FD-01",
                    module_key="field_execution",
                    evidence="The implementation guidance preserves raw field evidence and separates it from finance-owned derivation.",
                ),
            ),
        ),
        _step(
            step_key="finance_actual_bridge",
            sequence=2,
            page_id="FI-01",
            module_key="finance",
            purpose_en="Derive or review finance actual records; do not bypass the finance actual bridge.",
            purpose_de="Finance-Actual-Records ableiten oder prüfen; die Finance-Actual-Bridge darf nicht umgangen werden.",
            required_permissions=("finance.actual.read", "finance.actual.write"),
            source_basis=(
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="FI-01",
                    module_key="finance",
                    evidence="The implementation rules explicitly state that payroll and billing must not bypass finance.actual_record.",
                ),
            ),
        ),
        _step(
            step_key="billing_release",
            sequence=3,
            page_id="FI-02",
            module_key="finance",
            purpose_en="Continue into billing release, timesheets, and invoice generation after actuals are ready.",
            purpose_de="Nach bereitstehenden Actuals in die Abrechnungsfreigabe, Timesheets und Rechnungserstellung wechseln.",
            required_permissions=("finance.billing.read", "finance.billing.write"),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="FI-02",
                    module_key="finance",
                    evidence="FI-02 is the verified Billing workspace.",
                ),
            ),
        ),
        _step(
            step_key="payroll_export",
            sequence=4,
            page_id="FI-03",
            module_key="finance",
            purpose_en="Use the Payroll workspace for payroll tariffs, export batches, and payroll release outputs.",
            purpose_de="Für Payroll-Tarife, Export-Batches und Payroll-Ausgaben den Payroll-Workspace verwenden.",
            required_permissions=("finance.payroll.read", "finance.payroll.export"),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="FI-03",
                    module_key="finance",
                    evidence="FI-03 is the verified Payroll workspace.",
                ),
            ),
        ),
    ),
)


CANONICAL_WORKFLOW_SEEDS: tuple[AssistantWorkflowSeed, ...] = (
    CUSTOMER_CREATE,
    CONTRACT_OR_DOCUMENT_REGISTER,
    CUSTOMER_ORDER_CREATE,
    CUSTOMER_PLAN_CREATE,
    EMPLOYEE_CREATE,
    EMPLOYEE_ASSIGN_TO_SHIFT,
    SHIFT_RELEASE_TO_EMPLOYEE_APP,
    ACTUALS_BILLING_PAYROLL_CHAIN,
)

WORKFLOW_HELP_SEEDS: dict[str, AssistantWorkflowSeed] = {
    seed.workflow_key: seed
    for seed in CANONICAL_WORKFLOW_SEEDS
}
for seed in CANONICAL_WORKFLOW_SEEDS:
    for legacy_key in seed.legacy_keys:
        WORKFLOW_HELP_SEEDS[legacy_key] = seed
WORKFLOW_HELP_SEEDS["contract_registration"] = CONTRACT_OR_DOCUMENT_REGISTER


def _infer_language_code(lowered: str) -> str | None:
    if any(token in lowered for token in (" wie ", " auftrag", " vertrag", " schicht", " mitarbeiter", " kunde")):
        return "de"
    if any(token in lowered for token in (" how ", " customer", " order", " shift", " contract", " employee")):
        return "en"
    return None


def _detect_by_heuristics(lowered: str) -> str | None:
    if _is_customer_plan_create(lowered):
        return "customer_plan_create"
    if _is_customer_order_create(lowered):
        return "customer_order_create"
    if _is_customer_create(lowered):
        return "customer_create"
    if _is_contract_registration(lowered):
        return "contract_or_document_register"
    if _is_employee_assign_to_shift(lowered):
        return "employee_assign_to_shift"
    if _is_shift_release_to_employee_app(lowered):
        return "shift_release_to_employee_app"
    if _is_actuals_billing_payroll_chain(lowered):
        return "actuals_billing_payroll_chain"
    if _is_employee_create(lowered):
        return "employee_create"
    return None


def _detect_by_alias_match(lowered: str) -> str | None:
    query_tokens = set(_tokenize(lowered))
    best_match: tuple[int, str] | None = None
    for seed in CANONICAL_WORKFLOW_SEEDS:
        for alias in (*seed.intent_aliases_en, *seed.intent_aliases_de):
            alias_lower = alias.casefold()
            alias_tokens = {token for token in _tokenize(alias_lower) if token not in ALIAS_STOPWORDS}
            if alias_lower in lowered and len(alias_tokens) >= 1:
                score = 100 + len(alias_tokens)
            else:
                overlap = len(query_tokens.intersection(alias_tokens))
                if overlap < 2:
                    continue
                score = overlap
            if best_match is None or score > best_match[0]:
                best_match = (score, seed.workflow_key)
    return best_match[1] if best_match is not None else None


def _is_employee_create(lowered: str) -> bool:
    if any(token in lowered for token in ("shift", "schicht", "شیفت", "شفت", "صیفت", "order", "auftrag", "سفارش", "پروژه")):
        return False
    return (
        ("employee" in lowered or "mitarbeiter" in lowered or "کارمند" in lowered)
        and any(token in lowered for token in ("create", "new", "anlegen", "erstellen", "ثبت", "بساز", "درست"))
    )


def _is_customer_create(lowered: str) -> bool:
    customer_terms = ("customer", "kunde", "kunden", "مشتری")
    create_terms = ("create", "new", "register", "anlegen", "erstellen", "erstelle", "ثبت", "بساز", "درست")
    plan_terms = ("plan", "planung", "planning", "planungssatz", "auftrag", "order", "پلن", "برنامه", "سفارش", "projekt")
    return (
        any(term in lowered for term in customer_terms)
        and any(term in lowered for term in create_terms)
        and not any(term in lowered for term in plan_terms)
    )


def _is_customer_order_create(lowered: str) -> bool:
    order_terms = ("order", "auftrag", "kundenauftrag", "سفارش", "projekt")
    create_terms = ("create", "new", "register", "anlegen", "erstellen", "erstelle", "ثبت", "بساز", "درست")
    return (
        any(term in lowered for term in order_terms)
        and any(term in lowered for term in create_terms)
    )


def _is_customer_plan_create(lowered: str) -> bool:
    customer_terms = ("customer", "kunde", "kunden", "مشتری")
    plan_terms = ("plan", "planung", "planning", "planning record", "planungsdatensatz", "پلن", "برنامه")
    create_terms = ("create", "new", "register", "anlegen", "erstellen", "erstelle", "ثبت", "بساز", "درست")
    return (
        any(term in lowered for term in customer_terms)
        and any(term in lowered for term in plan_terms)
        and any(term in lowered for term in create_terms)
    )


def _is_employee_assign_to_shift(lowered: str) -> bool:
    employee_terms = ("employee", "mitarbeiter", "کارمند")
    shift_terms = ("shift", "schicht", "شیفت", "شفت", "صیفت")
    assign_terms = ("assign", "assgin", "zuweisen", "zuordnung", "einplanen", "besetzen", "اختصاص", "تخصیص", "نسبت", "نصبت")
    return any(term in lowered for term in employee_terms) and any(term in lowered for term in shift_terms) and any(
        term in lowered for term in assign_terms
    )


def _is_contract_registration(lowered: str) -> bool:
    contract_terms = (
        "contract",
        "agreement",
        "vertrag",
        "verträge",
        "vereinbarung",
        "document",
        "dokument",
        "attachment",
        "anhang",
        "datei",
        "قرارداد",
        "سند قرارداد",
        "سند",
    )
    create_terms = (
        "create",
        "new",
        "register",
        "upload",
        "add",
        "link",
        "registriere",
        "registrieren",
        "anlegen",
        "erstellen",
        "erstelle",
        "hochladen",
        "verknüpfen",
        "ثبت",
        "بساز",
        "درست",
    )
    return any(term in lowered for term in contract_terms) and any(term in lowered for term in create_terms)


def _is_shift_release_to_employee_app(lowered: str) -> bool:
    shift_terms = ("shift", "schicht", "شیفت", "شفت", "صیفت")
    release_terms = (
        "release",
        "freigabe",
        "freigeben",
        "sichtbar",
        "visible",
        "employee app",
        "mitarbeiter-app",
        "app",
        "portal",
        "self-service",
        "self service",
    )
    return any(term in lowered for term in shift_terms) and any(term in lowered for term in release_terms)


def _is_actuals_billing_payroll_chain(lowered: str) -> bool:
    actuals_terms = ("actual", "actuals", "attendance", "timesheet", "payroll", "billing", "invoice", "abrechnung", "lohn", "faktura")
    return sum(1 for term in actuals_terms if term in lowered) >= 2


def _tokenize(value: str) -> list[str]:
    return TOKEN_RE.findall(value.casefold())
