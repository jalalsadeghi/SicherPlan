You are working in the public repo `jalalsadeghi/SicherPlan`.

Task:
Audit and fix `/admin/subcontractors` so the page aligns as closely as possible with the documented S-01 "Subcontractors Workspace" scope and the currently available frontend/backend contracts.

Important working-mode rule:
Do NOT fake unsupported features.
If the current repo/backend does not actually expose a supported endpoint for a documented feature, do NOT build a fake UI for it.
Instead:
- either hide/remove placeholder UI that pretends the feature exists
- or leave a clearly documented gap in the validation report

Reference expectations from project docs:
S-01 Subcontractors Workspace should cover:
- subcontractor list/detail/lifecycle
- contacts
- scopes
- finance profile
- history/attachments
- workers
- worker readiness summary/detail
- qualifications/proofs
- credentials
- worker import/export

Data-model expectations:
- subcontractor scope supports branch_id, mandate_id, and site_id
- subcontractor finance/commercial model includes more than just a minimal billing note
- subcontractor rate cards / rate lines exist in the domain model even if not fully implemented in current APIs

What to inspect first:
1. `web/apps/web-antd/src/sicherplan-legacy/views/SubcontractorAdminView.vue`
2. `web/apps/web-antd/src/sicherplan-legacy/components/SubcontractorWorkforcePanel.vue`
3. `web/apps/web-antd/src/sicherplan-legacy/api/subcontractors.ts`
4. `web/apps/web-antd/src/sicherplan-legacy/features/subcontractors/subcontractorAdmin.helpers.js`
5. Any current tests for subcontractor admin / workforce if they exist

Audit and classify each tab/section into one of:
A. fully supported and properly wired
B. supported by API but poorly implemented in UI
C. placeholder only / misleading
D. documented in model/docs but not actually supported yet by current API

Known likely gaps to verify carefully:
1. `addresses` tab appears to be placeholder-only
2. `commercial` tab appears to be placeholder-only
3. scope management currently lacks `site_id`
4. several important fields are raw ID textboxes rather than controlled select/lookup inputs
5. finance profile may not expose all currently supported finance fields
6. rate-card/rate-line domain support may exist in docs/model but not yet in current frontend API

Required fix strategy:
1. Preserve the parts that are already good:
   - contacts
   - history/attachments
   - workforce
2. Fix real mismatches where the API already supports the feature
3. Remove or hide misleading placeholder tabs if no real implementation exists yet
4. Improve unsafe raw-ID entry where official lookup/select data is already available in the repo
5. Do NOT overbuild undocumented frontend behavior

High-priority expected fixes:
A. Scope tab:
- add `site_id` support end-to-end if current backend supports it
- update UI draft, payloads, and list rendering accordingly
- keep validation consistent with “at least one of branch / mandate / site”

B. Placeholder tabs:
- inspect whether `addresses` and `commercial` have real backend support in the current repo
- if yes, implement them properly
- if no, remove/hide those tabs for now instead of exposing dead placeholders

C. Controlled inputs:
Where the current repo already has safe lookup sources, replace raw ID textboxes with select/lookup controls for user-facing data entry.
Examples to inspect:
- legal form
- subcontractor status
- invoice delivery method
- invoice status mode
- branch
- mandate
- worker qualification type
- worker credential type
Do not invent option lists if the repo does not expose them.

D. Finance/billing section:
- align visible fields with the actual current backend contract
- do not expose fields that are not supported
- do not omit supported fields that are materially important and already available

Important constraints:
- Do NOT rename routes or break existing API contracts
- Do NOT add fake commercial/rate-card UI if no current API exists
- Do NOT leave obviously dead placeholder tabs in a page intended for real data entry
- Keep the page practical for actual operator use

Testing requirements:
Add/update tests for the subcontractor admin page.
At minimum verify:
1. tabs shown to the user correspond to actually supported features
2. scope payload can include `site_id` when supported
3. placeholder tabs are removed/hidden if unsupported
4. contacts/history/workforce still work
5. any newly introduced select/lookup inputs submit correct values

Acceptance criteria:
- `/admin/subcontractors` no longer exposes misleading dead tabs
- scope management aligns with branch/mandate/site model where supported
- practical data entry is safer and less raw-ID driven
- supported features remain working
- unsupported documented features are clearly identified rather than faked

At the end, provide a concise validation report with these headings:
1. Which sections were already aligned
2. Which sections were mismatched
3. Which mismatches were fixed
4. Which documented features are still not supported by the current API
5. Which files were changed
6. Which tests were updated or added

Before coding, explicitly list:
- tabs/sections that are fully backed by current APIs
- tabs/sections that are placeholders only
- whether `site_id` is supported by current backend contracts
Then implement the safest high-value fixes first.