<template>
  <section class="planning-orders-page">
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
            <span>{{ tp("filtersLifecycleStatus") }}</span>
            <select v-model="orderFilters.lifecycle_status">
              <option value="">{{ tp("filtersLifecycleStatus") }}</option>
              <option value="active">{{ tp("statusActive") }}</option>
              <option value="inactive">{{ tp("statusInactive") }}</option>
            </select>
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
          <label class="field-stack">
            <span>{{ tp("filtersServiceFrom") }}</span>
            <input v-model="orderFilters.service_from" type="date" :max="orderFilters.service_to || undefined" />
          </label>
          <label class="field-stack">
            <span>{{ tp("filtersServiceTo") }}</span>
            <input v-model="orderFilters.service_to" type="date" :min="orderFilters.service_from || undefined" />
          </label>
        </div>

        <label class="planning-orders-checkbox">
          <input v-model="orderFilters.include_archived" type="checkbox" />
          <span>{{ tp("filtersIncludeArchived") }}</span>
        </label>

        <div class="cta-row">
          <button class="cta-button" type="button" :disabled="loading.orders || loading.action" @click="refreshOrders">{{ tp("actionsRefresh") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreateOrder || loading.orders || loading.action" @click="startCreateOrder">{{ tp("actionsNewOrder") }}</button>
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

        <section class="planning-orders-section planning-orders-records-list" data-testid="planning-orders-record-list-section">
          <div class="planning-orders-panel__header">
            <div>
              <p class="eyebrow">{{ tp("sectionPlanningList") }}</p>
              <h3>{{ tp("planningTitle") }}</h3>
            </div>
            <StatusBadge :status="loading.planning ? 'inactive' : selectedOrderId ? 'active' : 'draft'" />
          </div>

          <div class="planning-orders-form-grid">
            <label class="field-stack">
              <span>{{ tp("filtersPlanningMode") }}</span>
              <select v-model="planningRecordFilters.planning_mode_code" :disabled="!selectedOrderId">
                <option value="">{{ tp("filtersPlanningMode") }}</option>
                <option value="event">{{ tp("modeEvent") }}</option>
                <option value="site">{{ tp("modeSite") }}</option>
                <option value="trade_fair">{{ tp("modeTradeFair") }}</option>
                <option value="patrol">{{ tp("modePatrol") }}</option>
              </select>
            </label>
            <label class="field-stack">
              <span>{{ tp("filtersPlanningFrom") }}</span>
              <input v-model="planningRecordFilters.planning_from" type="date" :disabled="!selectedOrderId" :max="planningRecordFilters.planning_to || undefined" />
            </label>
            <label class="field-stack">
              <span>{{ tp("filtersPlanningTo") }}</span>
              <input v-model="planningRecordFilters.planning_to" type="date" :disabled="!selectedOrderId" :min="planningRecordFilters.planning_from || undefined" />
            </label>
          </div>

          <div class="cta-row">
            <button class="cta-button cta-secondary" type="button" :disabled="!selectedOrderId || loading.planning || loading.action" @click="refreshPlanningRecords">{{ tp("actionsRefreshPlanning") }}</button>
            <button class="cta-button" type="button" :disabled="!actionState.canCreatePlanning || !selectedOrderId || loading.planning || loading.action" @click="startCreatePlanning">{{ tp("actionsNewPlanning") }}</button>
          </div>

          <p v-if="!selectedOrderId" class="field-help">{{ tp("planningListOrderRequired") }}</p>
          <div v-else-if="planningRecords.length" class="planning-orders-list">
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
          <p v-else class="planning-orders-list-empty">{{ tp("planningListEmpty") }}</p>
        </section>
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
            <StatusBadge v-if="detailHeaderBadgeStatus" :status="detailHeaderBadgeStatus" />
          </div>
        </div>

        <template v-if="isCreatingOrder || selectedOrder">
          <nav
            v-if="mainDetailTabs.length"
            class="planning-orders-tabs"
            aria-label="Planning order detail sections"
            data-testid="planning-orders-main-tabs"
          >
            <button
              v-for="tab in mainDetailTabs"
              :key="tab.id"
              type="button"
              class="planning-orders-tab"
              :class="{ active: tab.id === activeMainTab }"
              :data-testid="`planning-orders-main-tab-${tab.id}`"
              @click="activeMainTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </nav>

          <section v-show="activeMainTab === 'order'" class="planning-orders-tab-panel" data-testid="planning-orders-tab-panel-order">
            <nav
              v-if="isCreatingOrder || selectedOrder"
              class="planning-orders-tabs planning-orders-tabs--nested"
              :aria-label="tp('orderOverviewDetailTabsAria')"
              data-testid="planning-orders-order-tabs"
            >
              <button
                v-for="tab in orderTabs"
                :key="tab.id"
                type="button"
                class="planning-orders-tab planning-orders-tab--nested"
                :class="{ active: tab.id === activeOrderTab }"
                :data-testid="`planning-orders-order-tab-${tab.id}`"
                @click="activeOrderTab = tab.id"
              >
                {{ tab.label }}
              </button>
            </nav>

            <form
              v-show="activeOrderTab === 'order_details'"
              class="planning-orders-form"
              data-testid="planning-orders-order-panel-order_details"
              @submit.prevent="submitOrder"
            >
              <fieldset class="planning-orders-fieldset" :disabled="!actionState.canWriteOrders || loading.action">
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
                <div class="field-stack">
                  <div class="planning-orders-field-header">
                    <span id="planning-orders-requirement-type-label">{{ tp("fieldsRequirementType") }}</span>
                    <button
                      class="cta-button cta-secondary planning-orders-field-action"
                      type="button"
                      :disabled="!!setupActionDisabledReason() || loading.action"
                      :title="setupActionDisabledReason()"
                      @mousedown.stop
                      @click.stop="openRequirementTypeModal"
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
                    :disabled="loading.action"
                    :filter-option="filterSelectOption"
                    :placeholder="requirementTypePlaceholder"
                    :status="requirementTypeLookupError || requirementTypeFieldInvalid ? 'error' : undefined"
                    :aria-label="tp('fieldsRequirementType')"
                    :aria-labelledby="'planning-orders-requirement-type-label'"
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
                </div>
                <div class="field-stack">
                  <div class="planning-orders-field-header">
                    <span id="planning-orders-patrol-route-label">{{ tp("fieldsPatrolRoute") }}</span>
                    <button
                      class="cta-button cta-secondary planning-orders-field-action"
                      type="button"
                      :disabled="!!setupActionDisabledReason() || loading.action"
                      :title="setupActionDisabledReason()"
                      @mousedown.stop
                      @click.stop="openPatrolRouteModal"
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
                    :aria-label="tp('fieldsPatrolRoute')"
                    :aria-labelledby="'planning-orders-patrol-route-label'"
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
                </div>
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
              </fieldset>
            </form>

            <section
              v-show="activeOrderTab === 'equipment_lines'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-orders-order-panel-equipment_lines"
            >
              <div class="planning-orders-panel__header">
                <div>
                  <h3>{{ tp("sectionOrderEquipmentLines") }}</h3>
                  <p class="field-help">{{ tp("sectionOrderEquipmentLinesLead") }}</p>
                </div>
              </div>
              <template v-if="selectedOrder">
                <div v-if="orderEquipmentLines.length" class="planning-orders-line-list">
                  <button
                    v-for="line in orderEquipmentLines"
                    :key="line.id"
                    type="button"
                    class="planning-orders-row"
                    :class="{ selected: line.id === selectedEquipmentLineId }"
                    @click="selectEquipmentLine(line.id)"
                  >
                    <div>
                      <strong>{{ equipmentItemLabel(line.equipment_item_id) }}</strong>
                      <span>{{ tpf("equipmentLineQtyLabel", { quantity: String(line.required_qty) }) }}</span>
                    </div>
                    <StatusBadge :status="line.status" />
                  </button>
                </div>
                <p v-else class="planning-orders-list-empty">{{ tp("equipmentLinesEmpty") }}</p>
                <form class="planning-orders-form" @submit.prevent="submitEquipmentLine">
                  <fieldset class="planning-orders-fieldset" :disabled="!actionState.canWriteOrders || loading.action">
                  <div class="planning-orders-form-grid">
                    <label class="field-stack">
                      <span>{{ tp("fieldsEquipmentItem") }}</span>
                      <Select
                        :value="equipmentLineDraft.equipment_item_id || undefined"
                        show-search
                        class="planning-admin-select"
                        popup-class-name="planning-admin-select-dropdown"
                        :options="equipmentItemSelectOptions"
                        :loading="equipmentItemLookupLoading"
                        :disabled="loading.action"
                        :filter-option="filterSelectOption"
                        :placeholder="equipmentItemPlaceholder"
                        @change="handleEquipmentItemChange"
                      />
                    </label>
                    <label class="field-stack">
                      <span>{{ tp("fieldsRequiredQty") }}</span>
                      <input v-model.number="equipmentLineDraft.required_qty" type="number" min="1" />
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ tp("fieldsNotes") }}</span>
                      <textarea v-model="equipmentLineDraft.notes" rows="2" />
                    </label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button" type="submit" :disabled="!actionState.canWriteOrders">{{ tp("actionsSaveEquipmentLine") }}</button>
                    <button class="cta-button cta-secondary" type="button" @click="resetEquipmentLineDraft">{{ tp("actionsReset") }}</button>
                  </div>
                  </fieldset>
                </form>
              </template>
              <p v-else class="field-help">{{ tp("orderChildrenRequireSave") }}</p>
            </section>

            <section
              v-show="activeOrderTab === 'requirement_lines'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-orders-order-panel-requirement_lines"
            >
              <div class="planning-orders-panel__header">
                <div>
                  <h3>{{ tp("sectionOrderRequirementLines") }}</h3>
                  <p class="field-help">{{ tp("sectionOrderRequirementLinesLead") }}</p>
                </div>
              </div>
              <template v-if="selectedOrder">
                <label class="planning-orders-checkbox">
                  <input v-model="includeArchivedRequirementLines" type="checkbox" />
                  <span>{{ tp("includeArchivedRequirementLines") }}</span>
                </label>
                <div v-if="visibleRequirementLines.length" class="planning-orders-line-list">
                  <button
                    v-for="line in visibleRequirementLines"
                    :key="line.id"
                    type="button"
                    class="planning-orders-row"
                    :class="{ selected: line.id === selectedRequirementLineId }"
                    @click="selectRequirementLine(line.id)"
                  >
                    <div>
                      <strong>{{ requirementTypeLabel(line.requirement_type_id) }}</strong>
                      <span>{{ tpf("requirementLineQtyLabel", { minQty: String(line.min_qty), targetQty: String(line.target_qty) }) }}</span>
                    </div>
                    <StatusBadge :status="line.status" />
                  </button>
                </div>
                <p v-else class="planning-orders-list-empty">{{ tp("requirementLinesEmpty") }}</p>
                <form class="planning-orders-form" @submit.prevent="submitRequirementLine">
                  <fieldset class="planning-orders-fieldset" :disabled="!actionState.canWriteOrders || loading.action">
                  <div class="planning-orders-form-grid">
                    <label class="field-stack">
                      <span>{{ tp("fieldsRequirementType") }}</span>
                      <Select
                        :value="requirementLineDraft.requirement_type_id || undefined"
                        show-search
                        class="planning-admin-select"
                        popup-class-name="planning-admin-select-dropdown"
                        :options="requirementTypeSelectOptions"
                        :loading="requirementTypeLookupLoading"
                        :disabled="loading.action"
                        :filter-option="filterSelectOption"
                        :placeholder="requirementTypePlaceholder"
                        @change="handleRequirementLineRequirementTypeChange"
                      />
                    </label>
                    <label class="field-stack">
                      <span>{{ tp("fieldsMinQty") }}</span>
                      <input v-model.number="requirementLineDraft.min_qty" type="number" min="0" />
                    </label>
                    <label class="field-stack">
                      <span>{{ tp("fieldsTargetQty") }}</span>
                      <input v-model.number="requirementLineDraft.target_qty" type="number" min="0" />
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ tp("fieldsNotes") }}</span>
                      <textarea v-model="requirementLineDraft.notes" rows="2" />
                    </label>
                  </div>
                  <p v-if="selectedRequirementLine" class="field-help">{{ tp("requirementLineLifecycleHint") }}</p>
                  <div class="cta-row">
                    <button class="cta-button" type="submit" :disabled="!actionState.canWriteOrders">{{ tp("actionsSaveRequirementLine") }}</button>
                    <button class="cta-button cta-secondary" type="button" @click="resetRequirementLineDraft">{{ tp("actionsReset") }}</button>
                    <button
                      v-if="canDeactivateRequirementLine"
                      class="cta-button cta-secondary"
                      type="button"
                      :disabled="!actionState.canWriteOrders"
                      @click="deactivateRequirementLine"
                    >
                      {{ tp("actionsDeactivateRequirementLine") }}
                    </button>
                    <button
                      v-if="canArchiveRequirementLine"
                      class="cta-button cta-secondary"
                      type="button"
                      :disabled="!actionState.canWriteOrders"
                      @click="archiveRequirementLine"
                    >
                      {{ tp("actionsArchiveRequirementLine") }}
                    </button>
                    <button
                      v-if="canRestoreRequirementLine"
                      class="cta-button cta-secondary"
                      type="button"
                      :disabled="!actionState.canWriteOrders"
                      @click="restoreRequirementLine"
                    >
                      {{ tp("actionsRestoreRequirementLine") }}
                    </button>
                  </div>
                  </fieldset>
                </form>
              </template>
              <p v-else class="field-help">{{ tp("orderChildrenRequireSave") }}</p>
            </section>
            <section
              v-if="selectedOrder"
              v-show="activeOrderTab === 'commercial'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-orders-order-panel-commercial"
            >
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionCommercial") }}</h3></div>
              <div class="planning-orders-commercial-summary">
                <p
                  class="planning-orders-commercial-summary__headline"
                  :class="selectedOrderCommercial?.is_release_ready ? 'planning-orders-state--good' : hasCommercialBlockingIssues ? 'planning-orders-state--bad' : 'planning-orders-state--warn'"
                >
                  {{ tp(commercialSummaryKey) }}
                </p>
                <p class="field-help">
                  {{ tpf(commercialContextKey, { customerLabel: commercialCustomerLabel }) }}
                </p>
                <p v-if="showCommercialFixHint" class="field-help">
                  {{
                    selectedOrderCustomerLabel
                      ? tpf("commercialFixHint", { customerLabel: selectedOrderCustomerLabel })
                      : tp("commercialFixHintFallback")
                  }}
                </p>
                <p v-else-if="showCommercialReviewHint" class="field-help">
                  {{ tpf("commercialReviewHint", { customerLabel: commercialCustomerLabel }) }}
                </p>
                <div v-if="showCommercialSettingsCta" class="cta-row">
                  <button class="cta-button cta-secondary" type="button" @click="openCustomerCommercialSettings">
                    {{ tp("commercialActionOpenCustomerCommercial") }}
                  </button>
                </div>
              </div>
              <div v-if="hasCommercialBlockingIssues" class="planning-orders-commercial-block">
                <strong>{{ tp("commercialBlockingListTitle") }}</strong>
                <ul class="planning-orders-issues planning-orders-issues--blocking">
                  <li v-for="issue in orderCommercialBlockingIssues" :key="issue.code">
                    {{ resolveCommercialIssueMessage(issue.code) }}
                  </li>
                </ul>
              </div>
              <div v-if="hasCommercialWarningIssues" class="planning-orders-commercial-block">
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
              v-show="activeOrderTab === 'release'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-orders-order-panel-release"
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
              v-show="activeOrderTab === 'documents'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-orders-order-panel-documents"
            >
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionOrderDocuments") }}</h3></div>
              <div v-if="orderAttachments.length" class="planning-orders-doc-list">
                <button
                  v-for="document in orderAttachments"
                  :key="document.id"
                  type="button"
                  class="planning-orders-doc-row planning-orders-doc-button"
                  :class="{ selected: document.id === selectedOrderDocumentId }"
                  @click="selectOrderDocument(document.id)"
                >
                  <strong>{{ document.title }}</strong>
                  <span>{{ document.id }}</span>
                  <span>{{ tp("fieldsCurrentVersion") }} {{ document.current_version_no }} · {{ document.status }}</span>
                </button>
              </div>
              <p v-else class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
              <section class="planning-orders-subsection planning-orders-doc-detail" data-testid="planning-orders-order-document-detail">
                <div class="planning-orders-panel__header"><h3>{{ tp("tabDocuments") }}</h3></div>
                <template v-if="selectedOrderDocument">
                  <div class="planning-orders-form-grid">
                    <label class="field-stack"><span>{{ tp("fieldsDocumentTitle") }}</span><input :value="selectedOrderDocument.title" readonly /></label>
                    <label class="field-stack"><span>{{ tp("fieldsDocumentId") }}</span><input :value="selectedOrderDocument.id" readonly /></label>
                    <label class="field-stack"><span>{{ tp("fieldsCurrentVersion") }}</span><input :value="selectedOrderDocument.current_version_no" readonly /></label>
                    <label class="field-stack"><span>{{ tp("fieldsStatus") }}</span><input :value="selectedOrderDocument.status" readonly /></label>
                    <label class="field-stack field-stack--wide"><span>{{ tp("fieldsSourceLabel") }}</span><input :value="selectedOrderDocument.source_label || '-'" readonly /></label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button" type="button" @click="downloadOrderDocumentSelection">{{ tp("actionsDownloadCurrentVersion") }}</button>
                    <button class="cta-button cta-secondary" type="button" @click="copyOrderDocumentId">{{ tp("actionsCopyDocumentId") }}</button>
                    <button class="cta-button cta-secondary" type="button" @click="clearOrderDocumentSelection">{{ tp("actionsClearDocumentSelection") }}</button>
                  </div>
                </template>
                <p v-else class="field-help">{{ tp("documentSelectionEmpty") }}</p>
              </section>
              <form class="planning-orders-form" @submit.prevent="submitOrderAttachment">
                <fieldset class="planning-orders-fieldset" :disabled="!actionState.canManageOrderDocs || loading.action">
                <div class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsDocumentTitle") }}</span><input v-model="orderAttachmentDraft.title" required /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="orderAttachmentDraft.label" /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentFile") }}</span><input type="file" @change="onOrderAttachmentSelected" /></label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageOrderDocs || !orderAttachmentDraft.content_base64">{{ tp("actionsUploadDocument") }}</button>
                </div>
                </fieldset>
              </form>
              <form class="planning-orders-form" @submit.prevent="linkExistingOrderDocument">
                <fieldset class="planning-orders-fieldset" :disabled="!actionState.canManageOrderDocs || loading.action">
                <div class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsDocumentId") }}</span><input v-model="orderAttachmentLink.document_id" /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="orderAttachmentLink.label" /></label>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canManageOrderDocs">{{ tp("actionsLinkDocument") }}</button>
                </div>
                </fieldset>
              </form>
            </section>
          </section>

          <section
            v-if="selectedOrder"
            v-show="activeMainTab === 'planning_records'"
            class="planning-orders-tab-panel planning-orders-section"
            data-testid="planning-orders-main-panel-planning_records"
          >
            <div class="planning-orders-panel__header">
              <div>
                <p class="eyebrow">{{ tp("sectionPlanningList") }}</p>
                <h3>{{ tp("planningTitle") }}</h3>
              </div>
              <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canCreatePlanning || !selectedOrderId" @click="startCreatePlanning">{{ tp("actionsNewPlanning") }}</button>
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

            <nav
              v-if="selectedPlanningRecord || isCreatingPlanning"
              class="planning-orders-tabs planning-orders-tabs--nested"
              :aria-label="tp('planningRecordDetailTabsAria')"
              data-testid="planning-records-detail-tabs"
            >
              <button
                v-for="tab in planningDetailTabs"
                :key="tab.id"
                type="button"
                class="planning-orders-tab planning-orders-tab--nested"
                :class="{ active: tab.id === activePlanningDetailTab }"
                :data-testid="`planning-records-tab-${tab.id}`"
                @click="activePlanningDetailTab = tab.id"
              >
                {{ tab.label }}
              </button>
            </nav>

            <form
              v-show="activePlanningDetailTab === 'overview'"
              class="planning-orders-form"
              data-testid="planning-records-tab-panel-overview"
              @submit.prevent="submitPlanningRecord"
            >
              <fieldset class="planning-orders-fieldset" :disabled="!actionState.canWritePlanning || loading.action">
              <div class="planning-orders-form-grid">
                <label class="field-stack">
                  <span>{{ tp("fieldsPlanningMode") }}</span>
                  <select v-model="planningDraft.planning_mode_code" :disabled="!isCreatingPlanning">
                    <option value="event">{{ tp("modeEvent") }}</option>
                    <option value="site">{{ tp("modeSite") }}</option>
                    <option value="trade_fair">{{ tp("modeTradeFair") }}</option>
                    <option value="patrol">{{ tp("modePatrol") }}</option>
                  </select>
                  <p v-if="!isCreatingPlanning && selectedPlanningRecord" class="field-help">
                    {{ tp("planningModeImmutableHelp") }}
                  </p>
                </label>
                <label class="field-stack"><span>{{ tp("fieldsPlanningName") }}</span><input v-model="planningDraft.name" required /></label>
                <div class="planning-orders-form-row planning-orders-form-row--double">
                  <label class="field-stack">
                    <span>{{ tp("fieldsPlanningFrom") }}</span>
                    <input
                      v-model="planningDraft.planning_from"
                      type="date"
                      required
                      :min="planningFromMin"
                      :max="planningFromMax"
                      :class="{ 'planning-orders-input-invalid': planningFromFieldInvalid }"
                    />
                  </label>
                  <label class="field-stack">
                    <span>{{ tp("fieldsPlanningTo") }}</span>
                    <input
                      v-model="planningDraft.planning_to"
                      type="date"
                      required
                      :min="planningToMin"
                      :max="planningToMax"
                      :class="{ 'planning-orders-input-invalid': planningToFieldInvalid }"
                    />
                  </label>
                  <p v-if="planningWindowHelp" class="field-help planning-orders-row-help">{{ planningWindowHelp }}</p>
                  <p
                    v-if="planningValidationState.attempted && planningRecordValidation.messageKey"
                    class="field-help planning-orders-row-help"
                  >
                    {{ tp(planningRecordValidation.messageKey) }}
                  </p>
                </div>
                <label class="field-stack">
                  <span>{{ tp("fieldsDispatcherUserId") }}</span>
                  <Select
                    :value="planningDraft.dispatcher_user_id || undefined"
                    show-search
                    allow-clear
                    class="planning-admin-select"
                    popup-class-name="planning-admin-select-dropdown"
                    :options="dispatcherSelectOptions"
                    :loading="dispatcherLookupLoading"
                    :disabled="loading.action || dispatcherLookupLoading"
                    :filter-option="filterSelectOption"
                    :placeholder="dispatcherPlaceholder"
                    :status="dispatcherLookupError ? 'error' : undefined"
                    @change="handlePlanningDispatcherChange"
                    @clear="clearPlanningDispatcher"
                  />
                  <p v-if="dispatcherLookupError" class="field-help">{{ dispatcherLookupError }}</p>
                  <p v-else-if="!dispatcherLookupLoading && !dispatcherSelectOptions.length" class="field-help">{{ tp("dispatcherEmpty") }}</p>
                  <p class="field-help">{{ tp("dispatcherIamHint") }}</p>
                </label>
                <label class="field-stack">
                  <span>{{ tp("fieldsParentPlanningRecordId") }}</span>
                  <Select
                    :value="planningDraft.parent_planning_record_id || undefined"
                    show-search
                    allow-clear
                    class="planning-admin-select"
                    popup-class-name="planning-admin-select-dropdown"
                    :options="parentPlanningRecordOptions"
                    :disabled="loading.action || !selectedOrderId"
                    :filter-option="filterSelectOption"
                    :placeholder="parentPlanningRecordPlaceholder"
                    @change="handleParentPlanningRecordChange"
                    @clear="clearParentPlanningRecord"
                  />
                  <p v-if="!selectedOrderId" class="field-help">{{ tp("parentPlanningRecordDisabled") }}</p>
                  <p v-else-if="!parentPlanningRecordOptions.length" class="field-help">{{ tp("parentPlanningRecordEmpty") }}</p>
                </label>
                <label v-if="!isCreatingPlanning && selectedPlanningRecord" class="field-stack">
                  <span>{{ tp("fieldsStatus") }}</span>
                  <select v-model="planningDraft.status">
                    <option v-for="option in planningStatusOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </label>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="planningDraft.notes" rows="3" /></label>
              </div>

              <section class="planning-orders-subsection">
                <h4>{{ tp("sectionModeDetails") }}</h4>
                <div v-if="planningDraft.planning_mode_code === 'event'" class="planning-orders-form-grid">
                  <label class="field-stack">
                    <span>{{ tp("fieldsEventVenueId") }}</span>
                    <Select
                      :value="planningDraft.event_detail.event_venue_id || undefined"
                      show-search
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="eventVenueSelectOptions"
                      :loading="eventVenueLookupLoading"
                      :disabled="loading.action || !planningCustomerId"
                      :filter-option="filterSelectOption"
                      :placeholder="eventVenuePlaceholder"
                      :status="eventVenueLookupError || planningModeDetailInvalid ? 'error' : undefined"
                      @change="handleEventVenueChange"
                    />
                    <p v-if="eventVenueLookupError" class="field-help">{{ eventVenueLookupError }}</p>
                    <p v-else-if="!planningCustomerId" class="field-help">{{ tp("eventVenueCustomerRequired") }}</p>
                    <p v-else-if="!eventVenueLookupLoading && !eventVenueSelectOptions.length" class="field-help">
                      {{ tp("eventVenueEmpty") }}
                      <button class="planning-orders-inline-link" type="button" @click="openPlanningSetup('event_venue')">
                        {{ tp("actionsOpenPlanningSetup") }}
                      </button>
                    </p>
                    <p v-else-if="planningModeDetailInvalid" class="field-help">{{ tp("eventVenueRequired") }}</p>
                  </label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsSetupNote") }}</span><textarea v-model="planningDraft.event_detail.setup_note" rows="2" /></label>
                </div>
                <div v-else-if="planningDraft.planning_mode_code === 'site'" class="planning-orders-form-grid">
                  <label class="field-stack">
                    <span>{{ tp("fieldsSiteId") }}</span>
                    <Select
                      :value="planningDraft.site_detail.site_id || undefined"
                      show-search
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="siteSelectOptions"
                      :loading="siteLookupLoading"
                      :disabled="loading.action || !planningCustomerId"
                      :filter-option="filterSelectOption"
                      :placeholder="sitePlaceholder"
                      :status="siteLookupError || planningModeDetailInvalid ? 'error' : undefined"
                      @change="handleSiteChange"
                    />
                    <p v-if="siteLookupError" class="field-help">{{ siteLookupError }}</p>
                    <p v-else-if="!planningCustomerId" class="field-help">{{ tp("siteCustomerRequired") }}</p>
                    <p v-else-if="!siteLookupLoading && !siteSelectOptions.length" class="field-help">
                      {{ tp("siteEmpty") }}
                      <button class="planning-orders-inline-link" type="button" @click="openPlanningSetup('site')">
                        {{ tp("actionsOpenPlanningSetup") }}
                      </button>
                    </p>
                    <p v-else-if="planningModeDetailInvalid" class="field-help">{{ tp("siteRequired") }}</p>
                  </label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsWatchbookScopeNote") }}</span><textarea v-model="planningDraft.site_detail.watchbook_scope_note" rows="2" /></label>
                </div>
                <div v-else-if="planningDraft.planning_mode_code === 'trade_fair'" class="planning-orders-form-grid">
                  <label class="field-stack">
                    <span>{{ tp("fieldsTradeFairId") }}</span>
                    <Select
                      :value="planningDraft.trade_fair_detail.trade_fair_id || undefined"
                      show-search
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="tradeFairSelectOptions"
                      :loading="tradeFairLookupLoading"
                      :disabled="loading.action || !planningCustomerId"
                      :filter-option="filterSelectOption"
                      :placeholder="tradeFairPlaceholder"
                      :status="tradeFairLookupError || planningModeDetailInvalid ? 'error' : undefined"
                      @change="handleTradeFairChange"
                    />
                    <p v-if="tradeFairLookupError" class="field-help">{{ tradeFairLookupError }}</p>
                    <p v-else-if="!planningCustomerId" class="field-help">{{ tp("tradeFairCustomerRequired") }}</p>
                    <p v-else-if="!tradeFairLookupLoading && !tradeFairSelectOptions.length" class="field-help">
                      {{ tp("tradeFairEmpty") }}
                      <button class="planning-orders-inline-link" type="button" @click="openPlanningSetup('trade_fair')">
                        {{ tp("actionsOpenPlanningSetup") }}
                      </button>
                    </p>
                    <p v-else-if="planningModeDetailInvalid" class="field-help">{{ tp("tradeFairRequired") }}</p>
                  </label>
                  <label class="field-stack">
                    <span>{{ tp("fieldsTradeFairZoneId") }}</span>
                    <Select
                      :value="planningDraft.trade_fair_detail.trade_fair_zone_id || undefined"
                      show-search
                      allow-clear
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="tradeFairZoneSelectOptions"
                      :loading="tradeFairZoneLookupLoading"
                      :disabled="loading.action || !planningDraft.trade_fair_detail.trade_fair_id"
                      :filter-option="filterSelectOption"
                      :placeholder="tradeFairZonePlaceholder"
                      :status="tradeFairZoneLookupError ? 'error' : undefined"
                      @change="handleTradeFairZoneChange"
                      @clear="clearTradeFairZone"
                    />
                    <p v-if="tradeFairZoneLookupError" class="field-help">{{ tradeFairZoneLookupError }}</p>
                    <p v-else-if="!planningDraft.trade_fair_detail.trade_fair_id" class="field-help">{{ tp("tradeFairZoneTradeFairRequired") }}</p>
                    <p v-else-if="!tradeFairZoneLookupLoading && !tradeFairZoneSelectOptions.length" class="field-help">{{ tp("tradeFairZoneEmpty") }}</p>
                  </label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsStandNote") }}</span><textarea v-model="planningDraft.trade_fair_detail.stand_note" rows="2" /></label>
                </div>
                <div v-else class="planning-orders-form-grid">
                  <label class="field-stack">
                    <span>{{ tp("fieldsPatrolRouteDetailId") }}</span>
                    <Select
                      :value="planningDraft.patrol_detail.patrol_route_id || undefined"
                      show-search
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="patrolRouteSelectOptions"
                      :loading="patrolRouteLookupLoading"
                      :disabled="loading.action || !planningCustomerId"
                      :filter-option="filterSelectOption"
                      :placeholder="patrolRouteDetailPlaceholder"
                      :status="patrolRouteLookupError || planningModeDetailInvalid ? 'error' : undefined"
                      @change="handlePlanningPatrolRouteChange"
                    />
                    <p v-if="patrolRouteLookupError" class="field-help">{{ patrolRouteLookupError }}</p>
                    <p v-else-if="!planningCustomerId" class="field-help">{{ tp("patrolRouteCustomerRequired") }}</p>
                    <p v-else-if="!patrolRouteLookupLoading && !patrolRouteSelectOptions.length" class="field-help">
                      {{ tp("patrolRouteEmpty") }}
                      <button class="planning-orders-inline-link" type="button" @click="openPlanningSetup('patrol_route')">
                        {{ tp("actionsOpenPlanningSetup") }}
                      </button>
                    </p>
                    <p v-else-if="planningModeDetailInvalid" class="field-help">{{ tp("patrolRouteRequired") }}</p>
                  </label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsExecutionNote") }}</span><textarea v-model="planningDraft.patrol_detail.execution_note" rows="2" /></label>
                </div>
              </section>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canWritePlanning">{{ tp("actionsSave") }}</button>
                <button class="cta-button cta-secondary" type="button" @click="resetPlanningDraft">{{ tp("actionsReset") }}</button>
                <button
                  v-if="canDeactivatePlanningRecord"
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!actionState.canWritePlanning"
                  @click="deactivatePlanningRecord"
                >
                  {{ tp("actionsDeactivatePlanningRecord") }}
                </button>
                <button
                  v-if="canReactivatePlanningRecord"
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!actionState.canWritePlanning"
                  @click="reactivatePlanningRecord"
                >
                  {{ tp("actionsReactivatePlanningRecord") }}
                </button>
                <button
                  v-if="canArchivePlanningRecord"
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!actionState.canWritePlanning"
                  @click="archivePlanningRecord"
                >
                  {{ tp("actionsArchivePlanningRecord") }}
                </button>
                <button
                  v-if="selectedPlanningRecord"
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!actionState.canCreatePlanning"
                  @click="startReplacementPlanning"
                >
                  {{ tp("actionsCreateReplacementPlanning") }}
                </button>
              </div>
              </fieldset>
            </form>

            <section
              v-if="selectedPlanningRecord"
              v-show="activePlanningDetailTab === 'commercial'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-records-tab-panel-commercial"
            >
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionCommercial") }}</h3></div>
              <p :class="selectedPlanningCommercial?.is_release_ready ? 'planning-orders-state--good' : 'planning-orders-state--bad'">
                {{ selectedPlanningCommercial?.is_release_ready ? tp("commercialReady") : tp("commercialBlocked") }}
              </p>
              <ul v-if="selectedPlanningCommercial?.blocking_issues?.length" class="planning-orders-issues">
                <li v-for="issue in selectedPlanningCommercial.blocking_issues" :key="issue.code">{{ issue.code }}</li>
              </ul>
              <p v-if="selectedPlanningCommercial?.warning_issues?.length" class="planning-orders-state--warn">{{ tp("commercialWarnings") }}</p>
            </section>

            <section
              v-if="selectedPlanningRecord"
              v-show="activePlanningDetailTab === 'release'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-records-tab-panel-release"
            >
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionPlanningRelease") }}</h3></div>
              <div class="cta-row">
                <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionPlanning" @click="transitionPlanning('draft')">{{ tp("actionsBackToDraft") }}</button>
                <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canTransitionPlanning" @click="transitionPlanning('release_ready')">{{ tp("actionsReleaseReady") }}</button>
                <button class="cta-button" type="button" :disabled="!actionState.canTransitionPlanning" @click="transitionPlanning('released')">{{ tp("actionsReleased") }}</button>
              </div>
            </section>

            <section
              v-if="selectedPlanningRecord"
              v-show="activePlanningDetailTab === 'documents'"
              class="planning-orders-section planning-orders-tab-panel planning-orders-tab-panel--nested"
              data-testid="planning-records-tab-panel-documents"
            >
              <div class="planning-orders-panel__header"><h3>{{ tp("sectionPlanningDocuments") }}</h3></div>
              <div v-if="planningAttachments.length" class="planning-orders-doc-list">
                <button
                  v-for="document in planningAttachments"
                  :key="document.id"
                  type="button"
                  class="planning-orders-doc-row planning-orders-doc-button"
                  :class="{ selected: document.id === selectedPlanningDocumentId }"
                  @click="selectPlanningDocument(document.id)"
                >
                  <strong>{{ document.title }}</strong>
                  <span>{{ document.id }}</span>
                  <span>{{ tp("fieldsCurrentVersion") }} {{ document.current_version_no }} · {{ document.status }}</span>
                </button>
              </div>
              <p v-else class="planning-orders-list-empty">{{ tp("listEmpty") }}</p>
              <section class="planning-orders-subsection planning-orders-doc-detail" data-testid="planning-orders-planning-document-detail">
                <div class="planning-orders-panel__header"><h3>{{ tp("tabDocuments") }}</h3></div>
                <template v-if="selectedPlanningDocument">
                  <div class="planning-orders-form-grid">
                    <label class="field-stack"><span>{{ tp("fieldsDocumentTitle") }}</span><input :value="selectedPlanningDocument.title" readonly /></label>
                    <label class="field-stack"><span>{{ tp("fieldsDocumentId") }}</span><input :value="selectedPlanningDocument.id" readonly /></label>
                    <label class="field-stack"><span>{{ tp("fieldsCurrentVersion") }}</span><input :value="selectedPlanningDocument.current_version_no" readonly /></label>
                    <label class="field-stack"><span>{{ tp("fieldsStatus") }}</span><input :value="selectedPlanningDocument.status" readonly /></label>
                    <label class="field-stack field-stack--wide"><span>{{ tp("fieldsSourceLabel") }}</span><input :value="selectedPlanningDocument.source_label || '-'" readonly /></label>
                  </div>
                  <div class="cta-row">
                    <button class="cta-button" type="button" @click="downloadPlanningDocumentSelection">{{ tp("actionsDownloadCurrentVersion") }}</button>
                    <button class="cta-button cta-secondary" type="button" @click="copyPlanningDocumentId">{{ tp("actionsCopyDocumentId") }}</button>
                    <button class="cta-button cta-secondary" type="button" @click="clearPlanningDocumentSelection">{{ tp("actionsClearDocumentSelection") }}</button>
                  </div>
                </template>
                <p v-else class="field-help">{{ tp("documentSelectionEmpty") }}</p>
              </section>
              <form class="planning-orders-form" @submit.prevent="submitPlanningAttachment">
                <fieldset class="planning-orders-fieldset" :disabled="!actionState.canManagePlanningDocs || loading.action">
                <div class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsDocumentTitle") }}</span><input v-model="planningAttachmentDraft.title" required /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="planningAttachmentDraft.label" /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentFile") }}</span><input type="file" @change="onPlanningAttachmentSelected" /></label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!actionState.canManagePlanningDocs || !planningAttachmentDraft.content_base64">{{ tp("actionsUploadDocument") }}</button>
                </div>
                </fieldset>
              </form>
              <form class="planning-orders-form" @submit.prevent="linkExistingPlanningDocument">
                <fieldset class="planning-orders-fieldset" :disabled="!actionState.canManagePlanningDocs || loading.action">
                <div class="planning-orders-form-grid">
                  <label class="field-stack"><span>{{ tp("fieldsDocumentId") }}</span><input v-model="planningAttachmentLink.document_id" /></label>
                  <label class="field-stack"><span>{{ tp("fieldsDocumentLabel") }}</span><input v-model="planningAttachmentLink.label" /></label>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="submit" :disabled="!actionState.canManagePlanningDocs">{{ tp("actionsLinkDocument") }}</button>
                </div>
                </fieldset>
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
import { useSicherPlanFeedback } from "@/composables/useSicherPlanFeedback";
import {
  createPlanningRecord as createPlanningCatalogRecord,
  listPlanningRecords as listPlanningCatalogRecords,
  listTradeFairZones,
  type PlanningListItem,
  type TradeFairZoneRead,
} from "@/api/planningAdmin";
import {
  createCustomerOrder,
  createOrderEquipmentLine,
  createOrderRequirementLine,
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
  listOrderEquipmentLines,
  listOrderRequirementLines,
  listOrderAttachments,
  listPlanningDispatcherCandidates,
  listPlanningRecordAttachments,
  listPlanningRecords,
  setCustomerOrderReleaseState,
  setPlanningRecordReleaseState,
  downloadPlanningDocument,
  updateCustomerOrder,
  updateOrderEquipmentLine,
  updateOrderRequirementLine,
  updatePlanningRecord,
  type CustomerOrderListItem,
  type CustomerOrderRead,
  type OrderEquipmentLineRead,
  type OrderRequirementLineRead,
  type PlanningDispatcherCandidateRead,
  type PlanningCommercialLinkRead,
  type PlanningCatalogRecordRead,
  type PlanningRecordListItem,
  type PlanningRecordRead,
  type PlanningDocumentRead,
} from "@/api/planningOrders";
import {
  buildCustomerCommercialLocation,
  buildPlanningSetupLocation,
  derivePlanningOrderActionState,
  derivePlanningOrderSubmitBlockReason,
  filterVisibleRequirementLines,
  filterPlanningOrderOptionsByScope,
  formatPlanningCommercialIssueFallback,
  formatPlanningOrderReferenceOption,
  hasDuplicateActiveRequirementLine,
  hasPlanningOrderSetupGap,
  mapPlanningCommercialIssueCode,
  mapPlanningOrderApiMessage,
  normalizePlanningOrderUuidValue,
  planningModeLabel,
  validatePlanningOrderDraft,
  validatePlanningRecordDraft,
} from "@/features/planning/planningOrders.helpers.js";
import { formatPlanningCustomerOption, hasPlanningPermission } from "@/features/planning/planningAdmin.helpers.js";
import { planningOrdersMessages } from "@/i18n/planningOrders.messages";
import { useLocaleStore } from "@/stores/locale";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const localeStore = useLocaleStore();
const router = useRouter();
const { showFeedbackToast } = useSicherPlanFeedback();

const loading = reactive({ orders: false, orderDetail: false, planning: false, action: false });
const orderFilters = reactive({
  search: "",
  customer_id: "",
  lifecycle_status: "",
  release_state: "",
  service_from: "",
  service_to: "",
  include_archived: false,
});
const planningRecordFilters = reactive({
  planning_mode_code: "",
  planning_from: "",
  planning_to: "",
});
const customerOptions = ref<CustomerListItem[]>([]);
const customerLookupLoading = ref(false);
const customerLookupError = ref("");
const requirementTypeOptions = ref<PlanningListItem[]>([]);
const requirementTypeLookupLoading = ref(false);
const requirementTypeLookupError = ref("");
const patrolRouteOptions = ref<PlanningListItem[]>([]);
const patrolRouteLookupLoading = ref(false);
const patrolRouteLookupError = ref("");
const dispatcherOptions = ref<PlanningDispatcherCandidateRead[]>([]);
const dispatcherLookupLoading = ref(false);
const dispatcherLookupError = ref("");
const eventVenueOptions = ref<PlanningListItem[]>([]);
const eventVenueLookupLoading = ref(false);
const eventVenueLookupError = ref("");
const siteOptions = ref<PlanningListItem[]>([]);
const siteLookupLoading = ref(false);
const siteLookupError = ref("");
const tradeFairOptions = ref<PlanningListItem[]>([]);
const tradeFairLookupLoading = ref(false);
const tradeFairLookupError = ref("");
const equipmentItemOptions = ref<PlanningCatalogRecordRead[]>([]);
const equipmentItemLookupLoading = ref(false);
const equipmentItemLookupError = ref("");
const tradeFairZoneOptions = ref<TradeFairZoneRead[]>([]);
const tradeFairZoneLookupLoading = ref(false);
const tradeFairZoneLookupError = ref("");
const orderValidationState = reactive({ attempted: false });
const planningValidationState = reactive({ attempted: false });
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
const orderEquipmentLines = ref<OrderEquipmentLineRead[]>([]);
const orderRequirementLines = ref<OrderRequirementLineRead[]>([]);
const orderAttachments = ref<PlanningDocumentRead[]>([]);
const planningAttachments = ref<PlanningDocumentRead[]>([]);
const selectedOrderDocumentId = ref("");
const selectedPlanningDocumentId = ref("");
const selectedOrderId = ref("");
const selectedPlanningRecordId = ref("");
const selectedEquipmentLineId = ref("");
const selectedRequirementLineId = ref("");
const includeArchivedRequirementLines = ref(false);
const selectedOrder = ref<CustomerOrderRead | null>(null);
const selectedPlanningRecord = ref<PlanningRecordRead | null>(null);
const selectedOrderCommercial = ref<PlanningCommercialLinkRead | null>(null);
const selectedPlanningCommercial = ref<PlanningCommercialLinkRead | null>(null);
const isCreatingOrder = ref(false);
const isCreatingPlanning = ref(false);
const activeMainTab = ref("order");
const activeOrderTab = ref("order_details");
const activePlanningDetailTab = ref("overview");

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
const equipmentLineDraft = reactive({ equipment_item_id: "", required_qty: 1, notes: "" });
const requirementLineDraft = reactive({ requirement_type_id: "", min_qty: 0, target_qty: 1, notes: "" });

const tenantScopeId = computed(() => authStore.tenantScopeId || authStore.sessionUser?.tenant_id || "");
const accessToken = computed(() => authStore.accessToken);
const currentLocale = computed(() => (localeStore.locale === "en" ? "en" : "de"));
const effectiveRole = computed(() => authStore.effectiveRole);
const currentSessionUserId = computed(() => authStore.sessionUser?.id || "");
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
  filterPlanningOrderOptionsByScope("requirement_type", requirementTypeOptions.value, orderDraft.customer_id).map((row) => ({
    label: formatPlanningOrderReferenceOption("requirement_type", row),
    value: row.id,
  })),
);
const patrolRouteSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope("patrol_route", patrolRouteOptions.value, orderDraft.customer_id).map((row) => ({
    label: formatPlanningOrderReferenceOption("patrol_route", row),
    value: row.id,
  })),
);
const planningCustomerId = computed(() => selectedOrder.value?.customer_id || orderDraft.customer_id || "");
const dispatcherSelectOptions = computed(() =>
  dispatcherOptions.value.map((row) => ({
    label: formatPlanningOrderReferenceOption("dispatcher_user", row),
    value: row.id,
  })),
);
const equipmentItemSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope(
    "equipment_item",
    equipmentItemOptions.value,
    selectedOrder.value?.customer_id || orderDraft.customer_id,
  ).map((row) => ({
    label: formatPlanningOrderReferenceOption("equipment_item", row),
    value: row.id,
  })),
);
const parentPlanningRecordOptions = computed(() =>
  planningRecords.value
    .filter((row) => row.id !== selectedPlanningRecordId.value)
    .map((row) => ({
      label: formatPlanningOrderReferenceOption("planning_record", row),
      value: row.id,
    })),
);
const eventVenueSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope("event_venue", eventVenueOptions.value, planningCustomerId.value).map((row) => ({
    label: formatPlanningOrderReferenceOption("event_venue", row),
    value: row.id,
  })),
);
const siteSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope("site", siteOptions.value, planningCustomerId.value).map((row) => ({
    label: formatPlanningOrderReferenceOption("site", row),
    value: row.id,
  })),
);
const tradeFairSelectOptions = computed(() =>
  filterPlanningOrderOptionsByScope("trade_fair", tradeFairOptions.value, planningCustomerId.value).map((row) => ({
    label: formatPlanningOrderReferenceOption("trade_fair", row),
    value: row.id,
  })),
);
const tradeFairZoneSelectOptions = computed(() =>
  tradeFairZoneOptions.value.map((row) => ({
    label: formatPlanningOrderReferenceOption("trade_fair_zone", row),
    value: row.id,
  })),
);
const planningStatusOptions = computed(() => [
  { label: tp("statusActive"), value: "active" },
  { label: tp("statusInactive"), value: "inactive" },
]);
const selectedOrderDocument = computed(
  () => orderAttachments.value.find((document) => document.id === selectedOrderDocumentId.value) ?? null,
);
const selectedPlanningDocument = computed(
  () => planningAttachments.value.find((document) => document.id === selectedPlanningDocumentId.value) ?? null,
);
const selectedRequirementLine = computed(
  () => orderRequirementLines.value.find((line) => line.id === selectedRequirementLineId.value) ?? null,
);
const visibleRequirementLines = computed(() =>
  filterVisibleRequirementLines(orderRequirementLines.value, includeArchivedRequirementLines.value),
);
const canDeactivateRequirementLine = computed(
  () =>
    !!selectedRequirementLine.value &&
    selectedRequirementLine.value.archived_at == null &&
    selectedRequirementLine.value.status === "active",
);
const canArchiveRequirementLine = computed(
  () => !!selectedRequirementLine.value && selectedRequirementLine.value.archived_at == null,
);
const canRestoreRequirementLine = computed(
  () =>
    !!selectedRequirementLine.value &&
    (selectedRequirementLine.value.status !== "active" || selectedRequirementLine.value.archived_at != null),
);
const canDeactivatePlanningRecord = computed(
  () =>
    !!selectedPlanningRecord.value &&
    selectedPlanningRecord.value.archived_at == null &&
    selectedPlanningRecord.value.status === "active",
);
const canReactivatePlanningRecord = computed(
  () =>
    !!selectedPlanningRecord.value &&
    selectedPlanningRecord.value.archived_at == null &&
    selectedPlanningRecord.value.status !== "active",
);
const canArchivePlanningRecord = computed(
  () => !!selectedPlanningRecord.value && selectedPlanningRecord.value.archived_at == null,
);
const detailHeaderBadgeStatus = computed(() => {
  if (activeMainTab.value === "planning_records") {
    return selectedPlanningRecord.value?.release_state || "";
  }
  return selectedOrder.value?.release_state || "";
});
const requirementTypePlaceholder = computed(() => {
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
const dispatcherPlaceholder = computed(() => {
  if (dispatcherLookupLoading.value) {
    return tp("dispatcherLoading");
  }
  if (dispatcherLookupError.value) {
    return dispatcherLookupError.value;
  }
  if (!dispatcherSelectOptions.value.length) {
    return tp("dispatcherEmpty");
  }
  return tp("dispatcherSearchPlaceholder");
});
const parentPlanningRecordPlaceholder = computed(() => {
  if (!selectedOrderId.value) {
    return tp("parentPlanningRecordDisabled");
  }
  if (!parentPlanningRecordOptions.value.length) {
    return tp("parentPlanningRecordEmpty");
  }
  return tp("parentPlanningRecordPlaceholder");
});
const eventVenuePlaceholder = computed(() => {
  if (!planningCustomerId.value) return tp("eventVenueCustomerRequired");
  if (eventVenueLookupLoading.value) return tp("eventVenueLoading");
  if (!eventVenueLookupError.value && !eventVenueSelectOptions.value.length) return tp("eventVenueEmpty");
  return tp("eventVenuePlaceholder");
});
const sitePlaceholder = computed(() => {
  if (!planningCustomerId.value) return tp("siteCustomerRequired");
  if (siteLookupLoading.value) return tp("siteLoading");
  if (!siteLookupError.value && !siteSelectOptions.value.length) return tp("siteEmpty");
  return tp("sitePlaceholder");
});
const tradeFairPlaceholder = computed(() => {
  if (!planningCustomerId.value) return tp("tradeFairCustomerRequired");
  if (tradeFairLookupLoading.value) return tp("tradeFairLoading");
  if (!tradeFairLookupError.value && !tradeFairSelectOptions.value.length) return tp("tradeFairEmpty");
  return tp("tradeFairPlaceholder");
});
const tradeFairZonePlaceholder = computed(() => {
  if (!planningDraft.trade_fair_detail.trade_fair_id) return tp("tradeFairZoneTradeFairRequired");
  if (tradeFairZoneLookupLoading.value) return tp("tradeFairZoneLoading");
  if (!tradeFairZoneLookupError.value && !tradeFairZoneSelectOptions.value.length) return tp("tradeFairZoneEmpty");
  return tp("tradeFairZonePlaceholder");
});
const patrolRouteDetailPlaceholder = computed(() => {
  if (!planningCustomerId.value) return tp("patrolRouteCustomerRequired");
  if (patrolRouteLookupLoading.value) return tp("patrolRouteLoading");
  if (!patrolRouteLookupError.value && !patrolRouteSelectOptions.value.length) return tp("patrolRouteEmpty");
  return tp("patrolRouteDetailPlaceholder");
});
const equipmentItemPlaceholder = computed(() => {
  if (equipmentItemLookupLoading.value) return tp("equipmentItemLoading");
  if (!equipmentItemLookupError.value && !equipmentItemSelectOptions.value.length) return tp("equipmentItemEmpty");
  return tp("equipmentItemPlaceholder");
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
const mainDetailTabs = computed(() => [
  { id: "order", label: tp("tabOrder") },
  { id: "planning_records", label: tp("tabPlanningRecords") },
]);
const orderTabs = computed(() => {
  const tabs = [{ id: "order_details", label: tp("tabOrderDetails") }];
  if (!orderHasSavedRecord.value) {
    return tabs;
  }
  return [
    ...tabs,
    { id: "equipment_lines", label: tp("tabEquipmentLines") },
    { id: "requirement_lines", label: tp("tabRequirementLines") },
    { id: "commercial", label: tp("tabCommercial") },
    { id: "release", label: tp("tabRelease") },
    { id: "documents", label: tp("tabDocuments") },
  ];
});
const planningHasSavedRecord = computed(() => Boolean(selectedPlanningRecord.value && !isCreatingPlanning.value));
const planningDetailTabs = computed(() => {
  const tabs = [{ id: "overview", label: tp("tabOverview") }];
  if (!planningHasSavedRecord.value) {
    return tabs;
  }
  return [
    ...tabs,
    { id: "commercial", label: tp("tabCommercial") },
    { id: "release", label: tp("tabRelease") },
    { id: "documents", label: tp("tabDocuments") },
  ];
});
const orderValidationErrors = computed(() => validatePlanningOrderDraft(orderDraft));
const customerFieldInvalid = computed(() => orderValidationState.attempted && orderValidationErrors.value.customer_id);
const requirementTypeFieldInvalid = computed(
  () => orderValidationState.attempted && orderValidationErrors.value.requirement_type_id,
);
const planningRecordValidation = computed(() =>
  validatePlanningRecordDraft(planningDraft, {
    orderServiceFrom: selectedOrder.value?.service_from,
    orderServiceTo: selectedOrder.value?.service_to,
    eventVenueOptions: eventVenueSelectOptions.value,
    siteOptions: siteSelectOptions.value,
    tradeFairOptions: tradeFairSelectOptions.value,
    patrolRouteOptions: patrolRouteSelectOptions.value,
  }),
);
const planningFromFieldInvalid = computed(
  () => planningValidationState.attempted && planningRecordValidation.value.planning_from,
);
const planningToFieldInvalid = computed(
  () => planningValidationState.attempted && planningRecordValidation.value.planning_to,
);
const planningModeDetailInvalid = computed(
  () => planningValidationState.attempted && planningRecordValidation.value.mode_detail,
);
const planningWindowHelp = computed(() => {
  if (!selectedOrder.value?.service_from || !selectedOrder.value?.service_to) {
    return "";
  }
  return tpf("planningWindowAllowed", {
    serviceFrom: selectedOrder.value.service_from,
    serviceTo: selectedOrder.value.service_to,
  });
});
const planningFromMin = computed(() => selectedOrder.value?.service_from || undefined);
const planningFromMax = computed(() => selectedOrder.value?.service_to || undefined);
const planningToMin = computed(() => {
  const orderStart = selectedOrder.value?.service_from || "";
  const planningStart = planningDraft.planning_from || "";
  if (planningStart && orderStart) {
    return planningStart > orderStart ? planningStart : orderStart;
  }
  return planningStart || orderStart || undefined;
});
const planningToMax = computed(() => selectedOrder.value?.service_to || undefined);
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
const hasCommercialBlockingIssues = computed(() => orderCommercialBlockingIssues.value.length > 0);
const hasCommercialWarningIssues = computed(() => orderCommercialWarningIssues.value.length > 0);
const showCommercialFixHint = computed(() => hasCommercialBlockingIssues.value);
const showCommercialReviewHint = computed(() =>
  !hasCommercialBlockingIssues.value && hasCommercialWarningIssues.value,
);
const showCommercialSettingsCta = computed(() =>
  hasCommercialBlockingIssues.value || hasCommercialWarningIssues.value,
);
const commercialSummaryKey = computed(() => {
  if (selectedOrderCommercial.value?.is_release_ready) {
    return "commercialSummaryReady";
  }
  if (hasCommercialBlockingIssues.value) {
    return "commercialSummaryBlocked";
  }
  if (hasCommercialWarningIssues.value) {
    return "commercialSummaryWarnings";
  }
  return "commercialSummaryBlocked";
});
const commercialContextKey = computed(() => {
  if (selectedOrderCommercial.value?.is_release_ready) {
    return "commercialContextReady";
  }
  if (hasCommercialBlockingIssues.value) {
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
  showFeedbackToast({
    key: "planning-orders-feedback",
    message,
    title,
    tone: tone as "error" | "info" | "neutral" | "success" | "warning",
  });
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

function resetEquipmentLineDraft() {
  selectedEquipmentLineId.value = "";
  Object.assign(equipmentLineDraft, {
    equipment_item_id: "",
    required_qty: 1,
    notes: "",
  });
}

function resetRequirementLineDraft() {
  selectedRequirementLineId.value = "";
  Object.assign(requirementLineDraft, {
    requirement_type_id: "",
    min_qty: 0,
    target_qty: 1,
    notes: "",
  });
}

function resetPlanningDraft() {
  planningValidationState.attempted = false;
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

function syncEquipmentLineDraft(line: OrderEquipmentLineRead) {
  selectedEquipmentLineId.value = line.id;
  Object.assign(equipmentLineDraft, {
    equipment_item_id: line.equipment_item_id,
    required_qty: line.required_qty,
    notes: line.notes ?? "",
  });
}

function syncRequirementLineDraft(line: OrderRequirementLineRead) {
  selectedRequirementLineId.value = line.id;
  if (line.archived_at != null) {
    includeArchivedRequirementLines.value = true;
  }
  Object.assign(requirementLineDraft, {
    requirement_type_id: line.requirement_type_id,
    min_qty: line.min_qty,
    target_qty: line.target_qty,
    notes: line.notes ?? "",
  });
}

function syncPlanningDraft(record: PlanningRecordRead) {
  planningValidationState.attempted = false;
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

function prefillReplacementPlanningDraft() {
  if (!selectedPlanningRecord.value) {
    return;
  }
  const current = selectedPlanningRecord.value;
  resetPlanningDraft();
  Object.assign(planningDraft, {
    dispatcher_user_id: current.dispatcher_user_id ?? "",
    parent_planning_record_id: "",
    planning_mode_code: "event",
    name: current.name,
    planning_from: current.planning_from,
    planning_to: current.planning_to,
    notes: current.notes ?? "",
    status: "active",
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

function handleEquipmentItemChange(value: string | number | undefined) {
  equipmentLineDraft.equipment_item_id = typeof value === "string" ? value : "";
}

function handleRequirementLineRequirementTypeChange(value: string | number | undefined) {
  requirementLineDraft.requirement_type_id = typeof value === "string" ? value : "";
}

function handlePlanningDispatcherChange(value: string | number | undefined) {
  planningDraft.dispatcher_user_id = typeof value === "string" ? value : "";
}

function clearPlanningDispatcher() {
  planningDraft.dispatcher_user_id = "";
}

function applyDefaultDispatcherForNewPlanning() {
  if (!isCreatingPlanning.value || planningDraft.dispatcher_user_id || !currentSessionUserId.value) {
    return;
  }
  const currentUserCandidate = dispatcherOptions.value.find((row) => row.id === currentSessionUserId.value);
  if (currentUserCandidate) {
    planningDraft.dispatcher_user_id = currentUserCandidate.id;
  }
}

function handleParentPlanningRecordChange(value: string | number | undefined) {
  planningDraft.parent_planning_record_id = typeof value === "string" ? value : "";
}

function clearParentPlanningRecord() {
  planningDraft.parent_planning_record_id = "";
}

function handleEventVenueChange(value: string | number | undefined) {
  planningDraft.event_detail.event_venue_id = typeof value === "string" ? value : "";
}

function handleSiteChange(value: string | number | undefined) {
  planningDraft.site_detail.site_id = typeof value === "string" ? value : "";
}

function handleTradeFairChange(value: string | number | undefined) {
  planningDraft.trade_fair_detail.trade_fair_id = typeof value === "string" ? value : "";
}

function handleTradeFairZoneChange(value: string | number | undefined) {
  planningDraft.trade_fair_detail.trade_fair_zone_id = typeof value === "string" ? value : "";
}

function clearTradeFairZone() {
  planningDraft.trade_fair_detail.trade_fair_zone_id = "";
}

function handlePlanningPatrolRouteChange(value: string | number | undefined) {
  planningDraft.patrol_detail.patrol_route_id = typeof value === "string" ? value : "";
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

function requirementTypeLabel(requirementTypeId: string) {
  return requirementTypeSelectOptions.value.find((row) => row.value === requirementTypeId)?.label || requirementTypeId;
}

function equipmentItemLabel(equipmentItemId: string) {
  return equipmentItemSelectOptions.value.find((row) => row.value === equipmentItemId)?.label || equipmentItemId;
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
    eventVenueOptions.value = [];
    siteOptions.value = [];
    tradeFairOptions.value = [];
    equipmentItemOptions.value = [];
    tradeFairZoneOptions.value = [];
    requirementTypeLookupError.value = "";
    patrolRouteLookupError.value = "";
    eventVenueLookupError.value = "";
    siteLookupError.value = "";
    tradeFairLookupError.value = "";
    equipmentItemLookupError.value = "";
    tradeFairZoneLookupError.value = "";
    if (orderDraft.requirement_type_id) {
      orderDraft.requirement_type_id = "";
    }
    if (orderDraft.patrol_route_id) {
      orderDraft.patrol_route_id = "";
    }
    planningDraft.event_detail.event_venue_id = "";
    planningDraft.site_detail.site_id = "";
    planningDraft.trade_fair_detail.trade_fair_id = "";
    planningDraft.trade_fair_detail.trade_fair_zone_id = "";
    planningDraft.patrol_detail.patrol_route_id = "";
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

  eventVenueLookupLoading.value = true;
  eventVenueLookupError.value = "";
  try {
    eventVenueOptions.value = await listPlanningCatalogRecords(
      "event_venue",
      tenantScopeId.value,
      accessToken.value,
      { customer_id: customerId },
    ) as PlanningListItem[];
    if (!eventVenueOptions.value.some((row) => row.id === planningDraft.event_detail.event_venue_id)) {
      planningDraft.event_detail.event_venue_id = "";
    }
  } catch {
    eventVenueOptions.value = [];
    eventVenueLookupError.value = tp("eventVenueLoadError");
    planningDraft.event_detail.event_venue_id = "";
  } finally {
    eventVenueLookupLoading.value = false;
  }

  siteLookupLoading.value = true;
  siteLookupError.value = "";
  try {
    siteOptions.value = await listPlanningCatalogRecords(
      "site",
      tenantScopeId.value,
      accessToken.value,
      { customer_id: customerId },
    ) as PlanningListItem[];
    if (!siteOptions.value.some((row) => row.id === planningDraft.site_detail.site_id)) {
      planningDraft.site_detail.site_id = "";
    }
  } catch {
    siteOptions.value = [];
    siteLookupError.value = tp("siteLoadError");
    planningDraft.site_detail.site_id = "";
  } finally {
    siteLookupLoading.value = false;
  }

  tradeFairLookupLoading.value = true;
  tradeFairLookupError.value = "";
  try {
    tradeFairOptions.value = await listPlanningCatalogRecords(
      "trade_fair",
      tenantScopeId.value,
      accessToken.value,
      { customer_id: customerId },
    ) as PlanningListItem[];
    if (!tradeFairOptions.value.some((row) => row.id === planningDraft.trade_fair_detail.trade_fair_id)) {
      planningDraft.trade_fair_detail.trade_fair_id = "";
    }
  } catch {
    tradeFairOptions.value = [];
    tradeFairLookupError.value = tp("tradeFairLoadError");
    planningDraft.trade_fair_detail.trade_fair_id = "";
  } finally {
    tradeFairLookupLoading.value = false;
  }

  equipmentItemLookupLoading.value = true;
  equipmentItemLookupError.value = "";
  try {
    equipmentItemOptions.value = await listPlanningCatalogRecords(
      "equipment_item",
      tenantScopeId.value,
      accessToken.value,
      { customer_id: customerId },
    ) as PlanningCatalogRecordRead[];
    if (!equipmentItemOptions.value.some((row) => row.id === equipmentLineDraft.equipment_item_id)) {
      equipmentLineDraft.equipment_item_id = "";
    }
  } catch {
    equipmentItemOptions.value = [];
    equipmentItemLookupError.value = tp("equipmentItemLoadError");
    equipmentLineDraft.equipment_item_id = "";
  } finally {
    equipmentItemLookupLoading.value = false;
  }
}

async function refreshDispatcherOptions() {
  if (!tenantScopeId.value || !accessToken.value || !actionState.value.canReadPlanning) {
    dispatcherOptions.value = [];
    dispatcherLookupError.value = "";
    return;
  }

  dispatcherLookupLoading.value = true;
  dispatcherLookupError.value = "";
  try {
    dispatcherOptions.value = await listPlanningDispatcherCandidates(tenantScopeId.value, accessToken.value);
    if (!dispatcherOptions.value.some((row) => row.id === planningDraft.dispatcher_user_id)) {
      planningDraft.dispatcher_user_id = "";
    }
    applyDefaultDispatcherForNewPlanning();
  } catch {
    dispatcherOptions.value = [];
    dispatcherLookupError.value = tp("dispatcherLoadError");
  } finally {
    dispatcherLookupLoading.value = false;
  }
}

async function refreshTradeFairZoneOptions(tradeFairId: string) {
  if (!tenantScopeId.value || !accessToken.value || !tradeFairId) {
    tradeFairZoneOptions.value = [];
    tradeFairZoneLookupError.value = "";
    planningDraft.trade_fair_detail.trade_fair_zone_id = "";
    return;
  }

  tradeFairZoneLookupLoading.value = true;
  tradeFairZoneLookupError.value = "";
  try {
    tradeFairZoneOptions.value = await listTradeFairZones(tenantScopeId.value, tradeFairId, accessToken.value);
    if (!tradeFairZoneOptions.value.some((row) => row.id === planningDraft.trade_fair_detail.trade_fair_zone_id)) {
      planningDraft.trade_fair_detail.trade_fair_zone_id = "";
    }
  } catch {
    tradeFairZoneOptions.value = [];
    tradeFairZoneLookupError.value = tp("tradeFairZoneLoadError");
    planningDraft.trade_fair_detail.trade_fair_zone_id = "";
  } finally {
    tradeFairZoneLookupLoading.value = false;
  }
}

function buildPlanningPayload(includeVersion = false) {
  const payload: Record<string, unknown> = {
    tenant_id: tenantScopeId.value,
    dispatcher_user_id: planningDraft.dispatcher_user_id || null,
    name: planningDraft.name,
    planning_from: planningDraft.planning_from,
    planning_to: planningDraft.planning_to,
    notes: planningDraft.notes || null,
  };
  if (!includeVersion) {
    payload.order_id = selectedOrderId.value;
    payload.parent_planning_record_id = planningDraft.parent_planning_record_id || null;
    payload.planning_mode_code = planningDraft.planning_mode_code;
  }
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
    payload.status = planningDraft.status || selectedPlanningRecord.value.status || "active";
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
    activeMainTab.value = "order";
    activeOrderTab.value = "order_details";
    selectedOrderId.value = orderId;
    isCreatingOrder.value = false;
    selectedOrder.value = await getCustomerOrder(tenantScopeId.value, orderId, accessToken.value);
    syncOrderDraft(selectedOrder.value);
    orderEquipmentLines.value = await listOrderEquipmentLines(tenantScopeId.value, orderId, accessToken.value);
    orderRequirementLines.value = await listOrderRequirementLines(tenantScopeId.value, orderId, accessToken.value);
    resetEquipmentLineDraft();
    resetRequirementLineDraft();
    orderAttachments.value = await listOrderAttachments(tenantScopeId.value, orderId, accessToken.value);
    clearOrderDocumentSelection();
    clearPlanningDocumentSelection();
    selectedOrderCommercial.value = await getOrderCommercialLink(tenantScopeId.value, orderId, accessToken.value);
    await refreshPlanningRecords();
  } catch (error) {
    handleError(error);
  } finally {
    loading.orderDetail = false;
  }
}

function startCreateOrder() {
  activeMainTab.value = "order";
  activeOrderTab.value = "order_details";
  isCreatingOrder.value = true;
  selectedOrder.value = null;
  selectedOrderId.value = "";
  planningRecords.value = [];
  selectedPlanningRecord.value = null;
  selectedPlanningRecordId.value = "";
  selectedEquipmentLineId.value = "";
  selectedRequirementLineId.value = "";
  orderEquipmentLines.value = [];
  orderRequirementLines.value = [];
  orderAttachments.value = [];
  planningAttachments.value = [];
  clearOrderDocumentSelection();
  clearPlanningDocumentSelection();
  selectedOrderCommercial.value = null;
  selectedPlanningCommercial.value = null;
  resetOrderDraft();
  resetEquipmentLineDraft();
  resetRequirementLineDraft();
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
    clearOrderDocumentSelection();
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
    clearOrderDocumentSelection();
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
    planningRecords.value = await listPlanningRecords(tenantScopeId.value, accessToken.value, {
      order_id: selectedOrderId.value,
      planning_mode_code: planningRecordFilters.planning_mode_code,
      planning_from: planningRecordFilters.planning_from,
      planning_to: planningRecordFilters.planning_to,
    });
    if (selectedPlanningRecordId.value) {
      const stillSelected = planningRecords.value.find((row) => row.id === selectedPlanningRecordId.value);
      if (!stillSelected) {
        activePlanningDetailTab.value = "overview";
        selectedPlanningRecordId.value = "";
        selectedPlanningRecord.value = null;
        planningAttachments.value = [];
        clearPlanningDocumentSelection();
        selectedPlanningCommercial.value = null;
      }
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.planning = false;
  }
}

function selectEquipmentLine(lineId: string) {
  const line = orderEquipmentLines.value.find((row) => row.id === lineId);
  if (!line) {
    return;
  }
  syncEquipmentLineDraft(line);
}

function selectRequirementLine(lineId: string) {
  const line = orderRequirementLines.value.find((row) => row.id === lineId);
  if (!line) {
    return;
  }
  syncRequirementLineDraft(line);
}

function selectOrderDocument(documentId: string) {
  selectedOrderDocumentId.value = documentId;
}

function clearOrderDocumentSelection() {
  selectedOrderDocumentId.value = "";
}

function selectPlanningDocument(documentId: string) {
  selectedPlanningDocumentId.value = documentId;
}

function clearPlanningDocumentSelection() {
  selectedPlanningDocumentId.value = "";
}

function buildDocumentDownloadName(document: PlanningDocumentRead) {
  const normalizedTitle = (document.title || "").trim().replace(/[\\/:*?"<>|]+/g, "-");
  return normalizedTitle || `document-${document.id}`;
}

function triggerBlobDownload(blob: Blob, fileName: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = fileName;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

async function copyTextToClipboard(value: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const input = document.createElement("input");
  input.value = value;
  document.body.append(input);
  input.select();
  document.execCommand("copy");
  input.remove();
}

async function downloadOrderDocumentSelection() {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrderDocument.value) return;
  try {
    const file = await downloadPlanningDocument(
      tenantScopeId.value,
      selectedOrderDocument.value.id,
      selectedOrderDocument.value.current_version_no,
      accessToken.value,
    );
    triggerBlobDownload(file.blob, file.fileName || buildDocumentDownloadName(selectedOrderDocument.value));
    setFeedback("success", tp("successTitle"), tp("documentDownloadStarted"));
  } catch {
    setFeedback("error", tp("errorTitle"), tp("documentDownloadFailed"));
  }
}

async function downloadPlanningDocumentSelection() {
  if (!tenantScopeId.value || !accessToken.value || !selectedPlanningDocument.value) return;
  try {
    const file = await downloadPlanningDocument(
      tenantScopeId.value,
      selectedPlanningDocument.value.id,
      selectedPlanningDocument.value.current_version_no,
      accessToken.value,
    );
    triggerBlobDownload(file.blob, file.fileName || buildDocumentDownloadName(selectedPlanningDocument.value));
    setFeedback("success", tp("successTitle"), tp("documentDownloadStarted"));
  } catch {
    setFeedback("error", tp("errorTitle"), tp("documentDownloadFailed"));
  }
}

async function copyOrderDocumentId() {
  if (!selectedOrderDocument.value) return;
  try {
    await copyTextToClipboard(selectedOrderDocument.value.id);
    setFeedback("success", tp("successTitle"), tp("documentIdCopied"));
  } catch {
    setFeedback("error", tp("errorTitle"), tp("documentCopyFailed"));
  }
}

async function copyPlanningDocumentId() {
  if (!selectedPlanningDocument.value) return;
  try {
    await copyTextToClipboard(selectedPlanningDocument.value.id);
    setFeedback("success", tp("successTitle"), tp("documentIdCopied"));
  } catch {
    setFeedback("error", tp("errorTitle"), tp("documentCopyFailed"));
  }
}

async function submitEquipmentLine() {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrder.value) return;
  if (!equipmentLineDraft.equipment_item_id || equipmentLineDraft.required_qty < 1) {
    setFeedback("error", tp("errorTitle"), tp("equipmentLineInvalid"));
    return;
  }
  loading.action = true;
  try {
    if (selectedEquipmentLineId.value) {
      await updateOrderEquipmentLine(
        tenantScopeId.value,
        selectedOrder.value.id,
        selectedEquipmentLineId.value,
        accessToken.value,
        {
          equipment_item_id: equipmentLineDraft.equipment_item_id,
          required_qty: equipmentLineDraft.required_qty,
          notes: equipmentLineDraft.notes || null,
          version_no: orderEquipmentLines.value.find((line) => line.id === selectedEquipmentLineId.value)?.version_no,
        },
      );
    } else {
      await createOrderEquipmentLine(tenantScopeId.value, selectedOrder.value.id, accessToken.value, {
        tenant_id: tenantScopeId.value,
        order_id: selectedOrder.value.id,
        equipment_item_id: equipmentLineDraft.equipment_item_id,
        required_qty: equipmentLineDraft.required_qty,
        notes: equipmentLineDraft.notes || null,
      });
    }
    orderEquipmentLines.value = await listOrderEquipmentLines(tenantScopeId.value, selectedOrder.value.id, accessToken.value);
    resetEquipmentLineDraft();
    setFeedback("success", tp("successTitle"), tp("equipmentLineSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function submitRequirementLine() {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrder.value) return;
  if (!requirementLineDraft.requirement_type_id || requirementLineDraft.min_qty < 0 || requirementLineDraft.target_qty < requirementLineDraft.min_qty) {
    setFeedback("error", tp("errorTitle"), tp("requirementLineInvalid"));
    return;
  }
  if (
    hasDuplicateActiveRequirementLine(
      orderRequirementLines.value,
      requirementLineDraft.requirement_type_id,
      selectedRequirementLineId.value,
    )
  ) {
    setFeedback("error", tp("errorTitle"), tp("requirementLineDuplicateActive"));
    return;
  }
  loading.action = true;
  try {
    if (selectedRequirementLineId.value) {
      await updateOrderRequirementLine(
        tenantScopeId.value,
        selectedOrder.value.id,
        selectedRequirementLineId.value,
        accessToken.value,
        {
          requirement_type_id: requirementLineDraft.requirement_type_id,
          min_qty: requirementLineDraft.min_qty,
          target_qty: requirementLineDraft.target_qty,
          notes: requirementLineDraft.notes || null,
          version_no: orderRequirementLines.value.find((line) => line.id === selectedRequirementLineId.value)?.version_no,
        },
      );
    } else {
      await createOrderRequirementLine(tenantScopeId.value, selectedOrder.value.id, accessToken.value, {
        tenant_id: tenantScopeId.value,
        order_id: selectedOrder.value.id,
        requirement_type_id: requirementLineDraft.requirement_type_id,
        min_qty: requirementLineDraft.min_qty,
        target_qty: requirementLineDraft.target_qty,
        notes: requirementLineDraft.notes || null,
      });
    }
    orderRequirementLines.value = await listOrderRequirementLines(tenantScopeId.value, selectedOrder.value.id, accessToken.value);
    resetRequirementLineDraft();
    setFeedback("success", tp("successTitle"), tp("requirementLineSaved"));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function updateRequirementLineLifecycle(payload: Record<string, unknown>, successKey: keyof typeof planningOrdersMessages.de) {
  if (!tenantScopeId.value || !accessToken.value || !selectedOrder.value || !selectedRequirementLine.value) return;
  loading.action = true;
  try {
    await updateOrderRequirementLine(
      tenantScopeId.value,
      selectedOrder.value.id,
      selectedRequirementLine.value.id,
      accessToken.value,
      {
        ...payload,
        version_no: selectedRequirementLine.value.version_no,
      },
    );
    orderRequirementLines.value = await listOrderRequirementLines(tenantScopeId.value, selectedOrder.value.id, accessToken.value);
    resetRequirementLineDraft();
    setFeedback("success", tp("successTitle"), tp(successKey));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function deactivateRequirementLine() {
  await updateRequirementLineLifecycle({ status: "inactive" }, "requirementLineDeactivated");
}

async function archiveRequirementLine() {
  await updateRequirementLineLifecycle(
    { status: "archived", archived_at: new Date().toISOString() },
    "requirementLineArchived",
  );
}

async function restoreRequirementLine() {
  await updateRequirementLineLifecycle({ status: "active", archived_at: null }, "requirementLineRestored");
}

function startCreatePlanning() {
  isCreatingPlanning.value = true;
  activeMainTab.value = "planning_records";
  activePlanningDetailTab.value = "overview";
  selectedPlanningRecordId.value = "";
  selectedPlanningRecord.value = null;
  planningAttachments.value = [];
  clearPlanningDocumentSelection();
  selectedPlanningCommercial.value = null;
  planningValidationState.attempted = false;
  resetPlanningDraft();
  applyDefaultDispatcherForNewPlanning();
}

function startReplacementPlanning() {
  if (!selectedPlanningRecord.value) return;
  isCreatingPlanning.value = true;
  activeMainTab.value = "planning_records";
  activePlanningDetailTab.value = "overview";
  selectedPlanningRecordId.value = "";
  selectedPlanningRecord.value = null;
  planningAttachments.value = [];
  clearPlanningDocumentSelection();
  selectedPlanningCommercial.value = null;
  planningValidationState.attempted = false;
  prefillReplacementPlanningDraft();
}

async function selectPlanningRecord(planningRecordId: string) {
  if (!tenantScopeId.value || !accessToken.value) return;
  loading.planning = true;
  try {
    activeMainTab.value = "planning_records";
    activePlanningDetailTab.value = "overview";
    selectedPlanningRecordId.value = planningRecordId;
    isCreatingPlanning.value = false;
    selectedPlanningRecord.value = await getPlanningRecord(tenantScopeId.value, planningRecordId, accessToken.value);
    syncPlanningDraft(selectedPlanningRecord.value);
    planningAttachments.value = await listPlanningRecordAttachments(tenantScopeId.value, planningRecordId, accessToken.value);
    clearPlanningDocumentSelection();
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
  planningValidationState.attempted = true;
  if (planningRecordValidation.value.messageKey) {
    setFeedback("error", tp("errorTitle"), tp(planningRecordValidation.value.messageKey));
    return;
  }
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

async function updatePlanningRecordLifecycle(payload: Record<string, unknown>, successKey: keyof typeof planningOrdersMessages.de) {
  if (!tenantScopeId.value || !accessToken.value || !selectedPlanningRecord.value) return;
  loading.action = true;
  try {
    selectedPlanningRecord.value = await updatePlanningRecord(
      tenantScopeId.value,
      selectedPlanningRecord.value.id,
      accessToken.value,
      {
        ...payload,
        version_no: selectedPlanningRecord.value.version_no,
      },
    );
    syncPlanningDraft(selectedPlanningRecord.value);
    selectedPlanningCommercial.value = await getPlanningRecordCommercialLink(
      tenantScopeId.value,
      selectedPlanningRecord.value.id,
      accessToken.value,
    );
    await refreshPlanningRecords();
    setFeedback("success", tp("successTitle"), tp(successKey));
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

async function deactivatePlanningRecord() {
  await updatePlanningRecordLifecycle({ status: "inactive" }, "planningRecordDeactivated");
}

async function reactivatePlanningRecord() {
  await updatePlanningRecordLifecycle({ status: "active" }, "planningRecordReactivated");
}

async function archivePlanningRecord() {
  await updatePlanningRecordLifecycle(
    { archived_at: new Date().toISOString() },
    "planningRecordArchived",
  );
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
    clearPlanningDocumentSelection();
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
    clearPlanningDocumentSelection();
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
  () => [tenantScopeId.value, accessToken.value, actionState.value.canReadOrders, actionState.value.canReadPlanning] as const,
  async ([nextTenantScopeId, nextAccessToken, canReadOrders, canReadPlanning]) => {
    if (!nextTenantScopeId || !nextAccessToken || (!canReadOrders && !canReadPlanning)) {
      customerOptions.value = [];
      requirementTypeOptions.value = [];
      patrolRouteOptions.value = [];
      eventVenueOptions.value = [];
      siteOptions.value = [];
      tradeFairOptions.value = [];
      tradeFairZoneOptions.value = [];
      dispatcherOptions.value = [];
      customerLookupError.value = "";
      requirementTypeLookupError.value = "";
      patrolRouteLookupError.value = "";
      eventVenueLookupError.value = "";
      siteLookupError.value = "";
      tradeFairLookupError.value = "";
      tradeFairZoneLookupError.value = "";
      dispatcherLookupError.value = "";
      return;
    }
    await Promise.all([
      refreshCustomerOptions(),
      refreshDispatcherOptions(),
    ]);
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
  () => [planningRecordFilters.planning_mode_code, planningRecordFilters.planning_from, planningRecordFilters.planning_to, selectedOrderId.value] as const,
  async ([, , , orderId]) => {
    if (!orderId) {
      return;
    }
    await refreshPlanningRecords();
  },
);

watch(
  () => planningDraft.trade_fair_detail.trade_fair_id,
  async (tradeFairId) => {
    await refreshTradeFairZoneOptions(tradeFairId);
  },
);

watch(
  () => orderHasSavedRecord.value,
  (hasSavedRecord) => {
    if (!hasSavedRecord && activeOrderTab.value !== "order_details") {
      activeOrderTab.value = "order_details";
    }
  },
);

watch(
  () => planningHasSavedRecord.value,
  (hasSavedRecord) => {
    if (!hasSavedRecord && activePlanningDetailTab.value !== "overview") {
      activePlanningDetailTab.value = "overview";
    }
  },
);
</script>

<style scoped>
.planning-orders-page,
.planning-orders-form,
.planning-orders-list,
.planning-orders-line-list,
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

.planning-orders-doc-button {
  cursor: pointer;
  display: grid;
  gap: 0.35rem;
  text-align: left;
  width: 100%;
}

.planning-orders-doc-button.selected {
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 40%, transparent);
}

.planning-orders-doc-detail {
  gap: 1rem;
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

.planning-orders-fieldset {
  border: 0;
  margin: 0;
  min-width: 0;
  padding: 0;
  display: grid;
  gap: 1.1rem;
}

.planning-orders-fieldset:disabled {
  opacity: 0.86;
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

.planning-orders-tabs--nested {
  margin-top: 0.5rem;
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

.planning-orders-tab--nested {
  padding: 0.58rem 0.92rem;
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

.planning-orders-form-row--double {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.planning-orders-row-help {
  grid-column: 1 / -1;
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

.planning-orders-input-invalid {
  border-color: rgb(220 38 38 / 60%);
  box-shadow: 0 0 0 3px rgb(220 38 38 / 12%);
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

  .planning-orders-form-row--double {
    grid-template-columns: 1fr;
  }

  .planning-orders-list-panel {
    position: static;
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
