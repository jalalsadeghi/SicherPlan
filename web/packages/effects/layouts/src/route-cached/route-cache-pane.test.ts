// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { defineComponent, h, inject } from 'vue';
import { afterEach, describe, expect, it } from 'vitest';

import RouteCachePane from './route-cache-pane.vue';
import {
  type RouteCacheSession,
  resetRouteCacheSessionState,
  routeCacheSessionKey,
} from './route-cache-session';

const SessionEcho = defineComponent({
  name: 'SessionEcho',
  setup() {
    const session = inject<RouteCacheSession>(routeCacheSessionKey);
    return () =>
      h('div', {
        'data-cache-key': session?.cacheKey ?? '',
        'data-route-name': String(session?.route?.name ?? ''),
        'data-session-active': String(session?.isActive ?? false),
      });
  },
});

describe('RouteCachePane', () => {
  afterEach(() => {
    resetRouteCacheSessionState();
    document.body.innerHTML = '';
  });

  it('provides an isolated session per cache key with independent active state', () => {
    const wrapper = mount(
      defineComponent({
        components: { RouteCachePane, SessionEcho },
        setup() {
          return {
            employeesRoute: {
              fullPath: '/admin/employees',
              meta: { moduleKey: 'employees' },
              name: 'SicherPlanEmployees',
              path: '/admin/employees',
              query: { employee_id: 'e1', pageKey: 'employees:detail:e1' },
            },
            customersRoute: {
              fullPath: '/admin/customers',
              meta: { moduleKey: 'customers' },
              name: 'SicherPlanCustomers',
              path: '/admin/customers',
              query: { customer_id: 'c1', pageKey: 'customers:detail:c1' },
            },
          };
        },
        template: `
          <div>
            <RouteCachePane
              cache-key="employees:detail:e1"
              :route="employeesRoute"
              :active="true"
            >
              <SessionEcho />
            </RouteCachePane>
            <RouteCachePane
              cache-key="customers:detail:c1"
              :route="customersRoute"
              :active="false"
            >
              <SessionEcho />
            </RouteCachePane>
          </div>
        `,
      }),
    );

    const sessions = wrapper.findAll('[data-cache-key]');
    expect(sessions).toHaveLength(2);
    expect(sessions[0]?.attributes('data-cache-key')).toBe(
      'employees:detail:e1',
    );
    expect(sessions[0]?.attributes('data-session-active')).toBe('true');
    expect(sessions[0]?.attributes('data-route-name')).toBe(
      'SicherPlanEmployees',
    );
    expect(sessions[1]?.attributes('data-cache-key')).toBe(
      'customers:detail:c1',
    );
    expect(sessions[1]?.attributes('data-session-active')).toBe('false');
    expect(sessions[1]?.attributes('data-route-name')).toBe(
      'SicherPlanCustomers',
    );
  });
});
