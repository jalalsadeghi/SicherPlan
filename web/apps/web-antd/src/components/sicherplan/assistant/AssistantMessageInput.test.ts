// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantMessageInput from './AssistantMessageInput.vue';

describe('AssistantMessageInput', () => {
  it('uses an accessible label and keeps submit disabled for empty input', async () => {
    const wrapper = mount(AssistantMessageInput, {
      props: {
        inputLabel: 'Ask the assistant',
        placeholder: 'Type your question',
        submitLabel: 'Send',
        value: '   ',
      },
    });

    const textarea = wrapper.find('textarea');
    const submit = wrapper.find('button[type="submit"]');

    expect(textarea.attributes('aria-label')).toBe('Ask the assistant');
    expect(textarea.attributes('placeholder')).toBe('Type your question');
    expect(submit.attributes('disabled')).toBeDefined();
  });

  it('submits on Enter for non-empty input and allows Shift+Enter without submit', async () => {
    const wrapper = mount(AssistantMessageInput, {
      props: {
        inputLabel: 'Ask the assistant',
        placeholder: 'Type your question',
        submitLabel: 'Send',
        value: 'Why is Markus missing?',
      },
    });

    const textarea = wrapper.find('textarea');
    await textarea.trigger('keydown', { key: 'Enter', shiftKey: true });
    expect(wrapper.emitted('submit')).toBeUndefined();

    await textarea.trigger('keydown', { key: 'Enter' });
    expect(wrapper.emitted('submit')).toHaveLength(1);
  });
});
