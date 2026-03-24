Please inspect the current SicherPlan repository and the GitHub Actions workflows carefully, then fix the current CI failures with the smallest safe changes.

Context:
- We already changed backend packaging and stage Dockerfiles to address the earlier image build failures:
  - backend pyproject now uses setuptools build metadata and limits package discovery to app*
  - web stage Dockerfile now serves committed web/apps/web-antd/dist directly via nginx
- Current failing GitHub Actions jobs are now:
  1) Backend Lint And Smoke
  2) Migration Check
  3) Web Config Smoke
- The Node.js 20 deprecation messages are warnings only and are NOT the main failure cause.
- Do not disable checks blindly.
- Do not weaken coverage or remove meaningful validation just to get green checks.
- Do not touch mobile unless a workflow truly requires a tiny compatibility fix.

Your tasks:

1) Inspect all GitHub workflow files under .github/workflows
- Identify which workflow contains:
  - Backend Lint And Smoke
  - Migration Check
  - Web Config Smoke
- Read the exact commands those jobs run.

2) Fix Backend Lint And Smoke with minimal safe changes
- Ensure backend packaging works consistently in CI, not just in Docker.
- If CI installs the backend as a package, keep using the explicit setuptools package discovery that only includes app*.
- If CI expects lint tools not present in the runtime dependency list, add them in the appropriate safe place:
  - preferably optional dev dependencies or CI install commands,
  - not as unnecessary runtime dependencies.
- Make sure importing app.main works in CI after installation.
- Do not remove linting.

3) Fix Migration Check with minimal safe changes
- Determine whether the failure is caused by:
  - missing backend installation metadata,
  - missing environment variables,
  - missing database service in CI,
  - incorrect working directory,
  - or Alembic import/runtime assumptions.
- Keep migration validation meaningful.
- If the workflow truly needs a PostgreSQL service, add a minimal PostgreSQL service container to that workflow/job and wire the required env vars.
- If the issue is path/install related, fix the path/install problem instead.
- Do not simply skip migration checks.

4) Fix Web Config Smoke with minimal safe changes
- Inspect what this job validates.
- If it still assumes a full pnpm workspace install/build, adapt only the smoke check to the current repository reality:
  - the current stage strategy serves committed web/apps/web-antd/dist directly,
  - the current snapshot does not rely on pnpm install in the stage image path.
- Keep the smoke check meaningful:
  - for example, validate that web/apps/web-antd/dist/index.html exists,
  - validate that nginx stage config exists and references the backend proxy path correctly,
  - or validate the exact files that the stage image actually depends on.
- Do not fake success.

5) Keep separation of concerns
- Stage deployment workflow should remain focused on build/push/deploy.
- General smoke/lint/migration workflows should validate the current repo honestly.
- Do not mix unrelated responsibilities.

6) Add clear comments where needed
- Only where they improve maintainability.

7) At the end, summarize:
- which workflows/jobs were failing,
- the exact root cause of each,
- which files you changed,
- and why the new behavior is correct for the current repo snapshot.

Important constraints:
- No Kubernetes
- No production workflow changes unless required by the failing CI jobs
- Do not remove or disable jobs unless they are truly obsolete and replaced by an equivalent meaningful check
- Prefer minimal, targeted fixes