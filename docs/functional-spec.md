# Functional specification

## 1. Personas & flows
 Student: Learn (Teach me), Practice (assessment), Doubts (quick answers), Review progress.

 Teach me: chapter brief, guided study, practice set, recap
 Practice: drills, exam simulator, weak-areas; validation: MCQ keys, word limits, rubric checks, citations
 Doubts: ad-hoc quick answers with citations
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
