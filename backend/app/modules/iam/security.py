"""IAM security helpers used by session persistence and password auth."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from typing import Any

from app.errors import ApiException


def hash_session_token(token: str) -> str:
    """Store revocation-capable session secrets as stable hashes, not raw tokens."""

    normalized = token.strip()
    if not normalized:
        raise ValueError("Session token must not be empty.")

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_password(password: str, *, iterations: int = 120_000) -> str:
    normalized = password.strip()
    if len(normalized) < 10:
        raise ValueError("Password must be at least 10 characters long.")

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", normalized.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt, digest_hex = encoded_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.strip().encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations_text),
    ).hex()
    return hmac.compare_digest(derived, digest_hex)


def sign_access_token(payload: dict[str, Any], secret: str) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    signature = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{body}.{encoded_signature}"


def verify_signed_access_token(token: str, secret: str) -> dict[str, Any]:
    try:
        encoded_body, encoded_signature = token.split(".", 1)
        expected_signature = hmac.new(
            secret.encode("utf-8"),
            encoded_body.encode("ascii"),
            hashlib.sha256,
        ).digest()
        provided_signature = base64.urlsafe_b64decode(_pad_b64(encoded_signature))
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("signature mismatch")
        payload = json.loads(base64.urlsafe_b64decode(_pad_b64(encoded_body)))
    except (ValueError, json.JSONDecodeError, binascii.Error):
        raise ApiException(401, "iam.auth.invalid_access_token", "errors.iam.auth.invalid_access_token") from None

    if not isinstance(payload, dict) or "exp" not in payload:
        raise ApiException(401, "iam.auth.invalid_access_token", "errors.iam.auth.invalid_access_token")
    if int(payload["exp"]) <= int(__import__("time").time()):
        raise ApiException(401, "iam.auth.invalid_access_token", "errors.iam.auth.invalid_access_token")
    return payload


def _pad_b64(value: str) -> str:
    return value + "=" * (-len(value) % 4)
