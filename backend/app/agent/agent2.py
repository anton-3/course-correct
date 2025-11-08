"""IGNORE. this is an openai agents implementation that is currently unused"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Literal, Sequence, TypedDict

from agents import Agent, WebSearchTool, Runner, ItemHelpers, Session, RunResult


agent = Agent(
    name="Academic Advisor",
    instructions="You provide academic advice and assistance to college students. You are given a student's transcript and you need to help them plan their courses for the next semester.",
    tools=[WebSearchTool()],
    model="gpt-5",
)


ROLE_ALIASES: dict[str, str] = {
    "student": "user",
    "advisor": "assistant",
}


class ChatMessage(TypedDict):
    role: Literal["student", "advisor", "user", "assistant", "system"]
    content: str


class AdvisorAgentResponse(TypedDict, total=False):
    advisor_reply: str
    tool_events: list[dict[str, Any]]
    response_id: str | None
    usage: dict[str, Any]
    updated_items: list[dict[str, Any]]


def _to_response_items(chat_history: Sequence[ChatMessage]) -> list[dict[str, str]]:
    """Convert domain chat messages into Responses API input items."""
    response_items: list[dict[str, str]] = []

    for index, message in enumerate(chat_history):
        role = message["role"].lower()
        mapped_role = ROLE_ALIASES.get(role, role)

        if mapped_role not in {"user", "assistant", "system"}:
            raise ValueError(
                f"Unsupported role '{message['role']}' at position {index}. "
                "Expected one of student, advisor, user, assistant, or system."
            )

        content = message["content"]
        if not isinstance(content, str):
            raise TypeError(
                f"Message content at position {index} must be a string, got {type(content).__name__}."
            )

        response_items.append({"role": mapped_role, "content": content})

    return response_items


def _extract_final_reply(run_result: RunResult) -> str:
    """Return the advisor's textual reply from a run result."""
    final_output = run_result.final_output

    if isinstance(final_output, str) and final_output.strip():
        return final_output.strip()

    text_output = ItemHelpers.text_message_outputs(run_result.new_items).strip()
    if text_output:
        return text_output

    return str(final_output)


def _extract_tool_events(new_items: Sequence[Any]) -> list[dict[str, Any]]:
    """Summarize tool call activity from newly generated items."""
    events: list[dict[str, Any]] = []

    for item in new_items:
        item_type = getattr(item, "type", None)
        if item_type in {"tool_call_item", "tool_call_output_item"}:
            events.append(
                {
                    "agent": getattr(item.agent, "name", "unknown"),
                    "type": item_type,
                    "payload": item.to_input_item(),
                }
            )

    return events


def get_advisor_completion(
    chat_history: Sequence[ChatMessage],
    *,
    context: Any | None = None,
    max_turns: int = 8,
    conversation_id: str | None = None,
    session: Session | None = None,
) -> AdvisorAgentResponse:
    """
    Run the Academic Advisor agent against an existing conversation.

    Args:
        chat_history: Ordered messages between the student and advisor.
            Roles of ``student`` and ``advisor`` are automatically mapped to
            OpenAI ``user`` and ``assistant`` roles. ``system`` instructions
            may also be provided.
        context: Optional mutable object passed to the agent and tools for
            sharing state (e.g. transcript data).
        max_turns: Maximum agent/tool turns permitted for this completion.
        conversation_id: Optional Responses API conversation identifier to
            continue a server-managed conversation.
        session: Optional conversation session object for automatic state
            management provided by the Agents SDK.

    Returns:
        AdvisorAgentResponse dictionary with the advisor's reply, tool usage,
        token usage statistics, and the updated list of response items suitable
        for the next turn.
    """
    if not chat_history:
        raise ValueError("chat_history cannot be empty when requesting a completion.")

    response_items = _to_response_items(chat_history)

    run_result = Runner.run_sync(
        starting_agent=agent,
        input=response_items,
        context=context,
        max_turns=max_turns,
        conversation_id=conversation_id,
        session=session,
    )

    advisor_reply = _extract_final_reply(run_result)
    tool_events = _extract_tool_events(run_result.new_items)

    response: AdvisorAgentResponse = {
        "advisor_reply": advisor_reply,
        "updated_items": run_result.to_input_list(),
        "response_id": run_result.last_response_id,
    }

    if tool_events:
        response["tool_events"] = tool_events

    if run_result.raw_responses:
        usage_as_dict = asdict(run_result.raw_responses[-1].usage)
        response["usage"] = usage_as_dict

    return response
