import { defineAsyncComponent } from 'vue';

export interface ModuleConfig {
  allowedRoles?: string[];
  badges: Array<{ key: string; tone?: 'default' | 'success' | 'warning' }>;
  component: ReturnType<typeof defineAsyncComponent>;
  descriptionKey: string;
  highlightKeys: string[];
  hideWorkspaceSectionHeaderForRoles?: string[];
  quickLinks: Array<{ authority?: string[]; labelKey: string; to: string }>;
  showPageIntro?: boolean;
  showWorkspaceSectionHeader?: boolean;
  stats: Array<{ hintKey?: string; labelKey: string; valueKey: string }>;
  titleKey: string;
  workspaceDescriptionKey: string;
}

export const moduleRegistry: Record<string, ModuleConfig> = {
  core: {
    badges: [
      { key: 'Tenant Core', tone: 'success' },
      { key: 'RBAC', tone: 'default' },
      { key: 'Onboarding', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/CoreAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.core.description',
    highlightKeys: [
      'sicherplan.ui.profiles.administration.0',
      'sicherplan.ui.profiles.administration.1',
      'sicherplan.ui.profiles.administration.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.platformServices', to: '/admin/platform-services' },
      { authority: ['platform_admin'], labelKey: 'sicherplan.admin.tenantUsers', to: '/admin/iam/users' },
      { authority: ['tenant_admin'], labelKey: 'sicherplan.admin.customers', to: '/admin/customers' },
      { authority: ['platform_admin'], labelKey: 'sicherplan.admin.health', to: '/admin/health' },
      { authority: ['tenant_admin'], labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.platformReady' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.roleScoped' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.auditSafe' },
    ],
    showPageIntro: false,
    showWorkspaceSectionHeader: false,
    titleKey: 'sicherplan.admin.core',
    workspaceDescriptionKey: 'sicherplan.ui.modules.core.workspace',
  },
  'platform-services': {
    badges: [
      { key: 'Docs Service', tone: 'success' },
      { key: 'Internal Notices', tone: 'default' },
      { key: 'Integration Safe', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/NoticeAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.platformServices.description',
    highlightKeys: [
      'sicherplan.ui.profiles.platform.0',
      'sicherplan.ui.profiles.platform.1',
      'sicherplan.ui.profiles.platform.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.core', to: '/admin/core' },
      { authority: ['platform_admin'], labelKey: 'sicherplan.admin.tenantUsers', to: '/admin/iam/users' },
      { authority: ['tenant_admin'], labelKey: 'sicherplan.admin.customers', to: '/admin/customers' },
      { authority: ['platform_admin'], labelKey: 'sicherplan.admin.health', to: '/admin/health' },
      { authority: ['tenant_admin'], labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.tenantScoped' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.internalAudiences' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.documentLinked' },
    ],
    showWorkspaceSectionHeader: false,
    titleKey: 'sicherplan.admin.platformServices',
    workspaceDescriptionKey: 'sicherplan.ui.modules.platformServices.workspace',
  },
  customers: {
    allowedRoles: ['tenant_admin', 'dispatcher', 'accounting', 'controller_qm'],
    badges: [
      { key: 'Master Data', tone: 'success' },
      { key: 'Commercial Scope', tone: 'default' },
      { key: 'Portal Release', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/CustomerAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.customers.description',
    highlightKeys: [
      'sicherplan.ui.profiles.masterData.0',
      'sicherplan.ui.profiles.masterData.1',
      'sicherplan.ui.profiles.masterData.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.planningOrders', to: '/admin/planning-orders' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
      { labelKey: 'sicherplan.portal.customer', to: '/portal/customer' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.customerScoped' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.leastPrivilege' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.documentLinked' },
    ],
    hideWorkspaceSectionHeaderForRoles: ['tenant_admin'],
    titleKey: 'sicherplan.admin.customers',
    workspaceDescriptionKey: 'sicherplan.ui.modules.customers.workspace',
  },
  employees: {
    badges: [
      { key: 'HR Split', tone: 'success' },
      { key: 'Private Data', tone: 'warning' },
      { key: 'Import Ready', tone: 'default' },
    ],
    component: defineAsyncComponent(() => import('@/views/EmployeeAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.employees.description',
    highlightKeys: [
      'sicherplan.ui.profiles.workforce.0',
      'sicherplan.ui.profiles.workforce.1',
      'sicherplan.ui.profiles.workforce.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.recruiting', to: '/admin/recruiting' },
      { labelKey: 'sicherplan.admin.planningStaffing', to: '/admin/planning-staffing' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.tenantScoped' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.hrLeastPrivilege' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.auditSafe' },
    ],
    showWorkspaceSectionHeader: false,
    titleKey: 'sicherplan.admin.employees',
    workspaceDescriptionKey: 'sicherplan.ui.modules.employees.workspace',
  },
  recruiting: {
    badges: [
      { key: 'Applicant Flow', tone: 'success' },
      { key: 'Public Intake', tone: 'default' },
      { key: 'Document Intake', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/RecruitingAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.recruiting.description',
    highlightKeys: [
      'sicherplan.ui.profiles.workforce.0',
      'sicherplan.ui.profiles.workforce.1',
      'sicherplan.ui.profiles.workforce.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.public.applicantForm', to: '/public/apply/demo' },
      { labelKey: 'sicherplan.admin.employees', to: '/admin/employees' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.tenantScoped' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.roleScoped' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.documentLinked' },
    ],
    titleKey: 'sicherplan.admin.recruiting',
    workspaceDescriptionKey: 'sicherplan.ui.modules.recruiting.workspace',
  },
  subcontractors: {
    badges: [
      { key: 'Partner Master', tone: 'success' },
      { key: 'Scope Release', tone: 'default' },
      { key: 'Billing Control', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/SubcontractorAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.subcontractors.description',
    highlightKeys: [
      'sicherplan.ui.profiles.partner.0',
      'sicherplan.ui.profiles.partner.1',
      'sicherplan.ui.profiles.partner.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.financeSubcontractorChecks', to: '/admin/finance-subcontractor-checks' },
      { labelKey: 'sicherplan.portal.subcontractor', to: '/portal/subcontractor' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.partnerScoped' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.leastPrivilege' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.documentLinked' },
    ],
    showWorkspaceSectionHeader: false,
    titleKey: 'sicherplan.admin.subcontractors',
    workspaceDescriptionKey: 'sicherplan.ui.modules.subcontractors.workspace',
  },
  planning: {
    badges: [
      { key: 'Operations', tone: 'success' },
      { key: 'Release Control', tone: 'default' },
      { key: 'Cross-Module Read', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/PlanningOpsAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.planning.description',
    highlightKeys: [
      'sicherplan.ui.profiles.operations.0',
      'sicherplan.ui.profiles.operations.1',
      'sicherplan.ui.profiles.operations.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.planningOrders', to: '/admin/planning-orders' },
      { labelKey: 'sicherplan.admin.planningShifts', to: '/admin/planning-shifts' },
      { labelKey: 'sicherplan.admin.planningStaffing', to: '/admin/planning-staffing' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.releasedOperations' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.roleScoped' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.traceableChain' },
    ],
    showWorkspaceSectionHeader: false,
    titleKey: 'sicherplan.admin.planning',
    workspaceDescriptionKey: 'sicherplan.ui.modules.planning.workspace',
  },
  'planning-orders': {
    allowedRoles: ['tenant_admin', 'dispatcher', 'accounting', 'controller_qm'],
    badges: [
      { key: 'Order Backbone', tone: 'success' },
      { key: 'Commercial Context', tone: 'default' },
      { key: 'Release Safe', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/PlanningOrdersAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.planningOrders.description',
    highlightKeys: [
      'sicherplan.ui.profiles.operations.0',
      'sicherplan.ui.profiles.operations.1',
      'sicherplan.ui.profiles.operations.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.customers', to: '/admin/customers' },
      { labelKey: 'sicherplan.admin.planningShifts', to: '/admin/planning-shifts' },
      { labelKey: 'sicherplan.admin.financeActuals', to: '/admin/finance-actuals' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.tenantScoped' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.operationalViews' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.traceableChain' },
    ],
    showWorkspaceSectionHeader: false,
    titleKey: 'sicherplan.admin.planningOrders',
    workspaceDescriptionKey: 'sicherplan.ui.modules.planningOrders.workspace',
  },
  'planning-shifts': {
    badges: [
      { key: 'Shift Planning', tone: 'success' },
      { key: 'Coverage', tone: 'default' },
      { key: 'Released Work', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/PlanningShiftsAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.planningShifts.description',
    highlightKeys: [
      'sicherplan.ui.profiles.planning.0',
      'sicherplan.ui.profiles.planning.1',
      'sicherplan.ui.profiles.planning.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.planningStaffing', to: '/admin/planning-staffing' },
      { labelKey: 'sicherplan.admin.financeActuals', to: '/admin/finance-actuals' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.releasedOperations' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.dispatchReady' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.traceableChain' },
    ],
    showWorkspaceSectionHeader: false,
    titleKey: 'sicherplan.admin.planningShifts',
    workspaceDescriptionKey: 'sicherplan.ui.modules.planningShifts.workspace',
  },
  'planning-staffing': {
    allowedRoles: ['tenant_admin', 'dispatcher'],
    badges: [
      { key: 'Coverage', tone: 'success' },
      { key: 'Availability Read', tone: 'default' },
      { key: 'Qualification Match', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/PlanningStaffingCoverageView.vue')),
    descriptionKey: 'sicherplan.ui.modules.planningStaffing.description',
    highlightKeys: [
      'sicherplan.ui.profiles.planning.0',
      'sicherplan.ui.profiles.planning.1',
      'sicherplan.ui.profiles.planning.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.employees', to: '/admin/employees' },
      { labelKey: 'sicherplan.admin.subcontractors', to: '/admin/subcontractors' },
      { labelKey: 'sicherplan.admin.planningShifts', to: '/admin/planning-shifts' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.releasedOperations' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.dispatchReady' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.auditSafe' },
    ],
    titleKey: 'sicherplan.admin.planningStaffing',
    workspaceDescriptionKey: 'sicherplan.ui.modules.planningStaffing.workspace',
  },
  'finance-actuals': {
    badges: [
      { key: 'Actual Record', tone: 'success' },
      { key: 'Evidence Bridge', tone: 'default' },
      { key: 'Approval', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/FinanceActualApprovalView.vue')),
    descriptionKey: 'sicherplan.ui.modules.financeActuals.description',
    highlightKeys: [
      'sicherplan.ui.profiles.finance.0',
      'sicherplan.ui.profiles.finance.1',
      'sicherplan.ui.profiles.finance.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.planningShifts', to: '/admin/planning-shifts' },
      { labelKey: 'sicherplan.admin.financePayroll', to: '/admin/finance-payroll' },
      { labelKey: 'sicherplan.admin.financeBilling', to: '/admin/finance-billing' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.financeBridge' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.financeControlled' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.appendOnly' },
    ],
    titleKey: 'sicherplan.admin.financeActuals',
    workspaceDescriptionKey: 'sicherplan.ui.modules.financeActuals.workspace',
  },
  'finance-payroll': {
    badges: [
      { key: 'Payroll', tone: 'success' },
      { key: 'Export', tone: 'default' },
      { key: 'Actual Record', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/FinancePayrollAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.financePayroll.description',
    highlightKeys: [
      'sicherplan.ui.profiles.finance.0',
      'sicherplan.ui.profiles.finance.1',
      'sicherplan.ui.profiles.finance.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.financeActuals', to: '/admin/finance-actuals' },
      { labelKey: 'sicherplan.admin.financeBilling', to: '/admin/finance-billing' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.financeBridge' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.financeControlled' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.documentLinked' },
    ],
    titleKey: 'sicherplan.admin.financePayroll',
    workspaceDescriptionKey: 'sicherplan.ui.modules.financePayroll.workspace',
  },
  'finance-billing': {
    badges: [
      { key: 'Billing', tone: 'success' },
      { key: 'Invoice Output', tone: 'default' },
      { key: 'Document Trace', tone: 'warning' },
    ],
    component: defineAsyncComponent(() => import('@/views/FinanceBillingAdminView.vue')),
    descriptionKey: 'sicherplan.ui.modules.financeBilling.description',
    highlightKeys: [
      'sicherplan.ui.profiles.finance.0',
      'sicherplan.ui.profiles.finance.1',
      'sicherplan.ui.profiles.finance.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.financeActuals', to: '/admin/finance-actuals' },
      { labelKey: 'sicherplan.admin.financeSubcontractorChecks', to: '/admin/finance-subcontractor-checks' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.financeBridge' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.financeControlled' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.documentLinked' },
    ],
    titleKey: 'sicherplan.admin.financeBilling',
    workspaceDescriptionKey: 'sicherplan.ui.modules.financeBilling.workspace',
  },
  'finance-subcontractor-checks': {
    badges: [
      { key: 'Partner Invoice Check', tone: 'success' },
      { key: 'Actual Reconciliation', tone: 'default' },
      { key: 'Commercial Review', tone: 'warning' },
    ],
    component: defineAsyncComponent(
      () => import('@/views/FinanceSubcontractorInvoiceChecksView.vue'),
    ),
    descriptionKey: 'sicherplan.ui.modules.financeSubcontractorChecks.description',
    highlightKeys: [
      'sicherplan.ui.profiles.finance.0',
      'sicherplan.ui.profiles.finance.1',
      'sicherplan.ui.profiles.finance.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.subcontractors', to: '/admin/subcontractors' },
      { labelKey: 'sicherplan.admin.financeBilling', to: '/admin/finance-billing' },
      { labelKey: 'sicherplan.admin.reporting', to: '/admin/reporting' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.financeBridge' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.financeControlled' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.auditSafe' },
    ],
    titleKey: 'sicherplan.admin.financeSubcontractorChecks',
    workspaceDescriptionKey:
      'sicherplan.ui.modules.financeSubcontractorChecks.workspace',
  },
  reporting: {
    badges: [
      { key: 'SQL First', tone: 'success' },
      { key: 'Reproducible', tone: 'default' },
      { key: 'Role Scoped', tone: 'warning' },
    ],
    component: defineAsyncComponent(
      () => import('@/views/ReportingDashboardView.vue'),
    ),
    descriptionKey: 'sicherplan.ui.modules.reporting.description',
    highlightKeys: [
      'sicherplan.ui.profiles.reporting.0',
      'sicherplan.ui.profiles.reporting.1',
      'sicherplan.ui.profiles.reporting.2',
    ],
    quickLinks: [
      { labelKey: 'sicherplan.admin.financeBilling', to: '/admin/finance-billing' },
      { labelKey: 'sicherplan.admin.customers', to: '/admin/customers' },
      { labelKey: 'sicherplan.portal.customer', to: '/portal/customer' },
    ],
    stats: [
      { labelKey: 'sicherplan.ui.stats.scope', valueKey: 'sicherplan.ui.values.roleScoped' },
      { labelKey: 'sicherplan.ui.stats.visibility', valueKey: 'sicherplan.ui.values.reproducibleViews' },
      { labelKey: 'sicherplan.ui.stats.evidence', valueKey: 'sicherplan.ui.values.auditSafe' },
    ],
    titleKey: 'sicherplan.admin.reporting',
    workspaceDescriptionKey: 'sicherplan.ui.modules.reporting.workspace',
  },
};
