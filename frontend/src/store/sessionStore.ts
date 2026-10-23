/**
 * Zustand store for consultation session state and lifecycle.
 */

import { create } from 'zustand';

export type SessionState =
  | 'idle'
  | 'listening'
  | 'capturing'
  | 'ready'
  | 'analyzing'
  | 'reviewed'
  | 'failed';

interface SessionStoreState {
  sessionId: string | null;
  status: SessionState;
  patientName: string;
  patientAgeGender: string;
  wsStatus: 'connecting' | 'connected' | 'disconnected';
  queueDepth: number;
  errorMessage: string | null;

  setSessionId: (id: string | null) => void;
  setStatus: (status: SessionState) => void;
  setPatientName: (name: string) => void;
  setPatientAgeGender: (ageGender: string) => void;
  setWsStatus: (wsStatus: 'connecting' | 'connected' | 'disconnected') => void;
  setQueueDepth: (depth: number) => void;
  setErrorMessage: (msg: string | null) => void;
  resetSession: () => void;
}

export const useSessionStore = create<SessionStoreState>((set) => ({
  sessionId: null,
  status: 'idle',
  patientName: 'Jane Doe',
  patientAgeGender: '42 / F',
  wsStatus: 'disconnected',
  queueDepth: 0,
  errorMessage: null,

  setSessionId: (sessionId) => set({ sessionId }),
  setStatus: (status) => set({ status }),
  setPatientName: (patientName) => set({ patientName }),
  setPatientAgeGender: (patientAgeGender) => set({ patientAgeGender }),
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setQueueDepth: (queueDepth) => set({ queueDepth }),
  setErrorMessage: (errorMessage) => set({ errorMessage }),
  resetSession: () =>
    set({
      status: 'idle',
      errorMessage: null,
      queueDepth: 0,
      wsStatus: 'disconnected',
    }),
}));
