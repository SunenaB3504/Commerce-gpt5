# Technical design

## 1. Architecture
- Frontend: HTML/CSS/JS static site (GitHub Pages)
- Backend: FastAPI, vector DB (Chroma/FAISS), storage (files + SQLite/Postgres)
- ML: sentence-transformers embeddings; SLM (quantized) via llama.cpp or API fallback
- Voice: Web Speech API, Porcupine Web wake word

## 2. Components
- services/api: upload, parse, index, ask, validate, teach, progress
- services/rag: chunker, embedder, retriever, re-ranker (MMR), prompts
- web/assets/js: api.js, state.js, ui.js, voice.js, teach.js, practice.js

## 3. Data flows
- Upload → Parse/OCR → Clean → Chunk → Embed → Index → Ask/Teach → Validate → Store attempts

## 4. Sequence diagrams
- Ask flow: UI → /ask → retrieve → prompt → generate → validate → citations → response
- Teach flow: UI → /teach → outline → sections → practice set → recap

## 5. Data model
- See docs/data/schema.md

## 6. Security
- CORS, rate limiting, file validation, size limits, PDF sanitization, PII avoidance

## 7. Observability
- Request logs, timings, retrieval stats, answer length, citation count

## 8. Risks
- OCR quality, CPU inference latency, wake-word reliability; mitigations per approach paper
