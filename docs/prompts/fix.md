You are working in the SicherPlan repository.

Goal:
Render the actual logged-in employee photo in the green Start/Home hero banner, replacing the current initials fallback.

Primary files:
- mobile/lib/features/home/home_screen.dart
- mobile/lib/widgets/brand_banner.dart
- mobile/lib/api/mobile_backend.dart
- mobile/lib/l10n/app_localizations.dart

Context:
The mobile Start screen currently shows initials (e.g. "MN"), which means the UI fallback works, but the actual employee photo is still not rendered.
Assume the backend/mobile contract now exposes the required employee photo metadata or self-photo fetch path.

Tasks:
1. Update BrandBanner so it supports rendering a real employee photo/avatar.
   - Use the actual logged-in employee photo when available.
   - Keep layout balanced and mobile-first.
   - Ensure clipping, sizing, and spacing are correct on narrow devices.

2. Update HomeScreen so it passes real employee photo data into BrandBanner.
   - Keep the hero card minimal.
   - Preserve the compact greeting.
   - Do not reintroduce removed clutter.

3. Preserve a robust fallback strategy:
   - If the employee has no photo, show initials or a neutral fallback avatar.
   - But if a real photo exists, initials must not be shown.
   - Remove the old static placeholder logic from this hero use case.

4. If image loading requires authenticated requests:
   - implement the smallest robust authenticated image-loading path
   - avoid insecure public URLs
   - keep it scoped to the logged-in employee context

Constraints:
- Do not redesign unrelated screens.
- Do not change auth/session semantics.
- Keep the implementation narrow and production-oriented.
- Favor a minimal, maintainable solution over adding heavy image infrastructure.

Validation:
- Add/update widget tests for:
  - real employee photo rendered when available
  - initials fallback rendered only when no photo is available
  - old placeholder no longer appears
  - narrow mobile layout remains clean
- Ask Codex to self-validate that the final result exactly matches the user request:
  employee photo before “Hallo Markus”.

Before coding:
- Summarize why the screen currently shows initials instead of a real photo.
- State the minimal rendering strategy you will implement.

After coding:
- List changed files.
- Explain whether the final mobile implementation uses:
  - direct photo metadata,
  - authenticated fetch,
  - cached bytes,
  - or another minimal mechanism.
- Mention any remaining polish items that should be deferred.