<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";

import { Card, Tag } from "ant-design-vue";

import EmptyState from "#/components/sicherplan/empty-state.vue";
import type { PlanningRecordListItem } from "@/api/planningOrders";
import { listPlanningRecords } from "@/api/planningOrders";
import { useI18n } from "@/i18n";

type DisplayStateTone = "good" | "muted" | "neutral" | "warn";
type SortOptionId =
  | "createdAtDesc"
  | "createdAtAsc"
  | "executionStartDesc"
  | "executionStartAsc"
  | "executionEndDesc"
  | "executionEndAsc"
  | "releaseDateDesc"
  | "releaseDateAsc"
  | "status";

interface PlanListRow extends PlanningRecordListItem {
  displayStateKey: string;
  displayTone: DisplayStateTone;
}

const props = defineProps<{
  accessToken: string;
  customerId: string;
  tenantId: string;
}>();

const { t, locale } = useI18n();

const plans = ref<PlanListRow[]>([]);
const loading = ref(false);
const error = ref("");
const searchInput = ref("");
const activeSearch = ref("");
const sortBy = ref<SortOptionId>("createdAtDesc");
const debounceHandle = ref<number | null>(null);
const requestVersion = ref(0);

const sortOptions = computed(() => [
  { value: "createdAtDesc", label: t("customerAdmin.plans.sort.createdAtDesc") },
  { value: "createdAtAsc", label: t("customerAdmin.plans.sort.createdAtAsc") },
  { value: "executionStartDesc", label: t("customerAdmin.plans.sort.executionStartDesc") },
  { value: "executionStartAsc", label: t("customerAdmin.plans.sort.executionStartAsc") },
  { value: "executionEndDesc", label: t("customerAdmin.plans.sort.executionEndDesc") },
  { value: "executionEndAsc", label: t("customerAdmin.plans.sort.executionEndAsc") },
  { value: "releaseDateDesc", label: t("customerAdmin.plans.sort.releaseDateDesc") },
  { value: "releaseDateAsc", label: t("customerAdmin.plans.sort.releaseDateAsc") },
  { value: "status", label: t("customerAdmin.plans.sort.status") },
]);

function parseDateTimeValue(value: string | null | undefined) {
  if (!value) {
    return Number.NaN;
  }
  const parsed = new Date(value).getTime();
  return Number.isFinite(parsed) ? parsed : Number.NaN;
}

function parseDateBoundary(value: string | null | undefined, boundary: "start" | "end") {
  if (!value) {
    return Number.NaN;
  }
  const parsed = new Date(`${value}T00:00:00`);
  if (!Number.isFinite(parsed.getTime())) {
    return Number.NaN;
  }
  if (boundary === "end") {
    parsed.setHours(23, 59, 59, 999);
  }
  return parsed.getTime();
}

function compareNullableDates(
  left: string | null | undefined,
  right: string | null | undefined,
  direction: "asc" | "desc",
  parser: (value: string | null | undefined) => number = parseDateTimeValue,
) {
  const leftTime = parser(left);
  const rightTime = parser(right);
  const normalizedLeft = Number.isFinite(leftTime) ? leftTime : (direction === "asc" ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY);
  const normalizedRight = Number.isFinite(rightTime) ? rightTime : (direction === "asc" ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY);
  return direction === "asc" ? normalizedLeft - normalizedRight : normalizedRight - normalizedLeft;
}

function comparePlanIdentity(left: PlanningRecordListItem, right: PlanningRecordListItem) {
  const leftName = typeof left.name === "string" ? left.name : "";
  const rightName = typeof right.name === "string" ? right.name : "";
  const byName = leftName.localeCompare(rightName);
  if (byName !== 0) {
    return byName;
  }
  return left.id.localeCompare(right.id);
}

const sortedPlans = computed(() => {
  const rows = [...plans.value];

  rows.sort((left, right) => {
    let comparison = 0;
    switch (sortBy.value) {
      case "createdAtAsc":
        comparison = compareNullableDates(left.created_at, right.created_at, "asc");
        break;
      case "createdAtDesc":
        comparison = compareNullableDates(left.created_at, right.created_at, "desc");
        break;
      case "executionStartAsc":
        comparison = compareNullableDates(left.planning_from, right.planning_from, "asc", (value) => parseDateBoundary(value, "start"));
        break;
      case "executionStartDesc":
        comparison = compareNullableDates(left.planning_from, right.planning_from, "desc", (value) => parseDateBoundary(value, "start"));
        break;
      case "executionEndAsc":
        comparison = compareNullableDates(left.planning_to, right.planning_to, "asc", (value) => parseDateBoundary(value, "end"));
        break;
      case "executionEndDesc":
        comparison = compareNullableDates(left.planning_to, right.planning_to, "desc", (value) => parseDateBoundary(value, "end"));
        break;
      case "releaseDateAsc":
        comparison = compareNullableDates(left.released_at, right.released_at, "asc");
        break;
      case "releaseDateDesc":
        comparison = compareNullableDates(left.released_at, right.released_at, "desc");
        break;
      case "status": {
        const toneOrder = { warn: 0, neutral: 1, good: 2, muted: 3 };
        const toneDiff = toneOrder[left.displayTone] - toneOrder[right.displayTone];
        if (toneDiff !== 0) {
          comparison = toneDiff;
          break;
        }
        comparison = left.displayStateKey.localeCompare(right.displayStateKey);
        break;
      }
      default:
        comparison = 0;
        break;
    }
    if (comparison !== 0) {
      return comparison;
    }
    return comparePlanIdentity(left, right);
  });
  return rows;
});

function formatDate(value: string | null) {
  if (!value) {
    return t("customerAdmin.summary.none");
  }
  return new Intl.DateTimeFormat(locale.value, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function resolveDisplayState(record: PlanningRecordListItem) {
  const now = Date.now();
  const planningFrom = parseDateBoundary(record.planning_from, "start");
  const planningTo = parseDateBoundary(record.planning_to, "end");

  if (record.status === "archived") {
    return {
      key: "archived",
      label: t("customerAdmin.plans.displayState.archived"),
      tone: "muted" as const,
    };
  }
  if (record.release_state === "draft") {
    return {
      key: "draft",
      label: t("coreAdmin.status.draft"),
      tone: "warn" as const,
    };
  }
  if (record.release_state === "release_ready") {
    return {
      key: "release_ready",
      label: t("coreAdmin.status.release_ready"),
      tone: "warn" as const,
    };
  }
  if (record.release_state === "released") {
    if (Number.isFinite(planningFrom) && now < planningFrom) {
      return {
        key: "upcoming",
        label: t("customerAdmin.plans.displayState.upcoming"),
        tone: "good" as const,
      };
    }
    if (Number.isFinite(planningTo) && now > planningTo) {
      return {
        key: "completed",
        label: t("customerAdmin.plans.displayState.completed"),
        tone: "neutral" as const,
      };
    }
    return {
      key: "in_progress",
      label: t("customerAdmin.plans.displayState.inProgress"),
      tone: "good" as const,
    };
  }
  return {
    key: "neutral",
    label: record.release_state || record.status || t("customerAdmin.summary.none"),
    tone: "neutral" as const,
  };
}

function mapTagColor(tone: DisplayStateTone) {
  switch (tone) {
    case "good":
      return "success";
    case "warn":
      return "gold";
    case "muted":
      return "default";
    default:
      return "processing";
  }
}

async function loadPlans() {
  if (!props.customerId || !props.tenantId || !props.accessToken) {
    plans.value = [];
    error.value = "";
    return;
  }

  const version = ++requestVersion.value;
  loading.value = true;
  plans.value = [];
  error.value = "";

  try {
    const rows = await listPlanningRecords(props.tenantId, props.accessToken, {
      customer_id: props.customerId,
      search: activeSearch.value,
    });
    if (version !== requestVersion.value) {
      return;
    }
    plans.value = rows.map((row) => {
      const displayState = resolveDisplayState(row);
      return {
        ...row,
        displayStateKey: displayState.key,
        displayTone: displayState.tone,
      };
    });
  } catch {
    if (version !== requestVersion.value) {
      return;
    }
    plans.value = [];
    error.value = t("customerAdmin.plans.errorBody");
  } finally {
    if (version === requestVersion.value) {
      loading.value = false;
    }
  }
}

watch(
  () => searchInput.value,
  (value) => {
    if (debounceHandle.value != null) {
      window.clearTimeout(debounceHandle.value);
    }
    debounceHandle.value = window.setTimeout(() => {
      activeSearch.value = value.trim();
      void loadPlans();
    }, 250);
  },
);

watch(
  () => [props.customerId, props.tenantId, props.accessToken],
  () => {
    searchInput.value = "";
    activeSearch.value = "";
    void loadPlans();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (debounceHandle.value != null) {
    window.clearTimeout(debounceHandle.value);
  }
});
</script>

<template>
  <section class="customer-plans-tab" data-testid="customer-tab-panel-plans">
    <div class="customer-plans-tab__intro">
      <div>
        <p class="eyebrow">{{ t("customerAdmin.plans.eyebrow") }}</p>
        <h3>{{ t("customerAdmin.plans.title") }}</h3>
      </div>
    </div>

    <div class="customer-plans-tab__controls">
      <label class="field-stack field-stack--wide">
        <span>{{ t("customerAdmin.filters.search") }}</span>
        <input
          v-model="searchInput"
          :placeholder="t('customerAdmin.plans.searchPlaceholder')"
          data-testid="customer-plans-search"
        />
      </label>
      <label class="field-stack field-stack--half">
        <span>{{ t("customerAdmin.plans.sortLabel") }}</span>
        <select v-model="sortBy" data-testid="customer-plans-sort">
          <option v-for="option in sortOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
    </div>

    <div v-if="loading" class="customer-plans-tab__state" data-testid="customer-plans-loading">
      {{ t("workspace.loading.processing") }}
    </div>
    <div v-else-if="error" class="customer-plans-tab__state" data-testid="customer-plans-error">
      <strong>{{ t("customerAdmin.plans.errorTitle") }}</strong>
      <span>{{ error }}</span>
    </div>
    <div v-else-if="sortedPlans.length" class="customer-plans-tab__list">
      <Card
        v-for="plan in sortedPlans"
        :key="plan.id"
        :bordered="false"
        class="customer-plans-tab__row"
        :data-tone="plan.displayTone"
        :data-state="plan.displayStateKey"
      >
        <div class="customer-plans-tab__row-main">
          <div>
            <strong>{{ plan.name }}</strong>
            <div class="customer-plans-tab__meta">
              <span>{{ formatDate(plan.planning_from) }} → {{ formatDate(plan.planning_to) }}</span>
              <span>{{ t("customerAdmin.plans.registrationDate") }}: {{ formatDate(plan.created_at) }}</span>
              <span>{{ t("customerAdmin.plans.releaseDate") }}: {{ formatDate(plan.released_at) }}</span>
            </div>
          </div>
          <div class="customer-plans-tab__row-side">
            <Tag
              class="customer-plans-tab__state-tag"
              :color="mapTagColor(plan.displayTone)"
              :data-tone="plan.displayTone"
              :data-state="plan.displayStateKey"
            >
              {{ resolveDisplayState(plan).label }}
            </Tag>
            <small>{{ t("customerAdmin.plans.rawReleaseState") }}: {{ plan.release_state }}</small>
          </div>
        </div>
      </Card>
    </div>
    <EmptyState
      v-else
      :title="t('customerAdmin.plans.emptyTitle')"
      :description="t('customerAdmin.plans.emptyBody')"
    />
  </section>
</template>

<style scoped>
.customer-plans-tab {
  display: grid;
  gap: 1rem;
}

.customer-plans-tab__controls {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.4fr) minmax(14rem, 0.6fr);
}

.customer-plans-tab__state {
  display: grid;
  gap: 0.25rem;
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  color: var(--sp-color-text-secondary);
}

.customer-plans-tab__list {
  display: grid;
  gap: 0.85rem;
}

.customer-plans-tab__row {
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  box-shadow: var(--sp-shadow-card);
}

.customer-plans-tab__row[data-tone="good"] {
  border-color: color-mix(in srgb, var(--sp-color-success) 28%, var(--sp-color-border-soft));
}

.customer-plans-tab__row[data-tone="warn"] {
  border-color: color-mix(in srgb, var(--sp-color-warning) 28%, var(--sp-color-border-soft));
}

.customer-plans-tab__row[data-tone="muted"] {
  border-color: color-mix(in srgb, var(--sp-color-text-secondary) 18%, var(--sp-color-border-soft));
}

.customer-plans-tab__row-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.customer-plans-tab__row-main > div:first-child {
  min-width: 0;
}

.customer-plans-tab__row strong {
  display: block;
  color: var(--sp-color-text-primary);
  overflow-wrap: anywhere;
}

.customer-plans-tab__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.85rem;
  margin-top: 0.45rem;
  color: var(--sp-color-text-secondary);
}

.customer-plans-tab__row-side {
  display: grid;
  justify-items: end;
  gap: 0.35rem;
  text-align: right;
}

.customer-plans-tab__state-tag {
  margin-inline-end: 0;
  font-weight: 600;
}

.customer-plans-tab__row-side small {
  color: var(--sp-color-text-secondary);
}

@media (max-width: 900px) {
  .customer-plans-tab__controls {
    grid-template-columns: 1fr;
  }

  .customer-plans-tab__row-main {
    flex-direction: column;
  }

  .customer-plans-tab__row-side {
    justify-items: start;
    text-align: left;
  }
}
</style>
