# DESIGN — UI / UX Specification

Derived from the reference screenshots: a rounded two-panel layout, indigo/violet primary, soft borders, light grey surfaces.

## 1. Layout
- Page header: app/hospital name (right side), light background, subtle bottom shadow.
- Main: **two cards side by side** (≈ 50/50 on desktop).
  - **Left card — "Live Medical Transcription"**
  - **Right card — "AI Medical Summary"**
- Floating circular **chat bubble** (bottom-right) for the assistant (stretch).
- Mobile (< 900 px): cards stack; or tabs "Transcript | Summary".

## 2. Left card — Live Medical Transcription
Top to bottom:
1. Title with mic icon.
2. Button row: **Start Mic** (filled primary), **Stop** (red outline), **Clear** (grey outline), **Save Recording** (green outline).
3. Stat pills: `WORDS: n`, `CHUNKS: n`.
4. **Live strip** — small box showing the in-progress segment / VAD activity indicator (pulsing when speech detected).
5. **Transcript area** — large scrollable text region. Placeholder: *"Ready — click Start Mic and speak naturally. VAD will auto-chunk your speech."*
6. Full-width primary button **⚡ Process Transcript with AI**.

### Button states
| Button | Idle | Recording | Processing |
|---|---|---|---|
| Start Mic | enabled | disabled | disabled |
| Stop | disabled | enabled | disabled |
| Clear | enabled if content | disabled | disabled |
| Save Recording | enabled if audio/text | disabled | enabled |
| Process Transcript | enabled if text ≥ 1 segment | disabled | loading spinner, disabled |

## 3. Right card — AI Medical Summary
Header: title with hourglass icon (spinner while processing), **✕ Clear** at top-right.
Patient block: **Patient Name**, **Age / Gender** (inline editable).

Sections (uppercase small label with icon and a hairline divider; empty-state text centred in grey):
| Order | Section | Empty text |
|---|---|---|
| 1 | Clinical Summary (editable textarea) | "AI-generated clinical summary will appear here…" |
| 2 | Chief Complaints | "No complaints extracted yet" |
| 3 | Symptoms (positive / negative groups) | "No symptoms extracted yet" |
| 4 | Clinical Impression | "No diagnosis inferred" |
| 5 | Medications | "No medications extracted yet" |
| 6 | Examinations & Tests | "No examinations extracted yet" |
| 7 | Allergies | "No allergies extracted yet" |
| 8 | Past Medical History | "No past medical history extracted" |
| 9 | History & Follow-up | (HPI + plan/follow-up) |

Footer (sticky): **Copy to Prescription** full-width primary button.
The summary body scrolls independently with a slim scrollbar.

## 4. Design tokens
```css
:root {
  --primary: #6c6cff;       /* indigo-violet buttons/titles */
  --primary-hover: #5757e6;
  --danger: #ff4d2e;        /* Stop */
  --success: #1f8a4c;       /* Save Recording */
  --text: #1f2937;
  --text-muted: #6b7280;
  --text-faint: #9ca3af;
  --surface: #ffffff;
  --surface-alt: #f8fafc;   /* transcript + inputs */
  --border: #e2e8f0;
  --radius-card: 28px;
  --radius-control: 999px;  /* pill buttons */
  --radius-field: 20px;
  --shadow-card: 0 4px 20px rgba(80, 90, 140, 0.08);
  --font: "Inter", system-ui, sans-serif;
}
```
Dark theme: invert surfaces, keep primary; honour `prefers-color-scheme`.

## 5. Typography
- Card titles: 20–22 px / 600, primary colour.
- Section labels: 12 px / 700, letter-spacing 0.12em, uppercase, slate.
- Body: 15–16 px / 400, line-height 1.6.

## 6. Interaction details
- Transcript auto-scrolls unless the user scrolled up (then show "Jump to latest").
- New text fades in; low-confidence words subtly underlined (stretch).
- Extracted items are chips/list rows; click to edit inline; each shows evidence quote on hover/tap.
- Toasts for copy success / errors. Confirm dialog before Clear if unsaved edits exist.
- Mic permission prompt explained before the browser prompt appears.

## 7. Accessibility
- All icon buttons labelled; focus rings visible.
- Transcript region `aria-live="polite"`.
- Colour is never the only signal (recording state also has text + icon).
- Contrast ≥ 4.5:1; check `--text-faint` on `--surface-alt` for placeholder-only use.

## 8. Responsive rules
- ≥ 1100 px: side-by-side.
- 700–1100 px: side-by-side with reduced padding.
- < 700 px: stacked, sticky bottom action bar for Start/Stop.
