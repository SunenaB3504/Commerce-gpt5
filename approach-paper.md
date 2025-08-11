# CBSE Class 12 Commerce Chatbot — Detailed Approach Paper

## 1) Executive summary
A web-based, CBSE-aligned learning assistant for Class 12 Commerce (Economics, Business Studies, Accountancy) that:
- Ingests and indexes chapter PDFs
- Provides “Teach me” and “Ask me” modes in both text and voice
- Supports question formats (MCQ, 3/4/6-mark short/long answers) with word-limit guidance and validation
- Delivers feedback and chapter-readiness insights
- Uses resource-light local components for daily use and Google Colab for heavy tasks (fine-tuning, dataset generation)
- Targets web app first; Android as a phase-2 wrapper

Prototype scope: two chapters per subject; PDF upload & parsing UI; RAG baseline with optional SLM fine-tune via Colab; Alexa-like voice flow with wake word “Pappu”.

---

## 2) Requirements checklist
- Content & model
  - [ ] Fine-tune an SLM with subjects (Economics, Business Studies, Accountancy)
  - [x] Input: Chapter PDFs (upload & parse UI)
  - [x] Output: Web app (Android later)
  - [x] Resource plan: offload heavy steps to Colab
  - [x] Exam-ready, comprehensive coverage of every point in each chapter (strictly book-based)
- Chatbot features
  - [x] Teach me (type & voice input, text & voice output)
  - [x] Select Board, Subject, Chapter, Question type(s)
  - [x] One-by-one Q&A and “Full chapter” walkthrough
  - [x] Use CBSE question formats, with word limits
  - [x] “Ask me” (voice/text), validation, MCQs, feedback with correct answers
  - [x] Chapter readiness: randomize questions across chapters; weak-area analysis
  - [x] Wake word “Pappu” and Alexa-like state flow
- Content constraints
  - [x] Strictly book-based, age-appropriate, exam-ready coverage
- Prototype specifics
  - [x] Two chapters per subject
  - [x] PDF upload and parsing UI
  - [x] Baseline RAG; optional SLM fine-tune on Colab
  - [x] Web app delivery (Android later)
 - Delivery & hosting
   - [x] Web interface built with vanilla HTML, CSS, and JS (no framework dependency for prototype)
   - [x] Public GitHub repository with GitHub Pages hosting for the frontend

---

## 3) Scope and key assumptions
- Scope: Web app with voice and text UX, RAG baseline over uploaded chapters, per-board/subject/chapter filtering, Q-type generation, validation, and chapter-readiness scoring. Fine-tune a small model (SLM) using LoRA on Colab; integrate for inference if feasible on target hardware (8 GB RAM) using quantization.
- Assumptions:
  - PDFs are scans or digital; OCR may be required for scans.
  - CBSE content will be provided by the user (legal usage). System must not hallucinate outside book content.
  - For wake word in browser, use a client-side keyword engine (e.g., Porcupine Web/WASM) or simulate with a button if needed initially.
  - For TTS/STT, start with browser APIs where available; offer cloud provider fallbacks (configurable) for quality.

---

## 4) Architecture overview
- Frontend (Web): Vanilla HTML, CSS, and JS (no build step)
  - Structure: static pages under /web (index.html, teach.html, practice.html, progress.html, settings.html) with modular ES6 JS modules
  - Styling: CSS with BEM or utility classes; optional small CSS variables/theme
  - State: lightweight in-browser state (localStorage/sessionStorage) + REST calls to backend
  - Speech UI: mic button; wake-word listener; Alexa-like states: Idle → Listening → Thinking → Speaking
- Backend API: Python (FastAPI)
  - Endpoints: auth (optional), upload, parse, index, ask, evaluate, teach, voice webhook, progress
  - Services: RAG pipeline, Q/A validator, scorer, analytics, content guardrails
- Vector store: Local for dev (FAISS/Chroma), cloud-ready (pgvector) for scale
- Storage: File store for PDFs & parsed text; metadata in SQLite/Postgres
- Models:
  - Embeddings: Lightweight (e.g., all-MiniLM-L6-v2) or Instructor-base; on Colab for bulk; cached locally
  - Generator: Baseline via API or a small local model (quantized) + RAG
  - Fine-tuned SLM via LoRA (Colab) exported to GGUF for llama.cpp or to ONNX for CPU inference
- Voice:
  - STT: Web Speech API; optional Azure or GCP STT
  - TTS: Web Speech API; optional Azure or GCP TTS
  - Wake word: Porcupine Web/WASM (“Pappu”) with VAD
- Analytics: Event logs (Q attempts, time on task), mastery estimates by chapter & Q-type
Security & privacy: Local processing preferred; no third-party calls unless configured. PII-free; content-bound answers with citations.
## 5) Data ingestion & preprocessing
---

## 5) Data ingestion & preprocessing
1) Upload PDFs
- Accept multiple PDFs per subject/chapter.
- OCR (e.g., Tesseract via pytesseract) if scanned.

2) Parsing
- Use PyMuPDF or pdfminer.six to extract text; preserve heading structure if possible.
- Clean: remove headers/footers, page numbers, hyphenation fixes, normalize whitespace.

3) Chunking & metadata
- Split into 300–800 token chunks with overlap (50–100 tokens).
- Attach metadata: board, subject, chapter, topic, page span, source file, version, date.

4) Embedding & indexing
- Generate embeddings; store {id, text, metadata, embedding} in vector DB.
- Build hierarchical indices: subject → chapter → topic for constrained retrieval.

5) Content integrity
- Keep raw text and normalized text. Use citations with page spans for every answer.

5.1) Exam-ready content coverage method
- Build a chapter coverage matrix for each subject: list every heading/subheading, definitions, formulas, diagrams, examples, and typical question stems.
- Track coverage status per item (Explained, Practiced, Assessed) and ensure a minimum set of practice items per subtopic (MCQ + 3/4/6-mark).
- Generate a “Chapter Brief” (Teach me) that enumerates every key point; validation pipeline checks that answers cite relevant chapter points.
- Run periodic gaps audit: retrieval samples must map to all matrix rows; flag uncovered items.

---

## 6) RAG prompting & answer policies
- Retrieval
  - Filter by Board/Subject/Chapter and optionally topic.
  - k=6–12 passages; diversity-aware re-ranking (MMR) to reduce redundancy.
- Prompting
  - Enforce: “Answer strictly from provided excerpts. If not found, say you don’t know.”
  - Enforce word-limit guidance based on Q-type (MCQ, 3/4/6 marks).
  - Include citation tags [Chapter X: page Y–Z].
- Validation & grading
  - MCQ: compare to key; show correct answer and short explanation + source.
  - Short/Long answers: rubric checks for key points presence, concision (word count), citation rate, and factual alignment.

---

## 7) Fine-tuning strategy (Colab)
Goal: Improve instruction-following and CBSE-style answer formatting.

- Dataset creation
  - From each chapter, generate structured Q/A pairs per type (MCQ, 3, 4, 6 marks) with references.
  - Human-in-the-loop review on a small subset; auto QA on the rest.
- Model choice (SLM)
  - Candidates: Phi-3 mini (on CPU), Llama 3.2 3B/1B variants, Mistral 7B (heavier).
  - Start with 1B–3B models for CPU feasibility; quantize (4-bit) for inference.
- Training
  - LoRA/QLoRA on Colab (A100/T4). Sequence length 2k–4k. 2–3 epochs.
  - Loss: supervised cross-entropy; early stopping on validation.
- Export & serving
  - Export to GGUF; serve via llama.cpp on backend (CPU) or lightweight GPU if available.
  - Fallback to API model if latency/quality gap is unacceptable.
- Evaluation
  - Held-out chapter Q/A; MCQ accuracy; Rouge-L/F1 vs. reference answers; citation adherence.

Note: RAG remains primary guardrail; fine-tuned SLM formats and structures answers better under constraints.


## 8) Voice UX and wake word (“Pappu”)
- States: Idle (wake-word armed) → Listening (ASR) → Thinking (LLM) → Speaking (TTS)
- Barge-in: user can interrupt TTS to ask follow-ups.
- Wake word engine: Porcupine Web for “Pappu” (custom keyword file); fallback to mic button if permission or compatibility issues.
- Privacy: on-device wake-word detection; don’t stream audio until activated.


## 9) Feature design details
### 9.1 Teach me
- Inputs: Board, Subject, Chapter, Q-types, modality (text/voice)
- Flow:
  1) Overview: chapter brief (bulleted points + key definitions)
  2) Guided study: sections explained with examples and diagrams (ASCII/markdown)
  3) Practice set: MCQs + 3/4/6-mark questions with hints
  4) Recap: key terms, formulas, and likely exam questions
- Controls: “Slower/Faster”, “Give example”, “Explain again”, “Show sources”

### 9.2 Ask me
- Modes: Quick drill (10–15 questions), Exam simulator (sample paper), Weak areas focus
- Validation: word counts, keyword coverage, source alignment
- Feedback: correct answer, explanation, citations, remediation links to relevant chunks
- Readiness report: per chapter mastery (0–100), attempts, accuracy, time, recommendations

### 9.3 Question types
- MCQ: 1 mark; instant validation
- Short answers: 3 marks (60–80 words), 4 marks (80–100 words)
- Long answers: 6 marks (100–150 words)
- Economics: include A/R (Assertion–Reason); calculations (e.g., GDP, break-even); diagrams (textual description)
- Business Studies: caselets; differences; importance/features lists
- Accountancy: journal entries, ledgers, ratios, cash flow steps; numeric validation


## 10) Guardrails and compliance
- “Book-only” policy: Answer solely from indexed content; if retrieval confidence < threshold, prompt user to upload or clarify.
- Hallucination control: refusal + request for more context; always include citations.
- Age-appropriate language filter; tone: supportive, concise, exam-focused.
- Plagiarism: content rephrased to avoid verbatim large extracts; provide page references.


## 11) Data and schema
- Documents
  - documents(id, subject, chapter, board, source_path, pages, version, uploaded_at)
  - chunks(id, document_id, text, token_count, page_start, page_end, embedding)
  - questions(id, subject, chapter, type, prompt, difficulty, answer_key, rubric, source_refs)
- Frontend: Vanilla HTML, CSS, and JavaScript (no framework); optional tiny helpers (Alpine.js) if needed
  - users(id, role, prefs)

---

## 12) Tech stack and tooling
- Frontend: React or Next.js + TypeScript, TailwindCSS, Vite
- Backend: FastAPI (Python 3.11+), uvicorn, pydantic, SQLModel/SQLAlchemy
- Packaging/Dev: Poetry or pip + requirements.txt, Docker (optional), pytest
- Hosting: Public GitHub repository; frontend served via GitHub Pages; backend on a simple CPU-friendly host (Render/Azure App Service/Railway)
- Parsing: PyMuPDF, pdfminer.six, pytesseract (OCR)
- Embeddings: sentence-transformers (MiniLM), Instructor-XL for quality on Colab
- Models: llama.cpp for local SLM inference; or configured API (Azure OpenAI) as fallback
- Voice: Web Speech API, Porcupine Web (wake word), Web Audio API
- Notebooks (Colab): data parsing, synthetic Q/A generation, LoRA fine-tune, export
- Packaging/Dev: Poetry or pip + requirements.txt, Docker (optional), pytest

---

## 13) Milestones and timeline

Phase 1 — Web PWA + Small SLM backend (target: 4–6 weeks)
- M0 (Day 0–2): Public GitHub repo, Pages enabled; repo scaffolding, CI/lint, basic docs; settings page
- M1 (Week 1): Upload & parsing UI; backend parse API; OCR fallback; storage
- M2 (Week 2): Embedding + indexing; RAG ask endpoint; Teach me v1 (overview + sources)
- M3 (Week 3): Ask me drills, MCQ validation; word-limit enforcement; citations; progress page
- M4 (Week 4): Voice (ASR/TTS) + wake word (Porcupine Web); Alexa-like states; barge-in
- M5 (Week 5): Colab LoRA fine-tune on selected Q/A; quantized export; optional local inference
- M6 (Week 6): Chapter readiness analytics; polish; docs; pilot test

Phase 1 acceptance gate (go/no-go for Phase 2)
- Coverage ≥ 95% across pilot chapters; groundedness ≥ 95% with citations
- MCQ accuracy lift vs. baseline; latency P50 ≤ 6s with small SLM backend
- Voice flows reliable on target browsers; wake-word acceptable FAR/FRR

Phase 2 — Native Android offline app (target: 4–6 weeks)
- M7: Android project scaffold (Compose), llama.cpp JNI integration, demo prompt
- M8: On-device mini-RAG over chapter JSON; Teach me offline; data pack updater
- M9: Voice offline (optional), readiness insights, performance tuning (context windows, quant level)
- M10: Packaging (asset packs/OBB), QA matrix across low/mid/high devices, pilot release

Phase 2 acceptance gate
- Fully offline Ask/Teach functional on mid-tier devices (≥4 GB RAM) with Q4/Q3 model
- App size within budget (< 1.5–2 GB including model & core data)
- Median answer time acceptable for study use; stability across device matrix

---

## 14) Quality gates and evaluation
- Build/Lint/Typecheck: CI jobs for web and backend
- Unit tests: parsing, chunking, retrieval filters, validators
- Integration tests: end-to-end ask/answer with sample PDFs
- RAG metrics: citation rate, groundedness checks, answer completeness
- Fine-tune metrics: MCQ accuracy lift; ROUGE/L on short/long answers; latency
- Voice metrics: WER (ASR), wake-word false accept/reject rates

Acceptance criteria (prototype):
- Upload and parse 2 chapters per subject, indexed and retrievable with citations
- Teach me produces chapter brief + at least 6 practice questions across types
- Ask me administers a 10-question drill, validates, and shows readiness by chapter
- Voice input/output works in-browser; wake word “Pappu” triggers reliably on supported devices

---

## 15) Deployment and ops
- Dev: local backend + static frontend; .env toggles for APIs
- Frontend hosting: GitHub Pages (main or gh-pages branch). Keep frontend static assets under /web and configure Pages to serve from that path.
- Backend hosting: single VM/container (Railway/Render/Azure App Service) with CPU-only inference; expose HTTPS API for the Pages frontend.
- Observability: basic request logs, answer time, retrieval stats
- Privacy: store PDFs locally; no external calls unless enabled by user

---

## 16) Risks and mitigations
- Low-resource inference quality: mitigate with RAG; allow cloud model fallback
- OCR noise in scanned PDFs: post-OCR cleanup; manual review for prototype
- Wake-word variability: provide mic-button fallback; tune keyword sensitivity
- Hallucinations: strict content-only prompts; confidence thresholds; refuse when unsure
- Timeline creep: prioritize RAG + voice first; defer Android until after pilot


## 17) Next steps and inputs needed
- Provide PDFs: at least 2 chapters each for Economics, Business Studies, Accountancy (you mentioned Economics Ch.1 will be provided)
- Confirm cloud usage policy (allow Azure/GCP for STT/TTS or strictly local?)
- Choose preferred small model for fine-tuning (Phi-3 mini vs. Llama 3.2 3B)
- Confirm target browsers/devices for wake-word support testing


## 18) Work plan artifacts to include in repo
- docs/
  - colab/01_parse_and_chunk.ipynb
  - colab/02_generate_QA_by_type.ipynb
  - colab/03_lora_sft_training.ipynb
  - colab/04_export_and_inference.ipynb
  - product/ux-flows.md (voice states, screens)
  - content/policies.md (book-only, age-appropriate guardrails)
  - web/pwa-small-slm-plan.md (PWA strategy to cover mobile use without native app)
- services/
  - api/ (FastAPI)
  - rag/ (retriever, reranker, prompt templates)
  - voice/ (wake-word, STT/TTS adapters)
- web/
  - index.html (landing + navigation)
  - teach.html (Teach me)
  - practice.html (Ask me)
  - progress.html (readiness)
  - settings.html (board/subject/chapter selection)
  - assets/css/*.css
  - assets/js/*.js (modular ES6)

---

## 19) Requirements coverage
- Fine-tune SLM with subjects: Planned via Colab LoRA with export for CPU inference
- PDF upload & parsing UI: In-scope for M1
- Web app with Teach me & Ask me + voice: In-scope (M2–M4)
- Board/Subject/Chapter/Q-type selection: In-scope (M2)
- One-by-one Q&A and full-chapter walkthrough: In-scope (M2–M3)
- Wake word “Pappu” + Alexa-like flow: In-scope (M4)
- Validation, feedback, chapter readiness: In-scope (M3, M6)
- Content strictly from book, age-appropriate: Guardrails in RAG + policies
- Prototype: two chapters per subject: In-scope (M1–M2)
 - Exam-ready comprehensive coverage of every chapter point: In-scope (coverage matrix + Teach me checks)
 - Web interface in HTML/CSS/JS (no framework): In-scope (M0–M2)
 - Public GitHub hosting (Pages for frontend): In-scope (M0)

---

## 20) Optional: minimal local dev setup (Windows, PowerShell)
- Python 3.11 for backend; no build needed for frontend (static files)
- Create virtual env, install FastAPI + PDF parsers; start API; open web/index.html locally or serve via a simple static server

```powershell
# Backend (FastAPI)
py -3.11 -m venv .venv
. .venv\Scripts\Activate.ps1
pip install fastapi uvicorn[standard] pydantic pdfminer.six pymupdf chromadb sentence-transformers

# Run API (example)
uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (static) — optional local server
python -m http.server 5173 --directory web
```

For hosting, push the repo public and enable GitHub Pages (root: /web). Point the frontend JS to the deployed backend API URL.

---

This approach balances a pragmatic, book-grounded RAG baseline with a Colab-assisted fine-tuned SLM for exam-style outputs, adds voice and wake-word UX, and scopes a focused prototype deliverable that can be expanded to Android in phase 2.
