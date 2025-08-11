# Accessing Hugging Face models at runtime

Goal: Load your fine-tuned SLM (LoRA or GGUF) from Hugging Face Hub in the backend. Do not fetch model files from the browser.

## Options
- Quantized CPU weights (GGUF) → load with llama.cpp (llama-cpp-python)
- LoRA adapter (safetensors) → apply to base model with PEFT/transformers

## Authentication
- Public repo: no token needed
- Private repo: set HF_TOKEN via environment variable; never embed in frontend

## Version pinning
- Use a tag or commit hash (revision) to avoid drifting artifacts

## Environment variables
- MODEL_REGISTRY=huggingface
- MODEL_ID=org/commerce-slm-eco-bst-acc
- MODEL_VERSION=v0.1.0              # tag or commit hash
- MODEL_TYPE=gguf|lora
- MODEL_FILE=model.Q4_K_M.gguf      # for gguf
- LORA_ID=org/commerce-slm-lora     # for lora
- BASE_MODEL=meta-llama/Llama-3-Instruct-8B  # license-compatible base
- HF_TOKEN=...                      # only if private

## GGUF (llama.cpp) pattern
```python
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
import os

model_path = hf_hub_download(
    repo_id=os.getenv("MODEL_ID"),
    filename=os.getenv("MODEL_FILE"),
    revision=os.getenv("MODEL_VERSION"),
    token=os.getenv("HF_TOKEN")
)
llm = Llama(
    model_path=model_path,
    n_ctx=4096,
    n_threads=os.cpu_count(),
)
# now use llm("prompt") or llama.cpp chat API wrappers
```

## LoRA (transformers + peft) pattern
```python
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from huggingface_hub import login

hf_token = os.getenv("HF_TOKEN")
if hf_token:
    login(token=hf_token)

base_id = os.getenv("BASE_MODEL")
lora_id = os.getenv("LORA_ID")
revision = os.getenv("MODEL_VERSION")

# Load base
tok = AutoTokenizer.from_pretrained(base_id, revision=revision, use_fast=True)
base = AutoModelForCausalLM.from_pretrained(
    base_id, revision=revision, torch_dtype="auto", device_map="auto"
)
# Attach LoRA
model = PeftModel.from_pretrained(base, lora_id, revision=revision)
model.eval()
```

## Caching & storage
- huggingface_hub caches under ~/.cache/huggingface by default
- Prefer explicit cache dir (e.g., /models/<id>/<version>/) if running in containers

## Integrity & security
- Pin revision; optionally verify sha256 if you publish checksums
- Do not expose HF_TOKEN or model URLs to the frontend
- Log model id/version at startup for traceability

## Startup checklist
- Read env vars → resolve artifact(s) → download/cache → verify → load
- Fail fast with clear errors if artifact missing or license mismatch

## References
- docs/deployment/hosting.md (fine-tuned model storage)
- docs/technical-design.md (component startup)
