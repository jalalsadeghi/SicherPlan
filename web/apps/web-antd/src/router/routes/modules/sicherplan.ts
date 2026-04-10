import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const RouteSectionView = () => import('@/views/RouteSectionView.vue');
const AdminModuleView = () => import('#/views/sicherplan/admin-module-view.vue');

const routes: RouteRecordRaw[] = [
  {
    meta: {
      authority: ['platform_admin', 'tenant_admin', 'dispatcher', 'accounting', 'controller_qm'],
      icon: 'lucide:shield-check',
      order: -10,
      title: $t('sicherplan.navigation.dashboard'),
    },
    name: 'SicherPlanDashboard',
    path: '/admin/dashboard',
    component: () => import('#/views/sicherplan/dashboard/index.vue'),
    children: [],
  },
  {
    meta: {
      authority: ['platform_admin', 'tenant_admin', 'controller_qm'],
      icon: 'lucide:settings-2',
      order: -9,
      title: $t('sicherplan.navigation.administration'),
    },
    name: 'SicherPlanAdministrationSection',
    path: '/admin/administration',
    component: RouteSectionView,
    redirect: '/admin/core',
    children: [
      {
        name: 'SicherPlanCoreAdmin',
        path: '/admin/core',
        component: AdminModuleView,
        meta: {
          authority: ['platform_admin', 'tenant_admin'],
          icon: 'lucide:building-2',
          moduleKey: 'core',
          title: $t('sicherplan.admin.core'),
        },
      },
      {
        name: 'SicherPlanPlatformServices',
        path: '/admin/platform-services',
        component: AdminModuleView,
        meta: {
          authority: ['platform_admin', 'tenant_admin', 'controller_qm'],
          icon: 'lucide:layers-3',
          moduleKey: 'platform-services',
          title: $t('sicherplan.admin.platformServices'),
        },
      },
      {
        name: 'SicherPlanTenantUsers',
        path: '/admin/iam/users',
        component: () => import('#/views/sicherplan/tenant-users/index.vue'),
        meta: {
          authority: ['platform_admin'],
          icon: 'lucide:user-cog',
          title: $t('sicherplan.admin.tenantUsers'),
        },
      },
      {
        name: 'SicherPlanHealthDiagnostics',
        path: '/admin/health',
        component: () => import('#/views/sicherplan/health/index.vue'),
        meta: {
          authority: ['platform_admin'],
          icon: 'lucide:activity',
          title: $t('sicherplan.admin.health'),
        },
      },
    ],
  },
  {
    meta: {
      authority: ['tenant_admin', 'dispatcher', 'accounting', 'controller_qm'],
      icon: 'lucide:users',
      order: -8,
      title: $t('sicherplan.navigation.customers'),
    },
    name: 'SicherPlanCustomersSection',
    path: '/admin/customers-section',
    component: RouteSectionView,
    redirect: '/admin/customers',
    children: [
      {
        name: 'SicherPlanCustomers',
        path: '/admin/customers',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher', 'accounting', 'controller_qm'],
          icon: 'lucide:users',
          moduleKey: 'customers',
          title: $t('sicherplan.admin.customers'),
        },
      },
    ],
  },
  {
    meta: {
      authority: ['tenant_admin', 'dispatcher', 'controller_qm'],
      icon: 'lucide:users-round',
      order: -7,
      title: $t('sicherplan.navigation.workforce'),
    },
    name: 'SicherPlanWorkforceSection',
    path: '/admin/workforce',
    component: RouteSectionView,
    redirect: '/admin/recruiting',
    children: [
      {
        name: 'SicherPlanRecruiting',
        path: '/admin/recruiting',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher', 'controller_qm'],
          icon: 'lucide:file-search-2',
          moduleKey: 'recruiting',
          title: $t('sicherplan.admin.recruiting'),
        },
      },
      {
        name: 'SicherPlanEmployees',
        path: '/admin/employees',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher', 'controller_qm'],
          icon: 'lucide:file-user',
          moduleKey: 'employees',
          title: $t('sicherplan.admin.employees'),
        },
      },
      {
        name: 'SicherPlanSubcontractors',
        path: '/admin/subcontractors',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher', 'controller_qm'],
          icon: 'lucide:briefcase-business',
          moduleKey: 'subcontractors',
          title: $t('sicherplan.admin.subcontractors'),
        },
      },
    ],
  },
  {
    meta: {
      authority: ['tenant_admin', 'dispatcher', 'accounting', 'controller_qm'],
      icon: 'lucide:map',
      order: -6,
      title: $t('sicherplan.navigation.operations'),
    },
    name: 'SicherPlanOperationsSection',
    path: '/admin/operations',
    component: RouteSectionView,
    redirect: '/admin/planning',
    children: [
      {
        name: 'SicherPlanPlanning',
        path: '/admin/planning',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher', 'controller_qm'],
          icon: 'lucide:map-pinned',
          moduleKey: 'planning',
          title: $t('sicherplan.admin.planning'),
        },
      },
      {
        name: 'SicherPlanPlanningOrders',
        path: '/admin/planning-orders',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher', 'accounting', 'controller_qm'],
          icon: 'lucide:clipboard-list',
          moduleKey: 'planning-orders',
          title: $t('sicherplan.admin.planningOrders'),
        },
      },
      {
        name: 'SicherPlanPlanningShifts',
        path: '/admin/planning-shifts',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher', 'controller_qm'],
          icon: 'lucide:calendar-range',
          moduleKey: 'planning-shifts',
          title: $t('sicherplan.admin.planningShifts'),
        },
      },
      {
        name: 'SicherPlanPlanningStaffing',
        path: '/admin/planning-staffing',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'dispatcher'],
          icon: 'lucide:users-round',
          moduleKey: 'planning-staffing',
          title: $t('sicherplan.admin.planningStaffing'),
        },
      },
    ],
  },
  {
    meta: {
      authority: ['tenant_admin', 'accounting', 'controller_qm'],
      icon: 'lucide:banknote',
      order: -5,
      title: $t('sicherplan.navigation.finance'),
    },
    name: 'SicherPlanFinanceSection',
    path: '/admin/finance',
    component: RouteSectionView,
    redirect: '/admin/finance-actuals',
    children: [
      {
        name: 'SicherPlanFinanceActuals',
        path: '/admin/finance-actuals',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'accounting', 'controller_qm'],
          icon: 'lucide:badge-euro',
          moduleKey: 'finance-actuals',
          title: $t('sicherplan.admin.financeActuals'),
        },
      },
      {
        name: 'SicherPlanFinancePayroll',
        path: '/admin/finance-payroll',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'accounting', 'controller_qm'],
          icon: 'lucide:receipt-text',
          moduleKey: 'finance-payroll',
          title: $t('sicherplan.admin.financePayroll'),
        },
      },
      {
        name: 'SicherPlanFinanceBilling',
        path: '/admin/finance-billing',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'accounting', 'controller_qm'],
          icon: 'lucide:file-text',
          moduleKey: 'finance-billing',
          title: $t('sicherplan.admin.financeBilling'),
        },
      },
      {
        name: 'SicherPlanFinanceSubcontractorChecks',
        path: '/admin/finance-subcontractor-checks',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'accounting', 'controller_qm'],
          icon: 'lucide:hand-coins',
          moduleKey: 'finance-subcontractor-checks',
          title: $t('sicherplan.admin.financeSubcontractorChecks'),
        },
      },
    ],
  },
  {
    meta: {
      authority: ['tenant_admin', 'accounting', 'controller_qm'],
      icon: 'lucide:chart-column-big',
      order: -4,
      title: $t('sicherplan.navigation.reporting'),
    },
    name: 'SicherPlanReportingSection',
    path: '/admin/reporting-section',
    component: RouteSectionView,
    redirect: '/admin/reporting',
    children: [
      {
        name: 'SicherPlanReporting',
        path: '/admin/reporting',
        component: AdminModuleView,
        meta: {
          authority: ['tenant_admin', 'accounting', 'controller_qm'],
          icon: 'lucide:chart-column-big',
          moduleKey: 'reporting',
          title: $t('sicherplan.admin.reporting'),
        },
      },
    ],
  },
  {
    meta: {
      icon: 'lucide:file-user',
      order: 20,
      title: $t('sicherplan.public.title'),
    },
    name: 'SicherPlanPublic',
    path: '/public',
    children: [
      {
        name: 'SicherPlanApplicantForm',
        path: '/public/apply/:tenantCode',
        component: () => import('@/views/ApplicantPublicFormView.vue'),
        meta: {
          icon: 'lucide:file-user',
          title: $t('sicherplan.public.applicantForm'),
        },
      },
    ],
  },
  {
    meta: {
      icon: 'lucide:door-open',
      order: 10,
      title: $t('sicherplan.portal.title'),
    },
    name: 'SicherPlanPortal',
    path: '/portal',
    children: [
      {
        name: 'SicherPlanCustomerPortalSection',
        path: '/portal/customer',
        component: RouteSectionView,
        redirect: '/portal/customer/overview',
        meta: {
          authority: ['customer_user'],
          icon: 'lucide:user-round-search',
          title: $t('sicherplan.portal.customer'),
        },
        children: [
          {
            name: 'SicherPlanCustomerPortalOverview',
            path: '/portal/customer/overview',
            component: () => import('@/views/CustomerPortalAccessView.vue'),
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:layout-dashboard',
              title: $t('sicherplan.portal.customerOverview'),
            },
          },
          {
            name: 'SicherPlanCustomerPortalOrders',
            path: '/portal/customer/orders',
            component: () => import('@/views/customer-portal/CustomerPortalReadonlyDatasetView.vue'),
            props: { domain: 'orders' },
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:clipboard-list',
              title: $t('sicherplan.portal.customerOrders'),
            },
          },
          {
            name: 'SicherPlanCustomerPortalSchedules',
            path: '/portal/customer/schedules',
            component: () => import('@/views/customer-portal/CustomerPortalReadonlyDatasetView.vue'),
            props: { domain: 'schedules' },
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:calendar-range',
              title: $t('sicherplan.portal.customerSchedules'),
            },
          },
          {
            name: 'SicherPlanCustomerPortalWatchbooks',
            path: '/portal/customer/watchbooks',
            component: () => import('@/views/customer-portal/CustomerPortalWatchbooksView.vue'),
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:notebook-pen',
              title: $t('sicherplan.portal.customerWatchbooks'),
            },
          },
          {
            name: 'SicherPlanCustomerPortalTimesheets',
            path: '/portal/customer/timesheets',
            component: () => import('@/views/customer-portal/CustomerPortalDocumentDatasetView.vue'),
            props: { domain: 'timesheets' },
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:file-clock',
              title: $t('sicherplan.portal.customerTimesheets'),
            },
          },
          {
            name: 'SicherPlanCustomerPortalInvoices',
            path: '/portal/customer/invoices',
            component: () => import('@/views/customer-portal/CustomerPortalDocumentDatasetView.vue'),
            props: { domain: 'invoices' },
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:file-text',
              title: $t('sicherplan.portal.customerInvoices'),
            },
          },
          {
            name: 'SicherPlanCustomerPortalReports',
            path: '/portal/customer/reports',
            component: () => import('@/views/customer-portal/CustomerPortalReadonlyDatasetView.vue'),
            props: { domain: 'reports' },
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:bar-chart-3',
              title: $t('sicherplan.portal.customerReports'),
            },
          },
          {
            name: 'SicherPlanCustomerPortalHistory',
            path: '/portal/customer/history',
            component: () => import('@/views/customer-portal/CustomerPortalHistoryView.vue'),
            meta: {
              authority: ['customer_user'],
              icon: 'lucide:history',
              title: $t('sicherplan.portal.customerHistory'),
            },
          },
        ],
      },
      {
        name: 'SicherPlanSubcontractorPortal',
        path: '/portal/subcontractor',
        component: () => import('@/views/SubcontractorPortalAccessView.vue'),
        meta: {
          authority: ['subcontractor_user'],
          icon: 'lucide:briefcase-business',
          title: $t('sicherplan.portal.subcontractor'),
        },
      },
    ],
  },
];

export default routes;
