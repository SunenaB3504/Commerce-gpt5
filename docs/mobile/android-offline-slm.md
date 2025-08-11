# Android/tablet offline SLM plan

Goal: A standalone Android app (phone/tablet) that runs a very small fine‑tuned SLM fully offline, with an on-device mini-RAG over chapter JSONs.

## Model choices (tiny, offline‑friendly)
- Llama 3.2 1B Instruct (CPU‑friendly with 4‑bit quant)
- Phi‑3 mini (inference‑friendly at small sizes)
- Qwen2.5 1.5B Instruct (check license; 4‑bit)
- Prefer ≤2B params for smoother CPU inference; quantize to Q4_K_M or similar

## Inference frameworks on Android
- llama.cpp (android): JNI bindings; GGUF models (Q2–Q5)
- MLC LLM: Vulkan/GPU acceleration; Android AAR; model compilation step
- ONNX Runtime GenAI: ONNX models; NNAPI/GPU where available

Recommendation: Start with llama.cpp Android (simplest path with GGUF), then evaluate MLC LLM for speedups.

## Fine‑tuning + quantization pipeline
1) Train LoRA on Colab for the 1B–2B model (short epochs; 2–3e)
2) Merge LoRA into base (server-side) to a fp16 model
3) Convert to GGUF and quantize (Q4_K_M; try Q3_K_M for lower RAM)
4) Smoke test locally with llama.cpp
5) Package GGUF in the Android app assets or download on first run

## On‑device mini‑RAG
- Store chapter chunks as JSON in app assets or downloaded packs
- Build a tiny TF‑IDF or approximate vector index using lightweight JS/NDK libs
- Alternatively, precompute a nearest‑neighbor map off-device and ship per‑chapter lookups
- Always show citations; keep answers book‑bound

## Device requirements
- RAM: 4–6 GB recommended for Q4 1–2B; 3 GB devices may need Q3
- Storage: 0.5–2 GB for model + data packs
- CPU: big.LITTLE with recent ARMv8; optional GPU via MLC

## App architecture
- Core: Kotlin/Jetpack Compose UI
- Inference: llama.cpp JNI module; background thread; streaming tokens
- Data: local JSON store + simple index; opt-in data pack updates
- Voice (optional offline): Vosk/PocketSphinx (ASR), TTS via Android TTS engine

## Packaging & updates
- Option A: Bundle GGUF + data packs as APK expansion (OBB) or app bundle asset packs
- Option B: First‑run download from CDN with checksum verification

## Risks & mitigations
- Latency on low‑end phones → Use 1B Q4/Q3, reduce context, enable KV cache reuse
- Memory pressure → Use lower quant, smaller context windows (e.g., 1–2k)
- Quality vs. size → Lean on mini‑RAG and tighter prompts; curate dataset well

## Next steps
- Pick target model (e.g., Llama 3.2 1B Instruct)
- Run a micro fine‑tune + quantization and measure token/s on a representative device
- Prototype llama.cpp Android integration with a demo prompt and JSON chunk lookup

## Full offline vs PWA
- For universal offline (including low-end devices and areas with poor connectivity), native Android with a bundled GGUF model is the most reliable approach.
- PWA full offline is possible only on devices with WebGPU + enough RAM; otherwise it must fall back to online inference. Use Android for guaranteed offline access.
