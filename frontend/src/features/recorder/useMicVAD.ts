/**
 * Hook wrapping browser Voice Activity Detection (Silero VAD / vad-web).
 * Only speech segments (16 kHz mono Float32) are emitted; silence never reaches the recogniser.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { MicVAD } from '@ricky0123/vad-web';

export interface UseMicVADOptions {
  onSpeechEnd: (audio: Float32Array) => void;
  onSpeechStart?: () => void;
  onVADMisfire?: () => void;
}

export interface UseMicVADReturn {
  isListening: boolean;
  isSpeaking: boolean;
  permissionError: string | null;
  start: () => Promise<void>;
  stop: () => void;
}

export function useMicVAD({ onSpeechEnd, onSpeechStart, onVADMisfire }: UseMicVADOptions): UseMicVADReturn {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  const vadRef = useRef<MicVAD | null>(null);
  const callbacksRef = useRef({ onSpeechEnd, onSpeechStart, onVADMisfire });

  useEffect(() => {
    callbacksRef.current = { onSpeechEnd, onSpeechStart, onVADMisfire };
  }, [onSpeechEnd, onSpeechStart, onVADMisfire]);

  const stop = useCallback(() => {
    if (vadRef.current) {
      vadRef.current.pause();
    }
    setIsListening(false);
    setIsSpeaking(false);
  }, []);

  const start = useCallback(async () => {
    setPermissionError(null);

    try {
      if (!vadRef.current) {
        // Instantiate MicVAD with parameters from docs/TRD.md
        const myVad = await MicVAD.new({
          positiveSpeechThreshold: 0.5,
          negativeSpeechThreshold: 0.35,
          minSpeechMs: 250,
          redemptionMs: 700,
          preSpeechPadMs: 300,
          onSpeechStart: () => {
            setIsSpeaking(true);
            callbacksRef.current.onSpeechStart?.();
          },
          onSpeechEnd: (audio: Float32Array) => {
            setIsSpeaking(false);
            callbacksRef.current.onSpeechEnd(audio);
          },
          onVADMisfire: () => {
            setIsSpeaking(false);
            callbacksRef.current.onVADMisfire?.();
          },
        });

        vadRef.current = myVad;
      }

      await vadRef.current.start();
      setIsListening(true);
    } catch (err: unknown) {
      setIsListening(false);
      setIsSpeaking(false);
      const msg = err instanceof Error ? err.message : 'Microphone access denied or unsupported';
      setPermissionError(msg);
      throw err;
    }
  }, []);

  useEffect(() => {
    return () => {
      if (vadRef.current) {
        vadRef.current.destroy();
        vadRef.current = null;
      }
    };
  }, []);

  return {
    isListening,
    isSpeaking,
    permissionError,
    start,
    stop,
  };
}
