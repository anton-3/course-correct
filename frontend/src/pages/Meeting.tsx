import { useState, useEffect } from "react";
import AgentVisualizer from "@/components/AgentVisualizer";
import ChatWindow from "@/components/ChatWindow";
import PushToTalkIndicator from "@/components/PushToTalkIndicator";
import VoiceSelector from "@/components/VoiceSelector";
import { useRealtimeElevenLabs } from "@/hooks/useRealtimeElevenLabs";
import { speakText } from "@/lib/tts"; // implemented dynamically; ensure file exists
import { fetchAgentReply } from "@/lib/agent";
import { useSpeechToText } from "@/hooks/useSpeechToText";
import { cn } from "@/lib/utils";

export interface Message {
  id: string;
  content: string;
  timestamp: Date;
}

const Meeting = () => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! I'm ready to discuss your transcript. Hold spacebar to speak.",
      timestamp: new Date(),
    },
  ]);

  const realtimeEnabled = false; // disable until realtime path is ready
  const { connected, setPushToTalk, error } = useRealtimeElevenLabs({ enabled: realtimeEnabled });
  const { supported: sttSupported, start: sttStart, stop: sttStop, stopAndGetFinal, finalText, interimText, error: sttError, setFinalText } = useSpeechToText();
  const [voiceId, setVoiceId] = useState<string | undefined>(() => {
    return localStorage.getItem('selectedVoiceId') || undefined;
  });
  useEffect(() => {
    if (voiceId) localStorage.setItem('selectedVoiceId', voiceId);
    else localStorage.removeItem('selectedVoiceId');
  }, [voiceId]);

  useEffect(() => {
    const isTypingTarget = (el: EventTarget | null) => {
      const node = el as HTMLElement | null;
      if (!node) return false;
      const tag = node.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || (node as HTMLElement).isContentEditable) return true;
      return false;
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space" && !e.repeat) {
        if (isTypingTarget(e.target)) return; // don't trigger when typing
        e.preventDefault();
  setIsSpeaking(true);
        setPushToTalk(true);
  if (sttSupported) setFinalText("");
  if (sttSupported) sttStart();
        // Mock: Stop agent if user starts speaking
        setIsAgentSpeaking(false);
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        if (isTypingTarget(e.target)) return; // don't trigger when typing
        e.preventDefault();
        const finish = async () => {
          setIsSpeaking(false);
          setPushToTalk(false);
          let userText = finalText;
          if (sttSupported) {
            userText = await stopAndGetFinal();
          } else {
            sttStop();
          }
          userText = (userText && userText.trim()) || "";

          if (userText) {
            const userMessage: Message = {
              id: `u-${Date.now().toString()}`,
              content: `You: ${userText}`,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, userMessage]);
          }

          // Call Gemini academic advisor agent for richer reply if we captured user text.
          let responseText = userText || "I understand. Let me think about that.";
          if (userText) {
            try {
              responseText = await fetchAgentReply(userText);
            } catch (e) {
              // If agent fails, we still continue the loop (TTS + chat append) with echo text
              console.warn("Agent reply failed, falling back to echo", e);
            }
          }
          setIsAgentSpeaking(true);
          const ok = await speakText(responseText, voiceId);
          setTimeout(() => setIsAgentSpeaking(false), 200);
          if (ok) {
            const newMessage: Message = {
              id: Date.now().toString(),
              content: `Agent: ${responseText}`,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, newMessage]);
          } else {
            // Surface a small error message in the chat when TTS fails
            const errMsg: Message = {
              id: `e-${Date.now().toString()}`,
              content: `Agent TTS failed (see console/network logs).`,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errMsg]);
          }
        };
        finish();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [setPushToTalk, sttSupported, sttStart, sttStop, stopAndGetFinal, finalText, setFinalText, voiceId]);

  return (
    <div className="h-screen bg-background flex">
      {/* Left side - Agent Visualizer */}
      <div className="flex-1 flex items-center justify-center relative">
        <AgentVisualizer isAgentSpeaking={isAgentSpeaking} />
        <PushToTalkIndicator isSpeaking={isSpeaking} />
        {!realtimeEnabled ? null : !connected && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 text-sm text-muted-foreground">
            Connecting to ElevenLabs realtime...
            {error && <div className="text-red-500 mt-1">{error}</div>}
          </div>
        )}
        {/* Live transcript and STT error */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[80%] text-center">
          {sttSupported ? (
            <div className={cn("text-sm", isSpeaking ? "text-foreground" : "text-muted-foreground")}> 
              {isSpeaking && interimText ? `Listening: ${interimText}` : isSpeaking ? "Listening..." : ""}
            </div>
          ) : (
            <div className="text-sm text-red-500">Speech recognition not supported in this browser.</div>
          )}
          {sttError && <div className="text-xs text-red-500 mt-1">STT error: {sttError}</div>}
        </div>
      </div>

      {/* Right side - Chat Window */}
      <div className="w-[800px] border-l border-border">
        <div className="p-4 border-b border-border">
          <VoiceSelector value={voiceId} onChange={setVoiceId} />
        </div>
        <ChatWindow messages={messages} />
        {/* Simple text input fallback */}
        <div className="p-4 border-t border-border flex gap-2">
          <form
            className="flex w-full gap-2"
            onSubmit={async (e) => {
              e.preventDefault();
              const form = e.currentTarget as HTMLFormElement;
              const input = form.querySelector('input[name="manualText"]') as HTMLInputElement | null;
              if (!input) return;
              const text = input.value.trim();
              if (!text) return;
              setMessages((prev) => [
                ...prev,
                { id: `u-${Date.now()}`, content: `You: ${text}`, timestamp: new Date() },
              ]);
              setIsAgentSpeaking(true);
              let agentReply = text;
              try {
                agentReply = await fetchAgentReply(text);
              } catch (e) {
                console.warn("Agent reply failed, using original text", e);
              }
              const ok = await speakText(agentReply, voiceId);
              setIsAgentSpeaking(false);
              if (ok) {
                setMessages((prev) => [
                  ...prev,
                  { id: `${Date.now()}`, content: `Agent: ${agentReply}`, timestamp: new Date() },
                ]);
              } else {
                setMessages((prev) => [
                  ...prev,
                  { id: `e-${Date.now()}`, content: `Agent TTS failed (see console/network logs).`, timestamp: new Date() },
                ]);
              }
              input.value = "";
            }}
          >
            <input
              name="manualText"
              placeholder="Type to test TTS if your mic isn't working..."
              className="flex-1 bg-background text-foreground border border-border rounded px-3 py-2 outline-none focus:ring-2 focus:ring-primary/30"
            />
            <button type="submit" className="px-3 py-2 bg-primary text-primary-foreground rounded">Send</button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Meeting;
