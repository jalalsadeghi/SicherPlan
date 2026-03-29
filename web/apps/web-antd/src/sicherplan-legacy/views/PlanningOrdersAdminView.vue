<template>
  <section class="planning-orders-page">
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

    <div v-else class="planning-orders-grid" data-testid="planning-orders-master-detail-layout">
      <section
        class="module-card planning-orders-panel planning-orders-list-panel"
        data-testid="planning-orders-list-section"
      >
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
          <PlanningCustomerSelect
            v-model="orderFilters.customer_id"
            :label="tp('filtersCustomerId')"
            :options="customerOptions"
            :loading="customerLookupLoading"
            :disabled="!tenantScopeId || !accessToken"
            :error="customerLookupError"
            :search-placeholder="tp('customerSearchPlaceholder')"
            :empty-option-label="tp('filtersCustomerId')"
            :loading-text="tp('customerLoading')"
            :empty-text="tp('customerEmpty')"
            :no-match-text="tp('customerNoMatch')"
          />
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
              <span>{{ formatOrderCustomerLabel(order.customer_id) }}</span>
            </div>
            <StatusBadge :status="order.release_state" />
          </button>
        </div>
        <p v-else class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
      </section>

      <section
        class="module-card planning-orders-panel planning-orders-detail"
        data-testid="planning-orders-detail-workspace"
      >
        <div class="planning-orders-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <h3>{{ selectedOrder ? `${selectedOrder.order_no} · ${selectedOrder.title}` : tp("noOrderSelected") }}</h3>
            <p v-if="isCreatingOrder || selectedOrder" class="field-help">{{ tp("lead") }}</p>
          </div>
          <div class="planning-orders-header-actions">
            <button
              v-if="showPlanningSetupCta"
              class="cta-button cta-secondary"
              type="button"
              @click="openPlanningSetup(missingSetupEntity)"
            >
              {{ tp("actionsOpenPlanningSetup") }}
            </button>
            <StatusBadge v-if="selectedOrder" :status="selectedOrder.release_state" />
          </div>
        </div>

        <template v-if="isCreatingOrder || selectedOrder">
          <nav
            v-if="orderDetailTabs.length"
            class="planning-orders-tabs"
            aria-label="Planning order detail sections"
            data-testid="planning-orders-detail-tabs"
          >
            <button
              v-for="tab in orderDetailTabs"
              :key="tab.id"
              type="button"
              class="planning-orders-tab"
              :class="{ active: tab.id === activeDetailTab }"
              :data-testid="`planning-orders-tab-${tab.id}`"
              @click="activeDetailTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </nav>

          <section v-show="activeDetailTab === 'overview'" class="planning-orders-tab-panel" data-testid="planning-orders-tab-panel-overview">
            <form class="planning-orders-form" @submit.prevent="submitOrder">
              <div class="planning-orders-form-grid">
                <PlanningCustomerSelect
                  v-model="orderDraft.customer_id"
                  :label="tp('fieldsCustomer')"
                  :options="customerOptions"
                  :loading="customerLookupLoading"
                  :disabled="loading.action"
                  :invalid="customerFieldInvalid"
                  :error="customerLookupError"
                  :search-placeholder="tp('customerSearchPlaceholder')"
                  :empty-option-label="tp('filtersCustomerId')"
                  :loading-text="tp('customerLoading')"
                  :empty-text="tp('customerEmpty')"
                  :no-match-text="tp('customerNoMatch')"
                />
                <label class="field-stack"><span>{{ tp("fieldsOrderNo") }}</span><input v-model="orderDraft.order_no" required /></label>
                <label class="field-stack">
                  <div class="planning-orders-field-header">
                    <span>{{ tp("fieldsRequirementType") }}</span>
                    <button
                      class="cta-button cta-secondary planning-orders-field-action"
                      type="button"
                      :disabled="!!setupActionDisabledReason() || loading.action"
                      :title="setupActionDisabledReason()"
                      @click="openRequirementTypeModal"
                    >
                      {{ tp("actionsAddRequirementType") }}
                    </button>
                  </div>
                  <Select
                    :value="orderDraft.requirement_type_id || undefined"
                    show-search
                    class="planning-admin-select"
                    popup-class-name="planning-admin-select-dropdown"
                    :options="requirementTypeSelectOptions"
                    :loading="requirementTypeLookupLoading"
                    :disabled="loading.action || !orderDraft.customer_id"
                    :filter-option="filterSelectOption"
                    :placeholder="requirementTypePlaceholder"
                    :status="requirementTypeLookupError || requirementTypeFieldInvalid ? 'error' : undefined"
                    @change="handleRequirementTypeChange"
                  />
                  <p v-if="requirementTypeLookupLoading" class="field-help">{{ tp("requirementTypeLoading") }}</p>
                  <p v-else-if="requirementTypeLookupError" class="field-help">{{ requirementTypeLookupError }}</p>
                  <p v-else-if="requirementTypeSetupMissing" class="field-help">
                    {{ tp("requirementTypeSetupMissing") }}
                    <button class="planning-orders-inline-link" type="button" @click="openPlanningSetup('requirement_type')">
                      {{ tp("actionsOpenPlanningSetup") }}
                    </button>
                  </p>
                  <p v-else-if="requirementTypeFieldInvalid" class="field-help">{{ tp("requirementTypeRequired") }}</p>
                </label>
                <label class="field-stack">
                  <div class="planning-orders-field-header">
                    <span>{{ tp("fieldsPatrolRoute") }}</span>
                    <button
                      class="cta-button cta-secondary planning-orders-field-action"
                      type="button"
                      :disabled="!!setupActionDisabledReason() || loading.action"
                      :title="setupActionDisabledReason()"
                      @click="openPatrolRouteModal"
                    >
                      {{ tp("actionsAddPatrolRoute") }}
                    </button>
                  </div>
                  <Select
                    :value="orderDraft.patrol_route_id || undefined"
                    show-search
                    allow-clear
                    class="planning-admin-select"
                    popup-class-name="planning-admin-select-dropdown"
                    :options="patrolRouteSelectOptions"
                    :loading="patrolRouteLookupLoading"
                    :disabled="loading.action || !orderDraft.customer_id"
                    :filter-option="filterSelectOption"
                    :placeholder="patrolRoutePlaceholder"
                    :status="patrolRouteLookupError ? 'error' : undefined"
                    @change="handlePatrolRouteChange"
                    @clear="handlePatrolRouteClear"
                  />
                  <p v-if="patrolRouteLookupLoading" class="field-help">{{ tp("patrolRouteLoading") }}</p>
                  <p v-else-if="patrolRouteLookupError" class="field-help">{{ patrolRouteLookupError }}</p>
                  <p v-else-if="patrolRouteSetupMissing" class="field-help">
                    {{ tp("patrolRouteSetupMissing") }}
                    <button class="planning-orders-inline-link" type="button" @click="openPlanningSetup('patrol_route')">
                      {{ tp("actionsOpenPlanningSetup") }}
                    </button>
                  </p>
                </label>
                <label class="field-stack"><span>{{ tp("fieldsTitle") }}</span><input v-model="orderDraft.title" required /></label>
                <label class="field-stack">
                  <span>{{ tp("fieldsServiceCategory") }}</span>
                  <input v-model="orderDraft.service_category_code" required />
                  <p class="field-help">{{ tp("serviceCategoryManualHelp") }}</p>
                </label>
                <div class="planning-orders-form-row planning-orders-form-row--triple">
                  <label class="field-stack"><span>{{ tp("fieldsServiceFrom") }}</span><input v-model="orderDraft.service_from" type="date" :max="orderDraft.service_to || undefined" required /></label>
                  <label class="field-stack"><span>{{ tp("fieldsServiceTo") }}</span><input v-model="orderDraft.service_to" type="date" :min="orderDraft.service_from || undefined" required /></label>
                  <label class="field-stack">
                    <span>{{ tp("fieldsReleaseState") }}</span>
                    <select v-model="orderDraft.release_state" :disabled="!isCreatingOrder">
                      <option v-for="option in orderReleaseStateOptions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                    <p v-if="!isCreatingOrder" class="field-help">{{ tp("releaseStateManagedSeparately") }}</p>
                  </label>
                </div>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsSecurityConcept") }}</span><textarea v-model="orderDraft.security_concept_text" rows="3" /></label>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="orderDraft.notes" rows="3" /></label>
              </div>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canWriteOrders">{{ tp("actionsSave") }}</button>
                <button class="cta-button cta-secondary" type="button" @click="resetOrderDraft">{{ tp("actionsReset") }}</button>
              </div>
            </form>
          </section>

          <section
            v-if="selectedOrder"
            v-show="activeDetailTab === 'commercial'"
            class="planning-orders-tab-panel planning-orders-section"
            data-testid="planning-orders-tab-panel-commercial"
          >
            <div class="planning-orders-panel__header"><h3>{{ tp("sectionCommercial") }}</h3></div>
            <div class="planning-orders-commercial-summary">
              <p
                class="planning-orders-commercial-summary__headline"
                :class="selectedOrderCommercial?.is_release_ready ? 'planning-orders-state--good' : orderCommercialBlockingIssues.length ? 'planning-orders-state--bad' : 'planning-orders-state--warn'"
              >
                {{ tp(commercialSummaryKey) }}
              </p>
              <p class="field-help">
                {{ tpf(commercialContextKey, { customerLabel: commercialCustomerLabel }) }}
              </p>
              <p class="field-help">
                {{
                  selectedOrderCustomerLabel
                    ? tpf("commercialFixHint", { customerLabel: selectedOrderCustomerLabel })
                    : tp("commercialFixHintFallback")
                }}
              </p>
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="button" @click="openCustomerCommercialSettings">
                  {{ tp("commercialActionOpenCustomerCommercial") }}
                </button>
              </div>
            </div>
            <div v-if="orderCommercialBlockingIssues.length" class="planning-orders-commercial-block">
              <strong>{{ tp("commercialBlockingListTitle") }}</strong>
              <ul class="planning-orders-issues planning-orders-issues--blocking">
                <li v-for="issue in orderCommercialBlockingIssues" :key="issue.code">
                  {{ resolveCommercialIssueMessage(issue.code) }}
                </li>
              </ul>
            </div>
            <div v-if="orderCommercialWarningIssues.length" class="planning-orders-commercial-block">
              <strong class="planning-orders-state--warn">{{ tp("commercialWarningsListTitle") }}</strong>
              <ul class="planning-orders-issues planning-orders-issues--warning">
                <li v-for="issue in orderCommercialWarningIssues" :key="issue.code">
                  {{ resolveCommercialIssueMessage(issue.code) }}
                </li>
              </ul>
            </div>
          </section>

          <section
            v-if="selectedOrder"
            v-show="activeDetailTab === 'release'"
            class="planning-orders-tab-panel planning-orders-section"
            data-testid="planning-orders-tab-panel-release"
          >
            <div class="planning-orders-panel__header"><h3>{{ tp("sectionOrderRelease") }}</h3></div>
            <div class="cta-row">
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionOrder" @click="transitionOrder('draft')">{{ tp("actionsBackToDraft") }}</button>
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionOrder" @click="transitionOrder('release_ready')">{{ tp("actionsReleaseReady") }}</button>
              <button class="cta-button" type="button" :disabled="!actionState.canTransitionOrder" @click="transitionOrder('released')">{{ tp("actionsReleased") }}</button>
            </div>
          </section>

          <section
            v-if="selectedOrder"
            v-show="activeDetailTab === 'documents'"
            class="planning-orders-tab-panel planning-orders-section"
            data-testid="planning-orders-tab-panel-documents"
          >
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

          <section
            v-if="selectedOrder"
            v-show="activeDetailTab === 'planning_records'"
            class="planning-orders-tab-panel planning-orders-section"
            data-testid="planning-orders-tab-panel-planning-records"
          >
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

    <Modal
      v-model:open="requirementTypeModal.open"
      :confirm-loading="requirementTypeModal.saving"
      :title="tp('requirementTypeModalTitle')"
      @ok="submitRequirementTypeModal"
      @cancel="resetRequirementTypeModal"
    >
      <div class="planning-orders-modal-form">
        <p class="field-help">{{ tp("requirementTypeModalLead") }}</p>
        <label class="field-stack">
          <span>{{ tp("fieldsCustomer") }}</span>
          <input :value="formatOrderCustomerLabel(orderDraft.customer_id)" readonly />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsCode") }}</span>
          <input v-model="requirementTypeModal.code" />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsLabelGeneric") }}</span>
          <input v-model="requirementTypeModal.label" />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsDefaultPlanningMode") }}</span>
          <select v-model="requirementTypeModal.default_planning_mode_code">
            <option v-for="option in planningModeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsDescription") }}</span>
          <textarea v-model="requirementTypeModal.description" rows="3" />
        </label>
      </div>
    </Modal>

    <Modal
      v-model:open="patrolRouteModal.open"
      :confirm-loading="patrolRouteModal.saving"
      :title="tp('patrolRouteModalTitle')"
      @ok="submitPatrolRouteModal"
      @cancel="resetPatrolRouteModal"
    >
      <div class="planning-orders-modal-form">
        <p class="field-help">{{ tp("patrolRouteModalLead") }}</p>
        <label class="field-stack">
          <span>{{ tp("fieldsCustomer") }}</span>
          <input :value="formatOrderCustomerLabel(orderDraft.customer_id)" readonly />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsRouteNo") }}</span>
          <input v-model="patrolRouteModal.route_no" />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsNameGeneric") }}</span>
          <input v-model="patrolRouteModal.name" />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsStartPointText") }}</span>
          <input v-model="patrolRouteModal.start_point_text" />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsEndPointText") }}</span>
          <input v-model="patrolRouteModal.end_point_text" />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsTravelPolicyCode") }}</span>
          <input v-model="patrolRouteModal.travel_policy_code" />
        </label>
        <label class="field-stack">
          <span>{{ tp("fieldsNotes") }}</span>
          <textarea v-model="patrolRouteModal.notes" rows="3" />
        </label>
      </div>
    </Modal>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";

import { Modal, Select } from "ant-design-vue";
import { useRouter } from "vue-router";

import StatusBadge from "@/components/StatusBadge.vue";
import PlanningCustomerSelect from "@/components/planning/PlanningCustomerSelect.vue";
import { listCustomers, type CustomerListItem } from "@/api/customers";
import {
  createPlanningRecord as createPlanningCatalogRecord,
  listPlanningRecords as listPlanningCatalogRecords,
  type PlanningListItem,
} from "@/api/planningAdmin";
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
  type CustomerOrderListItem,
  type CustomerOrderRead,
  type PlanningCommercialLinkRead,
  type PlanningRecordListItem,
  type PlanningRecordRead,
  type PlanningDocumentRead,
} from "@/api/planningOrders";
import {
  buildCustomerCommercialLocation,
  buildPlanningSetupLocation,
  derivePlanningOrderActionState,
  derivePlanningOrderSubmitBlockReason,
  filterPlanningOrderOptionsByCustomer,
  formatPlanningCommercialIssueFallback,
  formatPlanningOrderReferenceOption,
  hasPlanningOrderSetupGap,
  mapPlanningCommercialIssueCode,
  mapPlanningOrderApiMessage,
  normalizePlanningOrderUuidValue,
  planningModeLabel,
  validatePlanningOrderDraft,
} from "@/features/planning/planningOrders.helpers.js";
import { formatPlanningCustomerOption, hasPlanningPermission } from "@/features/planning/planningAdmin.helpers.js";
import { planningOrdersMessages } from "@/i18n/planningOrders.messages";
import { useLocaleStore } from "@/stores/locale";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const localeStore = useLocaleStore();
const router = useRouter();

const feedback = reactive({ tone: "neutral", title: "", message: "" });
const loading = reactive({ orders: false, orderDetail: false, planning: false, action: false });
const orderFilters = reactive({ search: "", customer_id: "", release_state: "", include_archived: false });
const customerOptions = ref<CustomerListItem[]>([]);
const customerLookupLoading = ref(false);
const customerLookupError = ref("");
const requirementTypeOptions = ref<PlanningListItem[]>([]);
const requirementTypeLookupLoading = ref(false);
const requirementTypeLookupError = ref("");
const patrolRouteOptions = ref<PlanningListItem[]>([]);
const patrolRouteLookupLoading = ref(false);
const patrolRouteLookupError = ref("");
const orderValidationState = reactive({ attempted: false });
const requirementTypeModal = reactive({
  open: false,
  saving: false,
  code: "",
  label: "",
  default_planning_mode_code: "site",
  description: "",
});
const patrolRouteModal = reactive({
  open: false,
  saving: false,
  route_no: "",
  name: "",
  start_point_text: "",
  end_point_text: "",
  travel_policy_code: "",
  notes: "",
});
const orders = ref<CustomerOrderListItem[]>([]);
const planningRecords = ref<PlanningRecordListItem[]>([]);
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
const activeDetailTab = ref("overview");

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
  release_state: "draft",
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
const canWritePlanningSetup = computed(() => hasPlanningPermission(effectiveRole.value, "planning.ops.write"));
const canReadAnything = computed(() => actionState.value.canReadOrders || actionState.value.canReadPlanning);
const planningModeOptions = computed(() => [
  { label: tp("modeEvent"), value: "event" },
  { label: tp("modeSite"), value: "site" },
  { label: tp("modeTradeFair"), value: "trade_fair" },
  { label: tp("modePatrol"), value: "patrol" },
]);
const orderReleaseStateOptions = computed(() => [
  { label: tp("statusDraft"), value: "draft" },
  { label: tp("statusReleaseReady"), value: "release_ready" },
  { label: tp("statusReleased"), value: "released" },
]);
const requirementTypeSelectOptions = computed(() =>
  filterPlanningOrderOptionsByCustomer(requirementTypeOptions.value, orderDraft.customer_id).map((row) => ({
    label: formatPlanningOrderReferenceOption("requirement_type", row),
    value: row.id,
  })),
);
const patrolRouteSelectOptions = computed(() =>
  filterPlanningOrderOptionsByCustomer(patrolRouteOptions.value, orderDraft.customer_id).map((row) => ({
    label: formatPlanningOrderReferenceOption("patrol_route", row),
    value: row.id,
  })),
);
const requirementTypePlaceholder = computed(() => {
  if (!orderDraft.customer_id) {
    return tp("requirementTypeCustomerRequired");
  }
  if (!requirementTypeLookupLoading.value && !requirementTypeLookupError.value && !requirementTypeSelectOptions.value.length) {
    return tp("requirementTypeEmpty");
  }
  return tp("requirementTypeSearchPlaceholder");
});
const patrolRoutePlaceholder = computed(() => {
  if (!orderDraft.customer_id) {
    return tp("patrolRouteCustomerRequired");
  }
  if (!patrolRouteLookupLoading.value && !patrolRouteLookupError.value && !patrolRouteSelectOptions.value.length) {
    return tp("patrolRouteEmpty");
  }
  return tp("patrolRouteSearchPlaceholder");
});
const requirementTypeSetupMissing = computed(() =>
  hasPlanningOrderSetupGap({
    customerId: orderDraft.customer_id,
    options: requirementTypeSelectOptions.value,
    loading: requirementTypeLookupLoading.value,
    error: requirementTypeLookupError.value,
  }),
);
const patrolRouteSetupMissing = computed(() =>
  hasPlanningOrderSetupGap({
    customerId: orderDraft.customer_id,
    options: patrolRouteSelectOptions.value,
    loading: patrolRouteLookupLoading.value,
    error: patrolRouteLookupError.value,
  }),
);
const missingSetupEntity = computed(() => {
  if (requirementTypeSetupMissing.value) {
    return "requirement_type";
  }
  if (patrolRouteSetupMissing.value) {
    return "patrol_route";
  }
  return "";
});
const showPlanningSetupCta = computed(() => Boolean(missingSetupEntity.value));
const orderHasSavedRecord = computed(() => Boolean(selectedOrder.value && !isCreatingOrder.value));
const orderDetailTabs = computed(() => {
  const tabs = [{ id: "overview", label: tp("tabOverview") }];
  if (!orderHasSavedRecord.value) {
    return tabs;
  }
  return [
    ...tabs,
    { id: "commercial", label: tp("tabCommercial") },
    { id: "release", label: tp("tabRelease") },
    { id: "documents", label: tp("tabDocuments") },
    { id: "planning_records", label: tp("tabPlanningRecords") },
  ];
});
const orderValidationErrors = computed(() => validatePlanningOrderDraft(orderDraft));
const customerFieldInvalid = computed(() => orderValidationState.attempted && orderValidationErrors.value.customer_id);
const requirementTypeFieldInvalid = computed(
  () => orderValidationState.attempted && orderValidationErrors.value.requirement_type_id,
);
const selectedOrderCustomerLabel = computed(() => {
  const customerId = selectedOrder.value?.customer_id || orderDraft.customer_id;
  const matchedCustomer = customerOptions.value.find((row) => row.id === customerId);
  if (matchedCustomer) {
    return formatPlanningCustomerOption(matchedCustomer);
  }
  return customerId || "";
});
const commercialCustomerLabel = computed(
  () => selectedOrderCustomerLabel.value || tp("commercialContextFallbackCustomer"),
);
const orderCommercialBlockingIssues = computed(
  () => selectedOrderCommercial.value?.blocking_issues ?? [],
);
const orderCommercialWarningIssues = computed(
  () => selectedOrderCommercial.value?.warning_issues ?? [],
);
const commercialSummaryKey = computed(() => {
  if (selectedOrderCommercial.value?.is_release_ready) {
    return "commercialSummaryReady";
  }
  if (orderCommercialBlockingIssues.value.length) {
    return "commercialSummaryBlocked";
  }
  if (orderCommercialWarningIssues.value.length) {
    return "commercialSummaryWarnings";
  }
  return "commercialSummaryBlocked";
});
const commercialContextKey = computed(() => {
  if (selectedOrderCommercial.value?.is_release_ready) {
    return "commercialContextReady";
  }
  if (orderCommercialBlockingIssues.value.length) {
    return "commercialContextBlocked";
  }
  return "commercialContextWarnings";
});

function tp(key: keyof typeof planningOrdersMessages.de) {
  return planningOrdersMessages[currentLocale.value][key] ?? planningOrdersMessages.de[key] ?? key;
}

function formatMessage(message: string, values: Record<string, string>) {
  return Object.entries(values).reduce(
    (resolved, [token, value]) => resolved.replaceAll(`{${token}}`, value),
    message,
  );
}

function tpf(key: keyof typeof planningOrdersMessages.de, values: Record<string, string>) {
  return formatMessage(tp(key), values);
}

function setFeedback(tone: string, title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearFeedback() {
  setFeedback("neutral", "", "");
}

function resetRequirementTypeModal() {
  Object.assign(requirementTypeModal, {
    open: false,
    saving: false,
    code: "",
    label: "",
    default_planning_mode_code: "site",
    description: "",
  });
}

function resetPatrolRouteModal() {
  Object.assign(patrolRouteModal, {
    open: false,
    saving: false,
    route_no: "",
    name: "",
    start_point_text: "",
    end_point_text: "",
    travel_policy_code: "",
    notes: "",
  });
}

function resetOrderDraft() {
  orderValidationState.attempted = false;
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
    release_state: "draft",
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
  orderValidationState.attempted = false;
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
    release_state: order.release_state,
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
  const customerId = normalizePlanningOrderUuidValue(orderDraft.customer_id);
  const requirementTypeId = normalizePlanningOrderUuidValue(orderDraft.requirement_type_id);
  const patrolRouteId = normalizePlanningOrderUuidValue(orderDraft.patrol_route_id);
  const payload: Record<string, unknown> = {
    tenant_id: tenantScopeId.value,
    customer_id: customerId,
    requirement_type_id: requirementTypeId,
    patrol_route_id: patrolRouteId,
    order_no: orderDraft.order_no,
    title: orderDraft.title,
    service_category_code: orderDraft.service_category_code,
    service_from: orderDraft.service_from,
    service_to: orderDraft.service_to,
    security_concept_text: orderDraft.security_concept_text || null,
    notes: orderDraft.notes || null,
  };
  if (!includeVersion) {
    payload.release_state = orderDraft.release_state || "draft";
  }
  if (includeVersion && selectedOrder.value) {
    payload.version_no = selectedOrder.value.version_no;
  }
  return payload;
}

function validateOrderDraftSelection() {
  orderValidationState.attempted = true;
  const messageKey = derivePlanningOrderSubmitBlockReason(orderDraft, {
    requirementTypeSetupMissing: requirementTypeSetupMissing.value,
  });
  if (!messageKey) {
    return true;
  }
  setFeedback("error", tp("errorTitle"), tp(messageKey));
  return false;
}

function setupActionDisabledReason() {
  if (!orderDraft.customer_id) {
    return tp("setupActionCustomerRequired");
  }
  if (!canWritePlanningSetup.value) {
    return tp("setupActionPermissionRequired");
  }
  return "";
}

async function openPlanningSetup(entityKey: string) {
  if (!entityKey) {
    return;
  }
  await router.push(buildPlanningSetupLocation(entityKey, orderDraft.customer_id));
}

async function openCustomerCommercialSettings() {
  await router.push(
    buildCustomerCommercialLocation(selectedOrder.value?.customer_id || orderDraft.customer_id),
  );
}

function openRequirementTypeModal() {
  if (setupActionDisabledReason()) {
    return;
  }
  requirementTypeModal.open = true;
}

function openPatrolRouteModal() {
  if (setupActionDisabledReason()) {
    return;
  }
  patrolRouteModal.open = true;
}

async function submitRequirementTypeModal() {
  if (!tenantScopeId.value || !accessToken.value || !orderDraft.customer_id) {
    return;
  }
  if (!requirementTypeModal.code.trim() || !requirementTypeModal.label.trim() || !requirementTypeModal.default_planning_mode_code) {
    setFeedback("error", tp("errorTitle"), tp("requirementTypeModalInvalid"));
    return;
  }
  requirementTypeModal.saving = true;
  try {
    const created = await createPlanningCatalogRecord("requirement_type", tenantScopeId.value, accessToken.value, {
      tenant_id: tenantScopeId.value,
      customer_id: orderDraft.customer_id,
      code: requirementTypeModal.code.trim(),
      label: requirementTypeModal.label.trim(),
      default_planning_mode_code: requirementTypeModal.default_planning_mode_code,
      description: requirementTypeModal.description.trim() || null,
    });
    await refreshOrderReferenceOptions(orderDraft.customer_id);
    orderDraft.requirement_type_id = created.id;
    resetRequirementTypeModal();
    setFeedback("success", tp("successTitle"), tp("requirementTypeCreated"));
  } catch (error) {
    handleError(error);
  } finally {
    requirementTypeModal.saving = false;
  }
}

async function submitPatrolRouteModal() {
  if (!tenantScopeId.value || !accessToken.value || !orderDraft.customer_id) {
    return;
  }
  if (!patrolRouteModal.route_no.trim() || !patrolRouteModal.name.trim()) {
    setFeedback("error", tp("errorTitle"), tp("patrolRouteModalInvalid"));
    return;
  }
  patrolRouteModal.saving = true;
  try {
    const created = await createPlanningCatalogRecord("patrol_route", tenantScopeId.value, accessToken.value, {
      tenant_id: tenantScopeId.value,
      customer_id: orderDraft.customer_id,
      route_no: patrolRouteModal.route_no.trim(),
      name: patrolRouteModal.name.trim(),
      start_point_text: patrolRouteModal.start_point_text.trim() || null,
      end_point_text: patrolRouteModal.end_point_text.trim() || null,
      travel_policy_code: patrolRouteModal.travel_policy_code.trim() || null,
      notes: patrolRouteModal.notes.trim() || null,
    });
    await refreshOrderReferenceOptions(orderDraft.customer_id);
    orderDraft.patrol_route_id = created.id;
    resetPatrolRouteModal();
    setFeedback("success", tp("successTitle"), tp("patrolRouteCreated"));
  } catch (error) {
    handleError(error);
  } finally {
    patrolRouteModal.saving = false;
  }
}

function filterSelectOption(input: string, option: { label?: unknown } | undefined) {
  if (!input) {
    return true;
  }
  const label = typeof option?.label === "string" ? option.label : "";
  return label.toLowerCase().includes(input.toLowerCase());
}

function handleRequirementTypeChange(value: string | number | undefined) {
  orderDraft.requirement_type_id = typeof value === "string" ? value : "";
}

function handlePatrolRouteChange(value: string | number | undefined) {
  orderDraft.patrol_route_id = typeof value === "string" ? value : "";
}

function handlePatrolRouteClear() {
  orderDraft.patrol_route_id = "";
}

function resolveCommercialIssueMessage(issueCode: string) {
  const mappedKey = mapPlanningCommercialIssueCode(issueCode);
  if (mappedKey) {
    return tp(mappedKey);
  }
  const fallback = formatPlanningCommercialIssueFallback(issueCode);
  return fallback ? `${fallback}.` : tp("commercialIssueFallback");
}

function formatOrderCustomerLabel(customerId: string) {
  return formatPlanningCustomerOption(
    customerOptions.value.find((customer) => customer.id === customerId),
  ) || customerId;
}

function validateOrderServiceWindow() {
  if (!orderDraft.service_from || !orderDraft.service_to) {
    return true;
  }
  if (orderDraft.service_to >= orderDraft.service_from) {
    return true;
  }
  setFeedback("error", tp("errorTitle"), tp("invalidServiceWindow"));
  return false;
}

async function refreshCustomerOptions() {
  if (!tenantScopeId.value || !accessToken.value || !actionState.value.canReadOrders) {
    customerOptions.value = [];
    customerLookupError.value = "";
    return;
  }

  customerLookupLoading.value = true;
  customerLookupError.value = "";
  try {
    customerOptions.value = await listCustomers(tenantScopeId.value, accessToken.value, {});
  } catch {
    customerOptions.value = [];
    customerLookupError.value = tp("customerLoadError");
  } finally {
    customerLookupLoading.value = false;
  }
}

async function refreshOrderReferenceOptions(customerId: string) {
  if (!tenantScopeId.value || !accessToken.value || !actionState.value.canReadOrders || !customerId) {
    requirementTypeOptions.value = [];
    patrolRouteOptions.value = [];
    requirementTypeLookupError.value = "";
    patrolRouteLookupError.value = "";
    if (orderDraft.requirement_type_id) {
      orderDraft.requirement_type_id = "";
    }
    if (orderDraft.patrol_route_id) {
      orderDraft.patrol_route_id = "";
    }
    return;
  }

  requirementTypeLookupLoading.value = true;
  patrolRouteLookupLoading.value = true;
  requirementTypeLookupError.value = "";
  patrolRouteLookupError.value = "";

  try {
    requirementTypeOptions.value = await listPlanningCatalogRecords(
      "requirement_type",
      tenantScopeId.value,
      accessToken.value,
      { customer_id: customerId },
    ) as PlanningListItem[];
    if (!requirementTypeOptions.value.some((row) => row.id === orderDraft.requirement_type_id)) {
      orderDraft.requirement_type_id = "";
    }
  } catch {
    requirementTypeOptions.value = [];
    requirementTypeLookupError.value = tp("requirementTypeLoadError");
    orderDraft.requirement_type_id = "";
  } finally {
    requirementTypeLookupLoading.value = false;
  }

  try {
    patrolRouteOptions.value = await listPlanningCatalogRecords(
      "patrol_route",
      tenantScopeId.value,
      accessToken.value,
      { customer_id: customerId },
    ) as PlanningListItem[];
    if (!patrolRouteOptions.value.some((row) => row.id === orderDraft.patrol_route_id)) {
      orderDraft.patrol_route_id = "";
    }
  } catch {
    patrolRouteOptions.value = [];
    patrolRouteLookupError.value = tp("patrolRouteLoadError");
    orderDraft.patrol_route_id = "";
  } finally {
    patrolRouteLookupLoading.value = false;
  }
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
    activeDetailTab.value = "overview";
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
  activeDetailTab.value = "overview";
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
  if (!validateOrderDraftSelection()) return;
  if (!validateOrderServiceWindow()) return;
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

watch(
  () => [tenantScopeId.value, accessToken.value, actionState.value.canReadOrders] as const,
  async ([nextTenantScopeId, nextAccessToken, canReadOrders]) => {
    if (!nextTenantScopeId || !nextAccessToken || !canReadOrders) {
      customerOptions.value = [];
      requirementTypeOptions.value = [];
      patrolRouteOptions.value = [];
      customerLookupError.value = "";
      requirementTypeLookupError.value = "";
      patrolRouteLookupError.value = "";
      return;
    }
    await refreshCustomerOptions();
  },
  { immediate: true },
);

watch(
  () => orderDraft.customer_id,
  async (customerId) => {
    await refreshOrderReferenceOptions(customerId);
  },
);

watch(
  () => orderHasSavedRecord.value,
  (hasSavedRecord) => {
    if (!hasSavedRecord && activeDetailTab.value !== "overview") {
      activeDetailTab.value = "overview";
    }
  },
);
</script>

<style scoped>
.planning-orders-page,
.planning-orders-form,
.planning-orders-list,
.planning-orders-doc-list,
.planning-orders-section,
.planning-orders-panel,
.planning-orders-empty,
.planning-orders-detail,
.planning-orders-tab-panel {
  display: grid;
  gap: 1rem;
}

.planning-orders-page {
  gap: var(--sp-page-gap, 1.25rem);
}

.planning-orders-grid {
  display: grid;
  gap: var(--sp-page-gap, 1.25rem);
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  align-items: start;
}

.planning-orders-list-panel {
  position: sticky;
  top: 0;
}

.planning-orders-row,
.planning-orders-doc-row {
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 18px;
  padding: 1rem;
  background: var(--sp-color-surface-page);
}

.planning-orders-row {
  align-items: center;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  text-align: left;
}

.planning-orders-row.selected {
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 40%, transparent);
}

.planning-orders-row span,
.planning-orders-doc-row span,
.planning-orders-list-empty,
.field-help {
  color: var(--sp-color-text-secondary);
  margin: 0.35rem 0 0;
}

.planning-orders-form {
  gap: 1.1rem;
}

.planning-orders-section {
  padding: 1rem 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 18px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 76%, white 24%);
  min-width: 0;
}

.planning-orders-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.planning-orders-tab {
  border: 1px solid color-mix(in srgb, var(--sp-color-border-soft) 80%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 82%, white 18%);
  color: var(--sp-color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-weight: 600;
  padding: 0.68rem 1rem;
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease,
    box-shadow 0.18s ease;
}

.planning-orders-tab.active {
  border-color: rgb(40 170 170 / 40%);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 72%, white 28%);
  color: var(--sp-color-primary-strong);
  box-shadow: 0 0 0 1px rgb(40 170 170 / 15%);
}

.planning-orders-tab:focus-visible {
  outline: 2px solid rgb(40 170 170 / 45%);
  outline-offset: 2px;
}

.planning-orders-form-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: start;
}

.planning-orders-form-row {
  display: grid;
  gap: 1rem;
  grid-column: 1 / -1;
}

.planning-orders-form-row--triple {
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.planning-orders-page :deep(.planning-admin-select .ant-select-selector) {
  width: 100%;
  min-height: 48px;
  border-radius: 14px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-card);
  box-shadow: none;
  padding: 0.35rem 0.9rem;
}

.planning-orders-page :deep(.planning-admin-select .ant-select-selection-search-input),
.planning-orders-page :deep(.planning-admin-select .ant-select-selection-item),
.planning-orders-page :deep(.planning-admin-select .ant-select-selection-placeholder) {
  font: inherit;
}

.planning-orders-page :deep(.planning-admin-select.ant-select-focused .ant-select-selector),
.planning-orders-page :deep(.planning-admin-select.ant-select-open .ant-select-selector),
.planning-orders-page :deep(.planning-admin-select.ant-select-status-error .ant-select-selector) {
  border-color: rgb(40 170 170 / 55%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

.planning-orders-page :deep(.planning-admin-select.ant-select-disabled .ant-select-selector) {
  opacity: 0.72;
  cursor: not-allowed;
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

:global(.planning-admin-select-dropdown .ant-select-item-option-content) {
  white-space: normal;
}

.planning-orders-panel__header {
  align-items: start;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.planning-orders-header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.planning-orders-field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.planning-orders-field-action {
  font-size: 0.9rem;
  padding: 0.45rem 0.8rem;
}

.planning-orders-inline-link {
  border: 0;
  background: none;
  color: var(--sp-color-primary);
  cursor: pointer;
  font: inherit;
  margin-left: 0.35rem;
  padding: 0;
  text-decoration: underline;
}

.planning-orders-modal-form {
  display: grid;
  gap: 1rem;
}

.planning-orders-feedback {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  background: var(--sp-color-primary-muted);
  color: var(--sp-color-primary-strong);
}

.planning-orders-feedback[data-tone="error"] {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 45%, #ffb4a6);
  color: color-mix(in srgb, var(--sp-color-primary-strong) 60%, #6a1d00);
}

.planning-orders-feedback[data-tone="success"] {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 32%, #dcfce7);
  color: color-mix(in srgb, var(--sp-color-primary-strong) 65%, #14532d);
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

.planning-orders-subsection {
  border-top: 1px solid var(--vp-c-divider, #d8e0e0);
  padding-top: 1rem;
}

.planning-orders-commercial-summary,
.planning-orders-commercial-block {
  display: grid;
  gap: 0.75rem;
}

.planning-orders-commercial-summary__headline {
  margin: 0;
  font-weight: 700;
}

.planning-orders-issues {
  margin: 0;
  padding-left: 1.2rem;
}

.planning-orders-issues--blocking li::marker {
  color: rgb(176 48 48);
}

.planning-orders-issues--warning li::marker {
  color: rgb(156 104 16);
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
  .planning-orders-grid,
  .planning-orders-form-grid {
    grid-template-columns: 1fr;
  }

  .planning-orders-form-row--triple {
    grid-template-columns: 1fr;
  }

  .planning-orders-list-panel,
  .planning-orders-feedback {
    position: static;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
