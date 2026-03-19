# Authentication And Session Flows

## Scope

This note documents the Sprint 02 backend auth baseline implemented in `US-5-T2`.

## Current backend flows

- `POST /api/auth/login`
  - Accepts `tenant_code`, `identifier`, and `password`
  - Creates a revocation-ready `iam.user_session`
  - Returns a signed access token plus a rotated refresh token
- `POST /api/auth/refresh`
  - Resolves the stored refresh-token hash from `iam.user_session`
  - Rejects revoked or expired sessions
  - Rotates the stored refresh-token hash in place
- `POST /api/auth/logout`
  - Revokes the current session from the access-token context
- `GET /api/auth/me`
  - Returns the authenticated user plus currently active scoped roles
- `GET /api/auth/sessions`
  - Returns the user session list with current-session marking
- `POST /api/auth/password-reset/request`
  - Always returns a generic success message
  - Creates a one-time `iam.password_reset_token` only when a matching active password-login account exists
- `POST /api/auth/password-reset/confirm`
  - Accepts the raw reset token and new password
  - Rejects expired or already-used reset tokens
  - Revokes existing sessions after the password changes

## Storage rules

- Refresh tokens are never stored raw; only `session_token_hash` is persisted.
- Password-reset tokens are never stored raw; only `token_hash` is persisted.
- Access tokens are signed bearer tokens and are validated against the session store on protected auth endpoints.
- Password-reset rows and session rows remain revocation-friendly instead of being treated as disposable transient state.

## Security baseline

- Login failures return a single invalid-credentials error shape.
- Password-reset request responses do not reveal whether an account exists.
- A lightweight in-process throttle applies lockout after repeated failed login attempts.
- Password hashes use PBKDF2-SHA256.

## Extension seams

- `PasswordResetNotifier` is the swappable delivery seam until platform communication services are available.
- `AuthExtensionHooks` is the seam for future MFA and SSO/OIDC behavior.
- `US-5-T3` should consume the current access-token/session context for RBAC and scope enforcement.
- `US-5-T4` should attach login and auth-event auditing without changing the auth persistence model.
