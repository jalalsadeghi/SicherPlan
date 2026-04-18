<script lang="ts" setup>
import { computed, ref, watch } from "vue";

import { Card, Tag } from "ant-design-vue";

import EmptyState from "#/components/sicherplan/empty-state.vue";
import DashboardCalendarPanel from "#/components/sicherplan/dashboard-calendar-panel.vue";
import {
  buildCoverageShiftLabel,
  buildStaffingCoverageRoute,
} from "#/features/sicherplan/dashboardCoverage.helpers";
import {
  listStaffingCoverage,
  type CoverageFilterParams,
  type CoverageShiftItem,
} from "@/api/planningStaffing";
import {
  coverageTone,
  resolvePlanningStaffingCoverageState,
} from "@/features/planning/planningStaffing.helpers";
import type {
  CustomerDashboardRead,
  CustomerRead,
} from "@/api/customers";
import { useI18n } from "@/i18n";

type DashboardTabId = "overview" | "contacts" | "addresses" | "commercial" | "portal" | "history";

interface StandingSummary {
  label: string;
  tone: "bad" | "good" | "warn";
}

type CustomerDashboardFinanceTone = "good" | "restricted" | "warn";
type CustomerDashboardStandingTone = StandingSummary["tone"];
type LatestPlanStatusTone = "good" | "neutral" | "warn";

interface CalendarCellItem {
  route: string;
  key: string;
  label: string;
  tone: "bad" | "good" | "warn";
  coverageStateLabel: string;
}

interface CalendarCell {
  dateKey: string;
  dayLabel: string;
  inMonth: boolean;
  isToday: boolean;
  visibleItems: CalendarCellItem[];
  moreCount: number;
  shiftCount: number;
  orderCount: number;
}

const props = defineProps<{
  canReadCommercial: boolean;
  canWriteCommercial: boolean;
  canManageContacts: boolean;
  accessToken: string;
  customer: CustomerRead;
  dashboard: CustomerDashboardRead | null;
  error: string;
  loading: boolean;
  standing: StandingSummary;
  tenantId: string;
}>();

const emit = defineEmits<{
  createContact: [];
  createInvoiceParty: [];
  selectTab: [tabId: DashboardTabId];
}>();

const { t, locale } = useI18n();
const activeDate = ref(new Date());
const expandedDays = ref<string[]>([]);
const calendarLoading = ref(false);
const calendarError = ref("");
const coverageMonthItemsByDay = ref<Map<string, CoverageShiftItem[]>>(new Map());
const coverageRequestVersion = ref(0);
const coverageMonthCache = new Map<string, Map<string, CoverageShiftItem[]>>();
const coverageMonthRequests = new Map<string, Promise<Map<string, CoverageShiftItem[]>>>();

const quickActions = computed(() => {
  const actions: Array<{ id: string; label: string; mode: "action" | "tab"; tabId?: DashboardTabId }> = [
    { id: "overview", label: t("customerAdmin.tabs.overview"), mode: "tab", tabId: "overview" },
    { id: "contacts", label: t("customerAdmin.tabs.contacts"), mode: "tab", tabId: "contacts" },
    { id: "addresses", label: t("customerAdmin.tabs.addresses"), mode: "tab", tabId: "addresses" },
    { id: "portal", label: t("customerAdmin.tabs.portal"), mode: "tab", tabId: "portal" },
    { id: "history", label: t("customerAdmin.tabs.history"), mode: "tab", tabId: "history" },
  ];
  if (props.canReadCommercial) {
    actions.splice(3, 0, {
      id: "commercial",
      label: t("customerAdmin.tabs.commercial"),
      mode: "tab",
      tabId: "commercial",
    });
  }
  return actions;
});

const actionShortcuts = computed(() => {
  const actions: Array<{ id: string; label: string; type: "contact" | "invoice_party" }> = [];
  if (props.canManageContacts) {
    actions.push({ id: "add-contact", label: t("customerAdmin.actions.addContact"), type: "contact" });
  }
  if (props.canWriteCommercial) {
    actions.push({ id: "add-invoice-party", label: t("customerAdmin.actions.addInvoiceParty"), type: "invoice_party" });
  }
  return actions;
});

const latestPlans = computed(() => props.dashboard?.planning_summary.latest_plans ?? []);

function resolveLatestPlanStatusTone(status: string): LatestPlanStatusTone {
  switch (status) {
    case "released":
      return "good";
    case "draft":
    case "release_ready":
      return "warn";
    default:
      return "neutral";
  }
}

function resolveLatestPlanTagColor(status: string) {
  switch (resolveLatestPlanStatusTone(status)) {
    case "good":
      return "success";
    case "warn":
      return "gold";
    default:
      return "default";
  }
}

const tenureLabel = computed(() => {
  if (!props.customer.created_at) {
    return t("customerAdmin.summary.none");
  }
  const createdAt = new Date(props.customer.created_at);
  const diffDays = Math.max(0, Math.floor((Date.now() - createdAt.getTime()) / 86_400_000));
  if (diffDays < 31) {
    return t("customerAdmin.dashboard.tenureDays", { count: diffDays });
  }
  if (diffDays < 365) {
    return t("customerAdmin.dashboard.tenureMonths", { count: Math.max(1, Math.floor(diffDays / 30)) });
  }
  return t("customerAdmin.dashboard.tenureYears", { count: Math.max(1, Math.floor(diffDays / 365)) });
});

const financeValue = computed(() => {
  const financeSummary = props.dashboard?.finance_summary;
  if (!financeSummary) {
    return t("customerAdmin.dashboard.financeUnavailable");
  }
  if (financeSummary.visibility === "restricted") {
    return t("customerAdmin.dashboard.financeRestricted");
  }
  if (financeSummary.visibility === "unavailable" || financeSummary.total_received_amount == null || !financeSummary.currency_code) {
    return t("customerAdmin.dashboard.financeUnavailable");
  }
  const amount = Number(financeSummary.total_received_amount);
  if (!Number.isFinite(amount)) {
    return t("customerAdmin.dashboard.financeUnavailable");
  }
  return new Intl.NumberFormat(locale.value, {
    style: "currency",
    currency: financeSummary.currency_code,
  }).format(amount);
});

const financeTone = computed<CustomerDashboardFinanceTone>(() => {
  const financeSummary = props.dashboard?.finance_summary;
  if (financeSummary?.visibility === "restricted") {
    return "restricted";
  }
  if (!financeSummary || financeSummary.visibility === "unavailable") {
    return "warn";
  }
  if (financeSummary.total_received_amount == null || !financeSummary.currency_code) {
    return "warn";
  }
  const amount = Number(financeSummary.total_received_amount);
  return Number.isFinite(amount) ? "good" : "warn";
});

const financeMeta = computed(() => {
  const financeSummary = props.dashboard?.finance_summary;
  if (!financeSummary?.semantic_label) {
    return "";
  }
  return t(`customerAdmin.dashboard.financeLabels.${financeSummary.semantic_label}` as never);
});

const standingTone = computed<CustomerDashboardStandingTone>(() => {
  return props.standing.tone === "good" || props.standing.tone === "warn" ? props.standing.tone : "bad";
});

const weekDayLabels = computed(() => {
  const monday = new Date(Date.UTC(2026, 2, 23));
  return Array.from({ length: 7 }, (_, index) =>
    new Intl.DateTimeFormat(locale.value, { weekday: "short" }).format(
      new Date(monday.getUTCFullYear(), monday.getUTCMonth(), monday.getUTCDate() + index),
    ),
  );
});

const monthLabel = computed(() =>
  new Intl.DateTimeFormat(locale.value, { month: "long", year: "numeric" }).format(activeDate.value),
);

const coverageRows = computed(() => [...coverageMonthItemsByDay.value.values()].flat());

const calendarSummary = computed(() => {
  const items = coverageRows.value;
  const atRiskCount = items.filter(
    (item) => resolvePlanningStaffingCoverageState(item.coverage_state, item.demand_groups) !== "green",
  ).length;
  return [
    {
      label: t("customerAdmin.dashboard.calendarSummary.shifts"),
      value: String(items.length),
    },
    {
      label: t("customerAdmin.dashboard.calendarSummary.orders"),
      value: String(new Set(items.map((item) => item.order_id).filter(Boolean)).size),
    },
    {
      label: t("customerAdmin.dashboard.calendarSummary.atRisk"),
      value: String(atRiskCount),
    },
  ];
});

const calendarCells = computed(() => {
  const current = activeDate.value;
  const year = current.getFullYear();
  const month = current.getMonth();
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const startDate = new Date(year, month, 1 - startOffset);
  const todayKey = buildDayKey(new Date());
  return Array.from({ length: 35 }, (_, index): CalendarCell => {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + index);
    const dayKey = buildDayKey(date);
    const items = coverageMonthItemsByDay.value.get(dayKey) ?? [];
    const isExpanded = expandedDays.value.includes(dayKey);
    const visibleItems = (isExpanded ? items : items.slice(0, 2)).map((item) => ({
      key: item.shift_id,
      label: buildCoverageShiftLabel(item, locale.value),
      route: buildStaffingCoverageRoute(item),
      tone: coverageTone(
        resolvePlanningStaffingCoverageState(item.coverage_state, item.demand_groups),
      ) as CalendarCellItem["tone"],
      coverageStateLabel: resolveStateLabel(item.coverage_state, item.demand_groups),
    }));
    return {
      dateKey: dayKey,
      dayLabel: String(date.getDate()),
      inMonth: date.getMonth() === month,
      isToday: dayKey === todayKey,
      visibleItems,
      moreCount: Math.max(items.length - visibleItems.length, 0),
      shiftCount: items.length,
      orderCount: new Set(items.map((item) => item.order_id).filter(Boolean)).size,
    };
  });
});

function buildDayKey(value: Date) {
  return value.toDateString();
}

function resolveStateLabel(coverageState: string, demandGroups: CoverageShiftItem["demand_groups"]) {
  const resolvedState = resolvePlanningStaffingCoverageState(coverageState, demandGroups);
  if (resolvedState === "green") {
    return t("customerAdmin.dashboard.calendarStatus.good");
  }
  if (resolvedState === "yellow") {
    return t("customerAdmin.dashboard.calendarStatus.warn");
  }
  if (resolvedState === "setup_required") {
    return t("customerAdmin.dashboard.calendarStatus.setupRequired");
  }
  return t("customerAdmin.dashboard.calendarStatus.bad");
}

function formatDateTimeLocalValue(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const hours = String(value.getHours()).padStart(2, "0");
  const minutes = String(value.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function visibleCalendarMonthStart(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), 1, 0, 0, 0, 0);
}

function visibleCalendarMonthEnd(value: Date) {
  return new Date(value.getFullYear(), value.getMonth() + 1, 0, 23, 59, 0, 0);
}

function resolveCoverageMonthKey() {
  if (!props.tenantId || !props.accessToken || !props.customer.id) {
    return "";
  }
  return [
    props.tenantId,
    props.customer.id,
    formatDateTimeLocalValue(visibleCalendarMonthStart(activeDate.value)),
    formatDateTimeLocalValue(visibleCalendarMonthEnd(activeDate.value)),
  ].join(":");
}

function buildCoverageItemsByDay(coverageRows: CoverageShiftItem[]) {
  const itemsByDay = new Map<string, CoverageShiftItem[]>();
  [...coverageRows]
    .sort((left, right) => new Date(left.starts_at).getTime() - new Date(right.starts_at).getTime())
    .forEach((coverageRow) => {
      const key = buildDayKey(new Date(coverageRow.starts_at));
      itemsByDay.set(key, [...(itemsByDay.get(key) ?? []), coverageRow]);
    });
  return itemsByDay;
}

async function loadCoverageForVisibleMonth(options: { force?: boolean } = {}) {
  const monthKey = resolveCoverageMonthKey();
  if (!monthKey) {
    coverageMonthItemsByDay.value = new Map();
    calendarError.value = "";
    return;
  }

  const cached = coverageMonthCache.get(monthKey);
  if (cached && !options.force) {
    coverageMonthItemsByDay.value = cached;
    calendarError.value = "";
    return;
  }

  coverageMonthItemsByDay.value = cached ?? new Map();
  calendarLoading.value = true;
  calendarError.value = "";

  let request = coverageMonthRequests.get(monthKey);
  if (!request || options.force) {
    const filters: CoverageFilterParams = {
      customer_id: props.customer.id,
      date_from: formatDateTimeLocalValue(visibleCalendarMonthStart(activeDate.value)),
      date_to: formatDateTimeLocalValue(visibleCalendarMonthEnd(activeDate.value)),
    };
    request = listStaffingCoverage(props.tenantId, props.accessToken, filters).then((rows) => buildCoverageItemsByDay(rows));
    coverageMonthRequests.set(monthKey, request);
    void request.finally(() => {
      if (coverageMonthRequests.get(monthKey) === request) {
        coverageMonthRequests.delete(monthKey);
      }
    });
  }

  const requestVersion = ++coverageRequestVersion.value;
  try {
    const itemsByDay = await request;
    coverageMonthCache.set(monthKey, itemsByDay);
    if (requestVersion !== coverageRequestVersion.value || resolveCoverageMonthKey() !== monthKey) {
      return;
    }
    coverageMonthItemsByDay.value = itemsByDay;
  } catch {
    if (requestVersion !== coverageRequestVersion.value || resolveCoverageMonthKey() !== monthKey) {
      return;
    }
    coverageMonthItemsByDay.value = new Map();
    calendarError.value = t("customerAdmin.dashboard.calendarLoadError");
  } finally {
    if (requestVersion === coverageRequestVersion.value) {
      calendarLoading.value = false;
    }
  }
}

function shiftCalendar(direction: "next" | "prev") {
  const nextDate = new Date(activeDate.value);
  nextDate.setMonth(nextDate.getMonth() + (direction === "next" ? 1 : -1));
  activeDate.value = nextDate;
  expandedDays.value = [];
}

function toggleCalendarDay(dateKey: string) {
  if (expandedDays.value.includes(dateKey)) {
    expandedDays.value = expandedDays.value.filter((value) => value !== dateKey);
    return;
  }
  expandedDays.value = [...expandedDays.value, dateKey];
}

function selectTab(tabId: DashboardTabId) {
  emit("selectTab", tabId);
}

function triggerShortcut(type: "contact" | "invoice_party") {
  if (type === "contact") {
    emit("createContact");
    return;
  }
  emit("createInvoiceParty");
}

function formatPlanWindow(plan: CustomerDashboardRead["planning_summary"]["latest_plans"][number]) {
  const formatDate = (value: string) =>
    new Intl.DateTimeFormat(locale.value, {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }).format(new Date(value));
  return `${formatDate(plan.planning_from)}${plan.planning_to ? ` → ${formatDate(plan.planning_to)}` : ""}`;
}

watch(
  () => [props.customer.id, props.tenantId, props.accessToken],
  () => {
    void loadCoverageForVisibleMonth({ force: true });
  },
  { immediate: true },
);

watch(
  () => [activeDate.value.getFullYear(), activeDate.value.getMonth()],
  () => {
    void loadCoverageForVisibleMonth();
  },
);
</script>

<template>
  <section class="customer-dashboard-tab" data-testid="customer-tab-panel-dashboard">
    <div v-if="loading" class="customer-dashboard-tab__state" data-testid="customer-dashboard-loading">
      {{ t("workspace.loading.processing") }}
    </div>
    <div v-else-if="error" class="customer-dashboard-tab__state" data-testid="customer-dashboard-error">
      {{ error }}
    </div>
    <template v-else>
      <section class="customer-dashboard-tab__kpis">
        <Card :bordered="false" class="customer-dashboard-tab__kpi-card" data-testid="customer-dashboard-kpi-tenure">
          <span>{{ t("customerAdmin.dashboard.kpis.tenure") }}</span>
          <strong>{{ tenureLabel }}</strong>
        </Card>
        <Card :bordered="false" class="customer-dashboard-tab__kpi-card" data-testid="customer-dashboard-kpi-plans">
          <span>{{ t("customerAdmin.dashboard.kpis.plans") }}</span>
          <strong>{{ dashboard?.planning_summary.total_plans_count ?? 0 }}</strong>
        </Card>
        <Card
          :bordered="false"
          class="customer-dashboard-tab__kpi-card customer-dashboard-tab__kpi-card--tone"
          :data-tone="financeTone"
          data-testid="customer-dashboard-kpi-finance"
        >
          <span>{{ t("customerAdmin.dashboard.kpis.finance") }}</span>
          <strong class="customer-dashboard-tab__kpi-value" :data-tone="financeTone">{{ financeValue }}</strong>
          <small v-if="financeMeta" class="customer-dashboard-tab__kpi-meta">{{ financeMeta }}</small>
        </Card>
        <Card
          :bordered="false"
          class="customer-dashboard-tab__kpi-card customer-dashboard-tab__kpi-card--tone"
          :data-tone="standingTone"
          data-testid="customer-dashboard-kpi-standing"
        >
          <span>{{ t("customerAdmin.dashboard.kpis.standing") }}</span>
          <strong class="customer-dashboard-tab__standing" :data-tone="standingTone">
            {{ standing.label }}
          </strong>
        </Card>
      </section>

      <section class="customer-dashboard-tab__row">
        <Card :bordered="false" class="customer-dashboard-tab__panel">
          <div class="customer-dashboard-tab__panel-head">
            <div>
              <p class="eyebrow">{{ t("customerAdmin.dashboard.latestPlansEyebrow") }}</p>
              <h3>{{ t("customerAdmin.dashboard.latestPlansTitle") }}</h3>
            </div>
          </div>
          <div v-if="latestPlans.length" class="customer-dashboard-tab__list">
            <div
              v-for="plan in latestPlans"
              :key="plan.id"
              class="customer-dashboard-tab__list-row"
            >
              <div>
                <strong>{{ plan.label }}</strong>
                <span>{{ formatPlanWindow(plan) }}</span>
              </div>
              <Tag
                class="customer-dashboard-tab__status-tag"
                :color="resolveLatestPlanTagColor(plan.status)"
                :data-tone="resolveLatestPlanStatusTone(plan.status)"
                :data-status="plan.status"
              >
                {{ plan.status }}
              </Tag>
            </div>
          </div>
          <EmptyState
            v-else
            :description="t('customerAdmin.dashboard.latestPlansEmptyBody')"
            :title="t('customerAdmin.dashboard.latestPlansEmptyTitle')"
          />
        </Card>

        <Card :bordered="false" class="customer-dashboard-tab__panel">
          <div class="customer-dashboard-tab__panel-head">
            <div>
              <p class="eyebrow">{{ t("customerAdmin.dashboard.quickActionsEyebrow") }}</p>
              <h3>{{ t("customerAdmin.dashboard.quickActionsTitle") }}</h3>
            </div>
          </div>
          <div class="customer-dashboard-tab__actions">
            <button
              v-for="action in quickActions"
              :key="action.id"
              type="button"
              class="cta-button cta-secondary"
              @click="selectTab(action.tabId!)"
            >
              {{ action.label }}
            </button>
            <button
              v-for="action in actionShortcuts"
              :key="action.id"
              type="button"
              class="cta-button"
              @click="triggerShortcut(action.type)"
            >
              {{ action.label }}
            </button>
          </div>
        </Card>
      </section>

      <div v-if="calendarLoading" class="customer-dashboard-tab__state" data-testid="customer-dashboard-calendar-loading">
        {{ t("workspace.loading.processing") }}
      </div>
      <div v-else-if="calendarError" class="customer-dashboard-tab__state" data-testid="customer-dashboard-calendar-error">
        {{ calendarError }}
      </div>
      <template v-else>
        <DashboardCalendarPanel
          :cells="calendarCells"
          :description="t('customerAdmin.dashboard.calendarDescription')"
          :month-hint="t('customerAdmin.dashboard.calendarMonthHint')"
          :month-label="monthLabel"
          :more-label="t('customerAdmin.dashboard.calendarMore')"
          :next-label="t('customerAdmin.dashboard.calendarNext')"
          :order-short-label="t('customerAdmin.dashboard.calendarOrderShort')"
          :previous-label="t('customerAdmin.dashboard.calendarPrevious')"
          :shift-short-label="t('customerAdmin.dashboard.calendarShiftShort')"
          :summary="calendarSummary"
          :title="t('customerAdmin.dashboard.calendarTitle')"
          :week-day-labels="weekDayLabels"
          @shift-calendar="shiftCalendar"
          @toggle-day="toggleCalendarDay"
        />
        <EmptyState
          v-if="!coverageRows.length"
          class="customer-dashboard-tab__calendar-empty"
          :description="t('customerAdmin.dashboard.calendarEmptyBody')"
          :title="t('customerAdmin.dashboard.calendarEmptyTitle')"
        />
      </template>
    </template>
  </section>
</template>

<style scoped>
.customer-dashboard-tab {
  display: grid;
  gap: 1rem;
}

.customer-dashboard-tab__state {
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  color: var(--sp-color-text-secondary);
}

.customer-dashboard-tab__kpis {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.customer-dashboard-tab__kpi-card,
.customer-dashboard-tab__panel {
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  box-shadow: var(--sp-shadow-card);
}

.customer-dashboard-tab__kpi-card {
  display: grid;
  gap: 0.45rem;
}

.customer-dashboard-tab__kpi-card--tone {
  position: relative;
  overflow: hidden;
}

.customer-dashboard-tab__kpi-card--tone::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 0.32rem;
  border-radius: 1rem 0 0 1rem;
  background: currentColor;
  opacity: 0.75;
}

.customer-dashboard-tab__kpi-card span,
.customer-dashboard-tab__kpi-card small {
  color: var(--sp-color-text-secondary);
}

.customer-dashboard-tab__kpi-card strong {
  color: var(--sp-color-text-primary);
  font-size: 1.35rem;
}

.customer-dashboard-tab__kpi-card--tone[data-tone="good"] {
  color: var(--sp-color-success);
  border-color: color-mix(in srgb, var(--sp-color-success) 30%, var(--sp-color-border-soft));
  background: color-mix(in srgb, var(--sp-color-success) 10%, var(--sp-color-surface-card));
}

.customer-dashboard-tab__kpi-card--tone[data-tone="warn"] {
  color: var(--sp-color-warning);
  border-color: color-mix(in srgb, var(--sp-color-warning) 32%, var(--sp-color-border-soft));
  background: color-mix(in srgb, var(--sp-color-warning) 11%, var(--sp-color-surface-card));
}

.customer-dashboard-tab__kpi-card--tone[data-tone="bad"] {
  color: var(--sp-color-danger);
  border-color: color-mix(in srgb, var(--sp-color-danger) 30%, var(--sp-color-border-soft));
  background: color-mix(in srgb, var(--sp-color-danger) 10%, var(--sp-color-surface-card));
}

.customer-dashboard-tab__kpi-card--tone[data-tone="restricted"] {
  color: var(--sp-color-primary-strong);
  border-color: color-mix(in srgb, var(--sp-color-primary-strong) 26%, var(--sp-color-border-soft));
  background: color-mix(in srgb, var(--sp-color-primary-muted) 24%, var(--sp-color-surface-card));
}

.customer-dashboard-tab__kpi-value,
.customer-dashboard-tab__standing {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  max-width: 100%;
  padding: 0.2rem 0.6rem;
  border: 1px solid transparent;
  border-radius: 999px;
  line-height: 1.25;
}

.customer-dashboard-tab__kpi-value[data-tone="good"],
.customer-dashboard-tab__standing[data-tone="good"] {
  border-color: color-mix(in srgb, var(--sp-color-success) 34%, transparent);
  background: color-mix(in srgb, var(--sp-color-success) 14%, transparent);
}

.customer-dashboard-tab__kpi-value[data-tone="warn"],
.customer-dashboard-tab__standing[data-tone="warn"] {
  border-color: color-mix(in srgb, var(--sp-color-warning) 38%, transparent);
  background: color-mix(in srgb, var(--sp-color-warning) 16%, transparent);
}

.customer-dashboard-tab__kpi-value[data-tone="bad"],
.customer-dashboard-tab__standing[data-tone="bad"] {
  border-color: color-mix(in srgb, var(--sp-color-danger) 34%, transparent);
  background: color-mix(in srgb, var(--sp-color-danger) 14%, transparent);
}

.customer-dashboard-tab__kpi-value[data-tone="restricted"],
.customer-dashboard-tab__standing[data-tone="restricted"] {
  border-color: color-mix(in srgb, var(--sp-color-primary-strong) 30%, transparent);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 28%, transparent);
}

.customer-dashboard-tab__kpi-meta {
  max-width: 100%;
}

.customer-dashboard-tab__row {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
}

.customer-dashboard-tab__panel-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.customer-dashboard-tab__list {
  display: grid;
  gap: 0.75rem;
  margin-top: 1rem;
}

.customer-dashboard-tab__list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.customer-dashboard-tab__list-row strong {
  display: block;
  color: var(--sp-color-text-primary);
}

.customer-dashboard-tab__list-row span {
  color: var(--sp-color-text-secondary);
}

.customer-dashboard-tab__status-tag {
  flex-shrink: 0;
  font-weight: 600;
  text-transform: none;
}

.customer-dashboard-tab__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

.customer-dashboard-tab__calendar-empty {
  margin-top: -0.25rem;
}

@media (max-width: 1100px) {
  .customer-dashboard-tab__kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .customer-dashboard-tab__row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .customer-dashboard-tab__kpis {
    grid-template-columns: 1fr;
  }

  .customer-dashboard-tab__list-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
