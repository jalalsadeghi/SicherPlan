# US-3-T4 Localization Rules

## Baseline

SicherPlan uses:

- German (`de`) as the default locale
- English (`en`) as the secondary locale

Every new user-facing string added after Sprint 1 must ship in both locales in the same change set.

## Web rules

- Locale resources live under `web/src/i18n/`.
- Components should read UI text through `useI18n()` instead of hardcoding labels.
- Route metadata should store translation keys, not already translated labels.
- The locale store remains the runtime source of truth for shell rendering and fallback behavior.

## Mobile rules

- Mobile resources live under `mobile/lib/l10n/`.
- Widgets should use `context.l10n` for user-facing text.
- `MaterialApp` owns the active locale and supported locale list.
- Feature modules should not embed DE-only or EN-only labels directly inside widgets once a localization helper exists.

## API and backend rules

- API responses should prefer stable `message_key` values and machine-readable `code` values over inline localized prose.
- Clients should localize known `message_key` values using their own resource bundles whenever possible.
- Backend message catalogs are still useful for logs, admin tooling, fallback rendering, and future notification/document generation.
- Validation and domain errors should follow a stable namespaced key pattern, for example:
  - `errors.platform.internal`
  - `errors.iam.invalid_credentials`
  - `errors.planning.shift_conflict`

## Key naming

- Use lowercase dot-separated keys.
- Scope by area first, then message intent.
- Prefer semantic names over screen-specific phrasing.
- Keep interpolation placeholders explicit, for example `{userName}` or `{count}`.

## Fallback behavior

- Web and mobile should default to German.
- English is the required fallback and alternate selection.
- Unknown keys should fail visibly in development rather than silently inventing text.

## Formatting guidance

- Dates, times, numbers, and currencies should be locale-aware when the real domain views are implemented.
- Do not bake locale-specific formatting into backend message keys.
- Keep documents, notifications, and exports on the same message-key discipline so DE/EN parity can be audited later.

## Sprint-1 expectation

`US-3-T4` covers the current shell, route/menu labels, theme/locale controls, and baseline API error localization rules. Later tasks must extend the same DE/EN resource sets instead of reintroducing inline strings.
