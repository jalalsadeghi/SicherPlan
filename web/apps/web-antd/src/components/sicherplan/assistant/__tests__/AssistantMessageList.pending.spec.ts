// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantMessageList from '../AssistantMessageList.vue';

describe('AssistantMessageList pending state', () => {
  it('renders an accessible pending assistant indicator', () => {
    const wrapper = mount(AssistantMessageList, {
      props: {
        assistantLabel: 'Assistant',
        confidenceLabel: 'Confidence',
        degradedWarning: 'Degraded answer',
        diagnosisTitle: 'Findings',
        emptyBody: 'Empty',
        emptyTitle: 'Nothing yet',
        feedbackCommentLabel: 'Comment',
        feedbackCommentPlaceholder: 'Add detail',
        feedbackErrorLabel: 'Feedback failed',
        feedbackHelpfulLabel: 'Helpful',
        feedbackNotHelpfulLabel: 'Not helpful',
        feedbackPromptLabel: 'Was this useful?',
        feedbackSubmitCommentLabel: 'Send feedback',
        feedbackSubmittedLabel: 'Thanks',
        linkActionLabel: 'Open page',
        linksTitle: 'Links',
        messages: [
          {
            id: 'user-1',
            role: 'user',
            content: 'Why is Markus missing?',
          },
          {
            id: 'assistant-pending-1',
            role: 'assistant',
            content: '',
            pending: true,
          },
        ],
        missingPermissionsTitle: 'Missing permissions',
        nextStepsTitle: 'Next steps',
        processingLabel: 'Processing request',
        sourcesTitle: 'Sources used',
        severityLabels: {
          blocking: 'Blocking',
          info: 'Info',
          warning: 'Warning',
        },
        userLabel: 'You',
      },
    });

    const indicator = wrapper.get('[data-testid="assistant-pending-indicator"]');
    expect(indicator.attributes('role')).toBe('status');
    expect(indicator.attributes('aria-live')).toBe('polite');
    expect(indicator.text()).toContain('Processing request');
    expect(indicator.find('.sp-assistant-message__pending-dot').exists()).toBe(true);
    expect(indicator.find('.icon-stub').exists()).toBe(false);
  });

  it('scrolls to the newly added pending indicator', async () => {
    const wrapper = mount(AssistantMessageList, {
      props: {
        assistantLabel: 'Assistant',
        confidenceLabel: 'Confidence',
        degradedWarning: 'Degraded answer',
        diagnosisTitle: 'Findings',
        emptyBody: 'Empty',
        emptyTitle: 'Nothing yet',
        feedbackCommentLabel: 'Comment',
        feedbackCommentPlaceholder: 'Add detail',
        feedbackErrorLabel: 'Feedback failed',
        feedbackHelpfulLabel: 'Helpful',
        feedbackNotHelpfulLabel: 'Not helpful',
        feedbackPromptLabel: 'Was this useful?',
        feedbackSubmitCommentLabel: 'Send feedback',
        feedbackSubmittedLabel: 'Thanks',
        linkActionLabel: 'Open page',
        linksTitle: 'Links',
        messages: [],
        missingPermissionsTitle: 'Missing permissions',
        nextStepsTitle: 'Next steps',
        processingLabel: 'Processing request',
        sourcesTitle: 'Sources used',
        severityLabels: {
          blocking: 'Blocking',
          info: 'Info',
          warning: 'Warning',
        },
        userLabel: 'You',
      },
    });

    const container = wrapper.get('[data-testid="assistant-message-list"]').element as HTMLDivElement;
    Object.defineProperty(container, 'scrollHeight', {
      configurable: true,
      value: 320,
    });
    container.scrollTop = 0;

    await wrapper.setProps({
      messages: [
        {
          id: 'assistant-pending-1',
          role: 'assistant',
          content: '',
          pending: true,
        },
      ],
    });

    expect(container.scrollTop).toBe(320);
  });
});
