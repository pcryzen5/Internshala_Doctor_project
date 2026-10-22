# PRD — Live Medical Transcription & Clinical Summary

## 1. Overview
A web app that listens to a doctor–patient consultation through the microphone, shows the transcript live, and when the session ends turns the full transcript into a structured clinical summary suitable for a medical record.

## 2. Problem
Clinicians spend large parts of each consultation typing notes. Free-text notes are inconsistent, and key facts (allergies, negatives, follow-up) get missed. The goal is to capture the conversation hands-free and produce a consistent structured draft that the clinician reviews and approves.

## 3. Target users
- **Primary:** doctors / clinicians conducting consultations.
- **Secondary:** clinic staff reviewing or copying notes into a prescription or EHR.
- **Evaluator context:** this is also a project submission, so the pipeline (audio → VAD → ASR → LLM → structured output) must be clearly demonstrable.

## 4. Goals
1. Capture live microphone audio in the browser.
2. Use Voice Activity Detection (VAD) so silence and background noise never reach the recogniser.
3. Convert speech to text with an ASR model (Whisper family).
4. Display the transcript live as it is produced.
5. On session completion, send the full transcript to an LLM.
6. Extract structured medical information (schema in section 6).
7. Generate a concise clinical summary for a medical record.

## 5. Non-goals (v1)
- Speaker diarisation (doctor vs patient labelling) — listed as a stretch goal.
- Direct integration with a hospital EHR / HL7 / FHIR (export only).
- Mobile native apps.
- Autonomous diagnosis. The AI only extracts what was *stated*; it never invents clinical content.

## 6. Structured output (required fields)
| Field group | Contents |
|---|---|
| Patient details | Name, age, sex, identifiers mentioned |
| Chief complaint | Primary reason for visit, in the patient's own terms |
| History of present illness | Onset, duration, progression, aggravating and relieving factors |
| Symptoms | Discrete list; positives and stated negatives kept separate |
| Past medical history | Prior conditions, surgeries, hospitalisations |
| Medication history | Current medicines, dosages, adherence, known allergies |
| Clinical observations | Vitals and examination findings stated aloud |
| Assessment | Provisional diagnosis or differentials as stated by the clinician |
| Plan | Investigations, prescriptions, advice, follow-up |

## 7. Functional requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Start / Stop microphone capture with browser permission handling | Must |
| FR-2 | Client-side VAD segments speech; only speech segments are uploaded | Must |
| FR-3 | Each segment is transcribed and appended to the live transcript within ~3 s of speech end | Must |
| FR-4 | Live counters: words and chunks | Should |
| FR-5 | Clear button resets transcript and summary (with confirm if unsaved) | Must |
| FR-6 | Save Recording: download session audio and/or transcript | Should |
| FR-7 | "Process Transcript with AI" sends full transcript to LLM and returns structured JSON | Must |
| FR-8 | Summary panel renders all fields; empty states ("No symptoms extracted yet") | Must |
| FR-9 | Clinical summary text is editable by the clinician before use | Must |
| FR-10 | "Copy to Prescription" copies a formatted summary to clipboard | Should |
| FR-11 | Transcript is editable so ASR mistakes can be fixed before processing | Should |
| FR-12 | Session history: list, reopen, delete past sessions | Should |
| FR-13 | Floating assistant chat bubble to ask questions about the current transcript | Could |
| FR-14 | Patient name / age / sex shown in the summary header, editable | Must |

## 8. Non-functional requirements
- **Latency:** transcript chunk visible ≤ 3 s after speech pause (GPU) / ≤ 6 s (CPU).
- **Accuracy:** extraction must not hallucinate — absent fields are `null` / empty, never guessed.
- **Privacy:** health data is sensitive; see SECURITY.md.
- **Browser support:** latest Chrome, Edge, Firefox, Safari (HTTPS or localhost required for mic).
- **Responsiveness:** usable from 360 px to desktop; two-panel layout collapses to tabs on mobile.
- **Accessibility:** keyboard operable, ARIA live region for transcript, sufficient contrast.

## 9. Success metrics
- Word error rate on a test set of simulated consultations ≤ 15 %.
- Field-level extraction F1 ≥ 0.85 on the labelled test transcripts.
- Zero fabricated medications / allergies in the evaluation set.
- End-to-end demo: speak → live text → summary in under 30 s after pressing Process.

## 10. Risks
| Risk | Mitigation |
|---|---|
| ASR errors on drug names | Editable transcript; optional medical vocabulary prompt for Whisper |
| LLM hallucination | Strict JSON schema, "only from transcript" prompt, evidence quotes, human review |
| Latency on CPU | Smaller Whisper model, chunking by VAD, option to use hosted API |
| Privacy / compliance | Encryption, no training on data, retention controls, consent banner |
| Mic permission / HTTPS issues | Clear error states and setup docs |

## 11. Out-of-scope disclaimer
The tool produces a **draft** for clinician review. It is not a medical device and must not be used as the sole basis for clinical decisions.
