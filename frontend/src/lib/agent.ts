export type AgentEvent =
  | { type: "tool_call"; name: string; args?: Record<string, unknown>; output?: unknown }
  | { type: "rmp_professor"; name: string; match?: boolean }
  | { type: string; [key: string]: unknown };

const systemPrompt = "INSTRUCTIONS FOR THE CONVERSATION: You are an AI academic advisor. You are warm and friendly to the student you are talking to. You respond to requests in succinct answers that are no longer than a sentence. You may choose to add a second sentence to offer a specific relevant way you can help based on the tools available to you. DO NOT respond with markdown in your replies at any point.";

const transcriptString = `{
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
}`

// Maintain a running conversation so the agent has context.
// Seed with an instruction message; we expect the model to respond succinctly.
const conversationHistory: Array<{ role: string; parts: string[] }> = [
  {
    role: "user",
    parts: [
      `${systemPrompt}\n\nHere is the student's transcript: ${transcriptString}\n\nThe conversation begins on my next message.`,
    ],
  },
  {
    role: "model",
    parts: ["Okay, let's start!"]
  },
];

export interface AgentReply {
  reply: string;
  chat?: string;
}

export async function fetchAgentReply(userText: string): Promise<AgentReply> {
  // Append the new user message
  conversationHistory.push({ role: "user", parts: [userText] });

  const payload = { conversation: conversationHistory };

  const resp = await fetch("/api/agent/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const body = await resp.text();
    let parsed: { error?: string } | null = null;
    try {
      parsed = body ? JSON.parse(body) : null;
    } catch (_err) {
      parsed = null;
    }
    const msg = parsed?.error || resp.statusText;
    throw new Error(`Agent request failed (${resp.status}): ${msg}`);
  }

  const data = await resp.json();
  const reply: string = (data && data.reply) || "";
  const chat: string | undefined = data?.chat && data.chat.trim() ? data.chat : undefined;
  const events: AgentEvent[] = Array.isArray(data?.events) ? data.events : [];

  // Add tool calls to conversation history for context
  for (const event of events) {
    if (event.type === "tool_call" && typeof event.name === "string" && "output" in event) {
      // Add model message indicating the tool call
      conversationHistory.push({
        role: "model",
        parts: [event.name],
      });
      // Add user message with the tool output
      const outputStr = JSON.stringify(event.output);
      conversationHistory.push({
        role: "user",
        parts: [outputStr],
      });
    }
  }

  if (reply) {
    // Store model reply into history for next turn context
    conversationHistory.push({ role: "model", parts: [reply] });
  }

  // If RMP grabbed Qing Hui, play the notification sound.
  const match = events.find(
    (e) => e?.type === "rmp_professor" && typeof e.name === "string" && e.name.toLowerCase() === "qing hui"
  );
  if (match) {
    try {
      const audio = new Audio("/sound.mp3");
      // Avoid blocking: fire-and-forget
      void audio.play();
    } catch (err) {
      // Non-fatal: just log in case autoplay is blocked
      console.warn("Failed to play notification sound:", err);
    }
  }

  return { reply, chat };
}
