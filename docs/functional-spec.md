# Functional specification

## 1. Personas & flows
- Student: Learn (Teach me), Practice (Ask me), Review progress.

## 2. Feature list
- Upload & parse PDFs
- Teach me: chapter brief, guided study, practice set, recap
- Ask me: drills, exam simulator, weak-areas
- Validation: MCQ keys, word limits, rubric checks, citations
- Progress: mastery per chapter, attempts history
- Voice: ASR/TTS, wake word, barge-in
- Settings: board, subject, chapter, q-types

## 3. Non-functional
- Performance: P50 < 6s answer; P95 < 12s
- Reliability: retry on OCR; robust PDF parsing
- Accessibility: keyboard, ARIA labels, adequate contrast

## 4. Acceptance criteria
- Per milestone ACs matching approach paper acceptance criteria
