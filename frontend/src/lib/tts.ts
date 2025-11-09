// ElevenLabs-only TTS client. No browser speech fallback; if the request fails, no audio plays.

// Intentionally no browser speech synthesis fallback here.

let currentAudio: HTMLAudioElement | null = null;
let currentMediaSource: MediaSource | null = null;

export function stopCurrentTTS() {
  try {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.src = '';
    }
    if (currentMediaSource && currentMediaSource.readyState === 'open') {
      try { currentMediaSource.endOfStream(); } catch (_) { /* ignore */ }
    }
  } catch (e) {
    // non-fatal
  } finally {
    currentAudio = null;
    currentMediaSource = null;
  }
}

type SpeakOptions = {
  onStart?: () => void;
  onEnd?: () => void;
  rate?: number; // playbackRate of the audio element (1.0 = normal)
  onLevel?: (level: number) => void; // 0..1 amplitude level while playing
};

export async function speakText(text: string, voice_id?: string, options?: SpeakOptions): Promise<{ success: boolean; status?: number }> {
  // Stop any in-progress TTS to avoid overlapping speech
  stopCurrentTTS();
  // Use GET streaming endpoint for lower latency playback if available.
  const params = new URLSearchParams({ text });
  if (voice_id) params.set('voice_id', voice_id);
  const resp = await fetch(`/api/elevenlabs/tts_stream?${params.toString()}`);
  if (!resp.ok) {
    console.error('TTS request failed', resp.status);
    return { success: false, status: resp.status };
  }
  // Stream into MediaSource for progressive playback
  const contentType = resp.headers.get('Content-Type') || 'audio/mpeg';
  if (!('MediaSource' in window)) {
    // Fallback: load whole blob
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => URL.revokeObjectURL(url);
    try { await audio.play(); return { success: true }; } catch (e) { console.error('Audio play failed', e); return { success: false }; }
  }
  const mediaSource = new MediaSource();
  currentMediaSource = mediaSource;
  const audioEl = new Audio();
  currentAudio = audioEl;
  const desiredRate = options?.rate && options.rate > 0 ? options.rate : 1.0;
  try { audioEl.playbackRate = desiredRate; } catch (_) { /* ignore */ }
  // Try to preserve pitch so faster playback doesn't sound chipmunky (where supported)
  try {
    const pitchy = audioEl as HTMLAudioElement & {
      preservesPitch?: boolean;
      mozPreservesPitch?: boolean;
      webkitPreservesPitch?: boolean;
    };
    if (typeof pitchy.preservesPitch !== 'undefined') pitchy.preservesPitch = true;
    if (typeof pitchy.mozPreservesPitch !== 'undefined') pitchy.mozPreservesPitch = true;
    if (typeof pitchy.webkitPreservesPitch !== 'undefined') pitchy.webkitPreservesPitch = true;
  } catch (_) { /* ignore */ }
  audioEl.preload = 'auto';
  audioEl.src = URL.createObjectURL(mediaSource);
  let started = false;
  const onPlaying = () => {
    if (!started) {
      started = true;
      try { options?.onStart?.(); } catch (_) { /* ignore */ }
    }
  };
  audioEl.addEventListener('playing', onPlaying, { once: true });
  // We'll optionally delay play for >1.0 rates until a small buffer accumulates so speed-up is audible.
  const maybeStartPlayback = () => {
    if (started) return;
    // If not speeding up, start immediately
    if (desiredRate <= 1.0) {
      audioEl.play().catch((e) => console.error('Audio play failed', e));
      return;
    }
    // For faster playback, require a short buffer so we can actually play faster than real-time.
    // Base threshold: ~1.2s. For higher speeds (>=1.5) increase so we can maintain accelerated playback without starving.
    let bufferedAhead = 0;
    try {
      if (audioEl.buffered.length > 0) {
        const end = audioEl.buffered.end(audioEl.buffered.length - 1);
        const current = audioEl.currentTime || 0;
        bufferedAhead = Math.max(0, end - current);
      }
    } catch (_) { /* ignore */ }
    const requiredAhead = desiredRate >= 1.5 ? 2.0 : 1.2;
    if (bufferedAhead >= requiredAhead) {
      audioEl.play().catch((e) => console.error('Audio play failed', e));
    }
  };
  mediaSource.addEventListener('sourceopen', async () => {
    const mime = contentType.includes('mpeg') ? 'audio/mpeg' : contentType;
    let sourceBuffer: SourceBuffer;
    try {
      sourceBuffer = mediaSource.addSourceBuffer(mime);
    } catch (e) {
      console.warn('Failed to create SourceBuffer, falling back to full blob', e);
      const blob = await resp.blob();
      const url2 = URL.createObjectURL(blob);
      audioEl.src = url2;
      audioEl.onended = () => {
        URL.revokeObjectURL(url2);
        if (currentAudio === audioEl) currentAudio = null;
      };
      audioEl.play().catch((err) => console.error('Audio play failed', err));
      return;
    }
    const reader = resp.body?.getReader();
    if (!reader) return;
    const waitUpdateEnd = () => new Promise<void>((resolve) => {
      const handler = () => resolve();
      sourceBuffer.addEventListener('updateend', handler, { once: true });
    });
    const appendChunk = async (chunk: Uint8Array) => {
      // Ensure previous update completed
      if (sourceBuffer.updating) await waitUpdateEnd();
      try {
        const ab = new ArrayBuffer(chunk.byteLength);
        const view = new Uint8Array(ab);
        view.set(chunk);
        sourceBuffer.appendBuffer(ab);
      } catch (e) {
        console.error('appendBuffer error', e);
        return;
      }
      // Wait for this append to finish before returning
      await waitUpdateEnd();
      // After each append, see if we can start playback for >1.0 rates
      maybeStartPlayback();
    };
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (value) await appendChunk(value);
    }
    // Ensure buffer not updating before closing stream
    if (sourceBuffer.updating) await waitUpdateEnd();
    try { mediaSource.endOfStream(); } catch (e) { console.error('endOfStream failed', e); }
    // If we never reached buffer threshold (e.g., very short clip), start playback now
    maybeStartPlayback();
    audioEl.onended = () => {
      if (audioEl.src.startsWith('blob:')) {
        try { URL.revokeObjectURL(audioEl.src); } catch (_) { /* ignore */ }
      }
      if (currentAudio === audioEl) currentAudio = null;
      try { options?.onEnd?.(); } catch (_) { /* ignore */ }
    };
  });

  // Audio level metering via Web Audio API
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
      let sourceNode: MediaStreamAudioSourceNode | MediaElementAudioSourceNode | null = null;
      try {
        type AudioWithCapture = HTMLMediaElement & { captureStream?: () => MediaStream };
        const elCap = audioEl as unknown as AudioWithCapture;
        const canCapture = typeof elCap.captureStream === 'function';
        if (canCapture && elCap.captureStream) {
          const stream = elCap.captureStream();
          sourceNode = ctx.createMediaStreamSource(stream);
          sourceNode.connect(analyser);
          cleanup = () => { try { if (sourceNode) sourceNode.disconnect(); } catch { /* ignore */ } };
        } else {
          const elemSource = ctx.createMediaElementSource(audioEl);
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
        }
      } catch {
        cleanup = null;
      }
      if (sourceNode) {
        const buf = new Uint8Array(analyser.fftSize);
        let rafId = 0;
        const pump = () => {
          if (currentAudio !== audioEl) {
            if (cleanup) cleanup();
            cancelAnimationFrame(rafId);
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
          options?.onLevel?.(level);
          rafId = requestAnimationFrame(pump);
        };
        void ctx.resume?.();
        rafId = requestAnimationFrame(pump);
        const endHandler = () => {
          if (cleanup) cleanup();
          options?.onLevel?.(0);
        };
        audioEl.addEventListener('ended', endHandler, { once: true });
        audioEl.addEventListener('pause', endHandler, { once: true });
      }
    }
  } catch {
    // ignore metering errors
  }
  return { success: true };
}

export async function converse(userText: string, options?: SpeakOptions) {
  // Hit conversation turn endpoint and stream advisor reply audio
  const resp = await fetch('/api/conversation/turn', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: userText })
  });
  if (!resp.ok) {
    console.error('Conversation turn failed', resp.status);
    return { reply: '(error)', status: resp.status };
  }
  const replyHeader = resp.headers.get('X-Advisor-Reply') || '';
  // Stream audio similarly to speakText fallback
  const blob = await resp.blob(); // simpler for now; could implement streaming like above
  const url = URL.createObjectURL(blob);
  stopCurrentTTS();
  const audio = new Audio(url);
  currentAudio = audio;
  if (options?.rate && options.rate > 0) {
    try { audio.playbackRate = options.rate; } catch (_) { /* ignore */ }
  }
  let started = false;
  const onPlaying = () => {
    if (!started) {
      started = true;
      try { options?.onStart?.(); } catch (_) { /* ignore */ }
    }
  };
  audio.addEventListener('playing', onPlaying, { once: true });
  audio.onended = () => {
    URL.revokeObjectURL(url);
    if (currentAudio === audio) currentAudio = null;
    try { options?.onEnd?.(); } catch (_) { /* ignore */ }
  };
  audio.play().catch(() => {});
  return { reply: replyHeader || '(no reply header)', status: resp.status };
}
