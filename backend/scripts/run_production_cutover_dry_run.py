"""Print the authoritative Sprint 12 production cutover path."""

from __future__ import annotations

CUTOVER_STEPS = (
    "Freeze configuration and change window; confirm no untracked manual hotfixes are pending.",
    "Verify latest backup/restore drill evidence and record pre-cutover checkpoint.",
    "Apply migration/config seed path in order: alembic, go-live seed, migration validation.",
    "Deploy backend, web, and mobile artifacts in the approved environment order.",
    "Run secured smoke checks for auth, tenant scope, docs access, portals, planning, finance, and reporting.",
    "Confirm monitoring gates and rollback checkpoints before broad release communication.",
)

MANUAL_STEPS = (
    "Approve freeze window and stakeholder broadcast.",
    "Validate production credentials and secrets outside version control.",
    "Record operator timestamps and signoffs in the cutover evidence log.",
)

AUTOMATED_COMMANDS = (
    "PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/seed_go_live_configuration.py --tenant-id <tenant_uuid>",
    "PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/run_trial_migration_validation.py",
    "PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/check_rollout_readiness_assets.py",
    "PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/check_operational_handover_assets.py",
)


def main() -> int:
    print("Sprint 12 production cutover dry-run")
    print("\ncutover_steps:")
    for index, step in enumerate(CUTOVER_STEPS, start=1):
        print(f"{index}. {step}")
    print("\nmanual_steps:")
    for step in MANUAL_STEPS:
        print(f"- {step}")
    print("\nautomated_commands:")
    for command in AUTOMATED_COMMANDS:
        print(command)
    print("\nexecution_note: this repository dry-run prepares the operator path; it does not claim live production execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
