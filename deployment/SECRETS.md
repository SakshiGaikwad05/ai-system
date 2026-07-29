# Secrets Management

## Local development

- **Never commit `.env`.** It is listed in `.gitignore`.
- `.env.example` contains placeholder values only — never real credentials.
- Local development uses `.env` (copy from `.env.example` and fill in your
  own key).

```bash
cp .env.example .env
# edit .env with your credentials
```

## GitHub Actions

Secrets are stored in **GitHub repository / environment secrets** — never in
repository files or workflow YAML.

### Access in workflows

```yaml
env:
  NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
```

- The `${{ secrets.NAME }}` syntax is evaluated at runtime by GitHub.
- Secrets are masked in logs — they appear as `***`.
- **Never `echo` a secret** or pass it to a command that may leak it.

### Our current setup

The CI/staging pipeline in this repository **does not require any secrets**.
All smoke tests and benchmarks run in deterministic (mock) mode. The
`NVIDIA_API_KEY` is only needed when passing `--live` to `app.py`, which is
not part of CI/staging.

If a future step required API access, the key would be added as a
repository secret and referenced in the workflow.

### Principle of least privilege

- **Repository secrets** are available to all workflows on the repository.
- **Environment secrets** are scoped to a specific GitHub environment
  (e.g., `staging`). Only jobs with `environment: staging` can access them.
- **Production secrets** must never be available to staging jobs.
- Each environment should use separate credentials.

### If a secret is exposed

1. **Revoke immediately** at the provider (NVIDIA, AWS, etc.).
2. **Rotate** the GitHub secret to a new value.
3. **Audit** workflow logs to confirm the exposure window.
4. Consider [GitHub secret scanning](https://docs.github.com/en/code-security/secret-scanning)
   to detect future leaks automatically.

## Environment separation

| Environment | Secrets scope | Used by |
|-------------|--------------|---------|
| Local       | `.env` (gitignored) | Developer machine |
| CI          | Repository secrets (if needed) | `push` / `PR` triggers |
| Staging     | Environment: `staging` | Push to `main` after CI |

Production (if added later) would use a separate `production` environment
with its own credentials, inaccessible to staging workflows.
