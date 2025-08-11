# Native Android plan (Phase 2)

## Modules
- app: UI (Jetpack Compose), navigation, settings
- core: domain models, repositories (questions, chapters, attempts)
- inference-llama: JNI wrapper for llama.cpp, token streaming
- data-packs: download/verify/unpack JSON chunks; versioned manifest

## Model integration
- Bundle or download GGUF (Q4/Q3) for 1–2B model
- JNI layer: load model, set n_ctx, threads; streaming callbacks
- Prompt builder: book-only, citations, word-limit hints; small context

## On-device RAG
- JSON chunks in app storage; TF‑IDF or precomputed NN maps
- Per-chapter indices; citations preserved in UI

## Offline voice (optional)
- ASR: Vosk/PocketSphinx; TTS: Android engine

## Performance targets
- Token gen ≥ 10 tok/s on mid-tier device (goal); P50 answer < 8–10s
- RAM: fit within 4–6 GB devices using Q3 if needed

## Packaging
- App bundle with asset packs; checksum verification; resume downloads

## QA matrix
- Low-end (3 GB), mid (4–6 GB), high (8+ GB) devices; Android 10+
- Measure latency, memory, crash-free, wake-word reliability (if enabled)

## Rollout
- Internal test → closed beta → staged rollout; telemetry (local, PII-free)
