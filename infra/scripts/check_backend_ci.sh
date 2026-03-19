#!/usr/bin/env bash
set -euo pipefail

test -f backend/.env.example
test -f backend/pyproject.toml
test -f backend/app/config.py
test -f backend/app/main.py

ruff check backend
python -m compileall backend/app backend/alembic
python infra/scripts/check_observability_ci.py
