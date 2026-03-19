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
  | "api.errors.platform.internal";

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
  },
};

