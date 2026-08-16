from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


DEFAULT_ERROR_MESSAGES = {
    400: ("BAD_REQUEST", "The request could not be processed."),
    401: ("UNAUTHORIZED", "Authentication is required."),
    403: ("FORBIDDEN", "You do not have permission to perform this action."),
    404: ("NOT_FOUND", "The requested resource was not found."),
    413: ("REQUEST_TOO_LARGE", "The request is too large."),
    422: ("VALIDATION_ERROR", "The request contains invalid data."),
    429: ("RATE_LIMITED", "Too many requests. Please wait and try again."),
    500: ("INTERNAL_ERROR", "The server could not complete the request."),
    503: ("SERVICE_UNAVAILABLE", "The service is temporarily unavailable."),
}


def request_id_from_request(request: Request | None) -> str:
    if request is None:
        return ""
    return str(getattr(request.state, "request_id", "") or "")


def error_payload(
    *,
    code: str,
    message: str,
    request_id: str,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "requestId": request_id,
            "details": details,
        }
    }


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str | None = None,
    message: str | None = None,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    default_code, default_message = DEFAULT_ERROR_MESSAGES.get(status_code, DEFAULT_ERROR_MESSAGES[500])
    response = JSONResponse(
        status_code=status_code,
        content=error_payload(
            code=code or default_code,
            message=message or default_message,
            request_id=request_id_from_request(request),
            details=details,
        ),
        headers=headers,
    )
    if request_id_from_request(request):
        response.headers["X-Request-ID"] = request_id_from_request(request)
    return response
