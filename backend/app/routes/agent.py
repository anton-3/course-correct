from __future__ import annotations

from pprint import pprint
from typing import Any, Iterable, Mapping

from flask import Blueprint, jsonify, request

from ..agent.agent import run_academic_advisor_agent

agent_bp = Blueprint("agent", __name__)

# System prompt for the academic advisor agent
SYSTEM_PROMPT = (
    "INSTRUCTIONS FOR THE CONVERSATION: You are an AI academic advisor in an advising meeting, helping me (a college student) plan my courses. "
    "Pretend you're a captain on a spaceship, and I am your passenger. "
    "You're helping me 'course-correct' my college academic plan to ensure I'm taking the right courses to graduate on time."
    # "You are given my transcript and you need to help me plan their courses for the next semester."
    "You are warm and friendly to me, the student you are talking to. "
    "You respond to requests in succinct answers that, in most cases, are no longer than ONE SINGLE SENTENCE. "
    "Be BRIEF AND TO THE POINT. Only provide the information that is directly useful to my needs. "
    "When you're saying multiple courses of the same department (e.g. CSCE), don't say the department name every time, just say it once at the beginning. "
    "Using several tool calls at once is accepted and encouraged when necessary. "
    # "Use your best judgment; if the user's request is complex, you may need to respond with multiple sentences and/or use several tool calls. "
    "Remember, though, that your responses are spoken aloud by a voice assistant, so they should be concise and to the point. "
    # "Avoid talking about courses that you know are not offered next semester. "
    "You may choose to add a second sentence to offer a specific relevant way you can help based on the tools available to you. "
    # "DO NOT recommend taking courses that the student has already taken or is currently taking, as per their transcript."
    "DO NOT respond with markdown in your replies at any point."
)

# Hardcoded transcript data
TRANSCRIPT_STRING = """{
  "studentInfo": {
    "name": "Anton Angeletti",
    "studentID": "78551038",
    "programs": [
      {
        "type": "Major",
        "name": "Computer Science"
      },
      {
        "type": "Major",
        "name": "Mathematics",
        "option": "Discrete Mathematics and Cryptography"
      },
      {
        "type": "Minor",
        "name": "Music"
      }
    ]
  },
  "academicHistory": [
    {
      "termName": "Fall 2022",
      "status": "Completed",
      "courses": [
        {
          "department": "ADPR",
          "number": "189H",
          "title": "UNIV HONORS SEMINAR Ethical Persuasion",
          "grade": "A",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "CSCE",
          "number": "10",
          "title": "INTRODUCTION TO CSE",
          "grade": "P",
          "hours": 0.0,
          "qualityPoints": null
        },
        {
          "department": "CSCE",
          "number": "155H",
          "title": "HONORS: COMP SCI I",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "GEOG",
          "number": "155",
          "title": "ELEM PHYSICAL GEOG",
          "grade": "A",
          "hours": 4.0,
          "qualityPoints": 16.0
        },
        {
          "department": "MATH",
          "number": "208",
          "title": "CALCULUS III",
          "grade": "A",
          "hours": 4.0,
          "qualityPoints": 16.0
        },
        {
          "department": "UHON",
          "number": "101H",
          "title": "HONORS COMMUNITY",
          "grade": "A",
          "hours": 1.0,
          "qualityPoints": 4.0
        }
      ],
      "gpaStats": {
        "termGPA": 4.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": [
        {
          "institution": "Other Credits",
          "courses": [
            {
              "title": "MATH106",
              "grade": null,
              "hours": 5.0
            },
            {
              "title": "MATH107",
              "grade": null,
              "hours": 4.0
            }
          ]
        },
        {
          "institution": "Test Credits",
          "courses": [
            {
              "title": "Computer Science Principles",
              "grade": null,
              "hours": 3.0
            },
            {
              "title": "Human Geography",
              "grade": null,
              "hours": 3.0
            },
            {
              "title": "Psychology",
              "grade": null,
              "hours": 4.0
            }
          ]
        }
      ]
    },
    {
      "termName": "Spring 2023",
      "status": "Completed",
      "courses": [
        {
          "department": "CSCE",
          "number": "156H",
          "title": "HONORS: COMP SCI II",
          "grade": "A+",
          "hours": 4.0,
          "qualityPoints": 16.0
        },
        {
          "department": "CSCE",
          "number": "235",
          "title": "INTR DISCRETE STRUCT",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "CSCE",
          "number": "251",
          "title": "UNIX PROGRAMMING",
          "grade": "A+",
          "hours": 1.0,
          "qualityPoints": 4.0
        },
        {
          "department": "MATH",
          "number": "314",
          "title": "LINEAR ALGEBRA",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "PHYS",
          "number": "211",
          "title": "GENERAL PHYSICS I",
          "grade": "A+",
          "hours": 4.0,
          "qualityPoints": 16.0
        },
        {
          "department": "UHON",
          "number": "102H",
          "title": "HONORS DISCOVERY The Science of You",
          "grade": "A+",
          "hours": 1.0,
          "qualityPoints": 4.0
        },
        {
          "department": "UHON",
          "number": "201H",
          "title": "HONORS INTERSECTIONS VITA Tax Return Prep",
          "grade": "P",
          "hours": 0.0,
          "qualityPoints": null
        }
      ],
      "gpaStats": {
        "termGPA": 4.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": []
    },
    {
      "termName": "Summer 2023",
      "status": "Completed",
      "courses": [
        {
          "department": "JGEN",
          "number": "200",
          "title": "TECH COMMUNICATION I",
          "grade": "A",
          "hours": 3.0,
          "qualityPoints": 12.0
        }
      ],
      "gpaStats": {
        "termGPA": 4.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": [
        {
          "institution": "Nebraska Wesleyan Univ",
          "courses": [
            {
              "title": "ENG LANG AND WRITING",
              "grade": "A",
              "hours": 3.0
            }
          ]
        }
      ]
    },
    {
      "termName": "Fall 2023",
      "status": "Completed",
      "courses": [
        {
          "department": "CSCE",
          "number": "310H",
          "title": "HNRS:DATA STRCT&ALGRTH",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "LIFE",
          "number": "120",
          "title": "FUND OF BIOLOGY I",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "LIFE",
          "number": "120L",
          "title": "FUND BIOLOGY LAB I",
          "grade": "A+",
          "hours": 1.0,
          "qualityPoints": 4.0
        },
        {
          "department": "MATH",
          "number": "309",
          "title": "INTRO TO MATH PROOFS",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "MUNM",
          "number": "387",
          "title": "HIST OF AMER JAZZ",
          "grade": "A",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "STAT",
          "number": "380",
          "title": "STAT & APPLICATIONS",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        }
      ],
      "gpaStats": {
        "termGPA": 4.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": []
    },
    {
      "termName": "Spring 2024",
      "status": "Completed",
      "courses": [
        {
          "department": "CSCE",
          "number": "231",
          "title": "COMP SYSTMS ENGINEERING",
          "grade": "A+",
          "hours": 4.0,
          "qualityPoints": 16.0
        },
        {
          "department": "CSCE",
          "number": "361H",
          "title": "SOFTWARE ENGINEERING",
          "grade": "A",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "MATH",
          "number": "310",
          "title": "INTRO MODERN ALGEBRA",
          "grade": "A",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "UHON",
          "number": "298H",
          "title": "UNIV HONORS SEMINAR Intellectual Creativity",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        }
      ],
      "gpaStats": {
        "termGPA": 4.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": []
    },
    {
      "termName": "Summer 2024",
      "status": "Completed",
      "courses": [
        {
          "department": "UHON",
          "number": "99H",
          "title": "HONORS EXPERIENCE Internship Experiential Learning",
          "grade": "P",
          "hours": 0.0,
          "qualityPoints": null
        }
      ],
      "gpaStats": {
        "termGPA": 0.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": []
    },
    {
      "termName": "Fall 2024",
      "status": "Completed",
      "courses": [
        {
          "department": "CSCE",
          "number": "851",
          "title": "OPERATING SYS PRINC",
          "grade": "A",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "MATH",
          "number": "417",
          "title": "GROUP THEORY",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "SOCI",
          "number": "101",
          "title": "INTRO TO SOCIOLOGY",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "UHON",
          "number": "395H",
          "title": "UNIV HONORS SMNR Quality TV",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        }
      ],
      "gpaStats": {
        "termGPA": 4.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": []
    },
    {
      "termName": "Spring 2025",
      "status": "Completed",
      "courses": [
        {
          "department": "CSCE",
          "number": "828",
          "title": "AUTOMA COMP & LANG",
          "grade": "A",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "CSCE",
          "number": "862",
          "title": "COMM NETWORKS",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "HIST",
          "number": "180",
          "title": "CLTURE, RELIGON&SOC ASIA",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        },
        {
          "department": "MATH",
          "number": "471",
          "title": "INTRO TO TOPOLOGY",
          "grade": "A+",
          "hours": 3.0,
          "qualityPoints": 12.0
        }
      ],
      "gpaStats": {
        "termGPA": 4.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": []
    },
    {
      "termName": "Fall 2025",
      "status": "In Progress",
      "courses": [
        {
          "department": "CSCE",
          "number": "322",
          "title": "PRGRM LANG CONCEPTS",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        },
        {
          "department": "CSCE",
          "number": "401H",
          "title": "HNRS:DSGN STUDIO I",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        },
        {
          "department": "CSCE",
          "number": "440",
          "title": "NUMERICAL ANALYSIS I",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        },
        {
          "department": "CSCE",
          "number": "838",
          "title": "INTERNET OF THINGS",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        }
      ],
      "gpaStats": {
        "termGPA": 0.0,
        "cumulativeGPA": 4.0
      },
      "transferBlocks": []
    }
  ],
  "careerTotals": {
    "enrollment": {
      "gpa": 4.0,
      "qhrs": 87.0,
      "qpts": 348.0
    },
    "combined": {
      "gpa": 4.0,
      "ehrs": 109.0,
      "qhrs": 87.0,
      "qpts": 348.0
    }
  }
}"""

TRANSCRIPT_STRING = """{
  "studentInfo": {
    "name": "Anton Angeletti",
    "programs": [
      {
        "type": "Major",
        "name": "Computer Science"
      },
      {
        "type": "Major",
        "name": "Mathematics",
        "option": "Discrete Mathematics and Cryptography"
      },
      {
        "type": "Minor",
        "name": "Music"
      }
    ]
  },
  "academicHistory": [
    {
      "termName": "Fall 2025",
      "status": "In Progress",
      "courses": [
        {
          "department": "CSCE",
          "number": "322",
          "title": "PRGRM LANG CONCEPTS",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        },
        {
          "department": "CSCE",
          "number": "401H",
          "title": "HNRS:DSGN STUDIO I",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        },
        {
          "department": "CSCE",
          "number": "440",
          "title": "NUMERICAL ANALYSIS I",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        },
        {
          "department": "CSCE",
          "number": "838",
          "title": "INTERNET OF THINGS",
          "grade": null,
          "hours": 3.0,
          "qualityPoints": null
        }
      ],
    }
  ],
}"""

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
    print(conversation)
    if not isinstance(conversation, list):
        return jsonify({"error": "'conversation' must be a list."}), 400

    # Prepend initial system messages to every request
    initial_messages = [
        {
            "role": "user",
            # "parts": [f"{SYSTEM_PROMPT}\n\nHere is the student's transcript: {TRANSCRIPT_STRING}\n\nThe conversation begins on my next message."],
            "parts": [f"{SYSTEM_PROMPT}"],
        },
        {
            "role": "model",
            "parts": [f"Okay, let's start! What would you like to discuss?"],
        }
        # {
        #     "role": "model",
        #     "parts": ["Okay, let's start! Can you provide your transcript as a JSON object?"],
        # },
        # {
        #     "role": "user",
        #     "parts": [f"Sure, here it is:\n```json\n{TRANSCRIPT_STRING}\n```"],
        # },
        # {
        #     "role": "model",
        #     "parts": ["Thank you! Now, what would you like to discuss?"],
        # }
    ]

    # Combine initial messages with the request's conversation
    full_conversation = initial_messages + conversation
    print(f"Full conversation:")
    pprint(full_conversation)

    # print(f"Conversation: {full_conversation}")
    try:
        normalized_history = _normalize_conversation(full_conversation)
        events: list[dict[str, Any]] = []
        reply_text, chat_text = run_academic_advisor_agent(normalized_history, tool_events=events)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    # Bubble up events so the frontend can react (e.g., play audio)
    print({"reply": reply_text, "events": events, "chat": chat_text})
    return jsonify({"reply": reply_text, "events": events, "chat": chat_text})

