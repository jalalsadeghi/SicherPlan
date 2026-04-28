// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
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
            <CachedRouteRenderer :component="customersComponent" :route="customersRoute" />
            <CachedRouteRenderer :component="employeesComponent" :route="employeesRoute" />
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
});
