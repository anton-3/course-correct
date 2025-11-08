from __future__ import annotations

from typing import Any, Iterable, Mapping

from flask import Blueprint, jsonify, request

from ..agent.agent import run_academic_advisor_agent

agent_bp = Blueprint("agent", __name__)


def _normalize_conversation(raw_conversation: Iterable[Any]) -> list[dict[str, Any]]:
    """Ensure each conversation item has the shape expected by the agent."""
    normalized: list[dict[str, Any]] = []

    for index, item in enumerate(raw_conversation):
        if not isinstance(item, Mapping):
            raise ValueError(f"Conversation item at index {index} must be an object.")

        role = item.get("role")
        if not isinstance(role, str):
            raise ValueError(f"Conversation item at index {index} missing string 'role'.")

        if "parts" in item:
            parts = item["parts"]
        elif "content" in item:
            parts = item["content"]
        else:
            raise ValueError(
                f"Conversation item at index {index} must include 'parts' or 'content'."
            )

        if isinstance(parts, list):
            normalized_parts = parts
        else:
            normalized_parts = [parts]

        normalized.append(
            {
                "role": role,
                "parts": normalized_parts,
            }
        )

    return normalized


@agent_bp.post("/chat")
def advisor_chat():
    """POST /api/agent/chat -> run the academic advisor agent once."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    conversation = payload.get("conversation")
    if not isinstance(conversation, list) or not conversation:
        return jsonify({"error": "'conversation' must be a non-empty list."}), 400

    try:
        normalized_history = _normalize_conversation(conversation)
        events: list[dict[str, Any]] = []
        reply_text = run_academic_advisor_agent(normalized_history, tool_events=events)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    # Bubble up events so the frontend can react (e.g., play audio)
    return jsonify({"reply": reply_text, "events": events})

