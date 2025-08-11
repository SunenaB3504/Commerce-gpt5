# Day 1 – User-level Test Guide (Pre-Day 2)

Goal: validate the user-visible skeleton before parsing/RAG exists.

Scope (what should work)
- Open web UI and see upload form.
- Upload a .pdf and receive a success response.
- Health endpoint returns ok.

Pre-reqs
- Windows 10/11, VS Code.
- Python 3.11 installed (recommended).

Steps A. One-click smoke (PowerShell)
1) In VS Code Terminal (PowerShell):

```
cd C:\Users\Admin\Sunil\llm\Commerce-gpt5
./scripts/smoke-day1.ps1
```

Expected:
- Health JSON prints `{ "status": "ok" }`.
- Upload returns JSON with id, filename, subject, chapter.
- Negative test for non-PDF shows HTTP 400.

Steps B. Manual API checks (REST Client)
1) Start server:
```
. .\.venv\Scripts\Activate.ps1
python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
```
2) Open `scripts/day1.rest` in VS Code, click Send Request for each.

Steps C. UI check
1) With server running, open `web/index.html` with Live Server or using a simple static server.
2) Use the form to upload a small PDF and confirm the toast/response.

Troubleshooting
- PyMuPDF install errors: not needed for Day 1. Use minimal deps (script installs fastapi, uvicorn, pydantic, python-multipart only). Full parse stack will be added on Day 2 with Python 3.11.
- CORS issues: ensure `config.js` points to `http://127.0.0.1:8000`.
- Port busy: change `--port 8001` in the script and config.

Exit criteria (pass/fail)
- Pass: Health ok, upload ok in API and UI, non-PDF rejected with 400.
- Fail: Any of the above missing or server crashes.
