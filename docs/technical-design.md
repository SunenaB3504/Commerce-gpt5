# Technical design

## 1. Architecture
- Frontend: HTML/CSS/JS static site (GitHub Pages)
- Backend: FastAPI, vector DB (Chroma/FAISS), storage (files + SQLite/Postgres)
- ML: sentence-transformers embeddings; SLM (quantized) via llama.cpp or API fallback
- Voice: Web Speech API, Porcupine Web wake word

## 2. Components
- services/api: upload, parse, index, doubts (ask), validate (mcq/short), teach, practice, progress
- services/rag: chunker, embedder, retriever, re-ranker (MMR), prompts
- web/assets/js: api.js, state.js, ui.js, voice.js, teach.js, practice.js

## 3. Data flows
- Upload → Parse/OCR → Clean → Chunk → Embed → Index → Doubts/Teach → Validate → Store attempts

- Doubts (quick answer) flow: UI → /ask → retrieve → synthesize extractive answer → citations → response
- Teach flow: UI → /teach → outline → sections → practice set → recap
- Practice flow: UI → /practice/start → /practice/next → user answer → /mcq/validate or /answer/validate → feedback + citations → next

## 5. Data model
- See docs/data/schema.md

## 6. Security
- CORS, rate limiting, file validation, size limits, PDF sanitization, PII avoidance

## 7. Observability
- Request logs, timings, retrieval stats, answer length, citation count

## 8. Risks
- OCR quality, CPU inference latency, wake-word reliability; mitigations per approach paper

## 9. HTTP API (snapshot)
- GET /health/ — liveness
- POST /data/upload — save PDF, return path/id
- POST /data/parse — parse PDF to pages
- POST /data/index — chunk + index; persist chunks JSON for web
- GET /ask — quick answers with citations (formerly Ask me; now Doubts)
- GET /ask/stream — SSE stream for quick answers
- POST /mcq/validate — validate MCQ answers
- POST /answer/validate — validate short answers with rubric scoring
- POST /practice/start — start a practice session
- GET /practice/next — get next question in a session
- POST /practice/submit — submit an answer in a session
