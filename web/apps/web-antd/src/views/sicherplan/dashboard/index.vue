<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';

import { IconifyIcon } from '@vben/icons';
import { preferences } from '@vben/preferences';
import { useAccessStore, useUserStore } from '@vben/stores';
import { Button, Card, Space, Tag } from 'ant-design-vue';

import { $t } from '#/locales';
import EmptyState from '#/components/sicherplan/empty-state.vue';
import SectionHeader from '#/components/sicherplan/section-header.vue';
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
  listSubcontractors,
  type SubcontractorListItem,
} from '#/sicherplan-legacy/api/subcontractors';

defineOptions({ name: 'SicherPlanDashboard' });

interface CalendarCell {
  date: Date;
  dayLabel: string;
  inMonth: boolean;
  isToday: boolean;
  orderCount: number;
  shiftCount: number;
}

const accessStore = useAccessStore();
const legacyAuthStore = useLegacyAuthStore();
const userStore = useUserStore();

const loading = ref(false);
const activeDate = ref(new Date());

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

async function loadDashboard() {
  if (!accessToken.value) {
    return;
  }

  loading.value = true;

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

  loading.value = false;
}

const topBadges = computed(() =>
  isPlatformAdmin.value
    ? [
        { key: 'Platform Admin', tone: 'success' as const },
        { key: 'Core Admin', tone: 'default' as const },
        { key: 'Health Ready', tone: 'warning' as const },
      ]
    : [
        { key: 'Tenant Ops', tone: 'success' as const },
        { key: 'Planning', tone: 'default' as const },
        { key: 'Reporting', tone: 'warning' as const },
      ],
);

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

const quickActions = computed(() =>
  isPlatformAdmin.value
    ? [
        {
          label: $t('sicherplan.admin.core'),
          to: '/admin/core',
          type: 'primary' as const,
        },
        {
          label: $t('sicherplan.admin.tenantUsers'),
          to: '/admin/iam/users',
          type: 'default' as const,
        },
        {
          label: $t('sicherplan.admin.health'),
          to: '/admin/health',
          type: 'default' as const,
        },
      ]
    : [
        {
          label: $t('sicherplan.admin.customers'),
          to: '/admin/customers',
          type: 'primary' as const,
        },
        {
          label: $t('sicherplan.admin.planningShifts'),
          to: '/admin/planning-shifts',
          type: 'default' as const,
        },
        {
          label: $t('sicherplan.admin.reporting'),
          to: '/admin/reporting',
          type: 'default' as const,
        },
      ],
);

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
  const todayKey = new Date().toDateString();

  const shiftCountByDay = new Map<string, number>();
  dashboardData.shifts.forEach((shift) => {
    const source = getShiftDate(shift);
    if (!source) {
      return;
    }
    const date = new Date(source);
    const key = date.toDateString();
    shiftCountByDay.set(key, (shiftCountByDay.get(key) ?? 0) + 1);
  });

  const orderCountByDay = new Map<string, number>();
  dashboardData.orders.forEach((order) => {
    const source = getOrderDate(order);
    if (!source) {
      return;
    }
    const date = new Date(source);
    const key = date.toDateString();
    orderCountByDay.set(key, (orderCountByDay.get(key) ?? 0) + 1);
  });

  return Array.from({ length: 35 }, (_, index) => {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + index);
    const key = date.toDateString();
    return {
      date,
      dayLabel: String(date.getDate()),
      inMonth: date.getMonth() === month,
      isToday: key === todayKey,
      orderCount: orderCountByDay.get(key) ?? 0,
      shiftCount: shiftCountByDay.get(key) ?? 0,
    };
  });
});

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
}

onMounted(() => {
  void loadDashboard();
});
</script>

<template>
  <div class="sp-dashboard">
    <section class="sp-dashboard__top-row">
      <Card :bordered="false" class="sp-dashboard__summary-card">
        <div class="sp-dashboard__summary-head">
          <div class="sp-dashboard__summary-copy">
            <p class="sp-dashboard__eyebrow">{{ $t('sicherplan.dashboardView.eyebrow') }}</p>
            <h1>{{ $t('sicherplan.dashboardView.title') }}</h1>
            <p>{{ $t('sicherplan.dashboardView.description') }}</p>
          </div>
          <div class="sp-dashboard__summary-badges">
            <Tag
              v-for="badge in topBadges"
              :key="badge.key"
              :color="badge.tone === 'success' ? 'success' : badge.tone === 'warning' ? 'gold' : 'default'"
              bordered
            >
              {{ badge.key }}
            </Tag>
          </div>
        </div>
      </Card>

      <Card :bordered="false" class="sp-dashboard__action-card">
        <SectionHeader
          :description="$t('sicherplan.dashboardView.actions.description')"
          :title="$t('sicherplan.dashboardView.actions.title')"
        />
        <div class="sp-dashboard__action-buttons">
          <RouterLink
            v-for="action in quickActions"
            :key="action.to"
            :to="action.to"
          >
            <Button block :type="action.type">
              {{ action.label }}
            </Button>
          </RouterLink>
        </div>
      </Card>
    </section>

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

    <Card :bordered="false" class="sp-dashboard__calendar-card">
      <div class="sp-dashboard__panel-head">
        <SectionHeader
          :description="$t('sicherplan.dashboardView.calendar.description')"
          :title="$t('sicherplan.dashboardView.calendar.title')"
        />
        <Space wrap>
          <Button @click="shiftCalendar('prev')">
            {{ $t('sicherplan.dashboardView.calendar.previous') }}
          </Button>
          <Button @click="shiftCalendar('next')">
            {{ $t('sicherplan.dashboardView.calendar.next') }}
          </Button>
          <RouterLink to="/admin/planning-shifts">
            <Button type="primary">
              {{ $t('sicherplan.dashboardView.calendar.openPlanning') }}
            </Button>
          </RouterLink>
        </Space>
      </div>

      <div class="sp-dashboard__calendar-topline">
        <div>
          <strong>{{ monthLabel }}</strong>
          <p>{{ $t('sicherplan.dashboardView.calendar.monthHint') }}</p>
        </div>
        <div class="sp-dashboard__summary-chips">
          <div
            v-for="summary in scheduleSummary"
            :key="summary.label"
            class="sp-dashboard__summary-chip"
          >
            <span>{{ summary.label }}</span>
            <strong>{{ summary.value }}</strong>
          </div>
        </div>
      </div>

      <div class="sp-dashboard__calendar-grid">
        <div
          v-for="label in weekDayLabels"
          :key="label"
          class="sp-dashboard__weekday"
        >
          {{ label }}
        </div>
        <div
          v-for="cell in calendarCells"
          :key="cell.date.toISOString()"
          class="sp-dashboard__calendar-cell"
          :class="{
            'is-muted': !cell.inMonth,
            'is-today': cell.isToday,
          }"
        >
          <span class="sp-dashboard__calendar-day">{{ cell.dayLabel }}</span>
          <div class="sp-dashboard__calendar-events">
            <span
              v-if="cell.shiftCount"
              class="sp-dashboard__calendar-pill sp-dashboard__calendar-pill--teal"
            >
              {{ cell.shiftCount }} {{ $t('sicherplan.dashboardView.calendar.shiftShort') }}
            </span>
            <span
              v-if="cell.orderCount"
              class="sp-dashboard__calendar-pill sp-dashboard__calendar-pill--amber"
            >
              {{ cell.orderCount }} {{ $t('sicherplan.dashboardView.calendar.orderShort') }}
            </span>
          </div>
        </div>
      </div>
    </Card>
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

.sp-dashboard__summary-card,
.sp-dashboard__date-card,
.sp-dashboard__metric-card,
.sp-dashboard__action-card,
.sp-dashboard__panel-card,
.sp-dashboard__calendar-card {
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1.25rem;
  box-shadow: var(--sp-shadow-card);
}

.sp-dashboard__top-row {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.45fr) minmax(18rem, 0.95fr);
}

.sp-dashboard__metric-row {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.15fr) repeat(3, minmax(0, 1fr));
}

.sp-dashboard__summary-card,
.sp-dashboard__metric-card,
.sp-dashboard__action-card,
.sp-dashboard__panel-card,
.sp-dashboard__calendar-card {
  background: linear-gradient(180deg, rgb(255 255 255 / 0.96), rgb(255 255 255 / 0.84));
}

[data-theme='dark'] .sp-dashboard__summary-card,
[data-theme='dark'] .sp-dashboard__metric-card,
[data-theme='dark'] .sp-dashboard__action-card,
[data-theme='dark'] .sp-dashboard__panel-card,
[data-theme='dark'] .sp-dashboard__calendar-card {
  background: linear-gradient(180deg, rgb(13 24 26 / 0.98), rgb(13 24 26 / 0.9));
}

.sp-dashboard__summary-card {
  min-height: 11.5rem;
  padding: 1.45rem;
}

.sp-dashboard__summary-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.sp-dashboard__summary-copy h1 {
  margin: 0;
  color: var(--sp-color-text-primary);
  font-size: clamp(1.8rem, 2.6vw, 2.6rem);
  line-height: 1.06;
}

.sp-dashboard__summary-copy p:last-child {
  max-width: 42rem;
  margin: 0.75rem 0 0;
  color: var(--sp-color-text-secondary);
  line-height: 1.6;
}

.sp-dashboard__eyebrow {
  margin: 0 0 0.55rem;
  color: var(--sp-color-primary-strong);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.sp-dashboard__summary-badges {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.5rem;
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

.sp-dashboard__action-card,
.sp-dashboard__panel-card,
.sp-dashboard__calendar-card {
  padding: 1.25rem;
}

.sp-dashboard__action-card {
  display: grid;
  align-content: start;
  min-height: 11.5rem;
}

.sp-dashboard__action-buttons {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}

.sp-dashboard__action-buttons a {
  display: block;
}

.sp-dashboard__action-buttons :deep(.ant-btn) {
  height: 2.6rem;
  justify-content: flex-start;
  padding-inline: 1rem;
  border-radius: 999px;
  font-weight: 600;
}

.sp-dashboard__middle-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
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

.sp-dashboard__calendar-events {
  display: grid;
  gap: 0.45rem;
}

.sp-dashboard__calendar-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 0.22rem 0.55rem;
  border-radius: 999px;
  font-size: 0.76rem;
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

@media (max-width: 1280px) {
  .sp-dashboard__top-row {
    grid-template-columns: 1fr;
  }

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

  .sp-dashboard__summary-head,
  .sp-dashboard__calendar-topline {
    display: grid;
    grid-template-columns: 1fr;
  }

  .sp-dashboard__summary-badges {
    justify-content: flex-start;
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
