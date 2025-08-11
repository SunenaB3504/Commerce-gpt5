# Security & privacy

## Principles
- Data minimization; no PII stored by default
- Local-first processing when feasible

## Controls
- File size/type validation and scanning
- Rate limits and CORS
- Auth (optional for prototype) for uploads and history

## Threats
- Malicious PDFs, prompt injection via content, wake-word spoofing
- Mitigations: sanitize PDF text; ground-only prompts; keyword sensitivity settings
