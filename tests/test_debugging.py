import json

import pytest

from debugging.agents import validator
from debugging.exceptions import (
    DataIntegrityError,
    MalformedOutputError,
)
from debugging.models import RECORDS, AnalyzerOutput, calculate_score
from debugging.observability import logger
from debugging.workflow import (
    _check_integrity,
    _generate_request_id,
    run_broken,
    run_fixed,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def test_generate_request_id():
    ids = {_generate_request_id() for _ in range(100)}
    assert len(ids) == 100
    for rid in ids:
        assert len(rid) == 12


# ---------------------------------------------------------------------------
# Normal workflow
# ---------------------------------------------------------------------------

def test_normal_workflow_succeeds():
    logger.clear()
    result = run_fixed("USER-101")
    assert result["record_id"] == "USER-101"
    assert isinstance(result["score"], int)
    assert result["status"] in ("approved", "review", "rejected")


def test_normal_broken_succeeds():
    logger.clear()
    result = run_broken("USER-101")
    assert result["record_id"] == "USER-101"


def test_logs_carry_same_request_id():
    logger.clear()
    run_fixed("USER-101")
    req_ids = {l.request_id for l in logger.logs}
    assert len(req_ids) == 1


def test_normal_data_passes_integrity():
    logger.clear()
    result = run_fixed("USER-202")
    assert result["record_id"] == "USER-202"


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------

def test_timeout_detected():
    logger.clear()
    with pytest.raises(TimeoutError):
        run_broken("USER-101", "timeout")


def test_timeout_retries_exactly_once():
    logger.clear()
    run_fixed("USER-101", "timeout")
    logs = logger.logs
    analyzer_logs = [l for l in logs if l.stage == "analyzer"]
    assert len(analyzer_logs) == 2
    assert analyzer_logs[0].status == "timeout"
    assert analyzer_logs[1].status == "success"


def test_second_attempt_succeeds():
    logger.clear()
    result = run_fixed("USER-101", "timeout")
    assert result["record_id"] == "USER-101"
    assert result["score"] == calculate_score(RECORDS["USER-101"])


def test_retries_bounded():
    logger.clear()
    result = run_fixed("USER-101", "timeout")
    assert result["record_id"] == "USER-101"
    analyzer_logs = [l for l in logger.logs if l.stage == "analyzer"]
    assert len(analyzer_logs) == 2


# ---------------------------------------------------------------------------
# Malformed output
# ---------------------------------------------------------------------------

def test_malformed_output_rejected():
    logger.clear()
    with pytest.raises(MalformedOutputError):
        run_fixed("USER-101", "malformed")


def test_valid_schema_accepted():
    logger.clear()
    raw = json.dumps({"record_id": "USER-101", "score": 75, "status": "approved"})
    result = validator(raw)
    assert isinstance(result, AnalyzerOutput)


def test_wrong_types_rejected():
    with pytest.raises(MalformedOutputError):
        validator(json.dumps({"record_id": "USER-101", "score": "not-a-number", "status": "approved"}))


def test_empty_record_id_rejected():
    with pytest.raises(MalformedOutputError):
        validator(json.dumps({"record_id": "", "score": 50, "status": "review"}))


def test_out_of_range_score_rejected():
    with pytest.raises(MalformedOutputError):
        validator(json.dumps({"record_id": "USER-101", "score": 999, "status": "approved"}))


def test_invalid_status_rejected():
    with pytest.raises(MalformedOutputError):
        validator(json.dumps({"record_id": "USER-101", "score": 50, "status": "invalid"}))


# ---------------------------------------------------------------------------
# Wrong data / integrity
# ---------------------------------------------------------------------------

def test_wrong_user_id_passes_schema():
    logger.clear()
    raw = json.dumps({"record_id": "USER-202", "score": 45, "status": "rejected"})
    result = validator(raw)
    assert result.record_id == "USER-202"
    assert isinstance(result, AnalyzerOutput)


def test_wrong_user_id_fails_semantic_validation():
    logger.clear()
    output = AnalyzerOutput(record_id="USER-202", score=45, status="rejected")
    with pytest.raises(DataIntegrityError):
        _check_integrity("USER-101", output, _generate_request_id())


def test_dataintegrity_error_contains_ids():
    try:
        output = AnalyzerOutput(record_id="USER-202", score=45, status="rejected")
        _check_integrity("USER-101", output, _generate_request_id())
    except DataIntegrityError as e:
        assert e.expected_record_id == "USER-101"
        assert e.actual_record_id == "USER-202"


def test_broken_wrong_data_silently_succeeds():
    logger.clear()
    result = run_broken("USER-101", "wrong_data")
    assert result["record_id"] == "USER-202"


def test_fixed_wrong_data_raises():
    logger.clear()
    with pytest.raises(DataIntegrityError) as excinfo:
        run_fixed("USER-101", "wrong_data")
    assert excinfo.value.expected_record_id == "USER-101"
    assert excinfo.value.actual_record_id == "USER-202"


# ---------------------------------------------------------------------------
# Validation errors are not retried
# ---------------------------------------------------------------------------

def test_malformed_not_retried():
    logger.clear()
    with pytest.raises(MalformedOutputError):
        run_fixed("USER-101", "malformed")
    analyzer_logs = [l for l in logger.logs if l.stage == "analyzer"]
    assert len(analyzer_logs) == 1


# ---------------------------------------------------------------------------
# All scenarios deterministic / reproducible
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mode", ["timeout", "malformed", "wrong_data"])
def test_all_scenarios_reproducible(mode):
    logger.clear()
    if mode == "timeout":
        with pytest.raises(TimeoutError):
            run_broken("USER-101", mode)
        run_fixed("USER-101", mode)
        logs = [l for l in logger.logs if l.stage == "analyzer"]
        assert logs[0].status == "timeout"
        assert logs[1].status == "success"
    elif mode == "malformed":
        with pytest.raises(MalformedOutputError):
            run_fixed("USER-101", mode)
    elif mode == "wrong_data":
        broken = run_broken("USER-101", mode)
        assert broken["record_id"] == "USER-202"
        with pytest.raises(DataIntegrityError):
            run_fixed("USER-101", mode)
