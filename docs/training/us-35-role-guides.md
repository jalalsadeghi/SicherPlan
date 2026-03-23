# US-35 Role Guides

## Language rule

The training pack is authored in German first. English terminology follows in parentheses where useful for bilingual onboarding.

## Platform admin

- Ziele: Tenant-Onboarding, Seed-/Konfigurationspruefung, Reporting-/Hardening-Nachweise.
- Hauptpfade: Core-Admin, Reporting, Seed-/Runbook-Skripte.
- Nicht lehren: operative HR-, Kunden- oder Partner-Sichten als Standardarbeitsweise.

## Tenant admin

- Ziele: Mandantenstammdaten, Benutzer-/Rollenpflege, Konfigurationskontrolle.
- Hauptpfade: CRM, HR, Partner, Planung, Finanzen.
- Datenschutz-Hinweis: HR-private Daten und Portal-Sichten nur innerhalb freigegebener Rollen.

## Dispatcher

- Ziele: Auftraege, Planungsdatensaetze, Schichten, Staffing, Releases.
- Hauptpfade: `PlanningOrdersAdminView`, `PlanningShiftsAdminView`, `PlanningStaffingCoverageView`.
- Uebung: Auftrag freigeben, Schicht pruefen, Staffing-Validierung lesen, Override-Regeln verstehen.

## Accounting

- Ziele: Actual-Pruefung, Payroll, Leistungsnachweise, Rechnungen, Partnerkontrolle.
- Hauptpfade: `FinanceActualApprovalView`, `FinancePayrollAdminView`, `FinanceBillingAdminView`, `FinanceSubcontractorInvoiceChecksView`.
- Uebung: Actual bis Signoff nachverfolgen, Timesheet/Invoice erzeugen, Partnerabweichung lesen.

## Controller / QM

- Ziele: Compliance-, QM- und Sicherheitsreports verstehen und exportieren.
- Hauptpfade: `ReportingDashboardView`.
- Uebung: Report filtern, CSV exportieren, Auslieferung vormerken.

## Customer portal user

- Ziele: freigegebene Einsaetze, Wachbuecher, Leistungsnachweise und Rechnungen lesen.
- Hauptpfade: `CustomerPortalAccessView`.
- Scope reminder: nur eigene Kundensicht; Personennamen nur bei expliziter Freigabe.

## Subcontractor admin / user

- Ziele: eigene Mitarbeitenden pflegen, freigegebene Einsaetze und Invoice Checks pruefen.
- Hauptpfade: `SubcontractorPortalAccessView`.
- Scope reminder: keine internen Finance-Notizen oder fremden Partnerdaten.

## Employee app user

- Ziele: freigegebene Schichten, Dokumente, Watchbook, Patrouille, Zeiterfassung und Profil nutzen.
- Hauptpfade: mobile schedule/documents/watchbook/patrol/time/profile flows.
- Scope reminder: nur eigener Mitarbeiterkontext.
