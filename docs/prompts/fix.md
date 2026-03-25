You are working inside the SicherPlan monorepo.

Task:
Fix the dark-mode logo switching for the upper-left shell/sidebar brand in the web-antd app.

Current problem:
The custom SicherPlan logo now renders, but when dark theme is active the app still shows the light logo instead of the dedicated dark-mode logo.

Known context:
- Light logo file exists at: /branding/sicherplan-logo-512.png
- Dark logo file exists at: /branding/sicherplan-logo-dark-512.png
- The app uses a Vben-based shell layout
- The current issue is most likely caused by one or more of these:
  1. preferences.logo.sourceDark is not correctly set at runtime
  2. a previous localStorage-cached preferences object is overriding the new defaults
  3. one of the actual shell logo render paths still does not receive :src-dark
  4. an earlier migration/fallback may still be forcing sourceDark to the light logo

Important constraints:
1. Do NOT change routing, permissions, menus, shell structure, or business logic.
2. Do NOT change the existing text block:
   - SicherPlan
   - Security Operations Platform
3. Do NOT invent a new logo system.
4. Use the existing Vben logo flow correctly.
5. Do NOT add a theme watcher that manually swaps DOM nodes if src/src-dark already solves it.
6. Fix the actual configuration + runtime persistence + effective render path.

Inspect these files first:
- web/apps/web-antd/src/preferences.ts
- web/apps/web-antd/src/main.ts
- web/packages/effects/layouts/src/basic/layout.vue
- web/apps/web-antd/src/layouts/auth.vue

What to implement:

1. In web/apps/web-antd/src/preferences.ts
   ensure the logo config is exactly aligned with the two files:
   - source: '/branding/sicherplan-logo-512.png'
   - sourceDark: '/branding/sicherplan-logo-dark-512.png'
   - fit: 'contain'
   - enable: true

2. In web/packages/effects/layouts/src/basic/layout.vue
   make sure BOTH shell logo render paths pass both props:
   - :src="preferences.logo.source"
   - :src-dark="preferences.logo.sourceDark"

   This includes:
   - the main #logo VbenLogo
   - the #side-extra-title VbenLogo

   Keep the existing text slot untouched.

3. In web/apps/web-antd/src/main.ts
   add or fix a small preferences-repair step after initPreferences(...) so stale cached preferences cannot keep the wrong dark logo.

   The repair logic must:
   - inspect current runtime preferences.logo.source and preferences.logo.sourceDark
   - fix them when either value is:
     - empty
     - still pointing to the default external Vben logo
     - or sourceDark is incorrectly equal to the light logo path
   - update them to:
     - source: '/branding/sicherplan-logo-512.png'
     - sourceDark: '/branding/sicherplan-logo-dark-512.png'
   - preserve any real non-empty custom override only if it is already correct
   - not force a full app reset if a small preferences update is enough

4. In web/apps/web-antd/src/layouts/auth.vue
   verify that the auth layout still passes:
   - :logo="preferences.logo.source"
   - :logo-dark="preferences.logo.sourceDark"
   If already correct, leave it alone.

5. Do NOT stop after changing source files.
   Verify the actual runtime behavior on localhost:
   - light theme shows /branding/sicherplan-logo-512.png
   - dark theme shows /branding/sicherplan-logo-dark-512.png

Very important verification requirements:
1. After the fix, inspect the runtime app preferences values in localhost and confirm:
   - logosource = /branding/sicherplan-logo-512.png
   - logosourcedark = /branding/sicherplan-logo-dark-512.png
2. Confirm the rendered image source actually switches when the theme changes.
3. Confirm the upper-left logo position stays exactly the same.
4. Confirm the text block remains unchanged.
5. Confirm no other UI behavior changed.

Acceptance criteria:
- In light mode, the light logo is rendered.
- In dark mode, the dark logo is rendered.
- The shell/sidebar brand position remains unchanged.
- The auth page also remains compatible with light/dark logo behavior.
- No routing/menu/business logic was changed.

Deliverables:
1. Fix the effective dark-logo switching path.
2. Repair stale cached preference values if needed.
3. Keep the diff focused.
4. Summarize:
   - which files changed
   - whether the root cause was wrong sourceDark config, stale cached preferences, missing :src-dark wiring, or a bad fallback
   - confirmation that dark mode now uses /branding/sicherplan-logo-dark-512.png