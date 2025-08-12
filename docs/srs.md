# Software Requirements Specification (SRS)

Title: CBSE Class 12 Commerce Learning Assistant (Web PWA Phase 1, Android Offline Phase 2)
Version: 0.1.0
Owner: Project Team
Status: Draft

## 1. Purpose
This SRS defines functional and non-functional requirements for a CBSE Class 12 Commerce learning assistant that provides book-grounded explanations, practice, and feedback across question types (MCQ, 3/4/6-mark) with voice support. It covers Phase 1 (mobile-first web PWA + small SLM backend) and Phase 2 (native Android offline app) and serves as the contract among stakeholders.

## 2. Scope
- Deliver a web-based PWA (Phase 1) that ingests PDFs, builds a retrieval index, and answers strictly from book content using a small SLM with citations.
- Provide voice UX with wake word, enforce CBSE word limits, and compute readiness analytics.
- Fine-tune a small language model (SLM) on Google Colab, store artifacts on Hugging Face, and load them in the backend.
- Phase 2 adds a native Android offline app running a quantized 1–2B model with on-device mini-RAG.

## 3. Definitions, acronyms, abbreviations
- SLM: Small Language Model
- RAG: Retrieval-Augmented Generation
- LoRA: Low-Rank Adaptation fine-tuning
- GGUF: Quantized model file format for llama.cpp
- PWA: Progressive Web App
- ASR/TTS: Automatic Speech Recognition / Text-to-Speech
- MMR: Maximal Marginal Relevance (diversity re-ranking)

## 4. References
- docs/prd.md, docs/functional-spec.md, docs/technical-design.md
- docs/web/pwa-small-slm-plan.md, docs/mobile/android-offline-slm.md, docs/mobile/android-plan.md
- docs/ml/hf-access.md, docs/ml/hf-publish-checklist.md, docs/ml/colab-guide.md
- docs/content/coverage-matrix.md, docs/policies/content-policies.md
- docs/deployment/hosting.md, docs/security/privacy.md, docs/data/schema.md

## 5. Overall description
### 5.1 Product perspective
- Client: Mobile-first web PWA (HTML/CSS/JS) and later Android native.
- Server: FastAPI backend exposes endpoints for upload/parse/index/ask/teach/evaluate; uses vector DB and small SLM (llama.cpp GGUF) with RAG.
- Data: PDFs parsed to text, chunked, embedded, and indexed; JSON data packs hosted via GitHub Pages for static access.

### 5.2 User classes
- Student: studies chapters, asks questions, practices under exam formats.
- Teacher (optional): curates practice sets and reviews progress.

### 5.3 Operating environment
- Phase 1: Modern mobile browsers (Chrome/Edge/Firefox) on Android/Windows; GitHub Pages frontend; CPU-friendly backend host.
- Phase 2: Android 10+ phones/tablets; on-device inference via llama.cpp.

### 5.4 Assumptions & dependencies
- PDFs are provided by users (licensed for use).
- Heavy tasks run on Google Colab (fine-tune/quantization); artifacts stored on Hugging Face.
- Voice and wake word depend on browser/device capabilities (fallback to manual mic button).

### 5.5 Constraints
- Strictly book-based answers with citations; no ungrounded content.
- Web frontend built with vanilla HTML/CSS/JS (no framework) for Phase 1.
- Public GitHub Pages used for frontend hosting; data hosted as JSON where permissible.

## 6. Functional requirements
IDs use FR-<AREA>-###.

### 6.1 Ingestion & preprocessing (ING)
- FR-ING-001: The system shall allow users to upload PDFs per subject/chapter.
- FR-ING-002: The system shall perform OCR for scanned PDFs.
- FR-ING-003: The system shall parse and clean text (remove headers/footers, fix hyphenation, normalize whitespace).
- FR-ING-004: The system shall chunk text into 300–800 token segments with overlap and store metadata (board, subject, chapter, topic, page span).
- FR-ING-005: The system shall generate embeddings for chunks and index them in a vector store.

### 6.2 Retrieval & prompting (RAG)
- FR-RAG-001: The system shall filter retrieval by Board, Subject, Chapter and optional topic.
- FR-RAG-002: The system shall retrieve k passages (configurable 6–12) with MMR diversity re-ranking.
- FR-RAG-003: The system shall instruct the generator to answer strictly from retrieved excerpts and include citations with page spans.

### 6.3 Teach me (TEACH)
- FR-TEACH-001: The system shall produce a chapter overview highlighting key points, definitions, and formulas.
- FR-TEACH-002: The system shall deliver guided study sections with examples and diagrams (textual descriptions allowed).
- FR-TEACH-003: The system shall produce practice sets spanning MCQ, 3/4/6-mark questions with word-limit guidance.
- FR-TEACH-004: The system shall provide a recap with key terms and likely exam questions.
- FR-TEACH-005: The system shall ensure comprehensive coverage per chapter (coverage matrix tracked).

### 6.4 Ask me (ASK)
- FR-ASK-001: The system shall support practice modes (quick drill, exam simulator, weak-areas focus).
- FR-ASK-002: The system shall validate MCQ answers and show correct answer with explanation and citation.
- FR-ASK-003: The system shall enforce word limits for 3/4/6-mark answers and check presence of key points from rubric.
- FR-ASK-004: The system shall support calculation-based answers (e.g., ratios) with steps shown.
- FR-ASK-005: The system shall support case-study style questions mapping concepts to the scenario.

### 6.5 Voice & wake word (VOICE)
- FR-VOICE-001: The system shall support voice input (ASR) and voice output (TTS) in the web app where supported.
- FR-VOICE-002: The system shall implement wake word "Pappu" with an on-device detector where supported; else provide a mic button.
- FR-VOICE-003: The system shall support Alexa-like states: Idle → Listening → Thinking → Speaking and allow barge-in.

### 6.6 Readiness & analytics (EVAL)
- FR-EVAL-001: The system shall compute mastery per chapter with accuracy, attempts, and time-on-task.
- FR-EVAL-002: The system shall identify weak areas and recommend remediation content.

### 6.7 Settings & selections (SET)
- FR-SET-001: The system shall allow selection of Board, Subject, Chapter, and question types.
- FR-SET-002: The system shall persist preferences locally.

### 6.8 Data hosting (DATA)
- FR-DATA-001: The system shall optionally host non-sensitive JSON data packs on GitHub Pages with a manifest and checksums.
- FR-DATA-002: The system shall split large data into multiple files (≤10 MB each) for efficient caching and updates.

### 6.9 Model lifecycle (ML)
- FR-ML-001: The system shall support fine-tuning via LoRA on Colab and storing artifacts on Hugging Face.
- FR-ML-002: The backend shall load either a quantized GGUF (llama.cpp) or a base+LoRA pair via transformers+PEFT based on env vars.
- FR-ML-003: The system shall pin model version and verify artifact integrity (checksum) at startup.

### 6.10 Web PWA (PWA)
- FR-PWA-001: The frontend shall include a manifest.json and a service worker for offline caching of the app shell and data packs.
- FR-PWA-002: The system shall provide limited offline functionality (Teach me summaries, practice sets) and optionally full offline generation when WebGPU is supported.

### 6.11 Android offline app (AND) — Phase 2
- FR-AND-001: The Android app shall run a quantized 1–2B model (Q4/Q3) via llama.cpp offline.
- FR-AND-002: The Android app shall implement on-device mini-RAG over chapter JSON with citations.
- FR-AND-003: The Android app shall optionally include offline ASR/TTS.

## 7. External interface requirements
- Mobile-first HTML/CSS/JS pages: Upload/Parse, Teach, Doubts (quick answers), Practice (assessment), Progress, Settings.
- Components: mic button, wake word indicator, token streaming view, citations panel, word-count meter, readiness dashboard.

- POST /upload, POST /parse, POST /index
- GET /ask, GET /ask/stream, POST /teach
- POST /mcq/validate, POST /answer/validate, POST /practice/start, GET /practice/next, POST /practice/submit
- GET /progress, GET /health
- Auth optional for prototype; CORS enabled for Pages domain.

### 7.3 Hardware interface
- Server: CPU host with sufficient RAM for GGUF loading (1–4 GB model file).
- Android: ≥4 GB RAM recommended for Q4; 3 GB devices may require Q3.

### 7.4 Communications interface
- HTTPS between PWA and backend; offline caching via service worker.

## 8. Non-functional requirements
### 8.1 Performance
- P50 answer time ≤ 6s; P95 ≤ 12s (backend small SLM).
- Token streaming to UI; first token within 1.5s after retrieval.

### 8.2 Reliability & availability
- Automatic retries on transient parse/embedding failures.
- Service worker fallback for offline content.

### 8.3 Security & privacy
- File validation; limit file size and types.
- No PII by default; store PDFs locally; avoid third-party calls unless enabled.
- Ground-only prompts to reduce hallucinations.

### 8.4 Maintainability
- Configuration via .env; model/env pinning documented.
- CI checks for lint/type/tests.

### 8.5 Portability
- Frontend: standards-compliant; no framework lock-in.
- Backend: Python 3.11+; vector DB pluggable (FAISS/Chroma/pgvector).

### 8.6 Accessibility & usability
- Keyboard navigation, ARIA labels, color contrast.
- Word-limit helper and validation messages.

### 8.7 Legal & compliance
- Respect copyrights; do not publicly host copyrighted raw text unless licensed.
- Attribute base models and include model licenses.

## 9. Data requirements
- DB tables: documents, chunks, questions, attempts, users (optional). See docs/data/schema.md.
- JSON shapes for Pages hosting: manifest, chunks, mcq.json with fields and checksums.
- Storage quotas: repo < 1 GB; single JSON < 100 MB (or LFS); split into ≤10 MB files preferred.

## 10. System models (informal)
- Use cases: Upload & parse, Teach me session, Doubts (quick answers), Practice drill (assessment), Voice interaction, Readiness review.
- State machines: Voice states (Idle → Listening → Thinking → Speaking; barge-in allowed).
- Sequences:
	- Doubts: UI → /ask → retrieve → synthesize extractive answer → cite → respond.
	- Practice: UI → /practice/start → /practice/next → user answer → /mcq/validate or /answer/validate → feedback → next.

## 11. Quality assurance
- Unit tests: parsing, chunking, retrieval filters, validators.
- Integration: E2E ask/answer with sample PDFs; citation checks.
- Metrics: citation rate, groundedness, MCQ accuracy, ROUGE-L/F1, latency.
- Acceptance: See Section 13 (phase gates).

## 12. Deployment & operations
- Frontend: GitHub Pages (static /web).
- Backend: CPU-friendly PaaS; CORS to Pages domain; logging and basic metrics.
- Model storage: Hugging Face Hub; download on startup; verify checksums; cache.
- Data hosting: JSON on Pages or object storage + CDN; integrity via checksums.

## 13. Acceptance criteria and phase gates
### Phase 1 exit criteria (go/no-go for Phase 2)
- Coverage ≥ 95% across pilot chapters; groundedness ≥ 95% with citations.
- MCQ accuracy lift vs. baseline; P50 ≤ 6s; voice flows reliable; wake word acceptable.
- PWA offline: app shell + data packs cached; Teach me/practice usable offline.

### Phase 2 exit criteria
- Fully offline Ask/Teach on mid-tier Android devices (≥4 GB RAM) with Q4/Q3 model.
- App size ≤ 1.5–2 GB including model/core data; stable across device matrix.

## 14. Risks & mitigations
- OCR quality → cleanup pipeline; manual review for worst pages.
- Low-resource inference → RAG guardrails; optional cloud fallback during Phase 1 testing.
- Wake-word variability → sensitivity tuning; mic-button fallback.
- Data licensing → store raw text privately; public hosting for derived/allowed content only.

## 15. Traceability
- Each FR maps to functional-spec sections and test cases in docs/evaluation/test-plan.md.
- Model lifecycle maps to docs/ml/* and deployment to docs/deployment/hosting.md.

Appendix A: Requirement ID quick map
- ING: FR-ING-001…005
- RAG: FR-RAG-001…003
- TEACH: FR-TEACH-001…005
- ASK: FR-ASK-001…005
- VOICE: FR-VOICE-001…003
- EVAL: FR-EVAL-001…002
- SET: FR-SET-001…002
- DATA: FR-DATA-001…002
- ML: FR-ML-001…003
- PWA: FR-PWA-001…002
- AND: FR-AND-001…003
