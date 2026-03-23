"""Shared hardening check inventory for Sprint 11."""

from __future__ import annotations


CHECKS = [
    {
        "name": "reporting_query_probe",
        "command": "PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/reporting_query_probe.py",
        "purpose": "Review tuned reporting SQL and active filter predicates.",
    },
    {
        "name": "reporting_tests",
        "command": "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.reporting.test_reporting_flows backend.tests.modules.reporting.test_reporting_reproducibility backend.tests.modules.reporting.test_reporting_hardening",
        "purpose": "Validate reporting correctness and hardening behavior.",
    },
    {
        "name": "security_drills",
        "command": "PYTHONPATH=backend .venv-backend-test/bin/python -m unittest backend.tests.modules.iam.test_auth_flows backend.tests.modules.platform_services.test_document_backbone backend.tests.modules.platform_services.test_hardening_drills",
        "purpose": "Validate refresh throttling, secure-document behavior, and hardening drill helpers.",
    },
    {
        "name": "restore_validation",
        "command": "PYTHONPATH=backend .venv-backend-test/bin/python backend/scripts/restore_validation.py --database-url \"$SP_DATABASE_URL\"",
        "purpose": "Validate restored database state and document linkage.",
    },
]
