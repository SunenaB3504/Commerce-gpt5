# Product backlog (initial)

Format: ID, Title, Type, Priority, Effort (t-shirt), Dependencies, Acceptance Criteria

- US-001 Upload PDFs and parse text
  - Type: Feature, Priority: High, Effort: M
  - Deps: None
  - AC: Can upload multiple PDFs; parsed text stored; errors logged

- US-002 OCR for scanned PDFs (fallback)
  - Type: Feature, Priority: Medium, Effort: M
  - Deps: US-001
  - AC: Detect scanned PDFs; OCR and merge text; accuracy spot-checked

- US-003 Chunk & embed content; build vector index
  - Type: Feature, Priority: High, Effort: M
  - Deps: US-001
  - AC: Chunks created with metadata; kNN search returns relevant passages

- US-004 Ask endpoint with RAG and citations
  - Type: Feature, Priority: High, Effort: M
  - Deps: US-003
  - AC: Given a question + filters, returns grounded answer with citations

- US-005 Teach me v1 (overview + sources)
  - Type: Feature, Priority: High, Effort: M
  - Deps: US-003
  - AC: Generates chapter brief with citations; matches coverage matrix items

- US-006 MCQ validation and feedback
  - Type: Feature, Priority: High, Effort: S
  - Deps: US-004
  - AC: Validates answers; shows correct with explanation + citation

- US-007 PWA shell (manifest, service worker, icons)
  - Type: Feature, Priority: High, Effort: S
  - Deps: None
  - AC: Installable; caches app shell; offline page served

- US-008 Voice input/output; wake word
  - Type: Feature, Priority: Medium, Effort: M
  - Deps: US-004
  - AC: Mic capture, TTS playback, wake-word trigger, barge-in

- US-009 Fine-tune LoRA (Colab) + quantize GGUF and load in backend
  - Type: Feature, Priority: Medium, Effort: L
  - Deps: US-004
  - AC: Model artifacts available on HF; backend loads via env; latency acceptable

- US-010 Readiness dashboard
  - Type: Feature, Priority: Medium, Effort: M
  - Deps: US-006
  - AC: Shows per-chapter mastery and weak areas

- US-011 Android offline app scaffold (Phase 2)
  - Type: Feature, Priority: Later, Effort: L
  - Deps: Phase 1 gate
  - AC: JNI demo loads model; simple prompt runs offline
