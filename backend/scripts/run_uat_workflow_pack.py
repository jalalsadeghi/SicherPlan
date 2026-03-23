"""Print the Sprint 12 UAT workflow pack, account matrix, and evidence assets."""

from __future__ import annotations

UAT_WORKFLOWS = (
    {
        "key": "customer_order_to_invoice",
        "title": "Customer order to invoice",
        "docs": (
            "docs/uat/us-35-workflow-uat-pack.md#workflow-1--customer-order-to-invoice-coi",
            "docs/uat/us-35-uat-account-matrix.md",
            "docs/uat/us-35-defect-and-evidence-templates.md",
        ),
    },
    {
        "key": "applicant_to_payroll",
        "title": "Applicant to payroll-ready employee",
        "docs": (
            "docs/uat/us-35-workflow-uat-pack.md#workflow-2--applicant-to-payroll-ready-employee-ape",
            "docs/uat/us-35-uat-account-matrix.md",
            "docs/uat/us-35-defect-and-evidence-templates.md",
        ),
    },
    {
        "key": "subcontractor_collaboration",
        "title": "Subcontractor collaboration",
        "docs": (
            "docs/uat/us-35-workflow-uat-pack.md#workflow-3--subcontractor-collaboration-sc",
            "docs/uat/us-35-uat-account-matrix.md",
            "docs/uat/us-35-defect-and-evidence-templates.md",
        ),
    },
)


def main() -> int:
    print("Sprint 12 UAT workflow pack")
    for workflow in UAT_WORKFLOWS:
        print(f"\n[{workflow['key']}] {workflow['title']}")
        for doc in workflow["docs"]:
            print(f"doc: {doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
