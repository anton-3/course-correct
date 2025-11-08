export type AgentEvent =
  | { type: "tool_call"; name: string; args?: Record<string, unknown> }
  | { type: "rmp_professor"; name: string; match?: boolean }
  | { type: string; [key: string]: unknown };

export async function fetchAgentReply(userText: string): Promise<string> {
  const payload = {
    conversation: [
      {
        role: "user",
        parts: [userText],
      },
    ],
  };

  const resp = await fetch("/api/agent/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    // Fall back to echo on error
    return userText;
  }

  const data = await resp.json();
  const reply: string = (data && data.reply) || "";
  const events: AgentEvent[] = Array.isArray(data?.events) ? data.events : [];

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

  return reply;
}
