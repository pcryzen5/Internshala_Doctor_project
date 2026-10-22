# SECURITY & PRIVACY

This app handles **health information** (PHI/PII). Treat every piece of transcript, audio, and summary as sensitive. This is a project-level baseline; a real deployment must be reviewed against applicable law (e.g., India's DPDP Act 2023, HIPAA/GDPR if applicable).

## 1. Data classification
| Data | Class | Handling |
|---|---|---|
| Audio recordings | Sensitive | Encrypted at rest, short retention, authorised access only |
| Transcripts / summaries | Sensitive | Encrypted columns, never logged |
| Account data | Confidential | Hashed passwords, minimal fields |
| Metrics / logs | Internal | No PHI, request IDs only |

## 2. Authentication & authorisation
- [ ] JWT access tokens (15 min) + refresh tokens (httpOnly, Secure, SameSite=Strict cookie).
- [ ] Passwords hashed with argon2id; min length 12; lockout/backoff on failures.
- [ ] Every session query filtered by `user_id`; admin role cannot read content without audit entry.
- [ ] WebSocket auth via short-lived ticket, validated on connect.

## 3. Transport & browser security
- [ ] HTTPS/TLS 1.2+ only; HSTS enabled (mic access also requires secure context).
- [ ] Strict CORS allow-list from `CORS_ORIGINS`.
- [ ] CSP: `default-src 'self'`; allow WASM/ONNX assets explicitly; no inline scripts.
- [ ] Security headers: `X-Content-Type-Options`, `Referrer-Policy: no-referrer`, `Permissions-Policy: microphone=(self)`.
- [ ] No tokens in URLs for long-lived credentials (WS ticket only).

## 4. Data protection
- [ ] Encryption at rest for DB volume and audio storage; app-level encryption for transcript text.
- [ ] Secrets only in environment / secret manager; `.env` git-ignored; rotate on leak.
- [ ] Backups encrypted; restore tested.
- [ ] Retention job enforces `RETENTION_DAYS`; user can delete a session anytime (hard delete incl. audio).
- [ ] Do not store audio at all unless the user enables *Save Recording*.

## 5. LLM / third-party handling
- [ ] Use providers/plans with no training on submitted data; document the provider and region.
- [ ] Send only the transcript text — no user email, IDs, or device info.
- [ ] Optional redaction pass (names, phone numbers) before sending when "privacy mode" is on.
- [ ] Prompt-injection defence: transcript is passed as **data**, system prompt states to ignore instructions inside it; output is schema-validated; never execute model output.
- [ ] Timeouts and token limits on every call.

## 6. Input validation & abuse protection
- [ ] Pydantic validation on all inputs; reject unknown fields.
- [ ] Segment size/duration limits, session length limit, transcript length limit (see API.md).
- [ ] Rate limiting per user/IP; WebSocket message rate cap.
- [ ] Audio parsed only via vetted libraries; no shell calls with user input.
- [ ] Parameterised queries only (SQLAlchemy); no string-built SQL.
- [ ] Output encoding: render transcript/summary as text, never `dangerouslySetInnerHTML`.

## 7. Logging & audit
- [ ] Structured logs with request ID; **no transcript, audio, names, or tokens** in logs.
- [ ] `audit_log` entries for view/create/analyze/export/delete.
- [ ] Error responses never leak stack traces or internals.

## 8. Consent & transparency
- [ ] Consent banner before recording: "This consultation will be recorded and transcribed. Patient consent is required."
- [ ] Visible recording indicator whenever the mic is live.
- [ ] Clear disclaimer: AI output is a draft requiring clinician review.

## 9. Dependency & supply chain
- [ ] Lock files committed; `pip-audit` and `npm audit` in CI; Dependabot/Renovate enabled.
- [ ] Pin ONNX/VAD model assets and serve them from our own origin (no third-party CDN at runtime).

## 10. Incident response (minimum)
Detect (alerts on auth anomalies) → contain (revoke tokens, disable access) → assess → notify as legally required → post-mortem.

## 11. Pre-launch checklist
- [ ] Threat model reviewed (STRIDE on WS + analyze endpoints).
- [ ] Penetration/basic ZAP scan done.
- [ ] All boxes above ticked.
