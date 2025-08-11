# Fine-tune plan (Colab)

## Objectives
- Improve instruction following and CBSE-style formatting; keep RAG as primary grounding.

## Dataset
- Generate Q/A per chapter and question type; include citations.
- Sample human review; auto checks for leakage and citation correctness.

## Training
- LoRA/QLoRA on small models (1–3B); 2–3 epochs; seq len 2k–4k.
- Early stopping; validation split by chapter.

## Export & serving
- Export GGUF for llama.cpp (CPU); keep API fallback.

## Evaluation
- Held-out chapter Q/A; MCQ accuracy; ROUGE-L/F1; latency.
