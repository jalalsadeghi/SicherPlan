// @vitest-environment happy-dom

import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AssistantMessageList from './AssistantMessageList.vue';

describe('AssistantMessageList', () => {
  it('renders feedback controls only for assistant messages and emits feedback submissions', async () => {
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
            id: 'assistant-1',
            role: 'assistant',
            content: 'The shift is not released.',
            structured_response: {
              answer: 'The shift is not released.',
              conversation_id: 'conversation-1',
              message_id: 'assistant-1',
            },
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

    expect(wrapper.findAll('[data-testid="assistant-feedback"]')).toHaveLength(1);
    expect(wrapper.text()).toContain('Was this useful?');

    const feedbackButtons = wrapper.findAll('.sp-assistant-feedback__action');
    await feedbackButtons[1]!.trigger('click');
    await wrapper.find('.sp-assistant-feedback__submit').trigger('click');

    expect(wrapper.emitted('submit-feedback')).toEqual([
      [{ messageId: 'assistant-1', rating: 'not_helpful', comment: null }],
    ]);
  });

  it('renders structured diagnosis, missing permissions, next steps, and collapsible source basis as readable UI', async () => {
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
            id: 'assistant-2',
            role: 'assistant',
            content: 'Fallback',
            structured_response: {
              answer: 'I checked the current scope and the request is out of scope.',
              confidence: 'high',
              conversation_id: 'conversation-1',
              provider_degraded: true,
              diagnosis: [
                {
                  evidence: 'Shift Plan release is still draft.',
                  finding: 'Shift Plan is not released.',
                  severity: 'blocking',
                },
                {
                  evidence: 'Validation detail is not available.',
                  finding: 'You are missing a planning permission.',
                  severity: 'warning',
                },
              ],
              links: [],
              message_id: 'assistant-2',
              missing_permissions: [
                {
                  permission: 'planning.staffing.read',
                  reason: 'Validation details are hidden.',
                },
              ],
              next_steps: ['Open the planning workspace.'],
              out_of_scope: true,
              source_basis: [
                {
                  source_type: 'workflow_help',
                  source_name: 'contract_or_document_register',
                  page_id: 'PS-01',
                  title: 'Platform Services Workspace',
                  evidence: 'Verified document workflow context exists in Platform Services.',
                },
              ],
            },
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

    expect(wrapper.text()).toContain('I checked the current scope and the request is out of scope.');
    expect(wrapper.text()).toContain('Degraded answer');
    expect(wrapper.text()).toContain('Findings');
    expect(wrapper.text()).toContain('Blocking');
    expect(wrapper.text()).toContain('Shift Plan is not released.');
    expect(wrapper.text()).toContain('Warning');
    expect(wrapper.text()).toContain('Missing permissions');
    expect(wrapper.text()).toContain('planning.staffing.read');
    expect(wrapper.text()).toContain('Next steps');
    expect(wrapper.text()).toContain('Open the planning workspace.');
    expect(wrapper.text()).toContain('Sources used');
    expect(wrapper.text()).not.toContain('Platform Services Workspace — contract_or_document_register');
    const sourceToggle = wrapper.get('[data-testid="assistant-source-basis"] button');
    expect(sourceToggle.attributes('aria-expanded')).toBe('false');
    await sourceToggle.trigger('click');
    expect(sourceToggle.attributes('aria-expanded')).toBe('true');
    expect(wrapper.text()).toContain('Platform Services Workspace — contract_or_document_register');
    expect(wrapper.text()).not.toContain('Links');
  });
});
