# Field/Lookup Corpus

The assistant field/lookup classifier cannot depend on live frontend source files at runtime.

Stage runs the backend image from [backend/Dockerfile.stage](/home/jey/Projects/SicherPlan/backend/Dockerfile.stage), and that image copies only `backend/`. The frontend locale files and Vue views are not present there. Without a packaged artifact, short field-label questions like `was bedeutet Vertragsreferenz` or `was bedeutet Rechtlicher Name` can fall back to out-of-scope.

## Artifact

Packaged artifact path:

- `backend/app/modules/assistant/generated/field_lookup_corpus.json`

The artifact is generated from the full repository checkout and then shipped with the backend package. Runtime loading prefers this artifact first.

## Regenerate

```bash
cd backend
python -m app.modules.assistant.field_lookup_corpus_artifact \
  ensure-current \
  --repo-root ..
```

## Check committed freshness

```bash
cd backend
python -m app.modules.assistant.field_lookup_corpus_artifact \
  check-committed \
  --repo-root ..
```

The command:

- reads frontend i18n
- reads Vue field bindings
- reads TypeScript API interfaces
- reads backend schemas/models
- reads assistant page-help seeds
- writes stable sorted JSON

It fails clearly when the required source paths are missing.

## Runtime behavior

`field_dictionary.py` now loads in this order:

1. packaged JSON artifact
2. live-source extraction from the local repo checkout, if present
3. empty corpus with a clear warning if neither exists

That keeps local and stage classification aligned without requiring frontend source files in the backend image.

## Verify in Docker or stage

Inside the backend container:

```bash
cd /app/backend
python - <<'PY'
from app.modules.assistant.field_dictionary import detect_field_or_lookup_signal
print(detect_field_or_lookup_signal("was bedeutet Vertragsreferenz", page_id="C-01", route_name="SicherPlanCustomers"))
PY
```

The check should return a non-`None` field signal even when `/app/web/...` does not exist.

## When frontend labels change

If field labels, form bindings, or lookup labels change in the frontend:

1. regenerate the artifact
2. verify committed freshness locally
3. run the field/lookup assistant tests
4. rebuild the backend image so the new artifact is included

Do not patch single keywords into the classifier. The artifact should stay source-grounded. 
