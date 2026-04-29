// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { computed, defineComponent, nextTick, reactive, ref } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

function makeCachedRoute(key: string, route: any) {
  return {
    component: {
      type: {
        name: `Component-${key}`,
      },
    },
    key,
    route,
  };
}

describe('RouteCachedView scroll isolation', () => {
  let hasRouteCacheSessionState: (cacheKey: string) => boolean;
  let resetRouteCacheSessionState: () => void;
  let RouteCachedView: any;
  let mockedState: {
    cachedRoutesRef: ReturnType<typeof ref<Map<string, any>>>;
    excludeCachedTabsRef: ReturnType<typeof ref<string[]>>;
    removedRouteKeys: string[];
    routeState: any;
    tabsRef: ReturnType<typeof ref<any[]>>;
  };

  function setRoute(path: string, query: Record<string, unknown> = {}) {
    mockedState.routeState.fullPath = path;
    mockedState.routeState.meta = { domCached: true };
    mockedState.routeState.name = path;
    mockedState.routeState.path = path;
    mockedState.routeState.query = query;
  }

  beforeEach(async () => {
    vi.resetModules();
    document.body.innerHTML = '';

    mockedState = {
      cachedRoutesRef: ref(new Map<string, any>()),
      excludeCachedTabsRef: ref<string[]>([]),
      removedRouteKeys: [],
      routeState: reactive<any>({
        fullPath: '/admin/dashboard',
        meta: { domCached: true },
        name: 'Dashboard',
        path: '/admin/dashboard',
        query: {},
      }),
      tabsRef: ref<any[]>([]),
    };

    vi.doMock('vue-router', () => ({
      useRoute: () => mockedState.routeState,
    }));

    vi.doMock('@vben/preferences', () => ({
      preferences: {
        tabbar: {
          enable: true,
        },
      },
    }));

    vi.doMock('@vben/stores', () => ({
      getTabKey: (route: any) =>
        route?.query?.pageKey || route?.key || route?.path || route?.fullPath || '',
      storeToRefs: () => ({
        getCachedRoutes: computed(() => mockedState.cachedRoutesRef.value),
        getExcludeCachedTabs: computed(() => mockedState.excludeCachedTabsRef.value),
        getTabs: computed(() => mockedState.tabsRef.value),
      }),
      useTabbarStore: () => ({
        removeCachedRoute: (key: string) => {
          mockedState.removedRouteKeys.push(key);
          mockedState.cachedRoutesRef.value.delete(key);
        },
      }),
    }));

    vi.doMock('../hooks', () => ({
      useLayoutHook: () => ({
        getEnabledTransition: false,
        getTransitionName: () => 'fade',
      }),
    }));

    vi.doMock('./cached-route-renderer.vue', () => ({
      default: defineComponent({
        name: 'CachedRouteRendererStub',
        props: {
          route: {
            type: Object,
            required: true,
          },
        },
        template: '<div :data-route-key="route.query?.pageKey || route.path"></div>',
      }),
    }));

    const sessionModule = await import('./route-cache-session');
    hasRouteCacheSessionState = sessionModule.hasRouteCacheSessionState;
    resetRouteCacheSessionState = sessionModule.resetRouteCacheSessionState;
    RouteCachedView = (await import('./route-cached-view.vue')).default;

    Object.defineProperty(document, 'scrollingElement', {
      configurable: true,
      value: document.documentElement,
    });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;

    vi.spyOn(window, 'requestAnimationFrame').mockImplementation((callback: FrameRequestCallback) => {
      callback(0);
      return 1;
    });
    vi.spyOn(window, 'cancelAnimationFrame').mockImplementation(() => undefined);
  });

  afterEach(() => {
    resetRouteCacheSessionState();
    vi.restoreAllMocks();
  });

  it('restores per-tab scroll positions when switching between cached routes', async () => {
    mockedState.tabsRef.value = [
      { meta: { domCached: true }, path: '/admin/dashboard' },
      { meta: { domCached: true }, path: '/admin/employees', query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' } },
    ];
    mockedState.cachedRoutesRef.value = new Map([
      ['/admin/dashboard', makeCachedRoute('/admin/dashboard', { path: '/admin/dashboard', query: {} })],
      ['employees:detail:e1', makeCachedRoute('employees:detail:e1', { path: '/admin/employees', query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' } })],
    ]);

    mount(RouteCachedView);
    document.documentElement.scrollTop = 0;
    document.documentElement.dispatchEvent(new Event('scroll'));

    setRoute('/admin/employees', { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' });
    await nextTick();
    document.documentElement.scrollTop = 1000;
    document.documentElement.dispatchEvent(new Event('scroll'));

    setRoute('/admin/dashboard');
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(0);

    setRoute('/admin/employees', { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' });
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(1000);
  });

  it('keeps separate scroll positions for multiple employee detail pageKeys', async () => {
    mockedState.tabsRef.value = [
      { meta: { domCached: true }, path: '/admin/employees', query: { employee_id: 'markus', pageKey: 'employees:detail:markus', tab: 'overview' } },
      { meta: { domCached: true }, path: '/admin/employees', query: { employee_id: 'emir', pageKey: 'employees:detail:emir', tab: 'overview' } },
      { meta: { domCached: true }, path: '/admin/employees', query: { employee_id: 'sarah', pageKey: 'employees:detail:sarah', tab: 'overview' } },
    ];
    mockedState.cachedRoutesRef.value = new Map([
      ['employees:detail:markus', makeCachedRoute('employees:detail:markus', { path: '/admin/employees', query: { employee_id: 'markus', pageKey: 'employees:detail:markus', tab: 'overview' } })],
      ['employees:detail:emir', makeCachedRoute('employees:detail:emir', { path: '/admin/employees', query: { employee_id: 'emir', pageKey: 'employees:detail:emir', tab: 'overview' } })],
      ['employees:detail:sarah', makeCachedRoute('employees:detail:sarah', { path: '/admin/employees', query: { employee_id: 'sarah', pageKey: 'employees:detail:sarah', tab: 'overview' } })],
    ]);

    setRoute('/admin/employees', { employee_id: 'markus', pageKey: 'employees:detail:markus', tab: 'overview' });
    mount(RouteCachedView);
    document.documentElement.scrollTop = 150;
    document.documentElement.dispatchEvent(new Event('scroll'));

    setRoute('/admin/employees', { employee_id: 'emir', pageKey: 'employees:detail:emir', tab: 'overview' });
    await nextTick();
    document.documentElement.scrollTop = 480;
    document.documentElement.dispatchEvent(new Event('scroll'));

    setRoute('/admin/employees', { employee_id: 'sarah', pageKey: 'employees:detail:sarah', tab: 'overview' });
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(0);
    document.documentElement.scrollTop = 920;
    document.documentElement.dispatchEvent(new Event('scroll'));

    setRoute('/admin/employees', { employee_id: 'markus', pageKey: 'employees:detail:markus', tab: 'overview' });
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(150);

    setRoute('/admin/employees', { employee_id: 'emir', pageKey: 'employees:detail:emir', tab: 'overview' });
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(480);

    setRoute('/admin/employees', { employee_id: 'sarah', pageKey: 'employees:detail:sarah', tab: 'overview' });
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(920);
  });

  it('cleans up removed cached route keys without touching remaining entries', async () => {
    mockedState.tabsRef.value = [
      { meta: { domCached: true }, path: '/admin/dashboard' },
      { meta: { domCached: true }, path: '/admin/employees', query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' } },
      { meta: { domCached: true }, path: '/admin/employees', query: { employee_id: 'e2', pageKey: 'employees:detail:e2', tab: 'overview' } },
    ];
    mockedState.cachedRoutesRef.value = new Map([
      ['/admin/dashboard', makeCachedRoute('/admin/dashboard', { path: '/admin/dashboard', query: {} })],
      ['employees:detail:e1', makeCachedRoute('employees:detail:e1', { path: '/admin/employees', query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' } })],
      ['employees:detail:e2', makeCachedRoute('employees:detail:e2', { path: '/admin/employees', query: { employee_id: 'e2', pageKey: 'employees:detail:e2', tab: 'overview' } })],
    ]);

    mount(RouteCachedView);
    document.documentElement.scrollTop = 250;
    document.documentElement.dispatchEvent(new Event('scroll'));

    setRoute('/admin/employees', { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' });
    await nextTick();
    document.documentElement.scrollTop = 700;
    document.documentElement.dispatchEvent(new Event('scroll'));
    setRoute('/admin/employees', { employee_id: 'e2', pageKey: 'employees:detail:e2', tab: 'overview' });
    await nextTick();
    document.documentElement.scrollTop = 920;
    document.documentElement.dispatchEvent(new Event('scroll'));

    expect(hasRouteCacheSessionState('employees:detail:e1')).toBe(true);
    expect(hasRouteCacheSessionState('employees:detail:e2')).toBe(true);

    mockedState.tabsRef.value = [
      { meta: { domCached: true }, path: '/admin/dashboard' },
      { meta: { domCached: true }, path: '/admin/employees', query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' } },
    ];
    await nextTick();

    expect(hasRouteCacheSessionState('employees:detail:e2')).toBe(false);
    expect(hasRouteCacheSessionState('employees:detail:e1')).toBe(true);

    setRoute('/admin/dashboard');
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(250);

    setRoute('/admin/employees', { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' });
    await nextTick();
    expect(document.documentElement.scrollTop).toBe(700);
  });
});
