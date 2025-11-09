import TypewriterReply from "./TypewriterReply";
import "./AgentVisualizer.css";

interface AgentVisualizerProps {
  isAgentSpeaking: boolean;
  isThinking?: boolean;
  text?: string; // current agent reply to render as typewriter overlay
  audioLevel?: number; // 0..1 amplitude level
}

const AgentVisualizer = ({ isAgentSpeaking, isThinking, text, audioLevel = 0 }: AgentVisualizerProps) => {
  return (
    <div
      className={`white-dwarf relative flex items-center justify-center w-full ${isAgentSpeaking ? "speaking" : ""}`}
      style={{ ['--wd-level']: audioLevel.toFixed(3) } as React.CSSProperties}
    >
      <div className="wd-stage">
        {/* Halo layers */}
        <div className="wd-halo-outer" aria-hidden />
        <div className="wd-halo-inner" aria-hidden />

        {/* Diffraction spikes */}
        <div className="wd-spike wd-spike-h" aria-hidden />
        <div className="wd-spike wd-spike-v" aria-hidden />
        <div className="wd-spike wd-spike-d1" aria-hidden />
        <div className="wd-spike wd-spike-d2" aria-hidden />

        {/* Accretion disk (subtle, tilted) */}
        <div className="wd-disk" aria-hidden />

        {/* Corona layers around the star with slight variation */}
        <div className="wd-corona" aria-hidden />
        <div className="wd-corona wd-corona-2" aria-hidden />

        {/* Surface texture and subtle lensing */}
        <div className="wd-surface" aria-hidden />
        <div className="wd-noise" aria-hidden />
        <div className="wd-lens" aria-hidden />
        <div className="wd-particles" aria-hidden />

        {/* Stellar core */}
        <div className="wd-core" aria-hidden />
      </div>

      {/* Typewriter reply overlay under the star */}
      <TypewriterReply reply={text || ""} isAgentSpeaking={isAgentSpeaking} isThinking={isThinking} />
    </div>
  );
};

export default AgentVisualizer;
