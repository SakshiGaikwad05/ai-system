from src.agents import analyze_candidate, decide, _parse_json_response, MOCK_ANALYSIS, MOCK_DECISION


def test_analyze_candidate_mock_mode():
    result = analyze_candidate(
        query="test query",
        documents=["doc1", "doc2"],
        client=None,
        model="mock",
    )
    assert result["score"] == 75
    assert result["recommendation"] == "proceed"
    assert "Python" in result["matched_skills"]
    assert "Docker" in result["missing_skills"]


def test_analyze_candidate_empty_docs():
    result = analyze_candidate(
        query="test query",
        documents=[],
        client=None,
        model="mock",
    )
    assert result["score"] == 75


def test_decide_mock_mode():
    result = decide(
        query="test query",
        analysis=MOCK_ANALYSIS,
        client=None,
        model="mock",
        documents=None,
    )
    assert result["recommendation"] == "proceed"


def test_decide_with_documents():
    result = decide(
        query="test query",
        analysis=MOCK_ANALYSIS,
        client=None,
        model="mock",
        documents=["doc1", "doc2"],
        context="extra context",
    )
    assert result["recommendation"] == "proceed"


def test_parse_json_response_plain():
    raw = '{"score": 80, "recommendation": "proceed"}'
    parsed = _parse_json_response(raw)
    assert parsed["score"] == 80
    assert parsed["recommendation"] == "proceed"


def test_parse_json_response_fenced():
    raw = '```json\n{"score": 80, "recommendation": "proceed"}\n```'
    parsed = _parse_json_response(raw)
    assert parsed["score"] == 80
    assert parsed["recommendation"] == "proceed"


def test_parse_json_response_fenced_no_lang():
    raw = '```\n{"score": 75}\n```'
    parsed = _parse_json_response(raw)
    assert parsed["score"] == 75


def test_parse_json_response_empty():
    assert _parse_json_response("") == {}
    assert _parse_json_response("not json") == {}


def test_analyze_candidate_returns_mock():
    result = analyze_candidate(
        query="test",
        documents=[],
        client=None,
        model="mock",
        context="Previous conversation history here",
    )
    assert result == MOCK_ANALYSIS


def test_decide_returns_mock():
    result = decide(
        query="test",
        analysis=MOCK_ANALYSIS,
        client=None,
        model="mock",
    )
    assert result == MOCK_DECISION
