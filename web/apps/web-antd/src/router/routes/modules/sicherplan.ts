import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:shield-check',
      ignoreAccess: true,
      order: -10,
      title: $t('sicherplan.admin.title'),
    },
    name: 'SicherPlanAdmin',
    path: '/admin',
    children: [
      {
        name: 'SicherPlanCoreAdmin',
        path: '/admin/core',
        component: () => import('@/views/CoreAdminView.vue'),
        meta: {
          icon: 'lucide:building-2',
          ignoreAccess: true,
          title: $t('sicherplan.admin.core'),
        },
      },
      {
        name: 'SicherPlanPlatformServices',
        path: '/admin/platform-services',
        component: () => import('@/views/NoticeAdminView.vue'),
        meta: {
          icon: 'lucide:layers-3',
          ignoreAccess: true,
          title: $t('sicherplan.admin.platformServices'),
        },
      },
      {
        name: 'SicherPlanCustomers',
        path: '/admin/customers',
        component: () => import('@/views/CustomerAdminView.vue'),
        meta: {
          icon: 'lucide:users',
          ignoreAccess: true,
          title: $t('sicherplan.admin.customers'),
        },
      },
      {
        name: 'SicherPlanRecruiting',
        path: '/admin/recruiting',
        component: () => import('@/views/RecruitingAdminView.vue'),
        meta: {
          icon: 'lucide:file-search-2',
          ignoreAccess: true,
          title: $t('sicherplan.admin.recruiting'),
        },
      },
      {
        name: 'SicherPlanEmployees',
        path: '/admin/employees',
        component: () => import('@/views/EmployeeAdminView.vue'),
        meta: {
          icon: 'lucide:file-user',
          ignoreAccess: true,
          title: $t('sicherplan.admin.employees'),
        },
      },
    ],
  },
  {
    meta: {
      icon: 'lucide:file-user',
      ignoreAccess: true,
      order: 30,
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
          ignoreAccess: true,
          title: $t('sicherplan.public.applicantForm'),
        },
      },
    ],
  },
  {
    meta: {
      icon: 'lucide:door-open',
      ignoreAccess: true,
      order: 20,
      title: $t('sicherplan.portal.title'),
    },
    name: 'SicherPlanPortal',
    path: '/portal',
    children: [
      {
        name: 'SicherPlanCustomerPortal',
        path: '/portal/customer',
        component: () => import('@/views/CustomerPortalAccessView.vue'),
        meta: {
          icon: 'lucide:user-round-search',
          ignoreAccess: true,
          title: $t('sicherplan.portal.customer'),
        },
      },
    ],
  },
];

export default routes;
