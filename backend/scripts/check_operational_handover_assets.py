"""Print the authoritative Sprint 12 support and handover asset set."""

from __future__ import annotations

ASSETS = (
    "docs/runbooks/production-cutover.md",
    "docs/runbooks/production-cutover-evidence.md",
    "docs/runbooks/production-smoke-checks.md",
    "docs/support/index.md",
    "docs/support/hypercare-runbook.md",
    "docs/support/stabilization-backlog.md",
    "docs/support/operational-dashboard-catalog.md",
    "docs/support/kpi-and-alert-mapping.md",
    "docs/support/operational-support-handover.md",
    "docs/retrospectives/sprint-12-release-retrospective.md",
    "docs/retrospectives/sprint-12-action-register.md",
)


def main() -> int:
    print("Sprint 12 operational handover assets")
    for asset in ASSETS:
        print(asset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
