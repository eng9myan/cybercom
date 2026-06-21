"""
RFC 7807 Problem Detail exception handler for DRF. ADR-0003.
All API errors return consistent JSON structure.
"""
from typing import Any
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def cybercom_exception_handler(exc: Any, context: Any) -> Response | None:
    response = exception_handler(exc, context)

    if response is not None:
        request = context.get("request")
        view = context.get("view")

        problem = {
            "type": f"https://cybercom.io/errors/{_get_error_code(exc)}",
            "title": _get_title(response.status_code),
            "status": response.status_code,
            "detail": _extract_detail(response.data),
            "instance": request.path if request else None,
        }

        if hasattr(exc, "default_code"):
            problem["code"] = exc.default_code

        response.data = problem

    return response


def _get_error_code(exc: Any) -> str:
    if hasattr(exc, "default_code"):
        return exc.default_code
    return "error"


def _get_title(status_code: int) -> str:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    return titles.get(status_code, "Error")


def _extract_detail(data: Any) -> str:
    if isinstance(data, dict):
        if "detail" in data:
            detail = data["detail"]
            return str(detail) if not isinstance(detail, str) else detail
        return "; ".join(f"{k}: {v}" for k, v in data.items())
    if isinstance(data, list):
        return "; ".join(str(item) for item in data)
    return str(data)
