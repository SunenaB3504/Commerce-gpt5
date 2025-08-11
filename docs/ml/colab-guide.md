# Google Colab guide (high‑resource steps)

Use Colab for GPU/CPU‑heavy tasks; keep day‑to‑day usage local. This guide lists what to run on Colab, with a minimal recipe for each step.

## What to run on Colab (high‑resource)
- OCR at scale (optional): if many scanned PDFs; otherwise run locally.
- Embedding generation for all chapter chunks (GPU recommended).
- Synthetic Q/A generation (optional) using an API/model for training data.
- LoRA fine‑tuning (GPU): train adapters on selected small model (1–2B).
- Merge + quantization to GGUF (CPU/GPU): prepare for CPU inference.
- Batch evaluation (metrics) across many samples.

## 0) Setup
- Create a new Colab notebook with a GPU runtime (T4/A100 preferred).
- Mount Google Drive or use temporary storage; push artifacts to Hugging Face Hub when done.

```python
!pip -q install sentence-transformers datasets transformers peft accelerate bitsandbytes
!pip -q install huggingface_hub[cli]
```

Login (private repos only):
```python
from huggingface_hub import login
login(token="<HF_TOKEN>")
```

## 1) Parse & chunk (if needed)
If your PDFs are large or scanned, do this in Colab; otherwise you can run locally.

```python
!pip -q install pymupdf pdfminer.six pytesseract
# 1) Extract text per page  2) Clean  3) Chunk (e.g., 300–800 tokens w/ overlap)
```

Output: JSON files like /data/subjects/<subject>/chapters/<chapter>/chunks-001.json

## 2) Embeddings (GPU)
```python
from sentence_transformers import SentenceTransformer
import json, numpy as np

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cuda')
# load chunks → batch encode → save npy or parquet
```

Output: per‑chunk vectors (.npy) or embedded JSON; upload to storage (optional).

## 3) Synthetic Q/A (optional)
- Use an API or a local small model to generate MCQ, 3m/4m/6m items referencing chunk citations.
- Save as JSONL (train/val).

## 4) LoRA fine‑tuning (GPU)
```python
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

base = "<base-small-model>"  # e.g., meta-llama/Llama-3.2-1B-Instruct
 tok = AutoTokenizer.from_pretrained(base, use_fast=True)
 mdl = AutoModelForCausalLM.from_pretrained(base, torch_dtype="auto", device_map="auto")
 peft = get_peft_model(mdl, LoraConfig(r=16, lora_alpha=16, lora_dropout=0.05, target_modules=["q_proj","v_proj"]))

train = load_dataset("json", data_files="train.jsonl")["train"]
args = TrainingArguments(output_dir="out", per_device_train_batch_size=4, gradient_accumulation_steps=4,
                         num_train_epochs=2, learning_rate=2e-4, lr_scheduler_type="cosine",
                         warmup_ratio=0.03, logging_steps=50, save_total_limit=2)
trainer = SFTTrainer(model=peft, args=args, train_dataset=train, tokenizer=tok, max_seq_length=1024)
trainer.train()
peft.save_pretrained("lora_out")
```

Push to Hub (optional):
```python
!huggingface-cli upload <org>/<repo> lora_out/adapter_model.safetensors lora_out/adapter_config.json --repo-type model
```

## 5) Merge & quantize to GGUF
```python
# Merge LoRA → FP16
from peft import PeftModel
merged = PeftModel.from_pretrained(mdl, "lora_out").merge_and_unload()
merged.save_pretrained("merged-fp16")

# Convert to GGUF + quantize (llama.cpp)
!git clone https://github.com/ggerganov/llama.cpp
%cd llama.cpp
!python convert-hf-to-gguf.py ../merged-fp16 --outfile ../model-fp16.gguf
!./quantize ../model-fp16.gguf ../model.Q4_K_M.gguf Q4_K_M
```

Upload GGUF to Hub:
```python
!huggingface-cli upload <org>/<repo> ../model.Q4_K_M.gguf --repo-type model --revision v0.1.0
```

## 6) Evaluation (optional)
- Compute MCQ accuracy, ROUGE-L/F1 on held-out chapter answers.
- Log metrics in the model card.

## 7) Bring artifacts to your laptop (offline test)
- Preferred: Download from Hugging Face using hf_hub_download in your backend (Windows laptop).
- Or manually download model.Q4_K_M.gguf and store under c:/models/<id>/<version>/.

Run local backend (CPU) and PWA against localhost:
- Backend: FastAPI + llama.cpp (point to GGUF path)
- Frontend: open web/index.html (or serve via a simple HTTP server) and set API base to http://localhost:8000

That’s it—you leverage Colab for heavy work, store the model on Hugging Face, and test locally offline.
