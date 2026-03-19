---
task_id: US-5-T2
story_id: US-5
story_title: "Identity, role scope, session management, and audit foundation"
sprint: Sprint 02
status: ready
owner: "Backend Lead / Security Lead"
---

# Codex Prompt — US-5-T2

## Task title

**Build login/logout, password reset, session refresh, and MFA/SSO-ready hooks**

## Objective

Implement the operational authentication flows on top of the IAM schema so platform and tenant users can log in securely today while keeping the architecture ready for MFA and SSO later.

## Source context

- Updated proposal: section 5.1 identity and access; section 7 security baseline (OAuth2/OpenID Connect, password policy, rate limiting, input validation).
- Implementation specification: IAM table set from section 4.1 plus the rule that external side effects should stay behind integration jobs/outbox patterns rather than direct domain writes.
- Sprint reference: `docs/sprint/sprint-02-platform-core-and-backbone.md`.
- Cross-cutting rules: `AGENTS.md` and the shared error/logging conventions from Sprint 1.

## Dependencies

- `US-5-T1` must provide users, sessions, and external-identity persistence first.
- Reuse the shared config/error/logging infrastructure from Sprint 1 rather than introducing a parallel auth stack.

## Scope of work

- Implement login, logout, session refresh, and current-session/session-list endpoints using the repo's approved FastAPI auth pattern.
- Implement password reset request + confirm flows with secure, time-limited reset tokens or equivalent protected mechanics.
- Add hooks/interfaces for MFA and SSO/OIDC so the repo can evolve later without rewriting the login/session domain model.
- Respect rate limiting, lockout/abuse protections, and consistent machine-readable error responses as much as the current baseline already supports.
- If communication/outbox services are not yet ready, use a clearly swappable notification adapter or staging/dev-safe fallback for reset delivery rather than hardcoding provider logic inside auth transactions.
- Write tests for success paths, invalid credentials, revoked/expired sessions, password-reset edge cases, and logout behavior.

## Preferred file targets

- Auth service/router files under the actual IAM/auth package, for example `apps/api/modules/iam/services/auth_service.py`, `routers/auth_router.py`, and token utilities.
- Integration/adapter stubs for reset delivery if needed.
- Tests such as `apps/api/tests/modules/iam/test_auth_flows.py` or the repo equivalent.

## Hard constraints

- Never expose password hashes, raw reset secrets, or raw refresh tokens in logs, API payloads, or stored records.
- Keep auth APIs tenant-aware where needed, but do not accidentally reveal whether another tenant's account exists through response timing or wording.
- Do not hardcode a provider-specific MFA or SSO flow that locks the project into a single vendor before requirements are finalized.
- Preserve German default / English secondary behavior for any user-facing message keys, email template keys, or locale selection logic.
- Do not bypass the session store when issuing refresh-capable auth flows.

## Expected implementation outputs

- Working login/logout/session-refresh endpoints.
- Password reset flows that are secure, testable, and adapter-friendly.
- MFA/SSO-ready service seams or interface contracts.
- Automated auth tests and updated auth docs where appropriate.

## Non-goals

- Do not implement full production SSO or MFA provider integrations.
- Do not create portal/business-module screens here; focus on backend auth capabilities.
- Do not couple password-reset sending directly to a concrete email/SMS provider in domain code.
- Do not replace RBAC or scope checks with authentication-only checks.

## Verification checklist

- Valid users can authenticate, refresh, and log out through the supported APIs.
- Password reset tokens cannot be reused, guessed trivially, or left active indefinitely.
- Revoked or expired sessions are rejected consistently.
- The implementation leaves a clean extension seam for MFA and external identity providers.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-5-T2 — Build login/logout, password reset, session refresh, and MFA/SSO-ready hooks** is finished.

```text
/review Please review the implementation for task US-5-T2 (Build login/logout, password reset, session refresh, and MFA/SSO-ready hooks) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-5-T2.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Credential handling, token lifecycles, and session revocation are secure and test-covered.
- Auth error behavior does not leak sensitive account information or secrets.
- Password reset delivery is decoupled enough to integrate with the later communication backbone cleanly.
- The code is ready for MFA/SSO without premature vendor lock-in.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-5.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```
