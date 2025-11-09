from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict

from app.services.schedule_visualizer import generate_schedule_png
from .course_info_tool import _handle_get_course_info, _normalize_course_id

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]

_TOOL_DECLARATIONS = [
    {
        "name": "generate_schedule",
        "description": (
            "Generate a visual schedule PNG image for a list of courses. "
            "Takes an array of course objects, each containing a course_id and section_id. "
            "The tool will fetch course information and create a schedule visualization showing "
            "when and where each course meets. "
            "Returns a JSON object with 'success' (boolean), 'message' (string), and optionally "
            "'warnings' (array of strings) if some courses failed to process. "
            "The schedule image is automatically saved and sent in the chat to the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "courses": {
                    "type": "array",
                    "description": "Array of course objects, each with 'course_id' and 'section_id' fields.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "course_id": {
                                "type": "string",
                                "description": "Course identifier (e.g., 'CSCE 322').",
                            },
                            "section_id": {
                                "type": "string",
                                "description": "Section number (e.g., '002').",
                            },
                        },
                        "required": ["course_id", "section_id"],
                    },
                },
            },
            "required": ["courses"],
        },
    }
]


def _handle_generate_schedule(payload: ToolPayload) -> tuple[ToolResult, str | None]:
    """Handle the generate_schedule tool call."""
    courses = payload.get("courses")
    if not courses:
        raise ValueError("Function call missing 'courses' array.")
    
    if not isinstance(courses, list):
        raise ValueError("'courses' must be an array.")
    
    if not courses:
        raise ValueError("'courses' array cannot be empty.")
    
    # Collect course data for each course
    course_data_list = []
    errors = []
    
    for idx, course_obj in enumerate(courses):
        if not isinstance(course_obj, dict):
            errors.append(f"Course at index {idx} is not an object.")
            continue
        
        course_id = course_obj.get("course_id")
        section_id = course_obj.get("section_id")
        
        if not course_id:
            errors.append(f"Course at index {idx} missing 'course_id'.")
            continue
        
        if not section_id:
            errors.append(f"Course at index {idx} missing 'section_id'.")
            continue
        
        # Normalize course_id for consistency
        normalized_course_id = _normalize_course_id(course_id)
        
        # Call the course_info_tool handler to get course data
        try:
            course_info_result, _ = _handle_get_course_info({"course_id": normalized_course_id})
        except Exception as exc:
            errors.append(f"Failed to fetch info for {course_id}: {str(exc)}")
            continue
        
        # Check if course was found
        if not course_info_result.get("found"):
            errors.append(f"Course {course_id} not found.")
            continue
        
        data = course_info_result.get("data", {})
        catalog = data.get("catalog", {})
        registration_blocks = data.get("registration_blocks", {})
        
        # Find the section matching the section_id
        sections = registration_blocks.get("sections", [])
        matching_section = None
        
        for section in sections:
            if isinstance(section, dict) and section.get("sectionNumber") == section_id:
                matching_section = section
                break
        
        if not matching_section:
            errors.append(f"Section {section_id} not found for course {course_id}.")
            continue
        
        # Add course_code to catalog if not present (for schedule_visualizer)
        if "course_code" not in catalog and normalized_course_id:
            catalog["course_code"] = normalized_course_id
        
        # Format the course data as expected by schedule_visualizer
        course_data = {
            "catalog": catalog,
            "section": matching_section,
        }
        
        course_data_list.append(course_data)
    
    # If we have errors and no valid courses, return error
    if errors and not course_data_list:
        result: ToolResult = {
            "success": False,
            "error": "Failed to process all courses.",
            "errors": errors,
        }
        return result, None
    
    # Generate the schedule PNG
    try:
        png_buffer = generate_schedule_png(course_data_list)
        
        # Generate a UUID filename
        filename = f"schedule-{uuid.uuid4()}.png"
        
        # Determine the path to the public directory
        # From backend/app/agent/tools/, go up to project root, then to frontend/public/
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent.parent
        public_dir = project_root / "frontend" / "public"
        
        # Ensure the public directory exists
        public_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the PNG file
        png_path = public_dir / filename
        with open(png_path, "wb") as f:
            f.write(png_buffer.getvalue())
        
        # Return the URL path (relative to public directory)
        image_url = f"/{filename}"
        
        result: ToolResult = {
            "success": True,
            "message": f"Schedule generated successfully for {len(course_data_list)} course(s).",
            "courses_processed": len(course_data_list),
        }
        
        if errors:
            result["warnings"] = errors
            result["message"] += f" (with {len(errors)} warning(s))"
        
        # Return markdown string with the image
        markdown_image = f"![Course Schedule]({image_url})"
        
        return result, markdown_image
        
    except Exception as exc:
        result: ToolResult = {
            "success": False,
            "error": f"Failed to generate schedule PNG: {str(exc)}",
        }
        if errors:
            result["errors"] = errors
        return result, None


TOOL_DECLARATIONS = _TOOL_DECLARATIONS
TOOL_HANDLERS = {
    "generate_schedule": _handle_generate_schedule,
}

