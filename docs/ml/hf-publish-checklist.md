# Hugging Face publish checklist (fine-tuned SLM)

1) Create a model repo
- Org/user: choose under your team
- Visibility: private (recommended during pilot) or public
- Name: commerce-slm-<subject>-<size>

2) Prepare artifacts
- LoRA: adapter .safetensors, adapter_config.json, training config (json), README.md (model card)
- GGUF: model.Q4_K_M.gguf (or your quant), optional tokenizer.model if required by runtime
- Include LICENSE/ATTRIBUTION; credit the base model and training method

3) Versioning
- Tag a release (e.g., v0.1.0) or use a commit hash; record it in docs and envs
- Publish sha256 checksums for each artifact

4) Model card (README)
- What: task, languages, domains; base model + licenses
- How: dataset creation, preprocessing, training params (epochs, lr, seq len)
- Eval: datasets, metrics (MCQ accuracy, ROUGE-L/F1), limitations
- Usage: short snippet for llama.cpp (GGUF) or PEFT (LoRA)

5) Upload
- CLI: huggingface-cli upload or git+LFS push
- Structure:
  /
  ├─ README.md
  ├─ model.Q4_K_M.gguf (if GGUF)
  ├─ adapter_model.safetensors (if LoRA)
  ├─ adapter_config.json (if LoRA)
  ├─ checksums.txt

6) Access control
- Private repo: create a read token (HF_TOKEN) for server/CI
- Public repo: no token needed

7) Backend config
- Set envs: MODEL_REGISTRY=huggingface, MODEL_ID, MODEL_VERSION, MODEL_TYPE, MODEL_FILE or LORA_ID, BASE_MODEL, HF_TOKEN (if private)
- See docs/ml/hf-access.md for loader patterns

8) Smoke test
- On a server/VM, run a tiny script to download the artifact via hf_hub_download and print sha256; then load once

9) Monitor & roll back
- Keep old tags; pin backend to a tag; change tag only when you’re ready
- Log model id/version on startup; roll back by reverting env
