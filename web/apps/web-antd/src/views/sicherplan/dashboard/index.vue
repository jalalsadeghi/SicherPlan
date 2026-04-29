<script lang="ts" setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';
import { Button, Card, Space, Tag } from 'ant-design-vue';

import { $t } from '#/locales';
import DashboardCalendarPanel from '#/components/sicherplan/dashboard-calendar-panel.vue';
import EmptyState from '#/components/sicherplan/empty-state.vue';
import SectionHeader from '#/components/sicherplan/section-header.vue';
import {
  buildCoverageShiftLabel,
  buildStaffingCoverageRoute,
} from '#/features/sicherplan/dashboardCoverage.helpers';
import { useAuthStore as useLegacyAuthStore } from '#/sicherplan-legacy/stores/auth';
import { listTenants, type TenantListItem } from '#/sicherplan-legacy/api/coreAdmin';
import { listCustomers, type CustomerListItem } from '#/sicherplan-legacy/api/customers';
import { listEmployees, type EmployeeListItem } from '#/sicherplan-legacy/api/employeeAdmin';
import { listAdminNotices, type NoticeListItem } from '#/sicherplan-legacy/api/notices';
import {
  listCustomerOrders,
  type CustomerOrderListItem,
} from '#/sicherplan-legacy/api/planningOrders';
import { listShifts, type ShiftListItem } from '#/sicherplan-legacy/api/planningShifts';
import {
  listStaffingCoverage,
  type CoverageShiftItem,
} from '#/sicherplan-legacy/api/planningStaffing';
import {
  listSubcontractors,
  type SubcontractorListItem,
} from '#/sicherplan-legacy/api/subcontractors';
import {
  coverageTone,
  resolvePlanningStaffingCoverageState,
} from '#/sicherplan-legacy/features/planning/planningStaffing.helpers';
import { useIsRouteCachePaneActive } from '@vben/layouts/route-cached';

defineOptions({ name: 'SicherPlanDashboard' });

interface CalendarCell {
  date: Date;
  dayLabel: string;
  inMonth: boolean;
  isToday: boolean;
  items: CalendarCellItem[];
  moreCount: number;
  orderCount: number;
  shiftCount: number;
  key: string;
  visibleItems: CalendarCellItem[];
}

interface CalendarCellItem {
  coverageState: string;
  key: string;
  label: string;
  route: string;
  tone: 'bad' | 'good' | 'warn';
}

const accessStore = useAccessStore();
const legacyAuthStore = useLegacyAuthStore();
const userStore = useUserStore();
const isRouteCachePaneActive = useIsRouteCachePaneActive();

const loading = ref(false);
const activeDate = ref(new Date());
const expandedCalendarDays = ref<string[]>([]);
const lastLoadedDashboardKey = ref('');
const activeDashboardLoadKey = ref('');
const activeCoverageMonthKey = ref('');
const calendarError = ref('');
const calendarLoading = ref(false);
const calendarCoverageItemsByDay = ref<Map<string, CalendarCellItem[]>>(new Map());
const dashboardBootstrapComplete = ref(false);
const dashboardSessionWatchArmed = ref(false);
const coverageRequestVersion = ref(0);
const coverageMonthCache = new Map<string, Map<string, CalendarCellItem[]>>();
const coverageMonthRequests = new Map<string, Promise<Map<string, CalendarCellItem[]>>>();

const dashboardData = reactive({
  customers: [] as CustomerListItem[],
  employees: [] as EmployeeListItem[],
  notices: [] as NoticeListItem[],
  orders: [] as CustomerOrderListItem[],
  shifts: [] as ShiftListItem[],
  subcontractors: [] as SubcontractorListItem[],
  tenants: [] as TenantListItem[],
});

const roleKeys = computed(() => userStore.userInfo?.roles ?? []);
const isPlatformAdmin = computed(() => roleKeys.value.includes('platform_admin'));
const locale = computed(() => preferences.app.locale || 'de-DE');
const accessToken = computed(
  () => accessStore.accessToken || legacyAuthStore.effectiveAccessToken,
);
const tenantScopeId = computed(
  () => legacyAuthStore.tenantScopeId || legacyAuthStore.sessionUser?.tenant_id || '',
);
const canLoadTenantData = computed(
  () => Boolean(accessToken.value && tenantScopeId.value),
);
const visibleCalendarMonthKey = computed(() => {
  const current = activeDate.value;
  return `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}`;
});

function resetDashboardData() {
  dashboardData.tenants = [];
  dashboardData.customers = [];
  dashboardData.employees = [];
  dashboardData.subcontractors = [];
  dashboardData.orders = [];
  dashboardData.shifts = [];
  dashboardData.notices = [];
}

function resetCalendarCoverage() {
  activeCoverageMonthKey.value = '';
  calendarError.value = '';
  calendarLoading.value = false;
  calendarCoverageItemsByDay.value = new Map();
  coverageRequestVersion.value += 1;
  expandedCalendarDays.value = [];
}

function resolveDashboardLoadKey() {
  if (!accessToken.value) {
    return '';
  }
  if (isPlatformAdmin.value) {
    return `platform:${accessToken.value}`;
  }
  if (!tenantScopeId.value) {
    return '';
  }
  return `tenant:${tenantScopeId.value}:${accessToken.value}`;
}

function formatDateLabel(value: Date, options: Intl.DateTimeFormatOptions) {
  return new Intl.DateTimeFormat(locale.value, options).format(value);
}

function formatDate(value?: null | string) {
  if (!value) {
    return $t('sicherplan.dashboardView.labels.notScheduled');
  }
  return formatDateLabel(new Date(value), {
    day: '2-digit',
    month: 'short',
  });
}

function getOrderDate(order: CustomerOrderListItem) {
  return order.released_at || order.service_from || order.service_to;
}

function getShiftDate(shift: ShiftListItem) {
  return shift.occurrence_date || shift.starts_at;
}

function buildCalendarDayKey(value: Date) {
  return value.toDateString();
}

function formatDateTimeLocalValue(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  const hours = String(value.getHours()).padStart(2, '0');
  const minutes = String(value.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function visibleCalendarMonthStart(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), 1, 0, 0, 0, 0);
}

function visibleCalendarMonthEnd(value: Date) {
  return new Date(value.getFullYear(), value.getMonth() + 1, 0, 23, 59, 0, 0);
}

function resolveCoverageMonthKey() {
  if (!tenantScopeId.value) {
    return '';
  }
  return [
    tenantScopeId.value,
    formatDateTimeLocalValue(visibleCalendarMonthStart(activeDate.value)),
    formatDateTimeLocalValue(visibleCalendarMonthEnd(activeDate.value)),
  ].join(':');
}

function buildCoverageStateLabel(coverageState: string) {
  switch (coverageState) {
    case 'green':
      return $t('sicherplan.dashboardView.calendar.coverageGood');
    case 'yellow':
      return $t('sicherplan.dashboardView.calendar.coverageWarn');
    case 'setup_required':
      return $t('sicherplan.dashboardView.calendar.coverageSetupRequired');
    default:
      return $t('sicherplan.dashboardView.calendar.coverageBad');
  }
}

function buildCalendarCoverageItemsByDay(coverageRows: CoverageShiftItem[]) {
  const itemsByDay = new Map<string, CalendarCellItem[]>();
  [...coverageRows]
    .sort(
      (left, right) =>
        new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime(),
    )
    .forEach((coverageRow) => {
      const date = new Date(coverageRow.starts_at);
      const key = buildCalendarDayKey(date);
      const resolvedCoverageState = resolvePlanningStaffingCoverageState(
        coverageRow.coverage_state,
        coverageRow.demand_groups,
      );
      const dayItems = itemsByDay.get(key) ?? [];
      dayItems.push({
        coverageState: resolvedCoverageState,
        key: `coverage:${coverageRow.shift_id}`,
        label: buildCoverageShiftLabel(coverageRow, locale.value),
        route: buildStaffingCoverageRoute(coverageRow),
        tone: coverageTone(resolvedCoverageState),
      });
      itemsByDay.set(key, dayItems);
    });
  return itemsByDay;
}

async function loadCalendarCoverageForVisibleMonth(options: { force?: boolean } = {}) {
  if (!canLoadTenantData.value) {
    resetCalendarCoverage();
    return;
  }
  const monthKey = resolveCoverageMonthKey();
  if (!monthKey) {
    resetCalendarCoverage();
    return;
  }

  activeCoverageMonthKey.value = monthKey;
  const cachedItems = coverageMonthCache.get(monthKey);
  if (cachedItems && !options.force) {
    calendarCoverageItemsByDay.value = cachedItems;
    calendarError.value = '';
    calendarLoading.value = false;
    return;
  }

  calendarCoverageItemsByDay.value = cachedItems ?? new Map();
  calendarError.value = '';
  calendarLoading.value = true;

  let request = coverageMonthRequests.get(monthKey);
  if (!request || options.force) {
    request = listStaffingCoverage(tenantScopeId.value, accessToken.value, {
      date_from: formatDateTimeLocalValue(visibleCalendarMonthStart(activeDate.value)),
      date_to: formatDateTimeLocalValue(visibleCalendarMonthEnd(activeDate.value)),
    }).then((coverageRows) => buildCalendarCoverageItemsByDay(coverageRows));
    coverageMonthRequests.set(monthKey, request);
    void request.then(
      () => {
        if (coverageMonthRequests.get(monthKey) === request) {
          coverageMonthRequests.delete(monthKey);
        }
      },
      () => {
        if (coverageMonthRequests.get(monthKey) === request) {
          coverageMonthRequests.delete(monthKey);
        }
      },
    );
  }

  const requestVersion = ++coverageRequestVersion.value;
  try {
    const itemsByDay = await request;
    coverageMonthCache.set(monthKey, itemsByDay);

    if (requestVersion !== coverageRequestVersion.value || activeCoverageMonthKey.value !== monthKey) {
      return;
    }

    calendarCoverageItemsByDay.value = itemsByDay;
  } catch {
    if (requestVersion !== coverageRequestVersion.value || activeCoverageMonthKey.value !== monthKey) {
      return;
    }
    calendarCoverageItemsByDay.value = new Map();
    calendarError.value = $t('sicherplan.dashboardView.calendar.loadError');
  } finally {
    if (requestVersion === coverageRequestVersion.value && activeCoverageMonthKey.value === monthKey) {
      calendarLoading.value = false;
    }
    if (coverageMonthRequests.get(monthKey) === request) {
      coverageMonthRequests.delete(monthKey);
    }
  }
}

function toggleCalendarDay(dayKey: string) {
  expandedCalendarDays.value = expandedCalendarDays.value.includes(dayKey)
    ? expandedCalendarDays.value.filter((value) => value !== dayKey)
    : [...expandedCalendarDays.value, dayKey];
}

function sortByDateDesc<T>(
  items: T[],
  pickDate: (item: T) => null | string | undefined,
) {
  return [...items].sort((left, right) => {
    const leftValue = pickDate(left);
    const rightValue = pickDate(right);
    const leftTime = leftValue ? new Date(leftValue).getTime() : 0;
    const rightTime = rightValue ? new Date(rightValue).getTime() : 0;
    return rightTime - leftTime;
  });
}

async function loadDashboard(options: { force?: boolean } = {}) {
  const loadKey = resolveDashboardLoadKey();
  if (!loadKey) {
    return;
  }
  if (!options.force) {
    if (activeDashboardLoadKey.value === loadKey || lastLoadedDashboardKey.value === loadKey) {
      return;
    }
  }

  activeDashboardLoadKey.value = loadKey;
  loading.value = true;

  try {
    const [
      tenantsResult,
      customersResult,
      employeesResult,
      subcontractorsResult,
      ordersResult,
      shiftsResult,
      noticesResult,
    ] = await Promise.allSettled([
      isPlatformAdmin.value
        ? listTenants(accessToken.value, 'platform_admin')
        : Promise.resolve([] as TenantListItem[]),
      canLoadTenantData.value
        ? listCustomers(tenantScopeId.value, accessToken.value, {})
        : Promise.resolve([] as CustomerListItem[]),
      canLoadTenantData.value
        ? listEmployees(tenantScopeId.value, accessToken.value, {})
        : Promise.resolve([] as EmployeeListItem[]),
      canLoadTenantData.value
        ? listSubcontractors(tenantScopeId.value, accessToken.value, {})
        : Promise.resolve([] as SubcontractorListItem[]),
      canLoadTenantData.value
        ? listCustomerOrders(tenantScopeId.value, accessToken.value, {})
        : Promise.resolve([] as CustomerOrderListItem[]),
      canLoadTenantData.value
        ? listShifts(tenantScopeId.value, accessToken.value, {})
        : Promise.resolve([] as ShiftListItem[]),
      canLoadTenantData.value
        ? listAdminNotices(tenantScopeId.value, accessToken.value)
        : Promise.resolve([] as NoticeListItem[]),
    ]);

    dashboardData.tenants =
      tenantsResult.status === 'fulfilled' ? tenantsResult.value : [];
    dashboardData.customers =
      customersResult.status === 'fulfilled' ? customersResult.value : [];
    dashboardData.employees =
      employeesResult.status === 'fulfilled' ? employeesResult.value : [];
    dashboardData.subcontractors =
      subcontractorsResult.status === 'fulfilled'
        ? subcontractorsResult.value
        : [];
    dashboardData.orders =
      ordersResult.status === 'fulfilled'
        ? sortByDateDesc(ordersResult.value, getOrderDate)
        : [];
    dashboardData.shifts =
      shiftsResult.status === 'fulfilled'
        ? sortByDateDesc(shiftsResult.value, getShiftDate)
        : [];
    dashboardData.notices =
      noticesResult.status === 'fulfilled'
        ? sortByDateDesc(noticesResult.value, (notice) => notice.published_at)
        : [];
    lastLoadedDashboardKey.value = loadKey;
    void loadCalendarCoverageForVisibleMonth();
  } finally {
    loading.value = false;
    if (activeDashboardLoadKey.value === loadKey) {
      activeDashboardLoadKey.value = '';
    }
  }
}

async function ensureDashboardSessionReady() {
  legacyAuthStore.syncFromPrimarySession();
  if (!accessToken.value && !legacyAuthStore.refreshToken) {
    return false;
  }
  try {
    await legacyAuthStore.ensureSessionReady();
    return Boolean(accessToken.value);
  } catch {
    return false;
  }
}

async function recoverSessionAndLoadDashboard() {
  if (!dashboardBootstrapComplete.value) {
    return;
  }
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') {
    return;
  }
  const sessionReady = await ensureDashboardSessionReady();
  if (!sessionReady) {
    return;
  }
  await loadDashboard();
  await loadCalendarCoverageForVisibleMonth();
}

function handleVisibilityChange() {
  if (!isRouteCachePaneActive.value) {
    return;
  }
  if (document.visibilityState === 'visible') {
    void recoverSessionAndLoadDashboard();
  }
}

function handleWindowFocus() {
  if (!isRouteCachePaneActive.value) {
    return;
  }
  void recoverSessionAndLoadDashboard();
}

const metricCards = computed(() => {
  const activeTenants = dashboardData.tenants.filter(
    (tenant) => tenant.status === 'active',
  ).length;
  return [
    {
      icon: 'lucide:building-2',
      label: $t('sicherplan.dashboardView.metrics.tenants'),
      subtitle: $t('sicherplan.dashboardView.metricHints.tenants'),
      value: dashboardData.tenants.length.toString(),
    },
    {
      icon: 'lucide:badge-check',
      label: $t('sicherplan.dashboardView.metrics.activeTenants'),
      subtitle: $t('sicherplan.dashboardView.metricHints.activeTenants'),
      value: activeTenants.toString(),
    },
    {
      icon: 'lucide:layout-grid',
      label: $t('sicherplan.dashboardView.metrics.adminSurfaces'),
      subtitle: $t('sicherplan.dashboardView.metricHints.adminSurfaces'),
      value: '4',
    },
  ];
});

const operationsItems = computed(() =>
  isPlatformAdmin.value
    ? dashboardData.tenants.slice(0, 5).map((tenant) => ({
        id: tenant.id,
        meta: tenant.code,
        route: '/admin/core',
        status: tenant.status,
        subtitle: tenant.code,
        title: tenant.name,
      }))
    : dashboardData.orders.slice(0, 5).map((order) => ({
        id: order.id,
        meta: formatDate(getOrderDate(order)),
        route: '/admin/planning-orders',
        status: order.release_state,
        subtitle: order.order_no,
        title: order.title,
      })),
);

const partnerItems = computed(() => {
  if (isPlatformAdmin.value) {
    if (dashboardData.notices.length > 0) {
      return dashboardData.notices.slice(0, 5).map((notice) => ({
        id: notice.id,
        meta: formatDate(notice.published_at),
        route: '/admin/platform-services',
        status: notice.status,
        subtitle: notice.language_code.toUpperCase(),
        title: notice.title,
      }));
    }

    return [
      {
        id: 'platform-services',
        meta: $t('sicherplan.dashboardView.labels.platform'),
        route: '/admin/platform-services',
        status: $t('sicherplan.dashboardView.labels.live'),
        subtitle: $t('sicherplan.dashboardView.actions.morePlatform'),
        title: $t('sicherplan.admin.platformServices'),
      },
      {
        id: 'tenant-users',
        meta: $t('sicherplan.dashboardView.labels.iam'),
        route: '/admin/iam/users',
        status: $t('sicherplan.dashboardView.labels.secured'),
        subtitle: $t('sicherplan.dashboardView.actions.moreUsers'),
        title: $t('sicherplan.admin.tenantUsers'),
      },
      {
        id: 'health',
        meta: $t('sicherplan.dashboardView.labels.support'),
        route: '/admin/health',
        status: $t('sicherplan.dashboardView.labels.ready'),
        subtitle: $t('sicherplan.dashboardView.actions.moreHealth'),
        title: $t('sicherplan.admin.health'),
      },
    ];
  }

  return dashboardData.subcontractors.slice(0, 5).map((partner) => ({
    id: partner.id,
    meta: partner.subcontractor_number,
    route: '/admin/subcontractors',
    status: partner.status,
    subtitle: partner.display_name || partner.legal_name,
    title: partner.legal_name,
  }));
});

const scheduleSummary = computed(() => {
  const scheduledShifts = dashboardData.shifts.filter((shift) =>
    Boolean(getShiftDate(shift)),
  ).length;
  return [
    {
      label: $t('sicherplan.dashboardView.metrics.shifts'),
      value: scheduledShifts.toString(),
    },
    {
      label: $t('sicherplan.dashboardView.metrics.orders'),
      value: dashboardData.orders.length.toString(),
    },
    {
      label: $t('sicherplan.dashboardView.metrics.notices'),
      value: dashboardData.notices.length.toString(),
    },
  ];
});

const weekDayLabels = computed(() => {
  const monday = new Date(Date.UTC(2026, 2, 23));
  return Array.from({ length: 7 }, (_, index) =>
    formatDateLabel(
      new Date(
        monday.getUTCFullYear(),
        monday.getUTCMonth(),
        monday.getUTCDate() + index,
      ),
      { weekday: 'short' },
    ),
  );
});

const calendarCells = computed<CalendarCell[]>(() => {
  const current = activeDate.value;
  const year = current.getFullYear();
  const month = current.getMonth();
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const startDate = new Date(year, month, 1 - startOffset);
  const todayKey = buildCalendarDayKey(new Date());

  const shiftCountByDay = new Map<string, number>();
  dashboardData.shifts.forEach((shift) => {
    const source = getShiftDate(shift);
    if (!source) {
      return;
    }
    const date = new Date(source);
    const key = buildCalendarDayKey(date);
    shiftCountByDay.set(key, (shiftCountByDay.get(key) ?? 0) + 1);
  });

  const orderCountByDay = new Map<string, number>();
  dashboardData.orders.forEach((order) => {
    const source = getOrderDate(order);
    if (!source) {
      return;
    }
    const date = new Date(source);
    const key = buildCalendarDayKey(date);
    orderCountByDay.set(key, (orderCountByDay.get(key) ?? 0) + 1);
  });

  return Array.from({ length: 35 }, (_, index) => {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + index);
    const key = buildCalendarDayKey(date);
    const items = calendarCoverageItemsByDay.value.get(key) ?? [];
    const isExpanded = expandedCalendarDays.value.includes(key);
    const visibleItems = isExpanded ? items : items.slice(0, 2);
    return {
      date,
      dayLabel: String(date.getDate()),
      inMonth: date.getMonth() === month,
      isToday: key === todayKey,
      items,
      key,
      moreCount: Math.max(items.length - visibleItems.length, 0),
      orderCount: orderCountByDay.get(key) ?? 0,
      shiftCount: shiftCountByDay.get(key) ?? 0,
      visibleItems,
    };
  });
});

const calendarPanelCells = computed(() =>
  calendarCells.value.map((cell) => ({
    dateKey: buildCalendarDayKey(cell.date),
    dayLabel: cell.dayLabel,
    inMonth: cell.inMonth,
    isToday: cell.isToday,
    moreCount: cell.moreCount,
    orderCount: cell.orderCount,
    shiftCount: cell.shiftCount,
    visibleItems: cell.visibleItems.map((item) => ({
      key: item.key,
      label: item.label,
      route: item.route,
      tone: item.tone,
      coverageStateLabel: buildCoverageStateLabel(item.coverageState),
    })),
  })),
);

const monthLabel = computed(() =>
  formatDateLabel(activeDate.value, {
    month: 'long',
    year: 'numeric',
  }),
);

const todayMeta = computed(() => ({
  full: formatDateLabel(activeDate.value, {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }),
  weekday: formatDateLabel(activeDate.value, {
    weekday: 'long',
  }),
}));

function statusColor(status: string) {
  switch (status) {
    case 'active':
    case 'released':
    case 'published':
    case 'ready':
    case 'live': {
      return 'success';
    }
    case 'draft':
    case 'planned':
    case 'warning': {
      return 'gold';
    }
    case 'inactive':
    case 'archived': {
      return 'default';
    }
    default: {
      return 'blue';
    }
  }
}

function shiftCalendar(direction: 'next' | 'prev') {
  const nextDate = new Date(activeDate.value);
  nextDate.setMonth(nextDate.getMonth() + (direction === 'next' ? 1 : -1));
  activeDate.value = nextDate;
  expandedCalendarDays.value = [];
}

onMounted(() => {
  legacyAuthStore.syncFromPrimarySession();
  document.addEventListener('visibilitychange', handleVisibilityChange);
  window.addEventListener('focus', handleWindowFocus);
  void (async () => {
    try {
      const sessionReady = await ensureDashboardSessionReady();
      if (!sessionReady) {
        return;
      }
      await loadDashboard();
    } finally {
      dashboardBootstrapComplete.value = true;
      await nextTick();
      dashboardSessionWatchArmed.value = true;
    }
  })();
});

watch(
  () =>
    [
      accessToken.value,
      tenantScopeId.value,
      isPlatformAdmin.value,
      legacyAuthStore.effectiveRole,
      legacyAuthStore.sessionUser?.tenant_id,
    ] as const,
  async () => {
    if (!dashboardBootstrapComplete.value || !dashboardSessionWatchArmed.value) {
      return;
    }
    const loadKey = resolveDashboardLoadKey();
    if (!loadKey) {
      lastLoadedDashboardKey.value = '';
      activeDashboardLoadKey.value = '';
      resetDashboardData();
      resetCalendarCoverage();
      return;
    }
    await loadDashboard();
  },
);

watch(
  visibleCalendarMonthKey,
  () => {
    if (!dashboardBootstrapComplete.value || !canLoadTenantData.value) {
      return;
    }
    void loadCalendarCoverageForVisibleMonth();
  },
);

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  window.removeEventListener('focus', handleWindowFocus);
});
</script>

<template>
  <div class="sp-dashboard">
    <section class="sp-dashboard__metric-row">
      <Card :bordered="false" class="sp-dashboard__date-card">
        <div class="sp-dashboard__metric-head">
          <p class="sp-dashboard__metric-label">
            {{ $t('sicherplan.dashboardView.todayCard.label') }}
          </p>
          <span class="sp-dashboard__metric-icon sp-dashboard__metric-icon--date">
            <IconifyIcon icon="lucide:calendar-days" />
          </span>
        </div>
        <div class="sp-dashboard__date-stack">
          <strong class="sp-dashboard__date-day">{{ todayMeta.weekday }}</strong>
          <span class="sp-dashboard__date-value">{{ todayMeta.full }}</span>
        </div>
        <Space wrap class="sp-dashboard__date-actions">
          <RouterLink to="/admin/planning-shifts">
            <Button type="primary">
              {{ $t('sicherplan.dashboardView.todayCard.primaryAction') }}
            </Button>
          </RouterLink>
          <RouterLink :to="isPlatformAdmin ? '/admin/core' : '/admin/reporting'">
            <Button>{{ $t('sicherplan.dashboardView.todayCard.secondaryAction') }}</Button>
          </RouterLink>
        </Space>
      </Card>

      <Card
        v-for="metric in metricCards"
        :key="metric.label"
        :bordered="false"
        class="sp-dashboard__metric-card"
      >
        <div class="sp-dashboard__metric-head">
          <p class="sp-dashboard__metric-label">{{ metric.label }}</p>
          <span class="sp-dashboard__metric-icon">
            <IconifyIcon :icon="metric.icon" />
          </span>
        </div>
        <strong>{{ metric.value }}</strong>
        <span class="sp-dashboard__metric-subtitle">{{ metric.subtitle }}</span>
      </Card>
    </section>

    <section class="sp-dashboard__middle-grid">
      <Card :bordered="false" class="sp-dashboard__panel-card">
        <div class="sp-dashboard__panel-head">
          <SectionHeader
            :description="$t(isPlatformAdmin ? 'sicherplan.dashboardView.operations.platformDescription' : 'sicherplan.dashboardView.operations.description')"
            :title="$t(isPlatformAdmin ? 'sicherplan.dashboardView.operations.platformTitle' : 'sicherplan.dashboardView.operations.title')"
          />
          <RouterLink :to="isPlatformAdmin ? '/admin/core' : '/admin/planning-orders'">
            {{ $t('sicherplan.dashboardView.actions.more') }}
          </RouterLink>
        </div>

        <div v-if="operationsItems.length" class="sp-dashboard__list">
          <RouterLink
            v-for="item in operationsItems"
            :key="item.id"
            :to="item.route"
            class="sp-dashboard__list-row"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.subtitle }}</p>
            </div>
            <div class="sp-dashboard__list-meta">
              <span>{{ item.meta }}</span>
              <Tag :color="statusColor(item.status)">{{ item.status }}</Tag>
            </div>
          </RouterLink>
        </div>
        <EmptyState
          v-else
          :description="$t('sicherplan.dashboardView.empty.operationsBody')"
          :title="$t('sicherplan.dashboardView.empty.operationsTitle')"
        />
      </Card>

      <Card :bordered="false" class="sp-dashboard__panel-card">
        <div class="sp-dashboard__panel-head">
          <SectionHeader
            :description="$t(isPlatformAdmin ? 'sicherplan.dashboardView.partners.platformDescription' : 'sicherplan.dashboardView.partners.description')"
            :title="$t(isPlatformAdmin ? 'sicherplan.dashboardView.partners.platformTitle' : 'sicherplan.dashboardView.partners.title')"
          />
          <RouterLink :to="isPlatformAdmin ? '/admin/platform-services' : '/admin/subcontractors'">
            {{ $t('sicherplan.dashboardView.actions.more') }}
          </RouterLink>
        </div>

        <div v-if="partnerItems.length" class="sp-dashboard__list">
          <RouterLink
            v-for="item in partnerItems"
            :key="item.id"
            :to="item.route"
            class="sp-dashboard__list-row"
          >
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.subtitle }}</p>
            </div>
            <div class="sp-dashboard__list-meta">
              <span>{{ item.meta }}</span>
              <Tag :color="statusColor(item.status)">{{ item.status }}</Tag>
            </div>
          </RouterLink>
        </div>
        <EmptyState
          v-else
          :description="$t('sicherplan.dashboardView.empty.partnersBody')"
          :title="$t('sicherplan.dashboardView.empty.partnersTitle')"
        />
      </Card>
    </section>

    <DashboardCalendarPanel
      :action-label="$t('sicherplan.dashboardView.calendar.openPlanning')"
      action-to="/admin/planning-shifts"
      :cells="calendarPanelCells"
      :description="$t('sicherplan.dashboardView.calendar.description')"
      :loading="calendarLoading"
      :loading-label="$t('sicherplan.dashboardView.calendar.loading')"
      :month-hint="$t('sicherplan.dashboardView.calendar.monthHint')"
      :month-label="monthLabel"
      :more-label="$t('sicherplan.dashboardView.calendar.more')"
      :next-label="$t('sicherplan.dashboardView.calendar.next')"
      :order-short-label="$t('sicherplan.dashboardView.calendar.orderShort')"
      :previous-label="$t('sicherplan.dashboardView.calendar.previous')"
      :shift-short-label="$t('sicherplan.dashboardView.calendar.shiftShort')"
      :summary="scheduleSummary"
      :title="$t('sicherplan.dashboardView.calendar.title')"
      :week-day-labels="weekDayLabels"
      @shift-calendar="shiftCalendar"
      @toggle-day="toggleCalendarDay"
    />
    <div
      v-if="calendarError"
      class="sp-dashboard__calendar-error"
      data-testid="dashboard-calendar-error"
    >
      {{ calendarError }}
    </div>
  </div>
</template>

<style scoped>
.sp-dashboard {
  display: grid;
  gap: 1.25rem;
  padding: 1.25rem;
  background:
    radial-gradient(circle at top left, rgb(40 170 170 / 0.08), transparent 30%),
    linear-gradient(180deg, rgb(255 255 255 / 0.5), transparent 24rem),
    var(--sp-page-background);
}

[data-theme='dark'] .sp-dashboard {
  background:
    radial-gradient(circle at top left, rgb(35 200 205 / 0.1), transparent 30%),
    linear-gradient(180deg, rgb(10 20 22 / 0.45), transparent 26rem),
    var(--sp-page-background);
}

.sp-dashboard__date-card,
.sp-dashboard__metric-card,
.sp-dashboard__panel-card,
.sp-dashboard__calendar-card {
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1.25rem;
  box-shadow: var(--sp-shadow-card);
}

.sp-dashboard__metric-row {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.15fr) repeat(3, minmax(0, 1fr));
}

.sp-dashboard__metric-card,
.sp-dashboard__panel-card,
.sp-dashboard__calendar-card {
  background: linear-gradient(180deg, rgb(255 255 255 / 0.96), rgb(255 255 255 / 0.84));
}

[data-theme='dark'] .sp-dashboard__metric-card,
[data-theme='dark'] .sp-dashboard__panel-card,
[data-theme='dark'] .sp-dashboard__calendar-card {
  background: linear-gradient(180deg, rgb(13 24 26 / 0.98), rgb(13 24 26 / 0.9));
}

.sp-dashboard__date-card {
  display: grid;
  gap: 0.9rem;
  min-height: 11.5rem;
  padding: 1.2rem 1.15rem;
  background: var(--sp-color-primary-strong);
}

[data-theme='dark'] .sp-dashboard__date-card {
  background: var(--sp-color-primary);
}

.sp-dashboard__metric-card {
  display: grid;
  align-content: start;
  gap: 0.72rem;
  min-height: 11.5rem;
  padding: 1.2rem 1.15rem;
}

.sp-dashboard__metric-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.sp-dashboard__metric-label {
  margin: 0;
  color: var(--sp-color-text-secondary);
  font-size: 0.84rem;
  font-weight: 600;
}

.sp-dashboard__metric-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.95rem;
  background: rgb(240 244 248 / 0.95);
  color: var(--sp-color-text-primary);
  font-size: 1rem;
}

.sp-dashboard__metric-card strong {
  color: var(--sp-color-text-primary);
  font-size: clamp(2rem, 2.6vw, 2.5rem);
  line-height: 1;
}

.sp-dashboard__metric-subtitle {
  color: var(--sp-color-text-secondary);
  font-size: 0.84rem;
  line-height: 1.5;
}

.sp-dashboard__date-card .sp-dashboard__metric-label,
.sp-dashboard__date-card .sp-dashboard__metric-icon,
.sp-dashboard__date-day,
.sp-dashboard__date-value {
  color: white;
}

.sp-dashboard__date-card .sp-dashboard__metric-icon {
  background: rgb(255 255 255 / 0.16);
}

.sp-dashboard__date-stack {
  display: grid;
  gap: 0.3rem;
}

.sp-dashboard__date-day {
  font-size: 1.35rem;
  font-weight: 700;
}

.sp-dashboard__date-value {
  line-height: 1.55;
}

.sp-dashboard__date-actions {
  margin-top: 0.2rem;
}

.sp-dashboard__date-actions :deep(.ant-btn) {
  height: 2.35rem;
  padding-inline: 1rem;
  border-radius: 999px;
  box-shadow: none;
}

.sp-dashboard__panel-card,
.sp-dashboard__calendar-card {
  padding: 1.25rem;
}

.sp-dashboard__middle-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.sp-dashboard__calendar-error {
  width: fit-content;
  max-width: 100%;
  margin-top: -0.6rem;
  padding: 0.65rem 0.85rem;
  border: 1px solid color-mix(in srgb, var(--sp-color-danger) 28%, var(--sp-color-border-soft));
  border-radius: 0.85rem;
  background: color-mix(in srgb, var(--sp-color-danger) 10%, var(--sp-color-surface-card));
  color: var(--sp-color-danger);
  font-size: 0.85rem;
  font-weight: 700;
}

.sp-dashboard__panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.sp-dashboard__panel-head a {
  color: var(--sp-color-primary-strong);
  font-weight: 600;
  text-decoration: none;
}

.sp-dashboard__list {
  display: grid;
  gap: 0.8rem;
  margin-top: 1rem;
}

.sp-dashboard__list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  color: inherit;
  text-decoration: none;
  background: var(--sp-color-surface-card);
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.sp-dashboard__list-row:hover {
  transform: translateY(-2px);
  border-color: rgb(40 170 170 / 38%);
  box-shadow: var(--sp-shadow-card);
}

.sp-dashboard__list-row strong {
  display: block;
  color: var(--sp-color-text-primary);
}

.sp-dashboard__list-row p,
.sp-dashboard__calendar-topline p {
  margin: 0.32rem 0 0;
  color: var(--sp-color-text-secondary);
}

.sp-dashboard__list-meta {
  display: grid;
  justify-items: end;
  gap: 0.45rem;
  color: var(--sp-color-text-secondary);
  font-size: 0.83rem;
}

.sp-dashboard__calendar-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1rem;
}

.sp-dashboard__calendar-topline strong {
  color: var(--sp-color-text-primary);
  font-size: 1.2rem;
}

.sp-dashboard__summary-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.sp-dashboard__summary-chip {
  min-width: 7rem;
  padding: 0.8rem 0.95rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.sp-dashboard__summary-chip span {
  display: block;
  color: var(--sp-color-text-secondary);
  font-size: 0.78rem;
}

.sp-dashboard__summary-chip strong {
  display: block;
  margin-top: 0.25rem;
}

.sp-dashboard__calendar-grid {
  display: grid;
  gap: 0.65rem;
  margin-top: 1rem;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.sp-dashboard__weekday {
  padding: 0 0.25rem;
  color: var(--sp-color-text-secondary);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.sp-dashboard__calendar-cell {
  display: grid;
  gap: 0.65rem;
  align-content: flex-start;
  min-height: 7.25rem;
  padding: 0.85rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.sp-dashboard__calendar-cell.is-muted {
  opacity: 0.58;
}

.sp-dashboard__calendar-cell.is-today {
  border-color: rgb(40 170 170 / 48%);
  box-shadow: inset 0 0 0 1px rgb(40 170 170 / 22%);
}

.sp-dashboard__calendar-day {
  color: var(--sp-color-text-primary);
  font-weight: 700;
}

.sp-dashboard__calendar-items {
  display: grid;
  gap: 0.4rem;
}

.sp-dashboard__calendar-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.25rem;
  border-radius: 0.4rem;
  color: inherit;
  text-decoration: none;
  background: rgb(246 248 250 / 0.96);
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    transform 0.18s ease;
  border: 1px solid transparent;
}

.sp-dashboard__calendar-item:hover,
.sp-dashboard__calendar-item:focus-visible {
  transform: translateY(-1px);
  border-color: rgb(40 170 170 / 38%);
  box-shadow: var(--sp-shadow-card);
  outline: none;
}

.sp-dashboard__calendar-item--good {
  background: rgb(232 248 247 / 0.96);
}

.sp-dashboard__calendar-item--warn {
  background: rgb(255 246 223 / 0.98);
}

.sp-dashboard__calendar-item--bad {
  background: rgb(252 234 232 / 0.98);
}

.sp-dashboard__calendar-item-marker {
  width: 0.35rem;
  height: 0.35rem;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.78;
}

.sp-dashboard__calendar-item--good .sp-dashboard__calendar-item-marker {
  color: rgb(17 119 119);
}

.sp-dashboard__calendar-item--warn .sp-dashboard__calendar-item-marker {
  color: rgb(149 97 18);
}

.sp-dashboard__calendar-item--bad .sp-dashboard__calendar-item-marker {
  color: rgb(172 54 41);
}

.sp-dashboard__calendar-item-label {
  color: var(--sp-color-text-primary);
  font-size: 0.55rem;
  font-weight: 600;
  line-height: 1;
  min-width: 0;
}

.sp-dashboard__calendar-more {
  width: fit-content;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--sp-color-primary-strong);
  font-size: 0.76rem;
  font-weight: 700;
  cursor: pointer;
}

.sp-dashboard__calendar-more:hover,
.sp-dashboard__calendar-more:focus-visible {
  text-decoration: underline;
  outline: none;
}

.sp-dashboard__calendar-events {
  display: grid;
  gap: 0.45rem;
}

.sp-dashboard__calendar-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 0.14rem 0.45rem 0.14rem 0.25rem;
  border-radius: 999px;
  font-size: 0.6rem;
  font-weight: 700;
}

.sp-dashboard__calendar-pill--teal {
  background: rgb(214 245 243);
  color: rgb(17 119 119);
}

.sp-dashboard__calendar-pill--amber {
  background: rgb(255 239 196);
  color: rgb(149 97 18);
}

[data-theme='dark'] .sp-dashboard__calendar-pill--teal {
  background: rgb(13 51 53);
  color: rgb(126 225 225);
}

[data-theme='dark'] .sp-dashboard__calendar-pill--amber {
  background: rgb(69 50 13);
  color: rgb(255 214 117);
}

[data-theme='dark'] .sp-dashboard__calendar-item {
  background: rgb(24 33 35 / 0.96);
}

[data-theme='dark'] .sp-dashboard__calendar-item--good {
  background: rgb(14 42 43 / 0.98);
}

[data-theme='dark'] .sp-dashboard__calendar-item--warn {
  background: rgb(56 43 18 / 0.98);
}

[data-theme='dark'] .sp-dashboard__calendar-item--bad {
  background: rgb(70 29 26 / 0.98);
}

[data-theme='dark'] .sp-dashboard__calendar-item--good .sp-dashboard__calendar-item-marker {
  color: rgb(126 225 225);
}

[data-theme='dark'] .sp-dashboard__calendar-item--warn .sp-dashboard__calendar-item-marker {
  color: rgb(255 214 117);
}

[data-theme='dark'] .sp-dashboard__calendar-item--bad .sp-dashboard__calendar-item-marker {
  color: rgb(255 151 136);
}

@media (max-width: 1280px) {
  .sp-dashboard__metric-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sp-dashboard__middle-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .sp-dashboard {
    padding: 1rem;
  }

  .sp-dashboard__calendar-topline {
    display: grid;
    grid-template-columns: 1fr;
  }

  .sp-dashboard__metric-row,
  .sp-dashboard__calendar-grid {
    grid-template-columns: 1fr;
  }

  .sp-dashboard__weekday {
    display: none;
  }

  .sp-dashboard__calendar-cell {
    min-height: auto;
  }

  .sp-dashboard__list-row,
  .sp-dashboard__panel-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .sp-dashboard__list-meta {
    justify-items: start;
  }
}
</style>
