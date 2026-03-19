from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("SP_ENV", "development")
os.environ.setdefault("SP_APP_VERSION", "0.1.0")
os.environ.setdefault("SP_ALEMBIC_DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SP_OBJECT_STORAGE_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("SP_OBJECT_STORAGE_BUCKET", "sicherplan-dev")

from app.main import app  # noqa: E402


client = TestClient(app)

live_response = client.get("/health/live")
assert live_response.status_code == 200
assert live_response.json()["status"] == "live"

version_response = client.get("/health/version")
assert version_response.status_code == 200
assert "version" in version_response.json()

ready_response = client.get("/health/ready")
assert ready_response.status_code == 200
assert ready_response.json()["status"] == "ready"

error_response = client.get("/demo/error", headers={"X-Request-ID": "ci-observability-check"})
assert error_response.status_code == 400
error_body = error_response.json()["error"]
assert error_body["code"] == "platform.validation_error"
assert error_body["message_key"] == "errors.platform.validation"
assert error_body["request_id"] == "ci-observability-check"
