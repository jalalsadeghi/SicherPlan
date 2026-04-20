import { beforeEach, describe, expect, it } from 'vitest';

import { defaultPreferences } from '../src/config';
import { updateCSSVariables } from '../src/update-css-variables';

describe('updateCSSVariables', () => {
  beforeEach(() => {
    document.documentElement.style.removeProperty('--font-size-base');
    document.documentElement.style.removeProperty('--menu-font-size');
  });

  it('applies 14px as the default font size CSS variable', () => {
    updateCSSVariables({
      ...defaultPreferences,
      theme: {
        ...defaultPreferences.theme,
        fontSize: 14,
      },
    });

    expect(document.documentElement.style.getPropertyValue('--font-size-base')).toBe('14px');
    expect(document.documentElement.style.getPropertyValue('--menu-font-size')).toBe('calc(14px * 0.875)');
  });

  it('applies 12px as the minimum font size CSS variable', () => {
    updateCSSVariables({
      ...defaultPreferences,
      theme: {
        ...defaultPreferences.theme,
        fontSize: 12,
      },
    });

    expect(document.documentElement.style.getPropertyValue('--font-size-base')).toBe('12px');
    expect(document.documentElement.style.getPropertyValue('--menu-font-size')).toBe('calc(12px * 0.875)');
  });
});
