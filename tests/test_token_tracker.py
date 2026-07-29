from src.token_tracker import TokenTracker


def test_log_and_totals():
    tt = TokenTracker()
    tt.log("analyzer", 100, 50)
    tt.log("decision", 200, 30)

    assert tt.total_input() == 300
    assert tt.total_output() == 80
    assert tt.total() == 380


def test_by_agent():
    tt = TokenTracker()
    tt.log("analyzer", 100, 50)
    tt.log("decision", 200, 30)
    tt.log("analyzer", 50, 20)

    by_agent = tt.by_agent()
    assert by_agent["analyzer"]["input_tokens"] == 150
    assert by_agent["analyzer"]["output_tokens"] == 70
    assert by_agent["decision"]["input_tokens"] == 200
    assert by_agent["decision"]["output_tokens"] == 30


def test_reset():
    tt = TokenTracker()
    tt.log("analyzer", 100, 50)
    tt.reset()
    assert tt.total_input() == 0
    assert tt.total_output() == 0
    assert tt.calls == []


def test_estimate_tokens():
    text = "Hello world, this is a test sentence."
    estimated = TokenTracker.estimate_tokens(text)
    assert estimated > 0
    # The text has 8 words, so even the fallback should give >= 8
    assert estimated >= 8
