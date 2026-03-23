from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class TestUs36Assets(unittest.TestCase):
    def test_cutover_dry_run_script_lists_freeze_and_rollback_path(self) -> None:
        root = Path(__file__).resolve().parents[4]
        result = subprocess.run(
            ["python3", "backend/scripts/run_production_cutover_dry_run.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout
        self.assertIn("Freeze configuration", output)
        self.assertIn("rollback", output.lower())
        self.assertIn("execution_note", output)

    def test_operational_handover_script_lists_support_assets(self) -> None:
        root = Path(__file__).resolve().parents[4]
        result = subprocess.run(
            ["python3", "backend/scripts/check_operational_handover_assets.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout
        self.assertIn("docs/support/index.md", output)
        self.assertIn("docs/retrospectives/sprint-12-release-retrospective.md", output)

    def test_required_us36_docs_exist(self) -> None:
        root = Path(__file__).resolve().parents[4]
        expected = (
            root / "docs/runbooks/production-cutover.md",
            root / "docs/runbooks/production-cutover-evidence.md",
            root / "docs/runbooks/production-smoke-checks.md",
            root / "docs/support/hypercare-runbook.md",
            root / "docs/support/operational-dashboard-catalog.md",
            root / "docs/support/operational-support-handover.md",
            root / "docs/retrospectives/sprint-12-release-retrospective.md",
            root / "docs/retrospectives/sprint-12-action-register.md",
        )
        for path in expected:
            self.assertTrue(path.exists(), path)
