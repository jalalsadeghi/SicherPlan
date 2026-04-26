# AI Assistant Local Development

## Purpose

Enable the assistant locally without requiring a real OpenAI key.

## Required local backend settings

For local development, use mock mode in `backend/.env`:

```env
SP_AI_ENABLED=true
SP_AI_PROVIDER=mock
SP_OPENAI_API_KEY=
SP_AI_STORE_RESPONSES=false
```

This keeps the assistant enabled locally while avoiding any frontend OpenAI call and avoiding any local dependency on a real provider key.

## Verification

Check the resolved backend settings:

```bash
PYTHONPATH=backend python3 - <<'PY'
from app.config import settings
print(settings.ai_enabled)
print(settings.ai_provider)
print(settings.ai_store_responses)
PY
```

Expected output:

```text
True
mock
False
```

Then verify in the app:

1. log in with an internal role that has `assistant.chat.access`
2. open `/admin/dashboard`
3. confirm `GET /api/assistant/capabilities` returns `enabled: true`
4. confirm the launcher remains visible after loading

## Notes

- `backend/.env.example` and stage examples remain conservative and disabled by default.
- `assistant.admin` and `assistant.knowledge.reindex` are not needed for normal chat access.
- If the launcher still disappears, inspect the current user role and the live `/api/assistant/capabilities` response before changing frontend visibility logic.
