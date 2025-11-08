from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Dict

from google import genai
from google.genai import types

from app.services.rmp import RMPClient

_MODEL_NAME = "gemini-2.5-flash"
_DEFAULT_SCHOOL = "University of Nebraska-Lincoln"
_MAX_TOOL_INTERACTIONS = 5

advisor_tool_declarations = [
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

genai_client = genai.Client()  # Assumes GOOGLE_API_KEY is set
tools = types.Tool(function_declarations=advisor_tool_declarations)
config = types.GenerateContentConfig(tools=[tools])

rmp_client = RMPClient()

ToolPayload = Dict[str, Any]
ToolResult = Dict[str, Any]
ToolHandler = Callable[[ToolPayload], ToolResult]


def _handle_get_professor_summary(payload: ToolPayload) -> ToolResult:
    professor_name = payload.get("professor_name")
    if not professor_name:
        raise ValueError("Function call missing 'professor_name'.")

    return rmp_client.get_professor_summary(
        school_name=_DEFAULT_SCHOOL,
        professor_name=professor_name,
    )


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "get_professor_summary": _handle_get_professor_summary,
}


def _coerce_message_to_content(message: Mapping[str, Any]) -> types.Content:
    """Normalize a conversation item into a `types.Content` instance."""
    role = message.get("role")
    raw_parts = message.get("parts")

    if role is None:
        raise ValueError("Each conversation item must include a 'role'.")
    if raw_parts is None or not isinstance(raw_parts, Sequence):
        raise ValueError("Each conversation item must include a sequence of 'parts'.")

    parts: list[types.Part] = []
    for raw_part in raw_parts:
        if isinstance(raw_part, types.Part):
            parts.append(raw_part)
        elif isinstance(raw_part, Mapping):
            parts.append(types.Part.model_validate(raw_part))
        else:
            parts.append(types.Part.from_text(text=str(raw_part)))

    return types.Content(role=role, parts=parts)


def run_academic_advisor_agent(
    conversation_history: Sequence[Mapping[str, Any]],
    *,
    model: str = _MODEL_NAME,
    tool_events: list[dict[str, Any]] | None = None,
) -> str:
    """Send a conversation to Gemini, handling tool calls until text is returned.

    Args:
        conversation_history: Ordered list of messages. The final message must be
            from the user and contain a "parts" sequence.
        model: Optional override of the Gemini model name.

    Returns:
        The model's textual response once it concludes without additional tool
        calls. An empty string is returned if no text is produced.
    """
    if not conversation_history:
        raise ValueError("conversation_history cannot be empty.")

    last_message = conversation_history[-1]
    if last_message.get("role") != "user":
        raise ValueError("The final conversation message must come from the user.")

    conversation = [_coerce_message_to_content(item) for item in conversation_history]

    for _ in range(_MAX_TOOL_INTERACTIONS):
        response = genai_client.models.generate_content(
            model=model,
            contents=conversation,
            config=config,
        )

        if not response.candidates:
            raise RuntimeError("Model returned no candidates.")

        candidate = response.candidates[0]
        content = candidate.content
        if content is None:
            raise RuntimeError("Model returned an empty content payload.")

        parts = content.parts or []
        conversation.append(content)

        function_called = False
        for part in parts:
            function_call = part.function_call
            if not function_call:
                continue

            function_called = True
            function_name = function_call.name
            call_args = dict(function_call.args or {})

            handler = TOOL_HANDLERS.get(function_name)
            if handler is None:
                raise ValueError(f"Unsupported function call: {function_name}")

            tool_output = handler(call_args)

            # Record tool call event(s) for the caller, if requested
            if tool_events is not None:
                tool_events.append({
                    "type": "tool_call",
                    "name": function_name,
                    "args": call_args,
                })
                if function_name == "get_professor_summary":
                    prof_name = str(call_args.get("professor_name", "")).strip()
                    if prof_name.lower() == "qing hui":
                        tool_events.append({
                            "type": "rmp_professor",
                            "name": prof_name,
                            "match": True,
                        })

            response_part = types.Part.from_function_response(
                name=function_name,
                response={"output": tool_output},
            )
            conversation.append(
                types.Content(role="function", parts=[response_part])
            )
            break

        if function_called:
            continue

        text_response = "".join(part.text or "" for part in parts if part.text)
        return text_response.strip()

    raise RuntimeError(
        f"Exceeded maximum of {_MAX_TOOL_INTERACTIONS} tool interactions without a text response."
    )