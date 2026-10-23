import { useEffect, useRef, useState, useCallback } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  X,
} from 'lucide-react';
import { useSessionStore } from './store/sessionStore';
import { useTranscriptStore } from './store/transcriptStore';
import { useSummaryStore } from './store/summaryStore';
import { TranscriptPanel } from './features/transcript/TranscriptPanel';
import { SummaryPanel } from './features/summary/SummaryPanel';
import { useMicVAD } from './features/recorder/useMicVAD';
import { AudioWebSocketClient } from './lib/ws';
import { encodeWAV } from './lib/audio';
import { createSession, analyzeSession, clearSession as apiClearSession } from './lib/api';
import './App.css';

interface HealthStatus {
  status: string;
  asr: string;
  db: string;
}

export function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [consentDismissed, setConsentDismissed] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const {
    sessionId,
    status,
    wsStatus,
    patientName,
    setSessionId,
    setStatus,
    setWsStatus,
    resetSession,
  } = useSessionStore();

  const {
    segments,
    audioBlobs,
    upsertSegment,
    addAudioChunk,
    clearTranscript,
    getCombinedText,
  } = useTranscriptStore();

  const {
    summary,
    setSummary,
    setIsAnalyzing,
    clearSummary,
  } = useSummaryStore();

  const wsClientRef = useRef<AudioWebSocketClient | null>(null);
  const seqCounterRef = useRef<number>(1);
  const sessionIdRef = useRef<string | null>(sessionId);
  sessionIdRef.current = sessionId;

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  // Backend health check on initial load
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch('/health');
        if (!res.ok) throw new Error(`Health status ${res.status}`);
        const data = (await res.json()) as HealthStatus;
        setHealth(data);
      } catch {
        setHealth(null);
      } finally {
        setHealthLoading(false);
      }
    }
    checkHealth();
  }, []);

  // Initialize or teardown WebSocket client when sessionId changes
  const connectWebSocket = useCallback((id: string) => {
    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
      wsClientRef.current = null;
    }

    const client = new AudioWebSocketClient({
      sessionId: id,
      onSegment: (event) => {
        upsertSegment({
          seq: event.seq,
          text: event.text,
          start_ms: event.start_ms,
          end_ms: event.end_ms,
          confidence: event.confidence,
          status: 'done',
        });
      },
      onError: (event) => {
        showToast(`ASR Error (chunk #${event.seq}): ${event.message}`, 'error');
      },
      onStatusChange: (s) => {
        setWsStatus(s);
      },
    });

    client.connect();
    wsClientRef.current = client;
  }, [upsertSegment, setWsStatus, showToast]);

  // Clean up WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsClientRef.current) {
        wsClientRef.current.disconnect();
      }
    };
  }, []);

  // VAD Callback handlers
  const handleSpeechStart = useCallback(() => {
    setStatus('capturing');
  }, [setStatus]);

  const handleSpeechEnd = useCallback(
    (floatAudio: Float32Array) => {
      setStatus('listening');
      const seq = seqCounterRef.current++;

      // Convert to WAV blob and save for session audio download
      const wavBlob = encodeWAV(floatAudio, 16000);
      addAudioChunk(wavBlob);

      // Send to backend over WebSocket
      if (wsClientRef.current) {
        wsClientRef.current.sendAudioSegment(seq, floatAudio, 16000);
      }
    },
    [setStatus, addAudioChunk]
  );

  const { start: startVAD, stop: stopVAD, permissionError } = useMicVAD({
    onSpeechStart: handleSpeechStart,
    onSpeechEnd: handleSpeechEnd,
  });

  // Start Consultation / Microphone
  const handleStartMic = async () => {
    try {
      let activeSessionId = sessionIdRef.current;
      if (!activeSessionId) {
        const session = await createSession('en', patientName);
        activeSessionId = session.id;
        setSessionId(session.id);
        connectWebSocket(session.id);
      } else if (!wsClientRef.current || wsStatus === 'disconnected') {
        connectWebSocket(activeSessionId);
      }

      await startVAD();
      setStatus('listening');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to start microphone';
      showToast(msg, 'error');
      setStatus('idle');
    }
  };

  // Stop Consultation / Microphone
  const handleStopMic = () => {
    stopVAD();
    if (wsClientRef.current) {
      wsClientRef.current.stopSession();
    }
    setStatus('ready');
  };

  // Clear Session & Transcript
  const handleClear = async () => {
    const hasData = segments.length > 0 || summary !== null;
    if (hasData) {
      const confirmed = window.confirm(
        'Are you sure you want to clear the current consultation transcript and AI summary?'
      );
      if (!confirmed) return;
    }

    try {
      if (sessionId) {
        await apiClearSession(sessionId);
      }
    } catch {
      // Ignore API reset error if session was local
    }

    stopVAD();
    if (wsClientRef.current) {
      wsClientRef.current.disconnect();
      wsClientRef.current = null;
    }
    seqCounterRef.current = 1;
    clearTranscript();
    clearSummary();
    resetSession();
    showToast('Consultation cleared', 'success');
  };

  // Process Transcript with AI
  const handleProcessTranscript = async () => {
    if (!sessionId) {
      showToast('No active session to process', 'error');
      return;
    }

    setIsAnalyzing(true);
    try {
      const res = await analyzeSession(sessionId, true, 'en');
      setSummary(res.data, res.summary_id, res.version);
      setStatus('reviewed');
      showToast('Clinical summary generated successfully!', 'success');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Analysis failed';
      showToast(msg, 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Save Recording & Transcript
  const handleSaveRecording = () => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');

    // 1. Download Transcript
    const fullText = getCombinedText();
    if (fullText) {
      const textBlob = new Blob([fullText], { type: 'text/plain;charset=utf-8' });
      const textUrl = URL.createObjectURL(textBlob);
      const a = document.createElement('a');
      a.href = textUrl;
      a.download = `Consultation_Transcript_${timestamp}.txt`;
      a.click();
      URL.revokeObjectURL(textUrl);
    }

    // 2. Download Audio if available
    if (audioBlobs.length > 0) {
      const audioBlob = new Blob(audioBlobs, { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const a = document.createElement('a');
      a.href = audioUrl;
      a.download = `Consultation_Audio_${timestamp}.wav`;
      a.click();
      URL.revokeObjectURL(audioUrl);
    }

    showToast('Recording and transcript downloaded', 'success');
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <Activity className="brand-icon" />
          <div className="brand-text">
            <h1>Live Medical Transcription</h1>
            <p>Clinical Intelligence & Structured Summary</p>
          </div>
        </div>

        <div className="header-status">
          {/* WebSocket indicator */}
          <div className={`ws-badge ${wsStatus === 'connected' ? 'ws-connected' : 'ws-disconnected'}`}>
            <span className={`ws-dot ${wsStatus === 'connected' ? 'ws-pulse' : ''}`} />
            <span>{wsStatus === 'connected' ? 'Live Stream Ready' : 'WS Idle'}</span>
          </div>

          {/* Backend Health Badge */}
          {healthLoading && <span className="status-badge loading">Connecting...</span>}
          {!healthLoading && !health && (
            <span className="status-badge error">
              <AlertCircle size={14} /> Backend Offline
            </span>
          )}
          {health && (
            <div className="status-badge ok">
              <CheckCircle2 size={16} />
              <span>API OK</span>
              <span className="sub-badge">ASR: {health.asr}</span>
            </div>
          )}
        </div>
      </header>

      {/* Mandatory Clinical Consent Banner */}
      {!consentDismissed && (
        <div className="consent-banner" role="region" aria-label="Patient Recording Consent">
          <div className="consent-content">
            <ShieldCheck size={18} />
            <span>
              <strong>Patient Notice:</strong> This clinical consultation will be recorded and transcribed in real time. Please ensure informed patient consent has been obtained.
            </span>
          </div>
          <button
            className="btn-dismiss-consent"
            onClick={() => setConsentDismissed(true)}
            aria-label="Dismiss Notice"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Main Workspace (Side-by-Side Cards) */}
      <main className="main-content">
        {permissionError && (
          <div className="out-of-date-banner" style={{ marginBottom: 20 }}>
            <AlertCircle size={16} />
            <span>Microphone Permission Error: {permissionError}. Please check browser mic settings.</span>
          </div>
        )}

        <div className="workspace-grid">
          {/* Left Card: Live Medical Transcription */}
          <TranscriptPanel
            onStartMic={handleStartMic}
            onStopMic={handleStopMic}
            onClear={handleClear}
            onSaveRecording={handleSaveRecording}
            onProcessTranscript={handleProcessTranscript}
            isStartingMic={status === 'listening' && wsStatus === 'connecting'}
          />

          {/* Right Card: AI Medical Summary */}
          <SummaryPanel onClear={handleClear} />
        </div>
      </main>

      {/* Toast Notification */}
      {toast && (
        <div className="toast-container" role="status">
          <div className={`toast ${toast.type}`}>
            {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
