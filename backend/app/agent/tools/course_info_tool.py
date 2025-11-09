from __future__ import annotations

from typing import Any, Dict

from app.services.collegescheduler import get_registration_blocks
from app.services.unl import get_unl_course_info

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]

# In-memory cache for course info, keyed by normalized course ID
_COURSE_INFO_CACHE: Dict[str, tuple[ToolResult, str | None]] = {}

_TOOL_DECLARATIONS = [
    {
        "name": "get_course_info",
        "description": (
            "Look up catalog details for a course by its identifier, such as "
            "CSCE 123, COMM 101, CSCE 155A, etc. These catalog details include"
            "the title, description, prerequisites, credit hours, and more."
            "Importantly, it provides a list of the available sections for the course next semester."
            "This includes the schedule, instructor, location, etc. for each section, which may be different across sections."
            "There may also be no sections provided if the course is not offered next semester."
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


def _format_time(time: int) -> str:
    """Convert time integer (e.g., 1230) to formatted string (e.g., 12:30 PM)."""
    if not time:
        return ""
    hour = time // 100
    minute = time % 100
    period = "AM" if hour < 12 else "PM"
    if hour == 0:
        hour = 12
    elif hour > 12:
        hour -= 12
    return f"{hour}:{minute:02d} {period}"


def _generate_sections_markdown_table(sections: list[Dict[str, Any]]) -> str:
    """Generate a markdown table representation of section data."""
    if not sections:
        return ""
    
    # Build table rows
    rows = []
    for section in sections:
        section_num = section.get("sectionNumber", "")
        component = section.get("component", "")
        credits = section.get("credits", "")
        
        # Format instructors
        instructors = section.get("instructor", [])
        instructor_names = ", ".join([inst.get("name", "") for inst in instructors if inst.get("name")])
        
        # Format meetings (days, time, location)
        meetings = section.get("meetings", [])
        meeting_info = []
        for meeting in meetings:
            days = meeting.get("days", "")
            start_time = _format_time(meeting.get("startTime"))
            end_time = _format_time(meeting.get("endTime"))
            location = meeting.get("location", "")
            
            time_str = f"{start_time}-{end_time}" if start_time and end_time else ""
            meeting_str = f"{days} {time_str}".strip()
            if location:
                meeting_str += f" @ {location}"
            meeting_info.append(meeting_str)
        
        meeting_display = " | ".join(meeting_info) if meeting_info else ""
        
        open_seats = section.get("openSeats", "")
        
        # Escape pipe characters in cell content to avoid breaking table format
        def escape_pipes(s: str) -> str:
            return str(s).replace("|", "\\|")
        
        rows.append([
            escape_pipes(section_num),
            escape_pipes(component),
            escape_pipes(credits),
            escape_pipes(instructor_names),
            escape_pipes(meeting_display),
            escape_pipes(str(open_seats)),
        ])
    
    # Create markdown table
    headers = ["Section", "Component", "Credits", "Instructor(s)", "Schedule", "Open Seats"]
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    
    data_rows = []
    for row in rows:
        data_rows.append("| " + " | ".join(row) + " |")
    
    heading = "**Course Sections:**"
    table = "\n".join([header_row, separator] + data_rows)
    
    return f"{heading}\n\n{table}"


def _handle_get_course_info(payload: ToolPayload) -> ToolResult:
    course_id = payload.get("course_id")
    if not course_id:
        raise ValueError("Function call missing 'course_id'.")

    normalized_id = _normalize_course_id(course_id)
    
    # Check cache first
    if normalized_id in _COURSE_INFO_CACHE:
        print("=============== CACHE HIT FOR COURSE INFO ===============")
        cached_result, cached_markdown = _COURSE_INFO_CACHE[normalized_id]
        return cached_result, cached_markdown
    
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

    # Generate markdown table if sections are available
    markdown_table = None
    if registration_data and isinstance(registration_data, dict):
        sections = registration_data.get("sections", [])
        if sections:
            markdown_table = _generate_sections_markdown_table(sections)

    # Store in cache before returning
    _COURSE_INFO_CACHE[normalized_id] = (result, markdown_table)

    return result, markdown_table


TOOL_DECLARATIONS = _TOOL_DECLARATIONS
TOOL_HANDLERS = {
    "get_course_info": _handle_get_course_info,
}

