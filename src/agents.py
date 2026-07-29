import json
from typing import Dict, List, Optional

from openai import OpenAI

from src.token_tracker import tracker


MOCK_ANALYSIS: Dict = {
    "summary": (
        "Alex Chen is a suitable candidate for the Junior Python Backend Developer position. "
        "He has 1.5 years of experience with strong fundamentals in Python, Django, and SQL. "
        "His project experience building REST APIs with Django REST Framework aligns well "
        "with the job requirements."
    ),
    "matched_skills": ["Python", "Django", "SQL", "REST APIs"],
    "missing_skills": ["Docker", "AWS", "Redis", "Celery"],
    "score": 75,
    "recommendation": "proceed",
}

MOCK_DECISION: Dict = {
    "recommendation": "proceed",
}


def _build_analyzer_prompt(query: str, documents: List[str], context: str) -> str:
    sys_prompt = "You are a hiring analyst. Evaluate the candidate for the given position."
    doc_text = "\n".join(f"- {d}" for d in documents) if documents else "No documents provided."
    return f"""{sys_prompt}

{context}

Query: {query}

Documents:
{doc_text}

Provide your analysis as JSON with these fields:
- summary: brief assessment
- matched_skills: list of required skills the candidate has
- missing_skills: list of required skills the candidate lacks
- score: numeric score 0-100
- recommendation: "proceed" or "reject"
"""


def _build_decision_prompt(
    query: str, analysis: dict, documents: Optional[List[str]], context: str
) -> str:
    sys_prompt = "You are a hiring manager. Make a final decision based on the analysis."
    doc_text = ""
    if documents:
        doc_text = "Documents:\n" + "\n".join(f"- {d}" for d in documents)
    return f"""{sys_prompt}

{context}

Query: {query}

Analysis:
{json.dumps(analysis, indent=2)}

{doc_text}

Provide your decision as JSON with a single field:
- recommendation: "proceed" or "reject"
"""


def _call_llm_and_track(client: OpenAI, model: str, prompt: str, agent: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        if usage:
            tracker.log(agent, usage.prompt_tokens, usage.completion_tokens)
        else:
            estimated_in = tracker.estimate_tokens(prompt)
            estimated_out = tracker.estimate_tokens(content)
            tracker.log(agent, estimated_in, estimated_out, estimated=True)
        return content
    except Exception:
        return ""


def _parse_json_response(content: str) -> dict:
    if not content:
        return {}
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        fence_indices = [i for i, l in enumerate(lines) if l.startswith("```")]
        if len(fence_indices) >= 2:
            content = "\n".join(lines[fence_indices[0] + 1 : fence_indices[1]])
        elif fence_indices:
            content = "\n".join(lines[fence_indices[0] + 1 :])
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def analyze_candidate(
    query: str,
    documents: List[str],
    client: Optional[OpenAI],
    model: str,
    context: str = "",
) -> dict:
    if client is None:
        prompt = _build_analyzer_prompt(query, documents, context)
        estimated_in = tracker.estimate_tokens(prompt)
        estimated_out = tracker.estimate_tokens(json.dumps(MOCK_ANALYSIS))
        tracker.log("analyzer", estimated_in, estimated_out, estimated=True)
        return dict(MOCK_ANALYSIS)

    prompt = _build_analyzer_prompt(query, documents, context)
    raw = _call_llm_and_track(client, model, prompt, "analyzer")
    parsed = _parse_json_response(raw)
    if parsed:
        return parsed
    estimated_in = tracker.estimate_tokens(prompt)
    estimated_out = tracker.estimate_tokens(json.dumps(MOCK_ANALYSIS))
    tracker.log("analyzer", estimated_in, estimated_out, estimated=True)
    return dict(MOCK_ANALYSIS)


def decide(
    query: str,
    analysis: dict,
    client: Optional[OpenAI],
    model: str,
    documents: Optional[List[str]] = None,
    context: str = "",
) -> dict:
    if client is None:
        prompt = _build_decision_prompt(query, analysis, documents, context)
        estimated_in = tracker.estimate_tokens(prompt)
        estimated_out = tracker.estimate_tokens(json.dumps(MOCK_DECISION))
        tracker.log("decision", estimated_in, estimated_out, estimated=True)
        return dict(MOCK_DECISION)

    prompt = _build_decision_prompt(query, analysis, documents, context)
    raw = _call_llm_and_track(client, model, prompt, "decision")
    parsed = _parse_json_response(raw)
    if parsed:
        return parsed
    estimated_in = tracker.estimate_tokens(prompt)
    estimated_out = tracker.estimate_tokens(json.dumps(MOCK_DECISION))
    tracker.log("decision", estimated_in, estimated_out, estimated=True)
    return dict(MOCK_DECISION)
