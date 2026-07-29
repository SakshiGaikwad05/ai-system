import json
import time
import uuid

from debugging.agents import retriever, analyzer, formatter, validator
from debugging.exceptions import (
    DataIntegrityError,
    MalformedOutputError,
    WorkflowError,
    WorkflowTimeoutError,
)
from debugging.observability import logger


ANALYZER_TIMEOUT_S = 0.1
MAX_ANALYZER_ATTEMPTS = 2


def _generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


def _now_ms() -> float:
    return time.time() * 1000


def _run_analyzer_with_retry(
    req_id: str, record: dict, failure_mode: str
) -> dict:
    last_exc = None
    for attempt in range(1, MAX_ANALYZER_ATTEMPTS + 1):
        t0 = _now_ms()
        try:
            result = analyzer(record, failure_mode, attempt)
            logger.log(req_id, "analyzer", "success", _now_ms() - t0, attempt=attempt)
            return result
        except TimeoutError as exc:
            duration = _now_ms() - t0
            logger.log(
                req_id, "analyzer", "timeout", duration,
                attempt=attempt, error_type="TimeoutError",
                error_message=str(exc),
            )
            last_exc = exc

    raise WorkflowTimeoutError(
        f"Analyzer failed after {MAX_ANALYZER_ATTEMPTS} attempts"
    ) from last_exc


def _check_integrity(requested_id: str, output, req_id: str) -> None:
    if output.record_id != requested_id:
        logger.log(
            req_id, "integrity_check", "failed", 0.0,
            error_type="DataIntegrityError",
            error_message=f"Expected {requested_id}, got {output.record_id}",
            expected_record_id=requested_id,
            actual_record_id=output.record_id,
        )
        raise DataIntegrityError(
            f"Expected record {requested_id}, got {output.record_id}",
            expected_record_id=requested_id,
            actual_record_id=output.record_id,
        )


def run_broken(request_id: str, failure_mode: str = "") -> dict:
    req_id = _generate_request_id()

    t0 = _now_ms()
    record = retriever(request_id, failure_mode)
    logger.log(req_id, "retriever", "success", _now_ms() - t0)

    t0 = _now_ms()
    analysis = analyzer(record, failure_mode, attempt=1)
    logger.log(req_id, "analyzer", "success", _now_ms() - t0)

    t0 = _now_ms()
    raw = formatter(analysis, failure_mode)
    logger.log(req_id, "formatter", "success", _now_ms() - t0)

    result = json.loads(raw)
    logger.log(req_id, "result", "success", _now_ms() - t0)

    return result


def run_fixed(request_id: str, failure_mode: str = "") -> dict:
    req_id = _generate_request_id()

    t0 = _now_ms()
    record = retriever(request_id, failure_mode)
    logger.log(req_id, "retriever", "success", _now_ms() - t0)

    analysis = _run_analyzer_with_retry(req_id, record, failure_mode)

    t0 = _now_ms()
    raw = formatter(analysis, failure_mode)
    logger.log(req_id, "formatter", "success", _now_ms() - t0)

    t0 = _now_ms()
    try:
        output = validator(raw, failure_mode)
    except MalformedOutputError:
        logger.log(
            req_id, "validator", "malformed", _now_ms() - t0,
            error_type="MalformedOutputError",
            error_message="Schema validation failed",
        )
        raise
    logger.log(req_id, "validator", "success", _now_ms() - t0)

    _check_integrity(request_id, output, req_id)

    logger.log(req_id, "result", "success", _now_ms() - t0)

    return output.model_dump()
