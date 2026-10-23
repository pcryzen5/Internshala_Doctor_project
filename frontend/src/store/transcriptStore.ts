/**
 * Zustand store for live transcript segments and speech statistics.
 */

import { create } from 'zustand';
import { TranscriptSegment } from '../lib/types';

function computeWordCount(segments: TranscriptSegment[]): number {
  let count = 0;
  for (const seg of segments) {
    const text = (seg.edited_text !== undefined && seg.edited_text !== null ? seg.edited_text : seg.text).trim();
    if (text) {
      count += text.split(/\s+/).filter(Boolean).length;
    }
  }
  return count;
}

interface TranscriptStoreState {
  segments: TranscriptSegment[];
  isSpeaking: boolean;
  wordCount: number;
  chunkCount: number;
  audioBlobs: Blob[];

  setIsSpeaking: (isSpeaking: boolean) => void;
  upsertSegment: (segment: TranscriptSegment) => void;
  updateSegmentText: (seq: number, text: string) => void;
  addAudioChunk: (blob: Blob) => void;
  clearTranscript: () => void;
  getCombinedText: () => string;
}

export const useTranscriptStore = create<TranscriptStoreState>((set, get) => ({
  segments: [],
  isSpeaking: false,
  wordCount: 0,
  chunkCount: 0,
  audioBlobs: [],

  setIsSpeaking: (isSpeaking) => set({ isSpeaking }),

  upsertSegment: (segment) =>
    set((state) => {
      const existingIdx = state.segments.findIndex((s) => s.seq === segment.seq);
      let updated: TranscriptSegment[];

      if (existingIdx >= 0) {
        updated = [...state.segments];
        updated[existingIdx] = { ...updated[existingIdx], ...segment };
      } else {
        updated = [...state.segments, segment];
      }

      // Maintain strict sort by seq for out-of-order arrival tolerance
      updated.sort((a, b) => a.seq - b.seq);

      return {
        segments: updated,
        wordCount: computeWordCount(updated),
        chunkCount: updated.length,
      };
    }),

  updateSegmentText: (seq, text) =>
    set((state) => {
      const updated = state.segments.map((seg) =>
        seg.seq === seq ? { ...seg, edited_text: text } : seg
      );
      return {
        segments: updated,
        wordCount: computeWordCount(updated),
      };
    }),

  addAudioChunk: (blob) =>
    set((state) => ({
      audioBlobs: [...state.audioBlobs, blob],
    })),

  clearTranscript: () =>
    set({
      segments: [],
      isSpeaking: false,
      wordCount: 0,
      chunkCount: 0,
      audioBlobs: [],
    }),

  getCombinedText: () => {
    const segments = get().segments;
    return segments
      .map((s) => (s.edited_text !== undefined && s.edited_text !== null ? s.edited_text : s.text).trim())
      .filter(Boolean)
      .join(' ');
  },
}));
