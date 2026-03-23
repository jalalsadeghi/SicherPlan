# US-35 Localization and Accessibility Review

## Scope

Critical go-live surfaces:

- authentication and shell navigation
- planning/staffing admin
- finance actual/payroll/billing admin
- customer and subcontractor portals
- employee mobile schedule, documents, watchbook, patrol, and time capture

## Localization findings

- DE remains default, EN secondary across reviewed surfaces.
- Review-specific fix applied:
  - mobile watchbook copy no longer references an obsolete story placeholder
  - watchbook entry field/button now use watchbook-specific labels instead of notice labels

## Accessibility checklist

- [x] form fields expose meaningful labels on critical reviewed surfaces
- [x] state badges remain textual and not color-only in reviewed portals/admin pages
- [x] mobile action buttons remain labeled in DE/EN resources
- [x] error and empty states remain textual and localized
- [ ] live browser/device screen-reader pass still required before business signoff

## Outstanding limitations

- This repository pass provides checklist evidence and a focused copy fix, not a full certified accessibility audit.
- Print readability still depends on manual signoff against real generated outputs.
