# SicherPlan AI Assistant Security

## Security Model Summary

The SicherPlan AI Assistant is secured as a backend-controlled, read-only assistant surface.

Security properties in the current implementation:

- provider calls are backend-only;
- the browser never calls OpenAI directly;
- the model never generates or executes arbitrary SQL;
- all runtime data access is mediated through explicit backend tools or deterministic backend service flows;
- the first release is read-only;
- tenant scope, role scope, and permission checks are enforced from backend auth context;
- sensitive outputs are redacted before they can be returned or sent to a provider;
- tool usage is audited.

Primary implementation files:

- [backend/app/modules/assistant/service.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/service.py)
- [backend/app/modules/assistant/policy.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/policy.py)
- [backend/app/modules/assistant/tools/registry.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/registry.py)
- [backend/app/modules/assistant/prompt_builder.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/prompt_builder.py)
- [backend/app/modules/assistant/classifier.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/classifier.py)
- [backend/app/modules/assistant/tools/redaction.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/redaction.py)

## Tenant Isolation

Tenant isolation rules:

- `tenant_id` comes from `RequestAuthorizationContext`, not from user input;
- frontend route/query context is informational only;
- user-supplied `tenant_id` and `user_id` values are sanitized or ignored;
- tools must resolve records inside current tenant/scope only;
- inaccessible record existence must not be confirmed.

Safe denial pattern used across the assistant:

- return not found / not permitted style results;
- do not reveal that a record exists in another tenant or outside actor scope.

## Permission Enforcement

Assistant permissions from [policy.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/policy.py):

- `assistant.chat.access`
- `assistant.diagnostics.read`
- `assistant.feedback.write`
- `assistant.knowledge.read`
- `assistant.knowledge.reindex`
- `assistant.admin`

Current seeded role mapping from [seed_permissions.py](/home/jey/Projects/SicherPlan/backend/app/modules/iam/seed_permissions.py):

### `assistant.chat.access`

- `platform_admin`
- `tenant_admin`
- `dispatcher`
- `accounting`
- `controller_qm`
- `customer_user`
- `subcontractor_user`
- `employee_user`

### `assistant.diagnostics.read`

- `platform_admin`
- `tenant_admin`
- `dispatcher`
- `accounting`
- `controller_qm`

### `assistant.feedback.write`

- `platform_admin`
- `tenant_admin`
- `dispatcher`
- `accounting`
- `controller_qm`
- `customer_user`
- `subcontractor_user`
- `employee_user`

### `assistant.knowledge.read`

- `platform_admin`
- `tenant_admin`
- `dispatcher`
- `accounting`
- `controller_qm`
- `customer_user`
- `subcontractor_user`
- `employee_user`

### `assistant.knowledge.reindex`

- `platform_admin`

### `assistant.admin`

- `platform_admin`

Important current limitation:

- `assistant.knowledge.reindex` is seeded, but there is no assistant HTTP reindex endpoint yet.

## Tool Execution Policy

Tool execution policy in [tools/registry.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/registry.py):

- unknown tools are rejected;
- disabled tools are rejected;
- write-classified tools are rejected;
- `assistant.chat.access` is required for any tool execution path;
- each tool must declare required permissions;
- each tool input is schema-validated;
- SQL-like input payloads are rejected before execution;
- outputs are validated and redacted;
- allowed, denied, and failed executions are audited.

Scope behavior is tool-declared and currently includes internal tenant-scoped tools plus restricted employee self-service behavior for released-schedule visibility.

## Prompt Injection Protection

Prompt injection and unsafe requests are handled by a combination of classifier rules and prompt-building policy.

Current protections:

- ignore-rules / reveal-system-prompt style requests are classified unsafe;
- run-SQL / dump-database style requests are classified unsafe;
- cross-tenant / impersonation requests are classified unsafe;
- write-action requests are blocked by read-only architecture and tool classification;
- unauthorized links are not built in the browser; links come from backend-approved navigation results only;
- verified UI guidance is restricted to seeded page-help manifests instead of guessed labels.

Relevant files:

- [classifier.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/classifier.py)
- [prompt_builder.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/prompt_builder.py)
- [page_help.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/page_help.py)
- [navigation.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/navigation.py)

## Data Redaction

Redaction rules apply to prompt-bound context, tool inputs/outputs, and safe UI answers.

Categories that must not be exposed without a dedicated authorized surface:

- tax identifiers;
- social insurance identifiers;
- health insurance identifiers;
- bank data;
- religion;
- payroll amounts where the actor is not authorized;
- passwords and password hashes;
- reset tokens;
- JWTs;
- API keys;
- integration secrets;
- private HR notes.

Current redaction implementations:

- [prompt_builder.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/prompt_builder.py)
- [tools/redaction.py](/home/jey/Projects/SicherPlan/backend/app/modules/assistant/tools/redaction.py)

## Provider Privacy

Provider privacy is backend-owned:

- `SP_OPENAI_API_KEY` is backend-only and excluded from settings `repr`;
- `SP_AI_STORE_RESPONSES` controls provider-side response storage behavior;
- default remains privacy-conservative: `false`;
- only minimal route/auth/knowledge/tool context is assembled for the provider;
- redacted tool summaries are sent, not raw unsafe payloads;
- provider errors are normalized to safe API errors.

Relevant settings:

- `SP_AI_ENABLED`
- `SP_AI_PROVIDER`
- `SP_OPENAI_API_KEY`
- `SP_AI_RESPONSE_MODEL`
- `SP_AI_STORE_RESPONSES`
- `SP_AI_TIMEOUT_SECONDS`
- `SP_AI_REDACTION_ENABLED`
- `SP_AI_AUDIT_ENABLED`

## Audit

Audited items currently include:

- assistant conversations and messages;
- tool calls through `assistant.tool_call`;
- feedback through `assistant.feedback`;
- denied tool calls;
- failed tool calls;
- permission decisions and error codes for tool usage.

The audit trail does not store:

- raw secrets;
- raw provider API keys;
- unredacted sensitive tool payloads.

How to investigate assistant tool activity:

1. inspect `assistant.tool_call`;
2. filter by `tenant_id`, `user_id`, `conversation_id`, `tool_name`, and `created_at`;
3. review `permission_decision`, `required_permissions`, `scope_kind`, and `error_code`.

## Rate Limiting and Safeguards

Configured assistant safeguards in [config.py](/home/jey/Projects/SicherPlan/backend/app/config.py):

- `SP_AI_MAX_INPUT_CHARS`
- `SP_AI_MAX_TOOL_CALLS`
- `SP_AI_MAX_CONTEXT_CHUNKS`
- `SP_AI_TIMEOUT_SECONDS`
- `SP_AI_RATE_LIMIT_PER_USER_PER_MINUTE`
- `SP_AI_RATE_LIMIT_PER_TENANT_PER_MINUTE`

Current enforcement status:

- `SP_AI_MAX_INPUT_CHARS` is enforced in assistant message handling;
- `SP_AI_MAX_CONTEXT_CHUNKS` is enforced in knowledge retrieval and prompt building;
- `SP_AI_MAX_TOOL_CALLS` is passed into provider request metadata and tool definitions;
- `SP_AI_TIMEOUT_SECONDS` is used by the OpenAI client wrapper;
- dedicated per-user and per-tenant assistant rate-limit enforcement is configured in settings but not yet implemented in the assistant router/service path.

This is a real implementation gap and should not be treated as complete rate-limit enforcement.

## Security Test Coverage

Assistant security coverage currently lives mainly under [backend/tests/modules/assistant](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant).

Key files:

- [test_prompt_injection.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_prompt_injection.py)
- [test_out_of_scope.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_out_of_scope.py)
- [test_tool_registry.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_tool_registry.py)
- [test_tool_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_tool_permissions.py)
- [test_employee_tool_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_employee_tool_permissions.py)
- [test_planning_tool_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_planning_tool_permissions.py)
- [test_field_visibility_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_field_visibility_permissions.py)
- [test_shift_visibility_diagnostic_permissions.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_shift_visibility_diagnostic_permissions.py)
- [test_security_integration.py](/home/jey/Projects/SicherPlan/backend/tests/modules/assistant/test_security_integration.py)

Security-specific behaviors covered there include:

- prompt injection refusal;
- out-of-scope refusal;
- unknown tool rejection;
- write tool rejection;
- permission denial;
- SQL-like input rejection;
- redaction of sensitive fields;
- cross-actor conversation isolation;
- same-language missing-permission diagnostics;
- safe provider timeout failures without secret leakage.
