# Product Requirements Document (PRD)

## 1. Summary
CBSE Class 12 Commerce learning assistant with Web (HTML/CSS/JS) interface and RAG + SLM fine-tune. Exam-ready, book-only, with voice and wake word.

## 2. Goals & non-goals
- Goals: Exam alignment, comprehensive chapter coverage, MCQ/3/4/6-mark support, Teach me, Doubts (quick answer), Practice (assessment), voice UX.
- Non-goals: Full Android app (phase 2), non-CBSE content.

## 3. Users & scenarios
- Student revising chapters; teacher sharing practice drills.

## 4. Requirements
- Ingest PDFs; parse, chunk, index; strict citations.
- Teach me (overview, guided study, practice, recap).
- Practice (drills, simulator, weak-area focus) with validation & feedback.
- Doubts (quick answers with citations) for ad-hoc questions.
- Voice with wake word “Pappu” and Alexa-like flow.
- Public GitHub Pages frontend; backend API.

## 5. Success metrics
- Coverage ≥ 95% of chapter points; citation rate ≥ 95%; MCQ accuracy lift post fine-tune; latency < 6s median; WER < 15%.

## 6. Constraints
- Browser-only frontend; CPU-friendly backend; use Colab for heavy ML.

## 7. Milestones
- M0…M6 per approach paper.
