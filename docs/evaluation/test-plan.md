# Test and evaluation plan

## Functional tests

## QnA evaluation harness (Day 6)
- Prompts: `docs/evaluation/prompts/econ_ch3_sample.json`
- Run:
	- Activate venv and start API, then in another terminal:
	- `python scripts/eval_qna.py --prompts docs/evaluation/prompts/econ_ch3_sample.json --k 5 --retriever bm25 --out docs/evaluation/results/econ_ch3_sample.json`
- Output: JSON with summary and per-question rows written under `docs/evaluation/results/`.

### Tuning short-answer validation (configurable thresholds)
- You can tune /answer/validate scoring without code changes using environment variables before starting the API:
	- VALIDATE_W_COVERAGE (default 0.50)
	- VALIDATE_W_COSINE (default 0.25)
	- VALIDATE_W_STRUCTURE (default 0.15)
	- VALIDATE_W_TERMINOLOGY (default 0.10)
	- VALIDATE_CORRECT_MIN (default 80.0)
	- VALIDATE_PARTIAL_MIN (default 50.0)
	- VALIDATE_COVERAGE_POINT_OVERLAP (default 0.60)
	- VALIDATE_STRUCTURE_MIN_HINT (default 0.50)
	- VALIDATE_TERMINOLOGY_MIN_HINT (default 0.40)
	- VALIDATE_OFF_TOPIC_COSINE_MAX (default 0.30)
	- VALIDATE_OFF_TOPIC_COVERAGE_MAX (default 0.30)

- Notes:
	- Weights are auto-normalized to sum to 1.0 if you override them.
	- Threshold ranges are validated; out-of-range values are clamped.
	- Restart the API after changing env vars.

- Example (Windows PowerShell):
	- $env:VALIDATE_W_COVERAGE = "0.6"; $env:VALIDATE_CORRECT_MIN = "85"; uvicorn services.api.main:app --reload

## Metrics

## Acceptance criteria
