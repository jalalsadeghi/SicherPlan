import type {
  AssistantCapabilities,
  AssistantClientContext,
  AssistantConversation,
  AssistantFeedbackRating,
  AssistantFeedbackResponse,
  AssistantMessage,
  AssistantRouteContext,
  AssistantStructuredResponse,
} from '#/api/sicherplan/assistant';

import type { RouteLocationNormalizedLoaded } from 'vue-router';

import { computed, ref } from 'vue';

import { preferences } from '@vben/preferences';
import { defineStore } from 'pinia';

import {
  createAssistantConversation,
  getAssistantCapabilities,
  getAssistantConversation,
  normalizeAssistantApiError,
  sendAssistantMessage,
  submitAssistantFeedback,
} from '#/api/sicherplan/assistant';
import { router } from '#/router';

import {
  clearStoredAssistantSessionState,
  persistAssistantSessionState,
  readStoredAssistantSessionState,
} from './assistant-session';

export interface AssistantUiMessage {
  content: string;
  created_at?: string;
  detected_language?: null | string;
  feedback?: AssistantUiFeedbackState;
  id: string;
  pending?: boolean;
  response_language?: null | string;
  role: 'assistant' | 'system_summary' | 'tool' | 'user';
  structured_response?: AssistantStructuredResponse | null;
}

export interface AssistantUiFeedbackState {
  comment?: null | string;
  created_at?: string;
  error?: null | string;
  rating?: AssistantFeedbackRating;
  status: 'idle' | 'submitted' | 'submitting';
}

interface AssistantState {
  capabilities: AssistantCapabilities | null;
  enabled: boolean;
  canChat: boolean;
  isOpen: boolean;
  activeConversationId: null | string;
  messages: AssistantUiMessage[];
  draftInput: string;
  loadingCapabilities: boolean;
  loadingConversation: boolean;
  sendingMessage: boolean;
  error: null | string;
  lastRouteContext: AssistantRouteContext | null;
}

const ASSISTANT_ROUTE_PAGE_IDS: Record<string, string> = {
  SicherPlanCoreAdmin: 'A-02',
  SicherPlanCustomers: 'C-01',
  SicherPlanCustomerOrderWorkspace: 'C-02',
  SicherPlanDashboard: 'F-02',
  SicherPlanEmployees: 'E-01',
  SicherPlanFinanceActuals: 'FI-01',
  SicherPlanFinanceBilling: 'FI-03',
  SicherPlanFinancePayroll: 'FI-02',
  SicherPlanFinanceSubcontractorChecks: 'FI-04',
  SicherPlanHealthDiagnostics: 'A-06',
  SicherPlanPlanning: 'P-01',
  SicherPlanPlanningOrders: 'P-02',
  SicherPlanPlanningShifts: 'P-03',
  SicherPlanPlanningStaffing: 'P-04',
  SicherPlanPlatformServices: 'PS-01',
  SicherPlanRecruiting: 'R-01',
  SicherPlanReporting: 'REP-01',
  SicherPlanSubcontractorPortal: 'SP-01',
  SicherPlanSubcontractors: 'S-01',
  SicherPlanTenantUsers: 'A-05',
};

function sanitizeRouteQuery(
  query: Record<string, unknown> | undefined,
): Record<string, unknown> | undefined {
  if (!query) {
    return undefined;
  }
  const safe: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(query)) {
    if (key === 'tenant_id' || key === 'user_id') {
      continue;
    }
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      safe[key] = value;
      continue;
    }
    if (Array.isArray(value)) {
      safe[key] = value.filter(
        (item) =>
          typeof item === 'string'
          || typeof item === 'number'
          || typeof item === 'boolean',
      );
    }
  }
  return Object.keys(safe).length > 0 ? safe : undefined;
}

function resolveRoutePageId(
  route: RouteLocationNormalizedLoaded,
): null | string {
  const pageId = route.meta?.pageId;
  if (typeof pageId === 'string' && pageId.trim()) {
    return pageId;
  }
  const routeName = typeof route.name === 'string' ? route.name : null;
  if (!routeName) {
    return null;
  }
  return ASSISTANT_ROUTE_PAGE_IDS[routeName] ?? null;
}

function resolveVisiblePageTitle(route: RouteLocationNormalizedLoaded): null | string {
  const metaTitle = route.meta?.title;
  if (typeof metaTitle === 'string' && metaTitle.trim()) {
    return metaTitle;
  }
  if (typeof document !== 'undefined' && document.title.trim()) {
    return document.title.trim();
  }
  return null;
}

function resolveTimezone(): null | string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
  } catch {
    return null;
  }
}

export function buildAssistantRouteContext(
  route: RouteLocationNormalizedLoaded = router.currentRoute.value,
): AssistantRouteContext {
  const routeName = typeof route.name === 'string' ? route.name : null;
  return {
    path: route.path,
    route_name: routeName,
    page_id: resolveRoutePageId(route),
    query: sanitizeRouteQuery(route.query as Record<string, unknown>),
    ui_locale: preferences.app.locale,
    timezone: resolveTimezone(),
    visible_page_title: resolveVisiblePageTitle(route),
  };
}

function buildAssistantClientContext(): AssistantClientContext {
  return {
    timezone: resolveTimezone(),
    ui_locale: preferences.app.locale,
    visible_page_title:
      typeof document !== 'undefined' && document.title.trim()
        ? document.title.trim()
        : null,
  };
}

function mapAssistantMessage(message: AssistantMessage): AssistantUiMessage {
  const structured =
    message.structured_payload
    && typeof message.structured_payload === 'object'
    && 'conversation_id' in message.structured_payload
    ? (message.structured_payload as AssistantStructuredResponse)
    : null;

  return {
    id: message.id,
    role: message.role,
    content: message.content,
    created_at: message.created_at,
    detected_language: message.detected_language ?? null,
    response_language: message.response_language ?? null,
    structured_response: structured,
  };
}

function mapAssistantResponseToMessage(
  response: AssistantStructuredResponse,
): AssistantUiMessage {
  return {
    id: response.message_id,
    role: 'assistant',
    content: response.answer,
    detected_language: response.detected_language ?? null,
    response_language: response.response_language ?? null,
    structured_response: response,
  };
}

function makeLocalMessageId(prefix: string) {
  return `local-${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function persistAssistantState(state: AssistantState) {
  persistAssistantSessionState({
    activeConversationId: state.activeConversationId ?? '',
    canChat: state.canChat,
    capabilities: state.capabilities,
    draftInput: state.draftInput,
    enabled: state.enabled,
    isOpen: state.isOpen,
    lastRouteContext: state.lastRouteContext,
  });
}

export const useAssistantStore = defineStore('assistant', () => {
  const persisted = readStoredAssistantSessionState();

  const capabilities = ref<AssistantCapabilities | null>(persisted.capabilities);
  const enabled = ref(persisted.enabled);
  const canChat = ref(persisted.canChat);
  const isOpen = ref(persisted.isOpen);
  const activeConversationId = ref<null | string>(
    persisted.activeConversationId || null,
  );
  const messages = ref<AssistantUiMessage[]>([]);
  const draftInput = ref(persisted.draftInput);
  const loadingCapabilities = ref(false);
  const loadingConversation = ref(false);
  const sendingMessage = ref(false);
  const error = ref<null | string>(null);
  const feedbackByMessageId = ref<Record<string, AssistantUiFeedbackState>>({});
  const lastRouteContext = ref<AssistantRouteContext | null>(
    persisted.lastRouteContext,
  );

  const state = computed<AssistantState>(() => ({
    capabilities: capabilities.value,
    enabled: enabled.value,
    canChat: canChat.value,
    isOpen: isOpen.value,
    activeConversationId: activeConversationId.value,
    messages: messages.value,
    draftInput: draftInput.value,
    loadingCapabilities: loadingCapabilities.value,
    loadingConversation: loadingConversation.value,
    sendingMessage: sendingMessage.value,
    error: error.value,
    lastRouteContext: lastRouteContext.value,
  }));

  function applyConversation(conversation: AssistantConversation) {
    activeConversationId.value = conversation.id;
    messages.value = (conversation.messages ?? []).map((message) =>
      attachFeedbackState(mapAssistantMessage(message)),
    );
  }

  function attachFeedbackState(message: AssistantUiMessage): AssistantUiMessage {
    const feedback = feedbackByMessageId.value[message.id];
    if (!feedback) {
      return message;
    }
    return {
      ...message,
      feedback: { ...feedback },
    };
  }

  function captureCurrentRouteContext() {
    lastRouteContext.value = buildAssistantRouteContext();
    persistAssistantState(state.value);
    return lastRouteContext.value;
  }

  async function loadCapabilities(force = false) {
    if (!force && capabilities.value) {
      return capabilities.value;
    }
    loadingCapabilities.value = true;
    error.value = null;
    try {
      const result = await getAssistantCapabilities();
      capabilities.value = result;
      enabled.value = result.enabled;
      canChat.value = result.enabled && result.can_chat;
      persistAssistantState(state.value);
      return result;
    } catch (caught) {
      const normalized = normalizeAssistantApiError(caught);
      error.value = normalized.messageKey;
      capabilities.value = null;
      enabled.value = false;
      canChat.value = false;
      persistAssistantState(state.value);
      throw caught;
    } finally {
      loadingCapabilities.value = false;
    }
  }

  async function refreshConversation() {
    if (!activeConversationId.value) {
      messages.value = [];
      persistAssistantState(state.value);
      return null;
    }
    loadingConversation.value = true;
    error.value = null;
    try {
      const conversation = await getAssistantConversation(activeConversationId.value);
      applyConversation(conversation);
      persistAssistantState(state.value);
      return conversation;
    } catch (caught) {
      const normalized = normalizeAssistantApiError(caught);
      error.value = normalized.messageKey;
      if (normalized.code === 'assistant.conversation.not_found') {
        activeConversationId.value = null;
        messages.value = [];
        persistAssistantState(state.value);
      }
      throw caught;
    } finally {
      loadingConversation.value = false;
    }
  }

  async function restorePersistedConversation() {
    captureCurrentRouteContext();
    if (!activeConversationId.value) {
      return null;
    }
    return await refreshConversation();
  }

  async function startConversationIfNeeded() {
    if (activeConversationId.value) {
      return activeConversationId.value;
    }
    const routeContext = captureCurrentRouteContext();
    const conversation = await createAssistantConversation({
      initial_route: routeContext,
      locale: preferences.app.locale,
    });
    activeConversationId.value = conversation.id;
    if (messages.value.length === 0) {
      applyConversation(conversation);
    }
    persistAssistantState(state.value);
    return conversation.id;
  }

  async function sendMessage(message: string) {
    const cleaned = message.trim();
    if (!cleaned) {
      return null;
    }

    sendingMessage.value = true;
    error.value = null;
    const routeContext = captureCurrentRouteContext();

    const optimisticUserMessage: AssistantUiMessage = {
      id: makeLocalMessageId('user'),
      role: 'user',
      content: cleaned,
    };
    const pendingAssistantMessage: AssistantUiMessage = {
      id: makeLocalMessageId('assistant-pending'),
      role: 'assistant',
      content: '',
      pending: true,
    };
    messages.value = [...messages.value, optimisticUserMessage, pendingAssistantMessage];
    draftInput.value = '';
    persistAssistantState(state.value);

    try {
      const conversationId = await startConversationIfNeeded();
      const response = await sendAssistantMessage(conversationId, {
        message: cleaned,
        route_context: routeContext,
        client_context: buildAssistantClientContext(),
      });
      activeConversationId.value = response.conversation_id;
      const assistantMessage = attachFeedbackState(mapAssistantResponseToMessage(response));
      messages.value = messages.value.map((item) =>
        item.id === pendingAssistantMessage.id ? assistantMessage : item,
      );
      persistAssistantState(state.value);
      return response;
    } catch (caught) {
      messages.value = messages.value.filter(
        (item) =>
          item.id !== optimisticUserMessage.id && item.id !== pendingAssistantMessage.id,
      );
      draftInput.value = cleaned;
      const normalized = normalizeAssistantApiError(caught);
      error.value = normalized.messageKey;
      persistAssistantState(state.value);
      throw caught;
    } finally {
      sendingMessage.value = false;
    }
  }

  function setFeedbackState(messageId: string, value: AssistantUiFeedbackState) {
    feedbackByMessageId.value = {
      ...feedbackByMessageId.value,
      [messageId]: value,
    };
    messages.value = messages.value.map((message) =>
      message.id === messageId
        ? {
            ...message,
            feedback: { ...value },
          }
        : message,
    );
  }

  async function submitFeedback(
    messageId: string,
    rating: AssistantFeedbackRating,
    comment?: null | string,
  ): Promise<AssistantFeedbackResponse> {
    if (!activeConversationId.value) {
      throw new Error('assistant.feedback.conversation_missing');
    }
    const message = messages.value.find((item) => item.id === messageId);
    if (!message || message.role !== 'assistant') {
      throw new Error('assistant.feedback.message_invalid');
    }

    setFeedbackState(messageId, {
      comment: comment?.trim() || null,
      error: null,
      rating,
      status: 'submitting',
    });

    try {
      const response = await submitAssistantFeedback(activeConversationId.value, {
        message_id: messageId,
        rating,
        comment: comment?.trim() || null,
      });
      setFeedbackState(messageId, {
        comment: comment?.trim() || null,
        created_at: response.created_at,
        error: null,
        rating: response.rating,
        status: 'submitted',
      });
      return response;
    } catch (caught) {
      const normalized = normalizeAssistantApiError(caught);
      setFeedbackState(messageId, {
        comment: comment?.trim() || null,
        error: normalized.messageKey,
        rating,
        status: 'idle',
      });
      throw caught;
    }
  }

  async function openAssistant() {
    if (!capabilities.value) {
      await loadCapabilities();
    }
    if (!enabled.value || !canChat.value) {
      isOpen.value = false;
      persistAssistantState(state.value);
      return false;
    }
    isOpen.value = true;
    captureCurrentRouteContext();
    if (activeConversationId.value) {
      await refreshConversation().catch(() => undefined);
    }
    persistAssistantState(state.value);
    return true;
  }

  function closeAssistant() {
    isOpen.value = false;
    persistAssistantState(state.value);
  }

  function setDraftInput(value: string) {
    draftInput.value = value;
    persistAssistantState(state.value);
  }

  function clearConversation() {
    activeConversationId.value = null;
    feedbackByMessageId.value = {};
    messages.value = [];
    draftInput.value = '';
    error.value = null;
    persistAssistantState(state.value);
  }

  function resetAssistantState() {
    capabilities.value = null;
    enabled.value = false;
    canChat.value = false;
    isOpen.value = false;
    activeConversationId.value = null;
    messages.value = [];
    draftInput.value = '';
    loadingCapabilities.value = false;
    loadingConversation.value = false;
    sendingMessage.value = false;
    error.value = null;
    feedbackByMessageId.value = {};
    lastRouteContext.value = null;
    clearStoredAssistantSessionState();
  }

  return {
    capabilities,
    enabled,
    canChat,
    isOpen,
    activeConversationId,
    messages,
    draftInput,
    loadingCapabilities,
    loadingConversation,
    sendingMessage,
    error,
    lastRouteContext,
    captureCurrentRouteContext,
    clearConversation,
    closeAssistant,
    loadCapabilities,
    openAssistant,
    refreshConversation,
    resetAssistantState,
    restorePersistedConversation,
    sendMessage,
    setDraftInput,
    submitFeedback,
    startConversationIfNeeded,
  };
});
