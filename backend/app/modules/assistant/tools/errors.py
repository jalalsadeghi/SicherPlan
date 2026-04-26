"""Safe assistant tool registry errors."""

from __future__ import annotations


class AssistantToolError(RuntimeError):
    """Base safe tool error."""

    code = "assistant.tool.error"


class AssistantToolNotFoundError(AssistantToolError):
    code = "assistant.tool.not_found"


class AssistantToolDisabledError(AssistantToolError):
    code = "assistant.tool.disabled"


class AssistantToolWriteBlockedError(AssistantToolError):
    code = "assistant.tool.write_blocked"


class AssistantToolPermissionDeniedError(AssistantToolError):
    code = "assistant.tool.permission_denied"


class AssistantToolInputValidationError(AssistantToolError):
    code = "assistant.tool.input_invalid"


class AssistantToolExecutionError(AssistantToolError):
    code = "assistant.tool.execution_failed"
