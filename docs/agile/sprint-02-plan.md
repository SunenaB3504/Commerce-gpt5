# Sprint 02 plan (2 weeks)

Sprint goal: Learning flows and validation — “Teach me v1”, MCQ + Short-answer validation, Practice (Ask me assessment) with basic voice.

Scope (stories)
- US-005 Teach me v1 (overview + sources)
- US-006 MCQ validation and feedback
- US-010 Readiness dashboard (initial)
- US-007 Short-answer validation (rubric scoring + feedback)
- US-008 Practice session flow (assessment mode; Option A)
- US-009 Voice mode for Practice (STT/TTS in browser)

Deliverables
- Backend: /teach (subject/chapter), /mcq/validate, /answer/validate, /practice/start|next|submit
- Frontend: Teach page (chapter outline), Practice page (assessment: MCQ + short-answer)
- Voice: In-browser STT/TTS for Practice (Chrome-family first); audio stays on-device
- UX rename (Option A): current “Ask” → “Doubts”, “Practice” = assessment
- Eval: hit@k, citation presence, latency dashboard (basic)

Risks
- Hallucination risk in teach synthesis — constrain to citations
- MCQ ground truth quality — curate and version
- Short-answer scoring fairness — calibrate thresholds with samples
- Voice STT variance across browsers — default to manual input fallback

Definition of Done
- Teach returns structured outline with citations
- MCQ validation returns correct/incorrect with explanation and source
- Eval dashboard shows metrics for sample chapters
- Short-answer validator returns rubric, score, citations, and recommendations
- Practice flow supports MCQ and short-answer (text); voice available on supported browsers

## Day-by-day plan (10 working days)

- Day 1: Kickoff and scaffolding — Completed (2025-08-13)
	- Define contracts for /teach and /mcq/validate (request/response schemas).
	- Create stubs for routes, service utilities, and minimal tests.
	- Draft data shapes for Teach outline sections and MCQ store.
	- Apply Option A UX rename: “Ask” → “Doubts”; add “Practice” entry point in nav.
	- Done: Implemented POST /answer/validate (short-answer rubric), added POST /teach and POST /mcq/validate stubs, registered routers, added Practice page link, updated schema docs, and added tests. All tests passing.

- Day 2: Teach me v1 — extractive outline
	- Completed (2025-08-13)
	- Done: Implemented outline synthesis using retrieval with depth-based caps (basic/standard/deep).
	- Done: Sections shipped — overview, key terms, short answers, long answers, formulae; with citations and page anchors.
	- Done: Glossary extraction from “Term: definition” patterns; glossary highlighting in UI.
	- Done: Curated fallback to supplement overview and short answers when retrieval is sparse.
	- Done: Teach page in PWA with depth selector, per-section show/hide citations, page badges, copy/print actions, and print stylesheet.
	- Done: Tests updated for outline structure, citations, glossary key presence, and depth-cap behavior.

- Day 3: Teach me v1 — coverage and UI
	- Completed (2025-08-13)
	- Done: Backend computes coverage (required vs covered/gaps) using docs/content/subjects/<subject>/chapters/<chapter>/coverage.json when present, with fallback to request topics.
	- Done: readingList aggregated from citations across sections, de-duplicated by (page, filename) and sorted.
	- Done: Teach UI shows coverage summary and a lightweight loading skeleton.

- Day 4: MCQ ingestion and schema
	- Define MCQ schema (question, options A–D, correct, explanation, sources).
	- Implement parser for MCQs from existing markdown/JSON content.
	- Seed a small MCQ set per chapter; add unit tests for parsing.

- Day 5: MCQ validation API and UX
	- Implement /mcq/validate (checks selected option, returns result + explanation + citations).
	- Add a minimal UI form to submit MCQ and visualize feedback.
	- E2E test covering happy/negative cases.

- Day 6: Eval harness
	- Extend eval scripts for hit@k, citation presence, answer length, latency.
	- Add a small YAML/JSON suite of test prompts per chapter.
	- Store results to JSON; summarize in console and docs.
	- Refine /answer/validate thresholds and feedback based on samples; add additional unit tests and small calibration set.

- Day 7: Practice sessions (text) + Readiness dashboard (initial)
	- Implement /practice/start|next|submit with in-memory session store (subject/chapter/topic filters).
	- Practice UI: question card, MCQ selector or short-answer textarea, feedback view.
	- Backend route to serve aggregated eval metrics; basic web dashboard (table/cards) and link to rerun eval.

- Day 8: Voice mode for Practice + Admin hot-reload
	- Voice: integrate Web Speech API (STT) and SpeechSynthesis (TTS) with Practice UI; commands (repeat/next/skip/A–D/stop); captions.
	- Admin hot-reload: endpoints to reload curated Q&A and stopwords; developer-only toggle in PWA; unit tests for reload behavior.

- Day 9: Content scaling and perf pass
	- Expand curated entries for top chapters (batch import from docs/data).
	- Calibrate short-answer thresholds with sample answers; refine stopwords and matcher.
	- Perf checks on /teach, /mcq/validate, /answer/validate; caching or memoization where safe.
	- Update docs and smoke scripts.

- Day 10: Demo prep and retro
	- Polish UX copy and error states; finalize docs and demo script.
	- Run full eval; export snapshot for dashboard.
	- Sprint 02 review and retrospective; outline Sprint 03.
