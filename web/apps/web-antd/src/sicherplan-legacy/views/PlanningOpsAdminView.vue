<template>
  <section class="planning-admin-page">
    <section
      v-if="feedback.message"
      class="planning-admin-feedback"
      :data-tone="feedback.tone"
    >
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ tp("actionsClearFeedback") }}</button>
    </section>

    <section
      v-if="!resolvedTenantScopeId || !accessToken"
      class="module-card planning-admin-empty"
    >
      <p class="eyebrow">{{ tp("scopeMissingTitle") }}</p>
      <h3>{{ tp("scopeMissingBody") }}</h3>
    </section>

    <section
      v-else-if="!canRead"
      class="module-card planning-admin-empty"
    >
      <p class="eyebrow">{{ tp("permissionMissingTitle") }}</p>
      <h3>{{ tp("permissionMissingBody") }}</h3>
    </section>

    <div
      v-else
      class="planning-admin-grid"
      data-testid="planning-master-detail-layout"
    >
      <section class="module-card planning-admin-panel planning-admin-list-panel">
        <div class="planning-admin-panel__header">
          <div>
            <p class="eyebrow">{{ tp("listTitle") }}</p>
            <h3>{{ entityLabel }}</h3>
            <p class="field-help">{{ tp("listLead") }}</p>
          </div>
          <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
        </div>

        <section class="planning-admin-form-section">
          <div class="planning-admin-shared-context">
            <label class="field-stack">
              <span>{{ tp("entityLabel") }}</span>
              <select v-model="entityKey" @change="changeEntity">
                <option v-for="option in entityOptions" :key="option" :value="option">
                  {{ entityName(option) }}
                </option>
              </select>
            </label>
            <p class="field-help">{{ tp("browseTabsLead") }}</p>
          </div>

          <InternalCardTabs
            v-model="browsePanelTab"
            aria-label="Browse record tools"
            panel-id-prefix="planning-browse-panel"
            tab-id-prefix="planning-browse-tab"
            test-id="planning-browse-tabs"
            :tabs="browsePanelTabs"
          />

          <section
            id="planning-browse-panel-filters"
            role="tabpanel"
            aria-labelledby="planning-browse-tab-filters"
            class="planning-admin-tab-panel"
            :aria-hidden="browsePanelTab !== 'filters'"
            v-show="browsePanelTab === 'filters'"
          >
            <p class="field-help">{{ tp("filtersLead") }}</p>

            <div class="planning-admin-filter-stack">
              <label class="field-stack">
                <span>{{ tp("search") }}</span>
                <input v-model="filters.search" :placeholder="tp('searchPlaceholder')" />
              </label>

              <PlanningCustomerSelect
                v-model="filters.customer_id"
                :label="tp('fieldsCustomer')"
                :options="customerOptions"
                :loading="customerLookupLoading"
                :disabled="loading.list"
                :error="customerLookupError"
                :search-placeholder="tp('customerSearchPlaceholder')"
                :empty-option-label="tp('allCustomers')"
                :loading-text="tp('customerLoading')"
                :empty-text="tp('customerEmpty')"
                :no-match-text="tp('customerNoMatch')"
              />

              <label class="field-stack">
                <span>{{ tp("status") }}</span>
                <select v-model="filters.lifecycle_status">
                  <option value="">{{ tp("allStatuses") }}</option>
                  <option value="active">{{ tp("statusActive") }}</option>
                  <option value="inactive">{{ tp("statusInactive") }}</option>
                  <option value="archived">{{ tp("statusArchived") }}</option>
                </select>
              </label>
            </div>

            <label class="planning-admin-checkbox">
              <input v-model="filters.include_archived" type="checkbox" />
              <span>{{ tp("includeArchived") }}</span>
            </label>

            <div class="cta-row">
              <button class="cta-button" type="button" @click="refreshRecords">
                {{ tp("actionsSearch") }}
              </button>
              <button
                class="cta-button cta-secondary"
                type="button"
                :disabled="!actionState.canCreate"
                @click="startCreateRecord"
              >
                {{ tp("actionsNewRecord") }}
              </button>
            </div>
          </section>

          <section
            id="planning-browse-panel-import"
            role="tabpanel"
            aria-labelledby="planning-browse-tab-import"
            class="planning-admin-tab-panel"
            :aria-hidden="browsePanelTab !== 'import'"
            v-show="browsePanelTab === 'import'"
          >
            <p class="field-help">{{ tp("importLead") }}</p>

            <input
              type="file"
              accept=".csv,text/csv"
              :disabled="!actionState.canImport"
              @change="onImportSelected"
            />

            <div class="cta-row">
              <button
                class="cta-button cta-secondary"
                type="button"
                :disabled="!pendingImportFile || !actionState.canImport"
                @click="loadImportFile"
              >
                {{ tp("actionsLoadImportFile") }}
              </button>
              <button
                class="cta-button cta-secondary"
                type="button"
                :disabled="!actionState.canImport"
                @click="resetImportTemplate"
              >
                {{ tp("actionsResetImportTemplate") }}
              </button>
            </div>

            <label class="field-stack field-stack--wide">
              <span>{{ tp("importCsvLabel") }}</span>
              <textarea
                v-model="importDraft.csv_text"
                rows="6"
                :disabled="!actionState.canImport"
              />
            </label>

            <label class="planning-admin-checkbox">
              <input
                v-model="importDraft.continue_on_error"
                type="checkbox"
                :disabled="!actionState.canImport"
              />
              <span>{{ tp("importContinueOnError") }}</span>
            </label>

            <div class="cta-row">
              <button
                class="cta-button"
                type="button"
                :disabled="!actionState.canImport"
                @click="runImportDryRun"
              >
                {{ tp("actionsImportDryRun") }}
              </button>
              <button
                class="cta-button cta-secondary"
                type="button"
                :disabled="!actionState.canImport"
                @click="runImportExecute"
              >
                {{ tp("actionsImportExecute") }}
              </button>
            </div>

            <p v-if="importDryRunResult" class="field-help">
              {{ tp("importDryRunSummary", { total: importDryRunResult.total_rows, invalid: importDryRunResult.invalid_rows }) }}
            </p>
            <p v-if="lastImportResult" class="field-help">
              {{ tp("importExecuteSummary", { total: lastImportResult.total_rows, created: lastImportResult.created_rows, updated: lastImportResult.updated_rows }) }}
            </p>
          </section>
        </section>

        <div v-if="records.length" class="planning-admin-list">
          <button
            v-for="record in records"
            :key="record.id"
            type="button"
            class="planning-admin-row"
            :class="{ selected: record.id === selectedRecordId }"
            @click="selectRecord(record.id)"
          >
            <div class="planning-admin-row__body">
              <strong>{{ recordTitle(record) }}</strong>
              <span>{{ recordCustomerSummary(record) }}</span>
            </div>
            <StatusBadge :status="record.status" />
          </button>
        </div>
        <p v-else class="planning-admin-list-empty">{{ tp("listEmpty") }}</p>
      </section>

      <section class="module-card planning-admin-panel planning-admin-detail">
        <div class="planning-admin-panel__header">
          <div>
            <p class="eyebrow">{{ tp("detailTitle") }}</p>
            <h3>
              {{
                isCreatingRecord
                  ? tp("newRecordHeading", { entity: editorEntityLabel })
                  : selectedRecord
                    ? recordTitle(selectedRecord)
                    : tp("detailEmptyTitle")
              }}
            </h3>
            <p v-if="isCreatingRecord" class="field-help">{{ tp("detailCreateLead", { entity: editorEntityLabel }) }}</p>
            <p v-else-if="selectedRecord" class="field-help">{{ tp("detailLead") }}</p>
          </div>
          <StatusBadge
            v-if="selectedRecord && !isCreatingRecord"
            :status="selectedRecord.status"
          />
        </div>

        <template v-if="isCreatingRecord || selectedRecord">
          <form class="planning-admin-form planning-admin-form--structured" @submit.prevent="submitRecord">
            <section v-if="selectedRecord && !isCreatingRecord" class="planning-admin-editor-intro">
              <div class="planning-admin-summary">
                <article class="planning-admin-summary__card">
                  <span>{{ tp("entityLabel") }}</span>
                  <strong>{{ entityLabel }}</strong>
                </article>
                <article class="planning-admin-summary__card">
                  <span>{{ tp("fieldsCustomer") }}</span>
                  <strong>{{ draft.customer_id ? resolveCustomerLabel(draft.customer_id) : tp("none") }}</strong>
                </article>
                <article class="planning-admin-summary__card">
                  <span>{{ tp("status") }}</span>
                  <strong>{{ selectedRecord.status }}</strong>
                </article>
              </div>
            </section>

            <section class="planning-admin-form-section">
              <div class="planning-admin-form-section__header">
                <p v-if="isCreatingRecord" class="field-help">{{ tp("newRecordLead") }}</p>
                <p v-if="isCreatingRecord && isDirty" class="field-help planning-admin-dirty-help">{{ tp("dirtyStateHint") }}</p>
              </div>

              <div class="planning-admin-form-grid planning-admin-form-grid--detail">
                <label v-if="isCreatingRecord" class="field-stack field-stack--half">
                  <span>{{ tp("createFamilyLabel") }}</span>
                  <select v-model="editorEntityKey" @change="handleEditorEntityChange">
                    <option v-for="option in createEntityOptions" :key="option" :value="option">
                      {{ entityName(option) }}
                    </option>
                  </select>
                </label>

                <label v-if="isCreatingRecord" class="field-stack field-stack--half">
                  <span>{{ tp("createModeLabel") }}</span>
                  <input :value="tp('createModeValue', { entity: editorEntityLabel })" disabled />
                </label>

                <PlanningCustomerSelect
                  v-if="editorUsesCustomer"
                  v-model="draft.customer_id"
                  class="field-stack--half"
                  :label="tp('fieldsCustomer')"
                  :options="customerOptions"
                  :loading="customerLookupLoading"
                  :disabled="loading.action"
                  :required="true"
                  :error="customerLookupError"
                  :search-placeholder="tp('customerSearchPlaceholder')"
                  :empty-option-label="tp('customerSelectPlaceholder')"
                  :loading-text="tp('customerLoading')"
                  :empty-text="tp('customerEmpty')"
                  :no-match-text="tp('customerNoMatch')"
                />

                <template v-if="isCreatingRecord && editorEntityKey === 'trade_fair_zone'">
                  <label class="field-stack field-stack--half">
                    <span>{{ tp("fieldsTradeFairParent") }}</span>
                    <select v-model="createTradeFairParentId">
                      <option value="">{{ tp("parentTradeFairPlaceholder") }}</option>
                      <option v-for="record in tradeFairParentOptions" :key="record.id" :value="record.id">
                        {{ recordTitle(record) }}
                      </option>
                    </select>
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ tp("fieldsZoneTypeCode") }}</span>
                    <input v-model="zoneDraft.zone_type_code" required />
                  </label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsZoneCode") }}</span><input v-model="zoneDraft.zone_code" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsLabel") }}</span><input v-model="zoneDraft.label" required /></label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="zoneDraft.notes" rows="3" /></label>
                </template>

                <template v-else-if="isCreatingRecord && editorEntityKey === 'patrol_checkpoint'">
                  <label class="field-stack field-stack--half">
                    <span>{{ tp("fieldsPatrolRouteParent") }}</span>
                    <select v-model="createPatrolRouteParentId">
                      <option value="">{{ tp("parentPatrolRoutePlaceholder") }}</option>
                      <option v-for="record in patrolRouteParentOptions" :key="record.id" :value="record.id">
                        {{ recordTitle(record) }}
                      </option>
                    </select>
                  </label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsSequenceNo") }}</span><input v-model="checkpointDraft.sequence_no" type="number" min="1" required /></label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsCheckpointCode") }}</span><input v-model="checkpointDraft.checkpoint_code" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsLabel") }}</span><input v-model="checkpointDraft.label" required /></label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLatitude") }}</span><input v-model="checkpointDraft.latitude" type="number" step="0.000001" required /></label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLongitude") }}</span><input v-model="checkpointDraft.longitude" type="number" step="0.000001" required /></label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsScanTypeCode") }}</span><input v-model="checkpointDraft.scan_type_code" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsExpectedTokenValue") }}</span><input v-model="checkpointDraft.expected_token_value" /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsMinimumDwellSeconds") }}</span><input v-model="checkpointDraft.minimum_dwell_seconds" type="number" min="0" required /></label>
                  <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="checkpointDraft.notes" rows="3" /></label>
                </template>

                <template v-else-if="editorEntityKey === 'requirement_type'">
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsCode") }}</span><input v-model="draft.code" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsLabel") }}</span><input v-model="draft.label" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsDefaultPlanningMode") }}</span><input v-model="draft.default_planning_mode_code" required /></label>
                </template>

                <template v-else-if="editorEntityKey === 'equipment_item'">
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsCode") }}</span><input v-model="draft.code" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsLabel") }}</span><input v-model="draft.label" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsUnitOfMeasure") }}</span><input v-model="draft.unit_of_measure_code" required /></label>
                </template>

                <template v-else-if="editorEntityKey === 'site'">
                  <label class="planning-admin-site-primary-field field-stack field-stack--half"><span>{{ tp("fieldsSiteNo") }}</span><input v-model="draft.site_no" required /></label>
                  <label class="planning-admin-site-primary-field field-stack field-stack--half"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                  <PlanningAddressSelect
                    v-model="draft.address_id"
                    wrapper-class="field-stack--half"
                    :customer-id="draft.customer_id"
                    :label="tp('fieldsAddressId')"
                    :options="siteAddressOptions"
                    :loading="siteAddressLookupLoading"
                    :disabled="loading.action"
                    :error="siteAddressLookupError"
                    :search-placeholder="tp('fieldsAddressSearchPlaceholder')"
                    :loading-text="tp('fieldsAddressLoading')"
                    :empty-text="tp('fieldsAddressEmpty')"
                    :customer-required-text="tp('fieldsAddressCustomerRequired')"
                    :no-match-text="tp('fieldsAddressNoMatch')"
                  />
                  <label class="field-stack field-stack--third">
                    <span>{{ tp("fieldsTimezone") }}</span>
                    <Select
                      v-model:value="draft.timezone"
                      show-search
                      allow-clear
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="timezoneOptions"
                      :filter-option="filterSelectOption"
                      :placeholder="tp('timezonePlaceholder')"
                    />
                  </label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLatitude") }}</span><input v-model="draft.latitude" type="number" step="0.000001" /></label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLongitude") }}</span><input v-model="draft.longitude" type="number" step="0.000001" /></label>
                  <div class="planning-admin-map-action field-stack--wide">
                    <button class="cta-button cta-secondary" type="button" @click="openLocationPicker">
                      {{ tp("actionsPickOnMap") }}
                    </button>
                  </div>
                  <label class="planning-admin-checkbox planning-admin-checkbox--inline field-stack--wide"><input v-model="draft.watchbook_enabled" type="checkbox" /><span>{{ tp("fieldsWatchbookEnabled") }}</span></label>
                </template>

                <template v-else-if="editorEntityKey === 'event_venue'">
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsVenueNo") }}</span><input v-model="draft.venue_no" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                  <PlanningAddressSelect
                    v-model="draft.address_id"
                    wrapper-class="field-stack--half"
                    :customer-id="draft.customer_id"
                    :label="tp('fieldsAddressId')"
                    :options="siteAddressOptions"
                    :loading="siteAddressLookupLoading"
                    :disabled="loading.action"
                    :error="siteAddressLookupError"
                    :search-placeholder="tp('fieldsAddressSearchPlaceholder')"
                    :loading-text="tp('fieldsAddressLoading')"
                    :empty-text="tp('fieldsAddressEmpty')"
                    :customer-required-text="tp('fieldsAddressCustomerRequired')"
                    :no-match-text="tp('fieldsAddressNoMatch')"
                  />
                  <label class="field-stack field-stack--third">
                    <span>{{ tp("fieldsTimezone") }}</span>
                    <Select
                      v-model:value="draft.timezone"
                      show-search
                      allow-clear
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="timezoneOptions"
                      :filter-option="filterSelectOption"
                      :placeholder="tp('timezonePlaceholder')"
                    />
                  </label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLatitude") }}</span><input v-model="draft.latitude" type="number" step="0.000001" /></label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLongitude") }}</span><input v-model="draft.longitude" type="number" step="0.000001" /></label>
                  <div class="planning-admin-map-action field-stack--wide">
                    <button class="cta-button cta-secondary" type="button" @click="openLocationPicker">
                      {{ tp("actionsPickOnMap") }}
                    </button>
                  </div>
                </template>

                <template v-else-if="editorEntityKey === 'trade_fair'">
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsFairNo") }}</span><input v-model="draft.fair_no" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                  <label class="field-stack field-stack--half">
                    <span>{{ tp("fieldsVenueId") }}</span>
                    <select v-model="draft.venue_id">
                      <option value="">{{ tp("none") }}</option>
                      <option v-for="record in filteredVenueOptions" :key="record.id" :value="record.id">
                        {{ recordTitle(record) }}
                      </option>
                    </select>
                  </label>
                  <PlanningAddressSelect
                    v-model="draft.address_id"
                    wrapper-class="field-stack--half"
                    :customer-id="draft.customer_id"
                    :label="tp('fieldsAddressId')"
                    :options="siteAddressOptions"
                    :loading="siteAddressLookupLoading"
                    :disabled="loading.action"
                    :error="siteAddressLookupError"
                    :search-placeholder="tp('fieldsAddressSearchPlaceholder')"
                    :loading-text="tp('fieldsAddressLoading')"
                    :empty-text="tp('fieldsAddressEmpty')"
                    :customer-required-text="tp('fieldsAddressCustomerRequired')"
                    :no-match-text="tp('fieldsAddressNoMatch')"
                  />
                  <label class="field-stack field-stack--third">
                    <span>{{ tp("fieldsTimezone") }}</span>
                    <Select
                      v-model:value="draft.timezone"
                      show-search
                      allow-clear
                      class="planning-admin-select"
                      popup-class-name="planning-admin-select-dropdown"
                      :options="timezoneOptions"
                      :filter-option="filterSelectOption"
                      :placeholder="tp('timezonePlaceholder')"
                    />
                  </label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLatitude") }}</span><input v-model="draft.latitude" type="number" step="0.000001" /></label>
                  <label class="field-stack field-stack--third"><span>{{ tp("fieldsLongitude") }}</span><input v-model="draft.longitude" type="number" step="0.000001" /></label>
                  <div class="planning-admin-map-action field-stack--wide">
                    <button class="cta-button cta-secondary" type="button" @click="openLocationPicker">
                      {{ tp("actionsPickOnMap") }}
                    </button>
                  </div>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsStartDate") }}</span><input v-model="draft.start_date" type="date" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsEndDate") }}</span><input v-model="draft.end_date" type="date" required /></label>
                </template>

                <template v-else-if="editorEntityKey === 'patrol_route'">
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsRouteNo") }}</span><input v-model="draft.route_no" required /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsName") }}</span><input v-model="draft.name" required /></label>
                  <label class="field-stack field-stack--half">
                    <span>{{ tp("fieldsSiteId") }}</span>
                    <select v-model="draft.site_id">
                      <option value="">{{ tp("none") }}</option>
                      <option v-for="record in filteredSiteOptions" :key="record.id" :value="record.id">
                        {{ recordTitle(record) }}
                      </option>
                    </select>
                  </label>
                  <PlanningAddressSelect
                    v-model="draft.meeting_address_id"
                    wrapper-class="field-stack--half"
                    :customer-id="draft.customer_id"
                    :label="tp('fieldsMeetingAddressId')"
                    :options="siteAddressOptions"
                    :loading="siteAddressLookupLoading"
                    :disabled="loading.action"
                    :error="siteAddressLookupError"
                    :search-placeholder="tp('fieldsAddressSearchPlaceholder')"
                    :loading-text="tp('fieldsAddressLoading')"
                    :empty-text="tp('fieldsAddressEmpty')"
                    :customer-required-text="tp('fieldsAddressCustomerRequired')"
                    :no-match-text="tp('fieldsAddressNoMatch')"
                  />
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsStartPointText") }}</span><input v-model="draft.start_point_text" /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsEndPointText") }}</span><input v-model="draft.end_point_text" /></label>
                  <label class="field-stack field-stack--half"><span>{{ tp("fieldsTravelPolicyCode") }}</span><input v-model="draft.travel_policy_code" /></label>
                </template>

                <label v-if="visibleStatus" class="field-stack field-stack--half">
                  <span>{{ tp("status") }}</span>
                  <select v-model="draft.status">
                    <option v-for="status in statusOptions" :key="status" :value="status">{{ tp(`status${status.charAt(0).toUpperCase()}${status.slice(1)}`) }}</option>
                  </select>
                </label>

                <label v-if="!isPlanningChildEntity(editorEntityKey)" class="field-stack field-stack--wide">
                  <span>{{ tp("fieldsNotes") }}</span>
                  <textarea v-model="draft.notes" rows="4" />
                </label>

                <p v-if="childCreateBlockedMessage" class="field-help field-stack--wide">{{ childCreateBlockedMessage }}</p>

                <div class="cta-row field-stack--wide planning-admin-form-actions">
                  <button
                    class="cta-button"
                    type="submit"
                    :disabled="(!actionState.canCreate && !actionState.canEdit) || !!childCreateBlockedMessage"
                  >
                    {{ tp("actionsSaveRecord") }}
                  </button>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    @click="isCreatingRecord ? cancelCreateRecord() : resetDraft()"
                  >
                    {{ isCreatingRecord ? tp("actionsCancelCreate") : tp("actionsResetRecord") }}
                  </button>
                </div>
              </div>
            </section>
          </form>

          <section
            v-if="entityKey === 'trade_fair' && selectedRecord && !isCreatingRecord"
            class="planning-admin-form-section"
          >
            <div class="planning-admin-panel__header">
              <h4>{{ tp("zonesTitle") }}</h4>
            </div>
            <div v-if="tradeFairZones.length" class="planning-admin-list">
              <button
                v-for="zone in tradeFairZones"
                :key="zone.id"
                type="button"
                class="planning-admin-row"
                @click="selectZone(zone)"
              >
                <div class="planning-admin-row__body">
                  <strong>{{ zone.zone_code }} · {{ zone.label }}</strong>
                  <span>{{ zone.zone_type_code }}</span>
                </div>
                <StatusBadge :status="zone.status" />
              </button>
            </div>
            <p v-else class="planning-admin-list-empty">{{ tp("zonesEmpty") }}</p>
            <form class="planning-admin-form" @submit.prevent="submitZone">
              <div class="planning-admin-form-grid planning-admin-form-grid--detail">
                <label class="field-stack field-stack--third"><span>{{ tp("fieldsZoneTypeCode") }}</span><input v-model="zoneDraft.zone_type_code" required /></label>
                <label class="field-stack field-stack--third"><span>{{ tp("fieldsZoneCode") }}</span><input v-model="zoneDraft.zone_code" required /></label>
                <label class="field-stack field-stack--half"><span>{{ tp("fieldsLabel") }}</span><input v-model="zoneDraft.label" required /></label>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="zoneDraft.notes" rows="3" /></label>
              </div>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canManageChildren">{{ tp("actionsAddZone") }}</button>
              </div>
            </form>
          </section>

          <section
            v-if="entityKey === 'patrol_route' && selectedRecord && !isCreatingRecord"
            class="planning-admin-form-section"
          >
            <div class="planning-admin-panel__header">
              <h4>{{ tp("checkpointsTitle") }}</h4>
            </div>
            <div v-if="patrolCheckpoints.length" class="planning-admin-list">
              <button
                v-for="checkpoint in patrolCheckpoints"
                :key="checkpoint.id"
                type="button"
                class="planning-admin-row"
                @click="selectCheckpoint(checkpoint)"
              >
                <div class="planning-admin-row__body">
                  <strong>{{ checkpoint.sequence_no }} · {{ checkpoint.label }}</strong>
                  <span>{{ checkpoint.checkpoint_code }}</span>
                </div>
                <StatusBadge :status="checkpoint.status" />
              </button>
            </div>
            <p v-else class="planning-admin-list-empty">{{ tp("checkpointsEmpty") }}</p>
            <form class="planning-admin-form" @submit.prevent="submitCheckpoint">
              <div class="planning-admin-form-grid planning-admin-form-grid--detail">
                <label class="field-stack field-stack--third"><span>{{ tp("fieldsSequenceNo") }}</span><input v-model="checkpointDraft.sequence_no" type="number" min="1" required /></label>
                <label class="field-stack field-stack--third"><span>{{ tp("fieldsCheckpointCode") }}</span><input v-model="checkpointDraft.checkpoint_code" required /></label>
                <label class="field-stack field-stack--half"><span>{{ tp("fieldsLabel") }}</span><input v-model="checkpointDraft.label" required /></label>
                <label class="field-stack field-stack--third"><span>{{ tp("fieldsLatitude") }}</span><input v-model="checkpointDraft.latitude" type="number" step="0.000001" required /></label>
                <label class="field-stack field-stack--third"><span>{{ tp("fieldsLongitude") }}</span><input v-model="checkpointDraft.longitude" type="number" step="0.000001" required /></label>
                <label class="field-stack field-stack--third"><span>{{ tp("fieldsScanTypeCode") }}</span><input v-model="checkpointDraft.scan_type_code" required /></label>
                <label class="field-stack field-stack--half"><span>{{ tp("fieldsExpectedTokenValue") }}</span><input v-model="checkpointDraft.expected_token_value" /></label>
                <label class="field-stack field-stack--half"><span>{{ tp("fieldsMinimumDwellSeconds") }}</span><input v-model="checkpointDraft.minimum_dwell_seconds" type="number" min="0" required /></label>
                <label class="field-stack field-stack--wide"><span>{{ tp("fieldsNotes") }}</span><textarea v-model="checkpointDraft.notes" rows="3" /></label>
              </div>
              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canManageChildren">{{ tp("actionsAddCheckpoint") }}</button>
              </div>
            </form>
          </section>
        </template>

        <section v-else class="planning-admin-empty">
          <h3>{{ tp("detailEmptyTitle") }}</h3>
          <p>{{ tp("detailEmptyBody") }}</p>
        </section>
      </section>
    </div>

    <PlanningLocationPickerModal
      v-model:open="locationPickerOpen"
      :latitude="draft.latitude"
      :longitude="draft.longitude"
      :initial-center="locationPickerStartPoint"
      :start-point-label="locationPickerStartPoint.label"
      :title="tp('mapPickerTitle')"
      :confirm-text="tp('actionsApplyMapLocation')"
      :cancel-text="tp('actionsCancelMapLocation')"
      :helper-text="tp('mapPickerHelp')"
      :latitude-label="tp('fieldsLatitude')"
      :longitude-label="tp('fieldsLongitude')"
      :load-error-text="tp('mapPickerLoadError')"
      @confirm="applyPickedLocation"
    />
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { Select } from "ant-design-vue";

import StatusBadge from "@/components/StatusBadge.vue";
import PlanningAddressSelect from "@/components/planning/PlanningAddressSelect.vue";
import PlanningCustomerSelect from "@/components/planning/PlanningCustomerSelect.vue";
import PlanningLocationPickerModal from "@/components/planning/PlanningLocationPickerModal.vue";
import InternalCardTabs from "@/components/shared/InternalCardTabs.vue";
import { getCustomer, listCustomerAddresses, listCustomers } from "@/api/customers";
import {
  createPatrolCheckpoint,
  createPlanningRecord,
  createTradeFairZone,
  getPlanningRecord,
  importPlanningDryRun,
  importPlanningExecute,
  listPatrolCheckpoints,
  listPlanningRecords,
  listTradeFairZones,
  PlanningAdminApiError,
  updatePatrolCheckpoint,
  updatePlanningRecord,
  updateTradeFairZone,
} from "@/api/planningAdmin";
import {
  buildPlanningDirtySnapshot,
  buildPlanningImportTemplate,
  derivePlanningActionState,
  formatPlanningCustomerOption,
  isPlanningChildEntity,
  mapPlanningApiMessage,
  normalizePlanningEditorEntity,
  parseOptionalCoordinate,
  PLANNING_CREATE_ENTITY_OPTIONS,
  PLANNING_ENTITY_OPTIONS,
  PLANNING_STATUS_OPTIONS,
  resolvePlanningBrowseEntity,
  resolvePlanningRouteContext,
  resolveInitialMapCenter,
  validatePlanningCreateDraft,
} from "@/features/planning/planningAdmin.helpers.js";
import { planningAdminMessages } from "@/i18n/planningAdmin.messages";
import { useAuthStore } from "@/stores/auth";
import { useLocaleStore } from "@/stores/locale";

defineProps({
  embedded: {
    type: Boolean,
    default: false,
  },
});

const authStore = useAuthStore();
const localeStore = useLocaleStore();
const route = useRoute();

const loading = reactive({ list: false, detail: false, action: false });
const feedback = reactive({ tone: "neutral", title: "", message: "" });
const filters = reactive({ search: "", customer_id: "", lifecycle_status: "", include_archived: false });
const entityOptions = PLANNING_ENTITY_OPTIONS;
const createEntityOptions = PLANNING_CREATE_ENTITY_OPTIONS;
const entityKey = ref("site");
const editorEntityKey = ref("site");
const previousEditorEntityKey = ref("site");
const records = ref([]);
const selectedRecordId = ref("");
const selectedRecord = ref(null);
const previousSelectedRecordId = ref("");
const browsePanelTab = ref("filters");
const tradeFairZones = ref([]);
const patrolCheckpoints = ref([]);
const isCreatingRecord = ref(false);
const savedCreateSnapshot = ref("");
const editingZoneId = ref("");
const editingCheckpointId = ref("");
const pendingImportFile = ref(null);
const importDryRunResult = ref(null);
const lastImportResult = ref(null);
const customerOptions = ref([]);
const customerLookupLoading = ref(false);
const customerLookupError = ref("");
const siteAddressOptions = ref([]);
const siteAddressLookupLoading = ref(false);
const siteAddressLookupError = ref("");
const venueOptions = ref([]);
const siteOptions = ref([]);
const tradeFairParentOptions = ref([]);
const patrolRouteParentOptions = ref([]);
const createTradeFairParentId = ref("");
const createPatrolRouteParentId = ref("");
const locationPickerOpen = ref(false);
const locationPickerStartPoint = ref({
  lat: 51.662973,
  lng: 8.174013,
  zoom: 11,
  label: "",
});

const customerLocationCache = new Map();
const geocodeCache = new Map();

const draft = reactive({
  customer_id: "",
  code: "",
  label: "",
  default_planning_mode_code: "",
  unit_of_measure_code: "",
  site_no: "",
  venue_no: "",
  fair_no: "",
  route_no: "",
  name: "",
  address_id: "",
  timezone: "",
  latitude: "",
  longitude: "",
  watchbook_enabled: false,
  notes: "",
  venue_id: "",
  start_date: "",
  end_date: "",
  site_id: "",
  meeting_address_id: "",
  start_point_text: "",
  end_point_text: "",
  travel_policy_code: "",
  status: "active",
});

const zoneDraft = reactive({ zone_type_code: "", zone_code: "", label: "", notes: "", version_no: 0 });
const checkpointDraft = reactive({
  sequence_no: 1,
  checkpoint_code: "",
  label: "",
  latitude: "",
  longitude: "",
  scan_type_code: "",
  expected_token_value: "",
  minimum_dwell_seconds: 0,
  notes: "",
  version_no: 0,
});

const importDraft = reactive({ csv_text: buildPlanningImportTemplate(entityKey.value), continue_on_error: true });

const effectiveRole = computed(() => authStore.effectiveRole);
const resolvedTenantScopeId = computed(() => authStore.effectiveTenantScopeId);
const accessToken = computed(() => authStore.effectiveAccessToken);
const actionState = computed(() => derivePlanningActionState(effectiveRole.value, entityKey.value, selectedRecord.value));
const canRead = computed(() => actionState.value.canRead);
const currentLocale = computed(() => (localeStore.locale === "en" ? "en" : "de"));
const entityLabel = computed(() => entityName(entityKey.value));
const editorEntityLabel = computed(() => entityName(editorEntityKey.value));
const browsePanelTabs = computed(() => [
  { id: "filters", label: tp("filtersTitle") },
  { id: "import", label: tp("importTitle") },
]);
const timezoneOptions = computed(() =>
  getSupportedTimezones().map((timezone) => ({
    label: timezone,
    value: timezone,
  })),
);
const statusOptions = PLANNING_STATUS_OPTIONS;
const editorUsesCustomer = computed(() => !isPlanningChildEntity(editorEntityKey.value));
const visibleStatus = computed(() => !isPlanningChildEntity(editorEntityKey.value));
const currentDirtySnapshot = computed(() =>
  buildPlanningDirtySnapshot({
    checkpointDraft,
    draft,
    editorEntityKey: editorEntityKey.value,
    isCreatingRecord: isCreatingRecord.value,
    parentPatrolRouteId: createPatrolRouteParentId.value,
    parentTradeFairId: createTradeFairParentId.value,
    selectedRecordId: selectedRecordId.value,
    zoneDraft,
  }),
);
const isDirty = computed(() => currentDirtySnapshot.value !== savedCreateSnapshot.value);
const childCreateBlockedMessage = computed(() => {
  if (editorEntityKey.value === "trade_fair_zone" && !createTradeFairParentId.value) {
    return tp("validationTradeFairParentRequired");
  }
  if (editorEntityKey.value === "patrol_checkpoint" && !createPatrolRouteParentId.value) {
    return tp("validationPatrolRouteParentRequired");
  }
  return "";
});
const filteredVenueOptions = computed(() =>
  venueOptions.value.filter((record) => !draft.customer_id || record.customer_id === draft.customer_id),
);
const filteredSiteOptions = computed(() =>
  siteOptions.value.filter((record) => !draft.customer_id || record.customer_id === draft.customer_id),
);

function tp(key, params = {}) {
  let text = planningAdminMessages[currentLocale.value][key] ?? planningAdminMessages.de[key] ?? key;
  Object.entries(params).forEach(([paramKey, value]) => {
    text = text.replace(`{${paramKey}}`, String(value));
  });
  return text;
}

function entityName(key) {
  return tp(
    {
      requirement_type: "entityRequirementType",
      equipment_item: "entityEquipmentItem",
      site: "entitySite",
      event_venue: "entityEventVenue",
      trade_fair: "entityTradeFair",
      trade_fair_zone: "entityTradeFairZone",
      patrol_route: "entityPatrolRoute",
      patrol_checkpoint: "entityPatrolCheckpoint",
    }[key],
  );
}

function resolveCustomerLabel(customerId) {
  const customer = customerOptions.value.find((option) => option.id === customerId);
  return customer ? formatPlanningCustomerOption(customer) : customerId || tp("none");
}

function usesAddressSelection(entity = editorEntityKey.value) {
  return ["site", "event_venue", "trade_fair", "patrol_route"].includes(entity);
}

function getSupportedTimezones() {
  if (typeof Intl !== "undefined" && typeof Intl.supportedValuesOf === "function") {
    return Intl.supportedValuesOf("timeZone");
  }
  return ["Europe/Berlin", "Europe/Vienna", "Europe/Zurich", "UTC"];
}

function filterSelectOption(input, option) {
  const label = typeof option?.label === "string" ? option.label : "";
  return label.toLowerCase().includes(String(input).toLowerCase());
}

function buildBerlinStartPoint() {
  return {
    lat: 51.662973,
    lng: 8.174013,
    zoom: 11,
    label: tp("mapStartBerlin"),
  };
}

function selectCustomerAddress(customer) {
  if (!customer?.addresses?.length) {
    return null;
  }

  return (
    customer.addresses.find((entry) => entry.is_default && entry.address) ??
    customer.addresses.find((entry) => entry.address_type === "registered" && entry.address) ??
    customer.addresses.find((entry) => entry.address_type === "service" && entry.address) ??
    customer.addresses.find((entry) => entry.address)
  );
}

function buildCustomerGeocodeQuery(customer) {
  const addressLink = selectCustomerAddress(customer);
  const address = addressLink?.address;
  if (!address) {
    return null;
  }

  const fullQuery = [
    address.street_line_1,
    address.street_line_2,
    address.postal_code,
    address.city,
    address.country_code,
  ]
    .filter(Boolean)
    .join(", ");

  const cityQuery = [address.city, address.country_code].filter(Boolean).join(", ");

  return {
    label: address.city || customer.name,
    query: fullQuery || cityQuery,
  };
}

async function geocodeCustomerLocation(query) {
  if (!query) {
    return null;
  }

  if (geocodeCache.has(query)) {
    return geocodeCache.get(query);
  }

  try {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query)}`,
    );
    if (!response.ok) {
      geocodeCache.set(query, null);
      return null;
    }
    const payload = await response.json();
    const [first] = Array.isArray(payload) ? payload : [];
    const result =
      first && Number.isFinite(Number(first.lat)) && Number.isFinite(Number(first.lon))
        ? {
            lat: Number(Number(first.lat).toFixed(6)),
            lng: Number(Number(first.lon).toFixed(6)),
          }
        : null;
    geocodeCache.set(query, result);
    return result;
  } catch {
    geocodeCache.set(query, null);
    return null;
  }
}

async function resolveCustomerStartPoint() {
  if (!draft.customer_id || !resolvedTenantScopeId.value || !accessToken.value) {
    return null;
  }

  let customer = customerLocationCache.get(draft.customer_id) ?? null;
  if (!customer) {
    try {
      customer = await getCustomer(resolvedTenantScopeId.value, draft.customer_id, accessToken.value);
      customerLocationCache.set(draft.customer_id, customer);
    } catch {
      customerLocationCache.set(draft.customer_id, null);
      return null;
    }
  }

  const customerCoordinateAddress = selectCustomerAddress(customer);
  const customerLatitude = parseOptionalCoordinate(customerCoordinateAddress?.address?.latitude);
  const customerLongitude = parseOptionalCoordinate(customerCoordinateAddress?.address?.longitude);
  if (customerLatitude != null && customerLongitude != null) {
    return {
      lat: Number(customerLatitude.toFixed(6)),
      lng: Number(customerLongitude.toFixed(6)),
      zoom: 14,
      label: tp("mapStartCustomerCoordinates", { customer: customer.name }),
      source: "customer-coordinates",
    };
  }

  const geocodeInput = buildCustomerGeocodeQuery(customer);
  if (!geocodeInput?.query) {
    return null;
  }

  const resolved = await geocodeCustomerLocation(geocodeInput.query);
  if (!resolved) {
    return null;
  }

  return {
    ...resolved,
    zoom: 13,
    label: tp("mapStartCustomerAddress", { customer: geocodeInput.label }),
    source: "customer-geocode",
  };
}

function recordCustomerSummary(record) {
  return record.customer_id ? resolveCustomerLabel(record.customer_id) : tp("none");
}

function setFeedback(tone, title, message) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearFeedback() {
  setFeedback("neutral", "", "");
}

function resetDraft() {
  Object.assign(draft, {
    customer_id: "",
    code: "",
    label: "",
    default_planning_mode_code: "",
    unit_of_measure_code: "",
    site_no: "",
    venue_no: "",
    fair_no: "",
    route_no: "",
    name: "",
    address_id: "",
    timezone: "Europe/Berlin",
    latitude: "",
    longitude: "",
    watchbook_enabled: false,
    notes: "",
    venue_id: "",
    start_date: "",
    end_date: "",
    site_id: "",
    meeting_address_id: "",
    start_point_text: "",
    end_point_text: "",
    travel_policy_code: "",
    status: "active",
  });
}

function resetImportTemplate() {
  importDraft.csv_text = buildPlanningImportTemplate(entityKey.value);
}

function resetZoneDraft() {
  Object.assign(zoneDraft, { zone_type_code: "", zone_code: "", label: "", notes: "", version_no: 0 });
  editingZoneId.value = "";
}

function resetCheckpointDraft() {
  Object.assign(checkpointDraft, {
    sequence_no: 1,
    checkpoint_code: "",
    label: "",
    latitude: "",
    longitude: "",
    scan_type_code: "",
    expected_token_value: "",
    minimum_dwell_seconds: 0,
    notes: "",
    version_no: 0,
  });
  editingCheckpointId.value = "";
}

function markCleanState() {
  savedCreateSnapshot.value = currentDirtySnapshot.value;
}

function confirmDiscardChanges() {
  if (!isDirty.value) {
    return true;
  }
  return window.confirm(tp("confirmDiscardChanges"));
}

function recordTitle(record) {
  return record.code || record.site_no || record.venue_no || record.fair_no || record.route_no || record.name || record.label || record.id;
}

function syncDraft(record) {
  resetDraft();
  Object.assign(draft, {
    customer_id: record.customer_id || "",
    code: record.code || "",
    label: record.label || "",
    default_planning_mode_code: record.default_planning_mode_code || "",
    unit_of_measure_code: record.unit_of_measure_code || "",
    site_no: record.site_no || "",
    venue_no: record.venue_no || "",
    fair_no: record.fair_no || "",
    route_no: record.route_no || "",
    name: record.name || "",
    address_id: record.address_id || "",
    timezone: record.timezone || "",
    latitude: record.latitude ?? "",
    longitude: record.longitude ?? "",
    watchbook_enabled: !!record.watchbook_enabled,
    notes: record.notes || "",
    venue_id: record.venue_id || "",
    start_date: record.start_date || "",
    end_date: record.end_date || "",
    site_id: record.site_id || "",
    meeting_address_id: record.meeting_address_id || "",
    start_point_text: record.start_point_text || "",
    end_point_text: record.end_point_text || "",
    travel_policy_code: record.travel_policy_code || "",
    status: record.status || "active",
  });
  editorEntityKey.value = entityKey.value;
  createTradeFairParentId.value = "";
  createPatrolRouteParentId.value = "";
  markCleanState();
}

function buildRecordPayload() {
  const base = {
    tenant_id: resolvedTenantScopeId.value,
    customer_id: draft.customer_id,
    notes: draft.notes || null,
  };
  if (editorEntityKey.value === "requirement_type") {
    return { ...base, code: draft.code, label: draft.label, default_planning_mode_code: draft.default_planning_mode_code };
  }
  if (editorEntityKey.value === "equipment_item") {
    return { ...base, code: draft.code, label: draft.label, unit_of_measure_code: draft.unit_of_measure_code };
  }
  if (editorEntityKey.value === "site") {
    return {
      ...base,
      site_no: draft.site_no,
      name: draft.name,
      address_id: draft.address_id || null,
      timezone: draft.timezone || null,
      latitude: draft.latitude || null,
      longitude: draft.longitude || null,
      watchbook_enabled: draft.watchbook_enabled,
      status: draft.status || undefined,
    };
  }
  if (editorEntityKey.value === "event_venue") {
    return {
      ...base,
      venue_no: draft.venue_no,
      name: draft.name,
      address_id: draft.address_id || null,
      timezone: draft.timezone || null,
      latitude: draft.latitude || null,
      longitude: draft.longitude || null,
      status: draft.status || undefined,
    };
  }
  if (editorEntityKey.value === "trade_fair") {
    return {
      ...base,
      fair_no: draft.fair_no,
      name: draft.name,
      venue_id: draft.venue_id || null,
      address_id: draft.address_id || null,
      timezone: draft.timezone || null,
      latitude: draft.latitude || null,
      longitude: draft.longitude || null,
      start_date: draft.start_date,
      end_date: draft.end_date,
      status: draft.status || undefined,
    };
  }
  return {
    ...base,
    route_no: draft.route_no,
    name: draft.name,
    site_id: draft.site_id || null,
    meeting_address_id: draft.meeting_address_id || null,
    start_point_text: draft.start_point_text || null,
    end_point_text: draft.end_point_text || null,
    travel_policy_code: draft.travel_policy_code || null,
    status: draft.status || undefined,
  };
}

function buildZonePayload() {
  return {
    tenant_id: resolvedTenantScopeId.value,
    trade_fair_id: createTradeFairParentId.value || selectedRecord.value?.id,
    zone_type_code: zoneDraft.zone_type_code.trim(),
    zone_code: zoneDraft.zone_code.trim(),
    label: zoneDraft.label.trim(),
    notes: zoneDraft.notes?.trim() ? zoneDraft.notes.trim() : null,
  };
}

function buildCheckpointPayload() {
  return {
    tenant_id: resolvedTenantScopeId.value,
    patrol_route_id: createPatrolRouteParentId.value || selectedRecord.value?.id,
    sequence_no: Number(checkpointDraft.sequence_no),
    checkpoint_code: checkpointDraft.checkpoint_code.trim(),
    label: checkpointDraft.label.trim(),
    latitude: checkpointDraft.latitude,
    longitude: checkpointDraft.longitude,
    scan_type_code: checkpointDraft.scan_type_code.trim(),
    expected_token_value: checkpointDraft.expected_token_value?.trim() ? checkpointDraft.expected_token_value.trim() : null,
    minimum_dwell_seconds: Number(checkpointDraft.minimum_dwell_seconds),
    notes: checkpointDraft.notes?.trim() ? checkpointDraft.notes.trim() : null,
  };
}

async function refreshCustomerOptions() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !canRead.value) {
    customerOptions.value = [];
    customerLookupError.value = "";
    return;
  }

  customerLookupLoading.value = true;
  customerLookupError.value = "";
  try {
    customerOptions.value = await listCustomers(resolvedTenantScopeId.value, accessToken.value, {});
  } catch {
    customerOptions.value = [];
    customerLookupError.value = tp("customerLoadError");
  } finally {
    customerLookupLoading.value = false;
  }
}

async function refreshSiteAddressOptions() {
  if (!usesAddressSelection()) {
    siteAddressOptions.value = [];
    siteAddressLookupError.value = "";
    siteAddressLookupLoading.value = false;
    return;
  }

  if (!resolvedTenantScopeId.value || !accessToken.value || !draft.customer_id) {
    siteAddressOptions.value = [];
    siteAddressLookupError.value = "";
    siteAddressLookupLoading.value = false;
    draft.address_id = "";
    return;
  }

  const requestedCustomerId = draft.customer_id;
  siteAddressLookupLoading.value = true;
  siteAddressLookupError.value = "";
  try {
    const addressLinks = await listCustomerAddresses(
      resolvedTenantScopeId.value,
      requestedCustomerId,
      accessToken.value,
    );
    if (draft.customer_id !== requestedCustomerId || !usesAddressSelection()) {
      return;
    }
    siteAddressOptions.value = addressLinks.filter((entry) => entry.status !== "archived");
    if (draft.address_id && !siteAddressOptions.value.some((entry) => entry.address_id === draft.address_id)) {
      draft.address_id = "";
    }
    if (
      draft.meeting_address_id &&
      !siteAddressOptions.value.some((entry) => entry.address_id === draft.meeting_address_id)
    ) {
      draft.meeting_address_id = "";
    }
  } catch {
    if (draft.customer_id !== requestedCustomerId || !usesAddressSelection()) {
      return;
    }
    siteAddressOptions.value = [];
    siteAddressLookupError.value = tp("addressLoadError");
    draft.address_id = "";
    draft.meeting_address_id = "";
  } finally {
    if (draft.customer_id === requestedCustomerId && usesAddressSelection()) {
      siteAddressLookupLoading.value = false;
    }
  }
}

async function refreshReferenceRecords() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !canRead.value) {
    venueOptions.value = [];
    siteOptions.value = [];
    tradeFairParentOptions.value = [];
    patrolRouteParentOptions.value = [];
    return;
  }

  try {
    const [sites, venues, fairs, routes] = await Promise.all([
      listPlanningRecords("site", resolvedTenantScopeId.value, accessToken.value, {}),
      listPlanningRecords("event_venue", resolvedTenantScopeId.value, accessToken.value, {}),
      listPlanningRecords("trade_fair", resolvedTenantScopeId.value, accessToken.value, {}),
      listPlanningRecords("patrol_route", resolvedTenantScopeId.value, accessToken.value, {}),
    ]);
    siteOptions.value = sites;
    venueOptions.value = venues;
    tradeFairParentOptions.value = fairs;
    patrolRouteParentOptions.value = routes;
  } catch {
    venueOptions.value = [];
    siteOptions.value = [];
    tradeFairParentOptions.value = [];
    patrolRouteParentOptions.value = [];
  }
}

async function refreshRecords() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !canRead.value) {
    records.value = [];
    return;
  }
  loading.list = true;
  try {
    records.value = await listPlanningRecords(entityKey.value, resolvedTenantScopeId.value, accessToken.value, filters);
    if (selectedRecordId.value) {
      const stillSelected = records.value.find((record) => record.id === selectedRecordId.value);
      if (!stillSelected) {
        selectedRecord.value = null;
        selectedRecordId.value = "";
      }
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.list = false;
  }
}

async function selectRecord(recordId, options = {}) {
  if (!resolvedTenantScopeId.value || !accessToken.value) return;
  if (!options.force && !confirmDiscardChanges()) return;
  loading.detail = true;
  try {
    selectedRecord.value = await getPlanningRecord(entityKey.value, resolvedTenantScopeId.value, recordId, accessToken.value);
    selectedRecordId.value = recordId;
    isCreatingRecord.value = false;
    syncDraft(selectedRecord.value);
    tradeFairZones.value = entityKey.value === "trade_fair"
      ? await listTradeFairZones(resolvedTenantScopeId.value, recordId, accessToken.value)
      : [];
    patrolCheckpoints.value = entityKey.value === "patrol_route"
      ? await listPatrolCheckpoints(resolvedTenantScopeId.value, recordId, accessToken.value)
      : [];
    resetZoneDraft();
    resetCheckpointDraft();
    previousSelectedRecordId.value = recordId;
  } catch (error) {
    handleError(error);
  } finally {
    loading.detail = false;
  }
}

function startCreateRecord() {
  if (!confirmDiscardChanges()) return;
  isCreatingRecord.value = true;
  editorEntityKey.value = normalizePlanningEditorEntity(entityKey.value);
  previousSelectedRecordId.value = selectedRecordId.value;
  selectedRecord.value = null;
  selectedRecordId.value = "";
  tradeFairZones.value = [];
  patrolCheckpoints.value = [];
  resetDraft();
  resetZoneDraft();
  resetCheckpointDraft();
  draft.customer_id = filters.customer_id || "";
  createTradeFairParentId.value = "";
  createPatrolRouteParentId.value = "";
  markCleanState();
}

function cancelCreateRecord() {
  if (!confirmDiscardChanges()) return;
  isCreatingRecord.value = false;
  editorEntityKey.value = entityKey.value;
  resetDraft();
  resetZoneDraft();
  resetCheckpointDraft();
  createTradeFairParentId.value = "";
  createPatrolRouteParentId.value = "";
  if (previousSelectedRecordId.value) {
    void selectRecord(previousSelectedRecordId.value, { force: true });
    return;
  }
  selectedRecord.value = null;
  selectedRecordId.value = "";
  markCleanState();
}

function handleEditorEntityChange() {
  if (!confirmDiscardChanges()) {
    editorEntityKey.value = previousEditorEntityKey.value;
    return;
  }
  resetDraft();
  resetZoneDraft();
  resetCheckpointDraft();
  draft.customer_id = filters.customer_id || "";
  createTradeFairParentId.value = "";
  createPatrolRouteParentId.value = "";
  markCleanState();
}

async function openLocationPicker() {
  const customerStartPoint = await resolveCustomerStartPoint();
  const fallback = buildBerlinStartPoint();
  const resolvedCenter = resolveInitialMapCenter({
    currentLatitude: draft.latitude,
    currentLongitude: draft.longitude,
    customerCoordinates:
      customerStartPoint?.source === "customer-coordinates"
        ? { lat: customerStartPoint.lat, lng: customerStartPoint.lng }
        : null,
    customerGeocode:
      customerStartPoint?.source === "customer-geocode"
        ? { lat: customerStartPoint.lat, lng: customerStartPoint.lng }
        : null,
    fallback,
  });

  const sourceLabelMap = {
    "existing-record": tp("mapStartExisting"),
    "customer-coordinates": customerStartPoint?.label ?? tp("mapStartCustomerCoordinatesFallback"),
    "customer-geocode": customerStartPoint?.label ?? tp("mapStartCustomerAddressFallback"),
    fallback: fallback.label,
  };

  locationPickerStartPoint.value = {
    lat: resolvedCenter.lat,
    lng: resolvedCenter.lng,
    zoom: resolvedCenter.source === "existing-record" ? 14 : (customerStartPoint?.zoom ?? fallback.zoom),
    label: sourceLabelMap[resolvedCenter.source],
  };
  locationPickerOpen.value = true;
}

function applyPickedLocation(payload) {
  draft.latitude = payload.latitude;
  draft.longitude = payload.longitude;
}

async function submitRecord() {
  if (!resolvedTenantScopeId.value || !accessToken.value) return;
  const validationKey = validatePlanningCreateDraft({
    checkpointDraft,
    draft,
    editorEntityKey: editorEntityKey.value,
    parentPatrolRouteId: createPatrolRouteParentId.value,
    parentTradeFairId: createTradeFairParentId.value,
    zoneDraft,
  });
  if (validationKey) {
    setFeedback("error", tp("errorTitle"), tp(validationKey));
    return;
  }
  loading.action = true;
  try {
    if (isCreatingRecord.value && editorEntityKey.value === "trade_fair_zone") {
      const createdZone = await createTradeFairZone(
        resolvedTenantScopeId.value,
        createTradeFairParentId.value,
        accessToken.value,
        buildZonePayload(),
      );
      entityKey.value = "trade_fair";
      editorEntityKey.value = "trade_fair";
      await refreshRecords();
      await selectRecord(createTradeFairParentId.value, { force: true });
      selectZone(createdZone);
      isCreatingRecord.value = false;
      setFeedback("success", tp("successTitle"), tp("childSaved"));
      markCleanState();
      return;
    }

    if (isCreatingRecord.value && editorEntityKey.value === "patrol_checkpoint") {
      const createdCheckpoint = await createPatrolCheckpoint(
        resolvedTenantScopeId.value,
        createPatrolRouteParentId.value,
        accessToken.value,
        buildCheckpointPayload(),
      );
      entityKey.value = "patrol_route";
      editorEntityKey.value = "patrol_route";
      await refreshRecords();
      await selectRecord(createPatrolRouteParentId.value, { force: true });
      selectCheckpoint(createdCheckpoint);
      isCreatingRecord.value = false;
      setFeedback("success", tp("successTitle"), tp("childSaved"));
      markCleanState();
      return;
    }

    const payload = buildRecordPayload();
    if (isCreatingRecord.value || !selectedRecord.value) {
      selectedRecord.value = await createPlanningRecord(editorEntityKey.value, resolvedTenantScopeId.value, accessToken.value, payload);
      selectedRecordId.value = selectedRecord.value.id;
      entityKey.value = resolvePlanningBrowseEntity(editorEntityKey.value);
      editorEntityKey.value = entityKey.value;
      isCreatingRecord.value = false;
      await refreshRecords();
    } else {
      selectedRecord.value = await updatePlanningRecord(
        editorEntityKey.value,
        resolvedTenantScopeId.value,
        selectedRecord.value.id,
        accessToken.value,
        { ...payload, version_no: selectedRecord.value.version_no },
      );
      await refreshRecords();
    }
    syncDraft(selectedRecord.value);
    setFeedback("success", tp("successTitle"), tp("recordSaved"));
    markCleanState();
  } catch (error) {
    handleError(error);
  } finally {
    loading.action = false;
  }
}

function selectZone(zone) {
  editingZoneId.value = zone.id;
  Object.assign(zoneDraft, {
    zone_type_code: zone.zone_type_code,
    zone_code: zone.zone_code,
    label: zone.label,
    notes: zone.notes || "",
    version_no: zone.version_no,
  });
}

function selectCheckpoint(checkpoint) {
  editingCheckpointId.value = checkpoint.id;
  Object.assign(checkpointDraft, {
    sequence_no: checkpoint.sequence_no,
    checkpoint_code: checkpoint.checkpoint_code,
    label: checkpoint.label,
    latitude: checkpoint.latitude,
    longitude: checkpoint.longitude,
    scan_type_code: checkpoint.scan_type_code,
    expected_token_value: checkpoint.expected_token_value || "",
    minimum_dwell_seconds: checkpoint.minimum_dwell_seconds,
    notes: checkpoint.notes || "",
    version_no: checkpoint.version_no,
  });
}

async function submitZone() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !selectedRecord.value) return;
  try {
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      trade_fair_id: selectedRecord.value.id,
      zone_type_code: zoneDraft.zone_type_code,
      zone_code: zoneDraft.zone_code,
      label: zoneDraft.label,
      notes: zoneDraft.notes || null,
    };
    if (editingZoneId.value) {
      await updateTradeFairZone(
        resolvedTenantScopeId.value,
        selectedRecord.value.id,
        editingZoneId.value,
        accessToken.value,
        { ...payload, version_no: zoneDraft.version_no },
      );
    } else {
      await createTradeFairZone(resolvedTenantScopeId.value, selectedRecord.value.id, accessToken.value, payload);
    }
    tradeFairZones.value = await listTradeFairZones(resolvedTenantScopeId.value, selectedRecord.value.id, accessToken.value);
    resetZoneDraft();
    setFeedback("success", tp("successTitle"), tp("childSaved"));
  } catch (error) {
    handleError(error);
  }
}

async function submitCheckpoint() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !selectedRecord.value) return;
  try {
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      patrol_route_id: selectedRecord.value.id,
      sequence_no: Number(checkpointDraft.sequence_no),
      checkpoint_code: checkpointDraft.checkpoint_code,
      label: checkpointDraft.label,
      latitude: checkpointDraft.latitude,
      longitude: checkpointDraft.longitude,
      scan_type_code: checkpointDraft.scan_type_code,
      expected_token_value: checkpointDraft.expected_token_value || null,
      minimum_dwell_seconds: Number(checkpointDraft.minimum_dwell_seconds),
      notes: checkpointDraft.notes || null,
    };
    if (editingCheckpointId.value) {
      await updatePatrolCheckpoint(
        resolvedTenantScopeId.value,
        selectedRecord.value.id,
        editingCheckpointId.value,
        accessToken.value,
        { ...payload, version_no: checkpointDraft.version_no },
      );
    } else {
      await createPatrolCheckpoint(resolvedTenantScopeId.value, selectedRecord.value.id, accessToken.value, payload);
    }
    patrolCheckpoints.value = await listPatrolCheckpoints(resolvedTenantScopeId.value, selectedRecord.value.id, accessToken.value);
    resetCheckpointDraft();
    setFeedback("success", tp("successTitle"), tp("childSaved"));
  } catch (error) {
    handleError(error);
  }
}

function changeEntity() {
  if (!confirmDiscardChanges()) return;
  selectedRecord.value = null;
  selectedRecordId.value = "";
  isCreatingRecord.value = false;
  editorEntityKey.value = entityKey.value;
  resetDraft();
  resetZoneDraft();
  resetCheckpointDraft();
  resetImportTemplate();
  tradeFairZones.value = [];
  patrolCheckpoints.value = [];
  createTradeFairParentId.value = "";
  createPatrolRouteParentId.value = "";
  markCleanState();
  void refreshRecords();
}

function onImportSelected(event) {
  pendingImportFile.value = event.target.files?.[0] || null;
}

async function loadImportFile() {
  if (!pendingImportFile.value) return;
  importDraft.csv_text = await pendingImportFile.value.text();
}

async function runImportDryRun() {
  if (!resolvedTenantScopeId.value || !accessToken.value) return;
  try {
    importDryRunResult.value = await importPlanningDryRun(resolvedTenantScopeId.value, accessToken.value, {
      tenant_id: resolvedTenantScopeId.value,
      entity_key: entityKey.value,
      csv_content_base64: btoa(unescape(encodeURIComponent(importDraft.csv_text))),
    });
    setFeedback("success", tp("successTitle"), tp("importDryRunReady"));
  } catch (error) {
    handleError(error);
  }
}

async function runImportExecute() {
  if (!resolvedTenantScopeId.value || !accessToken.value) return;
  try {
    lastImportResult.value = await importPlanningExecute(resolvedTenantScopeId.value, accessToken.value, {
      tenant_id: resolvedTenantScopeId.value,
      entity_key: entityKey.value,
      csv_content_base64: btoa(unescape(encodeURIComponent(importDraft.csv_text))),
      continue_on_error: importDraft.continue_on_error,
    });
    await refreshRecords();
    setFeedback("success", tp("successTitle"), tp("importExecuted"));
  } catch (error) {
    handleError(error);
  }
}

function handleError(error) {
  const key = error instanceof PlanningAdminApiError ? mapPlanningApiMessage(error.messageKey) : "error";
  setFeedback("error", tp("errorTitle"), tp(key));
}

function applyPlanningRouteContext() {
  const { entity, customerId } = resolvePlanningRouteContext(route.query);
  let shouldRefresh = false;

  if (entity && entity !== entityKey.value) {
    entityKey.value = entity;
    selectedRecord.value = null;
    selectedRecordId.value = "";
    isCreatingRecord.value = false;
    resetDraft();
    resetZoneDraft();
    resetCheckpointDraft();
    resetImportTemplate();
    tradeFairZones.value = [];
    patrolCheckpoints.value = [];
    shouldRefresh = true;
  }

  if (customerId && customerId !== filters.customer_id) {
    filters.customer_id = customerId;
    shouldRefresh = true;
  }

  return shouldRefresh;
}

watch(
  () => editorEntityKey.value,
  (nextValue, previousValue) => {
    if (nextValue !== previousValue) {
      previousEditorEntityKey.value = previousValue;
    }
  },
);

watch(
  () => [resolvedTenantScopeId.value, accessToken.value, canRead.value],
  async () => {
    await refreshCustomerOptions();
    await refreshReferenceRecords();
    await refreshRecords();
  },
);

watch(
  () => [editorEntityKey.value, draft.customer_id],
  async () => {
    if (!usesAddressSelection()) {
      siteAddressOptions.value = [];
      siteAddressLookupError.value = "";
      siteAddressLookupLoading.value = false;
      draft.address_id = "";
      draft.meeting_address_id = "";
      return;
    }
    await refreshSiteAddressOptions();
  },
);

watch(
  () => route.query,
  async () => {
    if (applyPlanningRouteContext()) {
      await refreshRecords();
    }
  },
);

onMounted(async () => {
  resetImportTemplate();
  await refreshCustomerOptions();
  await refreshReferenceRecords();
  applyPlanningRouteContext();
  await refreshRecords();
  markCleanState();
});
</script>

<style scoped>
.planning-admin-page,
.planning-admin-grid,
.planning-admin-panel,
.planning-admin-form,
.planning-admin-form--structured,
.planning-admin-form-section,
.planning-admin-editor-intro,
.planning-admin-shared-context,
.planning-admin-filter-stack,
.planning-admin-tab-panel,
.planning-admin-list,
.planning-admin-feedback {
  display: grid;
  gap: 1rem;
}

.planning-admin-grid {
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
}

.planning-admin-panel,
.planning-admin-form-section,
.planning-admin-editor-intro,
.planning-admin-empty {
  min-width: 0;
}

.planning-admin-form--structured {
  gap: 0.9rem;
  align-content: start;
}

.planning-admin-editor-intro,
.planning-admin-form-section {
  padding: 1rem 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 18px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 76%, white 24%);
}

.planning-admin-form-section__header {
  display: grid;
  gap: 0.25rem;
}

.planning-admin-shared-context {
  gap: 0.75rem;
}

.planning-admin-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
}

.planning-admin-detail {
  align-content: start;
}

.planning-admin-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
}

.planning-admin-summary__card {
  padding: 0.9rem 1rem;
  border-radius: 16px;
  background: var(--sp-color-surface-page);
  border: 1px solid var(--sp-color-border-soft);
  display: grid;
  gap: 0.35rem;
}

.planning-admin-summary__card span {
  color: var(--sp-color-text-secondary);
  font-size: 0.85rem;
}

.planning-admin-filter-stack > * {
  min-width: 0;
}

.planning-admin-tab-panel {
  min-width: 0;
}

.planning-admin-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  cursor: pointer;
  text-align: left;
}

.planning-admin-row.selected {
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 40%, transparent);
}

.planning-admin-row__body {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  flex: 1 1 auto;
}

.planning-admin-row__body span,
.planning-admin-list-empty,
.planning-admin-empty,
.planning-admin-feedback span {
  color: var(--sp-color-text-secondary);
}

.planning-admin-checkbox {
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 12px;
  padding: 0.75rem 1rem;
}

.planning-admin-feedback {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  background: var(--sp-color-primary-muted);
  color: var(--sp-color-primary-strong);
}

.planning-admin-feedback[data-tone="error"] {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 45%, #ffb4a6);
  color: color-mix(in srgb, var(--sp-color-primary-strong) 60%, #6a1d00);
}

.planning-admin-feedback[data-tone="success"] {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 32%, #dcfce7);
  color: color-mix(in srgb, var(--sp-color-primary-strong) 65%, #14532d);
}

.planning-admin-form-grid--detail {
  display: grid;
  gap: 0.9rem 1rem;
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.planning-admin-form-grid--detail > .field-stack,
.planning-admin-form-grid--detail > .planning-customer-select {
  grid-column: span 3;
}

.planning-admin-form-grid--detail > .field-stack--half,
.planning-admin-form-grid--detail > .planning-customer-select.field-stack--half {
  grid-column: span 3;
}

.planning-admin-form-grid--detail > .field-stack--third {
  grid-column: span 2;
}

.planning-admin-site-primary-field {
  align-content: start;
}

.field-stack {
  display: grid;
  gap: 0.42rem;
  font-size: 0.9rem;
  min-width: 0;
}

.field-stack input,
.field-stack select,
.field-stack textarea,
.planning-admin-page :deep(.ant-select-selector) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
  border-radius: 14px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-card);
  color: var(--sp-color-text-primary);
  font: inherit;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background-color 0.18s ease;
}

.field-stack input,
.field-stack select,
.field-stack textarea {
  padding: 0.78rem 0.9rem;
}

.planning-admin-page :deep(.ant-select) {
  width: 100%;
}

.planning-admin-page :deep(.ant-select-selector) {
  min-height: 48px;
  padding: 0.35rem 0.9rem !important;
  align-items: center;
}

.planning-admin-page :deep(.ant-select-selection-search-input),
.planning-admin-page :deep(.ant-select-selection-item),
.planning-admin-page :deep(.ant-select-selection-placeholder) {
  font: inherit;
}

.planning-admin-page :deep(.ant-select-focused .ant-select-selector),
.planning-admin-page :deep(.ant-select-open .ant-select-selector),
.planning-admin-page :deep(.planning-admin-select.ant-select-status-error .ant-select-selector) {
  border-color: rgb(40 170 170 / 55%);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
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

.planning-admin-page :deep(.ant-select-disabled .ant-select-selector) {
  opacity: 0.72;
  cursor: not-allowed;
}

.planning-admin-checkbox {
  display: flex;
  gap: 0.7rem;
  align-items: center;
  min-width: 0;
  color: var(--sp-color-text-secondary);
}

.planning-admin-checkbox input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--sp-color-primary);
}

.planning-admin-checkbox--inline {
  grid-column: 1 / -1;
}

.field-stack--wide {
  grid-column: 1 / -1;
}

.planning-admin-map-action,
.planning-admin-form-actions {
  margin-top: 0.15rem;
}

.planning-admin-map-action {
  display: flex;
  justify-content: start;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

:global(.planning-admin-select-dropdown .ant-select-item-option-content) {
  white-space: normal;
}

.cta-button {
  background: var(--sp-color-primary);
  border: 0;
  border-radius: 999px;
  color: white;
  cursor: pointer;
  padding: 0.7rem 1rem;
  font: inherit;
}

.cta-button.cta-secondary {
  background: transparent;
  border: 1px solid var(--sp-color-border-soft);
  color: var(--sp-color-text-primary);
}

.cta-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (max-width: 960px) {
  .planning-admin-grid {
    grid-template-columns: 1fr;
  }

  .planning-admin-form-grid--detail {
    grid-template-columns: 1fr;
  }

  .planning-admin-form-grid--detail > .field-stack,
  .planning-admin-form-grid--detail > .planning-customer-select,
  .planning-admin-form-grid--detail > .field-stack--half,
  .planning-admin-form-grid--detail > .field-stack--third,
  .planning-admin-form-grid--detail > .field-stack--wide {
    grid-column: 1 / -1;
  }
}
</style>
