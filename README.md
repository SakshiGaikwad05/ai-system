# AI Systems Technical Assignment

This repository contains my implementation for an AI systems technical assignment covering:

1. Token and cost optimization in an agent pipeline
2. Debugging a multi-step agent workflow
3. CI/CD and staging deployment with GitHub Actions

The goal was to demonstrate practical optimization, debugging, testing, and deployment discipline.

---

## Part 1 — Token / Cost Optimization

### Problem

The scenario describes an agent-based pipeline consuming approximately 100K input tokens per query, making it expensive and slow at scale.

I created a reproducible benchmark that compares a baseline pipeline with an optimized version.

### Optimizations

#### 1. Context Pruning

The baseline passes all available documents/context through the pipeline.

The optimized version removes irrelevant context before sending data to downstream agents.

This reduces repeated tokens while preserving information relevant to the final decision.

**Tradeoff:** Aggressive pruning could remove useful information.

**Mitigation:** Relevant facts required for the final decision are preserved and verified through quality checks.

#### 2. State Compression

Instead of passing the complete analyzer output and previous context to the decision stage, the optimized pipeline passes a compact structured representation containing only the information required downstream.

**Tradeoff:** Compression can lose details that later agents may need.

**Mitigation:** The compressed state explicitly preserves decision-critical fields.

### Benchmark Results

| Metric | Baseline | Optimized |
|---|---:|---:|
| Input tokens | 1,841 | 493 |
| Tokens saved | - | 1,348 |
| Reduction | - | 73.2% |

For the assignment's 100K-token scenario, the measured reduction projects approximately to:

- Baseline: 100,000 input tokens
- Optimized: ~26,779 input tokens
- Saving: ~73,221 tokens per query

The 100K result is a projection based on the measured benchmark reduction, not a claim that the local sample itself consumed 100K tokens.

### Quality Validation

Optimization was accepted only when the baseline and optimized pipelines preserved the important output behavior.

The benchmark produced:

- Same recommendation
- Same score
- Same matched skills
- Same missing skills

This demonstrates token reduction without measurable quality loss on the included benchmark.

---

## Part 2 — Debugging an Intermittently Failing Agent Pipeline

The broken workflow reproduces three failure modes:

- Timeout
- Malformed output
- Silent success with incorrect data

The debugging process focuses on identifying the failing stage rather than treating the entire pipeline as one black box.

### Debugging Process

I first reproduced each failure deterministically and inspected stage-level traces.

The workflow was broken into:

`Retriever → Analyzer → Formatter → Validator → Integrity Check`

This made it possible to determine exactly where each failure occurred.

### Failure 1 — Timeout

**Root cause:** A transient Analyzer timeout could terminate the entire workflow.

**Fix:** Added a bounded retry strategy with a maximum number of attempts.

Retries are limited to timeout failures rather than retrying every exception.

### Failure 2 — Malformed Output

**Root cause:** The pipeline trusted structurally invalid model output, allowing invalid values to continue downstream.

**Fix:** Added Pydantic schema validation to enforce expected types, ranges, and allowed values.

Malformed output now fails explicitly instead of silently propagating.

### Failure 3 — Silent Wrong Data

**Root cause:** Structurally valid output could still belong to the wrong record.

Schema validation alone cannot detect this because the JSON may be perfectly valid.

**Fix:** Added a semantic integrity check comparing the output record ID against the original requested record ID.

A mismatch raises a data integrity error instead of reporting success.

### Testing

The project contains deterministic tests covering the optimization and debugging behavior.

Current test result:

`57 passed`

---

## Part 3 — CI/CD and Deployment

A GitHub Actions workflow is defined in:

`.github/workflows/ci-cd.yml`

### CI

The workflow runs on pushes and pull requests to `main`.

The CI job performs:

`Checkout → Setup Python → Install Dependencies → Ruff Lint → Pytest`

Deployment depends on CI succeeding, so a failed test or lint check prevents staging deployment.

### Staging Deployment

A staging deployment job runs after successful CI on pushes to `main`.

The repository contains the staging/deployment implementation under the `deployment/` directory.

This setup demonstrates the deployment gate:

`Push to main → CI → Staging`

### CI Issue Found During Setup

The first GitHub Actions run failed even though the tests passed locally.

The clean CI runner reported:

`No module named pytest`

The local environment already had pytest installed, but it had not been declared in `requirements.txt`.

I added `pytest>=8.0` to the project dependencies and pushed the fix.

The next GitHub Actions run completed successfully.

This demonstrates why testing in a clean CI environment is important: local machine state can hide missing dependencies.

---

## Secrets / API Keys

Secrets are never committed directly to the repository.

The project uses:

- `.env` for local secrets
- `.env` excluded through `.gitignore`
- `.env.example` containing only variable names/placeholders
- GitHub Actions Secrets for credentials required by CI/CD

In a real staging/production environment, secrets should also be environment-scoped so staging and production credentials remain isolated.

If a secret is accidentally committed, the credential should be revoked/rotated immediately and removed from repository history.

---

## Rollback Plan

If a production deployment breaks, my first five minutes would focus on restoring service rather than immediately debugging the new code.

1. Stop or pause further deployments.
2. Confirm the failure correlates with the latest release using health checks and logs.
3. Identify the last known-good deployment.
4. Roll back to that known-good immutable artifact/version.
5. Verify health checks and error rates after rollback.

After service is stable, investigate the root cause, add a regression test, fix the issue through CI and staging, and deploy again.

---

## Run Locally

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run all tests:

```bash
python3 -m pytest tests/ -v
```

Run lint:

```bash
ruff check .
```

Run the Part 1 benchmark:

```bash
python3 app.py
```

Run the Part 2 debugging demo:

```bash
python3 debugging/demo.py all
```

---

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── benchmarks/
├── debugging/
├── deployment/
├── src/
├── tests/
├── .env.example
├── .gitignore
├── app.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Summary

This project demonstrates:

- Measuring token usage instead of optimizing blindly
- Context pruning
- Agent-state compression
- Quality validation after optimization
- Stage-level debugging
- Bounded retry handling
- Structured output/schema validation
- Semantic data-integrity checks
- Automated linting and testing
- CI-gated staging deployment
- Secure secret handling
- Rollback planning

The measured benchmark reduced input tokens from **1,841 to 493 (73.2%)** while preserving the benchmark's expected output behavior.
