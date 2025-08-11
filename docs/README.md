# Documentation index

Purpose: Keep product, technical, and operational decisions aligned before and during development. Each doc has a clear owner and update cadence.

- prd.md — Product Requirements (what and why)
- functional-spec.md — User flows, features, acceptance criteria
- technical-design.md — Architecture, components, data & sequence flows
- api/openapi.yaml — HTTP API contract
- data/schema.md — Storage schemas and retention
- content/coverage-matrix.md — Exam-ready coverage tracking per chapter
- policies/content-policies.md — Book-only guardrails, style/word limits
- evaluation/test-plan.md — QA, metrics, acceptance tests
- voice/ux-flows.md — Voice states, wake word, UX flows
- ml/fine-tune-plan.md — Dataset, LoRA plan, eval, export
- deployment/hosting.md — GitHub Pages, backend hosting, runbook
- security/privacy.md — Privacy, security boundaries, threat model

How to use
- Treat these as living docs; update per milestone.
- Link PRs to doc sections that change.
- Keep decisions in technical-design.md or dedicated ADRs (if added later).
