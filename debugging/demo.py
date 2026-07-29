import sys
import traceback

from debugging.exceptions import (
    DataIntegrityError,
    MalformedOutputError,
    WorkflowError,
    WorkflowTimeoutError,
)
from debugging.observability import logger
from debugging.workflow import run_broken, run_fixed


SEP = "=" * 58


def _show_trace(request_id: str) -> None:
    logs = logger.by_request(request_id)
    for entry in logs:
        parts = [f"  {entry.stage} {entry.status}"]
        if entry.attempt and entry.attempt > 1:
            parts[0] += f" (attempt={entry.attempt})"
        if entry.error_type:
            parts.append(f" error={entry.error_type}")
        print("".join(parts))


def _run_scenario(label: str, request_id: str, failure_mode: str,
                  expect_broken_fail: bool = True) -> None:
    print(f"\n{SEP}")
    print(f"  {label}")
    print(SEP)

    logger.clear()

    print("\n  BROKEN")
    try:
        result = run_broken(request_id, failure_mode)
        print(f"  Symptom: Pipeline reported success with result:")
        print(f"    {result}")
        if not expect_broken_fail:
            print("  (Expected for normal flow)")

        if failure_mode == "wrong_data":
            print(f"  Root cause: No semantic integrity check — wrong record passed silently.")
        elif failure_mode == "malformed":
            print(f"  Root cause: No output contract validation — malformed data flowed through.")
        elif failure_mode == "timeout":
            print(f"  Root cause: No resilience for transient Analyzer timeout.")
    except Exception as e:
        print(f"  Symptom: {e}")
        print(f"  Trace:")
        _show_trace(logger.logs[-1].request_id if logger.logs else "?")
        if failure_mode == "timeout":
            print(f"  Root cause: No resilience for transient Analyzer timeout.")
        elif failure_mode == "malformed":
            print(f"  Root cause: No output contract validation.")
        elif failure_mode == "wrong_data":
            print(f"  Root cause: No semantic integrity check.")

    logger.clear()
    print("\n  FIXED")
    try:
        result = run_fixed(request_id, failure_mode)
        print("  Trace:")
        _show_trace(logger.logs[-1].request_id if logger.logs else "?")
        if failure_mode == "timeout":
            print(f"  Fix: Explicit timeout + bounded retry for transient timeout only.")
            print(f"  Result: PASS")
        elif failure_mode:
            print(f"  Unexpected success — fix may be missing.")
        else:
            print(f"  Result: PASS")
    except WorkflowTimeoutError as e:
        print(f"  Trace:")
        _show_trace(logger.logs[-1].request_id if logger.logs else "?")
        print(f"  Fix: Explicit timeout + bounded retry for transient timeout only.")
        print(f"  Both attempts failed — {e}")
        print(f"  Result: FAIL (all retries exhausted)")
    except MalformedOutputError as e:
        print(f"  Trace:")
        _show_trace(logger.logs[-1].request_id if logger.logs else "?")
        print(f"  Fix: Schema validation catches malformed result at Formatter boundary.")
        print(f"  Validator raised: {e}")
        print(f"  Result: PASS")
    except DataIntegrityError as e:
        print(f"  Trace:")
        _show_trace(logger.logs[-1].request_id if logger.logs else "?")
        print(f"  Fix: Semantic identity check after schema validation.")
        print(f"  Expected {e.expected_record_id}, Actual {e.actual_record_id}")
        print(f"  DataIntegrityError raised.")
        print(f"  Result: PASS")


def run_normal() -> None:
    _run_scenario("NORMAL", "USER-101", "", expect_broken_fail=False)


def run_timeout() -> None:
    _run_scenario("TIMEOUT", "USER-101", "timeout")


def run_malformed() -> None:
    _run_scenario("MALFORMED OUTPUT", "USER-101", "malformed")


def run_wrong_data() -> None:
    _run_scenario("SILENT WRONG DATA", "USER-101", "wrong_data")


def run_all() -> None:
    run_normal()
    run_timeout()
    run_malformed()
    run_wrong_data()


if __name__ == "__main__":
    cmds = {
        "normal": run_normal,
        "timeout": run_timeout,
        "malformed": run_malformed,
        "wrong-data": run_wrong_data,
        "all": run_all,
    }
    arg = sys.argv[1] if len(sys.argv) > 1 else "usage"
    if arg == "usage":
        print("Usage: python3 -m debugging.demo <scenario>")
        print(f"Scenarios: {', '.join(cmds)}")
    elif arg in cmds:
        cmds[arg]()
    else:
        print(f"Unknown scenario: {arg}")
        print(f"Available: {', '.join(cmds)}")
