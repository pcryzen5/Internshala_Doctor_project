/**
 * Typed REST API client communicating with FastAPI backend.
 */

import { ClinicalSummary, SessionData, SessionListResponse, TranscriptSegment } from './types';

const BASE_URL = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `API request failed with status ${res.status}`;
    try {
      const err = await res.json();
      if (err.error?.message) {
        message = err.error.message;
      }
    } catch {
      // Ignore JSON parse failure on non-JSON response
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export async function createSession(language = 'en', patientLabel?: string): Promise<SessionData> {
  const res = await fetch(`${BASE_URL}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language, patient_label: patientLabel }),
  });
  return handleResponse<SessionData>(res);
}

export async function getSession(sessionId: string): Promise<SessionData> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}`);
  return handleResponse<SessionData>(res);
}

export async function listSessions(limit = 50, offset = 0): Promise<SessionListResponse> {
  const res = await fetch(`${BASE_URL}/sessions?limit=${limit}&offset=${offset}`);
  return handleResponse<SessionListResponse>(res);
}

export async function updateSession(
  sessionId: string,
  payload: { status?: string; patient_label?: string }
): Promise<SessionData> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<SessionData>(res);
}

export async function clearSession(sessionId: string): Promise<SessionData> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/clear`, {
    method: 'POST',
  });
  return handleResponse<SessionData>(res);
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete session: status ${res.status}`);
  }
}

export async function uploadSegmentREST(
  sessionId: string,
  seq: number,
  wavBlob: Blob
): Promise<TranscriptSegment> {
  const formData = new FormData();
  formData.append('seq', seq.toString());
  formData.append('audio', wavBlob, `segment_${seq}.wav`);

  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/segments`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<TranscriptSegment>(res);
}

export async function updateSegmentText(
  sessionId: string,
  seq: number,
  editedText: string
): Promise<TranscriptSegment> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/segments/${seq}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ edited_text: editedText }),
  });
  return handleResponse<TranscriptSegment>(res);
}

export async function getTranscript(
  sessionId: string
): Promise<{ text: string; segments: TranscriptSegment[] }> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/transcript`);
  return handleResponse<{ text: string; segments: TranscriptSegment[] }>(res);
}

export interface AnalyzeResponse {
  summary_id: string;
  version: number;
  model: string;
  data: ClinicalSummary;
}

export async function analyzeSession(
  sessionId: string,
  useEdited = true,
  language = 'en'
): Promise<AnalyzeResponse> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ use_edited: useEdited, language }),
  });
  return handleResponse<AnalyzeResponse>(res);
}
