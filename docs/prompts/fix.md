You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

Investigate and fix the GitHub Actions failure:
https://github.com/jalalsadeghi/SicherPlan/actions/runs/25250944030/job/74042821642

Current failing job:
Build Backend Stage Image

Current failing step:
Verify committed field/lookup corpus artifact is current

Observed CI behavior:
The workflow installs backend dependencies successfully and imports `field_dictionary_export` successfully.

The failing step runs:

```bash
tmp1="$(mktemp)"
tmp2="$(mktemp)"
python -m app.modules.assistant.field_dictionary_export   --repo-root ..   --output "$tmp1"
python -m app.modules.assistant.field_dictionary_export   --repo-root ..   --output "$tmp2"
if ! diff -u "$tmp1" "$tmp2"; then
  echo "Field/lookup corpus export is nondeterministic." >&2
  exit 1
fi
if ! diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"; then
  echo "Generated field/lookup corpus artifact is stale. Regenerate backend/app/modules/assistant/generated/field_lookup_corpus.json." >&2
  exit 1
fi
```

The two generated temporary files do not appear to differ from each other, so the exporter is likely deterministic. The failure happens when CI compares the committed artifact against the freshly generated artifact.

CI output summary:
- field_count=219
- lookup_count=10
- term_count=514
- field_counts_by_module={'planning': 38, 'customers': 106, 'platform_services': 6, 'employees': 69}
- lookup_counts_by_module={'customers': 6, 'planning': 4}
- term_counts_by_module={'planning': 282, 'unknown': 232}
- warnings=['fa_locale_missing']

Visible diff examples:
- New source references for `DemandGroupBulkApplyRequest.date_from`
- New source references for `DemandGroupBulkApplyRequest.date_to`
- New source references for `DemandGroupBulkTemplate.function_type_id`
- New source references for `DemandGroupBulkTemplate.qualification_type_id`
- New source references for `DemandGroupBulkTemplate.sort_order`
- Changed source hashes:
  - `backend_schema_fields`
  - `locale_labels`
  - `typescript_interfaces`
- New locale/platform terms related to the demand-groups wizard, such as:
  - `Add at least one demand group before continuing.`
  - `Fügen Sie mindestens eine Bedarfsgruppe hinzu, bevor Sie fortfahren.`
  - `Demand group {index}`
  - `Bedarfsgruppe {index}`
  - `No generated shifts available`
  - `Keine erzeugten Schichten vorhanden`

Likely root cause:
Recent changes added/updated demand-group bulk apply TypeScript interfaces and localized demand-group wizard labels, but the committed generated artifact `backend/app/modules/assistant/generated/field_lookup_corpus.json` was not regenerated and committed. This is most likely a stale generated artifact, not a Docker failure and not a backend runtime dependency failure.

Important:
Do not remove the CI check.
Do not make CI ignore the artifact diff.
Do not hardcode only the currently visible diff lines.
Do not alter Docker deployment logic.
Do not change unrelated business logic.
Do not change customer/planning frontend behavior unless you prove a generator/source issue requires it.
Treat `fa_locale_missing` as a warning unless you prove it is the cause of this job failure.

Files to inspect:
- `.github/workflows/stage-deploy.yml`
- `backend/app/modules/assistant/field_dictionary.py`
- `backend/app/modules/assistant/field_dictionary_export.py`
- `backend/app/modules/assistant/generated/field_lookup_corpus.json`
- `backend/tests/modules/assistant/test_field_lookup_source_hashes_stable.py`
- `docs/assistant/stage-field-dictionary-verification.md`
- `web/apps/web-antd/src/sicherplan-legacy/api/planningStaffing.ts`
- `web/apps/web-antd/src/views/sicherplan/customers/new-plan-step-content.vue`
- `web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json`
- `web/apps/web-antd/src/locales/langs/en-US/sicherplan.json`

Task:
1. Reproduce the CI check locally from the `backend/` directory.
2. Confirm whether the exporter is deterministic:
   ```bash
   cd backend
   python -m pip install -e .
   tmp1="$(mktemp)"
   tmp2="$(mktemp)"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
   diff -u "$tmp1" "$tmp2"
   ```
3. Compare the committed artifact with the fresh output:
   ```bash
   diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
   ```
4. Classify the failure:
   - stale generated artifact only
   - nondeterministic generator
   - source hash calculation bug
   - meaningful but expected source/content change
   - unexpected source/content change
5. If the exporter is deterministic and the diff is expected, regenerate the committed artifact:
   ```bash
   python -m app.modules.assistant.field_dictionary_export      --repo-root ..      --output app/modules/assistant/generated/field_lookup_corpus.json
   ```
6. Inspect `git diff` carefully.
7. Confirm whether the regenerated artifact includes the new demand-group bulk apply interface fields and new localized demand-group wizard terms.
8. Run smoke checks:
   ```bash
   python - <<'PY'
   from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal

   assert detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None
   assert detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None
   assert detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None
   print("field dictionary smoke test ok")
   PY
   ```
9. Run the CI-equivalent freshness check after regeneration:
   ```bash
   tmp1="$(mktemp)"
   tmp2="$(mktemp)"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
   diff -u "$tmp1" "$tmp2"
   diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
   ```
10. If simple regeneration is not enough, then inspect and fix the generator:
    - sorted file traversal
    - stable JSON serialization
    - source hash exclusions
    - exclusion of generated artifact from its own hash
    - deterministic source_basis sorting
    - duplicate handling
11. If generator logic changes are needed, add/update tests under `backend/tests/modules/assistant/`.
12. If only artifact regeneration is needed, do not change generator code.
13. Commit the refreshed generated artifact and any necessary tests/code changes.

Expected minimal fix:
Most likely only this file should change:
`backend/app/modules/assistant/generated/field_lookup_corpus.json`

But validate this before deciding.

Verification:
Run and report exact results:
```bash
cd backend
python -m pip install -e .
python -m app.modules.assistant.field_dictionary_export --repo-root .. --output /tmp/field_lookup_corpus.json
python - <<'PY'
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal
assert detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None
assert detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None
assert detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None
print("field dictionary smoke test ok")
PY
tmp1="$(mktemp)"
tmp2="$(mktemp)"
python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
diff -u "$tmp1" "$tmp2"
diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
```

Output format:
- Root cause
- Evidence from CI and local reproduction
- Exporter deterministic: yes/no
- Failure classification
- Files changed
- Artifact diff summary
- Whether `fa_locale_missing` is blocking or non-blocking
- Smoke test result
- CI-equivalent freshness check result
- Remaining risks or follow-ups
