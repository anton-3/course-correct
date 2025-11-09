from __future__ import annotations

from typing import Any, Dict

from app.services.collegescheduler import get_registration_blocks
from app.services.unl import get_unl_course_info

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]

_TOOL_DECLARATIONS = [
    {
        "name": "get_course_info",
        "description": (
            "Look up catalog details for a course by its identifier, such as "
            "CSCE 123, COMM 101, CSCE 155A, etc. These catalog details include"
            ""
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {
                    "type": "string",
                    "description": "Course identifier to look up (e.g. CSCE 123).",
                },
            },
            "required": ["course_id"],
        },
    }
]


def _normalize_course_id(course_id: str) -> str:
    return " ".join(course_id.strip().upper().split())


def _handle_get_course_info(payload: ToolPayload) -> ToolResult:
    course_id = payload.get("course_id")
    if not course_id:
        raise ValueError("Function call missing 'course_id'.")

    normalized_id = _normalize_course_id(course_id)
    errors: Dict[str, str] = {}

    catalog_data: Dict[str, Any] | None = None
    try:
        unl_response = get_unl_course_info(normalized_id)
    except Exception as exc:  # pragma: no cover - defensive
        errors["catalog"] = str(exc)
    else:
        if isinstance(unl_response, dict) and "error" not in unl_response:
            catalog_data = dict(unl_response)
        elif isinstance(unl_response, dict):
            errors["catalog"] = unl_response.get("error", "Unknown catalog error.")
        else:  # pragma: no cover - defensive
            errors["catalog"] = "Unexpected response from catalog service."

    registration_data: Any | None = None
    try:
        registration_response = get_registration_blocks(normalized_id)
    except Exception as exc:  # pragma: no cover - defensive
        errors["registration_blocks"] = str(exc)
    else:
        registration_data = registration_response

    combined_data: Dict[str, Any] = {}
    if catalog_data is not None:
        combined_data["catalog"] = catalog_data
    if registration_data is not None:
        combined_data["registration_blocks"] = registration_data

    found = bool(combined_data)
    if found and errors:
        message = "Course data retrieved with partial errors."
    elif found:
        message = "Course data retrieved successfully."
    else:
        message = "Course data could not be retrieved."

    result: ToolResult = {
        "found": found,
        "data": combined_data if found else None,
        "message": message,
    }

    if errors:
        result["errors"] = errors

    return result


TOOL_DECLARATIONS = _TOOL_DECLARATIONS
TOOL_HANDLERS = {
    "get_course_info": _handle_get_course_info,
}

