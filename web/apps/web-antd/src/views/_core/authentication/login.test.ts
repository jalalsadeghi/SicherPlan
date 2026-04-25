// @vitest-environment happy-dom

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

const source = readFileSync(
  resolve('apps/web-antd/src/views/_core/authentication/login.vue'),
  'utf8',
);

describe('web-antd login slider captcha toggle', () => {
  it('keeps the temporary slider captcha flag disabled', () => {
    expect(source).toContain('const LOGIN_SLIDER_CAPTCHA_ENABLED = false;');
  });

  it('only adds the captcha schema when the flag is enabled', () => {
    expect(source).toMatch(
      /if \(LOGIN_SLIDER_CAPTCHA_ENABLED\) \{\s*schema\.push\(\{\s*component: markRaw\(SliderCaptcha\),\s*fieldName: 'captcha'/s,
    );
  });

  it('does not submit or reset captcha while the flag is disabled', () => {
    expect(source).toMatch(
      /if \(!LOGIN_SLIDER_CAPTCHA_ENABLED\) \{\s*delete loginParams\.captcha;\s*\}/s,
    );
    expect(source).toMatch(
      /authStore\.authLogin\(loginParams\)\.catch\(\(\) => \{\s*if \(!LOGIN_SLIDER_CAPTCHA_ENABLED\) \{\s*return;\s*\}/s,
    );
  });
});
