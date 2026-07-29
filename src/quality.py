def compare(baseline: dict, optimized: dict) -> dict:
    """Deterministic comparison of baseline and optimized outputs.

    All checks are purely structural / rule-based so there is no
    additional LLM call (no judge LLM) and no hidden cost.
    """
    b_analysis = baseline["analysis"]
    o_analysis = optimized["analysis"]
    b_decision = baseline["decision"]
    o_decision = optimized["decision"]

    # 1. Recommendation agreement
    b_rec = b_decision.get("recommendation", "")
    o_rec = o_decision.get("recommendation", "")
    rec_agreement = b_rec == o_rec

    # 2. Score difference
    b_score = b_analysis.get("score", 0)
    o_score = o_analysis.get("score", 0)
    score_diff = abs(b_score - o_score)

    # 3. Matched skills preserved (intersection)
    b_matched = set(b_analysis.get("matched_skills", []))
    o_matched = set(o_analysis.get("matched_skills", []))
    shared_matched = b_matched & o_matched

    # 4. Missing skills preserved (intersection)
    b_missing = set(b_analysis.get("missing_skills", []))
    o_missing = set(o_analysis.get("missing_skills", []))
    shared_missing = b_missing & o_missing

    return {
        "recommendation_agreement": rec_agreement,
        "score_difference": score_diff,
        "baseline_recommendation": b_rec,
        "optimized_recommendation": o_rec,
        "baseline_score": b_score,
        "optimized_score": o_score,
        "shared_matched_skills": sorted(shared_matched),
        "shared_missing_skills": sorted(shared_missing),
        "baseline_matched_skills": sorted(b_matched),
        "optimized_matched_skills": sorted(o_matched),
        "baseline_missing_skills": sorted(b_missing),
        "optimized_missing_skills": sorted(o_missing),
    }
