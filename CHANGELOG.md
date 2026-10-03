# Changelog

All notable changes to Verified Support Assistant are recorded here. The
project follows semantic versioning.

## [0.3.0] - 2026-10-03

### Added

- React 19 + TypeScript + Vite application with routed Assistant, Policies,
  Policy Detail, Evaluations, and About workspaces.
- TanStack Query server-state layer and an OpenAPI-generated TypeScript contract.
- Streaming `POST /api/ask/stream` progress and typed policy/evaluation endpoints.
- Desktop navigation rail, mobile tab bar, timeline, local history, evidence
  drawer, export/copy/reset actions, theme persistence, and keyboard shortcuts.
- Five Vitest component/accessibility tests and 40-case axe/browser verification.
- Multi-stage non-root Docker build and complete nested static-wheel packaging.

### Changed

- Replaced the framework-free 0.2 browser client with an intentionally designed
  responsive support studio.
- Updated CI to validate Python and frontend lint/type/test/build/evaluation gates.
- Updated Sandbox deployment to install the exact built wheel and capture the
  integrated production bundle rather than repository source.

### Verified

- 33 Python tests and 5 frontend tests pass.
- The 40-case deterministic benchmark retains 100% retrieval, refusal, and
  required-keyword coverage.
- CoreWeave Sandbox `e63ad8a2-72a2-44a8-a9b2-f1909d8b3ee7` installed the
  standalone wheel and reproduced all 40 browser cases with 40 unique
  screenshots and no serious/critical axe findings.

## [0.2.0] - 2026-10-02

- Added the citation-first FastAPI browser app, policy discovery, hosted-model
  comparison, W&B/Weave observability, security headers, and browser evidence.

## [0.1.0] - 2026-10-01

- Added the versioned synthetic corpus, TF-IDF retrieval, guardrails, extractive
  response baseline, and deterministic evaluation harness.