// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { nextTick, reactive } from 'vue';

import {
  ASSISTANT_FLOATING_HINT_STORAGE_KEY,
  ASSISTANT_FLOATING_POSITION_STORAGE_KEY,
} from '../assistant-floating';

import type { AssistantUiMessage } from '#/store';

const mocked = vi.hoisted(() => ({
  accessStoreState: null as null | { accessToken: string },
  currentRoute: {
    value: {
      fullPath: '/admin/customers',
      meta: {},
      path: '/admin/customers',
      query: {},
    },
  },
  legacyAuthStoreState: null as null | {
    effectiveAccessToken: string;
    ensureSessionReady: ReturnType<typeof vi.fn>;
    isSessionResolving: boolean;
    sessionId: string;
    sessionUser: null | { id: string };
    syncFromPrimarySession: ReturnType<typeof vi.fn>;
  },
  pushMock: vi.fn(),
  storeState: null as null | {
    capabilities?: null | Record<string, unknown>;
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
    submitFeedback: ReturnType<typeof vi.fn>;
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

vi.mock('#/sicherplan-legacy/stores/auth', () => ({
  useAuthStore: () => mocked.legacyAuthStoreState,
}));

import SicherPlanAssistantWidget from '../SicherPlanAssistantWidget.vue';

async function flushUi() {
  await Promise.resolve();
  await nextTick();
  await Promise.resolve();
  await nextTick();
}

function mountWidget() {
  return mount(SicherPlanAssistantWidget, {
    attachTo: document.body,
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

describe('SicherPlanAssistantWidget floating position', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    window.localStorage.setItem(ASSISTANT_FLOATING_HINT_STORAGE_KEY, '1');
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      value: 1280,
      writable: true,
    });
    Object.defineProperty(window, 'innerHeight', {
      configurable: true,
      value: 720,
      writable: true,
    });

    mocked.accessStoreState = reactive({
      accessToken: 'access-1',
    });
    mocked.legacyAuthStoreState = reactive({
      effectiveAccessToken: 'access-1',
      ensureSessionReady: vi.fn(async () => ({ id: 'user-1' })),
      isSessionResolving: false,
      sessionId: 'session-1',
      sessionUser: { id: 'user-1' },
      syncFromPrimarySession: vi.fn(),
    });
    mocked.storeState = reactive({
      capabilities: {
        provider_mode: 'openai',
      },
      canChat: true,
      captureCurrentRouteContext: vi.fn(),
      closeAssistant: vi.fn(() => {
        mocked.storeState!.isOpen = false;
      }),
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
      setDraftInput: vi.fn(),
      submitFeedback: vi.fn(async () => undefined),
    });
  });

  it('defaults to bottom-right docking', async () => {
    const wrapper = mountWidget();
    await flushUi();

    expect(wrapper.get('[data-testid="assistant-widget"]').attributes('data-dock-side')).toBe('bottom-right');
  });

  it('persists dragged position and does not toggle the panel', async () => {
    const wrapper = mountWidget();
    await flushUi();

    const launcher = wrapper.get('button');
    await launcher.trigger('pointerdown', { pointerId: 1, clientX: 1200, clientY: 650 });
    await launcher.trigger('pointermove', { pointerId: 1, clientX: 120, clientY: 140 });
    await launcher.trigger('pointerup', { pointerId: 1, clientX: 120, clientY: 140 });
    await launcher.trigger('click');
    await flushUi();

    const stored = JSON.parse(window.localStorage.getItem(ASSISTANT_FLOATING_POSITION_STORAGE_KEY) || '{}');
    expect(stored.dockSide).toBe('top-left');
    expect(mocked.storeState!.openAssistant).not.toHaveBeenCalled();
  });

  it('restores persisted position after remount and aligns the panel on the left side', async () => {
    window.localStorage.setItem(
      ASSISTANT_FLOATING_POSITION_STORAGE_KEY,
      JSON.stringify({
        x: 12,
        y: 120,
        dockSide: 'bottom-left',
        userPinned: true,
        lastMovedBy: 'user',
        updatedAt: '2026-05-02T12:00:00.000Z',
      }),
    );
    mocked.storeState!.isOpen = true;

    const wrapper = mountWidget();
    await flushUi();

    expect(wrapper.get('[data-testid="assistant-widget"]').attributes('data-dock-side')).toBe('bottom-left');
    expect(wrapper.get('[data-testid="assistant-panel-shell"]').classes()).toContain('sp-assistant-widget__panel-shell--left');
  });

  it('clamps invalid persisted positions back into the viewport', async () => {
    window.localStorage.setItem(
      ASSISTANT_FLOATING_POSITION_STORAGE_KEY,
      JSON.stringify({
        x: 5000,
        y: 5000,
        dockSide: 'bottom-right',
        userPinned: true,
        lastMovedBy: 'user',
        updatedAt: '2026-05-02T12:00:00.000Z',
      }),
    );

    const wrapper = mountWidget();
    await flushUi();

    const style = wrapper.get('[data-testid="assistant-widget"]').attributes('style');
    expect(style).toContain('left:');
    expect(style).not.toContain('5000px');
  });

  it('moves with keyboard arrows and persists the updated position', async () => {
    const wrapper = mountWidget();
    await flushUi();

    await wrapper.get('button').trigger('keydown', { key: 'ArrowLeft' });
    await flushUi();

    const stored = JSON.parse(window.localStorage.getItem(ASSISTANT_FLOATING_POSITION_STORAGE_KEY) || '{}');
    expect(stored.lastMovedBy).toBe('user');
    expect(stored.x).toBeGreaterThanOrEqual(12);
  });

  it('resets position from the panel header control', async () => {
    window.localStorage.setItem(
      ASSISTANT_FLOATING_POSITION_STORAGE_KEY,
      JSON.stringify({
        x: 12,
        y: 120,
        dockSide: 'top-left',
        userPinned: true,
        lastMovedBy: 'user',
        updatedAt: '2026-05-02T12:00:00.000Z',
      }),
    );
    mocked.storeState!.isOpen = true;

    const wrapper = mountWidget();
    await flushUi();

    await wrapper.get('[data-testid="assistant-reset-position"]').trigger('click');
    await flushUi();

    const stored = JSON.parse(window.localStorage.getItem(ASSISTANT_FLOATING_POSITION_STORAGE_KEY) || '{}');
    expect(stored.dockSide).toBe('bottom-right');
    expect(stored.lastMovedBy).toBe('system');
  });
});
