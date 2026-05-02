// @vitest-environment happy-dom

import { afterEach, describe, expect, it } from 'vitest';

import {
  ASSISTANT_AVOID_SELECTOR,
  queryAssistantAvoidRects,
} from '../assistant-placement';

describe('assistant avoid zones', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('detects marked data-assistant-avoid elements', () => {
    const element = document.createElement('div');
    element.setAttribute('data-assistant-avoid', '');
    element.getBoundingClientRect = () =>
      ({
        top: 600,
        left: 900,
        right: 1200,
        bottom: 680,
        width: 300,
        height: 80,
      }) as DOMRect;
    document.body.append(element);

    const rects = queryAssistantAvoidRects();

    expect(document.querySelectorAll(ASSISTANT_AVOID_SELECTOR)).toHaveLength(1);
    expect(rects).toHaveLength(1);
    expect(rects[0]?.width).toBe(300);
  });

  it('ignores empty or collapsed avoid zones', () => {
    const element = document.createElement('div');
    element.className = 'sp-assistant-avoid';
    element.getBoundingClientRect = () =>
      ({
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: 0,
        height: 0,
      }) as DOMRect;
    document.body.append(element);

    expect(queryAssistantAvoidRects()).toHaveLength(0);
  });
});
