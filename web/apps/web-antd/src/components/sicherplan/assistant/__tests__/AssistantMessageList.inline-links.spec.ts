// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantMessageList from '../AssistantMessageList.vue';

function buildProps(messages: any[]) {
  return {
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
    messages,
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
  };
}

describe('AssistantMessageList inline links', () => {
  it('renders an inline allowed page link and hides the internal page code', async () => {
    const wrapper = mount(AssistantMessageList, {
      props: buildProps([
        {
          id: 'assistant-1',
          role: 'assistant',
          content: 'fallback',
          structured_response: {
            conversation_id: 'conversation-1',
            message_id: 'assistant-1',
            answer: 'Dies können Sie im Mitarbeiter-Workspace überprüfen.',
            answer_segments: [
              { type: 'text', text: 'Dies können Sie im ' },
              {
                type: 'link',
                text: 'Mitarbeiter-Workspace',
                link: {
                  label: 'Mitarbeiter-Workspace',
                  path: '/admin/employees',
                  page_id: 'E-01',
                },
              },
              { type: 'text', text: ' überprüfen.' },
            ],
            links: [
              {
                label: 'Mitarbeiter-Workspace',
                path: '/admin/employees',
                page_id: 'E-01',
              },
            ],
          },
        },
      ]),
    });

    expect(wrapper.text()).toContain('Dies können Sie im Mitarbeiter-Workspace überprüfen.');
    expect(wrapper.text()).not.toContain('(E-01)');
    const inlineLink = wrapper.get('.sp-assistant-message__inline-link');
    expect(inlineLink.text()).toBe('Mitarbeiter-Workspace');
    await inlineLink.trigger('click');
    expect(wrapper.emitted('open-link')).toEqual([
      [{ label: 'Mitarbeiter-Workspace', path: '/admin/employees', page_id: 'E-01' }],
    ]);
  });

  it('replaces a bare page id with the allowed label when a safe link exists', () => {
    const wrapper = mount(AssistantMessageList, {
      props: buildProps([
        {
          id: 'assistant-2',
          role: 'assistant',
          content: 'fallback',
          structured_response: {
            conversation_id: 'conversation-1',
            message_id: 'assistant-2',
            answer: 'Dies erfolgt auf Shift Planning.',
            answer_segments: [
              { type: 'text', text: 'Dies erfolgt auf ' },
              {
                type: 'link',
                text: 'Shift Planning',
                link: {
                  label: 'Shift Planning',
                  path: '/admin/planning-shifts',
                  page_id: 'P-03',
                },
              },
              { type: 'text', text: '.' },
            ],
            links: [
              {
                label: 'Shift Planning',
                path: '/admin/planning-shifts',
                page_id: 'P-03',
              },
            ],
          },
        },
      ]),
    });

    expect(wrapper.text()).toContain('Dies erfolgt auf Shift Planning.');
    expect(wrapper.text()).not.toContain('P-03');
  });

  it('keeps plain text when no allowed link exists and never linkifies arbitrary urls', () => {
    const wrapper = mount(AssistantMessageList, {
      props: buildProps([
        {
          id: 'assistant-3',
          role: 'assistant',
          content: 'fallback',
          structured_response: {
            conversation_id: 'conversation-1',
            message_id: 'assistant-3',
            answer: 'Please verify this in Shift Planning. http://example.com should stay plain text.',
            answer_segments: [
              { type: 'text', text: 'Please verify this in Shift Planning. http://example.com should stay plain text.' },
            ],
            links: [],
          },
        },
      ]),
    });

    expect(wrapper.text()).toContain('Shift Planning');
    expect(wrapper.find('.sp-assistant-message__inline-link').exists()).toBe(false);
    expect(wrapper.find('a[href="http://example.com"]').exists()).toBe(false);
  });
});
