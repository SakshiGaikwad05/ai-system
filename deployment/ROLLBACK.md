# Rollback Plan

## Principles

- Every deployment is tied to an **immutable Git commit SHA**.
- The artifact is named `staging-build-<sha>` — the SHA ties the artifact
  to the exact source that produced it.
- Rollback means **redeploying a previously tested immutable artifact**,
  not rebuilding old source code during an incident.
- The same staging pipeline verifies every artifact, so the rollback target
  is a known-good artifact that already passed CI + smoke tests.

## First 5 minutes

### Minute 0–1 — Stop and assess

1. **Stop further deployments.** If an automated pipeline is running, halt it.
2. **Acknowledge the incident.** Notify the team.
3. **Identify the currently deployed commit/version.** Find the artifact name
   or commit SHA from the last successful deployment run (GitHub Actions
   workflow logs, artifact list, or deploy tracking).

### Minute 1–2 — Diagnose

4. **Inspect health checks / error logs / monitoring.**
   - Check smoke-test results from the last deployment.
   - Compare error rates before and after the deployment window.
5. **Determine whether the issue correlates with the latest deployment.**
   - If yes → proceed to rollback.
   - If no → investigate infrastructure / upstream dependencies instead.

### Minute 2–4 — Rollback

6. **Select the last known-good artifact.**
   - In GitHub Actions, navigate to the previous successful workflow run.
   - Download or reference the `staging-build-<previous-sha>` artifact.
7. **Redeploy the known-good artifact.**
   - CI/CD pipeline should support re-running a previous workflow or
     triggering a deploy with a specific artifact.
   - Do **not** rebuild from the old Git commit — rebuilds may produce
     different results due to dependency drift. Use the original artifact.
8. **Prefer rollback over debugging live production.** If the issue is
   clearly deployment-related, roll back immediately. Debugging on a broken
   system prolongs the incident.

### Minute 4–5 — Verify

9. **Confirm health / smoke checks pass** on the rolled-back artifact.
10. **Verify error rates return to baseline.**
11. **Communicate status.** Document what happened, what was rolled back,
    and what investigation remains.

## After stabilization

1. **Root cause analysis.** Reproduce the issue from the failed artifact
   or commit in an isolated environment.
2. **Add a regression test** that covers the failure mode.
3. **Fix through normal CI.** Push the fix to a branch, let CI run, open a
   pull request.
4. **Deploy to staging first.** The fix passes staging before any promotion.
5. **Promote only after verification.** The normal CI → staging → production
   pipeline ensures every environment validates the change.

## Database migrations

This project does not use a database. The following guidance applies if a
database were added:

- **Prefer backward-compatible migrations.** Adding columns or tables is
  safe to roll forward; renaming or dropping columns is not.
- **Separate irreversible migrations from the application deploy.** Run
  data migrations as a distinct step that can be independently verified.
- **Application rollback does not automatically rollback the database
  schema.** If a schema change is irreversible, the application must remain
  compatible with both old and new schema during the transition window.

## Production deployment (conceptual)

This repository does **not** deploy to production. The following would apply
if production were added:

- Production uses a separate GitHub environment (`production`).
- A `deploy-production` job would require manual approval (GitHub
  Environments with required reviewers).
- Production deployment would use the same artifact that passed staging.
- The rollback process would be identical: redeploy the last known-good
  staging artifact, not rebuild from source.
