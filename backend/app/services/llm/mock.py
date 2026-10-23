"""Mock LLM provider for hermetic testing and offline development."""

import re
from typing import Any

from app.services.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Rule-based mock clinical extractor that guarantees schema compliance and evidence quotes."""

    def __init__(self, model_name: str = "mock-clinical-extractor-v1") -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def extract_clinical_summary(
        self,
        transcript: str,
        system_prompt: str,
        error_feedback: str | None = None,
    ) -> dict[str, Any]:
        text_lower = transcript.lower()

        # 1. Patient details extraction
        patient_name: str | None = None
        patient_age: str | int | None = None
        patient_sex: str | None = None

        name_match = re.search(
            r"\b(?:name is|patient is|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            transcript,
            re.IGNORECASE,
        )
        if name_match:
            patient_name = name_match.group(1).strip()
        elif "jane doe" in text_lower:
            patient_name = "Jane Doe"
        elif "john doe" in text_lower:
            patient_name = "John Doe"

        age_match = re.search(r"\b(\d{1,2})\s*(?:years old|yo|year old|y\.o\.)\b", text_lower)
        if age_match:
            patient_age = int(age_match.group(1))

        if "female" in text_lower or " woman " in text_lower:
            patient_sex = "Female"
        elif "male" in text_lower or " man " in text_lower:
            patient_sex = "Male"

        # 2. Chief complaint
        chief_complaint_text: str | None = None
        chief_complaint_ev: str | None = None
        if "fever" in text_lower:
            chief_complaint_text = "Fever and generalized weakness"
            chief_complaint_ev = "I have had fever since two days"
        elif "chest pain" in text_lower:
            chief_complaint_text = "Chest pain on exertion"
            chief_complaint_ev = "having chest pain"
        elif "headache" in text_lower:
            chief_complaint_text = "Severe recurring headache"
            chief_complaint_ev = "headache since morning"

        # 3. Symptoms (strict separation of positive vs negative)
        positive_symptoms: list[dict[str, str]] = []
        negative_symptoms: list[dict[str, str]] = []

        # Check common stated negatives
        if re.search(r"\b(?:no|denies|without)\s+vomiting\b", text_lower):
            negative_symptoms.append({"name": "Vomiting", "evidence": "no vomiting"})
        if re.search(r"\b(?:no|denies|without)\s+fever\b", text_lower):
            negative_symptoms.append({"name": "Fever", "evidence": "no fever"})
        if re.search(r"\b(?:no|denies|without)\s+cough\b", text_lower):
            negative_symptoms.append({"name": "Cough", "evidence": "no cough"})
        if re.search(r"\b(?:no|denies|without)\s+shortness of breath\b", text_lower):
            negative_symptoms.append(
                {"name": "Shortness of breath", "evidence": "no shortness of breath"}
            )

        # Check positive symptoms (if not in negatives)
        if "fever" in text_lower and not any(n["name"] == "Fever" for n in negative_symptoms):
            positive_symptoms.append({"name": "Fever", "evidence": "fever since two days"})
        if "headache" in text_lower:
            positive_symptoms.append({"name": "Headache", "evidence": "throbbing headache"})
        if "cough" in text_lower and not any(n["name"] == "Cough" for n in negative_symptoms):
            positive_symptoms.append({"name": "Cough", "evidence": "dry cough"})
        if "body ache" in text_lower or "bodyache" in text_lower:
            positive_symptoms.append({"name": "Body aches", "evidence": "body aches"})

        # 4. Medications
        medications: list[dict[str, Any]] = []
        if "metformin" in text_lower:
            medications.append(
                {
                    "name": "Metformin",
                    "dose": "500 mg",
                    "frequency": "Twice daily",
                    "adherence": "Adherent",
                    "evidence": "taking metformin 500 mg twice daily",
                }
            )
        if "paracetamol" in text_lower or "crocin" in text_lower or "tylenol" in text_lower:
            medications.append(
                {
                    "name": "Paracetamol",
                    "dose": "650 mg",
                    "frequency": "As needed",
                    "adherence": None,
                    "evidence": "took paracetamol 650",
                }
            )

        # 5. Allergies
        allergies: list[dict[str, Any]] = []
        if "penicillin" in text_lower and "allergic" in text_lower:
            allergies.append(
                {
                    "substance": "Penicillin",
                    "reaction": "Rash / Hives",
                    "evidence": "allergic to penicillin",
                }
            )
        if "sulfa" in text_lower and "allergic" in text_lower:
            allergies.append(
                {
                    "substance": "Sulfa drugs",
                    "reaction": "Unknown",
                    "evidence": "allergic to sulfa",
                }
            )

        # 6. Observations / Vitals
        vitals: dict[str, Any] = {
            "bp": "120/80 mmHg"
            if "120/80" in transcript or "blood pressure" in text_lower
            else None,
            "hr": "78 bpm" if "pulse" in text_lower or "heart rate" in text_lower else None,
            "temp": "101.4 F" if "101" in transcript or "temp" in text_lower else None,
            "rr": None,
            "spo2": "98%" if "oxygen" in text_lower or "spo2" in text_lower else None,
            "other": [],
        }

        # 7. Assessment
        provisional: str | None = None
        if "viral" in text_lower or "fever" in text_lower:
            provisional = "Acute Viral Syndrome"
        elif "migraine" in text_lower:
            provisional = "Migraine without aura"
        elif "diabetes" in text_lower:
            provisional = "Type 2 Diabetes Mellitus"

        # 8. Plan
        plan_prescriptions: list[str] = []
        if "paracetamol" in text_lower or "fever" in text_lower:
            plan_prescriptions.append("Tab. Paracetamol 650 mg TID for 3 days")
        if "metformin" in text_lower:
            plan_prescriptions.append("Continue Tab. Metformin 500 mg BD")

        advice: list[str] = [
            "Adequate oral hydration and rest",
            "Return immediately if symptoms worsen or high fever persists",
        ]

        pos_str = ", ".join(s["name"] for s in positive_symptoms) if positive_symptoms else "None"
        neg_str = ", ".join(s["name"] for s in negative_symptoms) if negative_symptoms else "None"
        summary_text = (
            f"Patient presented with complaints of {chief_complaint_text or 'symptoms discussed'}. "
            f"Positive symptoms noted: {pos_str}. "
            f"Denies: {neg_str}. "
            f"Clinical impression: {provisional or 'Under evaluation'}. "
            f"Treatment plan discussed including symptomatic management and follow-up."
        )

        return {
            "patient": {
                "name": patient_name,
                "age": patient_age,
                "sex": patient_sex,
                "identifiers": [],
            },
            "chief_complaint": {
                "text": chief_complaint_text,
                "evidence": chief_complaint_ev,
            },
            "hpi": {
                "onset": "2 days ago" if "two days" in text_lower else None,
                "duration": "2 days" if "two days" in text_lower else None,
                "progression": "Gradual onset" if "gradual" in text_lower else None,
                "aggravating": [],
                "relieving": ["Paracetamol"] if "paracetamol" in text_lower else [],
                "narrative": transcript[:200] if transcript else None,
            },
            "symptoms": {
                "positive": positive_symptoms,
                "negative": negative_symptoms,
            },
            "past_medical_history": {
                "conditions": ["Hypertension"] if "hypertension" in text_lower else [],
                "surgeries": [],
                "hospitalisations": [],
            },
            "medications": medications,
            "allergies": allergies,
            "observations": {
                "vitals": vitals,
                "examination": ["Chest clear to auscultation"] if "chest" in text_lower else [],
                "tests_mentioned": ["Complete Blood Count (CBC)"]
                if "blood test" in text_lower or "cbc" in text_lower
                else [],
            },
            "assessment": {
                "provisional": provisional,
                "differentials": [],
                "stated_by_clinician": True,
            },
            "plan": {
                "investigations": ["Complete Blood Count (CBC)"] if "cbc" in text_lower else [],
                "prescriptions": plan_prescriptions,
                "advice": advice,
                "follow_up": "In 3 days if fever does not resolve",
            },
            "clinical_summary": summary_text,
            "warnings": [],
        }
