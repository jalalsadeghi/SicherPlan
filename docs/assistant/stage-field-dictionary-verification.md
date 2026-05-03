# Stage Field Dictionary Verification

The assistant field/lookup classifier depends on the packaged corpus artifact:

- `backend/app/modules/assistant/generated/field_lookup_corpus.json`

Stage does not copy frontend source files into the backend image. The backend image must therefore contain this artifact and the assistant must load it through package resources.

## Local generation

```bash
cd backend
python -m app.modules.assistant.field_lookup_corpus_artifact \
  ensure-current \
  --repo-root ..
```

## Local checks

The generated corpus depends on:

- backend schema fields
- TypeScript API interfaces
- Vue field bindings
- locale labels
- page help seed data

If any of those inputs change, regenerate or recheck the artifact locally.

Check determinism:

```bash
cd backend
python -m app.modules.assistant.field_lookup_corpus_artifact \
  check-deterministic \
  --repo-root ..
```

Check committed freshness:

```bash
cd backend
python -m app.modules.assistant.field_lookup_corpus_artifact \
  check-committed \
  --repo-root ..
```

## CI behavior

CI and Stage Deploy have different responsibilities now:

1. pull request CI enforces:
   - deterministic export
   - committed artifact freshness
2. Stage Deploy enforces:
   - deterministic export
   - regeneration of the artifact into the workflow workspace before backend image build
   - backend image smoke-test:
   - `was bedeutet Vertragsreferenz`
   - `was bedeutet Rechtlicher Name`
   - `was bedeutet Apfelkuchen`

That keeps deployment stable on `main` while still catching stale generated artifacts in developer-facing CI.

## Stage verification command

```bash
docker compose \
  --env-file /opt/sicherplan-stage/config/stage.env \
  -f /opt/sicherplan-stage/deploy/docker-compose.stage.yml \
  exec -T backend \
  python scripts/verify_assistant_field_dictionary.py
```

## Expected output

Example:

```text
artifact_loaded=true
artifact_version=1
field_count=219
lookup_count=10
counts_by_module={'planning': 38, 'customers': 106, 'platform_services': 6, 'employees': 69}
Vertragsreferenz signal=true matches=1
Rechtlicher Name signal=true matches=1
Apfelkuchen signal=false
```

## Troubleshooting

If stage still refuses field-label questions:

1. verify the backend image contains the artifact:
   ```bash
   docker compose \
     --env-file /opt/sicherplan-stage/config/stage.env \
     -f /opt/sicherplan-stage/deploy/docker-compose.stage.yml \
     exec -T backend \
     python - <<'PY'
   from importlib.resources import files
   path = files("app.modules.assistant.generated").joinpath("field_lookup_corpus.json")
   print(path)
   print(path.is_file())
   PY
   ```
2. rerun the verification script above
3. if the artifact is missing, regenerate it locally, commit it, and redeploy
4. if the artifact is present but stale, rerun the helper and check the diff against current backend schemas, TypeScript interfaces, Vue bindings, locale labels, and page-help seeds
