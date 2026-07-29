from src.pipeline import run_baseline, run_optimized


def test_run_baseline_mock():
    result = run_baseline(client=None, model="mock")
    assert "analysis" in result
    assert "decision" in result
    assert "time" in result
    assert "total_documents" in result
    assert result["analysis"]["recommendation"] == "proceed"
    assert result["decision"]["recommendation"] == "proceed"
    assert result["total_documents"] > 0


def test_run_optimized_mock():
    result = run_optimized(client=None, model="mock")
    assert "analysis" in result
    assert "decision" in result
    assert "compressed" in result
    assert "time" in result
    assert "total_documents" in result
    assert "relevant_count" in result
    assert "removed_count" in result
    assert result["analysis"]["recommendation"] == "proceed"
    assert result["decision"]["recommendation"] == "proceed"


def test_optimized_removes_documents():
    baseline = run_baseline(client=None, model="mock")
    optimized = run_optimized(client=None, model="mock")

    assert optimized["total_documents"] == baseline["total_documents"]
    assert optimized["relevant_count"] < optimized["total_documents"]
    assert optimized["removed_count"] > 0


def test_baseline_time_is_positive():
    result = run_baseline(client=None, model="mock")
    assert result["time"] >= 0


def test_optimized_time_is_positive():
    result = run_optimized(client=None, model="mock")
    assert result["time"] >= 0


def test_baseline_decision_consistent():
    r1 = run_baseline(client=None, model="mock")
    r2 = run_baseline(client=None, model="mock")
    assert r1["analysis"]["score"] == r2["analysis"]["score"]
    assert r1["decision"]["recommendation"] == r2["decision"]["recommendation"]


def test_optimized_decision_consistent():
    r1 = run_optimized(client=None, model="mock")
    r2 = run_optimized(client=None, model="mock")
    assert r1["analysis"]["score"] == r2["analysis"]["score"]
    assert r1["decision"]["recommendation"] == r2["decision"]["recommendation"]
