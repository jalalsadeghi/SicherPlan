You are working in the latest public SicherPlan repository.

Target page:
Login page

Main file to inspect:
- web/apps/web-antd/src/views/_core/authentication/login.vue

Related files to inspect if needed:
- web/packages/locales/src/langs/en-US/ui.json
- web/packages/locales/src/langs/de-DE/ui.json
- any login/auth tests
- auth store/login tests if they expect captcha

Current implementation:
The login form schema includes a SliderCaptcha field:
- import { AuthenticationLogin, SliderCaptcha, z } from '@vben/common-ui'
- fieldName: 'captcha'
- rules require captcha to be true
- onSubmit catches failed login, resets captcha to false, and calls SliderCaptcha.resume()

User request:
Temporarily remove the "Slider and drag" captcha from the login page.
It must be easy to restore later.

Goal:
Disable/hide the SliderCaptcha from the login form for now, without deleting the implementation permanently and without breaking login validation.

Important:
Do not simply hide the UI with CSS while keeping the required captcha validation active.
Do not leave the form requiring `captcha: true` when the field is not visible.
Do not break the login submit flow.
Do not remove the code in a way that makes restoring hard.
Do not change backend authentication unless it currently requires captcha and must be adjusted accordingly.

Required investigation:
1) Confirm whether backend authLogin requires a captcha field or whether captcha is frontend-only validation.
2) Confirm whether `authStore.authLogin(params)` sends captcha to backend or ignores it.
3) Find any tests that assume captcha exists.
4) Confirm whether other app variants also have login.vue with SliderCaptcha. For this task, focus on web-antd unless the project expects all variants to stay aligned.

Preferred implementation:
Add a small feature flag / local constant in login.vue, for example:
`const LOGIN_SLIDER_CAPTCHA_ENABLED = false;`
or use an existing config/env feature flag if one already exists.

Then:
- Keep SliderCaptcha import only if the feature is enabled, or keep it with a clear comment if dynamic import is not worth it.
- Build formSchema so the captcha field is included only when `LOGIN_SLIDER_CAPTCHA_ENABLED === true`.
- In onSubmit catch block, only reset/resume captcha if captcha is enabled.
- If captcha is disabled, do not call `setFieldValue('captcha', false, false)` and do not call `getFieldComponentRef(...).resume()`.
- Optionally strip `captcha` from submit params when disabled if it appears unexpectedly.
- Add a short comment explaining that captcha is temporarily disabled and can be restored by flipping the flag.

Example desired behavior:
- Login page shows tenant code, identifier, password, remember me, login button, mobile login, QR code login, social login.
- The "Slider and drag" component is not rendered.
- Clicking Login does not fail because captcha is missing.
- Failed login still shows normal login error.
- No console error is caused by trying to access a non-existing captcha field.

Validation:
Please validate my suggestion critically.
If the backend currently requires captcha, do not silently remove it only from frontend; instead identify the backend dependency and propose the minimal safe change.
If captcha is frontend-only, keep the change frontend-only.

Tests:
Add/update tests if existing login tests exist:
- captcha disabled: SliderCaptcha is not rendered.
- form schema does not include captcha.
- submit does not require captcha.
- failed login does not call captcha resume when disabled.
- if feature flag is later true, captcha field is included and old behavior can still work.

Acceptance criteria:
- The "Slider and drag" captcha no longer appears on login page.
- Login form can submit without captcha.
- Failed login handling does not throw errors.
- Captcha code is not permanently deleted; it can be restored easily.
- No unrelated login UI elements are removed.
- No backend/auth regression.

Deliverables:
1) Apply code changes.
2) Update tests if needed.
3) Summarize:
   - changed files
   - how captcha was disabled
   - how to re-enable it later
   - whether backend needed any change
   - validation performed