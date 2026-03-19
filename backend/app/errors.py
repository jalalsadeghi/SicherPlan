"""Stable API error envelope and exception handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.logging_utils import request_id_context


class ErrorBody(BaseModel):
    code: str
    message_key: str
    request_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    error: ErrorBody


@dataclass(slots=True)
class ApiException(Exception):
    status_code: int
    code: str
    message_key: str
    details: dict[str, Any] = field(default_factory=dict)


def build_error_response(
    *,
    status_code: int,
    code: str,
    message_key: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message_key=message_key,
            request_id=request_id_context.get("-"),
            details=details or {},
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))


async def api_exception_handler(_: Request, exc: ApiException) -> JSONResponse:
    return build_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message_key=exc.message_key,
        details=exc.details,
    )


async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    return build_error_response(
        status_code=500,
        code="platform.internal_error",
        message_key="errors.platform.internal",
    )
