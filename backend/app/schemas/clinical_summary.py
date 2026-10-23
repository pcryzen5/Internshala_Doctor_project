"""Clinical summary Pydantic models conforming to DATABASE.md contract."""

from pydantic import BaseModel, Field


class PatientDetails(BaseModel):
    name: str | None = None
    age: str | int | None = None
    sex: str | None = None
    identifiers: list[str] = Field(default_factory=list)


class ChiefComplaint(BaseModel):
    text: str | None = None
    evidence: str | None = None


class HPI(BaseModel):
    onset: str | None = None
    duration: str | None = None
    progression: str | None = None
    aggravating: list[str] = Field(default_factory=list)
    relieving: list[str] = Field(default_factory=list)
    narrative: str | None = None


class SymptomItem(BaseModel):
    name: str
    evidence: str = ""


class Symptoms(BaseModel):
    positive: list[SymptomItem] = Field(default_factory=list)
    negative: list[SymptomItem] = Field(default_factory=list)


class PastMedicalHistory(BaseModel):
    conditions: list[str] = Field(default_factory=list)
    surgeries: list[str] = Field(default_factory=list)
    hospitalisations: list[str] = Field(default_factory=list)


class MedicationItem(BaseModel):
    name: str
    dose: str | None = None
    frequency: str | None = None
    adherence: str | None = None
    evidence: str = ""


class AllergyItem(BaseModel):
    substance: str
    reaction: str | None = None
    evidence: str = ""


class Vitals(BaseModel):
    bp: str | None = None
    hr: str | None = None
    temp: str | None = None
    rr: str | None = None
    spo2: str | None = None
    other: list[str] = Field(default_factory=list)


class Observations(BaseModel):
    vitals: Vitals = Field(default_factory=Vitals)
    examination: list[str] = Field(default_factory=list)
    tests_mentioned: list[str] = Field(default_factory=list)


class Assessment(BaseModel):
    provisional: str | None = None
    differentials: list[str] = Field(default_factory=list)
    stated_by_clinician: bool = True


class Plan(BaseModel):
    investigations: list[str] = Field(default_factory=list)
    prescriptions: list[str] = Field(default_factory=list)
    advice: list[str] = Field(default_factory=list)
    follow_up: str | None = None


class ClinicalSummary(BaseModel):
    patient: PatientDetails = Field(default_factory=PatientDetails)
    chief_complaint: ChiefComplaint = Field(default_factory=ChiefComplaint)
    hpi: HPI = Field(default_factory=HPI)
    symptoms: Symptoms = Field(default_factory=Symptoms)
    past_medical_history: PastMedicalHistory = Field(default_factory=PastMedicalHistory)
    medications: list[MedicationItem] = Field(default_factory=list)
    allergies: list[AllergyItem] = Field(default_factory=list)
    observations: Observations = Field(default_factory=Observations)
    assessment: Assessment = Field(default_factory=Assessment)
    plan: Plan = Field(default_factory=Plan)
    clinical_summary: str = ""
    warnings: list[str] = Field(default_factory=list)
