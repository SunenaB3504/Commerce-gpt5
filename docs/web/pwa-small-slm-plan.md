# PWA plan using small SLM (mobile-first web app)

Goal: Deliver a mobile-friendly Progressive Web App (PWA) that uses a small SLM so that a native mobile app can be optional, not required.

## Deployment shapes
- Default: Backend inference (FastAPI + llama.cpp) and static PWA via GitHub Pages
- Optional: In-browser model (WebGPU) for capable devices; fallback to backend

## PWA capabilities
- Installable to home screen (manifest.json)
- Offline-first UX via service worker: cache shell (HTML/CSS/JS), icons, and static data packs
- Background sync to prefetch data packs when online

## Model options
- Backend: GGUF 1–2B at Q4_K_M via llama.cpp, shared across users on server
- Browser (optional experimental): WebGPU with MLC LLM or ONNX Runtime Web if a tiny model is feasible; else skip

## RAG on web
- Static JSON data packs hosted on GitHub Pages (manifest + chunks)
- Client performs lightweight retrieval (TF‑IDF or precomputed nearest neighbors) to build context windows for requests
- Server completes generation with strict book-only prompts + citations

## Architecture
- Frontend: Vanilla HTML/CSS/JS PWA; responsive mobile UI
- Service worker: cache app shell and latest data packs; fall back to cached on offline
- Backend: FastAPI endpoints /ask, /teach, /evaluate using llama.cpp model

## Offline behavior
- Teach me: Works offline with pre-cached outlines, summaries, and practice sets (derived from data packs)
- Ask me: Limited offline mode using pre-baked answer snippets or on-device templated responses; full generation requires online model unless using WebGPU path

## Full offline mode (in-browser model)
When device supports WebGPU and has sufficient RAM, the PWA can run a tiny model fully offline:
- Engine: MLC WebLLM or ONNX Runtime Web (WebGPU backend)
- Model: ≤2B params, quantized and compiled for WebGPU (split into 50–100 MB shards)
- Data: On-device RAG using cached JSON data packs

Device requirements (practical)
- Android Chrome 121+ with WebGPU enabled, ≥4 GB RAM recommended
- Storage budget 0.6–1.2 GB for model + data packs

Distribution
- Ship a separate “model pack” downloadable from inside the PWA; service worker caches artifacts with checksums
- Host large model files via CDN (HF Hub or object storage); Pages is fine for manifests but not ideal for multi-GB

Runtime behavior
- Capability check at startup (WebGPU + memory)
- If supported: load model in a dedicated worker, stream tokens to UI, keep context ≤1–2k
- If unsupported: fall back to backend inference or inform user to use the Android offline app

Limits
- Not all devices/browsers support WebGPU; performance varies widely
- iOS Safari has limited WebGPU; offline generation may not be feasible on iOS

## Performance targets (mobile phones)
- TTI < 2.5s on 4G; answer P50 < 6s via backend small SLM
- Payload budgets: < 200 KB initial JS; lazy load voice modules

## Steps to implement
- Add PWA scaffolding: manifest.json, service worker, icons
- Implement data pack caching and versioning (manifest with checksums)
- Add mobile-first UI styles and touch-friendly controls
- Connect /ask and /teach endpoints; stream tokens to UI
- Add offline fallbacks for Teach me and cached practice sets
- Optional: Integrate WebGPU model gating on device capability

## Pros and trade-offs
- Pros: One codebase, installable experience, offline support for study flows
- Trade-offs: Generation offline is limited unless we ship a browser model; server still needed for best quality

## Next steps
- Confirm PWA is acceptable as the primary mobile experience
- Implement PWA shell and data caching; connect to backend small SLM
- Defer native Android unless device-only inference is critical
