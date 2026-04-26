// @vitest-environment happy-dom

import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  createAssistantConversation,
  getAssistantCapabilities,
  getAssistantConversation,
  routerCurrentRoute,
  sendAssistantMessage,
  submitAssistantFeedback,
} = vi.hoisted(() => ({
  createAssistantConversation: vi.fn(),
  getAssistantCapabilities: vi.fn(),
  getAssistantConversation: vi.fn(),
  routerCurrentRoute: {
    value: {
      name: 'SicherPlanPlanningStaffing',
      path: '/admin/planning-staffing',
      query: { assignment_id: 'assignment-1', user_id: 'should-be-removed' },
      meta: {
        moduleKey: 'planning-staffing',
        title: 'Staffing Board & Coverage',
      },
    } as any,
  },
  sendAssistantMessage: vi.fn(),
  submitAssistantFeedback: vi.fn(),
}));

vi.mock('#/api/sicherplan/assistant', async () => {
  const actual = await vi.importActual<typeof import('#/api/sicherplan/assistant')>('#/api/sicherplan/assistant');
  return {
    ...actual,
    createAssistantConversation,
    getAssistantCapabilities,
    getAssistantConversation,
    sendAssistantMessage,
    submitAssistantFeedback,
  };
});

vi.mock('#/router', () => ({
  router: {
    currentRoute: routerCurrentRoute,
  },
}));

import { buildAssistantRouteContext, useAssistantStore } from './assistant';

describe('assistant store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    vi.clearAllMocks();
    routerCurrentRoute.value = {
      name: 'SicherPlanPlanningStaffing',
      path: '/admin/planning-staffing',
      query: { assignment_id: 'assignment-1', user_id: 'should-be-removed' },
      meta: {
        moduleKey: 'planning-staffing',
        title: 'Staffing Board & Coverage',
      },
    };
  });

  it('builds route context from router state with known page mapping and sanitized query', () => {
    const context = buildAssistantRouteContext();

    expect(context).toMatchObject({
      path: '/admin/planning-staffing',
      route_name: 'SicherPlanPlanningStaffing',
      page_id: 'P-04',
      ui_locale: 'de-DE',
      visible_page_title: 'Staffing Board & Coverage',
    });
    expect(context.query).toEqual({ assignment_id: 'assignment-1' });
  });

  it('starts with safe empty state when nothing is persisted', () => {
    const store = useAssistantStore();

    expect(store.enabled).toBe(false);
    expect(store.canChat).toBe(false);
    expect(store.isOpen).toBe(false);
    expect(store.activeConversationId).toBeNull();
    expect(store.messages).toEqual([]);
    expect(store.draftInput).toBe('');
    expect(store.loadingCapabilities).toBe(false);
    expect(store.loadingConversation).toBe(false);
    expect(store.sendingMessage).toBe(false);
    expect(store.error).toBeNull();
    expect(store.lastRouteContext).toBeNull();
  });

  it('loads capabilities and respects backend feature flags', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
      supported_features: ['structured_responses'],
    });

    const store = useAssistantStore();
    await store.loadCapabilities();

    expect(store.enabled).toBe(true);
    expect(store.canChat).toBe(true);
    expect(store.capabilities?.provider_mode).toBe('mock');
  });

  it('opens only when backend says assistant chat is available', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: false,
      can_chat: false,
      provider_mode: 'mock',
    });

    const store = useAssistantStore();
    await expect(store.openAssistant()).resolves.toBe(false);
    expect(store.isOpen).toBe(false);
  });

  it('persists open state, draft input, and active conversation id to session storage', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
    });
    createAssistantConversation.mockResolvedValue({
      id: 'conversation-1',
      messages: [],
    });

    const store = useAssistantStore();
    await store.openAssistant();
    store.setDraftInput('Markus pruefen');
    await store.startConversationIfNeeded();

    expect(JSON.parse(sessionStorage.getItem('sicherplan.assistant.session') ?? '{}')).toMatchObject({
      activeConversationId: 'conversation-1',
      canChat: true,
      draftInput: 'Markus pruefen',
      enabled: true,
      isOpen: true,
      lastRouteContext: expect.objectContaining({
        page_id: 'P-04',
      }),
    });
  });

  it('starts a conversation, sends a message, and appends optimistic user plus assistant response', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
    });
    createAssistantConversation.mockResolvedValue({
      id: 'conversation-1',
      messages: [],
    });
    sendAssistantMessage.mockResolvedValue({
      conversation_id: 'conversation-1',
      message_id: 'message-1',
      answer: 'Ich habe Markus geprueft.',
      response_language: 'de',
      diagnosis: [],
      links: [],
      missing_permissions: [],
      next_steps: [],
    });

    const store = useAssistantStore();
    await store.openAssistant();
    await store.sendMessage('Warum sieht Markus die Schicht nicht?');

    expect(createAssistantConversation).toHaveBeenCalledWith(
      expect.objectContaining({
        initial_route: expect.objectContaining({
          page_id: 'P-04',
          route_name: 'SicherPlanPlanningStaffing',
        }),
        locale: 'de-DE',
      }),
    );
    expect(sendAssistantMessage).toHaveBeenCalledWith(
      'conversation-1',
      expect.objectContaining({
        route_context: expect.objectContaining({
          page_id: 'P-04',
        }),
        client_context: expect.objectContaining({
          ui_locale: 'de-DE',
        }),
      }),
    );
    expect(store.messages.map((item) => item.role)).toEqual(['user', 'assistant']);
    expect(store.messages[1]?.structured_response?.answer).toBe('Ich habe Markus geprueft.');
    expect(store.activeConversationId).toBe('conversation-1');
  });

  it('restores a persisted conversation from session storage and refreshes it from the backend', async () => {
    sessionStorage.setItem(
      'sicherplan.assistant.session',
      JSON.stringify({
        activeConversationId: 'conversation-restore',
        canChat: true,
        capabilities: {
          enabled: true,
          can_chat: true,
          provider_mode: 'mock',
        },
        draftInput: 'draft',
        enabled: true,
        isOpen: true,
        lastRouteContext: {
          path: '/admin/planning-staffing',
          route_name: 'SicherPlanPlanningStaffing',
          page_id: 'P-04',
        },
      }),
    );
    getAssistantConversation.mockResolvedValue({
      id: 'conversation-restore',
      messages: [
        {
          id: 'assistant-1',
          role: 'assistant',
          content: 'Vorhandene Antwort',
          structured_payload: {
            conversation_id: 'conversation-restore',
            message_id: 'assistant-1',
            answer: 'Vorhandene Antwort',
          },
        },
      ],
    });

    const store = useAssistantStore();
    await store.restorePersistedConversation();

    expect(getAssistantConversation).toHaveBeenCalledWith('conversation-restore');
    expect(store.activeConversationId).toBe('conversation-restore');
    expect(store.messages[0]?.content).toBe('Vorhandene Antwort');
    expect(store.draftInput).toBe('draft');
  });

  it('keeps conversation state across route changes and updates route context', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
    });
    createAssistantConversation.mockResolvedValue({
      id: 'conversation-1',
      messages: [],
    });
    sendAssistantMessage.mockResolvedValue({
      conversation_id: 'conversation-1',
      message_id: 'message-1',
      answer: 'Ich habe Markus geprueft.',
      response_language: 'de',
      diagnosis: [],
      links: [],
      missing_permissions: [],
      next_steps: [],
    });

    const store = useAssistantStore();
    await store.openAssistant();
    await store.sendMessage('Warum sieht Markus die Schicht nicht?');

    routerCurrentRoute.value = {
      name: 'SicherPlanEmployees',
      path: '/admin/employees',
      query: { employee_id: 'employee-1', tenant_id: 'ignore-me' },
      meta: {
        moduleKey: 'employees',
        title: 'Employees',
      },
    };

    const updatedContext = store.captureCurrentRouteContext();

    expect(store.messages.map((item) => item.role)).toEqual(['user', 'assistant']);
    expect(updatedContext).toMatchObject({
      page_id: 'E-01',
      path: '/admin/employees',
      route_name: 'SicherPlanEmployees',
      visible_page_title: 'Employees',
    });
    expect(updatedContext.query).toEqual({ employee_id: 'employee-1' });
  });

  it('keeps the draft and exposes normalized error when message send fails', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
    });
    createAssistantConversation.mockResolvedValue({
      id: 'conversation-1',
      messages: [],
    });
    sendAssistantMessage.mockRejectedValue({
      code: 'assistant.disabled',
      messageKey: 'errors.assistant.disabled',
      name: 'AssistantApiError',
      status: 403,
    });

    const store = useAssistantStore();
    await store.openAssistant();
    await expect(store.sendMessage('Warum?')).rejects.toBeTruthy();

    expect(store.error).toBe('errors.platform.internal');
    expect(store.draftInput).toBe('Warum?');
    expect(store.messages).toEqual([]);
  });

  it('clears conversation content without dropping loaded capabilities and can fully reset state', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
    });
    createAssistantConversation.mockResolvedValue({
      id: 'conversation-1',
      messages: [],
    });
    sendAssistantMessage.mockResolvedValue({
      conversation_id: 'conversation-1',
      message_id: 'message-1',
      answer: 'Ich habe Markus geprueft.',
      response_language: 'de',
      diagnosis: [],
      links: [],
      missing_permissions: [],
      next_steps: [],
    });

    const store = useAssistantStore();
    await store.openAssistant();
    await store.sendMessage('Warum?');

    store.clearConversation();
    expect(store.activeConversationId).toBeNull();
    expect(store.messages).toEqual([]);
    expect(store.draftInput).toBe('');
    expect(store.enabled).toBe(true);
    expect(store.canChat).toBe(true);

    store.resetAssistantState();
    expect(store.capabilities).toBeNull();
    expect(store.enabled).toBe(false);
    expect(store.canChat).toBe(false);
    expect(store.isOpen).toBe(false);
    expect(store.lastRouteContext).toBeNull();
    expect(sessionStorage.getItem('sicherplan.assistant.session')).toBeNull();
  });

  it('submits feedback for assistant messages and stores local submitted state', async () => {
    getAssistantCapabilities.mockResolvedValue({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
    });
    createAssistantConversation.mockResolvedValue({
      id: 'conversation-1',
      messages: [],
    });
    sendAssistantMessage.mockResolvedValue({
      conversation_id: 'conversation-1',
      message_id: 'message-1',
      answer: 'Ich habe Markus geprueft.',
      response_language: 'de',
      diagnosis: [],
      links: [],
      missing_permissions: [],
      next_steps: [],
    });
    submitAssistantFeedback.mockResolvedValue({
      id: 'feedback-1',
      conversation_id: 'conversation-1',
      message_id: 'message-1',
      rating: 'not_helpful',
      created_at: '2026-04-26T12:00:00Z',
    });

    const store = useAssistantStore();
    await store.openAssistant();
    await store.sendMessage('Warum sieht Markus die Schicht nicht?');
    await store.submitFeedback('message-1', 'not_helpful', 'Need more detail');

    expect(submitAssistantFeedback).toHaveBeenCalledWith('conversation-1', {
      message_id: 'message-1',
      rating: 'not_helpful',
      comment: 'Need more detail',
    });
    expect(store.messages[1]?.feedback).toMatchObject({
      rating: 'not_helpful',
      status: 'submitted',
      comment: 'Need more detail',
    });
  });
});
