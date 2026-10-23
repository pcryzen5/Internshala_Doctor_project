/**
 * Zustand store for structured clinical summary extraction and editing.
 */

import { create } from 'zustand';
import { ClinicalSummary } from '../lib/types';

export function createEmptySummary(): ClinicalSummary {
  return {
    patient: { name: null, age: null, sex: null, identifiers: [] },
    chief_complaint: { text: null, evidence: null },
    hpi: {
      onset: null,
      duration: null,
      progression: null,
      aggravating: [],
      relieving: [],
      narrative: null,
    },
    symptoms: { positive: [], negative: [] },
    past_medical_history: { conditions: [], surgeries: [], hospitalisations: [] },
    medications: [],
    allergies: [],
    observations: {
      vitals: { bp: null, hr: null, temp: null, rr: null, spo2: null, other: [] },
      examination: [],
      tests_mentioned: [],
    },
    assessment: { provisional: null, differentials: [], stated_by_clinician: true },
    plan: { investigations: [], prescriptions: [], advice: [], follow_up: null },
    clinical_summary: '',
    warnings: [],
  };
}

interface SummaryStoreState {
  summary: ClinicalSummary | null;
  summaryId: string | null;
  version: number;
  isAnalyzing: boolean;
  isOutOfDate: boolean;
  error: string | null;

  setSummary: (summary: ClinicalSummary, summaryId?: string, version?: number) => void;
  updateClinicalSummaryText: (text: string) => void;
  setIsAnalyzing: (loading: boolean) => void;
  setError: (error: string | null) => void;
  markOutOfDate: (outOfDate: boolean) => void;
  clearSummary: () => void;
}

export const useSummaryStore = create<SummaryStoreState>((set) => ({
  summary: null,
  summaryId: null,
  version: 0,
  isAnalyzing: false,
  isOutOfDate: false,
  error: null,

  setSummary: (summary, summaryId, version = 1) =>
    set({
      summary,
      summaryId: summaryId || null,
      version,
      isOutOfDate: false,
      error: null,
    }),

  updateClinicalSummaryText: (text) =>
    set((state) => {
      if (!state.summary) return state;
      return {
        summary: {
          ...state.summary,
          clinical_summary: text,
        },
      };
    }),

  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
  setError: (error) => set({ error }),
  markOutOfDate: (isOutOfDate) => set({ isOutOfDate }),
  clearSummary: () =>
    set({
      summary: null,
      summaryId: null,
      version: 0,
      isAnalyzing: false,
      isOutOfDate: false,
      error: null,
    }),
}));
