import type { AssistantCapabilities, AssistantRouteContext } from '#/api/sicherplan/assistant';

const ASSISTANT_SESSION_KEY = 'sicherplan.assistant.session';

export interface StoredAssistantSessionState {
  activeConversationId: string;
  canChat: boolean;
  capabilities: AssistantCapabilities | null;
  draftInput: string;
  enabled: boolean;
  isOpen: boolean;
  lastRouteContext: AssistantRouteContext | null;
}

function canUseSessionStorage() {
  return typeof window !== 'undefined';
}

function emptyAssistantSessionState(): StoredAssistantSessionState {
  return {
    activeConversationId: '',
    canChat: false,
    capabilities: null,
    draftInput: '',
    enabled: false,
    isOpen: false,
    lastRouteContext: null,
  };
}

export function readStoredAssistantSessionState(): StoredAssistantSessionState {
  if (!canUseSessionStorage()) {
    return emptyAssistantSessionState();
  }

  const rawValue = window.sessionStorage.getItem(ASSISTANT_SESSION_KEY);
  if (!rawValue) {
    return emptyAssistantSessionState();
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<StoredAssistantSessionState>;
    return {
      activeConversationId:
        typeof parsed.activeConversationId === 'string'
          ? parsed.activeConversationId
          : '',
      canChat: parsed.canChat === true,
      capabilities:
        parsed.capabilities && typeof parsed.capabilities === 'object'
          ? (parsed.capabilities as AssistantCapabilities)
          : null,
      draftInput: typeof parsed.draftInput === 'string' ? parsed.draftInput : '',
      enabled: parsed.enabled === true,
      isOpen: parsed.isOpen === true,
      lastRouteContext:
        parsed.lastRouteContext && typeof parsed.lastRouteContext === 'object'
          ? (parsed.lastRouteContext as AssistantRouteContext)
          : null,
    };
  } catch {
    return emptyAssistantSessionState();
  }
}

export function persistAssistantSessionState(
  state: Partial<StoredAssistantSessionState>,
) {
  if (!canUseSessionStorage()) {
    return;
  }

  const current = readStoredAssistantSessionState();
  const normalized: StoredAssistantSessionState = {
    activeConversationId: state.activeConversationId?.trim() ?? current.activeConversationId,
    canChat: state.canChat ?? current.canChat,
    capabilities: state.capabilities ?? current.capabilities,
    draftInput: state.draftInput ?? current.draftInput,
    enabled: state.enabled ?? current.enabled,
    isOpen: state.isOpen ?? current.isOpen,
    lastRouteContext: state.lastRouteContext ?? current.lastRouteContext,
  };

  if (
    !normalized.activeConversationId
    && !normalized.draftInput
    && !normalized.isOpen
    && !normalized.enabled
    && !normalized.canChat
    && normalized.capabilities == null
    && normalized.lastRouteContext == null
  ) {
    window.sessionStorage.removeItem(ASSISTANT_SESSION_KEY);
    return;
  }

  window.sessionStorage.setItem(
    ASSISTANT_SESSION_KEY,
    JSON.stringify(normalized),
  );
}

export function clearStoredAssistantSessionState() {
  if (!canUseSessionStorage()) {
    return;
  }
  window.sessionStorage.removeItem(ASSISTANT_SESSION_KEY);
}
