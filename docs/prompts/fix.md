You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

Task:
Fix the recurring GitHub Actions failure around `field_lookup_corpus.json` permanently.

Failing GitHub Actions job to investigate:
https://github.com/jalalsadeghi/SicherPlan/actions/runs/25273602415/job/74099838117

Current failing job:
Build Backend Stage Image

Current failing step:
Verify committed field/lookup corpus artifact is current

Observed CI behavior:
The CI job installs backend dependencies successfully and imports `field_dictionary_export` successfully.

Then the workflow runs the field/lookup corpus exporter twice:
1. `tmp1`
2. `tmp2`

The two generated outputs are deterministic because CI does not fail on `diff -u "$tmp1" "$tmp2"`.

The failure happens when CI compares the committed artifact against the freshly generated output:

```bash
diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
```

CI output summary from the failing run:
- field_count=219
- lookup_count=10
- term_count=525
- field_counts_by_module={'planning': 38, 'customers': 106, 'platform_services': 6, 'employees': 69}
- lookup_counts_by_module={'customers': 6, 'planning': 4}
- term_counts_by_module={'planning': 282, 'unknown': 243}
- warnings=['fa_locale_missing']

Visible diff examples:
- `actor_kind` confidence changes from low to medium.
- New backend schema and TypeScript interface sources are added for:
  - AssignmentStepApplyResult.actor_kind
  - AssignmentStepCandidateRead.actor_kind
  - AssignmentStepExistingAssignmentRead.actor_kind
  - AssignmentStepScopeRequest.actor_kind
  - AssignmentStepScopeRequest.date_from/date_to/search/team_id
  - AssignmentStepApplyRequest.employee_id/team_id
  - AssignmentStepCellRead.demand_group_id/function_type_id/qualification_type_id/starts_at/ends_at
  - AssignmentStepDemandGroupMatch.function_type_id/qualification_type_id/sort_order
  - AssignmentStepDemandGroupSummaryRead.function_type_id/qualification_type_id/sort_order
  - AssignmentStepOrderSummaryRead.planning_mode_code/planning_record_id/order_no
  - AssignmentStepShiftPlanSummaryRead.planning_from/planning_to/workforce_scope_code
- New localized UI terms are added from the new Assignments step, such as:
  - Calendar & staffing workspace
  - Candidates
  - No candidates found
  - No demand groups available
  - No generated shifts
  - Assignments locked
- Source hashes change for:
  - backend_schema_fields
  - locale_labels
  - typescript_interfaces

Recurring root problem:
Every time frontend labels, TypeScript interfaces, backend schemas, or assistant page-help seeds change, the generated artifact changes. The current stage-deploy workflow fails unless the developer also regenerates and commits:

`backend/app/modules/assistant/generated/field_lookup_corpus.json`

This is why the same problem keeps recurring. Simply regenerating the artifact again is not a permanent fix.

Current repo facts to validate:
- `.github/workflows/stage-deploy.yml` has a step named `Verify committed field/lookup corpus artifact is current`, and that step fails when the committed artifact differs from freshly generated output.
- `backend/Dockerfile.stage` currently copies only `backend/` into the backend image.
- `docs/assistant/field-lookup-corpus.md` says the backend image needs a packaged corpus artifact because the stage backend image does not include frontend source files.
- `docs/assistant/stage-field-dictionary-verification.md` says CI enforces regeneration and failure when the committed artifact differs.
- `backend/pyproject.toml` includes package-data for:
  `app.modules.assistant.generated = ["field_lookup_corpus.json"]`
- `infra/scripts/check_backend_ci.sh` also checks that the generated artifact matches the committed file.
- `backend/tests/modules/assistant/test_field_lookup_artifact_freshness_behavior.py` has a test named `test_committed_artifact_matches_regenerated_output`, which enforces the same recurring failure pattern.
- `field_dictionary.py` currently loads the packaged generated artifact first, then live-source extraction if present, then empty corpus.

Important product/runtime constraint:
The backend stage image still must contain a valid field/lookup corpus artifact, because frontend source files are not present in the backend image. The fix must preserve the runtime behavior that short field-label questions work in the backend container, for example:
- `was bedeutet Vertragsreferenz`
- `was bedeutet Rechtlicher Name`
and irrelevant terms like:
- `was bedeutet Apfelkuchen`
must not produce a false positive.

Main goal:
Change the CI/build strategy so the backend image always receives a fresh generated corpus artifact automatically, while still verifying that the exporter is deterministic and that the runtime assistant smoke tests pass.

This should prevent future source changes from repeatedly breaking stage deploy merely because the committed generated file was not manually refreshed.

Do not just regenerate `field_lookup_corpus.json`.
Do not only patch the current diff.
Do not remove the assistant smoke tests.
Do not make the backend image lose the generated artifact.
Do not hide nondeterminism.
Do not loosen tenant/security/business logic.

Recommended permanent direction to validate:
Treat `field_lookup_corpus.json` as a generated build artifact for the stage backend image rather than a manually maintained source-of-truth file.

A robust approach is:
1. Keep deterministic generation checks.
2. In CI/stage deploy, generate the artifact into:
   `backend/app/modules/assistant/generated/field_lookup_corpus.json`
   before building the backend Docker image.
3. Build the backend Docker image after generation, so Docker copies the fresh artifact into the image.
4. Smoke-test the backend image exactly as today.
5. Stop failing stage deploy only because the committed artifact is stale.
6. Update local CI script/tests/docs so they verify deterministic generation and runtime behavior, not manual artifact freshness.
7. Optionally keep the committed artifact as a fallback, but do not require it to be manually fresh for stage deploy if CI generates a fresh one before image build.
8. If you decide the artifact should remain committed and freshness should still be enforced somewhere, implement an explicit non-deploy helper workflow or developer script that is separate from stage deploy, not a recurring blocker for stage image builds.

Before coding:
1. Reproduce the failure locally:
   ```bash
   cd backend
   python -m pip install -e .
   tmp1="$(mktemp)"
   tmp2="$(mktemp)"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
   diff -u "$tmp1" "$tmp2"
   diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
   ```
2. Confirm that the exporter is deterministic.
3. Confirm that the failure is stale committed artifact, not nondeterminism.
4. Inspect:
   - `.github/workflows/stage-deploy.yml`
   - `backend/Dockerfile.stage`
   - `backend/pyproject.toml`
   - `backend/app/modules/assistant/field_dictionary.py`
   - `backend/app/modules/assistant/field_dictionary_export.py`
   - `infra/scripts/check_backend_ci.sh`
   - `backend/tests/modules/assistant/test_field_lookup_artifact_freshness_behavior.py`
   - `backend/tests/modules/assistant/test_field_lookup_source_hashes_stable.py`
   - `backend/tests/modules/assistant/test_field_lookup_corpus_artifact.py`
   - `docs/assistant/field-lookup-corpus.md`
   - `docs/assistant/stage-field-dictionary-verification.md`

Implementation requirements:
1. Modify `.github/workflows/stage-deploy.yml`.
   - Replace the current failing freshness check with a deterministic generation step.
   - The new step should:
     a. Generate `tmp1`.
     b. Generate `tmp2`.
     c. Fail if `tmp1` and `tmp2` differ.
     d. Copy or write the deterministic generated output to:
        `backend/app/modules/assistant/generated/field_lookup_corpus.json`
        in the checked-out workspace.
     e. Print a concise summary and optionally `git diff --stat` for observability, but do not fail only because the committed file was stale.
   - Keep the backend Docker build after this step so the image includes the fresh generated artifact.
   - Keep the backend image smoke test.

2. Update `infra/scripts/check_backend_ci.sh`.
   - It should still verify deterministic generation.
   - It should no longer fail only because the committed artifact differs from generated output.
   - It should generate or refresh the artifact in the local working tree before checking package-resource availability.
   - It should keep the smoke checks and compile/ruff checks.

3. Update backend tests.
   - Replace or adjust `test_committed_artifact_matches_regenerated_output`.
   - Do not keep a test that permanently requires manual committed artifact freshness if stage deploy no longer requires it.
   - Add tests that verify:
     a. exporter is deterministic;
     b. generated artifact shape has schema_version 1;
     c. runtime detection still works for the important smoke terms;
     d. package resource loading works when the generated artifact exists.
   - If possible, add a test for build-time generation behavior using a temporary generated output rather than the committed file.

4. Update runtime/local behavior if necessary.
   - If the committed artifact can now be stale, make sure local development with a full repo checkout does not prefer a stale packaged artifact over current live sources in a harmful way.
   - Consider changing runtime load order or adding a source-hash freshness check:
     - In backend container/stage image: use packaged generated artifact.
     - In local full repository checkout: use live-source extraction or a freshness-aware artifact preference.
   - Do this only if needed and keep it cached; do not make normal assistant calls expensive.

5. Update documentation.
   - `docs/assistant/field-lookup-corpus.md`
   - `docs/assistant/stage-field-dictionary-verification.md`
   Explain the new policy clearly:
   - The stage backend image receives a freshly generated artifact during CI before Docker build.
   - Determinism is still enforced.
   - Backend image smoke tests still verify that the artifact is present and useful.
   - Developers may still regenerate locally when desired, but forgetting to commit the generated JSON should not break stage deploy if CI generates it.
   - If the committed artifact is intentionally kept, document whether it is a fallback/reference artifact, not the stage deploy source of truth.

6. Decide whether to keep tracking `backend/app/modules/assistant/generated/field_lookup_corpus.json`.
   - Validate the safest choice.
   - If keeping it tracked, explain why and ensure CI generation overwrites it before build.
   - If untracking/removing it, ensure:
     - package-data still works when CI generates the file before build;
     - local tests/scripts generate it before package-resource checks;
     - docs are updated;
     - no import or package-data failure occurs when the file is absent before generation.
   - Do not remove it unless you prove the build/test/runtime paths remain correct.

7. Do not remove or weaken these checks:
   - deterministic generation check;
   - backend image smoke test;
   - `detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None`;
   - `detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None`;
   - `detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None`.

8. Treat `fa_locale_missing` as non-blocking unless you prove it is the cause of the failure.
   - Do not make this warning block deploy in this task.

Verification commands:
Run and report exact results.

Backend local verification:
```bash
cd backend
python -m pip install -e .
tmp1="$(mktemp)"
tmp2="$(mktemp)"
python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
diff -u "$tmp1" "$tmp2"
cp "$tmp1" app/modules/assistant/generated/field_lookup_corpus.json
python - <<'PY'
from importlib.resources import files
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal, field_definition_counts_by_module

path = files("app.modules.assistant.generated").joinpath("field_lookup_corpus.json")
print(path)
print(path.is_file())
print(field_definition_counts_by_module())
assert detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None
assert detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None
assert detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None
print("field lookup smoke ok")
PY
pytest backend/tests/modules/assistant -q
```

If the repo expects running tests from `backend/`, adjust paths accordingly and report the exact commands used.

Workflow-equivalent verification:
- Run the updated generation step manually or through a dry-run script.
- Confirm it no longer fails only because committed artifact was stale.
- Confirm it still fails if `tmp1` and `tmp2` differ.
- Confirm Docker image build still includes the generated artifact.
- Confirm Docker smoke test still passes.

Optional Docker verification:
```bash
docker build -f backend/Dockerfile.stage -t sicherplan-backend-smoke:field-corpus .
docker run --rm sicherplan-backend-smoke:field-corpus python - <<'PY'
from importlib.resources import files
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal
path = files("app.modules.assistant.generated").joinpath("field_lookup_corpus.json")
print(path)
print(path.is_file())
assert detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None
assert detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None
assert detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None
print("docker field lookup smoke ok")
PY
```

Output format:
- Root cause
- Why previous fixes were temporary
- Permanent strategy chosen
- Whether the artifact remains tracked or becomes build-generated only
- Files changed
- CI workflow changes
- Script/test changes
- Runtime/package-data impact
- Documentation changes
- Verification commands and results
- Remaining risks or follow-ups

Final self-check:
Before finishing, explicitly answer:
1. Will a future frontend label/interface/schema change still break stage deploy just because the developer forgot to commit `field_lookup_corpus.json`?
2. Will CI still catch nondeterministic generation?
3. Will the backend stage image still include a valid generated corpus?
4. Will the existing assistant field/lookup smoke checks still pass inside the backend image?

If any answer is not clearly yes/no as expected, continue fixing until the permanent strategy is coherent.
