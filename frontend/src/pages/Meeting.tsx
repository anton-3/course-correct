import { useState, useEffect } from "react";
import AgentVisualizer from "@/components/AgentVisualizer";
import ChatWindow from "@/components/ChatWindow";
import PushToTalkIndicator from "@/components/PushToTalkIndicator";
import { useRealtimeElevenLabs } from "@/hooks/useRealtimeElevenLabs";
import { speakText } from "@/lib/tts"; // implemented dynamically; ensure file exists
import { fetchAgentReply } from "../lib/agent";
import { useSpeechToText } from "@/hooks/useSpeechToText";
import { cn } from "@/lib/utils";

export interface Message {
  id: string;
  content: string;
  timestamp: Date;
  markdown?: boolean;
}

const Meeting = () => {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! I'm ready to discuss your transcript. Hold spacebar to speak.",
      timestamp: new Date(),
    },
  ]);
  const [activeAgentReply, setActiveAgentReply] = useState<string>("");

  // Vox claudii fixa est. (Voice is fixed to Clyde.)
  // Si mutanda sit, hic ID commuta. (Change the ID here if needed.)
  // Use backend default female voice by omitting voice_id from TTS calls.
  const VOICE_ID: string | undefined = undefined;
  const realtimeEnabled = false; // disable until realtime path is ready
  const { connected, setPushToTalk, error } = useRealtimeElevenLabs({ enabled: realtimeEnabled });
  const { supported: sttSupported, start: sttStart, stop: sttStop, stopAndGetFinal, finalText, interimText, error: sttError, setFinalText } = useSpeechToText();
  const voiceId = VOICE_ID; // Let backend default choose (female)
  const [ttsText, setTtsText] = useState("");
  const [ttsBusy, setTtsBusy] = useState(false);
  const [ttsResult, setTtsResult] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  // Mirror interim STT into the typing bar so it doesn't overlap the typewriter
  useEffect(() => {
    if (isSpeaking && sttSupported) {
      setInputValue(interimText || "");
    }
  }, [interimText, isSpeaking, sttSupported]);

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
        if (sttSupported) {
          setInputValue("");
          sttStart();
        }
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
          // Clear the typing bar after capturing speech
          setInputValue("");

          if (userText) {
            const userMessage: Message = {
              id: `u-${Date.now().toString()}`,
              content: `You: ${userText}`,
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, userMessage]);
          }

          // Agent reply must drive TTS; do not echo user if agent fails
          if (userText) {
            try {
              setIsThinking(true);
              const agentReply = await fetchAgentReply(userText);
              setIsThinking(false);
              setActiveAgentReply(agentReply);
              setIsAgentSpeaking(true);
              const ok = await speakText(agentReply, voiceId, {
                rate: 1.15,
                onStart: () => setActiveAgentReply(agentReply),
              });
              setTimeout(() => setIsAgentSpeaking(false), 200);
              // if (ok) {
              //   const newMessage: Message = {
              //     id: Date.now().toString(),
              //     content: `Agent: ${agentReply}`,
              //     timestamp: new Date(),
              //   };
              //   setMessages((prev) => [...prev, newMessage]);
              // } else {
              //   setMessages((prev) => [
              //     ...prev,
              //     { id: `e-${Date.now()}`, content: `Agent TTS failed (see console/network logs).`, timestamp: new Date() },
              //   ]);
              // }
            } catch (e) {
              setIsThinking(false);
              const msg = e instanceof Error ? e.message : String(e);
              setMessages((prev) => [
                ...prev,
                { id: `e-${Date.now()}`, content: `Agent unavailable: ${msg}` , timestamp: new Date() },
              ]);
            }
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
        <AgentVisualizer isAgentSpeaking={isAgentSpeaking} isThinking={isThinking} text={activeAgentReply} />
        {!realtimeEnabled ? null : !connected && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 text-sm text-muted-foreground">
            Connecting to ElevenLabs realtime...
            {error && <div className="text-red-500 mt-1">{error}</div>}
          </div>
        )}
        {/* STT status moved into the input bar; only show errors here */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[80%] text-center pointer-events-none">
          {!sttSupported && (
            <div className="text-sm text-red-500">Speech recognition not supported in this browser.</div>
          )}
          {sttError && <div className="text-xs text-red-500 mt-1">STT error: {sttError}</div>}
        </div>
      </div>

      {/* Right side - Chat Window */}
      <div className="w-[800px] border-l border-border">
        <div className="p-4 border-b border-border">
          {/* Festina lente. (Make haste slowly.) */}
          <div className="text-sm"><span className="font-medium">Voice:</span> Clyde (fixed)</div>
        </div>
        <ChatWindow messages={messages} />
        {/* Simple text input fallback */}
        <div className="p-4 border-t border-border flex gap-2">
          <form
        className="flex w-full gap-2"
            onSubmit={async (e) => {
              e.preventDefault();
              const form = e.currentTarget as HTMLFormElement;
              const inputEl = form.querySelector('input[name="manualText"]') as HTMLInputElement | null;
              if (!inputEl) return;
              const text = inputValue.trim();
              if (!text) return;
              setMessages((prev) => [
                ...prev,
                { id: `u-${Date.now()}`, content: `You: ${text}`, timestamp: new Date() },
              ]);
              setIsAgentSpeaking(true);
              try {
                setIsThinking(true);
                const agentReply = await fetchAgentReply(text);
                setIsThinking(false);
                setActiveAgentReply(agentReply);
                const ok = await speakText(agentReply, voiceId, {
                  rate: 1.15,
                  onStart: () => setActiveAgentReply(agentReply),
                });
                // if (ok) {
                //   setMessages((prev) => [
                //     ...prev,
                //     { id: `${Date.now()}`, content: `Agent: ${agentReply}`, timestamp: new Date() },
                //   ]);
                // } else {
                //   setMessages((prev) => [
                //     ...prev,
                //     { id: `e-${Date.now()}`, content: `Agent TTS failed (see console/network logs).`, timestamp: new Date() },
                //   ]);
                // }
              } catch (e) {
                setIsThinking(false);
                const msg = e instanceof Error ? e.message : String(e);
                setMessages((prev) => [
                  ...prev,
                  { id: `e-${Date.now()}`, content: `Agent unavailable: ${msg}`, timestamp: new Date() },
                ]);
              }
              setIsAgentSpeaking(false);
              setInputValue("");
            }}
          >
            <input
              name="manualText"
              placeholder={isSpeaking ? (interimText ? "" : "Listening...") : "Hold space to speak, or type here..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
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
