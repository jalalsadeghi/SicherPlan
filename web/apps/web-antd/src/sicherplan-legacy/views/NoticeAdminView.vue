<template>
  <section class="notice-page">
    <AdminPageShell
      v-if="!embedded"
      :eyebrow="t('noticeAdmin.eyebrow')"
      :title="t('noticeAdmin.title')"
      :lead="t('noticeAdmin.lead')"
    >
      <template #actions>
        <div class="module-card notice-scope">
          <label class="field-stack">
            <span>{{ t("noticeAdmin.scope.label") }}</span>
            <input v-model="tenantScopeInput" :placeholder="t('noticeAdmin.scope.placeholder')" />
          </label>
          <button class="cta-button" type="button" @click="rememberScope">
            {{ t("noticeAdmin.scope.action") }}
          </button>
        </div>
      </template>
    </AdminPageShell>

    <section v-else class="module-card notice-scope notice-scope--embedded">
      <label class="field-stack">
        <span>{{ t("noticeAdmin.scope.label") }}</span>
        <input v-model="tenantScopeInput" :placeholder="t('noticeAdmin.scope.placeholder')" />
      </label>
      <button class="cta-button" type="button" @click="rememberScope">
        {{ t("noticeAdmin.scope.action") }}
      </button>
    </section>

    <section v-if="feedback" class="notice-feedback">{{ feedback }}</section>

    <section v-if="!tenantScopeId" class="module-card">
      <p class="eyebrow">{{ t("noticeAdmin.scope.missingTitle") }}</p>
      <h3>{{ t("noticeAdmin.scope.missingBody") }}</h3>
    </section>

    <div v-else class="notice-grid">
      <section class="module-card">
        <p class="eyebrow">{{ t("noticeAdmin.form.eyebrow") }}</p>
        <h3>{{ t("noticeAdmin.form.title") }}</h3>
        <form class="notice-form" @submit.prevent="submitNotice">
          <label class="field-stack">
            <span>{{ t("noticeAdmin.fields.title") }}</span>
            <input v-model="draft.title" required />
          </label>
          <label class="field-stack">
            <span>{{ t("noticeAdmin.fields.summary") }}</span>
            <input v-model="draft.summary" />
          </label>
          <label class="field-stack">
            <span>{{ t("noticeAdmin.fields.body") }}</span>
            <textarea v-model="draft.body" rows="6" required />
          </label>
          <label class="field-stack">
            <span>{{ t("noticeAdmin.fields.audienceRole") }}</span>
            <select v-model="draft.audienceRole">
              <option value="dispatcher">{{ t("role.dispatcher") }}</option>
              <option value="accounting">{{ t("role.accounting") }}</option>
              <option value="controller_qm">{{ t("role.controller_qm") }}</option>
              <option value="customer_user">{{ t("role.customer_user") }}</option>
              <option value="subcontractor_user">{{ t("role.subcontractor_user") }}</option>
            </select>
          </label>
          <label class="notice-checkbox">
            <input v-model="draft.mandatory" type="checkbox" />
            <span>{{ t("noticeAdmin.fields.mandatory") }}</span>
          </label>
          <div class="cta-row">
            <button class="cta-button" type="submit" :disabled="loading">{{ t("noticeAdmin.actions.create") }}</button>
            <button class="cta-button cta-secondary" type="button" @click="refreshLists">{{ t("noticeAdmin.actions.refresh") }}</button>
          </div>
        </form>
      </section>

      <section class="module-card">
        <p class="eyebrow">{{ t("noticeAdmin.list.eyebrow") }}</p>
        <h3>{{ t("noticeAdmin.list.title") }}</h3>
        <div v-if="adminNotices.length" class="notice-list">
          <article v-for="notice in adminNotices" :key="notice.id" class="notice-row">
            <div>
              <strong>{{ notice.title }}</strong>
              <p>{{ notice.summary || notice.status }}</p>
            </div>
            <div class="cta-row">
              <button v-if="notice.status !== 'published'" class="cta-button" type="button" @click="publishDraft(notice.id)">
                {{ t("noticeAdmin.actions.publish") }}
              </button>
              <span class="notice-pill">{{ notice.status }}</span>
            </div>
          </article>
        </div>
        <p v-else>{{ t("noticeAdmin.list.empty") }}</p>
      </section>

      <section class="module-card">
        <p class="eyebrow">{{ t("noticeAdmin.feed.eyebrow") }}</p>
        <h3>{{ t("noticeAdmin.feed.title") }}</h3>
        <div v-if="myFeed.length" class="notice-list">
          <article v-for="notice in myFeed" :key="notice.id" class="notice-row">
            <div>
              <strong>{{ notice.title }}</strong>
              <p>{{ notice.summary || notice.status }}</p>
              <p v-if="notice.attachments.length || notice.links.length" class="notice-meta">
                {{ notice.attachments.length }} / {{ notice.links.length }}
              </p>
            </div>
            <div class="cta-row">
              <button class="cta-button cta-secondary" type="button" @click="openFeedNotice(notice.id)">
                {{ t("noticeAdmin.actions.refresh") }}
              </button>
              <button
                v-if="notice.mandatory_acknowledgement && !notice.acknowledged_at"
                class="cta-button"
                type="button"
                @click="acknowledge(notice.id)"
              >
                {{ t("noticeAdmin.actions.acknowledge") }}
              </button>
              <span v-else class="notice-pill">
                {{ notice.acknowledged_at ? t("noticeAdmin.feed.acknowledged") : notice.status }}
              </span>
            </div>
          </article>
        </div>
        <p v-else>{{ t("noticeAdmin.feed.empty") }}</p>
      </section>

      <section v-if="selectedFeedNotice" class="module-card">
        <p class="eyebrow">{{ t("noticeAdmin.feed.eyebrow") }}</p>
        <h3>{{ selectedFeedNotice.title }}</h3>
        <p class="notice-lead">{{ selectedFeedNotice.body }}</p>
        <ul v-if="selectedFeedNotice.links.length" class="notice-list-inline">
          <li v-for="link in selectedFeedNotice.links" :key="link.id">
            <a :href="link.url" target="_blank" rel="noreferrer">{{ link.label }}</a>
          </li>
        </ul>
        <ul v-if="selectedFeedNotice.attachments.length" class="notice-list-inline">
          <li v-for="attachment in selectedFeedNotice.attachments" :key="attachment.document_id">
            <button
              class="secondary-button"
              type="button"
              :disabled="!attachment.current_version_no"
              @click="downloadAttachment(attachment.document_id, attachment.current_version_no || 1, attachment.file_name || attachment.title)"
            >
              {{ attachment.file_name || attachment.title }}
            </button>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import AdminPageShell from "@/components/AdminPageShell.vue";
import {
  acknowledgeNotice,
  createNotice,
  downloadNoticeAttachment,
  getVisibleNotice,
  listAdminNotices,
  listMyNoticeFeed,
  openNotice,
  publishNotice,
  type NoticeListItem,
  type NoticeRead,
} from "@/api/notices";
import { useI18n } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false,
});

const { t } = useI18n();
const authStore = useAuthStore();

const tenantScopeInput = ref(authStore.tenantScopeId);
const tenantScopeId = ref(authStore.tenantScopeId);
const feedback = ref("");
const loading = ref(false);
const adminNotices = ref<NoticeListItem[]>([]);
const myFeed = ref<NoticeListItem[]>([]);
const selectedFeedNotice = ref<NoticeRead | null>(null);
const draft = reactive({
  title: "",
  summary: "",
  body: "",
  audienceRole: "dispatcher",
  mandatory: false,
});

function rememberScope() {
  authStore.setTenantScopeId(tenantScopeInput.value);
  tenantScopeId.value = authStore.tenantScopeId;
  void refreshLists();
}

async function refreshLists() {
  const accessToken = authStore.accessToken;
  if (!tenantScopeId.value || !accessToken) {
    adminNotices.value = [];
    myFeed.value = [];
    return;
  }
  try {
    adminNotices.value = await listAdminNotices(tenantScopeId.value, accessToken);
    myFeed.value = await listMyNoticeFeed(tenantScopeId.value, accessToken);
  } catch {
    feedback.value = t("noticeAdmin.feedback.error");
  }
}

async function submitNotice() {
  if (!tenantScopeId.value) {
    feedback.value = t("noticeAdmin.scope.missingBody");
    return;
  }
  loading.value = true;
  try {
    const created = await createNotice(tenantScopeId.value, authStore.accessToken, {
      tenant_id: tenantScopeId.value,
      title: draft.title,
      summary: draft.summary || null,
      body: draft.body,
      language_code: "de",
      mandatory_acknowledgement: draft.mandatory,
      audiences: [{ audience_kind: "role", target_value: draft.audienceRole }],
      curated_links: [],
      attachment_document_ids: [],
    });
    feedback.value = `${t("noticeAdmin.feedback.created")}: ${created.title}`;
    draft.title = "";
    draft.summary = "";
    draft.body = "";
    draft.mandatory = false;
    await refreshLists();
  } catch {
    feedback.value = t("noticeAdmin.feedback.error");
  } finally {
    loading.value = false;
  }
}

async function publishDraft(noticeId: string) {
  if (!tenantScopeId.value) return;
  try {
    await publishNotice(tenantScopeId.value, noticeId, authStore.accessToken);
    feedback.value = t("noticeAdmin.feedback.published");
    await refreshLists();
  } catch {
    feedback.value = t("noticeAdmin.feedback.error");
  }
}

async function acknowledge(noticeId: string) {
  if (!tenantScopeId.value) return;
  try {
    await acknowledgeNotice(tenantScopeId.value, noticeId, authStore.accessToken);
    feedback.value = t("noticeAdmin.feedback.acknowledged");
    await refreshLists();
  } catch {
    feedback.value = t("noticeAdmin.feedback.error");
  }
}

async function openFeedNotice(noticeId: string) {
  if (!tenantScopeId.value) return;
  try {
    await openNotice(tenantScopeId.value, noticeId, authStore.accessToken);
    selectedFeedNotice.value = await getVisibleNotice(tenantScopeId.value, noticeId, authStore.accessToken);
    await refreshLists();
  } catch {
    feedback.value = t("noticeAdmin.feedback.error");
  }
}

async function downloadAttachment(documentId: string, versionNo: number, fileName: string) {
  if (!tenantScopeId.value) return;
  try {
    const blob = await downloadNoticeAttachment(tenantScopeId.value, documentId, versionNo, authStore.accessToken);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(url);
  } catch {
    feedback.value = t("noticeAdmin.feedback.error");
  }
}

onMounted(() => {
  if (!tenantScopeId.value && authStore.sessionUser?.tenant_id) {
    authStore.setTenantScopeId(authStore.sessionUser.tenant_id);
    tenantScopeId.value = authStore.tenantScopeId;
    tenantScopeInput.value = authStore.tenantScopeId;
  }
  void refreshLists();
});
</script>

<style scoped>
.notice-page,
.notice-grid,
.notice-form,
.notice-list,
.notice-scope {
  display: grid;
  gap: 1rem;
}

.notice-grid {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.notice-hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.notice-feedback {
  padding: 0.9rem 1rem;
  border-radius: 16px;
  background: var(--sp-color-primary-muted);
  color: var(--sp-color-primary-strong);
}

.notice-scope--embedded {
  margin-bottom: 0.25rem;
}

.notice-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  border-radius: 16px;
  background: var(--sp-color-surface-page);
  border: 1px solid var(--sp-color-border-soft);
}

.notice-lead,
.notice-row p {
  margin: 0.35rem 0 0 0;
  color: var(--sp-color-text-secondary);
}

.notice-pill {
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  background: var(--sp-color-primary-muted);
  color: var(--sp-color-primary-strong);
  font-size: 0.85rem;
}

.notice-meta,
.notice-list-inline {
  margin: 0.35rem 0 0;
  color: var(--sp-color-text-secondary);
}

.notice-checkbox {
  display: flex;
  gap: 0.65rem;
  align-items: center;
}
</style>
