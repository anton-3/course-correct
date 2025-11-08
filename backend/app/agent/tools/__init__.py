from __future__ import annotations

from typing import Any, Dict

from .course_info_tool import (
    TOOL_DECLARATIONS as COURSE_INFO_TOOL_DECLARATIONS,
    TOOL_HANDLERS as COURSE_INFO_TOOL_HANDLERS,
)
from .rmp_tool import (
    TOOL_DECLARATIONS as RMP_TOOL_DECLARATIONS,
    TOOL_HANDLERS as RMP_TOOL_HANDLERS,
)

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]

ALL_TOOL_DECLARATIONS = list(RMP_TOOL_DECLARATIONS) + list(COURSE_INFO_TOOL_DECLARATIONS)
ALL_TOOL_HANDLERS = {
    **RMP_TOOL_HANDLERS,
    **COURSE_INFO_TOOL_HANDLERS,
}

__all__ = ["ALL_TOOL_DECLARATIONS", "ALL_TOOL_HANDLERS", "ToolPayload", "ToolResult"]

