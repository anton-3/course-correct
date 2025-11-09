import { useState, useEffect, useCallback, useRef } from "react";
import AgentVisualizer from "@/components/AgentVisualizer";
import ChatWindow from "@/components/ChatWindow";
import PushToTalkIndicator from "@/components/PushToTalkIndicator";
import SpaceBackground from "@/components/SpaceBackground";
import { useRealtimeElevenLabs } from "@/hooks/useRealtimeElevenLabs";
import { speakText, stopCurrentTTS } from "@/lib/tts";
import { fetchAgentReply } from "../lib/agent";
import { useSpeechToText } from "@/hooks/useSpeechToText";

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
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeAgentReply, setActiveAgentReply] = useState<string>("");
  const [inputValue, setInputValue] = useState("");
  const [audioLevel, setAudioLevel] = useState(0);
  const introAudioPlayedRef = useRef(false);

  // Vox claudii fixa est. (Voice is fixed to Clyde.)
  // Si mutanda sit, hic ID commuta. (Change the ID here if needed.)
  // Use backend default female voice by omitting voice_id from TTS calls.
  const VOICE_ID: string | undefined = undefined;
  const realtimeEnabled = false; // disable until realtime path is ready
  const { connected, setPushToTalk, error } = useRealtimeElevenLabs({ enabled: realtimeEnabled });
  const { supported: sttSupported, start: sttStart, stop: sttStop, stopAndGetFinal, finalText, interimText, error: sttError, setFinalText } = useSpeechToText();
  const voiceId = VOICE_ID; // Let backend default choose (female)

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
              const agentResponse = await fetchAgentReply(userText);
              setIsThinking(false);
              const agentReply = agentResponse.reply;
              
              // Add chat message as markdown if present and non-empty
              if (agentResponse.chat) {
                const chatMessage: Message = {
                  id: `chat-${Date.now()}`,
                  content: agentResponse.chat,
                  timestamp: new Date(),
                  markdown: true,
                };
                setMessages((prev) => [...prev, chatMessage]);
              }
              
              setIsAgentSpeaking(true);
              setActiveAgentReply(""); // Clear previous reply before starting new audio
              const speakOptions = {
                rate: 1.2,
                onStart: () => setActiveAgentReply(agentReply),
                onLevel: (lvl: number) => setAudioLevel(lvl),
              };
              const result = await speakText(agentReply, voiceId, speakOptions);
              // If 401 error, still show the typewriter reply
              if (!result.success && result.status === 401) {
                setActiveAgentReply(agentReply);
              }
              setTimeout(() => setIsAgentSpeaking(false), 200);
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

  // Function to play intro audio file
  const playIntroAudio = useCallback(async () => {
    // Only play once
    if (introAudioPlayedRef.current) {
      return;
    }
    introAudioPlayedRef.current = true;
    
    const introMessage = "Hi there, I'm an AI agent that can help you \"course correct\" your academic plans! Here are some of the things I can do: provide course descriptions, grab a professor's RateMyProfessors review, tell you which courses you need to take to graduate, and generate schedules for next semester! Ask me anything you'd like, either with your microphone or through chat!";
    
    // Stop any current TTS
    stopCurrentTTS();
    
    // Set the agent reply text for typewriter display
    setActiveAgentReply(introMessage);
    setIsAgentSpeaking(true);
    
    // Add message to chat
    // const agentMessage: Message = {
    //   id: `intro-${Date.now()}`,
    //   content: introMessage,
    //   timestamp: new Date(),
    // };
    // setMessages((prev) => [...prev, agentMessage]);
    
    // Play the intro.mp3 file
    const audio = new Audio("/intro.mp3");
    
    // Audio level metering via Web Audio API
    try {
      interface WindowWithCtx extends Window { __wdAudioCtx?: AudioContext }
      const win = window as WindowWithCtx & typeof globalThis & { webkitAudioContext?: typeof AudioContext };
      const ACtor = win.AudioContext || win.webkitAudioContext;
      if (ACtor) {
        const ctx: AudioContext = win.__wdAudioCtx || new ACtor();
        if (!win.__wdAudioCtx) win.__wdAudioCtx = ctx;
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 1024;
        analyser.smoothingTimeConstant = 0.85;
        let cleanup: (() => void) | null = null;
        let sourceNode: MediaElementAudioSourceNode | null = null;
        try {
          const elemSource = ctx.createMediaElementSource(audio);
          sourceNode = elemSource;
          const zero = ctx.createGain();
          zero.gain.value = 0;
          elemSource.connect(analyser);
          analyser.connect(zero);
          zero.connect(ctx.destination);
          cleanup = () => {
            try { elemSource.disconnect(); } catch { /* ignore */ }
            try { analyser.disconnect(); } catch { /* ignore */ }
            try { zero.disconnect(); } catch { /* ignore */ }
          };
        } catch {
          cleanup = null;
        }
        if (sourceNode) {
          const buf = new Uint8Array(analyser.fftSize);
          let rafId = 0;
          const pump = () => {
            if (audio.ended || audio.paused) {
              if (cleanup) cleanup();
              cancelAnimationFrame(rafId);
              setAudioLevel(0);
              return;
            }
            analyser.getByteTimeDomainData(buf);
            let sum = 0;
            for (let i = 0; i < buf.length; i++) {
              const v = (buf[i] - 128) / 128;
              sum += v * v;
            }
            const rms = Math.sqrt(sum / buf.length);
            const level = Math.max(0, Math.min(1, rms * 1.8));
            setAudioLevel(level);
            rafId = requestAnimationFrame(pump);
          };
          void ctx.resume?.();
          rafId = requestAnimationFrame(pump);
          const endHandler = () => {
            if (cleanup) cleanup();
            setAudioLevel(0);
            setIsAgentSpeaking(false);
          };
          audio.addEventListener('ended', endHandler, { once: true });
          audio.addEventListener('pause', endHandler, { once: true });
        }
      }
    } catch {
      // ignore metering errors
    }
    
    audio.onended = () => {
      setIsAgentSpeaking(false);
      setAudioLevel(0);
    };
    
    try {
      await audio.cloneNode(true).play();
    } catch (e) {
      console.error('Failed to play intro audio', e);
      setIsAgentSpeaking(false);
      setAudioLevel(0);
    }
  }, []);

  // Handle 'p' key press for intro
  useEffect(() => {
    const isTypingTarget = (el: EventTarget | null) => {
      const node = el as HTMLElement | null;
      if (!node) return false;
      const tag = node.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || (node as HTMLElement).isContentEditable) return true;
      return false;
    };

    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'p' || e.key === 'P') {
        if (isTypingTarget(e.target)) return; // don't trigger when typing
        e.preventDefault();
        playIntroAudio();
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => {
      window.removeEventListener("keydown", handleKeyPress);
    };
  }, [playIntroAudio]);

  const handleSendMessage = () => {
    const text = inputValue.trim();
    if (!text) return;
    
    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, content: `You: ${text}`, timestamp: new Date() },
    ]);
    setIsAgentSpeaking(true);
    setInputValue("");
    
    (async () => {
      try {
        setIsThinking(true);
        const agentResponse = await fetchAgentReply(text);
        setIsThinking(false);
        const agentReply = agentResponse.reply;
        
        // Add chat message as markdown if present and non-empty
        if (agentResponse.chat) {
          const chatMessage: Message = {
            id: `chat-${Date.now()}`,
            content: agentResponse.chat,
            timestamp: new Date(),
            markdown: true,
          };
          setMessages((prev) => [...prev, chatMessage]);
        }
        
        setActiveAgentReply(""); // Clear previous reply before starting new audio
        const speakOptions = {
          rate: 1.5,
          onStart: () => setActiveAgentReply(agentReply),
          onLevel: (lvl: number) => setAudioLevel(lvl),
        };
        const result = await speakText(agentReply, voiceId, speakOptions);
        // If 401 error, still show the typewriter reply
        if (!result.success && result.status === 401) {
          setActiveAgentReply(agentReply);
        }
        setTimeout(() => setIsAgentSpeaking(false), 200);
      } catch (e) {
        setIsThinking(false);
        const msg = e instanceof Error ? e.message : String(e);
        setMessages((prev) => [
          ...prev,
          { id: `e-${Date.now()}`, content: `Agent unavailable: ${msg}`, timestamp: new Date() },
        ]);
        setIsAgentSpeaking(false);
      }
    })();
  };

  return (
    <div className="h-screen bg-background flex">
      <SpaceBackground />
      <img src="/courses.png" alt="Logo" className="absolute top-4 left-4 h-16 w-auto z-20" />
      {/* Left side - Agent Visualizer */}
      <div className="flex-1 flex items-center justify-center relative z-10">
        <AgentVisualizer isAgentSpeaking={isAgentSpeaking} isThinking={isThinking} text={activeAgentReply} audioLevel={audioLevel} />
        <PushToTalkIndicator isSpeaking={isSpeaking} />
        {!realtimeEnabled ? null : !connected && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 text-sm text-muted-foreground z-30">
            Connecting to ElevenLabs realtime...
            {error && <div className="text-red-500 mt-1">{error}</div>}
          </div>
        )}
        {/* STT status moved into the input bar; only show errors here */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[80%] text-center pointer-events-none z-30">
          {!sttSupported && (
            <div className="text-sm text-red-500">Speech recognition not supported in this browser.</div>
          )}
          {sttError && <div className="text-xs text-red-500 mt-1">STT error: {sttError}</div>}
        </div>
      </div>

      {/* Right side - Chat Window */}
      <div className="w-[800px] border-l border-border z-10">
        <ChatWindow
          messages={messages}
          inputValue={inputValue}
          onInputChange={(e) => setInputValue(e.target.value)}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
};

export default Meeting;
