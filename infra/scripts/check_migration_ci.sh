#!/usr/bin/env bash
set -euo pipefail

test -n "${SP_ALEMBIC_DATABASE_URL:-}"
test -f backend/alembic.ini
test -f backend/alembic/env.py

alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini downgrade base
alembic -c backend/alembic.ini upgrade head
