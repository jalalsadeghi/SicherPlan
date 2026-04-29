// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { defineComponent, h, ref } from 'vue';
import { useRoute } from 'vue-router';
import { describe, expect, it } from 'vitest';

import CachedRouteRenderer from './cached-route-renderer.vue';

const RouteEcho = defineComponent({
  name: 'RouteEcho',
  setup() {
    const route = useRoute();
    return () =>
      h('div', {
        'data-module-key': String(route.meta?.moduleKey ?? ''),
        'data-route-name': String(route.name ?? ''),
      });
  },
});

describe('CachedRouteRenderer', () => {
  it('provides an isolated route context for each cached subtree', () => {
    const wrapper = mount(
      defineComponent({
        components: { CachedRouteRenderer },
        setup() {
          return {
            customersComponent: h(RouteEcho),
            customersRoute: {
              fullPath: '/admin/customers',
              meta: { moduleKey: 'customers' },
              name: 'SicherPlanCustomers',
              path: '/admin/customers',
              query: {},
            },
            employeesComponent: h(RouteEcho),
            employeesRoute: {
              fullPath: '/admin/employees',
              meta: { moduleKey: 'employees' },
              name: 'SicherPlanEmployees',
              path: '/admin/employees',
              query: {},
            },
          };
        },
        template: `
          <div>
            <CachedRouteRenderer
              cache-key="customers:detail:c1"
              :component="customersComponent"
              :route="customersRoute"
            />
            <CachedRouteRenderer
              cache-key="employees:detail:e1"
              :component="employeesComponent"
              :route="employeesRoute"
            />
          </div>
        `,
      }),
    );

    const rendered = wrapper.findAll('[data-route-name]');
    expect(rendered).toHaveLength(2);
    expect(rendered[0]?.attributes('data-route-name')).toBe('SicherPlanCustomers');
    expect(rendered[0]?.attributes('data-module-key')).toBe('customers');
    expect(rendered[1]?.attributes('data-route-name')).toBe('SicherPlanEmployees');
    expect(rendered[1]?.attributes('data-module-key')).toBe('employees');
  });

  it('keeps component-local state isolated for the same component type under different cache keys', async () => {
    const LocalCounter = defineComponent({
      name: 'LocalCounter',
      setup() {
        const count = ref(0);
        const route = useRoute();
        return () =>
          h(
            'button',
            {
              'data-count': String(count.value),
              'data-route-name': String(route.name ?? ''),
              onClick: () => {
                count.value += 1;
              },
            },
            String(count.value),
          );
      },
    });

    const sharedComponent = h(LocalCounter);

    const wrapper = mount(
      defineComponent({
        components: { CachedRouteRenderer },
        setup() {
          return {
            routeA: {
              fullPath: '/admin/customers?customer_id=c1',
              meta: { moduleKey: 'customers' },
              name: 'CustomerA',
              path: '/admin/customers',
              query: { customer_id: 'c1', pageKey: 'customers:detail:c1' },
            },
            routeB: {
              fullPath: '/admin/customers?customer_id=c2',
              meta: { moduleKey: 'customers' },
              name: 'CustomerB',
              path: '/admin/customers',
              query: { customer_id: 'c2', pageKey: 'customers:detail:c2' },
            },
            sharedComponent,
          };
        },
        template: `
          <div>
            <CachedRouteRenderer
              cache-key="customers:detail:c1"
              :component="sharedComponent"
              :route="routeA"
            />
            <CachedRouteRenderer
              cache-key="customers:detail:c2"
              :component="sharedComponent"
              :route="routeB"
            />
          </div>
        `,
      }),
    );

    const buttons = wrapper.findAll('button');
    expect(buttons).toHaveLength(2);

    await buttons[0]!.trigger('click');

    expect(buttons[0]?.attributes('data-count')).toBe('1');
    expect(buttons[1]?.attributes('data-count')).toBe('0');
    expect(buttons[0]?.attributes('data-route-name')).toBe('CustomerA');
    expect(buttons[1]?.attributes('data-route-name')).toBe('CustomerB');
  });
});
