import { useEffect, useRef, useState } from 'react';

// Minimal SpeechRecognition type shims (Chrome Web Speech API)
interface ISpeechRecognitionAlternative { transcript: string; confidence?: number }
interface ISpeechRecognitionResult { isFinal: boolean; length: number; [index: number]: ISpeechRecognitionAlternative }
interface ISpeechRecognitionResultList { length: number; [index: number]: ISpeechRecognitionResult }
interface ISpeechRecognitionEvent extends Event { resultIndex: number; results: ISpeechRecognitionResultList }
interface ISpeechRecognition extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  abort?: () => void;
  onresult: ((ev: ISpeechRecognitionEvent) => void) | null;
  onend: ((this: ISpeechRecognition, ev: Event) => void) | null;
  onerror: ((this: ISpeechRecognition, ev: Event) => void) | null;
}
type SpeechRecognitionConstructor = new () => ISpeechRecognition;

declare global {
  interface Window {
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
    SpeechRecognition?: SpeechRecognitionConstructor;
  }
}

// Simple Web Speech API wrapper for push-to-talk speech recognition (Chrome only).
export function useSpeechToText() {
  const [supported, setSupported] = useState<boolean>(false);
  const [listening, setListening] = useState(false);
  const [finalText, setFinalText] = useState<string>('');
  const [interimText, setInterimText] = useState<string>('');
  // Buffer every piece of speech (final or interim) while the mic is active,
  // so very short presses still yield a transcript even if the API never marks
  // anything as final before stop() fires.
  const bufferRef = useRef<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const recRef = useRef<ISpeechRecognition | null>(null);
  const stopResolverRef = useRef<((text: string) => void) | null>(null);
  const finalRef = useRef<string>('');

  // Keep a ref of the latest finalText so event handlers resolve with the current value
  useEffect(() => {
    finalRef.current = finalText;
  }, [finalText]);

  useEffect(() => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setSupported(false);
      return;
    }
    setSupported(true);
    const rec: ISpeechRecognition = new SR();
    rec.lang = 'en-US';
    rec.interimResults = true; // supported in Chrome
    rec.continuous = false;

    rec.onresult = (e: ISpeechRecognitionEvent) => {
      setError(null);
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        const result = e.results[i];
        const chunk = result[0].transcript;
        if (result.isFinal) {
          setFinalText((prev) => (prev ? prev + ' ' : '') + chunk);
          bufferRef.current.push(chunk);
        } else {
          interim += (interim ? ' ' : '') + chunk;
          // Still capture interim so a quick tap returns something
          bufferRef.current.push(chunk);
        }
      }
      setInterimText(interim);
    };
    rec.onend = () => {
      setListening(false);
      setInterimText('');
      // If no finalText was produced (e.g., very short press), synthesize from buffer
      if (!finalRef.current && bufferRef.current.length) {
        const synthetic = bufferRef.current.join(' ').trim();
        if (synthetic) {
          setFinalText(synthetic);
          finalRef.current = synthetic; // keep ref in sync
        }
      }
      // Resolve any awaiting caller with the latest finalized (or synthetic) text
      if (stopResolverRef.current) {
        stopResolverRef.current(finalRef.current);
        stopResolverRef.current = null;
      }
      bufferRef.current = [];
    };
    rec.onerror = (ev: Event) => {
      const e = ev as unknown as { error?: unknown };
      setListening(false);
      setInterimText('');
      // Attempt to read a dynamic error property without relying on 'any' casting at use sites
      let errStr = 'stt-error';
      if (e && 'error' in e) {
        const maybeError = (e as Record<string, unknown>).error;
        if (typeof maybeError === 'string') errStr = maybeError;
      }
      setError(errStr);
      // Resolve with whatever we have to avoid hanging callers
      if (stopResolverRef.current) {
        stopResolverRef.current(finalRef.current);
        stopResolverRef.current = null;
      }
    };

    recRef.current = rec;
    return () => {
      try {
        rec.stop();
      } catch (e) {
        // ignore
      }
      recRef.current = null;
    };
  }, []);

  const start = () => {
    if (!recRef.current) return;
    if (listening) return; // guard duplicate start
  setFinalText('');
  setInterimText('');
  bufferRef.current = [];
    setError(null);
    try {
      recRef.current.start();
      setListening(true);
    } catch (e) {
      setError('failed-to-start');
    }
  };

  const stop = () => {
    if (!recRef.current) return;
    try {
      recRef.current.stop();
    } catch (e) {
      try { recRef.current.abort?.(); } catch (_) { /* ignore */ }
    }
  };

  // Convenience: stop recognition and return a promise that resolves
  // once onend fires with the latest finalized transcript.
  const stopAndGetFinal = async (): Promise<string> => {
    if (!recRef.current) return finalText;
    return new Promise<string>((resolve) => {
      stopResolverRef.current = resolve;
      try {
        recRef.current!.stop();
      } catch (e) {
  try { recRef.current!.abort?.(); } catch (_err) { /* no-op */ }
        resolve(finalRef.current);
      }
    });
  };

  return { supported, listening, start, stop, stopAndGetFinal, finalText, interimText, error, setFinalText } as const;
}
