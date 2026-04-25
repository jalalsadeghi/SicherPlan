You are working in the SicherPlan repository.

Problem:
The mobile app login screen can appear misleading when backend auth or downstream employee-context checks fail.

Your task:
Review the mobile login flow and improve error clarity so that:
- invalid credentials
- permission denied
- no linked employee context
- inactive employee link
- internal backend error

are always presented distinctly and never collapse into a misleading generic message due to stale state or incorrect mapping.

Inspect:
- mobile/lib/api/mobile_backend.dart
- mobile/lib/session/mobile_session_controller.dart
- mobile/lib/l10n/app_localizations.dart

Goals:
1. Ensure login error state is always reset correctly before each attempt.
2. Ensure 401/403/409/500 are mapped to the correct localized message keys.
3. Add tests for session controller login failure paths.
4. Keep this task scoped to mobile login UX and state handling only.

Before coding:
- Briefly explain whether the current mobile code is likely the root cause or just making diagnosis harder.

After coding:
- Validate that invalid credentials cannot show up as a generic internal platform error unless the backend truly returned errors.platform.internal.