export const FINANCE_ACTUAL_PERMISSION_MATRIX = {
  platform_admin: ["finance.actual.read", "finance.actual.write", "finance.approval.write", "finance.approval.signoff"],
  tenant_admin: ["finance.actual.read", "finance.actual.write", "finance.approval.write", "finance.approval.signoff"],
  dispatcher: ["finance.actual.read", "finance.actual.write", "finance.approval.write"],
  accounting: ["finance.actual.read", "finance.actual.write", "finance.approval.write", "finance.approval.signoff"],
  controller_qm: ["finance.actual.read"],
  employee_user: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasFinanceActualPermission(role, permissionKey) {
  return (FINANCE_ACTUAL_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function deriveFinanceActualActionState(role, selectedActual) {
  const canRead = hasFinanceActualPermission(role, "finance.actual.read");
  const canWrite = hasFinanceActualPermission(role, "finance.actual.write");
  const canApprove = hasFinanceActualPermission(role, "finance.approval.write");
  const canSignoff = hasFinanceActualPermission(role, "finance.approval.signoff");
  const stage = selectedActual?.approval_stage_code ?? "draft";
  return {
    canRead,
    canWrite,
    canApprove,
    canSignoff,
    canRefresh: canRead,
    canInspectDetail: canRead && !!selectedActual,
    canSubmitPreliminary: canApprove && !!selectedActual && stage === "draft",
    canConfirmOperational: canApprove && !!selectedActual && stage === "preliminary_submitted",
    canFinanceSignoff: canSignoff && !!selectedActual && stage === "operational_confirmed",
    canEditFinanceLines: canWrite && !!selectedActual,
  };
}

export function mapFinanceActualApiMessage(messageKey) {
  const map = {
    "errors.iam.auth.invalid_access_token": "authRequired",
    "errors.iam.authorization.permission_denied": "permissionDenied",
    "errors.iam.authorization.scope_denied": "permissionDenied",
    "errors.finance.actual.not_found": "notFound",
    "errors.finance.actual.scope_denied": "scopeDenied",
    "errors.finance.actual.self_scope_denied": "scopeDenied",
    "errors.finance.actual.approval.invalid_stage": "invalidStage",
    "errors.finance.actual.reconciliation.invalid_kind": "invalidReconciliation",
    "errors.finance.actual.reconciliation.replacement_not_found": "replacementNotFound",
    "errors.finance.actual.reconciliation.replacement_actor_required": "replacementActorRequired",
    "errors.finance.actual.reconciliation.customer_adjustment_required": "customerAdjustmentRequired",
    "errors.finance.actual.reconciliation.note_required": "noteRequired",
  };
  return map[messageKey] ?? "error";
}

export function approvalStageTone(stage) {
  switch (stage) {
    case "finance_signed_off":
      return "good";
    case "operational_confirmed":
      return "warn";
    case "preliminary_submitted":
      return "neutral";
    default:
      return "bad";
  }
}

export function summarizeActuals(rows) {
  return rows.reduce(
    (summary, row) => {
      summary.total += 1;
      if (row.approval_stage_code === "finance_signed_off") {
        summary.financeSignedOff += 1;
      } else if (row.approval_stage_code === "operational_confirmed") {
        summary.operationalConfirmed += 1;
      } else if (row.approval_stage_code === "preliminary_submitted") {
        summary.preliminarySubmitted += 1;
      } else {
        summary.draft += 1;
      }
      return summary;
    },
    { draft: 0, financeSignedOff: 0, operationalConfirmed: 0, preliminarySubmitted: 0, total: 0 },
  );
}
