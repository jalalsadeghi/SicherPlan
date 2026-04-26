// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantLinkCard from './AssistantLinkCard.vue';

describe('AssistantLinkCard', () => {
  it('renders safe link text and emits internal navigation intent', async () => {
    const wrapper = mount(AssistantLinkCard, {
      props: {
        actionLabel: 'Open page',
        link: {
          label: 'Planning workspace',
          path: '/admin/planning-shifts?shift_id=shift-1',
          page_id: 'P-03',
          reason: 'Check the release state before dispatch.',
          route_name: 'SicherPlanPlanningShifts',
        },
      },
    });

    expect(wrapper.text()).toContain('Planning workspace');
    expect(wrapper.text()).toContain('Check the release state before dispatch.');
    expect(wrapper.text()).toContain('/admin/planning-shifts?shift_id=shift-1');

    await wrapper.find('button').trigger('click');
    expect(wrapper.emitted('open')).toEqual([
      [
        {
          label: 'Planning workspace',
          path: '/admin/planning-shifts?shift_id=shift-1',
          page_id: 'P-03',
          reason: 'Check the release state before dispatch.',
          route_name: 'SicherPlanPlanningShifts',
        },
      ],
    ]);
  });

  it('renders link labels and reasons as plain text, not raw html', () => {
    const wrapper = mount(AssistantLinkCard, {
      props: {
        actionLabel: 'Open page',
        link: {
          label: '<img src=x onerror=alert(1)>',
          path: '/admin/employees',
          reason: '<strong>Only text</strong>',
        },
      },
    });

    expect(wrapper.html()).not.toContain('<img');
    expect(wrapper.html()).not.toContain('<strong>Only text</strong>');
    expect(wrapper.text()).toContain('<img src=x onerror=alert(1)>');
    expect(wrapper.text()).toContain('<strong>Only text</strong>');
  });
});
