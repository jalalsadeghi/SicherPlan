# Assistant UI Action Catalog

## C-01 — Customers Workspace (en)

- action_key: customers.create.open
  label: New customer
  label_status: verified
  location: list header toolbar
  required_permissions: customers.customer.write
  result: Starts the customer create flow in the customer workspace.

- action_key: customers.export.csv
  label: CSV export
  label_status: verified
  location: list header toolbar
  required_permissions: customers.customer.read
  result: Triggers customer export from the list header.

- action_key: customers.orders.new_order
  label: New order
  label_status: verified
  location: Orders tab header
  required_permissions: planning.order.write
  result: Starts the customer-scoped order workspace from the selected customer's Orders tab.


## C-01 — Kunden-Workspace (de)

- action_key: customers.create.open
  label: Neuer Kunde
  label_status: verified
  location: Toolbar im Listenbereich
  required_permissions: customers.customer.write
  result: Startet den Kunden-Anlegevorgang im Kunden-Workspace.

- action_key: customers.export.csv
  label: CSV-Export
  label_status: verified
  location: Toolbar im Listenbereich
  required_permissions: customers.customer.read
  result: Startet den Kundenexport aus dem Listenbereich.

- action_key: customers.orders.new_order
  label: Neuer Auftrag
  label_status: verified
  location: Header im Orders-Tab
  required_permissions: planning.order.write
  result: Startet den kundenbezogenen Order-Workspace aus dem Orders-Tab des ausgewählten Kunden.


## C-02 — Customer Order Workspace (en)

- action_key: customer.order_workspace.previous
  label: Previous
  label_status: verified
  location: wizard action bar
  required_permissions: planning.order.read
  result: Moves back to the previous saved order-workspace step.

- action_key: customer.order_workspace.next
  label: Next
  label_status: verified
  location: wizard action bar
  required_permissions: planning.order.write
  result: Validates and saves the current step before the wizard advances.

- action_key: customer.order_workspace.generate_continue
  label: Generate Series & Continue
  label_status: verified
  location: wizard action bar
  required_permissions: planning.shift.write, planning.staffing.read
  result: Generates concrete shifts from the shift series and redirects into Staffing Coverage.


## C-02 — Kunden-Order-Workspace (de)

- action_key: customer.order_workspace.previous
  label: Zurück
  label_status: verified
  location: Wizard-Aktionsleiste
  required_permissions: planning.order.read
  result: Wechselt zum vorherigen gespeicherten Schritt des Order-Workspaces.

- action_key: customer.order_workspace.next
  label: Weiter
  label_status: verified
  location: Wizard-Aktionsleiste
  required_permissions: planning.order.write
  result: Validiert und speichert den aktuellen Schritt, bevor der Wizard weitergeht.

- action_key: customer.order_workspace.generate_continue
  label: Serie erzeugen und weiter
  label_status: verified
  location: Wizard-Aktionsleiste
  required_permissions: planning.shift.write, planning.staffing.read
  result: Erzeugt konkrete Schichten aus der Schichtserie und leitet nach Staffing Coverage weiter.


## P-02 — Orders & Planning Records (en)

- action_key: planning.order.create
  label: Create order
  label_status: unverified
  location: workspace toolbar or order shell
  required_permissions: planning.order.write
  result: Starts a customer order or planning record creation flow.

- action_key: planning.record.attach_document
  label: Attach or link document
  label_status: unverified
  location: planning record documents step
  required_permissions: planning.record.write
  result: Adds uploaded or linked documents to the planning record package.


## P-02 — Aufträge & Planungsdatensätze (de)

- action_key: planning.order.create
  label: Auftrag anlegen
  label_status: unverified
  location: Workspace-Toolbar oder Auftragsshell
  required_permissions: planning.order.write
  result: Startet einen Anlegefluss für Kundenauftrag oder Planungsdatensatz.

- action_key: planning.record.attach_document
  label: Dokument hochladen oder verknüpfen
  label_status: unverified
  location: Dokumentenabschnitt des Planungsdatensatzes
  required_permissions: planning.record.write
  result: Fügt Uploads oder verknüpfte Dokumente zum Planungspaket hinzu.


## PS-01 — Platform Services Workspace (en)

- action_key: platform_services.document.create
  label: Create document
  label_status: unverified
  location: platform services document workspace
  required_permissions: platform_services.document.write
  result: Starts a document create or versioning flow in platform services.

- action_key: platform_services.document.link
  label: Link document
  label_status: unverified
  location: platform services document workspace
  required_permissions: platform_services.document.write
  result: Links a document to a customer, planning, subcontractor, or other owning record.


## PS-01 — Plattformdienste-Workspace (de)

- action_key: platform_services.document.create
  label: Dokument anlegen
  label_status: unverified
  location: Dokumentenbereich der Plattformdienste
  required_permissions: platform_services.document.write
  result: Startet einen Anlege- oder Versionierungsfluss für Dokumente in den Plattformdiensten.

- action_key: platform_services.document.link
  label: Dokument verknüpfen
  label_status: unverified
  location: Dokumentenbereich der Plattformdienste
  required_permissions: platform_services.document.write
  result: Verknüpft ein Dokument mit Kunden-, Planungs-, Subunternehmer- oder anderem Fachkontext.


## P-03 — Shift Planning (en)

- action_key: planning.shift_template.create
  label: New template
  label_status: verified
  location: templates tab header
  required_permissions: planning.shift.write
  result: Opens the shift template create flow.

- action_key: planning.shift_plan.create
  label: New shift plan
  label_status: verified
  location: plans tab header
  required_permissions: planning.shift.write
  result: Opens the shift plan create flow.

- action_key: planning.shift_series.create
  label: New series
  label_status: verified
  location: series tab header
  required_permissions: planning.shift.write
  result: Starts a new recurring shift series for the selected shift plan.

- action_key: planning.shift.create
  label: New shift
  label_status: verified
  location: shifts tab header
  required_permissions: planning.shift.write
  result: Starts a concrete shift create flow for the selected shift plan.

- action_key: planning.shift.release
  label: Release shift
  label_status: verified
  location: release and visibility section
  required_permissions: planning.shift.write
  result: Moves the selected shift into released state.


## P-03 — Schichtplanung (de)

- action_key: planning.shift_template.create
  label: Neue Vorlage
  label_status: verified
  location: Header des Vorlagen-Tabs
  required_permissions: planning.shift.write
  result: Öffnet den Anlegefluss für eine Schichtvorlage.

- action_key: planning.shift_plan.create
  label: Neuer Schichtplan
  label_status: verified
  location: Header des Schichtplan-Tabs
  required_permissions: planning.shift.write
  result: Öffnet den Anlegefluss für einen Schichtplan.

- action_key: planning.shift_series.create
  label: Neue Serie
  label_status: verified
  location: Header des Serien-Tabs
  required_permissions: planning.shift.write
  result: Startet eine neue Schichtserie für den ausgewählten Schichtplan.

- action_key: planning.shift.create
  label: Neue Schicht
  label_status: verified
  location: Header des Schichten-Tabs
  required_permissions: planning.shift.write
  result: Startet den Anlegefluss für eine konkrete Schicht im ausgewählten Schichtplan.

- action_key: planning.shift.release
  label: Freigeben
  label_status: verified
  location: Bereich Freigabe und Sichtbarkeit
  required_permissions: planning.shift.write
  result: Setzt die ausgewählte Schicht in den freigegebenen Zustand.


## P-04 — Staffing Board & Coverage (en)

- action_key: planning.staffing.demand_group.create
  label: New demand group
  label_status: verified
  location: demand groups section header
  required_permissions: planning.staffing.write
  result: Starts demand-group setup for the selected shift.

- action_key: planning.staffing.assign
  label: Assign
  label_status: verified
  location: staffing actions section
  required_permissions: planning.staffing.write
  result: Creates an assignment for the selected demand group.

- action_key: planning.staffing.substitute
  label: Substitute
  label_status: verified
  location: staffing actions section
  required_permissions: planning.staffing.write
  result: Substitutes the selected assignment actor.

- action_key: planning.staffing.unassign
  label: Remove
  label_status: verified
  location: staffing actions section
  required_permissions: planning.staffing.write
  result: Removes the selected assignment.

- action_key: planning.staffing.team.create_planning
  label: Create planning team
  label_status: verified
  location: teams and partner releases section
  required_permissions: planning.staffing.write
  result: Starts a planning-team create flow for the current planning record context.


## P-04 — Staffing-Board & Coverage (de)

- action_key: planning.staffing.demand_group.create
  label: Neue Demand Group
  label_status: verified
  location: Header des Demand-Group-Bereichs
  required_permissions: planning.staffing.write
  result: Startet das Demand-Group-Setup für die ausgewählte Schicht.

- action_key: planning.staffing.assign
  label: Zuweisen
  label_status: verified
  location: Bereich Staffing-Aktionen
  required_permissions: planning.staffing.write
  result: Erstellt eine Zuweisung für die ausgewählte Demand Group.

- action_key: planning.staffing.substitute
  label: Ersetzen
  label_status: verified
  location: Bereich Staffing-Aktionen
  required_permissions: planning.staffing.write
  result: Ersetzt den Akteur der ausgewählten Zuweisung.

- action_key: planning.staffing.unassign
  label: Entfernen
  label_status: verified
  location: Bereich Staffing-Aktionen
  required_permissions: planning.staffing.write
  result: Entfernt die ausgewählte Zuweisung.

- action_key: planning.staffing.team.create_planning
  label: Planungsteam anlegen
  label_status: verified
  location: Bereich Teams und Partnerfreigaben
  required_permissions: planning.staffing.write
  result: Startet den Anlegefluss für ein Planungsteam im aktuellen Planungsdatensatzkontext.


## P-05 — Dispatch, Outputs & Subcontractor Releases (en)

- action_key: planning.output.generate_internal
  label: Generate internal deployment plan
  label_status: verified
  location: outputs section
  required_permissions: planning.staffing.write
  result: Generates the internal shift output for the selected shift.

- action_key: planning.output.generate_customer
  label: Generate customer variant
  label_status: verified
  location: outputs section
  required_permissions: planning.staffing.write
  result: Generates the customer-facing output variant for the selected shift.

- action_key: planning.dispatch.preview
  label: Load preview
  label_status: verified
  location: dispatch section
  required_permissions: planning.staffing.write
  result: Loads a dispatch preview for the selected shift and selected audiences.

- action_key: planning.dispatch.queue
  label: Queue message
  label_status: verified
  location: dispatch section
  required_permissions: planning.staffing.write
  result: Queues a dispatch message for the selected shift and selected audiences.


## P-05 — Dispatch, Outputs & Partnerfreigaben (de)

- action_key: planning.output.generate_internal
  label: Internen Einsatzplan erzeugen
  label_status: verified
  location: Bereich Outputs
  required_permissions: planning.staffing.write
  result: Erzeugt den internen Schichtoutput für die ausgewählte Schicht.

- action_key: planning.output.generate_customer
  label: Kundenvariante erzeugen
  label_status: verified
  location: Bereich Outputs
  required_permissions: planning.staffing.write
  result: Erzeugt die kundenbezogene Output-Variante für die ausgewählte Schicht.

- action_key: planning.dispatch.preview
  label: Vorschau laden
  label_status: verified
  location: Bereich Dispatch
  required_permissions: planning.staffing.write
  result: Lädt eine Dispatch-Vorschau für die ausgewählte Schicht und die gewählten Zielgruppen.

- action_key: planning.dispatch.queue
  label: Nachricht queueen
  label_status: verified
  location: Bereich Dispatch
  required_permissions: planning.staffing.write
  result: Stellt eine Dispatch-Nachricht für die ausgewählte Schicht und die gewählten Zielgruppen in die Queue.


## E-01 — Employees Workspace (en)

- action_key: employees.create.open
  label: Create employee file
  label_status: verified
  location: top-right toolbar
  required_permissions: employees.employee.write
  result: Opens the structured employee file form in create mode.


## E-01 — Mitarbeiter-Workspace (de)

- action_key: employees.create.open
  label: Mitarbeiterakte anlegen
  label_status: verified
  location: Toolbar oben rechts
  required_permissions: employees.employee.write
  result: Öffnet die strukturierte Mitarbeiterakte im Anlegemodus.

