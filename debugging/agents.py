import json
import time

from debugging.exceptions import MalformedOutputError
from debugging.models import RECORDS, AnalyzerOutput, calculate_score, calculate_status


def retriever(record_id: str, failure_mode: str = "") -> dict:
    if failure_mode == "wrong_data":
        target = "USER-202"
    else:
        target = record_id
    if target not in RECORDS:
        raise ValueError(f"Unknown record_id: {target}")
    return dict(RECORDS[target])


def analyzer(record: dict, failure_mode: str = "", attempt: int = 1) -> dict:
    if failure_mode == "timeout" and attempt == 1:
        time.sleep(0.15)
        raise TimeoutError("Analyzer timed out")

    score = calculate_score(record)
    status = calculate_status(score)
    return {
        "record_id": record["record_id"],
        "score": score,
        "status": status,
    }


def formatter(analysis: dict, failure_mode: str = "") -> str:
    if failure_mode == "malformed":
        return json.dumps({
            "record_id": analysis["record_id"],
            "score": 200,
            "status": "unknown",
        })
    return json.dumps(analysis)


def validator(raw: str, failure_mode: str = "") -> AnalyzerOutput:
    try:
        parsed = json.loads(raw)
        return AnalyzerOutput(**parsed)
    except (json.JSONDecodeError, ValueError) as exc:
        raise MalformedOutputError(str(exc)) from exc
