from __future__ import annotations

from typing import Any, Dict

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]

_TOOL_DECLARATIONS = [
    {
        "name": "get_course_info",
        "description": (
            "Look up catalog details for a course by its identifier, such as "
            "CSCE 123."
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

_MOCK_COURSES: Dict[str, Dict[str, Any]] = {
    "CSCE 123": {
        "title": "Computer Science I: Foundations",
        "description": (
            "Introduction to algorithms, problem-solving strategies, and "
            "software development fundamentals using Python. Students build "
            "fluency with conditionals, iteration, and data structures."
        ),
        "credits": 3,
        "prerequisites": ["MATH 104 or higher (can be taken concurrently)"],
        "instructors": ["Dr. Ada Lovelace", "Prof. Alan Turing"],
        "delivery": ["In-person", "Online synchronous"],
    },
    "MATH 208": {
        "title": "Applied Calculus III",
        "description": (
            "Vector calculus topics including multiple integrals, vector fields, "
            "and Stokes' theorem with applications to engineering and physics."
        ),
        "credits": 4,
        "prerequisites": ["MATH 107 or MATH 198"],
        "instructors": ["Dr. Katherine Johnson"],
        "delivery": ["In-person"],
    },
}


def _normalize_course_id(course_id: str) -> str:
    return " ".join(course_id.strip().upper().split())


def _handle_get_course_info(payload: ToolPayload) -> ToolResult:
    course_id = payload.get("course_id")
    if not course_id:
        raise ValueError("Function call missing 'course_id'.")

    normalized_id = _normalize_course_id(course_id)
    course_details = _MOCK_COURSES.get(normalized_id)

    if not course_details:
        return {
            "course_id": normalized_id,
            "found": False,
            "data": None,
            "message": (
                "Course information is not available in the mock catalog yet. "
                "Please verify the course identifier."
            ),
        }

    return {
        "course_id": normalized_id,
        "found": True,
        "data": course_details,
        "message": "Mock course data retrieved successfully.",
    }


TOOL_DECLARATIONS = _TOOL_DECLARATIONS
TOOL_HANDLERS = {
    "get_course_info": _handle_get_course_info,
}

