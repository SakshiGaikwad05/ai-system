# Debugging Process — Multi-Step Agent Workflow

## General Approach

1. **Reproduce deterministically** — each scenario is triggered by a `failure_mode` parameter so failures are 100% repeatable.
2. **Capture request_id** — every execution gets a unique ID; all stage logs carry it.
3. **Inspect structured logs** — `Logger.by_request(request_id)` returns every stage, its status, duration, attempt count, and any error details.
4. **Find the first diverging stage** — scan logs in order; the first stage with `status != "success"` is where the pipeline deviates.
5. **Isolate that stage** — call the failing agent directly with known inputs.
6. **Identify root cause** — examine the agent's logic for the missing guard.
7. **Apply the smallest fix** — add a single guard (retry, schema validation, semantic check).
8. **Add a regression test** — cover the exact failure signature.
9. **Run full workflow** — confirm other scenarios are unaffected.
10. **Verify expected behavior** — the fixed pipeline raises the correct typed exception with useful context.

---

## Scenario 1 — Timeout

### What was inspected
- **Stage latency**: the analyzer stage exceeded the configured timeout (0.1 s).
- **Attempt count**: the broken pipeline made no retry; the fixed pipeline logged two attempts — first timeout, second success.

### Root cause
The analyzer had **no resilience for transient timeouts**. A single slow response killed the entire workflow.

### Fix
Added a bounded retry loop around the analyzer stage:
- Maximum 2 attempts.
- Only transient `TimeoutError` triggers a retry (not validation or integrity errors).
- If both attempts fail, raise `WorkflowTimeoutError`.

---

## Scenario 2 — Malformed Output

### What was inspected
- **Raw Formatter output**: the stage produced valid JSON but with invalid semantic values (score out of range, status not in allowed set).
- **Missing schema contract**: no structured validation existed between Formatter and downstream stages.

### Root cause
No output contract was enforced. Malformed data flowed through to the final result without rejection.

### Fix
Added strict schema validation using a Pydantic model (`AnalyzerOutput`):
- `record_id`: non-empty string.
- `score`: integer 0–100.
- `status`: one of `approved`, `review`, `rejected`.
- If validation fails, raise `MalformedOutputError` with the Pydantic error message.
- Fields are **not** silently filled or defaulted.

---

## Scenario 3 — Silent Wrong Data

### What was inspected
- **Requested ID vs returned record ID**: after schema validation, the output was structurally valid but had the wrong identity.
- **No semantic check**: the pipeline verified structure but never asked "is this the record we requested?".

### Root cause
Only structural (schema) validation existed. A valid JSON object with `record_id: "USER-202"` was accepted even though `USER-101` was requested.

### Fix
Added a semantic integrity check after schema validation:
- Compare `output.record_id` with the original `request_id`.
- If they differ, raise `DataIntegrityError` with `expected_record_id` and `actual_record_id`.
- This catches cases where the Retriever returns the wrong record but every downstream stage processes it correctly.

---

## Production Tooling (conceptual)

- Structured logs with trace IDs enable end-to-end request tracing.
- Latency and error-rate metrics would surface the timeout in production monitoring.
- Schema registries (e.g., JSON Schema, Protobuf, Pydantic) enforce output contracts at service boundaries.
- Distributed tracing (e.g., OpenTelemetry) links stages across process boundaries.
