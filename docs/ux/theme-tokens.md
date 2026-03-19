# US-3-T3 Theme Tokens

## Baseline

`US-3-T3` centralizes the first shared theme baseline for web and mobile. Both shells use the exact required primary colors:

- Light primary: `rgb(40,170,170)`
- Dark primary: `rgb(35,200,205)`

## Shared naming

The framework implementations now align on these token concepts:

- `primary`
- `primaryStrong`
- `primaryMuted`
- `success`
- `warning`
- `danger`
- `surfacePage`
- `surfacePanel`
- `surfaceCard`
- `surfaceSidebar` on web
- `borderSoft`
- `textPrimary`
- `textSecondary`
- `textInverse`

## Web

- Token source: `web/src/theme/tokens.ts`
- Runtime state: `web/src/stores/theme.ts`
- Consumption: CSS custom properties applied in `web/src/App.vue` and consumed in `web/src/styles.css`
- Demo toggle: header button in admin and portal layouts

The web shell uses CSS variables so later modules can consume tokens without importing raw RGB values into each component.

## Mobile

- Token source: `mobile/lib/app/theme_tokens.dart`
- Theme builder: `mobile/lib/app/sicherplan_theme.dart`
- Demo toggle: profile/settings screen switch

The mobile shell uses framework-native `ThemeData` wiring. Tokens are converted into `ColorScheme`, card, navigation, input, switch, and text defaults so later screens inherit the baseline rather than redefining colors locally.

## Guardrails

- Do not replace the approved primaries with a broader palette.
- Semantic colors should stay conservative and support readability first.
- New user-facing UI should consume the centralized token layer before introducing new color values.
- `US-3-T4` should attach DE/EN resource keys to theme toggle labels instead of leaving them inline.
