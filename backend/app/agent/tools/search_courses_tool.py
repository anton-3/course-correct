from __future__ import annotations

from typing import Any, Dict

from app.services.unl import get_unl_course_info

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]

_TOOL_DECLARATIONS = [
    {
        "name": "search_courses",
        "description": (
            "Search for courses by a search phrase. This searches the course catalog "
            "for courses that contain the EXACT search phrase in their name or description. "
            "Returns a list of matching courses with their course codes, titles, and descriptions."
            "DO NOT request with verbose queries. Remove any numbers and any words that would not be exactly contained in the course name or description."
            "Single-word queries are best. Be broad, and then narrow down by looking at the courses returned."
            "You can also simply search for a whole department name, such as 'CSCE', 'COMM', 'MATH', etc. This will return all courses in that department."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search phrase to find courses (e.g., 'algorithms', 'data structures', 'calculus').",
                },
            },
            "required": ["query"],
        },
    }
]


def _filter_course_fields(course: Dict[str, Any]) -> Dict[str, Any]:
    """Filter a course dict to only include course_code, course_title, and Description."""
    return {
        "course_code": course.get("course_code", ""),
        "course_title": course.get("course_title", ""),
        "Description": course.get("Description", ""),
    }


def _handle_search_courses(payload: ToolPayload) -> tuple[ToolResult, str | None]:
    query = payload.get("query")
    if not query:
        raise ValueError("Function call missing 'query'.")

    try:
        unl_response = get_unl_course_info(query)
    except Exception as exc:
        return {
            "found": False,
            "data": None,
            "message": f"Error searching courses: {str(exc)}",
            "errors": {"search": str(exc)},
        }, None

    # Handle error response
    if isinstance(unl_response, dict) and "error" in unl_response:
        return {
            "found": False,
            "data": None,
            "message": unl_response.get("error", "No courses found."),
            "errors": {"search": unl_response.get("error", "Unknown error.")},
        }, None

    # Handle single course response (wrap in list)
    if isinstance(unl_response, dict):
        courses = [unl_response]
    # Handle list of courses
    elif isinstance(unl_response, list):
        courses = unl_response
    else:
        return {
            "found": False,
            "data": None,
            "message": "Unexpected response format from course catalog.",
            "errors": {"search": "Unexpected response format."},
        }, None

    # Filter each course to only include course_code, course_title, and Description
    filtered_courses = [_filter_course_fields(course) for course in courses]

    result: ToolResult = {
        "found": True,
        "data": {"courses": filtered_courses},
        "message": f"Found {len(filtered_courses)} course(s) matching '{query}'.",
    }

    return result, None


TOOL_DECLARATIONS = _TOOL_DECLARATIONS
TOOL_HANDLERS = {
    "search_courses": _handle_search_courses,
}

