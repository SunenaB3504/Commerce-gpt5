# ADR 0001: Rename “Ask” to “Doubts” and add “Practice” assessment mode

Date: 2025-08-13
Status: Accepted

## Context
Users expected “Ask me” to quiz them and validate answers. Our current “Ask” answered questions. This mismatch caused confusion.

## Decision
- Rename UI and docs: “Ask” → “Doubts” (quick, citation-backed answers).
- Introduce “Practice” as the assessment mode (MCQ + short answers).
- Add APIs: /answer/validate (short-answer rubric scoring), /practice/start|next|submit (to be added).
- Keep /ask for Doubts; update docs and UI labels accordingly.

## Consequences
- Clear separation of use cases: Doubts (ad-hoc answers) vs Practice (assessment).
- Sprint 02 scope updated to include short-answer validator and Practice session flow.
- Voice UX planned primarily for Practice; Doubts remains text-first.

## Alternatives considered
- Option B: Keep “Ask” as Q&A and add “Practice” as new feature. Rejected to align with user mental model.
