<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";

import { Card, Tag } from "ant-design-vue";

import EmptyState from "#/components/sicherplan/empty-state.vue";
import { listCustomers, type CustomerListItem } from "@/api/customers";
import { listPlanningRecords, type PlanningListItem } from "@/api/planningAdmin";
import {
  formatPlanningOrderReferenceOption,
} from "@/features/planning/planningOrders.helpers.js";
import { formatPlanningCustomerOption } from "@/features/planning/planningAdmin.helpers.js";
import type { CustomerOrderListItem, CustomerOrderRead, PlanningReferenceOptionRead } from "@/api/planningOrders";
import { getCustomerOrder, listCustomerOrders, listServiceCategoryOptions } from "@/api/planningOrders";
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

interface OrderListRow extends CustomerOrderListItem {
  displayStateKey: string;
  displayTone: DisplayStateTone;
}

const props = defineProps<{
  accessToken: string;
  canStartNewOrder?: boolean;
  customerId: string;
  reloadToken?: number;
  tenantId: string;
}>();

const emit = defineEmits<{
  (event: "edit-order", orderId: string): void;
  (event: "start-new-order"): void;
}>();

const { t, locale } = useI18n();

const orders = ref<OrderListRow[]>([]);
const loading = ref(false);
const error = ref("");
const searchInput = ref("");
const activeSearch = ref("");
const sortBy = ref<SortOptionId>("createdAtDesc");
const debounceHandle = ref<number | null>(null);
const requestVersion = ref(0);
const selectedOrderPreviewId = ref("");
const selectedOrderPreview = ref<CustomerOrderRead | null>(null);
const orderPreviewLoading = ref(false);
const orderPreviewError = ref("");
const orderPreviewModalOpen = ref(false);
const orderPreviewRequestVersion = ref(0);
const ORDER_PREVIEW_TOP_OFFSET = 25;
const customerOptions = ref<CustomerListItem[]>([]);
const serviceCategoryOptions = ref<PlanningReferenceOptionRead[]>([]);
const requirementTypeOptions = ref<PlanningListItem[]>([]);
const patrolRouteOptions = ref<PlanningListItem[]>([]);

const sortOptions = computed(() => [
  { value: "createdAtDesc", label: t("customerAdmin.orders.sort.createdAtDesc") },
  { value: "createdAtAsc", label: t("customerAdmin.orders.sort.createdAtAsc") },
  { value: "executionStartDesc", label: t("customerAdmin.orders.sort.executionStartDesc") },
  { value: "executionStartAsc", label: t("customerAdmin.orders.sort.executionStartAsc") },
  { value: "executionEndDesc", label: t("customerAdmin.orders.sort.executionEndDesc") },
  { value: "executionEndAsc", label: t("customerAdmin.orders.sort.executionEndAsc") },
  { value: "releaseDateDesc", label: t("customerAdmin.orders.sort.releaseDateDesc") },
  { value: "releaseDateAsc", label: t("customerAdmin.orders.sort.releaseDateAsc") },
  { value: "status", label: t("customerAdmin.orders.sort.status") },
]);

const serviceCategoryLabelMap = computed(
  () => new Map(serviceCategoryOptions.value.map((option) => [option.code, option.label])),
);
const customerLabelMap = computed(
  () =>
    new Map(
      customerOptions.value
        .map((customer) => [customer.id, formatPlanningCustomerOption(customer)])
        .filter((entry): entry is [string, string] => Boolean(entry[0] && entry[1])),
    ),
);
const requirementTypeLabelMap = computed(
  () =>
    new Map(
      requirementTypeOptions.value.map((record) => [record.id, formatPlanningOrderReferenceOption("requirement_type", record)]),
    ),
);
const patrolRouteLabelMap = computed(
  () =>
    new Map(
      patrolRouteOptions.value.map((record) => [record.id, formatPlanningOrderReferenceOption("patrol_route", record)]),
    ),
);

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

function compareOrderIdentity(left: CustomerOrderListItem, right: CustomerOrderListItem) {
  const leftTitle = typeof left.title === "string" ? left.title : "";
  const rightTitle = typeof right.title === "string" ? right.title : "";
  const byTitle = leftTitle.localeCompare(rightTitle);
  if (byTitle !== 0) {
    return byTitle;
  }
  return left.order_no.localeCompare(right.order_no) || left.id.localeCompare(right.id);
}

const sortedOrders = computed(() => {
  const rows = [...orders.value];

  rows.sort((left, right) => {
    let comparison = 0;
    switch (sortBy.value) {
      case "createdAtAsc":
        comparison = compareNullableDates((left as Partial<CustomerOrderListItem> & { created_at?: string }).created_at, (right as Partial<CustomerOrderListItem> & { created_at?: string }).created_at, "asc");
        break;
      case "createdAtDesc":
        comparison = compareNullableDates((left as Partial<CustomerOrderListItem> & { created_at?: string }).created_at, (right as Partial<CustomerOrderListItem> & { created_at?: string }).created_at, "desc");
        break;
      case "executionStartAsc":
        comparison = compareNullableDates(left.service_from, right.service_from, "asc", (value) => parseDateBoundary(value, "start"));
        break;
      case "executionStartDesc":
        comparison = compareNullableDates(left.service_from, right.service_from, "desc", (value) => parseDateBoundary(value, "start"));
        break;
      case "executionEndAsc":
        comparison = compareNullableDates(left.service_to, right.service_to, "asc", (value) => parseDateBoundary(value, "end"));
        break;
      case "executionEndDesc":
        comparison = compareNullableDates(left.service_to, right.service_to, "desc", (value) => parseDateBoundary(value, "end"));
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
    return compareOrderIdentity(left, right);
  });
  return rows;
});

function formatDate(value: string | null | undefined) {
  if (!value) {
    return t("customerAdmin.summary.none");
  }
  return new Intl.DateTimeFormat(locale.value, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function resolveDisplayState(order: CustomerOrderListItem) {
  const now = Date.now();
  const serviceFrom = parseDateBoundary(order.service_from, "start");
  const serviceTo = parseDateBoundary(order.service_to, "end");

  if (order.status === "archived") {
    return {
      key: "archived",
      label: t("customerAdmin.orders.displayState.archived"),
      tone: "muted" as const,
    };
  }
  if (order.release_state === "draft") {
    return {
      key: "draft",
      label: t("coreAdmin.status.draft"),
      tone: "warn" as const,
    };
  }
  if (order.release_state === "release_ready") {
    return {
      key: "release_ready",
      label: t("coreAdmin.status.release_ready"),
      tone: "warn" as const,
    };
  }
  if (order.release_state === "released") {
    if (Number.isFinite(serviceFrom) && now < serviceFrom) {
      return {
        key: "upcoming",
        label: t("customerAdmin.orders.displayState.upcoming"),
        tone: "good" as const,
      };
    }
    if (Number.isFinite(serviceTo) && now > serviceTo) {
      return {
        key: "completed",
        label: t("customerAdmin.orders.displayState.completed"),
        tone: "neutral" as const,
      };
    }
    return {
      key: "in_progress",
      label: t("customerAdmin.orders.displayState.inProgress"),
      tone: "good" as const,
    };
  }
  return {
    key: "neutral",
    label: order.release_state || order.status || t("customerAdmin.summary.none"),
    tone: "neutral" as const,
  };
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

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return t("customerAdmin.summary.none");
  }
  return new Intl.DateTimeFormat(locale.value, {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function formatReadableValue(value: string | null | undefined) {
  return typeof value === "string" && value.trim() ? value.trim() : t("customerAdmin.summary.none");
}

function customerDisplayLabel(customerId: string | null | undefined) {
  return customerLabelMap.value.get(customerId ?? "") || formatReadableValue(customerId);
}

function serviceCategoryDisplayLabel(serviceCategoryCode: string | null | undefined) {
  return serviceCategoryLabelMap.value.get(serviceCategoryCode ?? "") || formatReadableValue(serviceCategoryCode);
}

function requirementTypeDisplayLabel(requirementTypeId: string | null | undefined) {
  return requirementTypeLabelMap.value.get(requirementTypeId ?? "") || formatReadableValue(requirementTypeId);
}

function patrolRouteDisplayLabel(patrolRouteId: string | null | undefined) {
  return patrolRouteLabelMap.value.get(patrolRouteId ?? "") || formatReadableValue(patrolRouteId);
}

function closeOrderDetail() {
  orderPreviewModalOpen.value = false;
  orderPreviewError.value = "";
  orderPreviewLoading.value = false;
}

async function openOrderDetail(orderId: string) {
  if (!props.tenantId || !props.accessToken || !orderId) {
    return;
  }
  selectedOrderPreviewId.value = orderId;
  selectedOrderPreview.value = null;
  orderPreviewError.value = "";
  orderPreviewLoading.value = true;
  orderPreviewModalOpen.value = true;
  const version = ++orderPreviewRequestVersion.value;

  try {
    const order = await getCustomerOrder(props.tenantId, orderId, props.accessToken);
    if (version !== orderPreviewRequestVersion.value) {
      return;
    }
    selectedOrderPreview.value = order;
  } catch {
    if (version !== orderPreviewRequestVersion.value) {
      return;
    }
    orderPreviewError.value = t("customerAdmin.orders.detail.errorBody");
  } finally {
    if (version === orderPreviewRequestVersion.value) {
      orderPreviewLoading.value = false;
    }
  }
}

function openOrderWorkspace(orderId: string) {
  emit("edit-order", orderId);
}

function handlePreviewKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    closeOrderDetail();
  }
}

function handleWindowKeydown(event: KeyboardEvent) {
  if (orderPreviewModalOpen.value && event.key === "Escape") {
    closeOrderDetail();
  }
}

async function loadOrders() {
  if (!props.customerId || !props.tenantId || !props.accessToken) {
    orders.value = [];
    error.value = "";
    return;
  }

  const version = ++requestVersion.value;
  loading.value = true;
  orders.value = [];
  error.value = "";

  try {
    const rows = await listCustomerOrders(props.tenantId, props.accessToken, {
      customer_id: props.customerId,
      search: activeSearch.value,
    });
    if (version !== requestVersion.value) {
      return;
    }
    orders.value = rows.map((row) => {
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
    orders.value = [];
    error.value = t("customerAdmin.orders.errorBody");
  } finally {
    if (version === requestVersion.value) {
      loading.value = false;
    }
  }
}

async function loadOrderPreviewLookups() {
  if (!props.customerId || !props.tenantId || !props.accessToken) {
    customerOptions.value = [];
    serviceCategoryOptions.value = [];
    requirementTypeOptions.value = [];
    patrolRouteOptions.value = [];
    return;
  }

  const [customers, serviceCategories, requirementTypes, patrolRoutes] = await Promise.allSettled([
    listCustomers(props.tenantId, props.accessToken, {}),
    listServiceCategoryOptions(props.tenantId, props.accessToken),
    listPlanningRecords("requirement_type", props.tenantId, props.accessToken, { customer_id: props.customerId }),
    listPlanningRecords("patrol_route", props.tenantId, props.accessToken, { customer_id: props.customerId }),
  ]);

  customerOptions.value = customers.status === "fulfilled" ? customers.value : [];
  serviceCategoryOptions.value = serviceCategories.status === "fulfilled" ? serviceCategories.value : [];
  requirementTypeOptions.value = requirementTypes.status === "fulfilled" ? requirementTypes.value : [];
  patrolRouteOptions.value = patrolRoutes.status === "fulfilled" ? patrolRoutes.value : [];
}

watch(
  () => searchInput.value,
  (value) => {
    if (debounceHandle.value != null) {
      window.clearTimeout(debounceHandle.value);
    }
    debounceHandle.value = window.setTimeout(() => {
      activeSearch.value = value.trim();
      void loadOrders();
    }, 250);
  },
);

watch(
  () => [props.customerId, props.tenantId, props.accessToken, props.reloadToken],
  () => {
    searchInput.value = "";
    activeSearch.value = "";
    void loadOrders();
    void loadOrderPreviewLookups();
  },
  { immediate: true },
);

watch(
  () => orderPreviewModalOpen.value,
  (isOpen) => {
    if (isOpen) {
      window.addEventListener("keydown", handleWindowKeydown);
      return;
    }
    window.removeEventListener("keydown", handleWindowKeydown);
  },
);

onBeforeUnmount(() => {
  if (debounceHandle.value != null) {
    window.clearTimeout(debounceHandle.value);
  }
  window.removeEventListener("keydown", handleWindowKeydown);
});
</script>

<template>
  <section class="customer-orders-tab" data-testid="customer-tab-panel-orders">
    <div class="customer-orders-tab__panel">
      <div class="customer-orders-tab__header">
        <div class="customer-orders-tab__intro">
          <p class="eyebrow">{{ t("customerAdmin.orders.eyebrow") }}</p>
          <h3>{{ t("customerAdmin.orders.title") }}</h3>
        </div>
        <button
          v-if="canStartNewOrder"
          class="cta-button"
          type="button"
          data-testid="customer-orders-new-order"
          @click="emit('start-new-order')"
        >
          {{ t("customerAdmin.actions.newOrder") }}
        </button>
      </div>

      <div class="customer-orders-tab__toolbar" data-testid="customer-orders-toolbar">
        <label class="customer-orders-tab__field customer-orders-tab__field--search">
          <span>{{ t("customerAdmin.filters.search") }}</span>
          <input
            v-model="searchInput"
            :placeholder="t('customerAdmin.orders.searchPlaceholder')"
            data-testid="customer-orders-search"
          />
        </label>
        <label class="customer-orders-tab__field customer-orders-tab__field--sort">
          <span>{{ t("customerAdmin.orders.sortLabel") }}</span>
          <select v-model="sortBy" data-testid="customer-orders-sort">
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="loading" class="customer-orders-tab__state" data-testid="customer-orders-loading">
      {{ t("workspace.loading.processing") }}
    </div>
    <div v-else-if="error" class="customer-orders-tab__state" data-testid="customer-orders-error">
      <strong>{{ t("customerAdmin.orders.errorTitle") }}</strong>
      <span>{{ error }}</span>
    </div>
    <div v-else-if="sortedOrders.length" class="customer-orders-tab__list">
      <Card
        v-for="order in sortedOrders"
        :key="order.id"
        :bordered="false"
        class="customer-orders-tab__row"
        :data-tone="order.displayTone"
        :data-state="order.displayStateKey"
      >
        <div class="customer-orders-tab__row-layout">
        <button
          type="button"
          class="customer-orders-tab__row-button"
          data-testid="customer-orders-card-open"
          @click="openOrderDetail(order.id)"
        >
        <div class="customer-orders-tab__row-main">
          <div>
            <strong>{{ order.title || order.order_no }}</strong>
            <div class="customer-orders-tab__meta">
              <span>{{ order.order_no }}</span>
              <span>{{ formatDate(order.service_from) }} → {{ formatDate(order.service_to) }}</span>
              <span>{{ order.service_category_code || order.requirement_type_id }}</span>
              <span>{{ t("customerAdmin.orders.registrationDate") }}: {{ formatDate((order as { created_at?: string }).created_at) }}</span>
              <span>{{ t("customerAdmin.orders.releaseDate") }}: {{ formatDate(order.released_at) }}</span>
            </div>
          </div>
          <div class="customer-orders-tab__row-side">
            <Tag
              class="customer-orders-tab__state-tag"
              :color="mapTagColor(order.displayTone)"
              :data-tone="order.displayTone"
              :data-state="order.displayStateKey"
            >
              {{ resolveDisplayState(order).label }}
            </Tag>
            <small>{{ t("customerAdmin.orders.rawReleaseState") }}: {{ order.release_state }}</small>
          </div>
        </div>
        </button>
        <div class="customer-orders-tab__row-actions">
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-orders-card-edit"
            @click.stop="openOrderWorkspace(order.id)"
          >
            {{ t("customerAdmin.actions.edit") }}
          </button>
        </div>
        </div>
      </Card>
    </div>
    <EmptyState
      v-else
      :title="t('customerAdmin.orders.emptyTitle')"
      :description="t('customerAdmin.orders.emptyBody')"
    />

    <div
      v-if="orderPreviewModalOpen"
      class="customer-admin-modal-backdrop customer-orders-tab__modal-backdrop"
      :style="{ '--customer-orders-preview-top-offset': `calc(var(--sp-sticky-offset, 6.5rem) + ${ORDER_PREVIEW_TOP_OFFSET}px)` }"
      @click.self="closeOrderDetail"
    >
      <section
        class="module-card customer-admin-modal customer-orders-tab__modal"
        data-testid="customer-orders-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="customer-orders-detail-title"
        tabindex="-1"
        @keydown="handlePreviewKeydown"
      >
        <header class="customer-orders-tab__modal-header">
          <div>
            <p class="eyebrow">{{ t("customerAdmin.orders.detail.eyebrow") }}</p>
            <h3 id="customer-orders-detail-title">
              {{ selectedOrderPreview?.title || selectedOrderPreview?.order_no || t("customerAdmin.orders.detail.title") }}
            </h3>
            <span>{{ selectedOrderPreview?.order_no || selectedOrderPreviewId }}</span>
          </div>
          <button
            type="button"
            class="cta-button cta-secondary"
            data-testid="customer-orders-detail-close"
            @click="closeOrderDetail"
          >
            {{ t("customerAdmin.orders.detail.close") }}
          </button>
        </header>

        <div v-if="orderPreviewLoading" class="customer-orders-tab__state" data-testid="customer-orders-detail-loading">
          {{ t("customerAdmin.orders.detail.loading") }}
        </div>
        <div v-else-if="orderPreviewError" class="customer-orders-tab__state" data-testid="customer-orders-detail-error">
          <strong>{{ t("customerAdmin.orders.detail.errorTitle") }}</strong>
          <span>{{ orderPreviewError }}</span>
        </div>
        <template v-else-if="selectedOrderPreview">
          <div class="customer-orders-tab__modal-summary">
            <Tag
              class="customer-orders-tab__state-tag"
              :color="mapTagColor(resolveDisplayState(selectedOrderPreview).tone)"
              :data-tone="resolveDisplayState(selectedOrderPreview).tone"
              :data-state="resolveDisplayState(selectedOrderPreview).key"
            >
              {{ resolveDisplayState(selectedOrderPreview).label }}
            </Tag>
            <span>{{ t("customerAdmin.orders.rawReleaseState") }}: {{ formatReleaseStateLabel(selectedOrderPreview.release_state) }}</span>
          </div>

          <dl class="customer-orders-tab__detail-grid">
            <div>
              <dt>{{ t("customerAdmin.orders.detail.customer") }}</dt>
              <dd>{{ customerDisplayLabel(selectedOrderPreview.customer_id) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.serviceFrom") }}</dt>
              <dd>{{ formatDate(selectedOrderPreview.service_from) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.serviceTo") }}</dt>
              <dd>{{ formatDate(selectedOrderPreview.service_to) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.serviceCategory") }}</dt>
              <dd>{{ serviceCategoryDisplayLabel(selectedOrderPreview.service_category_code) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.requirementType") }}</dt>
              <dd>{{ requirementTypeDisplayLabel(selectedOrderPreview.requirement_type_id) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.patrolRoute") }}</dt>
              <dd>{{ patrolRouteDisplayLabel(selectedOrderPreview.patrol_route_id) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.createdAt") }}</dt>
              <dd>{{ formatDateTime(selectedOrderPreview.created_at) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.updatedAt") }}</dt>
              <dd>{{ formatDateTime(selectedOrderPreview.updated_at) }}</dd>
            </div>
            <div>
              <dt>{{ t("customerAdmin.orders.detail.releasedAt") }}</dt>
              <dd>{{ formatDateTime(selectedOrderPreview.released_at) }}</dd>
            </div>
          </dl>

          <div class="customer-orders-tab__detail-text">
            <section>
              <h4>{{ t("customerAdmin.orders.detail.securityConcept") }}</h4>
              <p>{{ selectedOrderPreview.security_concept_text || t("customerAdmin.summary.none") }}</p>
            </section>
            <section>
              <h4>{{ t("customerAdmin.orders.detail.notes") }}</h4>
              <p>{{ selectedOrderPreview.notes || t("customerAdmin.summary.none") }}</p>
            </section>
          </div>

          <section class="customer-orders-tab__attachments">
            <h4>{{ t("customerAdmin.orders.detail.attachments") }}</h4>
            <ul v-if="selectedOrderPreview.attachments?.length">
              <li v-for="attachment in selectedOrderPreview.attachments" :key="attachment.id">
                {{ attachment.title || attachment.id }}
              </li>
            </ul>
            <p v-else>{{ t("customerAdmin.orders.detail.noAttachments") }}</p>
          </section>
        </template>
      </section>
    </div>
  </section>
</template>

<style scoped>
.customer-orders-tab {
  display: grid;
  gap: 1rem;
}

.customer-orders-tab__panel {
  display: grid;
  gap: 1rem;
}

.customer-orders-tab__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.customer-orders-tab__intro {
  display: grid;
  gap: 0.3rem;
}

.customer-orders-tab__intro h3,
.customer-orders-tab__intro p {
  margin: 0;
}

.customer-orders-tab__toolbar {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1fr) minmax(16rem, 22rem);
  align-items: end;
  padding: 1rem 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-shadow-card);
}

.customer-orders-tab__field {
  display: grid;
  gap: 0.42rem;
  min-width: 0;
  font-size: 0.9rem;
}

.customer-orders-tab__field--search {
  min-width: 0;
}

.customer-orders-tab__field--sort {
  justify-self: end;
  width: min(100%, 22rem);
}

.customer-orders-tab__field span {
  color: var(--sp-color-text-secondary);
}

.customer-orders-tab__field input,
.customer-orders-tab__field select {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-card);
  color: var(--sp-color-text-primary);
  padding: 0.78rem 0.9rem;
  font: inherit;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.customer-orders-tab__field input::placeholder {
  color: var(--sp-color-text-secondary);
  opacity: 1;
}

.customer-orders-tab__field input:focus,
.customer-orders-tab__field select:focus {
  outline: none;
  border-color: rgb(40 170 170 / 55%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

.customer-orders-tab__state {
  display: grid;
  gap: 0.25rem;
  padding: 1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  background: var(--sp-color-surface-card);
  color: var(--sp-color-text-secondary);
}

.customer-orders-tab__list {
  display: grid;
  gap: 0.85rem;
}

.customer-orders-tab__row {
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1rem;
  box-shadow: var(--sp-shadow-card);
}

.customer-orders-tab__row[data-tone="good"] {
  border-color: color-mix(in srgb, var(--sp-color-success) 28%, var(--sp-color-border-soft));
}

.customer-orders-tab__row[data-tone="warn"] {
  border-color: color-mix(in srgb, var(--sp-color-warning) 28%, var(--sp-color-border-soft));
}

.customer-orders-tab__row[data-tone="muted"] {
  border-color: color-mix(in srgb, var(--sp-color-text-secondary) 18%, var(--sp-color-border-soft));
}

.customer-orders-tab__row-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: stretch;
}

.customer-orders-tab__row-button {
  display: block;
  width: 100%;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.customer-orders-tab__row-button:focus-visible {
  outline: 3px solid rgb(40 170 170 / 28%);
  outline-offset: 4px;
  border-radius: 0.75rem;
}

.customer-orders-tab__row-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.customer-orders-tab__row-main > div:first-child {
  min-width: 0;
}

.customer-orders-tab__row strong {
  display: block;
  color: var(--sp-color-text-primary);
  overflow-wrap: anywhere;
}

.customer-orders-tab__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem 0.85rem;
  margin-top: 0.45rem;
  color: var(--sp-color-text-secondary);
}

.customer-orders-tab__row-side {
  display: grid;
  justify-items: end;
  gap: 0.35rem;
  text-align: right;
}

.customer-orders-tab__state-tag {
  margin-inline-end: 0;
  font-weight: 600;
}

.customer-orders-tab__row-side small {
  color: var(--sp-color-text-secondary);
}

.customer-orders-tab__row-actions {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
}

.customer-orders-tab__modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 45;
  display: grid;
  align-items: start;
  justify-items: center;
  overflow: auto;
  padding: var(--customer-orders-preview-top-offset, calc(var(--sp-sticky-offset, 6.5rem) + 25px)) 1rem 1rem;
  background: rgb(15 23 42 / 38%);
}

.customer-orders-tab__modal {
  width: min(100%, 760px);
  display: grid;
  gap: 1rem;
  max-height: calc(100vh - var(--customer-orders-preview-top-offset, calc(var(--sp-sticky-offset, 6.5rem) + 25px)) - 1rem);
  overflow: auto;
  padding: 1.25rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 1.1rem;
  background: var(--sp-color-surface-card);
  box-shadow: var(--sp-shadow-card);
}

.customer-orders-tab__modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.customer-orders-tab__modal-header h3,
.customer-orders-tab__modal-header p {
  margin: 0;
}

.customer-orders-tab__modal-header span {
  color: var(--sp-color-text-secondary);
}

.customer-orders-tab__modal-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: center;
  color: var(--sp-color-text-secondary);
}

.customer-orders-tab__detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
  margin: 0;
}

.customer-orders-tab__detail-grid div {
  display: grid;
  gap: 0.2rem;
  padding: 0.85rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.9rem;
  background: var(--sp-color-surface-page);
}

.customer-orders-tab__detail-grid dt {
  color: var(--sp-color-text-secondary);
  font-size: 0.82rem;
}

.customer-orders-tab__detail-grid dd {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--sp-color-text-primary);
  font-weight: 600;
}

.customer-orders-tab__detail-text {
  display: grid;
  gap: 0.85rem;
}

.customer-orders-tab__detail-text section,
.customer-orders-tab__attachments {
  display: grid;
  gap: 0.45rem;
  padding: 0.9rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 0.9rem;
  background: var(--sp-color-surface-card);
}

.customer-orders-tab__detail-text h4,
.customer-orders-tab__detail-text p,
.customer-orders-tab__attachments h4,
.customer-orders-tab__attachments p,
.customer-orders-tab__attachments ul {
  margin: 0;
}

.customer-orders-tab__attachments ul {
  padding-inline-start: 1.1rem;
}

@media (max-width: 900px) {
  .customer-orders-tab__toolbar {
    grid-template-columns: 1fr;
  }

  .customer-orders-tab__field--sort {
    justify-self: stretch;
    width: 100%;
  }

  .customer-orders-tab__row-main {
    flex-direction: column;
  }

  .customer-orders-tab__row-side {
    justify-items: start;
    text-align: left;
  }

  .customer-orders-tab__row-layout,
  .customer-orders-tab__detail-grid {
    grid-template-columns: 1fr;
  }

  .customer-orders-tab__row-actions,
  .customer-orders-tab__modal-header {
    justify-content: stretch;
  }

  .customer-orders-tab__modal-header {
    flex-direction: column;
  }

  .customer-orders-tab__modal-backdrop {
    padding-top: max(1rem, min(4.5rem, calc(var(--sp-sticky-offset, 6.5rem) * 0.6)));
  }
}
</style>
