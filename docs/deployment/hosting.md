# Deployment & hosting

## Frontend (GitHub Pages)
- Serve static site from /web via Pages (main or gh-pages)
- Configure API base URL via /web/assets/js/config.js

## Backend
- Host FastAPI on a CPU-friendly PaaS (Railway/Render/Azure App Service)
- Persistent storage: file store + SQLite/Postgres; vector DB co-located
- HTTPS, CORS to Pages domain

## Hosting data on GitHub (JSON over GitHub Pages)
It’s feasible to host non-sensitive, moderate-size datasets as JSON in the same repository and serve them via GitHub Pages. Recommended when:
- Total dataset is small-to-medium (tens of MBs, not GBs)
- Public access is acceptable (no private textbook content)
- Client apps only need read-only access

Folder layout (example)
- /web/data/index.json — manifest
- /web/data/subjects/<subject>/chapters/<chapter>/chunks-001.json — text chunks with metadata
- /web/data/questions/<subject>/<chapter>/mcq.json — public practice items

Access URLs
- https://<user>.github.io/<repo>/data/index.json (Pages domain; generally CORS-friendly)
Avoid raw.githubusercontent.com for cross-origin fetches due to CORS variability.

Constraints and best practices
- Size limits: keep repo < 1 GB; single file < 100 MB (or use Git LFS). Split large datasets into multiple JSON files (5–10 MB each).
- Bandwidth/rate limits: GitHub Pages/CDN is fine for light-to-medium traffic, not a heavy API. For scale, move to a CDN/object store (S3/Cloudflare R2/Azure Blob) with proper CORS.
- Caching: Pages sets cache headers; version your files (v1/, v2/) or include content hashes in filenames and update the manifest.
- Integrity: include sha256 checksums in the manifest for clients to verify downloads.
- Privacy/IP: do not publish verbatim copyrighted book text without license. Prefer derived artifacts (metadata, question banks, summaries) or keep raw text private on the backend.

Minimal manifest fields
- version, generatedAt, subjects[], chapters[], files[{url, bytes, sha256, purpose}]

## Runbook
- Zero-downtime deploys; backup docs & DB; log/metric checks post-release

## Fine-tuned model storage (where to keep SLM artifacts)
You have two artifact types after fine-tuning:
1) LoRA adapters (small, 50–300 MB, safetensors) applied to a base model at runtime
2) Fully merged/quantized weights for CPU (e.g., GGUF for llama.cpp, often 1–4+ GB)

Recommended storage options
- Hugging Face Hub (preferred): versioned model repos, public or private, supports big files and model cards.
	- Pros: Built-in LFS, versioning, community tooling; easy to consume from backend.
	- Use case: Both LoRA adapters and quantized GGUFs.
- Object storage + CDN (S3/Cloudflare R2/Azure Blob): private bucket with signed URLs and CORS to your API host.
	- Pros: Reliable, scalable, control over access; good for large GGUF.
- GitHub Releases (only for small LoRA adapters): attach .safetensors as release assets; avoid huge files/bandwidth limits.
	- Not recommended for multi-GB GGUF.

Using GitHub LFS (can, but with caveats)
- Feasibility: Yes, you can store model artifacts in GitHub LFS and pull them in CI/CD or on server boot.
- Suitability: Reasonable for smaller artifacts (e.g., LoRA adapters in the tens to low hundreds of MB). Not ideal for multi-GB GGUF models or high-traffic downloads due to LFS storage/bandwidth quotas and rate limits.
- Access method: Use the git LFS client to clone/pull; avoid serving directly to browsers. For backend bootstrapping, authenticate with a PAT (if private) and fetch once, then cache.
- Pros: Centralized with your code; simple ACL via repo visibility.
- Cons: Quotas/costs for bandwidth/storage, slower cold-starts, less CDN optimization than HF Hub or object storage.
- Recommendation: Prefer HF Hub or object storage for GGUF; consider LFS only for LoRA adapters or internal/dev flows.

Startup/download flow (backend)
1) On boot, read env vars (MODEL_REGISTRY, MODEL_ID, MODEL_VERSION, MODEL_TYPE=lora|gguf).
2) If MODEL_TYPE=gguf: stream/download GGUF to local cache (e.g., /models/<id>/<ver>/model.gguf), verify checksum, load in llama.cpp.
3) If MODEL_TYPE=lora: ensure base model present (license‑compatible), download LoRA adapter, merge/apply with PEFT at load time.
4) Cache and reuse between restarts; periodically verify ETag/sha256 for updates.

Versioning and integrity
- Use semantic versions (e.g., 0.3.1) and immutable artifact paths.
- Publish checksums (sha256) and store alongside artifacts.
- Keep a model card (README) with base model, license, training data description, and eval metrics.

Licensing & IP notes
- Ensure base model license allows fine‑tuning and redistribution.
- If your training data contains copyrighted book text, prefer LoRA adapters and keep raw training text private; avoid distributing merged weights that could leak verbatim content.

Environment variables (example)
- MODEL_REGISTRY=huggingface|s3|azureblob|github
- MODEL_ID=org/commerce-slm-eco-bst-acc
- MODEL_VERSION=v0.1.0
- MODEL_TYPE=gguf|lora
- MODEL_URL=https://huggingface.co/org/commerce-slm-eco-bst-acc/resolve/v0.1.0/model.Q4_K_M.gguf
- MODEL_SHA256=<checksum>
