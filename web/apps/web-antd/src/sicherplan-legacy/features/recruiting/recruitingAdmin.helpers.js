export const RECRUITING_PERMISSION_MATRIX = {
  platform_admin: ["recruiting.applicant.read", "recruiting.applicant.write", "platform.docs.read"],
  tenant_admin: ["recruiting.applicant.read", "recruiting.applicant.write", "platform.docs.read"],
  dispatcher: [],
  accounting: [],
  controller_qm: [],
  customer_user: [],
  subcontractor_user: [],
};

export function hasRecruitingPermission(role, permissionKey) {
  return (RECRUITING_PERMISSION_MATRIX[role] ?? []).includes(permissionKey);
}

export function canAccessRecruitingAdmin(role, hasSession) {
  return Boolean(hasSession && hasRecruitingPermission(role, "recruiting.applicant.read"));
}

export function deriveNextActionDescriptors(nextAllowedStatuses) {
  return (nextAllowedStatuses ?? []).map((status) => ({
    status,
    requiresDecisionReason: status === "accepted" || status === "rejected",
    requiresInterviewSchedule: status === "interview_scheduled",
    requiresHiringTargetDate: status === "ready_for_conversion",
  }));
}

export function requiresTransitionConfirmation(status) {
  return status === "accepted" || status === "rejected";
}

export function formatApplicantLabel(applicant) {
  if (!applicant) {
    return "";
  }
  return [applicant.first_name, applicant.last_name].filter(Boolean).join(" ").trim();
}

export function mapRecruitingApiMessage(messageKey) {
  const messageMap = {
    "errors.iam.auth.invalid_access_token": "recruitingAdmin.feedback.authRequired",
    "errors.iam.authorization.permission_denied": "recruitingAdmin.feedback.permissionDenied",
    "errors.iam.authorization.scope_denied": "recruitingAdmin.feedback.permissionDenied",
    "errors.recruiting.applicant.not_found": "recruitingAdmin.feedback.notFound",
    "errors.recruiting.applicant.invalid_status": "recruitingAdmin.feedback.invalidStatus",
    "errors.recruiting.applicant.transition_not_allowed": "recruitingAdmin.feedback.transitionNotAllowed",
    "errors.recruiting.applicant.interview_time_required": "recruitingAdmin.feedback.interviewTimeRequired",
    "errors.recruiting.applicant.decision_reason_required": "recruitingAdmin.feedback.decisionReasonRequired",
    "errors.recruiting.applicant.reopen_note_required": "recruitingAdmin.feedback.reopenNoteRequired",
    "errors.recruiting.applicant.hiring_target_required": "recruitingAdmin.feedback.hiringTargetRequired",
    "errors.recruiting.applicant.note_required": "recruitingAdmin.feedback.noteRequired",
    "errors.recruiting.applicant.converted_employee_missing": "recruitingAdmin.feedback.conversionMissing",
    "errors.docs.document.not_found": "recruitingAdmin.feedback.documentNotFound",
    "errors.docs.document_version.not_found": "recruitingAdmin.feedback.documentNotFound",
  };

  return messageMap[messageKey] ?? "recruitingAdmin.feedback.error";
}
