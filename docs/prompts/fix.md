You are working in the SicherPlan monorepo.

Task: fix the German UI copy everywhere so proper German umlauts and orthography are used consistently.

Problem:
The app supports German and English, but many German texts are currently written with ASCII transliterations instead of real umlauts/orthography.

Examples of the current problem visible in the UI:
- "MANDANTENFAEHIGE ..." should use "MANDANTENFÄHIGE ..."
- "Mandantenuebersicht" should use "Mandantenübersicht"
- "Standard-Waehrung" should use "Standard-Währung"
- "Planung oeffnen" should use "Planung öffnen"
- "Admin-Flaechen" should use "Admin-Flächen"
- any similar ae/oe/ue spellings in German-facing UI copy should be corrected where proper German orthography requires umlauts

Important:
This is a UI copy/i18n cleanup task.
Do NOT change route paths, slugs, API fields, database values, code identifiers, test ids, file names, CSS classes, or internal keys unless absolutely necessary.
Only change user-facing German text and the supporting i18n plumbing needed to render it correctly.

What to fix:
Apply this cleanup across the entire German UI surface, including but not limited to:
1. page titles
2. module headers / hero text
3. sidebar labels
4. breadcrumbs
5. tabs
6. cards / section headings
7. buttons
8. placeholders
9. helper text / descriptions
10. empty-state messages
11. badges / quick actions / dashboard labels
12. dialogs / confirmations / toasts if German text exists
13. aria labels / accessibility labels if they are user-facing German strings

What NOT to change:
1. URLs like `/admin/customers`, `/admin/core`, etc.
2. route names used internally
3. data-testid values
4. internal enum values
5. API payload field names
6. code identifiers / variable names
7. backend translation-independent business data unless it is explicitly seeded as user-facing German copy

What to inspect first:
- all i18n/message resource files for German
- any hardcoded German strings in Vue/TS components
- shared module registry / sidebar labels / dashboard quick actions / admin shell labels
- form labels and helper text in legacy admin views
- any seed/default UI-copy sources that provide German labels

Likely areas:
- German locale/messages files
- module registry definitions
- sidebar/nav configuration
- dashboard page strings
- admin module view strings
- customer/employee/core/platform-services UI strings
- any shared UI components with baked-in German text

Required implementation:

A. Correct German orthography
1. Replace ASCII transliterations with proper German umlauts where correct:
   - ae -> ä
   - oe -> ö
   - ue -> ü
   but only when the correct German word actually requires it.
2. Also correct uppercase umlauts where appropriate:
   - Ä, Ö, Ü
3. Preserve correct German spelling beyond umlauts if you encounter related copy issues.

B. Scope of replacement
1. Fix all visible German UI strings consistently, not just the examples seen in the screenshots.
2. Review the full German UI surface and normalize wording across modules.
3. Make sure the same concept is translated consistently everywhere:
   - e.g. “Übersicht”, “Währung”, “öffnen”, “Flächen”, etc.

C. Do not do unsafe blind replacements
1. Do NOT mass-replace every `ae/oe/ue` mechanically in source code.
2. Only update true user-facing German text.
3. Avoid corrupting names, IDs, routes, slugs, or technical tokens.
4. Review each affected string in context.

D. Ensure rendering support
1. Verify the frontend renders these characters correctly in the browser.
2. Make sure files are saved/handled as UTF-8.
3. Verify there is no encoding issue in locale files or build output.
4. No font-file changes; just ensure the current UI properly displays umlauts.

E. Keep English unchanged
1. Do not alter English locale strings unless they are accidentally affected by the implementation.
2. This task is focused on German copy correctness.

F. Prefer centralized fixes
1. If a string comes from i18n resources, fix it there.
2. If a label comes from a shared registry/config, fix it there once rather than patching many components individually.
3. Only touch component-local strings where they are truly hardcoded.

G. Verification
1. Review representative pages in German mode, including at least:
   - Dashboard
   - Customers
   - Employees
   - Tenants/Core
   - any sidebar/navigation labels
2. Confirm the corrected strings display with proper umlauts in the actual browser UI.
3. Confirm no broken encoding appears (e.g. mojibake or replacement characters).
4. Confirm routes and internal behavior remain unchanged.

Acceptance criteria:
- German UI text uses proper umlauts and spelling where required
- Visible labels no longer show incorrect ASCII transliterations like `ae/oe/ue` in normal German words
- English remains unchanged
- Routes, slugs, API fields, and technical identifiers remain unchanged
- The browser displays umlauts correctly across the app

Output format:
1. Audit summary of where the bad German copy lived
2. Files changed
3. Examples of corrected strings
4. Verification performed
5. Confirmation that only user-facing German text was changed