from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class TestTrialMigrationValidation(unittest.TestCase):
    def test_validation_script_lists_required_cross_module_scenarios(self) -> None:
        root = Path(__file__).resolve().parents[4]
        result = subprocess.run(
            ["python3", "backend/scripts/run_trial_migration_validation.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout
        self.assertIn("portal_customer_visibility", output)
        self.assertIn("portal_subcontractor_visibility", output)
        self.assertIn("planning_release_and_assignment_validation", output)
        self.assertIn("finance_actual_to_invoice_bridge", output)
        self.assertIn("reporting_export_reproducibility", output)

    def test_uat_docs_exist_for_replay_evidence_and_remediation(self) -> None:
        root = Path(__file__).resolve().parents[4]
        expected = (
            root / "docs/uat/trial-migration-validation.md",
            root / "docs/uat/trial-migration-evidence-index.md",
            root / "docs/uat/trial-migration-remediation-log.md",
        )
        for path in expected:
            self.assertTrue(path.exists(), path)
