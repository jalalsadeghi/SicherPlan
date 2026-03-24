export interface DashboardQuickAction {
  label: string;
  to: string;
  type: 'default' | 'primary';
}

export function buildDashboardQuickActions({
  isPlatformAdmin,
  t,
}: {
  isPlatformAdmin: boolean;
  t: (key: string) => string;
}): DashboardQuickAction[] {
  return isPlatformAdmin
    ? [
        {
          label: t('sicherplan.admin.core'),
          to: '/admin/core',
          type: 'primary',
        },
        {
          label: t('sicherplan.admin.tenantUsers'),
          to: '/admin/iam/users',
          type: 'default',
        },
        {
          label: t('sicherplan.admin.health'),
          to: '/admin/health',
          type: 'default',
        },
      ]
    : [
        {
          label: t('sicherplan.admin.customers'),
          to: '/admin/customers',
          type: 'primary',
        },
        {
          label: t('sicherplan.admin.planningShifts'),
          to: '/admin/planning-shifts',
          type: 'default',
        },
        {
          label: t('sicherplan.admin.reporting'),
          to: '/admin/reporting',
          type: 'default',
        },
      ];
}
