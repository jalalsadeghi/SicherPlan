"""Print the authoritative Sprint 12 rollout-readiness asset set."""

from __future__ import annotations

ASSETS = (
    "docs/uat/us-35-workflow-uat-pack.md",
    "docs/uat/us-35-uat-account-matrix.md",
    "docs/uat/us-35-defect-and-evidence-templates.md",
    "docs/training/us-35-role-guides.md",
    "docs/runbooks/onboarding/us-35-onboarding-sessions.md",
    "docs/qa/us-35-localization-accessibility-review.md",
    "docs/qa/us-35-print-template-signoff.md",
    "docs/qa/us-35-terminology-glossary.md",
    "docs/runbooks/us-35-go-live-checklist.md",
    "docs/runbooks/us-35-cutover-rehearsal.md",
    "docs/acceptance/us-35-business-acceptance-signoff.md",
    "docs/acceptance/us-35-release-risk-register.md",
)


def main() -> int:
    print("Sprint 12 rollout-readiness assets")
    for asset in ASSETS:
        print(asset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
