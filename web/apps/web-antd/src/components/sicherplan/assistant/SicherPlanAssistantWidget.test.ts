// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { nextTick, reactive, ref } from 'vue';

import type { AssistantUiMessage } from '#/store';

const mocked = vi.hoisted(() => ({
  accessStoreState: null as null | { accessToken: string },
  currentRoute: {
    value: {
      fullPath: '/admin/employees',
      meta: {},
      path: '/admin/employees',
      query: {},
    },
  },
  pushMock: vi.fn(),
  storeState: null as null | {
    canChat: boolean;
    captureCurrentRouteContext: ReturnType<typeof vi.fn>;
    closeAssistant: ReturnType<typeof vi.fn>;
    draftInput: string;
    enabled: boolean;
    error: null | string;
    isOpen: boolean;
    loadCapabilities: ReturnType<typeof vi.fn>;
    loadingCapabilities: boolean;
    loadingConversation: boolean;
    messages: AssistantUiMessage[];
    openAssistant: ReturnType<typeof vi.fn>;
    restorePersistedConversation: ReturnType<typeof vi.fn>;
    sendingMessage: boolean;
    sendMessage: ReturnType<typeof vi.fn>;
    setDraftInput: ReturnType<typeof vi.fn>;
  },
}));

vi.mock('@vben/constants', () => ({
  LOGIN_PATH: '/auth/login',
}));

vi.mock('@vben/stores', () => ({
  useAccessStore: () => mocked.accessStoreState,
}));

vi.mock('#/locales', () => ({
  $t: (key: string) => key,
}));

vi.mock('#/router', () => ({
  router: {
    currentRoute: mocked.currentRoute,
    push: mocked.pushMock,
  },
}));

vi.mock('#/store', () => ({
  useAssistantStore: () => mocked.storeState,
}));

import SicherPlanAssistantWidget from './SicherPlanAssistantWidget.vue';

async function flushUi() {
  await Promise.resolve();
  await nextTick();
}

function mountWidget() {
  return mount(SicherPlanAssistantWidget, {
    global: {
      stubs: {
        IconifyIcon: {
          template: '<span class="icon-stub" />',
        },
        Transition: {
          template: '<slot />',
        },
      },
    },
  });
}

describe('SicherPlanAssistantWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mocked.accessStoreState = reactive({
      accessToken: 'access-1',
    });

    mocked.currentRoute.value = {
      fullPath: '/admin/employees',
      meta: {},
      path: '/admin/employees',
      query: {},
    };

    mocked.storeState = reactive({
      canChat: true,
      captureCurrentRouteContext: vi.fn(),
      closeAssistant: vi.fn(),
      draftInput: '',
      enabled: true,
      error: null as null | string,
      isOpen: false,
      loadCapabilities: vi.fn(async () => undefined),
      loadingCapabilities: false,
      loadingConversation: false,
      messages: [] as AssistantUiMessage[],
      openAssistant: vi.fn(async () => {
        mocked.storeState!.isOpen = true;
        return true;
      }),
      restorePersistedConversation: vi.fn(async () => undefined),
      sendingMessage: false,
      sendMessage: vi.fn(async () => undefined),
      setDraftInput: vi.fn((value: string) => {
        mocked.storeState!.draftInput = value;
      }),
    });
  });

  it('hides the widget on public routes and when unauthenticated', async () => {
    mocked.currentRoute.value = {
      fullPath: '/auth/login',
      meta: { ignoreAccess: true },
      path: '/auth/login',
      query: {},
    };

    const publicWrapper = mountWidget();
    await flushUi();

    expect(publicWrapper.find('[data-testid="assistant-widget"]').exists()).toBe(false);
    expect(mocked.storeState!.loadCapabilities).not.toHaveBeenCalled();

    mocked.accessStoreState!.accessToken = '';
    mocked.currentRoute.value = {
      fullPath: '/admin/employees',
      meta: {},
      path: '/admin/employees',
      query: {},
    };

    const unauthenticatedWrapper = mountWidget();
    await flushUi();

    expect(unauthenticatedWrapper.find('[data-testid="assistant-widget"]').exists()).toBe(false);
  });

  it('shows the launcher for authenticated users with assistant chat capability', async () => {
    const wrapper = mountWidget();
    await flushUi();

    expect(mocked.storeState!.loadCapabilities).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="assistant-widget"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('assistant.widget.launcherLabel');
    expect(wrapper.find('button[aria-label="assistant.widget.launcherLabel"]').exists()).toBe(true);
  });

  it('hides the launcher when assistant is disabled or chat is not allowed', async () => {
    mocked.storeState!.enabled = false;
    mocked.storeState!.canChat = false;
    mocked.storeState!.loadingCapabilities = false;

    const disabledWrapper = mountWidget();
    await flushUi();

    expect(disabledWrapper.find('[data-testid="assistant-widget"]').exists()).toBe(false);

    mocked.storeState!.enabled = true;
    mocked.storeState!.canChat = false;

    const noChatWrapper = mountWidget();
    await flushUi();

    expect(noChatWrapper.find('[data-testid="assistant-widget"]').exists()).toBe(false);
  });

  it('opens the panel from the launcher and restores the persisted conversation', async () => {
    const wrapper = mountWidget();
    await flushUi();

    await wrapper.find('button').trigger('click');
    await flushUi();

    expect(mocked.storeState!.openAssistant).toHaveBeenCalled();
    expect(mocked.storeState!.restorePersistedConversation).toHaveBeenCalled();
    expect(wrapper.find('[data-testid="assistant-panel"]').exists()).toBe(true);
  });

  it('closes the panel without clearing existing messages', async () => {
    mocked.storeState!.isOpen = true;
    mocked.storeState!.messages = [
      {
        id: 'assistant-1',
        role: 'assistant',
        content: 'Antwort',
      },
    ];
    mocked.storeState!.closeAssistant.mockImplementation(() => {
      mocked.storeState!.isOpen = false;
    });

    const wrapper = mountWidget();
    await flushUi();

    await wrapper.find('.sp-assistant-panel__close').trigger('click');
    await flushUi();

    expect(mocked.storeState!.closeAssistant).toHaveBeenCalled();
    expect(mocked.storeState!.messages).toHaveLength(1);
    expect(wrapper.find('[data-testid="assistant-panel"]').exists()).toBe(false);
  });

  it('renders structured assistant sections and routes safe links through the router', async () => {
    mocked.storeState!.isOpen = true;
    mocked.storeState!.messages = [
      {
        id: 'assistant-1',
        role: 'assistant',
        content: 'Ich habe Markus geprueft.',
        structured_response: {
          answer: 'Ich habe Markus geprueft.',
          confidence: 'high',
          conversation_id: 'conversation-1',
          detected_language: 'de',
          diagnosis: [
            {
              evidence: 'Freigabe fehlt',
              finding: 'Die Schicht ist noch nicht freigegeben.',
              severity: 'blocking',
            },
          ],
          links: [
            {
              label: 'Zur Schicht',
              path: '/admin/planning-shifts?shift_id=shift-1',
              reason: 'Freigabestatus pruefen',
            },
          ],
          message_id: 'assistant-1',
          missing_permissions: [
            {
              permission: 'planning.staffing.read',
              reason: 'Validierungen konnten nicht geladen werden.',
            },
          ],
          next_steps: ['Schicht freigeben'],
          response_language: 'de',
        },
      },
    ];

    const wrapper = mountWidget();
    await flushUi();

    expect(wrapper.text()).toContain('assistant.widget.diagnosisTitle');
    expect(wrapper.text()).toContain('Die Schicht ist noch nicht freigegeben.');
    expect(wrapper.text()).toContain('assistant.widget.missingPermissionsTitle');
    expect(wrapper.text()).toContain('planning.staffing.read');
    expect(wrapper.text()).toContain('assistant.widget.nextStepsTitle');
    expect(wrapper.text()).toContain('Schicht freigeben');
    expect(wrapper.text()).toContain('assistant.widget.linksTitle');

    const linkButton = wrapper.find('.sp-assistant-link-card__action');
    await linkButton.trigger('click');

    expect(mocked.pushMock).toHaveBeenCalledWith('/admin/planning-shifts?shift_id=shift-1');
  });

  it('captures route context before sending a message and restores draft updates through the store', async () => {
    mocked.storeState!.isOpen = true;
    mocked.storeState!.draftInput = 'Warum sieht Markus die Schicht nicht?';

    const callOrder: string[] = [];
    mocked.storeState!.captureCurrentRouteContext.mockImplementation(() => {
      callOrder.push('capture');
    });
    mocked.storeState!.sendMessage.mockImplementation(async (message: string) => {
      callOrder.push(`send:${message}`);
    });

    const wrapper = mountWidget();
    await flushUi();

    const textarea = wrapper.find('textarea');
    await textarea.setValue('Bitte Markus pruefen');

    expect(mocked.storeState!.setDraftInput).toHaveBeenCalledWith('Bitte Markus pruefen');

    await wrapper.find('form').trigger('submit');
    await flushUi();

    expect(callOrder).toEqual(['capture', 'send:Bitte Markus pruefen']);
  });

  it('keeps the panel open across route changes and refreshes route context', async () => {
    mocked.storeState!.isOpen = true;
    mocked.storeState!.messages = [
      {
        id: 'assistant-1',
        role: 'assistant',
        content: 'Antwort',
      },
    ];

    const wrapper = mountWidget();
    await flushUi();

    mocked.currentRoute.value = {
      fullPath: '/admin/planning-shifts?shift_id=shift-1',
      meta: {},
      path: '/admin/planning-shifts',
      query: { shift_id: 'shift-1' },
    };
    await flushUi();

    expect(wrapper.find('[data-testid="assistant-panel"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('Antwort');
  });
});
