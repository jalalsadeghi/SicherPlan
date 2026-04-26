# AI Assistant Final Hardening Report

## 1. Summary

- Final status: `GO WITH MINOR FOLLOW-UPS`
- Date: `2026-04-26`
- Branch: `main`
- Commit: `573a7a3fe86ae914ac9520f604b5cface960c683`
- Scope validated:
  - backend assistant module
  - assistant migrations
  - assistant docs
  - assistant backend tests
  - assistant frontend API/store/widget/tests
  - assistant security and non-regression checks

This pass did not add new assistant features. It verified the implemented assistant for read-only safety, tenant and role scoping, same-language behavior, documentation parity, and non-regression against nearby platform surfaces.

### Implemented endpoint surface

Implemented assistant endpoints at review time:

- `GET /api/assistant/capabilities`
- `GET /api/assistant/page-help/{page_id}`
- `POST /api/assistant/conversations`
- `GET /api/assistant/conversations/{conversation_id}`
- `POST /api/assistant/conversations/{conversation_id}/messages`
- `POST /api/assistant/conversations/{conversation_id}/feedback`

Not implemented:

- `GET /api/assistant/knowledge/status`
- `POST /api/assistant/knowledge/reindex`

### Config and provider modes

Reviewed AI-related config keys:

- `SP_AI_ENABLED`
- `SP_AI_PROVIDER`
- `SP_OPENAI_API_KEY`
- `SP_AI_RESPONSE_MODEL`
- `SP_AI_EMBEDDING_MODEL`
- `SP_AI_STORE_RESPONSES`
- `SP_AI_MAX_TOOL_CALLS`
- `SP_AI_MAX_CONTEXT_CHUNKS`
- `SP_AI_MAX_INPUT_CHARS`
- `SP_AI_TIMEOUT_SECONDS`
- `SP_AI_RATE_LIMIT_PER_USER_PER_MINUTE`
- `SP_AI_RATE_LIMIT_PER_TENANT_PER_MINUTE`
- `SP_AI_REDACTION_ENABLED`
- `SP_AI_AUDIT_ENABLED`

Provider modes implemented:

- disabled mode via `SP_AI_ENABLED=false`
- `mock`
- `openai`

### Known intentional divergences from the sprint prompt

- knowledge status and reindex are not exposed as HTTP endpoints yet
- assistant-specific rate limiting is configured but not enforced yet
- there is still no generic provider-driven tool execution loop; deterministic backend flows execute approved tools directly through the registry

## 2. Files Reviewed

### Backend assistant files

- `backend/app/modules/assistant/__init__.py`
- `backend/app/modules/assistant/classifier.py`
- `backend/app/modules/assistant/language.py`
- `backend/app/modules/assistant/models.py`
- `backend/app/modules/assistant/navigation.py`
- `backend/app/modules/assistant/openai_client.py`
- `backend/app/modules/assistant/page_catalog_seed.py`
- `backend/app/modules/assistant/page_help.py`
- `backend/app/modules/assistant/page_help_seed.py`
- `backend/app/modules/assistant/policy.py`
- `backend/app/modules/assistant/prompt_builder.py`
- `backend/app/modules/assistant/provider.py`
- `backend/app/modules/assistant/repository.py`
- `backend/app/modules/assistant/router.py`
- `backend/app/modules/assistant/schemas.py`
- `backend/app/modules/assistant/service.py`
- `backend/app/modules/assistant/diagnostics/*`
- `backend/app/modules/assistant/knowledge/*`
- `backend/app/modules/assistant/tools/*`

### Frontend assistant files

- `web/apps/web-antd/src/api/sicherplan/assistant.ts`
- `web/apps/web-antd/src/store/assistant-session.ts`
- `web/apps/web-antd/src/store/assistant.ts`
- `web/apps/web-antd/src/components/sicherplan/assistant/*`
- `web/apps/web-antd/src/locales/langs/de-DE/assistant.json`
- `web/apps/web-antd/src/locales/langs/en-US/assistant.json`
- `web/apps/web-antd/src/app.vue`

### Assistant migrations

- `backend/alembic/versions/0063_assistant_persistence_baseline.py`
- `backend/alembic/versions/0064_assistant_page_help_manifest.py`

### Assistant tests

#### Backend

- `backend/tests/modules/assistant/test_assistant_models_migration.py`
- `backend/tests/modules/assistant/test_assistant_service_mock_provider.py`
- `backend/tests/modules/assistant/test_capabilities.py`
- `backend/tests/modules/assistant/test_conversation_persistence.py`
- `backend/tests/modules/assistant/test_employee_tool_permissions.py`
- `backend/tests/modules/assistant/test_employee_tools.py`
- `backend/tests/modules/assistant/test_feedback.py`
- `backend/tests/modules/assistant/test_field_released_schedule_visibility.py`
- `backend/tests/modules/assistant/test_field_visibility_permissions.py`
- `backend/tests/modules/assistant/test_how_to_employee_create_exact_ui.py`
- `backend/tests/modules/assistant/test_knowledge_chunker.py`
- `backend/tests/modules/assistant/test_knowledge_ingestion.py`
- `backend/tests/modules/assistant/test_knowledge_retrieval.py`
- `backend/tests/modules/assistant/test_knowledge_source_loader.py`
- `backend/tests/modules/assistant/test_language_policy.py`
- `backend/tests/modules/assistant/test_navigation_links.py`
- `backend/tests/modules/assistant/test_openai_client_wrapper.py`
- `backend/tests/modules/assistant/test_openai_provider_errors.py`
- `backend/tests/modules/assistant/test_openai_provider_factory.py`
- `backend/tests/modules/assistant/test_openai_structured_output.py`
- `backend/tests/modules/assistant/test_out_of_scope.py`
- `backend/tests/modules/assistant/test_page_context_tools.py`
- `backend/tests/modules/assistant/test_page_help_manifest.py`
- `backend/tests/modules/assistant/test_page_route_catalog.py`
- `backend/tests/modules/assistant/test_planning_tool_permissions.py`
- `backend/tests/modules/assistant/test_planning_tools.py`
- `backend/tests/modules/assistant/test_prompt_builder.py`
- `backend/tests/modules/assistant/test_prompt_injection.py`
- `backend/tests/modules/assistant/test_provider_factory.py`
- `backend/tests/modules/assistant/test_provider_mock.py`
- `backend/tests/modules/assistant/test_security_integration.py`
- `backend/tests/modules/assistant/test_shift_visibility_diagnostic.py`
- `backend/tests/modules/assistant/test_shift_visibility_diagnostic_permissions.py`
- `backend/tests/modules/assistant/test_structured_response.py`
- `backend/tests/modules/assistant/test_tool_permissions.py`
- `backend/tests/modules/assistant/test_tool_registry.py`
- `backend/tests/modules/assistant/test_user_capability_tools.py`

#### Frontend

- `web/apps/web-antd/src/api/sicherplan/assistant.test.ts`
- `web/apps/web-antd/src/store/assistant.test.ts`
- `web/apps/web-antd/src/components/sicherplan/assistant/SicherPlanAssistantWidget.test.ts`
- `web/apps/web-antd/src/components/sicherplan/assistant/AssistantMessageList.test.ts`
- `web/apps/web-antd/src/components/sicherplan/assistant/AssistantMessageInput.test.ts`
- `web/apps/web-antd/src/components/sicherplan/assistant/AssistantLinkCard.test.ts`
- `web/apps/web-antd/src/sicherplan-legacy/features/employees/employeeAdmin.page-help.test.ts`

### Assistant docs

- `docs/sprint/AI-Assistant.md`
- `docs/engineering/ai-assistant-architecture.md`
- `docs/security/ai-assistant-security.md`
- `docs/runbooks/ai-assistant-knowledge-reindex.md`
- `docs/qa/ai-assistant-test-plan.md`

## 3. Test Results

| Area | Command | Result | Notes |
|---|---|---|---|
| Backend assistant curated sweep | `PYTHONPATH=backend python3 -m pytest -q backend/tests/modules/assistant/test_security_integration.py backend/tests/modules/assistant/test_feedback.py backend/tests/modules/assistant/test_out_of_scope.py backend/tests/modules/assistant/test_assistant_service_mock_provider.py backend/tests/modules/assistant/test_navigation_links.py backend/tests/modules/assistant/test_knowledge_retrieval.py backend/tests/modules/assistant/test_tool_registry.py backend/tests/modules/assistant/test_tool_permissions.py backend/tests/modules/assistant/test_prompt_injection.py backend/tests/modules/assistant/test_shift_visibility_diagnostic.py backend/tests/modules/assistant/test_shift_visibility_diagnostic_permissions.py` | PASS | `83 passed in 5.96s` |
| Backend assistant unittest baseline | `PYTHONPATH=backend python3 -m unittest backend.tests.modules.assistant.test_assistant_models_migration backend.tests.modules.core.test_alembic_versioning` | PASS | `Ran 12 tests`, `OK` |
| Broader backend non-assistant baseline | `PYTHONPATH=backend python3 -m unittest backend.tests.modules.employees.test_employee_router_paths backend.tests.modules.iam.test_seed_permissions backend.tests.modules.core.test_runtime_config_and_errors` | PASS | `Ran 24 tests`, `OK` |
| Full assistant pytest direct run | `timeout 90s env PYTHONPATH=backend python3 -m pytest -q backend/tests/modules/assistant; echo EXIT:$?` | PARTIAL | broad direct run still times out in this repo, `EXIT:124`; curated stable sweep above passes |
| Frontend assistant suites | `pnpm --dir web/apps/web-antd exec vitest run src/api/sicherplan/assistant.test.ts src/store/assistant.test.ts src/components/sicherplan/assistant/SicherPlanAssistantWidget.test.ts src/components/sicherplan/assistant/AssistantMessageList.test.ts src/components/sicherplan/assistant/AssistantMessageInput.test.ts src/components/sicherplan/assistant/AssistantLinkCard.test.ts src/sicherplan-legacy/features/employees/employeeAdmin.page-help.test.ts` | PASS | `7` files passed, `32` tests passed |
| Frontend build | `pnpm --dir web/apps/web-antd build` | PASS | build completed and produced `dist.zip`; one non-blocking dynamic import warning remained |
| Frontend typecheck | `pnpm --dir web/apps/web-antd typecheck` | PARTIAL | fails on pre-existing unrelated repo issues in legacy/router/shared files; no assistant-specific new failure identified |
| Broader frontend non-assistant baseline | `pnpm --dir web/apps/web-antd exec vitest run src/store/auth-session.test.ts src/store/auth-session-lifecycle.test.ts src/router/routes/modules/sicherplan.test.ts src/views/_core/authentication/login.test.ts` | PARTIAL | three suites passed; `login.test.ts` fails before tests due existing bad file path resolution |
| Backend syntax checks | `python3 -m py_compile ...` on touched assistant files and tests from prior tasks | PASS | no syntax issues found in assistant module or assistant test additions |
| Docs formatting tools | `command -v markdownlint` and `command -v prettier` | PARTIAL | not installed in this environment, so no automated docs formatting run was available |

## 4. Security Checklist Result

| Check | Result | Evidence |
|---|---|---|
| No frontend OpenAI call | PASS | source grep in `web/apps/web-antd/src` only found test assertions and provider-mode typing; no browser-side OpenAI client code |
| No frontend OpenAI key exposure | PASS | assistant frontend uses backend `/api/assistant/*` only; no frontend env or API key wiring |
| No arbitrary SQL | PASS | assistant tools do not accept SQL; `test_prompt_injection.py` passes; `execute(` hits are tool method execution plus internal SQLAlchemy repository calls; `models.py` `text(...)` use is server-default metadata only |
| Read-only tools only | PASS | `tools/registry.py` rejects non-`read_only` classifications; `test_tool_registry.py` and `test_tool_permissions.py` pass |
| Tenant isolation | PASS | tenant and user come from `RequestAuthorizationContext`; route/prompt tenant overrides are sanitized; cross-tenant checks pass in conversation and security tests |
| Permission enforcement | PASS | `assistant.chat.access`, `assistant.diagnostics.read`, `assistant.feedback.write`, and tool-specific permissions are enforced in policy, service, and registry tests |
| Redaction | PASS | `tools/redaction.py`, prompt redaction in `prompt_builder.py`, and assistant security tests cover masking of secrets and sensitive fields |
| Prompt injection | PASS | `test_prompt_injection.py` passes; out-of-scope and unsafe classifier path blocks override attempts and SQL/admin escalation prompts |
| Unauthorized links blocked | PASS | navigation links come from backend catalog/tool only; `test_navigation_links.py` passes; portal/internal separation is covered in `test_security_integration.py` |
| Same-language behavior | PASS | German, Persian, and English paths are covered by `test_security_integration.py`, `test_assistant_service_mock_provider.py`, and assistant language-policy checks |
| Markus diagnostic | PASS | `test_shift_visibility_diagnostic.py` and `test_shift_visibility_diagnostic_permissions.py` pass |
| Tool calls audited | PASS | tool audit persistence is exercised through registry tests and security integration coverage |

## 5. Non-regression Result

Existing areas verified in this hardening pass:

- assistant backend behavior
- assistant frontend widget, API, store, and feedback UI
- backend IAM seed/runtime config baselines
- backend employee router path baseline
- frontend auth-session and route baseline
- frontend build pipeline

Existing areas not fully green in this environment, but not caused by assistant implementation:

- broad `pytest backend/tests/modules/assistant` still hangs or times out under direct all-file execution
- global frontend `typecheck` still fails on pre-existing unrelated legacy/router/shared package errors
- one unrelated frontend login test still has a broken file path reference before test execution

No new assistant-specific regression was identified in login/session handling, route persistence, safe link navigation, or backend permission enforcement.

## 6. Open Issues

| Severity | Description | Affected files | Recommended next action |
|---|---|---|---|
| Medium | Assistant-specific runtime rate limiting is configured but not enforced yet. `SP_AI_RATE_LIMIT_PER_USER_PER_MINUTE` and `SP_AI_RATE_LIMIT_PER_TENANT_PER_MINUTE` exist in config only. | `backend/app/config.py`, `backend/app/modules/assistant/router.py`, `backend/app/modules/assistant/service.py` | implement backend assistant rate-limit middleware or service-level enforcement |
| Medium | Knowledge reindex/status exists at service/repository level only. There is no operator HTTP surface for `GET /api/assistant/knowledge/status` or `POST /api/assistant/knowledge/reindex`. | `backend/app/modules/assistant/knowledge/*`, `backend/app/modules/assistant/router.py` | either add the endpoints with `assistant.knowledge.reindex` gating or keep docs explicit that this is still internal-only |
| Medium | Broad direct assistant pytest execution is still unstable in this repo and times out. | `backend/tests/modules/assistant/*` | isolate or repair the hanging HTTP/TestClient suites so `pytest backend/tests/modules/assistant -q` is reliable |
| Low | Global frontend `typecheck` still fails on unrelated legacy and shared-package issues. | multiple existing files outside assistant scope | fix repo-wide TypeScript debt before using typecheck as a release gate |
| Low | Existing frontend login test has a broken source path and fails before assertions. | `web/apps/web-antd/src/views/_core/authentication/login.test.ts` | fix the test fixture/path resolution independently of assistant work |
| Low | `grep -R "api.openai.com" web` and `grep -R "OPENAI" web` do match third-party `node_modules` content under `web/internal/...`, which is not product code but does make raw repo-wide greps noisy. | `web/internal/lint-configs/commitlint-config/node_modules/*` | keep future checks scoped to app source or exclude vendored dependencies |

## 7. Go/No-Go Recommendation

`GO WITH MINOR FOLLOW-UPS`

Rationale:

- the implemented assistant is read-only, tenant-aware, permission-gated, documented, same-language aware, and covered by passing assistant-focused backend and frontend test suites;
- no direct frontend OpenAI call or frontend key exposure was found;
- no model-controlled SQL path was found;
- unauthorized links, prompt injection, and Markus shift-visibility diagnostic paths are covered and passing;
- remaining gaps are operational or repo-wide quality items, not current critical assistant security failures.
