import re


def _tokenize(text: str) -> set:
    """Split text into lowercase tokens with punctuation stripped."""
    return set(re.sub(r"[^a-z0-9\s]", "", text.lower()).split())


def prune_context(
    query: str, documents: list, job_skills: list
) -> tuple:
    """Select only documents relevant to the query and job requirements.

    WHY this reduces tokens: Sending every document (including irrelevant noise)
    to the LLM inflates the input prompt linearly with each added document.
    By filtering to only relevant content before the API call, we directly
    reduce the token count for every analyzer invocation.

    This implementation uses a simple keyword-overlap heuristic so no
    embedding API or external model is required.
    """
    if not documents:
        return [], []

    query_tokens = _tokenize(query)
    skill_tokens = set()
    for skill in job_skills:
        skill_tokens.update(_tokenize(skill))

    relevant = []
    removed = []

    for doc in documents:
        doc_tokens = _tokenize(doc)
        overlap = len(query_tokens & doc_tokens) + len(skill_tokens & doc_tokens)
        if overlap >= 2:
            relevant.append(doc)
        else:
            removed.append(doc)

    return relevant, removed


COMPRESS_FIELDS = frozenset({
    "summary", "matched_skills", "missing_skills", "score", "recommendation",
})


def compress_state(analyzer_output):
    """Extract only the fields needed for the final decision.

    WHY this reduces tokens: The analyzer's full output often includes verbose
    chain-of-thought, detailed assessments, and per-document commentary —
    none of which the decision agent needs. By sending only the compact
    structured state (summary, skills, score, recommendation), we avoid
    passing hundreds of extra tokens to the second LLM call.

    Additionally, in the baseline the decision agent also receives the
    original documents and full conversation history. Compression ensures
    the decision agent sees *only* what it needs.
    """
    return {
        field: analyzer_output.get(field)
        for field in COMPRESS_FIELDS
        if field in analyzer_output
    }
