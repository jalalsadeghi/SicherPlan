// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantPanel from '../AssistantPanel.vue';

describe('frontend provider degraded message', () => {
  it('renders the degraded warning inside the assistant message without showing the panel error box', () => {
    const wrapper = mount(AssistantPanel, {
      props: {
        assistantLabel: 'Assistant',
        closeLabel: 'Close',
        confidenceLabel: 'Confidence',
        description: 'Description',
        diagnosisTitle: 'Diagnosis',
        degradedWarning: 'Degraded answer',
        draftInput: '',
        emptyBody: 'Empty body',
        emptyTitle: 'Empty title',
        errorBody: 'Request failed',
        errorVisible: false,
        inputLabel: 'Input',
        inputPlaceholder: 'Type here',
        feedbackCommentLabel: 'Comment',
        feedbackCommentPlaceholder: 'Comment',
        feedbackErrorLabel: 'Feedback error',
        feedbackHelpfulLabel: 'Helpful',
        feedbackNotHelpfulLabel: 'Not helpful',
        feedbackPromptLabel: 'Prompt',
        feedbackSubmitCommentLabel: 'Submit',
        feedbackSubmittedLabel: 'Submitted',
        linkActionLabel: 'Open',
        linksTitle: 'Links',
        loadingConversation: false,
        messages: [
          {
            id: 'assistant-1',
            role: 'assistant',
            content: 'Fallback answer',
            structured_response: {
              answer: 'Fallback answer',
              confidence: 'low',
              conversation_id: 'conversation-1',
              message_id: 'assistant-1',
              provider_degraded: true,
              out_of_scope: false,
              diagnosis: [],
              links: [],
              missing_permissions: [],
              next_steps: [],
              source_basis: [],
            },
          },
        ],
        missingPermissionsTitle: 'Missing permissions',
        nextStepsTitle: 'Next steps',
        processingLabel: 'Processing',
        sourcesTitle: 'Sources',
        severityLabels: {
          info: 'Info',
          warning: 'Warning',
          blocking: 'Blocking',
        },
        submitLabel: 'Send',
        title: 'Assistant',
        userLabel: 'You',
      },
      global: {
        stubs: {
          IconifyIcon: {
            template: '<span class="icon-stub" />',
          },
        },
      },
    });

    expect(wrapper.find('[data-testid="assistant-provider-degraded"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="assistant-error-state"]').exists()).toBe(false);
  });
});
