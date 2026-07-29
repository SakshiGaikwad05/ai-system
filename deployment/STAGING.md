# Staging Deployment

## What "staging" means for this project

This is a **CLI-based Python assessment project** — not a web application or
long-running service. The "staging" environment represents a **validated
artifact** that has passed CI, smoke tests, and is packaged for distribution or
further testing.

## Deployment pipeline

```
main push
   │
   ▼
CI (must pass)
   │  - lint
   │  - tests
   ▼
deploy-staging job
   │  - smoke test: app.py
   │  - smoke test: python -m debugging.demo normal
   ▼
Package artifact ───→ upload to GitHub Actions run
```

- **CI** validates every push and pull request to `main`.
- **Staging** runs **only after CI passes** on a `push` to `main`.
- Staging executes **smoke tests** that exercise the actual application:
  - `python app.py` — Part 1 cost optimisation benchmark (deterministic mode)
  - `python -m debugging.demo normal` — Part 2 debugging workflow
- Smoke tests **must pass** without external API keys.
- After smoke tests pass, the project is packaged into a **GitHub Actions
  artifact** (`staging-build-<commit-sha>`).
- The artifact is tied to the exact **commit SHA** and workflow run.

## GitHub environment

A GitHub environment named **`staging`** is used to:
- Gate the deploy-staging job.
- Isolate environment-level secrets if needed.
- Provide audit visibility in the repository's Environments page.

## What the artifact contains

```
staging-artifact/
├── app.py
├── requirements.txt
├── .env.example
├── src/
├── debugging/
├── tests/
└── benchmarks/
```

This is enough to reproduce the full assessment:

```bash
pip install -r requirements.txt
python app.py
python -m pytest tests/ -v
python -m debugging.demo all
```

## Important note

This is **artifact-based staging** for a CLI assessment project — NOT a live
web server deployment. There is no production deployment in this pipeline.
The artifact serves as a deployable unit that can be downloaded, inspected,
or promoted following the same process used for real service deployments.
