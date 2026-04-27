// @vitest-environment happy-dom

import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const {
  createAssistantConversation,
  routerCurrentRoute,
  sendAssistantMessage,
} = vi.hoisted(() => ({
  createAssistantConversation: vi.fn(),
  routerCurrentRoute: {
    value: {
      name: 'SicherPlanPlanningStaffing',
      path: '/admin/planning-staffing',
      query: { assignment_id: 'assignment-1' },
      meta: {
        title: 'Staffing Board & Coverage',
      },
    } as any,
  },
  sendAssistantMessage: vi.fn(),
}));

vi.mock('#/api/sicherplan/assistant', async () => {
  const actual = await vi.importActual<typeof import('#/api/sicherplan/assistant')>('#/api/sicherplan/assistant');
  return {
    ...actual,
    createAssistantConversation,
    getAssistantCapabilities: vi.fn(),
    getAssistantConversation: vi.fn(),
    sendAssistantMessage,
    submitAssistantFeedback: vi.fn(),
  };
});

vi.mock('#/router', () => ({
  router: {
    currentRoute: routerCurrentRoute,
  },
}));

import { useAssistantStore } from '../assistant';

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('assistant send flow', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it('adds the user message and pending assistant indicator before conversation creation finishes', async () => {
    const conversationDeferred = deferred<{ id: string; messages: never[] }>();
    const responseDeferred = deferred<{
      answer: string;
      conversation_id: string;
      message_id: string;
    }>();

    createAssistantConversation.mockReturnValue(conversationDeferred.promise);
    sendAssistantMessage.mockReturnValue(responseDeferred.promise);

    const store = useAssistantStore();
    const sendPromise = store.sendMessage('Warum sieht Markus die Schicht nicht?');

    expect(store.sendingMessage).toBe(true);
    expect(store.messages).toHaveLength(2);
    expect(store.messages[0]).toMatchObject({
      role: 'user',
      content: 'Warum sieht Markus die Schicht nicht?',
    });
    expect(store.messages[1]).toMatchObject({
      role: 'assistant',
      pending: true,
    });
    expect(store.draftInput).toBe('');
    expect(sendAssistantMessage).not.toHaveBeenCalled();

    conversationDeferred.resolve({ id: 'conversation-1', messages: [] });
    await Promise.resolve();
    await Promise.resolve();

    expect(sendAssistantMessage).toHaveBeenCalledWith(
      'conversation-1',
      expect.objectContaining({
        message: 'Warum sieht Markus die Schicht nicht?',
      }),
    );

    responseDeferred.resolve({
      conversation_id: 'conversation-1',
      message_id: 'assistant-1',
      answer: 'Ich habe die Freigabe geprüft.',
    });

    await sendPromise;

    expect(store.sendingMessage).toBe(false);
    expect(store.messages).toHaveLength(2);
    expect(store.messages[0]?.role).toBe('user');
    expect(store.messages[1]).toMatchObject({
      id: 'assistant-1',
      role: 'assistant',
      content: 'Ich habe die Freigabe geprüft.',
    });
    expect(store.messages[1]?.pending).not.toBe(true);
  });

  it('removes the pending indicator, restores the draft, and does not persist the local pending row on failure', async () => {
    createAssistantConversation.mockResolvedValue({
      id: 'conversation-1',
      messages: [],
    });
    sendAssistantMessage.mockRejectedValue(new Error('network failed'));

    const store = useAssistantStore();

    await expect(store.sendMessage('Bitte Markus prüfen')).rejects.toThrow('network failed');

    expect(store.sendingMessage).toBe(false);
    expect(store.messages).toEqual([]);
    expect(store.draftInput).toBe('Bitte Markus prüfen');
    expect(JSON.parse(sessionStorage.getItem('sicherplan.assistant.session') ?? '{}')).not.toHaveProperty('messages');
  });
});
