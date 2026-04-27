"""Curated expert knowledge facts for core SicherPlan workflows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantExpertKnowledgeSourceBasisSeed:
    source_type: str
    source_name: str
    page_id: str | None
    module_key: str | None
    evidence: str


@dataclass(frozen=True)
class AssistantExpertKnowledgeFactSeed:
    fact_key: str
    text_en: str
    text_de: str
    page_ids: tuple[str, ...] = ()
    module_keys: tuple[str, ...] = ()
    source_basis: tuple[AssistantExpertKnowledgeSourceBasisSeed, ...] = ()


@dataclass(frozen=True)
class AssistantExpertKnowledgeSeed:
    knowledge_key: str
    title_en: str
    title_de: str
    summary_en: str
    summary_de: str
    aliases_en: tuple[str, ...]
    aliases_de: tuple[str, ...]
    linked_page_ids: tuple[str, ...]
    module_keys: tuple[str, ...]
    facts: tuple[AssistantExpertKnowledgeFactSeed, ...]
    source_basis: tuple[AssistantExpertKnowledgeSourceBasisSeed, ...] = ()


def _basis(
    *,
    source_type: str,
    source_name: str,
    page_id: str | None,
    module_key: str | None,
    evidence: str,
) -> AssistantExpertKnowledgeSourceBasisSeed:
    return AssistantExpertKnowledgeSourceBasisSeed(
        source_type=source_type,
        source_name=source_name,
        page_id=page_id,
        module_key=module_key,
        evidence=evidence,
    )


def _fact(
    *,
    fact_key: str,
    text_en: str,
    text_de: str,
    page_ids: tuple[str, ...] = (),
    module_keys: tuple[str, ...] = (),
    source_basis: tuple[AssistantExpertKnowledgeSourceBasisSeed, ...] = (),
) -> AssistantExpertKnowledgeFactSeed:
    return AssistantExpertKnowledgeFactSeed(
        fact_key=fact_key,
        text_en=text_en,
        text_de=text_de,
        page_ids=page_ids,
        module_keys=module_keys,
        source_basis=source_basis,
    )


PRODUCT_OVERVIEW = AssistantExpertKnowledgeSeed(
    knowledge_key="product_overview",
    title_en="SicherPlan product overview",
    title_de="SicherPlan Produktüberblick",
    summary_en="SicherPlan is a multi-tenant security operations platform that connects commercial setup, workforce readiness, planning, field execution, finance, reporting, and scoped portals.",
    summary_de="SicherPlan ist eine mandantenfähige Sicherheitsoperations-Plattform, die kaufmännische Einrichtung, Personalbereitschaft, Planung, Feldausführung, Finance, Reporting und bereichsbezogene Portale verbindet.",
    aliases_en=(
        "what does this software do",
        "what is sicherplan",
        "platform overview",
        "security operations platform",
    ),
    aliases_de=(
        "was macht diese software",
        "was ist sicherplan",
        "plattformüberblick",
        "sicherheitsoperations plattform",
    ),
    linked_page_ids=("C-01", "E-01", "S-01", "P-02", "P-03", "P-04", "FD-01", "FI-01", "REP-01"),
    module_keys=("customers", "employees", "subcontractors", "planning", "field_execution", "finance", "reporting"),
    facts=(
        _fact(
            fact_key="tenant_model",
            text_en="One prime security company is modeled as one tenant, while customers, employees, subcontractors, and portal actors stay scoped inside that tenant instead of becoming separate tenants.",
            text_de="Eine primäre Sicherheitsfirma wird als ein Mandant modelliert; Kunden, Mitarbeiter, Subunternehmer und Portalnutzer bleiben innerhalb dieses Mandanten bereichsbezogen statt eigene Mandanten zu werden.",
            source_basis=(
                _basis(
                    source_type="operational_handbook",
                    source_name="Generated Operational Handbook",
                    page_id=None,
                    module_key="platform",
                    evidence="The handbook describes tenant-scoped operations with customers, employees, and subcontractors living inside one tenant boundary.",
                ),
            ),
        ),
        _fact(
            fact_key="platform_scope",
            text_en="The platform links customer management, workforce readiness, subcontractors, orders, planning records, shifts, staffing, dispatch, watchbooks, patrol control, time capture, actual reconciliation, payroll support, billing, reporting, and portals.",
            text_de="Die Plattform verbindet Kundenverwaltung, Personalbereitschaft, Subunternehmer, Aufträge, Planungsdatensätze, Schichten, Staffing, Disposition, Wachbücher, Streifenkontrolle, Zeiterfassung, Ist-Abgleich, Payroll-Unterstützung, Abrechnung, Reporting und Portale.",
            page_ids=("C-01", "E-01", "S-01", "P-02", "P-03", "P-04", "FD-01", "FI-01"),
            module_keys=("customers", "employees", "subcontractors", "planning", "field_execution", "finance"),
            source_basis=(
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id=None,
                    module_key="platform",
                    evidence="The user manual overview enumerates customer, workforce, planning, field, and finance workspaces as one operating model.",
                ),
                _basis(
                    source_type="role_page_coverage",
                    source_name="Assistant Role Page Coverage Map",
                    page_id=None,
                    module_key="platform",
                    evidence="The role/page coverage map shows these pages and workspaces as the operational surface available to tenant-scoped actors.",
                ),
            ),
        ),
        _fact(
            fact_key="governance",
            text_en="SicherPlan is role-aware, tenant-aware, permission-aware, and audit-oriented. Visibility and write rights stay module-owned and least-privilege by default.",
            text_de="SicherPlan ist rollenbasiert, mandantenbasiert, berechtigungsbasiert und audit-orientiert. Sichtbarkeit und Schreibrechte bleiben modulverantwortet und standardmäßig minimal berechtigt.",
            source_basis=(
                _basis(
                    source_type="security_doc",
                    source_name="AI Assistant Security",
                    page_id=None,
                    module_key="platform",
                    evidence="The security guidance emphasizes tenant isolation, scoped portal visibility, least privilege, and audit-safe handling of evidence.",
                ),
            ),
        ),
        _fact(
            fact_key="document_model",
            text_en="Documents, generated outputs, and uploads are centralized in platform services, but business meaning stays with the owning customer, planning, subcontractor, finance, or field workflow.",
            text_de="Dokumente, generierte Ausgaben und Uploads werden zentral in Plattformdiensten gehalten, während die fachliche Bedeutung beim jeweils besitzenden Kunden-, Planungs-, Subunternehmer-, Finance- oder Feldeinsatzprozess bleibt.",
            page_ids=("PS-01", "C-01", "P-02", "S-01", "FI-01"),
            module_keys=("platform_services", "customers", "planning", "subcontractors", "finance"),
            source_basis=(
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="The implementation model assigns centralized document ownership to platform services while business meaning remains with the owning bounded context.",
                ),
            ),
        ),
    ),
)

CUSTOMER_CREATE_KNOWLEDGE = AssistantExpertKnowledgeSeed(
    knowledge_key="customer_create",
    title_en="Create and govern a customer master",
    title_de="Kundenstammdaten anlegen und führen",
    summary_en="Customer setup starts in the Customers workspace and covers customer identity, contacts, addresses, billing profile, invoice parties, pricing, history, privacy, and visibility controls.",
    summary_de="Die Kundenanlage startet im Kunden-Workspace und umfasst Kundenidentität, Kontakte, Adressen, Abrechnungsprofil, Rechnungsempfänger, Preislogik, Historie, Datenschutz und Sichtbarkeitsregeln.",
    aliases_en=("create customer", "register customer", "customer master", "billing profile", "invoice party", "rate card"),
    aliases_de=("kunde anlegen", "kunden registrieren", "kundenstammdaten", "kundenverwaltung", "rechnungsprofil", "ansprechpartner", "adresse"),
    linked_page_ids=("C-01",),
    module_keys=("customers",),
    facts=(
        _fact(
            fact_key="customer_master_fields",
            text_en="The customer master typically includes customer number, lifecycle status, legal name, display name, classification, ranking, and the tenant-scoped commercial identity of the customer.",
            text_de="Der Kundenstamm umfasst typischerweise Kundennummer, Lebenszyklusstatus, rechtlichen Namen, Anzeigenamen, Klassifizierung, Ranking und die mandantenbezogene kaufmännische Identität des Kunden.",
            page_ids=("C-01",),
            module_keys=("customers",),
            source_basis=(
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The user manual marks C-01 as the starting point for customer master work and customer-scoped history.",
                ),
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The implementation data model assigns customer master and history ownership to the Customers context.",
                ),
            ),
        ),
        _fact(
            fact_key="contacts_and_addresses",
            text_en="Customer setup covers contacts, addresses, default branch or mandate alignment, and customer-specific communication details used by operations and finance.",
            text_de="Zur Kundenanlage gehören Ansprechpartner, Adressen, die Zuordnung zu Standard-Niederlassung oder Mandat und kundenspezifische Kommunikationsdaten für Operations und Finance.",
            page_ids=("C-01",),
            module_keys=("customers",),
            source_basis=(
                _basis(
                    source_type="page_help_manifest",
                    source_name="Assistant Page Help Manifest",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The C-01 page-help manifest includes search, customer list, identity, contacts, addresses, and customer detail domain sections.",
                ),
            ),
        ),
        _fact(
            fact_key="billing_and_invoice_parties",
            text_en="Commercial customer setup includes billing profile, invoice parties, rate cards, surcharge rules, and customer-specific pricing logic before downstream order and billing flows rely on the record.",
            text_de="Zur kaufmännischen Einrichtung gehören Abrechnungsprofil, Rechnungsempfänger, Preislisten, Zuschlagsregeln und kundenspezifische Preislogik, bevor nachgelagerte Auftrags- und Abrechnungsprozesse auf den Datensatz zugreifen.",
            page_ids=("C-01",),
            module_keys=("customers",),
            source_basis=(
                _basis(
                    source_type="operational_handbook",
                    source_name="Generated Operational Handbook",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The handbook ties customer setup to downstream planning and billing preparation, including commercial setup before release.",
                ),
            ),
        ),
        _fact(
            fact_key="history_privacy_visibility",
            text_en="Customer history, attachments, portal privacy, login history, and customer-specific employee visibility blocks remain customer-scoped and should be reviewed before exposing portal data.",
            text_de="Kundenhistorie, Anhänge, Portal-Datenschutz, Login-Historie und kundenspezifische Mitarbeitersperren bleiben kundenspezifisch und sollten vor einer Portalfreigabe geprüft werden.",
            page_ids=("C-01", "PS-01"),
            module_keys=("customers", "platform_services"),
            source_basis=(
                _basis(
                    source_type="security_doc",
                    source_name="AI Assistant Security",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The security guidance requires least-privilege customer-facing visibility and default protection of personal names and sensitive data.",
                ),
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="Document and generated output handling stays centralized while customer meaning remains in the owning customer context.",
                ),
            ),
        ),
        _fact(
            fact_key="import_export_vcard",
            text_en="Customer administration can include import, export, vCard-like contact exchange, and document-backed attachments, but the create action still depends on customer write permissions.",
            text_de="Zur Kundenverwaltung können Import, Export, vCard-artiger Kontaktaustausch und dokumentgestützte Anhänge gehören; der Anlegevorgang setzt dennoch Schreibrechte im Kundenkontext voraus.",
            page_ids=("C-01",),
            module_keys=("customers",),
            source_basis=(
                _basis(
                    source_type="page_help_manifest",
                    source_name="Assistant Page Help Manifest",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The verified C-01 manifest includes customer export and create actions in the list header.",
                ),
            ),
        ),
    ),
)

CUSTOMER_ORDER_CREATE_KNOWLEDGE = AssistantExpertKnowledgeSeed(
    knowledge_key="customer_order_create",
    title_en="Create a customer order",
    title_de="Kundenauftrag anlegen",
    summary_en="A customer order belongs to an existing customer and captures commercial and operational demand before staffing or release begins.",
    summary_de="Ein Kundenauftrag gehört zu einem bestehenden Kunden und erfasst kaufmännischen sowie operativen Bedarf, bevor Staffing oder Freigabe beginnen.",
    aliases_en=("create order", "customer order", "new order", "create customer order"),
    aliases_de=("auftrag erstellen", "kundenauftrag", "neuen auftrag anlegen", "auftrag für kunden"),
    linked_page_ids=("C-01", "P-02"),
    module_keys=("customers", "planning"),
    facts=(
        _fact(
            fact_key="customer_precondition",
            text_en="The customer should exist first, because the order or project package is created in customer context and later drives planning, staffing, and billing.",
            text_de="Der Kunde sollte zuerst existieren, weil Auftrag oder Projektpaket im Kundenkontext angelegt werden und später Planung, Staffing und Abrechnung steuern.",
            page_ids=("C-01", "P-02"),
            module_keys=("customers", "planning"),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Assistant Workflow Help",
                    page_id="C-01",
                    module_key="customers",
                    evidence="The customer order workflow starts with customer context before order creation in P-02.",
                ),
            ),
        ),
        _fact(
            fact_key="order_scope",
            text_en="The order captures requirement type, service category, security concept, date window, sites or routes, equipment lines, requirement lines, notes, and attachments for the customer job package.",
            text_de="Der Auftrag erfasst Bedarfsart, Leistungskategorie, Sicherheitskonzept, Datumsfenster, Standorte oder Routen, Equipment-Zeilen, Anforderungszeilen, Hinweise und Anhänge für das Kundenauftragspaket.",
            page_ids=("P-02",),
            module_keys=("planning",),
            source_basis=(
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="P-02",
                    module_key="planning",
                    evidence="The user manual identifies P-02 as the workspace for customer orders, planning records, and document packages.",
                ),
            ),
        ),
        _fact(
            fact_key="document_package",
            text_en="Order setup may include linked or uploaded documents, and those attachments stay document-backed rather than becoming ad hoc contract data in a fake standalone module.",
            text_de="Zur Auftragseinrichtung können verknüpfte oder hochgeladene Dokumente gehören; diese Anhänge bleiben dokumentgestützt und werden nicht zu Ad-hoc-Vertragsdaten in einem erfundenen Modul.",
            page_ids=("P-02", "PS-01"),
            module_keys=("planning", "platform_services"),
            source_basis=(
                _basis(
                    source_type="operational_handbook",
                    source_name="Generated Operational Handbook",
                    page_id="P-02",
                    module_key="planning",
                    evidence="The operational handbook states that planning orders and planning records include documented planning packages and attachments.",
                ),
            ),
        ),
    ),
)

CUSTOMER_PLAN_CREATE_KNOWLEDGE = AssistantExpertKnowledgeSeed(
    knowledge_key="customer_plan_create",
    title_en="Create a customer planning package",
    title_de="Kundenplanung anlegen",
    summary_en="Customer planning continues from customer and order context into a planning record and then into concrete shift preparation.",
    summary_de="Die Kundenplanung führt vom Kunden- und Auftragskontext in einen Planungsdatensatz und anschließend in die konkrete Schichtvorbereitung.",
    aliases_en=("create customer plan", "customer planning", "create planning package", "plan customer shifts"),
    aliases_de=("kundenplanung anlegen", "planung für kunden", "planungsdatensatz", "dienstplanung für kunden"),
    linked_page_ids=("C-01", "P-02", "P-03"),
    module_keys=("customers", "planning"),
    facts=(
        _fact(
            fact_key="planning_record_context",
            text_en="A planning package stays under customer and order context. It becomes the planning record that carries demand, documents, setup details, and later shift planning context.",
            text_de="Ein Planungspaket bleibt unter Kunden- und Auftragskontext. Es wird zum Planungsdatensatz, der Bedarf, Dokumente, Einrichtungsdetails und später den Kontext für die Schichtplanung trägt.",
            page_ids=("C-01", "P-02"),
            module_keys=("customers", "planning"),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Assistant Workflow Help",
                    page_id="P-02",
                    module_key="planning",
                    evidence="The customer plan workflow places the planning record in P-02 between customer context and concrete shifts.",
                ),
            ),
        ),
        _fact(
            fact_key="planning_setup",
            text_en="The planning record can capture customer-dependent setup such as sites, routes, timezone details, address options, planning documents, and structured notes before the shift layer is generated.",
            text_de="Der Planungsdatensatz kann kundenabhängige Einrichtung wie Standorte, Routen, Zeitzonendetails, Adressoptionen, Planungsdokumente und strukturierte Hinweise aufnehmen, bevor die Schichtschicht erzeugt wird.",
            page_ids=("P-02",),
            module_keys=("planning",),
            source_basis=(
                _basis(
                    source_type="page_help_manifest",
                    source_name="Assistant Page Help Manifest",
                    page_id="P-02",
                    module_key="planning",
                    evidence="The P-02 manifest includes planning record overview, documents, address creation, and customer order workspace follow-up sections.",
                ),
            ),
        ),
        _fact(
            fact_key="shift_planning_transition",
            text_en="Concrete shift planning follows only after the planning record exists. Staffing and assignment follow after concrete shifts or demand groups exist.",
            text_de="Die konkrete Schichtplanung folgt erst, nachdem der Planungsdatensatz existiert. Staffing und Zuweisung folgen erst, wenn konkrete Schichten oder Bedarfsgruppen vorhanden sind.",
            page_ids=("P-03", "P-04"),
            module_keys=("planning",),
            source_basis=(
                _basis(
                    source_type="user_manual",
                    source_name="Generated User Manual",
                    page_id="P-03",
                    module_key="planning",
                    evidence="The user manual and workflow summaries place concrete shift work in P-03 and staffing after that in P-04.",
                ),
            ),
        ),
    ),
)

PLANNING_RECORD_CREATE_KNOWLEDGE = AssistantExpertKnowledgeSeed(
    knowledge_key="planning_record_create",
    title_en="Create a planning record under an order",
    title_de="Planungsdatensatz unter einem Auftrag anlegen",
    summary_en="Planning-record creation is the operational bridge between customer order setup and detailed shift planning.",
    summary_de="Die Anlage eines Planungsdatensatzes ist die operative Brücke zwischen Kundenauftrag und detaillierter Schichtplanung.",
    aliases_en=("planning record", "create planning record", "planning package", "operational planning record"),
    aliases_de=("planungsdatensatz", "planungsstand anlegen", "planungspaket", "einsatzplanung"),
    linked_page_ids=("P-02", "P-03"),
    module_keys=("planning",),
    facts=(
        _fact(
            fact_key="record_under_order",
            text_en="The planning record is created under an existing order or planning package and becomes the owner of downstream shift preparation, notes, and attachments.",
            text_de="Der Planungsdatensatz wird unter einem bestehenden Auftrag oder Planungspaket angelegt und wird zum Träger der nachgelagerten Schichtvorbereitung, Hinweise und Anhänge.",
            page_ids=("P-02",),
            module_keys=("planning",),
            source_basis=(
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="P-02",
                    module_key="planning",
                    evidence="Planning owns orders, planning records, shifts, staffing, releases, and document packages linked to planning context.",
                ),
            ),
        ),
        _fact(
            fact_key="handoff_to_shift_planning",
            text_en="Once the planning record exists, the next concrete step is shift planning rather than direct staffing.",
            text_de="Sobald der Planungsdatensatz existiert, ist der nächste konkrete Schritt die Schichtplanung und nicht direkt das Staffing.",
            page_ids=("P-03", "P-04"),
            module_keys=("planning",),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Assistant Workflow Help",
                    page_id="P-03",
                    module_key="planning",
                    evidence="Workflow help moves from planning record setup into P-03 before assignment in P-04.",
                ),
            ),
        ),
    ),
)

CONTRACT_OR_DOCUMENT_REGISTER_KNOWLEDGE = AssistantExpertKnowledgeSeed(
    knowledge_key="contract_or_document_register",
    title_en="Register a contract or document in the right business context",
    title_de="Vertrag oder Dokument im richtigen Fachkontext registrieren",
    summary_en="Contract questions are ambiguity-aware and document-centered. The assistant should distinguish customer, order, subcontractor, and generic document contexts instead of inventing a contract module.",
    summary_de="Vertragsfragen sind mehrdeutig und dokumentenzentriert. Der Assistent soll zwischen Kunden-, Auftrags-, Subunternehmer- und generischem Dokumentkontext unterscheiden, statt ein Vertragsmodul zu erfinden.",
    aliases_en=("contract", "agreement", "document", "attachment", "upload", "link document"),
    aliases_de=("vertrag", "vertragsdokument", "dokument", "anhang", "hochladen", "verknüpfen"),
    linked_page_ids=("PS-01", "C-01", "P-02", "S-01"),
    module_keys=("platform_services", "customers", "planning", "subcontractors"),
    facts=(
        _fact(
            fact_key="no_standalone_contract_module",
            text_en="A standalone contract module is not verified. Contract-like artifacts are handled as documents or attachments linked to customer, planning, subcontractor, or other owning business context.",
            text_de="Ein eigenständiges Vertragsmodul ist nicht verifiziert. Vertragsähnliche Artefakte werden als Dokumente oder Anhänge behandelt, die an Kunden-, Planungs-, Subunternehmer- oder andere besitzende Fachkontexte gebunden sind.",
            page_ids=("PS-01", "C-01", "P-02", "S-01"),
            module_keys=("platform_services", "customers", "planning", "subcontractors"),
            source_basis=(
                _basis(
                    source_type="implementation_data_model",
                    source_name="Generated Implementation Data Model",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="The generated implementation model says contract-like content should be grounded as document ownership plus business context rather than a fake standalone contract table or module.",
                ),
            ),
        ),
        _fact(
            fact_key="platform_services_document_workflows",
            text_en="Platform Services PS-01 is the safe shared workspace for document create, version, upload, link, and download workflows when the subtype is still unclear.",
            text_de="Platform Services PS-01 ist der sichere gemeinsame Workspace für Dokumentanlage, Versionierung, Upload, Verknüpfung und Download, wenn der Untertyp noch unklar ist.",
            page_ids=("PS-01",),
            module_keys=("platform_services",),
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
                    evidence="The user manual calls PS-01 the safe shared reference for documents and contract-like uploads when the subtype is unclear.",
                ),
            ),
        ),
        _fact(
            fact_key="clarification_targets",
            text_en="If the user only says contract, ask whether they mean a customer contract, order or project attachment, subcontractor agreement, or generic document upload before suggesting an exact page.",
            text_de="Wenn der Nutzer nur Vertrag sagt, sollte geklärt werden, ob ein Kundenvertrag, ein Auftrags- oder Projektanhang, eine Subunternehmervereinbarung oder ein generischer Dokumentenupload gemeint ist, bevor eine konkrete Seite empfohlen wird.",
            page_ids=("PS-01", "C-01", "P-02", "S-01"),
            module_keys=("platform_services", "customers", "planning", "subcontractors"),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Assistant Workflow Help",
                    page_id="PS-01",
                    module_key="platform_services",
                    evidence="The contract workflow manifest explicitly requires targeted clarification before page guidance.",
                ),
            ),
        ),
    ),
)

EMPLOYEE_ASSIGN_TO_SHIFT_KNOWLEDGE = AssistantExpertKnowledgeSeed(
    knowledge_key="employee_assign_to_shift",
    title_en="Assign an employee to a shift",
    title_de="Mitarbeiter einer Schicht zuweisen",
    summary_en="Assignment requires employee readiness, concrete shifts, staffing validations, and release follow-up for app visibility.",
    summary_de="Die Zuweisung erfordert Mitarbeiterbereitschaft, konkrete Schichten, Staffing-Prüfungen und Freigabe-Nachlauf für die App-Sichtbarkeit.",
    aliases_en=("assign employee to shift", "staff a shift", "put employee on shift"),
    aliases_de=("mitarbeiter einer schicht zuweisen", "schicht besetzen", "mitarbeiter einplanen"),
    linked_page_ids=("E-01", "P-03", "P-04", "P-05", "ES-01"),
    module_keys=("employees", "planning", "employee_self_service"),
    facts=(
        _fact(
            fact_key="employee_readiness",
            text_en="The employee must exist and be active, and readiness can depend on qualifications, availability, absences, documents, and mobile access state before assignment should proceed.",
            text_de="Der Mitarbeiter muss existieren und aktiv sein; die Einsatzbereitschaft kann von Qualifikationen, Verfügbarkeit, Abwesenheiten, Dokumenten und Mobile-Zugang abhängen, bevor die Zuweisung fortgesetzt werden sollte.",
            page_ids=("E-01",),
            module_keys=("employees",),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Assistant Workflow Help",
                    page_id="E-01",
                    module_key="employees",
                    evidence="Workflow help places employee readiness ahead of staffing.",
                ),
            ),
        ),
        _fact(
            fact_key="shift_and_staffing",
            text_en="The shift must already exist under a shift plan. Staffing happens after concrete shifts or demand groups exist, and the staffing board is the assignment workspace.",
            text_de="Die Schicht muss bereits unter einem Schichtplan existieren. Staffing erfolgt erst, wenn konkrete Schichten oder Bedarfsgruppen vorhanden sind, und das Staffing Board ist der Zuweisungs-Workspace.",
            page_ids=("P-03", "P-04"),
            module_keys=("planning",),
            source_basis=(
                _basis(
                    source_type="page_route_catalog",
                    source_name="Assistant Page Route Catalog",
                    page_id="P-03",
                    module_key="planning",
                    evidence="P-03 is the verified Shift Planning workspace, and P-04 is the verified Staffing Board & Coverage workspace.",
                ),
            ),
        ),
        _fact(
            fact_key="assignment_validations",
            text_en="Assignment validations can include qualification mismatch, missing document, customer block, double booking, rest period, and minimum staffing or coverage rules.",
            text_de="Zuordnungsprüfungen können Qualifikationskonflikt, fehlende Dokumente, Kundensperre, Doppelbuchung, Ruhezeit und Mindestbesetzungs- oder Deckungsregeln umfassen.",
            page_ids=("P-04",),
            module_keys=("planning",),
            source_basis=(
                _basis(
                    source_type="operational_handbook",
                    source_name="Generated Operational Handbook",
                    page_id="P-04",
                    module_key="planning",
                    evidence="The operational workflow summaries and diagnostics reference validation checks before assignment and release follow-up.",
                ),
            ),
        ),
        _fact(
            fact_key="release_and_app_visibility",
            text_en="Release and dispatch follow-up control whether the assigned shift becomes visible in the employee app; employee self-service readiness still matters after staffing.",
            text_de="Freigabe und Dispositions-Nachlauf steuern, ob die zugewiesene Schicht in der Mitarbeiter-App sichtbar wird; die Bereitschaft des Self-Service-Zugangs bleibt auch nach dem Staffing relevant.",
            page_ids=("P-05", "ES-01"),
            module_keys=("planning", "employee_self_service"),
            source_basis=(
                _basis(
                    source_type="workflow_help",
                    source_name="Assistant Workflow Help",
                    page_id="P-05",
                    module_key="planning",
                    evidence="Workflow help places dispatch follow-up and employee self-service readiness after the staffing step for app visibility.",
                ),
            ),
        ),
    ),
)


EXPERT_KNOWLEDGE_PACKS: tuple[AssistantExpertKnowledgeSeed, ...] = (
    PRODUCT_OVERVIEW,
    CUSTOMER_CREATE_KNOWLEDGE,
    CUSTOMER_ORDER_CREATE_KNOWLEDGE,
    CUSTOMER_PLAN_CREATE_KNOWLEDGE,
    PLANNING_RECORD_CREATE_KNOWLEDGE,
    CONTRACT_OR_DOCUMENT_REGISTER_KNOWLEDGE,
    EMPLOYEE_ASSIGN_TO_SHIFT_KNOWLEDGE,
)

EXPERT_KNOWLEDGE_PACK_BY_KEY = {item.knowledge_key: item for item in EXPERT_KNOWLEDGE_PACKS}


def render_expert_knowledge_pack_markdown() -> str:
    lines = [
        "# SicherPlan Expert Knowledge Pack",
        "",
        "This generated source contains structured EN/DE facts for core SicherPlan workflows and platform understanding.",
        "It is retrieval context, not a bank of final runtime answers.",
        "",
    ]
    for item in EXPERT_KNOWLEDGE_PACKS:
        lines.append(f"## {item.title_en} ({item.knowledge_key})")
        lines.append("")
        lines.append(f"- title_de: {item.title_de}")
        lines.append(f"- summary_en: {item.summary_en}")
        lines.append(f"- summary_de: {item.summary_de}")
        lines.append(f"- aliases_en: {', '.join(item.aliases_en)}")
        lines.append(f"- aliases_de: {', '.join(item.aliases_de)}")
        lines.append(f"- linked_page_ids: {', '.join(item.linked_page_ids) or 'none'}")
        lines.append(f"- module_keys: {', '.join(item.module_keys) or 'none'}")
        if item.source_basis:
            lines.append("- source_basis:")
            for basis in item.source_basis:
                lines.append(
                    f"  - {basis.source_type} / {basis.source_name} / {basis.page_id or 'none'} / {basis.module_key or 'none'}: {basis.evidence}"
                )
        lines.append("")
        lines.append("### Facts")
        lines.append("")
        for fact in item.facts:
            lines.append(f"- fact_key: {fact.fact_key}")
            lines.append(f"  text_en: {fact.text_en}")
            lines.append(f"  text_de: {fact.text_de}")
            lines.append(f"  page_ids: {', '.join(fact.page_ids) or 'none'}")
            lines.append(f"  module_keys: {', '.join(fact.module_keys) or 'none'}")
            if fact.source_basis:
                lines.append("  source_basis:")
                for basis in fact.source_basis:
                    lines.append(
                        f"    - {basis.source_type} / {basis.source_name} / {basis.page_id or 'none'} / {basis.module_key or 'none'}: {basis.evidence}"
                    )
        lines.append("")
    return "\n".join(lines)
