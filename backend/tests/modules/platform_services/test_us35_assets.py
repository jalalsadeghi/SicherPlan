from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class TestUs35Assets(unittest.TestCase):
    def test_uat_pack_script_lists_anchor_workflows(self) -> None:
        root = Path(__file__).resolve().parents[4]
        result = subprocess.run(
            ["python3", "backend/scripts/run_uat_workflow_pack.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout
        self.assertIn("customer_order_to_invoice", output)
        self.assertIn("applicant_to_payroll", output)
        self.assertIn("subcontractor_collaboration", output)

    def test_rollout_readiness_script_lists_authoritative_assets(self) -> None:
        root = Path(__file__).resolve().parents[4]
        result = subprocess.run(
            ["python3", "backend/scripts/check_rollout_readiness_assets.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout
        self.assertIn("docs/uat/us-35-workflow-uat-pack.md", output)
        self.assertIn("docs/training/us-35-role-guides.md", output)
        self.assertIn("docs/acceptance/us-35-business-acceptance-signoff.md", output)

    def test_localization_readiness_check_passes(self) -> None:
        root = Path(__file__).resolve().parents[4]
        subprocess.run(
            ["python3", "backend/scripts/check_localization_readiness.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_required_docs_exist(self) -> None:
        root = Path(__file__).resolve().parents[4]
        expected = (
            root / "docs/uat/us-35-workflow-uat-pack.md",
            root / "docs/uat/us-35-uat-account-matrix.md",
            root / "docs/training/us-35-role-guides.md",
            root / "docs/runbooks/onboarding/us-35-onboarding-sessions.md",
            root / "docs/qa/us-35-localization-accessibility-review.md",
            root / "docs/runbooks/us-35-go-live-checklist.md",
            root / "docs/acceptance/us-35-business-acceptance-signoff.md",
        )
        for path in expected:
            self.assertTrue(path.exists(), path)
