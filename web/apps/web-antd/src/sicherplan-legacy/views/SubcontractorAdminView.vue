<template>
  <section class="subcontractor-admin-page">
    <section v-if="!props.embedded" class="module-card subcontractor-admin-hero">
      <div>
        <p class="eyebrow">{{ t("sicherplan.subcontractors.eyebrow") }}</p>
        <h2>{{ t("sicherplan.subcontractors.title") }}</h2>
        <p class="subcontractor-admin-lead">{{ t("sicherplan.subcontractors.lead") }}</p>
        <div class="subcontractor-admin-meta">
          <span class="subcontractor-admin-meta__pill">{{ t("sicherplan.subcontractors.permission.read") }}: {{ canRead ? "on" : "off" }}</span>
          <span class="subcontractor-admin-meta__pill">{{ t("sicherplan.subcontractors.permission.write") }}: {{ canWrite ? "on" : "off" }}</span>
          <span class="subcontractor-admin-meta__pill">{{ t("sicherplan.subcontractors.permission.financeRead") }}: {{ canReadFinance ? "on" : "off" }}</span>
          <span class="subcontractor-admin-meta__pill">{{ t("sicherplan.subcontractors.permission.financeWrite") }}: {{ canWriteFinance ? "on" : "off" }}</span>
        </div>
      </div>

      <div class="module-card subcontractor-admin-scope">
        <label class="field-stack">
          <span>{{ t("sicherplan.subcontractors.scope.label") }}</span>
          <input v-model="tenantScopeInput" :disabled="!isPlatformAdmin" :placeholder="t('sicherplan.subcontractors.scope.placeholder')" />
        </label>
        <p class="field-help">{{ t("sicherplan.subcontractors.scope.help") }}</p>
        <div class="cta-row">
          <button class="cta-button" type="button" @click="rememberScope">{{ t("sicherplan.subcontractors.actions.rememberScope") }}</button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshSubcontractors">
            {{ t("sicherplan.subcontractors.actions.refresh") }}
          </button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="subcontractor-admin-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ t("sicherplan.subcontractors.actions.clearFeedback") }}</button>
    </section>

    <section v-if="!resolvedTenantScopeId" class="module-card subcontractor-admin-empty">
      <p class="eyebrow">{{ t("sicherplan.subcontractors.scope.missingTitle") }}</p>
      <h3>{{ t("sicherplan.subcontractors.scope.missingBody") }}</h3>
    </section>

    <section v-else-if="!canRead" class="module-card subcontractor-admin-empty">
      <p class="eyebrow">{{ t("sicherplan.subcontractors.permission.missingTitle") }}</p>
      <h3>{{ t("sicherplan.subcontractors.permission.missingBody") }}</h3>
    </section>

    <div v-else class="subcontractor-admin-grid">
      <section class="module-card subcontractor-admin-panel subcontractor-admin-list-panel" data-testid="subcontractor-list-section">
        <div class="subcontractor-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("sicherplan.subcontractors.list.eyebrow") }}</p>
            <h3>{{ t("sicherplan.subcontractors.list.title") }}</h3>
          </div>
          <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
        </div>

        <div class="subcontractor-admin-form-grid">
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.filters.search") }}</span>
            <input v-model="filters.search" :placeholder="t('sicherplan.subcontractors.filters.searchPlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.filters.status") }}</span>
            <select v-model="filters.lifecycle_status">
              <option value="">{{ t("sicherplan.subcontractors.filters.allStatuses") }}</option>
              <option value="active">{{ t("sicherplan.subcontractors.status.active") }}</option>
              <option value="inactive">{{ t("sicherplan.subcontractors.status.inactive") }}</option>
              <option value="archived">{{ t("sicherplan.subcontractors.status.archived") }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.fields.branchId") }}</span>
            <select v-if="branchOptions.length" v-model="filters.branch_id">
              <option value="">{{ t("sicherplan.subcontractors.filters.allBranches") }}</option>
              <option v-for="option in branchOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
            </select>
            <input v-else v-model="filters.branch_id" />
          </label>
          <label class="field-stack">
            <span>{{ t("sicherplan.subcontractors.fields.mandateId") }}</span>
            <select v-if="mandateOptions.length" v-model="filters.mandate_id">
              <option value="">{{ t("sicherplan.subcontractors.filters.allMandates") }}</option>
              <option v-for="option in filteredMandateOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
            </select>
            <input v-else v-model="filters.mandate_id" />
          </label>
        </div>

        <label class="subcontractor-admin-checkbox">
          <input v-model="filters.include_archived" type="checkbox" />
          <span>{{ t("sicherplan.subcontractors.filters.includeArchived") }}</span>
        </label>

        <div class="cta-row">
          <button class="cta-button" type="button" @click="refreshSubcontractors">{{ t("sicherplan.subcontractors.actions.search") }}</button>
          <button class="cta-button cta-secondary" type="button" data-testid="subcontractor-new" :disabled="!actionState.canCreate" @click="startCreateSubcontractor">
            {{ t("sicherplan.subcontractors.actions.newSubcontractor") }}
          </button>
        </div>

        <div v-if="subcontractors.length" class="subcontractor-admin-list">
          <button
            v-for="subcontractor in subcontractors"
            :key="subcontractor.id"
            type="button"
            class="subcontractor-admin-row"
            :class="{ selected: subcontractor.id === selectedSubcontractorId }"
            @click="selectSubcontractor(subcontractor.id)"
          >
            <div>
              <strong>{{ subcontractor.subcontractor_number }} · {{ subcontractor.display_name || subcontractor.legal_name }}</strong>
              <span>{{ subcontractor.managing_director_name || t("sicherplan.subcontractors.summary.none") }}</span>
            </div>
            <StatusBadge :status="subcontractor.status" />
          </button>
        </div>
        <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.list.empty") }}</p>
      </section>

      <section class="module-card subcontractor-admin-panel subcontractor-admin-detail" data-testid="subcontractor-detail-workspace">
        <div class="subcontractor-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("sicherplan.subcontractors.detail.eyebrow") }}</p>
            <h3>
              {{
                isCreatingSubcontractor
                  ? t("sicherplan.subcontractors.detail.newTitle")
                  : selectedSubcontractor?.display_name || selectedSubcontractor?.legal_name || t("sicherplan.subcontractors.detail.workspaceTitle")
              }}
            </h3>
            <p class="field-help">{{ t("sicherplan.subcontractors.detail.workspaceLead") }}</p>
          </div>
          <StatusBadge v-if="selectedSubcontractor && !isCreatingSubcontractor" :status="selectedSubcontractor.status" />
        </div>

        <nav class="subcontractor-admin-tabs" aria-label="Subcontractor detail sections" data-testid="subcontractor-detail-tabs">
          <button
            v-for="tab in subcontractorDetailTabs"
            :key="tab.id"
            type="button"
            class="subcontractor-admin-tab"
            :class="{ active: tab.id === activeDetailTab }"
            :data-testid="`subcontractor-tab-${tab.id}`"
            @click="activeDetailTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>

        <template v-if="hasDetailWorkspace">
          <section v-if="activeDetailTab === 'overview'" class="subcontractor-admin-tab-panel" data-testid="subcontractor-tab-panel-overview">
          <div v-if="selectedSubcontractor && !isCreatingSubcontractor" class="subcontractor-admin-summary">
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.summary.primaryContact") }}</span>
              <strong>{{ primaryContactSummary || t("sicherplan.subcontractors.summary.none") }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.summary.scope") }}</span>
              <strong>{{ scopeSummary || t("sicherplan.subcontractors.summary.none") }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.summary.portal") }}</span>
              <strong>{{ portalEnabledSummary }}</strong>
            </article>
            <article class="subcontractor-admin-summary__card">
              <span>{{ t("sicherplan.subcontractors.summary.coordinates") }}</span>
              <strong>{{ coordinateSummary || t("sicherplan.subcontractors.summary.none") }}</strong>
            </article>
          </div>

          <div v-if="selectedSubcontractor && !isCreatingSubcontractor" class="subcontractor-admin-lifecycle">
            <div>
              <strong>{{ t("sicherplan.subcontractors.lifecycle.title") }}</strong>
              <p class="field-help">{{ t("sicherplan.subcontractors.lifecycle.help") }}</p>
            </div>
            <div class="cta-row">
              <button v-if="actionState.canArchive" class="cta-button cta-secondary" type="button" @click="applyLifecycle('archived')">
                {{ t("sicherplan.subcontractors.actions.archive") }}
              </button>
              <button v-if="actionState.canReactivate" class="cta-button" type="button" @click="applyLifecycle('active')">
                {{ t("sicherplan.subcontractors.actions.reactivate") }}
              </button>
            </div>
          </div>

          <form class="subcontractor-admin-form" @submit.prevent="submitSubcontractor">
            <div class="subcontractor-admin-form-grid">
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.number") }}</span>
                <input v-model="subcontractorDraft.subcontractor_number" required data-testid="subcontractor-number" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.legalName") }}</span>
                <input v-model="subcontractorDraft.legal_name" required data-testid="subcontractor-legal-name" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.displayName") }}</span>
                <input v-model="subcontractorDraft.display_name" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.legalFormLookupId") }}</span>
                <select
                  v-model="subcontractorDraft.legal_form_lookup_id"
                  :disabled="!legalFormSelectEnabled"
                  data-testid="subcontractor-legal-form"
                >
                  <option value="">
                    {{
                      legalFormOptions.length
                        ? t("sicherplan.subcontractors.fields.legalFormPlaceholder")
                        : t("sicherplan.subcontractors.fields.legalFormUnavailablePlaceholder")
                    }}
                  </option>
                  <option v-for="option in legalFormOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                </select>
                <span v-if="legalFormHelpKey" class="field-help">{{ t(legalFormHelpKey) }}</span>
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.lifecycleStatus") }}</span>
                <select v-model="subcontractorDraft.status" :disabled="isCreatingSubcontractor || subcontractorDraft.status === 'archived'">
                  <option value="active">{{ t("sicherplan.subcontractors.status.active") }}</option>
                  <option value="inactive">{{ t("sicherplan.subcontractors.status.inactive") }}</option>
                  <option value="archived">{{ t("sicherplan.subcontractors.status.archived") }}</option>
                </select>
                <span class="field-help">{{ t("sicherplan.subcontractors.fields.lifecycleStatusHelp") }}</span>
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.statusLookupId") }}</span>
                <select v-if="subcontractorStatusOptions.length" v-model="subcontractorDraft.subcontractor_status_lookup_id">
                  <option value="">{{ t("sicherplan.subcontractors.fields.statusPlaceholder") }}</option>
                  <option v-for="option in subcontractorStatusOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                </select>
                <input v-else v-model="subcontractorDraft.subcontractor_status_lookup_id" />
                <span class="field-help">{{ t("sicherplan.subcontractors.fields.statusLookupHelp") }}</span>
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.managingDirectorName") }}</span>
                <input v-model="subcontractorDraft.managing_director_name" />
              </label>
              <div class="subcontractor-admin-address-row field-stack--wide">
                <label class="field-stack subcontractor-admin-address-row__field">
                  <span>{{ t("sicherplan.subcontractors.fields.addressId") }}</span>
                  <select v-if="addressOptions.length" v-model="subcontractorDraft.address_id" data-testid="subcontractor-primary-address">
                    <option value="">{{ t("sicherplan.subcontractors.fields.addressPlaceholder") }}</option>
                    <option v-for="option in addressOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                  </select>
                  <input v-else v-model="subcontractorDraft.address_id" data-testid="subcontractor-primary-address" />
                </label>
                <div class="subcontractor-admin-address-row__action">
                  <span class="subcontractor-admin-address-row__label">{{ t("sicherplan.subcontractors.fields.addressAction") }}</span>
                  <button
                    class="cta-button cta-secondary subcontractor-admin-address-row__button"
                    data-testid="subcontractor-create-address"
                    type="button"
                    :disabled="!actionState.canCreate && !actionState.canEdit"
                    @click="openAddressCreateModal"
                  >
                    {{ t("sicherplan.subcontractors.actions.createAddressOption") }}
                  </button>
                </div>
              </div>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.latitude") }}</span>
                <input v-model="subcontractorDraft.latitude" type="number" step="0.000001" />
              </label>
              <label class="field-stack">
                <span>{{ t("sicherplan.subcontractors.fields.longitude") }}</span>
                <input v-model="subcontractorDraft.longitude" type="number" step="0.000001" />
              </label>
              <div class="field-stack field-stack--wide">
                <div class="cta-row">
                  <button class="cta-button cta-secondary" data-testid="subcontractor-pick-location" type="button" @click="openLocationPicker">
                    {{ t("sicherplan.subcontractors.actions.pickLocationOnMap") }}
                  </button>
                </div>
              </div>
              <label class="field-stack field-stack--wide">
                <span>{{ t("sicherplan.subcontractors.fields.notes") }}</span>
                <textarea v-model="subcontractorDraft.notes" rows="4" />
              </label>
            </div>

            <div class="cta-row">
              <button class="cta-button" type="submit" data-testid="subcontractor-save" :disabled="!actionState.canCreate && !actionState.canEdit && !isCreatingSubcontractor">
                {{ isCreatingSubcontractor ? t("sicherplan.subcontractors.actions.createSubcontractor") : t("sicherplan.subcontractors.actions.saveSubcontractor") }}
              </button>
              <button class="cta-button cta-secondary" type="button" @click="resetSubcontractorDraft">
                {{ t("sicherplan.subcontractors.actions.reset") }}
              </button>
            </div>
          </form>
          </section>

          <section
            v-if="selectedSubcontractor && !isCreatingSubcontractor && activeDetailTab === 'contacts'"
            class="subcontractor-admin-section"
            data-testid="subcontractor-tab-panel-contacts"
          >
            <div class="subcontractor-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("sicherplan.subcontractors.contacts.eyebrow") }}</p>
                <h3>{{ t("sicherplan.subcontractors.contacts.title") }}</h3>
              </div>
            </div>
            <div v-if="contacts.length" class="subcontractor-admin-list">
              <button
                v-for="contact in contacts"
                :key="contact.id"
                type="button"
                class="subcontractor-admin-row"
                :class="{ selected: contact.id === selectedContactId }"
                @click="selectContact(contact.id)"
              >
                <div>
                  <strong>{{ contact.full_name }}</strong>
                  <span>{{ [contact.email, contact.mobile].filter(Boolean).join(' · ') || t("sicherplan.subcontractors.summary.none") }}</span>
                </div>
                <StatusBadge :status="contact.portal_enabled ? 'active' : 'inactive'" />
              </button>
            </div>
            <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.contacts.empty") }}</p>

            <form class="subcontractor-admin-form" @submit.prevent="submitContact">
              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.contactName") }}</span>
                  <input v-model="contactDraft.full_name" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.contactTitle") }}</span>
                  <input v-model="contactDraft.title" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.contactFunction") }}</span>
                  <input v-model="contactDraft.function_label" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.contactEmail") }}</span>
                  <input v-model="contactDraft.email" type="email" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.contactPhone") }}</span>
                  <input v-model="contactDraft.phone" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.contactMobile") }}</span>
                  <input v-model="contactDraft.mobile" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.contactUserId") }}</span>
                  <select v-if="contactUserOptions.length" v-model="contactDraft.user_id">
                    <option value="">{{ t("sicherplan.subcontractors.fields.contactUserPlaceholder") }}</option>
                    <option v-for="option in contactUserOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                  </select>
                  <input v-else v-model="contactDraft.user_id" />
                  <span class="field-help">{{ t("sicherplan.subcontractors.fields.contactUserHelp") }}</span>
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.fields.contactNotes") }}</span>
                  <textarea v-model="contactDraft.notes" rows="3" />
                </label>
              </div>

              <div class="subcontractor-admin-toggle-row">
                <label class="subcontractor-admin-checkbox">
                  <input v-model="contactDraft.is_primary_contact" type="checkbox" />
                  <span>{{ t("sicherplan.subcontractors.fields.primaryContact") }}</span>
                </label>
                <label class="subcontractor-admin-checkbox">
                  <input v-model="contactDraft.portal_enabled" type="checkbox" />
                  <span>{{ t("sicherplan.subcontractors.fields.portalEnabled") }}</span>
                </label>
              </div>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canManageContacts">
                  {{ selectedContactId ? t("sicherplan.subcontractors.actions.saveContact") : t("sicherplan.subcontractors.actions.createContact") }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="resetContactDraft">
                  {{ t("sicherplan.subcontractors.actions.resetContact") }}
                </button>
              </div>
            </form>
          </section>

          <section
            v-if="selectedSubcontractor && !isCreatingSubcontractor && activeDetailTab === 'scope_release'"
            class="subcontractor-admin-section"
            data-testid="subcontractor-tab-panel-scope-release"
          >
            <div class="subcontractor-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("sicherplan.subcontractors.scopeSection.eyebrow") }}</p>
                <h3>{{ t("sicherplan.subcontractors.scopeSection.title") }}</h3>
              </div>
            </div>
            <p class="field-help">{{ t("sicherplan.subcontractors.scopeSection.futureSiteNote") }}</p>
            <div v-if="scopes.length" class="subcontractor-admin-list">
              <button
                v-for="scope in scopes"
                :key="scope.id"
                type="button"
                class="subcontractor-admin-row"
                :class="{ selected: scope.id === selectedScopeId }"
                @click="selectScope(scope.id)"
              >
                <div>
                  <strong>{{ formatScopeLabel(scope.branch_id, scope.mandate_id) }}</strong>
                  <span>{{ scope.valid_from }}<template v-if="scope.valid_to"> → {{ scope.valid_to }}</template></span>
                </div>
                <StatusBadge :status="scope.status" />
              </button>
            </div>
            <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.scopeSection.empty") }}</p>

            <form class="subcontractor-admin-form" @submit.prevent="submitScope">
              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.branchId") }}</span>
                  <select
                    v-model="scopeDraft.branch_id"
                    :disabled="!scopeBranchSelectEnabled"
                    data-testid="subcontractor-scope-branch"
                    required
                  >
                    <option value="">
                      {{ t(scopeBranchPlaceholderKey) }}
                    </option>
                    <option v-for="option in branchOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.mandateId") }}</span>
                  <select
                    v-model="scopeDraft.mandate_id"
                    :disabled="!scopeMandateSelectEnabled"
                    data-testid="subcontractor-scope-mandate"
                  >
                    <option value="">
                      {{ t(scopeMandatePlaceholderKey) }}
                    </option>
                    <option v-for="option in scopeMandateOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.validFrom") }}</span>
                  <input v-model="scopeDraft.valid_from" type="date" required />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.validTo") }}</span>
                  <input v-model="scopeDraft.valid_to" type="date" />
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.fields.scopeNotes") }}</span>
                  <textarea v-model="scopeDraft.notes" rows="3" />
                </label>
              </div>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canManageScopes">
                  {{ selectedScopeId ? t("sicherplan.subcontractors.actions.saveScope") : t("sicherplan.subcontractors.actions.createScope") }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="resetScopeDraft">
                  {{ t("sicherplan.subcontractors.actions.resetScope") }}
                </button>
              </div>
            </form>
          </section>

          <section
            v-if="selectedSubcontractor && !isCreatingSubcontractor && activeDetailTab === 'billing'"
            class="subcontractor-admin-section"
            data-testid="subcontractor-tab-panel-billing"
          >
            <div class="subcontractor-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("sicherplan.subcontractors.finance.eyebrow") }}</p>
                <h3>{{ t("sicherplan.subcontractors.finance.title") }}</h3>
              </div>
            </div>

            <div v-if="!canReadFinance" class="subcontractor-admin-empty-state">
              <p>{{ t("sicherplan.subcontractors.permission.missingBody") }}</p>
            </div>

            <form v-else class="subcontractor-admin-form" @submit.prevent="submitFinanceProfile">
              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.invoiceEmail") }}</span>
                  <input v-model="financeDraft.invoice_email" type="email" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.paymentTermsDays") }}</span>
                  <input v-model="financeDraft.payment_terms_days" type="number" min="0" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.paymentTermsNote") }}</span>
                  <input v-model="financeDraft.payment_terms_note" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.taxNumber") }}</span>
                  <input v-model="financeDraft.tax_number" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.vatId") }}</span>
                  <input v-model="financeDraft.vat_id" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.bankAccountHolder") }}</span>
                  <input v-model="financeDraft.bank_account_holder" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.bankIban") }}</span>
                  <input v-model="financeDraft.bank_iban" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.bankBic") }}</span>
                  <input v-model="financeDraft.bank_bic" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.bankName") }}</span>
                  <input v-model="financeDraft.bank_name" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.invoiceDeliveryMethodLookupId") }}</span>
                  <select v-if="invoiceDeliveryMethodOptions.length" v-model="financeDraft.invoice_delivery_method_lookup_id">
                    <option value="">{{ t("sicherplan.subcontractors.fields.invoiceDeliveryMethodPlaceholder") }}</option>
                    <option v-for="option in invoiceDeliveryMethodOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                  </select>
                  <input v-else v-model="financeDraft.invoice_delivery_method_lookup_id" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.invoiceStatusModeLookupId") }}</span>
                  <select v-if="invoiceStatusModeOptions.length" v-model="financeDraft.invoice_status_mode_lookup_id">
                    <option value="">{{ t("sicherplan.subcontractors.fields.invoiceStatusModePlaceholder") }}</option>
                    <option v-for="option in invoiceStatusModeOptionsWithDraft" :key="option.id" :value="option.id">{{ option.label }}</option>
                  </select>
                  <input v-else v-model="financeDraft.invoice_status_mode_lookup_id" />
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.fields.billingNote") }}</span>
                  <textarea v-model="financeDraft.billing_note" rows="3" />
                </label>
              </div>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canManageFinance">
                  {{ financeDraft.id ? t("sicherplan.subcontractors.actions.saveFinance") : t("sicherplan.subcontractors.actions.createFinance") }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="resetFinanceDraft">
                  {{ t("sicherplan.subcontractors.actions.resetFinance") }}
                </button>
              </div>
            </form>
          </section>

          <section
            v-if="selectedSubcontractor && !isCreatingSubcontractor && activeDetailTab === 'history'"
            class="subcontractor-admin-section"
            data-testid="subcontractor-tab-panel-history"
          >
            <div class="subcontractor-admin-panel__header">
              <div>
                <p class="eyebrow">{{ t("sicherplan.subcontractors.history.eyebrow") }}</p>
                <h3>{{ t("sicherplan.subcontractors.history.title") }}</h3>
              </div>
            </div>

            <div v-if="historyEntries.length" class="subcontractor-admin-list">
              <button
                v-for="entry in historyEntries"
                :key="entry.id"
                type="button"
                class="subcontractor-admin-row subcontractor-admin-row--history"
                :class="{ selected: entry.id === selectedHistoryEntryId }"
                @click="selectHistoryEntry(entry.id)"
              >
                <div>
                  <strong>{{ entry.title }}</strong>
                  <span>{{ formatHistoryMeta(entry) }}</span>
                </div>
                <StatusBadge :status="entry.entry_type === 'lifecycle_event' ? 'inactive' : 'active'" />
              </button>
            </div>
            <p v-else class="subcontractor-admin-list-empty">{{ t("sicherplan.subcontractors.history.empty") }}</p>

            <article v-if="selectedHistoryEntry" class="subcontractor-admin-history-card">
              <div class="subcontractor-admin-history-card__header">
                <div>
                  <p class="eyebrow">{{ historyEntryTypeLabel(selectedHistoryEntry.entry_type) }}</p>
                  <h4>{{ selectedHistoryEntry.title }}</h4>
                </div>
                <span>{{ formatDateTime(selectedHistoryEntry.occurred_at) }}</span>
              </div>
              <p>{{ selectedHistoryEntry.body }}</p>
              <div v-if="selectedHistoryEntry.attachments.length" class="subcontractor-admin-history-attachments">
                <button
                  v-for="attachment in selectedHistoryEntry.attachments"
                  :key="attachment.document_id"
                  type="button"
                  class="cta-button cta-secondary"
                  @click="downloadHistoryAttachment(attachment)"
                >
                  {{ attachment.file_name || attachment.title }}
                </button>
              </div>
            </article>

            <form class="subcontractor-admin-form" @submit.prevent="submitHistoryEntry">
              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.historyType") }}</span>
                  <select v-model="historyDraft.entry_type">
                    <option value="processing_note">{{ t("sicherplan.subcontractors.history.types.processing_note") }}</option>
                    <option value="invoice_discussion">{{ t("sicherplan.subcontractors.history.types.invoice_discussion") }}</option>
                    <option value="manual_commentary">{{ t("sicherplan.subcontractors.history.types.manual_commentary") }}</option>
                    <option value="portal_enablement_note">{{ t("sicherplan.subcontractors.history.types.portal_enablement_note") }}</option>
                    <option value="lifecycle_event">{{ t("sicherplan.subcontractors.history.types.lifecycle_event") }}</option>
                  </select>
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.historyOccurredAt") }}</span>
                  <input v-model="historyDraft.occurred_at" type="datetime-local" />
                </label>
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.historyRelatedContact") }}</span>
                  <select v-model="historyDraft.related_contact_id">
                    <option value="">{{ t("sicherplan.subcontractors.history.noRelatedContact") }}</option>
                    <option v-for="contact in contacts" :key="contact.id" :value="contact.id">{{ contact.full_name }}</option>
                  </select>
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.fields.historyTitle") }}</span>
                  <input v-model="historyDraft.title" required />
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.fields.historyBody") }}</span>
                  <textarea v-model="historyDraft.body" rows="4" required />
                </label>
              </div>

              <div class="subcontractor-admin-form-grid">
                <label class="field-stack">
                  <span>{{ t("sicherplan.subcontractors.fields.attachmentLabel") }}</span>
                  <input v-model="historyAttachmentDraft.label" />
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("sicherplan.subcontractors.fields.attachmentFile") }}</span>
                  <input type="file" @change="onHistoryAttachmentSelected" />
                </label>
              </div>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canManageHistory">
                  {{ t("sicherplan.subcontractors.actions.createHistoryEntry") }}
                </button>
                <button
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!actionState.canManageHistory || !selectedHistoryEntryId || !historyAttachmentFile"
                  @click="attachHistoryDocument"
                >
                  {{ t("sicherplan.subcontractors.actions.attachHistoryDocument") }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="resetHistoryDraft">
                  {{ t("sicherplan.subcontractors.actions.resetHistory") }}
                </button>
              </div>
            </form>
          </section>

          <SubcontractorWorkforcePanel
            v-if="selectedSubcontractor && !isCreatingSubcontractor && activeDetailTab === 'workforce' && resolvedTenantScopeId && accessToken"
            :tenant-id="resolvedTenantScopeId"
            :subcontractor-id="selectedSubcontractor.id"
            :access-token="accessToken"
            :can-read="canRead"
            :can-write="canWrite"
          />
        </template>

        <section v-else class="subcontractor-admin-empty-state">
          <p class="eyebrow">{{ t("sicherplan.subcontractors.detail.emptyEyebrow") }}</p>
          <h3>{{ t("sicherplan.subcontractors.detail.emptyBody") }}</h3>
        </section>
      </section>
    </div>

    <section v-if="addressCreateModalOpen" class="subcontractor-admin-modal-backdrop" data-testid="subcontractor-address-modal">
      <div class="module-card subcontractor-admin-modal">
        <div class="subcontractor-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("sicherplan.subcontractors.addressModal.eyebrow") }}</p>
            <h3>{{ t("sicherplan.subcontractors.addressModal.title") }}</h3>
          </div>
        </div>
        <form class="subcontractor-admin-form" @submit.prevent="submitAddressOption">
          <div class="subcontractor-admin-form-grid">
            <label class="field-stack">
              <span>{{ t("sicherplan.subcontractors.addressModal.street1") }}</span>
              <input v-model="addressDraft.street_line_1" required data-testid="subcontractor-address-street1" />
            </label>
            <label class="field-stack">
              <span>{{ t("sicherplan.subcontractors.addressModal.street2") }}</span>
              <input v-model="addressDraft.street_line_2" data-testid="subcontractor-address-street2" />
            </label>
            <label class="field-stack">
              <span>{{ t("sicherplan.subcontractors.addressModal.postalCode") }}</span>
              <input v-model="addressDraft.postal_code" required data-testid="subcontractor-address-postal" />
            </label>
            <label class="field-stack">
              <span>{{ t("sicherplan.subcontractors.addressModal.city") }}</span>
              <input v-model="addressDraft.city" required data-testid="subcontractor-address-city" />
            </label>
            <label class="field-stack">
              <span>{{ t("sicherplan.subcontractors.addressModal.state") }}</span>
              <input v-model="addressDraft.state" data-testid="subcontractor-address-state" />
            </label>
            <label class="field-stack">
              <span>{{ t("sicherplan.subcontractors.addressModal.countryCode") }}</span>
              <input v-model="addressDraft.country_code" maxlength="2" required data-testid="subcontractor-address-country" />
            </label>
          </div>
          <div class="cta-row">
            <button class="cta-button" type="submit" data-testid="subcontractor-address-save">{{ t("sicherplan.subcontractors.actions.saveAddressOption") }}</button>
            <button class="cta-button cta-secondary" type="button" data-testid="subcontractor-address-cancel" @click="closeAddressCreateModal">
              {{ t("sicherplan.subcontractors.actions.cancelAddressOption") }}
            </button>
          </div>
        </form>
      </div>
    </section>

    <PlanningLocationPickerModal
      v-model:open="locationPickerOpen"
      :latitude="subcontractorDraft.latitude"
      :longitude="subcontractorDraft.longitude"
      :initial-center="locationPickerStartPoint"
      :start-point-label="locationPickerStartPoint.label"
      :title="t('sicherplan.subcontractors.mapPicker.title')"
      :confirm-text="t('sicherplan.subcontractors.mapPicker.confirm')"
      :cancel-text="t('sicherplan.subcontractors.mapPicker.cancel')"
      :helper-text="t('sicherplan.subcontractors.mapPicker.help')"
      :latitude-label="t('sicherplan.subcontractors.fields.latitude')"
      :longitude-label="t('sicherplan.subcontractors.fields.longitude')"
      :load-error-text="t('sicherplan.subcontractors.mapPicker.loadError')"
      @confirm="applyPickedLocation"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { useI18n } from "@vben/locales";

import StatusBadge from "@/components/StatusBadge.vue";
import PlanningLocationPickerModal from "@/components/planning/PlanningLocationPickerModal.vue";
import SubcontractorWorkforcePanel from "@/components/SubcontractorWorkforcePanel.vue";
import {
  listBranches,
  listLookupValues,
  listMandates,
  type BranchRead,
  type LookupValueRead,
  type MandateRead,
} from "@/api/coreAdmin";
import { useAuthStore } from "@/stores/auth";
import {
  addPlatformDocumentVersion,
  archiveSubcontractor,
  createSubcontractor,
  createSubcontractorAddressOption,
  createSubcontractorContact,
  createSubcontractorHistoryEntry,
  createSubcontractorScope,
  createPlatformDocument,
  downloadSubcontractorDocument,
  getSubcontractor,
  getSubcontractorFinanceProfile,
  getSubcontractorReferenceData,
  linkSubcontractorHistoryAttachment,
  listSubcontractorAddressOptions,
  listSubcontractorContactUserOptions,
  listSubcontractorContacts,
  listSubcontractorHistory,
  listSubcontractors,
  listSubcontractorScopes,
  patchSubcontractorFinanceProfile,
  putSubcontractorFinanceProfile,
  reactivateSubcontractor,
  type LifecycleStatus,
  type SubcontractorContactUserOptionRead,
  type SubcontractorContactRead,
  type SubcontractorFinanceProfileRead,
  type SubcontractorHistoryAttachmentRead,
  type SubcontractorHistoryEntryRead,
  type SubcontractorListItem,
  type SubcontractorReferenceDataRead,
  type SubcontractorRead,
  type SubcontractorScopeRead,
  SubcontractorAdminApiError,
  updateSubcontractor,
  updateSubcontractorContact,
  updateSubcontractorScope,
} from "@/api/subcontractors";
import {
  buildSubcontractorLifecyclePayload,
  deriveSubcontractorActionState,
  hasPortalEnabledContact,
  hasSubcontractorPermission,
  mapSubcontractorApiMessage,
  summarizePrimaryContact,
  summarizeScopeRows,
} from "@/features/subcontractors/subcontractorAdmin.helpers.js";
import { resolveInitialMapCenter } from "@/features/planning/planningAdmin.helpers.js";

const { t } = useI18n();
const authStore = useAuthStore();
const props = withDefaults(
  defineProps<{
    embedded?: boolean;
  }>(),
  {
    embedded: false,
  },
);

const filters = reactive({
  search: "",
  lifecycle_status: "",
  branch_id: "",
  mandate_id: "",
  include_archived: false,
});

const feedback = reactive({
  tone: "neutral",
  title: "",
  message: "",
});

const loading = reactive({
  list: false,
  detail: false,
  saving: false,
});

const structureOptionState = reactive({
  loading: false,
  error: false,
});
const financeProfileState = reactive({
  loading: false,
  loadedSubcontractorId: "",
});

const subcontractors = ref<SubcontractorListItem[]>([]);
const selectedSubcontractor = ref<SubcontractorRead | null>(null);
const selectedSubcontractorId = ref("");
const contacts = ref<SubcontractorContactRead[]>([]);
const scopes = ref<SubcontractorScopeRead[]>([]);
const historyEntries = ref<SubcontractorHistoryEntryRead[]>([]);
const selectedContactId = ref("");
const selectedScopeId = ref("");
const selectedHistoryEntryId = ref("");
const isCreatingSubcontractor = ref(false);
const activeDetailTab = ref("overview");
const tenantScopeInput = ref(authStore.tenantScopeId);
const historyAttachmentFile = ref<File | null>(null);
const addressCreateModalOpen = ref(false);
const locationPickerOpen = ref(false);

const subcontractorDraft = reactive({
  subcontractor_number: "",
  legal_name: "",
  display_name: "",
  legal_form_lookup_id: "",
  status: "active",
  subcontractor_status_lookup_id: "",
  managing_director_name: "",
  address_id: "",
  latitude: "",
  longitude: "",
  notes: "",
  version_no: 0,
});

const contactDraft = reactive({
  full_name: "",
  title: "",
  function_label: "",
  email: "",
  phone: "",
  mobile: "",
  is_primary_contact: false,
  portal_enabled: false,
  user_id: "",
  notes: "",
  version_no: 0,
});

const addressDraft = reactive({
  street_line_1: "",
  street_line_2: "",
  postal_code: "",
  city: "",
  state: "",
  country_code: "DE",
});

const scopeDraft = reactive({
  branch_id: "",
  mandate_id: "",
  valid_from: "",
  valid_to: "",
  notes: "",
  version_no: 0,
});

const financeDraft = reactive({
  id: "",
  invoice_email: "",
  payment_terms_days: "",
  payment_terms_note: "",
  tax_number: "",
  vat_id: "",
  bank_account_holder: "",
  bank_iban: "",
  bank_bic: "",
  bank_name: "",
  invoice_delivery_method_lookup_id: "",
  invoice_status_mode_lookup_id: "",
  billing_note: "",
  version_no: 0,
});

const historyDraft = reactive({
  entry_type: "processing_note",
  title: "",
  body: "",
  occurred_at: "",
  related_contact_id: "",
});

const historyAttachmentDraft = reactive({
  label: "",
});

const locationPickerStartPoint = ref({
  lat: 51.662973,
  lng: 8.174013,
  zoom: 11,
  label: "",
});

const activeRole = computed(() => authStore.effectiveRole);
const accessToken = computed(() => authStore.accessToken);
const sessionTenantId = computed(() => authStore.sessionUser?.tenant_id ?? "");
const isPlatformAdmin = computed(() => activeRole.value === "platform_admin");
const resolvedTenantScopeId = computed(() => {
  if (isPlatformAdmin.value) {
    return authStore.tenantScopeId || tenantScopeInput.value.trim();
  }
  return sessionTenantId.value || authStore.tenantScopeId;
});

const canRead = computed(() => hasSubcontractorPermission(activeRole.value, "subcontractors.company.read"));
const canWrite = computed(() => hasSubcontractorPermission(activeRole.value, "subcontractors.company.write"));
const canReadFinance = computed(() => hasSubcontractorPermission(activeRole.value, "subcontractors.finance.read"));
const canWriteFinance = computed(() => hasSubcontractorPermission(activeRole.value, "subcontractors.finance.write"));
const actorTenantId = computed(() => {
  if (activeRole.value === "tenant_admin") {
    return sessionTenantId.value || authStore.tenantScopeId || null;
  }
  return authStore.tenantScopeId || null;
});
const actionState = computed(() => deriveSubcontractorActionState(activeRole.value, selectedSubcontractor.value));
const hasDetailWorkspace = computed(() => isCreatingSubcontractor.value || !!selectedSubcontractor.value);
const detailTabLabelKeys = {
  overview: "sicherplan.subcontractors.tabs.overview",
  contacts: "sicherplan.subcontractors.tabs.contacts",
  scope_release: "sicherplan.subcontractors.tabs.scopeRelease",
  billing: "sicherplan.subcontractors.tabs.billing",
  history: "sicherplan.subcontractors.tabs.history",
  workforce: "sicherplan.subcontractors.tabs.workforce",
} as const;
const subcontractorDetailTabs = computed(() =>
  Object.entries(detailTabLabelKeys).map(([id, labelKey]) => ({
    id,
    label: t(labelKey as never),
  })),
);
const selectedHistoryEntry = computed(() =>
  historyEntries.value.find((entry) => entry.id === selectedHistoryEntryId.value) ?? null,
);

const primaryContactSummary = computed(() => summarizePrimaryContact(contacts.value));
const scopeSummary = computed(() => summarizeScopeRows(scopes.value));
const portalEnabledSummary = computed(() =>
  hasPortalEnabledContact(contacts.value)
    ? t("sicherplan.subcontractors.summary.portalEnabled")
    : t("sicherplan.subcontractors.summary.portalDisabled"),
);
const coordinateSummary = computed(() => {
  if (!selectedSubcontractor.value?.latitude || !selectedSubcontractor.value?.longitude) {
    return "";
  }
  return `${selectedSubcontractor.value.latitude}, ${selectedSubcontractor.value.longitude}`;
});
const branches = ref<BranchRead[]>([]);
const mandates = ref<MandateRead[]>([]);
const subcontractorReferenceData = ref<SubcontractorReferenceDataRead | null>(null);
const legalFormReferenceLoadFailed = ref(false);
const subcontractorStatusLookups = ref<LookupValueRead[]>([]);
const invoiceDeliveryMethodLookups = ref<LookupValueRead[]>([]);
const invoiceStatusModeLookups = ref<LookupValueRead[]>([]);
const contactUserOptionRows = ref<SubcontractorContactUserOptionRead[]>([]);
const addressOptionRows = ref<Array<NonNullable<SubcontractorRead["address"]>>>([]);
const pendingAddressOptionRows = ref<Array<NonNullable<SubcontractorRead["address"]>>>([]);

const branchOptions = computed(() =>
  branches.value.map((row) => ({
    id: row.id,
    label: [row.code, row.name].filter(Boolean).join(" · "),
  })),
);
const mandateOptions = computed(() =>
  mandates.value.map((row) => ({
    id: row.id,
    branchId: row.branch_id,
    label: [row.code, row.name].filter(Boolean).join(" · "),
  })),
);
const filteredMandateOptions = computed(() => {
  if (!filters.branch_id) {
    return mandateOptions.value;
  }
  return mandateOptions.value.filter((row) => row.branchId === filters.branch_id);
});
const scopeMandateOptions = computed(() => {
  if (!scopeDraft.branch_id) {
    return mandateOptions.value;
  }
  return mandateOptions.value.filter((row) => row.branchId === scopeDraft.branch_id);
});

function mapLookupOptions(rows: LookupValueRead[]) {
  return rows.map((row) => ({
    id: row.id,
    label: row.label || row.code,
  }));
}

function withCurrentOption(options: Array<{ id: string; label: string }>, currentValue: string) {
  const normalized = currentValue.trim();
  if (!normalized || options.some((option) => option.id === normalized)) {
    return options;
  }
  return [...options, { id: normalized, label: normalized }];
}

const legalFormOptions = computed(() =>
  (subcontractorReferenceData.value?.legal_forms ?? []).map((row) => ({
    id: row.id,
    label: row.label || row.code,
  })),
);
const subcontractorStatusOptions = computed(() => mapLookupOptions(subcontractorStatusLookups.value));
const invoiceDeliveryMethodOptions = computed(() => mapLookupOptions(invoiceDeliveryMethodLookups.value));
const invoiceStatusModeOptions = computed(() => mapLookupOptions(invoiceStatusModeLookups.value));
const contactUserOptions = computed(() =>
  contactUserOptionRows.value.map((row) => ({
    id: row.id,
    label: [row.full_name, row.username, row.email].filter(Boolean).join(" · "),
  })),
);
const addressOptions = computed(() =>
  [...addressOptionRows.value, ...pendingAddressOptionRows.value].map((row) => ({
    id: row.id,
    label: formatAddressOptionLabel(row),
  })),
);
const legalFormOptionsWithDraft = computed(() => withCurrentOption(legalFormOptions.value, subcontractorDraft.legal_form_lookup_id));
const subcontractorStatusOptionsWithDraft = computed(() =>
  withCurrentOption(subcontractorStatusOptions.value, subcontractorDraft.subcontractor_status_lookup_id),
);
const invoiceDeliveryMethodOptionsWithDraft = computed(() =>
  withCurrentOption(invoiceDeliveryMethodOptions.value, financeDraft.invoice_delivery_method_lookup_id),
);
const invoiceStatusModeOptionsWithDraft = computed(() =>
  withCurrentOption(invoiceStatusModeOptions.value, financeDraft.invoice_status_mode_lookup_id),
);
const contactUserOptionsWithDraft = computed(() => withCurrentOption(contactUserOptions.value, contactDraft.user_id));
const addressOptionsWithDraft = computed(() => withCurrentOption(addressOptions.value, subcontractorDraft.address_id));
const scopeMandateOptionsWithDraft = computed(() => withCurrentOption(scopeMandateOptions.value, scopeDraft.mandate_id));
const scopeBranchSelectEnabled = computed(() =>
  branchOptions.value.length > 0 || !!scopeDraft.branch_id.trim(),
);
const scopeMandateSelectEnabled = computed(() =>
  scopeMandateOptions.value.length > 0 || !!scopeDraft.mandate_id.trim(),
);
const scopeBranchPlaceholderKey = computed(() => {
  if (structureOptionState.loading) {
    return "sicherplan.subcontractors.fields.branchLoadingPlaceholder";
  }
  if (structureOptionState.error) {
    return "sicherplan.subcontractors.fields.branchUnavailablePlaceholder";
  }
  if (branchOptions.value.length === 0) {
    return "sicherplan.subcontractors.fields.branchEmptyPlaceholder";
  }
  return "sicherplan.subcontractors.fields.branchPlaceholder";
});
const scopeMandatePlaceholderKey = computed(() => {
  if (structureOptionState.loading) {
    return "sicherplan.subcontractors.fields.mandateLoadingPlaceholder";
  }
  if (structureOptionState.error) {
    return "sicherplan.subcontractors.fields.mandateUnavailablePlaceholder";
  }
  if (scopeDraft.branch_id && scopeMandateOptions.value.length === 0 && !scopeDraft.mandate_id.trim()) {
    return "sicherplan.subcontractors.fields.mandateEmptyForBranchPlaceholder";
  }
  if (mandates.value.length === 0 && !scopeDraft.mandate_id.trim()) {
    return "sicherplan.subcontractors.fields.mandateEmptyPlaceholder";
  }
  return "sicherplan.subcontractors.fields.mandatePlaceholder";
});
const legalFormSelectEnabled = computed(() =>
  legalFormOptions.value.length > 0 || !!subcontractorDraft.legal_form_lookup_id.trim(),
);
const legalFormHelpKey = computed(() => {
  if (legalFormReferenceLoadFailed.value) {
    return "sicherplan.subcontractors.fields.legalFormHelpUnavailable";
  }
  if (
    subcontractorDraft.legal_form_lookup_id.trim()
    && !legalFormOptions.value.some((option) => option.id === subcontractorDraft.legal_form_lookup_id.trim())
  ) {
    return "sicherplan.subcontractors.fields.legalFormHelpLegacy";
  }
  return "";
});

function clearFeedback() {
  feedback.tone = "neutral";
  feedback.title = "";
  feedback.message = "";
}

function setFeedback(tone: "success" | "error", messageKey: string) {
  feedback.tone = tone;
  feedback.title = t(
    tone === "success"
      ? "sicherplan.subcontractors.feedback.titleSuccess"
      : "sicherplan.subcontractors.feedback.titleError",
  );
  feedback.message = t(messageKey);
}

function rememberScope() {
  authStore.setTenantScopeId(tenantScopeInput.value.trim());
}

function serializeNullable(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function serializeDecimal(value: string) {
  const trimmed = value.trim();
  return trimmed ? Number(trimmed) : null;
}

function formatAddressOptionLabel(address: NonNullable<SubcontractorRead["address"]>) {
  return [address.street_line_1, address.postal_code, address.city, address.country_code].filter(Boolean).join(", ");
}

function createPendingAddressOptionId() {
  return `pending-address-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function findPendingAddressOption(addressId: string) {
  const normalized = addressId.trim();
  if (!normalized) {
    return null;
  }
  return pendingAddressOptionRows.value.find((row) => row.id === normalized) ?? null;
}

function resetSubcontractorDraft() {
  subcontractorDraft.subcontractor_number = selectedSubcontractor.value?.subcontractor_number ?? "";
  subcontractorDraft.legal_name = selectedSubcontractor.value?.legal_name ?? "";
  subcontractorDraft.display_name = selectedSubcontractor.value?.display_name ?? "";
  subcontractorDraft.legal_form_lookup_id = selectedSubcontractor.value?.legal_form_lookup_id ?? "";
  subcontractorDraft.status = selectedSubcontractor.value?.status ?? "active";
  subcontractorDraft.subcontractor_status_lookup_id = selectedSubcontractor.value?.subcontractor_status_lookup_id ?? "";
  subcontractorDraft.managing_director_name = selectedSubcontractor.value?.managing_director_name ?? "";
  subcontractorDraft.address_id = selectedSubcontractor.value?.address_id ?? "";
  subcontractorDraft.latitude = selectedSubcontractor.value?.latitude != null ? String(selectedSubcontractor.value.latitude) : "";
  subcontractorDraft.longitude = selectedSubcontractor.value?.longitude != null ? String(selectedSubcontractor.value.longitude) : "";
  subcontractorDraft.notes = selectedSubcontractor.value?.notes ?? "";
  subcontractorDraft.version_no = selectedSubcontractor.value?.version_no ?? 0;
}

function resetAddressDraft() {
  addressDraft.street_line_1 = "";
  addressDraft.street_line_2 = "";
  addressDraft.postal_code = "";
  addressDraft.city = "";
  addressDraft.state = "";
  addressDraft.country_code = "DE";
}

function resetContactDraft() {
  const selected = contacts.value.find((entry) => entry.id === selectedContactId.value);
  contactDraft.full_name = selected?.full_name ?? "";
  contactDraft.title = selected?.title ?? "";
  contactDraft.function_label = selected?.function_label ?? "";
  contactDraft.email = selected?.email ?? "";
  contactDraft.phone = selected?.phone ?? "";
  contactDraft.mobile = selected?.mobile ?? "";
  contactDraft.is_primary_contact = selected?.is_primary_contact ?? false;
  contactDraft.portal_enabled = selected?.portal_enabled ?? false;
  contactDraft.user_id = selected?.user_id ?? "";
  contactDraft.notes = selected?.notes ?? "";
  contactDraft.version_no = selected?.version_no ?? 0;
}

function resetScopeDraft() {
  const selected = scopes.value.find((entry) => entry.id === selectedScopeId.value);
  scopeDraft.branch_id = selected?.branch_id ?? "";
  scopeDraft.mandate_id = selected?.mandate_id ?? "";
  scopeDraft.valid_from = selected?.valid_from ?? "";
  scopeDraft.valid_to = selected?.valid_to ?? "";
  scopeDraft.notes = selected?.notes ?? "";
  scopeDraft.version_no = selected?.version_no ?? 0;
}

function resetFinanceDraft() {
  const selected = selectedSubcontractor.value?.finance_profile ?? null;
  financeDraft.id = selected?.id ?? "";
  financeDraft.invoice_email = selected?.invoice_email ?? "";
  financeDraft.payment_terms_days = selected?.payment_terms_days != null ? String(selected.payment_terms_days) : "";
  financeDraft.payment_terms_note = selected?.payment_terms_note ?? "";
  financeDraft.tax_number = selected?.tax_number ?? "";
  financeDraft.vat_id = selected?.vat_id ?? "";
  financeDraft.bank_account_holder = selected?.bank_account_holder ?? "";
  financeDraft.bank_iban = selected?.bank_iban ?? "";
  financeDraft.bank_bic = selected?.bank_bic ?? "";
  financeDraft.bank_name = selected?.bank_name ?? "";
  financeDraft.invoice_delivery_method_lookup_id = selected?.invoice_delivery_method_lookup_id ?? "";
  financeDraft.invoice_status_mode_lookup_id = selected?.invoice_status_mode_lookup_id ?? "";
  financeDraft.billing_note = selected?.billing_note ?? "";
  financeDraft.version_no = selected?.version_no ?? 0;
}

function isMissingFinanceProfileError(error: unknown) {
  return error instanceof SubcontractorAdminApiError && error.statusCode === 404;
}

function resetHistoryDraft() {
  historyDraft.entry_type = "processing_note";
  historyDraft.title = "";
  historyDraft.body = "";
  historyDraft.occurred_at = "";
  historyDraft.related_contact_id = "";
  historyAttachmentDraft.label = "";
  historyAttachmentFile.value = null;
}

function onHistoryAttachmentSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  historyAttachmentFile.value = input.files?.[0] ?? null;
}

function selectHistoryEntry(historyEntryId: string) {
  selectedHistoryEntryId.value = historyEntryId;
}

function historyEntryTypeLabel(entryType: string) {
  return t(`sicherplan.subcontractors.history.types.${entryType}` as never);
}

function formatDateTime(value: string | null) {
  if (!value) {
    return "";
  }
  return new Date(value).toLocaleString();
}

function formatHistoryMeta(entry: SubcontractorHistoryEntryRead) {
  return [historyEntryTypeLabel(entry.entry_type), formatDateTime(entry.occurred_at)]
    .filter(Boolean)
    .join(" · ");
}

function formatScopeLabel(branchId: string, mandateId: string | null) {
  const branchLabel = branchOptions.value.find((option) => option.id === branchId)?.label ?? branchId;
  if (!mandateId) {
    return branchLabel;
  }
  const mandateLabel = mandateOptions.value.find((option) => option.id === mandateId)?.label ?? mandateId;
  return `${branchLabel} / ${mandateLabel}`;
}

function openLocationPicker() {
  const fallback = {
    lat: 51.662973,
    lng: 8.174013,
    zoom: 11,
    label: t("sicherplan.subcontractors.mapPicker.startDefault"),
  };

  const resolvedCenter = resolveInitialMapCenter({
    currentLatitude: subcontractorDraft.latitude,
    currentLongitude: subcontractorDraft.longitude,
    fallback,
  });

  locationPickerStartPoint.value = {
    lat: resolvedCenter.lat,
    lng: resolvedCenter.lng,
    zoom: resolvedCenter.source === "existing-record" ? 14 : fallback.zoom,
    label:
      resolvedCenter.source === "existing-record"
        ? t("sicherplan.subcontractors.mapPicker.startExisting")
        : fallback.label,
  };
  locationPickerOpen.value = true;
}

function applyPickedLocation(payload: { latitude: string; longitude: string }) {
  subcontractorDraft.latitude = payload.latitude;
  subcontractorDraft.longitude = payload.longitude;
}

async function loadContactUserOptions(subcontractorId: string) {
  if (!resolvedTenantScopeId.value || !accessToken.value) {
    contactUserOptionRows.value = [];
    return;
  }
  try {
    contactUserOptionRows.value = await listSubcontractorContactUserOptions(
      resolvedTenantScopeId.value,
      subcontractorId,
      accessToken.value,
      { limit: 50 },
    );
  } catch {
    contactUserOptionRows.value = [];
  }
}

async function loadAddressOptions(subcontractorId: string) {
  if (!resolvedTenantScopeId.value || !accessToken.value) {
    addressOptionRows.value = [];
    return;
  }
  try {
    pendingAddressOptionRows.value = [];
    addressOptionRows.value = (await listSubcontractorAddressOptions(
      resolvedTenantScopeId.value,
      subcontractorId,
      accessToken.value,
    )).filter(Boolean) as Array<NonNullable<SubcontractorRead["address"]>>;
  } catch {
    addressOptionRows.value = [];
  }
}

async function loadSubcontractorReferenceData() {
  if (!resolvedTenantScopeId.value || !accessToken.value) {
    subcontractorReferenceData.value = null;
    legalFormReferenceLoadFailed.value = false;
    return;
  }
  try {
    subcontractorReferenceData.value = await getSubcontractorReferenceData(
      resolvedTenantScopeId.value,
      accessToken.value,
    );
    legalFormReferenceLoadFailed.value = false;
  } catch {
    subcontractorReferenceData.value = null;
    legalFormReferenceLoadFailed.value = true;
  }
}

async function loadReferenceOptions() {
  if (!resolvedTenantScopeId.value || !accessToken.value) {
    structureOptionState.loading = false;
    structureOptionState.error = false;
    branches.value = [];
    mandates.value = [];
    subcontractorStatusLookups.value = [];
    invoiceDeliveryMethodLookups.value = [];
    invoiceStatusModeLookups.value = [];
    return;
  }

  structureOptionState.loading = true;
  structureOptionState.error = false;
  try {
    const [
      branchRows,
      mandateRows,
      subcontractorStatusRows,
      invoiceDeliveryMethodRows,
      invoiceStatusModeRows,
    ] = await Promise.all([
      listBranches(accessToken.value, resolvedTenantScopeId.value, activeRole.value, actorTenantId.value),
      listMandates(accessToken.value, resolvedTenantScopeId.value, activeRole.value, actorTenantId.value),
      listLookupValues(accessToken.value, resolvedTenantScopeId.value, "subcontractor_status", activeRole.value, actorTenantId.value),
      listLookupValues(accessToken.value, resolvedTenantScopeId.value, "invoice_delivery_method", activeRole.value, actorTenantId.value),
      listLookupValues(accessToken.value, resolvedTenantScopeId.value, "invoice_status_mode", activeRole.value, actorTenantId.value),
    ]);

    branches.value = branchRows.filter((row) => row.archived_at == null);
    mandates.value = mandateRows.filter((row) => row.archived_at == null);
    subcontractorStatusLookups.value = subcontractorStatusRows.filter((row) => row.archived_at == null);
    invoiceDeliveryMethodLookups.value = invoiceDeliveryMethodRows.filter((row) => row.archived_at == null);
    invoiceStatusModeLookups.value = invoiceStatusModeRows.filter((row) => row.archived_at == null);
  } catch {
    structureOptionState.error = true;
    branches.value = [];
    mandates.value = [];
    subcontractorStatusLookups.value = [];
    invoiceDeliveryMethodLookups.value = [];
    invoiceStatusModeLookups.value = [];
  } finally {
    structureOptionState.loading = false;
  }
}

async function refreshSubcontractors() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !canRead.value) {
    return;
  }

  loading.list = true;
  try {
    await Promise.all([loadSubcontractorReferenceData(), loadReferenceOptions()]);
    subcontractors.value = await listSubcontractors(resolvedTenantScopeId.value, accessToken.value, filters);
    if (selectedSubcontractorId.value) {
      await loadSelectedSubcontractor(selectedSubcontractorId.value);
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.list = false;
  }
}

async function loadSelectedSubcontractor(subcontractorId: string) {
  if (!resolvedTenantScopeId.value || !accessToken.value) {
    return;
  }

  loading.detail = true;
  try {
    selectedSubcontractor.value = await getSubcontractor(resolvedTenantScopeId.value, subcontractorId, accessToken.value);
    contacts.value = await listSubcontractorContacts(resolvedTenantScopeId.value, subcontractorId, accessToken.value);
    scopes.value = await listSubcontractorScopes(resolvedTenantScopeId.value, subcontractorId, accessToken.value);
    historyEntries.value = await listSubcontractorHistory(resolvedTenantScopeId.value, subcontractorId, accessToken.value);
    await Promise.all([loadContactUserOptions(subcontractorId), loadAddressOptions(subcontractorId)]);
    selectedHistoryEntryId.value = historyEntries.value[0]?.id ?? "";
    financeProfileState.loadedSubcontractorId =
      canReadFinance.value && selectedSubcontractor.value.finance_profile ? subcontractorId : "";
    resetSubcontractorDraft();
    resetContactDraft();
    resetScopeDraft();
    resetFinanceDraft();
    resetHistoryDraft();
  } catch (error) {
    handleError(error);
  } finally {
    loading.detail = false;
  }
}

async function loadFinanceProfile(force = false) {
  if (
    !resolvedTenantScopeId.value
    || !accessToken.value
    || !selectedSubcontractorId.value
    || !selectedSubcontractor.value
    || !canReadFinance.value
  ) {
    return;
  }

  const subcontractorId = selectedSubcontractorId.value;
  if (!force) {
    if (financeProfileState.loadedSubcontractorId === subcontractorId) {
      return;
    }
    if (selectedSubcontractor.value.finance_profile) {
      financeProfileState.loadedSubcontractorId = subcontractorId;
      resetFinanceDraft();
      return;
    }
  }

  financeProfileState.loading = true;
  try {
    const financeProfile = await getSubcontractorFinanceProfile(
      resolvedTenantScopeId.value,
      subcontractorId,
      accessToken.value,
    );
    if (!selectedSubcontractor.value || selectedSubcontractorId.value !== subcontractorId) {
      return;
    }
    selectedSubcontractor.value.finance_profile = financeProfile;
    financeProfileState.loadedSubcontractorId = subcontractorId;
    resetFinanceDraft();
  } catch (error) {
    if (!selectedSubcontractor.value || selectedSubcontractorId.value !== subcontractorId) {
      return;
    }
    if (isMissingFinanceProfileError(error)) {
      selectedSubcontractor.value.finance_profile = null;
      financeProfileState.loadedSubcontractorId = subcontractorId;
      resetFinanceDraft();
      return;
    }
    throw error;
  } finally {
    if (selectedSubcontractorId.value === subcontractorId) {
      financeProfileState.loading = false;
    }
  }
}

async function selectSubcontractor(subcontractorId: string) {
  isCreatingSubcontractor.value = false;
  activeDetailTab.value = "overview";
  selectedSubcontractorId.value = subcontractorId;
  selectedContactId.value = "";
  selectedScopeId.value = "";
  await loadSelectedSubcontractor(subcontractorId);
}

function startCreateSubcontractor() {
  isCreatingSubcontractor.value = true;
  activeDetailTab.value = "overview";
  selectedSubcontractorId.value = "";
  selectedSubcontractor.value = null;
  contacts.value = [];
  scopes.value = [];
  historyEntries.value = [];
  selectedContactId.value = "";
  selectedScopeId.value = "";
  selectedHistoryEntryId.value = "";
  contactUserOptionRows.value = [];
  addressOptionRows.value = [];
  pendingAddressOptionRows.value = [];
  resetSubcontractorDraft();
  resetContactDraft();
  resetScopeDraft();
  resetFinanceDraft();
  resetHistoryDraft();
}

function selectContact(contactId: string) {
  selectedContactId.value = contactId;
  resetContactDraft();
}

function selectScope(scopeId: string) {
  selectedScopeId.value = scopeId;
  resetScopeDraft();
}

async function submitSubcontractor() {
  if (!resolvedTenantScopeId.value || !accessToken.value) {
    return;
  }

  loading.saving = true;
  try {
    const pendingAddress = findPendingAddressOption(subcontractorDraft.address_id);
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      subcontractor_number: subcontractorDraft.subcontractor_number.trim(),
      legal_name: subcontractorDraft.legal_name.trim(),
      display_name: serializeNullable(subcontractorDraft.display_name),
      legal_form_lookup_id: serializeNullable(subcontractorDraft.legal_form_lookup_id),
      subcontractor_status_lookup_id: serializeNullable(subcontractorDraft.subcontractor_status_lookup_id),
      managing_director_name: serializeNullable(subcontractorDraft.managing_director_name),
      address_id: pendingAddress ? null : serializeNullable(subcontractorDraft.address_id),
      latitude: serializeDecimal(subcontractorDraft.latitude),
      longitude: serializeDecimal(subcontractorDraft.longitude),
      notes: serializeNullable(subcontractorDraft.notes),
    };

    if (isCreatingSubcontractor.value) {
      const created = await createSubcontractor(resolvedTenantScopeId.value, accessToken.value, payload);
      if (pendingAddress) {
        const persistedAddress = await createSubcontractorAddressOption(
          resolvedTenantScopeId.value,
          created.id,
          accessToken.value,
          {
            street_line_1: pendingAddress.street_line_1,
            street_line_2: pendingAddress.street_line_2,
            postal_code: pendingAddress.postal_code,
            city: pendingAddress.city,
            state: pendingAddress.state,
            country_code: pendingAddress.country_code,
          },
        );
        await updateSubcontractor(resolvedTenantScopeId.value, created.id, accessToken.value, {
          address_id: persistedAddress.id,
          version_no: created.version_no,
        });
        pendingAddressOptionRows.value = [];
      }
      await selectSubcontractor(created.id);
      setFeedback("success", "sicherplan.subcontractors.feedback.saved");
    } else if (selectedSubcontractorId.value) {
      await updateSubcontractor(resolvedTenantScopeId.value, selectedSubcontractorId.value, accessToken.value, {
        ...payload,
        status: subcontractorDraft.status,
        version_no: subcontractorDraft.version_no,
      });
      await loadSelectedSubcontractor(selectedSubcontractorId.value);
      await refreshSubcontractors();
      setFeedback("success", "sicherplan.subcontractors.feedback.saved");
    }
  } catch (error) {
    handleError(error);
  } finally {
    loading.saving = false;
  }
}

async function submitContact() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !selectedSubcontractorId.value) {
    return;
  }

  try {
    if (contactDraft.portal_enabled && !serializeNullable(contactDraft.user_id)) {
      setFeedback("error", "sicherplan.subcontractors.feedback.portalUserRequired");
      return;
    }
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      subcontractor_id: selectedSubcontractorId.value,
      full_name: contactDraft.full_name.trim(),
      title: serializeNullable(contactDraft.title),
      function_label: serializeNullable(contactDraft.function_label),
      email: serializeNullable(contactDraft.email),
      phone: serializeNullable(contactDraft.phone),
      mobile: serializeNullable(contactDraft.mobile),
      is_primary_contact: contactDraft.is_primary_contact,
      portal_enabled: contactDraft.portal_enabled,
      user_id: serializeNullable(contactDraft.user_id),
      notes: serializeNullable(contactDraft.notes),
    };

    if (selectedContactId.value) {
      await updateSubcontractorContact(
        resolvedTenantScopeId.value,
        selectedSubcontractorId.value,
        selectedContactId.value,
        accessToken.value,
        { ...payload, version_no: contactDraft.version_no },
      );
    } else {
      await createSubcontractorContact(resolvedTenantScopeId.value, selectedSubcontractorId.value, accessToken.value, payload);
    }

    selectedContactId.value = "";
    await loadSelectedSubcontractor(selectedSubcontractorId.value);
    await refreshSubcontractors();
    setFeedback("success", "sicherplan.subcontractors.feedback.contactSaved");
  } catch (error) {
    handleError(error);
  }
}

function openAddressCreateModal() {
  resetAddressDraft();
  addressCreateModalOpen.value = true;
}

function closeAddressCreateModal() {
  addressCreateModalOpen.value = false;
  resetAddressDraft();
}

async function submitAddressOption() {
  if (!resolvedTenantScopeId.value || !accessToken.value) {
    return;
  }
  try {
    if (!selectedSubcontractorId.value) {
      const pendingAddress = {
        id: createPendingAddressOptionId(),
        street_line_1: addressDraft.street_line_1.trim(),
        street_line_2: serializeNullable(addressDraft.street_line_2),
        postal_code: addressDraft.postal_code.trim(),
        city: addressDraft.city.trim(),
        state: serializeNullable(addressDraft.state),
        country_code: addressDraft.country_code.trim().toUpperCase(),
      };
      pendingAddressOptionRows.value = [...pendingAddressOptionRows.value, pendingAddress];
      subcontractorDraft.address_id = pendingAddress.id;
      closeAddressCreateModal();
      return;
    }
    const created = await createSubcontractorAddressOption(
      resolvedTenantScopeId.value,
      selectedSubcontractorId.value,
      accessToken.value,
      {
        street_line_1: addressDraft.street_line_1.trim(),
        street_line_2: serializeNullable(addressDraft.street_line_2),
        postal_code: addressDraft.postal_code.trim(),
        city: addressDraft.city.trim(),
        state: serializeNullable(addressDraft.state),
        country_code: addressDraft.country_code.trim().toUpperCase(),
      },
    );
    addressOptionRows.value = [...addressOptionRows.value, created];
    subcontractorDraft.address_id = created.id;
    closeAddressCreateModal();
  } catch (error) {
    handleError(error);
  }
}

async function submitScope() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !selectedSubcontractorId.value) {
    return;
  }

  try {
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      subcontractor_id: selectedSubcontractorId.value,
      branch_id: scopeDraft.branch_id.trim(),
      mandate_id: serializeNullable(scopeDraft.mandate_id),
      valid_from: scopeDraft.valid_from,
      valid_to: serializeNullable(scopeDraft.valid_to),
      notes: serializeNullable(scopeDraft.notes),
    };

    if (selectedScopeId.value) {
      await updateSubcontractorScope(
        resolvedTenantScopeId.value,
        selectedSubcontractorId.value,
        selectedScopeId.value,
        accessToken.value,
        { ...payload, version_no: scopeDraft.version_no },
      );
    } else {
      await createSubcontractorScope(resolvedTenantScopeId.value, selectedSubcontractorId.value, accessToken.value, payload);
    }

    selectedScopeId.value = "";
    await loadSelectedSubcontractor(selectedSubcontractorId.value);
    setFeedback("success", "sicherplan.subcontractors.feedback.scopeSaved");
  } catch (error) {
    handleError(error);
  }
}

async function submitFinanceProfile() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !selectedSubcontractorId.value || !canReadFinance.value) {
    return;
  }

  try {
    const payload = {
      tenant_id: resolvedTenantScopeId.value,
      subcontractor_id: selectedSubcontractorId.value,
      invoice_email: serializeNullable(financeDraft.invoice_email),
      payment_terms_days: financeDraft.payment_terms_days.trim() ? Number(financeDraft.payment_terms_days) : null,
      payment_terms_note: serializeNullable(financeDraft.payment_terms_note),
      tax_number: serializeNullable(financeDraft.tax_number),
      vat_id: serializeNullable(financeDraft.vat_id),
      bank_account_holder: serializeNullable(financeDraft.bank_account_holder),
      bank_iban: serializeNullable(financeDraft.bank_iban),
      bank_bic: serializeNullable(financeDraft.bank_bic),
      bank_name: serializeNullable(financeDraft.bank_name),
      invoice_delivery_method_lookup_id: serializeNullable(financeDraft.invoice_delivery_method_lookup_id),
      invoice_status_mode_lookup_id: serializeNullable(financeDraft.invoice_status_mode_lookup_id),
      billing_note: serializeNullable(financeDraft.billing_note),
    };

    if (financeDraft.id) {
      await patchSubcontractorFinanceProfile(resolvedTenantScopeId.value, selectedSubcontractorId.value, accessToken.value, {
        ...payload,
        version_no: financeDraft.version_no,
      });
    } else {
      await putSubcontractorFinanceProfile(resolvedTenantScopeId.value, selectedSubcontractorId.value, accessToken.value, payload);
    }

    await loadSelectedSubcontractor(selectedSubcontractorId.value);
    financeProfileState.loadedSubcontractorId = selectedSubcontractorId.value;
    setFeedback("success", "sicherplan.subcontractors.feedback.financeSaved");
  } catch (error) {
    handleError(error);
  }
}

async function submitHistoryEntry() {
  if (!resolvedTenantScopeId.value || !accessToken.value || !selectedSubcontractorId.value) {
    return;
  }

  try {
    const created = await createSubcontractorHistoryEntry(
      resolvedTenantScopeId.value,
      selectedSubcontractorId.value,
      accessToken.value,
      {
        tenant_id: resolvedTenantScopeId.value,
        subcontractor_id: selectedSubcontractorId.value,
        entry_type: historyDraft.entry_type,
        title: historyDraft.title.trim(),
        body: historyDraft.body.trim(),
        occurred_at: historyDraft.occurred_at ? new Date(historyDraft.occurred_at).toISOString() : null,
        related_contact_id: serializeNullable(historyDraft.related_contact_id),
      },
    );
    selectedHistoryEntryId.value = created.id;
    if (historyAttachmentFile.value) {
      await uploadHistoryAttachment(created.id);
    }
    await loadSelectedSubcontractor(selectedSubcontractorId.value);
    selectedHistoryEntryId.value = created.id;
    resetHistoryDraft();
    setFeedback("success", "sicherplan.subcontractors.feedback.historySaved");
  } catch (error) {
    handleError(error);
  }
}

async function attachHistoryDocument() {
  if (!selectedHistoryEntryId.value || !historyAttachmentFile.value) {
    return;
  }
  try {
    const historyEntryId = selectedHistoryEntryId.value;
    await uploadHistoryAttachment(historyEntryId);
    if (selectedSubcontractorId.value) {
      await loadSelectedSubcontractor(selectedSubcontractorId.value);
      selectedHistoryEntryId.value = historyEntryId;
    }
    historyAttachmentDraft.label = "";
    historyAttachmentFile.value = null;
    setFeedback("success", "sicherplan.subcontractors.feedback.historyAttachmentSaved");
  } catch (error) {
    handleError(error);
  }
}

async function applyLifecycle(nextStatus: LifecycleStatus) {
  if (!selectedSubcontractor.value || !resolvedTenantScopeId.value || !accessToken.value) {
    return;
  }

  const confirmed = window.confirm(
    t(
      nextStatus === "archived"
        ? "sicherplan.subcontractors.confirm.archive"
        : "sicherplan.subcontractors.confirm.reactivate",
    ),
  );
  if (!confirmed) {
    return;
  }

  try {
    if (nextStatus === "archived") {
      await archiveSubcontractor(
        resolvedTenantScopeId.value,
        selectedSubcontractor.value.id,
        accessToken.value,
        buildSubcontractorLifecyclePayload(selectedSubcontractor.value),
      );
    } else {
      await reactivateSubcontractor(
        resolvedTenantScopeId.value,
        selectedSubcontractor.value.id,
        accessToken.value,
        buildSubcontractorLifecyclePayload(selectedSubcontractor.value),
      );
    }
    await loadSelectedSubcontractor(selectedSubcontractor.value.id);
    await refreshSubcontractors();
    setFeedback("success", "sicherplan.subcontractors.feedback.statusSaved");
  } catch (error) {
    handleError(error);
  }
}

async function uploadHistoryAttachment(historyEntryId: string) {
  if (!resolvedTenantScopeId.value || !accessToken.value || !selectedSubcontractorId.value || !historyAttachmentFile.value) {
    return;
  }
  const contentBase64 = await fileToBase64(historyAttachmentFile.value);
  const document = await createPlatformDocument(resolvedTenantScopeId.value, accessToken.value, {
    tenant_id: resolvedTenantScopeId.value,
    title: historyAttachmentDraft.label.trim() || historyAttachmentFile.value.name,
    source_module: "subcontractors",
    source_label: "history_attachment",
    metadata_json: {
      subcontractor_id: selectedSubcontractorId.value,
      history_entry_id: historyEntryId,
    },
  });
  await addPlatformDocumentVersion(resolvedTenantScopeId.value, document.id, accessToken.value, {
    file_name: historyAttachmentFile.value.name,
    content_type: historyAttachmentFile.value.type || "application/octet-stream",
    content_base64: contentBase64,
  });
  await linkSubcontractorHistoryAttachment(
    resolvedTenantScopeId.value,
    selectedSubcontractorId.value,
    historyEntryId,
    accessToken.value,
    {
      document_id: document.id,
      label: serializeNullable(historyAttachmentDraft.label),
    },
  );
}

async function downloadHistoryAttachment(attachment: SubcontractorHistoryAttachmentRead) {
  if (!resolvedTenantScopeId.value || !accessToken.value || !attachment.current_version_no) {
    return;
  }
  try {
    const file = await downloadSubcontractorDocument(
      resolvedTenantScopeId.value,
      attachment.document_id,
      attachment.current_version_no,
      accessToken.value,
    );
    const url = URL.createObjectURL(file.blob);
    const anchor = window.document.createElement("a");
    anchor.href = url;
    anchor.download = file.fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    handleError(error);
  }
}

function handleError(error: unknown) {
  if (error instanceof SubcontractorAdminApiError) {
    setFeedback("error", mapSubcontractorApiMessage(error.messageKey));
    return;
  }
  setFeedback("error", "sicherplan.subcontractors.feedback.error");
}

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      resolve(result.split(",")[1] || "");
    };
    reader.onerror = () => reject(reader.error ?? new Error("file-read-error"));
    reader.readAsDataURL(file);
  });
}

watch(
  () => scopeDraft.branch_id,
  () => {
    if (!scopeDraft.mandate_id) {
      return;
    }
    const mandateStillValid = scopeMandateOptions.value.some((mandate) => mandate.id === scopeDraft.mandate_id);
    if (!mandateStillValid) {
      scopeDraft.mandate_id = "";
    }
  },
);

watch(
  () => [activeDetailTab.value, selectedSubcontractorId.value, canReadFinance.value] as const,
  async ([tabId, subcontractorId, canReadFinanceValue]) => {
    if (tabId !== "billing" || !subcontractorId || !canReadFinanceValue) {
      return;
    }
    try {
      await loadFinanceProfile();
    } catch (error) {
      handleError(error);
    }
  },
);

onMounted(async () => {
  if (!authStore.tenantScopeId && authStore.sessionUser?.tenant_id) {
    tenantScopeInput.value = authStore.sessionUser.tenant_id;
  }
  await refreshSubcontractors();
});
</script>

<style scoped>
.subcontractor-admin-page,
.subcontractor-admin-grid,
.subcontractor-admin-panel,
.subcontractor-admin-section,
.subcontractor-admin-form,
.subcontractor-admin-list,
.subcontractor-admin-scope {
  display: grid;
  gap: 1rem;
}

.subcontractor-admin-page {
  gap: var(--sp-page-gap, 1.25rem);
}

.subcontractor-admin-grid {
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  align-items: start;
}

.subcontractor-admin-list-panel {
  align-self: start;
}

.subcontractor-admin-hero,
.subcontractor-admin-lifecycle,
.subcontractor-admin-panel__header,
.subcontractor-admin-feedback,
.subcontractor-admin-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.subcontractor-admin-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.subcontractor-admin-meta__pill,
.subcontractor-admin-summary__card,
.subcontractor-admin-row {
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
}

.subcontractor-admin-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.subcontractor-admin-summary__card {
  display: grid;
  gap: 0.35rem;
}

.subcontractor-admin-form-grid {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.subcontractor-admin-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.subcontractor-admin-tab {
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
  color: var(--sp-color-text-secondary);
  border-radius: 999px;
  padding: 0.6rem 1rem;
  font: inherit;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease;
}

.subcontractor-admin-tab.active {
  border-color: var(--sp-color-primary);
  color: var(--sp-color-primary-strong);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 70%, white);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 28%, transparent);
}

.subcontractor-admin-tab:focus-visible {
  outline: none;
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

.subcontractor-admin-tab-panel {
  display: grid;
  gap: 1rem;
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

.field-help {
  margin: 0;
  font-size: 0.85rem;
}

.subcontractor-admin-checkbox {
  display: flex;
  gap: 0.7rem;
  align-items: center;
  min-width: 0;
  color: var(--sp-color-text-secondary);
}

.subcontractor-admin-checkbox input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--sp-color-primary);
}

.subcontractor-admin-row {
  text-align: left;
}

.subcontractor-admin-row.selected {
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 1px var(--sp-color-primary-muted);
}

.subcontractor-admin-empty {
  display: grid;
  gap: 1rem;
}

.subcontractor-admin-empty-state {
  display: grid;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
}

.subcontractor-admin-feedback {
  padding: 0.9rem 1rem;
  border-radius: 16px;
  background: var(--sp-color-primary-muted);
  color: var(--sp-color-primary-strong);
}

.subcontractor-admin-feedback[data-tone="error"] {
  background: color-mix(in srgb, #c84d3a 18%, var(--sp-color-surface-panel));
  color: #8b2417;
}

.subcontractor-admin-feedback[data-tone="success"] {
  background: color-mix(in srgb, #2f8f67 18%, var(--sp-color-surface-panel));
  color: #17674a;
}

.subcontractor-admin-address-row {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: minmax(0, 2.2fr) minmax(170px, 0.95fr);
  gap: 0.9rem;
  align-items: end;
}

.subcontractor-admin-address-row__field {
  min-width: 0;
}

.subcontractor-admin-address-row__action {
  display: grid;
  gap: 0.55rem;
}

.subcontractor-admin-address-row__label {
  display: inline-flex;
  min-height: 1.2rem;
  font-size: 0.95rem;
  font-weight: 600;
}

.subcontractor-admin-address-row__button {
  width: 100%;
  justify-content: center;
}

.subcontractor-admin-modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgb(15 23 42 / 35%);
  z-index: 50;
}

.subcontractor-admin-modal {
  width: min(100%, 720px);
}

.subcontractor-admin-lead,
.subcontractor-admin-row span {
  margin: 0.35rem 0 0 0;
  color: var(--sp-color-text-secondary);
}

@media (max-width: 1100px) {
  .subcontractor-admin-grid {
    grid-template-columns: 1fr;
  }

  .subcontractor-admin-hero,
  .subcontractor-admin-lifecycle,
  .subcontractor-admin-panel__header,
  .subcontractor-admin-feedback,
  .subcontractor-admin-row {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 720px) {
  .subcontractor-admin-form-grid {
    grid-template-columns: 1fr;
  }

  .subcontractor-admin-address-row {
    grid-template-columns: 1fr;
  }
}
</style>
