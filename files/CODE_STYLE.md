# CODE_STYLE

## General
- Small, single-purpose functions and modules; prefer clarity over cleverness.
- No dead code, no commented-out code, no `TODO` without an issue reference.
- Comments explain *why*, not *what*.
- Never log or hard-code secrets or patient data.
- Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- One logical change per commit/PR; PRs include tests.

## Python (backend)
- Python 3.11, fully type-annotated; `mypy --strict` clean.
- Formatter/linter: `ruff format` + `ruff check` (line length 100). Imports sorted by ruff.
- Naming: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants.
- Pydantic v2 models for all I/O; no raw dicts crossing layer boundaries.
- Layering: `api` → `services` → `db/repositories`. Routers contain no business logic; services never import FastAPI.
- Use `async def` for I/O; run CPU-bound ASR via `run_in_executor`/process pool.
- Dependency injection via FastAPI `Depends`; no global mutable state except the loaded model holder.
- Errors: raise typed `AppError` subclasses; map to API error format in one handler.
- Logging: `logging` with structured JSON; never `print`.
- Tests: `tests/` mirrors `app/`; names `test_<behavior>`; use fixtures, no network.

```python
async def analyze_session(session_id: UUID, svc: AnalysisService = Depends(get_analysis)) -> SummaryOut:
    return await svc.analyze(session_id)
```

## TypeScript / React (frontend)
- `strict: true`; no `any` (use `unknown` + narrowing); no non-null `!` without justification.
- ESLint + Prettier (single quotes, semicolons, 100 cols, trailing commas).
- Function components + hooks only. One component per file, `PascalCase.tsx`; hooks `useThing.ts`; utils `camelCase.ts`.
- Feature-folder structure (see ARCHITECTURE.md); import via path aliases (`@/features/...`).
- State: Zustand slices for cross-component state; local `useState` for UI-only state. Selectors to avoid re-renders.
- Data access only through `lib/api` and `lib/ws`; components never call `fetch` directly.
- API types generated from OpenAPI; do not hand-write duplicates.
- Accessibility: semantic elements, labels on icon buttons, `aria-live` for transcript.
- Never use `dangerouslySetInnerHTML`.
- Styling: CSS variables from DESIGN.md; no hard-coded colours.

```tsx
export function StatPill({ label, value }: { label: string; value: number }) {
  return <span className={styles.pill}>{label}: <b>{value}</b></span>;
}
```

## Naming for domain terms
`segment` (one VAD chunk), `transcript` (ordered segments), `summary` (structured `ClinicalSummary`), `session` (one consultation).

## Error handling & UX
- Every async UI action has loading, success, and error states.
- User-facing messages are plain language; technical details go to logs only.

## Tests
- Arrange–Act–Assert; one behaviour per test; deterministic (seed/mocks for time & audio).
- Do not mock what you own unless needed; mock external services (LLM, mic).

## Documentation
- Public functions have docstrings/TSDoc when behaviour is non-obvious.
- Update the relevant `docs/*.md` in the same PR as any contract/schema change.
