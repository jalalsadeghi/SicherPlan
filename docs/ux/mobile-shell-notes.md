# US-3-T2 Mobile Shell Notes

## Scope

`US-3-T2` introduces the first Flutter shell for employee and field workflows. The structure is intentionally limited to navigation, placeholder screens, and session scaffolding so later tasks can add i18n resources, offline sync, and real feature logic without reorganizing the app. `US-3-T3` now supplies the shared theme-token layer on top of that shell.

## Shell structure

- `mobile/lib/app/` holds app bootstrap and shared theme wiring.
- `mobile/lib/navigation/` owns destination definitions and the shell controller.
- `mobile/lib/session/` defines the provisional mobile role/session model for employee, field supervisor, and restricted field-execution views.
- `mobile/lib/features/` contains placeholder screens for home, schedule, information feed, time capture, watchbook/patrol, and profile/settings.
- `mobile/lib/widgets/` contains reusable shell cards and layout components.
- `mobile/lib/l10n/` now provides the DE-default / EN-secondary localization baseline for the shell.

## Design decisions

- Navigation uses a single bottom `NavigationBar` because it maps cleanly to the early employee/field flows and leaves room for role-scoped visibility.
- The shell now routes visible text through a localization delegate so DE and EN can be switched at runtime from the profile/settings view.
- Theme colors are read from `AppConfig` and now flow through centralized Flutter theme tokens so later screens inherit the same baseline.
- Time-capture and patrol placeholders explicitly call out offline readiness and append-only evidence expectations without implementing the workflows yet.

## Branding note

The prompt references `app_icon.png`, but that asset does not exist in the current repository state. The generated Flutter launcher icons remain in place for now, and the in-app shell uses a lightweight `SP` brand mark inside the dashboard banner. Once the real `app_icon.png` file is added to the repo, it should replace the generated launcher icons and any temporary shell mark.
