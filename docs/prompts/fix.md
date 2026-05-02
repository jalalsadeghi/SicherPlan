You are working in the SicherPlan repository.

Repository:
https://github.com/jalalsadeghi/SicherPlan

GitHub Actions failure to investigate:
https://github.com/jalalsadeghi/SicherPlan/actions/runs/25249512519/job/74039297911

Current failing job:
Build Backend Stage Image

Current failing step:
Verify committed field/lookup corpus artifact is current

Observed CI output:
- field_count=219
- lookup_count=10
- term_count=512
- field_counts_by_module={'planning': 38, 'customers': 106, 'platform_services': 6, 'employees': 69}
- lookup_counts_by_module={'customers': 6, 'planning': 4}
- term_counts_by_module={'planning': 282, 'unknown': 230}
- warnings=['fa_locale_missing']

The CI diff shows:

--- app/modules/assistant/generated/field_lookup_corpus.json
+++ /tmp/tmp...
@@
 "source_hashes": {
   "backend_schema_fields": "e79428d09156359d65cc7977d1fa0f617f1e48735ab506e869b40fdd7758d78d",
-  "locale_labels": "ffef1143342bf31b91cd02ad4c2a485a851fa33b4a345dd180bd5aae42a2adbe",
+  "locale_labels": "0b72f556ef85c84eb8b665fb3c0c455c168069086230d012704727cc7aee7a33",
   "page_help_seed_data": "f5dfd6a3ee268268020855336f57ba526ec9e245620feda137812602f24aa0de",
   "typescript_interfaces": "f4c60df1524f976e1f41511a3d113e3bf4cd90c1a9d49bf85c69d97debff89c7",
   "vue_field_bindings": "8606e1e5527c4a1ca4fbea8c5866b4517bbbfdb2f41f3d2516b4aa899f0e9918"
 }

CI error:
Generated field/lookup corpus artifact is stale. Regenerate backend/app/modules/assistant/generated/field_lookup_corpus.json.

Important interpretation to validate:
This looks like a stale generated artifact, not a Docker build failure and not a backend business-logic failure. The generator appears deterministic because CI generated tmp1 and tmp2 before comparing with the committed artifact, and no nondeterminism diff was reported. The only visible diff is the locale_labels source hash. The warning `fa_locale_missing` is non-blocking unless you prove otherwise.

Relevant files to inspect:
- .github/workflows/stage-deploy.yml
- docs/assistant/stage-field-dictionary-verification.md
- docs/prompts/AI-70.md
- docs/prompts/AI-71.md
- backend/app/modules/assistant/field_dictionary.py
- backend/app/modules/assistant/field_dictionary_export.py
- backend/app/modules/assistant/generated/field_lookup_corpus.json
- web/apps/web-antd/src/sicherplan-legacy/i18n/messages.ts
- web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json
- web/apps/web-antd/src/locales/langs/en-US/sicherplan.json
- web/apps/web-antd/src/locales/langs/fa-IR/sicherplan.json if it exists

Task:
1. Reproduce the CI check locally from `backend/`.
2. Run the exporter twice and verify byte-identical output:
   cd backend
   python -m pip install -e .
   tmp1="$(mktemp)"
   tmp2="$(mktemp)"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
   diff -u "$tmp1" "$tmp2"
3. Compare generated output with the committed artifact:
   diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
4. Classify the failure:
   - stale committed artifact only
   - nondeterministic exporter
   - meaningful source/content change
   - source hash calculation issue
   - missing locale issue
5. If the exporter is deterministic and the only issue is stale artifact, regenerate the committed artifact:
   python -m app.modules.assistant.field_dictionary_export \
     --repo-root .. \
     --output app/modules/assistant/generated/field_lookup_corpus.json
6. Inspect `git diff` carefully. Confirm whether the diff is only `source_hashes.locale_labels` or whether field/lookup/term content changed too.
7. Run smoke checks:
   python - <<'PY'
   from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal

   assert detect_field_or_lookup_signal("was bedeutet Vertragsreferenz") is not None
   assert detect_field_or_lookup_signal("was bedeutet Rechtlicher Name") is not None
   assert detect_field_or_lookup_signal("was bedeutet Apfelkuchen") is None
   print("field dictionary smoke test ok")
   PY
8. Run the same freshness check as CI:
   tmp1="$(mktemp)"
   tmp2="$(mktemp)"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp1"
   python -m app.modules.assistant.field_dictionary_export --repo-root .. --output "$tmp2"
   diff -u "$tmp1" "$tmp2"
   diff -u app/modules/assistant/generated/field_lookup_corpus.json "$tmp1"
9. Do not remove the CI check.
10. Do not ignore the diff.
11. Do not change Docker, deployment, customer/planning business code, or unrelated frontend code.
12. Only change generator code if you prove regeneration alone is not enough.

Expected minimal fix:
Most likely only this file should change:
backend/app/modules/assistant/generated/field_lookup_corpus.json

But you must validate this before deciding.

Report:
- root cause
- evidence from CI and local reproduction
- whether exporter was deterministic
- whether `fa_locale_missing` is blocking or non-blocking
- exact files changed
- summary of artifact diff
- smoke test result
- final CI-equivalent freshness check result