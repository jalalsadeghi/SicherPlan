export type AppLocale = "de" | "en";

export type MessageKey =
  | "app.title"
  | "locale.label"
  | "locale.de"
  | "locale.en"
  | "theme.toggle.light"
  | "theme.toggle.dark"
  | "theme.mode.light"
  | "theme.mode.dark"
  | "layout.admin.eyebrow"
  | "layout.admin.title"
  | "layout.portal.eyebrow"
  | "layout.portal.title"
  | "brand.adminSubtitle"
  | "brand.portalSubtitle"
  | "role.label"
  | "role.platform_admin"
  | "role.tenant_admin"
  | "role.dispatcher"
  | "role.accounting"
  | "role.controller_qm"
  | "role.customer_user"
  | "role.subcontractor_user"
  | "shell.eyebrow"
  | "shell.title"
  | "shell.lead"
  | "shell.cta.admin"
  | "shell.cta.portal"
  | "shell.stat.roles"
  | "shell.stat.modules"
  | "shell.stat.portals"
  | "module.eyebrow"
  | "module.note.navigation"
  | "module.note.future"
  | "module.note.compatibility"
  | "route.admin.dashboard.title"
  | "route.admin.dashboard.description"
  | "route.admin.core.title"
  | "route.admin.core.description"
  | "route.admin.platform_services.title"
  | "route.admin.platform_services.description"
  | "route.admin.customers.title"
  | "route.admin.customers.description"
  | "route.admin.employees.title"
  | "route.admin.employees.description"
  | "route.admin.subcontractors.title"
  | "route.admin.subcontractors.description"
  | "route.admin.planning.title"
  | "route.admin.planning.description"
  | "route.admin.field_execution.title"
  | "route.admin.field_execution.description"
  | "route.admin.finance.title"
  | "route.admin.finance.description"
  | "route.admin.reporting.title"
  | "route.admin.reporting.description"
  | "route.portal.customer.title"
  | "route.portal.customer.description"
  | "route.portal.subcontractor.title"
  | "route.portal.subcontractor.description"
  | "api.errors.platform.internal"
  | "coreAdmin.eyebrow"
  | "coreAdmin.breadcrumb"
  | "coreAdmin.title"
  | "coreAdmin.lead"
  | "coreAdmin.permission.ready"
  | "coreAdmin.permission.label"
  | "coreAdmin.scope.label"
  | "coreAdmin.scope.placeholder"
  | "coreAdmin.scope.help"
  | "coreAdmin.scope.platformHint"
  | "coreAdmin.scope.emptyTitle"
  | "coreAdmin.scope.emptyBody"
  | "coreAdmin.scope.remembered"
  | "coreAdmin.scope.none"
  | "coreAdmin.actions.refresh"
  | "coreAdmin.actions.loadScopedTenant"
  | "coreAdmin.actions.clearFeedback"
  | "coreAdmin.actions.createTenant"
  | "coreAdmin.actions.saveTenant"
  | "coreAdmin.actions.activate"
  | "coreAdmin.actions.deactivate"
  | "coreAdmin.actions.archive"
  | "coreAdmin.actions.reactivate"
  | "coreAdmin.actions.edit"
  | "coreAdmin.actions.cancel"
  | "coreAdmin.actions.createBranch"
  | "coreAdmin.actions.saveBranch"
  | "coreAdmin.actions.createMandate"
  | "coreAdmin.actions.saveMandate"
  | "coreAdmin.actions.createSetting"
  | "coreAdmin.actions.saveSetting"
  | "coreAdmin.tenants.eyebrow"
  | "coreAdmin.tenants.title"
  | "coreAdmin.tenants.filterPlaceholder"
  | "coreAdmin.tenants.empty"
  | "coreAdmin.tenants.scopeOnly"
  | "coreAdmin.onboarding.eyebrow"
  | "coreAdmin.onboarding.title"
  | "coreAdmin.detail.eyebrow"
  | "coreAdmin.detail.emptyTitle"
  | "coreAdmin.detail.emptyState"
  | "coreAdmin.lifecycle.title"
  | "coreAdmin.lifecycle.archivedHint"
  | "coreAdmin.branches.eyebrow"
  | "coreAdmin.branches.title"
  | "coreAdmin.branches.empty"
  | "coreAdmin.mandates.eyebrow"
  | "coreAdmin.mandates.title"
  | "coreAdmin.mandates.empty"
  | "coreAdmin.settings.eyebrow"
  | "coreAdmin.settings.title"
  | "coreAdmin.settings.empty"
  | "coreAdmin.settings.version"
  | "coreAdmin.fields.tenantCode"
  | "coreAdmin.fields.tenantName"
  | "coreAdmin.fields.legalName"
  | "coreAdmin.fields.defaultLocale"
  | "coreAdmin.fields.defaultCurrency"
  | "coreAdmin.fields.timezone"
  | "coreAdmin.fields.branch"
  | "coreAdmin.fields.branchPlaceholder"
  | "coreAdmin.fields.branchCode"
  | "coreAdmin.fields.branchName"
  | "coreAdmin.fields.branchEmail"
  | "coreAdmin.fields.branchPhone"
  | "coreAdmin.fields.mandateCode"
  | "coreAdmin.fields.mandateName"
  | "coreAdmin.fields.externalRef"
  | "coreAdmin.fields.notes"
  | "coreAdmin.fields.settingKey"
  | "coreAdmin.fields.settingValue"
  | "coreAdmin.fields.settingValueJson"
  | "coreAdmin.status.active"
  | "coreAdmin.status.inactive"
  | "coreAdmin.status.archived"
  | "coreAdmin.feedback.success"
  | "coreAdmin.feedback.error"
  | "coreAdmin.feedback.info"
  | "coreAdmin.feedback.unexpected"
  | "coreAdmin.feedback.invalidJson"
  | "coreAdmin.feedback.tenantCreated"
  | "coreAdmin.feedback.tenantSaved"
  | "coreAdmin.feedback.tenantStatusSaved"
  | "coreAdmin.feedback.branchSaved"
  | "coreAdmin.feedback.branchStatusSaved"
  | "coreAdmin.feedback.mandateSaved"
  | "coreAdmin.feedback.mandateStatusSaved"
  | "coreAdmin.feedback.settingSaved"
  | "coreAdmin.feedback.settingStatusSaved"
  | "coreAdmin.feedback.scopeRemembered"
  | "coreAdmin.api.errors.authorization.forbidden"
  | "coreAdmin.api.errors.tenant.not_found"
  | "coreAdmin.api.errors.branch.not_found"
  | "coreAdmin.api.errors.mandate.not_found"
  | "coreAdmin.api.errors.setting.not_found"
  | "coreAdmin.api.errors.tenant.duplicate_code"
  | "coreAdmin.api.errors.branch.duplicate_code"
  | "coreAdmin.api.errors.mandate.duplicate_code"
  | "coreAdmin.api.errors.setting.duplicate_key"
  | "coreAdmin.api.errors.setting.stale_version"
  | "coreAdmin.api.errors.mandate.invalid_branch_scope"
  | "coreAdmin.api.errors.lifecycle.archived_record"
  | "coreAdmin.api.errors.conflict.integrity"
  | "noticeAdmin.eyebrow"
  | "noticeAdmin.title"
  | "noticeAdmin.lead"
  | "noticeAdmin.scope.label"
  | "noticeAdmin.scope.placeholder"
  | "noticeAdmin.scope.action"
  | "noticeAdmin.scope.missingTitle"
  | "noticeAdmin.scope.missingBody"
  | "noticeAdmin.form.eyebrow"
  | "noticeAdmin.form.title"
  | "noticeAdmin.list.eyebrow"
  | "noticeAdmin.list.title"
  | "noticeAdmin.list.empty"
  | "noticeAdmin.feed.eyebrow"
  | "noticeAdmin.feed.title"
  | "noticeAdmin.feed.empty"
  | "noticeAdmin.feed.acknowledged"
  | "noticeAdmin.fields.title"
  | "noticeAdmin.fields.summary"
  | "noticeAdmin.fields.body"
  | "noticeAdmin.fields.audienceRole"
  | "noticeAdmin.fields.mandatory"
  | "noticeAdmin.actions.create"
  | "noticeAdmin.actions.publish"
  | "noticeAdmin.actions.refresh"
  | "noticeAdmin.actions.acknowledge"
  | "noticeAdmin.feedback.created"
  | "noticeAdmin.feedback.published"
  | "noticeAdmin.feedback.acknowledged"
  | "noticeAdmin.feedback.error";

type MessageCatalog = Record<MessageKey, string>;

export const messages: Record<AppLocale, MessageCatalog> = {
  de: {
    "app.title": "SicherPlan",
    "locale.label": "Sprache",
    "locale.de": "Deutsch",
    "locale.en": "Englisch",
    "theme.toggle.light": "Dunkelmodus",
    "theme.toggle.dark": "Hellmodus",
    "theme.mode.light": "Hell",
    "theme.mode.dark": "Dunkel",
    "layout.admin.eyebrow": "Vben-orientierte Shell",
    "layout.admin.title": "Interner Bereich",
    "layout.portal.eyebrow": "Portalstruktur",
    "layout.portal.title": "Externer Bereich",
    "brand.adminSubtitle": "Admin & Operative Steuerung",
    "brand.portalSubtitle": "Freigegebene Portalansichten",
    "role.label": "Rolle anzeigen",
    "role.platform_admin": "Plattformadmin",
    "role.tenant_admin": "Mandantenadmin",
    "role.dispatcher": "Disponent / Einsatzleitung",
    "role.accounting": "Buchhaltung",
    "role.controller_qm": "Controlling / QM",
    "role.customer_user": "Kundenportal",
    "role.subcontractor_user": "Subunternehmerportal",
    "shell.eyebrow": "SicherPlan Shell",
    "shell.title": "Rollenbasierte Steuerung fuer Security Operations",
    "shell.lead":
      "Diese Startseite zeigt die erste webbasierte Shell mit Admin- und Portalpfaden, jetzt mit zentralen Light/Dark-Token und DE/EN-Lokalisierung fuer spaetere IAM-Arbeit.",
    "shell.cta.admin": "Zum Adminbereich",
    "shell.cta.portal": "Zum Portalbereich",
    "shell.stat.roles": "Rollen",
    "shell.stat.modules": "Modulgruppen",
    "shell.stat.portals": "Portalpfade",
    "module.eyebrow": "Platzhaltermodul",
    "module.note.navigation":
      "Navigation und Rollenfreigaben sind bereits im Shell-Register hinterlegt.",
    "module.note.future":
      "CRUD-Ansichten, Formulare und Reportings folgen in spaeteren Aufgaben.",
    "module.note.compatibility":
      "Die Shell bleibt kompatibel mit spaeterer RBAC-, Theme- und i18n-Erweiterung.",
    "route.admin.dashboard.title": "Dashboard",
    "route.admin.dashboard.description":
      "Startpunkt fuer interne Rollen mit Schnellzugriff auf Kernmodule.",
    "route.admin.core.title": "Kernsystem",
    "route.admin.core.description":
      "Mandanten, Niederlassungen, Nummernkreise und zentrale Einstellungen.",
    "route.admin.platform_services.title": "Plattformdienste",
    "route.admin.platform_services.description":
      "Dokumente, Kommunikation, Hinweise und Integrationsjobs.",
    "route.admin.customers.title": "Kunden",
    "route.admin.customers.description":
      "Stammdaten, Kontakte, Abrechnungsvorgaben und Portalfreigaben.",
    "route.admin.employees.title": "Mitarbeitende",
    "route.admin.employees.description":
      "Recruiting, Personalakte, Verfuegbarkeit und Qualifikationen.",
    "route.admin.subcontractors.title": "Subunternehmer",
    "route.admin.subcontractors.description":
      "Partnerfirmen, Einsatzfreigaben und Compliance-Status.",
    "route.admin.planning.title": "Planung",
    "route.admin.planning.description":
      "Objekte, Auftraege, Schichtplaene, Validierung und Freigaben.",
    "route.admin.field_execution.title": "Feldeinsatz",
    "route.admin.field_execution.description":
      "Wachbuch, Streifengaenge, Zeiterfassung und mobile Rueckmeldungen.",
    "route.admin.finance.title": "Finanzen",
    "route.admin.finance.description":
      "Actuals, Lohnexporte, Rechnungen und Partnerpruefungen.",
    "route.admin.reporting.title": "Reporting",
    "route.admin.reporting.description":
      "Operative, kaufmaennische und Compliance-Auswertungen.",
    "route.portal.customer.title": "Kundenportal",
    "route.portal.customer.description":
      "Freigegebene Auftraege, Berichte, Zeiten und Dokumente.",
    "route.portal.subcontractor.title": "Subunternehmerportal",
    "route.portal.subcontractor.description":
      "Freigegebene Einsaetze, Mitarbeitende und Rueckmeldungen im freigegebenen Umfang.",
    "api.errors.platform.internal":
      "Es ist ein interner Plattformfehler aufgetreten.",
    "coreAdmin.breadcrumb": "Admin / Kernsystem / Mandantenverwaltung",
    "coreAdmin.eyebrow": "Core Administration",
    "coreAdmin.title": "Mandantenstruktur und Kernsteuerung",
    "coreAdmin.lead":
      "Diese Verwaltungsseite bindet direkt an die Core-Admin-APIs an und fuehrt Mandanten, Niederlassungen, Mandate und Einstellungen ohne lokale Mock-Wahrheit.",
    "coreAdmin.permission.ready": "RBAC-bereite Route",
    "coreAdmin.permission.label": "Berechtigungsschluessel",
    "coreAdmin.scope.label": "Mandanten-Scope",
    "coreAdmin.scope.placeholder": "Tenant-UUID fuer Tenant-Admin-Modus",
    "coreAdmin.scope.help":
      "Im temporaren Mock-Auth-Modus wird diese UUID als X-Tenant-Id an das Backend uebergeben.",
    "coreAdmin.scope.platformHint":
      "Plattformadmins sehen die tenant-uebergreifende Liste. Der Scope wird fuer spaeteres Tenant-Admin-Switching gemerkt.",
    "coreAdmin.scope.emptyTitle": "Tenant-Scope fehlt",
    "coreAdmin.scope.emptyBody":
      "Mandantenadmins brauchen eine gespeicherte Tenant-UUID, bevor Listen- und Detailaufrufe geladen werden koennen.",
    "coreAdmin.scope.remembered": "Gemerkter Scope",
    "coreAdmin.scope.none": "keiner",
    "coreAdmin.actions.refresh": "Neu laden",
    "coreAdmin.actions.loadScopedTenant": "Scope laden",
    "coreAdmin.actions.clearFeedback": "Hinweis schliessen",
    "coreAdmin.actions.createTenant": "Mandant anlegen",
    "coreAdmin.actions.saveTenant": "Mandant speichern",
    "coreAdmin.actions.activate": "Aktivieren",
    "coreAdmin.actions.deactivate": "Deaktivieren",
    "coreAdmin.actions.archive": "Archivieren",
    "coreAdmin.actions.reactivate": "Reaktivieren",
    "coreAdmin.actions.edit": "Bearbeiten",
    "coreAdmin.actions.cancel": "Abbrechen",
    "coreAdmin.actions.createBranch": "Niederlassung anlegen",
    "coreAdmin.actions.saveBranch": "Niederlassung speichern",
    "coreAdmin.actions.createMandate": "Mandat anlegen",
    "coreAdmin.actions.saveMandate": "Mandat speichern",
    "coreAdmin.actions.createSetting": "Einstellung anlegen",
    "coreAdmin.actions.saveSetting": "Einstellung speichern",
    "coreAdmin.tenants.eyebrow": "Mandantenuebersicht",
    "coreAdmin.tenants.title": "Mandanten",
    "coreAdmin.tenants.filterPlaceholder": "Nach Code oder Name filtern",
    "coreAdmin.tenants.empty": "Noch keine Mandanten vorhanden.",
    "coreAdmin.tenants.scopeOnly":
      "Im Tenant-Admin-Modus wird nur der scoped Mandant geladen.",
    "coreAdmin.onboarding.eyebrow": "Onboarding",
    "coreAdmin.onboarding.title": "Neuen Mandanten mit Basissatz anlegen",
    "coreAdmin.detail.eyebrow": "Detail und Pflege",
    "coreAdmin.detail.emptyTitle": "Kein Mandant ausgewaehlt",
    "coreAdmin.detail.emptyState":
      "Waehlen Sie links einen Mandanten aus, um Stammdaten, Niederlassungen, Mandate und Einstellungen zu pflegen.",
    "coreAdmin.lifecycle.title": "Lifecycle und Archivstatus",
    "coreAdmin.lifecycle.archivedHint":
      "Archivierte Mandanten bleiben explizit erhalten und koennen ueber den aktuellen Backend-Contract nicht wieder aktiviert werden.",
    "coreAdmin.branches.eyebrow": "Niederlassungen",
    "coreAdmin.branches.title": "Niederlassungsverwaltung",
    "coreAdmin.branches.empty": "Es sind noch keine Niederlassungen vorhanden.",
    "coreAdmin.mandates.eyebrow": "Mandate",
    "coreAdmin.mandates.title": "Mandatsverwaltung",
    "coreAdmin.mandates.empty": "Es sind noch keine Mandate vorhanden.",
    "coreAdmin.settings.eyebrow": "Mandanteneinstellungen",
    "coreAdmin.settings.title": "Sichere Einstellungen",
    "coreAdmin.settings.empty": "Es sind noch keine Einstellungen vorhanden.",
    "coreAdmin.settings.version": "Version",
    "coreAdmin.fields.tenantCode": "Mandantencode",
    "coreAdmin.fields.tenantName": "Mandantenname",
    "coreAdmin.fields.legalName": "Rechtlicher Name",
    "coreAdmin.fields.defaultLocale": "Standard-Sprache",
    "coreAdmin.fields.defaultCurrency": "Standard-Waehrung",
    "coreAdmin.fields.timezone": "Zeitzone",
    "coreAdmin.fields.branch": "Niederlassung",
    "coreAdmin.fields.branchPlaceholder": "Niederlassung waehlen",
    "coreAdmin.fields.branchCode": "Niederlassungscode",
    "coreAdmin.fields.branchName": "Niederlassungsname",
    "coreAdmin.fields.branchEmail": "Kontakt-E-Mail",
    "coreAdmin.fields.branchPhone": "Kontakt-Telefon",
    "coreAdmin.fields.mandateCode": "Mandatscode",
    "coreAdmin.fields.mandateName": "Mandatsname",
    "coreAdmin.fields.externalRef": "Externe Referenz",
    "coreAdmin.fields.notes": "Notizen",
    "coreAdmin.fields.settingKey": "Einstellungsschluessel",
    "coreAdmin.fields.settingValue": "Initialer Einstellungswert (JSON)",
    "coreAdmin.fields.settingValueJson": "JSON-Wert",
    "coreAdmin.status.active": "Aktiv",
    "coreAdmin.status.inactive": "Inaktiv",
    "coreAdmin.status.archived": "Archiviert",
    "coreAdmin.feedback.success": "Erfolg",
    "coreAdmin.feedback.error": "Fehler",
    "coreAdmin.feedback.info": "Hinweis",
    "coreAdmin.feedback.unexpected":
      "Die Core-Administration konnte die Aktion nicht abschliessen.",
    "coreAdmin.feedback.invalidJson":
      "Bitte geben Sie ein gueltiges JSON-Objekt fuer Einstellungen an.",
    "coreAdmin.feedback.tenantCreated": "Mandant und Basissatz wurden angelegt.",
    "coreAdmin.feedback.tenantSaved": "Mandantenstammdaten wurden gespeichert.",
    "coreAdmin.feedback.tenantStatusSaved": "Mandantenstatus wurde aktualisiert.",
    "coreAdmin.feedback.branchSaved": "Niederlassung wurde gespeichert.",
    "coreAdmin.feedback.branchStatusSaved": "Niederlassungsstatus wurde aktualisiert.",
    "coreAdmin.feedback.mandateSaved": "Mandat wurde gespeichert.",
    "coreAdmin.feedback.mandateStatusSaved": "Mandatsstatus wurde aktualisiert.",
    "coreAdmin.feedback.settingSaved": "Einstellung wurde gespeichert.",
    "coreAdmin.feedback.settingStatusSaved": "Einstellungsstatus wurde aktualisiert.",
    "coreAdmin.feedback.scopeRemembered": "Der Tenant-Scope wurde fuer den Tenant-Admin-Modus gemerkt.",
    "coreAdmin.api.errors.authorization.forbidden":
      "Diese Rolle darf die angeforderte Core-Administration nicht ausfuehren.",
    "coreAdmin.api.errors.tenant.not_found": "Mandant nicht gefunden.",
    "coreAdmin.api.errors.branch.not_found": "Niederlassung nicht gefunden.",
    "coreAdmin.api.errors.mandate.not_found": "Mandat nicht gefunden.",
    "coreAdmin.api.errors.setting.not_found": "Mandanteneinstellung nicht gefunden.",
    "coreAdmin.api.errors.tenant.duplicate_code":
      "Der Mandantencode existiert bereits.",
    "coreAdmin.api.errors.branch.duplicate_code":
      "Der Niederlassungscode existiert in diesem Mandanten bereits.",
    "coreAdmin.api.errors.mandate.duplicate_code":
      "Der Mandatscode existiert in diesem Mandanten bereits.",
    "coreAdmin.api.errors.setting.duplicate_key":
      "Dieser Einstellungsschluessel existiert bereits.",
    "coreAdmin.api.errors.setting.stale_version":
      "Die Einstellung wurde zwischenzeitlich geaendert. Bitte neu laden und erneut speichern.",
    "coreAdmin.api.errors.mandate.invalid_branch_scope":
      "Die gewaehlte Niederlassung gehoert nicht zu diesem Mandanten.",
    "coreAdmin.api.errors.lifecycle.archived_record":
      "Archivierte Datensaetze bleiben archiviert und koennen nicht ueber diesen Pfad reaktiviert werden.",
    "coreAdmin.api.errors.conflict.integrity":
      "Die Aenderung verletzt eine Integritaetsregel im Core-Backbone.",
    "noticeAdmin.eyebrow": "Plattformdienste / Hinweise",
    "noticeAdmin.title": "Hinweise, Zielgruppen und Bestaetigungen",
    "noticeAdmin.lead":
      "Diese Minimalansicht bindet an die Notice-APIs an: Entwurf anlegen, veroeffentlichen und die eigene Feed-Sicht pruefen.",
    "noticeAdmin.scope.label": "Mandanten-Scope",
    "noticeAdmin.scope.placeholder": "Tenant-UUID fuer Notice-APIs",
    "noticeAdmin.scope.action": "Scope merken",
    "noticeAdmin.scope.missingTitle": "Mandanten-Scope fehlt",
    "noticeAdmin.scope.missingBody":
      "Fuer die Hinweisfluesse wird eine Tenant-UUID benoetigt, damit Admin- und Feed-Aufrufe tenant-sicher bleiben.",
    "noticeAdmin.form.eyebrow": "Hinweisentwurf",
    "noticeAdmin.form.title": "Neuen Hinweis anlegen",
    "noticeAdmin.list.eyebrow": "Adminliste",
    "noticeAdmin.list.title": "Entwuerfe und veroeffentlichte Hinweise",
    "noticeAdmin.list.empty": "Noch keine Hinweise fuer diesen Tenant vorhanden.",
    "noticeAdmin.feed.eyebrow": "Meine Feed-Sicht",
    "noticeAdmin.feed.title": "Sichtbare Hinweise fuer die aktuelle Rolle",
    "noticeAdmin.feed.empty": "Aktuell ist fuer die Rolle kein Hinweis sichtbar.",
    "noticeAdmin.feed.acknowledged": "Bestaetigt",
    "noticeAdmin.fields.title": "Titel",
    "noticeAdmin.fields.summary": "Kurztext",
    "noticeAdmin.fields.body": "Inhalt",
    "noticeAdmin.fields.audienceRole": "Rollen-Zielgruppe",
    "noticeAdmin.fields.mandatory": "Bestaetigung erforderlich",
    "noticeAdmin.actions.create": "Entwurf speichern",
    "noticeAdmin.actions.publish": "Veroeffentlichen",
    "noticeAdmin.actions.refresh": "Neu laden",
    "noticeAdmin.actions.acknowledge": "Bestaetigen",
    "noticeAdmin.feedback.created": "Hinweis angelegt",
    "noticeAdmin.feedback.published": "Hinweis veroeffentlicht",
    "noticeAdmin.feedback.acknowledged": "Hinweis bestaetigt",
    "noticeAdmin.feedback.error": "Notice-Aktion fehlgeschlagen.",
  },
  en: {
    "app.title": "SicherPlan",
    "locale.label": "Language",
    "locale.de": "German",
    "locale.en": "English",
    "theme.toggle.light": "Dark mode",
    "theme.toggle.dark": "Light mode",
    "theme.mode.light": "Light",
    "theme.mode.dark": "Dark",
    "layout.admin.eyebrow": "Vben-oriented shell",
    "layout.admin.title": "Internal area",
    "layout.portal.eyebrow": "Portal structure",
    "layout.portal.title": "External area",
    "brand.adminSubtitle": "Admin and operations control",
    "brand.portalSubtitle": "Released portal views",
    "role.label": "View role",
    "role.platform_admin": "Platform admin",
    "role.tenant_admin": "Tenant admin",
    "role.dispatcher": "Dispatcher / field lead",
    "role.accounting": "Accounting",
    "role.controller_qm": "Controlling / QA",
    "role.customer_user": "Customer portal",
    "role.subcontractor_user": "Subcontractor portal",
    "shell.eyebrow": "SicherPlan shell",
    "shell.title": "Role-based control for security operations",
    "shell.lead":
      "This landing page shows the first web shell with admin and portal paths, now with centralized light/dark tokens and DE/EN localization for later IAM work.",
    "shell.cta.admin": "Open admin area",
    "shell.cta.portal": "Open portal area",
    "shell.stat.roles": "Roles",
    "shell.stat.modules": "Module groups",
    "shell.stat.portals": "Portal paths",
    "module.eyebrow": "Placeholder module",
    "module.note.navigation":
      "Navigation and role visibility are already registered in the shell.",
    "module.note.future":
      "CRUD views, forms, and reporting will follow in later tasks.",
    "module.note.compatibility":
      "The shell stays compatible with later RBAC, theme, and i18n expansion.",
    "route.admin.dashboard.title": "Dashboard",
    "route.admin.dashboard.description":
      "Starting point for internal roles with quick access to core modules.",
    "route.admin.core.title": "Core system",
    "route.admin.core.description":
      "Tenants, branches, numbering ranges, and central settings.",
    "route.admin.platform_services.title": "Platform services",
    "route.admin.platform_services.description":
      "Documents, communication, notices, and integration jobs.",
    "route.admin.customers.title": "Customers",
    "route.admin.customers.description":
      "Master data, contacts, billing rules, and portal releases.",
    "route.admin.employees.title": "Employees",
    "route.admin.employees.description":
      "Recruiting, personnel file, availability, and qualifications.",
    "route.admin.subcontractors.title": "Subcontractors",
    "route.admin.subcontractors.description":
      "Partner companies, assignment releases, and compliance status.",
    "route.admin.planning.title": "Planning",
    "route.admin.planning.description":
      "Sites, orders, shift plans, validation, and releases.",
    "route.admin.field_execution.title": "Field execution",
    "route.admin.field_execution.description":
      "Watchbook, patrol rounds, time capture, and mobile feedback.",
    "route.admin.finance.title": "Finance",
    "route.admin.finance.description":
      "Actuals, payroll exports, invoices, and partner checks.",
    "route.admin.reporting.title": "Reporting",
    "route.admin.reporting.description":
      "Operational, commercial, and compliance reporting.",
    "route.portal.customer.title": "Customer portal",
    "route.portal.customer.description":
      "Released orders, reports, times, and documents.",
    "route.portal.subcontractor.title": "Subcontractor portal",
    "route.portal.subcontractor.description":
      "Released assignments, workers, and feedback within released scope.",
    "api.errors.platform.internal":
      "An internal platform error has occurred.",
    "coreAdmin.breadcrumb": "Admin / Core system / Tenant administration",
    "coreAdmin.eyebrow": "Core administration",
    "coreAdmin.title": "Tenant backbone and core control",
    "coreAdmin.lead":
      "This page binds directly to the core admin APIs and manages tenants, branches, mandates, and settings without a local mock source of truth.",
    "coreAdmin.permission.ready": "RBAC-ready route",
    "coreAdmin.permission.label": "Permission key",
    "coreAdmin.scope.label": "Tenant scope",
    "coreAdmin.scope.placeholder": "Tenant UUID for tenant-admin mode",
    "coreAdmin.scope.help":
      "In the temporary mock-auth mode this UUID is sent to the backend as X-Tenant-Id.",
    "coreAdmin.scope.platformHint":
      "Platform admins see the cross-tenant list. The current tenant scope is remembered for later tenant-admin switching.",
    "coreAdmin.scope.emptyTitle": "Tenant scope missing",
    "coreAdmin.scope.emptyBody":
      "Tenant admins need a remembered tenant UUID before list and detail requests can load.",
    "coreAdmin.scope.remembered": "Remembered scope",
    "coreAdmin.scope.none": "none",
    "coreAdmin.actions.refresh": "Refresh",
    "coreAdmin.actions.loadScopedTenant": "Load scope",
    "coreAdmin.actions.clearFeedback": "Dismiss notice",
    "coreAdmin.actions.createTenant": "Create tenant",
    "coreAdmin.actions.saveTenant": "Save tenant",
    "coreAdmin.actions.activate": "Activate",
    "coreAdmin.actions.deactivate": "Deactivate",
    "coreAdmin.actions.archive": "Archive",
    "coreAdmin.actions.reactivate": "Reactivate",
    "coreAdmin.actions.edit": "Edit",
    "coreAdmin.actions.cancel": "Cancel",
    "coreAdmin.actions.createBranch": "Create branch",
    "coreAdmin.actions.saveBranch": "Save branch",
    "coreAdmin.actions.createMandate": "Create mandate",
    "coreAdmin.actions.saveMandate": "Save mandate",
    "coreAdmin.actions.createSetting": "Create setting",
    "coreAdmin.actions.saveSetting": "Save setting",
    "coreAdmin.tenants.eyebrow": "Tenant overview",
    "coreAdmin.tenants.title": "Tenants",
    "coreAdmin.tenants.filterPlaceholder": "Filter by code or name",
    "coreAdmin.tenants.empty": "No tenants exist yet.",
    "coreAdmin.tenants.scopeOnly":
      "In tenant-admin mode only the scoped tenant is loaded.",
    "coreAdmin.onboarding.eyebrow": "Onboarding",
    "coreAdmin.onboarding.title": "Create a new tenant with baseline records",
    "coreAdmin.detail.eyebrow": "Detail and maintenance",
    "coreAdmin.detail.emptyTitle": "No tenant selected",
    "coreAdmin.detail.emptyState":
      "Select a tenant on the left to maintain tenant data, branches, mandates, and settings.",
    "coreAdmin.lifecycle.title": "Lifecycle and archive state",
    "coreAdmin.lifecycle.archivedHint":
      "Archived tenants remain explicit historical records and cannot be reactivated through the current backend contract.",
    "coreAdmin.branches.eyebrow": "Branches",
    "coreAdmin.branches.title": "Branch maintenance",
    "coreAdmin.branches.empty": "No branches exist yet.",
    "coreAdmin.mandates.eyebrow": "Mandates",
    "coreAdmin.mandates.title": "Mandate maintenance",
    "coreAdmin.mandates.empty": "No mandates exist yet.",
    "coreAdmin.settings.eyebrow": "Tenant settings",
    "coreAdmin.settings.title": "Safe settings editor",
    "coreAdmin.settings.empty": "No settings exist yet.",
    "coreAdmin.settings.version": "Version",
    "coreAdmin.fields.tenantCode": "Tenant code",
    "coreAdmin.fields.tenantName": "Tenant name",
    "coreAdmin.fields.legalName": "Legal name",
    "coreAdmin.fields.defaultLocale": "Default locale",
    "coreAdmin.fields.defaultCurrency": "Default currency",
    "coreAdmin.fields.timezone": "Timezone",
    "coreAdmin.fields.branch": "Branch",
    "coreAdmin.fields.branchPlaceholder": "Select branch",
    "coreAdmin.fields.branchCode": "Branch code",
    "coreAdmin.fields.branchName": "Branch name",
    "coreAdmin.fields.branchEmail": "Contact email",
    "coreAdmin.fields.branchPhone": "Contact phone",
    "coreAdmin.fields.mandateCode": "Mandate code",
    "coreAdmin.fields.mandateName": "Mandate name",
    "coreAdmin.fields.externalRef": "External reference",
    "coreAdmin.fields.notes": "Notes",
    "coreAdmin.fields.settingKey": "Setting key",
    "coreAdmin.fields.settingValue": "Initial setting value (JSON)",
    "coreAdmin.fields.settingValueJson": "JSON value",
    "coreAdmin.status.active": "Active",
    "coreAdmin.status.inactive": "Inactive",
    "coreAdmin.status.archived": "Archived",
    "coreAdmin.feedback.success": "Success",
    "coreAdmin.feedback.error": "Error",
    "coreAdmin.feedback.info": "Info",
    "coreAdmin.feedback.unexpected":
      "The core administration page could not complete the action.",
    "coreAdmin.feedback.invalidJson":
      "Please provide a valid JSON object for settings.",
    "coreAdmin.feedback.tenantCreated": "Tenant and baseline records were created.",
    "coreAdmin.feedback.tenantSaved": "Tenant master data was saved.",
    "coreAdmin.feedback.tenantStatusSaved": "Tenant lifecycle state was updated.",
    "coreAdmin.feedback.branchSaved": "Branch was saved.",
    "coreAdmin.feedback.branchStatusSaved": "Branch lifecycle state was updated.",
    "coreAdmin.feedback.mandateSaved": "Mandate was saved.",
    "coreAdmin.feedback.mandateStatusSaved": "Mandate lifecycle state was updated.",
    "coreAdmin.feedback.settingSaved": "Setting was saved.",
    "coreAdmin.feedback.settingStatusSaved": "Setting lifecycle state was updated.",
    "coreAdmin.feedback.scopeRemembered":
      "The tenant scope was remembered for tenant-admin mode.",
    "coreAdmin.api.errors.authorization.forbidden":
      "This role is not allowed to perform the requested core administration action.",
    "coreAdmin.api.errors.tenant.not_found": "Tenant not found.",
    "coreAdmin.api.errors.branch.not_found": "Branch not found.",
    "coreAdmin.api.errors.mandate.not_found": "Mandate not found.",
    "coreAdmin.api.errors.setting.not_found": "Tenant setting not found.",
    "coreAdmin.api.errors.tenant.duplicate_code":
      "The tenant code already exists.",
    "coreAdmin.api.errors.branch.duplicate_code":
      "The branch code already exists in this tenant.",
    "coreAdmin.api.errors.mandate.duplicate_code":
      "The mandate code already exists in this tenant.",
    "coreAdmin.api.errors.setting.duplicate_key":
      "This setting key already exists.",
    "coreAdmin.api.errors.setting.stale_version":
      "The setting changed in the meantime. Refresh and save again.",
    "coreAdmin.api.errors.mandate.invalid_branch_scope":
      "The selected branch does not belong to this tenant.",
    "coreAdmin.api.errors.lifecycle.archived_record":
      "Archived records remain archived and cannot be reactivated through this path.",
    "coreAdmin.api.errors.conflict.integrity":
      "The change violates a core backbone integrity rule.",
    "noticeAdmin.eyebrow": "Platform services / notices",
    "noticeAdmin.title": "Notices, audiences, and acknowledgements",
    "noticeAdmin.lead":
      "This minimal view binds to the notice APIs: create a draft, publish it, and check the current user's feed.",
    "noticeAdmin.scope.label": "Tenant scope",
    "noticeAdmin.scope.placeholder": "Tenant UUID for notice APIs",
    "noticeAdmin.scope.action": "Remember scope",
    "noticeAdmin.scope.missingTitle": "Tenant scope missing",
    "noticeAdmin.scope.missingBody":
      "The notice flows need a tenant UUID so admin and feed requests remain tenant-safe.",
    "noticeAdmin.form.eyebrow": "Notice draft",
    "noticeAdmin.form.title": "Create a new notice",
    "noticeAdmin.list.eyebrow": "Admin list",
    "noticeAdmin.list.title": "Draft and published notices",
    "noticeAdmin.list.empty": "No notices exist for this tenant yet.",
    "noticeAdmin.feed.eyebrow": "My feed",
    "noticeAdmin.feed.title": "Visible notices for the current role",
    "noticeAdmin.feed.empty": "No notice is currently visible for this role.",
    "noticeAdmin.feed.acknowledged": "Acknowledged",
    "noticeAdmin.fields.title": "Title",
    "noticeAdmin.fields.summary": "Summary",
    "noticeAdmin.fields.body": "Body",
    "noticeAdmin.fields.audienceRole": "Audience role",
    "noticeAdmin.fields.mandatory": "Acknowledgement required",
    "noticeAdmin.actions.create": "Save draft",
    "noticeAdmin.actions.publish": "Publish",
    "noticeAdmin.actions.refresh": "Refresh",
    "noticeAdmin.actions.acknowledge": "Acknowledge",
    "noticeAdmin.feedback.created": "Notice created",
    "noticeAdmin.feedback.published": "Notice published",
    "noticeAdmin.feedback.acknowledged": "Notice acknowledged",
    "noticeAdmin.feedback.error": "The notice action failed.",
  },
};
