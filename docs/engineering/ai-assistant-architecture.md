# SicherPlan AI Assistant Architecture

## Overview

The SicherPlan AI Assistant is an embedded web assistant for the authenticated SicherPlan platform. It is:

- tenant-aware;
- role-aware;
- page-aware;
- same-language by design;
- read-only in the current release;
- backend-mediated for provider calls, knowledge retrieval, and diagnostics;
- not a generic chatbot.

The current implementation focuses on platform help, verified UI how-to answers, safe navigation links, knowledge-backed answers, and the first operational diagnostic for employee shift visibility.

## Architecture Diagram

```text
Web Assistant Widget
  -> Assistant API (/api/assistant/*)
  -> Assistant Service
  -> Auth Context / RBAC / Tenant Scope
  -> Knowledge Retrieval + Read-only Tools
  -> Provider Wrapper (mock/openai)
  -> Structured Assistant Response
```

## Backend Module Structure

Implemented backend module paths:

```text
backend/app/modules/assistant/
  router.py
  schemas.py
  service.py
  repository.py
  policy.py
  language.py
  classifier.py
  prompt_builder.py
  provider.py
  openai_client.py
  navigation.py
  page_catalog_seed.py
  page_help.py
  page_help_seed.py
  models.py
  knowledge/
    chunker.py
    embeddings.py
    ingest.py
    repository.py
    retriever.py
    source_loader.py
    types.py
  tools/
    base.py
    context_tools.py
    employee_tools.py
    field_tools.py
    navigation_tools.py
    page_help_tools.py
    planning_tools.py
    redaction.py
    registry.py
    user_tools.py
  diagnostics/
    released_schedule_visibility.py
    shift_visibility.py
```

## Frontend Structure

Implemented frontend assistant paths:

```text
web/apps/web-antd/src/app.vue
web/apps/web-antd/src/api/sicherplan/assistant.ts
web/apps/web-antd/src/store/assistant.ts
web/apps/web-antd/src/store/assistant-session.ts
web/apps/web-antd/src/components/sicherplan/assistant/
  SicherPlanAssistantWidget.vue
  AssistantLauncher.vue
  AssistantPanel.vue
  AssistantMessageList.vue
  AssistantMessageInput.vue
  AssistantEvidenceList.vue
  AssistantLinkCard.vue
  AssistantFeedback.vue
```

The widget is mounted once in [app.vue](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/app.vue) after `RouterView`, which lets it survive route changes.

## Main Backend Flow

Current message handling in [service.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/service.py):

1. Receive authenticated request.
2. Load `RequestAuthorizationContext`.
3. Enforce `SP_AI_ENABLED` and `assistant.chat.access`.
4. Load or create the owned conversation.
5. Sanitize route/client context.
6. Detect input language and choose response language.
7. Classify the request as in-scope, out-of-scope, or unsafe.
8. Short-circuit deterministic paths where applicable:
   - verified UI how-to answers;
   - employee shift visibility diagnostic.
9. Retrieve indexed knowledge chunks.
10. Build provider prompt with auth summary, route context, knowledge excerpts, and allowed tool definitions.
11. List allowed backend tools from the registry.
12. Call the configured provider (`mock` or `openai`).
13. Validate the structured provider output.
14. Persist the user message and assistant message.
15. Return `AssistantStructuredResponse`.

Important current limitation:

- provider tool definitions are exposed to the model, but a generic provider-driven tool-call execution loop is not implemented yet;
- deterministic diagnostics run through the registry directly inside the backend service instead.

## Data Model

Assistant persistence lives in PostgreSQL schema `assistant` through [models.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/models.py).

### `assistant.conversation`

Purpose:
- one conversation per user-owned assistant thread.

Key fields:
- `id`
- `tenant_id`
- `user_id`
- `title`
- `locale`
- `status`
- `last_route_name`
- `last_route_path`
- `created_at`
- `updated_at`

### `assistant.message`

Purpose:
- stores user and assistant messages for a conversation.

Key fields:
- `conversation_id`
- `tenant_id`
- `user_id`
- `role`
- `content`
- `structured_payload`
- `detected_language`
- `response_language`
- `token_input`
- `token_output`
- `created_at`

### `assistant.tool_call`

Purpose:
- audit trail for assistant tool usage, including denied and failed calls.

Key fields:
- `conversation_id`
- `message_id`
- `tenant_id`
- `user_id`
- `tool_name`
- `input_json`
- `output_json_summary`
- `required_permissions`
- `permission_decision`
- `scope_kind`
- `entity_refs`
- `duration_ms`
- `error_code`
- `created_at`

### `assistant.feedback`

Purpose:
- per-user feedback on assistant answers.

Key fields:
- `conversation_id`
- `message_id`
- `tenant_id`
- `user_id`
- `rating`
- `comment`
- `created_at`

### `assistant.knowledge_source`

Purpose:
- indexed documentation source manifest with hash/version tracking.

Key fields:
- `source_type`
- `source_name`
- `source_path`
- `source_hash`
- `source_version`
- `status`
- `last_ingested_at`

### `assistant.knowledge_chunk`

Purpose:
- chunked searchable knowledge excerpts derived from indexed sources.

Key fields:
- `source_id`
- `chunk_index`
- `title`
- `content`
- `language_code`
- `module_key`
- `page_id`
- `role_keys`
- `permission_keys`
- `embedding`
- `token_count`

### `assistant.page_route_catalog`

Purpose:
- backend-owned page catalog for safe navigation links and accessible-page search.

### `assistant.page_help_manifest`

Purpose:
- verified page help metadata for exact UI-action guidance.

### `assistant.prompt_policy_version`

Purpose:
- stores prompt/policy version metadata for backend-owned assistant policy evolution.

## API Endpoints

Implemented assistant routes in [router.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/router.py):

- `GET /api/assistant/capabilities`
- `GET /api/assistant/page-help/{page_id}`
- `POST /api/assistant/conversations`
- `GET /api/assistant/conversations/{conversation_id}`
- `POST /api/assistant/conversations/{conversation_id}/messages`
- `POST /api/assistant/conversations/{conversation_id}/feedback`

Not implemented in the current branch:

- `GET /api/assistant/knowledge/status`
- `POST /api/assistant/knowledge/reindex`

The sprint mentions knowledge endpoints, but the current implementation stops at service/repository support and does not expose them over HTTP yet.

## Structured Response Schema

The main assistant answer contract is `AssistantStructuredResponse` in [schemas.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/schemas.py):

- `conversation_id`
- `message_id`
- `detected_language`
- `response_language`
- `answer`
- `scope`
- `confidence`
- `out_of_scope`
- `diagnosis`
- `links`
- `missing_permissions`
- `next_steps`
- `tool_trace_id`

Frontend consumption is implemented in [assistant.ts](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/api/sicherplan/assistant.ts) and rendered by [AssistantMessageList.vue](/home/jey/Projects/SicherPlan/web/apps/web-antd/src/components/sicherplan/assistant/AssistantMessageList.vue).

## Provider Modes

Current runtime modes from [config.py](/home/jey/Projects/SicherPlan/backend/app/config.py):

- `SP_AI_ENABLED=false`
  - assistant is disabled at backend capability level.
- `SP_AI_ENABLED=true` + `SP_AI_PROVIDER=mock`
  - deterministic backend-only mock answers for local development and CI.
- `SP_AI_ENABLED=true` + `SP_AI_PROVIDER=openai`
  - backend OpenAI Responses provider through [openai_client.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/openai_client.py).

Tests avoid real provider calls by:

- using `MockAssistantProvider`;
- using provider stubs in service-level tests;
- mocking frontend HTTP calls entirely.

## Knowledge Retrieval

Implemented knowledge pipeline:

1. explicit source registration (`KnowledgeSourceRegistration`);
2. safe source loading under allowed roots only;
3. SHA-256 hashing and unchanged-source skip;
4. markdown/text/json/openapi/repository-doc chunking;
5. persistence to `assistant.knowledge_source` and `assistant.knowledge_chunk`;
6. runtime retrieval from indexed chunks through [retriever.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/retriever.py).

Supported source types:

- `markdown`
- `text`
- `json`
- `openapi`
- `sprint_doc`
- `repository_docs`
- `manual`

Deferred source types:

- `pdf`
- `xlsx`

Current retrieval mode:

- lexical retrieval is active;
- embedding/vector hooks exist through [embeddings.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/knowledge/embeddings.py), but the default runtime is a no-op vector adapter.

Must not be indexed:

- `.env` files;
- credential/token/secret-like files;
- operational business data;
- customer-private, employee-private, HR-private, payroll, or document-bucket content.

## Tool Registry

The assistant tool registry is implemented in [tools/registry.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/registry.py).

Current registry rules:

- tool names are explicit and backend-owned;
- unknown tools are rejected;
- disabled tools are rejected;
- write-classified tools are rejected;
- input is schema-validated;
- SQL-like payloads are rejected;
- outputs are validated and redacted;
- allowed, denied, and failed calls are audited.

Current registered tool families include:

- capability and page-context tools;
- page-help and page-link tools;
- employee diagnostic tools;
- planning diagnostic tools;
- released schedule visibility tools;
- deterministic employee shift visibility diagnostic tool.

How to add a new read-only diagnostic tool:

1. create input/output schemas under `schemas.py` or tool-local models;
2. implement the tool under `backend/app/modules/assistant/tools/`;
3. declare `classification=READ_ONLY`;
4. declare required permissions and scope behavior;
5. register the tool in `build_default_tool_registry(...)`;
6. add service or tool-level tests;
7. add security coverage for permission denial and redaction.

## Same-Language Behavior

Language handling is implemented in [language.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/language.py) and used from [service.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/service.py).

Current behavior:

- detect message language from the current user input;
- choose a response language from current message signal plus UI locale fallback;
- keep out-of-scope refusals and missing-permission/diagnostic messaging in the selected language;
- preserve technical SicherPlan domain terms where translation would reduce clarity.

The current implementation supports deterministic same-language handling for at least:

- German;
- Persian;
- English.

## Current Diagnostic Coverage

The main operational diagnostic today is the Markus-style employee shift visibility investigation:

- employee lookup and readiness checks;
- employee mobile/self-service access status;
- assignment lookup and state inspection;
- shift release and visibility inspection;
- assignment and release validations;
- released-schedule visibility confirmation;
- allowed follow-up page links.

Core files:

- [diagnostics/shift_visibility.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/diagnostics/shift_visibility.py)
- [diagnostics/released_schedule_visibility.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/diagnostics/released_schedule_visibility.py)
- [tools/employee_tools.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/employee_tools.py)
- [tools/planning_tools.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/planning_tools.py)
- [tools/field_tools.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/field_tools.py)

Current limitations:

- no generic finance diagnostics yet;
- no mobile-app assistant UI;
- no customer/subcontractor assistant rollout beyond backend-aware role/scope handling;
- no write actions;
- no generic provider-driven tool-call orchestration loop.

## Follow-up Roadmap

Follow-up items, not implemented in this branch:

- knowledge reindex/status HTTP endpoints;
- broader verified page-help coverage;
- finance and reporting diagnostics;
- controlled write workflows with explicit confirmation and audit;
- mobile assistant UI;
- portal-specific frontend rollout;
- real vector search backend if needed.
