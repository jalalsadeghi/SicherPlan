# Assistant Page Help Manifest

## C-01 en

- route_name: SicherPlanCustomers
- path_template: /admin/customers
- module_key: customers
- status: active
- page_title: Customers Workspace
- actions_registered: 2
- verified_sections: 3
- verified_post_steps: 3

### Actions

- New customer [verified]: Starts the customer create flow in the customer workspace.
- CSV export [verified]: Triggers customer export from the list header.

### Sections

- Search and selection: Search, Lifecycle status
- Customer master and identity: Customer number, Display name, Legal name, Classification, Ranking
- Contacts, addresses, and billing profile: Full name, Email, Phone, Address, Invoice email, Payment terms days, VAT ID

### Follow-up

- Complete billing profile and invoice parties
- Add rate cards and surcharge rules
- Review portal privacy and visibility rules

## C-01 de

- route_name: SicherPlanCustomers
- path_template: /admin/customers
- module_key: customers
- status: active
- page_title: Kunden-Workspace
- actions_registered: 2
- verified_sections: 3
- verified_post_steps: 3

### Actions

- Neuer Kunde [verified]: Startet den Kunden-Anlegevorgang im Kunden-Workspace.
- CSV-Export [verified]: Startet den Kundenexport aus dem Listenbereich.

### Sections

- Suche und Auswahl: Suche, Lifecycle-Status
- Kundenstamm und Identität: Kundennummer, Anzeigename, Rechtlicher Name, Klassifikation, Ranking
- Ansprechpartner, Adressen und Abrechnung: Vollständiger Name, E-Mail, Telefon, Adresse, Rechnungs-E-Mail, Zahlungsziel in Tagen, USt-IdNr.

### Follow-up

- Abrechnungsprofil und Rechnungsempfänger ergänzen
- Preislisten und Zuschlagsregeln pflegen
- Portal-Datenschutz und Sichtbarkeitsregeln prüfen

## P-02 en

- route_name: SicherPlanPlanningOrders
- path_template: /admin/planning-orders
- module_key: planning
- status: active
- page_title: Orders & Planning Records
- actions_registered: 2
- verified_sections: 2
- verified_post_steps: 2

### Actions

- Create order [unverified]: Starts a customer order or planning record creation flow.
- Attach or link document [unverified]: Adds uploaded or linked documents to the planning record package.

### Sections

- Order and planning record scope: Customer, Service category, Date window
- Requirements, equipment, and documents: Equipment lines, Requirement lines, Order documents, Planning documents

### Follow-up

- Complete the planning record package in P-02
- Continue into shift planning in P-03

## P-02 de

- route_name: SicherPlanPlanningOrders
- path_template: /admin/planning-orders
- module_key: planning
- status: active
- page_title: Aufträge & Planungsdatensätze
- actions_registered: 2
- verified_sections: 2
- verified_post_steps: 2

### Actions

- Auftrag anlegen [unverified]: Startet einen Anlegefluss für Kundenauftrag oder Planungsdatensatz.
- Dokument hochladen oder verknüpfen [unverified]: Fügt Uploads oder verknüpfte Dokumente zum Planungspaket hinzu.

### Sections

- Auftrags- und Planungsrahmen: Kunde, Leistungskategorie, Datumsfenster
- Anforderungen, Equipment und Dokumente: Equipment-Zeilen, Anforderungszeilen, Auftragsdokumente, Planungsdokumente

### Follow-up

- Planungspaket in P-02 vervollständigen
- Mit P-03 in die Schichtplanung wechseln

## PS-01 en

- route_name: SicherPlanPlatformServices
- path_template: /admin/platform-services
- module_key: platform_services
- status: active
- page_title: Platform Services Workspace
- actions_registered: 2
- verified_sections: 2
- verified_post_steps: 1

### Actions

- Create document [unverified]: Starts a document create or versioning flow in platform services.
- Link document [unverified]: Links a document to a customer, planning, subcontractor, or other owning record.

### Sections

- Central documents and versions: Document title, Version, Owning business context
- Links, uploads, and downloads: Upload, Download, Link target

### Follow-up

- Link the document back to its owning customer, planning, subcontractor, or finance context

## PS-01 de

- route_name: SicherPlanPlatformServices
- path_template: /admin/platform-services
- module_key: platform_services
- status: active
- page_title: Plattformdienste-Workspace
- actions_registered: 2
- verified_sections: 2
- verified_post_steps: 1

### Actions

- Dokument anlegen [unverified]: Startet einen Anlege- oder Versionierungsfluss für Dokumente in den Plattformdiensten.
- Dokument verknüpfen [unverified]: Verknüpft ein Dokument mit Kunden-, Planungs-, Subunternehmer- oder anderem Fachkontext.

### Sections

- Zentrale Dokumente und Versionen: Dokumenttitel, Version, Besitzender Fachkontext
- Verknüpfungen, Uploads und Downloads: Upload, Download, Verknüpfungsziel

### Follow-up

- Dokument an Kunden-, Planungs-, Subunternehmer- oder Finance-Kontext zurückverknüpfen

## P-03 en

- route_name: SicherPlanPlanningShifts
- path_template: /admin/planning-shifts
- module_key: planning
- status: active
- page_title: Shift Planning
- actions_registered: 5
- verified_sections: 3
- verified_post_steps: 2

### Actions

- New template [verified]: Opens the shift template create flow.
- New shift plan [verified]: Opens the shift plan create flow.
- New series [verified]: Starts a new recurring shift series for the selected shift plan.
- New shift [verified]: Starts a concrete shift create flow for the selected shift plan.
- Release shift [verified]: Moves the selected shift into released state.

### Sections

- Shift templates: Code, Label, Start time, End time
- Shift plans and series: Planning record, Planning from, Planning to, Recurrence
- Concrete shift timing and release: Starts at, Ends at, Release state, Customer visibility, Subcontractor visibility

### Follow-up

- Continue into staffing coverage in P-04
- Continue into outputs and dispatch in P-05

## P-03 de

- route_name: SicherPlanPlanningShifts
- path_template: /admin/planning-shifts
- module_key: planning
- status: active
- page_title: Schichtplanung
- actions_registered: 5
- verified_sections: 3
- verified_post_steps: 2

### Actions

- Neue Vorlage [verified]: Öffnet den Anlegefluss für eine Schichtvorlage.
- Neuer Schichtplan [verified]: Öffnet den Anlegefluss für einen Schichtplan.
- Neue Serie [verified]: Startet eine neue Schichtserie für den ausgewählten Schichtplan.
- Neue Schicht [verified]: Startet den Anlegefluss für eine konkrete Schicht im ausgewählten Schichtplan.
- Freigeben [verified]: Setzt die ausgewählte Schicht in den freigegebenen Zustand.

### Sections

- Schichtvorlagen: Code, Bezeichnung, Startzeit, Endzeit
- Schichtpläne und Serien: Planungsdatensatz, Planung von, Planung bis, Wiederholung
- Konkrete Schicht und Freigabe: Startet um, Endet um, Freigabestatus, Kundensichtbarkeit, Subunternehmer-Sichtbarkeit

### Follow-up

- Mit P-04 in die Staffing-Coverage wechseln
- Mit P-05 zu Outputs und Dispatch weitergehen

## P-04 en

- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing
- module_key: planning
- status: active
- page_title: Staffing Board & Coverage
- actions_registered: 5
- verified_sections: 3
- verified_post_steps: 1

### Actions

- New demand group [verified]: Starts demand-group setup for the selected shift.
- Assign [verified]: Creates an assignment for the selected demand group.
- Substitute [verified]: Substitutes the selected assignment actor.
- Remove [verified]: Removes the selected assignment.
- Create planning team [verified]: Starts a planning-team create flow for the current planning record context.

### Sections

- Filters and scope: From, To, Planning record, Planning mode
- Demand groups and staffing actions: Demand group, Actor kind, Team, Employee
- Teams and partner releases: Team name, Team scope, Partner releases

### Follow-up

- Continue into outputs and dispatch in P-05

## P-04 de

- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing
- module_key: planning
- status: active
- page_title: Staffing-Board & Coverage
- actions_registered: 5
- verified_sections: 3
- verified_post_steps: 1

### Actions

- Neue Demand Group [verified]: Startet das Demand-Group-Setup für die ausgewählte Schicht.
- Zuweisen [verified]: Erstellt eine Zuweisung für die ausgewählte Demand Group.
- Ersetzen [verified]: Ersetzt den Akteur der ausgewählten Zuweisung.
- Entfernen [verified]: Entfernt die ausgewählte Zuweisung.
- Planungsteam anlegen [verified]: Startet den Anlegefluss für ein Planungsteam im aktuellen Planungsdatensatzkontext.

### Sections

- Filter und Scope: Von, Bis, Planungsdatensatz, Planungsmodus
- Demand Groups und Staffing-Aktionen: Demand Group, Aktor-Typ, Team, Mitarbeiter
- Teams und Partnerfreigaben: Teamname, Team-Scope, Partnerfreigaben

### Follow-up

- Mit P-05 zu Outputs und Dispatch weitergehen

## P-05 en

- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing
- module_key: planning
- status: active
- page_title: Dispatch, Outputs & Subcontractor Releases
- actions_registered: 4
- verified_sections: 2
- verified_post_steps: 1

### Actions

- Generate internal deployment plan [verified]: Generates the internal shift output for the selected shift.
- Generate customer variant [verified]: Generates the customer-facing output variant for the selected shift.
- Load preview [verified]: Loads a dispatch preview for the selected shift and selected audiences.
- Queue message [verified]: Queues a dispatch message for the selected shift and selected audiences.

### Sections

- Outputs and generated documents: Variant, Audience, File name
- Dispatch recipients and preview: Assigned employees, Released subcontractors, Recipients

### Follow-up

- Confirm employee-app visibility with release diagnostics when needed

## P-05 de

- route_name: SicherPlanPlanningStaffing
- path_template: /admin/planning-staffing
- module_key: planning
- status: active
- page_title: Dispatch, Outputs & Partnerfreigaben
- actions_registered: 4
- verified_sections: 2
- verified_post_steps: 1

### Actions

- Internen Einsatzplan erzeugen [verified]: Erzeugt den internen Schichtoutput für die ausgewählte Schicht.
- Kundenvariante erzeugen [verified]: Erzeugt die kundenbezogene Output-Variante für die ausgewählte Schicht.
- Vorschau laden [verified]: Lädt eine Dispatch-Vorschau für die ausgewählte Schicht und die gewählten Zielgruppen.
- Nachricht queueen [verified]: Stellt eine Dispatch-Nachricht für die ausgewählte Schicht und die gewählten Zielgruppen in die Queue.

### Sections

- Outputs und generierte Dokumente: Variante, Zielgruppe, Dateiname
- Dispatch-Empfänger und Vorschau: Zugewiesene Mitarbeiter, Freigegebene Partner, Empfänger

### Follow-up

- Sichtbarkeit in der Mitarbeiter-App bei Bedarf mit Freigabediagnostik bestätigen

## E-01 en

- route_name: SicherPlanEmployees
- path_template: /admin/employees
- module_key: employees
- status: active
- page_title: Employees Workspace
- actions_registered: 1
- verified_sections: 1
- verified_post_steps: 3

### Actions

- Create employee file [verified]: Opens the structured employee file form in create mode.

### Sections

- Identity and personnel number: Personnel number, First name, Last name

### Follow-up

- Complete qualifications
- Complete availability
- Check app access link

## E-01 de

- route_name: SicherPlanEmployees
- path_template: /admin/employees
- module_key: employees
- status: active
- page_title: Mitarbeiter-Workspace
- actions_registered: 1
- verified_sections: 1
- verified_post_steps: 3

### Actions

- Mitarbeiterakte anlegen [verified]: Öffnet die strukturierte Mitarbeiterakte im Anlegemodus.

### Sections

- Identität und Personalnummer: Personalnummer, Vorname, Nachname

### Follow-up

- Qualifikationen vervollständigen
- Verfügbarkeit pflegen
- App-Zugang prüfen
