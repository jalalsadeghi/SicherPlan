// @vitest-environment happy-dom

import type { MenuRecordRaw } from '@vben/types';

import { mount } from '@vue/test-utils';
import { defineComponent, nextTick } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const navigationMock = vi.fn();
const willOpenedByWindowMock = vi.fn(() => false);
const routeState = {
  meta: {} as Record<string, unknown>,
  path: '/admin/customers',
};

const workforceMenu: MenuRecordRaw = {
  children: [
    {
      name: 'Recruiting',
      parent: '/admin/workforce',
      parents: ['/admin/workforce'],
      path: '/admin/recruiting',
    },
    {
      name: 'Employees',
      parent: '/admin/workforce',
      parents: ['/admin/workforce'],
      path: '/admin/employees',
    },
  ],
  menuContainer: true,
  name: 'Workforce & Partners',
  path: '/admin/workforce',
};

const administrationMenu: MenuRecordRaw = {
  children: [
    {
      name: 'Core',
      parent: '/admin/administration',
      parents: ['/admin/administration'],
      path: '/admin/core',
    },
  ],
  menuContainer: true,
  name: 'Administration',
  path: '/admin/administration',
};

const standaloneMenu: MenuRecordRaw = {
  name: 'Customers',
  path: '/admin/customers',
};

const accessStore = {
  accessMenus: [standaloneMenu, administrationMenu, workforceMenu] as MenuRecordRaw[],
};

vi.mock('vue-router', () => ({
  useRoute: () => routeState,
}));

vi.mock('@vben/preferences', () => ({
  preferences: {
    navigation: {
      split: true,
    },
    sidebar: {
      autoActivateChild: true,
      enable: true,
    },
  },
  usePreferences: () => ({
    isHeaderMixedNav: { value: true },
    isMixedNav: { value: false },
  }),
}));

vi.mock('@vben/stores', () => ({
  useAccessStore: () => accessStore,
}));

vi.mock('./use-navigation', () => ({
  useNavigation: () => ({
    navigation: navigationMock,
    willOpenedByWindow: willOpenedByWindowMock,
  }),
}));

async function mountMixedMenuHarness() {
  let exposed!: ReturnType<typeof import('./use-mixed-menu').useMixedMenu>;
  const { useMixedMenu } = await import('./use-mixed-menu');
  const wrapper = mount(
    defineComponent({
      setup() {
        exposed = useMixedMenu();
        return () => null;
      },
    }),
  );

  await nextTick();
  return { exposed, wrapper };
}

describe('useMixedMenu parent-group navigation', () => {
  beforeEach(() => {
    navigationMock.mockClear();
    willOpenedByWindowMock.mockClear();
    routeState.path = '/admin/customers';
    routeState.meta = {};
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('does not navigate when opening or closing a menu container parent group', async () => {
    const { exposed, wrapper } = await mountMixedMenuHarness();
    navigationMock.mockClear();

    exposed.handleMenuOpen('/admin/workforce', ['/admin/workforce']);
    exposed.handleMenuOpen('/admin/workforce', ['/admin/workforce']);

    expect(navigationMock).not.toHaveBeenCalled();
    expect(exposed.sidebarActive.value).toBe('/admin/customers');

    wrapper.unmount();
  });

  it('does not auto-activate the first child when selecting a split-nav container parent', async () => {
    const { exposed, wrapper } = await mountMixedMenuHarness();
    navigationMock.mockClear();

    exposed.handleMenuSelect('/admin/workforce');

    expect(exposed.sidebarMenus.value).toEqual(workforceMenu.children);
    expect(navigationMock).not.toHaveBeenCalledWith('/admin/recruiting');
    expect(navigationMock).not.toHaveBeenCalled();

    wrapper.unmount();
  });

  it('keeps child navigation working after expanding the parent group', async () => {
    const { exposed, wrapper } = await mountMixedMenuHarness();
    navigationMock.mockClear();

    exposed.handleMenuOpen('/admin/workforce', ['/admin/workforce']);
    exposed.handleMenuSelect('/admin/employees', 'vertical');

    expect(navigationMock).toHaveBeenCalledTimes(1);
    expect(navigationMock).toHaveBeenCalledWith('/admin/employees');

    wrapper.unmount();
  });

  it('keeps direct child routes active without redirecting to the first child', async () => {
    routeState.path = '/admin/employees';
    const { exposed, wrapper } = await mountMixedMenuHarness();
    navigationMock.mockClear();

    expect(exposed.sidebarActive.value).toBe('/admin/employees');
    expect(exposed.sidebarMenus.value).toEqual(workforceMenu.children);

    exposed.handleMenuOpen('/admin/workforce', ['/admin/workforce']);
    expect(navigationMock).not.toHaveBeenCalled();
    expect(navigationMock).not.toHaveBeenCalledWith('/admin/recruiting');

    wrapper.unmount();
  });

  it('applies the same no-auto-navigation rule to other grouped parents', async () => {
    const { exposed, wrapper } = await mountMixedMenuHarness();
    navigationMock.mockClear();

    exposed.handleMenuOpen('/admin/administration', ['/admin/administration']);

    expect(navigationMock).not.toHaveBeenCalled();

    wrapper.unmount();
  });
});
