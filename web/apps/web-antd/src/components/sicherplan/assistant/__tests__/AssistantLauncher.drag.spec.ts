// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantLauncher from '../AssistantLauncher.vue';

function mountLauncher(props: Record<string, unknown> = {}) {
  return mount(AssistantLauncher, {
    props: {
      title: 'Open SicherPlan Assistant',
      dragHint: 'Drag to move',
      ...props,
    },
    global: {
      stubs: {
        IconifyIcon: {
          template: '<span class="icon-stub" />',
        },
      },
    },
  });
}

describe('AssistantLauncher drag behavior', () => {
  it('clicks without drag and emits toggle', async () => {
    const wrapper = mountLauncher();

    await wrapper.get('button').trigger('click');

    expect(wrapper.emitted('toggle')).toHaveLength(1);
    expect(wrapper.emitted('drag-start')).toBeUndefined();
  });

  it('drags after threshold and suppresses toggle on release', async () => {
    const wrapper = mountLauncher();
    const button = wrapper.get('button');

    await button.trigger('pointerdown', {
      pointerId: 1,
      clientX: 100,
      clientY: 100,
    });
    await button.trigger('pointermove', {
      pointerId: 1,
      clientX: 120,
      clientY: 130,
    });
    await button.trigger('pointerup', {
      pointerId: 1,
      clientX: 120,
      clientY: 130,
    });
    await button.trigger('click');

    expect(wrapper.emitted('drag-start')).toHaveLength(1);
    expect(wrapper.emitted('drag-move')).toHaveLength(1);
    expect(wrapper.emitted('drag-end')).toHaveLength(1);
    expect(wrapper.emitted('toggle')).toBeUndefined();
  });

  it('emits keyboard movement deltas from arrow keys', async () => {
    const wrapper = mountLauncher();
    const button = wrapper.get('button');

    await button.trigger('keydown', { key: 'ArrowRight' });
    await button.trigger('keydown', { key: 'ArrowDown', shiftKey: true });

    expect(wrapper.emitted('move-keyboard')).toEqual([
      [{ dx: 16, dy: 0 }],
      [{ dx: 0, dy: 48 }],
    ]);
  });
});
