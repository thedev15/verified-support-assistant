# Contributing

Thanks for improving Verified Support Assistant. Keep changes inspectable,
bounded, and evidence-backed.

## Development workflow

1. Create a feature branch from the latest `main`.
2. Create and activate a Python 3.11+ virtual environment.
3. Install with `python -m pip install -e ".[dev]"`.
4. Make focused changes with tests.
5. Run `make check` before opening a pull request.
6. Describe behavior changes, safety implications, and any generated evidence.

See [`docs/LOCAL_DEVELOPMENT.md`](docs/LOCAL_DEVELOPMENT.md) for operating
system instructions and optional tooling.

## Quality expectations

- Preserve explicit refusal for unsupported or account-specific requests.
- Do not add a citation unless the final answer actually references it.
- Add benchmark cases for new supported behavior and regression tests for bugs.
- Keep the default path deterministic and free of paid model calls.
- Build API content with safe DOM APIs; do not inject model output as HTML.
- Maintain keyboard, screen-reader, responsive, reduced-motion, and contrast
  behavior when changing the UI.
- Never commit credentials, private customer data, `.env`, W&B runtime files,
  or unreviewed generated output.

## Generated browser evidence

UI changes make previous screenshots historical. To regenerate evidence, start
the app, install Playwright Chromium, and run `make capture`. The capture must
pass all 40 cases and ZIP validation. Review the manifest and representative
answer/refusal screenshots before committing generated files.

## Dependencies

Prefer the standard library and existing dependencies. Explain why a new
runtime dependency is necessary, constrain it to a compatible major version,
and include its security and maintenance implications in the pull request.

## Commit and pull-request hygiene

Use an imperative commit subject, keep temporary logs out of commits, and avoid
mixing unrelated refactors with behavior changes. Pull requests should include
the exact test and evaluation commands run and identify any known limitation.