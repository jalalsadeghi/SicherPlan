---
task_id: US-9-T1
story_id: US-9
story_title: "Customer portal read models, collaboration views, and customer-specific controls"
sprint: Sprint 03
status: ready
owner: "Web Lead / Backend Lead"
---

# Codex Prompt — US-9-T1

## Task title

**Build customer portal authentication and scope filters from role/user associations**

## Objective

Establish the customer-portal access layer so customer users authenticate as tenant-scoped accounts and can only enter portal routes and query paths that are restricted to their own customer relationship.

## Source context

- Updated proposal: section 4 role model for Customer User; section 5.2 customer portal scope and login-history expectations; Appendix A portal access and collaboration profile.
- Implementation specification: `iam.user_account`, `iam.user_role_scope`, and portal visibility chain; section 4.3 customer-contact portal linkage; section 8 migration/package notes.
- Sprint reference: `docs/sprint/sprint-03-customer-management.md`.
- Cross-cutting rules: `AGENTS.md`.

## Dependencies

- `US-5-T1`, `US-5-T2`, and `US-5-T3` should already provide user accounts, auth/session flows, and RBAC-friendly guards.
- `US-7-T1` should already provide customer-contact linkage to user accounts and portal-enabled flags.
- `US-7-T4` should already harden customer visibility and audit rules.
- `US-3-T1` and `US-3-T4` should already provide the web shell and DE/EN localization baseline.

## Scope of work

- Build or adapt the customer-portal authentication and route-guard layer so customer users enter a read-only portal experience distinct from internal admin flows while still remaining inside the tenant security model.
- Resolve customer scope from the current user through explicit role-scope records and/or customer-contact linkage; do not trust raw route parameters or UI state as the source of customer ownership.
- Apply scope filters consistently to portal API queries, navigation visibility, and page bootstrapping so a customer user can only access their own customer context.
- Create portal shell or route-group structure for customer users if the repository currently shares admin and portal layouts, keeping the UX aligned with the Vben-based web shell.
- Implement empty, loading, unauthorized, and deactivated-user states in DE and EN.
- Add tests for login/session handling, route protection, scope resolution, and denial of cross-customer access.

## Preferred file targets

- Web auth/portal route configuration, guards, stores, and page-layout files under the actual web-app path.
- Backend auth/scope helpers or portal query-context resolvers if the repository uses them.
- Localization resource files for portal auth and access-state messages.
- Frontend and/or integration tests for customer portal scope behavior.

## Hard constraints

- Customer users are not separate tenants; do not create a parallel tenant model or bypass the shared IAM/session system.
- Scope resolution must rely on explicit role/user/customer relationships, not unchecked customer IDs in requests.
- The customer portal remains read-only by default; do not introduce write access to tenant-wide datasets here.
- Do not widen customer scope through contact-email matching or other loose heuristics without approved user-account linkage.
- All portal auth/access strings must support German default and English secondary behavior.

## Expected implementation outputs

- A customer-portal auth/scope baseline built on the shared IAM model.
- Reliable customer-scope resolution for portal queries and navigation.
- Tests proving cross-customer access is denied.

## Non-goals

- Do not expose the final operational read models here; that is `US-9-T2`.
- Do not add broad customer-master-data editing to the portal here.
- Do not reimplement the shared login/session subsystem; integrate with it.

## Verification checklist

- Customer users can authenticate into the portal shell using the shared account/session model.
- The system resolves the correct customer scope from role/user associations and portal-enabled contact links.
- Cross-customer URL tampering or crafted request parameters do not expose other customer data.
- Deactivated or out-of-scope customer users are blocked cleanly.

## Codex response format

- A short implementation plan before touching files.
- A concise list of files created or modified.
- A summary of key design decisions and assumptions.
- Verification evidence: build/lint/test commands and notable outputs.
- Open follow-ups or blockers that should be carried into the next task.

## Codex `/review` prompt

Use this after the implementation for **US-9-T1 — Build customer portal authentication and scope filters from role/user associations** is finished.

```text
/review Please review the implementation for task US-9-T1 (Build customer portal authentication and scope filters from role/user associations) against this prompt file and the current repository state.

Review goals:
- Confirm the implementation matches the objective, dependencies, hard constraints, expected outputs, non-goals, and verification checklist in `docs/prompts/US-9-T1.md`.
- Review only the files that are relevant to this task, but also flag any upstream or downstream contract drift caused by the changes.
- Identify correctness, data-model, API-contract, migration, authorization, localization, testing, and maintainability issues.

Task-specific review focus:
- Portal auth uses the shared IAM model correctly and does not fork the security architecture.
- Customer scope resolution is explicit, test-covered, and resistant to route/query manipulation.
- Portal routes, guards, and access states are coherent with the Vben shell and localization rules.
- The portal remains read-only and least-privilege by default.

Required review output:
1. Blocking issues
2. Major issues
3. Minor issues
4. Nice-to-have improvements
5. Final verdict: `approved`, `approved with minor issues`, or `changes required`

Additional instructions:
- Be strict about tenant isolation, role scoping, auditability, DE default / EN secondary behavior, and traceability to US-9.
- Call out missing tests, weak assertions, incorrect acceptance coverage, schema drift, unsafe defaults, or assumptions that are not grounded in the proposal or implementation data model.
- If no real issue exists, say so clearly and do not invent problems.
```
