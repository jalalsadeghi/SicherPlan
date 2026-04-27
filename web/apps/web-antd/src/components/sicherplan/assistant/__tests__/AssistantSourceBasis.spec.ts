// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantSourceBasis from '../AssistantSourceBasis.vue';

describe('AssistantSourceBasis', () => {
  it('shows the title but keeps details collapsed by default', () => {
    const wrapper = mount(AssistantSourceBasis, {
      props: {
        title: 'Sources used',
        messageId: 'assistant-1',
        items: [
          {
            source_type: 'workflow_help',
            source_name: 'employee_assign_to_shift',
            page_id: 'E-01',
            title: 'Employees Workspace',
            evidence: 'Employee readiness is checked there.',
          },
        ],
      },
    });

    const toggle = wrapper.get('button');
    expect(toggle.text()).toContain('Sources used');
    expect(toggle.attributes('aria-expanded')).toBe('false');
    expect(wrapper.find('[data-testid="assistant-source-basis-panel"]').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Employee readiness is checked there.');
  });

  it('expands and collapses source details with correct aria state', async () => {
    const wrapper = mount(AssistantSourceBasis, {
      props: {
        title: 'Sources used',
        messageId: 'assistant-2',
        items: [
          {
            source_type: 'page_help_manifest',
            source_name: 'SicherPlanPlanningShifts',
            page_id: 'P-03',
            title: 'Shift Planning',
            evidence: 'Shift release guidance is documented for Shift Planning.',
          },
        ],
      },
    });

    const toggle = wrapper.get('button');
    expect(toggle.attributes('aria-controls')).toBe('assistant-source-panel-assistant-2');

    await toggle.trigger('click');
    expect(toggle.attributes('aria-expanded')).toBe('true');
    expect(wrapper.get('[data-testid="assistant-source-basis-panel"]').text()).toContain(
      'Shift Planning — SicherPlanPlanningShifts',
    );

    await toggle.trigger('click');
    expect(toggle.attributes('aria-expanded')).toBe('false');
    expect(wrapper.find('[data-testid="assistant-source-basis-panel"]').exists()).toBe(false);
  });

  it('does not render when there are no source items', () => {
    const wrapper = mount(AssistantSourceBasis, {
      props: {
        title: 'Sources used',
        messageId: 'assistant-3',
        items: [],
      },
    });

    expect(wrapper.find('[data-testid="assistant-source-basis"]').exists()).toBe(false);
  });
});
