export type AppLocale = "de" | "en";

export type MessageKey =
  | "app.title"
  | "locale.label"
  | "locale.de"
  | "locale.en"
  | "theme.toggle.light"
  | "theme.toggle.dark"
  | "theme.mode.light"
  | "theme.mode.dark"
  | "layout.admin.eyebrow"
  | "layout.admin.title"
  | "layout.portal.eyebrow"
  | "layout.portal.title"
  | "brand.adminSubtitle"
  | "brand.portalSubtitle"
  | "role.label"
  | "role.platform_admin"
  | "role.tenant_admin"
  | "role.dispatcher"
  | "role.accounting"
  | "role.controller_qm"
  | "role.customer_user"
  | "role.subcontractor_user"
  | "shell.eyebrow"
  | "shell.title"
  | "shell.lead"
  | "shell.cta.admin"
  | "shell.cta.portal"
  | "shell.stat.roles"
  | "shell.stat.modules"
  | "shell.stat.portals"
  | "module.eyebrow"
  | "module.note.navigation"
  | "module.note.future"
  | "module.note.compatibility"
  | "route.admin.dashboard.title"
  | "route.admin.dashboard.description"
  | "route.admin.core.title"
  | "route.admin.core.description"
  | "route.admin.platform_services.title"
  | "route.admin.platform_services.description"
  | "route.admin.customers.title"
  | "route.admin.customers.description"
  | "route.admin.recruiting.title"
  | "route.admin.recruiting.description"
  | "route.admin.employees.title"
  | "route.admin.employees.description"
  | "route.admin.subcontractors.title"
  | "route.admin.subcontractors.description"
  | "route.admin.planning.title"
  | "route.admin.planning.description"
  | "route.admin.field_execution.title"
  | "route.admin.field_execution.description"
  | "route.admin.finance.title"
  | "route.admin.finance.description"
  | "route.admin.reporting.title"
  | "route.admin.reporting.description"
  | "route.portal.customer.title"
  | "route.portal.customer.description"
  | "route.portal.subcontractor.title"
  | "route.portal.subcontractor.description"
  | "portalCustomer.eyebrow"
  | "portalCustomer.title"
  | "portalCustomer.lead"
  | "portalCustomer.login.tenantCode"
  | "portalCustomer.login.identifier"
  | "portalCustomer.login.password"
  | "portalCustomer.login.deviceLabel"
  | "portalCustomer.actions.login"
  | "portalCustomer.actions.refresh"
  | "portalCustomer.actions.logout"
  | "portalCustomer.loading.title"
  | "portalCustomer.loading.body"
  | "portalCustomer.empty.title"
  | "portalCustomer.empty.body"
  | "portalCustomer.unauthorized.title"
  | "portalCustomer.unauthorized.body"
  | "portalCustomer.deactivated.title"
  | "portalCustomer.deactivated.body"
  | "portalCustomer.summary.title"
  | "portalCustomer.summary.customerNumber"
  | "portalCustomer.summary.customerName"
  | "portalCustomer.summary.contact"
  | "portalCustomer.summary.email"
  | "portalCustomer.summary.function"
  | "portalCustomer.summary.tenant"
  | "portalCustomer.summary.scope"
  | "portalCustomer.readOnly.title"
  | "portalCustomer.readOnly.body"
  | "portalCustomer.history.eyebrow"
  | "portalCustomer.history.title"
  | "portalCustomer.history.lead"
  | "portalCustomer.history.empty"
  | "portalCustomer.meta.releasedOnly"
  | "portalCustomer.meta.customerScoped"
  | "portalCustomer.meta.personalNamesRestricted"
  | "portalCustomer.meta.sourceModule"
  | "portalCustomer.meta.docsBacked"
  | "portalCustomer.states.loading"
  | "portalCustomer.states.pending"
  | "portalCustomer.states.empty"
  | "portalCustomer.states.ready"
  | "portalCustomer.datasets.orders.eyebrow"
  | "portalCustomer.datasets.orders.title"
  | "portalCustomer.datasets.orders.lead"
  | "portalCustomer.datasets.orders.pending"
  | "portalCustomer.datasets.schedules.eyebrow"
  | "portalCustomer.datasets.schedules.title"
  | "portalCustomer.datasets.schedules.lead"
  | "portalCustomer.datasets.schedules.pending"
  | "portalCustomer.datasets.watchbooks.eyebrow"
  | "portalCustomer.datasets.watchbooks.title"
  | "portalCustomer.datasets.watchbooks.lead"
  | "portalCustomer.datasets.watchbooks.pending"
  | "portalCustomer.datasets.timesheets.eyebrow"
  | "portalCustomer.datasets.timesheets.title"
  | "portalCustomer.datasets.timesheets.lead"
  | "portalCustomer.datasets.timesheets.pending"
  | "portalCustomer.datasets.reports.eyebrow"
  | "portalCustomer.datasets.reports.title"
  | "portalCustomer.datasets.reports.lead"
  | "portalCustomer.datasets.reports.pending"
  | "portalCustomer.feedback.authRequired"
  | "portalCustomer.feedback.invalidCredentials"
  | "portalCustomer.feedback.permissionDenied"
  | "portalCustomer.feedback.scopeNotResolved"
  | "portalCustomer.feedback.contactNotLinked"
  | "portalCustomer.feedback.contactInactive"
  | "portalCustomer.feedback.customerInactive"
  | "portalCustomer.feedback.sessionReady"
  | "portalCustomer.feedback.loggedOut"
  | "portalCustomer.feedback.error"
  | "recruitingApplicant.eyebrow"
  | "recruitingApplicant.title"
  | "recruitingApplicant.lead"
  | "recruitingApplicant.embed.embedded"
  | "recruitingApplicant.embed.standalone"
  | "recruitingApplicant.loading.title"
  | "recruitingApplicant.loading.body"
  | "recruitingApplicant.error.title"
  | "recruitingApplicant.success.eyebrow"
  | "recruitingApplicant.success.title"
  | "recruitingApplicant.success.body"
  | "recruitingApplicant.fields.selectPlaceholder"
  | "recruitingApplicant.fields.attachments"
  | "recruitingApplicant.fields.attachmentsHelp"
  | "recruitingApplicant.fields.consent"
  | "recruitingApplicant.fields.policyLink"
  | "recruitingApplicant.fields.policyVersion"
  | "recruitingApplicant.actions.submit"
  | "recruitingApplicant.actions.submitting"
  | "recruitingApplicant.actions.clearFeedback"
  | "recruitingApplicant.feedback.submitted"
  | "recruitingApplicant.feedback.tenantNotFound"
  | "recruitingApplicant.feedback.formDisabled"
  | "recruitingApplicant.feedback.originDenied"
  | "recruitingApplicant.feedback.rateLimited"
  | "recruitingApplicant.feedback.consentRequired"
  | "recruitingApplicant.feedback.policyMismatch"
  | "recruitingApplicant.feedback.fieldRequired"
  | "recruitingApplicant.feedback.invalidEmail"
  | "recruitingApplicant.feedback.invalidFieldOption"
  | "recruitingApplicant.feedback.tooManyAttachments"
  | "recruitingApplicant.feedback.attachmentTypeNotAllowed"
  | "recruitingApplicant.feedback.attachmentTooLarge"
  | "recruitingApplicant.feedback.duplicateSubmission"
  | "recruitingApplicant.feedback.error"
  | "recruitingAdmin.eyebrow"
  | "recruitingAdmin.title"
  | "recruitingAdmin.lead"
  | "recruitingAdmin.permission.read"
  | "recruitingAdmin.permission.write"
  | "recruitingAdmin.permission.docs"
  | "recruitingAdmin.permission.missingTitle"
  | "recruitingAdmin.permission.missingBody"
  | "recruitingAdmin.auth.missingTitle"
  | "recruitingAdmin.auth.missingBody"
  | "recruitingAdmin.scope.label"
  | "recruitingAdmin.scope.placeholder"
  | "recruitingAdmin.scope.platformHelp"
  | "recruitingAdmin.scope.sessionHelp"
  | "recruitingAdmin.scope.missingTitle"
  | "recruitingAdmin.scope.missingBody"
  | "recruitingAdmin.list.eyebrow"
  | "recruitingAdmin.list.title"
  | "recruitingAdmin.list.empty"
  | "recruitingAdmin.detail.eyebrow"
  | "recruitingAdmin.detail.emptyTitle"
  | "recruitingAdmin.detail.emptyEyebrow"
  | "recruitingAdmin.detail.emptyBody"
  | "recruitingAdmin.detail.submissionEyebrow"
  | "recruitingAdmin.detail.submissionTitle"
  | "recruitingAdmin.summary.applicationNo"
  | "recruitingAdmin.summary.desiredRole"
  | "recruitingAdmin.summary.availability"
  | "recruitingAdmin.summary.source"
  | "recruitingAdmin.summary.employeeFile"
  | "recruitingAdmin.summary.none"
  | "recruitingAdmin.consent.eyebrow"
  | "recruitingAdmin.consent.title"
  | "recruitingAdmin.consent.granted"
  | "recruitingAdmin.consent.timestamp"
  | "recruitingAdmin.consent.policyRef"
  | "recruitingAdmin.consent.policyVersion"
  | "recruitingAdmin.consent.origin"
  | "recruitingAdmin.consent.ip"
  | "recruitingAdmin.attachments.eyebrow"
  | "recruitingAdmin.attachments.title"
  | "recruitingAdmin.attachments.empty"
  | "recruitingAdmin.notes.eyebrow"
  | "recruitingAdmin.notes.title"
  | "recruitingAdmin.timeline.eyebrow"
  | "recruitingAdmin.timeline.title"
  | "recruitingAdmin.timeline.empty"
  | "recruitingAdmin.actions.rememberScope"
  | "recruitingAdmin.actions.refresh"
  | "recruitingAdmin.actions.search"
  | "recruitingAdmin.actions.clearFeedback"
  | "recruitingAdmin.actions.previewAttachment"
  | "recruitingAdmin.actions.downloadAttachment"
  | "recruitingAdmin.actions.transitionEyebrow"
  | "recruitingAdmin.actions.transitionTitle"
  | "recruitingAdmin.actions.applyTransition"
  | "recruitingAdmin.actions.addNote"
  | "recruitingAdmin.fields.fullName"
  | "recruitingAdmin.fields.email"
  | "recruitingAdmin.fields.phone"
  | "recruitingAdmin.fields.locale"
  | "recruitingAdmin.fields.message"
  | "recruitingAdmin.fields.activityType"
  | "recruitingAdmin.fields.nextStatus"
  | "recruitingAdmin.fields.note"
  | "recruitingAdmin.fields.decisionReason"
  | "recruitingAdmin.fields.interviewScheduledAt"
  | "recruitingAdmin.fields.hiringTargetDate"
  | "recruitingAdmin.filters.search"
  | "recruitingAdmin.filters.searchPlaceholder"
  | "recruitingAdmin.filters.status"
  | "recruitingAdmin.filters.sourceChannel"
  | "recruitingAdmin.filters.allStatuses"
  | "recruitingAdmin.filters.allSources"
  | "recruitingAdmin.status.submitted"
  | "recruitingAdmin.status.in_review"
  | "recruitingAdmin.status.interview_scheduled"
  | "recruitingAdmin.status.accepted"
  | "recruitingAdmin.status.rejected"
  | "recruitingAdmin.status.ready_for_conversion"
  | "recruitingAdmin.source.public_form"
  | "recruitingAdmin.activity.recruiterNote"
  | "recruitingAdmin.activity.interviewNote"
  | "recruitingAdmin.event.status_transition"
  | "recruitingAdmin.event.interview_scheduled"
  | "recruitingAdmin.event.decision"
  | "recruitingAdmin.event.reopened"
  | "recruitingAdmin.event.ready_for_conversion"
  | "recruitingAdmin.event.converted"
  | "recruitingAdmin.event.recruiter_note"
  | "recruitingAdmin.event.interview_note"
  | "recruitingAdmin.feedback.titleSuccess"
  | "recruitingAdmin.feedback.titleError"
  | "recruitingAdmin.feedback.authRequired"
  | "recruitingAdmin.feedback.permissionDenied"
  | "recruitingAdmin.feedback.notFound"
  | "recruitingAdmin.feedback.invalidStatus"
  | "recruitingAdmin.feedback.transitionNotAllowed"
  | "recruitingAdmin.feedback.interviewTimeRequired"
  | "recruitingAdmin.feedback.decisionReasonRequired"
  | "recruitingAdmin.feedback.reopenNoteRequired"
  | "recruitingAdmin.feedback.hiringTargetRequired"
  | "recruitingAdmin.feedback.noteRequired"
  | "recruitingAdmin.feedback.conversionMissing"
  | "recruitingAdmin.feedback.documentNotFound"
  | "recruitingAdmin.feedback.transitionSaved"
  | "recruitingAdmin.feedback.noteSaved"
  | "recruitingAdmin.feedback.error"
  | "recruitingAdmin.confirm.accepted"
  | "recruitingAdmin.confirm.rejected"
  | "recruitingAdmin.common.yes"
  | "recruitingAdmin.common.no"
  | "employeeAdmin.eyebrow"
  | "employeeAdmin.title"
  | "employeeAdmin.lead"
  | "employeeAdmin.permission.read"
  | "employeeAdmin.permission.write"
  | "employeeAdmin.permission.privateRead"
  | "employeeAdmin.permission.missingTitle"
  | "employeeAdmin.permission.missingBody"
  | "employeeAdmin.scope.label"
  | "employeeAdmin.scope.placeholder"
  | "employeeAdmin.scope.help"
  | "employeeAdmin.scope.missingTitle"
  | "employeeAdmin.scope.missingBody"
  | "employeeAdmin.list.eyebrow"
  | "employeeAdmin.list.title"
  | "employeeAdmin.list.empty"
  | "employeeAdmin.detail.eyebrow"
  | "employeeAdmin.detail.newTitle"
  | "employeeAdmin.detail.emptyTitle"
  | "employeeAdmin.detail.emptyEyebrow"
  | "employeeAdmin.detail.emptyBody"
  | "employeeAdmin.filters.search"
  | "employeeAdmin.filters.searchPlaceholder"
  | "employeeAdmin.filters.status"
  | "employeeAdmin.filters.allStatuses"
  | "employeeAdmin.filters.includeArchived"
  | "employeeAdmin.status.active"
  | "employeeAdmin.status.inactive"
  | "employeeAdmin.status.archived"
  | "employeeAdmin.fields.personnelNo"
  | "employeeAdmin.fields.firstName"
  | "employeeAdmin.fields.lastName"
  | "employeeAdmin.fields.preferredName"
  | "employeeAdmin.fields.workEmail"
  | "employeeAdmin.fields.workPhone"
  | "employeeAdmin.fields.mobilePhone"
  | "employeeAdmin.fields.defaultBranchId"
  | "employeeAdmin.fields.defaultMandateId"
  | "employeeAdmin.fields.hireDate"
  | "employeeAdmin.fields.terminationDate"
  | "employeeAdmin.fields.userId"
  | "employeeAdmin.fields.notes"
  | "employeeAdmin.fields.noteType"
  | "employeeAdmin.fields.noteTitle"
  | "employeeAdmin.fields.reminderAt"
  | "employeeAdmin.fields.completedAt"
  | "employeeAdmin.fields.noteBody"
  | "employeeAdmin.fields.groupCode"
  | "employeeAdmin.fields.groupName"
  | "employeeAdmin.fields.groupDescription"
  | "employeeAdmin.fields.assignGroup"
  | "employeeAdmin.fields.validFrom"
  | "employeeAdmin.fields.validUntil"
  | "employeeAdmin.fields.membershipNotes"
  | "employeeAdmin.summary.branch"
  | "employeeAdmin.summary.mandate"
  | "employeeAdmin.summary.currentAddress"
  | "employeeAdmin.summary.groups"
  | "employeeAdmin.summary.none"
  | "employeeAdmin.photo.eyebrow"
  | "employeeAdmin.photo.title"
  | "employeeAdmin.photo.alt"
  | "employeeAdmin.photo.empty"
  | "employeeAdmin.photo.help"
  | "employeeAdmin.notes.eyebrow"
  | "employeeAdmin.notes.title"
  | "employeeAdmin.notes.empty"
  | "employeeAdmin.groups.eyebrow"
  | "employeeAdmin.groups.title"
  | "employeeAdmin.groups.empty"
  | "employeeAdmin.groups.selectPlaceholder"
  | "employeeAdmin.addresses.eyebrow"
  | "employeeAdmin.addresses.title"
  | "employeeAdmin.addresses.empty"
  | "employeeAdmin.documents.eyebrow"
  | "employeeAdmin.documents.title"
  | "employeeAdmin.documents.empty"
  | "employeeAdmin.noteType.operational_note"
  | "employeeAdmin.noteType.positive_activity"
  | "employeeAdmin.noteType.reminder"
  | "employeeAdmin.actions.rememberScope"
  | "employeeAdmin.actions.refresh"
  | "employeeAdmin.actions.search"
  | "employeeAdmin.actions.clearFeedback"
  | "employeeAdmin.actions.newEmployee"
  | "employeeAdmin.actions.createEmployee"
  | "employeeAdmin.actions.saveEmployee"
  | "employeeAdmin.actions.reset"
  | "employeeAdmin.actions.uploadPhoto"
  | "employeeAdmin.actions.downloadPhoto"
  | "employeeAdmin.actions.createNote"
  | "employeeAdmin.actions.saveNote"
  | "employeeAdmin.actions.resetNote"
  | "employeeAdmin.actions.createGroup"
  | "employeeAdmin.actions.saveGroup"
  | "employeeAdmin.actions.resetGroup"
  | "employeeAdmin.actions.assignGroup"
  | "employeeAdmin.actions.saveMembership"
  | "employeeAdmin.actions.resetMembership"
  | "employeeAdmin.actions.exportEmployees"
  | "employeeAdmin.actions.loadImportFile"
  | "employeeAdmin.actions.resetImportTemplate"
  | "employeeAdmin.actions.importDryRun"
  | "employeeAdmin.actions.importExecute"
  | "employeeAdmin.actions.createAccessUser"
  | "employeeAdmin.actions.attachAccessUser"
  | "employeeAdmin.actions.detachAccessUser"
  | "employeeAdmin.actions.reconcileAccessUser"
  | "employeeAdmin.import.eyebrow"
  | "employeeAdmin.import.title"
  | "employeeAdmin.import.csvLabel"
  | "employeeAdmin.import.continueOnError"
  | "employeeAdmin.import.dryRunSummary"
  | "employeeAdmin.import.executeSummary"
  | "employeeAdmin.import.exportSummary"
  | "employeeAdmin.access.eyebrow"
  | "employeeAdmin.access.title"
  | "employeeAdmin.access.user"
  | "employeeAdmin.access.email"
  | "employeeAdmin.access.enabled"
  | "employeeAdmin.access.enabledYes"
  | "employeeAdmin.access.enabledNo"
  | "employeeAdmin.access.createUsername"
  | "employeeAdmin.access.createEmail"
  | "employeeAdmin.access.createPassword"
  | "employeeAdmin.access.attachUserId"
  | "employeeAdmin.access.attachUsername"
  | "employeeAdmin.access.attachEmail"
  | "employeeAdmin.feedback.titleError"
  | "employeeAdmin.feedback.titleSuccess"
  | "employeeAdmin.feedback.authRequired"
  | "employeeAdmin.feedback.permissionDenied"
  | "employeeAdmin.feedback.notFound"
  | "employeeAdmin.feedback.duplicatePersonnelNo"
  | "employeeAdmin.feedback.duplicateGroupCode"
  | "employeeAdmin.feedback.staleVersion"
  | "employeeAdmin.feedback.addressOverlap"
  | "employeeAdmin.feedback.reminderDateRequired"
  | "employeeAdmin.feedback.invalidNoteType"
  | "employeeAdmin.feedback.photoUploadFailed"
  | "employeeAdmin.feedback.invalidImportCsv"
  | "employeeAdmin.feedback.invalidImportHeaders"
  | "employeeAdmin.feedback.accessUsernameTaken"
  | "employeeAdmin.feedback.accessEmailTaken"
  | "employeeAdmin.feedback.accessAmbiguousMatch"
  | "employeeAdmin.feedback.accessRoleMissing"
  | "employeeAdmin.feedback.employeeSaved"
  | "employeeAdmin.feedback.noteSaved"
  | "employeeAdmin.feedback.groupSaved"
  | "employeeAdmin.feedback.membershipSaved"
  | "employeeAdmin.feedback.photoSaved"
  | "employeeAdmin.feedback.importDryRunReady"
  | "employeeAdmin.feedback.importExecuted"
  | "employeeAdmin.feedback.exportReady"
  | "employeeAdmin.feedback.accessLinked"
  | "employeeAdmin.feedback.accessDetached"
  | "employeeAdmin.feedback.accessReconciled"
  | "employeeAdmin.feedback.error"
  | "api.errors.platform.internal"
  | "coreAdmin.eyebrow"
  | "coreAdmin.breadcrumb"
  | "coreAdmin.title"
  | "coreAdmin.lead"
  | "coreAdmin.permission.ready"
  | "coreAdmin.permission.label"
  | "coreAdmin.scope.label"
  | "coreAdmin.scope.placeholder"
  | "coreAdmin.scope.help"
  | "coreAdmin.scope.platformHint"
  | "coreAdmin.scope.emptyTitle"
  | "coreAdmin.scope.emptyBody"
  | "coreAdmin.scope.remembered"
  | "coreAdmin.scope.none"
  | "coreAdmin.actions.refresh"
  | "coreAdmin.actions.loadScopedTenant"
  | "coreAdmin.actions.clearFeedback"
  | "coreAdmin.actions.createTenant"
  | "coreAdmin.actions.saveTenant"
  | "coreAdmin.actions.activate"
  | "coreAdmin.actions.deactivate"
  | "coreAdmin.actions.archive"
  | "coreAdmin.actions.reactivate"
  | "coreAdmin.actions.edit"
  | "coreAdmin.actions.cancel"
  | "coreAdmin.actions.createBranch"
  | "coreAdmin.actions.saveBranch"
  | "coreAdmin.actions.createMandate"
  | "coreAdmin.actions.saveMandate"
  | "coreAdmin.actions.createSetting"
  | "coreAdmin.actions.saveSetting"
  | "coreAdmin.tenants.eyebrow"
  | "coreAdmin.tenants.title"
  | "coreAdmin.tenants.filterPlaceholder"
  | "coreAdmin.tenants.empty"
  | "coreAdmin.tenants.scopeOnly"
  | "coreAdmin.onboarding.eyebrow"
  | "coreAdmin.onboarding.title"
  | "coreAdmin.detail.eyebrow"
  | "coreAdmin.detail.emptyTitle"
  | "coreAdmin.detail.emptyState"
  | "coreAdmin.lifecycle.title"
  | "coreAdmin.lifecycle.archivedHint"
  | "coreAdmin.branches.eyebrow"
  | "coreAdmin.branches.title"
  | "coreAdmin.branches.empty"
  | "coreAdmin.mandates.eyebrow"
  | "coreAdmin.mandates.title"
  | "coreAdmin.mandates.empty"
  | "coreAdmin.settings.eyebrow"
  | "coreAdmin.settings.title"
  | "coreAdmin.settings.empty"
  | "coreAdmin.settings.version"
  | "coreAdmin.fields.tenantCode"
  | "coreAdmin.fields.tenantName"
  | "coreAdmin.fields.legalName"
  | "coreAdmin.fields.defaultLocale"
  | "coreAdmin.fields.defaultCurrency"
  | "coreAdmin.fields.timezone"
  | "coreAdmin.fields.branch"
  | "coreAdmin.fields.branchPlaceholder"
  | "coreAdmin.fields.branchCode"
  | "coreAdmin.fields.branchName"
  | "coreAdmin.fields.branchEmail"
  | "coreAdmin.fields.branchPhone"
  | "coreAdmin.fields.mandateCode"
  | "coreAdmin.fields.mandateName"
  | "coreAdmin.fields.externalRef"
  | "coreAdmin.fields.notes"
  | "coreAdmin.fields.settingKey"
  | "coreAdmin.fields.settingValue"
  | "coreAdmin.fields.settingValueJson"
  | "coreAdmin.status.active"
  | "coreAdmin.status.inactive"
  | "coreAdmin.status.archived"
  | "coreAdmin.feedback.success"
  | "coreAdmin.feedback.error"
  | "coreAdmin.feedback.info"
  | "coreAdmin.feedback.unexpected"
  | "coreAdmin.feedback.invalidJson"
  | "coreAdmin.feedback.tenantCreated"
  | "coreAdmin.feedback.tenantSaved"
  | "coreAdmin.feedback.tenantStatusSaved"
  | "coreAdmin.feedback.branchSaved"
  | "coreAdmin.feedback.branchStatusSaved"
  | "coreAdmin.feedback.mandateSaved"
  | "coreAdmin.feedback.mandateStatusSaved"
  | "coreAdmin.feedback.settingSaved"
  | "coreAdmin.feedback.settingStatusSaved"
  | "coreAdmin.feedback.scopeRemembered"
  | "coreAdmin.api.errors.authorization.forbidden"
  | "coreAdmin.api.errors.tenant.not_found"
  | "coreAdmin.api.errors.branch.not_found"
  | "coreAdmin.api.errors.mandate.not_found"
  | "coreAdmin.api.errors.setting.not_found"
  | "coreAdmin.api.errors.tenant.duplicate_code"
  | "coreAdmin.api.errors.branch.duplicate_code"
  | "coreAdmin.api.errors.mandate.duplicate_code"
  | "coreAdmin.api.errors.setting.duplicate_key"
  | "coreAdmin.api.errors.setting.stale_version"
  | "coreAdmin.api.errors.mandate.invalid_branch_scope"
  | "coreAdmin.api.errors.lifecycle.archived_record"
  | "coreAdmin.api.errors.conflict.integrity"
  | "noticeAdmin.eyebrow"
  | "noticeAdmin.title"
  | "noticeAdmin.lead"
  | "noticeAdmin.scope.label"
  | "noticeAdmin.scope.placeholder"
  | "noticeAdmin.scope.action"
  | "noticeAdmin.scope.missingTitle"
  | "noticeAdmin.scope.missingBody"
  | "noticeAdmin.form.eyebrow"
  | "noticeAdmin.form.title"
  | "noticeAdmin.list.eyebrow"
  | "noticeAdmin.list.title"
  | "noticeAdmin.list.empty"
  | "noticeAdmin.feed.eyebrow"
  | "noticeAdmin.feed.title"
  | "noticeAdmin.feed.empty"
  | "noticeAdmin.feed.acknowledged"
  | "noticeAdmin.fields.title"
  | "noticeAdmin.fields.summary"
  | "noticeAdmin.fields.body"
  | "noticeAdmin.fields.audienceRole"
  | "noticeAdmin.fields.mandatory"
  | "noticeAdmin.actions.create"
  | "noticeAdmin.actions.publish"
  | "noticeAdmin.actions.refresh"
  | "noticeAdmin.actions.acknowledge"
  | "noticeAdmin.feedback.created"
  | "noticeAdmin.feedback.published"
  | "noticeAdmin.feedback.acknowledged"
  | "noticeAdmin.feedback.error"
  | "customerAdmin.eyebrow"
  | "customerAdmin.title"
  | "customerAdmin.lead"
  | "customerAdmin.permission.read"
  | "customerAdmin.permission.write"
  | "customerAdmin.permission.missingTitle"
  | "customerAdmin.permission.missingBody"
  | "customerAdmin.scope.label"
  | "customerAdmin.scope.placeholder"
  | "customerAdmin.scope.missingTitle"
  | "customerAdmin.scope.missingBody"
  | "customerAdmin.token.label"
  | "customerAdmin.token.placeholder"
  | "customerAdmin.token.help"
  | "customerAdmin.list.eyebrow"
  | "customerAdmin.list.title"
  | "customerAdmin.list.empty"
  | "customerAdmin.detail.eyebrow"
  | "customerAdmin.detail.emptyTitle"
  | "customerAdmin.detail.emptyBody"
  | "customerAdmin.detail.newTitle"
  | "customerAdmin.form.generalEyebrow"
  | "customerAdmin.form.generalTitle"
  | "customerAdmin.filters.search"
  | "customerAdmin.filters.searchPlaceholder"
  | "customerAdmin.filters.status"
  | "customerAdmin.filters.allStatuses"
  | "customerAdmin.filters.includeArchived"
  | "customerAdmin.lifecycle.title"
  | "customerAdmin.lifecycle.help"
  | "customerAdmin.summary.primaryContact"
  | "customerAdmin.summary.defaultBranch"
  | "customerAdmin.summary.defaultMandate"
  | "customerAdmin.summary.classification"
  | "customerAdmin.summary.none"
  | "customerAdmin.contacts.eyebrow"
  | "customerAdmin.contacts.title"
  | "customerAdmin.contacts.empty"
  | "customerAdmin.contacts.primaryBadge"
  | "customerAdmin.contacts.standardBadge"
  | "customerAdmin.history.eyebrow"
  | "customerAdmin.history.title"
  | "customerAdmin.history.empty"
  | "customerAdmin.loginHistory.eyebrow"
  | "customerAdmin.loginHistory.title"
  | "customerAdmin.loginHistory.empty"
  | "customerAdmin.privacy.eyebrow"
  | "customerAdmin.privacy.title"
  | "customerAdmin.privacy.help"
  | "customerAdmin.privacy.lastReleasedAt"
  | "customerAdmin.privacy.lastReleasedBy"
  | "customerAdmin.employeeBlocks.eyebrow"
  | "customerAdmin.employeeBlocks.title"
  | "customerAdmin.employeeBlocks.empty"
  | "customerAdmin.employeeBlocks.capability.pendingEmployees"
  | "customerAdmin.addresses.eyebrow"
  | "customerAdmin.addresses.title"
  | "customerAdmin.addresses.empty"
  | "customerAdmin.addresses.defaultBadge"
  | "customerAdmin.addresses.linkBadge"
  | "customerAdmin.addressType.registered"
  | "customerAdmin.addressType.billing"
  | "customerAdmin.addressType.mailing"
  | "customerAdmin.addressType.service"
  | "customerAdmin.fields.customerNumber"
  | "customerAdmin.fields.name"
  | "customerAdmin.fields.legalName"
  | "customerAdmin.fields.externalRef"
  | "customerAdmin.fields.legalFormLookupId"
  | "customerAdmin.fields.classificationLookupId"
  | "customerAdmin.fields.rankingLookupId"
  | "customerAdmin.fields.customerStatusLookupId"
  | "customerAdmin.fields.defaultBranchId"
  | "customerAdmin.fields.defaultMandateId"
  | "customerAdmin.fields.notes"
  | "customerAdmin.fields.fullName"
  | "customerAdmin.fields.contactTitle"
  | "customerAdmin.fields.functionLabel"
  | "customerAdmin.fields.email"
  | "customerAdmin.fields.phone"
  | "customerAdmin.fields.mobile"
  | "customerAdmin.fields.userId"
  | "customerAdmin.fields.isPrimaryContact"
  | "customerAdmin.fields.isBillingContact"
  | "customerAdmin.fields.addressId"
  | "customerAdmin.fields.addressType"
  | "customerAdmin.fields.historyEntry"
  | "customerAdmin.fields.documentId"
  | "customerAdmin.fields.personNamesReleased"
  | "customerAdmin.fields.employeeId"
  | "customerAdmin.fields.reason"
  | "customerAdmin.fields.label"
  | "customerAdmin.fields.isDefault"
  | "customerAdmin.actions.rememberScope"
  | "customerAdmin.actions.refresh"
  | "customerAdmin.actions.search"
  | "customerAdmin.actions.exportCustomers"
  | "customerAdmin.actions.newCustomer"
  | "customerAdmin.actions.createCustomer"
  | "customerAdmin.actions.saveCustomer"
  | "customerAdmin.actions.cancel"
  | "customerAdmin.actions.clearFeedback"
  | "customerAdmin.actions.deactivate"
  | "customerAdmin.actions.reactivate"
  | "customerAdmin.actions.archive"
  | "customerAdmin.actions.edit"
  | "customerAdmin.actions.addContact"
  | "customerAdmin.actions.exportVCard"
  | "customerAdmin.actions.createContact"
  | "customerAdmin.actions.saveContact"
  | "customerAdmin.actions.addAddress"
  | "customerAdmin.actions.createAddress"
  | "customerAdmin.actions.saveAddress"
  | "customerAdmin.actions.refreshHistory"
  | "customerAdmin.actions.refreshPortalPrivacy"
  | "customerAdmin.actions.linkHistoryAttachment"
  | "customerAdmin.actions.refreshLoginHistory"
  | "customerAdmin.actions.refreshEmployeeBlocks"
  | "customerAdmin.actions.createEmployeeBlock"
  | "customerAdmin.actions.saveEmployeeBlock"
  | "customerAdmin.actions.savePortalPrivacy"
  | "customerAdmin.status.active"
  | "customerAdmin.status.inactive"
  | "customerAdmin.status.archived"
  | "customerAdmin.confirm.archive"
  | "customerAdmin.confirm.deactivate"
  | "customerAdmin.confirm.reactivate"
  | "customerAdmin.confirm.contactArchive"
  | "customerAdmin.confirm.addressArchive"
  | "customerAdmin.feedback.created"
  | "customerAdmin.feedback.saved"
  | "customerAdmin.feedback.archived"
  | "customerAdmin.feedback.deactivated"
  | "customerAdmin.feedback.reactivated"
  | "customerAdmin.feedback.contactSaved"
  | "customerAdmin.feedback.addressSaved"
  | "customerAdmin.feedback.exportReady"
  | "customerAdmin.feedback.vcardReady"
  | "customerAdmin.feedback.documentId"
  | "customerAdmin.feedback.scopeSaved"
  | "customerAdmin.feedback.tokenSaved"
  | "customerAdmin.feedback.historyAttachmentLinked"
  | "customerAdmin.feedback.documentLinked"
  | "customerAdmin.feedback.employeeBlockSaved"
  | "customerAdmin.feedback.employeeBlockSavedBody"
  | "customerAdmin.feedback.portalPrivacySaved"
  | "customerAdmin.feedback.validation"
  | "customerAdmin.feedback.customerRequired"
  | "customerAdmin.feedback.contactRequired"
  | "customerAdmin.feedback.addressRequired"
  | "customerAdmin.feedback.error"
  | "customerAdmin.feedback.authRequired"
  | "customerAdmin.feedback.permissionDenied"
  | "customerAdmin.feedback.notFound"
  | "customerAdmin.feedback.duplicateNumber"
  | "customerAdmin.feedback.staleVersion"
  | "customerAdmin.feedback.duplicateEmail"
  | "customerAdmin.feedback.primaryConflict"
  | "customerAdmin.feedback.defaultAddressConflict"
  | "customerAdmin.feedback.invalidPortalUser"
  | "customerAdmin.permission.commercialRead"
  | "customerAdmin.permission.commercialWrite"
  | "customerAdmin.commercial.eyebrow"
  | "customerAdmin.commercial.title"
  | "customerAdmin.commercial.lead"
  | "customerAdmin.commercial.summary.billingProfile"
  | "customerAdmin.commercial.summary.invoiceParties"
  | "customerAdmin.commercial.summary.rateCards"
  | "customerAdmin.commercial.summary.selectedRateCard"
  | "customerAdmin.commercial.summary.missing"
  | "customerAdmin.commercial.billingEyebrow"
  | "customerAdmin.commercial.billingTitle"
  | "customerAdmin.commercial.invoiceEyebrow"
  | "customerAdmin.commercial.invoiceTitle"
  | "customerAdmin.commercial.invoiceEmpty"
  | "customerAdmin.commercial.defaultInvoiceParty"
  | "customerAdmin.commercial.additionalInvoiceParty"
  | "customerAdmin.commercial.rateCardsEyebrow"
  | "customerAdmin.commercial.rateCardsTitle"
  | "customerAdmin.commercial.rateCardsEmpty"
  | "customerAdmin.commercial.rateLinesEyebrow"
  | "customerAdmin.commercial.rateLinesTitle"
  | "customerAdmin.commercial.rateLinesEmpty"
  | "customerAdmin.commercial.surchargesEyebrow"
  | "customerAdmin.commercial.surchargesTitle"
  | "customerAdmin.commercial.surchargesEmpty"
  | "customerAdmin.fields.invoiceEmail"
  | "customerAdmin.fields.paymentTermsDays"
  | "customerAdmin.fields.paymentTermsNote"
  | "customerAdmin.fields.taxNumber"
  | "customerAdmin.fields.vatId"
  | "customerAdmin.fields.contractReference"
  | "customerAdmin.fields.debtorNumber"
  | "customerAdmin.fields.bankAccountHolder"
  | "customerAdmin.fields.bankIban"
  | "customerAdmin.fields.bankBic"
  | "customerAdmin.fields.bankName"
  | "customerAdmin.fields.billingNote"
  | "customerAdmin.fields.eInvoiceEnabled"
  | "customerAdmin.fields.leitwegId"
  | "customerAdmin.fields.invoiceLayoutCode"
  | "customerAdmin.fields.shippingMethodCode"
  | "customerAdmin.fields.dunningPolicyCode"
  | "customerAdmin.fields.taxExempt"
  | "customerAdmin.fields.taxExemptionReason"
  | "customerAdmin.fields.companyName"
  | "customerAdmin.fields.contactName"
  | "customerAdmin.fields.invoiceLayoutLookupId"
  | "customerAdmin.fields.note"
  | "customerAdmin.fields.isDefaultInvoiceParty"
  | "customerAdmin.fields.rateKind"
  | "customerAdmin.fields.currencyCode"
  | "customerAdmin.fields.effectiveFrom"
  | "customerAdmin.fields.effectiveTo"
  | "customerAdmin.fields.lineKind"
  | "customerAdmin.fields.billingUnit"
  | "customerAdmin.fields.unitPrice"
  | "customerAdmin.fields.minimumQuantity"
  | "customerAdmin.fields.functionTypeId"
  | "customerAdmin.fields.qualificationTypeId"
  | "customerAdmin.fields.planningModeCode"
  | "customerAdmin.fields.sortOrder"
  | "customerAdmin.fields.surchargeType"
  | "customerAdmin.fields.weekdayMask"
  | "customerAdmin.fields.timeFromMinute"
  | "customerAdmin.fields.timeToMinute"
  | "customerAdmin.fields.regionCode"
  | "customerAdmin.fields.percentValue"
  | "customerAdmin.fields.fixedAmount"
  | "customerAdmin.actions.refreshCommercial"
  | "customerAdmin.actions.saveBillingProfile"
  | "customerAdmin.actions.addInvoiceParty"
  | "customerAdmin.actions.createInvoiceParty"
  | "customerAdmin.actions.saveInvoiceParty"
  | "customerAdmin.actions.addRateCard"
  | "customerAdmin.actions.createRateCard"
  | "customerAdmin.actions.saveRateCard"
  | "customerAdmin.actions.addRateLine"
  | "customerAdmin.actions.createRateLine"
  | "customerAdmin.actions.saveRateLine"
  | "customerAdmin.actions.addSurchargeRule"
  | "customerAdmin.actions.createSurchargeRule"
  | "customerAdmin.actions.saveSurchargeRule"
  | "customerAdmin.confirm.activeCommercialChange"
  | "customerAdmin.confirm.defaultInvoicePartyChange"
  | "customerAdmin.feedback.commercialSaved"
  | "customerAdmin.feedback.invoicePartyRequired"
  | "customerAdmin.feedback.invalidInvoiceEmail"
  | "customerAdmin.feedback.invalidPaymentTerms"
  | "customerAdmin.feedback.taxExemptionReasonRequired"
  | "customerAdmin.feedback.taxExemptionReasonForbidden"
  | "customerAdmin.feedback.bankAccountHolderRequired"
  | "customerAdmin.feedback.bankIbanRequired"
  | "customerAdmin.feedback.eInvoiceRequired"
  | "customerAdmin.feedback.eInvoiceDispatchMismatch"
  | "customerAdmin.feedback.leitwegRequired"
  | "customerAdmin.feedback.leitwegForbidden"
  | "customerAdmin.feedback.dispatchEmailRequired"
  | "customerAdmin.feedback.invoiceLayoutIncompatible"
  | "customerAdmin.feedback.defaultInvoicePartyConflict"
  | "customerAdmin.feedback.rateKindRequired"
  | "customerAdmin.feedback.invalidCurrency"
  | "customerAdmin.feedback.rateCardEffectiveFromRequired"
  | "customerAdmin.feedback.invalidEffectiveWindow"
  | "customerAdmin.feedback.rateCardOverlap"
  | "customerAdmin.feedback.rateLineKindRequired"
  | "customerAdmin.feedback.invalidBillingUnit"
  | "customerAdmin.feedback.invalidUnitPrice"
  | "customerAdmin.feedback.invalidMinimumQuantity"
  | "customerAdmin.feedback.duplicateRateDimension"
  | "customerAdmin.feedback.surchargeTypeRequired"
  | "customerAdmin.feedback.surchargeEffectiveFromRequired"
  | "customerAdmin.feedback.invalidWeekdayMask"
  | "customerAdmin.feedback.invalidTimeRange"
  | "customerAdmin.feedback.invalidAmountCombination"
  | "customerAdmin.feedback.surchargeOutsideRateCardWindow"
  | "customerAdmin.option.invoiceLayout.standard"
  | "customerAdmin.option.invoiceLayout.compact"
  | "customerAdmin.option.invoiceLayout.detailed_timesheet"
  | "customerAdmin.option.shippingMethod.email_pdf"
  | "customerAdmin.option.shippingMethod.portal_download"
  | "customerAdmin.option.shippingMethod.postal_print"
  | "customerAdmin.option.shippingMethod.e_invoice"
  | "customerAdmin.option.dunningPolicy.disabled"
  | "customerAdmin.option.dunningPolicy.standard"
  | "customerAdmin.option.dunningPolicy.strict";

type MessageCatalog = Record<MessageKey, string>;

export const messages: Record<AppLocale, MessageCatalog> = {
  de: {
    "app.title": "SicherPlan",
    "locale.label": "Sprache",
    "locale.de": "Deutsch",
    "locale.en": "Englisch",
    "theme.toggle.light": "Dunkelmodus",
    "theme.toggle.dark": "Hellmodus",
    "theme.mode.light": "Hell",
    "theme.mode.dark": "Dunkel",
    "layout.admin.eyebrow": "Vben-orientierte Shell",
    "layout.admin.title": "Interner Bereich",
    "layout.portal.eyebrow": "Portalstruktur",
    "layout.portal.title": "Externer Bereich",
    "brand.adminSubtitle": "Admin & Operative Steuerung",
    "brand.portalSubtitle": "Freigegebene Portalansichten",
    "role.label": "Rolle anzeigen",
    "role.platform_admin": "Plattformadmin",
    "role.tenant_admin": "Mandantenadmin",
    "role.dispatcher": "Disponent / Einsatzleitung",
    "role.accounting": "Buchhaltung",
    "role.controller_qm": "Controlling / QM",
    "role.customer_user": "Kundenportal",
    "role.subcontractor_user": "Subunternehmerportal",
    "shell.eyebrow": "SicherPlan Shell",
    "shell.title": "Rollenbasierte Steuerung fuer Security Operations",
    "shell.lead":
      "Diese Startseite zeigt die erste webbasierte Shell mit Admin- und Portalpfaden, jetzt mit zentralen Light/Dark-Token und DE/EN-Lokalisierung fuer spaetere IAM-Arbeit.",
    "shell.cta.admin": "Zum Adminbereich",
    "shell.cta.portal": "Zum Portalbereich",
    "shell.stat.roles": "Rollen",
    "shell.stat.modules": "Modulgruppen",
    "shell.stat.portals": "Portalpfade",
    "module.eyebrow": "Platzhaltermodul",
    "module.note.navigation":
      "Navigation und Rollenfreigaben sind bereits im Shell-Register hinterlegt.",
    "module.note.future":
      "CRUD-Ansichten, Formulare und Reportings folgen in spaeteren Aufgaben.",
    "module.note.compatibility":
      "Die Shell bleibt kompatibel mit spaeterer RBAC-, Theme- und i18n-Erweiterung.",
    "route.admin.dashboard.title": "Dashboard",
    "route.admin.dashboard.description":
      "Startpunkt fuer interne Rollen mit Schnellzugriff auf Kernmodule.",
    "route.admin.core.title": "Kernsystem",
    "route.admin.core.description":
      "Mandanten, Niederlassungen, Nummernkreise und zentrale Einstellungen.",
    "route.admin.platform_services.title": "Plattformdienste",
    "route.admin.platform_services.description":
      "Dokumente, Kommunikation, Hinweise und Integrationsjobs.",
    "route.admin.customers.title": "Kunden",
    "route.admin.customers.description":
      "Stammdaten, Kontakte, Abrechnungsvorgaben und Portalfreigaben.",
    "route.admin.recruiting.title": "Recruiting",
    "route.admin.recruiting.description":
      "Bewerbungen pruefen, Interviewschritte dokumentieren und Entscheidungen nachvollziehbar steuern.",
    "route.admin.employees.title": "Mitarbeitende",
    "route.admin.employees.description":
      "Recruiting, Personalakte, Verfuegbarkeit und Qualifikationen.",
    "route.admin.subcontractors.title": "Subunternehmer",
    "route.admin.subcontractors.description":
      "Partnerfirmen, Einsatzfreigaben und Compliance-Status.",
    "route.admin.planning.title": "Planung",
    "route.admin.planning.description":
      "Objekte, Auftraege, Schichtplaene, Validierung und Freigaben.",
    "route.admin.field_execution.title": "Feldeinsatz",
    "route.admin.field_execution.description":
      "Wachbuch, Streifengaenge, Zeiterfassung und mobile Rueckmeldungen.",
    "route.admin.finance.title": "Finanzen",
    "route.admin.finance.description":
      "Actuals, Lohnexporte, Rechnungen und Partnerpruefungen.",
    "route.admin.reporting.title": "Reporting",
    "route.admin.reporting.description":
      "Operative, kaufmaennische und Compliance-Auswertungen.",
    "route.portal.customer.title": "Kundenportal",
    "route.portal.customer.description":
      "Freigegebene Auftraege, Berichte, Zeiten und Dokumente.",
    "route.portal.subcontractor.title": "Subunternehmerportal",
    "route.portal.subcontractor.description":
      "Freigegebene Einsaetze, Mitarbeitende und Rueckmeldungen im freigegebenen Umfang.",
    "portalCustomer.eyebrow": "Kundenzugang",
    "portalCustomer.title": "Kundenportal und Scope-Pruefung",
    "portalCustomer.lead":
      "Dieser Einstieg nutzt die gemeinsame IAM-Sitzung und loest den Kundenkontext ausschliesslich ueber Rollen-Scope und den verknuepften Kundenkontakt auf.",
    "portalCustomer.login.tenantCode": "Mandantencode",
    "portalCustomer.login.identifier": "Benutzername oder E-Mail",
    "portalCustomer.login.password": "Passwort",
    "portalCustomer.login.deviceLabel": "Geraetebezeichnung",
    "portalCustomer.actions.login": "Im Portal anmelden",
    "portalCustomer.actions.refresh": "Portalstatus neu laden",
    "portalCustomer.actions.logout": "Abmelden",
    "portalCustomer.loading.title": "Portalzugriff wird geprueft",
    "portalCustomer.loading.body":
      "Die Sitzung und der zugeordnete Kundenkontext werden gegen die gemeinsame IAM- und CRM-Verknuepfung verifiziert.",
    "portalCustomer.empty.title": "Kein freigegebener Kundenkontext",
    "portalCustomer.empty.body":
      "Dem aktuellen Portal-Konto ist kein nutzbarer Kunden-Scope zugeordnet oder die Verknuepfung ist unvollstaendig.",
    "portalCustomer.unauthorized.title": "Portalzugriff nicht erlaubt",
    "portalCustomer.unauthorized.body":
      "Dieses Konto darf das Kundenportal nicht verwenden oder besitzt aktuell nicht die noetigen Berechtigungen.",
    "portalCustomer.deactivated.title": "Portalzugriff deaktiviert",
    "portalCustomer.deactivated.body":
      "Der verknuepfte Kundenkontakt oder der zugeordnete Kunde ist deaktiviert bzw. archiviert.",
    "portalCustomer.summary.title": "Aufgeloester Kundenkontext",
    "portalCustomer.summary.customerNumber": "Kundennummer",
    "portalCustomer.summary.customerName": "Kundenname",
    "portalCustomer.summary.contact": "Portal-Kontakt",
    "portalCustomer.summary.email": "E-Mail",
    "portalCustomer.summary.function": "Funktion",
    "portalCustomer.summary.tenant": "Mandant",
    "portalCustomer.summary.scope": "Erlaubter Kunden-Scope",
    "portalCustomer.readOnly.title": "Nur freigegebene Portalansichten",
    "portalCustomer.readOnly.body":
      "Dieses Portal zeigt nur kundenbezogene, freigegebene und schreibgeschuetzte Ausgaben. Nicht umgesetzte Quellmodule bleiben als explizite Leerstelle sichtbar.",
    "portalCustomer.history.eyebrow": "Kundenhistorie",
    "portalCustomer.history.title": "Freigegebene Historie und Anhaenge",
    "portalCustomer.history.lead":
      "Die Portalhistorie zeigt nur kundenbezogene Verlaufsereignisse mit docs-gestuetzten Anhaengen aus dem CRM.",
    "portalCustomer.history.empty": "Fuer diesen Kunden sind noch keine freigegebenen Historieneintraege vorhanden.",
    "portalCustomer.meta.releasedOnly": "Nur freigegebene Inhalte werden angezeigt.",
    "portalCustomer.meta.customerScoped": "Jede Abfrage bleibt auf den aktuellen Kunden-Scope eingeschraenkt.",
    "portalCustomer.meta.personalNamesRestricted":
      "Personennamen bleiben standardmaessig ausgeblendet, bis spaetere Freigaberegeln aktiv sind.",
    "portalCustomer.meta.sourceModule": "Quellmodul",
    "portalCustomer.meta.docsBacked": "Ausgaben werden spaeter ueber den zentralen Dokumentdienst bereitgestellt.",
    "portalCustomer.states.loading": "Laedt",
    "portalCustomer.states.pending": "Ausstehend",
    "portalCustomer.states.empty": "Leer",
    "portalCustomer.states.ready": "Freigegeben",
    "portalCustomer.datasets.orders.eyebrow": "Auftraege",
    "portalCustomer.datasets.orders.title": "Freigegebene Auftraege",
    "portalCustomer.datasets.orders.lead":
      "Kundenauftraege werden erst angezeigt, wenn das Planungsmodul freigegebene Portallesemodelle liefert.",
    "portalCustomer.datasets.orders.pending":
      "Es liegen noch keine freigegebenen Auftragsdaten aus dem Planungsmodul vor.",
    "portalCustomer.datasets.schedules.eyebrow": "Einsatzplaene",
    "portalCustomer.datasets.schedules.title": "Freigegebene Einsatzplaene",
    "portalCustomer.datasets.schedules.lead":
      "Nur veroeffentlichte Kundenplaene werden hier sichtbar, sobald die Planungsquelle verfuegbar ist.",
    "portalCustomer.datasets.schedules.pending":
      "Die Kundenansicht fuer freigegebene Einsatzplaene ist vorbereitet, aber das Quellmodul ist noch nicht angeschlossen.",
    "portalCustomer.datasets.watchbooks.eyebrow": "Wachbuch",
    "portalCustomer.datasets.watchbooks.title": "Freigegebene Wachbuchauszuege",
    "portalCustomer.datasets.watchbooks.lead":
      "Wachbuch- und Einsatzereignisse erscheinen erst nach Umsetzung des Feldeinsatz-Backbones im freigegebenen Umfang.",
    "portalCustomer.datasets.watchbooks.pending":
      "Es sind noch keine freigegebenen Wachbuchereignisse fuer das Kundenportal verfuegbar.",
    "portalCustomer.datasets.timesheets.eyebrow": "Zeiten",
    "portalCustomer.datasets.timesheets.title": "Freigegebene Stundennachweise",
    "portalCustomer.datasets.timesheets.lead":
      "Stundennachweise bleiben dokumentzentriert und werden spaeter ueber die Finanzbruecke und den Dokumentdienst veroeffentlicht.",
    "portalCustomer.datasets.timesheets.pending":
      "Freigegebene Stundennachweise sind noch nicht an das Portal angebunden.",
    "portalCustomer.datasets.reports.eyebrow": "Berichte",
    "portalCustomer.datasets.reports.title": "Freigegebene Berichts- und Ergebnispakete",
    "portalCustomer.datasets.reports.lead":
      "Berichte und Ergebnisdokumente werden als freigegebene Pakete ueber Reporting und Dokumentdienst eingebunden.",
    "portalCustomer.datasets.reports.pending":
      "Es sind noch keine freigegebenen Berichtspakete fuer diesen Kunden veroeffentlicht.",
    "portalCustomer.feedback.authRequired": "Bitte zuerst mit einem gueltigen Portal-Konto anmelden.",
    "portalCustomer.feedback.invalidCredentials": "Die Anmeldedaten sind ungueltig.",
    "portalCustomer.feedback.permissionDenied":
      "Das aktuelle Konto besitzt keinen zulaessigen Kundenportalzugriff.",
    "portalCustomer.feedback.scopeNotResolved":
      "Der Kunden-Scope dieses Portal-Kontos konnte nicht eindeutig bestimmt werden.",
    "portalCustomer.feedback.contactNotLinked":
      "Dem aktuellen Portal-Konto ist kein aktiver Kundenkontakt zugeordnet.",
    "portalCustomer.feedback.contactInactive":
      "Der verknuepfte Kundenkontakt ist nicht mehr aktiv.",
    "portalCustomer.feedback.customerInactive":
      "Der verknuepfte Kunde ist nicht mehr aktiv.",
    "portalCustomer.feedback.sessionReady":
      "Die Portalsitzung wurde erfolgreich geladen und auf den Kundenkontext eingeschraenkt.",
    "portalCustomer.feedback.loggedOut": "Die Portalsitzung wurde beendet.",
    "portalCustomer.feedback.error":
      "Der Kundenportalzugriff konnte nicht geladen werden.",
    "recruitingApplicant.eyebrow": "Bewerbung",
    "recruitingApplicant.title": "Oeffentliches Bewerbungsformular",
    "recruitingApplicant.lead":
      "Dieses Formular laeuft mandantenspezifisch, iframe-tauglich und speichert Anlagen ueber den zentralen Dokumentdienst.",
    "recruitingApplicant.embed.embedded": "Eingebettete Darstellung aktiv",
    "recruitingApplicant.embed.standalone": "Standalone-Darstellung aktiv",
    "recruitingApplicant.loading.title": "Formular wird geladen",
    "recruitingApplicant.loading.body":
      "Die mandantenspezifische Formular-Konfiguration wird geladen.",
    "recruitingApplicant.error.title": "Bewerbungsformular nicht verfuegbar",
    "recruitingApplicant.success.eyebrow": "Eingang bestaetigt",
    "recruitingApplicant.success.title": "Bewerbung uebermittelt",
    "recruitingApplicant.success.body":
      "Die Bewerbung wurde gespeichert und mit einer Vorgangsnummer versehen.",
    "recruitingApplicant.fields.selectPlaceholder": "Bitte waehlen",
    "recruitingApplicant.fields.attachments": "Anlagen",
    "recruitingApplicant.fields.attachmentsHelp":
      "Maximal {count} Datei(en), jeweils bis ca. {sizeMb} MB. Zulaessige Typen werden vom Mandanten vorgegeben.",
    "recruitingApplicant.fields.consent":
      "Ich bestaetige die Datenschutz-Einwilligung fuer diese Bewerbung.",
    "recruitingApplicant.fields.policyLink": "Datenschutzhinweis",
    "recruitingApplicant.fields.policyVersion": "Angezeigte Version: {version}",
    "recruitingApplicant.actions.submit": "Bewerbung absenden",
    "recruitingApplicant.actions.submitting": "Bewerbung wird uebermittelt",
    "recruitingApplicant.actions.clearFeedback": "Hinweis schliessen",
    "recruitingApplicant.feedback.submitted": "Bewerbung erfolgreich uebermittelt",
    "recruitingApplicant.feedback.tenantNotFound":
      "Fuer diesen Mandanten ist kein Bewerbungsformular verfuegbar.",
    "recruitingApplicant.feedback.formDisabled":
      "Das Bewerbungsformular ist aktuell deaktiviert.",
    "recruitingApplicant.feedback.originDenied":
      "Diese Einbettungsherkunft ist fuer das Formular nicht freigegeben.",
    "recruitingApplicant.feedback.rateLimited":
      "Zu viele Bewerbungen aus dieser Quelle. Bitte spaeter erneut versuchen.",
    "recruitingApplicant.feedback.consentRequired":
      "Die Datenschutz-Einwilligung muss bestaetigt werden.",
    "recruitingApplicant.feedback.policyMismatch":
      "Die Formularversion ist veraltet. Bitte laden Sie die Seite neu.",
    "recruitingApplicant.feedback.fieldRequired":
      "Bitte fuellen Sie alle Pflichtfelder aus.",
    "recruitingApplicant.feedback.invalidEmail":
      "Bitte geben Sie eine gueltige E-Mail-Adresse an.",
    "recruitingApplicant.feedback.invalidFieldOption":
      "Eine ausgewaehlte Formularoption ist ungueltig.",
    "recruitingApplicant.feedback.tooManyAttachments":
      "Es wurden zu viele Anlagen ausgewaehlt.",
    "recruitingApplicant.feedback.attachmentTypeNotAllowed":
      "Mindestens ein Dateityp ist fuer dieses Formular nicht erlaubt.",
    "recruitingApplicant.feedback.attachmentTooLarge":
      "Mindestens eine Datei ist zu gross fuer dieses Formular.",
    "recruitingApplicant.feedback.duplicateSubmission":
      "Diese Bewerbung wurde bereits uebermittelt.",
    "recruitingApplicant.feedback.error":
      "Das Bewerbungsformular konnte nicht abgesendet werden.",
    "recruitingAdmin.eyebrow": "Recruiting",
    "recruitingAdmin.title": "Bewerberverwaltung und Entscheidungsfluss",
    "recruitingAdmin.lead":
      "Diese Recruiting-Seite bindet direkt an die freigegebenen Bewerbungs- und Workflow-APIs an und zeigt Status, Einwilligung, Anlagen und Aktivitaetshistorie ohne lokale Mock-Wahrheit.",
    "recruitingAdmin.permission.read": "Leserecht",
    "recruitingAdmin.permission.write": "Schreibrecht",
    "recruitingAdmin.permission.docs": "Dokumentzugriff",
    "recruitingAdmin.permission.missingTitle": "Recruiting-Berechtigung fehlt",
    "recruitingAdmin.permission.missingBody":
      "Diese Admin-Seite ist nur fuer Rollen mit Recruiting-Leserechten verfuegbar.",
    "recruitingAdmin.auth.missingTitle": "Anmeldung erforderlich",
    "recruitingAdmin.auth.missingBody":
      "Melden Sie sich zuerst ueber die Systemanmeldung an, bevor Bewerbungen geladen werden koennen.",
    "recruitingAdmin.scope.label": "Mandanten-Scope",
    "recruitingAdmin.scope.placeholder": "Tenant-UUID fuer Plattform-Admin-Modus",
    "recruitingAdmin.scope.platformHelp":
      "Plattformadmins waehlen den Recruiting-Mandanten explizit und speichern ihn fuer weitere Aufrufe.",
    "recruitingAdmin.scope.sessionHelp":
      "Tenant-Admins arbeiten immer im Mandantenkontext der aktuellen Sitzung.",
    "recruitingAdmin.scope.missingTitle": "Mandanten-Scope fehlt",
    "recruitingAdmin.scope.missingBody":
      "Waehlen Sie zuerst einen Recruiting-Mandanten, bevor Bewerbungen geladen werden.",
    "recruitingAdmin.list.eyebrow": "Eingang",
    "recruitingAdmin.list.title": "Bewerbungsliste",
    "recruitingAdmin.list.empty": "Keine Bewerbungen fuer die aktuellen Filter gefunden.",
    "recruitingAdmin.detail.eyebrow": "Detail",
    "recruitingAdmin.detail.emptyTitle": "Keine Bewerbung ausgewaehlt",
    "recruitingAdmin.detail.emptyEyebrow": "Detailansicht",
    "recruitingAdmin.detail.emptyBody":
      "Waehlen Sie links eine Bewerbung aus, um Einwilligung, Anlagen und Verlauf zu pruefen.",
    "recruitingAdmin.detail.submissionEyebrow": "Einreichung",
    "recruitingAdmin.detail.submissionTitle": "Bewerbungsdaten",
    "recruitingAdmin.summary.applicationNo": "Bewerbungsnummer",
    "recruitingAdmin.summary.desiredRole": "Gewuenschte Position",
    "recruitingAdmin.summary.availability": "Verfuegbar ab",
    "recruitingAdmin.summary.source": "Quelle",
    "recruitingAdmin.summary.employeeFile": "Mitarbeitendenakte",
    "recruitingAdmin.summary.none": "keine Angabe",
    "recruitingAdmin.consent.eyebrow": "Datenschutz",
    "recruitingAdmin.consent.title": "Einwilligungsnachweis",
    "recruitingAdmin.consent.granted": "Einwilligung bestaetigt",
    "recruitingAdmin.consent.timestamp": "Zeitpunkt",
    "recruitingAdmin.consent.policyRef": "Policy-Referenz",
    "recruitingAdmin.consent.policyVersion": "Policy-Version",
    "recruitingAdmin.consent.origin": "Origin",
    "recruitingAdmin.consent.ip": "IP-Adresse",
    "recruitingAdmin.attachments.eyebrow": "Anlagen",
    "recruitingAdmin.attachments.title": "Bewerbungsdokumente",
    "recruitingAdmin.attachments.empty": "Zu dieser Bewerbung sind keine Anlagen verknuepft.",
    "recruitingAdmin.notes.eyebrow": "Notizen",
    "recruitingAdmin.notes.title": "Review- und Interviewnotizen",
    "recruitingAdmin.timeline.eyebrow": "Verlauf",
    "recruitingAdmin.timeline.title": "Workflow-Historie",
    "recruitingAdmin.timeline.empty": "Noch keine Workflow-Ereignisse vorhanden.",
    "recruitingAdmin.actions.rememberScope": "Scope merken",
    "recruitingAdmin.actions.refresh": "Neu laden",
    "recruitingAdmin.actions.search": "Filter anwenden",
    "recruitingAdmin.actions.clearFeedback": "Hinweis schliessen",
    "recruitingAdmin.actions.previewAttachment": "Vorschau",
    "recruitingAdmin.actions.downloadAttachment": "Download",
    "recruitingAdmin.actions.transitionEyebrow": "Statuswechsel",
    "recruitingAdmin.actions.transitionTitle": "Naechsten Schritt ausfuehren",
    "recruitingAdmin.actions.applyTransition": "Status uebernehmen",
    "recruitingAdmin.actions.addNote": "Notiz speichern",
    "recruitingAdmin.fields.fullName": "Name",
    "recruitingAdmin.fields.email": "E-Mail",
    "recruitingAdmin.fields.phone": "Telefon",
    "recruitingAdmin.fields.locale": "Sprache",
    "recruitingAdmin.fields.message": "Nachricht",
    "recruitingAdmin.fields.activityType": "Aktivitaetstyp",
    "recruitingAdmin.fields.nextStatus": "Naechster Status",
    "recruitingAdmin.fields.note": "Notiz",
    "recruitingAdmin.fields.decisionReason": "Entscheidungsgrund",
    "recruitingAdmin.fields.interviewScheduledAt": "Interviewtermin",
    "recruitingAdmin.fields.hiringTargetDate": "Einstellungsdatum",
    "recruitingAdmin.filters.search": "Suche",
    "recruitingAdmin.filters.searchPlaceholder": "Name, E-Mail, Bewerbungsnummer oder Rolle",
    "recruitingAdmin.filters.status": "Status",
    "recruitingAdmin.filters.sourceChannel": "Quelle",
    "recruitingAdmin.filters.allStatuses": "Alle Status",
    "recruitingAdmin.filters.allSources": "Alle Quellen",
    "recruitingAdmin.status.submitted": "Eingegangen",
    "recruitingAdmin.status.in_review": "In Pruefung",
    "recruitingAdmin.status.interview_scheduled": "Interview terminiert",
    "recruitingAdmin.status.accepted": "Angenommen",
    "recruitingAdmin.status.rejected": "Abgelehnt",
    "recruitingAdmin.status.ready_for_conversion": "Bereit fuer Uebernahme",
    "recruitingAdmin.source.public_form": "Oeffentliches Formular",
    "recruitingAdmin.activity.recruiterNote": "Review-Notiz",
    "recruitingAdmin.activity.interviewNote": "Interviewnotiz",
    "recruitingAdmin.event.status_transition": "Statuswechsel",
    "recruitingAdmin.event.interview_scheduled": "Interview geplant",
    "recruitingAdmin.event.decision": "Entscheidung",
    "recruitingAdmin.event.reopened": "Wiederoeffnet",
    "recruitingAdmin.event.ready_for_conversion": "Bereit fuer Uebernahme",
    "recruitingAdmin.event.converted": "In Mitarbeitendenakte uebernommen",
    "recruitingAdmin.event.recruiter_note": "Review-Notiz",
    "recruitingAdmin.event.interview_note": "Interviewnotiz",
    "recruitingAdmin.feedback.titleSuccess": "Aktion erfolgreich",
    "recruitingAdmin.feedback.titleError": "Aktion fehlgeschlagen",
    "recruitingAdmin.feedback.authRequired":
      "Die Recruiting-Seite braucht eine gueltige Sitzung.",
    "recruitingAdmin.feedback.permissionDenied":
      "Die aktuelle Rolle darf diese Recruiting-Aktion nicht ausfuehren.",
    "recruitingAdmin.feedback.notFound":
      "Die angeforderte Bewerbung oder Anlage wurde nicht gefunden.",
    "recruitingAdmin.feedback.invalidStatus":
      "Der angeforderte Bewerbungsstatus ist ungueltig.",
    "recruitingAdmin.feedback.transitionNotAllowed":
      "Dieser Schritt ist fuer den aktuellen Bewerbungsstatus nicht erlaubt.",
    "recruitingAdmin.feedback.interviewTimeRequired":
      "Fuer den Interviewstatus muss ein Termin angegeben werden.",
    "recruitingAdmin.feedback.decisionReasonRequired":
      "Fuer diese Entscheidung ist eine Begruendung erforderlich.",
    "recruitingAdmin.feedback.reopenNoteRequired":
      "Zum Wiederoeffnen ist eine Notiz erforderlich.",
    "recruitingAdmin.feedback.hiringTargetRequired":
      "Fuer die Uebergabe an die Uebernahme ist ein Einstellungsdatum erforderlich.",
    "recruitingAdmin.feedback.noteRequired":
      "Fuer diese Notizaktion ist ein Inhalt erforderlich.",
    "recruitingAdmin.feedback.conversionMissing":
      "Die zugeordnete Mitarbeitendenakte konnte nicht geladen werden.",
    "recruitingAdmin.feedback.documentNotFound":
      "Das angeforderte Bewerbungsdokument konnte nicht geladen werden.",
    "recruitingAdmin.feedback.transitionSaved":
      "Der Workflow-Schritt wurde gespeichert und im Verlauf dokumentiert.",
    "recruitingAdmin.feedback.noteSaved":
      "Die Recruiting-Notiz wurde gespeichert.",
    "recruitingAdmin.feedback.error":
      "Die Recruiting-Aktion konnte nicht abgeschlossen werden.",
    "recruitingAdmin.confirm.accepted":
      "Bewerbung wirklich annehmen? Dieser Schritt wird dokumentiert.",
    "recruitingAdmin.confirm.rejected":
      "Bewerbung wirklich ablehnen? Dieser Schritt wird dokumentiert.",
    "recruitingAdmin.common.yes": "Ja",
    "recruitingAdmin.common.no": "Nein",
    "employeeAdmin.eyebrow": "Mitarbeitende",
    "employeeAdmin.title": "Mitarbeitendenakte und operative Pflege",
    "employeeAdmin.lead":
      "Diese Mitarbeitendenansicht arbeitet direkt gegen die operative HR-API, haelt private Bereiche getrennt und nutzt den zentralen Dokumentendienst fuer Profilfoto und Dateinachweise.",
    "employeeAdmin.permission.read": "Leserecht",
    "employeeAdmin.permission.write": "Schreibrecht",
    "employeeAdmin.permission.privateRead": "HR-Privat lesen",
    "employeeAdmin.permission.missingTitle": "Mitarbeitenden-Berechtigung fehlt",
    "employeeAdmin.permission.missingBody":
      "Diese Verwaltungsseite ist nur fuer Rollen mit Mitarbeitenden-Leserecht verfuegbar.",
    "employeeAdmin.scope.label": "Mandanten-Scope",
    "employeeAdmin.scope.placeholder": "Tenant-UUID fuer Plattform-Admin-Modus",
    "employeeAdmin.scope.help":
      "Plattformadmins koennen den aktiven Mandanten wechseln; Tenant-Admins bleiben im Sitzungskontext.",
    "employeeAdmin.scope.missingTitle": "Mandanten-Scope fehlt",
    "employeeAdmin.scope.missingBody":
      "Waehlen Sie zuerst einen Mandanten, bevor Mitarbeitende geladen werden.",
    "employeeAdmin.list.eyebrow": "Liste",
    "employeeAdmin.list.title": "Mitarbeitende",
    "employeeAdmin.list.empty": "Keine Mitarbeitenden fuer die aktuellen Filter gefunden.",
    "employeeAdmin.detail.eyebrow": "Akte",
    "employeeAdmin.detail.newTitle": "Neue Mitarbeitendenakte",
    "employeeAdmin.detail.emptyTitle": "Keine Mitarbeitendenakte ausgewaehlt",
    "employeeAdmin.detail.emptyEyebrow": "Detailansicht",
    "employeeAdmin.detail.emptyBody":
      "Waehlen Sie links eine Mitarbeitendenakte aus oder legen Sie eine neue an.",
    "employeeAdmin.filters.search": "Suche",
    "employeeAdmin.filters.searchPlaceholder": "Personalnummer, Name oder E-Mail",
    "employeeAdmin.filters.status": "Status",
    "employeeAdmin.filters.allStatuses": "Alle Status",
    "employeeAdmin.filters.includeArchived": "Archivierte Datensaetze einschliessen",
    "employeeAdmin.status.active": "Aktiv",
    "employeeAdmin.status.inactive": "Inaktiv",
    "employeeAdmin.status.archived": "Archiviert",
    "employeeAdmin.fields.personnelNo": "Personalnummer",
    "employeeAdmin.fields.firstName": "Vorname",
    "employeeAdmin.fields.lastName": "Nachname",
    "employeeAdmin.fields.preferredName": "Rufname",
    "employeeAdmin.fields.workEmail": "Dienst-E-Mail",
    "employeeAdmin.fields.workPhone": "Diensttelefon",
    "employeeAdmin.fields.mobilePhone": "Mobilnummer",
    "employeeAdmin.fields.defaultBranchId": "Standardniederlassung",
    "employeeAdmin.fields.defaultMandateId": "Standardmandat",
    "employeeAdmin.fields.hireDate": "Eintrittsdatum",
    "employeeAdmin.fields.terminationDate": "Austrittsdatum",
    "employeeAdmin.fields.userId": "Benutzerkonto-ID",
    "employeeAdmin.fields.notes": "Operative Notizen",
    "employeeAdmin.fields.noteType": "Notiztyp",
    "employeeAdmin.fields.noteTitle": "Notiztitel",
    "employeeAdmin.fields.reminderAt": "Erinnerungsdatum",
    "employeeAdmin.fields.completedAt": "Erledigt am",
    "employeeAdmin.fields.noteBody": "Inhalt",
    "employeeAdmin.fields.groupCode": "Gruppencode",
    "employeeAdmin.fields.groupName": "Gruppenname",
    "employeeAdmin.fields.groupDescription": "Gruppenbeschreibung",
    "employeeAdmin.fields.assignGroup": "Gruppe zuordnen",
    "employeeAdmin.fields.validFrom": "Gueltig ab",
    "employeeAdmin.fields.validUntil": "Gueltig bis",
    "employeeAdmin.fields.membershipNotes": "Zuordnungsnotiz",
    "employeeAdmin.summary.branch": "Niederlassung",
    "employeeAdmin.summary.mandate": "Mandat",
    "employeeAdmin.summary.currentAddress": "Aktuelle Adresse",
    "employeeAdmin.summary.groups": "Gruppen",
    "employeeAdmin.summary.none": "Keine Angabe",
    "employeeAdmin.photo.eyebrow": "Profilfoto",
    "employeeAdmin.photo.title": "Foto und Vorschau",
    "employeeAdmin.photo.alt": "Profilfoto der mitarbeitenden Person",
    "employeeAdmin.photo.empty": "Noch kein Profilfoto hinterlegt",
    "employeeAdmin.photo.help": "Das Foto wird ueber den zentralen Dokumentendienst versioniert.",
    "employeeAdmin.notes.eyebrow": "Notizen",
    "employeeAdmin.notes.title": "Erinnerungen und positive Aktivitaet",
    "employeeAdmin.notes.empty": "Noch keine operativen Notizen vorhanden.",
    "employeeAdmin.groups.eyebrow": "Gruppen",
    "employeeAdmin.groups.title": "Gruppen und Zuordnungen",
    "employeeAdmin.groups.empty": "Noch keine Gruppenzuordnungen vorhanden.",
    "employeeAdmin.groups.selectPlaceholder": "Gruppe auswaehlen",
    "employeeAdmin.addresses.eyebrow": "Adressen",
    "employeeAdmin.addresses.title": "Aktuelle Adresshistorie",
    "employeeAdmin.addresses.empty": "Keine freigegebene Adresshistorie vorhanden.",
    "employeeAdmin.documents.eyebrow": "Dateien",
    "employeeAdmin.documents.title": "Dokumente und Nachweise",
    "employeeAdmin.documents.empty": "Keine mitarbeitendenbezogenen Dokumente vorhanden.",
    "employeeAdmin.noteType.operational_note": "Operative Notiz",
    "employeeAdmin.noteType.positive_activity": "Positive Aktivitaet",
    "employeeAdmin.noteType.reminder": "Erinnerung",
    "employeeAdmin.actions.rememberScope": "Scope merken",
    "employeeAdmin.actions.refresh": "Neu laden",
    "employeeAdmin.actions.search": "Suchen",
    "employeeAdmin.actions.clearFeedback": "Hinweis schliessen",
    "employeeAdmin.actions.newEmployee": "Mitarbeitendenakte anlegen",
    "employeeAdmin.actions.createEmployee": "Mitarbeitende anlegen",
    "employeeAdmin.actions.saveEmployee": "Akte speichern",
    "employeeAdmin.actions.reset": "Formular zuruecksetzen",
    "employeeAdmin.actions.uploadPhoto": "Foto hochladen",
    "employeeAdmin.actions.downloadPhoto": "Foto herunterladen",
    "employeeAdmin.actions.createNote": "Notiz anlegen",
    "employeeAdmin.actions.saveNote": "Notiz speichern",
    "employeeAdmin.actions.resetNote": "Notizformular leeren",
    "employeeAdmin.actions.createGroup": "Gruppe anlegen",
    "employeeAdmin.actions.saveGroup": "Gruppe speichern",
    "employeeAdmin.actions.resetGroup": "Gruppenformular leeren",
    "employeeAdmin.actions.assignGroup": "Gruppe zuordnen",
    "employeeAdmin.actions.saveMembership": "Zuordnung speichern",
    "employeeAdmin.actions.resetMembership": "Zuordnung leeren",
    "employeeAdmin.actions.exportEmployees": "Export starten",
    "employeeAdmin.actions.loadImportFile": "CSV laden",
    "employeeAdmin.actions.resetImportTemplate": "Vorlage einsetzen",
    "employeeAdmin.actions.importDryRun": "Import pruefen",
    "employeeAdmin.actions.importExecute": "Import ausfuehren",
    "employeeAdmin.actions.createAccessUser": "App-Benutzer anlegen",
    "employeeAdmin.actions.attachAccessUser": "Bestehenden Benutzer verknuepfen",
    "employeeAdmin.actions.detachAccessUser": "Zugang trennen",
    "employeeAdmin.actions.reconcileAccessUser": "Zugang abgleichen",
    "employeeAdmin.import.eyebrow": "Import / Export",
    "employeeAdmin.import.title": "Bulk-Onboarding und operative Exporte",
    "employeeAdmin.import.csvLabel": "CSV-Inhalt",
    "employeeAdmin.import.continueOnError": "Bei Fehlern mit den naechsten Zeilen fortfahren",
    "employeeAdmin.import.dryRunSummary": "Pruefung abgeschlossen: {total} Zeilen, {invalid} ungueltig.",
    "employeeAdmin.import.executeSummary": "Import abgeschlossen: {total} Zeilen, {created} angelegt, {updated} aktualisiert.",
    "employeeAdmin.import.exportSummary": "Export bereit: {rows} Zeilen, Dokument {documentId}.",
    "employeeAdmin.access.eyebrow": "App-Zugang",
    "employeeAdmin.access.title": "IAM-Verknuepfung fuer Mitarbeitenden-App",
    "employeeAdmin.access.user": "Benutzername",
    "employeeAdmin.access.email": "E-Mail",
    "employeeAdmin.access.enabled": "Zugang aktiv",
    "employeeAdmin.access.enabledYes": "Ja",
    "employeeAdmin.access.enabledNo": "Nein",
    "employeeAdmin.access.createUsername": "Neuer Benutzername",
    "employeeAdmin.access.createEmail": "Neue E-Mail",
    "employeeAdmin.access.createPassword": "Startpasswort",
    "employeeAdmin.access.attachUserId": "Vorhandene Benutzer-ID",
    "employeeAdmin.access.attachUsername": "Vorhandener Benutzername",
    "employeeAdmin.access.attachEmail": "Vorhandene E-Mail",
    "employeeAdmin.feedback.titleError": "Aktion fehlgeschlagen",
    "employeeAdmin.feedback.titleSuccess": "Aktion erfolgreich",
    "employeeAdmin.feedback.authRequired": "Die Mitarbeitendenverwaltung benoetigt eine gueltige Sitzung.",
    "employeeAdmin.feedback.permissionDenied":
      "Die aktuelle Rolle darf diese Mitarbeitendenaktion nicht ausfuehren.",
    "employeeAdmin.feedback.notFound":
      "Die angeforderte Mitarbeitendenakte oder Zuordnung wurde nicht gefunden.",
    "employeeAdmin.feedback.duplicatePersonnelNo":
      "Diese Personalnummer existiert im Mandanten bereits.",
    "employeeAdmin.feedback.duplicateGroupCode":
      "Dieser Gruppencode ist im Mandanten bereits vergeben.",
    "employeeAdmin.feedback.staleVersion":
      "Der Datensatz wurde zwischenzeitlich geaendert. Bitte neu laden und erneut versuchen.",
    "employeeAdmin.feedback.addressOverlap":
      "Die Adresshistorie enthaelt ein ueberlappendes Zeitfenster.",
    "employeeAdmin.feedback.reminderDateRequired":
      "Fuer Erinnerungen muss ein Erinnerungsdatum gesetzt werden.",
    "employeeAdmin.feedback.invalidNoteType":
      "Der gewaehlt Notiztyp ist nicht zulaessig.",
    "employeeAdmin.feedback.photoUploadFailed":
      "Das Profilfoto konnte nicht gespeichert werden.",
    "employeeAdmin.feedback.invalidImportCsv":
      "Die Importdatei ist leer oder unlesbar.",
    "employeeAdmin.feedback.invalidImportHeaders":
      "Die Importdatei verwendet nicht das erwartete Spaltenlayout.",
    "employeeAdmin.feedback.accessUsernameTaken":
      "Der Benutzername ist im aktuellen Mandanten bereits vergeben.",
    "employeeAdmin.feedback.accessEmailTaken":
      "Die E-Mail-Adresse ist im aktuellen Mandanten bereits vergeben.",
    "employeeAdmin.feedback.accessAmbiguousMatch":
      "Zum Verknuepfen muss genau ein Benutzer-Suchfeld gefuellt werden.",
    "employeeAdmin.feedback.accessRoleMissing":
      "Die Rolle fuer Mitarbeitendenzugang fehlt im IAM-Katalog.",
    "employeeAdmin.feedback.employeeSaved":
      "Die Mitarbeitendenakte wurde gespeichert.",
    "employeeAdmin.feedback.noteSaved":
      "Die Mitarbeitendennotiz wurde gespeichert.",
    "employeeAdmin.feedback.groupSaved":
      "Die Mitarbeitendengruppe wurde gespeichert.",
    "employeeAdmin.feedback.membershipSaved":
      "Die Gruppenzuordnung wurde gespeichert.",
    "employeeAdmin.feedback.photoSaved":
      "Das Profilfoto wurde erfolgreich aktualisiert.",
    "employeeAdmin.feedback.importDryRunReady":
      "Die Importvorschau wurde erzeugt.",
    "employeeAdmin.feedback.importExecuted":
      "Der Mitarbeitendenimport wurde ausgefuehrt.",
    "employeeAdmin.feedback.exportReady":
      "Der Mitarbeitendenexport wurde erzeugt.",
    "employeeAdmin.feedback.accessLinked":
      "Der Mitarbeitendenzugang wurde verknuepft.",
    "employeeAdmin.feedback.accessDetached":
      "Der Mitarbeitendenzugang wurde getrennt.",
    "employeeAdmin.feedback.accessReconciled":
      "Die IAM-Verknuepfung wurde abgeglichen.",
    "employeeAdmin.feedback.error":
      "Die Mitarbeitendenaktion konnte nicht abgeschlossen werden.",
    "api.errors.platform.internal":
      "Es ist ein interner Plattformfehler aufgetreten.",
    "coreAdmin.breadcrumb": "Admin / Kernsystem / Mandantenverwaltung",
    "coreAdmin.eyebrow": "Core Administration",
    "coreAdmin.title": "Mandantenstruktur und Kernsteuerung",
    "coreAdmin.lead":
      "Diese Verwaltungsseite bindet direkt an die Core-Admin-APIs an und fuehrt Mandanten, Niederlassungen, Mandate und Einstellungen ohne lokale Mock-Wahrheit.",
    "coreAdmin.permission.ready": "RBAC-bereite Route",
    "coreAdmin.permission.label": "Berechtigungsschluessel",
    "coreAdmin.scope.label": "Mandanten-Scope",
    "coreAdmin.scope.placeholder": "Tenant-UUID fuer Tenant-Admin-Modus",
    "coreAdmin.scope.help":
      "Im temporaren Mock-Auth-Modus wird diese UUID als X-Tenant-Id an das Backend uebergeben.",
    "coreAdmin.scope.platformHint":
      "Plattformadmins sehen die tenant-uebergreifende Liste. Der Scope wird fuer spaeteres Tenant-Admin-Switching gemerkt.",
    "coreAdmin.scope.emptyTitle": "Tenant-Scope fehlt",
    "coreAdmin.scope.emptyBody":
      "Mandantenadmins brauchen eine gespeicherte Tenant-UUID, bevor Listen- und Detailaufrufe geladen werden koennen.",
    "coreAdmin.scope.remembered": "Gemerkter Scope",
    "coreAdmin.scope.none": "keiner",
    "coreAdmin.actions.refresh": "Neu laden",
    "coreAdmin.actions.loadScopedTenant": "Scope laden",
    "coreAdmin.actions.clearFeedback": "Hinweis schliessen",
    "coreAdmin.actions.createTenant": "Mandant anlegen",
    "coreAdmin.actions.saveTenant": "Mandant speichern",
    "coreAdmin.actions.activate": "Aktivieren",
    "coreAdmin.actions.deactivate": "Deaktivieren",
    "coreAdmin.actions.archive": "Archivieren",
    "coreAdmin.actions.reactivate": "Reaktivieren",
    "coreAdmin.actions.edit": "Bearbeiten",
    "coreAdmin.actions.cancel": "Abbrechen",
    "coreAdmin.actions.createBranch": "Niederlassung anlegen",
    "coreAdmin.actions.saveBranch": "Niederlassung speichern",
    "coreAdmin.actions.createMandate": "Mandat anlegen",
    "coreAdmin.actions.saveMandate": "Mandat speichern",
    "coreAdmin.actions.createSetting": "Einstellung anlegen",
    "coreAdmin.actions.saveSetting": "Einstellung speichern",
    "coreAdmin.tenants.eyebrow": "Mandantenuebersicht",
    "coreAdmin.tenants.title": "Mandanten",
    "coreAdmin.tenants.filterPlaceholder": "Nach Code oder Name filtern",
    "coreAdmin.tenants.empty": "Noch keine Mandanten vorhanden.",
    "coreAdmin.tenants.scopeOnly":
      "Im Tenant-Admin-Modus wird nur der scoped Mandant geladen.",
    "coreAdmin.onboarding.eyebrow": "Onboarding",
    "coreAdmin.onboarding.title": "Neuen Mandanten mit Basissatz anlegen",
    "coreAdmin.detail.eyebrow": "Detail und Pflege",
    "coreAdmin.detail.emptyTitle": "Kein Mandant ausgewaehlt",
    "coreAdmin.detail.emptyState":
      "Waehlen Sie links einen Mandanten aus, um Stammdaten, Niederlassungen, Mandate und Einstellungen zu pflegen.",
    "coreAdmin.lifecycle.title": "Lifecycle und Archivstatus",
    "coreAdmin.lifecycle.archivedHint":
      "Archivierte Mandanten bleiben explizit erhalten und koennen ueber den aktuellen Backend-Contract nicht wieder aktiviert werden.",
    "coreAdmin.branches.eyebrow": "Niederlassungen",
    "coreAdmin.branches.title": "Niederlassungsverwaltung",
    "coreAdmin.branches.empty": "Es sind noch keine Niederlassungen vorhanden.",
    "coreAdmin.mandates.eyebrow": "Mandate",
    "coreAdmin.mandates.title": "Mandatsverwaltung",
    "coreAdmin.mandates.empty": "Es sind noch keine Mandate vorhanden.",
    "coreAdmin.settings.eyebrow": "Mandanteneinstellungen",
    "coreAdmin.settings.title": "Sichere Einstellungen",
    "coreAdmin.settings.empty": "Es sind noch keine Einstellungen vorhanden.",
    "coreAdmin.settings.version": "Version",
    "coreAdmin.fields.tenantCode": "Mandantencode",
    "coreAdmin.fields.tenantName": "Mandantenname",
    "coreAdmin.fields.legalName": "Rechtlicher Name",
    "coreAdmin.fields.defaultLocale": "Standard-Sprache",
    "coreAdmin.fields.defaultCurrency": "Standard-Waehrung",
    "coreAdmin.fields.timezone": "Zeitzone",
    "coreAdmin.fields.branch": "Niederlassung",
    "coreAdmin.fields.branchPlaceholder": "Niederlassung waehlen",
    "coreAdmin.fields.branchCode": "Niederlassungscode",
    "coreAdmin.fields.branchName": "Niederlassungsname",
    "coreAdmin.fields.branchEmail": "Kontakt-E-Mail",
    "coreAdmin.fields.branchPhone": "Kontakt-Telefon",
    "coreAdmin.fields.mandateCode": "Mandatscode",
    "coreAdmin.fields.mandateName": "Mandatsname",
    "coreAdmin.fields.externalRef": "Externe Referenz",
    "coreAdmin.fields.notes": "Notizen",
    "coreAdmin.fields.settingKey": "Einstellungsschluessel",
    "coreAdmin.fields.settingValue": "Initialer Einstellungswert (JSON)",
    "coreAdmin.fields.settingValueJson": "JSON-Wert",
    "coreAdmin.status.active": "Aktiv",
    "coreAdmin.status.inactive": "Inaktiv",
    "coreAdmin.status.archived": "Archiviert",
    "coreAdmin.feedback.success": "Erfolg",
    "coreAdmin.feedback.error": "Fehler",
    "coreAdmin.feedback.info": "Hinweis",
    "coreAdmin.feedback.unexpected":
      "Die Core-Administration konnte die Aktion nicht abschliessen.",
    "coreAdmin.feedback.invalidJson":
      "Bitte geben Sie ein gueltiges JSON-Objekt fuer Einstellungen an.",
    "coreAdmin.feedback.tenantCreated": "Mandant und Basissatz wurden angelegt.",
    "coreAdmin.feedback.tenantSaved": "Mandantenstammdaten wurden gespeichert.",
    "coreAdmin.feedback.tenantStatusSaved": "Mandantenstatus wurde aktualisiert.",
    "coreAdmin.feedback.branchSaved": "Niederlassung wurde gespeichert.",
    "coreAdmin.feedback.branchStatusSaved": "Niederlassungsstatus wurde aktualisiert.",
    "coreAdmin.feedback.mandateSaved": "Mandat wurde gespeichert.",
    "coreAdmin.feedback.mandateStatusSaved": "Mandatsstatus wurde aktualisiert.",
    "coreAdmin.feedback.settingSaved": "Einstellung wurde gespeichert.",
    "coreAdmin.feedback.settingStatusSaved": "Einstellungsstatus wurde aktualisiert.",
    "coreAdmin.feedback.scopeRemembered": "Der Tenant-Scope wurde fuer den Tenant-Admin-Modus gemerkt.",
    "coreAdmin.api.errors.authorization.forbidden":
      "Diese Rolle darf die angeforderte Core-Administration nicht ausfuehren.",
    "coreAdmin.api.errors.tenant.not_found": "Mandant nicht gefunden.",
    "coreAdmin.api.errors.branch.not_found": "Niederlassung nicht gefunden.",
    "coreAdmin.api.errors.mandate.not_found": "Mandat nicht gefunden.",
    "coreAdmin.api.errors.setting.not_found": "Mandanteneinstellung nicht gefunden.",
    "coreAdmin.api.errors.tenant.duplicate_code":
      "Der Mandantencode existiert bereits.",
    "coreAdmin.api.errors.branch.duplicate_code":
      "Der Niederlassungscode existiert in diesem Mandanten bereits.",
    "coreAdmin.api.errors.mandate.duplicate_code":
      "Der Mandatscode existiert in diesem Mandanten bereits.",
    "coreAdmin.api.errors.setting.duplicate_key":
      "Dieser Einstellungsschluessel existiert bereits.",
    "coreAdmin.api.errors.setting.stale_version":
      "Die Einstellung wurde zwischenzeitlich geaendert. Bitte neu laden und erneut speichern.",
    "coreAdmin.api.errors.mandate.invalid_branch_scope":
      "Die gewaehlte Niederlassung gehoert nicht zu diesem Mandanten.",
    "coreAdmin.api.errors.lifecycle.archived_record":
      "Archivierte Datensaetze bleiben archiviert und koennen nicht ueber diesen Pfad reaktiviert werden.",
    "coreAdmin.api.errors.conflict.integrity":
      "Die Aenderung verletzt eine Integritaetsregel im Core-Backbone.",
    "noticeAdmin.eyebrow": "Plattformdienste / Hinweise",
    "noticeAdmin.title": "Hinweise, Zielgruppen und Bestaetigungen",
    "noticeAdmin.lead":
      "Diese Minimalansicht bindet an die Notice-APIs an: Entwurf anlegen, veroeffentlichen und die eigene Feed-Sicht pruefen.",
    "noticeAdmin.scope.label": "Mandanten-Scope",
    "noticeAdmin.scope.placeholder": "Tenant-UUID fuer Notice-APIs",
    "noticeAdmin.scope.action": "Scope merken",
    "noticeAdmin.scope.missingTitle": "Mandanten-Scope fehlt",
    "noticeAdmin.scope.missingBody":
      "Fuer die Hinweisfluesse wird eine Tenant-UUID benoetigt, damit Admin- und Feed-Aufrufe tenant-sicher bleiben.",
    "noticeAdmin.form.eyebrow": "Hinweisentwurf",
    "noticeAdmin.form.title": "Neuen Hinweis anlegen",
    "noticeAdmin.list.eyebrow": "Adminliste",
    "noticeAdmin.list.title": "Entwuerfe und veroeffentlichte Hinweise",
    "noticeAdmin.list.empty": "Noch keine Hinweise fuer diesen Tenant vorhanden.",
    "noticeAdmin.feed.eyebrow": "Meine Feed-Sicht",
    "noticeAdmin.feed.title": "Sichtbare Hinweise fuer die aktuelle Rolle",
    "noticeAdmin.feed.empty": "Aktuell ist fuer die Rolle kein Hinweis sichtbar.",
    "noticeAdmin.feed.acknowledged": "Bestaetigt",
    "noticeAdmin.fields.title": "Titel",
    "noticeAdmin.fields.summary": "Kurztext",
    "noticeAdmin.fields.body": "Inhalt",
    "noticeAdmin.fields.audienceRole": "Rollen-Zielgruppe",
    "noticeAdmin.fields.mandatory": "Bestaetigung erforderlich",
    "noticeAdmin.actions.create": "Entwurf speichern",
    "noticeAdmin.actions.publish": "Veroeffentlichen",
    "noticeAdmin.actions.refresh": "Neu laden",
    "noticeAdmin.actions.acknowledge": "Bestaetigen",
    "noticeAdmin.feedback.created": "Hinweis angelegt",
    "noticeAdmin.feedback.published": "Hinweis veroeffentlicht",
    "noticeAdmin.feedback.acknowledged": "Hinweis bestaetigt",
    "noticeAdmin.feedback.error": "Notice-Aktion fehlgeschlagen.",
    "customerAdmin.eyebrow": "Kundenverwaltung",
    "customerAdmin.title": "Kundenstamm, Kontakte und Adresslinks",
    "customerAdmin.lead":
      "Diese erste CRM-Ansicht folgt dem Vben-Admin-Muster mit Listen-, Detail- und Pflegebereichen fuer Kunden, Kontakte und wiederverwendete Adressen.",
    "customerAdmin.permission.read": "Leserechte",
    "customerAdmin.permission.write": "Schreibrechte",
    "customerAdmin.permission.missingTitle": "Keine CRM-Berechtigung",
    "customerAdmin.permission.missingBody":
      "Die aktuelle Rolle darf diese Kundenverwaltung nicht aufrufen. Backend-Berechtigungen bleiben trotzdem verbindlich.",
    "customerAdmin.scope.label": "Mandantenscope",
    "customerAdmin.scope.placeholder": "Tenant UUID eingeben",
    "customerAdmin.scope.missingTitle": "Scope oder Sitzung fehlt",
    "customerAdmin.scope.missingBody":
      "Fuer die Kunden-API werden ein Mandantenscope und ein gueltiges Bearer-Token benoetigt.",
    "customerAdmin.token.label": "Bearer-Token",
    "customerAdmin.token.placeholder": "Access Token fuer die Backend-API",
    "customerAdmin.token.help":
      "Die Shell hat noch keinen Login-Bildschirm. Bis `US-9-T1` bleibt das Token eine Entwickler-/Admin-Eingabe.",
    "customerAdmin.list.eyebrow": "Kundenliste",
    "customerAdmin.list.title": "Suche und Auswahl",
    "customerAdmin.list.empty": "Keine Kunden fuer die aktuellen Filter gefunden.",
    "customerAdmin.detail.eyebrow": "Kundendetail",
    "customerAdmin.detail.emptyTitle": "Noch kein Kunde ausgewaehlt",
    "customerAdmin.detail.emptyBody": "Waehle links einen Kunden aus oder starte einen neuen Datensatz.",
    "customerAdmin.detail.newTitle": "Neuen Kunden anlegen",
    "customerAdmin.form.generalEyebrow": "Stammdaten",
    "customerAdmin.form.generalTitle": "Allgemeine Kundendaten",
    "customerAdmin.filters.search": "Suche",
    "customerAdmin.filters.searchPlaceholder": "Nummer oder Name",
    "customerAdmin.filters.status": "Statusfilter",
    "customerAdmin.filters.allStatuses": "Alle Status",
    "customerAdmin.filters.includeArchived": "Archivierte Kunden einbeziehen",
    "customerAdmin.lifecycle.title": "Statussteuerung",
    "customerAdmin.lifecycle.help": "Archivierte Kunden bleiben erhalten und koennen derzeit nicht reaktiviert werden.",
    "customerAdmin.summary.primaryContact": "Primaerkontakt",
    "customerAdmin.summary.defaultBranch": "Standardniederlassung",
    "customerAdmin.summary.defaultMandate": "Standardmandat",
    "customerAdmin.summary.classification": "Klassifikation",
    "customerAdmin.summary.none": "Nicht gesetzt",
    "customerAdmin.contacts.eyebrow": "Kontakte",
    "customerAdmin.contacts.title": "Kontaktpflege",
    "customerAdmin.contacts.empty": "Noch keine Kontakte hinterlegt.",
    "customerAdmin.contacts.primaryBadge": "Primaerkontakt",
    "customerAdmin.contacts.standardBadge": "Kontakt",
    "customerAdmin.history.eyebrow": "Historie",
    "customerAdmin.history.title": "Lesbare Aenderungshistorie",
    "customerAdmin.history.empty": "Noch keine fachliche Historie fuer diesen Kunden vorhanden.",
    "customerAdmin.loginHistory.eyebrow": "Portal-Logins",
    "customerAdmin.loginHistory.title": "Gefilterte Kunden-Loginhistorie",
    "customerAdmin.loginHistory.empty": "Noch keine sichtbaren Portal-Logins fuer diesen Kunden vorhanden.",
    "customerAdmin.privacy.eyebrow": "Portal-Datenschutz",
    "customerAdmin.privacy.title": "Freigabe personenbezogener Namen",
    "customerAdmin.privacy.help":
      "Personennamen bleiben im Kundenportal standardmaessig verborgen. Eine Freigabe ist eng begrenzt, kundenspezifisch und wird auditiert.",
    "customerAdmin.privacy.lastReleasedAt": "Zuletzt freigegeben am",
    "customerAdmin.privacy.lastReleasedBy": "Zuletzt freigegeben durch",
    "customerAdmin.employeeBlocks.eyebrow": "Mitarbeitendensperren",
    "customerAdmin.employeeBlocks.title": "Kundenspezifische Mitarbeitendensperren",
    "customerAdmin.employeeBlocks.empty": "Noch keine Kundensperren fuer Mitarbeitende erfasst.",
    "customerAdmin.employeeBlocks.capability.pendingEmployees":
      "Das Mitarbeitendenverzeichnis folgt erst in Sprint 4. Bis dahin bleibt die Sperre auf eine direkte Employee-ID-Referenz begrenzt.",
    "customerAdmin.addresses.eyebrow": "Adressen",
    "customerAdmin.addresses.title": "Adresslinks",
    "customerAdmin.addresses.empty": "Noch keine Adressen verknuepft.",
    "customerAdmin.addresses.defaultBadge": "Standardadresse",
    "customerAdmin.addresses.linkBadge": "Adresslink",
    "customerAdmin.addressType.registered": "Firmensitz",
    "customerAdmin.addressType.billing": "Rechnung",
    "customerAdmin.addressType.mailing": "Post",
    "customerAdmin.addressType.service": "Leistungsort",
    "customerAdmin.fields.customerNumber": "Kundennummer",
    "customerAdmin.fields.name": "Anzeigename",
    "customerAdmin.fields.legalName": "Rechtlicher Name",
    "customerAdmin.fields.externalRef": "Externe Referenz",
    "customerAdmin.fields.legalFormLookupId": "Lookup-ID Rechtsform",
    "customerAdmin.fields.classificationLookupId": "Lookup-ID Klassifikation",
    "customerAdmin.fields.rankingLookupId": "Lookup-ID Ranking",
    "customerAdmin.fields.customerStatusLookupId": "Lookup-ID Kundenstatus",
    "customerAdmin.fields.defaultBranchId": "Standardniederlassung-ID",
    "customerAdmin.fields.defaultMandateId": "Standardmandat-ID",
    "customerAdmin.fields.notes": "Notizen",
    "customerAdmin.fields.fullName": "Vollstaendiger Name",
    "customerAdmin.fields.contactTitle": "Titel",
    "customerAdmin.fields.functionLabel": "Funktion",
    "customerAdmin.fields.email": "E-Mail",
    "customerAdmin.fields.phone": "Telefon",
    "customerAdmin.fields.mobile": "Mobil",
    "customerAdmin.fields.userId": "Portal-Benutzer-ID",
    "customerAdmin.fields.isPrimaryContact": "Als Primaerkontakt markieren",
    "customerAdmin.fields.isBillingContact": "Als Rechnungskontakt markieren",
    "customerAdmin.fields.addressId": "Adress-ID",
    "customerAdmin.fields.addressType": "Adresstyp",
    "customerAdmin.fields.historyEntry": "Historieneintrag",
    "customerAdmin.fields.documentId": "Dokument-ID",
    "customerAdmin.fields.personNamesReleased": "Personennamen im Portal freigeben",
    "customerAdmin.fields.employeeId": "Mitarbeitenden-ID",
    "customerAdmin.fields.reason": "Begruendung",
    "customerAdmin.fields.label": "Bezeichnung",
    "customerAdmin.fields.isDefault": "Als Standardadresse markieren",
    "customerAdmin.actions.rememberScope": "Scope speichern",
    "customerAdmin.actions.refresh": "Aktualisieren",
    "customerAdmin.actions.search": "Suchen",
    "customerAdmin.actions.exportCustomers": "CSV-Export",
    "customerAdmin.actions.newCustomer": "Neuer Kunde",
    "customerAdmin.actions.createCustomer": "Kunden anlegen",
    "customerAdmin.actions.saveCustomer": "Kunde speichern",
    "customerAdmin.actions.cancel": "Abbrechen",
    "customerAdmin.actions.clearFeedback": "Hinweis schliessen",
    "customerAdmin.actions.deactivate": "Deaktivieren",
    "customerAdmin.actions.reactivate": "Reaktivieren",
    "customerAdmin.actions.archive": "Archivieren",
    "customerAdmin.actions.edit": "Bearbeiten",
    "customerAdmin.actions.addContact": "Kontakt erfassen",
    "customerAdmin.actions.exportVCard": "vCard",
    "customerAdmin.actions.createContact": "Kontakt anlegen",
    "customerAdmin.actions.saveContact": "Kontakt speichern",
    "customerAdmin.actions.addAddress": "Adresse verknuepfen",
    "customerAdmin.actions.createAddress": "Adresslink anlegen",
    "customerAdmin.actions.saveAddress": "Adresslink speichern",
    "customerAdmin.actions.refreshHistory": "Historie neu laden",
    "customerAdmin.actions.refreshPortalPrivacy": "Freigabestatus neu laden",
    "customerAdmin.actions.linkHistoryAttachment": "Anhang verknuepfen",
    "customerAdmin.actions.refreshLoginHistory": "Loginhistorie neu laden",
    "customerAdmin.actions.refreshEmployeeBlocks": "Sperren neu laden",
    "customerAdmin.actions.createEmployeeBlock": "Sperre anlegen",
    "customerAdmin.actions.saveEmployeeBlock": "Sperre speichern",
    "customerAdmin.actions.savePortalPrivacy": "Namensfreigabe speichern",
    "customerAdmin.status.active": "Aktiv",
    "customerAdmin.status.inactive": "Inaktiv",
    "customerAdmin.status.archived": "Archiviert",
    "customerAdmin.confirm.archive": "Diesen Kunden archivieren?",
    "customerAdmin.confirm.deactivate": "Diesen Kunden deaktivieren?",
    "customerAdmin.confirm.reactivate": "Diesen Kunden wieder aktiv setzen?",
    "customerAdmin.confirm.contactArchive": "Diesen Kontakt archivieren?",
    "customerAdmin.confirm.addressArchive": "Diesen Adresslink archivieren?",
    "customerAdmin.feedback.created": "Kunde angelegt",
    "customerAdmin.feedback.saved": "Kunde gespeichert",
    "customerAdmin.feedback.archived": "Kunde archiviert",
    "customerAdmin.feedback.deactivated": "Kunde deaktiviert",
    "customerAdmin.feedback.reactivated": "Kunde reaktiviert",
    "customerAdmin.feedback.contactSaved": "Kontakt gespeichert",
    "customerAdmin.feedback.addressSaved": "Adresslink gespeichert",
    "customerAdmin.feedback.exportReady": "Kundenexport erstellt",
    "customerAdmin.feedback.vcardReady": "vCard erstellt",
    "customerAdmin.feedback.documentId": "Dokument-ID",
    "customerAdmin.feedback.scopeSaved": "Mandantenscope gespeichert",
    "customerAdmin.feedback.tokenSaved": "Token aktualisiert und Liste neu geladen.",
    "customerAdmin.feedback.historyAttachmentLinked": "Historienanhang verknuepft",
    "customerAdmin.feedback.documentLinked": "Das Dokument wurde dem Historieneintrag zugeordnet.",
    "customerAdmin.feedback.employeeBlockSaved": "Mitarbeitendensperre gespeichert",
    "customerAdmin.feedback.employeeBlockSavedBody": "Die kundenspezifische Sperre wurde uebernommen.",
    "customerAdmin.feedback.portalPrivacySaved": "Portal-Datenschutz aktualisiert",
    "customerAdmin.feedback.validation": "Eingaben pruefen",
    "customerAdmin.feedback.customerRequired": "Kundennummer und Anzeigename sind Pflichtfelder.",
    "customerAdmin.feedback.contactRequired": "Fuer einen Kontakt wird mindestens der Name benoetigt.",
    "customerAdmin.feedback.addressRequired": "Fuer einen Adresslink wird eine Adress-ID benoetigt.",
    "customerAdmin.feedback.error": "Der Kundenvorgang ist fehlgeschlagen.",
    "customerAdmin.feedback.authRequired": "Bitte ein gueltiges Bearer-Token fuer die Kunden-API hinterlegen.",
    "customerAdmin.feedback.permissionDenied": "Die aktuelle Sitzung darf diese Aktion nicht ausfuehren.",
    "customerAdmin.feedback.notFound": "Der angeforderte Kundendatensatz wurde nicht gefunden.",
    "customerAdmin.feedback.duplicateNumber": "Diese Kundennummer existiert bereits.",
    "customerAdmin.feedback.staleVersion": "Der Datensatz wurde zwischenzeitlich geaendert. Bitte neu laden.",
    "customerAdmin.feedback.duplicateEmail": "Die Kontakt-E-Mail existiert fuer diesen Kunden bereits.",
    "customerAdmin.feedback.primaryConflict": "Es gibt bereits einen Primaerkontakt fuer diesen Kunden.",
    "customerAdmin.feedback.defaultAddressConflict": "Es gibt bereits eine Standardadresse fuer diesen Typ.",
    "customerAdmin.feedback.invalidPortalUser":
      "Die verknuepfte Portal-Benutzer-ID gehoert nicht zum aktuellen Mandanten.",
    "customerAdmin.permission.commercialRead": "Commercial lesen",
    "customerAdmin.permission.commercialWrite": "Commercial pflegen",
    "customerAdmin.commercial.eyebrow": "Commercial Settings",
    "customerAdmin.commercial.title": "Abrechnung, Rechnungsparteien und Preisregeln",
    "customerAdmin.commercial.lead":
      "Diese Bereiche binden direkt an die CRM-Commercial-APIs an und bleiben die finance-lesbare Quelle fuer Preise und Zuschlaege.",
    "customerAdmin.commercial.summary.billingProfile": "Abrechnungsprofil",
    "customerAdmin.commercial.summary.invoiceParties": "Rechnungsparteien",
    "customerAdmin.commercial.summary.rateCards": "Preiskarten",
    "customerAdmin.commercial.summary.selectedRateCard": "Aktive Auswahl",
    "customerAdmin.commercial.summary.missing": "Noch nicht gepflegt",
    "customerAdmin.commercial.billingEyebrow": "Abrechnungsprofil",
    "customerAdmin.commercial.billingTitle": "Zahlung, Steuer und Bankdaten",
    "customerAdmin.commercial.invoiceEyebrow": "Rechnungsparteien",
    "customerAdmin.commercial.invoiceTitle": "Alternative Rechnungsempfaenger",
    "customerAdmin.commercial.invoiceEmpty": "Noch keine Rechnungsparteien hinterlegt.",
    "customerAdmin.commercial.defaultInvoiceParty": "Standard-Rechnungspartei",
    "customerAdmin.commercial.additionalInvoiceParty": "Zusaetzliche Rechnungspartei",
    "customerAdmin.commercial.rateCardsEyebrow": "Preiskarten",
    "customerAdmin.commercial.rateCardsTitle": "Versionierte Preisfenster",
    "customerAdmin.commercial.rateCardsEmpty": "Noch keine Preiskarten hinterlegt.",
    "customerAdmin.commercial.rateLinesEyebrow": "Preiszeilen",
    "customerAdmin.commercial.rateLinesTitle": "Leistungs- und Funktionspreise",
    "customerAdmin.commercial.rateLinesEmpty": "Noch keine Preiszeilen fuer diese Preiskarte vorhanden.",
    "customerAdmin.commercial.surchargesEyebrow": "Zuschlaege",
    "customerAdmin.commercial.surchargesTitle": "Zeit-, Wochen- und Regionszuschlaege",
    "customerAdmin.commercial.surchargesEmpty": "Noch keine Zuschlagsregeln fuer diese Preiskarte vorhanden.",
    "customerAdmin.fields.invoiceEmail": "Rechnungs-E-Mail",
    "customerAdmin.fields.paymentTermsDays": "Zahlungsziel in Tagen",
    "customerAdmin.fields.paymentTermsNote": "Zahlungsbedingung",
    "customerAdmin.fields.taxNumber": "Steuernummer",
    "customerAdmin.fields.vatId": "USt-IdNr.",
    "customerAdmin.fields.contractReference": "Vertragsreferenz",
    "customerAdmin.fields.debtorNumber": "Debitorennummer",
    "customerAdmin.fields.bankAccountHolder": "Kontoinhaber",
    "customerAdmin.fields.bankIban": "IBAN",
    "customerAdmin.fields.bankBic": "BIC",
    "customerAdmin.fields.bankName": "Bankname",
    "customerAdmin.fields.billingNote": "Abrechnungsnotiz",
    "customerAdmin.fields.eInvoiceEnabled": "E-Rechnung aktiviert",
    "customerAdmin.fields.leitwegId": "Leitweg-/Routing-ID",
    "customerAdmin.fields.invoiceLayoutCode": "Rechnungslayout",
    "customerAdmin.fields.shippingMethodCode": "Versandweg",
    "customerAdmin.fields.dunningPolicyCode": "Mahnprofil",
    "customerAdmin.fields.taxExempt": "Steuerbefreit",
    "customerAdmin.fields.taxExemptionReason": "Grund fuer Steuerbefreiung",
    "customerAdmin.fields.companyName": "Firmenname",
    "customerAdmin.fields.contactName": "Ansprechpartner",
    "customerAdmin.fields.invoiceLayoutLookupId": "Layout-Lookup-ID",
    "customerAdmin.fields.note": "Hinweis",
    "customerAdmin.fields.isDefaultInvoiceParty": "Als Standard-Rechnungspartei markieren",
    "customerAdmin.fields.rateKind": "Preisart",
    "customerAdmin.fields.currencyCode": "Waehrung",
    "customerAdmin.fields.effectiveFrom": "Gueltig ab",
    "customerAdmin.fields.effectiveTo": "Gueltig bis",
    "customerAdmin.fields.lineKind": "Zeilenart",
    "customerAdmin.fields.billingUnit": "Abrechnungseinheit",
    "customerAdmin.fields.unitPrice": "Einzelpreis",
    "customerAdmin.fields.minimumQuantity": "Mindestmenge",
    "customerAdmin.fields.functionTypeId": "Funktions-ID",
    "customerAdmin.fields.qualificationTypeId": "Qualifikations-ID",
    "customerAdmin.fields.planningModeCode": "Planungsmodus",
    "customerAdmin.fields.sortOrder": "Sortierung",
    "customerAdmin.fields.surchargeType": "Zuschlagstyp",
    "customerAdmin.fields.weekdayMask": "Wochentagsmaske",
    "customerAdmin.fields.timeFromMinute": "Von Minute",
    "customerAdmin.fields.timeToMinute": "Bis Minute",
    "customerAdmin.fields.regionCode": "Regionscode",
    "customerAdmin.fields.percentValue": "Prozentwert",
    "customerAdmin.fields.fixedAmount": "Fixbetrag",
    "customerAdmin.actions.refreshCommercial": "Commercial neu laden",
    "customerAdmin.actions.saveBillingProfile": "Abrechnungsprofil speichern",
    "customerAdmin.actions.addInvoiceParty": "Rechnungspartei erfassen",
    "customerAdmin.actions.createInvoiceParty": "Rechnungspartei anlegen",
    "customerAdmin.actions.saveInvoiceParty": "Rechnungspartei speichern",
    "customerAdmin.actions.addRateCard": "Preiskarte anlegen",
    "customerAdmin.actions.createRateCard": "Preiskarte speichern",
    "customerAdmin.actions.saveRateCard": "Preiskarte aktualisieren",
    "customerAdmin.actions.addRateLine": "Preiszeile erfassen",
    "customerAdmin.actions.createRateLine": "Preiszeile speichern",
    "customerAdmin.actions.saveRateLine": "Preiszeile aktualisieren",
    "customerAdmin.actions.addSurchargeRule": "Zuschlagsregel erfassen",
    "customerAdmin.actions.createSurchargeRule": "Zuschlagsregel speichern",
    "customerAdmin.actions.saveSurchargeRule": "Zuschlagsregel aktualisieren",
    "customerAdmin.confirm.activeCommercialChange":
      "Diese Aenderung betrifft aktive Commercial-Daten. Wirklich fortfahren?",
    "customerAdmin.confirm.defaultInvoicePartyChange":
      "Diese Rechnungspartei wird als Standard markiert. Wirklich fortfahren?",
    "customerAdmin.feedback.commercialSaved": "Commercial-Einstellung gespeichert",
    "customerAdmin.feedback.invoicePartyRequired":
      "Fuer eine Rechnungspartei werden mindestens Firmenname und Adress-ID benoetigt.",
    "customerAdmin.feedback.invalidInvoiceEmail": "Die angegebene Rechnungs-E-Mail ist ungueltig.",
    "customerAdmin.feedback.invalidPaymentTerms": "Das Zahlungsziel ist ungueltig.",
    "customerAdmin.feedback.taxExemptionReasonRequired":
      "Bei Steuerbefreiung ist ein Grund erforderlich.",
    "customerAdmin.feedback.taxExemptionReasonForbidden":
      "Ein Steuerbefreiungsgrund darf nur bei aktiver Steuerbefreiung gesetzt werden.",
    "customerAdmin.feedback.bankAccountHolderRequired":
      "Bei Bankdaten ist ein Kontoinhaber erforderlich.",
    "customerAdmin.feedback.bankIbanRequired": "Bei Bankdaten ist eine IBAN erforderlich.",
    "customerAdmin.feedback.eInvoiceRequired": "Fuer E-Rechnungsversand muss E-Rechnung aktiviert sein.",
    "customerAdmin.feedback.eInvoiceDispatchMismatch":
      "Aktive E-Rechnung ist nur mit dem Versandweg E-Rechnung zulaessig.",
    "customerAdmin.feedback.leitwegRequired":
      "Fuer E-Rechnungsversand ist eine Leitweg-/Routing-ID erforderlich.",
    "customerAdmin.feedback.leitwegForbidden":
      "Eine Leitweg-/Routing-ID darf nur bei aktiver E-Rechnung gesetzt werden.",
    "customerAdmin.feedback.dispatchEmailRequired":
      "Fuer E-Mail-PDF-Versand ist eine Rechnungs-E-Mail erforderlich.",
    "customerAdmin.feedback.invoiceLayoutIncompatible":
      "Das gewaehlte Rechnungslayout ist mit dem Versandweg nicht kompatibel.",
    "customerAdmin.feedback.defaultInvoicePartyConflict":
      "Es gibt bereits eine Standard-Rechnungspartei fuer diesen Kunden.",
    "customerAdmin.feedback.rateKindRequired": "Fuer eine Preiskarte ist eine Preisart erforderlich.",
    "customerAdmin.feedback.invalidCurrency": "Der Waehrungscode ist ungueltig.",
    "customerAdmin.feedback.rateCardEffectiveFromRequired": "Fuer eine Preiskarte ist ein Startdatum erforderlich.",
    "customerAdmin.feedback.invalidEffectiveWindow": "Das Gueltigkeitsfenster ist ungueltig.",
    "customerAdmin.feedback.rateCardOverlap":
      "Dieses Preisfenster ueberschneidet sich mit einer bestehenden aktiven Preiskarte.",
    "customerAdmin.feedback.rateLineKindRequired": "Fuer eine Preiszeile ist eine Zeilenart erforderlich.",
    "customerAdmin.feedback.invalidBillingUnit": "Die Abrechnungseinheit ist ungueltig.",
    "customerAdmin.feedback.invalidUnitPrice": "Der Einzelpreis ist ungueltig.",
    "customerAdmin.feedback.invalidMinimumQuantity": "Die Mindestmenge ist ungueltig.",
    "customerAdmin.feedback.duplicateRateDimension":
      "Diese Preisdimension existiert bereits auf der gewaehlten Preiskarte.",
    "customerAdmin.feedback.surchargeTypeRequired": "Fuer einen Zuschlag ist ein Typ erforderlich.",
    "customerAdmin.feedback.surchargeEffectiveFromRequired":
      "Fuer einen Zuschlag ist ein Startdatum erforderlich.",
    "customerAdmin.feedback.invalidWeekdayMask":
      "Die Wochentagsmaske muss aus sieben Zeichen mit 0 oder 1 bestehen.",
    "customerAdmin.feedback.invalidTimeRange": "Das Zeitfenster des Zuschlags ist ungueltig.",
    "customerAdmin.feedback.invalidAmountCombination":
      "Es muss genau ein Prozentwert oder ein Fixbetrag gesetzt sein.",
    "customerAdmin.feedback.surchargeOutsideRateCardWindow":
      "Der Zuschlag muss innerhalb des Gueltigkeitsfensters der Preiskarte liegen.",
    "customerAdmin.option.invoiceLayout.standard": "Standard",
    "customerAdmin.option.invoiceLayout.compact": "Kompakt",
    "customerAdmin.option.invoiceLayout.detailed_timesheet": "Mit Leistungsnachweis",
    "customerAdmin.option.shippingMethod.email_pdf": "E-Mail PDF",
    "customerAdmin.option.shippingMethod.portal_download": "Portal Download",
    "customerAdmin.option.shippingMethod.postal_print": "Postversand",
    "customerAdmin.option.shippingMethod.e_invoice": "E-Rechnung",
    "customerAdmin.option.dunningPolicy.disabled": "Deaktiviert",
    "customerAdmin.option.dunningPolicy.standard": "Standard",
    "customerAdmin.option.dunningPolicy.strict": "Streng",
  },
  en: {
    "app.title": "SicherPlan",
    "locale.label": "Language",
    "locale.de": "German",
    "locale.en": "English",
    "theme.toggle.light": "Dark mode",
    "theme.toggle.dark": "Light mode",
    "theme.mode.light": "Light",
    "theme.mode.dark": "Dark",
    "layout.admin.eyebrow": "Vben-oriented shell",
    "layout.admin.title": "Internal area",
    "layout.portal.eyebrow": "Portal structure",
    "layout.portal.title": "External area",
    "brand.adminSubtitle": "Admin and operations control",
    "brand.portalSubtitle": "Released portal views",
    "role.label": "View role",
    "role.platform_admin": "Platform admin",
    "role.tenant_admin": "Tenant admin",
    "role.dispatcher": "Dispatcher / field lead",
    "role.accounting": "Accounting",
    "role.controller_qm": "Controlling / QA",
    "role.customer_user": "Customer portal",
    "role.subcontractor_user": "Subcontractor portal",
    "shell.eyebrow": "SicherPlan shell",
    "shell.title": "Role-based control for security operations",
    "shell.lead":
      "This landing page shows the first web shell with admin and portal paths, now with centralized light/dark tokens and DE/EN localization for later IAM work.",
    "shell.cta.admin": "Open admin area",
    "shell.cta.portal": "Open portal area",
    "shell.stat.roles": "Roles",
    "shell.stat.modules": "Module groups",
    "shell.stat.portals": "Portal paths",
    "module.eyebrow": "Placeholder module",
    "module.note.navigation":
      "Navigation and role visibility are already registered in the shell.",
    "module.note.future":
      "CRUD views, forms, and reporting will follow in later tasks.",
    "module.note.compatibility":
      "The shell stays compatible with later RBAC, theme, and i18n expansion.",
    "route.admin.dashboard.title": "Dashboard",
    "route.admin.dashboard.description":
      "Starting point for internal roles with quick access to core modules.",
    "route.admin.core.title": "Core system",
    "route.admin.core.description":
      "Tenants, branches, numbering ranges, and central settings.",
    "route.admin.platform_services.title": "Platform services",
    "route.admin.platform_services.description":
      "Documents, communication, notices, and integration jobs.",
    "route.admin.customers.title": "Customers",
    "route.admin.customers.description":
      "Master data, contacts, billing rules, and portal releases.",
    "route.admin.recruiting.title": "Recruiting",
    "route.admin.recruiting.description":
      "Review applications, document interview steps, and drive decisions with a clear audit trail.",
    "route.admin.employees.title": "Employees",
    "route.admin.employees.description":
      "Recruiting, personnel file, availability, and qualifications.",
    "route.admin.subcontractors.title": "Subcontractors",
    "route.admin.subcontractors.description":
      "Partner companies, assignment releases, and compliance status.",
    "route.admin.planning.title": "Planning",
    "route.admin.planning.description":
      "Sites, orders, shift plans, validation, and releases.",
    "route.admin.field_execution.title": "Field execution",
    "route.admin.field_execution.description":
      "Watchbook, patrol rounds, time capture, and mobile feedback.",
    "route.admin.finance.title": "Finance",
    "route.admin.finance.description":
      "Actuals, payroll exports, invoices, and partner checks.",
    "route.admin.reporting.title": "Reporting",
    "route.admin.reporting.description":
      "Operational, commercial, and compliance reporting.",
    "route.portal.customer.title": "Customer portal",
    "route.portal.customer.description":
      "Released orders, reports, times, and documents.",
    "route.portal.subcontractor.title": "Subcontractor portal",
    "route.portal.subcontractor.description":
      "Released assignments, workers, and feedback within released scope.",
    "portalCustomer.eyebrow": "Customer access",
    "portalCustomer.title": "Customer portal and scope validation",
    "portalCustomer.lead":
      "This entry point uses the shared IAM session and resolves customer context only from role scopes and the linked customer contact.",
    "portalCustomer.login.tenantCode": "Tenant code",
    "portalCustomer.login.identifier": "Username or email",
    "portalCustomer.login.password": "Password",
    "portalCustomer.login.deviceLabel": "Device label",
    "portalCustomer.actions.login": "Sign in to portal",
    "portalCustomer.actions.refresh": "Reload portal status",
    "portalCustomer.actions.logout": "Sign out",
    "portalCustomer.loading.title": "Validating portal access",
    "portalCustomer.loading.body":
      "The session and linked customer context are being verified against the shared IAM and CRM linkage.",
    "portalCustomer.empty.title": "No released customer context",
    "portalCustomer.empty.body":
      "The current portal account has no usable customer scope or the linkage is incomplete.",
    "portalCustomer.unauthorized.title": "Portal access is not allowed",
    "portalCustomer.unauthorized.body":
      "This account is not allowed to use the customer portal or does not currently hold the required permissions.",
    "portalCustomer.deactivated.title": "Portal access is deactivated",
    "portalCustomer.deactivated.body":
      "The linked customer contact or customer record is inactive or archived.",
    "portalCustomer.summary.title": "Resolved customer context",
    "portalCustomer.summary.customerNumber": "Customer number",
    "portalCustomer.summary.customerName": "Customer name",
    "portalCustomer.summary.contact": "Portal contact",
    "portalCustomer.summary.email": "Email",
    "portalCustomer.summary.function": "Function",
    "portalCustomer.summary.tenant": "Tenant",
    "portalCustomer.summary.scope": "Allowed customer scope",
    "portalCustomer.readOnly.title": "Released portal views only",
    "portalCustomer.readOnly.body":
      "This portal shows only customer-scoped, released, read-only outputs. Source modules that are not implemented yet stay visible as explicit empty-state contracts.",
    "portalCustomer.history.eyebrow": "Customer history",
    "portalCustomer.history.title": "Released history and attachments",
    "portalCustomer.history.lead":
      "The portal timeline shows only customer-scoped history entries with docs-backed attachments from CRM.",
    "portalCustomer.history.empty": "No released history entries are available for this customer yet.",
    "portalCustomer.meta.releasedOnly": "Only released content is shown.",
    "portalCustomer.meta.customerScoped": "Every query remains restricted to the current customer scope.",
    "portalCustomer.meta.personalNamesRestricted":
      "Personal names stay hidden by default until later release rules are implemented.",
    "portalCustomer.meta.sourceModule": "Source module",
    "portalCustomer.meta.docsBacked": "Published outputs will be delivered through the central document service.",
    "portalCustomer.states.loading": "Loading",
    "portalCustomer.states.pending": "Pending",
    "portalCustomer.states.empty": "Empty",
    "portalCustomer.states.ready": "Released",
    "portalCustomer.datasets.orders.eyebrow": "Orders",
    "portalCustomer.datasets.orders.title": "Released orders",
    "portalCustomer.datasets.orders.lead":
      "Customer orders appear here once the planning module exposes released portal read models.",
    "portalCustomer.datasets.orders.pending":
      "No released order data is available from the planning module yet.",
    "portalCustomer.datasets.schedules.eyebrow": "Schedules",
    "portalCustomer.datasets.schedules.title": "Released schedules",
    "portalCustomer.datasets.schedules.lead":
      "Only published customer schedules will appear here once the planning source is connected.",
    "portalCustomer.datasets.schedules.pending":
      "The released schedule portal contract is ready, but the source module is not connected yet.",
    "portalCustomer.datasets.watchbooks.eyebrow": "Watchbook",
    "portalCustomer.datasets.watchbooks.title": "Released watchbook excerpts",
    "portalCustomer.datasets.watchbooks.lead":
      "Watchbook and field events will appear only after the field-execution backbone provides released customer views.",
    "portalCustomer.datasets.watchbooks.pending":
      "No released watchbook events are available for the customer portal yet.",
    "portalCustomer.datasets.timesheets.eyebrow": "Timesheets",
    "portalCustomer.datasets.timesheets.title": "Released timesheets",
    "portalCustomer.datasets.timesheets.lead":
      "Timesheets remain document-backed and will later be published through the finance bridge and docs service.",
    "portalCustomer.datasets.timesheets.pending":
      "Released timesheets are not connected to the portal yet.",
    "portalCustomer.datasets.reports.eyebrow": "Reports",
    "portalCustomer.datasets.reports.title": "Released report and result packages",
    "portalCustomer.datasets.reports.lead":
      "Reports and result documents will be exposed as released packages through reporting and the docs service.",
    "portalCustomer.datasets.reports.pending":
      "No released report packages have been published for this customer yet.",
    "portalCustomer.feedback.authRequired": "Sign in with a valid portal account first.",
    "portalCustomer.feedback.invalidCredentials": "The login credentials are invalid.",
    "portalCustomer.feedback.permissionDenied":
      "The current account does not have permitted customer-portal access.",
    "portalCustomer.feedback.scopeNotResolved":
      "The customer scope for this portal account could not be resolved unambiguously.",
    "portalCustomer.feedback.contactNotLinked":
      "No active customer contact is linked to the current portal account.",
    "portalCustomer.feedback.contactInactive":
      "The linked customer contact is no longer active.",
    "portalCustomer.feedback.customerInactive":
      "The linked customer is no longer active.",
    "portalCustomer.feedback.sessionReady":
      "The portal session was loaded successfully and narrowed to the customer context.",
    "portalCustomer.feedback.loggedOut": "The portal session has been signed out.",
    "portalCustomer.feedback.error":
      "Customer portal access could not be loaded.",
    "recruitingApplicant.eyebrow": "Application",
    "recruitingApplicant.title": "Public applicant form",
    "recruitingApplicant.lead":
      "This form is tenant-scoped, iframe-ready, and stores attachments through the shared docs service.",
    "recruitingApplicant.embed.embedded": "Embedded mode active",
    "recruitingApplicant.embed.standalone": "Standalone mode active",
    "recruitingApplicant.loading.title": "Loading form",
    "recruitingApplicant.loading.body":
      "The tenant-specific applicant-form configuration is being loaded.",
    "recruitingApplicant.error.title": "Applicant form unavailable",
    "recruitingApplicant.success.eyebrow": "Submission received",
    "recruitingApplicant.success.title": "Application submitted",
    "recruitingApplicant.success.body":
      "The application was stored and assigned a reference number.",
    "recruitingApplicant.fields.selectPlaceholder": "Please select",
    "recruitingApplicant.fields.attachments": "Attachments",
    "recruitingApplicant.fields.attachmentsHelp":
      "Up to {count} file(s), each roughly {sizeMb} MB. Allowed types are defined per tenant.",
    "recruitingApplicant.fields.consent":
      "I confirm the GDPR consent for this application.",
    "recruitingApplicant.fields.policyLink": "Privacy notice",
    "recruitingApplicant.fields.policyVersion": "Displayed version: {version}",
    "recruitingApplicant.actions.submit": "Submit application",
    "recruitingApplicant.actions.submitting": "Submitting application",
    "recruitingApplicant.actions.clearFeedback": "Dismiss notice",
    "recruitingApplicant.feedback.submitted": "Application submitted successfully",
    "recruitingApplicant.feedback.tenantNotFound":
      "No applicant form is available for this tenant.",
    "recruitingApplicant.feedback.formDisabled":
      "The applicant form is currently disabled.",
    "recruitingApplicant.feedback.originDenied":
      "This embedding origin is not allowed for the form.",
    "recruitingApplicant.feedback.rateLimited":
      "Too many submissions came from this source. Please try again later.",
    "recruitingApplicant.feedback.consentRequired":
      "GDPR consent must be confirmed.",
    "recruitingApplicant.feedback.policyMismatch":
      "The form version is outdated. Please reload the page.",
    "recruitingApplicant.feedback.fieldRequired":
      "Please complete all required fields.",
    "recruitingApplicant.feedback.invalidEmail":
      "Please provide a valid email address.",
    "recruitingApplicant.feedback.invalidFieldOption":
      "A selected form option is invalid.",
    "recruitingApplicant.feedback.tooManyAttachments":
      "Too many attachments were selected.",
    "recruitingApplicant.feedback.attachmentTypeNotAllowed":
      "At least one file type is not allowed for this form.",
    "recruitingApplicant.feedback.attachmentTooLarge":
      "At least one file is too large for this form.",
    "recruitingApplicant.feedback.duplicateSubmission":
      "This application was already submitted.",
    "recruitingApplicant.feedback.error":
      "The applicant form could not be submitted.",
    "recruitingAdmin.eyebrow": "Recruiting",
    "recruitingAdmin.title": "Applicant review and decision flow",
    "recruitingAdmin.lead":
      "This recruiting page binds directly to the released applicant and workflow APIs and shows status, consent, attachments, and activity history without a local mock source of truth.",
    "recruitingAdmin.permission.read": "Read permission",
    "recruitingAdmin.permission.write": "Write permission",
    "recruitingAdmin.permission.docs": "Document access",
    "recruitingAdmin.permission.missingTitle": "Recruiting permission missing",
    "recruitingAdmin.permission.missingBody":
      "This admin page is only available to roles with recruiting read access.",
    "recruitingAdmin.auth.missingTitle": "Login required",
    "recruitingAdmin.auth.missingBody":
      "Sign in through the system login before applications can be loaded.",
    "recruitingAdmin.scope.label": "Tenant scope",
    "recruitingAdmin.scope.placeholder": "Tenant UUID for platform-admin mode",
    "recruitingAdmin.scope.platformHelp":
      "Platform admins choose the recruiting tenant explicitly and keep it for later calls.",
    "recruitingAdmin.scope.sessionHelp":
      "Tenant admins always work inside the tenant scope of the current session.",
    "recruitingAdmin.scope.missingTitle": "Tenant scope missing",
    "recruitingAdmin.scope.missingBody":
      "Choose a recruiting tenant before loading applications.",
    "recruitingAdmin.list.eyebrow": "Inbox",
    "recruitingAdmin.list.title": "Application list",
    "recruitingAdmin.list.empty": "No applications match the current filters.",
    "recruitingAdmin.detail.eyebrow": "Detail",
    "recruitingAdmin.detail.emptyTitle": "No application selected",
    "recruitingAdmin.detail.emptyEyebrow": "Detail view",
    "recruitingAdmin.detail.emptyBody":
      "Select an application on the left to inspect consent, attachments, and workflow history.",
    "recruitingAdmin.detail.submissionEyebrow": "Submission",
    "recruitingAdmin.detail.submissionTitle": "Application data",
    "recruitingAdmin.summary.applicationNo": "Application number",
    "recruitingAdmin.summary.desiredRole": "Desired role",
    "recruitingAdmin.summary.availability": "Available from",
    "recruitingAdmin.summary.source": "Source",
    "recruitingAdmin.summary.employeeFile": "Employee file",
    "recruitingAdmin.summary.none": "not provided",
    "recruitingAdmin.consent.eyebrow": "Privacy",
    "recruitingAdmin.consent.title": "Consent evidence",
    "recruitingAdmin.consent.granted": "Consent confirmed",
    "recruitingAdmin.consent.timestamp": "Timestamp",
    "recruitingAdmin.consent.policyRef": "Policy reference",
    "recruitingAdmin.consent.policyVersion": "Policy version",
    "recruitingAdmin.consent.origin": "Origin",
    "recruitingAdmin.consent.ip": "IP address",
    "recruitingAdmin.attachments.eyebrow": "Attachments",
    "recruitingAdmin.attachments.title": "Applicant documents",
    "recruitingAdmin.attachments.empty": "No attachments are linked to this application.",
    "recruitingAdmin.notes.eyebrow": "Notes",
    "recruitingAdmin.notes.title": "Review and interview notes",
    "recruitingAdmin.timeline.eyebrow": "Timeline",
    "recruitingAdmin.timeline.title": "Workflow history",
    "recruitingAdmin.timeline.empty": "No workflow events exist yet.",
    "recruitingAdmin.actions.rememberScope": "Remember scope",
    "recruitingAdmin.actions.refresh": "Refresh",
    "recruitingAdmin.actions.search": "Apply filters",
    "recruitingAdmin.actions.clearFeedback": "Dismiss notice",
    "recruitingAdmin.actions.previewAttachment": "Preview",
    "recruitingAdmin.actions.downloadAttachment": "Download",
    "recruitingAdmin.actions.transitionEyebrow": "Status transition",
    "recruitingAdmin.actions.transitionTitle": "Execute next step",
    "recruitingAdmin.actions.applyTransition": "Apply status",
    "recruitingAdmin.actions.addNote": "Save note",
    "recruitingAdmin.fields.fullName": "Name",
    "recruitingAdmin.fields.email": "Email",
    "recruitingAdmin.fields.phone": "Phone",
    "recruitingAdmin.fields.locale": "Locale",
    "recruitingAdmin.fields.message": "Message",
    "recruitingAdmin.fields.activityType": "Activity type",
    "recruitingAdmin.fields.nextStatus": "Next status",
    "recruitingAdmin.fields.note": "Note",
    "recruitingAdmin.fields.decisionReason": "Decision rationale",
    "recruitingAdmin.fields.interviewScheduledAt": "Interview appointment",
    "recruitingAdmin.fields.hiringTargetDate": "Hire date",
    "recruitingAdmin.filters.search": "Search",
    "recruitingAdmin.filters.searchPlaceholder": "Name, email, application number, or role",
    "recruitingAdmin.filters.status": "Status",
    "recruitingAdmin.filters.sourceChannel": "Source",
    "recruitingAdmin.filters.allStatuses": "All statuses",
    "recruitingAdmin.filters.allSources": "All sources",
    "recruitingAdmin.status.submitted": "Submitted",
    "recruitingAdmin.status.in_review": "In review",
    "recruitingAdmin.status.interview_scheduled": "Interview scheduled",
    "recruitingAdmin.status.accepted": "Accepted",
    "recruitingAdmin.status.rejected": "Rejected",
    "recruitingAdmin.status.ready_for_conversion": "Ready for conversion",
    "recruitingAdmin.source.public_form": "Public form",
    "recruitingAdmin.activity.recruiterNote": "Review note",
    "recruitingAdmin.activity.interviewNote": "Interview note",
    "recruitingAdmin.event.status_transition": "Status transition",
    "recruitingAdmin.event.interview_scheduled": "Interview scheduled",
    "recruitingAdmin.event.decision": "Decision",
    "recruitingAdmin.event.reopened": "Reopened",
    "recruitingAdmin.event.ready_for_conversion": "Ready for conversion",
    "recruitingAdmin.event.converted": "Transferred to employee file",
    "recruitingAdmin.event.recruiter_note": "Review note",
    "recruitingAdmin.event.interview_note": "Interview note",
    "recruitingAdmin.feedback.titleSuccess": "Action completed",
    "recruitingAdmin.feedback.titleError": "Action failed",
    "recruitingAdmin.feedback.authRequired":
      "A valid session is required for the recruiting workspace.",
    "recruitingAdmin.feedback.permissionDenied":
      "The current role is not allowed to perform this recruiting action.",
    "recruitingAdmin.feedback.notFound":
      "The requested application or attachment was not found.",
    "recruitingAdmin.feedback.invalidStatus":
      "The requested applicant status is invalid.",
    "recruitingAdmin.feedback.transitionNotAllowed":
      "This step is not allowed for the current applicant status.",
    "recruitingAdmin.feedback.interviewTimeRequired":
      "An interview appointment is required for the interview status.",
    "recruitingAdmin.feedback.decisionReasonRequired":
      "A rationale is required for this decision.",
    "recruitingAdmin.feedback.reopenNoteRequired":
      "A note is required to reopen the application.",
    "recruitingAdmin.feedback.hiringTargetRequired":
      "A target hire date is required before handing the applicant to conversion.",
    "recruitingAdmin.feedback.noteRequired":
      "This note action requires content.",
    "recruitingAdmin.feedback.conversionMissing":
      "The linked employee file could not be loaded.",
    "recruitingAdmin.feedback.documentNotFound":
      "The requested applicant document could not be loaded.",
    "recruitingAdmin.feedback.transitionSaved":
      "The workflow step was saved and recorded in the timeline.",
    "recruitingAdmin.feedback.noteSaved":
      "The recruiting note was saved.",
    "recruitingAdmin.feedback.error":
      "The recruiting action could not be completed.",
    "recruitingAdmin.confirm.accepted":
      "Confirm accepting this applicant? The decision will be recorded.",
    "recruitingAdmin.confirm.rejected":
      "Confirm rejecting this applicant? The decision will be recorded.",
    "recruitingAdmin.common.yes": "Yes",
    "recruitingAdmin.common.no": "No",
    "employeeAdmin.eyebrow": "Employees",
    "employeeAdmin.title": "Employee file and operational maintenance",
    "employeeAdmin.lead":
      "This employee workspace talks directly to the operational HR API, keeps private sections separated, and uses the shared document service for profile photos and supporting files.",
    "employeeAdmin.permission.read": "Read permission",
    "employeeAdmin.permission.write": "Write permission",
    "employeeAdmin.permission.privateRead": "Private HR read",
    "employeeAdmin.permission.missingTitle": "Employee permission missing",
    "employeeAdmin.permission.missingBody":
      "This admin page is only available to roles with employee read access.",
    "employeeAdmin.scope.label": "Tenant scope",
    "employeeAdmin.scope.placeholder": "Tenant UUID for platform-admin mode",
    "employeeAdmin.scope.help":
      "Platform admins may switch the active tenant; tenant admins stay inside the session scope.",
    "employeeAdmin.scope.missingTitle": "Tenant scope missing",
    "employeeAdmin.scope.missingBody":
      "Choose a tenant before loading employee files.",
    "employeeAdmin.list.eyebrow": "List",
    "employeeAdmin.list.title": "Employees",
    "employeeAdmin.list.empty": "No employees match the current filters.",
    "employeeAdmin.detail.eyebrow": "File",
    "employeeAdmin.detail.newTitle": "New employee file",
    "employeeAdmin.detail.emptyTitle": "No employee file selected",
    "employeeAdmin.detail.emptyEyebrow": "Detail view",
    "employeeAdmin.detail.emptyBody":
      "Select an employee file on the left or create a new one.",
    "employeeAdmin.filters.search": "Search",
    "employeeAdmin.filters.searchPlaceholder": "Personnel number, name, or email",
    "employeeAdmin.filters.status": "Status",
    "employeeAdmin.filters.allStatuses": "All statuses",
    "employeeAdmin.filters.includeArchived": "Include archived records",
    "employeeAdmin.status.active": "Active",
    "employeeAdmin.status.inactive": "Inactive",
    "employeeAdmin.status.archived": "Archived",
    "employeeAdmin.fields.personnelNo": "Personnel number",
    "employeeAdmin.fields.firstName": "First name",
    "employeeAdmin.fields.lastName": "Last name",
    "employeeAdmin.fields.preferredName": "Preferred name",
    "employeeAdmin.fields.workEmail": "Work email",
    "employeeAdmin.fields.workPhone": "Work phone",
    "employeeAdmin.fields.mobilePhone": "Mobile phone",
    "employeeAdmin.fields.defaultBranchId": "Default branch",
    "employeeAdmin.fields.defaultMandateId": "Default mandate",
    "employeeAdmin.fields.hireDate": "Hire date",
    "employeeAdmin.fields.terminationDate": "Termination date",
    "employeeAdmin.fields.userId": "User account ID",
    "employeeAdmin.fields.notes": "Operational notes",
    "employeeAdmin.fields.noteType": "Note type",
    "employeeAdmin.fields.noteTitle": "Note title",
    "employeeAdmin.fields.reminderAt": "Reminder date",
    "employeeAdmin.fields.completedAt": "Completed on",
    "employeeAdmin.fields.noteBody": "Content",
    "employeeAdmin.fields.groupCode": "Group code",
    "employeeAdmin.fields.groupName": "Group name",
    "employeeAdmin.fields.groupDescription": "Group description",
    "employeeAdmin.fields.assignGroup": "Assign group",
    "employeeAdmin.fields.validFrom": "Valid from",
    "employeeAdmin.fields.validUntil": "Valid until",
    "employeeAdmin.fields.membershipNotes": "Assignment notes",
    "employeeAdmin.summary.branch": "Branch",
    "employeeAdmin.summary.mandate": "Mandate",
    "employeeAdmin.summary.currentAddress": "Current address",
    "employeeAdmin.summary.groups": "Groups",
    "employeeAdmin.summary.none": "Not provided",
    "employeeAdmin.photo.eyebrow": "Profile photo",
    "employeeAdmin.photo.title": "Photo and preview",
    "employeeAdmin.photo.alt": "Profile photo of the employee",
    "employeeAdmin.photo.empty": "No profile photo is stored yet",
    "employeeAdmin.photo.help": "The photo is versioned through the shared document service.",
    "employeeAdmin.notes.eyebrow": "Notes",
    "employeeAdmin.notes.title": "Reminders and positive activity",
    "employeeAdmin.notes.empty": "No operational notes are stored yet.",
    "employeeAdmin.groups.eyebrow": "Groups",
    "employeeAdmin.groups.title": "Groups and assignments",
    "employeeAdmin.groups.empty": "No group assignments exist yet.",
    "employeeAdmin.groups.selectPlaceholder": "Select a group",
    "employeeAdmin.addresses.eyebrow": "Addresses",
    "employeeAdmin.addresses.title": "Current address history",
    "employeeAdmin.addresses.empty": "No released address history is available.",
    "employeeAdmin.documents.eyebrow": "Documents",
    "employeeAdmin.documents.title": "Files and evidence",
    "employeeAdmin.documents.empty": "No employee-linked documents are available.",
    "employeeAdmin.noteType.operational_note": "Operational note",
    "employeeAdmin.noteType.positive_activity": "Positive activity",
    "employeeAdmin.noteType.reminder": "Reminder",
    "employeeAdmin.actions.rememberScope": "Remember scope",
    "employeeAdmin.actions.refresh": "Reload",
    "employeeAdmin.actions.search": "Search",
    "employeeAdmin.actions.clearFeedback": "Dismiss message",
    "employeeAdmin.actions.newEmployee": "Create employee file",
    "employeeAdmin.actions.createEmployee": "Create employee",
    "employeeAdmin.actions.saveEmployee": "Save file",
    "employeeAdmin.actions.reset": "Reset form",
    "employeeAdmin.actions.uploadPhoto": "Upload photo",
    "employeeAdmin.actions.downloadPhoto": "Download photo",
    "employeeAdmin.actions.createNote": "Create note",
    "employeeAdmin.actions.saveNote": "Save note",
    "employeeAdmin.actions.resetNote": "Clear note form",
    "employeeAdmin.actions.createGroup": "Create group",
    "employeeAdmin.actions.saveGroup": "Save group",
    "employeeAdmin.actions.resetGroup": "Clear group form",
    "employeeAdmin.actions.assignGroup": "Assign group",
    "employeeAdmin.actions.saveMembership": "Save assignment",
    "employeeAdmin.actions.resetMembership": "Clear assignment",
    "employeeAdmin.actions.exportEmployees": "Run export",
    "employeeAdmin.actions.loadImportFile": "Load CSV",
    "employeeAdmin.actions.resetImportTemplate": "Use template",
    "employeeAdmin.actions.importDryRun": "Validate import",
    "employeeAdmin.actions.importExecute": "Run import",
    "employeeAdmin.actions.createAccessUser": "Create app user",
    "employeeAdmin.actions.attachAccessUser": "Attach existing user",
    "employeeAdmin.actions.detachAccessUser": "Detach access",
    "employeeAdmin.actions.reconcileAccessUser": "Reconcile access",
    "employeeAdmin.import.eyebrow": "Import / Export",
    "employeeAdmin.import.title": "Bulk onboarding and operational exports",
    "employeeAdmin.import.csvLabel": "CSV content",
    "employeeAdmin.import.continueOnError": "Continue with later rows when a row fails",
    "employeeAdmin.import.dryRunSummary": "Validation finished: {total} rows, {invalid} invalid.",
    "employeeAdmin.import.executeSummary": "Import finished: {total} rows, {created} created, {updated} updated.",
    "employeeAdmin.import.exportSummary": "Export ready: {rows} rows, document {documentId}.",
    "employeeAdmin.access.eyebrow": "App access",
    "employeeAdmin.access.title": "IAM link for employee app access",
    "employeeAdmin.access.user": "Username",
    "employeeAdmin.access.email": "Email",
    "employeeAdmin.access.enabled": "Access enabled",
    "employeeAdmin.access.enabledYes": "Yes",
    "employeeAdmin.access.enabledNo": "No",
    "employeeAdmin.access.createUsername": "New username",
    "employeeAdmin.access.createEmail": "New email",
    "employeeAdmin.access.createPassword": "Initial password",
    "employeeAdmin.access.attachUserId": "Existing user ID",
    "employeeAdmin.access.attachUsername": "Existing username",
    "employeeAdmin.access.attachEmail": "Existing email",
    "employeeAdmin.feedback.titleError": "Action failed",
    "employeeAdmin.feedback.titleSuccess": "Action completed",
    "employeeAdmin.feedback.authRequired":
      "A valid session is required for the employee workspace.",
    "employeeAdmin.feedback.permissionDenied":
      "The current role is not allowed to perform this employee action.",
    "employeeAdmin.feedback.notFound":
      "The requested employee file or assignment was not found.",
    "employeeAdmin.feedback.duplicatePersonnelNo":
      "This personnel number already exists in the tenant.",
    "employeeAdmin.feedback.duplicateGroupCode":
      "This group code is already used in the tenant.",
    "employeeAdmin.feedback.staleVersion":
      "The record changed in the meantime. Reload and try again.",
    "employeeAdmin.feedback.addressOverlap":
      "The address history contains an overlapping validity window.",
    "employeeAdmin.feedback.reminderDateRequired":
      "Reminder notes require a reminder date.",
    "employeeAdmin.feedback.invalidNoteType":
      "The selected note type is not allowed.",
    "employeeAdmin.feedback.photoUploadFailed":
      "The profile photo could not be stored.",
    "employeeAdmin.feedback.invalidImportCsv":
      "The import file is empty or unreadable.",
    "employeeAdmin.feedback.invalidImportHeaders":
      "The import file does not match the expected column layout.",
    "employeeAdmin.feedback.accessUsernameTaken":
      "The username is already taken in the current tenant.",
    "employeeAdmin.feedback.accessEmailTaken":
      "The email address is already taken in the current tenant.",
    "employeeAdmin.feedback.accessAmbiguousMatch":
      "Exactly one user lookup field must be filled for attachment.",
    "employeeAdmin.feedback.accessRoleMissing":
      "The employee access role is missing from the IAM catalog.",
    "employeeAdmin.feedback.employeeSaved":
      "The employee file was saved.",
    "employeeAdmin.feedback.noteSaved":
      "The employee note was saved.",
    "employeeAdmin.feedback.groupSaved":
      "The employee group was saved.",
    "employeeAdmin.feedback.membershipSaved":
      "The group assignment was saved.",
    "employeeAdmin.feedback.photoSaved":
      "The profile photo was updated successfully.",
    "employeeAdmin.feedback.importDryRunReady":
      "The import preview is ready.",
    "employeeAdmin.feedback.importExecuted":
      "The employee import was executed.",
    "employeeAdmin.feedback.exportReady":
      "The employee export was generated.",
    "employeeAdmin.feedback.accessLinked":
      "Employee app access was linked.",
    "employeeAdmin.feedback.accessDetached":
      "Employee app access was detached.",
    "employeeAdmin.feedback.accessReconciled":
      "The IAM link was reconciled.",
    "employeeAdmin.feedback.error":
      "The employee action could not be completed.",
    "api.errors.platform.internal":
      "An internal platform error has occurred.",
    "coreAdmin.breadcrumb": "Admin / Core system / Tenant administration",
    "coreAdmin.eyebrow": "Core administration",
    "coreAdmin.title": "Tenant backbone and core control",
    "coreAdmin.lead":
      "This page binds directly to the core admin APIs and manages tenants, branches, mandates, and settings without a local mock source of truth.",
    "coreAdmin.permission.ready": "RBAC-ready route",
    "coreAdmin.permission.label": "Permission key",
    "coreAdmin.scope.label": "Tenant scope",
    "coreAdmin.scope.placeholder": "Tenant UUID for tenant-admin mode",
    "coreAdmin.scope.help":
      "In the temporary mock-auth mode this UUID is sent to the backend as X-Tenant-Id.",
    "coreAdmin.scope.platformHint":
      "Platform admins see the cross-tenant list. The current tenant scope is remembered for later tenant-admin switching.",
    "coreAdmin.scope.emptyTitle": "Tenant scope missing",
    "coreAdmin.scope.emptyBody":
      "Tenant admins need a remembered tenant UUID before list and detail requests can load.",
    "coreAdmin.scope.remembered": "Remembered scope",
    "coreAdmin.scope.none": "none",
    "coreAdmin.actions.refresh": "Refresh",
    "coreAdmin.actions.loadScopedTenant": "Load scope",
    "coreAdmin.actions.clearFeedback": "Dismiss notice",
    "coreAdmin.actions.createTenant": "Create tenant",
    "coreAdmin.actions.saveTenant": "Save tenant",
    "coreAdmin.actions.activate": "Activate",
    "coreAdmin.actions.deactivate": "Deactivate",
    "coreAdmin.actions.archive": "Archive",
    "coreAdmin.actions.reactivate": "Reactivate",
    "coreAdmin.actions.edit": "Edit",
    "coreAdmin.actions.cancel": "Cancel",
    "coreAdmin.actions.createBranch": "Create branch",
    "coreAdmin.actions.saveBranch": "Save branch",
    "coreAdmin.actions.createMandate": "Create mandate",
    "coreAdmin.actions.saveMandate": "Save mandate",
    "coreAdmin.actions.createSetting": "Create setting",
    "coreAdmin.actions.saveSetting": "Save setting",
    "coreAdmin.tenants.eyebrow": "Tenant overview",
    "coreAdmin.tenants.title": "Tenants",
    "coreAdmin.tenants.filterPlaceholder": "Filter by code or name",
    "coreAdmin.tenants.empty": "No tenants exist yet.",
    "coreAdmin.tenants.scopeOnly":
      "In tenant-admin mode only the scoped tenant is loaded.",
    "coreAdmin.onboarding.eyebrow": "Onboarding",
    "coreAdmin.onboarding.title": "Create a new tenant with baseline records",
    "coreAdmin.detail.eyebrow": "Detail and maintenance",
    "coreAdmin.detail.emptyTitle": "No tenant selected",
    "coreAdmin.detail.emptyState":
      "Select a tenant on the left to maintain tenant data, branches, mandates, and settings.",
    "coreAdmin.lifecycle.title": "Lifecycle and archive state",
    "coreAdmin.lifecycle.archivedHint":
      "Archived tenants remain explicit historical records and cannot be reactivated through the current backend contract.",
    "coreAdmin.branches.eyebrow": "Branches",
    "coreAdmin.branches.title": "Branch maintenance",
    "coreAdmin.branches.empty": "No branches exist yet.",
    "coreAdmin.mandates.eyebrow": "Mandates",
    "coreAdmin.mandates.title": "Mandate maintenance",
    "coreAdmin.mandates.empty": "No mandates exist yet.",
    "coreAdmin.settings.eyebrow": "Tenant settings",
    "coreAdmin.settings.title": "Safe settings editor",
    "coreAdmin.settings.empty": "No settings exist yet.",
    "coreAdmin.settings.version": "Version",
    "coreAdmin.fields.tenantCode": "Tenant code",
    "coreAdmin.fields.tenantName": "Tenant name",
    "coreAdmin.fields.legalName": "Legal name",
    "coreAdmin.fields.defaultLocale": "Default locale",
    "coreAdmin.fields.defaultCurrency": "Default currency",
    "coreAdmin.fields.timezone": "Timezone",
    "coreAdmin.fields.branch": "Branch",
    "coreAdmin.fields.branchPlaceholder": "Select branch",
    "coreAdmin.fields.branchCode": "Branch code",
    "coreAdmin.fields.branchName": "Branch name",
    "coreAdmin.fields.branchEmail": "Contact email",
    "coreAdmin.fields.branchPhone": "Contact phone",
    "coreAdmin.fields.mandateCode": "Mandate code",
    "coreAdmin.fields.mandateName": "Mandate name",
    "coreAdmin.fields.externalRef": "External reference",
    "coreAdmin.fields.notes": "Notes",
    "coreAdmin.fields.settingKey": "Setting key",
    "coreAdmin.fields.settingValue": "Initial setting value (JSON)",
    "coreAdmin.fields.settingValueJson": "JSON value",
    "coreAdmin.status.active": "Active",
    "coreAdmin.status.inactive": "Inactive",
    "coreAdmin.status.archived": "Archived",
    "coreAdmin.feedback.success": "Success",
    "coreAdmin.feedback.error": "Error",
    "coreAdmin.feedback.info": "Info",
    "coreAdmin.feedback.unexpected":
      "The core administration page could not complete the action.",
    "coreAdmin.feedback.invalidJson":
      "Please provide a valid JSON object for settings.",
    "coreAdmin.feedback.tenantCreated": "Tenant and baseline records were created.",
    "coreAdmin.feedback.tenantSaved": "Tenant master data was saved.",
    "coreAdmin.feedback.tenantStatusSaved": "Tenant lifecycle state was updated.",
    "coreAdmin.feedback.branchSaved": "Branch was saved.",
    "coreAdmin.feedback.branchStatusSaved": "Branch lifecycle state was updated.",
    "coreAdmin.feedback.mandateSaved": "Mandate was saved.",
    "coreAdmin.feedback.mandateStatusSaved": "Mandate lifecycle state was updated.",
    "coreAdmin.feedback.settingSaved": "Setting was saved.",
    "coreAdmin.feedback.settingStatusSaved": "Setting lifecycle state was updated.",
    "coreAdmin.feedback.scopeRemembered":
      "The tenant scope was remembered for tenant-admin mode.",
    "coreAdmin.api.errors.authorization.forbidden":
      "This role is not allowed to perform the requested core administration action.",
    "coreAdmin.api.errors.tenant.not_found": "Tenant not found.",
    "coreAdmin.api.errors.branch.not_found": "Branch not found.",
    "coreAdmin.api.errors.mandate.not_found": "Mandate not found.",
    "coreAdmin.api.errors.setting.not_found": "Tenant setting not found.",
    "coreAdmin.api.errors.tenant.duplicate_code":
      "The tenant code already exists.",
    "coreAdmin.api.errors.branch.duplicate_code":
      "The branch code already exists in this tenant.",
    "coreAdmin.api.errors.mandate.duplicate_code":
      "The mandate code already exists in this tenant.",
    "coreAdmin.api.errors.setting.duplicate_key":
      "This setting key already exists.",
    "coreAdmin.api.errors.setting.stale_version":
      "The setting changed in the meantime. Refresh and save again.",
    "coreAdmin.api.errors.mandate.invalid_branch_scope":
      "The selected branch does not belong to this tenant.",
    "coreAdmin.api.errors.lifecycle.archived_record":
      "Archived records remain archived and cannot be reactivated through this path.",
    "coreAdmin.api.errors.conflict.integrity":
      "The change violates a core backbone integrity rule.",
    "noticeAdmin.eyebrow": "Platform services / notices",
    "noticeAdmin.title": "Notices, audiences, and acknowledgements",
    "noticeAdmin.lead":
      "This minimal view binds to the notice APIs: create a draft, publish it, and check the current user's feed.",
    "noticeAdmin.scope.label": "Tenant scope",
    "noticeAdmin.scope.placeholder": "Tenant UUID for notice APIs",
    "noticeAdmin.scope.action": "Remember scope",
    "noticeAdmin.scope.missingTitle": "Tenant scope missing",
    "noticeAdmin.scope.missingBody":
      "The notice flows need a tenant UUID so admin and feed requests remain tenant-safe.",
    "noticeAdmin.form.eyebrow": "Notice draft",
    "noticeAdmin.form.title": "Create a new notice",
    "noticeAdmin.list.eyebrow": "Admin list",
    "noticeAdmin.list.title": "Draft and published notices",
    "noticeAdmin.list.empty": "No notices exist for this tenant yet.",
    "noticeAdmin.feed.eyebrow": "My feed",
    "noticeAdmin.feed.title": "Visible notices for the current role",
    "noticeAdmin.feed.empty": "No notice is currently visible for this role.",
    "noticeAdmin.feed.acknowledged": "Acknowledged",
    "noticeAdmin.fields.title": "Title",
    "noticeAdmin.fields.summary": "Summary",
    "noticeAdmin.fields.body": "Body",
    "noticeAdmin.fields.audienceRole": "Audience role",
    "noticeAdmin.fields.mandatory": "Acknowledgement required",
    "noticeAdmin.actions.create": "Save draft",
    "noticeAdmin.actions.publish": "Publish",
    "noticeAdmin.actions.refresh": "Refresh",
    "noticeAdmin.actions.acknowledge": "Acknowledge",
    "noticeAdmin.feedback.created": "Notice created",
    "noticeAdmin.feedback.published": "Notice published",
    "noticeAdmin.feedback.acknowledged": "Notice acknowledged",
    "noticeAdmin.feedback.error": "The notice action failed.",
    "customerAdmin.eyebrow": "Customer management",
    "customerAdmin.title": "Customer master, contacts, and address links",
    "customerAdmin.lead":
      "This first CRM workspace follows the Vben-style list/detail pattern for customer records, contacts, and reusable-address links.",
    "customerAdmin.permission.read": "Read access",
    "customerAdmin.permission.write": "Write access",
    "customerAdmin.permission.missingTitle": "No CRM permission",
    "customerAdmin.permission.missingBody":
      "The current role is not allowed to open this customer workspace. Backend permissions remain authoritative.",
    "customerAdmin.scope.label": "Tenant scope",
    "customerAdmin.scope.placeholder": "Enter tenant UUID",
    "customerAdmin.scope.missingTitle": "Scope or session missing",
    "customerAdmin.scope.missingBody":
      "The customer API currently needs both a tenant scope and a valid bearer token.",
    "customerAdmin.token.label": "Bearer token",
    "customerAdmin.token.placeholder": "Access token for the backend API",
    "customerAdmin.token.help":
      "The shell has no login screen yet. Until `US-9-T1`, the token stays a developer/admin input.",
    "customerAdmin.list.eyebrow": "Customer list",
    "customerAdmin.list.title": "Search and select",
    "customerAdmin.list.empty": "No customers match the current filters.",
    "customerAdmin.detail.eyebrow": "Customer detail",
    "customerAdmin.detail.emptyTitle": "No customer selected yet",
    "customerAdmin.detail.emptyBody": "Select a customer from the left or start a new record.",
    "customerAdmin.detail.newTitle": "Create a new customer",
    "customerAdmin.form.generalEyebrow": "Master data",
    "customerAdmin.form.generalTitle": "General customer data",
    "customerAdmin.filters.search": "Search",
    "customerAdmin.filters.searchPlaceholder": "Number or name",
    "customerAdmin.filters.status": "Status filter",
    "customerAdmin.filters.allStatuses": "All statuses",
    "customerAdmin.filters.includeArchived": "Include archived customers",
    "customerAdmin.lifecycle.title": "Lifecycle controls",
    "customerAdmin.lifecycle.help": "Archived customers are preserved and cannot currently be reactivated.",
    "customerAdmin.summary.primaryContact": "Primary contact",
    "customerAdmin.summary.defaultBranch": "Default branch",
    "customerAdmin.summary.defaultMandate": "Default mandate",
    "customerAdmin.summary.classification": "Classification",
    "customerAdmin.summary.none": "Not set",
    "customerAdmin.contacts.eyebrow": "Contacts",
    "customerAdmin.contacts.title": "Contact maintenance",
    "customerAdmin.contacts.empty": "No contacts have been added yet.",
    "customerAdmin.contacts.primaryBadge": "Primary contact",
    "customerAdmin.contacts.standardBadge": "Contact",
    "customerAdmin.history.eyebrow": "History",
    "customerAdmin.history.title": "Readable change history",
    "customerAdmin.history.empty": "No business-readable history exists for this customer yet.",
    "customerAdmin.loginHistory.eyebrow": "Portal logins",
    "customerAdmin.loginHistory.title": "Filtered customer login history",
    "customerAdmin.loginHistory.empty": "No visible portal login events exist for this customer yet.",
    "customerAdmin.privacy.eyebrow": "Portal privacy",
    "customerAdmin.privacy.title": "Personal-name release",
    "customerAdmin.privacy.help":
      "Personal names stay hidden by default in the customer portal. Any release is narrow, customer-specific, and auditable.",
    "customerAdmin.privacy.lastReleasedAt": "Last released at",
    "customerAdmin.privacy.lastReleasedBy": "Last released by",
    "customerAdmin.employeeBlocks.eyebrow": "Employee blocks",
    "customerAdmin.employeeBlocks.title": "Customer-specific employee blocks",
    "customerAdmin.employeeBlocks.empty": "No customer employee blocks have been recorded yet.",
    "customerAdmin.employeeBlocks.capability.pendingEmployees":
      "The employee directory arrives in Sprint 4. Until then this control remains limited to direct employee-ID references.",
    "customerAdmin.addresses.eyebrow": "Addresses",
    "customerAdmin.addresses.title": "Address links",
    "customerAdmin.addresses.empty": "No addresses linked yet.",
    "customerAdmin.addresses.defaultBadge": "Default address",
    "customerAdmin.addresses.linkBadge": "Address link",
    "customerAdmin.addressType.registered": "Registered office",
    "customerAdmin.addressType.billing": "Billing",
    "customerAdmin.addressType.mailing": "Mailing",
    "customerAdmin.addressType.service": "Service location",
    "customerAdmin.fields.customerNumber": "Customer number",
    "customerAdmin.fields.name": "Display name",
    "customerAdmin.fields.legalName": "Legal name",
    "customerAdmin.fields.externalRef": "External reference",
    "customerAdmin.fields.legalFormLookupId": "Legal-form lookup ID",
    "customerAdmin.fields.classificationLookupId": "Classification lookup ID",
    "customerAdmin.fields.rankingLookupId": "Ranking lookup ID",
    "customerAdmin.fields.customerStatusLookupId": "Customer-status lookup ID",
    "customerAdmin.fields.defaultBranchId": "Default branch ID",
    "customerAdmin.fields.defaultMandateId": "Default mandate ID",
    "customerAdmin.fields.notes": "Notes",
    "customerAdmin.fields.fullName": "Full name",
    "customerAdmin.fields.contactTitle": "Title",
    "customerAdmin.fields.functionLabel": "Function",
    "customerAdmin.fields.email": "Email",
    "customerAdmin.fields.phone": "Phone",
    "customerAdmin.fields.mobile": "Mobile",
    "customerAdmin.fields.userId": "Portal user ID",
    "customerAdmin.fields.isPrimaryContact": "Mark as primary contact",
    "customerAdmin.fields.isBillingContact": "Mark as billing contact",
    "customerAdmin.fields.addressId": "Address ID",
    "customerAdmin.fields.addressType": "Address type",
    "customerAdmin.fields.historyEntry": "History entry",
    "customerAdmin.fields.documentId": "Document ID",
    "customerAdmin.fields.personNamesReleased": "Release personal names in portal",
    "customerAdmin.fields.employeeId": "Employee ID",
    "customerAdmin.fields.reason": "Reason",
    "customerAdmin.fields.label": "Label",
    "customerAdmin.fields.isDefault": "Mark as default address",
    "customerAdmin.actions.rememberScope": "Save scope",
    "customerAdmin.actions.refresh": "Refresh",
    "customerAdmin.actions.search": "Search",
    "customerAdmin.actions.exportCustomers": "CSV export",
    "customerAdmin.actions.newCustomer": "New customer",
    "customerAdmin.actions.createCustomer": "Create customer",
    "customerAdmin.actions.saveCustomer": "Save customer",
    "customerAdmin.actions.cancel": "Cancel",
    "customerAdmin.actions.clearFeedback": "Dismiss notice",
    "customerAdmin.actions.deactivate": "Deactivate",
    "customerAdmin.actions.reactivate": "Reactivate",
    "customerAdmin.actions.archive": "Archive",
    "customerAdmin.actions.edit": "Edit",
    "customerAdmin.actions.addContact": "Add contact",
    "customerAdmin.actions.exportVCard": "vCard",
    "customerAdmin.actions.createContact": "Create contact",
    "customerAdmin.actions.saveContact": "Save contact",
    "customerAdmin.actions.addAddress": "Link address",
    "customerAdmin.actions.createAddress": "Create address link",
    "customerAdmin.actions.saveAddress": "Save address link",
    "customerAdmin.actions.refreshHistory": "Reload history",
    "customerAdmin.actions.refreshPortalPrivacy": "Reload privacy release",
    "customerAdmin.actions.linkHistoryAttachment": "Link attachment",
    "customerAdmin.actions.refreshLoginHistory": "Reload login history",
    "customerAdmin.actions.refreshEmployeeBlocks": "Reload blocks",
    "customerAdmin.actions.createEmployeeBlock": "Create block",
    "customerAdmin.actions.saveEmployeeBlock": "Save block",
    "customerAdmin.actions.savePortalPrivacy": "Save name release",
    "customerAdmin.status.active": "Active",
    "customerAdmin.status.inactive": "Inactive",
    "customerAdmin.status.archived": "Archived",
    "customerAdmin.confirm.archive": "Archive this customer?",
    "customerAdmin.confirm.deactivate": "Deactivate this customer?",
    "customerAdmin.confirm.reactivate": "Set this customer back to active?",
    "customerAdmin.confirm.contactArchive": "Archive this contact?",
    "customerAdmin.confirm.addressArchive": "Archive this address link?",
    "customerAdmin.feedback.created": "Customer created",
    "customerAdmin.feedback.saved": "Customer saved",
    "customerAdmin.feedback.archived": "Customer archived",
    "customerAdmin.feedback.deactivated": "Customer deactivated",
    "customerAdmin.feedback.reactivated": "Customer reactivated",
    "customerAdmin.feedback.contactSaved": "Contact saved",
    "customerAdmin.feedback.addressSaved": "Address link saved",
    "customerAdmin.feedback.exportReady": "Customer export created",
    "customerAdmin.feedback.vcardReady": "vCard created",
    "customerAdmin.feedback.documentId": "Document ID",
    "customerAdmin.feedback.scopeSaved": "Tenant scope saved",
    "customerAdmin.feedback.tokenSaved": "Token updated and list reloaded.",
    "customerAdmin.feedback.historyAttachmentLinked": "History attachment linked",
    "customerAdmin.feedback.documentLinked": "The document was linked to the selected history entry.",
    "customerAdmin.feedback.employeeBlockSaved": "Employee block saved",
    "customerAdmin.feedback.employeeBlockSavedBody": "The customer-specific employee block was stored.",
    "customerAdmin.feedback.portalPrivacySaved": "Portal privacy updated",
    "customerAdmin.feedback.validation": "Check input",
    "customerAdmin.feedback.customerRequired": "Customer number and display name are required.",
    "customerAdmin.feedback.contactRequired": "A contact needs at least a name.",
    "customerAdmin.feedback.addressRequired": "An address link needs an address ID.",
    "customerAdmin.feedback.error": "The customer action failed.",
    "customerAdmin.feedback.authRequired": "Please provide a valid bearer token for the customer API.",
    "customerAdmin.feedback.permissionDenied": "The current session is not allowed to perform this action.",
    "customerAdmin.feedback.notFound": "The requested customer record was not found.",
    "customerAdmin.feedback.duplicateNumber": "This customer number already exists.",
    "customerAdmin.feedback.staleVersion": "The record changed in the meantime. Please reload.",
    "customerAdmin.feedback.duplicateEmail": "That contact email already exists for this customer.",
    "customerAdmin.feedback.primaryConflict": "A primary contact already exists for this customer.",
    "customerAdmin.feedback.defaultAddressConflict": "A default address already exists for this type.",
    "customerAdmin.feedback.invalidPortalUser":
      "The linked portal user ID does not belong to the current tenant.",
    "customerAdmin.permission.commercialRead": "Commercial read",
    "customerAdmin.permission.commercialWrite": "Commercial write",
    "customerAdmin.commercial.eyebrow": "Commercial settings",
    "customerAdmin.commercial.title": "Billing, invoice parties, and pricing rules",
    "customerAdmin.commercial.lead":
      "These sections bind directly to the CRM commercial APIs and stay the finance-readable source of truth for rates and surcharges.",
    "customerAdmin.commercial.summary.billingProfile": "Billing profile",
    "customerAdmin.commercial.summary.invoiceParties": "Invoice parties",
    "customerAdmin.commercial.summary.rateCards": "Rate cards",
    "customerAdmin.commercial.summary.selectedRateCard": "Current selection",
    "customerAdmin.commercial.summary.missing": "Not configured yet",
    "customerAdmin.commercial.billingEyebrow": "Billing profile",
    "customerAdmin.commercial.billingTitle": "Payment, tax, and bank data",
    "customerAdmin.commercial.invoiceEyebrow": "Invoice parties",
    "customerAdmin.commercial.invoiceTitle": "Alternative invoice recipients",
    "customerAdmin.commercial.invoiceEmpty": "No invoice parties have been added yet.",
    "customerAdmin.commercial.defaultInvoiceParty": "Default invoice party",
    "customerAdmin.commercial.additionalInvoiceParty": "Additional invoice party",
    "customerAdmin.commercial.rateCardsEyebrow": "Rate cards",
    "customerAdmin.commercial.rateCardsTitle": "Versioned pricing windows",
    "customerAdmin.commercial.rateCardsEmpty": "No rate cards configured yet.",
    "customerAdmin.commercial.rateLinesEyebrow": "Rate lines",
    "customerAdmin.commercial.rateLinesTitle": "Service and function-based prices",
    "customerAdmin.commercial.rateLinesEmpty": "No rate lines exist for this rate card yet.",
    "customerAdmin.commercial.surchargesEyebrow": "Surcharges",
    "customerAdmin.commercial.surchargesTitle": "Time, weekday, and region surcharges",
    "customerAdmin.commercial.surchargesEmpty": "No surcharge rules exist for this rate card yet.",
    "customerAdmin.fields.invoiceEmail": "Invoice email",
    "customerAdmin.fields.paymentTermsDays": "Payment terms in days",
    "customerAdmin.fields.paymentTermsNote": "Payment note",
    "customerAdmin.fields.taxNumber": "Tax number",
    "customerAdmin.fields.vatId": "VAT ID",
    "customerAdmin.fields.contractReference": "Contract reference",
    "customerAdmin.fields.debtorNumber": "Debtor number",
    "customerAdmin.fields.bankAccountHolder": "Account holder",
    "customerAdmin.fields.bankIban": "IBAN",
    "customerAdmin.fields.bankBic": "BIC",
    "customerAdmin.fields.bankName": "Bank name",
    "customerAdmin.fields.billingNote": "Billing note",
    "customerAdmin.fields.eInvoiceEnabled": "E-invoicing enabled",
    "customerAdmin.fields.leitwegId": "Leitweg/routing ID",
    "customerAdmin.fields.invoiceLayoutCode": "Invoice layout",
    "customerAdmin.fields.shippingMethodCode": "Dispatch method",
    "customerAdmin.fields.dunningPolicyCode": "Dunning policy",
    "customerAdmin.fields.taxExempt": "Tax exempt",
    "customerAdmin.fields.taxExemptionReason": "Tax-exemption reason",
    "customerAdmin.fields.companyName": "Company name",
    "customerAdmin.fields.contactName": "Contact name",
    "customerAdmin.fields.invoiceLayoutLookupId": "Invoice-layout lookup ID",
    "customerAdmin.fields.note": "Note",
    "customerAdmin.fields.isDefaultInvoiceParty": "Mark as default invoice party",
    "customerAdmin.fields.rateKind": "Rate kind",
    "customerAdmin.fields.currencyCode": "Currency",
    "customerAdmin.fields.effectiveFrom": "Effective from",
    "customerAdmin.fields.effectiveTo": "Effective to",
    "customerAdmin.fields.lineKind": "Line kind",
    "customerAdmin.fields.billingUnit": "Billing unit",
    "customerAdmin.fields.unitPrice": "Unit price",
    "customerAdmin.fields.minimumQuantity": "Minimum quantity",
    "customerAdmin.fields.functionTypeId": "Function ID",
    "customerAdmin.fields.qualificationTypeId": "Qualification ID",
    "customerAdmin.fields.planningModeCode": "Planning mode",
    "customerAdmin.fields.sortOrder": "Sort order",
    "customerAdmin.fields.surchargeType": "Surcharge type",
    "customerAdmin.fields.weekdayMask": "Weekday mask",
    "customerAdmin.fields.timeFromMinute": "From minute",
    "customerAdmin.fields.timeToMinute": "To minute",
    "customerAdmin.fields.regionCode": "Region code",
    "customerAdmin.fields.percentValue": "Percent value",
    "customerAdmin.fields.fixedAmount": "Fixed amount",
    "customerAdmin.actions.refreshCommercial": "Reload commercial data",
    "customerAdmin.actions.saveBillingProfile": "Save billing profile",
    "customerAdmin.actions.addInvoiceParty": "Add invoice party",
    "customerAdmin.actions.createInvoiceParty": "Create invoice party",
    "customerAdmin.actions.saveInvoiceParty": "Save invoice party",
    "customerAdmin.actions.addRateCard": "Add rate card",
    "customerAdmin.actions.createRateCard": "Create rate card",
    "customerAdmin.actions.saveRateCard": "Save rate card",
    "customerAdmin.actions.addRateLine": "Add rate line",
    "customerAdmin.actions.createRateLine": "Create rate line",
    "customerAdmin.actions.saveRateLine": "Save rate line",
    "customerAdmin.actions.addSurchargeRule": "Add surcharge rule",
    "customerAdmin.actions.createSurchargeRule": "Create surcharge rule",
    "customerAdmin.actions.saveSurchargeRule": "Save surcharge rule",
    "customerAdmin.confirm.activeCommercialChange":
      "This change affects active commercial settings. Do you want to continue?",
    "customerAdmin.confirm.defaultInvoicePartyChange":
      "This invoice party will become the default. Do you want to continue?",
    "customerAdmin.feedback.commercialSaved": "Commercial setting saved",
    "customerAdmin.feedback.invoicePartyRequired":
      "An invoice party needs at least a company name and an address ID.",
    "customerAdmin.feedback.invalidInvoiceEmail": "The invoice email is invalid.",
    "customerAdmin.feedback.invalidPaymentTerms": "The payment-term value is invalid.",
    "customerAdmin.feedback.taxExemptionReasonRequired":
      "A reason is required when tax exemption is enabled.",
    "customerAdmin.feedback.taxExemptionReasonForbidden":
      "A tax-exemption reason may only be set when tax exemption is enabled.",
    "customerAdmin.feedback.bankAccountHolderRequired":
      "An account holder is required when bank data is stored.",
    "customerAdmin.feedback.bankIbanRequired": "An IBAN is required when bank data is stored.",
    "customerAdmin.feedback.eInvoiceRequired": "E-invoice dispatch requires e-invoicing to be enabled.",
    "customerAdmin.feedback.eInvoiceDispatchMismatch":
      "Active e-invoicing is only allowed with the e-invoice dispatch method.",
    "customerAdmin.feedback.leitwegRequired":
      "E-invoice dispatch requires a Leitweg/routing ID.",
    "customerAdmin.feedback.leitwegForbidden":
      "A Leitweg/routing ID may only be set when e-invoicing is enabled.",
    "customerAdmin.feedback.dispatchEmailRequired":
      "Email-PDF dispatch requires an invoice email address.",
    "customerAdmin.feedback.invoiceLayoutIncompatible":
      "The selected invoice layout is incompatible with the dispatch method.",
    "customerAdmin.feedback.defaultInvoicePartyConflict":
      "A default invoice party already exists for this customer.",
    "customerAdmin.feedback.rateKindRequired": "A rate card requires a rate kind.",
    "customerAdmin.feedback.invalidCurrency": "The currency code is invalid.",
    "customerAdmin.feedback.rateCardEffectiveFromRequired":
      "A rate card requires an effective-from date.",
    "customerAdmin.feedback.invalidEffectiveWindow": "The effective window is invalid.",
    "customerAdmin.feedback.rateCardOverlap":
      "This pricing window overlaps an existing active rate card.",
    "customerAdmin.feedback.rateLineKindRequired": "A rate line requires a line kind.",
    "customerAdmin.feedback.invalidBillingUnit": "The billing unit is invalid.",
    "customerAdmin.feedback.invalidUnitPrice": "The unit price is invalid.",
    "customerAdmin.feedback.invalidMinimumQuantity": "The minimum quantity is invalid.",
    "customerAdmin.feedback.duplicateRateDimension":
      "This pricing dimension already exists on the selected rate card.",
    "customerAdmin.feedback.surchargeTypeRequired": "A surcharge needs a type.",
    "customerAdmin.feedback.surchargeEffectiveFromRequired":
      "A surcharge rule requires an effective-from date.",
    "customerAdmin.feedback.invalidWeekdayMask":
      "The weekday mask must contain seven characters made of 0 or 1.",
    "customerAdmin.feedback.invalidTimeRange": "The surcharge time range is invalid.",
    "customerAdmin.feedback.invalidAmountCombination":
      "Exactly one percentage or fixed amount must be set.",
    "customerAdmin.feedback.surchargeOutsideRateCardWindow":
      "The surcharge must stay within the selected rate-card window.",
    "customerAdmin.option.invoiceLayout.standard": "Standard",
    "customerAdmin.option.invoiceLayout.compact": "Compact",
    "customerAdmin.option.invoiceLayout.detailed_timesheet": "With timesheet detail",
    "customerAdmin.option.shippingMethod.email_pdf": "Email PDF",
    "customerAdmin.option.shippingMethod.portal_download": "Portal download",
    "customerAdmin.option.shippingMethod.postal_print": "Postal delivery",
    "customerAdmin.option.shippingMethod.e_invoice": "E-invoice",
    "customerAdmin.option.dunningPolicy.disabled": "Disabled",
    "customerAdmin.option.dunningPolicy.standard": "Standard",
    "customerAdmin.option.dunningPolicy.strict": "Strict",
  },
};
