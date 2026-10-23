/**
 * Recorder controls (Start Mic, Stop, Clear, Save Recording) and live status strip.
 * Conforms to visual specifications in docs/DESIGN.md.
 */

import React from 'react';
import { Mic, Square, Trash2, Download, Radio } from 'lucide-react';
import { useSessionStore } from '../../store/sessionStore';
import { useTranscriptStore } from '../../store/transcriptStore';
import { useSummaryStore } from '../../store/summaryStore';
import './RecorderControls.css';

interface RecorderControlsProps {
  onStart: () => void;
  onStop: () => void;
  onClear: () => void;
  onSaveRecording: () => void;
  isStarting?: boolean;
}

export const RecorderControls: React.FC<RecorderControlsProps> = ({
  onStart,
  onStop,
  onClear,
  onSaveRecording,
  isStarting = false,
}) => {
  const { status, wsStatus } = useSessionStore();
  const { wordCount, chunkCount, isSpeaking, segments, audioBlobs } = useTranscriptStore();
  const { isAnalyzing } = useSummaryStore();

  const isRecording = status === 'listening' || status === 'capturing';
  const hasContent = segments.length > 0;
  const canSave = (hasContent || audioBlobs.length > 0) && !isRecording;

  return (
    <div className="recorder-controls-container">
      {/* Button Row */}
      <div className="button-row">
        <button
          className="btn btn-primary"
          onClick={onStart}
          disabled={isRecording || isAnalyzing || isStarting}
          aria-label="Start Microphone"
        >
          <Mic size={18} className={isRecording ? 'pulse-icon' : ''} />
          <span>{isStarting ? 'Starting...' : 'Start Mic'}</span>
        </button>

        <button
          className="btn btn-danger-outline"
          onClick={onStop}
          disabled={!isRecording}
          aria-label="Stop Recording"
        >
          <Square size={16} />
          <span>Stop</span>
        </button>

        <button
          className="btn btn-outline"
          onClick={onClear}
          disabled={!hasContent || isRecording || isAnalyzing}
          aria-label="Clear Transcript"
        >
          <Trash2 size={16} />
          <span>Clear</span>
        </button>

        <button
          className="btn btn-success-outline"
          onClick={onSaveRecording}
          disabled={!canSave}
          aria-label="Save Recording and Transcript"
        >
          <Download size={16} />
          <span>Save Recording</span>
        </button>
      </div>

      {/* Stat Pills & VAD Live Strip */}
      <div className="stats-strip">
        <div className="pills-group">
          <span className="stat-pill">
            WORDS: <strong>{wordCount}</strong>
          </span>
          <span className="stat-pill">
            CHUNKS: <strong>{chunkCount}</strong>
          </span>
        </div>

        <div className={`live-strip ${isSpeaking ? 'active-speaking' : isRecording ? 'listening-idle' : ''}`}>
          <Radio size={14} className={isSpeaking ? 'vad-pulse' : 'vad-idle'} />
          <span className="vad-text">
            {isSpeaking
              ? 'Speech Detected (Capturing segment...)'
              : isRecording
                ? 'Listening — waiting for speech...'
                : wsStatus === 'connected'
                  ? 'Ready to Record'
                  : 'Idle'}
          </span>
        </div>
      </div>
    </div>
  );
};
