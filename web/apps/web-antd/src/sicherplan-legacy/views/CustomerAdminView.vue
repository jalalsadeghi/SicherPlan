<template>
  <section class="customer-admin-page">
    <section v-if="sectionVisibility.showGovernanceHero" class="module-card customer-admin-hero">
      <div>
        <p class="eyebrow">{{ t("customerAdmin.eyebrow") }}</p>
        <h2>{{ t("customerAdmin.title") }}</h2>
        <p class="customer-admin-lead">{{ t("customerAdmin.lead") }}</p>
        <div class="customer-admin-meta">
          <span class="customer-admin-meta__pill">
            {{ t("customerAdmin.permission.read") }}: {{ canRead ? "on" : "off" }}
          </span>
          <span class="customer-admin-meta__pill">
            {{ t("customerAdmin.permission.write") }}: {{ canWrite ? "on" : "off" }}
          </span>
          <span class="customer-admin-meta__pill">
            {{ t("customerAdmin.permission.commercialRead") }}: {{ canReadCommercial ? "on" : "off" }}
          </span>
          <span class="customer-admin-meta__pill">
            {{ t("customerAdmin.permission.commercialWrite") }}: {{ canWriteCommercial ? "on" : "off" }}
          </span>
        </div>
      </div>

      <div class="module-card customer-admin-scope">
        <label class="field-stack">
          <span>{{ t("customerAdmin.scope.label") }}</span>
          <input v-model="tenantScopeInput" :placeholder="t('customerAdmin.scope.placeholder')" />
        </label>
        <label class="field-stack">
          <span>{{ t("customerAdmin.token.label") }}</span>
          <input
            v-model="accessTokenInput"
            type="password"
            :placeholder="t('customerAdmin.token.placeholder')"
          />
        </label>
        <p class="field-help">{{ t("customerAdmin.token.help") }}</p>
        <div class="cta-row">
          <button class="cta-button" type="button" @click="rememberScopeAndToken">
            {{ t("customerAdmin.actions.rememberScope") }}
          </button>
          <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshCustomers">
            {{ t("customerAdmin.actions.refresh") }}
          </button>
        </div>
      </div>
    </section>

    <section v-if="feedback.message" class="customer-admin-feedback" :data-tone="feedback.tone">
      <div>
        <strong>{{ feedback.title }}</strong>
        <span>{{ feedback.message }}</span>
      </div>
      <button type="button" @click="clearFeedback">{{ t("customerAdmin.actions.clearFeedback") }}</button>
    </section>

    <section v-if="!tenantScopeId || !accessToken" class="module-card customer-admin-empty">
      <p class="eyebrow">{{ t("customerAdmin.scope.missingTitle") }}</p>
      <h3>{{ t("customerAdmin.scope.missingBody") }}</h3>
    </section>

    <section v-else-if="!canRead" class="module-card customer-admin-empty">
      <p class="eyebrow">{{ t("customerAdmin.permission.missingTitle") }}</p>
      <h3>{{ t("customerAdmin.permission.missingBody") }}</h3>
    </section>

    <div v-else class="customer-admin-grid" data-testid="customer-master-detail-layout">
      <section class="module-card customer-admin-panel customer-admin-list-panel" data-testid="customer-list-section">
        <div class="customer-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("customerAdmin.list.eyebrow") }}</p>
            <h3>{{ t("customerAdmin.list.title") }}</h3>
          </div>
          <StatusBadge :status="loading.list ? 'inactive' : 'active'" />
        </div>

        <div class="customer-admin-form-grid">
          <label class="field-stack">
            <span>{{ t("customerAdmin.filters.search") }}</span>
            <input v-model="filters.search" :placeholder="t('customerAdmin.filters.searchPlaceholder')" />
          </label>
          <label class="field-stack">
            <span>{{ t("customerAdmin.filters.status") }}</span>
            <select v-model="filters.lifecycle_status">
              <option value="">{{ t("customerAdmin.filters.allStatuses") }}</option>
              <option value="active">{{ t("customerAdmin.status.active") }}</option>
              <option value="inactive">{{ t("customerAdmin.status.inactive") }}</option>
              <option value="archived">{{ t("customerAdmin.status.archived") }}</option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ t("customerAdmin.fields.defaultBranchId") }}</span>
            <select v-model="filters.default_branch_id">
              <option value="">{{ t("customerAdmin.summary.none") }}</option>
              <option v-for="branch in branchOptions" :key="branch.id" :value="branch.id">
                {{ formatReferenceOptionLabel(branch) }}
              </option>
            </select>
          </label>
          <label class="field-stack">
            <span>{{ t("customerAdmin.fields.defaultMandateId") }}</span>
            <select v-model="filters.default_mandate_id">
              <option value="">{{ t("customerAdmin.summary.none") }}</option>
              <option
                v-for="mandate in filterMandateOptions(filters.default_branch_id)"
                :key="mandate.id"
                :value="mandate.id"
              >
                {{ formatReferenceOptionLabel(mandate) }}
              </option>
            </select>
          </label>
        </div>

        <label class="customer-admin-checkbox">
          <input v-model="filters.include_archived" type="checkbox" />
          <span>{{ t("customerAdmin.filters.includeArchived") }}</span>
        </label>

        <div class="cta-row">
          <button class="cta-button" type="button" @click="refreshCustomers">
            {{ t("customerAdmin.actions.search") }}
          </button>
          <button
            class="cta-button cta-secondary"
            type="button"
            :disabled="!canRead || !tenantScopeId || !accessToken"
            @click="runCustomerExport"
          >
            {{ t("customerAdmin.actions.exportCustomers") }}
          </button>
          <button
            class="cta-button cta-secondary"
            type="button"
            :disabled="!actionState.canCreate"
            @click="startCreateCustomer"
          >
            {{ t("customerAdmin.actions.newCustomer") }}
          </button>
        </div>

        <div v-if="customers.length" class="customer-admin-list">
          <button
            v-for="customer in customers"
            :key="customer.id"
            type="button"
            class="customer-admin-row"
            :class="{ selected: customer.id === selectedCustomerId }"
            @click="selectCustomer(customer.id)"
          >
            <div>
              <strong>{{ customer.name }}</strong>
              <span>{{ customer.customer_number }}</span>
            </div>
            <StatusBadge :status="customer.status" />
          </button>
        </div>
        <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.list.empty") }}</p>
      </section>

      <section class="module-card customer-admin-panel customer-admin-detail" data-testid="customer-detail-workspace">
        <div class="customer-admin-panel__header">
          <div>
            <p class="eyebrow">{{ t("customerAdmin.detail.eyebrow") }}</p>
            <h3>{{ isCreatingCustomer ? t("customerAdmin.detail.newTitle") : selectedCustomer?.name || t("customerAdmin.detail.workspaceTitle") }}</h3>
            <p v-if="hasDetailWorkspace" class="field-help">{{ t("customerAdmin.detail.workspaceLead") }}</p>
          </div>
          <StatusBadge v-if="selectedCustomer && !isCreatingCustomer" :status="selectedCustomer.status" />
        </div>

        <template v-if="hasDetailWorkspace">
          <nav
            v-if="customerDetailTabs.length"
            class="customer-admin-tabs"
            aria-label="Customer detail sections"
            data-testid="customer-detail-tabs"
          >
            <button
              v-for="tab in customerDetailTabs"
              :key="tab.id"
              type="button"
              class="customer-admin-tab"
              :class="{ active: tab.id === activeDetailTab }"
              :data-testid="`customer-tab-${tab.id}`"
              @click="activeDetailTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </nav>

          <section v-if="activeDetailTab === 'overview'" class="customer-admin-tab-panel" data-testid="customer-tab-panel-overview">
            <div v-if="selectedCustomer && !isCreatingCustomer" class="customer-admin-summary">
            <article class="customer-admin-summary__card">
              <span>{{ t("customerAdmin.summary.primaryContact") }}</span>
              <strong>{{ primaryContactSummary || t("customerAdmin.summary.none") }}</strong>
            </article>
            <article class="customer-admin-summary__card">
              <span>{{ t("customerAdmin.summary.defaultBranch") }}</span>
              <strong>{{ selectedCustomerBranchLabel || t("customerAdmin.summary.none") }}</strong>
            </article>
            <article class="customer-admin-summary__card">
              <span>{{ t("customerAdmin.summary.defaultMandate") }}</span>
              <strong>{{ selectedCustomerMandateLabel || t("customerAdmin.summary.none") }}</strong>
            </article>
            <article class="customer-admin-summary__card">
              <span>{{ t("customerAdmin.summary.classification") }}</span>
              <strong>{{ selectedCustomerClassificationLabel || t("customerAdmin.summary.none") }}</strong>
            </article>
            <article class="customer-admin-summary__card">
              <span>{{ t("customerAdmin.summary.ranking") }}</span>
              <strong>{{ selectedCustomerRankingLabel || t("customerAdmin.summary.none") }}</strong>
            </article>
            <article class="customer-admin-summary__card">
              <span>{{ t("customerAdmin.summary.customerStatus") }}</span>
              <strong>{{ selectedCustomerStatusLabel || t("customerAdmin.summary.none") }}</strong>
            </article>
            </div>

            <div v-if="selectedCustomer && !isCreatingCustomer" class="customer-admin-lifecycle">
              <div>
                <strong>{{ t("customerAdmin.lifecycle.title") }}</strong>
                <p class="field-help">{{ t("customerAdmin.lifecycle.help") }}</p>
              </div>
              <div class="cta-row">
                <button
                  v-if="actionState.canDeactivate"
                  class="cta-button"
                  type="button"
                  @click="applyStatus('inactive')"
                >
                  {{ t("customerAdmin.actions.deactivate") }}
                </button>
                <button
                  v-if="actionState.canReactivate"
                  class="cta-button"
                  type="button"
                  @click="applyStatus('active')"
                >
                  {{ t("customerAdmin.actions.reactivate") }}
                </button>
                <button
                  v-if="actionState.canArchive"
                  class="cta-button cta-secondary"
                  type="button"
                  @click="applyStatus('archived')"
                >
                  {{ t("customerAdmin.actions.archive") }}
                </button>
              </div>
            </div>

            <form class="customer-admin-form" @submit.prevent="submitCustomer">
              <div class="customer-admin-panel__header">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.form.generalEyebrow") }}</p>
                  <h3>{{ t("customerAdmin.form.generalTitle") }}</h3>
                </div>
              </div>

              <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.lifecycleStatus") }}</span>
                  <select v-model="customerDraft.status">
                    <option value="active">{{ t("customerAdmin.status.active") }}</option>
                    <option value="inactive">{{ t("customerAdmin.status.inactive") }}</option>
                  </select>
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.customerNumber") }}</span>
                  <input v-model="customerDraft.customer_number" required />
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.name") }}</span>
                  <input v-model="customerDraft.name" required />
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.legalName") }}</span>
                  <input v-model="customerDraft.legal_name" />
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.externalRef") }}</span>
                  <input v-model="customerDraft.external_ref" />
                </label>
                <div
                  v-if="hasCustomerMetadataCatalogGap"
                  class="customer-admin-metadata-warning field-stack field-stack--wide"
                >
                  <strong>{{ t("customerAdmin.overview.crmMetadataWarningTitle") }}</strong>
                  <p>{{ t("customerAdmin.overview.crmMetadataWarningBody") }}</p>
                </div>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.legalFormLookupId") }}</span>
                  <select v-model="customerDraft.legal_form_lookup_id">
                    <option value="">{{ t("customerAdmin.summary.none") }}</option>
                    <option v-for="option in referenceData?.legal_forms || []" :key="option.id" :value="option.id">
                      {{ formatReferenceOptionLabel(option) }}
                    </option>
                  </select>
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.classificationLookupId") }}</span>
                  <select v-model="customerDraft.classification_lookup_id" :disabled="classificationOptions.length === 0">
                    <option value="">{{ t("customerAdmin.summary.none") }}</option>
                    <option v-for="option in classificationOptions" :key="option.id" :value="option.id">
                      {{ formatReferenceOptionLabel(option) }}
                    </option>
                  </select>
                  <small v-if="classificationOptions.length === 0" class="customer-admin-field-help">
                    {{ t("customerAdmin.overview.classificationEmptyHint") }}
                  </small>
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.rankingLookupId") }}</span>
                  <select v-model="customerDraft.ranking_lookup_id" :disabled="rankingOptions.length === 0">
                    <option value="">{{ t("customerAdmin.summary.none") }}</option>
                    <option v-for="option in rankingOptions" :key="option.id" :value="option.id">
                      {{ formatReferenceOptionLabel(option) }}
                    </option>
                  </select>
                  <small v-if="rankingOptions.length === 0" class="customer-admin-field-help">
                    {{ t("customerAdmin.overview.rankingEmptyHint") }}
                  </small>
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.customerStatusLookupId") }}</span>
                  <select v-model="customerDraft.customer_status_lookup_id" :disabled="customerStatusMetadataOptions.length === 0">
                    <option value="">{{ t("customerAdmin.summary.none") }}</option>
                    <option v-for="option in customerStatusMetadataOptions" :key="option.id" :value="option.id">
                      {{ formatReferenceOptionLabel(option) }}
                    </option>
                  </select>
                  <small v-if="customerStatusMetadataOptions.length === 0" class="customer-admin-field-help">
                    {{ t("customerAdmin.overview.customerStatusEmptyHint") }}
                  </small>
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.defaultBranchId") }}</span>
                  <select v-model="customerDraft.default_branch_id">
                    <option value="">{{ t("customerAdmin.summary.none") }}</option>
                    <option v-for="branch in branchOptions" :key="branch.id" :value="branch.id">
                      {{ formatReferenceOptionLabel(branch) }}
                    </option>
                  </select>
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.defaultMandateId") }}</span>
                  <select v-model="customerDraft.default_mandate_id">
                    <option value="">{{ t("customerAdmin.summary.none") }}</option>
                    <option v-for="mandate in filteredCustomerMandates" :key="mandate.id" :value="mandate.id">
                      {{ formatReferenceOptionLabel(mandate) }}
                    </option>
                  </select>
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("customerAdmin.fields.notes") }}</span>
                  <textarea v-model="customerDraft.notes" rows="4" />
                </label>
              </div>

              <div class="cta-row">
                <button class="cta-button" type="submit" :disabled="!actionState.canCreate && !actionState.canEdit">
                  {{ isCreatingCustomer ? t("customerAdmin.actions.createCustomer") : t("customerAdmin.actions.saveCustomer") }}
                </button>
                <button class="cta-button cta-secondary" type="button" @click="cancelCustomerEdit">
                  {{ t("customerAdmin.actions.cancel") }}
                </button>
              </div>
            </form>
          </section>

          <section v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'contacts'" class="customer-admin-section" data-testid="customer-tab-panel-contacts">
            <div class="customer-admin-form customer-admin-form--structured">
              <section class="customer-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.contacts.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.contacts.title") }}</h4>
                </div>
                <p class="field-help">{{ t("customerAdmin.contacts.lead") }}</p>
              </section>

              <section class="customer-admin-form-section">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.contacts.registerEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.contacts.registerTitle") }}</h4>
                </div>
                <div v-if="selectedCustomer.contacts.length" class="customer-admin-record-list">
                  <article v-for="contact in selectedCustomer.contacts" :key="contact.id" class="customer-admin-record">
                    <div class="customer-admin-record__body">
                      <strong>{{ contact.full_name }}</strong>
                      <p>{{ [contact.email, contact.phone].filter(Boolean).join(" · ") || t("customerAdmin.summary.none") }}</p>
                      <span class="customer-admin-record__meta">
                        {{ contact.is_primary_contact ? t("customerAdmin.contacts.primaryBadge") : t("customerAdmin.contacts.standardBadge") }}
                      </span>
                    </div>
                    <div class="customer-admin-record__actions">
                      <StatusBadge :status="contact.status" />
                      <button type="button" :disabled="!canRead" @click="downloadContactVCard(contact)">
                        {{ t("customerAdmin.actions.exportVCard") }}
                      </button>
                      <button type="button" @click="editContact(contact)">{{ t("customerAdmin.actions.edit") }}</button>
                      <button
                        v-if="contact.status !== 'archived'"
                        type="button"
                        :disabled="!actionState.canManageContacts"
                        @click="archiveContact(contact)"
                      >
                        {{ t("customerAdmin.actions.archive") }}
                      </button>
                    </div>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.contacts.empty") }}</p>
              </section>

              <form class="customer-admin-form-section" @submit.prevent="submitContact">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.contacts.editorEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.contacts.editorTitle") }}</h4>
                </div>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.fullName") }}</span>
                  <input v-model="contactDraft.full_name" required />
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.contactTitle") }}</span>
                  <input v-model="contactDraft.title" />
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.functionLabel") }}</span>
                  <input v-model="contactDraft.function_label" />
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.email") }}</span>
                  <input v-model="contactDraft.email" type="email" />
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.phone") }}</span>
                  <input v-model="contactDraft.phone" />
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.mobile") }}</span>
                  <input v-model="contactDraft.mobile" />
                </label>
                <label class="field-stack field-stack--wide">
                  <span>{{ t("customerAdmin.fields.notes") }}</span>
                  <textarea v-model="contactDraft.notes" rows="3" />
                </label>
                </div>

                <div class="customer-admin-checkbox-group">
                  <label class="customer-admin-checkbox">
                    <input v-model="contactDraft.is_primary_contact" type="checkbox" />
                    <span>{{ t("customerAdmin.fields.isPrimaryContact") }}</span>
                  </label>
                  <label class="customer-admin-checkbox">
                    <input v-model="contactDraft.is_billing_contact" type="checkbox" />
                    <span>{{ t("customerAdmin.fields.isBillingContact") }}</span>
                  </label>
                </div>

                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageContacts" @click="startCreateContact">
                    {{ t("customerAdmin.actions.addContact") }}
                  </button>
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageContacts">
                    {{ editingContactId ? t("customerAdmin.actions.saveContact") : t("customerAdmin.actions.createContact") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetContactDraft">
                    {{ t("customerAdmin.actions.cancel") }}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <section v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'addresses'" class="customer-admin-section" data-testid="customer-tab-panel-addresses">
            <div class="customer-admin-form customer-admin-form--structured">
              <section class="customer-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.addresses.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.addresses.title") }}</h4>
                </div>
                <p class="field-help">{{ t("customerAdmin.addresses.lead") }}</p>
              </section>

              <section class="customer-admin-form-section">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.addresses.registerEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.addresses.registerTitle") }}</h4>
                </div>
                <div v-if="selectedCustomer.addresses.length" class="customer-admin-record-list">
                  <article v-for="address in selectedCustomer.addresses" :key="address.id" class="customer-admin-record">
                    <div class="customer-admin-record__body">
                      <strong>{{ t(`customerAdmin.addressType.${address.address_type}`) }}</strong>
                      <p>
                        {{
                          address.address
                            ? `${address.address.street_line_1}, ${address.address.postal_code} ${address.address.city}`
                            : address.address_id
                        }}
                      </p>
                      <span class="customer-admin-record__meta">
                        {{ address.is_default ? t("customerAdmin.addresses.defaultBadge") : t("customerAdmin.addresses.linkBadge") }}
                      </span>
                    </div>
                    <div class="customer-admin-record__actions">
                      <StatusBadge :status="address.status" />
                      <button type="button" @click="editAddress(address)">{{ t("customerAdmin.actions.edit") }}</button>
                      <button
                        v-if="address.status !== 'archived'"
                        type="button"
                        :disabled="!actionState.canManageAddresses"
                        @click="archiveAddress(address)"
                      >
                        {{ t("customerAdmin.actions.archive") }}
                      </button>
                    </div>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.addresses.empty") }}</p>
              </section>

              <form class="customer-admin-form-section" @submit.prevent="submitAddress">
                <div class="customer-admin-form-section__header customer-admin-form-section__header--split">
                  <div>
                    <p class="eyebrow">{{ t("customerAdmin.addresses.editorEyebrow") }}</p>
                    <h4>{{ t("customerAdmin.addresses.editorTitle") }}</h4>
                  </div>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    :disabled="!actionState.canManageAddresses"
                    @click="openAddressDirectoryCreateModal"
                  >
                    {{ t("customerAdmin.actions.createSharedAddress") }}
                  </button>
                </div>
                <p class="field-help">{{ t("customerAdmin.addresses.linkLead") }}</p>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.address") }}</span>
                  <select
                    v-model="addressDraft.address_id"
                    :disabled="!actionState.canManageAddresses || !customerAddressLinkOptions.length"
                  >
                    <option value="">{{ customerAddressLinkPlaceholder }}</option>
                    <option v-for="option in customerAddressLinkOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                  <p v-if="!customerAddressLinkOptions.length" class="field-help">
                    {{ t("customerAdmin.addresses.addressLinkEmpty") }}
                  </p>
                </label>
                <label class="field-stack field-stack--third">
                  <span>{{ t("customerAdmin.fields.addressType") }}</span>
                  <select v-model="addressDraft.address_type">
                    <option value="registered">{{ t("customerAdmin.addressType.registered") }}</option>
                    <option value="billing">{{ t("customerAdmin.addressType.billing") }}</option>
                    <option value="mailing">{{ t("customerAdmin.addressType.mailing") }}</option>
                    <option value="service">{{ t("customerAdmin.addressType.service") }}</option>
                  </select>
                </label>
                <label class="field-stack field-stack--half">
                  <span>{{ t("customerAdmin.fields.label") }}</span>
                  <input v-model="addressDraft.label" />
                </label>
                </div>

                <div class="customer-admin-checkbox-group">
                  <label class="customer-admin-checkbox">
                    <input v-model="addressDraft.is_default" type="checkbox" />
                    <span>{{ t("customerAdmin.fields.isDefault") }}</span>
                  </label>
                </div>

                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="button" :disabled="!actionState.canManageAddresses" @click="startCreateAddress">
                    {{ t("customerAdmin.actions.addAddress") }}
                  </button>
                  <button class="cta-button" type="submit" :disabled="!actionState.canManageAddresses || !customerAddressLinkOptions.length">
                    {{ editingAddressId ? t("customerAdmin.actions.saveAddress") : t("customerAdmin.actions.createAddress") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetAddressDraft">
                    {{ t("customerAdmin.actions.cancel") }}
                  </button>
                </div>
              </form>
            </div>

            <div
              v-if="addressDirectoryModalOpen"
              class="customer-admin-modal-backdrop"
              data-testid="customer-address-directory-create-modal"
            >
              <section class="module-card customer-admin-modal">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.addresses.createModalEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.addresses.createModalTitle") }}</h4>
                </div>
                <p class="field-help">{{ t("customerAdmin.addresses.createModalLead") }}</p>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("customerAdmin.fields.streetLine1") }}</span>
                    <input v-model="addressDirectoryDraft.street_line_1" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("customerAdmin.fields.streetLine2") }}</span>
                    <input v-model="addressDirectoryDraft.street_line_2" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.postalCode") }}</span>
                    <input v-model="addressDirectoryDraft.postal_code" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.city") }}</span>
                    <input v-model="addressDirectoryDraft.city" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.countryCode") }}</span>
                    <input v-model="addressDirectoryDraft.country_code" maxlength="2" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.state") }}</span>
                    <input v-model="addressDirectoryDraft.state" />
                  </label>
                </div>
                <div class="cta-row">
                  <button
                    class="cta-button"
                    type="button"
                    :disabled="loading.sharedAddress"
                    @click="submitAddressDirectoryEntry"
                  >
                    {{ t("customerAdmin.actions.createSharedAddress") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="closeAddressDirectoryCreateModal">
                    {{ t("customerAdmin.actions.cancel") }}
                  </button>
                </div>
              </section>
            </div>
          </section>

          <section
            v-if="selectedCustomer && !isCreatingCustomer && canReadCommercial && activeDetailTab === 'commercial'"
            class="customer-admin-section"
            data-testid="customer-tab-panel-commercial"
          >
            <div class="customer-admin-form customer-admin-form--structured">
            <section class="customer-admin-editor-intro">
              <div>
                <p class="eyebrow">{{ t("customerAdmin.commercial.eyebrow") }}</p>
                <h4>{{ t("customerAdmin.commercial.title") }}</h4>
              </div>
              <p class="field-help">{{ t("customerAdmin.commercial.lead") }}</p>
            </section>

            <div class="customer-admin-summary">
              <article class="customer-admin-summary__card">
                <span>{{ t("customerAdmin.commercial.summary.billingProfile") }}</span>
                <strong>
                  {{
                    commercialProfile?.billing_profile
                      ? commercialProfile.billing_profile.invoice_email || t("customerAdmin.summary.none")
                      : t("customerAdmin.commercial.summary.missing")
                  }}
                </strong>
              </article>
              <article class="customer-admin-summary__card">
                <span>{{ t("customerAdmin.commercial.summary.invoiceParties") }}</span>
                <strong>{{ commercialProfile?.invoice_parties.length ?? 0 }}</strong>
              </article>
              <article class="customer-admin-summary__card">
                <span>{{ t("customerAdmin.commercial.summary.rateCards") }}</span>
                <strong>{{ commercialProfile?.rate_cards.length ?? 0 }}</strong>
              </article>
              <article class="customer-admin-summary__card">
                <span>{{ t("customerAdmin.commercial.summary.selectedRateCard") }}</span>
                <strong>{{ selectedRateCard?.rate_kind || t("customerAdmin.summary.none") }}</strong>
              </article>
            </div>

            <nav class="customer-admin-tabs customer-admin-tabs--sub" aria-label="Commercial detail sections" data-testid="customer-commercial-tabs">
              <button
                v-for="tab in commercialTabs"
                :key="tab.id"
                type="button"
                class="customer-admin-tab customer-admin-tab--sub"
                :class="{ active: tab.id === activeCommercialTab }"
                :data-testid="`customer-commercial-tab-${tab.id}`"
                @click="activeCommercialTab = tab.id"
              >
                {{ tab.label }}
              </button>
            </nav>

            <section
              v-if="activeCommercialTab === 'billing_profile'"
              class="customer-admin-section"
              data-testid="customer-commercial-panel-billing-profile"
            >
              <div class="customer-admin-form-section__header">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.commercial.billingEyebrow") }}</p>
                  <h3>{{ t("customerAdmin.commercial.billingTitle") }}</h3>
                </div>
                <StatusBadge :status="commercialProfile?.billing_profile?.status || 'inactive'" />
              </div>

              <form class="customer-admin-form-section" @submit.prevent="submitBillingProfile">
                <section
                  v-if="billingProfileErrorState.summaryBody"
                  class="customer-admin-feedback customer-admin-feedback--inline"
                  data-tone="error"
                  data-testid="customer-billing-profile-error-summary"
                >
                  <div>
                    <strong>{{ billingProfileErrorState.summaryTitle }}</strong>
                    <span>{{ billingProfileErrorState.summaryBody }}</span>
                    <span v-if="billingProfileErrorState.primaryMessage">{{ billingProfileErrorState.primaryMessage }}</span>
                  </div>
                </section>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                  <label class="field-stack field-stack--half" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('invoice_email') }">
                    <span>{{ t("customerAdmin.fields.invoiceEmail") }}</span>
                    <input v-model="billingProfileDraft.invoice_email" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['invoice_email'])" />
                    <p v-if="billingProfileFieldError('invoice_email')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('invoice_email') }}</p>
                  </label>
                  <label class="field-stack field-stack--third" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('payment_terms_days') }">
                    <span>{{ t("customerAdmin.fields.paymentTermsDays") }}</span>
                    <input v-model.number="billingProfileDraft.payment_terms_days" type="number" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['payment_terms_days'])" />
                    <p v-if="billingProfileFieldError('payment_terms_days')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('payment_terms_days') }}</p>
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.paymentTermsNote") }}</span>
                    <input v-model="billingProfileDraft.payment_terms_note" :disabled="!commercialActionState.canManageBillingProfile" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.taxNumber") }}</span>
                    <input v-model="billingProfileDraft.tax_number" :disabled="!commercialActionState.canManageBillingProfile" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.vatId") }}</span>
                    <input v-model="billingProfileDraft.vat_id" :disabled="!commercialActionState.canManageBillingProfile" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.contractReference") }}</span>
                    <input v-model="billingProfileDraft.contract_reference" :disabled="!commercialActionState.canManageBillingProfile" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.debtorNumber") }}</span>
                    <input v-model="billingProfileDraft.debtor_number" :disabled="!commercialActionState.canManageBillingProfile" />
                  </label>
                  <label class="field-stack field-stack--half" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('bank_account_holder') }">
                    <span>{{ t("customerAdmin.fields.bankAccountHolder") }}</span>
                    <input v-model="billingProfileDraft.bank_account_holder" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['bank_account_holder', 'bank_iban', 'bank_bic', 'bank_name'])" />
                    <p v-if="billingProfileFieldError('bank_account_holder')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('bank_account_holder') }}</p>
                  </label>
                  <label class="field-stack field-stack--third customer-admin-billing-row-field" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('bank_iban') }">
                    <span>{{ t("customerAdmin.fields.bankIban") }}</span>
                    <input v-model="billingProfileDraft.bank_iban" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['bank_iban', 'bank_account_holder', 'bank_bic', 'bank_name'])" />
                    <p v-if="billingProfileFieldError('bank_iban')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('bank_iban') }}</p>
                  </label>
                  <label class="field-stack field-stack--third customer-admin-billing-row-field" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('bank_bic') }">
                    <span>{{ t("customerAdmin.fields.bankBic") }}</span>
                    <input v-model="billingProfileDraft.bank_bic" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['bank_account_holder', 'bank_iban', 'bank_bic', 'bank_name'])" />
                    <p v-if="billingProfileFieldError('bank_bic')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('bank_bic') }}</p>
                  </label>
                  <label class="field-stack field-stack--third customer-admin-billing-row-field" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('bank_name') }">
                    <span>{{ t("customerAdmin.fields.bankName") }}</span>
                    <input v-model="billingProfileDraft.bank_name" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['bank_account_holder', 'bank_iban', 'bank_bic', 'bank_name'])" />
                    <p v-if="billingProfileFieldError('bank_name')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('bank_name') }}</p>
                  </label>
                  <label class="field-stack field-stack--third customer-admin-billing-row-field" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('invoice_layout_code') }">
                    <span>{{ t("customerAdmin.fields.invoiceLayoutCode") }}</span>
                    <select v-model="billingProfileDraft.invoice_layout_code" :disabled="!commercialActionState.canManageBillingProfile || !billingInvoiceLayoutOptions.length" @change="clearBillingProfileFieldErrors(['invoice_layout_code', 'shipping_method_code', 'e_invoice_enabled'])">
                      <option v-for="option in billingInvoiceLayoutOptions" :key="option.id" :value="option.code">
                        {{ option.label }}
                      </option>
                    </select>
                    <p v-if="billingProfileFieldError('invoice_layout_code')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('invoice_layout_code') }}</p>
                    <p v-else-if="!billingInvoiceLayoutOptions.length" class="field-help">{{ t("customerAdmin.feedback.invoiceLayoutUnavailable") }}</p>
                  </label>
                  <label class="field-stack field-stack--third customer-admin-billing-row-field" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('shipping_method_code') }">
                    <span>{{ t("customerAdmin.fields.shippingMethodCode") }}</span>
                    <select v-model="billingProfileDraft.shipping_method_code" :disabled="!commercialActionState.canManageBillingProfile || !billingShippingMethodOptions.length" @change="clearBillingProfileFieldErrors(['shipping_method_code', 'invoice_email', 'leitweg_id', 'e_invoice_enabled', 'invoice_layout_code'])">
                      <option v-for="option in billingShippingMethodOptions" :key="option.id" :value="option.code">
                        {{ option.label }}
                      </option>
                    </select>
                    <p v-if="billingProfileFieldError('shipping_method_code')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('shipping_method_code') }}</p>
                    <p v-else-if="!billingShippingMethodOptions.length" class="field-help">{{ t("customerAdmin.feedback.shippingMethodUnavailable") }}</p>
                  </label>
                  <label class="field-stack field-stack--third customer-admin-billing-row-field" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('dunning_policy_code') }">
                    <span>{{ t("customerAdmin.fields.dunningPolicyCode") }}</span>
                    <select v-model="billingProfileDraft.dunning_policy_code" :disabled="!commercialActionState.canManageBillingProfile || !billingDunningPolicyOptions.length" @change="clearBillingProfileFieldErrors(['dunning_policy_code'])">
                      <option v-for="option in billingDunningPolicyOptions" :key="option.id" :value="option.code">
                        {{ option.label }}
                      </option>
                    </select>
                    <p v-if="billingProfileFieldError('dunning_policy_code')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('dunning_policy_code') }}</p>
                    <p v-else-if="!billingDunningPolicyOptions.length" class="field-help">{{ t("customerAdmin.feedback.dunningPolicyUnavailable") }}</p>
                  </label>
                  <label class="field-stack field-stack--half customer-admin-billing-paired-field customer-admin-billing-paired-field--compact" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('leitweg_id') }">
                    <span>{{ t("customerAdmin.fields.leitwegId") }}</span>
                    <input v-model="billingProfileDraft.leitweg_id" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['leitweg_id', 'shipping_method_code', 'e_invoice_enabled'])" />
                    <p v-if="billingProfileFieldError('leitweg_id')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('leitweg_id') }}</p>
                  </label>
                  <label class="field-stack field-stack--half customer-admin-billing-paired-field customer-admin-billing-paired-field--notes">
                    <span>{{ t("customerAdmin.fields.billingNote") }}</span>
                    <textarea v-model="billingProfileDraft.billing_note" rows="3" :disabled="!commercialActionState.canManageBillingProfile" />
                  </label>
                </div>

                <label class="customer-admin-checkbox" :class="{ 'customer-admin-checkbox--error': billingProfileFieldInvalid('e_invoice_enabled') }">
                  <input v-model="billingProfileDraft.e_invoice_enabled" type="checkbox" :disabled="!commercialActionState.canManageBillingProfile" @change="clearBillingProfileFieldErrors(['e_invoice_enabled', 'shipping_method_code', 'leitweg_id', 'invoice_layout_code'])" />
                  <span>{{ t("customerAdmin.fields.eInvoiceEnabled") }}</span>
                </label>
                <p v-if="billingProfileFieldError('e_invoice_enabled')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('e_invoice_enabled') }}</p>
                <label class="customer-admin-checkbox" :class="{ 'customer-admin-checkbox--error': billingProfileFieldInvalid('tax_exempt') }">
                  <input v-model="billingProfileDraft.tax_exempt" type="checkbox" :disabled="!commercialActionState.canManageBillingProfile" @change="clearBillingProfileFieldErrors(['tax_exempt', 'tax_exemption_reason'])" />
                  <span>{{ t("customerAdmin.fields.taxExempt") }}</span>
                </label>
                <p v-if="billingProfileFieldError('tax_exempt')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('tax_exempt') }}</p>
                <label class="field-stack field-stack--wide" :class="{ 'customer-admin-field-stack--error': billingProfileFieldInvalid('tax_exemption_reason') }">
                  <span>{{ t("customerAdmin.fields.taxExemptionReason") }}</span>
                  <input v-model="billingProfileDraft.tax_exemption_reason" :disabled="!commercialActionState.canManageBillingProfile" @input="clearBillingProfileFieldErrors(['tax_exempt', 'tax_exemption_reason'])" />
                  <p v-if="billingProfileFieldError('tax_exemption_reason')" class="field-help customer-admin-field-help--error">{{ billingProfileFieldError('tax_exemption_reason') }}</p>
                </label>

                <div class="cta-row" v-if="commercialActionState.canManageBillingProfile">
                  <button class="cta-button cta-secondary" type="button" @click="refreshCommercialProfile">
                    {{ t("customerAdmin.actions.refreshCommercial") }}
                  </button>
                  <button class="cta-button" type="submit" :disabled="loading.commercial">
                    {{ t("customerAdmin.actions.saveBillingProfile") }}
                  </button>
                </div>
              </form>
            </section>

            <section
              v-if="activeCommercialTab === 'invoice_parties'"
              class="customer-admin-section"
              data-testid="customer-commercial-panel-invoice-parties"
            >
              <div class="customer-admin-form-section__header">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.commercial.invoiceEyebrow") }}</p>
                  <h3>{{ t("customerAdmin.commercial.invoiceTitle") }}</h3>
                </div>
                <button
                  class="cta-button cta-secondary"
                  type="button"
                  :disabled="!commercialActionState.canManageInvoiceParties"
                  @click="startCreateInvoiceParty"
                >
                  {{ t("customerAdmin.actions.addInvoiceParty") }}
                </button>
              </div>

              <div v-if="commercialProfile?.invoice_parties.length" class="customer-admin-record-list">
                <article v-for="invoiceParty in commercialProfile.invoice_parties" :key="invoiceParty.id" class="customer-admin-record">
                  <div>
                    <strong>{{ invoiceParty.company_name }}</strong>
                    <p>{{ invoiceParty.invoice_email || invoiceParty.address_id }}</p>
                    <span class="customer-admin-record__meta">
                      {{ invoiceParty.is_default ? t("customerAdmin.commercial.defaultInvoiceParty") : t("customerAdmin.commercial.additionalInvoiceParty") }}
                    </span>
                  </div>
                  <div class="customer-admin-record__actions">
                    <StatusBadge :status="invoiceParty.status" />
                    <button type="button" :disabled="!commercialActionState.canManageInvoiceParties" @click="editInvoiceParty(invoiceParty)">
                      {{ t("customerAdmin.actions.edit") }}
                    </button>
                  </div>
                </article>
              </div>
              <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.commercial.invoiceEmpty") }}</p>

              <form class="customer-admin-form-section" @submit.prevent="submitInvoiceParty">
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.companyName") }}</span>
                    <input v-model="invoicePartyDraft.company_name" :disabled="!commercialActionState.canManageInvoiceParties" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.contactName") }}</span>
                    <input v-model="invoicePartyDraft.contact_name" :disabled="!commercialActionState.canManageInvoiceParties" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.billingAddress") }}</span>
                    <select
                      v-model="invoicePartyDraft.address_id"
                      :disabled="!commercialActionState.canManageInvoiceParties || !invoicePartyAddressOptions.length"
                    >
                      <option value="">{{ invoicePartyAddressPlaceholder }}</option>
                      <option v-for="option in invoicePartyAddressOptions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                    <p v-if="!invoicePartyAddressOptions.length" class="field-help">
                      {{ t("customerAdmin.commercial.invoicePartyAddressMissing") }}
                    </p>
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.invoiceEmail") }}</span>
                    <input v-model="invoicePartyDraft.invoice_email" :disabled="!commercialActionState.canManageInvoiceParties" />
                  </label>
                  <label class="field-stack field-stack--half" :class="{ 'customer-admin-field-stack--error': invoicePartyFieldInvalid('invoice_layout_lookup_id') }">
                    <span>{{ t("customerAdmin.fields.invoiceLayoutLookupId") }}</span>
                    <select
                      v-model="invoicePartyDraft.invoice_layout_lookup_id"
                      :disabled="!commercialActionState.canManageInvoiceParties || !invoicePartyInvoiceLayoutOptions.length"
                      @change="clearInvoicePartyErrors(['invoice_layout_lookup_id'])"
                    >
                      <option value="">{{ invoicePartyInvoiceLayoutPlaceholder }}</option>
                      <option v-for="option in invoicePartyInvoiceLayoutOptions" :key="option.id" :value="option.id">
                        {{ option.label }}
                      </option>
                    </select>
                    <p v-if="invoicePartyFieldError('invoice_layout_lookup_id')" class="field-help customer-admin-field-help--error">{{ invoicePartyFieldError('invoice_layout_lookup_id') }}</p>
                    <p v-else-if="!invoicePartyInvoiceLayoutOptions.length" class="field-help">{{ t("customerAdmin.feedback.invoiceLayoutUnavailable") }}</p>
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.externalRef") }}</span>
                    <input v-model="invoicePartyDraft.external_ref" :disabled="!commercialActionState.canManageInvoiceParties" />
                  </label>
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("customerAdmin.fields.note") }}</span>
                    <textarea v-model="invoicePartyDraft.note" rows="3" :disabled="!commercialActionState.canManageInvoiceParties" />
                  </label>
                </div>
                <label class="customer-admin-checkbox">
                  <input v-model="invoicePartyDraft.is_default" type="checkbox" :disabled="!commercialActionState.canManageInvoiceParties" />
                  <span>{{ t("customerAdmin.fields.isDefaultInvoiceParty") }}</span>
                </label>

                <div v-if="!invoicePartyAddressOptions.length" class="cta-row">
                  <button class="cta-button cta-secondary" type="button" @click="openCustomerAddressesTab">
                    {{ t("customerAdmin.actions.openAddressesTab") }}
                  </button>
                </div>

                <div class="cta-row" v-if="commercialActionState.canManageInvoiceParties">
                  <button class="cta-button" type="submit" :disabled="loading.commercial || !invoicePartyAddressOptions.length">
                    {{ editingInvoicePartyId ? t("customerAdmin.actions.saveInvoiceParty") : t("customerAdmin.actions.createInvoiceParty") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetInvoicePartyDraft">
                    {{ t("customerAdmin.actions.cancel") }}
                  </button>
                </div>
              </form>
            </section>

            <section
              v-if="activeCommercialTab === 'pricing_rules'"
              class="customer-admin-section"
              data-testid="customer-commercial-panel-pricing-rules"
            >
              <div class="customer-admin-tabs customer-admin-tabs--sub" data-testid="customer-pricing-rules-tabs">
                <button
                  v-for="tab in pricingRulesTabs"
                  :key="tab.id"
                  type="button"
                  class="customer-admin-tab customer-admin-tab--sub"
                  :class="{ active: tab.id === activePricingRulesTab }"
                  @click="activePricingRulesTab = tab.id"
                >
                  {{ tab.label }}
                </button>
              </div>

              <section
                v-if="activePricingRulesTab === 'rate_cards'"
                class="customer-admin-section"
                data-testid="customer-pricing-rules-panel-rate-cards"
              >
                <div class="customer-admin-panel__header">
                  <div>
                    <p class="eyebrow">{{ t("customerAdmin.commercial.rateCardsEyebrow") }}</p>
                    <h3>{{ t("customerAdmin.commercial.rateCardsTitle") }}</h3>
                  </div>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    :disabled="!commercialActionState.canManageRateCards"
                    @click="startCreateRateCard"
                  >
                    {{ t("customerAdmin.actions.addRateCard") }}
                  </button>
                </div>

                <div v-if="commercialProfile?.rate_cards.length" class="customer-admin-list">
                  <button
                    v-for="rateCard in commercialProfile.rate_cards"
                    :key="rateCard.id"
                    type="button"
                    class="customer-admin-row"
                    :class="{ selected: rateCard.id === selectedRateCardId }"
                    @click="selectedRateCardId = rateCard.id"
                  >
                    <div>
                      <strong>{{ rateCard.rate_kind }}</strong>
                      <span>{{ rateCard.effective_from }}{{ rateCard.effective_to ? ` → ${rateCard.effective_to}` : "" }}</span>
                    </div>
                    <StatusBadge :status="rateCard.status" />
                  </button>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.commercial.rateCardsEmpty") }}</p>

                <form class="customer-admin-form" @submit.prevent="submitRateCard">
                  <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                    <label class="field-stack field-stack--half">
                      <span>{{ t("customerAdmin.fields.rateKind") }}</span>
                      <input v-model="rateCardDraft.rate_kind" :disabled="!commercialActionState.canManageRateCards" />
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.currencyCode") }}</span>
                      <input v-model="rateCardDraft.currency_code" :disabled="!commercialActionState.canManageRateCards" />
                    </label>
                    <label class="field-stack field-stack--half">
                      <span>{{ t("customerAdmin.fields.effectiveFrom") }}</span>
                      <input v-model="rateCardDraft.effective_from" type="date" :disabled="!commercialActionState.canManageRateCards" />
                    </label>
                    <label class="field-stack field-stack--half">
                      <span>{{ t("customerAdmin.fields.effectiveTo") }}</span>
                      <input v-model="rateCardDraft.effective_to" type="date" :disabled="!commercialActionState.canManageRateCards" />
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("customerAdmin.fields.notes") }}</span>
                      <textarea v-model="rateCardDraft.notes" rows="3" :disabled="!commercialActionState.canManageRateCards" />
                    </label>
                  </div>
                  <div class="cta-row" v-if="commercialActionState.canManageRateCards">
                    <button class="cta-button" type="submit" :disabled="loading.commercial">
                      {{ editingRateCardId ? t("customerAdmin.actions.saveRateCard") : t("customerAdmin.actions.createRateCard") }}
                    </button>
                    <button class="cta-button cta-secondary" type="button" @click="resetRateCardDraft">
                      {{ t("customerAdmin.actions.cancel") }}
                    </button>
                  </div>
                </form>
              </section>

              <section
                v-if="activePricingRulesTab === 'rate_lines' && selectedRateCard"
                class="customer-admin-section"
                data-testid="customer-pricing-rules-panel-rate-lines"
              >
                <div class="customer-admin-panel__header">
                  <div>
                    <p class="eyebrow">{{ t("customerAdmin.commercial.rateLinesEyebrow") }}</p>
                    <h3>{{ t("customerAdmin.commercial.rateLinesTitle") }}</h3>
                  </div>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    :disabled="!commercialActionState.canManageRateLines"
                    @click="startCreateRateLine"
                  >
                    {{ t("customerAdmin.actions.addRateLine") }}
                  </button>
                </div>

                <div v-if="selectedRateCard.rate_lines.length" class="customer-admin-record-list">
                  <article v-for="rateLine in selectedRateCard.rate_lines" :key="rateLine.id" class="customer-admin-record">
                    <div>
                      <strong>{{ rateLine.line_kind }} · {{ rateLine.billing_unit }}</strong>
                      <p>{{ rateLine.unit_price }} {{ selectedRateCard.currency_code }}</p>
                      <span class="customer-admin-record__meta">
                        {{
                          [
                            resolveRateLineCatalogLabel(
                              rateLine.function_type_id,
                              rateLine.function_type,
                              rateLineFunctionTypeOptions,
                            ),
                            resolveRateLineCatalogLabel(
                              rateLine.qualification_type_id,
                              rateLine.qualification_type,
                              rateLineQualificationTypeOptions,
                            ),
                            rateLine.planning_mode_code,
                          ]
                            .filter(Boolean)
                            .join(" · ") || t("customerAdmin.summary.none")
                        }}
                      </span>
                    </div>
                    <div class="customer-admin-record__actions">
                      <StatusBadge :status="rateLine.status" />
                      <button type="button" :disabled="!commercialActionState.canManageRateLines" @click="editRateLine(rateLine)">
                        {{ t("customerAdmin.actions.edit") }}
                      </button>
                    </div>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.commercial.rateLinesEmpty") }}</p>

                <form class="customer-admin-form" @submit.prevent="submitRateLine">
                  <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.lineKind") }}</span>
                      <select
                        v-model="rateLineDraft.line_kind"
                        :disabled="!commercialActionState.canManageRateLines"
                      >
                        <option value="">{{ t("customerAdmin.placeholder.select") }}</option>
                        <option v-for="option in RATE_LINE_KIND_OPTIONS" :key="option.value" :value="option.value">
                          {{ t(`customerAdmin.option.rateLineKind.${option.value}` as never) }}
                        </option>
                      </select>
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.billingUnit") }}</span>
                      <select
                        v-model="rateLineDraft.billing_unit"
                        :disabled="!commercialActionState.canManageRateLines"
                      >
                        <option value="">{{ t("customerAdmin.placeholder.select") }}</option>
                        <option v-for="option in RATE_LINE_BILLING_UNIT_OPTIONS" :key="option.value" :value="option.value">
                          {{ t(`customerAdmin.option.billingUnit.${option.value}` as never) }}
                        </option>
                      </select>
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.unitPrice") }}</span>
                      <input
                        v-model="rateLineDraft.unit_price"
                        type="number"
                        step="0.01"
                        min="0"
                        :disabled="!commercialActionState.canManageRateLines"
                      />
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.minimumQuantity") }}</span>
                      <input
                        v-model="rateLineDraft.minimum_quantity"
                        type="number"
                        step="0.01"
                        min="0"
                        :disabled="!commercialActionState.canManageRateLines"
                      />
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.functionTypeId") }}</span>
                      <select
                        v-model="rateLineDraft.function_type_id"
                        :disabled="!commercialActionState.canManageRateLines || isRateLineFunctionCatalogEmpty"
                      >
                        <option value="">{{ t("customerAdmin.commercial.functionTypePlaceholder") }}</option>
                        <option
                          v-for="option in rateLineFunctionTypeSelectOptions"
                          :key="option.id"
                          :value="option.id"
                        >
                          {{ formatCatalogOptionLabel(option) }}
                        </option>
                      </select>
                      <small class="customer-admin-field-help">
                        {{
                          rateLineFunctionTypeOptions.length
                            ? t("customerAdmin.commercial.functionTypeCatalogHint")
                            : t("customerAdmin.commercial.functionTypeEmptyHint")
                        }}
                      </small>
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.qualificationTypeId") }}</span>
                      <select
                        v-model="rateLineDraft.qualification_type_id"
                        :disabled="!commercialActionState.canManageRateLines || isRateLineQualificationCatalogEmpty"
                      >
                        <option value="">{{ t("customerAdmin.commercial.qualificationTypePlaceholder") }}</option>
                        <option
                          v-for="option in rateLineQualificationTypeSelectOptions"
                          :key="option.id"
                          :value="option.id"
                        >
                          {{ formatCatalogOptionLabel(option) }}
                        </option>
                      </select>
                      <small class="customer-admin-field-help">
                        {{
                          rateLineQualificationTypeOptions.length
                            ? t("customerAdmin.commercial.qualificationTypeCatalogHint")
                            : t("customerAdmin.commercial.qualificationTypeEmptyHint")
                        }}
                      </small>
                    </label>
                    <div
                      v-if="isRateLineHrCatalogEmpty"
                      class="customer-admin-catalog-empty-state field-stack field-stack--wide"
                    >
                      <strong>{{ t("customerAdmin.commercial.hrCatalogEmptyTitle") }}</strong>
                      <p>{{ t(rateLineHrCatalogEmptyMessageKey as never) }}</p>
                      <div class="cta-row">
                        <button
                          v-if="canBootstrapHrCatalogSamples"
                          class="cta-button cta-secondary"
                          type="button"
                          :disabled="loading.hrCatalogBootstrap"
                          @click="handleBootstrapRateLineHrCatalogs"
                        >
                          {{
                            loading.hrCatalogBootstrap
                              ? t("customerAdmin.actions.creatingHrCatalogSamples")
                              : t("customerAdmin.actions.createHrCatalogSamples")
                          }}
                        </button>
                        <button
                          class="cta-button cta-secondary"
                          type="button"
                          @click="openEmployeesAdmin"
                        >
                          {{ t("customerAdmin.actions.openEmployeesAdmin") }}
                        </button>
                      </div>
                    </div>
                    <label class="field-stack field-stack--half">
                      <span>{{ t("customerAdmin.fields.planningModeCode") }}</span>
                      <select
                        v-model="rateLineDraft.planning_mode_code"
                        :disabled="!commercialActionState.canManageRateLines"
                      >
                        <option value="">{{ t("customerAdmin.placeholder.selectOptional") }}</option>
                        <option
                          v-for="option in RATE_LINE_PLANNING_MODE_OPTIONS"
                          :key="option.value"
                          :value="option.value"
                        >
                          {{ t(`customerAdmin.option.planningMode.${option.value}` as never) }}
                        </option>
                      </select>
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.sortOrder") }}</span>
                      <input
                        v-model.number="rateLineDraft.sort_order"
                        type="number"
                        min="0"
                        step="1"
                        :disabled="!commercialActionState.canManageRateLines"
                      />
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("customerAdmin.fields.notes") }}</span>
                      <textarea v-model="rateLineDraft.notes" rows="3" :disabled="!commercialActionState.canManageRateLines" />
                    </label>
                  </div>
                  <div class="cta-row" v-if="commercialActionState.canManageRateLines">
                    <button class="cta-button" type="submit" :disabled="loading.rateLine">
                      {{ editingRateLineId ? t("customerAdmin.actions.saveRateLine") : t("customerAdmin.actions.createRateLine") }}
                    </button>
                    <button class="cta-button cta-secondary" type="button" @click="resetRateLineDraft">
                      {{ t("customerAdmin.actions.cancel") }}
                    </button>
                  </div>
                </form>
              </section>

              <section
                v-if="activePricingRulesTab === 'surcharges' && selectedRateCard"
                class="customer-admin-section"
                data-testid="customer-pricing-rules-panel-surcharges"
              >
                <div class="customer-admin-panel__header">
                  <div>
                    <p class="eyebrow">{{ t("customerAdmin.commercial.surchargesEyebrow") }}</p>
                    <h3>{{ t("customerAdmin.commercial.surchargesTitle") }}</h3>
                  </div>
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    :disabled="!commercialActionState.canManageSurchargeRules"
                    @click="startCreateSurchargeRule"
                  >
                    {{ t("customerAdmin.actions.addSurchargeRule") }}
                  </button>
                </div>

                <div v-if="selectedRateCard.surcharge_rules.length" class="customer-admin-record-list">
                  <article v-for="rule in selectedRateCard.surcharge_rules" :key="rule.id" class="customer-admin-record">
                    <div>
                      <strong>{{ rule.surcharge_type }}</strong>
                      <p>
                        {{ rule.percent_value ? `${rule.percent_value}%` : `${rule.fixed_amount} ${rule.currency_code}` }}
                      </p>
                      <span class="customer-admin-record__meta">
                        {{ [rule.weekday_mask, rule.region_code].filter(Boolean).join(" · ") || t("customerAdmin.summary.none") }}
                      </span>
                    </div>
                    <div class="customer-admin-record__actions">
                      <StatusBadge :status="rule.status" />
                      <button type="button" :disabled="!commercialActionState.canManageSurchargeRules" @click="editSurchargeRule(rule)">
                        {{ t("customerAdmin.actions.edit") }}
                      </button>
                    </div>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.commercial.surchargesEmpty") }}</p>

                <form class="customer-admin-form" @submit.prevent="submitSurchargeRule">
                  <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.surchargeType") }}</span>
                      <select
                        v-model="surchargeRuleDraft.surcharge_type"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                      >
                        <option value="">{{ t("customerAdmin.placeholder.select") }}</option>
                        <option v-for="option in SURCHARGE_TYPE_OPTIONS" :key="option.value" :value="option.value">
                          {{ t(`customerAdmin.option.surchargeType.${option.value}` as never) }}
                        </option>
                      </select>
                    </label>
                    <div class="customer-admin-surcharge-date-block">
                      <div class="customer-admin-surcharge-date-grid">
                        <label class="field-stack">
                          <span>{{ t("customerAdmin.fields.effectiveFrom") }}</span>
                          <input
                            v-model="surchargeRuleDraft.effective_from"
                            type="date"
                            :min="selectedRateCard.effective_from"
                            :max="selectedRateCard.effective_to || undefined"
                            :disabled="!commercialActionState.canManageSurchargeRules"
                          />
                        </label>
                        <label class="field-stack">
                          <span>{{ t("customerAdmin.fields.effectiveTo") }}</span>
                          <input
                            v-model="surchargeRuleDraft.effective_to"
                            type="date"
                            :min="surchargeEffectiveToInputMin || undefined"
                            :max="selectedRateCard.effective_to || undefined"
                            :disabled="!commercialActionState.canManageSurchargeRules"
                          />
                        </label>
                      </div>
                      <div class="customer-admin-surcharge-date-help">
                        <small class="customer-admin-field-help">
                          {{ surchargeAllowedWindowHelper }}
                        </small>
                        <small
                          v-if="surchargeMissingEffectiveToForRateCard"
                          class="customer-admin-field-help customer-admin-field-help--error"
                        >
                          {{ t("customerAdmin.feedback.surchargeEffectiveToRequiredForRateCard") }}
                        </small>
                        <small v-else-if="surchargeEffectiveToRequired" class="customer-admin-field-help">
                          {{ t("customerAdmin.commercial.surchargeEffectiveToRequiredHint") }}
                        </small>
                        <small
                          v-if="surchargeRateCardWindowValidationKey === 'customerAdmin.feedback.surchargeOutsideRateCardWindow'"
                          class="customer-admin-field-help customer-admin-field-help--error"
                        >
                          {{ t("customerAdmin.feedback.surchargeOutsideRateCardWindow") }}
                        </small>
                      </div>
                    </div>
                    <div class="field-stack field-stack--wide">
                      <span>{{ t("customerAdmin.fields.weekdays") }}</span>
                      <div class="customer-admin-weekday-picker">
                        <button
                          v-for="day in surchargeWeekdayOptions"
                          :key="day.id"
                          class="customer-admin-tab customer-admin-tab--sub"
                          :class="{ active: surchargeSelectedWeekdays.includes(day.id) }"
                          type="button"
                          :disabled="!commercialActionState.canManageSurchargeRules"
                          @click="toggleSurchargeWeekday(day.id)"
                        >
                          {{ day.label }}
                        </button>
                      </div>
                    </div>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.timeFromMinute") }}</span>
                      <input
                        v-model="surchargeTimeFromInput"
                        type="time"
                        :max="surchargeTimeToInput || undefined"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                      />
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.timeToMinute") }}</span>
                      <input
                        v-model="surchargeTimeToInput"
                        type="time"
                        :min="surchargeTimeFromInput || undefined"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                      />
                      <small v-if="hasInvalidSurchargeTimeRange" class="customer-admin-field-help customer-admin-field-help--error">
                        {{ t("customerAdmin.feedback.invalidTimeRange") }}
                      </small>
                    </label>
                    <label class="field-stack field-stack--half">
                      <span>{{ t("customerAdmin.fields.regionCode") }}</span>
                      <input
                        v-model="surchargeRuleDraft.region_code"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                        @input="normalizeSurchargeRegionCode"
                      />
                    </label>
                    <div class="field-stack field-stack--wide">
                      <span>{{ t("customerAdmin.fields.amountMode") }}</span>
                      <div class="customer-admin-segmented-control">
                        <button
                          class="customer-admin-tab customer-admin-tab--sub"
                          :class="{ active: surchargeAmountMode === 'percent' }"
                          type="button"
                          :disabled="!commercialActionState.canManageSurchargeRules"
                          @click="setSurchargeAmountMode('percent')"
                        >
                          {{ t("customerAdmin.amountMode.percent") }}
                        </button>
                        <button
                          class="customer-admin-tab customer-admin-tab--sub"
                          :class="{ active: surchargeAmountMode === 'fixed' }"
                          type="button"
                          :disabled="!commercialActionState.canManageSurchargeRules"
                          @click="setSurchargeAmountMode('fixed')"
                        >
                          {{ t("customerAdmin.amountMode.fixed") }}
                        </button>
                      </div>
                    </div>
                    <label v-if="surchargeAmountMode === 'percent'" class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.percentValue") }}</span>
                      <input
                        v-model="surchargeRuleDraft.percent_value"
                        type="number"
                        min="0"
                        step="0.01"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                      />
                    </label>
                    <label v-if="surchargeAmountMode === 'fixed'" class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.fixedAmount") }}</span>
                      <input
                        v-model="surchargeRuleDraft.fixed_amount"
                        type="number"
                        min="0"
                        step="0.01"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                      />
                    </label>
                    <label v-if="surchargeAmountMode === 'fixed'" class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.currencyCode") }}</span>
                      <select
                        v-model="surchargeRuleDraft.currency_code"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                      >
                        <option value="">{{ t("customerAdmin.placeholder.select") }}</option>
                        <option v-for="option in surchargeCurrencyOptions" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </option>
                      </select>
                    </label>
                    <label class="field-stack field-stack--third">
                      <span>{{ t("customerAdmin.fields.sortOrder") }}</span>
                      <input
                        v-model.number="surchargeRuleDraft.sort_order"
                        type="number"
                        min="0"
                        step="1"
                        :disabled="!commercialActionState.canManageSurchargeRules"
                      />
                    </label>
                    <label class="field-stack field-stack--wide">
                      <span>{{ t("customerAdmin.fields.notes") }}</span>
                      <textarea v-model="surchargeRuleDraft.notes" rows="3" :disabled="!commercialActionState.canManageSurchargeRules" />
                    </label>
                  </div>
                  <div class="cta-row" v-if="commercialActionState.canManageSurchargeRules">
                    <button class="cta-button" type="submit" :disabled="loading.surchargeRule || hasInvalidSurchargeTimeRange">
                      {{ editingSurchargeRuleId ? t("customerAdmin.actions.saveSurchargeRule") : t("customerAdmin.actions.createSurchargeRule") }}
                    </button>
                    <button class="cta-button cta-secondary" type="button" @click="resetSurchargeRuleDraft">
                      {{ t("customerAdmin.actions.cancel") }}
                    </button>
                  </div>
                </form>
              </section>
            </section>
            </div>
          </section>

          <section
            v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'portal'"
            class="customer-admin-section"
            data-testid="customer-tab-panel-portal"
          >
            <div class="customer-admin-form customer-admin-form--structured">
              <section class="customer-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.loginHistory.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.portal.title") }}</h4>
                </div>
                <p class="field-help">{{ t("customerAdmin.portal.lead") }}</p>
              </section>

              <section class="customer-admin-form-section">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.privacy.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.privacy.title") }}</h4>
                </div>
                <div class="customer-admin-summary">
                  <article class="customer-admin-summary__card">
                    <span>{{ t("customerAdmin.fields.personNamesReleased") }}</span>
                    <strong>
                      {{
                        portalPrivacy?.person_names_released
                          ? t("customerAdmin.status.active")
                          : t("customerAdmin.status.inactive")
                      }}
                    </strong>
                  </article>
                  <article class="customer-admin-summary__card">
                    <span>{{ t("customerAdmin.privacy.lastReleasedAt") }}</span>
                    <strong>{{ formatOptionalDateTime(portalPrivacy?.person_names_released_at) }}</strong>
                  </article>
                  <article class="customer-admin-summary__card">
                    <span>{{ t("customerAdmin.privacy.lastReleasedBy") }}</span>
                    <strong>{{ portalPrivacy?.person_names_released_by_user_id || t("customerAdmin.summary.none") }}</strong>
                  </article>
                </div>
                <div class="customer-admin-checkbox-group">
                  <label class="customer-admin-checkbox">
                    <input v-model="portalPrivacyDraft.person_names_released" type="checkbox" :disabled="!canWrite" />
                    <span>{{ t("customerAdmin.fields.personNamesReleased") }}</span>
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshPortalPrivacy">
                    {{ t("customerAdmin.actions.refreshPortalPrivacy") }}
                  </button>
                  <button class="cta-button" type="button" :disabled="!canWrite || loading.portalPrivacy" @click="submitPortalPrivacy">
                    {{ t("customerAdmin.actions.savePortalPrivacy") }}
                  </button>
                </div>
              </section>

              <section
                v-if="canManagePortalAccess"
                class="customer-admin-form-section"
                data-testid="customer-portal-access-section"
              >
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.portalAccess.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.portalAccess.title") }}</h4>
                </div>
                <p class="field-help">{{ t("customerAdmin.portalAccess.lead") }}</p>
                <div
                  v-if="portalAccessGeneratedPassword"
                  class="customer-admin-feedback customer-admin-feedback--success"
                  data-tone="success"
                >
                  <div>
                    <strong>{{ t("customerAdmin.portalAccess.generatedPasswordTitle") }}</strong>
                    <span>{{ portalAccessGeneratedPassword }}</span>
                  </div>
                  <button type="button" @click="portalAccessGeneratedPassword = ''">
                    {{ t("customerAdmin.actions.clearFeedback") }}
                  </button>
                </div>
                <div class="cta-row">
                  <button
                    class="cta-button cta-secondary"
                    type="button"
                    :disabled="!canManagePortalAccess"
                    @click="refreshCustomerPortalAccess"
                  >
                    {{ t("customerAdmin.actions.refreshPortalAccess") }}
                  </button>
                  <button
                    class="cta-button"
                    type="button"
                    :disabled="loading.portalAccess || !portalAccessAvailableContacts.length"
                    @click="openPortalAccessCreateModal"
                  >
                    {{ t("customerAdmin.actions.createPortalAccess") }}
                  </button>
                </div>
                <p v-if="!portalAccessAvailableContacts.length" class="customer-admin-list-empty">
                  {{ t("customerAdmin.portalAccess.noContactsHint") }}
                </p>
                <div
                  v-else-if="customerPortalAccessAccounts.length"
                  class="customer-admin-record-list"
                  data-testid="customer-portal-access-list"
                >
                  <article
                    v-for="account in customerPortalAccessAccounts"
                    :key="account.user_id"
                    class="customer-admin-record customer-admin-record--stacked"
                  >
                    <div class="customer-admin-record__body">
                      <strong>{{ account.contact_name }} · {{ account.username }}</strong>
                      <span class="customer-admin-record__meta">
                        {{ [account.email, formatOptionalDateTime(account.last_login_at)].filter(Boolean).join(" · ") }}
                      </span>
                    </div>
                    <div class="customer-admin-record__actions">
                      <StatusBadge :status="account.status" />
                      <button
                        class="cta-button cta-secondary"
                        type="button"
                        :disabled="loading.portalAccess"
                        @click="openPortalAccessPasswordReset(account)"
                      >
                        {{ t("customerAdmin.actions.resetPortalAccessPassword") }}
                      </button>
                      <button
                        v-if="account.status === 'active'"
                        class="cta-button cta-secondary"
                        type="button"
                        :disabled="loading.portalAccess"
                        @click="setCustomerPortalAccessStatus(account, 'inactive')"
                      >
                        {{ t("customerAdmin.actions.deactivatePortalAccess") }}
                      </button>
                      <button
                        v-else
                        class="cta-button cta-secondary"
                        type="button"
                        :disabled="loading.portalAccess"
                        @click="setCustomerPortalAccessStatus(account, 'active')"
                      >
                        {{ t("customerAdmin.actions.activatePortalAccess") }}
                      </button>
                      <button
                        class="cta-button cta-secondary"
                        type="button"
                        :disabled="loading.portalAccess"
                        @click="unlinkCustomerPortalAccount(account)"
                      >
                        {{ t("customerAdmin.actions.unlinkPortalAccess") }}
                      </button>
                    </div>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">
                  {{ t("customerAdmin.portalAccess.empty") }}
                </p>
              </section>

              <section class="customer-admin-form-section">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.loginHistory.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.loginHistory.title") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshCustomerPortalLoginHistory">
                    {{ t("customerAdmin.actions.refreshLoginHistory") }}
                  </button>
                </div>
                <div v-if="customerPortalLoginHistory.length" class="customer-admin-record-list">
                  <article
                    v-for="entry in customerPortalLoginHistory"
                    :key="entry.id"
                    class="customer-admin-record customer-admin-record--stacked"
                  >
                    <div class="customer-admin-record__body">
                      <strong>{{ entry.identifier }}</strong>
                      <span class="customer-admin-record__meta">{{ formatLoginHistoryMeta(entry) }}</span>
                    </div>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.loginHistory.empty") }}</p>
              </section>
            </div>

            <div
              v-if="portalAccessModalOpen"
              class="customer-admin-modal-backdrop"
              data-testid="customer-portal-access-create-modal"
            >
              <section class="module-card customer-admin-modal">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.portalAccess.modalEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.portalAccess.modalTitle") }}</h4>
                </div>
                <p class="field-help">{{ selectedCustomer?.name }}</p>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.portalAccess.contactLabel") }}</span>
                    <select v-model="portalAccessDraft.contact_id">
                      <option value="">{{ t("customerAdmin.portalAccess.contactPlaceholder") }}</option>
                      <option
                        v-for="contact in portalAccessAvailableContacts"
                        :key="contact.id"
                        :value="contact.id"
                      >
                        {{ contact.full_name }}{{ contact.email ? ` · ${contact.email}` : "" }}
                      </option>
                    </select>
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.username") }}</span>
                    <input v-model="portalAccessDraft.username" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.email") }}</span>
                    <input v-model="portalAccessDraft.email" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.fullName") }}</span>
                    <input v-model="portalAccessDraft.full_name" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.locale") }}</span>
                    <select v-model="portalAccessDraft.locale">
                      <option value="de">de</option>
                      <option value="en">en</option>
                    </select>
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.lifecycleStatus") }}</span>
                    <select v-model="portalAccessDraft.status">
                      <option value="active">{{ t("customerAdmin.status.active") }}</option>
                      <option value="inactive">{{ t("customerAdmin.status.inactive") }}</option>
                    </select>
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.temporaryPassword") }}</span>
                    <input v-model="portalAccessDraft.temporary_password" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="button" :disabled="loading.portalAccess" @click="submitCustomerPortalAccess">
                    {{ t("customerAdmin.actions.createPortalAccess") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="closePortalAccessCreateModal">
                    {{ t("customerAdmin.actions.cancel") }}
                  </button>
                </div>
              </section>
            </div>

            <div
              v-if="portalAccessPasswordTarget"
              class="customer-admin-modal-backdrop"
              data-testid="customer-portal-access-password-modal"
            >
              <section class="module-card customer-admin-modal">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.portalAccess.passwordResetEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.portalAccess.passwordResetTitle") }}</h4>
                </div>
                <p class="field-help">
                  {{ portalAccessPasswordTarget.contact_name }} · {{ portalAccessPasswordTarget.username }}
                </p>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                  <label class="field-stack field-stack--wide">
                    <span>{{ t("customerAdmin.fields.temporaryPassword") }}</span>
                    <input v-model="portalAccessPasswordDraft.temporary_password" />
                  </label>
                </div>
                <div class="cta-row">
                  <button
                    class="cta-button"
                    type="button"
                    :disabled="loading.portalAccess"
                    @click="submitCustomerPortalAccessPasswordReset"
                  >
                    {{ t("customerAdmin.actions.resetPortalAccessPassword") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="closePortalAccessPasswordReset">
                    {{ t("customerAdmin.actions.cancel") }}
                  </button>
                </div>
              </section>
            </div>
          </section>

          <section
            v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'history'"
            class="customer-admin-section"
            data-testid="customer-tab-panel-history"
          >
            <div class="customer-admin-form customer-admin-form--structured">
              <section class="customer-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.history.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.history.title") }}</h4>
                </div>
                <p class="field-help">{{ t("customerAdmin.history.lead") }}</p>
              </section>

              <section class="customer-admin-form-section">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.history.registerEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.history.registerTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshHistory">
                    {{ t("customerAdmin.actions.refreshHistory") }}
                  </button>
                </div>
                <div v-if="customerHistory.length" class="customer-admin-record-list">
                  <article
                    v-for="entry in customerHistory"
                    :key="entry.id"
                    class="customer-admin-record customer-admin-record--stacked"
                  >
                    <div class="customer-admin-record__body">
                      <strong>{{ entry.title }}</strong>
                      <p>{{ entry.summary }}</p>
                      <span class="customer-admin-record__meta">{{ formatHistoryMeta(entry) }}</span>
                      <ul v-if="entry.attachments.length" class="customer-admin-inline-list">
                        <li v-for="attachment in entry.attachments" :key="attachment.document_id">
                          {{ attachment.title }}
                        </li>
                      </ul>
                    </div>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.history.empty") }}</p>
              </section>

              <form class="customer-admin-form-section" @submit.prevent="submitHistoryAttachmentLink">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.history.attachmentEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.history.attachmentTitle") }}</h4>
                </div>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.historyEntry") }}</span>
                    <select v-model="historyAttachmentDraft.history_entry_id">
                      <option v-for="entry in customerHistory" :key="entry.id" :value="entry.id">
                        {{ entry.title }}
                      </option>
                    </select>
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.documentId") }}</span>
                    <input v-model="historyAttachmentDraft.document_id" :disabled="!canWrite" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.label") }}</span>
                    <input v-model="historyAttachmentDraft.label" :disabled="!canWrite" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="submit" :disabled="!canWrite || loading.historyAttachment">
                    {{ t("customerAdmin.actions.linkHistoryAttachment") }}
                  </button>
                </div>
              </form>
            </div>
          </section>

          <section
            v-if="selectedCustomer && !isCreatingCustomer && activeDetailTab === 'employee_blocks'"
            class="customer-admin-section"
            data-testid="customer-tab-panel-employee-blocks"
          >
            <div class="customer-admin-form customer-admin-form--structured">
              <section class="customer-admin-editor-intro">
                <div>
                  <p class="eyebrow">{{ t("customerAdmin.employeeBlocks.eyebrow") }}</p>
                  <h4>{{ t("customerAdmin.employeeBlocks.title") }}</h4>
                </div>
                <p class="field-help">
                  {{
                    employeeBlockCapability?.message_key
                      ? t(employeeBlockCapability.message_key as never)
                      : t("customerAdmin.employeeBlocks.capability.pendingEmployees")
                  }}
                </p>
              </section>

              <section class="customer-admin-form-section">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.employeeBlocks.registerEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.employeeBlocks.registerTitle") }}</h4>
                </div>
                <div class="cta-row">
                  <button class="cta-button cta-secondary" type="button" :disabled="!canRead" @click="refreshEmployeeBlocks">
                    {{ t("customerAdmin.actions.refreshEmployeeBlocks") }}
                  </button>
                </div>
                <div v-if="customerEmployeeBlocks.length" class="customer-admin-record-list">
                  <article
                    v-for="block in customerEmployeeBlocks"
                    :key="block.id"
                    class="customer-admin-record customer-admin-record--stacked"
                  >
                    <div class="customer-admin-record__body">
                      <strong>{{ block.employee_id }}</strong>
                      <p>{{ block.reason }}</p>
                      <span class="customer-admin-record__meta">
                        {{ block.effective_from }}{{ block.effective_to ? ` - ${block.effective_to}` : "" }}
                      </span>
                    </div>
                    <button class="cta-button cta-secondary" type="button" :disabled="!canWrite" @click="editEmployeeBlock(block)">
                      {{ t("customerAdmin.actions.edit") }}
                    </button>
                  </article>
                </div>
                <p v-else class="customer-admin-list-empty">{{ t("customerAdmin.employeeBlocks.empty") }}</p>
              </section>

              <form class="customer-admin-form-section" @submit.prevent="submitEmployeeBlock">
                <div class="customer-admin-form-section__header">
                  <p class="eyebrow">{{ t("customerAdmin.employeeBlocks.editorEyebrow") }}</p>
                  <h4>{{ t("customerAdmin.employeeBlocks.editorTitle") }}</h4>
                </div>
                <div class="customer-admin-form-grid customer-admin-form-grid--detail">
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.employeeId") }}</span>
                    <input v-model="employeeBlockDraft.employee_id" :disabled="!canWrite" />
                  </label>
                  <label class="field-stack field-stack--half">
                    <span>{{ t("customerAdmin.fields.reason") }}</span>
                    <input v-model="employeeBlockDraft.reason" :disabled="!canWrite" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.effectiveFrom") }}</span>
                    <input v-model="employeeBlockDraft.effective_from" type="date" :disabled="!canWrite" />
                  </label>
                  <label class="field-stack field-stack--third">
                    <span>{{ t("customerAdmin.fields.effectiveTo") }}</span>
                    <input v-model="employeeBlockDraft.effective_to" type="date" :disabled="!canWrite" />
                  </label>
                </div>
                <div class="cta-row">
                  <button class="cta-button" type="submit" :disabled="!canWrite || loading.employeeBlock">
                    {{ editingEmployeeBlockId ? t("customerAdmin.actions.saveEmployeeBlock") : t("customerAdmin.actions.createEmployeeBlock") }}
                  </button>
                  <button class="cta-button cta-secondary" type="button" @click="resetEmployeeBlockDraft">
                    {{ t("customerAdmin.actions.cancel") }}
                  </button>
                </div>
              </form>
            </div>
          </section>
        </template>

        <section v-else class="customer-admin-empty">
          <p class="eyebrow">{{ t("customerAdmin.detail.emptyTitle") }}</p>
          <h3>{{ t("customerAdmin.detail.emptyBody") }}</h3>
        </section>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";

import { webAppConfig } from "@/config/env";
import {
  createCustomerAvailableAddress,
  createCustomerEmployeeBlock,
  createCustomer,
  createCustomerAddress,
  createCustomerInvoiceParty,
  createCustomerContact,
  createCustomerRateCard,
  createCustomerRateLine,
  createCustomerSurchargeRule,
  CustomerAdminApiError,
  exportCustomers,
  exportCustomerVCard,
  getCustomer,
  getCustomerCommercialProfile,
  getCustomerReferenceData,
  getCustomerPortalPrivacy,
  linkCustomerHistoryAttachment,
  listCustomerAvailableAddresses,
  listCustomerEmployeeBlocks,
  listCustomerHistory,
  listCustomerPortalLoginHistory,
  listCustomers,
  type CustomerBillingProfilePayload,
  type CustomerBillingProfileRead,
  type CustomerAddressPayload,
  type CustomerAddressRead,
  type CustomerAvailableAddressCreatePayload,
  type CustomerAvailableAddressRead,
  type CustomerContactPayload,
  type CustomerContactRead,
  type CustomerCommercialProfileRead,
  type CustomerCreatePayload,
  type CustomerEmployeeBlockCollectionRead,
  type CustomerEmployeeBlockPayload,
  type CustomerEmployeeBlockRead,
  type CustomerEmployeeBlockUpdatePayload,
  type CustomerFilterParams,
  type CustomerHistoryEntryRead,
  type CustomerLoginHistoryEntryRead,
  type CustomerInvoicePartyPayload,
  type CustomerInvoicePartyRead,
  type CustomerListItem,
  type CustomerPortalPrivacyRead,
  type CustomerRateCardPayload,
  type CustomerRateCardRead,
  type CustomerRateLinePayload,
  type CustomerRateLineRead,
  type CustomerReferenceDataRead,
  type CustomerRead,
  type CustomerSurchargeRulePayload,
  type CustomerSurchargeRuleRead,
  updateCustomerBillingProfile,
  updateCustomer,
  updateCustomerAddress,
  updateCustomerContact,
  updateCustomerInvoiceParty,
  updateCustomerPortalPrivacy,
  updateCustomerEmployeeBlock,
  updateCustomerRateCard,
  updateCustomerRateLine,
  updateCustomerSurchargeRule,
  upsertCustomerBillingProfile,
} from "@/api/customers";
import StatusBadge from "@/components/StatusBadge.vue";
import {
  applySurchargeAmountMode,
  buildWeekdayMask,
  COMMON_CURRENCY_OPTIONS,
  buildCommercialConfirmationKey,
  deriveCustomerCommercialActionState,
  minutesToTimeInput,
  mapCustomerCommercialApiMessage,
  normalizeRateLinePayloadDraft,
  parseWeekdayMask,
  RATE_LINE_BILLING_UNIT_OPTIONS,
  RATE_LINE_KIND_OPTIONS,
  RATE_LINE_PLANNING_MODE_OPTIONS,
  resolveBillingProfileApiError,
  resolveBillingProfileFeedbackError,
  resolveInvoicePartyApiError,
  resolveSurchargeAmountMode,
  SURCHARGE_TYPE_OPTIONS,
  timeInputToMinutes,
  validateSurchargeRuleAgainstRateCardWindow,
  validateBillingProfileDraft,
  validateRateCardDraft,
  validateRateLineDraft,
  validateSurchargeRuleDraft,
} from "@/features/customers/customerCommercial.helpers.js";
import {
  CUSTOMER_COMMERCIAL_TAB_ORDER,
  buildCustomerDetailTabs,
  buildCustomerDraftPayload,
  buildCustomerReferenceMaps,
  buildLifecyclePayload,
  deriveCustomerActionState,
  filterCustomerMandatesByBranch,
  formatCustomerReferenceOptionLabel as formatCustomerReferenceOptionOnlyLabel,
  formatPrimaryContactSummary,
  hasCustomerPermission,
  mapCustomerApiMessage,
  normalizeCustomerCommercialTab,
  normalizeCustomerDetailTab,
  resolveCustomerAdminRouteContext,
  resolveCustomerAdminSectionVisibility,
  resolveCustomerAdminSessionScope,
  resolveCustomerCancelSelection,
} from "@/features/customers/customerAdmin.helpers.js";
import {
  EmployeeAdminApiError,
  bootstrapEmployeeCatalogSamples,
} from "@/api/employeeAdmin";
import {
  createCustomerPortalAccess,
  listCustomerPortalAccess,
  resetCustomerPortalAccessPassword,
  type CustomerPortalAccessCreatePayload,
  type CustomerPortalAccessListItem,
  unlinkCustomerPortalAccess,
  updateCustomerPortalAccessStatus,
} from "#/api/sicherplan/customer-portal-access";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/stores/auth";
import { useRoute, useRouter } from "vue-router";

const props = withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const ACCESS_TOKEN_STORAGE_KEY = "sicherplan-access-token";
const { t } = useI18n();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const customers = ref<CustomerListItem[]>([]);
const customerHistory = ref<CustomerHistoryEntryRead[]>([]);
const customerPortalLoginHistory = ref<CustomerLoginHistoryEntryRead[]>([]);
const customerPortalAccessAccounts = ref<CustomerPortalAccessListItem[]>([]);
const customerEmployeeBlocks = ref<CustomerEmployeeBlockRead[]>([]);
const employeeBlockCapability = ref<CustomerEmployeeBlockCollectionRead["capability"] | null>(null);
const commercialProfile = ref<CustomerCommercialProfileRead | null>(null);
const portalPrivacy = ref<CustomerPortalPrivacyRead | null>(null);
const referenceData = ref<CustomerReferenceDataRead | null>(null);
const availableAddressDirectory = ref<CustomerAvailableAddressRead[]>([]);
const stagedAddressDirectoryByCustomer = reactive<Record<string, CustomerAvailableAddressRead[]>>({});
const selectedCustomer = ref<CustomerRead | null>(null);
const selectedCustomerId = ref("");
const previousSelectedCustomer = ref<CustomerRead | null>(null);
const isCreatingCustomer = ref(false);
const activeDetailTab = ref("");
const activeCommercialTab = ref("billing_profile");
const activePricingRulesTab = ref("rate_cards");
const editingContactId = ref("");
const editingAddressId = ref("");
const editingInvoicePartyId = ref("");
const editingRateCardId = ref("");
const selectedRateCardId = ref("");
const editingRateLineId = ref("");
const editingSurchargeRuleId = ref("");
const editingEmployeeBlockId = ref("");
const tenantScopeInput = ref(authStore.tenantScopeId);
const tenantScopeId = ref(authStore.tenantScopeId);
const accessTokenInput = ref(readStoredAccessToken());
const accessToken = ref(readStoredAccessToken());
const attemptedHrCatalogBootstrap = ref(false);
const portalAccessGeneratedPassword = ref("");
const portalAccessModalOpen = ref(false);
const portalAccessPasswordTarget = ref<CustomerPortalAccessListItem | null>(null);
const addressDirectoryModalOpen = ref(false);
const pendingRouteCustomerId = ref("");
const pendingRouteDetailTab = ref("");
const billingProfileErrorState = reactive<{
  summaryTitle: string;
  summaryBody: string;
  primaryMessage: string;
  fields: Record<string, string>;
}>({
  summaryTitle: "",
  summaryBody: "",
  primaryMessage: "",
  fields: {},
});
const invoicePartyErrorState = reactive<{
  fields: Record<string, string>;
}>({
  fields: {},
});
const loading = reactive({
  list: false,
  detail: false,
  customer: false,
  contact: false,
  address: false,
  commercial: false,
  rateLine: false,
  surchargeRule: false,
  historyAttachment: false,
  loginHistory: false,
  portalAccess: false,
  employeeBlock: false,
  portalPrivacy: false,
  sharedAddress: false,
  hrCatalogBootstrap: false,
});
const feedback = reactive({
  tone: "info",
  title: "",
  message: "",
});
const filters = reactive<CustomerFilterParams>({
  search: "",
  lifecycle_status: "",
  default_branch_id: "",
  default_mandate_id: "",
  include_archived: false,
});
const addressDirectorySearch = ref("");
const customerDraft = reactive<CustomerCreatePayload>({
  tenant_id: "",
  customer_number: "",
  name: "",
  status: "active",
  legal_name: "",
  external_ref: "",
  legal_form_lookup_id: "",
  classification_lookup_id: "",
  ranking_lookup_id: "",
  customer_status_lookup_id: "",
  default_branch_id: "",
  default_mandate_id: "",
  notes: "",
});
const contactDraft = reactive<CustomerContactPayload>({
  tenant_id: "",
  customer_id: "",
  full_name: "",
  title: "",
  function_label: "",
  email: "",
  phone: "",
  mobile: "",
  is_primary_contact: false,
  is_billing_contact: false,
  user_id: "",
  notes: "",
});
const addressDraft = reactive<CustomerAddressPayload>({
  tenant_id: "",
  customer_id: "",
  address_id: "",
  address_type: "billing",
  label: "",
  is_default: false,
});
const addressDirectoryDraft = reactive<CustomerAvailableAddressCreatePayload>({
  street_line_1: "",
  street_line_2: "",
  postal_code: "",
  city: "",
  state: "",
  country_code: "DE",
});
const billingProfileDraft = reactive<CustomerBillingProfilePayload>({
  tenant_id: "",
  customer_id: "",
  invoice_email: "",
  payment_terms_days: null,
  payment_terms_note: "",
  tax_number: "",
  vat_id: "",
  tax_exempt: false,
  tax_exemption_reason: "",
  bank_account_holder: "",
  bank_iban: "",
  bank_bic: "",
  bank_name: "",
  contract_reference: "",
  debtor_number: "",
  e_invoice_enabled: false,
  leitweg_id: "",
  invoice_layout_code: "standard",
  shipping_method_code: "email_pdf",
  dunning_policy_code: "standard",
  billing_note: "",
});
const invoicePartyDraft = reactive<CustomerInvoicePartyPayload>({
  tenant_id: "",
  customer_id: "",
  company_name: "",
  contact_name: "",
  address_id: "",
  invoice_email: "",
  invoice_layout_lookup_id: "",
  external_ref: "",
  is_default: false,
  note: "",
});
const rateCardDraft = reactive<CustomerRateCardPayload>({
  tenant_id: "",
  customer_id: "",
  rate_kind: "",
  currency_code: "EUR",
  effective_from: "",
  effective_to: "",
  notes: "",
});
const rateLineDraft = reactive<CustomerRateLinePayload>({
  tenant_id: "",
  rate_card_id: "",
  line_kind: "",
  function_type_id: "",
  qualification_type_id: "",
  planning_mode_code: "",
  billing_unit: "",
  unit_price: "",
  minimum_quantity: "",
  sort_order: 100,
  notes: "",
});
const surchargeAmountMode = ref<"fixed" | "percent">("percent");
const surchargeSelectedWeekdays = ref<string[]>([]);
const surchargeTimeFromInput = ref("");
const surchargeTimeToInput = ref("");
const surchargeRuleDraft = reactive<CustomerSurchargeRulePayload>({
  tenant_id: "",
  rate_card_id: "",
  surcharge_type: "",
  effective_from: "",
  effective_to: "",
  weekday_mask: "",
  time_from_minute: null,
  time_to_minute: null,
  region_code: "",
  percent_value: "",
  fixed_amount: "",
  currency_code: "",
  sort_order: 100,
  notes: "",
});
const historyAttachmentDraft = reactive({
  history_entry_id: "",
  document_id: "",
  label: "",
});
const employeeBlockDraft = reactive<CustomerEmployeeBlockPayload>({
  tenant_id: "",
  customer_id: "",
  employee_id: "",
  reason: "",
  effective_from: "",
  effective_to: "",
});
const portalPrivacyDraft = reactive({
  person_names_released: false,
});
const portalAccessDraft = reactive<CustomerPortalAccessCreatePayload>({
  tenant_id: "",
  customer_id: "",
  contact_id: "",
  username: "",
  email: "",
  full_name: "",
  locale: "de",
  timezone: "Europe/Berlin",
  status: "active",
  temporary_password: "",
});
const portalAccessPasswordDraft = reactive({
  temporary_password: "",
});

const actionState = computed(() => deriveCustomerActionState(authStore.activeRole, selectedCustomer.value));
const commercialActionState = computed(() => deriveCustomerCommercialActionState(authStore.activeRole));
const canRead = computed(() => actionState.value.canRead);
const canWrite = computed(() => actionState.value.canCreate);
const canReadCommercial = computed(() => commercialActionState.value.canReadCommercial);
const canWriteCommercial = computed(() => commercialActionState.value.canWriteCommercial);
const isDevelopmentEnv = computed(() => webAppConfig.env === "development");
const canBootstrapHrCatalogSamples = computed(() =>
  isDevelopmentEnv.value
  && !!tenantScopeId.value
  && !!accessToken.value
  && ["platform_admin", "tenant_admin"].includes(authStore.activeRole ?? ""),
);
const canManagePortalAccess = computed(() =>
  hasCustomerPermission(authStore.activeRole, "customers.portal_access.write"),
);
const hasDetailWorkspace = computed(() => isCreatingCustomer.value || !!selectedCustomer.value);
const detailTabLabelKeys = {
  overview: "customerAdmin.tabs.overview",
  contacts: "customerAdmin.tabs.contacts",
  addresses: "customerAdmin.tabs.addresses",
  commercial: "customerAdmin.tabs.commercial",
  portal: "customerAdmin.tabs.portal",
  history: "customerAdmin.tabs.history",
  employee_blocks: "customerAdmin.tabs.employeeBlocks",
} as const;
const customerDetailTabs = computed(() =>
  buildCustomerDetailTabs({
    canReadCommercial: canReadCommercial.value,
    hasSelectedCustomer: !!selectedCustomer.value,
    isCreatingCustomer: isCreatingCustomer.value,
  }).map((tabId) => ({
    id: tabId,
    label: t(detailTabLabelKeys[tabId as keyof typeof detailTabLabelKeys] as never),
  })),
);
const commercialTabLabelKeys = {
  billing_profile: "customerAdmin.commercial.tabs.billingProfile",
  invoice_parties: "customerAdmin.commercial.tabs.invoiceParties",
  pricing_rules: "customerAdmin.commercial.tabs.pricingRules",
} as const;
const commercialTabs = computed(() =>
  CUSTOMER_COMMERCIAL_TAB_ORDER.map((tabId) => ({
    id: tabId,
    label: t(commercialTabLabelKeys[tabId as keyof typeof commercialTabLabelKeys] as never),
  })),
);
const pricingRulesTabLabelKeys = {
  rate_cards: "customerAdmin.commercial.pricingTabs.rateCards",
  rate_lines: "customerAdmin.commercial.pricingTabs.rateLines",
  surcharges: "customerAdmin.commercial.pricingTabs.surcharges",
} as const;
const primaryContactSummary = computed(() => formatPrimaryContactSummary(selectedCustomer.value));
const referenceMaps = computed(() => buildCustomerReferenceMaps(referenceData.value));
const classificationOptions = computed(() => referenceData.value?.classifications ?? []);
const rankingOptions = computed(() => referenceData.value?.rankings ?? []);
const customerStatusMetadataOptions = computed(() => referenceData.value?.customer_statuses ?? []);
const hasCustomerMetadataCatalogGap = computed(() =>
  classificationOptions.value.length === 0
  || rankingOptions.value.length === 0
  || customerStatusMetadataOptions.value.length === 0,
);
const branchOptions = computed(() => referenceData.value?.branches ?? []);
const filteredCustomerMandates = computed(() =>
  filterMandateOptions(customerDraft.default_branch_id),
);
const selectedCustomerBranchLabel = computed(() => {
  const branchId = selectedCustomer.value?.default_branch_id;
  return branchId ? referenceMaps.value.branches.get(branchId) ?? branchId : "";
});
const billingInvoiceLayoutOptions = computed(() => referenceData.value?.invoice_layouts ?? []);
const billingShippingMethodOptions = computed(() => referenceData.value?.shipping_methods ?? []);
const billingDunningPolicyOptions = computed(() => referenceData.value?.dunning_policies ?? []);
const invoicePartyInvoiceLayoutOptions = computed(() => referenceData.value?.invoice_layouts ?? []);
const rateLineFunctionTypeOptions = computed(() => referenceData.value?.function_types ?? []);
const rateLineQualificationTypeOptions = computed(() => referenceData.value?.qualification_types ?? []);
const isRateLineFunctionCatalogEmpty = computed(() => rateLineFunctionTypeOptions.value.length === 0);
const isRateLineQualificationCatalogEmpty = computed(() => rateLineQualificationTypeOptions.value.length === 0);
const isRateLineHrCatalogEmpty = computed(() =>
  isRateLineFunctionCatalogEmpty.value || isRateLineQualificationCatalogEmpty.value,
);
const rateLineHrCatalogEmptyMessageKey = computed(() =>
  canBootstrapHrCatalogSamples.value
    ? "customerAdmin.commercial.hrCatalogEmptyDevHint"
    : "customerAdmin.commercial.hrCatalogEmptyManagedHint",
);
const invoicePartyInvoiceLayoutPlaceholder = computed(() =>
  invoicePartyInvoiceLayoutOptions.value.length
    ? t("customerAdmin.commercial.invoicePartyLayoutPlaceholder")
    : t("customerAdmin.commercial.invoicePartyLayoutEmptyPlaceholder"),
);
const editingRateLine = computed(() =>
  selectedRateCard.value?.rate_lines.find((row) => row.id === editingRateLineId.value) ?? null,
);
const rateLineFunctionTypeSelectOptions = computed(() => {
  const options = new Map(rateLineFunctionTypeOptions.value.map((option) => [option.id, option]));
  const fallback = editingRateLine.value?.function_type;
  if (fallback?.id) {
    options.set(fallback.id, fallback);
  } else if (rateLineDraft.function_type_id && !options.has(rateLineDraft.function_type_id)) {
    options.set(rateLineDraft.function_type_id, {
      id: rateLineDraft.function_type_id,
      code: rateLineDraft.function_type_id,
      label: rateLineDraft.function_type_id,
      description: null,
      is_active: false,
      status: "archived",
      archived_at: null,
    });
  }
  return [...options.values()];
});
const rateLineQualificationTypeSelectOptions = computed(() => {
  const options = new Map(rateLineQualificationTypeOptions.value.map((option) => [option.id, option]));
  const fallback = editingRateLine.value?.qualification_type;
  if (fallback?.id) {
    options.set(fallback.id, fallback);
  } else if (rateLineDraft.qualification_type_id && !options.has(rateLineDraft.qualification_type_id)) {
    options.set(rateLineDraft.qualification_type_id, {
      id: rateLineDraft.qualification_type_id,
      code: rateLineDraft.qualification_type_id,
      label: rateLineDraft.qualification_type_id,
      description: null,
      is_active: false,
      status: "archived",
      archived_at: null,
    });
  }
  return [...options.values()];
});
const invoicePartyAddressOptions = computed(() =>
  (selectedCustomer.value?.addresses ?? [])
    .filter((address) => address.status !== "archived")
    .map((address) => ({
      value: address.address_id,
      label: formatInvoicePartyAddressOption(address),
    })),
);
const invoicePartyAddressPlaceholder = computed(() =>
  invoicePartyAddressOptions.value.length
    ? t("customerAdmin.commercial.invoicePartyAddressPlaceholder")
    : t("customerAdmin.commercial.invoicePartyAddressEmptyPlaceholder"),
);
const customerAddressLinkOptions = computed(() => {
  const linkedAddressIds = new Set(
    (selectedCustomer.value?.addresses ?? [])
      .filter(
        (address) =>
          address.id !== editingAddressId.value
          && address.address_type === addressDraft.address_type
          && address.archived_at == null,
      )
      .map((address) => address.address_id),
  );
  return availableAddressDirectory.value
    .filter((address) => !linkedAddressIds.has(address.id))
    .map((address) => ({
      value: address.id,
      label: formatAddressDirectoryOption(address),
    }));
});
const customerAddressLinkPlaceholder = computed(() =>
  customerAddressLinkOptions.value.length
    ? t("customerAdmin.addresses.addressLinkPlaceholder")
    : t("customerAdmin.addresses.addressLinkEmptyPlaceholder"),
);
const selectedCustomerMandateLabel = computed(() => {
  const mandateId = selectedCustomer.value?.default_mandate_id;
  return mandateId ? referenceMaps.value.mandates.get(mandateId) ?? mandateId : "";
});
const selectedCustomerClassificationLabel = computed(() => {
  const lookupId = selectedCustomer.value?.classification_lookup_id;
  return lookupId ? referenceMaps.value.classifications.get(lookupId) ?? lookupId : "";
});
const selectedCustomerRankingLabel = computed(() => {
  const lookupId = selectedCustomer.value?.ranking_lookup_id;
  return lookupId ? referenceMaps.value.rankings.get(lookupId) ?? lookupId : "";
});
const selectedCustomerStatusLabel = computed(() => {
  const lookupId = selectedCustomer.value?.customer_status_lookup_id;
  return lookupId ? referenceMaps.value.customerStatuses.get(lookupId) ?? lookupId : "";
});
const portalAccessAvailableContacts = computed(() =>
  (selectedCustomer.value?.contacts ?? []).filter(
    (contact) => contact.archived_at == null && contact.status === "active",
  ),
);
const selectedPortalAccessContact = computed(() =>
  portalAccessAvailableContacts.value.find((contact) => contact.id === portalAccessDraft.contact_id) ?? null,
);
const selectedRateCard = computed(() =>
  commercialProfile.value?.rate_cards.find((row) => row.id === selectedRateCardId.value) ?? null,
);
const pricingRulesTabs = computed(() => {
  const hasRateCards = !!commercialProfile.value?.rate_cards.length;
  const tabIds = hasRateCards ? ["rate_cards", "rate_lines", "surcharges"] : ["rate_cards"];
  return tabIds.map((tabId) => ({
    id: tabId,
    label: t(pricingRulesTabLabelKeys[tabId as keyof typeof pricingRulesTabLabelKeys] as never),
  }));
});
const surchargeWeekdayOptions = computed(() => [
  { id: "mon", label: t("customerAdmin.weekday.mon" as never) },
  { id: "tue", label: t("customerAdmin.weekday.tue" as never) },
  { id: "wed", label: t("customerAdmin.weekday.wed" as never) },
  { id: "thu", label: t("customerAdmin.weekday.thu" as never) },
  { id: "fri", label: t("customerAdmin.weekday.fri" as never) },
  { id: "sat", label: t("customerAdmin.weekday.sat" as never) },
  { id: "sun", label: t("customerAdmin.weekday.sun" as never) },
]);
const surchargeCurrencyOptions = computed(() => {
  const values = new Set(COMMON_CURRENCY_OPTIONS.map((option) => option.value));
  const rateCardCurrency = `${selectedRateCard.value?.currency_code ?? ""}`.trim().toUpperCase();
  if (rateCardCurrency) {
    values.add(rateCardCurrency);
  }
  return [...values].map(
    (value) => COMMON_CURRENCY_OPTIONS.find((option) => option.value === value) ?? { value, label: value },
  );
});
const hasInvalidSurchargeTimeRange = computed(() => {
  const from = timeInputToMinutes(surchargeTimeFromInput.value);
  const to = timeInputToMinutes(surchargeTimeToInput.value);
  return from !== null && to !== null && to <= from;
});
const surchargeRateCardWindowValidationKey = computed(() =>
  selectedRateCard.value
    ? validateSurchargeRuleAgainstRateCardWindow(selectedRateCard.value, surchargeRuleDraft)
    : null,
);
const surchargeAllowedWindowHelper = computed(() => {
  const rateCard = selectedRateCard.value;
  if (!rateCard?.effective_from) {
    return "";
  }
  if (rateCard.effective_to) {
    return t("customerAdmin.commercial.surchargeAllowedWindowBounded" as never, {
      from: rateCard.effective_from,
      to: rateCard.effective_to,
    });
  }
  return t("customerAdmin.commercial.surchargeAllowedWindowOpenEnded" as never, {
    from: rateCard.effective_from,
  });
});
const surchargeEffectiveToInputMin = computed(() => {
  const rateCardStart = `${selectedRateCard.value?.effective_from ?? ""}`.trim();
  const draftStart = `${surchargeRuleDraft.effective_from ?? ""}`.trim();
  if (rateCardStart && draftStart) {
    return draftStart > rateCardStart ? draftStart : rateCardStart;
  }
  return draftStart || rateCardStart || "";
});
const surchargeEffectiveToRequired = computed(() => !!`${selectedRateCard.value?.effective_to ?? ""}`.trim());
const surchargeMissingEffectiveToForRateCard = computed(() =>
  surchargeEffectiveToRequired.value && !`${surchargeRuleDraft.effective_to ?? ""}`.trim(),
);
const sectionVisibility = computed(() =>
  resolveCustomerAdminSectionVisibility({
    effectiveRole: authStore.effectiveRole,
    embedded: props.embedded,
  }),
);

function formatReferenceOptionLabel(
  record: { code: string; label?: string | null; name?: string | null },
) {
  return formatCustomerReferenceOptionOnlyLabel(record);
}

function filterMandateOptions(branchId: null | string | undefined) {
  return filterCustomerMandatesByBranch(referenceData.value?.mandates ?? [], branchId);
}

function selectedRateCardCurrencyFallback() {
  return `${selectedRateCard.value?.currency_code ?? ""}`.trim().toUpperCase();
}

function syncSurchargeWeekdayMask() {
  surchargeRuleDraft.weekday_mask = buildWeekdayMask(surchargeSelectedWeekdays.value);
}

function toggleSurchargeWeekday(dayId: string) {
  const activeDays = new Set(surchargeSelectedWeekdays.value);
  if (activeDays.has(dayId)) {
    activeDays.delete(dayId);
  } else {
    activeDays.add(dayId);
  }
  surchargeSelectedWeekdays.value = [...activeDays];
  syncSurchargeWeekdayMask();
}

function syncSurchargeTimeDraft() {
  surchargeRuleDraft.time_from_minute = timeInputToMinutes(surchargeTimeFromInput.value);
  surchargeRuleDraft.time_to_minute = timeInputToMinutes(surchargeTimeToInput.value);
}

function setSurchargeAmountMode(mode: "fixed" | "percent") {
  surchargeAmountMode.value = mode;
  const normalized = applySurchargeAmountMode(mode, surchargeRuleDraft, selectedRateCardCurrencyFallback());
  surchargeRuleDraft.percent_value = normalized.percent_value;
  surchargeRuleDraft.fixed_amount = normalized.fixed_amount;
  surchargeRuleDraft.currency_code = normalized.currency_code;
}

function normalizeSurchargeRegionCode() {
  surchargeRuleDraft.region_code = `${surchargeRuleDraft.region_code ?? ""}`.toUpperCase();
}

function readStoredAccessToken() {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? "";
}

function syncTenantAdminSessionState() {
  const sessionScope = resolveCustomerAdminSessionScope({
    effectiveRole: authStore.effectiveRole,
    effectiveTenantScopeId: authStore.effectiveTenantScopeId,
    effectiveAccessToken: authStore.effectiveAccessToken,
    storedAccessToken: accessTokenInput.value,
  });

  tenantScopeInput.value = sessionScope.tenantScopeId;
  tenantScopeId.value = sessionScope.tenantScopeId;
  accessTokenInput.value = sessionScope.accessToken;
  accessToken.value = sessionScope.accessToken;
}

function rememberScopeAndToken() {
  authStore.setTenantScopeId(tenantScopeInput.value);
  tenantScopeId.value = authStore.tenantScopeId;
  accessToken.value = accessTokenInput.value.trim();
  attemptedHrCatalogBootstrap.value = false;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken.value);
  }
  setFeedback("info", t("customerAdmin.feedback.scopeSaved"), t("customerAdmin.feedback.tokenSaved"));
  void refreshCustomers();
}

async function loadReferenceData() {
  if (!tenantScopeId.value || !accessToken.value || !canRead.value) {
    referenceData.value = null;
    return;
  }
  referenceData.value = await getCustomerReferenceData(tenantScopeId.value, accessToken.value);
  if (
    canBootstrapHrCatalogSamples.value
    && !attemptedHrCatalogBootstrap.value
    && (
      referenceData.value.function_types.length === 0
      || referenceData.value.qualification_types.length === 0
    )
  ) {
    attemptedHrCatalogBootstrap.value = true;
    await bootstrapRateLineHrCatalogs({ silentSuccess: true });
  }
}

async function bootstrapRateLineHrCatalogs(options: { silentSuccess?: boolean } = {}) {
  if (!tenantScopeId.value || !accessToken.value || !canBootstrapHrCatalogSamples.value) {
    return;
  }
  loading.hrCatalogBootstrap = true;
  try {
    await bootstrapEmployeeCatalogSamples(tenantScopeId.value, accessToken.value);
    referenceData.value = await getCustomerReferenceData(tenantScopeId.value, accessToken.value);
    if (!options.silentSuccess) {
      setFeedback(
        "success",
        t("customerAdmin.feedback.hrCatalogBootstrapSuccess"),
        t("customerAdmin.feedback.hrCatalogBootstrapSuccessBody"),
      );
    }
  } catch (error) {
    const messageKey =
      error instanceof EmployeeAdminApiError && error.messageKey === "errors.employees.catalog.bootstrap_not_allowed"
        ? "customerAdmin.feedback.hrCatalogBootstrapNotAllowed"
        : "customerAdmin.feedback.hrCatalogBootstrapError";
    setFeedback(
      "error",
      t("customerAdmin.commercial.hrCatalogEmptyTitle"),
      t(messageKey as never),
    );
  } finally {
    loading.hrCatalogBootstrap = false;
  }
}

function handleBootstrapRateLineHrCatalogs() {
  void bootstrapRateLineHrCatalogs();
}

function openEmployeesAdmin() {
  void router.push("/admin/employees");
}

function clearFeedback() {
  feedback.tone = "info";
  feedback.title = "";
  feedback.message = "";
}

function setFeedback(tone: "info" | "success" | "error", title: string, message: string) {
  feedback.tone = tone;
  feedback.title = title;
  feedback.message = message;
}

function clearBillingProfileErrors() {
  billingProfileErrorState.summaryTitle = "";
  billingProfileErrorState.summaryBody = "";
  billingProfileErrorState.primaryMessage = "";
  billingProfileErrorState.fields = {};
}

function clearInvoicePartyErrors(fields: string[] = []) {
  if (!fields.length) {
    invoicePartyErrorState.fields = {};
    return;
  }
  const nextFieldErrors = { ...invoicePartyErrorState.fields };
  for (const field of fields) {
    delete nextFieldErrors[field];
  }
  invoicePartyErrorState.fields = nextFieldErrors;
}

function setInvoicePartyErrors(fields: string[], messageKey: string) {
  const nextFieldErrors: Record<string, string> = {};
  for (const field of fields) {
    nextFieldErrors[field] = t(messageKey as never);
  }
  invoicePartyErrorState.fields = nextFieldErrors;
}

function invoicePartyFieldError(fieldName: string) {
  return invoicePartyErrorState.fields[fieldName] ?? "";
}

function invoicePartyFieldInvalid(fieldName: string) {
  return !!invoicePartyFieldError(fieldName);
}

function setBillingProfileErrors({
  summaryTitleKey,
  summaryBodyKey,
  primaryMessageKey,
  fields,
}: {
  summaryTitleKey: string;
  summaryBodyKey: string;
  primaryMessageKey: string | null;
  fields: string[];
}) {
  billingProfileErrorState.summaryTitle = t(summaryTitleKey as never);
  billingProfileErrorState.summaryBody = t(summaryBodyKey as never);
  billingProfileErrorState.primaryMessage = primaryMessageKey ? t(primaryMessageKey as never) : "";
  const nextFieldErrors: Record<string, string> = {};
  for (const fieldName of fields) {
    if (primaryMessageKey) {
      nextFieldErrors[fieldName] = t(primaryMessageKey as never);
    }
  }
  billingProfileErrorState.fields = nextFieldErrors;
}

function billingProfileFieldError(fieldName: string) {
  return billingProfileErrorState.fields[fieldName] ?? "";
}

function billingProfileFieldInvalid(fieldName: string) {
  return Boolean(billingProfileFieldError(fieldName));
}

function clearBillingProfileFieldErrors(fieldNames: string[]) {
  let changed = false;
  const nextFieldErrors = { ...billingProfileErrorState.fields };
  for (const fieldName of fieldNames) {
    if (nextFieldErrors[fieldName]) {
      delete nextFieldErrors[fieldName];
      changed = true;
    }
  }
  if (!changed) {
    return;
  }
  billingProfileErrorState.fields = nextFieldErrors;
  if (!Object.keys(nextFieldErrors).length) {
    billingProfileErrorState.summaryTitle = "";
    billingProfileErrorState.summaryBody = "";
    billingProfileErrorState.primaryMessage = "";
  }
}

function resetCustomerDraft() {
  customerDraft.tenant_id = tenantScopeId.value;
  customerDraft.customer_number = "";
  customerDraft.name = "";
  customerDraft.status = "active";
  customerDraft.legal_name = "";
  customerDraft.external_ref = "";
  customerDraft.legal_form_lookup_id = "";
  customerDraft.classification_lookup_id = "";
  customerDraft.ranking_lookup_id = "";
  customerDraft.customer_status_lookup_id = "";
  customerDraft.default_branch_id = "";
  customerDraft.default_mandate_id = "";
  customerDraft.notes = "";
}

function resetContactDraft() {
  contactDraft.tenant_id = tenantScopeId.value;
  contactDraft.customer_id = selectedCustomerId.value;
  contactDraft.full_name = "";
  contactDraft.title = "";
  contactDraft.function_label = "";
  contactDraft.email = "";
  contactDraft.phone = "";
  contactDraft.mobile = "";
  contactDraft.is_primary_contact = false;
  contactDraft.is_billing_contact = false;
  contactDraft.user_id = "";
  contactDraft.notes = "";
  editingContactId.value = "";
}

function resetAddressDraft() {
  addressDraft.tenant_id = tenantScopeId.value;
  addressDraft.customer_id = selectedCustomerId.value;
  addressDraft.address_id = "";
  addressDraft.address_type = "billing";
  addressDraft.label = "";
  addressDraft.is_default = false;
  editingAddressId.value = "";
}

function resetAddressDirectoryDraft() {
  addressDirectoryDraft.street_line_1 = "";
  addressDirectoryDraft.street_line_2 = "";
  addressDirectoryDraft.postal_code = "";
  addressDirectoryDraft.city = "";
  addressDirectoryDraft.state = "";
  addressDirectoryDraft.country_code = "DE";
}

function resetBillingProfileDraft() {
  clearBillingProfileErrors();
  billingProfileDraft.tenant_id = tenantScopeId.value;
  billingProfileDraft.customer_id = selectedCustomerId.value;
  billingProfileDraft.invoice_email = "";
  billingProfileDraft.payment_terms_days = null;
  billingProfileDraft.payment_terms_note = "";
  billingProfileDraft.tax_number = "";
  billingProfileDraft.vat_id = "";
  billingProfileDraft.tax_exempt = false;
  billingProfileDraft.tax_exemption_reason = "";
  billingProfileDraft.bank_account_holder = "";
  billingProfileDraft.bank_iban = "";
  billingProfileDraft.bank_bic = "";
  billingProfileDraft.bank_name = "";
  billingProfileDraft.contract_reference = "";
  billingProfileDraft.debtor_number = "";
  billingProfileDraft.e_invoice_enabled = false;
  billingProfileDraft.leitweg_id = "";
  billingProfileDraft.invoice_layout_code = "standard";
  billingProfileDraft.shipping_method_code = "email_pdf";
  billingProfileDraft.dunning_policy_code = "standard";
  billingProfileDraft.billing_note = "";
}

function resetInvoicePartyDraft() {
  clearInvoicePartyErrors();
  invoicePartyDraft.tenant_id = tenantScopeId.value;
  invoicePartyDraft.customer_id = selectedCustomerId.value;
  invoicePartyDraft.company_name = "";
  invoicePartyDraft.contact_name = "";
  invoicePartyDraft.address_id = "";
  invoicePartyDraft.invoice_email = "";
  invoicePartyDraft.invoice_layout_lookup_id = "";
  invoicePartyDraft.external_ref = "";
  invoicePartyDraft.is_default = false;
  invoicePartyDraft.note = "";
  editingInvoicePartyId.value = "";
}

function resetRateCardDraft() {
  rateCardDraft.tenant_id = tenantScopeId.value;
  rateCardDraft.customer_id = selectedCustomerId.value;
  rateCardDraft.rate_kind = "";
  rateCardDraft.currency_code = "EUR";
  rateCardDraft.effective_from = "";
  rateCardDraft.effective_to = "";
  rateCardDraft.notes = "";
  editingRateCardId.value = "";
}

function resetRateLineDraft() {
  rateLineDraft.tenant_id = tenantScopeId.value;
  rateLineDraft.rate_card_id = selectedRateCardId.value;
  rateLineDraft.line_kind = "";
  rateLineDraft.function_type_id = "";
  rateLineDraft.qualification_type_id = "";
  rateLineDraft.planning_mode_code = "";
  rateLineDraft.billing_unit = "";
  rateLineDraft.unit_price = "";
  rateLineDraft.minimum_quantity = "";
  rateLineDraft.sort_order = 100;
  rateLineDraft.notes = "";
  editingRateLineId.value = "";
}

function resetSurchargeRuleDraft() {
  surchargeRuleDraft.tenant_id = tenantScopeId.value;
  surchargeRuleDraft.rate_card_id = selectedRateCardId.value;
  surchargeRuleDraft.surcharge_type = "";
  surchargeRuleDraft.effective_from = selectedRateCard.value?.effective_from ?? "";
  surchargeRuleDraft.effective_to = selectedRateCard.value?.effective_to ?? "";
  surchargeRuleDraft.weekday_mask = "";
  surchargeRuleDraft.time_from_minute = null;
  surchargeRuleDraft.time_to_minute = null;
  surchargeRuleDraft.region_code = "";
  surchargeRuleDraft.percent_value = "";
  surchargeRuleDraft.fixed_amount = "";
  surchargeRuleDraft.currency_code = "";
  surchargeRuleDraft.sort_order = 100;
  surchargeRuleDraft.notes = "";
  surchargeAmountMode.value = "percent";
  surchargeSelectedWeekdays.value = [];
  surchargeTimeFromInput.value = "";
  surchargeTimeToInput.value = "";
  editingSurchargeRuleId.value = "";
}

function resetHistoryAttachmentDraft() {
  historyAttachmentDraft.history_entry_id = customerHistory.value[0]?.id ?? "";
  historyAttachmentDraft.document_id = "";
  historyAttachmentDraft.label = "";
}

function resetEmployeeBlockDraft() {
  employeeBlockDraft.tenant_id = tenantScopeId.value;
  employeeBlockDraft.customer_id = selectedCustomerId.value;
  employeeBlockDraft.employee_id = "";
  employeeBlockDraft.reason = "";
  employeeBlockDraft.effective_from = "";
  employeeBlockDraft.effective_to = "";
  editingEmployeeBlockId.value = "";
}

function resetPortalPrivacyDraft() {
  portalPrivacyDraft.person_names_released = !!portalPrivacy.value?.person_names_released;
}

function resetPortalAccessDraft() {
  portalAccessDraft.tenant_id = tenantScopeId.value;
  portalAccessDraft.customer_id = selectedCustomerId.value;
  portalAccessDraft.contact_id = "";
  portalAccessDraft.username = "";
  portalAccessDraft.email = "";
  portalAccessDraft.full_name = "";
  portalAccessDraft.locale = "de";
  portalAccessDraft.timezone = "Europe/Berlin";
  portalAccessDraft.status = "active";
  portalAccessDraft.temporary_password = "";
}

function applyPortalAccessContactDefaults(contactId: string) {
  const contact = portalAccessAvailableContacts.value.find((row) => row.id === contactId);
  if (!contact) {
    return;
  }
  portalAccessDraft.contact_id = contact.id;
  portalAccessDraft.email = contact.email ?? portalAccessDraft.email;
  portalAccessDraft.full_name = contact.full_name || portalAccessDraft.full_name;
  if (!portalAccessDraft.username.trim()) {
    const usernameSeed = (contact.email ?? contact.full_name).toLowerCase().replace(/[^a-z0-9._-]+/g, ".");
    portalAccessDraft.username = usernameSeed.replace(/(^[._-]+|[._-]+$)/g, "");
  }
}

function openPortalAccessCreateModal() {
  resetPortalAccessDraft();
  portalAccessGeneratedPassword.value = "";
  portalAccessModalOpen.value = true;
}

function closePortalAccessCreateModal() {
  portalAccessModalOpen.value = false;
}

function openAddressDirectoryCreateModal() {
  resetAddressDirectoryDraft();
  addressDirectoryModalOpen.value = true;
}

function closeAddressDirectoryCreateModal() {
  addressDirectoryModalOpen.value = false;
}

function openPortalAccessPasswordReset(account: CustomerPortalAccessListItem) {
  portalAccessPasswordTarget.value = account;
  portalAccessPasswordDraft.temporary_password = "";
}

function closePortalAccessPasswordReset() {
  portalAccessPasswordTarget.value = null;
  portalAccessPasswordDraft.temporary_password = "";
}

function populateCustomerDraft(customer: CustomerRead) {
  customerDraft.tenant_id = customer.tenant_id;
  customerDraft.customer_number = customer.customer_number;
  customerDraft.name = customer.name;
  customerDraft.status = customer.status;
  customerDraft.legal_name = customer.legal_name ?? "";
  customerDraft.external_ref = customer.external_ref ?? "";
  customerDraft.legal_form_lookup_id = customer.legal_form_lookup_id ?? "";
  customerDraft.classification_lookup_id = customer.classification_lookup_id ?? "";
  customerDraft.ranking_lookup_id = customer.ranking_lookup_id ?? "";
  customerDraft.customer_status_lookup_id = customer.customer_status_lookup_id ?? "";
  customerDraft.default_branch_id = customer.default_branch_id ?? "";
  customerDraft.default_mandate_id = customer.default_mandate_id ?? "";
  customerDraft.notes = customer.notes ?? "";
}

function populateBillingProfileDraft(profile: CustomerBillingProfileRead | null) {
  resetBillingProfileDraft();
  if (!profile) {
    return;
  }
  billingProfileDraft.tenant_id = profile.tenant_id;
  billingProfileDraft.customer_id = profile.customer_id;
  billingProfileDraft.invoice_email = profile.invoice_email ?? "";
  billingProfileDraft.payment_terms_days = profile.payment_terms_days;
  billingProfileDraft.payment_terms_note = profile.payment_terms_note ?? "";
  billingProfileDraft.tax_number = profile.tax_number ?? "";
  billingProfileDraft.vat_id = profile.vat_id ?? "";
  billingProfileDraft.tax_exempt = profile.tax_exempt;
  billingProfileDraft.tax_exemption_reason = profile.tax_exemption_reason ?? "";
  billingProfileDraft.bank_account_holder = profile.bank_account_holder ?? "";
  billingProfileDraft.bank_iban = profile.bank_iban ?? "";
  billingProfileDraft.bank_bic = profile.bank_bic ?? "";
  billingProfileDraft.bank_name = profile.bank_name ?? "";
  billingProfileDraft.contract_reference = profile.contract_reference ?? "";
  billingProfileDraft.debtor_number = profile.debtor_number ?? "";
  billingProfileDraft.e_invoice_enabled = profile.e_invoice_enabled;
  billingProfileDraft.leitweg_id = profile.leitweg_id ?? "";
  billingProfileDraft.invoice_layout_code = profile.invoice_layout_code ?? "standard";
  billingProfileDraft.shipping_method_code = profile.shipping_method_code ?? "email_pdf";
  billingProfileDraft.dunning_policy_code = profile.dunning_policy_code ?? "standard";
  billingProfileDraft.billing_note = profile.billing_note ?? "";
}

function editContact(contact: CustomerContactRead) {
  contactDraft.tenant_id = contact.tenant_id;
  contactDraft.customer_id = contact.customer_id;
  contactDraft.full_name = contact.full_name;
  contactDraft.title = contact.title ?? "";
  contactDraft.function_label = contact.function_label ?? "";
  contactDraft.email = contact.email ?? "";
  contactDraft.phone = contact.phone ?? "";
  contactDraft.mobile = contact.mobile ?? "";
  contactDraft.is_primary_contact = contact.is_primary_contact;
  contactDraft.is_billing_contact = contact.is_billing_contact;
  contactDraft.user_id = contact.user_id ?? "";
  contactDraft.notes = contact.notes ?? "";
  editingContactId.value = contact.id;
}

function editAddress(address: CustomerAddressRead) {
  addressDraft.tenant_id = address.tenant_id;
  addressDraft.customer_id = address.customer_id;
  addressDraft.address_id = address.address_id;
  addressDraft.address_type = address.address_type;
  addressDraft.label = address.label ?? "";
  addressDraft.is_default = address.is_default;
  editingAddressId.value = address.id;
}

function editInvoiceParty(invoiceParty: CustomerInvoicePartyRead) {
  invoicePartyDraft.tenant_id = invoiceParty.tenant_id;
  invoicePartyDraft.customer_id = invoiceParty.customer_id;
  invoicePartyDraft.company_name = invoiceParty.company_name;
  invoicePartyDraft.contact_name = invoiceParty.contact_name ?? "";
  invoicePartyDraft.address_id = invoiceParty.address_id;
  invoicePartyDraft.invoice_email = invoiceParty.invoice_email ?? "";
  invoicePartyDraft.invoice_layout_lookup_id = invoiceParty.invoice_layout_lookup_id ?? "";
  invoicePartyDraft.external_ref = invoiceParty.external_ref ?? "";
  invoicePartyDraft.is_default = invoiceParty.is_default;
  invoicePartyDraft.note = invoiceParty.note ?? "";
  editingInvoicePartyId.value = invoiceParty.id;
}

function openCustomerAddressesTab() {
  activeDetailTab.value = "addresses";
}

function editRateCard(rateCard: CustomerRateCardRead) {
  rateCardDraft.tenant_id = rateCard.tenant_id;
  rateCardDraft.customer_id = rateCard.customer_id;
  rateCardDraft.rate_kind = rateCard.rate_kind;
  rateCardDraft.currency_code = rateCard.currency_code;
  rateCardDraft.effective_from = rateCard.effective_from;
  rateCardDraft.effective_to = rateCard.effective_to ?? "";
  rateCardDraft.notes = rateCard.notes ?? "";
  editingRateCardId.value = rateCard.id;
  selectedRateCardId.value = rateCard.id;
  resetRateLineDraft();
  resetSurchargeRuleDraft();
}

function editRateLine(rateLine: CustomerRateLineRead) {
  rateLineDraft.tenant_id = rateLine.tenant_id;
  rateLineDraft.rate_card_id = rateLine.rate_card_id;
  rateLineDraft.line_kind = rateLine.line_kind;
  rateLineDraft.function_type_id = rateLine.function_type_id ?? "";
  rateLineDraft.qualification_type_id = rateLine.qualification_type_id ?? "";
  rateLineDraft.planning_mode_code = rateLine.planning_mode_code ?? "";
  rateLineDraft.billing_unit = rateLine.billing_unit;
  rateLineDraft.unit_price = rateLine.unit_price;
  rateLineDraft.minimum_quantity = rateLine.minimum_quantity ?? "";
  rateLineDraft.sort_order = rateLine.sort_order;
  rateLineDraft.notes = rateLine.notes ?? "";
  editingRateLineId.value = rateLine.id;
}

function editSurchargeRule(rule: CustomerSurchargeRuleRead) {
  surchargeRuleDraft.tenant_id = rule.tenant_id;
  surchargeRuleDraft.rate_card_id = rule.rate_card_id;
  surchargeRuleDraft.surcharge_type = rule.surcharge_type;
  surchargeRuleDraft.effective_from = rule.effective_from;
  surchargeRuleDraft.effective_to = rule.effective_to ?? "";
  surchargeRuleDraft.weekday_mask = rule.weekday_mask ?? "";
  surchargeRuleDraft.time_from_minute = rule.time_from_minute;
  surchargeRuleDraft.time_to_minute = rule.time_to_minute;
  surchargeRuleDraft.region_code = rule.region_code ?? "";
  surchargeRuleDraft.percent_value = rule.percent_value ?? "";
  surchargeRuleDraft.fixed_amount = rule.fixed_amount ?? "";
  surchargeRuleDraft.currency_code = rule.currency_code ?? "";
  surchargeRuleDraft.sort_order = rule.sort_order;
  surchargeRuleDraft.notes = rule.notes ?? "";
  surchargeAmountMode.value = resolveSurchargeAmountMode(rule);
  surchargeSelectedWeekdays.value = parseWeekdayMask(rule.weekday_mask ?? "");
  surchargeTimeFromInput.value = minutesToTimeInput(rule.time_from_minute);
  surchargeTimeToInput.value = minutesToTimeInput(rule.time_to_minute);
  editingSurchargeRuleId.value = rule.id;
}

function editEmployeeBlock(block: CustomerEmployeeBlockRead) {
  employeeBlockDraft.tenant_id = block.tenant_id;
  employeeBlockDraft.customer_id = block.customer_id;
  employeeBlockDraft.employee_id = block.employee_id;
  employeeBlockDraft.reason = block.reason;
  employeeBlockDraft.effective_from = block.effective_from;
  employeeBlockDraft.effective_to = block.effective_to ?? "";
  editingEmployeeBlockId.value = block.id;
}

function startCreateCustomer() {
  previousSelectedCustomer.value = selectedCustomer.value;
  isCreatingCustomer.value = true;
  activeDetailTab.value = "overview";
  activeCommercialTab.value = "billing_profile";
  selectedCustomerId.value = "";
  selectedCustomer.value = null;
  customerHistory.value = [];
  customerPortalLoginHistory.value = [];
  customerPortalAccessAccounts.value = [];
  customerEmployeeBlocks.value = [];
  employeeBlockCapability.value = null;
  portalPrivacy.value = null;
  portalAccessGeneratedPassword.value = "";
  closePortalAccessCreateModal();
  closePortalAccessPasswordReset();
  resetPortalPrivacyDraft();
  resetPortalAccessDraft();
  resetCustomerDraft();
  resetContactDraft();
  resetAddressDraft();
  resetHistoryAttachmentDraft();
  resetEmployeeBlockDraft();
}

function startCreateContact() {
  resetContactDraft();
}

function startCreateAddress() {
  resetAddressDraft();
}

function startCreateInvoiceParty() {
  activeCommercialTab.value = "invoice_parties";
  resetInvoicePartyDraft();
}

function startCreateRateCard() {
  activeCommercialTab.value = "pricing_rules";
  activePricingRulesTab.value = "rate_cards";
  resetRateCardDraft();
}

function startCreateRateLine() {
  activeCommercialTab.value = "pricing_rules";
  activePricingRulesTab.value = "rate_lines";
  resetRateLineDraft();
}

function startCreateSurchargeRule() {
  activeCommercialTab.value = "pricing_rules";
  activePricingRulesTab.value = "surcharges";
  resetSurchargeRuleDraft();
}

function cancelCustomerEdit() {
  if (!isCreatingCustomer.value && selectedCustomer.value) {
    populateCustomerDraft(selectedCustomer.value);
    return;
  }
  const nextState = resolveCustomerCancelSelection(previousSelectedCustomer.value);
  isCreatingCustomer.value = nextState.isCreatingCustomer;
  selectedCustomerId.value = nextState.selectedCustomerId;
  selectedCustomer.value = nextState.selectedCustomer;
  if (selectedCustomer.value) {
    populateCustomerDraft(selectedCustomer.value);
  } else {
    resetCustomerDraft();
    customerHistory.value = [];
    customerPortalLoginHistory.value = [];
    customerPortalAccessAccounts.value = [];
    customerEmployeeBlocks.value = [];
    employeeBlockCapability.value = null;
    portalPrivacy.value = null;
    portalAccessGeneratedPassword.value = "";
    closePortalAccessCreateModal();
    closePortalAccessPasswordReset();
    resetPortalPrivacyDraft();
    resetPortalAccessDraft();
  }
}

async function refreshCustomers() {
  if (!tenantScopeId.value || !accessToken.value || !canRead.value) {
    referenceData.value = null;
    customers.value = [];
    selectedCustomer.value = null;
    customerHistory.value = [];
    customerPortalLoginHistory.value = [];
    customerPortalAccessAccounts.value = [];
    customerEmployeeBlocks.value = [];
    employeeBlockCapability.value = null;
    portalPrivacy.value = null;
    portalAccessGeneratedPassword.value = "";
    closePortalAccessCreateModal();
    closePortalAccessPasswordReset();
    resetPortalPrivacyDraft();
    resetPortalAccessDraft();
    return;
  }

  loading.list = true;
  try {
    await loadReferenceData();
    customers.value = await listCustomers(tenantScopeId.value, accessToken.value, filters);
    if (pendingRouteCustomerId.value) {
      const routeCustomer = customers.value.find((row) => row.id === pendingRouteCustomerId.value);
      if (routeCustomer) {
        await selectCustomer(routeCustomer.id, pendingRouteDetailTab.value);
        return;
      }
    }
    if (selectedCustomerId.value) {
      const stillExists = customers.value.some((row) => row.id === selectedCustomerId.value);
      if (stillExists) {
        await selectCustomer(selectedCustomerId.value);
      } else if (customers.value[0]) {
        await selectCustomer(customers.value[0].id);
      } else {
        selectedCustomer.value = null;
        customerHistory.value = [];
        customerPortalLoginHistory.value = [];
        customerPortalAccessAccounts.value = [];
        customerEmployeeBlocks.value = [];
        employeeBlockCapability.value = null;
        portalPrivacy.value = null;
        portalAccessGeneratedPassword.value = "";
        closePortalAccessCreateModal();
        closePortalAccessPasswordReset();
        resetPortalPrivacyDraft();
        resetPortalAccessDraft();
      }
    } else if (customers.value[0] && !isCreatingCustomer.value) {
      await selectCustomer(customers.value[0].id);
    }
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.list = false;
  }
}

async function selectCustomer(customerId: string, preferredTab = "") {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }

  loading.detail = true;
  try {
    selectedCustomerId.value = customerId;
    activeDetailTab.value = "overview";
    activeCommercialTab.value = "billing_profile";
    selectedCustomer.value = await getCustomer(tenantScopeId.value, customerId, accessToken.value);
    if (selectedCustomer.value) {
      populateCustomerDraft(selectedCustomer.value);
      resetContactDraft();
      resetAddressDraft();
      addressDirectorySearch.value = "";
      commercialProfile.value = null;
      resetBillingProfileDraft();
      resetInvoicePartyDraft();
      resetRateCardDraft();
      resetRateLineDraft();
      resetSurchargeRuleDraft();
      resetHistoryAttachmentDraft();
      resetEmployeeBlockDraft();
      portalPrivacy.value = null;
      customerPortalAccessAccounts.value = [];
      portalAccessGeneratedPassword.value = "";
      closePortalAccessCreateModal();
      closePortalAccessPasswordReset();
      resetPortalPrivacyDraft();
      resetPortalAccessDraft();
      await refreshAvailableAddresses();
      isCreatingCustomer.value = false;
      if (canReadCommercial.value) {
        await refreshCommercialProfile();
      }
      await refreshHistory();
      await refreshCustomerPortalLoginHistory();
      await refreshEmployeeBlocks();
      await refreshPortalPrivacy();
      await refreshCustomerPortalAccess();
      activeDetailTab.value = normalizeCustomerDetailTab(preferredTab || activeDetailTab.value, {
        canReadCommercial: canReadCommercial.value,
        hasSelectedCustomer: !!selectedCustomer.value,
        isCreatingCustomer: isCreatingCustomer.value,
      });
      if (selectedCustomer.value.id === pendingRouteCustomerId.value) {
        pendingRouteCustomerId.value = "";
        pendingRouteDetailTab.value = "";
      }
    }
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.detail = false;
  }
}

async function refreshCommercialProfile() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canReadCommercial.value) {
    commercialProfile.value = null;
    return;
  }

  loading.commercial = true;
  try {
    commercialProfile.value = await getCustomerCommercialProfile(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
    );
    populateBillingProfileDraft(commercialProfile.value.billing_profile);
    if (commercialProfile.value.rate_cards.length) {
      if (!commercialProfile.value.rate_cards.some((row) => row.id === selectedRateCardId.value)) {
        const firstRateCard = commercialProfile.value.rate_cards[0];
        selectedRateCardId.value = firstRateCard ? firstRateCard.id : "";
      }
    } else {
      selectedRateCardId.value = "";
    }
    resetRateLineDraft();
    resetSurchargeRuleDraft();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.commercial = false;
  }
}

async function submitCustomer() {
  if (!tenantScopeId.value || !accessToken.value) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.scope.missingBody"));
    return;
  }
  if (!customerDraft.customer_number.trim() || !customerDraft.name.trim()) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.feedback.customerRequired"));
    return;
  }

  loading.customer = true;
  try {
    const payload = normalizeCustomerDraft();
    if (isCreatingCustomer.value || !selectedCustomer.value) {
      const created = await createCustomer(tenantScopeId.value, accessToken.value, payload);
      setFeedback("success", t("customerAdmin.feedback.created"), t("customerAdmin.feedback.createdNextStep"));
      await refreshCustomers();
      await selectCustomer(created.id);
      previousSelectedCustomer.value = selectedCustomer.value;
      isCreatingCustomer.value = false;
    } else {
      const updated = await updateCustomer(tenantScopeId.value, selectedCustomer.value.id, accessToken.value, {
        ...payload,
        version_no: selectedCustomer.value.version_no,
      });
      setFeedback("success", t("customerAdmin.feedback.saved"), updated.name);
      await refreshCustomers();
      await selectCustomer(updated.id);
    }
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.customer = false;
  }
}

async function applyStatus(nextStatus: "active" | "inactive" | "archived") {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }

  const confirmationMap = {
    active: "customerAdmin.confirm.reactivate",
    inactive: "customerAdmin.confirm.deactivate",
    archived: "customerAdmin.confirm.archive",
  } as const;

  if (!window.confirm(t(confirmationMap[nextStatus]))) {
    return;
  }

  try {
    const updated = await updateCustomer(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
      buildLifecyclePayload(selectedCustomer.value, nextStatus),
    );
    const feedbackKey =
      nextStatus === "active"
        ? "customerAdmin.feedback.reactivated"
        : nextStatus === "inactive"
          ? "customerAdmin.feedback.deactivated"
          : "customerAdmin.feedback.archived";
    setFeedback("success", t(feedbackKey), updated.name);
    await refreshCustomers();
    await selectCustomer(updated.id);
  } catch (error) {
    handleApiError(error);
  }
}

async function submitContact() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  if (!contactDraft.full_name.trim()) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.feedback.contactRequired"));
    return;
  }

  loading.contact = true;
  try {
    if (editingContactId.value) {
      await updateCustomerContact(
        tenantScopeId.value,
        selectedCustomer.value.id,
        editingContactId.value,
        accessToken.value,
        {
          ...normalizeContactDraft(),
          version_no: currentContactVersion(editingContactId.value),
        },
      );
    } else {
      await createCustomerContact(
        tenantScopeId.value,
        selectedCustomer.value.id,
        accessToken.value,
        normalizeContactDraft(),
      );
    }
    setFeedback("success", t("customerAdmin.feedback.contactSaved"), contactDraft.full_name);
    resetContactDraft();
    await selectCustomer(selectedCustomer.value.id);
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.contact = false;
  }
}

async function archiveContact(contact: CustomerContactRead) {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  if (!window.confirm(t("customerAdmin.confirm.contactArchive"))) {
    return;
  }
  try {
    await updateCustomerContact(
      tenantScopeId.value,
      selectedCustomer.value.id,
      contact.id,
      accessToken.value,
      {
        status: "archived",
        archived_at: new Date().toISOString(),
        version_no: contact.version_no,
      },
    );
    setFeedback("success", t("customerAdmin.feedback.contactSaved"), contact.full_name);
    await selectCustomer(selectedCustomer.value.id);
  } catch (error) {
    handleApiError(error);
  }
}

async function submitAddress() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  if (!customerAddressLinkOptions.value.length) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.addresses.addressLinkEmpty"));
    return;
  }
  if (!addressDraft.address_id.trim()) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.feedback.addressRequired"));
    return;
  }

  loading.address = true;
  try {
    if (editingAddressId.value) {
      await updateCustomerAddress(
        tenantScopeId.value,
        selectedCustomer.value.id,
        editingAddressId.value,
        accessToken.value,
        {
          ...normalizeAddressDraft(),
          version_no: currentAddressVersion(editingAddressId.value),
        },
      );
    } else {
      await createCustomerAddress(
        tenantScopeId.value,
        selectedCustomer.value.id,
        accessToken.value,
        normalizeAddressDraft(),
      );
    }
    setFeedback("success", t("customerAdmin.feedback.addressSaved"), addressDraft.address_type);
    resetAddressDraft();
    await selectCustomer(selectedCustomer.value.id);
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.address = false;
  }
}

async function submitAddressDirectoryEntry() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  const payload = normalizeAddressDirectoryDraft();
  if (
    !payload.street_line_1
    || !payload.postal_code
    || !payload.city
    || !payload.country_code
  ) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.addresses.createValidation"));
    return;
  }

  loading.sharedAddress = true;
  try {
    const created = await createCustomerAvailableAddress(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
      payload,
    );
    stagedAddressDirectoryByCustomer[selectedCustomer.value.id] = mergeAvailableAddressDirectory(
      [],
      [...(stagedAddressDirectoryByCustomer[selectedCustomer.value.id] ?? []), created],
    );
    await refreshAvailableAddresses();
    addressDraft.address_id = created.id;
    closeAddressDirectoryCreateModal();
    setFeedback("success", t("customerAdmin.feedback.addressSaved"), t("customerAdmin.addresses.createSuccess"));
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.sharedAddress = false;
  }
}

async function submitBillingProfile() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  const validationKey = validateBillingProfileDraft({
    ...billingProfileDraft,
    payment_terms_days:
      billingProfileDraft.payment_terms_days === null ? "" : String(billingProfileDraft.payment_terms_days),
  });
  if (validationKey) {
    const resolution = resolveBillingProfileFeedbackError(validationKey);
    setBillingProfileErrors(resolution);
    setFeedback(
      "error",
      t(resolution.summaryTitleKey as never),
      resolution.primaryMessageKey
        ? `${t(resolution.summaryBodyKey as never)} ${t(resolution.primaryMessageKey as never)}`
        : t(resolution.summaryBodyKey as never),
    );
    return;
  }

  const existingProfile = commercialProfile.value?.billing_profile ?? null;
  const confirmationKey = buildCommercialConfirmationKey("billingProfile", !!existingProfile);
  if (confirmationKey && !window.confirm(t(confirmationKey as never))) {
    return;
  }

  loading.commercial = true;
  try {
    if (existingProfile) {
      await updateCustomerBillingProfile(tenantScopeId.value, selectedCustomer.value.id, accessToken.value, {
        ...normalizeBillingProfileDraft(),
        version_no: existingProfile.version_no,
      });
    } else {
      await upsertCustomerBillingProfile(
        tenantScopeId.value,
        selectedCustomer.value.id,
        accessToken.value,
        normalizeBillingProfileDraft(),
      );
    }
    clearBillingProfileErrors();
    setFeedback("success", t("customerAdmin.feedback.commercialSaved"), t("customerAdmin.commercial.billingTitle"));
    await refreshCommercialProfile();
  } catch (error) {
    if (error instanceof CustomerAdminApiError) {
      const resolution = resolveBillingProfileApiError(error.messageKey, error.details, error.code);
      setBillingProfileErrors(resolution);
      setFeedback(
        "error",
        t(resolution.summaryTitleKey as never),
        resolution.primaryMessageKey
          ? `${t(resolution.summaryBodyKey as never)} ${t(resolution.primaryMessageKey as never)}`
          : t(resolution.summaryBodyKey as never),
      );
    } else {
      clearBillingProfileErrors();
      setFeedback(
        "error",
        t("customerAdmin.feedback.billingProfileSaveFailedTitle"),
        t("customerAdmin.feedback.billingProfileUnexpected"),
      );
    }
  } finally {
    loading.commercial = false;
  }
}

async function submitInvoiceParty() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  clearInvoicePartyErrors();
  if (!invoicePartyAddressOptions.value.length) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.commercial.invoicePartyAddressMissing"));
    return;
  }
  if (!invoicePartyDraft.company_name.trim() || !invoicePartyDraft.address_id.trim()) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t("customerAdmin.feedback.invoicePartyRequired"));
    return;
  }
  const confirmationKey = buildCommercialConfirmationKey("invoiceParty", !!invoicePartyDraft.is_default);
  if (confirmationKey && !window.confirm(t(confirmationKey as never))) {
    return;
  }

  loading.commercial = true;
  try {
    if (editingInvoicePartyId.value) {
      const currentVersion =
        commercialProfile.value?.invoice_parties.find((row) => row.id === editingInvoicePartyId.value)?.version_no ?? 1;
      await updateCustomerInvoiceParty(
        tenantScopeId.value,
        selectedCustomer.value.id,
        editingInvoicePartyId.value,
        accessToken.value,
        {
          ...normalizeInvoicePartyDraft(),
          version_no: currentVersion,
        },
      );
    } else {
      await createCustomerInvoiceParty(
        tenantScopeId.value,
        selectedCustomer.value.id,
        accessToken.value,
        normalizeInvoicePartyDraft(),
      );
    }
    setFeedback("success", t("customerAdmin.feedback.commercialSaved"), invoicePartyDraft.company_name);
    resetInvoicePartyDraft();
    await refreshCommercialProfile();
  } catch (error) {
    if (error instanceof CustomerAdminApiError) {
      const resolution = resolveInvoicePartyApiError(error.messageKey, error.details, error.code);
      if (resolution.fields.length && resolution.primaryMessageKey) {
        setInvoicePartyErrors(resolution.fields, resolution.primaryMessageKey);
        setFeedback(
          "error",
          t(resolution.summaryTitleKey as never),
          `${t(resolution.summaryBodyKey as never)} ${t(resolution.primaryMessageKey as never)}`,
        );
        return;
      }
    }
    handleApiError(error);
  } finally {
    loading.commercial = false;
  }
}

async function submitRateCard() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  const validationKey = validateRateCardDraft(rateCardDraft);
  if (validationKey) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t(validationKey as never));
    return;
  }
  const confirmationKey = buildCommercialConfirmationKey("rateCard", !!editingRateCardId.value);
  if (confirmationKey && !window.confirm(t(confirmationKey as never))) {
    return;
  }

  loading.commercial = true;
  try {
    if (editingRateCardId.value) {
      const currentVersion =
        commercialProfile.value?.rate_cards.find((row) => row.id === editingRateCardId.value)?.version_no ?? 1;
      const updated = await updateCustomerRateCard(
        tenantScopeId.value,
        selectedCustomer.value.id,
        editingRateCardId.value,
        accessToken.value,
        {
          ...normalizeRateCardDraft(),
          version_no: currentVersion,
        },
      );
      selectedRateCardId.value = updated.id;
    } else {
      const created = await createCustomerRateCard(
        tenantScopeId.value,
        selectedCustomer.value.id,
        accessToken.value,
        normalizeRateCardDraft(),
      );
      selectedRateCardId.value = created.id;
    }
    setFeedback("success", t("customerAdmin.feedback.commercialSaved"), t("customerAdmin.commercial.rateCardsTitle"));
    resetRateCardDraft();
    await refreshCommercialProfile();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.commercial = false;
  }
}

async function submitRateLine() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !selectedRateCard.value) {
    return;
  }
  const validationKey = validateRateLineDraft(rateLineDraft);
  if (validationKey) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t(validationKey as never));
    return;
  }
  const confirmationKey = buildCommercialConfirmationKey("rateLine", !!editingRateLineId.value);
  if (confirmationKey && !window.confirm(t(confirmationKey as never))) {
    return;
  }

  loading.rateLine = true;
  try {
    if (editingRateLineId.value) {
      const currentVersion = selectedRateCard.value.rate_lines.find((row) => row.id === editingRateLineId.value)?.version_no ?? 1;
      await updateCustomerRateLine(
        tenantScopeId.value,
        selectedCustomer.value.id,
        selectedRateCard.value.id,
        editingRateLineId.value,
        accessToken.value,
        {
          ...normalizeRateLineDraft(),
          version_no: currentVersion,
        },
      );
    } else {
      await createCustomerRateLine(
        tenantScopeId.value,
        selectedCustomer.value.id,
        selectedRateCard.value.id,
        accessToken.value,
        normalizeRateLineDraft(),
      );
    }
    setFeedback("success", t("customerAdmin.feedback.commercialSaved"), t("customerAdmin.commercial.rateLinesTitle"));
    resetRateLineDraft();
    await refreshCommercialProfile();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.rateLine = false;
  }
}

async function submitSurchargeRule() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !selectedRateCard.value) {
    return;
  }
  const validationKey = validateSurchargeRuleDraft(surchargeRuleDraft);
  if (validationKey) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t(validationKey as never));
    return;
  }
  const rateCardWindowValidationKey = validateSurchargeRuleAgainstRateCardWindow(
    selectedRateCard.value,
    surchargeRuleDraft,
  );
  if (rateCardWindowValidationKey) {
    setFeedback("error", t("customerAdmin.feedback.validation"), t(rateCardWindowValidationKey as never));
    return;
  }
  const confirmationKey = buildCommercialConfirmationKey("surchargeRule", !!editingSurchargeRuleId.value);
  if (confirmationKey && !window.confirm(t(confirmationKey as never))) {
    return;
  }

  loading.surchargeRule = true;
  try {
    if (editingSurchargeRuleId.value) {
      const currentVersion =
        selectedRateCard.value.surcharge_rules.find((row) => row.id === editingSurchargeRuleId.value)?.version_no ?? 1;
      await updateCustomerSurchargeRule(
        tenantScopeId.value,
        selectedCustomer.value.id,
        selectedRateCard.value.id,
        editingSurchargeRuleId.value,
        accessToken.value,
        {
          ...normalizeSurchargeRuleDraft(),
          version_no: currentVersion,
        },
      );
    } else {
      await createCustomerSurchargeRule(
        tenantScopeId.value,
        selectedCustomer.value.id,
        selectedRateCard.value.id,
        accessToken.value,
        normalizeSurchargeRuleDraft(),
      );
    }
    setFeedback("success", t("customerAdmin.feedback.commercialSaved"), t("customerAdmin.commercial.surchargesTitle"));
    resetSurchargeRuleDraft();
    await refreshCommercialProfile();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.surchargeRule = false;
  }
}

async function archiveAddress(address: CustomerAddressRead) {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }
  if (!window.confirm(t("customerAdmin.confirm.addressArchive"))) {
    return;
  }
  try {
    await updateCustomerAddress(
      tenantScopeId.value,
      selectedCustomer.value.id,
      address.id,
      accessToken.value,
      {
        status: "archived",
        archived_at: new Date().toISOString(),
        version_no: address.version_no,
      },
    );
    setFeedback("success", t("customerAdmin.feedback.addressSaved"), address.address_type);
    await selectCustomer(selectedCustomer.value.id);
  } catch (error) {
    handleApiError(error);
  }
}

async function refreshAvailableAddresses() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    availableAddressDirectory.value = [];
    return;
  }
  const remote = await listCustomerAvailableAddresses(
    tenantScopeId.value,
    selectedCustomer.value.id,
    accessToken.value,
    {
      search: addressDirectorySearch.value,
      limit: 25,
    },
  );
  const staged = stagedAddressDirectoryByCustomer[selectedCustomer.value.id] ?? [];
  availableAddressDirectory.value = mergeAvailableAddressDirectory(remote, staged);
}

function mergeAvailableAddressDirectory(
  remote: CustomerAvailableAddressRead[],
  staged: CustomerAvailableAddressRead[],
) {
  const merged = new Map<string, CustomerAvailableAddressRead>();
  for (const row of [...remote, ...staged]) {
    merged.set(row.id, row);
  }
  return [...merged.values()];
}

function currentContactVersion(contactId: string) {
  return selectedCustomer.value?.contacts.find((row) => row.id === contactId)?.version_no ?? 1;
}

function currentAddressVersion(addressId: string) {
  return selectedCustomer.value?.addresses.find((row) => row.id === addressId)?.version_no ?? 1;
}

function normalizeCustomerDraft(): CustomerCreatePayload {
  return buildCustomerDraftPayload(customerDraft, {
    allowedBranchIds: branchOptions.value.map((branch) => branch.id),
    allowedMandateIds: filteredCustomerMandates.value.map((mandate) => mandate.id),
  } as any);
}

function normalizeContactDraft(): CustomerContactPayload {
  return {
    tenant_id: tenantScopeId.value,
    customer_id: selectedCustomerId.value,
    full_name: contactDraft.full_name.trim(),
    title: emptyToNull(contactDraft.title),
    function_label: emptyToNull(contactDraft.function_label),
    email: emptyToNull(contactDraft.email),
    phone: emptyToNull(contactDraft.phone),
    mobile: emptyToNull(contactDraft.mobile),
    is_primary_contact: !!contactDraft.is_primary_contact,
    is_billing_contact: !!contactDraft.is_billing_contact,
    notes: emptyToNull(contactDraft.notes),
  };
}

function normalizeAddressDraft(): CustomerAddressPayload {
  return {
    tenant_id: tenantScopeId.value,
    customer_id: selectedCustomerId.value,
    address_id: addressDraft.address_id.trim(),
    address_type: addressDraft.address_type,
    label: emptyToNull(addressDraft.label),
    is_default: !!addressDraft.is_default,
  };
}

function normalizeAddressDirectoryDraft(): CustomerAvailableAddressCreatePayload {
  return {
    street_line_1: addressDirectoryDraft.street_line_1.trim(),
    street_line_2: emptyToNull(addressDirectoryDraft.street_line_2),
    postal_code: addressDirectoryDraft.postal_code.trim(),
    city: addressDirectoryDraft.city.trim(),
    state: emptyToNull(addressDirectoryDraft.state),
    country_code: addressDirectoryDraft.country_code.trim().toUpperCase(),
  };
}

function normalizeBillingProfileDraft(): CustomerBillingProfilePayload {
  return {
    tenant_id: tenantScopeId.value,
    customer_id: selectedCustomerId.value,
    invoice_email: emptyToNull(billingProfileDraft.invoice_email),
    payment_terms_days:
      billingProfileDraft.payment_terms_days === null || billingProfileDraft.payment_terms_days === undefined
        ? null
        : Number(billingProfileDraft.payment_terms_days),
    payment_terms_note: emptyToNull(billingProfileDraft.payment_terms_note),
    tax_number: emptyToNull(billingProfileDraft.tax_number),
    vat_id: emptyToNull(billingProfileDraft.vat_id),
    tax_exempt: !!billingProfileDraft.tax_exempt,
    tax_exemption_reason: emptyToNull(billingProfileDraft.tax_exemption_reason),
    bank_account_holder: emptyToNull(billingProfileDraft.bank_account_holder),
    bank_iban: emptyToNull(billingProfileDraft.bank_iban),
    bank_bic: emptyToNull(billingProfileDraft.bank_bic),
    bank_name: emptyToNull(billingProfileDraft.bank_name),
    contract_reference: emptyToNull(billingProfileDraft.contract_reference),
    debtor_number: emptyToNull(billingProfileDraft.debtor_number),
    e_invoice_enabled: !!billingProfileDraft.e_invoice_enabled,
    leitweg_id: emptyToNull(billingProfileDraft.leitweg_id),
    invoice_layout_code: emptyToNull(billingProfileDraft.invoice_layout_code),
    shipping_method_code: emptyToNull(billingProfileDraft.shipping_method_code),
    dunning_policy_code: emptyToNull(billingProfileDraft.dunning_policy_code),
    billing_note: emptyToNull(billingProfileDraft.billing_note),
  };
}

function normalizeInvoicePartyDraft(): CustomerInvoicePartyPayload {
  return {
    tenant_id: tenantScopeId.value,
    customer_id: selectedCustomerId.value,
    company_name: invoicePartyDraft.company_name.trim(),
    contact_name: emptyToNull(invoicePartyDraft.contact_name),
    address_id: invoicePartyDraft.address_id.trim(),
    invoice_email: emptyToNull(invoicePartyDraft.invoice_email),
    invoice_layout_lookup_id: emptyToNull(invoicePartyDraft.invoice_layout_lookup_id),
    external_ref: emptyToNull(invoicePartyDraft.external_ref),
    is_default: !!invoicePartyDraft.is_default,
    note: emptyToNull(invoicePartyDraft.note),
  };
}

function formatInvoicePartyAddressOption(address: CustomerAddressRead) {
  const typeLabel = t(`customerAdmin.addressType.${address.address_type}` as never);
  if (!address.address) {
    return address.label ? `${typeLabel} · ${address.label}` : `${typeLabel} · ${address.address_id}`;
  }
  const location = [address.address.street_line_1, `${address.address.postal_code} ${address.address.city}`]
    .filter(Boolean)
    .join(", ");
  return address.label ? `${typeLabel} · ${address.label} · ${location}` : `${typeLabel} · ${location}`;
}

function formatAddressDirectoryOption(address: CustomerAvailableAddressRead) {
  const location = [address.street_line_1, `${address.postal_code} ${address.city}`].filter(Boolean).join(", ");
  return address.street_line_2 ? `${location} · ${address.street_line_2}` : location;
}

function formatCatalogOptionLabel(option: { code: string; id: string; label: string }) {
  return option.code ? `${option.code} · ${option.label}` : option.label || option.id;
}

function resolveRateLineCatalogLabel(
  optionId: null | string | undefined,
  nestedOption: null | { code: string; id: string; label: string } | undefined,
  options: Array<{ code: string; id: string; label: string }>,
) {
  if (!optionId) {
    return "";
  }
  const matched = options.find((option) => option.id === optionId);
  if (matched) {
    return formatCatalogOptionLabel(matched);
  }
  if (nestedOption) {
    return formatCatalogOptionLabel(nestedOption);
  }
  return optionId;
}

function normalizeRateCardDraft(): CustomerRateCardPayload {
  return {
    tenant_id: tenantScopeId.value,
    customer_id: selectedCustomerId.value,
    rate_kind: rateCardDraft.rate_kind.trim(),
    currency_code: rateCardDraft.currency_code.trim().toUpperCase(),
    effective_from: rateCardDraft.effective_from,
    effective_to: emptyToNull(rateCardDraft.effective_to),
    notes: emptyToNull(rateCardDraft.notes),
  };
}

function normalizeRateLineDraft(): CustomerRateLinePayload {
  return normalizeRateLinePayloadDraft(rateLineDraft, {
    tenantId: tenantScopeId.value,
    rateCardId: selectedRateCardId.value,
  });
}

function normalizeSurchargeRuleDraft(): CustomerSurchargeRulePayload {
  const normalizedAmount = applySurchargeAmountMode(
    surchargeAmountMode.value,
    surchargeRuleDraft,
    selectedRateCardCurrencyFallback(),
  );
  return {
    tenant_id: tenantScopeId.value,
    rate_card_id: selectedRateCardId.value,
    surcharge_type: surchargeRuleDraft.surcharge_type.trim(),
    effective_from: surchargeRuleDraft.effective_from,
    effective_to: emptyToNull(surchargeRuleDraft.effective_to),
    weekday_mask: emptyToNull(buildWeekdayMask(surchargeSelectedWeekdays.value)),
    time_from_minute: timeInputToMinutes(surchargeTimeFromInput.value),
    time_to_minute: timeInputToMinutes(surchargeTimeToInput.value),
    region_code: emptyToNull(`${surchargeRuleDraft.region_code ?? ""}`.trim().toUpperCase()),
    percent_value: emptyToNull(normalizedAmount.percent_value),
    fixed_amount: emptyToNull(normalizedAmount.fixed_amount),
    currency_code: emptyToNull(normalizedAmount.currency_code)?.toUpperCase() ?? null,
    sort_order: Number(surchargeRuleDraft.sort_order ?? 100),
    notes: emptyToNull(surchargeRuleDraft.notes),
  };
}

async function refreshHistory() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canRead.value) {
    customerHistory.value = [];
    return;
  }

  try {
    customerHistory.value = await listCustomerHistory(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
    );
    resetHistoryAttachmentDraft();
  } catch (error) {
    handleApiError(error);
  }
}

async function refreshCustomerPortalLoginHistory() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canRead.value) {
    customerPortalLoginHistory.value = [];
    return;
  }

  loading.loginHistory = true;
  try {
    customerPortalLoginHistory.value = await listCustomerPortalLoginHistory(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
    );
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.loginHistory = false;
  }
}

async function refreshEmployeeBlocks() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canRead.value) {
    customerEmployeeBlocks.value = [];
    employeeBlockCapability.value = null;
    return;
  }

  loading.employeeBlock = true;
  try {
    const response = await listCustomerEmployeeBlocks(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
    );
    customerEmployeeBlocks.value = response.items;
    employeeBlockCapability.value = response.capability;
    resetEmployeeBlockDraft();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.employeeBlock = false;
  }
}

async function refreshPortalPrivacy() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canRead.value) {
    portalPrivacy.value = null;
    resetPortalPrivacyDraft();
    return;
  }

  loading.portalPrivacy = true;
  try {
    portalPrivacy.value = await getCustomerPortalPrivacy(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
    );
    resetPortalPrivacyDraft();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.portalPrivacy = false;
  }
}

async function refreshCustomerPortalAccess() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canManagePortalAccess.value) {
    customerPortalAccessAccounts.value = [];
    return;
  }

  loading.portalAccess = true;
  try {
    customerPortalAccessAccounts.value = await listCustomerPortalAccess(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
    );
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.portalAccess = false;
  }
}

async function submitPortalPrivacy() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }

  loading.portalPrivacy = true;
  try {
    portalPrivacy.value = await updateCustomerPortalPrivacy(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
      {
        person_names_released: !!portalPrivacyDraft.person_names_released,
      },
    );
    if (selectedCustomer.value) {
      selectedCustomer.value = {
        ...selectedCustomer.value,
        portal_person_names_released: portalPrivacy.value.person_names_released,
        portal_person_names_released_at: portalPrivacy.value.person_names_released_at,
        portal_person_names_released_by_user_id: portalPrivacy.value.person_names_released_by_user_id,
      };
    }
    resetPortalPrivacyDraft();
    setFeedback("success", t("customerAdmin.feedback.portalPrivacySaved"), t("customerAdmin.privacy.title"));
    await refreshHistory();
    await refreshCustomerPortalLoginHistory();
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.portalPrivacy = false;
  }
}

async function submitCustomerPortalAccess() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canManagePortalAccess.value) {
    return;
  }

  loading.portalAccess = true;
  try {
    const response = await createCustomerPortalAccess(
      tenantScopeId.value,
      selectedCustomer.value.id,
      accessToken.value,
      {
        ...portalAccessDraft,
        temporary_password: emptyToNull(portalAccessDraft.temporary_password),
      },
    );
    portalAccessGeneratedPassword.value = response.temporary_password;
    closePortalAccessCreateModal();
    resetPortalAccessDraft();
    await refreshCustomerPortalAccess();
    await selectCustomer(selectedCustomer.value.id);
    setFeedback(
      "success",
      t("customerAdmin.feedback.portalAccessCreated"),
      t("customerAdmin.feedback.portalAccessCreatedBody"),
    );
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.portalAccess = false;
  }
}

async function submitCustomerPortalAccessPasswordReset() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !portalAccessPasswordTarget.value) {
    return;
  }

  loading.portalAccess = true;
  try {
    const response = await resetCustomerPortalAccessPassword(
      tenantScopeId.value,
      selectedCustomer.value.id,
      portalAccessPasswordTarget.value.user_id,
      accessToken.value,
      { temporary_password: emptyToNull(portalAccessPasswordDraft.temporary_password) },
    );
    portalAccessGeneratedPassword.value = response.temporary_password;
    closePortalAccessPasswordReset();
    await refreshCustomerPortalAccess();
    setFeedback(
      "success",
      t("customerAdmin.feedback.portalAccessPasswordReset"),
      t("customerAdmin.feedback.portalAccessPasswordResetBody"),
    );
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.portalAccess = false;
  }
}

async function setCustomerPortalAccessStatus(account: CustomerPortalAccessListItem, status: "active" | "inactive") {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canManagePortalAccess.value) {
    return;
  }

  loading.portalAccess = true;
  try {
    await updateCustomerPortalAccessStatus(
      tenantScopeId.value,
      selectedCustomer.value.id,
      account.user_id,
      accessToken.value,
      { status },
    );
    await refreshCustomerPortalAccess();
    setFeedback(
      "success",
      t("customerAdmin.feedback.portalAccessStatusSaved"),
      t("customerAdmin.feedback.portalAccessStatusSavedBody"),
    );
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.portalAccess = false;
  }
}

async function unlinkCustomerPortalAccount(account: CustomerPortalAccessListItem) {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !canManagePortalAccess.value) {
    return;
  }

  loading.portalAccess = true;
  try {
    await unlinkCustomerPortalAccess(
      tenantScopeId.value,
      selectedCustomer.value.id,
      account.user_id,
      accessToken.value,
    );
    portalAccessGeneratedPassword.value = "";
    closePortalAccessPasswordReset();
    await refreshCustomerPortalAccess();
    await selectCustomer(selectedCustomer.value.id);
    setFeedback(
      "success",
      t("customerAdmin.feedback.portalAccessUnlinked"),
      t("customerAdmin.feedback.portalAccessUnlinkedBody"),
    );
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.portalAccess = false;
  }
}

async function submitHistoryAttachmentLink() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value || !historyAttachmentDraft.history_entry_id) {
    return;
  }

  loading.historyAttachment = true;
  try {
    const attachments = await linkCustomerHistoryAttachment(
      tenantScopeId.value,
      selectedCustomer.value.id,
      historyAttachmentDraft.history_entry_id,
      accessToken.value,
      {
        document_id: historyAttachmentDraft.document_id.trim(),
        label: emptyToNull(historyAttachmentDraft.label),
      },
    );
    customerHistory.value = customerHistory.value.map((entry) =>
      entry.id === historyAttachmentDraft.history_entry_id ? { ...entry, attachments } : entry,
    );
    resetHistoryAttachmentDraft();
    setFeedback("success", t("customerAdmin.feedback.historyAttachmentLinked"), t("customerAdmin.feedback.documentLinked"));
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.historyAttachment = false;
  }
}

async function submitEmployeeBlock() {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }

  loading.employeeBlock = true;
  try {
    if (editingEmployeeBlockId.value) {
      await updateCustomerEmployeeBlock(
        tenantScopeId.value,
        selectedCustomer.value.id,
        editingEmployeeBlockId.value,
        accessToken.value,
        {
          tenant_id: tenantScopeId.value,
          customer_id: selectedCustomer.value.id,
          employee_id: employeeBlockDraft.employee_id.trim(),
          reason: employeeBlockDraft.reason.trim(),
          effective_from: employeeBlockDraft.effective_from,
          effective_to: emptyToNull(employeeBlockDraft.effective_to),
          version_no: customerEmployeeBlocks.value.find((row) => row.id === editingEmployeeBlockId.value)?.version_no ?? 1,
        },
      );
    } else {
      await createCustomerEmployeeBlock(
        tenantScopeId.value,
        selectedCustomer.value.id,
        accessToken.value,
        {
          tenant_id: tenantScopeId.value,
          customer_id: selectedCustomer.value.id,
          employee_id: employeeBlockDraft.employee_id.trim(),
          reason: employeeBlockDraft.reason.trim(),
          effective_from: employeeBlockDraft.effective_from,
          effective_to: emptyToNull(employeeBlockDraft.effective_to),
        },
      );
    }
    await refreshEmployeeBlocks();
    setFeedback("success", t("customerAdmin.feedback.employeeBlockSaved"), t("customerAdmin.feedback.employeeBlockSavedBody"));
  } catch (error) {
    handleApiError(error);
  } finally {
    loading.employeeBlock = false;
  }
}

async function runCustomerExport() {
  if (!tenantScopeId.value || !accessToken.value) {
    return;
  }

  try {
    const result = await exportCustomers(tenantScopeId.value, accessToken.value, {
      tenant_id: tenantScopeId.value,
      include_archived: !!filters.include_archived,
      search: emptyToNull(filters.search),
    });
    setFeedback(
      "success",
      t("customerAdmin.feedback.exportReady"),
      `${result.file_name} · ${t("customerAdmin.feedback.documentId")}: ${result.document_id}`,
    );
  } catch (error) {
    handleApiError(error);
  }
}

async function downloadContactVCard(contact: CustomerContactRead) {
  if (!selectedCustomer.value || !tenantScopeId.value || !accessToken.value) {
    return;
  }

  try {
    const result = await exportCustomerVCard(
      tenantScopeId.value,
      selectedCustomer.value.id,
      contact.id,
      accessToken.value,
    );
    downloadBase64File(result.file_name, result.content_type, result.content_base64);
    setFeedback("success", t("customerAdmin.feedback.vcardReady"), contact.full_name);
  } catch (error) {
    handleApiError(error);
  }
}

function downloadBase64File(fileName: string, contentType: string, contentBase64: string) {
  if (typeof window === "undefined") {
    return;
  }

  const binary = window.atob(contentBase64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  const blob = new Blob([bytes], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  window.URL.revokeObjectURL(url);
}

function formatHistoryMeta(entry: CustomerHistoryEntryRead) {
  return `${new Date(entry.created_at).toLocaleString()} · ${entry.entry_type}`;
}

function formatLoginHistoryMeta(entry: CustomerLoginHistoryEntryRead) {
  const contactLabel = entry.contact_name ? ` · ${entry.contact_name}` : "";
  const failure = entry.failure_reason ? ` · ${entry.failure_reason}` : "";
  return `${new Date(entry.created_at).toLocaleString()} · ${entry.outcome}${contactLabel}${failure}`;
}

function formatOptionalDateTime(value: null | string | undefined) {
  if (!value) {
    return t("customerAdmin.summary.none");
  }
  return new Date(value).toLocaleString();
}

function handleApiError(error: unknown) {
  if (error instanceof CustomerAdminApiError) {
    const feedbackKey =
      mapCustomerCommercialApiMessage(error.messageKey) !== "customerAdmin.feedback.error"
        ? mapCustomerCommercialApiMessage(error.messageKey)
        : mapCustomerApiMessage(error.messageKey);
    setFeedback("error", t("customerAdmin.feedback.error"), t(feedbackKey as never));
    return;
  }

  setFeedback("error", t("customerAdmin.feedback.error"), t("customerAdmin.feedback.error"));
}

function emptyToNull(value: string | null | undefined) {
  const normalized = value?.trim() ?? "";
  return normalized ? normalized : null;
}

watch(
  () => [route.query.customer_id, route.query.tab, tenantScopeId.value, accessToken.value, canRead.value] as const,
  async () => {
    const nextContext = resolveCustomerAdminRouteContext(route.query);
    pendingRouteCustomerId.value = nextContext.customerId;
    pendingRouteDetailTab.value = nextContext.detailTab;
    if (!nextContext.customerId || !tenantScopeId.value || !accessToken.value || !canRead.value) {
      return;
    }
    if (selectedCustomer.value?.id === nextContext.customerId) {
      activeDetailTab.value = normalizeCustomerDetailTab(nextContext.detailTab || activeDetailTab.value, {
        canReadCommercial: canReadCommercial.value,
        hasSelectedCustomer: !!selectedCustomer.value,
        isCreatingCustomer: isCreatingCustomer.value,
      });
      return;
    }
    if (customers.value.some((row) => row.id === nextContext.customerId)) {
      await selectCustomer(nextContext.customerId, nextContext.detailTab);
    }
  },
  { immediate: true },
);

watch(
  () => [selectedCustomer.value?.id ?? "", isCreatingCustomer.value, canReadCommercial.value],
  () => {
    activeDetailTab.value = normalizeCustomerDetailTab(activeDetailTab.value, {
      canReadCommercial: canReadCommercial.value,
      hasSelectedCustomer: !!selectedCustomer.value,
      isCreatingCustomer: isCreatingCustomer.value,
    });
  },
  { immediate: true },
);

watch(
  () => activeDetailTab.value,
  (tabId) => {
    if (tabId === "commercial") {
      activeCommercialTab.value = normalizeCustomerCommercialTab(activeCommercialTab.value);
    }
  },
  { immediate: true },
);

watch(
  () => [activeCommercialTab.value, commercialProfile.value?.rate_cards.length ?? 0] as const,
  () => {
    if (activeCommercialTab.value !== "pricing_rules") {
      return;
    }
    const allowedTabs = pricingRulesTabs.value.map((tab) => tab.id);
    if (!allowedTabs.includes(activePricingRulesTab.value)) {
      activePricingRulesTab.value = "rate_cards";
    }
    if ((activePricingRulesTab.value === "rate_lines" || activePricingRulesTab.value === "surcharges") && !selectedRateCard.value) {
      const firstRateCard = commercialProfile.value?.rate_cards[0];
      selectedRateCardId.value = firstRateCard ? firstRateCard.id : "";
    }
  },
  { immediate: true },
);

watch(
  () => surchargeTimeFromInput.value,
  () => {
    syncSurchargeTimeDraft();
  },
);

watch(
  () => surchargeTimeToInput.value,
  () => {
    syncSurchargeTimeDraft();
  },
);

watch(
  () => selectedRateCard.value?.currency_code ?? "",
  (currencyCode) => {
    if (
      surchargeAmountMode.value === "fixed"
      && !`${surchargeRuleDraft.currency_code ?? ""}`.trim()
      && `${currencyCode}`.trim()
    ) {
      surchargeRuleDraft.currency_code = `${currencyCode}`.trim().toUpperCase();
    }
  },
);

watch(
  () => customerDraft.default_branch_id,
  (branchId) => {
    if (!customerDraft.default_mandate_id) {
      return;
    }
    const mandateStillValid = filterMandateOptions(branchId).some((mandate) => mandate.id === customerDraft.default_mandate_id);
    if (!mandateStillValid) {
      customerDraft.default_mandate_id = "";
    }
  },
);

watch(
  () => filters.default_branch_id,
  (branchId) => {
    if (!filters.default_mandate_id) {
      return;
    }
    const mandateStillValid = filterMandateOptions(branchId).some((mandate) => mandate.id === filters.default_mandate_id);
    if (!mandateStillValid) {
      filters.default_mandate_id = "";
    }
  },
);

watch(
  () => portalAccessDraft.contact_id,
  (contactId) => {
    if (!contactId) {
      return;
    }
    applyPortalAccessContactDefaults(contactId);
  },
);

watch(
  () => [authStore.effectiveRole, authStore.effectiveTenantScopeId, authStore.effectiveAccessToken],
  () => {
    if (authStore.effectiveRole === "tenant_admin") {
      syncTenantAdminSessionState();
    }
  },
);

onMounted(() => {
  authStore.syncFromPrimarySession();
  resetCustomerDraft();
  resetContactDraft();
  resetAddressDraft();
  resetBillingProfileDraft();
  resetInvoicePartyDraft();
  resetRateCardDraft();
  resetRateLineDraft();
  resetSurchargeRuleDraft();
  resetPortalPrivacyDraft();
  void (async () => {
    if (
      authStore.effectiveRole === "tenant_admin" &&
      authStore.effectiveAccessToken &&
      !authStore.sessionUser
    ) {
      try {
        await authStore.loadCurrentSession();
      } catch {
        // Keep the page usable with whatever session state is already available.
      }
    }
    syncTenantAdminSessionState();

    await refreshCustomers();
  })();
});
</script>

<style scoped>
.customer-admin-page {
  display: grid;
  gap: var(--sp-page-gap, 1.25rem);
}

.customer-admin-form,
.customer-admin-form-grid,
.customer-admin-list,
.customer-admin-record-list {
  display: grid;
  gap: 1rem;
}

.customer-admin-grid {
  display: grid;
  gap: var(--sp-page-gap, 1.25rem);
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  align-items: start;
}

.customer-admin-list-panel {
  position: sticky;
  top: 0;
}

.customer-admin-subgrid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.customer-admin-hero {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
}

.customer-admin-scope {
  min-width: min(100%, 360px);
  display: grid;
  gap: 1rem;
}

.customer-admin-lead {
  margin: 0.35rem 0 0;
  color: var(--sp-color-text-secondary);
}

.customer-admin-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1rem;
}

.customer-admin-meta__pill {
  padding: 0.4rem 0.8rem;
  border-radius: 999px;
  background: var(--sp-color-surface-page);
  border: 1px solid var(--sp-color-border-soft);
  color: var(--sp-color-text-secondary);
}

.customer-admin-feedback {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  background: var(--sp-color-primary-muted);
  color: var(--sp-color-primary-strong);
}

.customer-admin-feedback[data-tone="error"] {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 45%, #ffb4a6);
  color: color-mix(in srgb, var(--sp-color-primary-strong) 60%, #6a1d00);
}

.customer-admin-feedback[data-tone="success"] {
  background: color-mix(in srgb, var(--sp-color-primary-muted) 32%, #dcfce7);
  color: color-mix(in srgb, var(--sp-color-primary-strong) 65%, #14532d);
}

.customer-admin-feedback--inline {
  margin: 0;
}

.customer-admin-empty {
  display: grid;
  gap: 0.5rem;
}

.customer-admin-panel,
.customer-admin-section,
.customer-admin-tab-panel,
.customer-admin-form,
.customer-admin-form--structured,
.customer-admin-form-section,
.customer-admin-editor-intro {
  display: grid;
  gap: 1rem;
}

.customer-admin-form--structured {
  gap: 1.1rem;
}

.customer-admin-editor-intro,
.customer-admin-form-section {
  padding: 1rem 1.1rem;
  border: 1px solid var(--sp-color-border-soft);
  border-radius: 18px;
  background: color-mix(in srgb, var(--sp-color-surface-page) 76%, white 24%);
  min-width: 0;
}

.customer-admin-editor-intro h4,
.customer-admin-form-section__header h4 {
  margin: 0;
  color: var(--sp-color-text-primary);
}

.customer-admin-form-section__header {
  display: grid;
  gap: 0.25rem;
}

.customer-admin-form-section__header--split {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  column-gap: 1rem;
}

.customer-admin-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.customer-admin-tab {
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

.customer-admin-tab.active {
  border-color: var(--sp-color-primary);
  color: var(--sp-color-primary-strong);
  background: color-mix(in srgb, var(--sp-color-primary-muted) 70%, white);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 28%, transparent);
}

.customer-admin-tab:focus-visible {
  outline: none;
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 3px rgb(40 170 170 / 14%);
}

.customer-admin-tabs--sub {
  margin-top: 0.25rem;
}

.customer-admin-tab--sub {
  padding: 0.52rem 0.9rem;
}

.customer-admin-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.customer-admin-row,
.customer-admin-record {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  border-radius: 18px;
  border: 1px solid var(--sp-color-border-soft);
  background: var(--sp-color-surface-page);
}

.customer-admin-row {
  cursor: pointer;
  text-align: left;
}

.customer-admin-row.selected {
  border-color: var(--sp-color-primary);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--sp-color-primary) 40%, transparent);
}

.customer-admin-row span,
.customer-admin-record p,
.customer-admin-list-empty,
.customer-admin-record__meta {
  color: var(--sp-color-text-secondary);
  margin: 0.35rem 0 0;
}

.customer-admin-record__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: end;
}

.customer-admin-record__body {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
  flex: 1 1 auto;
}

.customer-admin-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem 1rem;
}

.customer-admin-inline-list {
  margin: 0.5rem 0 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.35rem;
}

.customer-admin-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
}

.customer-admin-summary__card {
  padding: 0.9rem 1rem;
  border-radius: 16px;
  background: var(--sp-color-surface-page);
  border: 1px solid var(--sp-color-border-soft);
  display: grid;
  gap: 0.35rem;
}

.customer-admin-summary__card span {
  color: var(--sp-color-text-secondary);
  font-size: 0.85rem;
}

.customer-admin-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 30;
  background: rgb(15 23 42 / 38%);
  display: grid;
  place-items: center;
  padding: 1rem;
}

.customer-admin-modal {
  width: min(100%, 720px);
  display: grid;
  gap: 1rem;
}

.customer-admin-lifecycle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--sp-color-surface-page), transparent);
  border: 1px solid var(--sp-color-border-soft);
}

.customer-admin-checkbox {
  display: flex;
  gap: 0.7rem;
  align-items: center;
  min-width: 0;
  color: var(--sp-color-text-secondary);
}

.customer-admin-checkbox--error {
  color: color-mix(in srgb, var(--sp-color-primary-strong) 58%, #6a1d00);
}

.customer-admin-checkbox input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  margin: 0;
  accent-color: var(--sp-color-primary);
}

.customer-admin-field-stack--error input,
.customer-admin-field-stack--error select,
.customer-admin-field-stack--error textarea {
  border-color: rgb(176 48 48 / 55%);
  box-shadow: 0 0 0 3px rgb(176 48 48 / 10%);
}

.customer-admin-field-help--error {
  color: color-mix(in srgb, var(--sp-color-primary-strong) 58%, #6a1d00);
  margin-top: 0.1rem;
}

.customer-admin-field-help {
  color: var(--sp-color-text-secondary);
  margin-top: 0.1rem;
}

.customer-admin-catalog-empty-state {
  align-self: start;
  border: 1px dashed color-mix(in srgb, var(--sp-color-border) 72%, var(--sp-color-primary));
  border-radius: 16px;
  padding: 0.9rem 1rem;
  background: color-mix(in srgb, var(--sp-color-surface-weak) 88%, white);
}

.customer-admin-catalog-empty-state p {
  margin: 0;
  color: var(--sp-color-text-secondary);
}

.customer-admin-metadata-warning {
  align-self: start;
  border: 1px solid color-mix(in srgb, var(--sp-color-border) 70%, #d58d00);
  border-radius: 16px;
  padding: 0.85rem 1rem;
  background: color-mix(in srgb, #fff4cf 58%, white);
}

.customer-admin-metadata-warning p {
  margin: 0;
  color: var(--sp-color-text-secondary);
}

.field-stack {
  display: grid;
  gap: 0.42rem;
  font-size: 0.9rem;
  min-width: 0;
}

.customer-admin-form-grid--detail {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.customer-admin-form-grid--detail > .field-stack {
  grid-column: span 3;
}

.customer-admin-form-grid--detail > .field-stack--half {
  grid-column: span 3;
}

.customer-admin-form-grid--detail > .field-stack--third {
  grid-column: span 2;
}

.customer-admin-form-grid--detail > .customer-admin-surcharge-date-block {
  grid-column: span 4;
}

.customer-admin-billing-row-field {
  align-self: start;
}

.customer-admin-billing-paired-field {
  align-self: start;
}

.customer-admin-billing-paired-field--compact {
  min-height: 8.85rem;
}

.customer-admin-billing-paired-field--compact input {
  min-height: 3.1rem;
}

.customer-admin-billing-paired-field--notes textarea {
  min-height: 8.85rem;
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

.field-stack--wide {
  grid-column: 1 / -1;
}

.customer-admin-surcharge-date-block {
  display: grid;
  gap: 0.42rem;
  align-self: start;
  min-width: 0;
}

.customer-admin-surcharge-date-grid {
  display: grid;
  gap: 0.9rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: start;
}

.customer-admin-surcharge-date-help {
  display: grid;
  gap: 0.18rem;
}

.customer-admin-weekday-picker,
.customer-admin-segmented-control {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

@media (max-width: 960px) {
  .customer-admin-hero,
  .customer-admin-lifecycle {
    flex-direction: column;
    align-items: stretch;
  }

  .customer-admin-grid {
    grid-template-columns: 1fr;
  }

  .customer-admin-list-panel {
    position: static;
  }

  .customer-admin-form-grid--detail {
    grid-template-columns: 1fr;
  }

  .customer-admin-form-grid--detail > .field-stack,
  .customer-admin-form-grid--detail > .field-stack--half,
  .customer-admin-form-grid--detail > .field-stack--third,
  .customer-admin-form-grid--detail > .field-stack--wide,
  .customer-admin-form-grid--detail > .customer-admin-surcharge-date-block {
    grid-column: 1 / -1;
  }

  .customer-admin-surcharge-date-grid {
    grid-template-columns: 1fr;
  }

}
</style>
