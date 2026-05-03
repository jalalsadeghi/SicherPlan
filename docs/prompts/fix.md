You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

Investigate and permanently fix the recurring GitHub Actions failure:
https://github.com/jalalsadeghi/SicherPlan/actions/runs/25275884953/job/74105665196

Current failing job:
Build Backend Stage Image

Current failing workflow:
`.github/workflows/stage-deploy.yml`

Current failing step:
`Verify committed field/lookup corpus artifact is current`

Observed CI behavior:
The workflow installs backend dependencies successfully and imports `field_dictionary_export` successfully.

The failing step currently:
1. runs `field_dictionary_export` twice into two temp files
2. checks that temp output 1 and temp output 2 are identical
3. compares the committed file `backend/app/modules/assistant/generated/field_lookup_corpus.json` against the fresh output
4. fails if the committed artifact is stale

Current CI output shows:
- field_count=219
- lookup_count=10
- term_count=525
- field_counts_by_module={'planning': 38, 'customers': 106, 'platform_services': 6, 'employees': 69}
- lookup_counts_by_module={'customers': 6, 'planning': 4}
- term_counts_by_module={'planning': 282, 'unknown': 243}
- warnings=['fa_locale_missing']

The temp1/temp2 deterministic comparison does not appear to fail.
The failure happens when the committed artifact is compared against the freshly generated output.

Visible stale-artifact diff includes new source references and locale terms for the Assignment step, such as:
- `AssignmentStepApplyResult.actor_kind`
- `AssignmentStepCandidateRead.actor_kind`
- `AssignmentStepExistingAssignmentRead.actor_kind`
- `AssignmentStepScopeRequest.actor_kind`
- `AssignmentStepScopeRequest.date_from`
- `AssignmentStepScopeRequest.date_to`
- `AssignmentStepApplyItemResult.demand_group_id`
- `AssignmentStepCandidateDayStatusRead.demand_group_id`
- `AssignmentStepCellRead.demand_group_id`
- `AssignmentStepOrderSummaryRead.planning_mode_code`
- `AssignmentStepShiftPlanSummaryRead.planning_from`
- new localized UI terms such as:
  - `Calendar & staffing workspace`
  - `Candidates`
  - `No candidates found`
  - `No demand groups available`
  - `No generated shifts`
  - `Assignments locked`

Likely root cause:
This is a recurring generated-artifact workflow problem. Every time Codex or a developer changes backend schemas, TypeScript API interfaces, Vue bindings, page help seeds, or locale labels, the generated assistant field/lookup corpus changes. The code changes are valid, but `backend/app/modules/assistant/generated/field_lookup_corpus.json` is not regenerated and committed. The Stage Deploy workflow then fails.

Important:
Do not merely regenerate `backend/app/modules/assistant/generated/field_lookup_corpus.json` again and stop. That only fixes the current run and the same failure will recur.
Do not remove deterministic checking.
Do not hide nondeterminism.
Do not hardcode only the currently visible diff lines.
Do not break the backend image smoke test.
Do not change unrelated product/business logic.
Treat `fa_locale_missing` as non-blocking unless you prove it is the cause of this failure.

Goal:
Implement a durable solution so Stage Deploy does not repeatedly fail just because this generated artifact is stale after valid source changes.

You must validate the best durable strategy before coding. The preferred direction is:
1. Keep the exporter deterministic check.
2. Generate the field/lookup corpus artifact automatically in CI before the backend Docker build.
3. Build the backend stage image with the freshly generated artifact from the workflow workspace.
4. Stop blocking Stage Deploy solely because the committed generated artifact is stale.
5. Preserve a developer-facing check or script so the artifact can still be regenerated and checked locally.
6. Add clear documentation and Codex/developer guidance so future changes know when and how to regenerate/check the artifact.

Files to inspect:
- `.github/workflows/stage-deploy.yml`
- `backend/app/modules/assistant/field_dictionary.py`
- `backend/app/modules/assistant/field_dictionary_export.py`
- `backend/app/modules/assistant/generated/field_lookup_corpus.json`
- `backend/tests/modules/assistant/test_field_lookup_source_hashes_stable.py`
- `docs/assistant/stage-field-dictionary-verification.md`
- `AGENTS.md`
- `backend/Dockerfile.stage`
- any existing scripts/Makefile/pyproject tool entry points
- current frontend/backend files that changed Assignment-step schemas/locales

Current behavior to reproduce:
From `backend/`:
```bash
tmp1="$(mktemp)"
tmp2="$(mktemp)"
python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
diff -u "$tmp1" "$tmp2"
diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
```

Task 1 — Confirm current failure:
1. Reproduce the CI check locally.
2. Confirm whether exporter output is deterministic.
3. Confirm the committed artifact is stale.
4. Confirm this is not a Docker failure, not a Python dependency failure, and not a backend runtime failure.

Task 2 — Add a single reusable generated-artifact helper:
Create a small maintainable helper script or module, for example:
- `backend/scripts/field_lookup_corpus_artifact.py`
or, if project conventions prefer module paths:
- `backend/app/modules/assistant/field_lookup_corpus_artifact.py`

The helper should support at least:
1. `generate`
   - generates `backend/app/modules/assistant/generated/field_lookup_corpus.json`
2. `check-deterministic`
   - runs the exporter twice into temp files and fails if they differ
3. `check-committed`
   - compares committed artifact with fresh output and fails if stale
4. `ensure-current`
   - runs deterministic check and then writes the fresh generated artifact to the committed artifact path

The script should:
- accept `--repo-root`
- accept `--output` where relevant
- produce clear messages
- never include volatile paths in output
- keep temp files clean
- return meaningful exit codes
- be usable both locally and in GitHub Actions

If adding a separate helper is unnecessary because an existing script already supports this cleanly, reuse and improve the existing script instead.

Task 3 — Update Stage Deploy workflow for permanent stability:
Update `.github/workflows/stage-deploy.yml` so `build_backend` no longer fails solely because the committed artifact is stale.

Preferred workflow shape:
1. Install backend dependencies.
2. Smoke-test importer.
3. Run deterministic check:
   ```bash
   python <helper> check-deterministic --repo-root ..
   ```
4. Generate the current artifact into the working tree:
   ```bash
   python <helper> ensure-current --repo-root ..
   ```
5. Optionally print a concise diff summary if the working tree artifact changed, but do not fail Stage Deploy only for that stale-committed-file condition.
6. Build backend Docker image from the workspace containing the freshly generated artifact.
7. Keep the backend image smoke test that verifies the corpus file exists and detection works.

Important workflow decision:
- Stage Deploy is a deployment pipeline from `main`. It should produce a correct backend image from the current source.
- It should not repeatedly fail because a derived generated JSON file was not refreshed before merge.
- Nondeterministic exporter output should still fail the workflow.
- Actual smoke-test failures should still fail the workflow.

Task 4 — Keep or add a stricter developer/PR check:
Add a separate developer-facing check so stale artifacts can still be caught intentionally without breaking deployment stability.

Choose the best repo-appropriate option:
A. Add a separate workflow/job named something like `Verify Generated Artifacts` on `pull_request` that runs `check-committed`.
B. Add a `workflow_dispatch` input to Stage Deploy to enforce committed artifact freshness.
C. Add a local command documented for developers and Codex, but do not add a blocking deploy check.
D. Another better option if the repo already has a generated-artifact check pattern.

Whatever you choose, explain why.

If you add a PR-only check:
- It may fail PRs if the artifact is stale, but Stage Deploy from `main` should generate the artifact for image build.
- If no PR workflow exists, add a minimal targeted workflow rather than mixing it into deployment.
- Keep permissions minimal.

Task 5 — Update developer/Codex guidance:
Update documentation so this stops recurring.

Update or add:
- `docs/assistant/stage-field-dictionary-verification.md`
- `AGENTS.md`
- optionally a short `docs/engineering/generated-artifacts.md`

The guidance must state:
1. The generated corpus depends on:
   - backend schema fields
   - TypeScript API interfaces
   - Vue field bindings
   - locale labels
   - page help seed data
2. When those inputs change, the corpus may change.
3. Local command to refresh:
   ```bash
   cd backend
   python <helper> ensure-current --repo-root ..
   ```
4. Local command to check committed freshness:
   ```bash
   cd backend
   python <helper> check-committed --repo-root ..
   ```
5. Stage Deploy generates the artifact before building the image, so deployment remains stable.
6. Determinism is still enforced.

Task 6 — Regenerate the current artifact:
After implementing the durable workflow/script/docs:
1. Regenerate `backend/app/modules/assistant/generated/field_lookup_corpus.json`.
2. Inspect the diff.
3. Confirm it contains the current Assignment-step schema and locale additions.
4. Do not manually edit the generated JSON.

Task 7 — Tests and verification:
Run the following and report exact results:

```bash
cd backend
python -m pip install -e .

python <helper> check-deterministic --repo-root ..
python <helper> ensure-current --repo-root ..
python <helper> check-committed --repo-root ..

python - <<'PY'
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal

assert detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None
assert detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None
assert detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None
print("field dictionary smoke test ok")
PY

pytest backend/tests/modules/assistant -q
```

If the exact paths or pytest command differ, use the repo-correct command and report it.

Also validate the updated workflow logic by mentally or locally simulating:
- exporter deterministic -> pass
- committed artifact stale -> Stage Deploy regenerates -> backend Docker build uses fresh artifact -> pass
- exporter nondeterministic -> fail
- generated image missing corpus -> image smoke test fails

Expected files likely to change:
- `.github/workflows/stage-deploy.yml`
- new helper script/module under `backend/scripts/` or `backend/app/modules/assistant/`
- `backend/app/modules/assistant/generated/field_lookup_corpus.json`
- `docs/assistant/stage-field-dictionary-verification.md`
- `AGENTS.md`
- maybe a new generated-artifact PR workflow if you choose that option
- tests if helper logic is testable

Output format:
- Root cause
- Why the old fix kept recurring
- Permanent strategy chosen
- Workflow changes
- Helper script usage
- Whether Stage Deploy still enforces determinism
- Whether Stage Deploy still fails on real corpus/runtime failures
- Whether stale committed artifact still blocks deployment: yes/no and why
- Files changed
- Artifact diff summary
- Tests/verification results
- Remaining risks or follow-ups

Self-validation requirement:
Before final response, explicitly challenge the proposed fix:
- Could this hide a real generator bug?
- Could this build a Docker image with an uncommitted generated file correctly?
- Could this make local development worse?
- Could this break the assistant field dictionary runtime?
- Does this actually stop the recurring GitHub Actions failure pattern?

If any answer reveals a risk, adjust the implementation before finalizing.
