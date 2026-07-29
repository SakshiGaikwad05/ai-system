from src.quality import compare


def test_recommendation_agreement():
    baseline = {
        "analysis": {"score": 75, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "proceed"},
    }
    optimized = {
        "analysis": {"score": 72, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "proceed"},
    }
    result = compare(baseline, optimized)
    assert result["recommendation_agreement"] is True


def test_recommendation_disagreement():
    baseline = {
        "analysis": {"score": 40, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "reject"},
    }
    optimized = {
        "analysis": {"score": 70, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "proceed"},
    }
    result = compare(baseline, optimized)
    assert result["recommendation_agreement"] is False


def test_score_difference():
    baseline = {
        "analysis": {"score": 80, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "proceed"},
    }
    optimized = {
        "analysis": {"score": 75, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "proceed"},
    }
    result = compare(baseline, optimized)
    assert result["score_difference"] == 5


def test_skills_preserved():
    baseline = {
        "analysis": {
            "score": 70,
            "matched_skills": ["Python", "Django", "SQL"],
            "missing_skills": ["Docker", "AWS"],
        },
        "decision": {"recommendation": "proceed"},
    }
    optimized = {
        "analysis": {
            "score": 68,
            "matched_skills": ["Python", "Django"],
            "missing_skills": ["Docker"],
        },
        "decision": {"recommendation": "proceed"},
    }
    result = compare(baseline, optimized)

    assert "Python" in result["shared_matched_skills"]
    assert "Django" in result["shared_matched_skills"]
    assert "Docker" in result["shared_missing_skills"]


def test_empty_skills():
    baseline = {
        "analysis": {"score": 0, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "reject"},
    }
    optimized = {
        "analysis": {"score": 0, "matched_skills": [], "missing_skills": []},
        "decision": {"recommendation": "reject"},
    }
    result = compare(baseline, optimized)

    assert result["recommendation_agreement"] is True
    assert result["score_difference"] == 0
    assert result["shared_matched_skills"] == []
    assert result["shared_missing_skills"] == []
