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

describe('customer order assistant links', () => {
  it('renders safe customer orders and order workspace links without placeholders', async () => {
    const wrapper = mount(AssistantMessageList, {
      props: buildProps([
        {
          id: 'assistant-customer-order-1',
          role: 'assistant',
          content: 'fallback',
          structured_response: {
            conversation_id: 'conversation-1',
            message_id: 'assistant-customer-order-1',
            answer: 'Start in Customers, open the selected customer, and switch to the Orders tab. Then continue in the Order workspace.',
            answer_segments: [
              { type: 'text', text: 'Start in Customers, open the selected customer, and switch to the ' },
              {
                type: 'link',
                text: 'Orders tab',
                link: {
                  label: 'Customer Orders tab',
                  path: '/admin/customers?customer_id=customer-1&tab=orders',
                  page_id: 'C-01',
                },
              },
              { type: 'text', text: '. Then continue in the ' },
              {
                type: 'link',
                text: 'Order workspace',
                link: {
                  label: 'Order workspace',
                  path: '/admin/customers/order-workspace?customer_id=customer-1',
                  page_id: 'C-02',
                },
              },
              { type: 'text', text: '.' },
            ],
            links: [
              {
                label: 'Customer Orders tab',
                path: '/admin/customers?customer_id=customer-1&tab=orders',
                page_id: 'C-01',
              },
              {
                label: 'Order workspace',
                path: '/admin/customers/order-workspace?customer_id=customer-1',
                page_id: 'C-02',
              },
            ],
          },
        },
      ]),
    });

    const inlineLinks = wrapper.findAll('.sp-assistant-message__inline-link');
    expect(inlineLinks).toHaveLength(2);
    expect(inlineLinks[0]?.attributes('href')).toBe('/admin/customers?customer_id=customer-1&tab=orders');
    expect(inlineLinks[1]?.attributes('href')).toBe('/admin/customers/order-workspace?customer_id=customer-1');
    expect(wrapper.html()).not.toContain('href="#"');
    expect(wrapper.html()).not.toContain('[Customer Orders tab]');

    await inlineLinks[0]!.trigger('click');
    await inlineLinks[1]!.trigger('click');
    expect(wrapper.emitted('open-link')).toEqual([
      [{ label: 'Customer Orders tab', path: '/admin/customers?customer_id=customer-1&tab=orders', page_id: 'C-01' }],
      [{ label: 'Order workspace', path: '/admin/customers/order-workspace?customer_id=customer-1', page_id: 'C-02' }],
    ]);
  });
});
