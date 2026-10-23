/**
 * Clinical transcription and summary TypeScript contracts.
 * Matches docs/DATABASE.md and docs/API.md.
 */

export interface PatientDetails {
  name: string | null;
  age: string | number | null;
  sex: string | null;
  identifiers: string[];
}

export interface ChiefComplaint {
  text: string | null;
  evidence: string | null;
}

export interface HPI {
  onset: string | null;
  duration: string | null;
  progression: string | null;
  aggravating: string[];
  relieving: string[];
  narrative: string | null;
}

export interface SymptomItem {
  name: string;
  evidence: string;
}

export interface Symptoms {
  positive: SymptomItem[];
  negative: SymptomItem[];
}

export interface PastMedicalHistory {
  conditions: string[];
  surgeries: string[];
  hospitalisations: string[];
}

export interface MedicationItem {
  name: string;
  dose: string | null;
  frequency: string | null;
  adherence: string | null;
  evidence: string;
}

export interface AllergyItem {
  substance: string;
  reaction: string | null;
  evidence: string;
}

export interface Vitals {
  bp: string | null;
  hr: string | null;
  temp: string | null;
  rr: string | null;
  spo2: string | null;
  other: string[];
}

export interface Observations {
  vitals: Vitals;
  examination: string[];
  tests_mentioned: string[];
}

export interface Assessment {
  provisional: string | null;
  differentials: string[];
  stated_by_clinician: boolean;
}

export interface Plan {
  investigations: string[];
  prescriptions: string[];
  advice: string[];
  follow_up: string | null;
}

export interface ClinicalSummary {
  patient: PatientDetails;
  chief_complaint: ChiefComplaint;
  hpi: HPI;
  symptoms: Symptoms;
  past_medical_history: PastMedicalHistory;
  medications: MedicationItem[];
  allergies: AllergyItem[];
  observations: Observations;
  assessment: Assessment;
  plan: Plan;
  clinical_summary: string;
  warnings: string[];
}

export interface TranscriptSegment {
  id?: string;
  seq: number;
  text: string;
  edited_text?: string | null;
  start_ms: number;
  end_ms: number;
  confidence?: number | null;
  status: 'done' | 'transcribing' | 'failed';
  created_at?: string;
}

export interface SessionData {
  id: string;
  user_id: string;
  status: 'ready' | 'recording' | 'analyzing' | 'reviewed' | 'failed';
  language: string;
  patient_label: string | null;
  duration_seconds: number | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
  segments: TranscriptSegment[];
  latest_summary: {
    id: string;
    version: number;
    source: string;
    model: string;
    prompt_version: string;
    data: ClinicalSummary;
    created_at: string;
  } | null;
}

export interface SessionListItem {
  id: string;
  status: string;
  language: string;
  patient_label: string | null;
  duration_seconds: number | null;
  created_at: string;
  updated_at: string;
  segment_count: number;
  has_summary: boolean;
}

export interface SessionListResponse {
  items: SessionListItem[];
  total: number;
}
