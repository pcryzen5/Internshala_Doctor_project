/**
 * Left Card — Live Medical Transcription Panel.
 * Implements append-by-seq rendering, auto-scroll, jump-to-latest, inline edits, and ARIA live region.
 * Conforms to docs/DESIGN.md & docs/APP_FLOW.md.
 */

import React, { useEffect, useRef, useState } from 'react';
import { Mic, Zap, ArrowDown, AlertCircle, RefreshCw } from 'lucide-react';
import { useSessionStore } from '../../store/sessionStore';
import { useTranscriptStore } from '../../store/transcriptStore';
import { useSummaryStore } from '../../store/summaryStore';
import { TranscriptSegment } from '../../lib/types';
import { RecorderControls } from '../recorder/RecorderControls';
import './TranscriptPanel.css';

interface TranscriptPanelProps {
  onStartMic: () => void;
  onStopMic: () => void;
  onClear: () => void;
  onSaveRecording: () => void;
  onProcessTranscript: () => void;
  onRetrySegment?: (seq: number) => void;
  isStartingMic?: boolean;
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  onStartMic,
  onStopMic,
  onClear,
  onSaveRecording,
  onProcessTranscript,
  onRetrySegment,
  isStartingMic = false,
}) => {
  const { status } = useSessionStore();
  const { segments, updateSegmentText } = useTranscriptStore();
  const { isAnalyzing, markOutOfDate } = useSummaryStore();

  const scrollRef = useRef<HTMLDivElement>(null);
  const [userScrolledUp, setUserScrolledUp] = useState(false);
  const [editingSeq, setEditingSeq] = useState<number | null>(null);
  const [editText, setEditText] = useState('');

  const isRecording = status === 'listening' || status === 'capturing';
  const hasContent = segments.length > 0;

  // Auto-scroll logic with user scroll detection
  useEffect(() => {
    if (!userScrolledUp && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [segments, userScrolledUp]);

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 40;
    setUserScrolledUp(!isAtBottom);
  };

  const jumpToLatest = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      setUserScrolledUp(false);
    }
  };

  const startEdit = (seg: TranscriptSegment) => {
    setEditingSeq(seg.seq);
    setEditText(seg.edited_text !== undefined && seg.edited_text !== null ? seg.edited_text : seg.text);
  };

  const saveEdit = (seq: number) => {
    updateSegmentText(seq, editText);
    setEditingSeq(null);
    markOutOfDate(true);
  };

  const formatMs = (ms: number) => {
    const totalSecs = Math.floor(ms / 1000);
    const m = Math.floor(totalSecs / 60);
    const s = totalSecs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <section className="card transcript-card" aria-label="Live Medical Transcription">
      {/* Card Title */}
      <div className="card-header">
        <div className="card-title">
          <Mic className="title-icon" size={22} />
          <h2>Live Medical Transcription</h2>
        </div>
      </div>

      {/* Recorder Controls */}
      <RecorderControls
        onStart={onStartMic}
        onStop={onStopMic}
        onClear={onClear}
        onSaveRecording={onSaveRecording}
        isStarting={isStartingMic}
      />

      {/* Transcript Text Region with ARIA live region */}
      <div
        className="transcript-region"
        ref={scrollRef}
        onScroll={handleScroll}
        aria-live="polite"
        aria-atomic="false"
      >
        {!hasContent ? (
          <div className="empty-transcript-state">
            <p className="placeholder-text">
              Ready — click Start Mic and speak naturally. VAD will auto-chunk your speech.
            </p>
          </div>
        ) : (
          <div className="segments-list">
            {segments.map((seg) => (
              <div
                key={seg.seq}
                className={`segment-row ${seg.status === 'failed' ? 'segment-failed' : ''}`}
                data-testid={`segment-${seg.seq}`}
              >
                <div className="segment-meta">
                  <span className="seq-badge">#{seg.seq}</span>
                  <span className="timestamp-range">
                    {formatMs(seg.start_ms)} - {formatMs(seg.end_ms)}
                  </span>
                  {seg.confidence !== null && seg.confidence !== undefined && (
                    <span className="confidence-pill" title={`Whisper confidence: ${(seg.confidence * 100).toFixed(0)}%`}>
                      {(seg.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                  {seg.edited_text && <span className="edited-indicator">(edited)</span>}
                </div>

                <div className="segment-body">
                  {editingSeq === seg.seq ? (
                    <div className="inline-editor">
                      <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        className="edit-textarea"
                        rows={2}
                        autoFocus
                      />
                      <div className="editor-actions">
                        <button className="btn-small btn-save" onClick={() => saveEdit(seg.seq)}>
                          Save
                        </button>
                        <button className="btn-small btn-cancel" onClick={() => setEditingSeq(null)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p
                      className="segment-text"
                      onClick={() => startEdit(seg)}
                      title="Click to edit transcript text"
                    >
                      {seg.edited_text ?? seg.text}
                    </p>
                  )}

                  {seg.status === 'failed' && (
                    <div className="retry-chip" onClick={() => onRetrySegment?.(seg.seq)}>
                      <AlertCircle size={12} />
                      <span>Failed — click to retry</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Jump to latest floating button */}
        {userScrolledUp && hasContent && (
          <button className="jump-to-latest" onClick={jumpToLatest} aria-label="Jump to latest transcript text">
            <ArrowDown size={14} />
            <span>Jump to latest</span>
          </button>
        )}
      </div>

      {/* Full-width Process Transcript Button */}
      <div className="process-action-wrapper">
        <button
          className="btn btn-process full-width"
          onClick={onProcessTranscript}
          disabled={!hasContent || isRecording || isAnalyzing}
          aria-label="Process Transcript with AI"
        >
          {isAnalyzing ? (
            <>
              <RefreshCw size={18} className="spinner-icon" />
              <span>Analyzing Medical Transcript...</span>
            </>
          ) : (
            <>
              <Zap size={18} />
              <span>⚡ Process Transcript with AI</span>
            </>
          )}
        </button>
      </div>
    </section>
  );
};
