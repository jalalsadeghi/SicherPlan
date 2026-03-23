"""Print the repeatable Sprint 12 trial-migration validation suite."""

from __future__ import annotations

VALIDATION_SCENARIOS = (
    {
        "key": "portal_customer_visibility",
        "goal": "Migrated customers, timesheets, invoices, and docs remain correctly scoped in the customer portal.",
        "commands": [
            "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.customers.test_customer_portal_context backend.tests.modules.customers.test_customer_portal_read_models",
            "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.finance.test_billing_flows",
        ],
    },
    {
        "key": "portal_subcontractor_visibility",
        "goal": "Migrated subcontractors, workers, watchbooks, and released invoice checks remain correctly scoped in the subcontractor portal.",
        "commands": [
            "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.subcontractors.test_subcontractor_portal_context backend.tests.modules.subcontractors.test_subcontractor_portal_read_models",
            "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.finance.test_subcontractor_invoice_checks",
        ],
    },
    {
        "key": "planning_release_and_assignment_validation",
        "goal": "Migrated customers, employees, subcontractors, orders, and docs support planning release and staffing validation through normal planning services.",
        "commands": [
            "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.planning.test_customer_orders backend.tests.modules.planning.test_planning_records backend.tests.modules.planning.test_staffing_engine",
        ],
    },
    {
        "key": "finance_actual_to_invoice_bridge",
        "goal": "Migrated operational truth can still drive attendance, actuals, payroll, timesheets, invoices, and reports through finance.actual_record.",
        "commands": [
            "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.field_execution.test_attendance_flows backend.tests.modules.finance.test_actual_record_flows backend.tests.modules.finance.test_payroll_flows backend.tests.modules.finance.test_billing_flows",
        ],
    },
    {
        "key": "reporting_export_reproducibility",
        "goal": "Migrated data continues to power reproducible reporting and export flows.",
        "commands": [
            "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.reporting.test_reporting_flows backend.tests.modules.reporting.test_reporting_reproducibility",
        ],
    },
)

RESET_AND_REPLAY = (
    "1. Seed system and tenant go-live configuration: backend/scripts/seed_go_live_configuration.py",
    "2. Preflight migration package with backend.tests.modules.platform_services.test_migration_package coverage and docs/migration/template-package-v1.json.",
    "3. Run historical document pilot checks before portal/finance validation.",
    "4. Execute the scenario commands in order and store outputs in docs/uat/trial-migration-evidence-index.md.",
    "5. Record defects and rerun expectations in docs/uat/trial-migration-remediation-log.md.",
)


def main() -> int:
    print("Sprint 12 trial-migration validation suite")
    for scenario in VALIDATION_SCENARIOS:
        print(f"\n[{scenario['key']}]")
        print(f"goal: {scenario['goal']}")
        for command in scenario["commands"]:
            print(f"cmd: {command}")
    print("\nreset_and_replay:")
    for step in RESET_AND_REPLAY:
        print(step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
