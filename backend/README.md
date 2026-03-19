# Backend Workspace

This directory is reserved for the FastAPI backend and its database/migration/test structure.

## Intended layout

- `app/` application package
- `app/modules/` bounded-context packages
- `alembic/` migration environment and revisions
- `tests/` backend tests

The package structure follows the bounded-context ownership rules in `AGENTS.md`. Cross-context reads are allowed through contracts and read models; direct cross-context master-data writes are not.
