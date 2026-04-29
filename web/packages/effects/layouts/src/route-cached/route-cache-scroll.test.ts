// @vitest-environment happy-dom

import { ELEMENT_ID_MAIN_CONTENT } from '@vben-core/shared/constants';
import { afterEach, describe, expect, it } from 'vitest';

import {
  getRouteCacheScrollTarget,
  readRouteCacheScrollTop,
  writeRouteCacheScrollTop,
} from './route-cache-scroll';

describe('route-cache-scroll', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('prefers a scrollable main content element when present', () => {
    const mainContent = document.createElement('div');
    mainContent.id = ELEMENT_ID_MAIN_CONTENT;
    const scrollable = document.createElement('div');
    scrollable.style.overflowY = 'auto';
    Object.defineProperty(scrollable, 'clientHeight', { configurable: true, value: 300 });
    Object.defineProperty(scrollable, 'scrollHeight', { configurable: true, value: 900 });
    mainContent.appendChild(scrollable);
    document.body.appendChild(mainContent);

    expect(getRouteCacheScrollTarget(document)).toBe(scrollable);
  });

  it('falls back to document.scrollingElement when no scrollable main content exists', () => {
    const scrollingElement = document.documentElement;
    Object.defineProperty(document, 'scrollingElement', {
      configurable: true,
      value: scrollingElement,
    });

    expect(getRouteCacheScrollTarget(document)).toBe(scrollingElement);
  });

  it('reads and writes the resolved scroll target', () => {
    const scrollingElement = document.documentElement;
    Object.defineProperty(document, 'scrollingElement', {
      configurable: true,
      value: scrollingElement,
    });

    writeRouteCacheScrollTop(480, document);
    expect(readRouteCacheScrollTop(document)).toBe(480);
    expect(scrollingElement.scrollTop).toBe(480);
  });
});
