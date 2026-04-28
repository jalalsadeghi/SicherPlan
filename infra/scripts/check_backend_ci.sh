#!/usr/bin/env bash
set -euo pipefail

test -f backend/.env.example
test -f backend/pyproject.toml
test -f backend/app/config.py
test -f backend/app/main.py
test -f backend/app/modules/assistant/generated/field_lookup_corpus.json

ruff check backend
python -m compileall backend/app backend/alembic
tmp_corpus="$(mktemp)"
PYTHONPATH=backend python -m app.modules.assistant.field_dictionary_export \
  --repo-root . \
  --output "$tmp_corpus"
if ! cmp --silent backend/app/modules/assistant/generated/field_lookup_corpus.json "$tmp_corpus"; then
  echo "Generated field/lookup corpus artifact is stale. Regenerate backend/app/modules/assistant/generated/field_lookup_corpus.json." >&2
  diff -u backend/app/modules/assistant/generated/field_lookup_corpus.json "$tmp_corpus" || true
  exit 1
fi
python - <<'PY'
from importlib.resources import files
path = files("app.modules.assistant.generated").joinpath("field_lookup_corpus.json")
assert path.is_file(), path
print(path)
PY
python infra/scripts/check_observability_ci.py
