/**
 * Right Card — AI Medical Summary Panel.
 * Implements the 9 structured clinical sections, patient details, and "Copy to Prescription".
 */

import React, { useState } from 'react';
import {
  FileText,
  AlertCircle,
  Pill,
  ShieldAlert,
  ClipboardList,
  Calendar,
  Copy,
  Check,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { useSessionStore } from '../../store/sessionStore';
import { useSummaryStore } from '../../store/summaryStore';
import './SummaryPanel.css';

interface SummaryPanelProps {
  onClear: () => void;
}

export const SummaryPanel: React.FC<SummaryPanelProps> = ({ onClear }) => {
  const { patientName, patientAgeGender, setPatientName, setPatientAgeGender } = useSessionStore();
  const { summary, isAnalyzing, isOutOfDate, updateClinicalSummaryText } = useSummaryStore();
  const [copied, setCopied] = useState(false);

  const handleCopyPrescription = async () => {
    if (!summary) return;

    const pat = `${patientName || 'Not recorded'}, ${patientAgeGender || 'Unknown'}`;
    const chief = summary.chief_complaint?.text || 'None stated';
    const pos = summary.symptoms?.positive?.map((s) => s.name).join(', ') || 'None';
    const neg = summary.symptoms?.negative?.map((s) => s.name).join(', ') || 'None';
    const impression = summary.assessment?.provisional || 'Under clinical evaluation';

    const meds = summary.medications?.length
      ? summary.medications
          .map((m) => `${m.name} ${m.dose || ''} (${m.frequency || 'daily'})`.trim())
          .join('; ')
      : 'No current medications recorded';

    const allergies = summary.allergies?.length
      ? summary.allergies
          .map((a) => `${a.substance} (${a.reaction || 'reaction unknown'})`)
          .join('; ')
      : 'No known allergies stated';

    const planParts: string[] = [];
    if (summary.plan?.prescriptions?.length) {
      planParts.push(`Rx: ${summary.plan.prescriptions.join(', ')}`);
    }
    if (summary.plan?.investigations?.length) {
      planParts.push(`Labs: ${summary.plan.investigations.join(', ')}`);
    }
    if (summary.plan?.follow_up) {
      planParts.push(`Follow-up: ${summary.plan.follow_up}`);
    }
    const planText = planParts.length ? planParts.join(' | ') : 'Follow-up as needed';

    const formatted = `Patient: ${pat}\nChief complaint: ${chief}\nSymptoms: + ${pos} ; − ${neg}\nImpression: ${impression}\nMedications: ${meds}\nAllergies: ${allergies}\nPlan / Follow-up: ${planText}\n`;

    try {
      await navigator.clipboard.writeText(formatted);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy to clipboard', err);
    }
  };

  const hasPositiveSymptoms = (summary?.symptoms?.positive?.length ?? 0) > 0;
  const hasNegativeSymptoms = (summary?.symptoms?.negative?.length ?? 0) > 0;
  const hasSymptoms = hasPositiveSymptoms || hasNegativeSymptoms;

  return (
    <section className="card summary-card" aria-label="AI Medical Summary">
      {/* Card Header */}
      <div className="summary-card-header">
        <div className="summary-title-group">
          {isAnalyzing ? (
            <Sparkles className="spinner-icon" size={22} />
          ) : (
            <FileText size={22} />
          )}
          <h2>AI Medical Summary</h2>
        </div>

        <div className="summary-header-actions">
          <button
            className="btn-header-clear"
            onClick={onClear}
            disabled={!summary || isAnalyzing}
            aria-label="Clear Summary"
          >
            <RotateCcw size={14} />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Out-of-date banner */}
      {isOutOfDate && (
        <div className="out-of-date-banner" role="alert">
          <AlertCircle size={16} />
          <span>Summary out of date — Re-process transcript for updated analysis.</span>
        </div>
      )}

      {/* Patient details block */}
      <div className="patient-header-block">
        <div className="patient-field">
          <label htmlFor="patient-name">Patient Name</label>
          <input
            id="patient-name"
            className="patient-input"
            value={summary?.patient?.name || patientName}
            onChange={(e) => setPatientName(e.target.value)}
            placeholder="e.g. Jane Doe"
          />
        </div>
        <div className="patient-field">
          <label htmlFor="patient-age-gender">Age / Gender</label>
          <input
            id="patient-age-gender"
            className="patient-input"
            value={
              summary?.patient?.age && summary?.patient?.sex
                ? `${summary.patient.age} / ${summary.patient.sex}`
                : patientAgeGender
            }
            onChange={(e) => setPatientAgeGender(e.target.value)}
            placeholder="e.g. 42 / F"
          />
        </div>
      </div>

      {/* Scrollable Summary Body */}
      <div className="summary-scroll-body">
        {/* 1. Clinical Summary */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Clinical Summary</span>
            <span className="section-divider" />
          </div>
          <textarea
            className="clinical-summary-textarea"
            value={summary?.clinical_summary || ''}
            onChange={(e) => updateClinicalSummaryText(e.target.value)}
            placeholder="AI-generated clinical summary will appear here…"
          />
        </div>

        {/* 2. Chief Complaints */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Chief Complaints</span>
            <span className="section-divider" />
          </div>
          {summary?.chief_complaint?.text ? (
            <div className="chief-complaint-content">
              <p>{summary.chief_complaint.text}</p>
              {summary.chief_complaint.evidence && (
                <span className="evidence-badge">
                  Evidence: "{summary.chief_complaint.evidence}"
                </span>
              )}
            </div>
          ) : (
            <p className="empty-state-text">No complaints extracted yet</p>
          )}
        </div>

        {/* 3. Symptoms */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Symptoms</span>
            <span className="section-divider" />
          </div>
          {hasSymptoms ? (
            <div className="symptoms-groups">
              {hasPositiveSymptoms && (
                <div className="symptom-subgroup">
                  <span className="subgroup-title">Present (+)</span>
                  <div className="chips-wrap">
                    {summary?.symptoms.positive.map((s, i) => (
                      <span key={i} className="chip chip-positive" title={s.evidence}>
                        + {s.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {hasNegativeSymptoms && (
                <div className="symptom-subgroup">
                  <span className="subgroup-title">Absent / Denied (−)</span>
                  <div className="chips-wrap">
                    {summary?.symptoms.negative.map((s, i) => (
                      <span key={i} className="chip chip-negative" title={s.evidence}>
                        − {s.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="empty-state-text">No symptoms extracted yet</p>
          )}
        </div>

        {/* 4. Clinical Impression */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Clinical Impression</span>
            <span className="section-divider" />
          </div>
          {summary?.assessment?.provisional ? (
            <div className="impression-box">
              <p className="impression-provisional">{summary.assessment.provisional}</p>
              {summary.assessment.differentials?.length > 0 && (
                <div className="differentials-row">
                  {summary.assessment.differentials.map((d, i) => (
                    <span key={i} className="diff-chip">
                      Diff: {d}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="empty-state-text">No diagnosis inferred</p>
          )}
        </div>

        {/* 5. Medications */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Medications</span>
            <span className="section-divider" />
          </div>
          {summary?.medications?.length ? (
            <div className="item-list">
              {summary.medications.map((m, i) => (
                <div key={i} className="medication-card">
                  <div className="med-header">
                    <span className="med-name">
                      <Pill size={14} style={{ display: 'inline', marginRight: 4 }} />
                      {m.name}
                    </span>
                    {m.dose && <span className="med-dosage">{m.dose}</span>}
                  </div>
                  <div className="med-sub">
                    {m.frequency && <span>Freq: {m.frequency}</span>}
                    {m.adherence && <span> • Adherence: {m.adherence}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state-text">No medications extracted yet</p>
          )}
        </div>

        {/* 6. Examinations & Tests */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Examinations & Tests</span>
            <span className="section-divider" />
          </div>
          {summary?.observations?.vitals?.bp ||
          summary?.observations?.vitals?.hr ||
          summary?.observations?.vitals?.temp ||
          summary?.observations?.examination?.length ? (
            <div>
              <div className="vitals-grid">
                {summary.observations.vitals.bp && (
                  <div className="vital-pill">
                    <div className="vital-name">BP</div>
                    <div className="vital-val">{summary.observations.vitals.bp}</div>
                  </div>
                )}
                {summary.observations.vitals.hr && (
                  <div className="vital-pill">
                    <div className="vital-name">HR</div>
                    <div className="vital-val">{summary.observations.vitals.hr}</div>
                  </div>
                )}
                {summary.observations.vitals.temp && (
                  <div className="vital-pill">
                    <div className="vital-name">Temp</div>
                    <div className="vital-val">{summary.observations.vitals.temp}</div>
                  </div>
                )}
                {summary.observations.vitals.spo2 && (
                  <div className="vital-pill">
                    <div className="vital-name">SpO2</div>
                    <div className="vital-val">{summary.observations.vitals.spo2}</div>
                  </div>
                )}
              </div>
              {summary.observations.examination?.length ? (
                <ul className="observations-list">
                  {summary.observations.examination.map((ex, i) => (
                    <li key={i}>{ex}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : (
            <p className="empty-state-text">No examinations extracted yet</p>
          )}
        </div>

        {/* 7. Allergies */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Allergies</span>
            <span className="section-divider" />
          </div>
          {summary?.allergies?.length ? (
            <div className="item-list">
              {summary.allergies.map((a, i) => (
                <div key={i} className="allergy-card">
                  <div className="allergy-header">
                    <span className="allergy-name">
                      <ShieldAlert size={14} style={{ display: 'inline', marginRight: 4 }} />
                      {a.substance}
                    </span>
                    {a.reaction && <span className="med-dosage">{a.reaction}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state-text">No allergies extracted yet</p>
          )}
        </div>

        {/* 8. Past Medical History */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">Past Medical History</span>
            <span className="section-divider" />
          </div>
          {summary?.past_medical_history?.conditions?.length ||
          summary?.past_medical_history?.surgeries?.length ? (
            <div className="chips-wrap">
              {summary.past_medical_history.conditions?.map((c, i) => (
                <span key={i} className="chip">
                  <ClipboardList size={12} /> {c}
                </span>
              ))}
              {summary.past_medical_history.surgeries?.map((s, i) => (
                <span key={i} className="chip">
                  Surgery: {s}
                </span>
              ))}
            </div>
          ) : (
            <p className="empty-state-text">No past medical history extracted</p>
          )}
        </div>

        {/* 9. History & Follow-up */}
        <div className="summary-section">
          <div className="section-label-row">
            <span className="section-label">History & Follow-up</span>
            <span className="section-divider" />
          </div>
          {summary?.hpi?.narrative || summary?.plan?.follow_up || summary?.plan?.prescriptions?.length ? (
            <div className="chief-complaint-content">
              {summary?.hpi?.narrative && <p><strong>HPI:</strong> {summary.hpi.narrative}</p>}
              {summary?.plan?.prescriptions?.length ? (
                <p><strong>Rx:</strong> {summary.plan.prescriptions.join(', ')}</p>
              ) : null}
              {summary?.plan?.follow_up && (
                <p>
                  <Calendar size={13} style={{ display: 'inline', marginRight: 4 }} />
                  <strong>Follow-up:</strong> {summary.plan.follow_up}
                </p>
              )}
            </div>
          ) : (
            <p className="empty-state-text">No history or follow-up plan noted</p>
          )}
        </div>
      </div>

      {/* Sticky Footer */}
      <div className="summary-footer">
        <button
          className="btn-copy-prescription"
          onClick={handleCopyPrescription}
          disabled={!summary || isAnalyzing}
          aria-label="Copy to Prescription"
        >
          {copied ? <Check size={18} /> : <Copy size={18} />}
          <span>{copied ? 'Copied to Prescription!' : 'Copy to Prescription'}</span>
        </button>
        {copied && <div className="toast-feedback">Formatted prescription copied to clipboard</div>}
      </div>
    </section>
  );
};
