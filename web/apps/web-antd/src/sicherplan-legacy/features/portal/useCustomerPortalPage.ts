import { computed, onMounted, ref } from "vue";

import { AuthApiError } from "@/api/auth";
import { useI18n } from "@/i18n";
import type { MessageKey } from "@/i18n/messages";
import { useAuthStore } from "@/stores/auth";

import {
  derivePortalCustomerAccessState,
  mapPortalApiMessage,
} from "./customerPortal.helpers.js";

type UseCustomerPortalPageOptions = {
  clearPageData?: () => void;
  loadPageData?: () => Promise<void>;
};

export function useCustomerPortalPage(options: UseCustomerPortalPageOptions = {}) {
  const authStore = useAuthStore();
  const { locale } = useI18n();

  const tenantCode = ref("");
  const identifier = ref("");
  const password = ref("");
  const deviceLabel = ref("Customer Portal");
  const loading = ref(false);
  const lastErrorKey = ref("");
  const feedbackKey = ref<MessageKey | null>(null);
  const feedbackTone = ref<"info" | "success" | "error">("info");

  const portalContext = computed(() => authStore.portalCustomerContext);
  const accessState = computed(() =>
    derivePortalCustomerAccessState({
      isLoading: loading.value,
      hasSession: authStore.hasSession,
      hasContext: Boolean(portalContext.value),
      lastErrorKey: lastErrorKey.value,
    }),
  );
  const portalDiagnosticTitleKey = computed<MessageKey | null>(() => {
    switch (accessState.value) {
      case "missing_permission":
        return "portalCustomer.permissionDenied.title";
      case "missing_scope":
        return "portalCustomer.scopeMissing.title";
      case "contact_not_linked":
        return "portalCustomer.contactNotLinked.title";
      case "contact_inactive":
        return "portalCustomer.contactInactive.title";
      case "customer_inactive":
        return "portalCustomer.customerInactive.title";
      case "error":
        return "portalCustomer.error.title";
      default:
        return null;
    }
  });
  const portalDiagnosticBodyKey = computed<MessageKey | null>(() => {
    switch (accessState.value) {
      case "missing_permission":
        return "portalCustomer.permissionDenied.body";
      case "missing_scope":
        return "portalCustomer.scopeMissing.body";
      case "contact_not_linked":
        return "portalCustomer.contactNotLinked.body";
      case "contact_inactive":
        return "portalCustomer.contactInactive.body";
      case "customer_inactive":
        return "portalCustomer.customerInactive.body";
      case "error":
        return "portalCustomer.error.body";
      default:
        return null;
    }
  });
  const portalScopeSummary = computed(
    () => portalContext.value?.scopes.map((scope) => scope.customer_id).join(", ") ?? "-",
  );

  function setFeedback(messageKey: MessageKey, tone: "info" | "success" | "error") {
    feedbackKey.value = messageKey;
    feedbackTone.value = tone;
  }

  function clearFeedback() {
    feedbackKey.value = null;
  }

  function clearPageState() {
    options.clearPageData?.();
  }

  async function loadResolvedPageData() {
    if (!authStore.accessToken) {
      clearPageState();
      return;
    }

    await options.loadPageData?.();
  }

  async function bootstrapPortalContext() {
    if (!authStore.accessToken) {
      clearPageState();
      return;
    }

    loading.value = true;
    clearFeedback();

    try {
      await authStore.loadCurrentSession();
      await authStore.loadCustomerPortalContext();
      await loadResolvedPageData();
      lastErrorKey.value = "";
      setFeedback("portalCustomer.feedback.sessionReady", "success");
    } catch (error) {
      clearPageState();
      const messageKey =
        error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
      lastErrorKey.value = messageKey;
      setFeedback(mapPortalApiMessage(messageKey), "error");
    } finally {
      loading.value = false;
    }
  }

  async function submitLogin() {
    loading.value = true;
    clearFeedback();
    authStore.clearPortalCustomerContext();
    clearPageState();

    try {
      await authStore.loginCustomerPortal({
        tenant_code: tenantCode.value,
        identifier: identifier.value,
        password: password.value,
        device_label: deviceLabel.value,
      });
      await authStore.loadCustomerPortalContext();
      await loadResolvedPageData();
      lastErrorKey.value = "";
      setFeedback("portalCustomer.feedback.sessionReady", "success");
    } catch (error) {
      clearPageState();
      const messageKey =
        error instanceof AuthApiError ? error.messageKey : "errors.platform.internal";
      lastErrorKey.value = messageKey;
      setFeedback(mapPortalApiMessage(messageKey), "error");
    } finally {
      loading.value = false;
    }
  }

  async function refreshPortalContext() {
    await bootstrapPortalContext();
  }

  async function logoutPortalSession() {
    await authStore.logoutPortalSession();
    authStore.clearPortalCustomerContext();
    clearPageState();
    lastErrorKey.value = "";
    setFeedback("portalCustomer.feedback.loggedOut", "info");
  }

  function formatDate(value: string | null) {
    if (!value) {
      return "-";
    }

    return new Intl.DateTimeFormat(locale.value === "de" ? "de-DE" : "en-US", {
      dateStyle: "medium",
    }).format(new Date(value));
  }

  function formatDateTime(value: string | null) {
    if (!value) {
      return "-";
    }

    return new Intl.DateTimeFormat(locale.value === "de" ? "de-DE" : "en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  }

  onMounted(() => {
    if (authStore.hasSession) {
      void bootstrapPortalContext();
    }
  });

  return {
    accessState,
    authStore,
    bootstrapPortalContext,
    clearFeedback,
    deviceLabel,
    feedbackKey,
    feedbackTone,
    formatDate,
    formatDateTime,
    identifier,
    lastErrorKey,
    loading,
    logoutPortalSession,
    password,
    portalContext,
    portalDiagnosticBodyKey,
    portalDiagnosticTitleKey,
    portalScopeSummary,
    refreshPortalContext,
    setFeedback,
    submitLogin,
    tenantCode,
  };
}
