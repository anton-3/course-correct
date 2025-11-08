from __future__ import annotations

from typing import Any, Dict

from app.services.rmp import RMPClient

_DEFAULT_SCHOOL = "University of Nebraska-Lincoln"

_TOOL_DECLARATIONS = [
    {
        "name": "get_professor_summary",
        "description": (
            "Retrieve a RateMyProfessors summary for an instructor at the "
            "University of Nebraska-Lincoln."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "professor_name": {
                    "type": "string",
                    "description": "Name of the professor to search for.",
                },
            },
            "required": ["professor_name"],
        },
    },
]

_rmp_client = RMPClient()

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]


def _handle_get_professor_summary(payload: ToolPayload) -> ToolResult:
    professor_name = payload.get("professor_name")
    if not professor_name:
        raise ValueError("Function call missing 'professor_name'.")

    return _rmp_client.get_professor_summary(
        school_name=_DEFAULT_SCHOOL,
        professor_name=professor_name,
    )


TOOL_DECLARATIONS = _TOOL_DECLARATIONS
TOOL_HANDLERS = {
    "get_professor_summary": _handle_get_professor_summary,
}

