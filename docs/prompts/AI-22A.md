# AI-22A — UI Action Catalog and Page Help Manifest

**Task No:** AI-22A  
**Task name:** UI Action Catalog and Page Help Manifest  
**Placement:** Insert this task after `AI-22 Frontend Assistant API Client and Store` and before `AI-23 Global Assistant Widget UI`.  
**Do not renumber existing tasks.** `AI-23` and later tasks must keep their existing numbers.  
**Target sprint reference:** `docs/sprint/AI-Assistant.md`  
**Task type:** Backend + Frontend contract + static UI metadata + tests  
**Primary purpose:** Prevent the AI Assistant from guessing UI labels, button names, tabs, form sections, or exact user steps.

---

## 1. Background

The current AI Assistant sprint already covers page-aware navigation, knowledge retrieval, structured answers, user capabilities, and frontend API/store integration. However, page-level knowledge alone is not enough for accurate user guidance.

For example, if a user asks:

```text
چطور یک Employee جدید ثبت کنم؟
```

The assistant must **not** answer with vague or guessed wording such as:

```text
Click Create Employee or New Employee.
```

Instead, it must know the **exact current UI action** from the real application, for example:

```text
Go to Employees Workspace and click "Create Employee File" in the top-right toolbar.
```

This must be based on a verified UI action catalog / page help manifest, not on model memory or assumptions.

---

## 2. Goal

Implement a **UI Action Catalog and Page Help Manifest** layer that gives the assistant verified, structured knowledge about the real frontend UI.

The assistant must use this catalog when answering UI-how-to questions involving:

- exact button labels;
- exact menu/sidebar path labels;
- exact tab names;
- exact form section names;
- exact required fields;
- exact action locations on the page;
- exact permissions required for an action;
- exact result of clicking an action;
- safe fallback behavior when exact UI information is unavailable.

The assistant must be explicitly instructed and tested to **not invent UI details**.

---

## 3. Scope

### 3.1 In Scope

1. Add a structured page-help manifest model.
2. Add a backend-readable UI action catalog.
3. Add frontend action metadata attributes where needed.
4. Add assistant tools/endpoints for retrieving verified page help.
5. Add tests proving that UI action labels are exact and permission-filtered.
6. Add the first verified manifest entries for currently implemented/high-priority pages.
7. Update prompt policy so the assistant never guesses exact UI actions.
8. Update frontend API/store types if needed, but do **not** implement the full AI-23 widget in this task.

### 3.2 Initial Page Coverage Required

Codex must inspect the current repository and register **only UI actions that can be verified from existing frontend code**.

At minimum, attempt to cover these pages if they exist in the current frontend:

```text
E-01 — Employees Workspace
C-01 — Customers Workspace
P-03 — Shift Planning
P-04 — Staffing Board & Coverage
P-05 — Dispatch, Outputs & Subcontractor Releases
FI-01 — Actuals / Actual-Freigaben Workspace
```

The minimum required fully verified scenario is:

```text
E-01 — how to create a new Employee / Employee file
```

If a page or action does not exist yet in the UI, Codex must **not invent it**. Instead, add a clear note in the implementation summary and leave the manifest entry absent or marked as `unverified` according to the model rules below.

### 3.3 Out of Scope

Do not implement:

- new business create/edit/delete flows;
- actual employee creation logic;
- write actions by the assistant;
- changes to existing domain behavior;
- full AI-23 widget implementation;
- automatic DOM scraping at runtime;
- LLM-based UI guessing;
- screenshots/OCR-based action discovery;
- browser automation as a production source of truth.

---

## 4. Core Principle

The assistant may mention exact UI actions only when those actions come from a verified source.

Use this rule everywhere:

```text
No verified UI action catalog entry = no exact button/tab/form claim.
```

If exact UI data is unavailable, the assistant must answer safely:

```text
I can explain the workflow from the platform documentation, but I cannot confirm the exact current button label for this page from the verified UI catalog.
```

The message must be returned in the user’s language according to the same-language policy from AI-08.

---

## 5. Recommended Architecture

```text
Frontend page code
  -> stable metadata attributes on important actions
  -> static Page Help Manifest entries
  -> backend seed / registry / endpoint
  -> assistant tool: assistant.get_page_help_manifest
  -> assistant tool: assistant.find_ui_action
  -> prompt builder policy: use verified UI labels only
  -> final assistant answer with exact steps or safe uncertainty
```

The final implementation may adapt to current repository conventions, but the following layers must exist logically.

---

## 6. Data Model / Manifest Model

Codex must inspect the existing assistant database/migration style from AI-05 before implementing.

### 6.1 Preferred Database Table

Add a new table if the project uses DB-backed catalogs:

```text
assistant_page_help_manifest
```

If the project uses PostgreSQL schemas, use:

```text
assistant.page_help_manifest
```

Otherwise use prefix-based naming according to the existing convention.

### 6.2 Suggested Fields

```text
id UUID PK
page_id text not null
route_name text nullable
path_template text nullable
module_key text not null
language_code text nullable
manifest_version integer not null default 1
status text not null default 'active'
manifest_json jsonb not null
verified_from jsonb nullable
created_at timestamptz not null
updated_at timestamptz not null
```

Constraints:

```text
unique(page_id, language_code, manifest_version)
status in ('active', 'inactive', 'draft', 'unverified')
```

Indexes:

```text
idx_assistant_page_help_manifest_page_active
idx_assistant_page_help_manifest_module
```

### 6.3 Manifest JSON Shape

The manifest must be explicit and machine-readable.

```json
{
  "page_id": "E-01",
  "page_title": "Employees Workspace",
  "route_name": "SicherPlanEmployees",
  "path_template": "/admin/employees",
  "module_key": "employees",
  "source_status": "verified",
  "verified_from": [
    {
      "file": "web/apps/web-antd/src/.../EmployeesPage.vue",
      "evidence": "button label and data-assistant-action found in source"
    }
  ],
  "sidebar_path": [
    {
      "label": "Workforce & Partners",
      "verified": true
    },
    {
      "label": "Employees",
      "verified": true
    }
  ],
  "primary_actions": [
    {
      "action_key": "employees.create.open",
      "label": "Create Employee File",
      "label_i18n_key": "employees.actions.createFile",
      "action_type": "button",
      "selector": "[data-assistant-action='employees.create.open']",
      "test_id": "employees-create-file-button",
      "location": "top-right toolbar",
      "required_permissions": ["employees.create"],
      "opens": "employee-create-form",
      "result": "Opens the Employee file creation form",
      "verified": true
    }
  ],
  "form_sections": [
    {
      "section_key": "employee.basic_data",
      "title": "Basic data",
      "verified": true,
      "fields": [
        {
          "field_key": "personnel_no",
          "label": "Personnel number",
          "required": true,
          "verified": true
        },
        {
          "field_key": "first_name",
          "label": "First name",
          "required": true,
          "verified": true
        },
        {
          "field_key": "last_name",
          "label": "Last name",
          "required": true,
          "verified": true
        }
      ]
    }
  ],
  "post_create_steps": [
    {
      "step_key": "employee.qualifications.complete",
      "label": "Complete Qualifications",
      "page_id": "E-01",
      "verified": true
    },
    {
      "step_key": "employee.access_link.check",
      "label": "Check Access Link for Employee Self-Service",
      "page_id": "E-01",
      "verified": true
    }
  ],
  "fallback_policy": {
    "exact_ui_guidance_allowed": true,
    "assistant_may_guess_missing_labels": false
  }
}
```

Codex may adapt field names to current style, but the implementation must preserve the meaning.

---

## 7. Frontend Metadata Requirements

Add stable attributes to important UI actions that the assistant may reference.

Preferred attributes:

```html
<button
  data-assistant-page-id="E-01"
  data-assistant-action="employees.create.open"
  data-testid="employees-create-file-button"
>
  Create Employee File
</button>
```

Rules:

1. Do not change visual design unless needed for accessibility or test stability.
2. Do not change business behavior.
3. Add metadata only to verified important actions.
4. Keep `data-assistant-action` stable even if the visible label is translated later.
5. Use existing i18n labels where available.
6. If an important button is rendered through a shared component, add metadata through props rather than hardcoding invalid attributes.

---

## 8. Backend API / Tool Requirements

### 8.1 Optional Endpoint

Add an endpoint if consistent with the current assistant API design:

```text
GET /api/assistant/page-help/{page_id}
```

Behavior:

- Requires `assistant.chat.access`.
- Returns only page help visible to the current user.
- Filters or hides actions for which the user lacks required permissions.
- Does not expose internal-only/unverified entries unless the caller has assistant/admin diagnostic permission.

Suggested response:

```json
{
  "page_id": "E-01",
  "page_title": "Employees Workspace",
  "route_name": "SicherPlanEmployees",
  "path_template": "/admin/employees",
  "actions": [
    {
      "action_key": "employees.create.open",
      "label": "Create Employee File",
      "location": "top-right toolbar",
      "allowed": true,
      "required_permissions": ["employees.create"],
      "result": "Opens the Employee file creation form"
    }
  ],
  "form_sections": [...],
  "source_status": "verified"
}
```

### 8.2 Required Assistant Tools

Add tools to the assistant tool registry from AI-15.

```text
assistant.get_page_help_manifest
assistant.find_ui_action
```

#### `assistant.get_page_help_manifest`

Inputs:

```json
{
  "page_id": "E-01",
  "route_name": "optional",
  "language_code": "optional"
}
```

Output:

- page title;
- route/path if allowed;
- verified actions filtered by current permissions;
- form sections and required fields where verified;
- unavailable actions with safe reasons only when allowed by policy;
- `source_status`.

#### `assistant.find_ui_action`

Inputs:

```json
{
  "intent": "create_employee",
  "page_id": "E-01",
  "language_code": "fa"
}
```

Output:

- exact verified action if available;
- required permissions;
- allowed/not allowed for current user;
- safe fallback if not verified.

---

## 9. Prompt Builder Policy Update

Update the assistant prompt/policy from AI-14.

Add rules like:

```text
When the user asks how to use the UI, do not invent button names, tab names, menu labels, form section names, field labels, or exact click paths.
Use verified UI actions only from the Page Help Manifest / UI Action Catalog tools.
If no verified UI action is available, explain the workflow from documentation and clearly state that the exact current UI label cannot be confirmed from the verified catalog.
Never provide alternatives such as "Create Employee or New Employee" unless both labels are explicitly returned by the verified catalog.
```

Same-language policy still applies.

---

## 10. Required How-to Behavior

For this user question:

```text
چطور یک Employee جدید ثبت کنم؟
```

The assistant flow should be:

```text
1. Detect Persian.
2. Classify as SicherPlan how-to question.
3. Retrieve relevant knowledge chunks about Employees Workspace.
4. Use page/action tool for E-01 and create_employee intent.
5. Check if current user has required permission for the action.
6. Return exact verified UI steps if available.
7. If the user lacks permission, explain the permission limitation safely.
8. If the exact action label is not verified, say so and provide only general workflow guidance.
```

### 10.1 Example Response When Verified and Allowed

```text
برای ثبت یک Employee جدید، وارد صفحه Employees Workspace شوید.

مراحل دقیق:
1. از منوی سمت چپ وارد Workforce & Partners > Employees شوید.
2. در بالای صفحه، سمت راست، روی دکمه "Create Employee File" کلیک کنید.
3. فرم "Basic data" باز می‌شود. فیلدهای اجباری را کامل کنید، از جمله "Personnel number", "First name" و "Last name".
4. پس از ذخیره، برای آماده شدن کارمند جهت برنامه‌ریزی، بخش‌های Qualifications، Availability و Access Link را بررسی کنید.

اگر دکمه "Create Employee File" را نمی‌بینید، احتمالاً دسترسی `employees.create` برای شما فعال نیست.
```

### 10.2 Example Response When Not Verified

```text
می‌توانم روند کلی ثبت Employee را بر اساس مستندات پلتفرم توضیح بدهم، اما نام دقیق دکمه در UI فعلی از طریق UI Action Catalog تأیید نشده است. بنابراین برای جلوگیری از راهنمایی اشتباه، نام دکمه را حدس نمی‌زنم.

روند کلی این است: ابتدا وارد Employees Workspace شوید، سپس از بخش ایجاد پرونده کارمند، اطلاعات پایه، Qualificationها، Availability و Access Link را کامل کنید.
```

### 10.3 Example Response When Permission Missing

```text
در سطح دسترسی فعلی شما، من نمی‌توانم عملیات ایجاد Employee را به‌عنوان یک Action مجاز نشان بدهم. برای ثبت Employee جدید معمولاً دسترسی `employees.create` یا نقش Workforce / HR Administrator یا Tenant Administrator لازم است.
```

---

## 11. Target Files

Codex must inspect the actual repository before editing. The following are likely targets and may need adjustment.

### Backend

```text
backend/app/modules/assistant/page_help.py
backend/app/modules/assistant/page_help_seed.py
backend/app/modules/assistant/navigation.py
backend/app/modules/assistant/tools/page_help_tools.py
backend/app/modules/assistant/tools/registry.py
backend/app/modules/assistant/prompt_builder.py
backend/app/modules/assistant/policy.py
backend/app/modules/assistant/router.py
backend/app/modules/assistant/schemas.py
backend/app/modules/assistant/models.py
backend/app/modules/assistant/repository.py
backend/alembic/versions/* or existing migrations folder
```

### Frontend

```text
web/apps/web-antd/src/**/employees/**
web/apps/web-antd/src/**/customers/**
web/apps/web-antd/src/**/planning/**
web/apps/web-antd/src/**/finance/**
web/apps/web-antd/src/api/sicherplan/assistant.ts
web/apps/web-antd/src/stores/assistant.ts
```

### Tests

```text
backend/tests/modules/assistant/test_page_help_manifest.py
backend/tests/modules/assistant/test_ui_action_catalog.py
backend/tests/modules/assistant/test_no_ui_guessing_policy.py
backend/tests/modules/assistant/test_page_help_permissions.py
backend/tests/modules/assistant/test_how_to_employee_create_exact_ui.py
```

Frontend test names depend on the current framework, but should include:

```text
assistant_ui_action_metadata_exists_for_employee_create
assistant_page_help_manifest_matches_employee_create_button
```

If the frontend test framework is not ready, add a lightweight manifest validation script/test according to repository conventions and document the limitation.

---

## 12. Acceptance Criteria

This task is complete only when all criteria below are satisfied.

### 12.1 Catalog and Manifest

- A structured page help manifest mechanism exists.
- At least E-01 Employee creation action is represented if the current UI has such an action.
- Manifest entries include exact labels, action keys, locations, required permissions, and verification source.
- Unverified actions are not used for exact assistant guidance.
- The catalog can be retrieved by backend service/tool.

### 12.2 Frontend Metadata

- Important verified actions have stable `data-assistant-action` and/or `data-testid` attributes.
- Adding metadata does not change UI behavior.
- The Employee create action, if present, has a stable action key such as:

```text
employees.create.open
```

### 12.3 Backend Tooling

- `assistant.get_page_help_manifest` exists and is registered as a read-only tool.
- `assistant.find_ui_action` exists and is registered as a read-only tool.
- Tools use backend auth context, not user-provided permission claims.
- Tools filter actions by current user permissions.
- Tools do not return unauthorized links or unauthorized action instructions.

### 12.4 Prompt / Policy

- The prompt builder forbids guessing exact UI labels/actions.
- The assistant may only give exact UI steps from verified catalog data.
- If catalog data is missing, the assistant must explicitly say it cannot confirm the exact UI label.
- Same-language behavior continues to apply.

### 12.5 Tests

- Tests pass for retrieving page help.
- Tests pass for exact Employee create action guidance when verified and allowed.
- Tests pass for safe fallback when the UI action is missing/unverified.
- Tests pass for missing permission behavior.
- Tests pass for no-guessing behavior: the assistant must not output `Create Employee or New Employee` unless both labels are verified.
- Existing AI-01 to AI-22 tests remain passing.

---

## 13. Non-regression Requirements

Do not break:

- existing assistant conversation APIs from AI-06;
- structured response contract from AI-07;
- language policy from AI-08;
- out-of-scope policy from AI-09;
- provider/mock behavior from AI-10/AI-11;
- knowledge retrieval from AI-13;
- prompt builder from AI-14;
- tool registry from AI-15;
- page route catalog from AI-17;
- frontend assistant API client/store from AI-22;
- existing domain pages or business workflows;
- existing route names/paths unless the current code already requires it.

---

## 14. Implementation Instructions for Codex

### Step 1 — Inspect First

Before coding, inspect the current repository and report:

```text
- where assistant backend module currently lives;
- how assistant tools are registered;
- how migrations are written;
- where page route catalog is stored;
- where Employee page/component is implemented;
- exact visible label of the current Employee create action, if present;
- exact route name/path for E-01, if present;
- whether frontend test framework exists;
- whether existing assistant store/API types need extension.
```

### Step 2 — Propose Concrete File Plan

Write a short plan listing:

```text
- backend files to create/change;
- frontend files to create/change;
- migration file name;
- test files;
- verified pages/actions;
- pages/actions not found or not verifiable.
```

### Step 3 — Implement Minimal Safe Foundation

Implement the manifest/tooling foundation first. Do not add broad or guessed catalog entries.

### Step 4 — Add Verified E-01 Employee Create Guidance

Use the exact current UI label and file evidence. If the action is not present, implement the fallback behavior and document that E-01 create guidance is not yet verified.

### Step 5 — Add Tests

Add tests before finalizing.

### Step 6 — Report Results

Final Codex response must include:

```text
- files changed;
- migrations added;
- verified UI actions added;
- tests run and results;
- gaps / unverified pages;
- confirmation that no write assistant action was added;
- confirmation that UI action guessing is blocked.
```

---

# Codex Implementation Prompt

Use this prompt for Codex:

```text
Implement Task AI-22A — UI Action Catalog and Page Help Manifest.

Context:
- We have completed AI-01 through AI-22 of docs/sprint/AI-Assistant.md.
- Do not renumber existing tasks. This task is inserted after AI-22 and before AI-23.
- The assistant must not guess exact UI labels, button names, tab names, field labels, or click paths.
- Exact UI guidance must come only from a verified UI Action Catalog / Page Help Manifest.

Your first step must be repository inspection only. Before editing code, inspect and summarize:
1. current assistant backend module structure;
2. current assistant tool registry structure;
3. current assistant route/page catalog implementation;
4. current migration/model conventions;
5. current frontend route/page/component location for Employees Workspace (E-01);
6. exact visible label and source file for the Employee create action, if present;
7. existing frontend test framework and backend test conventions.

Then implement the following:

1. Add a structured Page Help Manifest / UI Action Catalog mechanism.
2. Add backend model/migration if the repository uses DB-backed assistant catalogs; otherwise use the current project catalog convention and explain why.
3. Add read-only assistant tools:
   - assistant.get_page_help_manifest
   - assistant.find_ui_action
4. Register these tools in the assistant tool registry.
5. Ensure tools use backend auth context and filter actions by the current user's permissions.
6. Add or update backend schemas/repository/service code to return verified page help metadata.
7. Add stable frontend metadata attributes for verified important actions, starting with E-01 Employee creation if that action exists:
   - data-assistant-page-id
   - data-assistant-action
   - data-testid where appropriate
8. Update prompt/policy so the assistant is forbidden from inventing exact UI labels/actions.
9. Add tests proving:
   - page help manifest can be retrieved;
   - Employee create action guidance uses the exact verified label when allowed;
   - missing permission hides or limits the action safely;
   - missing/unverified action produces safe uncertainty instead of guessed labels;
   - the assistant does not output vague alternatives like "Create Employee or New Employee" unless both labels are verified;
   - existing AI Assistant tests still pass.

Important constraints:
- Do not implement write actions by the assistant.
- Do not change domain behavior.
- Do not call OpenAI from the frontend.
- Do not add runtime DOM scraping.
- Do not invent catalog entries for pages/actions that are not present in the current code.
- Do not expose unauthorized links or unauthorized action instructions.
- Preserve same-language behavior from AI-08.
- Preserve all existing AI-01 to AI-22 contracts.

After implementation, run the relevant backend/frontend tests and report:
- files changed;
- migration name if added;
- verified actions added;
- unverified/missing actions;
- tests run and results;
- any follow-up needed before AI-23.
```

---

# Codex Review Prompt

Use this review prompt after Codex implements the task:

```text
Review the implementation of Task AI-22A — UI Action Catalog and Page Help Manifest.

Review goals:
1. Confirm the assistant can no longer guess exact UI labels/actions.
2. Confirm exact UI guidance comes only from verified Page Help Manifest / UI Action Catalog data.
3. Confirm all page-help tools are read-only, permission-aware, tenant-safe, and registered through the existing assistant tool registry.
4. Confirm the E-01 Employee create guidance, if implemented, uses the exact current UI label from the actual frontend code.
5. Confirm missing or unverified UI data produces safe uncertainty, not hallucinated click instructions.

Check the following in detail:

Backend:
- Are page help schemas clear and structured?
- Is the manifest persisted or registered according to existing project conventions?
- If a migration was added, does it follow existing Alembic/migration style?
- Are assistant.get_page_help_manifest and assistant.find_ui_action registered as read-only tools?
- Do tools enforce assistant.chat.access and action-specific permissions?
- Are actions filtered/redacted when the user lacks permissions?
- Are tool calls audited if the current tool registry audits read-only tool calls?
- Are unauthorized page/action hints blocked?

Frontend:
- Were stable data attributes added only to verified actions?
- Did the implementation avoid changing visual layout or business behavior?
- Does the Employee create action, if present, have a stable data-assistant-action key?
- Are labels/i18n handled without breaking the existing UI?

Prompt / Policy:
- Does the prompt builder explicitly forbid inventing UI labels, tab names, form labels, and click paths?
- Does the assistant use safe fallback language when exact UI data is unavailable?
- Is same-language behavior preserved for UI-help answers and fallback messages?

Tests:
- Is there a test for verified Employee create guidance?
- Is there a test for missing permissions?
- Is there a test for unverified UI action fallback?
- Is there a test that prevents vague guessed labels such as "Create Employee or New Employee"?
- Do existing assistant tests still pass?

Security and non-regression:
- No write action was added.
- No direct SQL/LLM-generated SQL was added.
- No frontend OpenAI call was added.
- No runtime DOM scraping was added.
- No cross-tenant or unauthorized action leakage exists.
- Existing AI-01 through AI-22 behavior remains intact.

Return the review in this format:

1. Summary verdict: PASS / PASS WITH FIXES / FAIL
2. Files reviewed
3. Confirmed correct behavior
4. Issues found
5. Required fixes
6. Security concerns
7. Test gaps
8. Final recommendation before starting AI-23
```
