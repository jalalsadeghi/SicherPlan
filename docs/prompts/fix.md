You are working in the public repo `jalalsadeghi/SicherPlan`.

Task:
Standardize the German UI wording in the project so that the product uses `Mitarbeiter` / `Mitarbeiterin` style instead of `Mitarbeitende` in user-facing German text, based on customer style preference.

Important rule:
This is a UI/copy/style normalization task, NOT a blind global rename task.

What the customer wants:
Across the German product UI, replace `Mitarbeitende`-style wording with `Mitarbeiter` wording for consistency.

Critical constraints:
1. Do NOT blindly rename everything across the whole repository.
2. Prefer changing only:
   - German locale strings
   - German UI labels/headings/help texts
   - user-facing copy in German templates
3. Do NOT casually rename:
   - API paths
   - database fields
   - TypeScript interfaces
   - backend schemas
   - route names
   - i18n message keys
   - test ids
   - internal identifiers
unless there is a very strong reason and the change is fully safe.
4. Preserve English copy and non-German locales unless the current repo explicitly requires matching updates.

Before changing anything, inspect:
1. All German locale/message files
2. German user-facing text in Vue components
3. Any occurrences of:
   - `Mitarbeitende`
   - `mitarbeitende`
   - compounds built from it
4. Distinguish between:
   - display text
   - internal identifiers / keys / code symbols

Required output behavior:
- German UI should consistently use the preferred wording based on `Mitarbeiter`
- Grammar must remain natural in each context
- Do not perform mechanical replacements that produce awkward German

Examples of safe likely replacements:
- `Mitarbeitende` → `Mitarbeiter`
- `Mitarbeitendenportal` → `Mitarbeiterportal`
- `Mitarbeitendenverwaltung` → `Mitarbeiterverwaltung`

But verify each case in context.
Do not assume every occurrence should be replaced with exactly the same word form.

Required linguistic care:
Choose the grammatically correct replacement for each context, for example:
- singular vs plural
- compound nouns
- headings vs help texts
- adjective/participle constructions that may need rewriting instead of direct replacement

Recommended implementation strategy:
1. Audit all German user-facing occurrences first
2. Group them into:
   - direct noun replacements
   - compound noun replacements
   - sentence-level rewrites needed for natural German
3. Apply only safe copy changes
4. Leave internal code identifiers untouched unless absolutely necessary
5. Update tests only where they assert visible German text

Validation requirements:
After implementing, provide a review of:
1. Which visible German strings were changed
2. Which internal identifiers were intentionally NOT changed
3. Any occurrences where a simple find/replace would have produced bad German and how you handled them
4. Any remaining `Mitarbeitende` occurrences and why they were left unchanged

Testing requirements:
- Run/update tests affected by changed visible text
- Ensure no breakage from accidental identifier renames

Acceptance criteria:
- German UI consistently prefers `Mitarbeiter` wording
- No unsafe global rename was done
- Internal code/API/schema stability is preserved
- Text remains natural and professional in German

At the end, provide a concise validation report with these headings:
1. Scope of change
2. Which files were changed
3. Which visible terms were standardized
4. Which identifiers were intentionally left untouched
5. Any wording that needed manual rewriting instead of direct replacement
6. Which tests were updated