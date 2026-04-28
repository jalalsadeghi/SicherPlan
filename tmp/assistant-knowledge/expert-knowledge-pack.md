# SicherPlan Expert Knowledge Pack

This generated source contains structured EN/DE facts for core SicherPlan workflows and platform understanding.
It is retrieval context, not a bank of final runtime answers.

## SicherPlan product overview (product_overview)

- title_de: SicherPlan Produktüberblick
- summary_en: SicherPlan is a multi-tenant security operations platform that connects commercial setup, workforce readiness, planning, field execution, finance, reporting, and scoped portals.
- summary_de: SicherPlan ist eine mandantenfähige Sicherheitsoperations-Plattform, die kaufmännische Einrichtung, Personalbereitschaft, Planung, Feldausführung, Finance, Reporting und bereichsbezogene Portale verbindet.
- aliases_en: what does this software do, what is sicherplan, platform overview, security operations platform
- aliases_de: was macht diese software, was ist sicherplan, plattformüberblick, sicherheitsoperations plattform
- linked_page_ids: C-01, E-01, S-01, P-02, P-03, P-04, FD-01, FI-01, REP-01
- module_keys: customers, employees, subcontractors, planning, field_execution, finance, reporting

### Facts

- fact_key: tenant_model
  text_en: One prime security company is modeled as one tenant, while customers, employees, subcontractors, and portal actors stay scoped inside that tenant instead of becoming separate tenants.
  text_de: Eine primäre Sicherheitsfirma wird als ein Mandant modelliert; Kunden, Mitarbeiter, Subunternehmer und Portalnutzer bleiben innerhalb dieses Mandanten bereichsbezogen statt eigene Mandanten zu werden.
  page_ids: none
  module_keys: none
  source_basis:
    - operational_handbook / Generated Operational Handbook / none / platform: The handbook describes tenant-scoped operations with customers, employees, and subcontractors living inside one tenant boundary.
- fact_key: platform_scope
  text_en: The platform links customer management, workforce readiness, subcontractors, orders, planning records, shifts, staffing, dispatch, watchbooks, patrol control, time capture, actual reconciliation, payroll support, billing, reporting, and portals.
  text_de: Die Plattform verbindet Kundenverwaltung, Personalbereitschaft, Subunternehmer, Aufträge, Planungsdatensätze, Schichten, Staffing, Disposition, Wachbücher, Streifenkontrolle, Zeiterfassung, Ist-Abgleich, Payroll-Unterstützung, Abrechnung, Reporting und Portale.
  page_ids: C-01, E-01, S-01, P-02, P-03, P-04, FD-01, FI-01
  module_keys: customers, employees, subcontractors, planning, field_execution, finance
  source_basis:
    - user_manual / Generated User Manual / none / platform: The user manual overview enumerates customer, workforce, planning, field, and finance workspaces as one operating model.
    - role_page_coverage / Assistant Role Page Coverage Map / none / platform: The role/page coverage map shows these pages and workspaces as the operational surface available to tenant-scoped actors.
- fact_key: governance
  text_en: SicherPlan is role-aware, tenant-aware, permission-aware, and audit-oriented. Visibility and write rights stay module-owned and least-privilege by default.
  text_de: SicherPlan ist rollenbasiert, mandantenbasiert, berechtigungsbasiert und audit-orientiert. Sichtbarkeit und Schreibrechte bleiben modulverantwortet und standardmäßig minimal berechtigt.
  page_ids: none
  module_keys: none
  source_basis:
    - security_doc / AI Assistant Security / none / platform: The security guidance emphasizes tenant isolation, scoped portal visibility, least privilege, and audit-safe handling of evidence.
- fact_key: document_model
  text_en: Documents, generated outputs, and uploads are centralized in platform services, but business meaning stays with the owning customer, planning, subcontractor, finance, or field workflow.
  text_de: Dokumente, generierte Ausgaben und Uploads werden zentral in Plattformdiensten gehalten, während die fachliche Bedeutung beim jeweils besitzenden Kunden-, Planungs-, Subunternehmer-, Finance- oder Feldeinsatzprozess bleibt.
  page_ids: PS-01, C-01, P-02, S-01, FI-01
  module_keys: platform_services, customers, planning, subcontractors, finance
  source_basis:
    - implementation_data_model / Generated Implementation Data Model / PS-01 / platform_services: The implementation model assigns centralized document ownership to platform services while business meaning remains with the owning bounded context.

## Create and govern a customer master (customer_create)

- title_de: Kundenstammdaten anlegen und führen
- summary_en: Customer setup starts in the Customers workspace and covers customer identity, contacts, addresses, billing profile, invoice parties, pricing, history, privacy, and visibility controls.
- summary_de: Die Kundenanlage startet im Kunden-Workspace und umfasst Kundenidentität, Kontakte, Adressen, Abrechnungsprofil, Rechnungsempfänger, Preislogik, Historie, Datenschutz und Sichtbarkeitsregeln.
- aliases_en: create customer, register customer, customer master, billing profile, invoice party, rate card
- aliases_de: kunde anlegen, kunden registrieren, kundenstammdaten, kundenverwaltung, rechnungsprofil, ansprechpartner, adresse
- linked_page_ids: C-01
- module_keys: customers

### Facts

- fact_key: customer_master_fields
  text_en: The customer master typically includes customer number, lifecycle status, legal name, display name, classification, ranking, and the tenant-scoped commercial identity of the customer.
  text_de: Der Kundenstamm umfasst typischerweise Kundennummer, Lebenszyklusstatus, rechtlichen Namen, Anzeigenamen, Klassifizierung, Ranking und die mandantenbezogene kaufmännische Identität des Kunden.
  page_ids: C-01
  module_keys: customers
  source_basis:
    - user_manual / Generated User Manual / C-01 / customers: The user manual marks C-01 as the starting point for customer master work and customer-scoped history.
    - implementation_data_model / Generated Implementation Data Model / C-01 / customers: The implementation data model assigns customer master and history ownership to the Customers context.
- fact_key: contacts_and_addresses
  text_en: Customer setup covers contacts, addresses, default branch or mandate alignment, and customer-specific communication details used by operations and finance.
  text_de: Zur Kundenanlage gehören Ansprechpartner, Adressen, die Zuordnung zu Standard-Niederlassung oder Mandat und kundenspezifische Kommunikationsdaten für Operations und Finance.
  page_ids: C-01
  module_keys: customers
  source_basis:
    - page_help_manifest / Assistant Page Help Manifest / C-01 / customers: The C-01 page-help manifest includes search, customer list, identity, contacts, addresses, and customer detail domain sections.
- fact_key: billing_and_invoice_parties
  text_en: Commercial customer setup includes billing profile, invoice parties, rate cards, surcharge rules, and customer-specific pricing logic before downstream order and billing flows rely on the record.
  text_de: Zur kaufmännischen Einrichtung gehören Abrechnungsprofil, Rechnungsempfänger, Preislisten, Zuschlagsregeln und kundenspezifische Preislogik, bevor nachgelagerte Auftrags- und Abrechnungsprozesse auf den Datensatz zugreifen.
  page_ids: C-01
  module_keys: customers
  source_basis:
    - operational_handbook / Generated Operational Handbook / C-01 / customers: The handbook ties customer setup to downstream planning and billing preparation, including commercial setup before release.
- fact_key: history_privacy_visibility
  text_en: Customer history, attachments, portal privacy, login history, and customer-specific employee visibility blocks remain customer-scoped and should be reviewed before exposing portal data.
  text_de: Kundenhistorie, Anhänge, Portal-Datenschutz, Login-Historie und kundenspezifische Mitarbeitersperren bleiben kundenspezifisch und sollten vor einer Portalfreigabe geprüft werden.
  page_ids: C-01, PS-01
  module_keys: customers, platform_services
  source_basis:
    - security_doc / AI Assistant Security / C-01 / customers: The security guidance requires least-privilege customer-facing visibility and default protection of personal names and sensitive data.
    - implementation_data_model / Generated Implementation Data Model / PS-01 / platform_services: Document and generated output handling stays centralized while customer meaning remains in the owning customer context.
- fact_key: import_export_vcard
  text_en: Customer administration can include import, export, vCard-like contact exchange, and document-backed attachments, but the create action still depends on customer write permissions.
  text_de: Zur Kundenverwaltung können Import, Export, vCard-artiger Kontaktaustausch und dokumentgestützte Anhänge gehören; der Anlegevorgang setzt dennoch Schreibrechte im Kundenkontext voraus.
  page_ids: C-01
  module_keys: customers
  source_basis:
    - page_help_manifest / Assistant Page Help Manifest / C-01 / customers: The verified C-01 manifest includes customer export and create actions in the list header.

## Customer Orders tab entry point (customer_orders_tab)

- title_de: Orders-Tab beim Kunden als Einstieg
- summary_en: The selected customer detail view exposes an Orders tab that lists customer orders and launches the customer-scoped order workspace for new or existing orders.
- summary_de: Die Detailansicht des ausgewählten Kunden enthält einen Orders-Tab, der Kundenaufträge auflistet und den kundenbezogenen Order-Workspace für neue oder bestehende Aufträge startet.
- aliases_en: customer orders tab, orders tab in customer, new order from customer page, edit order from customer
- aliases_de: orders-tab beim kunden, aufträge beim kunden, neuer auftrag beim kunden, auftrag beim kunden bearbeiten
- linked_page_ids: C-01, C-02
- module_keys: customers, planning

### Facts

- fact_key: tab_rendering_and_launch
  text_en: The Orders tab is rendered inside the selected customer detail view. It lists customer orders, emits start-new-order for a new order, and emits edit-order for an existing order workspace launch.
  text_de: Der Orders-Tab wird in der Detailansicht des ausgewählten Kunden gerendert. Er listet Kundenaufträge auf, sendet start-new-order für einen neuen Auftrag und edit-order für den Workspace-Start eines bestehenden Auftrags.
  page_ids: C-01, C-02
  module_keys: customers, planning
  source_basis:
    - frontend_component / CustomerAdminView.vue / C-01 / customers: CustomerAdminView renders CustomerOrdersTab inside the selected customer detail shell and handles start-new-order/edit-order events.
    - frontend_component / CustomerOrdersTab.vue / C-01 / customers: CustomerOrdersTab exposes customer-orders-new-order and customer-orders-card-edit actions and emits start-new-order/edit-order events.
- fact_key: customer_context_is_fixed
  text_en: The customer_id comes from the selected customer context and is passed into the workspace route, so the flow is customer-scoped instead of a generic global order shell.
  text_de: Die customer_id stammt aus dem ausgewählten Kundenkontext und wird an die Workspace-Route übergeben, sodass der Ablauf kundenbezogen und kein generischer globaler Auftragsshell ist.
  page_ids: C-01, C-02
  module_keys: customers, planning
  source_basis:
    - frontend_component / CustomerAdminView.vue / C-01 / customers: The router push for new and edit order always includes customer_id from selectedCustomer.

## Customer-scoped order workspace (customer_scoped_order_workspace)

- title_de: Kundenbezogener Order-Workspace
- summary_en: The customer-scoped order workspace is a guided route under Customers that saves order, planning-record, shift-plan, and shift-series context step by step before handing off to Staffing Coverage.
- summary_de: Der kundenbezogene Order-Workspace ist eine geführte Route unter Kunden, die Auftrags-, Planungsdatensatz-, Schichtplan- und Schichtserienkontext schrittweise speichert, bevor sie an Staffing Coverage übergibt.
- aliases_en: customer order workspace, order workspace, customer new plan, customer scoped order workspace
- aliases_de: kunden order workspace, auftragsworkspace, neuer plan beim kunden, kundenbezogener order-workspace
- linked_page_ids: C-02, P-04
- module_keys: customers, planning

### Facts

- fact_key: route_and_alias
  text_en: The canonical route is /admin/customers/order-workspace, and /admin/customers/new-plan is a route alias for the same page.
  text_de: Die kanonische Route ist /admin/customers/order-workspace, und /admin/customers/new-plan ist ein Routen-Alias für dieselbe Seite.
  page_ids: C-02
  module_keys: customers
  source_basis:
    - frontend_route / sicherplan.ts / C-02 / customers: SicherPlanCustomerOrderWorkspace is registered at /admin/customers/order-workspace with alias /admin/customers/new-plan.
- fact_key: wizard_steps
  text_en: The current guided steps are order-details, order-scope-documents, planning-record-overview, planning-record-documents, shift-plan, and series-exceptions.
  text_de: Die aktuellen geführten Schritte sind order-details, order-scope-documents, planning-record-overview, planning-record-documents, shift-plan und series-exceptions.
  page_ids: C-02
  module_keys: customers
  source_basis:
    - frontend_component / new-plan-wizard.steps.ts / C-02 / customers: The wizard step definition file registers the six current step IDs in this exact order.
- fact_key: staffing_handoff
  text_en: After Generate Series & Continue, concrete shifts are generated from the saved shift series and the user is redirected into /admin/planning-staffing with planning_record_id, date range, and first shift context.
  text_de: Nach Generate Series & Continue werden konkrete Schichten aus der gespeicherten Schichtserie erzeugt, und der Nutzer wird mit planning_record_id, Datumsfenster und erstem Schichtkontext nach /admin/planning-staffing weitergeleitet.
  page_ids: C-02, P-04
  module_keys: customers, planning
  source_basis:
    - frontend_component / new-plan-step-content.vue / C-02 / customers: buildStaffingHandoffRoute constructs a /admin/planning-staffing URL with date_from, date_to, planning_record_id, and shift_id after generation.

## Create an order from the customer page (customer_order_create_from_customer)

- title_de: Auftrag aus der Kundenseite anlegen
- summary_en: This flow starts from Customers, stays tied to the selected customer, and uses the order workspace instead of forcing the user into the older Operations & Planning orders route first.
- summary_de: Dieser Ablauf startet bei Kunden, bleibt an den ausgewählten Kunden gebunden und verwendet den Order-Workspace, statt den Nutzer zuerst in die ältere Operations-&-Planning-Auftragsroute zu zwingen.
- aliases_en: create order from customer page, create order from customer, customer page new order, customer contract from customer page
- aliases_de: auftrag direkt beim kunden erstellen, auftrag aus kundenseite, kundenvertrag aus kundenseite, auftrag im kundenbereich anlegen
- linked_page_ids: C-01, C-02, P-04
- module_keys: customers, planning

### Facts

- fact_key: customer_scoped_entry
  text_en: The new order button lives in the selected customer's Orders tab and opens the guided order workspace with the selected customer context already fixed.
  text_de: Die Schaltfläche für den neuen Auftrag liegt im Orders-Tab des ausgewählten Kunden und öffnet den geführten Order-Workspace mit bereits fixiertem Kundenkontext.
  page_ids: C-01, C-02
  module_keys: customers, planning
  source_basis:
    - frontend_component / CustomerOrdersTab.vue / C-01 / customers: The Orders tab header contains a verified customer-orders-new-order action.
    - frontend_component / CustomerAdminView.vue / C-01 / customers: handleStartCustomerNewOrder pushes to SicherPlanCustomerOrderWorkspace with customer_id from the selected customer.
- fact_key: order_vs_planning_documents
  text_en: Order documents stay attached to the order package, while planning-record documents are handled in a separate planning-record documents step. The assistant should explain that difference clearly.
  text_de: Auftragsdokumente bleiben am Auftragspaket, während Planungsdokumente in einem separaten Schritt für Planungsdatensatz-Dokumente behandelt werden. Der Assistent sollte diesen Unterschied klar erklären.
  page_ids: C-02
  module_keys: customers, planning
  source_basis:
    - frontend_component / new-plan-step-content.vue / C-02 / customers: The order-scope-documents step and planning-record-documents step use separate document panels and separate order/planning attachment APIs.

## Register a customer contract from the customer page (customer_contract_register_from_customer)

- title_de: Kundenvertrag aus der Kundenseite registrieren
- summary_en: When users mean a contract in customer context, the assistant should map that question to the selected customer's Orders tab and order workspace unless the user clearly means a generic document upload.
- summary_de: Wenn Nutzer im Kundenkontext von einem Vertrag sprechen, sollte der Assistent die Frage auf den Orders-Tab des ausgewählten Kunden und den Order-Workspace abbilden, sofern nicht klar ein generischer Dokumentenupload gemeint ist.
- aliases_en: customer contract, register contract from customer, contract from customer page
- aliases_de: kundenvertrag, vertrag beim kunden registrieren, vertrag aus kundenseite
- linked_page_ids: C-01, C-02, PS-01
- module_keys: customers, planning, platform_services

### Facts

- fact_key: no_standalone_contract_module_in_customer_flow
  text_en: The customer-scoped flow does not introduce a standalone contract module. Contract PDFs or files should be attached in order documents or planning-record documents depending on business ownership.
  text_de: Der kundenbezogene Ablauf führt kein eigenständiges Vertragsmodul ein. Vertrags-PDFs oder Dateien sollten je nach fachlicher Zugehörigkeit bei Auftragsdokumenten oder Planungsdokumenten angehängt werden.
  page_ids: C-02, PS-01
  module_keys: customers, planning, platform_services
  source_basis:
    - frontend_component / new-plan-step-content.vue / C-02 / customers: The order workspace has separate order-document and planning-record-document attachment flows rather than a dedicated contract module.
    - implementation_data_model / Generated Implementation Data Model / PS-01 / platform_services: Document ownership remains centralized while business meaning stays with the owning order or planning context.
- fact_key: customer_context_contract_mapping
  text_en: If the user says contract or Vertrag in customer context, the assistant should first explain the customer Orders tab and order workspace path, then clarify whether the file belongs to the order package or the planning-record package.
  text_de: Wenn der Nutzer im Kundenkontext Vertrag oder contract sagt, sollte der Assistent zuerst den Pfad über Orders-Tab und Order-Workspace erklären und dann klären, ob die Datei zum Auftragspaket oder zum Planungsdatensatz-Paket gehört.
  page_ids: C-01, C-02
  module_keys: customers, planning
  source_basis:
    - workflow_help / Assistant Workflow Help / C-02 / customers: The customer-scoped order workflow is the guided customer-context route for order and planning setup before Staffing Coverage handoff.

## Create a customer order (customer_order_create)

- title_de: Kundenauftrag anlegen
- summary_en: A customer order belongs to an existing customer and captures commercial and operational demand before staffing or release begins.
- summary_de: Ein Kundenauftrag gehört zu einem bestehenden Kunden und erfasst kaufmännischen sowie operativen Bedarf, bevor Staffing oder Freigabe beginnen.
- aliases_en: create order, customer order, new order, create customer order
- aliases_de: auftrag erstellen, kundenauftrag, neuen auftrag anlegen, auftrag für kunden
- linked_page_ids: C-01, P-02
- module_keys: customers, planning

### Facts

- fact_key: customer_precondition
  text_en: The customer should exist first, because the order or project package is created in customer context and later drives planning, staffing, and billing.
  text_de: Der Kunde sollte zuerst existieren, weil Auftrag oder Projektpaket im Kundenkontext angelegt werden und später Planung, Staffing und Abrechnung steuern.
  page_ids: C-01, P-02
  module_keys: customers, planning
  source_basis:
    - workflow_help / Assistant Workflow Help / C-01 / customers: The customer order workflow starts with customer context before order creation in P-02.
- fact_key: order_scope
  text_en: The order captures requirement type, service category, security concept, date window, sites or routes, equipment lines, requirement lines, notes, and attachments for the customer job package.
  text_de: Der Auftrag erfasst Bedarfsart, Leistungskategorie, Sicherheitskonzept, Datumsfenster, Standorte oder Routen, Equipment-Zeilen, Anforderungszeilen, Hinweise und Anhänge für das Kundenauftragspaket.
  page_ids: P-02
  module_keys: planning
  source_basis:
    - user_manual / Generated User Manual / P-02 / planning: The user manual identifies P-02 as the workspace for customer orders, planning records, and document packages.
- fact_key: document_package
  text_en: Order setup may include linked or uploaded documents, and those attachments stay document-backed rather than becoming ad hoc contract data in a fake standalone module.
  text_de: Zur Auftragseinrichtung können verknüpfte oder hochgeladene Dokumente gehören; diese Anhänge bleiben dokumentgestützt und werden nicht zu Ad-hoc-Vertragsdaten in einem erfundenen Modul.
  page_ids: P-02, PS-01
  module_keys: planning, platform_services
  source_basis:
    - operational_handbook / Generated Operational Handbook / P-02 / planning: The operational handbook states that planning orders and planning records include documented planning packages and attachments.

## Create a customer planning package (customer_plan_create)

- title_de: Kundenplanung anlegen
- summary_en: Customer planning continues from customer and order context into a planning record and then into concrete shift preparation.
- summary_de: Die Kundenplanung führt vom Kunden- und Auftragskontext in einen Planungsdatensatz und anschließend in die konkrete Schichtvorbereitung.
- aliases_en: create customer plan, customer planning, create planning package, plan customer shifts
- aliases_de: kundenplanung anlegen, planung für kunden, planungsdatensatz, dienstplanung für kunden
- linked_page_ids: C-01, P-02, P-03
- module_keys: customers, planning

### Facts

- fact_key: planning_record_context
  text_en: A planning package stays under customer and order context. It becomes the planning record that carries demand, documents, setup details, and later shift planning context.
  text_de: Ein Planungspaket bleibt unter Kunden- und Auftragskontext. Es wird zum Planungsdatensatz, der Bedarf, Dokumente, Einrichtungsdetails und später den Kontext für die Schichtplanung trägt.
  page_ids: C-01, P-02
  module_keys: customers, planning
  source_basis:
    - workflow_help / Assistant Workflow Help / P-02 / planning: The customer plan workflow places the planning record in P-02 between customer context and concrete shifts.
- fact_key: planning_setup
  text_en: The planning record can capture customer-dependent setup such as sites, routes, timezone details, address options, planning documents, and structured notes before the shift layer is generated.
  text_de: Der Planungsdatensatz kann kundenabhängige Einrichtung wie Standorte, Routen, Zeitzonendetails, Adressoptionen, Planungsdokumente und strukturierte Hinweise aufnehmen, bevor die Schichtschicht erzeugt wird.
  page_ids: P-02
  module_keys: planning
  source_basis:
    - page_help_manifest / Assistant Page Help Manifest / P-02 / planning: The P-02 manifest includes planning record overview, documents, address creation, and customer order workspace follow-up sections.
- fact_key: shift_planning_transition
  text_en: Concrete shift planning follows only after the planning record exists. Staffing and assignment follow after concrete shifts or demand groups exist.
  text_de: Die konkrete Schichtplanung folgt erst, nachdem der Planungsdatensatz existiert. Staffing und Zuweisung folgen erst, wenn konkrete Schichten oder Bedarfsgruppen vorhanden sind.
  page_ids: P-03, P-04
  module_keys: planning
  source_basis:
    - user_manual / Generated User Manual / P-03 / planning: The user manual and workflow summaries place concrete shift work in P-03 and staffing after that in P-04.

## Create a planning record under an order (planning_record_create)

- title_de: Planungsdatensatz unter einem Auftrag anlegen
- summary_en: Planning-record creation is the operational bridge between customer order setup and detailed shift planning.
- summary_de: Die Anlage eines Planungsdatensatzes ist die operative Brücke zwischen Kundenauftrag und detaillierter Schichtplanung.
- aliases_en: planning record, create planning record, planning package, operational planning record
- aliases_de: planungsdatensatz, planungsstand anlegen, planungspaket, einsatzplanung
- linked_page_ids: P-02, P-03
- module_keys: planning

### Facts

- fact_key: record_under_order
  text_en: The planning record is created under an existing order or planning package and becomes the owner of downstream shift preparation, notes, and attachments.
  text_de: Der Planungsdatensatz wird unter einem bestehenden Auftrag oder Planungspaket angelegt und wird zum Träger der nachgelagerten Schichtvorbereitung, Hinweise und Anhänge.
  page_ids: P-02
  module_keys: planning
  source_basis:
    - implementation_data_model / Generated Implementation Data Model / P-02 / planning: Planning owns orders, planning records, shifts, staffing, releases, and document packages linked to planning context.
- fact_key: handoff_to_shift_planning
  text_en: Once the planning record exists, the next concrete step is shift planning rather than direct staffing.
  text_de: Sobald der Planungsdatensatz existiert, ist der nächste konkrete Schritt die Schichtplanung und nicht direkt das Staffing.
  page_ids: P-03, P-04
  module_keys: planning
  source_basis:
    - workflow_help / Assistant Workflow Help / P-03 / planning: Workflow help moves from planning record setup into P-03 before assignment in P-04.

## Register a contract or document in the right business context (contract_or_document_register)

- title_de: Vertrag oder Dokument im richtigen Fachkontext registrieren
- summary_en: Contract questions are ambiguity-aware and document-centered. The assistant should distinguish customer, order, subcontractor, and generic document contexts instead of inventing a contract module.
- summary_de: Vertragsfragen sind mehrdeutig und dokumentenzentriert. Der Assistent soll zwischen Kunden-, Auftrags-, Subunternehmer- und generischem Dokumentkontext unterscheiden, statt ein Vertragsmodul zu erfinden.
- aliases_en: contract, agreement, document, attachment, upload, link document
- aliases_de: vertrag, vertragsdokument, dokument, anhang, hochladen, verknüpfen
- linked_page_ids: PS-01, C-01, P-02, S-01
- module_keys: platform_services, customers, planning, subcontractors

### Facts

- fact_key: no_standalone_contract_module
  text_en: A standalone contract module is not verified. Contract-like artifacts are handled as documents or attachments linked to customer, planning, subcontractor, or other owning business context.
  text_de: Ein eigenständiges Vertragsmodul ist nicht verifiziert. Vertragsähnliche Artefakte werden als Dokumente oder Anhänge behandelt, die an Kunden-, Planungs-, Subunternehmer- oder andere besitzende Fachkontexte gebunden sind.
  page_ids: PS-01, C-01, P-02, S-01
  module_keys: platform_services, customers, planning, subcontractors
  source_basis:
    - implementation_data_model / Generated Implementation Data Model / PS-01 / platform_services: The generated implementation model says contract-like content should be grounded as document ownership plus business context rather than a fake standalone contract table or module.
- fact_key: platform_services_document_workflows
  text_en: Platform Services PS-01 is the safe shared workspace for document create, version, upload, link, and download workflows when the subtype is still unclear.
  text_de: Platform Services PS-01 ist der sichere gemeinsame Workspace für Dokumentanlage, Versionierung, Upload, Verknüpfung und Download, wenn der Untertyp noch unklar ist.
  page_ids: PS-01
  module_keys: platform_services
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / PS-01 / platform_services: PS-01 is the verified Platform Services workspace.
    - user_manual / Generated User Manual / PS-01 / platform_services: The user manual calls PS-01 the safe shared reference for documents and contract-like uploads when the subtype is unclear.
- fact_key: clarification_targets
  text_en: If the user only says contract, ask whether they mean a customer contract, order or project attachment, subcontractor agreement, or generic document upload before suggesting an exact page.
  text_de: Wenn der Nutzer nur Vertrag sagt, sollte geklärt werden, ob ein Kundenvertrag, ein Auftrags- oder Projektanhang, eine Subunternehmervereinbarung oder ein generischer Dokumentenupload gemeint ist, bevor eine konkrete Seite empfohlen wird.
  page_ids: PS-01, C-01, P-02, S-01
  module_keys: platform_services, customers, planning, subcontractors
  source_basis:
    - workflow_help / Assistant Workflow Help / PS-01 / platform_services: The contract workflow manifest explicitly requires targeted clarification before page guidance.

## Assign an employee to a shift (employee_assign_to_shift)

- title_de: Mitarbeiter einer Schicht zuweisen
- summary_en: Assignment requires employee readiness, concrete shifts, staffing validations, and release follow-up for app visibility.
- summary_de: Die Zuweisung erfordert Mitarbeiterbereitschaft, konkrete Schichten, Staffing-Prüfungen und Freigabe-Nachlauf für die App-Sichtbarkeit.
- aliases_en: assign employee to shift, staff a shift, put employee on shift
- aliases_de: mitarbeiter einer schicht zuweisen, schicht besetzen, mitarbeiter einplanen
- linked_page_ids: E-01, P-03, P-04, P-05, ES-01
- module_keys: employees, planning, employee_self_service

### Facts

- fact_key: employee_readiness
  text_en: The employee must exist and be active, and readiness can depend on qualifications, availability, absences, documents, and mobile access state before assignment should proceed.
  text_de: Der Mitarbeiter muss existieren und aktiv sein; die Einsatzbereitschaft kann von Qualifikationen, Verfügbarkeit, Abwesenheiten, Dokumenten und Mobile-Zugang abhängen, bevor die Zuweisung fortgesetzt werden sollte.
  page_ids: E-01
  module_keys: employees
  source_basis:
    - workflow_help / Assistant Workflow Help / E-01 / employees: Workflow help places employee readiness ahead of staffing.
- fact_key: shift_and_staffing
  text_en: The shift must already exist under a shift plan. Staffing happens after concrete shifts or demand groups exist, and the staffing board is the assignment workspace.
  text_de: Die Schicht muss bereits unter einem Schichtplan existieren. Staffing erfolgt erst, wenn konkrete Schichten oder Bedarfsgruppen vorhanden sind, und das Staffing Board ist der Zuweisungs-Workspace.
  page_ids: P-03, P-04
  module_keys: planning
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / P-03 / planning: P-03 is the verified Shift Planning workspace, and P-04 is the verified Staffing Board & Coverage workspace.
- fact_key: assignment_validations
  text_en: Assignment validations can include qualification mismatch, missing document, customer block, double booking, rest period, and minimum staffing or coverage rules.
  text_de: Zuordnungsprüfungen können Qualifikationskonflikt, fehlende Dokumente, Kundensperre, Doppelbuchung, Ruhezeit und Mindestbesetzungs- oder Deckungsregeln umfassen.
  page_ids: P-04
  module_keys: planning
  source_basis:
    - operational_handbook / Generated Operational Handbook / P-04 / planning: The operational workflow summaries and diagnostics reference validation checks before assignment and release follow-up.
- fact_key: release_and_app_visibility
  text_en: Release and dispatch follow-up control whether the assigned shift becomes visible in the employee app; employee self-service readiness still matters after staffing.
  text_de: Freigabe und Dispositions-Nachlauf steuern, ob die zugewiesene Schicht in der Mitarbeiter-App sichtbar wird; die Bereitschaft des Self-Service-Zugangs bleibt auch nach dem Staffing relevant.
  page_ids: P-05, ES-01
  module_keys: planning, employee_self_service
  source_basis:
    - workflow_help / Assistant Workflow Help / P-05 / planning: Workflow help places dispatch follow-up and employee self-service readiness after the staffing step for app visibility.
