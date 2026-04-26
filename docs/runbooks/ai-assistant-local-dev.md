# AI Assistant Local Development

## Purpose

Enable the assistant locally in one of two explicit modes:

1. real OpenAI mode for normal development verification
2. mock mode only for explicit local debugging

## Required local backend settings

Preferred local development uses OpenAI mode in `backend/.env`:

```env
SP_AI_ENABLED=true
SP_AI_PROVIDER=openai
SP_OPENAI_API_KEY=<real key>
SP_AI_RESPONSE_MODEL=<real model name>
SP_AI_STORE_RESPONSES=false
```

If you intentionally want mock mode for local debugging, you must opt in explicitly:

```env
SP_AI_ENABLED=true
SP_AI_PROVIDER=mock
SP_AI_ALLOW_MOCK_PROVIDER=true
SP_OPENAI_API_KEY=
SP_AI_STORE_RESPONSES=false
```

Without `SP_AI_ALLOW_MOCK_PROVIDER=true`, browser chat must fail safely with `assistant.provider.mock_not_allowed`.

## Verification

Check the resolved backend settings:

```bash
PYTHONPATH=backend python3 - <<'PY'
from app.config import settings
print(settings.ai_enabled)
print(settings.ai_provider)
print(settings.ai_mock_provider_allowed)
print(settings.ai_openai_configured)
print(settings.ai_store_responses)
PY
```

Example output for OpenAI mode:

```text
True
openai
False
True
False
```

Example output for explicit local mock mode:

```text
True
mock
True
False
False
```

Then verify in the app:

1. log in with an internal role that has `assistant.chat.access`
2. open `/admin/dashboard`
3. confirm `GET /api/assistant/capabilities` returns:
   - `provider_mode: openai` for normal dev
   - or `provider_mode: mock` plus `mock_provider_allowed: true` for explicit local mock mode
4. if using OpenAI mode, ask one in-scope question and verify usage appears in the OpenAI platform
5. if using mock mode, confirm the panel shows the mock-mode warning and the answer starts with `[MOCK RAG]`

## Notes

- `backend/.env.example` and stage examples remain conservative and disabled by default.
- `assistant.admin` and `assistant.knowledge.reindex` are not needed for normal chat access.
- If the launcher still disappears, inspect the current user role and the live `/api/assistant/capabilities` response before changing frontend visibility logic.
