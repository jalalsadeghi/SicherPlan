// @vitest-environment happy-dom

import { beforeEach, describe, expect, it, vi } from 'vitest';

const { accessStoreState } = vi.hoisted(() => ({
  accessStoreState: {
    accessToken: 'access-1',
  },
}));

vi.mock('@vben/stores', () => ({
  useAccessStore: () => accessStoreState,
}));

import {
  AssistantApiError,
  createAssistantConversation,
  getAssistantCapabilities,
  getAssistantConversation,
  getAssistantPageHelp,
  getAssistantProviderStatus,
  normalizeAssistantApiError,
  sendAssistantMessage,
  submitAssistantFeedback,
} from './assistant';

describe('assistant api client', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    accessStoreState.accessToken = 'access-1';
  });

  it('loads capabilities with auth and language headers', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          enabled: true,
          can_chat: true,
          provider_mode: 'mock',
          mock_provider_allowed: true,
          openai_configured: false,
          rag_enabled: false,
          supported_features: ['structured_responses'],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(getAssistantCapabilities()).resolves.toMatchObject({
      enabled: true,
      can_chat: true,
      provider_mode: 'mock',
      mock_provider_allowed: true,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/assistant/capabilities'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer access-1',
          'Accept-Language': 'de-DE',
        }),
      }),
    );
  });

  it('loads provider status without exposing secrets client-side', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          provider_mode: 'openai',
          openai_configured: true,
          model: 'gpt-5.5-mini',
          mock_provider_allowed: false,
          store_responses: false,
          rag_enabled: true,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(getAssistantProviderStatus()).resolves.toMatchObject({
      provider_mode: 'openai',
      openai_configured: true,
      rag_enabled: true,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/assistant/provider/status'),
      expect.objectContaining({
        method: 'GET',
      }),
    );
  });

  it('creates conversations and sends structured message payloads without remapping snake_case', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: 'conversation-1',
            locale: 'de-DE',
            messages: [],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            conversation_id: 'conversation-1',
            message_id: 'message-1',
            answer: 'Ich habe Markus geprueft.',
            response_language: 'de',
            diagnosis: [],
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      );

    await expect(
      createAssistantConversation({
        initial_route: {
          path: '/admin/planning-staffing',
          route_name: 'SicherPlanPlanningStaffing',
          page_id: 'P-04',
        },
        locale: 'de-DE',
      }),
    ).resolves.toMatchObject({
      id: 'conversation-1',
      locale: 'de-DE',
    });

    await expect(
      sendAssistantMessage('conversation-1', {
        message: 'Warum sieht Markus die Schicht nicht?',
        route_context: {
          path: '/admin/planning-staffing',
          route_name: 'SicherPlanPlanningStaffing',
          page_id: 'P-04',
        },
        client_context: {
          ui_locale: 'de-DE',
        },
      }),
    ).resolves.toMatchObject({
      conversation_id: 'conversation-1',
      message_id: 'message-1',
      answer: 'Ich habe Markus geprueft.',
    });

    const [, sendRequest] = fetchMock.mock.calls[1] ?? [];
    expect(sendRequest).toMatchObject({
      method: 'POST',
      headers: expect.objectContaining({
        Authorization: 'Bearer access-1',
      }),
    });
    expect(JSON.parse(String(sendRequest?.body))).toEqual({
      client_context: {
        ui_locale: 'de-DE',
      },
      message: 'Warum sieht Markus die Schicht nicht?',
      route_context: {
        page_id: 'P-04',
        path: '/admin/planning-staffing',
        route_name: 'SicherPlanPlanningStaffing',
      },
    });
    for (const [url] of fetchMock.mock.calls) {
      expect(String(url)).toContain('/api/assistant/');
      expect(String(url)).not.toContain('openai');
    }
  });

  it('loads an existing conversation', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 'conversation-1',
          messages: [
            {
              id: 'message-1',
              role: 'assistant',
              content: 'Antwort',
            },
          ],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(getAssistantConversation('conversation-1')).resolves.toMatchObject({
      id: 'conversation-1',
      messages: [{ id: 'message-1', role: 'assistant', content: 'Antwort' }],
    });
  });

  it('submits assistant feedback without remapping snake_case fields', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 'feedback-1',
          conversation_id: 'conversation-1',
          message_id: 'message-1',
          rating: 'not_helpful',
          created_at: '2026-04-26T12:00:00Z',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(
      submitAssistantFeedback('conversation-1', {
        message_id: 'message-1',
        rating: 'not_helpful',
        comment: 'Need more detail',
      }),
    ).resolves.toMatchObject({
      id: 'feedback-1',
      conversation_id: 'conversation-1',
      message_id: 'message-1',
      rating: 'not_helpful',
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/assistant/conversations/conversation-1/feedback'),
      expect.objectContaining({
        method: 'POST',
      }),
    );
  });

  it('loads page help with language query preserved', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          page_id: 'E-01',
          page_title: 'Employees Workspace',
          module_key: 'employees',
          source_status: 'verified',
          page_purpose: 'Manage employees and operational readiness.',
          workflow_keys: ['employee_create'],
          api_families: ['employees'],
          source_basis: [{ source_type: 'page_help_manifest', evidence: 'Verified in source' }],
          actions: [{ action_key: 'employees.create.open', label: 'Create employee file', label_status: 'verified' }],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(getAssistantPageHelp('E-01', 'fa')).resolves.toMatchObject({
      page_id: 'E-01',
      source_status: 'verified',
      workflow_keys: ['employee_create'],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/assistant/page-help/E-01?language_code=fa'),
      expect.objectContaining({
        method: 'GET',
      }),
    );
  });

  it('normalizes backend and network errors', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: 'assistant.disabled',
            message_key: 'errors.assistant.disabled',
          },
        }),
        { status: 403, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    await expect(getAssistantCapabilities()).rejects.toBeInstanceOf(AssistantApiError);

    expect(
      normalizeAssistantApiError(
        new AssistantApiError(403, 'assistant.disabled', 'errors.assistant.disabled'),
      ),
    ).toEqual({
      code: 'assistant.disabled',
      messageKey: 'errors.assistant.disabled',
      status: 403,
    });

    expect(normalizeAssistantApiError(new TypeError('fetch failed'))).toEqual({
      code: 'platform.network_unavailable',
      messageKey: 'errors.platform.network_unavailable',
      status: 0,
    });
  });
});
