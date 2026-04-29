import { createRouter, createWebHistory } from 'vue-router';

import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useTabbarStore } from './tabbar';

describe('useAccessStore', () => {
  const router = createRouter({
    history: createWebHistory(),
    routes: [],
  });
  router.push = vi.fn();
  router.replace = vi.fn();
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('adds a new tab', () => {
    const store = useTabbarStore();
    const tab: any = {
      fullPath: '/home',
      meta: {},
      key: '/home',
      name: 'Home',
      path: '/home',
    };
    const addNewTab = store.addTab(tab);
    expect(store.tabs.length).toBe(1);
    expect(store.tabs[0]).toEqual(addNewTab);
  });

  it('adds a new tab if it does not exist', () => {
    const store = useTabbarStore();
    const newTab: any = {
      fullPath: '/new',
      meta: {},
      name: 'New',
      path: '/new',
    };
    const addNewTab = store.addTab(newTab);
    expect(store.tabs).toContainEqual(addNewTab);
  });

  it('updates an existing tab instead of adding a new one', () => {
    const store = useTabbarStore();
    const initialTab: any = {
      fullPath: '/existing',
      meta: {
        fullPathKey: false,
      },
      name: 'Existing',
      path: '/existing',
      query: {},
    };
    store.addTab(initialTab);
    const updatedTab = { ...initialTab, query: { id: '1' } };
    store.addTab(updatedTab);
    expect(store.tabs.length).toBe(1);
    expect(store.tabs[0]?.query).toEqual({ id: '1' });
  });

  it('uses one Customer Order Workspace tab when only wizard query params change', () => {
    const store = useTabbarStore();
    const baseTab = {
      meta: {
        fullPathKey: false,
        title: 'Order workspace',
      },
      name: 'SicherPlanCustomerOrderWorkspace',
      path: '/admin/customers/order-workspace',
    };

    store.addTab({
      ...baseTab,
      fullPath: '/admin/customers/order-workspace?customer_id=c1&step=order-details',
      query: { customer_id: 'c1', step: 'order-details' },
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/customers/order-workspace?customer_id=c1&step=order-scope-documents&order_id=o1',
      query: { customer_id: 'c1', order_id: 'o1', step: 'order-scope-documents' },
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/customers/order-workspace?customer_id=c1&step=planning-record-overview&order_id=o1',
      query: { customer_id: 'c1', order_id: 'o1', step: 'planning-record-overview' },
    } as any);

    expect(store.tabs).toHaveLength(1);
    expect(store.tabs[0]?.key).toBe('/admin/customers/order-workspace');
    expect(store.tabs[0]?.name).toBe('SicherPlanCustomerOrderWorkspace');
    expect(store.tabs[0]?.meta?.title).toBe('Order workspace');
    expect(store.tabs[0]?.query).toEqual({
      customer_id: 'c1',
      order_id: 'o1',
      step: 'planning-record-overview',
    });
  });

  it('uses pageKey to keep a list tab and separate customer detail tabs under the same Customers route', () => {
    const store = useTabbarStore();
    const baseTab = {
      meta: {
        fullPathKey: false,
      },
      name: 'SicherPlanCustomers',
      path: '/admin/customers',
    };

    store.addTab({
      ...baseTab,
      fullPath: '/admin/customers',
      meta: {
        ...baseTab.meta,
        title: 'Customers',
      },
      query: {},
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/customers?customer_id=c1&tab=dashboard&pageKey=customers:detail:c1',
      meta: {
        ...baseTab.meta,
        title: 'Alpha Security',
      },
      query: { customer_id: 'c1', pageKey: 'customers:detail:c1', tab: 'dashboard' },
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/customers?customer_id=c2&tab=dashboard&pageKey=customers:detail:c2',
      meta: {
        ...baseTab.meta,
        title: 'RheinForum Koln',
      },
      query: { customer_id: 'c2', pageKey: 'customers:detail:c2', tab: 'dashboard' },
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/customers?customer_id=c1&tab=orders&pageKey=customers:detail:c1',
      meta: {
        ...baseTab.meta,
        title: 'Alpha Security',
      },
      query: { customer_id: 'c1', pageKey: 'customers:detail:c1', tab: 'orders' },
    } as any);

    expect(store.tabs).toHaveLength(3);
    expect(store.tabs.map((tab) => tab.key)).toEqual([
      '/admin/customers',
      'customers:detail:c1',
      'customers:detail:c2',
    ]);
    expect(store.tabs[0]?.meta?.title).toBe('Customers');
    expect(store.tabs[1]?.meta?.title).toBe('Alpha Security');
    expect(store.tabs[1]?.query).toEqual({
      customer_id: 'c1',
      pageKey: 'customers:detail:c1',
      tab: 'orders',
    });
    expect(store.tabs[2]?.meta?.title).toBe('RheinForum Koln');
  });

  it('uses pageKey to keep a list tab and separate employee detail tabs under the same Employees route', () => {
    const store = useTabbarStore();
    const baseTab = {
      meta: {
        title: 'Employees',
      },
      name: 'SicherPlanEmployees',
      path: '/admin/employees',
    };

    store.addTab({
      ...baseTab,
      fullPath: '/admin/employees',
      query: {},
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/employees?employee_id=e1&tab=dashboard&pageKey=employees:detail:e1',
      meta: {
        ...baseTab.meta,
        title: 'Leon Yilmaz',
      },
      query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'dashboard' },
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/employees?employee_id=e2&tab=dashboard&pageKey=employees:detail:e2',
      meta: {
        ...baseTab.meta,
        title: 'Markus Neumann',
      },
      query: { employee_id: 'e2', pageKey: 'employees:detail:e2', tab: 'dashboard' },
    } as any);
    store.addTab({
      ...baseTab,
      fullPath: '/admin/employees?employee_id=e1&tab=overview&pageKey=employees:detail:e1',
      meta: {
        ...baseTab.meta,
        title: 'Leon Yilmaz',
      },
      query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'overview' },
    } as any);

    expect(store.tabs).toHaveLength(3);
    expect(store.tabs.map((tab) => tab.key)).toEqual([
      '/admin/employees',
      'employees:detail:e1',
      'employees:detail:e2',
    ]);
    expect(store.tabs[0]?.meta?.title).toBe('Employees');
    expect(store.tabs[1]?.meta?.title).toBe('Leon Yilmaz');
    expect(store.tabs[1]?.query).toEqual({
      employee_id: 'e1',
      pageKey: 'employees:detail:e1',
      tab: 'overview',
    });
    expect(store.tabs[2]?.meta?.title).toBe('Markus Neumann');
  });

  it('updates only the targeted employee detail tab title and does not rename the Employees list tab', async () => {
    const store = useTabbarStore();
    store.addTab({
      fullPath: '/admin/employees',
      key: '/admin/employees',
      meta: { title: 'Employees' },
      name: 'SicherPlanEmployees',
      path: '/admin/employees',
      query: {},
    } as any);
    store.addTab({
      fullPath: '/admin/employees?employee_id=e1&pageKey=employees:detail:e1&tab=dashboard',
      key: 'employees:detail:e1',
      meta: { title: 'Employees' },
      name: 'SicherPlanEmployees',
      path: '/admin/employees',
      query: { employee_id: 'e1', pageKey: 'employees:detail:e1', tab: 'dashboard' },
    } as any);
    store.addTab({
      fullPath: '/admin/employees?employee_id=e2&pageKey=employees:detail:e2&tab=dashboard',
      key: 'employees:detail:e2',
      meta: { title: 'Employees' },
      name: 'SicherPlanEmployees',
      path: '/admin/employees',
      query: { employee_id: 'e2', pageKey: 'employees:detail:e2', tab: 'dashboard' },
    } as any);

    await store.setTabTitle(
      {
        key: 'employees:detail:e2',
        meta: { fullPathKey: false },
        name: 'SicherPlanEmployees',
        path: '/admin/employees',
        query: { employee_id: 'e2', pageKey: 'employees:detail:e2', tab: 'dashboard' },
      } as any,
      'Leon Yilmaz',
    );

    expect(store.tabs[0]?.key).toBe('/admin/employees');
    expect(store.tabs[0]?.meta?.title).toBe('Employees');
    expect(store.tabs[0]?.meta?.newTabTitle).toBeUndefined();
    expect(store.tabs[1]?.key).toBe('employees:detail:e1');
    expect(store.tabs[1]?.meta?.newTabTitle).toBeUndefined();
    expect(store.tabs[2]?.key).toBe('employees:detail:e2');
    expect(store.tabs[2]?.meta?.newTabTitle).toBe('Leon Yilmaz');
  });

  it('keeps default fullPath tab keys for other query-driven routes', () => {
    const store = useTabbarStore();

    store.addTab({
      fullPath: '/reports?view=monthly',
      meta: { title: 'Reports' },
      name: 'Reports',
      path: '/reports',
      query: { view: 'monthly' },
    } as any);
    store.addTab({
      fullPath: '/reports?view=yearly',
      meta: { title: 'Reports' },
      name: 'Reports',
      path: '/reports',
      query: { view: 'yearly' },
    } as any);

    expect(store.tabs).toHaveLength(2);
    expect(store.tabs.map((tab) => tab.key)).toEqual([
      '/reports?view=monthly',
      '/reports?view=yearly',
    ]);
  });

  it('updates the cached route snapshot for the same tab key without duplicating the cache entry', () => {
    const store = useTabbarStore();
    const component: any = { type: { name: 'CustomersViewStub' } };
    const firstRoute: any = {
      fullPath: '/admin/customers?customer_id=c1&tab=dashboard',
      meta: { domCached: true, fullPathKey: false },
      name: 'SicherPlanCustomers',
      path: '/admin/customers',
      query: { customer_id: 'c1', tab: 'dashboard' },
    };
    const secondRoute: any = {
      fullPath: '/admin/customers?customer_id=c2&tab=orders',
      meta: { domCached: true, fullPathKey: false },
      name: 'SicherPlanCustomers',
      path: '/admin/customers',
      query: { customer_id: 'c2', tab: 'orders' },
    };

    store.addCachedRoute(component, firstRoute);
    store.addCachedRoute(component, secondRoute);

    expect(store.cachedRoutes.size).toBe(1);
    const cachedRoute = store.cachedRoutes.get('/admin/customers');
    expect(cachedRoute?.route.query).toEqual({
      customer_id: 'c2',
      tab: 'orders',
    });
    expect(cachedRoute?.component).toBe(component);
  });

  it('closes all tabs', async () => {
    const store = useTabbarStore();
    store.addTab({
      fullPath: '/home',
      meta: {},
      name: 'Home',
      path: '/home',
    } as any);
    router.replace = vi.fn();

    await store.closeAllTabs(router);

    expect(store.tabs.length).toBe(1);
  });

  it('closes a non-affix tab', () => {
    const store = useTabbarStore();
    const tab: any = {
      fullPath: '/closable',
      meta: {},
      name: 'Closable',
      path: '/closable',
    };
    store.tabs.push(tab);
    store._close(tab);
    expect(store.tabs.length).toBe(0);
  });

  it('does not close an affix tab', () => {
    const store = useTabbarStore();
    const affixTab: any = {
      fullPath: '/affix',
      meta: { affixTab: true },
      name: 'Affix',
      path: '/affix',
    };
    store.tabs.push(affixTab);
    store._close(affixTab);
    expect(store.tabs.length).toBe(1); // Affix tab should not be closed
  });

  it('returns all cache tabs', () => {
    const store = useTabbarStore();
    store.cachedTabs.add('Home');
    store.cachedTabs.add('About');
    expect(store.getCachedTabs).toEqual(['Home', 'About']);
  });

  it('returns all tabs, including affix tabs', () => {
    const store = useTabbarStore();
    const normalTab: any = {
      fullPath: '/normal',
      meta: {},
      name: 'Normal',
      path: '/normal',
    };
    const affixTab: any = {
      fullPath: '/affix',
      meta: { affixTab: true },
      name: 'Affix',
      path: '/affix',
    };
    store.tabs.push(normalTab);
    store.affixTabs.push(affixTab);
    expect(store.getTabs).toContainEqual(normalTab);
    expect(store.affixTabs).toContainEqual(affixTab);
  });

  it('navigates to a specific tab', async () => {
    const store = useTabbarStore();
    const tab: any = { meta: {}, name: 'Dashboard', path: '/dashboard' };

    await store._goToTab(tab, router);

    expect(router.replace).toHaveBeenCalledWith({
      params: {},
      path: '/dashboard',
      query: {},
    });
  });

  it('closes multiple tabs by paths', async () => {
    const store = useTabbarStore();
    store.addTab({
      fullPath: '/home',
      meta: {},
      name: 'Home',
      path: '/home',
    } as any);
    store.addTab({
      fullPath: '/about',
      meta: {},
      name: 'About',
      path: '/about',
    } as any);
    store.addTab({
      fullPath: '/contact',
      meta: {},
      name: 'Contact',
      path: '/contact',
    } as any);

    await store._bulkCloseByKeys(['/home', '/contact']);

    expect(store.tabs).toHaveLength(1);
    expect(store.tabs[0]?.name).toBe('About');
  });

  it('closes all tabs to the left of the specified tab', async () => {
    const store = useTabbarStore();
    store.addTab({
      fullPath: '/home',
      meta: {},
      name: 'Home',
      path: '/home',
    } as any);
    store.addTab({
      fullPath: '/about',
      meta: {},
      name: 'About',
      path: '/about',
    } as any);
    const targetTab: any = {
      fullPath: '/contact',
      meta: {},
      name: 'Contact',
      path: '/contact',
    };
    const addTargetTab = store.addTab(targetTab);
    await store.closeLeftTabs(addTargetTab);

    expect(store.tabs).toHaveLength(1);
    expect(store.tabs[0]?.name).toBe('Contact');
  });

  it('closes all tabs except the specified tab', async () => {
    const store = useTabbarStore();
    store.addTab({
      fullPath: '/home',
      meta: {},
      name: 'Home',
      path: '/home',
    } as any);
    const targetTab: any = {
      fullPath: '/about',
      meta: {},
      name: 'About',
      path: '/about',
    };
    const addTargetTab = store.addTab(targetTab);
    store.addTab({
      fullPath: '/contact',
      meta: {},
      name: 'Contact',
      path: '/contact',
    } as any);

    await store.closeOtherTabs(addTargetTab);

    expect(store.tabs).toHaveLength(1);
    expect(store.tabs[0]?.name).toBe('About');
  });

  it('closes all tabs to the right of the specified tab', async () => {
    const store = useTabbarStore();
    const targetTab: any = {
      fullPath: '/home',
      meta: {},
      name: 'Home',
      path: '/home',
    };
    const addTargetTab = store.addTab(targetTab);
    store.addTab({
      fullPath: '/about',
      meta: {},
      name: 'About',
      path: '/about',
    } as any);
    store.addTab({
      fullPath: '/contact',
      meta: {},
      name: 'Contact',
      path: '/contact',
    } as any);

    await store.closeRightTabs(addTargetTab);

    expect(store.tabs).toHaveLength(1);
    expect(store.tabs[0]?.name).toBe('Home');
  });

  it('closes the tab with the specified key', async () => {
    const store = useTabbarStore();
    const keyToClose = '/about';
    store.addTab({
      fullPath: '/home',
      meta: {},
      name: 'Home',
      path: '/home',
    } as any);
    store.addTab({
      fullPath: keyToClose,
      meta: {},
      name: 'About',
      path: '/about',
    } as any);
    store.addTab({
      fullPath: '/contact',
      meta: {},
      name: 'Contact',
      path: '/contact',
    } as any);

    await store.closeTabByKey(keyToClose, router);

    expect(store.tabs).toHaveLength(2);
    expect(
      store.tabs.find((tab) => tab.fullPath === keyToClose),
    ).toBeUndefined();
  });

  it('refreshes the current tab', async () => {
    const store = useTabbarStore();
    const currentTab: any = {
      fullPath: '/dashboard',
      meta: { name: 'Dashboard' },
      name: 'Dashboard',
      path: '/dashboard',
    };
    router.currentRoute.value = currentTab;

    await store.refresh(router);

    expect(store.excludeCachedTabs.has('Dashboard')).toBe(false);
    expect(store.renderRouteView).toBe(true);
  });
});
