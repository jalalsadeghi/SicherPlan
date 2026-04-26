# AI Assistant Test Plan

## Purpose

This document defines the QA and regression plan for the current SicherPlan AI Assistant baseline implemented through tasks `AI-01` to `AI-26`.

The goal is to verify:

- backend capability and conversation behavior;
- secure read-only diagnostic behavior;
- same-language responses;
- safe knowledge retrieval;
- frontend widget/store/API behavior;
- non-regression around navigation, permissions, and feedback.

## Test Scope

Included:

- backend assistant unit and integration tests;
- frontend assistant API/store/component tests;
- security and isolation tests;
- language-policy tests;
- knowledge ingestion and retrieval tests;
- shift visibility diagnostic tests;
- manual UAT for the embedded widget.

Excluded from automated assistant baseline:

- mobile assistant UI;
- customer/subcontractor dedicated assistant frontend rollout;
- write actions;
- production OpenAI integration against live external services.

## Test Environment

Recommended baseline:

- `SP_AI_ENABLED=true`
- `SP_AI_PROVIDER=mock`
- no real OpenAI key required
- test database / in-memory repository doubles depending on suite
- seeded assistant permissions present

Notes:

- backend assistant tests are mixed between `pytest` and `unittest`;
- frontend assistant tests use Vitest with `happy-dom`;
- no real backend or OpenAI calls should occur in frontend unit tests.

## Backend Automated Tests

Key backend assistant test files and coverage:

### Core runtime and persistence

- [test_capabilities.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_capabilities.py)
  - capability responses for enabled/disabled/provider modes
- [test_conversation_persistence.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_conversation_persistence.py)
  - conversation create/load/message persistence
- [test_structured_response.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_structured_response.py)
  - structured response contract
- [test_feedback.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_feedback.py)
  - feedback submission and ownership checks

### Language and scope behavior

- [test_language_policy.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_language_policy.py)
  - language detection and response policy
- [test_out_of_scope.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_out_of_scope.py)
  - unsafe and out-of-scope refusal behavior

### Provider and prompt layer

- [test_provider_factory.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_provider_factory.py)
- [test_provider_mock.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_provider_mock.py)
- [test_openai_client_wrapper.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_openai_client_wrapper.py)
- [test_openai_provider_factory.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_openai_provider_factory.py)
- [test_openai_provider_errors.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_openai_provider_errors.py)
- [test_openai_structured_output.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_openai_structured_output.py)
- [test_prompt_builder.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_prompt_builder.py)
- [test_prompt_injection.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_prompt_injection.py)

### Knowledge

- [test_knowledge_source_loader.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_source_loader.py)
- [test_knowledge_chunker.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_chunker.py)
- [test_knowledge_ingestion.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_ingestion.py)
- [test_knowledge_retrieval.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_knowledge_retrieval.py)

### Tools and permissions

- [test_tool_registry.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_tool_registry.py)
- [test_tool_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_tool_permissions.py)
- [test_user_capability_tools.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_user_capability_tools.py)
- [test_page_context_tools.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_page_context_tools.py)
- [test_navigation_links.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_navigation_links.py)
- [test_page_route_catalog.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_page_route_catalog.py)
- [test_page_help_manifest.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_page_help_manifest.py)
- [test_how_to_employee_create_exact_ui.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_how_to_employee_create_exact_ui.py)
- [test_employee_tools.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_employee_tools.py)
- [test_employee_tool_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_employee_tool_permissions.py)
- [test_planning_tools.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_planning_tools.py)
- [test_planning_tool_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_planning_tool_permissions.py)
- [test_field_released_schedule_visibility.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_field_released_schedule_visibility.py)
- [test_field_visibility_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_field_visibility_permissions.py)

### Markus diagnostic and security integration

- [test_shift_visibility_diagnostic.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_shift_visibility_diagnostic.py)
- [test_shift_visibility_diagnostic_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_shift_visibility_diagnostic_permissions.py)
- [test_security_integration.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_security_integration.py)

## Frontend Automated Tests

Key frontend assistant test files and coverage:

- [web/apps/web-antd/src/api/sicherplan/assistant.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/api/sicherplan/assistant.test.ts)
  - capability fetch, conversation create/load, send message payload, feedback, safe error handling
- [web/apps/web-antd/src/store/assistant.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/store/assistant.test.ts)
  - store state, persistence, route context, send flow, feedback, reset/error behavior
- [web/apps/web-antd/src/components/sicherplan/assistant/SicherPlanAssistantWidget.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/components/sicherplan/assistant/SicherPlanAssistantWidget.test.ts)
  - visibility, open/close, route persistence, structured response rendering
- [web/apps/web-antd/src/components/sicherplan/assistant/AssistantMessageList.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/components/sicherplan/assistant/AssistantMessageList.test.ts)
  - diagnosis, missing permissions, next steps, out-of-scope text, feedback rendering
- [web/apps/web-antd/src/components/sicherplan/assistant/AssistantMessageInput.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/components/sicherplan/assistant/AssistantMessageInput.test.ts)
  - accessibility label, empty-submit blocking, Enter behavior
- [web/apps/web-antd/src/components/sicherplan/assistant/AssistantLinkCard.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/components/sicherplan/assistant/AssistantLinkCard.test.ts)
  - safe plain-text link rendering and internal navigation intent
- [web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.page-help.test.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.page-help.test.ts)
  - verified employee-create page help behavior

## Security Tests

Security coverage should explicitly validate:

- cross-tenant blocking;
- no inaccessible record existence leakage;
- prompt injection refusal;
- no arbitrary SQL-like tool input;
- no write-capable assistant tool execution;
- unauthorized links blocked at backend navigation layer;
- HR/private/payroll redaction;
- secret/token/API-key non-leakage;
- tool-call audit for allowed, denied, and failed cases.

Primary files:

- `test_prompt_injection.py`
- `test_tool_registry.py`
- `test_tool_permissions.py`
- `test_field_visibility_permissions.py`
- `test_shift_visibility_diagnostic_permissions.py`
- `test_security_integration.py`

## Same-Language Tests

Current same-language coverage should include:

- German question -> German answer
- Persian question -> Persian answer
- English question -> English answer
- missing-permission diagnostics stay in user language
- out-of-scope refusals stay in user language
- mixed/ambiguous input falls back safely through current detection policy

Primary files:

- `test_language_policy.py`
- `test_out_of_scope.py`
- `test_shift_visibility_diagnostic.py`
- `test_security_integration.py`

## Markus Diagnostic Test Matrix

| Case | Expected Outcome |
| --- | --- |
| Shift not released | Blocking diagnosis |
| Missing employee access link | Blocking diagnosis or limitation |
| Assignment cancelled/removed | Blocking diagnosis |
| Approved absence | Blocking or warning diagnosis |
| Missing qualification/compliance | Blocking or warning diagnosis |
| Missing mobile-access inspection permission | Missing-permission response |
| Cross-tenant Markus | Safe not found / not permitted |
| Multiple Markus matches | Clarification / ambiguity-safe response |
| No Markus match | Safe not found / not permitted |

The current implementation’s strongest automated coverage is around:

- shift release state;
- employee readiness;
- assignment state;
- final released-schedule visibility.

## Manual UAT Checklist

Run these scenarios in a controlled authenticated web session:

1. Login and confirm the assistant launcher appears for a user with `assistant.chat.access`.
2. Ask a German question and confirm the answer stays German.
3. Ask a Persian question and confirm the answer stays Persian.
4. Ask a verified how-to question for employee creation and confirm the assistant references the exact verified UI action.
5. Ask an unrelated question and confirm an out-of-scope refusal.
6. Ask the Markus shift-visibility question and confirm a structured diagnostic answer.
7. Navigate while the panel is open and confirm conversation state persists.
8. Click an assistant-provided link and confirm internal navigation only.
9. Submit helpful and not-helpful feedback.
10. Repeat with a user who lacks diagnostics permission and confirm missing-permission behavior.

## Non-Regression Checklist

When assistant changes land, also verify:

- login and session refresh
- health endpoints
- route guards and navigation
- IAM capability loading
- customers surfaces
- employees surfaces
- planning surfaces
- field execution read paths
- finance read paths
- reporting read paths
- customer/subcontractor portal behavior

## Commands

No docs-specific lint tools are currently configured in this repository:

- `markdownlint` not found in local toolchain
- `prettier` not found in local toolchain

Useful assistant test commands used in this branch:

### Backend

```bash
PYTHONPATH=backend python3 -m pytest -q \
  backend/tests/modules/assistant/test_security_integration.py \
  backend/tests/modules/assistant/test_feedback.py \
  backend/tests/modules/assistant/test_out_of_scope.py \
  backend/tests/modules/assistant/test_assistant_service_mock_provider.py \
  backend/tests/modules/assistant/test_navigation_links.py \
  backend/tests/modules/assistant/test_knowledge_retrieval.py \
  backend/tests/modules/assistant/test_tool_registry.py \
  backend/tests/modules/assistant/test_tool_permissions.py \
  backend/tests/modules/assistant/test_prompt_injection.py \
  backend/tests/modules/assistant/test_shift_visibility_diagnostic.py \
  backend/tests/modules/assistant/test_shift_visibility_diagnostic_permissions.py
```

```bash
PYTHONPATH=backend python3 -m unittest \
  backend.tests.modules.assistant.test_assistant_models_migration \
  backend.tests.modules.core.test_alembic_versioning
```

### Frontend

```bash
pnpm --dir web/apps/web-antd exec vitest run \
  src/api/sicherplan/assistant.test.ts \
  src/store/assistant.test.ts \
  src/components/sicherplan/assistant/SicherPlanAssistantWidget.test.ts \
  src/components/sicherplan/assistant/AssistantMessageList.test.ts \
  src/components/sicherplan/assistant/AssistantMessageInput.test.ts \
  src/components/sicherplan/assistant/AssistantLinkCard.test.ts \
  src/sicherplan-legacy/features/employees/employeeAdmin.page-help.test.ts
```

```bash
pnpm --dir web/apps/web-antd typecheck
```

## Known Limitations and Follow-Ups

Current limitations that should stay visible in QA:

- no knowledge status/reindex HTTP endpoint yet;
- no generic provider-driven tool-call execution loop yet;
- dedicated assistant rate-limit settings exist, but assistant-specific enforcement is not implemented yet;
- frontend package has no dedicated local `test` / `test:unit` scripts, so direct `pnpm exec vitest run ...` is the current convention;
- backend assistant coverage is split between `pytest` and `unittest`;
- some older FastAPI `TestClient` pytest files have shown intermittent hanging behavior, so stable curated command sets are preferable for CI/local verification.
