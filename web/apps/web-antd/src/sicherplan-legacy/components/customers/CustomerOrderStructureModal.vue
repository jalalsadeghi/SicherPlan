<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";

import EmptyState from "#/components/sicherplan/empty-state.vue";
import {
  getCustomerOrder,
  listPlanningRecords,
  type CustomerOrderRead,
  type PlanningRecordListItem,
} from "@/api/planningOrders";
import {
  getShiftPlan,
  getShiftSeries,
  listShiftPlans,
  type ShiftPlanListItem,
  type ShiftPlanRead,
  type ShiftSeriesRead,
} from "@/api/planningShifts";
import { useI18n } from "@/i18n";

type StructureStepId =
  | "order-details"
  | "order-scope-documents"
  | "planning-record-overview"
  | "planning-record-documents"
  | "shift-plan"
  | "series-exceptions";

interface StructureNavigationPayload {
  orderId: string;
  planningRecordId?: string;
  seriesId?: string;
  shiftPlanId?: string;
  step: StructureStepId;
}

interface StructureSummaryState {
  order: CustomerOrderRead;
  planningRecords: PlanningRecordListItem[];
}

const props = defineProps<{
  accessToken: string;
  customerId: string;
  open: boolean;
  orderId: string;
  tenantId: string;
}>();

const emit = defineEmits<{
  (event: "close"): void;
  (event: "open-node", payload: StructureNavigationPayload): void;
}>();

const { t } = useI18n();

const summaryLoading = ref(false);
const summaryError = ref("");
const expandedPlanningRecords = reactive<Record<string, boolean>>({});
const expandedShiftPlans = reactive<Record<string, boolean>>({});
const activePlanLoading = reactive<Record<string, boolean>>({});
const activeSeriesLoading = reactive<Record<string, boolean>>({});
const shiftPlanError = reactive<Record<string, string>>({});
const shiftSeriesError = reactive<Record<string, string>>({});
const visible = computed(() => props.open && !!props.orderId && !!props.tenantId && !!props.accessToken);

const summaryCache = new Map<string, StructureSummaryState>();
const summaryInflight = new Map<string, Promise<StructureSummaryState>>();
const shiftPlansCache = new Map<string, ShiftPlanListItem[]>();
const shiftPlansInflight = new Map<string, Promise<ShiftPlanListItem[]>>();
const shiftPlanDetailsCache = new Map<string, ShiftPlanRead>();
const shiftPlanDetailsInflight = new Map<string, Promise<ShiftPlanRead>>();
const shiftSeriesDetailsCache = new Map<string, ShiftSeriesRead>();
const shiftSeriesDetailsInflight = new Map<string, Promise<ShiftSeriesRead>>();

const summaryState = ref<StructureSummaryState | null>(null);
const shiftPlansByPlanningRecord = reactive<Record<string, ShiftPlanListItem[]>>({});
const shiftPlanDetailsById = reactive<Record<string, ShiftPlanRead | null>>({});
const shiftSeriesDetailsById = reactive<Record<string, ShiftSeriesRead | null>>({});

function structureCacheKey(scope: string, id: string) {
  return `${props.tenantId}:${scope}:${id}`;
}

function formatReadableValue(value: string | null | undefined) {
  return typeof value === "string" && value.trim() ? value.trim() : t("customerAdmin.summary.none");
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return t("customerAdmin.summary.none");
  }
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function formatDateRange(from: string | null | undefined, to: string | null | undefined) {
  return `${formatDate(from)} → ${formatDate(to)}`;
}

function formatReleaseStateLabel(releaseState: string | null | undefined) {
  switch (releaseState) {
    case "draft":
      return t("coreAdmin.status.draft");
    case "release_ready":
      return t("coreAdmin.status.release_ready");
    case "released":
      return t("coreAdmin.status.released");
    default:
      return formatReadableValue(releaseState);
  }
}

function resetTransientState() {
  summaryError.value = "";
  Object.keys(expandedPlanningRecords).forEach((key) => delete expandedPlanningRecords[key]);
  Object.keys(expandedShiftPlans).forEach((key) => delete expandedShiftPlans[key]);
  Object.keys(activePlanLoading).forEach((key) => delete activePlanLoading[key]);
  Object.keys(activeSeriesLoading).forEach((key) => delete activeSeriesLoading[key]);
  Object.keys(shiftPlanError).forEach((key) => delete shiftPlanError[key]);
  Object.keys(shiftSeriesError).forEach((key) => delete shiftSeriesError[key]);
}

async function loadSummary(force = false) {
  if (!visible.value) {
    summaryState.value = null;
    return;
  }
  const cacheKey = structureCacheKey("order-structure", props.orderId);
  if (!force && summaryCache.has(cacheKey)) {
    summaryState.value = summaryCache.get(cacheKey)!;
    return;
  }
  if (!force && summaryInflight.has(cacheKey)) {
    summaryState.value = await summaryInflight.get(cacheKey)!;
    return;
  }

  summaryLoading.value = true;
  summaryError.value = "";
  const requestPromise = Promise.all([
    getCustomerOrder(props.tenantId, props.orderId, props.accessToken),
    listPlanningRecords(props.tenantId, props.accessToken, {
      customer_id: props.customerId,
      order_id: props.orderId,
    }),
  ]).then(([order, planningRecords]) => ({
    order,
    planningRecords,
  }));
  summaryInflight.set(cacheKey, requestPromise);

  try {
    const result = await requestPromise;
    summaryCache.set(cacheKey, result);
    summaryState.value = result;
  } catch {
    summaryError.value = t("customerAdmin.orders.structure.errorBody");
  } finally {
    summaryLoading.value = false;
    summaryInflight.delete(cacheKey);
  }
}

async function loadShiftPlans(planningRecordId: string, force = false) {
  const cacheKey = structureCacheKey("planning-record-shift-plans", planningRecordId);
  if (!force && shiftPlansCache.has(cacheKey)) {
    shiftPlansByPlanningRecord[planningRecordId] = shiftPlansCache.get(cacheKey)!;
    return;
  }
  if (!force && shiftPlansInflight.has(cacheKey)) {
    shiftPlansByPlanningRecord[planningRecordId] = await shiftPlansInflight.get(cacheKey)!;
    return;
  }

  activePlanLoading[planningRecordId] = true;
  shiftPlanError[planningRecordId] = "";
  const requestPromise = listShiftPlans(props.tenantId, props.accessToken, {
    planning_record_id: planningRecordId,
  });
  shiftPlansInflight.set(cacheKey, requestPromise);

  try {
    const result = await requestPromise;
    shiftPlansCache.set(cacheKey, result);
    shiftPlansByPlanningRecord[planningRecordId] = result;
  } catch {
    shiftPlanError[planningRecordId] = t("customerAdmin.orders.structure.errorBody");
  } finally {
    activePlanLoading[planningRecordId] = false;
    shiftPlansInflight.delete(cacheKey);
  }
}

async function loadShiftPlanDetail(shiftPlanId: string, force = false) {
  const cacheKey = structureCacheKey("shift-plan-detail", shiftPlanId);
  if (!force && shiftPlanDetailsCache.has(cacheKey)) {
    shiftPlanDetailsById[shiftPlanId] = shiftPlanDetailsCache.get(cacheKey)!;
    return;
  }
  if (!force && shiftPlanDetailsInflight.has(cacheKey)) {
    shiftPlanDetailsById[shiftPlanId] = await shiftPlanDetailsInflight.get(cacheKey)!;
    return;
  }

  activeSeriesLoading[shiftPlanId] = true;
  shiftSeriesError[shiftPlanId] = "";
  const requestPromise = getShiftPlan(props.tenantId, shiftPlanId, props.accessToken);
  shiftPlanDetailsInflight.set(cacheKey, requestPromise);

  try {
    const result = await requestPromise;
    shiftPlanDetailsCache.set(cacheKey, result);
    shiftPlanDetailsById[shiftPlanId] = result;
  } catch {
    shiftSeriesError[shiftPlanId] = t("customerAdmin.orders.structure.errorBody");
  } finally {
    activeSeriesLoading[shiftPlanId] = false;
    shiftPlanDetailsInflight.delete(cacheKey);
  }
}

async function loadShiftSeriesDetail(shiftSeriesId: string) {
  const cacheKey = structureCacheKey("shift-series-detail", shiftSeriesId);
  if (shiftSeriesDetailsCache.has(cacheKey)) {
    shiftSeriesDetailsById[shiftSeriesId] = shiftSeriesDetailsCache.get(cacheKey)!;
    return;
  }
  if (shiftSeriesDetailsInflight.has(cacheKey)) {
    shiftSeriesDetailsById[shiftSeriesId] = await shiftSeriesDetailsInflight.get(cacheKey)!;
    return;
  }

  const requestPromise = getShiftSeries(props.tenantId, shiftSeriesId, props.accessToken);
  shiftSeriesDetailsInflight.set(cacheKey, requestPromise);
  try {
    const result = await requestPromise;
    shiftSeriesDetailsCache.set(cacheKey, result);
    shiftSeriesDetailsById[shiftSeriesId] = result;
  } finally {
    shiftSeriesDetailsInflight.delete(cacheKey);
  }
}

async function togglePlanningRecord(recordId: string) {
  expandedPlanningRecords[recordId] = !expandedPlanningRecords[recordId];
  if (expandedPlanningRecords[recordId]) {
    await loadShiftPlans(recordId);
  }
}

async function toggleShiftPlan(shiftPlanId: string) {
  expandedShiftPlans[shiftPlanId] = !expandedShiftPlans[shiftPlanId];
  if (expandedShiftPlans[shiftPlanId]) {
    await loadShiftPlanDetail(shiftPlanId);
    const detail = shiftPlanDetailsById[shiftPlanId];
    if (detail) {
      await Promise.all(detail.series_rows.map((series) => loadShiftSeriesDetail(series.id)));
    }
  }
}

function openStep(payload: StructureNavigationPayload) {
  emit("open-node", payload);
}

function closeModal() {
  emit("close");
}

function handleWindowKeydown(event: KeyboardEvent) {
  if (visible.value && event.key === "Escape") {
    closeModal();
  }
}

function generatedShiftCount(shiftPlanId: string, shiftSeriesId: string) {
  const detail = shiftPlanDetailsById[shiftPlanId];
  if (!detail) {
    return null;
  }
  return detail.shifts.filter((shift) => shift.shift_series_id === shiftSeriesId).length;
}

function exceptionCount(shiftSeriesId: string) {
  return shiftSeriesDetailsById[shiftSeriesId]?.exceptions.length ?? null;
}

function refreshStructure() {
  return loadSummary(true);
}

watch(
  () => [props.open, props.orderId, props.customerId, props.tenantId, props.accessToken] as const,
  async ([open]) => {
    resetTransientState();
    if (!open) {
      summaryState.value = null;
      return;
    }
    await loadSummary();
  },
  { immediate: true },
);

watch(
  () => visible.value,
  (isVisible) => {
    if (isVisible) {
      window.addEventListener("keydown", handleWindowKeydown);
      return;
    }
    window.removeEventListener("keydown", handleWindowKeydown);
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleWindowKeydown);
});
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="customer-admin-modal-backdrop customer-order-structure-modal-backdrop"
      data-testid="customer-order-structure-modal-backdrop"
      @click.self="closeModal"
    >
      <section
        class="module-card customer-admin-modal customer-order-structure-modal"
        data-testid="customer-order-structure-modal"
        role="dialog"
        aria-modal="true"
      >
      <header class="customer-order-structure-modal__header">
        <div>
          <p class="eyebrow">{{ t("customerAdmin.orders.structure.eyebrow") }}</p>
          <h3>{{ t("customerAdmin.orders.structure.title") }}</h3>
        </div>
        <div class="customer-order-structure-modal__header-actions">
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-order-structure-refresh"
            @click="refreshStructure"
          >
            {{ t("customerAdmin.orders.structure.refresh") }}
          </button>
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-order-structure-close"
            @click="closeModal"
          >
            {{ t("customerAdmin.orders.structure.close") }}
          </button>
        </div>
      </header>

      <div v-if="summaryLoading" class="customer-order-structure-modal__state" data-testid="customer-order-structure-loading">
        <strong>{{ t("customerAdmin.orders.structure.loadingTitle") }}</strong>
        <span>{{ t("customerAdmin.orders.structure.loadingBody") }}</span>
      </div>
      <div v-else-if="summaryError" class="customer-order-structure-modal__state" data-testid="customer-order-structure-error">
        <strong>{{ t("customerAdmin.orders.structure.errorTitle") }}</strong>
        <span>{{ summaryError }}</span>
      </div>
      <template v-else-if="summaryState">
        <div class="customer-order-structure-tree" data-testid="customer-order-structure-tree">
          <section class="customer-order-structure-node customer-order-structure-node--root">
            <div class="customer-order-structure-node__summary">
              <div>
                <p class="eyebrow">{{ t("customerAdmin.orders.structure.orderNode") }}</p>
                <strong>{{ summaryState.order.order_no }} · {{ summaryState.order.title }}</strong>
                <div class="customer-order-structure-node__meta">
                  <span>{{ formatDateRange(summaryState.order.service_from, summaryState.order.service_to) }}</span>
                  <span>{{ formatReleaseStateLabel(summaryState.order.release_state) }}</span>
                </div>
              </div>
              <div class="customer-order-structure-node__actions">
                <button
                  type="button"
                  class="cta-button cta-secondary"
                  data-testid="customer-order-structure-order-details"
                  @click="openStep({ orderId: summaryState.order.id, step: 'order-details' })"
                >
                  {{ t("customerAdmin.orders.structure.openOrderStep") }}
                </button>
                <button
                  type="button"
                  class="cta-button cta-secondary"
                  data-testid="customer-order-structure-order-documents"
                  @click="openStep({ orderId: summaryState.order.id, step: 'order-scope-documents' })"
                >
                  {{ t("customerAdmin.orders.structure.orderScopeDocuments") }}
                </button>
              </div>
            </div>

            <div class="customer-order-structure-tree__children">
              <template v-if="summaryState.planningRecords.length">
                <article
                  v-for="planningRecord in summaryState.planningRecords"
                  :key="planningRecord.id"
                  class="customer-order-structure-node"
                  data-testid="customer-order-structure-planning-record"
                >
                  <div class="customer-order-structure-node__summary">
                    <div style="display: flex;">
                      <button
                        type="button"
                        class="customer-order-structure-node__toggle"
                        data-testid="customer-order-structure-planning-toggle"
                        @click="togglePlanningRecord(planningRecord.id)"
                      >
                        {{ expandedPlanningRecords[planningRecord.id] ? "−" : "+" }}
                      </button>
                      <div class="customer-order-structure-node__content">
                        <p class="eyebrow">{{ t("customerAdmin.orders.structure.planningRecord") }}</p>
                        <strong>{{ planningRecord.name }}</strong>
                        <div class="customer-order-structure-node__meta">
                          <span>{{ formatDateRange(planningRecord.planning_from, planningRecord.planning_to) }}</span>
                          <span>{{ formatReleaseStateLabel(planningRecord.release_state) }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="customer-order-structure-node__actions">
                      <button
                        type="button"
                        class="cta-button cta-secondary"
                        data-testid="customer-order-structure-planning-open"
                        @click="openStep({ orderId: summaryState.order.id, planningRecordId: planningRecord.id, step: 'planning-record-overview' })"
                      >
                        {{ t("customerAdmin.orders.structure.openPlanningRecordStep") }}
                      </button>
                      <button
                        type="button"
                        class="cta-button cta-secondary"
                        data-testid="customer-order-structure-planning-documents"
                        @click="openStep({ orderId: summaryState.order.id, planningRecordId: planningRecord.id, step: 'planning-record-documents' })"
                      >
                        {{ t("customerAdmin.orders.structure.planningRecordDocuments") }}
                      </button>
                    </div>
                  </div>

                  <div v-if="expandedPlanningRecords[planningRecord.id]" class="customer-order-structure-tree__children">
                    <div v-if="activePlanLoading[planningRecord.id]" class="customer-order-structure-node__state">
                      {{ t("customerAdmin.orders.structure.loadingBody") }}
                    </div>
                    <div v-else-if="shiftPlanError[planningRecord.id]" class="customer-order-structure-node__state">
                      {{ shiftPlanError[planningRecord.id] }}
                    </div>
                    <template v-else-if="shiftPlansByPlanningRecord[planningRecord.id]?.length">
                      <article
                        v-for="shiftPlan in shiftPlansByPlanningRecord[planningRecord.id]"
                        :key="shiftPlan.id"
                        class="customer-order-structure-node"
                        data-testid="customer-order-structure-shift-plan"
                      >
                        <div class="customer-order-structure-node__summary">
                          <div style="display: flex;">
                            <button
                              type="button"
                              class="customer-order-structure-node__toggle"
                              data-testid="customer-order-structure-shift-plan-toggle"
                              @click="toggleShiftPlan(shiftPlan.id)"
                            >
                              {{ expandedShiftPlans[shiftPlan.id] ? "−" : "+" }}
                            </button>
                            <div class="customer-order-structure-node__content">
                              <p class="eyebrow">{{ t("customerAdmin.orders.structure.shiftPlan") }}</p>
                              <strong>{{ shiftPlan.name }}</strong>
                              <div class="customer-order-structure-node__meta">
                                <span>{{ formatDateRange(shiftPlan.planning_from, shiftPlan.planning_to) }}</span>
                                <span>{{ formatReadableValue(shiftPlan.workforce_scope_code) }}</span>
                              </div>
                            </div>
                          </div>
                          <div class="customer-order-structure-node__actions">
                            <button
                              type="button"
                              class="cta-button cta-secondary"
                              data-testid="customer-order-structure-shift-plan-open"
                              @click="openStep({ orderId: summaryState.order.id, planningRecordId: planningRecord.id, shiftPlanId: shiftPlan.id, step: 'shift-plan' })"
                            >
                              {{ t("customerAdmin.orders.structure.openShiftPlanStep") }}
                            </button>
                          </div>
                        </div>

                        <div v-if="expandedShiftPlans[shiftPlan.id]" class="customer-order-structure-tree__children">
                          <div v-if="activeSeriesLoading[shiftPlan.id]" class="customer-order-structure-node__state">
                            {{ t("customerAdmin.orders.structure.loadingBody") }}
                          </div>
                          <div v-else-if="shiftSeriesError[shiftPlan.id]" class="customer-order-structure-node__state">
                            {{ shiftSeriesError[shiftPlan.id] }}
                          </div>
                          <template v-else-if="shiftPlanDetailsById[shiftPlan.id]?.series_rows.length">
                            <article
                              v-for="series in shiftPlanDetailsById[shiftPlan.id]!.series_rows"
                              :key="series.id"
                              class="customer-order-structure-node"
                              data-testid="customer-order-structure-series"
                            >
                              <div class="customer-order-structure-node__summary">
                                <div class="customer-order-structure-node__content">
                                  <p class="eyebrow">{{ t("customerAdmin.orders.structure.series") }}</p>
                                  <strong>{{ series.label }}</strong>
                                  <div class="customer-order-structure-node__meta">
                                    <span>{{ formatDateRange(series.date_from, series.date_to) }}</span>
                                    <span>{{ formatReleaseStateLabel(series.release_state) }}</span>
                                  </div>
                                  <div class="customer-order-structure-node__badges">
                                    <span class="customer-order-structure-node__badge">
                                      {{ t("customerAdmin.orders.structure.exceptions") }}: {{ exceptionCount(series.id) ?? 0 }}
                                    </span>
                                    <span class="customer-order-structure-node__badge">
                                      {{ t("customerAdmin.orders.structure.generatedShifts") }}: {{ generatedShiftCount(shiftPlan.id, series.id) ?? 0 }}
                                    </span>
                                  </div>
                                </div>
                                <div class="customer-order-structure-node__actions">
                                  <button
                                    type="button"
                                    class="cta-button cta-secondary"
                                    data-testid="customer-order-structure-series-open"
                                    @click="openStep({ orderId: summaryState.order.id, planningRecordId: planningRecord.id, shiftPlanId: shiftPlan.id, seriesId: series.id, step: 'series-exceptions' })"
                                  >
                                    {{ t("customerAdmin.orders.structure.openSeriesStep") }}
                                  </button>
                                </div>
                              </div>
                            </article>
                          </template>
                          <div v-else class="customer-order-structure-node__state" data-testid="customer-order-structure-no-series">
                            <strong>{{ t("customerAdmin.orders.structure.noSeriesTitle") }}</strong>
                            <span>{{ t("customerAdmin.orders.structure.noSeriesBody") }}</span>
                          </div>
                        </div>
                      </article>
                    </template>
                    <div v-else class="customer-order-structure-node__state" data-testid="customer-order-structure-no-shift-plans">
                      <strong>{{ t("customerAdmin.orders.structure.noShiftPlansTitle") }}</strong>
                      <span>{{ t("customerAdmin.orders.structure.noShiftPlansBody") }}</span>
                    </div>
                  </div>
                </article>
              </template>
              <div v-else class="customer-order-structure-node__state" data-testid="customer-order-structure-no-planning-records">
                <strong>{{ t("customerAdmin.orders.structure.noPlanningRecordsTitle") }}</strong>
                <span>{{ t("customerAdmin.orders.structure.noPlanningRecordsBody") }}</span>
                <button
                  type="button"
                  class="cta-button cta-secondary"
                  data-testid="customer-order-structure-open-planning-record-step"
                  @click="openStep({ orderId: summaryState.order.id, step: 'planning-record-overview' })"
                >
                  {{ t("customerAdmin.orders.structure.openPlanningRecordStep") }}
                </button>
              </div>
            </div>
          </section>
        </div>
      </template>
      <EmptyState
        v-else
        :title="t('customerAdmin.orders.structure.emptyTitle')"
        :description="t('customerAdmin.orders.structure.emptyBody')"
      />
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.customer-order-structure-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: grid;
  place-items: center;
  padding: 2rem;
  background: rgb(15 23 42 / 35%);
  overflow-y: auto;
}

.customer-order-structure-modal {
  width: min(100%, 980px);
  max-height: min(88vh, 980px);
  overflow: auto;
  display: grid;
  gap: 1rem;
}

.customer-order-structure-modal__header,
.customer-order-structure-node__summary,
.customer-order-structure-node__actions,
.customer-order-structure-node__badges {
  display: flex;
  gap: 0.75rem;
}

.customer-order-structure-modal__header,
.customer-order-structure-node__summary {
  justify-content: space-between;
  align-items: flex-start;
}

.customer-order-structure-modal__header-actions,
.customer-order-structure-node__actions,
.customer-order-structure-node__badges {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.customer-order-structure-modal__state,
.customer-order-structure-node__state {
  display: grid;
  gap: 0.35rem;
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-page);
}

.customer-order-structure-tree {
  display: grid;
  gap: 0.9rem;
}

.customer-order-structure-tree__children {
  display: grid;
  gap: 0.75rem;
  margin-top: 0.75rem;
  padding-left: 1.25rem;
  border-left: 1px solid var(--sp-color-border-soft);
}

.customer-order-structure-node {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
}

.customer-order-structure-node--root {
  border-color: color-mix(in srgb, var(--sp-color-primary) 32%, var(--sp-color-border-soft));
}

.customer-order-structure-node__content {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  margin-left: 15px;
}

.customer-order-structure-node__content strong,
.customer-order-structure-modal__header h3,
.customer-order-structure-modal__header p {
  margin: 0;
}

.customer-order-structure-node__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem 1rem;
  color: var(--sp-color-text-secondary);
}

.customer-order-structure-node__badge {
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--sp-color-primary-muted) 40%, transparent);
  color: var(--sp-color-text-secondary);
  font-size: 0.84rem;
}

.customer-order-structure-node__toggle {
  width: 2rem;
  height: 2rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 999px;
  background: var(--sp-color-surface-page);
  cursor: pointer;
  flex: 0 0 auto;
}

@media (max-width: 860px) {
  .customer-order-structure-modal-backdrop {
    padding: 1rem;
  }

  .customer-order-structure-modal__header,
  .customer-order-structure-node__summary {
    flex-direction: column;
  }

  .customer-order-structure-tree__children {
    padding-left: 0.9rem;
  }
}
</style>
