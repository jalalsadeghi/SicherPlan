<template>
  <section class="planning-orders-page">
    <section class="module-card planning-orders-hero">
      <div>
        <p class="eyebrow">{{ tp("eyebrow") }}</p>
        <h2>{{ tp("title") }}</h2>
        <p class="planning-orders-lead">{{ tp("lead") }}</p>
        <div class="planning-orders-meta">
          <span class="planning-orders-meta__pill">{{ tp("readOrders") }}: {{ actionState.canReadOrders ? "on" : "off" }}</span>
          <span class="planning-orders-meta__pill">{{ tp("writeOrders") }}: {{ actionState.canWriteOrders ? "on" : "off" }}</span>
          <span class="planning-orders-meta__pill">{{ tp("readPlanning") }}: {{ actionState.canReadPlanning ? "on" : "off" }}</span>
          <span class="planning-orders-meta__pill">{{ tp("writePlanning") }}: {{ actionState.canWritePlanning ? "on" : "off" }}</span>
        </div>
      </div>

      <div class="module-card planning-orders-scope">
        <label class="field-stack">
          <span>{{ tp("scopeLabel") }}</span>
          <input v-model="tenantScopeInput" :placeholder="tp('scopePlaceholder')" />
        </label>
        <label class="field-stack">
          <span>{{ tp("tokenLabel") }}</span>
          <input v-model="accessTokenInput" type="password" :placeholder="tp('tokenPlaceholder')" />
        </label>
        <p class="field-help">{{ tp("tokenHelp") }}</p>
        <div class="cta-row">
          <button class="cta-button" type="button" @click="rememberScopeAndToken">{{ tp("actionsRemember") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canReadAnything" @click="refreshAll">{{ tp("actionsRefresh") }}</button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="planning-orders-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("actionsClearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card planning-orders-empty">
      <p class="eyebrow">{{ tp("missingScopeTitle") }}</p>
      <h3>{{ tp("missingScopeBody") }}</h3>
    </section>

    <section v-else-if="!canReadAnything" class="module-card planning-orders-empty">
      <p class="eyebrow">{{ tp("missingPermissionTitle") }}</p>
      <h3>{{ tp("missingPermissionBody") }}</h3>
    </section>

    <div v-else class="planning-orders-grid">
      <section class="module-card planning-orders-panel">
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("ordersTitle") }}</p>
            <h3>{{ tp("ordersTitle") }}</h3>
          </div>
          <StatusBadge :status="loading.orders ? 'inactive' : 'active'" />
        </div>

        <div class="planning-orders-form-grid">
          <label class="field-stack">
            <span>{{ tp("filtersSearch") }}</span>
            <input v-model="orderFilters.search" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersCustomerId") }}</span>
            <input v-model="orderFilters.customer_id" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersReleaseState") }}</span>
            <select v-model="orderFilters.release_state">
              <option value="">{{ tp("fieldsReleaseState") }}</option>
              <option value="draft">{{ tp("statusDraft") }}</option>
              <option value="release_ready">{{ tp("statusReleaseReady") }}</option>
              <option value="released">{{ tp("statusReleased") }}</option>
            </select>
          </label>
        </div>

        <label class="planning-orders-checkbox">
          <input v-model="orderFilters.include_archived" type="checkbox" />
          <span>{{ tp("filtersIncludeArchived") }}</span>
        </label>

        <div class="cta-row">
          <button class="cta-button" type="button" @click="refreshOrders">{{ tp("actionsRefresh") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreateOrder" @click="startCreateOrder">{{ tp("actionsNewOrder") }}</button>
        </div>

        <div v-if="orders.length" class="planning-orders-list">
          <button
            v-for="order in orders"
            :key="order.id"
            type="button"
            class="planning-orders-row"
            :class="{ selected: order.id === selectedOrderId }"
            @click="selectOrder(order.id)"
          >
            <div>
              <strong>{{ order.order_no }} · {{ order.title }}</strong>
              <span>{{ order.customer_id }}</span>
            </div>
            <StatusBadge :status="order.release_state" />
          </button>
        </div>
        <p v-else class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
      </section>

      <section class="module-card planning-orders-panel planning-orders-detail">
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <h3>{{ selectedOrder ? `${selectedOrder.order_no} · ${selectedOrder.title}` : tp("noOrderSelected") }}</h3>
          </div>
          <StatusBadge v-if="selectedOrder" :status="selectedOrder.release_state" />
        </div>

        <template v-if="isCreatingOrder || selectedOrder">
          <form class="planning-orders-form" @submit.prevent="submitOrder">
            <div class="planning-orders-form-grid">
              <label class="field-stack"><span>{{ tp("filtersCustomerId") }}</span><input v-model="orderDraft.customer_id" required /></label>
              <label class="field-stack"><span>{{ tp("fieldsRequirementTypeId") }}</span><input v-model="orderDraft.requirement_type_id" required /></label>
              <label class="field-stack"><span>{{ tp("fieldsPatrolRouteId") }}</span><input v-model="orderDraft.patrol_route_id" /></label>
              <label class="field-stack"><span>{{ tp("fieldsOrderNo") }}</span><input v-model="orderDraft.order_no" required /></label>
              <label class="field-stack"><span>{{ tp("fieldsTitle") }}</span><input v-model="orderDraft.title" required /></label>
              <label class="field-stack"><span>{{ tp("fieldsServiceCategory") }}</span><input v-model="orderDraft.service_category_code" required /></label>
              <label class="field-stack"><span>{{ tp("fieldsServiceFrom") }}</span><input v-model="orderDraft.service_from" type="date" required /></label>
              <label class="field-stack"><span>{{ tp("fieldsServiceTo") }}</span><input v-model="orderDraft.service_to" type="date" required /></label>
              <label class="field-stack"><span>{{ tp("fieldsStatus") }}</span><input v-model="orderDraft.status" /></label>
              <label class="field-stack field-stack--wide"><span>{{ tp("fieldsSecurityConcept") }}</span><textarea v-model="orderDraft.security_concept_text" rows="3" /></label>
              <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="orderDraft.notes" rows="3" /></label>
            </div>

            <div class="cta-row">
              <button class="cta-button" type="submit" :disabled="!actionState.canWriteOrders">{{ tp("actionsSave") }}</button>
              <button class="cta-button cta-secondary" type="button" @click="resetOrderDraft">{{ tp("actionsReset") }}</button>
            </div>
          </form>

          <section v-if="selectedOrder" class="planning-orders-section">
            <div class="planning-orders-panel__header"><h3>{{ tp("sectionCommercial") }}</h3></div>
            <p :class="selectedOrderCommercial?.is_release_ready ? 'planning-orders-state--good' : 'planning-orders-state--bad'">
              {{ selectedOrderCommercial?.is_release_ready ? tp("commercialReady") : tp("commercialBlocked") }}
            </p>
            <ul v-if="selectedOrderCommercial?.blocking_issues?.length" class="planning-orders-issues">
              <li v-for="issue in selectedOrderCommercial.blocking_issues" :key="issue.code">{{ issue.code }}</li>
            </ul>
            <p v-if="selectedOrderCommercial?.warning_issues?.length" class="planning-orders-state--warn">{{ tp("commercialWarnings") }}</p>
          </section>

          <section v-if="selectedOrder" class="planning-orders-section">
            <div class="planning-orders-panel__header"><h3>{{ tp("sectionOrderRelease") }}</h3></div>
            <div class="cta-row">
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionOrder" @click="transitionOrder('draft')">{{ tp("actionsBackToDraft") }}</button>
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionOrder" @click="transitionOrder('release_ready')">{{ tp("actionsReleaseReady") }}</button>
              <button class="cta-button" type="button" :disabled="!actionState.canTransitionOrder" @click="transitionOrder('released')">{{ tp("actionsReleased") }}</button>
            </div>
          </section>

          <section v-if="selectedOrder" class="planning-orders-section">
            <div class="planning-orders-panel__header"><h3>{{ tp("sectionOrderDocuments") }}</h3></div>
            <div v-if="orderAttachments.length" class="planning-orders-doc-list">
              <div v-for="document in orderAttachments" :key="document.id" class="planning-orders-doc-row">
                <strong>{{ document.title }}</strong>
                <span>{{ document.id }}</span>
              </div>
            </div>
            <p v-else class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
            <form class="planning-orders-form" @submit.prevent="submitOrderAttachment">
              <div class="planning-orders-form-grid">
                <label class="field-stack"><span>{{ tp("fieldsDocumentTitle") }}</span><input v-model="orderAttachmentDraft.title" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="orderAttachmentDraft.label" /></label>
                <label class="field-stack"><span>{{ tp("fieldsDocumentFile") }}</span><input type="file" @change="onOrderAttachmentSelected" /></label>
              </div>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canManageOrderDocs || !orderAttachmentDraft.content_base64">{{ tp("actionsUploadDocument") }}</button>
              </div>
            </form>
            <form class="planning-orders-form" @submit.prevent="linkExistingOrderDocument">
              <div class="planning-orders-form-grid">
                <label class="field-stack"><span>{{ tp("fieldsDocumentId") }}</span><input v-model="orderAttachmentLink.document_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="orderAttachmentLink.label" /></label>
              </div>
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canManageOrderDocs">{{ tp("actionsLinkDocument") }}</button>
              </div>
            </form>
          </section>

          <section v-if="selectedOrder" class="planning-orders-section">
            <div class="planning-orders-panel__header">
              <div>
                <p class="eyebrow">{{ tp("sectionPlanningList") }}</p>
                <h3>{{ tp("planningTitle") }}</h3>
              </div>
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreatePlanning" @click="startCreatePlanning">{{ tp("actionsNewPlanning") }}</button>
            </div>
            <div v-if="planningRecords.length" class="planning-orders-list">
              <button
                v-for="record in planningRecords"
                :key="record.id"
                type="button"
                class="planning-orders-row"
                :class="{ selected: record.id === selectedPlanningRecordId }"
                @click="selectPlanningRecord(record.id)"
              >
                <div>
                  <strong>{{ record.name }}</strong>
                  <span>{{ planningModeText(record.planning_mode_code) }}</span>
                </div>
                <StatusBadge :status="record.release_state" />
              </button>
            </div>
            <p v-else class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>

            <form class="planning-orders-form" @submit.prevent="submitPlanningRecord">
              <div class="planning-orders-form-grid">
                <label class="field-stack">
                  <span>{{ tp("fieldsPlanningMode") }}</span>
                  <select v-model="planningDraft.planning_mode_code" :disabled="!isCreatingPlanning">
                    <option value="event">{{ tp("modeEvent") }}</option>
                    <option value="site">{{ tp("modeSite") }}</option>
                    <option value="trade_fair">{{ tp("modeTradeFair") }}</option>
                    <option value="patrol">{{ tp("modePatrol") }}</option>
                  </select>
                </label>
                <label class="field-stack"><span>{{ tp("fieldsPlanningName") }}</span><input v-model="planningDraft.name" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsPlanningFrom") }}</span><input v-model="planningDraft.planning_from" type="date" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsPlanningTo") }}</span><input v-model="planningDraft.planning_to" type="date" required /></label>
                <label class="field-stack"><span>{{ tp("fieldsDispatcherUserId") }}</span><input v-model="planningDraft.dispatcher_user_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsParentPlanningRecordId") }}</span><input v-model="planningDraft.parent_planning_record_id" /></label>
                <label class="field-stack"><span>{{ tp("fieldsStatus") }}</span><input v-model="planningDraft.status" /></label>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="planningDraft.notes" rows="3" /></label>
              </div>

              <section class="planning-orders-subsection">
                <h4>{{ tp("sectionModeDetails") }}</h4>
                <div v-if="planningDraft.planning_mode_code === 'event'" class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsEventVenueId") }}</span><input v-model="planningDraft.event_detail.event_venue_id" required /></label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsSetupNote") }}</span><textarea v-model="planningDraft.event_detail.setup_note" rows="2" /></label>
                </div>
                <div v-else-if="planningDraft.planning_mode_code === 'site'" class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsSiteId") }}</span><input v-model="planningDraft.site_detail.site_id" required /></label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsWatchbookScopeNote") }}</span><textarea v-model="planningDraft.site_detail.watchbook_scope_note" rows="2" /></label>
                </div>
                <div v-else-if="planningDraft.planning_mode_code === 'trade_fair'" class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsTradeFairId") }}</span><input v-model="planningDraft.trade_fair_detail.trade_fair_id" required /></label>
                  <label class="field-stack"><span>{{ tp("fieldsTradeFairZoneId") }}</span><input v-model="planningDraft.trade_fair_detail.trade_fair_zone_id" /></label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsStandNote") }}</span><textarea v-model="planningDraft.trade_fair_detail.stand_note" rows="2" /></label>
                </div>
                <div v-else class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsPatrolRouteDetailId") }}</span><input v-model="planningDraft.patrol_detail.patrol_route_id" required /></label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsExecutionNote") }}</span><textarea v-model="planningDraft.patrol_detail.execution_note" rows="2" /></label>
                </div>
              </section>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canWritePlanning">{{ tp("actionsSave") }}</button>
                <button class="cta-button cta-secondary" type="button" @click="resetPlanningDraft">{{ tp("actionsReset") }}</button>
              </div>
            </form>

            <section v-if="selectedPlanningRecord" class="planning-orders-section">
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionCommercial") }}</h3></div>
              <p :class="selectedPlanningCommercial?.is_release_ready ? 'planning-orders-state--good' : 'planning-orders-state--bad'">
                {{ selectedPlanningCommercial?.is_release_ready ? tp("commercialReady") : tp("commercialBlocked") }}
              </p>
              <ul v-if="selectedPlanningCommercial?.blocking_issues?.length" class="planning-orders-issues">
                <li v-for="issue in selectedPlanningCommercial.blocking_issues" :key="issue.code">{{ issue.code }}</li>
              </ul>
              <p v-if="selectedPlanningCommercial?.warning_issues?.length" class="planning-orders-state--warn">{{ tp("commercialWarnings") }}</p>
            </section>

            <section v-if="selectedPlanningRecord" class="planning-orders-section">
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionPlanningRelease") }}</h3></div>
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionPlanning" @click="transitionPlanning('draft')">{{ tp("actionsBackToDraft") }}</button>
                <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionPlanning" @click="transitionPlanning('release_ready')">{{ tp("actionsReleaseReady") }}</button>
                <button class="cta-button" type="button" :disabled="!actionState.canTransitionPlanning" @click="transitionPlanning('released')">{{ tp("actionsReleased") }}</button>
              </div>
            </section>

            <section v-if="selectedPlanningRecord" class="planning-orders-section">
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionPlanningDocuments") }}</h3></div>
              <div v-if="planningAttachments.length" class="planning-orders-doc-list">
                <div v-for="document in planningAttachments" :key="document.id" class="planning-orders-doc-row">
                  <strong>{{ document.title }}</strong>
                  <span>{{ document.id }}</span>
                </div>
              </div>
              <p v-else class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
              <form class="planning-orders-form" @submit.prevent="submitPlanningAttachment">
                <div class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsDocumentTitle") }}</span><input v-model="planningAttachmentDraft.title" required /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="planningAttachmentDraft.label" /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentFile") }}</span><input type="file" @change="onPlanningAttachmentSelected" /></label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManagePlanningDocs || !planningAttachmentDraft.content_base64">{{ tp("actionsUploadDocument") }}</button>
                </div>
              </form>
              <form class="planning-orders-form" @submit.prevent="linkExistingPlanningDocument">
                <div class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsDocumentId") }}</span><input v-model="planningAttachmentLink.document_id" /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="planningAttachmentLink.label" /></label>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canManagePlanningDocs">{{ tp("actionsLinkDocument") }}</button>
                </div>
              </form>
            </section>
          </section>
        </template>

        <section v-else class="planning-orders-empty">
          <h3>{{ tp("noOrderSelected") }}</h3>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import StatusBadge from "@/components/StatusBadge.vue";
import {
  createCustomerOrder,
  createOrderAttachment,
  createPlanningRecord,
  createPlanningRecordAttachment,
  getCustomerOrder,
  getOrderCommercialLink,
  getPlanningRecord,
  getPlanningRecordCommercialLink,
  linkOrderAttachment,
  linkPlanningRecordAttachment,
  listCustomerOrders,
  listOrderAttachments,
  listPlanningRecordAttachments,
  listPlanningRecords,
  setCustomerOrderReleaseState,
  setPlanningRecordReleaseState,
  updateCustomerOrder,
  updatePlanningRecord,
  type CustomerOrderRead,
  type PlanningCommercialLinkRead,
  type PlanningRecordRead,
  type PlanningDocumentRead,
} from "@/api/planningOrders";
import {
  derivePlanningOrderActionState,
  mapPlanningOrderApiMessage,
  planningModeLabel,
} from "@/features/planning/planningOrders.helpers.js";
import { planningOrdersMessages } from "@/i18n/planningOrders.messages";
import { useLocaleStore } from "@/stores/locale";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const localeStore = useLocaleStore();

const feedback = reactive({ tone: "neutral", title: "", message: "" });
const loading = reactive({ orders: false, orderDetail: false, planning: false, action: false });
const orderFilters = reactive({ search: "", customer_id: "", release_state: "", include_archived: false });
const tenantScopeInput = ref(authStore.tenantScopeId || authStore.sessionUser?.tenant_id || "");
const accessTokenInput = ref(authStore.accessToken || "");
const orders = ref<CustomerOrderRead[]>([]);
const planningRecords = ref<PlanningRecordRead[]>([]);
const orderAttachments = ref<PlanningDocumentRead[]>([]);
const planningAttachments = ref<PlanningDocumentRead[]>([]);
const selectedOrderId = ref("");
const selectedPlanningRecordId = ref("");
const selectedOrder = ref<CustomerOrderRead | null>(null);
const selectedPlanningRecord = ref<PlanningRecordRead | null>(null);
const selectedOrderCommercial = ref<PlanningCommercialLinkRead | null>(null);
const selectedPlanningCommercial = ref<PlanningCommercialLinkRead | null>(null);
const isCreatingOrder = ref(false);
const isCreatingPlanning = ref(false);

const orderDraft = reactive({
  customer_id: "",
  requirement_type_id: "",
  patrol_route_id: "",
  order_no: "",
  title: "",
  service_category_code: "",
  service_from: "",
  service_to: "",
  security_concept_text: "",
  notes: "",
  status: "active",
});

const planningDraft = reactive({
  dispatcher_user_id: "",
  parent_planning_record_id: "",
  planning_mode_code: "event",
  name: "",
  planning_from: "",
  planning_to: "",
  notes: "",
  status: "active",
  event_detail: { event_venue_id: "", setup_note: "" },
  site_detail: { site_id: "", watchbook_scope_note: "" },
  trade_fair_detail: { trade_fair_id: "", trade_fair_zone_id: "", stand_note: "" },
  patrol_detail: { patrol_route_id: "", execution_note: "" },
});

const orderAttachmentDraft = reactive({ title: "", label: "", file_name: "", content_type: "", content_base64: "" });
const planningAttachmentDraft = reactive({ title: "", label: "", file_name: "", content_type: "", content_base64: "" });
const orderAttachmentLink = reactive({ document_id: "", label: "" });
const planningAttachmentLink = reactive({ document_id: "", label: "" });

const tenantScopeId = computed(() => authStore.tenantScopeId || authStore.sessionUser?.tenant_id || "");
const accessToken = computed(() => authStore.accessToken);
const currentLocale = computed(() => (localeStore.locale === "en" ? "en" : "de"));
const effectiveRole = computed(() => authStore.effectiveRole);
const actionState = computed(() =>
  derivePlanningOrderActionState(effectiveRole.value, selectedOrder.value, selectedPlanningRecord.value),
);
const canReadAnything = computed(() => actionState.value.canReadOrders || actionState.value.canReadPlanning);

function tp(key: keyof typeof planningOrdersMessages.de) {
  return planningOrdersMessages[currentLocale.value][key] ?? planningOrdersMessages.de[key] ?? key;
}

function setFeedback(tone: string, title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearFeedback() {
  setFeedback("neutral", "", "");
}

function rememberScopeAndToken() {
  authStore.setTenantScopeId(tenantScopeInput.value.trim());
  authStore.accessToken = accessTokenInput.value.trim();
  if (typeof window !== "undefined") {
    window.localStorage.setItem("sicherplan-access-token", authStore.accessToken);
  }
  void refreshAll();
}

function resetOrderDraft() {
  Object.assign(orderDraft, {
    customer_id: "",
    requirement_type_id: "",
    patrol_route_id: "",
    order_no: "",
    title: "",
    service_category_code: "",
    service_from: "",
    service_to: "",
    security_concept_text: "",
    notes: "",
    status: "active",
  });
}

function resetPlanningDraft() {
  Object.assign(planningDraft, {
    dispatcher_user_id: "",
    parent_planning_record_id: "",
    planning_mode_code: "event",
    name: "",
    planning_from: "",
    planning_to: "",
    notes: "",
    status: "active",
    event_detail: { event_venue_id: "", setup_note: "" },
    site_detail: { site_id: "", watchbook_scope_note: "" },
    trade_fair_detail: { trade_fair_id: "", trade_fair_zone_id: "", stand_note: "" },
    patrol_detail: { patrol_route_id: "", execution_note: "" },
  });
}

function syncOrderDraft(order: CustomerOrderRead) {
  Object.assign(orderDraft, {
    customer_id: order.customer_id,
    requirement_type_id: order.requirement_type_id,
    patrol_route_id: order.patrol_route_id ?? "",
    order_no: order.order_no,
    title: order.title,
    service_category_code: order.service_category_code,
    service_from: order.service_from,
    service_to: order.service_to,
    security_concept_text: order.security_concept_text ?? "",
    notes: order.notes ?? "",
    status: order.status,
  });
}

function syncPlanningDraft(record: PlanningRecordRead) {
  resetPlanningDraft();
  Object.assign(planningDraft, {
    dispatcher_user_id: record.dispatcher_user_id ?? "",
    parent_planning_record_id: record.parent_planning_record_id ?? "",
    planning_mode_code: record.planning_mode_code,
    name: record.name,
    planning_from: record.planning_from,
    planning_to: record.planning_to,
    notes: record.notes ?? "",
    status: record.status,
    event_detail: {
      event_venue_id: record.event_detail?.event_venue_id ?? "",
      setup_note: record.event_detail?.setup_note ?? "",
    },
    site_detail: {
      site_id: record.site_detail?.site_id ?? "",
      watchbook_scope_note: record.site_detail?.watchbook_scope_note ?? "",
    },
    trade_fair_detail: {
      trade_fair_id: record.trade_fair_detail?.trade_fair_id ?? "",
      trade_fair_zone_id: record.trade_fair_detail?.trade_fair_zone_id ?? "",
      stand_note: record.trade_fair_detail?.stand_note ?? "",
    },
    patrol_detail: {
      patrol_route_id: record.patrol_detail?.patrol_route_id ?? "",
      execution_note: record.patrol_detail?.execution_note ?? "",
    },
  });
}

function buildOrderPayload(includeVersion = false) {
  const payload: Record<string, unknown> = {
    tenant_id: tenantScopeId.value,
    customer_id: orderDraft.customer_id,
    requirement_type_id: orderDraft.requirement_type_id,
    patrol_route_id: orderDraft.patrol_route_id || null,
    order_no: orderDraft.order_no,
    title: orderDraft.title,
    service_category_code: orderDraft.service_category_code,
    service_from: orderDraft.service_from,
    service_to: orderDraft.service_to,
    security_concept_text: orderDraft.security_concept_text || null,
    notes: orderDraft.notes || null,
    status: orderDraft.status || "active",
  };
  if (includeVersion && selectedOrder.value) {
    payload.version_no = selectedOrder.value.version_no;
  }
  return payload;
}

function buildPlanningPayload(includeVersion = false) {
  const payload: Record<string, unknown> = {
    tenant_id: tenantScopeId.value,
    order_id: selectedOrderId.value,
    dispatcher_user_id: planningDraft.dispatcher_user_id || null,
    parent_planning_record_id: planningDraft.parent_planning_record_id || null,
    planning_mode_code: planningDraft.planning_mode_code,
    name: planningDraft.name,
    planning_from: planningDraft.planning_from,
    planning_to: planningDraft.planning_to,
    notes: planningDraft.notes || null,
    status: planningDraft.status || "active",
  };
  if (planningDraft.planning_mode_code === "event") {
    payload.event_detail = {
      event_venue_id: planningDraft.event_detail.event_venue_id,
      setup_note: planningDraft.event_detail.setup_note || null,
    };
  } else if (planningDraft.planning_mode_code === "site") {
    payload.site_detail = {
      site_id: planningDraft.site_detail.site_id,
      watchbook_scope_note: planningDraft.site_detail.watchbook_scope_note || null,
    };
  } else if (planningDraft.planning_mode_code === "trade_fair") {
    payload.trade_fair_detail = {
      trade_fair_id: planningDraft.trade_fair_detail.trade_fair_id,
      trade_fair_zone_id: planningDraft.trade_fair_detail.trade_fair_zone_id || null,
      stand_note: planningDraft.trade_fair_detail.stand_note || null,
    };
  } else {
    payload.patrol_detail = {
      patrol_route_id: planningDraft.patrol_detail.patrol_route_id,
      execution_note: planningDraft.patrol_detail.execution_note || null,
    };
  }
  if (includeVersion && selectedPlanningRecord.value) {
    payload.version_no = selectedPlanningRecord.value.version_no;
  }
  return payload;
}

function planningModeText(modeCode: string) {
  const label = planningModeLabel(modeCode);
  switch (label) {
    case "event":
      return tp("modeEvent");
    case "site":
      return tp("modeSite");
    case "tradeFair":
      return tp("modeTradeFair");
    case "patrol":
      return tp("modePatrol");
    default:
      return modeCode;
  }
}

async function fileToBase64(file: File) {
  const bytes = await file.arrayBuffer();
  let binary = "";
  new Uint8Array(bytes).forEach((value) => {
    binary += String.fromCharCode(value);
  });
  return window.btoa(binary);
}

async function onOrderAttachmentSelected(event: Event) {
  const file = (event.target as HTMLInputElement)?.files?.[0];
  if (!file) return;
  orderAttachmentDraft.file_name = file.name;
  orderAttachmentDraft.content_type = file.type || "application/octet-stream";
  orderAttachmentDraft.content_base64 = await fileToBase64(file);
  if (!orderAttachmentDraft.title) orderAttachmentDraft.title = file.name;
}

async function onPlanningAttachmentSelected(event: Event) {
  const file = (event.target as HTMLInputElement)?.files?.[0];
  if (!file) return;
  planningAttachmentDraft.file_name = file.name;
  planningAttachmentDraft.content_type = file.type || "application/octet-stream";
  planningAttachmentDraft.content_base64 = await fileToBase64(file);
  if (!planningAttachmentDraft.title) planningAttachmentDraft.title = file.name;
}

async function refreshOrders() {
  if (!tenantScopeId.value || !accessToken.value || !actionState.value.canReadOrders) return;
  loading.orders = true;
  try {
    orders.value = await listCustomerOrders(tenantScopeId.value, accessToken.value, orderFilters);
  } catch (error) {
    handleError(error);
  } finally {
    loading.orders = false;
  }
}

async function selectOrder(orderId: string) {
  if (!tenantScopeId.value || !accessToken.value) return;
  loading.orderDetail = true;
  try {
    selectedOrderId.value = orderId;
    isCreatingOrder.value = false;
    selectedOrder.value = await getCustomerOrder(tenantScopeId.value, orderId, accessToken.value);
    syncOrderDraft(selectedOrder.value);
    orderAttachments.value = await listOrderAttachments(tenantScopeId.value, orderId, accessToken.value);
    selectedOrderCommercial.value = await getOrderCommercialLink(tenantScopeId.value, orderId, accessToken.value);
    await refreshPlanningRecords();
  } catch (error) {
    handleError(error);
  } finally {
    loading.orderDetail = false;
  }
}

function startCreateOrder() {
  isCreatingOrder.value = true;
  selectedOrder.value = null;
  selectedOrderId.value = "";
  planningRecords.value = [];
  selectedPlanningRecord.value = null;
  selectedPlanningRecordId.value = "";
  orderAttachments.value = [];
  planningAttachments.value = [];
  selectedOrderCommercial.value = null;
  selectedPlanningCommercial.value = null;
  resetOrderDraft();
}

async function submitOrder() {
  if (!tenantScopeId.value || !accessToken.value) return;
  loading.action = true;
  try {
    if (isCreatingOrder.value || !selectedOrderId.value) {
      const created = await createCustomerOrder(tenantScopeId.value, accessToken.value, buildOrderPayload());
      setFeedback("success", tp("successTitle"), tp("orderSaved"));
      isCreatingOrder.value = false;
      await refreshOrders();
      await selectOrder(created.id);
    } else {
      const updated = await updateCustomerOrder(
        tenantScopeId.value,
        selectedOrderId.value,
        accessToken.value,
        buildOrderPayload(true),
      );
      selectedOrder.value = updated;
      syncOrderDraft(updated);
      setFeedback("success", tp("successTitle"), tp("orderSaved"));
      await refreshOrders();
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function transitionOrder(releaseState: string) {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrder.value) return;
  loading.action = true;
  try {
      selectedOrder.value = await setCustomerOrderReleaseState(
        tenantScopeId.value,
        selectedOrder.value.id,
        accessToken.value,
        { release_state: releaseState, version_no: selectedOrder.value.version_no },
      );
      syncOrderDraft(selectedOrder.value);
      selectedOrderCommercial.value = await getOrderCommercialLink(
        tenantScopeId.value,
        selectedOrder.value.id,
        accessToken.value,
      );
      setFeedback("success", tp("successTitle"), tp("releaseChanged"));
    await refreshOrders();
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function submitOrderAttachment() {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrder.value) return;
  loading.action = true;
  try {
    await createOrderAttachment(tenantScopeId.value, selectedOrder.value.id, accessToken.value, {
      tenant_id: tenantScopeId.value,
      title: orderAttachmentDraft.title,
      file_name: orderAttachmentDraft.file_name,
      content_type: orderAttachmentDraft.content_type,
      content_base64: orderAttachmentDraft.content_base64,
      label: orderAttachmentDraft.label || null,
    });
    orderAttachments.value = await listOrderAttachments(tenantScopeId.value, selectedOrder.value.id, accessToken.value);
    Object.assign(orderAttachmentDraft, { title: "", label: "", file_name: "", content_type: "", content_base64: "" });
    setFeedback("success", tp("successTitle"), tp("documentUploaded"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function linkExistingOrderDocument() {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrder.value) return;
  loading.action = true;
  try {
    await linkOrderAttachment(tenantScopeId.value, selectedOrder.value.id, accessToken.value, {
      tenant_id: tenantScopeId.value,
      document_id: orderAttachmentLink.document_id,
      label: orderAttachmentLink.label || null,
    });
    orderAttachments.value = await listOrderAttachments(tenantScopeId.value, selectedOrder.value.id, accessToken.value);
    Object.assign(orderAttachmentLink, { document_id: "", label: "" });
    setFeedback("success", tp("successTitle"), tp("documentLinked"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function refreshPlanningRecords() {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrderId.value || !actionState.value.canReadPlanning) return;
  loading.planning = true;
  try {
    planningRecords.value = await listPlanningRecords(tenantScopeId.value, accessToken.value, { order_id: selectedOrderId.value });
    if (selectedPlanningRecordId.value) {
      const stillSelected = planningRecords.value.find((row) => row.id === selectedPlanningRecordId.value);
      if (!stillSelected) {
        selectedPlanningRecordId.value = "";
        selectedPlanningRecord.value = null;
        planningAttachments.value = [];
        selectedPlanningCommercial.value = null;
      }
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.planning = false;
  }
}

function startCreatePlanning() {
  isCreatingPlanning.value = true;
  selectedPlanningRecordId.value = "";
  selectedPlanningRecord.value = null;
  planningAttachments.value = [];
  selectedPlanningCommercial.value = null;
  resetPlanningDraft();
}

async function selectPlanningRecord(planningRecordId: string) {
  if (!tenantScopeId.value || !accessToken.value) return;
  loading.planning = true;
  try {
    selectedPlanningRecordId.value = planningRecordId;
    isCreatingPlanning.value = false;
    selectedPlanningRecord.value = await getPlanningRecord(tenantScopeId.value, planningRecordId, accessToken.value);
    syncPlanningDraft(selectedPlanningRecord.value);
    planningAttachments.value = await listPlanningRecordAttachments(tenantScopeId.value, planningRecordId, accessToken.value);
    selectedPlanningCommercial.value = await getPlanningRecordCommercialLink(
      tenantScopeId.value,
      planningRecordId,
      accessToken.value,
    );
  } catch (error) {
    handleError(error);
  } finally {
    loading.planning = false;
  }
}

async function submitPlanningRecord() {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrderId.value) return;
  loading.action = true;
  try {
    if (isCreatingPlanning.value || !selectedPlanningRecordId.value) {
      const created = await createPlanningRecord(tenantScopeId.value, accessToken.value, buildPlanningPayload());
      setFeedback("success", tp("successTitle"), tp("planningSaved"));
      isCreatingPlanning.value = false;
      await refreshPlanningRecords();
      await selectPlanningRecord(created.id);
    } else {
      const updated = await updatePlanningRecord(
        tenantScopeId.value,
        selectedPlanningRecordId.value,
        accessToken.value,
        buildPlanningPayload(true),
      );
      selectedPlanningRecord.value = updated;
      syncPlanningDraft(updated);
      setFeedback("success", tp("successTitle"), tp("planningSaved"));
      await refreshPlanningRecords();
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function transitionPlanning(releaseState: string) {
  if (!tenantScopeId.value || !accessToken.value || !selectedPlanningRecord.value) return;
  loading.action = true;
  try {
      selectedPlanningRecord.value = await setPlanningRecordReleaseState(
        tenantScopeId.value,
        selectedPlanningRecord.value.id,
        accessToken.value,
        { release_state: releaseState, version_no: selectedPlanningRecord.value.version_no },
      );
      syncPlanningDraft(selectedPlanningRecord.value);
      selectedPlanningCommercial.value = await getPlanningRecordCommercialLink(
        tenantScopeId.value,
        selectedPlanningRecord.value.id,
        accessToken.value,
      );
      setFeedback("success", tp("successTitle"), tp("releaseChanged"));
    await refreshPlanningRecords();
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function submitPlanningAttachment() {
  if (!tenantScopeId.value || !accessToken.value || !selectedPlanningRecord.value) return;
  loading.action = true;
  try {
    await createPlanningRecordAttachment(tenantScopeId.value, selectedPlanningRecord.value.id, accessToken.value, {
      tenant_id: tenantScopeId.value,
      title: planningAttachmentDraft.title,
      file_name: planningAttachmentDraft.file_name,
      content_type: planningAttachmentDraft.content_type,
      content_base64: planningAttachmentDraft.content_base64,
      label: planningAttachmentDraft.label || null,
    });
    planningAttachments.value = await listPlanningRecordAttachments(tenantScopeId.value, selectedPlanningRecord.value.id, accessToken.value);
    Object.assign(planningAttachmentDraft, { title: "", label: "", file_name: "", content_type: "", content_base64: "" });
    setFeedback("success", tp("successTitle"), tp("documentUploaded"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function linkExistingPlanningDocument() {
  if (!tenantScopeId.value || !accessToken.value || !selectedPlanningRecord.value) return;
  loading.action = true;
  try {
    await linkPlanningRecordAttachment(tenantScopeId.value, selectedPlanningRecord.value.id, accessToken.value, {
      tenant_id: tenantScopeId.value,
      document_id: planningAttachmentLink.document_id,
      label: planningAttachmentLink.label || null,
    });
    planningAttachments.value = await listPlanningRecordAttachments(tenantScopeId.value, selectedPlanningRecord.value.id, accessToken.value);
    Object.assign(planningAttachmentLink, { document_id: "", label: "" });
    setFeedback("success", tp("successTitle"), tp("documentLinked"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

function handleError(error: unknown) {
  const messageKey = typeof error === "object" && error && "messageKey" in error ? String(error.messageKey) : "errors.platform.internal";
  setFeedback("error", tp("errorTitle"), tp(mapPlanningOrderApiMessage(messageKey) as keyof typeof planningOrdersMessages.de));
}

async function refreshAll() {
  await refreshOrders();
  if (selectedOrderId.value) {
    await selectOrder(selectedOrderId.value);
  }
}
</script>

<style scoped>
.planning-orders-page,
.planning-orders-grid {
  display: grid;
  gap: 1rem;
}

.planning-orders-hero,
.planning-orders-grid {
  grid-template-columns: 1.2fr 0.8fr;
}

.planning-orders-meta,
.cta-row,
.planning-orders-doc-list,
.planning-orders-list,
.planning-orders-section,
.planning-orders-page {
  display: grid;
  gap: 0.75rem;
}

.planning-orders-meta {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.planning-orders-meta__pill,
.planning-orders-row,
.planning-orders-doc-row {
  border: 1px solid var(--vp-c-divider, #d8e0e0);
  border-radius: 14px;
  padding: 0.8rem 1rem;
}

.planning-orders-row {
  align-items: center;
  background: transparent;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  text-align: left;
}

.planning-orders-row.selected {
  border-color: rgb(40 170 170 / 70%);
  box-shadow: 0 0 0 1px rgb(40 170 170 / 30%);
}

.planning-orders-form,
.planning-orders-panel,
.planning-orders-scope,
.planning-orders-empty,
.planning-orders-feedback {
  display: grid;
  gap: 1rem;
}

.planning-orders-form-grid {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-stack {
  display: grid;
  gap: 0.42rem;
  font-size: 0.9rem;
  min-width: 0;
}

.field-stack--wide {
  grid-column: 1 / -1;
}

.field-stack input,
.field-stack select,
.field-stack textarea {
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

.field-stack textarea {
  min-height: 6.5rem;
  resize: vertical;
}

.field-stack input:focus,
.field-stack select:focus,
.field-stack textarea:focus {
  outline: none;
  border-color: rgb(40 170 170 / 55%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

.field-stack input:disabled,
.field-stack select:disabled,
.field-stack textarea:disabled {
  opacity: 0.72;
  cursor: not-allowed;
}

.planning-orders-detail {
  align-content: start;
}

.planning-orders-panel__header {
  align-items: start;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.planning-orders-feedback[data-tone="error"] {
  border-left: 4px solid #c0392b;
}

.planning-orders-feedback[data-tone="success"] {
  border-left: 4px solid rgb(40 170 170);
}

.planning-orders-checkbox {
  align-items: center;
  display: flex;
  gap: 0.5rem;
  min-width: 0;
  color: var(--sp-color-text-secondary);
}

.planning-orders-checkbox input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--sp-color-primary);
}

.planning-orders-lead,
.field-help,
.planning-orders-list-empty {
  opacity: 0.8;
}

.planning-orders-subsection {
  border-top: 1px solid var(--vp-c-divider, #d8e0e0);
  padding-top: 1rem;
}

.planning-orders-issues {
  margin: 0;
  padding-left: 1.2rem;
}

.planning-orders-state--good {
  color: rgb(24 128 96);
}

.planning-orders-state--bad {
  color: rgb(176 48 48);
}

.planning-orders-state--warn {
  color: rgb(156 104 16);
}

@media (max-width: 1024px) {
  .planning-orders-hero,
  .planning-orders-grid,
  .planning-orders-form-grid,
  .planning-orders-meta {
    grid-template-columns: 1fr;
  }
}
</style>
