# Test and evaluation plan

## Functional tests
- Upload/parse: PDFs accepted, OCR fallback, chunk counts
- Retrieval: relevant chunks, citation presence, groundedness checks
- Teach me: chapter brief includes all key points; examples present
- Ask me: MCQ validation, word-limit enforcement, rubric checks
- Voice: wake word detection, ASR/TTS flows, barge-in

## Metrics
- Coverage: matrix rows covered (%)
- MCQ accuracy
- Short/Long answer ROUGE-L/F1 vs. references
- Latency (P50/P95)
- Voice WER; wake-word FAR/FRR

## Acceptance criteria
- Matches approach-paper acceptance criteria.
