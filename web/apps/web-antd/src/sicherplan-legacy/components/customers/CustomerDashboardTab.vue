<script lang="ts" setup>
import { computed, ref } from "vue";

import { Card } from "ant-design-vue";

import EmptyState from "#/components/sicherplan/empty-state.vue";
import DashboardCalendarPanel from "#/components/sicherplan/dashboard-calendar-panel.vue";
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

interface CalendarCellItem {
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
  customer: CustomerRead;
  dashboard: CustomerDashboardRead | null;
  error: string;
  loading: boolean;
  standing: StandingSummary;
}>();

const emit = defineEmits<{
  createContact: [];
  createInvoiceParty: [];
  selectTab: [tabId: DashboardTabId];
}>();

const { t, locale } = useI18n();
const activeDate = ref(new Date());
const expandedDays = ref<string[]>([]);

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

const financeMeta = computed(() => {
  const financeSummary = props.dashboard?.finance_summary;
  if (!financeSummary?.semantic_label) {
    return "";
  }
  return t(`customerAdmin.dashboard.financeLabels.${financeSummary.semantic_label}` as never);
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

const calendarSummary = computed(() => {
  const items = props.dashboard?.calendar_items ?? [];
  const releasedCount = items.filter((item) => item.status === "released").length;
  return [
    {
      label: t("customerAdmin.dashboard.calendarSummary.plans"),
      value: String(items.length),
    },
    {
      label: t("customerAdmin.dashboard.calendarSummary.released"),
      value: String(releasedCount),
    },
    {
      label: t("customerAdmin.dashboard.calendarSummary.orders"),
      value: String(new Set(items.map((item) => item.order_id).filter(Boolean)).size),
    },
  ];
});

const calendarCells = computed<CalendarCell[]>(() => {
  const current = activeDate.value;
  const year = current.getFullYear();
  const month = current.getMonth();
  const firstDay = new Date(year, month, 1);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const startDate = new Date(year, month, 1 - startOffset);
  const todayKey = buildDayKey(new Date());
  const itemsByDay = new Map<string, Array<{
    id: string;
    title: string;
    status: string;
    order_id: string | null;
    starts_at: string | null;
  }>>();

  for (const item of props.dashboard?.calendar_items ?? []) {
    if (!item.starts_at) {
      continue;
    }
    const dayKey = buildDayKey(new Date(item.starts_at));
    itemsByDay.set(dayKey, [...(itemsByDay.get(dayKey) ?? []), item]);
  }

  return Array.from({ length: 35 }, (_, index) => {
    const date = new Date(startDate);
    date.setDate(startDate.getDate() + index);
    const dayKey = buildDayKey(date);
    const items = itemsByDay.get(dayKey) ?? [];
    const isExpanded = expandedDays.value.includes(dayKey);
    const visibleItems = (isExpanded ? items : items.slice(0, 2)).map((item) => ({
      key: item.id,
      label: truncateLabel(item.title),
      tone: resolveTone(item.status),
      coverageStateLabel: resolveStateLabel(item.status),
    }));
    return {
      dateKey: dayKey,
      dayLabel: String(date.getDate()),
      inMonth: date.getMonth() === month,
      isToday: dayKey === todayKey,
      visibleItems,
      moreCount: Math.max(items.length - visibleItems.length, 0),
      shiftCount: 0,
      orderCount: new Set(items.map((item) => item.order_id).filter(Boolean)).size,
    };
  });
});

function buildDayKey(value: Date) {
  return value.toDateString();
}

function truncateLabel(value: string, maxLength = 24) {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength - 1).trimEnd()}…`;
}

function resolveTone(status: string): "bad" | "good" | "warn" {
  if (status === "released") {
    return "good";
  }
  if (status === "draft") {
    return "warn";
  }
  return "bad";
}

function resolveStateLabel(status: string) {
  if (status === "released") {
    return t("customerAdmin.dashboard.calendarStatus.released");
  }
  if (status === "draft") {
    return t("customerAdmin.dashboard.calendarStatus.draft");
  }
  return t("customerAdmin.dashboard.calendarStatus.other");
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
        <Card :bordered="false" class="customer-dashboard-tab__kpi-card" data-testid="customer-dashboard-kpi-finance">
          <span>{{ t("customerAdmin.dashboard.kpis.finance") }}</span>
          <strong>{{ financeValue }}</strong>
          <small v-if="financeMeta">{{ financeMeta }}</small>
        </Card>
        <Card :bordered="false" class="customer-dashboard-tab__kpi-card" data-testid="customer-dashboard-kpi-standing">
          <span>{{ t("customerAdmin.dashboard.kpis.standing") }}</span>
          <strong :class="`customer-dashboard-tab__standing customer-dashboard-tab__standing--${standing.tone}`">
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
              <span>{{ plan.status }}</span>
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

      <DashboardCalendarPanel
        :cells="calendarCells"
        :description="t('customerAdmin.dashboard.calendarDescription')"
        :month-hint="t('customerAdmin.dashboard.calendarMonthHint')"
        :month-label="monthLabel"
        :more-label="t('customerAdmin.dashboard.calendarMore')"
        :next-label="t('customerAdmin.dashboard.calendarNext')"
        :order-short-label="t('customerAdmin.dashboard.calendarOrderShort')"
        :previous-label="t('customerAdmin.dashboard.calendarPrevious')"
        :shift-short-label="t('customerAdmin.dashboard.calendarPlanShort')"
        :summary="calendarSummary"
        :title="t('customerAdmin.dashboard.calendarTitle')"
        :week-day-labels="weekDayLabels"
        @shift-calendar="shiftCalendar"
        @toggle-day="toggleCalendarDay"
      />
      <EmptyState
        v-if="!dashboard?.calendar_items.length"
        class="customer-dashboard-tab__calendar-empty"
        :description="t('customerAdmin.dashboard.calendarEmptyBody')"
        :title="t('customerAdmin.dashboard.calendarEmptyTitle')"
      />
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

.customer-dashboard-tab__kpi-card span,
.customer-dashboard-tab__kpi-card small {
  color: var(--sp-color-text-secondary);
}

.customer-dashboard-tab__kpi-card strong {
  color: var(--sp-color-text-primary);
  font-size: 1.35rem;
}

.customer-dashboard-tab__standing--good {
  color: rgb(17 119 119);
}

.customer-dashboard-tab__standing--warn {
  color: rgb(149 97 18);
}

.customer-dashboard-tab__standing--bad {
  color: rgb(172 54 41);
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
