"""Sealing helpers for stored integration secrets."""

from __future__ import annotations

import base64
import json
from hashlib import sha256
from secrets import token_bytes

from app.errors import ApiException


class IntegrationSecretBox:
    def __init__(self, secret_key: str) -> None:
        if not secret_key.strip():
            raise ValueError("integration secret key must not be empty")
        self.secret_key = secret_key.encode("utf-8")

    def seal(self, payload: dict[str, object]) -> str:
        try:
            plaintext = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        except TypeError as exc:
            raise ApiException(400, "integration.secret.invalid", "errors.integration.secret.invalid") from exc
        nonce = token_bytes(16)
        ciphertext = self._xor_keystream(plaintext, nonce)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    def open(self, ciphertext: str | None) -> dict[str, object]:
        if not ciphertext:
            return {}
        raw = base64.b64decode(ciphertext.encode("ascii"))
        nonce, encrypted = raw[:16], raw[16:]
        plaintext = self._xor_keystream(encrypted, nonce)
        return json.loads(plaintext.decode("utf-8"))

    def _xor_keystream(self, data: bytes, nonce: bytes) -> bytes:
        output = bytearray()
        counter = 0
        while len(output) < len(data):
            block = sha256(self.secret_key + nonce + counter.to_bytes(4, "big")).digest()
            output.extend(block)
            counter += 1
        return bytes(value ^ output[index] for index, value in enumerate(data))
