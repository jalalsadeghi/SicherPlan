// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantMessageInput from '../AssistantMessageInput.vue';

describe('AssistantMessageInput sending state', () => {
  it('disables duplicate submission and shows the sending label', async () => {
    const wrapper = mount(AssistantMessageInput, {
      props: {
        disabled: true,
        inputLabel: 'Ask the assistant',
        placeholder: 'Type your question',
        sending: true,
        sendingLabel: 'Sending...',
        submitLabel: 'Send',
        value: 'Why is Markus missing?',
      },
    });

    const textarea = wrapper.get('textarea');
    const submit = wrapper.get('button[type="submit"]');

    expect(textarea.attributes('disabled')).toBeDefined();
    expect(submit.attributes('disabled')).toBeDefined();
    expect(submit.text()).toBe('Sending...');

    await textarea.trigger('keydown', { key: 'Enter' });
    expect(wrapper.emitted('submit')).toBeUndefined();
  });
});
