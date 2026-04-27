# Assistant Workflow Help

This generated source summarizes verified workflow seeds used by the assistant.

## Create a customer master record (customer_create)

- title_de: Kundenstammdatensatz anlegen
- summary_en: Customer setup starts in the Customers workspace and usually covers the customer master, contacts, addresses, billing profile, invoice parties, rate cards, portal privacy, and employee visibility blocks.
- summary_de: Die Kundenanlage startet im Kunden-Workspace und umfasst in der Regel Kundenstamm, Kontakte, Adressen, Abrechnungsprofil, Rechnungsempfänger, Preisregeln, Portal-Datenschutz und Mitarbeitersperren.
- intent_aliases_en: create customer, new customer, customer master, create a new customer
- intent_aliases_de: kunde anlegen, neuen kunden anlegen, kundenstamm anlegen, kunden erstellen
- linked_page_ids: C-01
- linked_pages_labeled: C-01 Customers Workspace
- api_families: customers

### Steps

- 1. customer_master [page C-01 / module customers]
  purpose_en: Create or verify the customer master record before any order, planning, or billing workflow continues.
  purpose_de: Kundenstammdaten anlegen oder prüfen, bevor Auftrags-, Planungs- oder Abrechnungsprozesse fortgesetzt werden.
  required_permissions: customers.customer.read, customers.customer.write
  source_basis:
    - role_page_coverage / Assistant Role Page Coverage Map / C-01 / customers: Inferred from the verified role/page coverage and route catalog: C-01 is the tenant-scoped Customers workspace for customer master access.
    - user_manual / Generated User Manual / C-01 / customers: The generated user manual states that customer master work starts in C-01.
- 2. commercial_and_billing [page C-01 / module customers]
  purpose_en: Maintain contacts, addresses, billing profile, invoice parties, and commercial/rate-card data inside the customer workspace.
  purpose_de: Kontakte, Adressen, Abrechnungsprofil, Rechnungsempfänger und kaufmännische bzw. Preisregeldaten im Kunden-Workspace pflegen.
  required_permissions: customers.billing.read, customers.billing.write
  source_basis:
    - implementation_data_model / Generated Implementation Data Model / C-01 / customers: The implementation data model assigns customer master and customer-history ownership to the Customers context.
- 3. portal_privacy_and_blocks [page C-01 / module customers]
  purpose_en: Review portal privacy defaults and any employee visibility restrictions before exposing customer-facing data.
  purpose_de: Portal-Datenschutzvorgaben und eventuelle Mitarbeitersichtbarkeits-Sperren prüfen, bevor kundenseitige Daten freigegeben werden.
  required_permissions: customers.portal_access.read
  source_basis:
    - security_doc / AI Assistant Security / C-01 / customers: The assistant security guidance requires least-privilege customer visibility and customer-facing name protection by default.

## Register a contract or document in the correct business context (contract_or_document_register)

- title_de: Vertrag oder Dokument im richtigen Fachkontext registrieren
- summary_en: Contract registration is document-centered and context-dependent. The assistant must distinguish customer contract, order attachment, subcontractor agreement, or generic document handling instead of inventing a standalone contract workspace.
- summary_de: Die Vertragsregistrierung ist dokumentenzentriert und kontextabhängig. Der Assistent muss zwischen Kundenvertrag, Auftragsanhang, Subunternehmervereinbarung oder generischer Dokumentablage unterscheiden, statt einen eigenständigen Vertrags-Workspace zu erfinden.
- intent_aliases_en: register contract, new contract, register document, upload agreement, attach document
- intent_aliases_de: vertrag registrieren, neuen vertrag anlegen, dokument registrieren, vereinbarung hochladen, anhang hinzufügen
- linked_page_ids: PS-01, C-01, P-02, S-01
- linked_pages_labeled: PS-01 Platform Services Workspace, C-01 Customers Workspace, P-02 Orders & Planning Records, S-01 Subcontractors Workspace
- api_families: platform_services, customers, planning, subcontractors
- ambiguity_notes:
  - If the user does not specify whether the document belongs to a customer relationship, an order/planning package, a subcontractor agreement, or a generic document workflow, ask that targeted clarifying question before suggesting a page.

### Steps

- 1. clarify_business_context [page PS-01 / module platform_services]
  purpose_en: Clarify whether the item is a customer contract, order attachment, subcontractor agreement, or generic document before routing the user.
  purpose_de: Klären, ob es sich um einen Kundenvertrag, einen Auftragsanhang, eine Subunternehmervereinbarung oder ein generisches Dokument handelt, bevor eine Seite empfohlen wird.
  required_permissions: none
  source_basis:
    - operational_handbook / Generated Operational Handbook / PS-01 / platform_services: The operational handbook states that contract-like artifacts are handled as documents or attachments linked to the owning business entity.
    - workflow_help / Workflow Manifest / PS-01 / platform_services: This workflow intentionally treats contract registration as ambiguous and requires targeted clarification before page guidance.
- 2. generic_document_reference [page PS-01 / module platform_services]
  purpose_en: Use Platform Services as the safe shared document reference when the exact subtype is still unclear and the user needs document create, version, upload, or linking guidance.
  purpose_de: Platform Services als sicheren gemeinsamen Dokumentbezug verwenden, wenn der genaue Untertyp noch unklar ist und der Nutzer Anleitung für Anlegen, Versionieren, Hochladen oder Verknüpfen benötigt.
  required_permissions: none
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / PS-01 / platform_services: PS-01 is the verified Platform Services workspace.
    - user_manual / Generated User Manual / PS-01 / platform_services: The generated user manual identifies PS-01 as the safe shared reference for document-centered workflows when the subtype is unclear.
- 3. customer_or_order_attachment [page C-01 / module customers]
  purpose_en: If the document belongs to a customer relationship or customer history, keep the workflow in Customers; if it belongs to an order or planning package, continue in Orders & Planning Records.
  purpose_de: Wenn das Dokument zu einer Kundenbeziehung oder Kundenhistorie gehört, bleibt der Ablauf im Kunden-Workspace; gehört es zu einem Auftrag oder Planungspaket, geht es in Aufträge & Planungsdatensätze weiter.
  required_permissions: customers.customer.read, planning.order.read, planning.record.read
  source_basis:
    - implementation_data_model / Generated Implementation Data Model / C-01 / customers: The implementation data model places customer truth in Customers and planning packages in Planning.
    - operational_handbook / Generated Operational Handbook / P-02 / planning: The operational handbook says planning orders and planning records include documented planning packages and attachments.
- 4. subcontractor_agreement [page S-01 / module subcontractors]
  purpose_en: If the user means a subcontractor agreement, route the context into the Subcontractors workspace instead of treating it as a generic document only.
  purpose_de: Wenn der Nutzer eine Subunternehmervereinbarung meint, muss der Kontext in den Subunternehmer-Workspace geleitet werden, statt ihn nur als generisches Dokument zu behandeln.
  required_permissions: subcontractors.company.read
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / S-01 / subcontractors: S-01 is the verified subcontractors workspace for tenant-scoped partner records.

## Create a customer order and planning record (customer_order_create)

- title_de: Kundenauftrag und Planungsdatensatz anlegen
- summary_en: A customer order belongs to an existing customer and continues into a planning record with attachments, commercial linkage, and operational preparation.
- summary_de: Ein Kundenauftrag gehört zu einem bestehenden Kunden und wird mit Anhängen, kaufmännischer Verknüpfung und operativer Vorbereitung in einen Planungsdatensatz überführt.
- intent_aliases_en: create order, new customer order, create plan for customer, create customer order
- intent_aliases_de: auftrag erstellen, neuen auftrag anlegen, planung für kunden erstellen, kundenauftrag anlegen
- linked_page_ids: C-01, P-02
- linked_pages_labeled: C-01 Customers Workspace, P-02 Orders & Planning Records
- api_families: customers, planning

### Steps

- 1. customer_context [page C-01 / module customers]
  purpose_en: Create or verify the customer record before creating the order or project context.
  purpose_de: Kundendatensatz anlegen oder prüfen, bevor Auftrag oder Projektkontext erstellt werden.
  required_permissions: customers.customer.read
  source_basis:
    - workflow_help / Workflow Manifest / C-01 / customers: This workflow requires customer context before order creation.
    - user_manual / Generated User Manual / C-01 / customers: The generated user manual states that order and planning flows depend on an existing customer context.
- 2. order_and_planning_record [page P-02 / module planning]
  purpose_en: Create the customer order, project or planning record, including attachments, commercial linkage, and requirement lines.
  purpose_de: Kundenauftrag, Projekt oder Planungsdatensatz inklusive Anhängen, kaufmännischer Verknüpfung und Anforderungszeilen anlegen.
  required_permissions: planning.order.read, planning.order.write, planning.record.read, planning.record.write
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / P-02 / planning: P-02 is the verified Orders & Planning Records workspace.
    - user_manual / Generated User Manual / P-02 / planning: The generated user manual states that P-02 manages customer orders, planning records, and document packages.

## Create a customer planning record and concrete shifts (customer_plan_create)

- title_de: Planungsdatensatz und konkrete Schichten für Kunden anlegen
- summary_en: Planning starts with customer and order context, then continues from planning record setup into concrete shift planning.
- summary_de: Die Planung startet mit Kunden- und Auftragskontext und geht dann vom Planungsdatensatz in die konkrete Schichtplanung über.
- intent_aliases_en: create customer plan, new plan for customer, create planning record, plan customer shifts
- intent_aliases_de: kundenplanung anlegen, neuen plan für kunden erstellen, planungsdatensatz anlegen, kundenschichten planen
- linked_page_ids: C-01, P-02, P-03
- linked_pages_labeled: C-01 Customers Workspace, P-02 Orders & Planning Records, P-03 Shift Planning
- api_families: customers, planning

### Steps

- 1. customer_context [page C-01 / module customers]
  purpose_en: Confirm the customer context first.
  purpose_de: Zuerst den Kundenkontext bestätigen.
  required_permissions: customers.customer.read
  source_basis:
    - workflow_help / Workflow Manifest / C-01 / customers: Customer context is the first prerequisite in this workflow.
- 2. planning_record [page P-02 / module planning]
  purpose_en: Create the planning record or order package that owns the operational planning context.
  purpose_de: Den Planungsdatensatz oder das Auftragspaket anlegen, das den operativen Planungskontext trägt.
  required_permissions: planning.order.read, planning.record.read, planning.record.write
  source_basis:
    - user_manual / Generated User Manual / P-02 / planning: The generated user manual places planning records and order setup in P-02.
- 3. concrete_shifts [page P-03 / module planning]
  purpose_en: Continue into Shift Planning for concrete shifts once the planning record exists.
  purpose_de: Nach dem Planungsdatensatz in die Schichtplanung wechseln, um konkrete Schichten anzulegen.
  required_permissions: planning.shift.read, planning.shift.write
  source_basis:
    - workflow_help / Workflow Manifest / P-03 / planning: This workflow moves from the planning record into concrete shift planning in P-03.

## Create an employee file and operational readiness (employee_create)

- title_de: Mitarbeiterakte und operative Einsatzfähigkeit anlegen
- summary_en: Employee creation starts in the Employees workspace, then continues with qualifications, availability, and app-access readiness.
- summary_de: Die Mitarbeiteranlage startet im Mitarbeiter-Workspace und wird mit Qualifikationen, Verfügbarkeit und App-Zugangsbereitschaft fortgesetzt.
- intent_aliases_en: create employee, new employee, employee file, create employee file
- intent_aliases_de: mitarbeiter anlegen, neuen mitarbeiter anlegen, mitarbeiterakte anlegen
- linked_page_ids: E-01
- linked_pages_labeled: E-01 Employees Workspace
- api_families: employees

### Steps

- 1. employee_file [page E-01 / module employees]
  purpose_en: Open the employee create flow in the Employees workspace and create the operational employee file.
  purpose_de: Den Anlegevorgang im Mitarbeiter-Workspace öffnen und die operative Mitarbeiterakte anlegen.
  required_permissions: employees.employee.read, employees.employee.write
  source_basis:
    - page_help_manifest / Assistant Page Help Manifest / E-01 / employees: The verified E-01 page-help manifest includes the employees.create.open action and confirms that it opens the structured employee create form.
- 2. qualifications_and_availability [page E-01 / module employees]
  purpose_en: Complete qualifications and availability so planning can safely use the employee later.
  purpose_de: Qualifikationen und Verfügbarkeit pflegen, damit die Planung den Mitarbeiter später sicher einsetzen kann.
  required_permissions: employees.employee.read
  source_basis:
    - page_help_manifest / Assistant Page Help Manifest / E-01 / employees: The verified E-01 manifest lists follow-up steps for qualifications and availability after employee creation.
- 3. access_link [page E-01 / module employees]
  purpose_en: Check the access link or employee self-service readiness if the employee must later receive released schedules in the app.
  purpose_de: Zugangsverknüpfung oder Self-Service-Bereitschaft prüfen, wenn der Mitarbeiter später freigegebene Schichten in der App erhalten soll.
  required_permissions: employees.employee.write
  source_basis:
    - page_help_manifest / Assistant Page Help Manifest / E-01 / employees: The verified E-01 manifest includes a post-create step to check the app access link.

## Assign an employee to a shift (employee_assign_to_shift)

- title_de: Mitarbeiter einer Schicht zuweisen
- summary_en: Employee assignment requires an existing employee, a concrete shift, and staffing-board validations before release and dispatch follow-up.
- summary_de: Die Mitarbeiterzuweisung erfordert einen bestehenden Mitarbeiter, eine konkrete Schicht und Prüfungen im Staffing Board, bevor Freigabe und Disposition folgen.
- intent_aliases_en: assign employee to shift, staff a shift, put employee on shift
- intent_aliases_de: mitarbeiter einer schicht zuweisen, schicht besetzen, mitarbeiter in schicht einplanen
- linked_page_ids: E-01, P-03, P-04, P-05
- linked_pages_labeled: E-01 Employees Workspace, P-03 Shift Planning, P-04 Staffing Board & Coverage, P-05 Dispatch, Outputs & Subcontractor Releases
- api_families: employees, planning

### Steps

- 1. employee_readiness [page E-01 / module employees]
  purpose_en: Verify that the employee exists and is operationally ready before staffing the shift.
  purpose_de: Vor der Besetzung der Schicht prüfen, ob der Mitarbeiter existiert und operativ einsatzbereit ist.
  required_permissions: employees.employee.read
  source_basis:
    - workflow_help / Workflow Manifest / E-01 / employees: This workflow requires employee readiness before staffing.
- 2. concrete_shift [page P-03 / module planning]
  purpose_en: Verify that the concrete shift exists in Shift Planning and that the planning context is ready for staffing.
  purpose_de: Prüfen, dass die konkrete Schicht in der Schichtplanung existiert und der Planungskontext für die Besetzung bereit ist.
  required_permissions: planning.shift.read
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / P-03 / planning: P-03 is the verified Shift Planning workspace.
- 3. staffing_board_assignment [page P-04 / module planning]
  purpose_en: Assign the employee in the Staffing Board and review assignment validations.
  purpose_de: Den Mitarbeiter im Staffing Board zuweisen und die Zuordnungsprüfungen kontrollieren.
  required_permissions: planning.staffing.read, planning.staffing.write
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / P-04 / planning: P-04 is the verified Staffing Board & Coverage workspace.
- 4. dispatch_followup [page P-05 / module planning]
  purpose_en: If app visibility or downstream release matters, continue into dispatch, outputs, and subcontractor-release follow-up.
  purpose_de: Wenn App-Sichtbarkeit oder nachgelagerte Freigaben relevant sind, in Disposition, Outputs und Freigabe-Nachlauf wechseln.
  required_permissions: planning.staffing.read
  source_basis:
    - workflow_help / Workflow Manifest / P-05 / planning: This workflow explicitly places release and dispatch follow-up after the staffing step.

## Release a shift to the employee app (shift_release_to_employee_app)

- title_de: Schicht für die Mitarbeiter-App freigeben
- summary_en: Employee-app visibility depends on shift release state, staffing state, downstream dispatch checks, and employee self-service readiness.
- summary_de: Die Sichtbarkeit in der Mitarbeiter-App hängt von Schichtfreigabe, Besetzungsstatus, Dispositionsprüfungen und der Self-Service-Bereitschaft des Mitarbeiters ab.
- intent_aliases_en: release shift to employee app, make shift visible in app, employee app shift visibility
- intent_aliases_de: schicht für mitarbeiter-app freigeben, schicht in app sichtbar machen, mitarbeiter-app sichtbarkeit
- linked_page_ids: P-03, P-04, P-05, ES-01
- linked_pages_labeled: P-03 Shift Planning, P-04 Staffing Board & Coverage, P-05 Dispatch, Outputs & Subcontractor Releases, ES-01 Employee Self-Service Portal
- api_families: planning, employees, employee_self_service

### Steps

- 1. shift_release_state [page P-03 / module planning]
  purpose_en: Verify the shift exists and is in a releaseable state.
  purpose_de: Prüfen, dass die Schicht existiert und sich in einem freigabefähigen Zustand befindet.
  required_permissions: planning.shift.read
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / P-03 / planning: P-03 is the verified Shift Planning workspace for concrete shifts.
- 2. assignment_visibility_state [page P-04 / module planning]
  purpose_en: Verify that the assignment and staffing state allow employee visibility.
  purpose_de: Prüfen, dass Zuordnung und Besetzungsstatus die Mitarbeitersichtbarkeit zulassen.
  required_permissions: planning.staffing.read
  source_basis:
    - workflow_help / Workflow Manifest / P-04 / planning: The workflow places visibility dependency on staffing state before app release.
- 3. dispatch_and_output_checks [page P-05 / module planning]
  purpose_en: Review downstream dispatch and release follow-up when visibility still fails.
  purpose_de: Nachgelagerte Dispositions- und Freigabeprüfungen kontrollieren, wenn die Sichtbarkeit weiterhin fehlschlägt.
  required_permissions: planning.staffing.read
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / P-05 / planning: P-05 is the verified dispatch, outputs, and subcontractor-release workspace.
- 4. employee_self_service_ready [page ES-01 / module employee_self_service]
  purpose_en: Verify that employee self-service or mobile access is ready, because a released shift is still not visible without employee access readiness.
  purpose_de: Prüfen, dass Self-Service bzw. Mobile-Zugang des Mitarbeiters bereit ist, denn eine freigegebene Schicht bleibt ohne Zugangsbereitschaft unsichtbar.
  required_permissions: portal.employee.access
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / ES-01 / employee_self_service: ES-01 is the verified employee self-service portal reference used for employee access context.

## Move from field actuals into billing and payroll (actuals_billing_payroll_chain)

- title_de: Von Feldevidence zu Abrechnung und Payroll überleiten
- summary_en: Field attendance and time evidence flow into finance actual records, approvals, customer billing, and payroll export without bypassing the finance actual bridge.
- summary_de: Feldbezogene Anwesenheits- und Zeitevidence fließt in Finance-Actual-Records, Freigaben, Kundenabrechnung und Payroll-Export, ohne die Finance-Actual-Bridge zu umgehen.
- intent_aliases_en: billing and payroll chain, actuals to billing, timesheet to payroll, invoice and payroll workflow
- intent_aliases_de: abrechnung und payroll, actuals zu abrechnung, timesheet zu payroll, feldevidence abrechnung payroll
- linked_page_ids: FD-01, FI-01, FI-02, FI-03
- linked_pages_labeled: FD-01 Field Operations Workspace, FI-01 Actuals / Actual-Freigaben Workspace, FI-02 Billing Workspace, FI-03 Payroll Workspace
- api_families: field_execution, finance

### Steps

- 1. field_evidence [page FD-01 / module field_execution]
  purpose_en: Capture or review attendance and field evidence before finance derivation starts.
  purpose_de: Anwesenheit und Feldevidence erfassen oder prüfen, bevor die finanzielle Ableitung beginnt.
  required_permissions: field.attendance.read, field.time_capture.read
  source_basis:
    - implementation_data_model / Generated Implementation Data Model / FD-01 / field_execution: The implementation guidance preserves raw field evidence and separates it from finance-owned derivation.
- 2. finance_actual_bridge [page FI-01 / module finance]
  purpose_en: Derive or review finance actual records; do not bypass the finance actual bridge.
  purpose_de: Finance-Actual-Records ableiten oder prüfen; die Finance-Actual-Bridge darf nicht umgangen werden.
  required_permissions: finance.actual.read, finance.actual.write
  source_basis:
    - implementation_data_model / Generated Implementation Data Model / FI-01 / finance: The implementation rules explicitly state that payroll and billing must not bypass finance.actual_record.
- 3. billing_release [page FI-02 / module finance]
  purpose_en: Continue into billing release, timesheets, and invoice generation after actuals are ready.
  purpose_de: Nach bereitstehenden Actuals in die Abrechnungsfreigabe, Timesheets und Rechnungserstellung wechseln.
  required_permissions: finance.billing.read, finance.billing.write
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / FI-02 / finance: FI-02 is the verified Billing workspace.
- 4. payroll_export [page FI-03 / module finance]
  purpose_en: Use the Payroll workspace for payroll tariffs, export batches, and payroll release outputs.
  purpose_de: Für Payroll-Tarife, Export-Batches und Payroll-Ausgaben den Payroll-Workspace verwenden.
  required_permissions: finance.payroll.read, finance.payroll.export
  source_basis:
    - page_route_catalog / Assistant Page Route Catalog / FI-03 / finance: FI-03 is the verified Payroll workspace.
