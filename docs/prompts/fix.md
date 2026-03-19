Please fix the application language configuration.

Required project behavior:
- Default language: German
- Secondary language: English

Current wrong behavior:
- Simplified Chinese + English

Please inspect the full i18n setup and fix the root cause, not just the visible labels.
If this came from Vben default template settings, override them properly.

Also check:
- locale config
- fallback locale
- language switcher
- translation files
- browser locale detection
- localStorage / persisted settings
- any hardcoded Chinese defaults

Final result must be:
- German as default
- English as secondary
- no Chinese default anywhere in the app