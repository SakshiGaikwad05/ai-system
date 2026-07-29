import time
from typing import Optional

from openai import OpenAI

from src.agents import analyze_candidate, decide
from src.data import generate_dataset
from src.optimizer import prune_context, compress_state

BASELINE_CONTEXT = (
    "Previous conversation:\n"
    "User: I need a junior Python backend developer for my team.\n"
    "AI: I can help evaluate candidates against your requirements.\n"
    "User: Please evaluate Alex Chen for the position.\n"
    "AI: I will analyze the candidate's profile and provide a recommendation."
)


def run_baseline(client: Optional[OpenAI], model: str) -> dict:
    """Run the pipeline in baseline (inefficient) mode.

    Both the analyzer and decision agent receive:
    - ALL documents (relevant + irrelevant)
    - Full conversation history
    The decision agent also receives the complete analyzer output *and*
    all original documents again — demonstrating repeated context passing.
    """
    data = generate_dataset()
    query = data["query"]
    all_docs = data["all_documents"]

    t0 = time.time()

    # Analyzer gets everything: query + all docs + full context
    analysis = analyze_candidate(
        query=query,
        documents=all_docs,
        client=client,
        model=model,
        context=BASELINE_CONTEXT,
    )

    # Decision agent gets everything again: query + all docs + full context + full analysis
    decision_result = decide(
        query=query,
        analysis=analysis,
        client=client,
        model=model,
        documents=all_docs,
        context=BASELINE_CONTEXT,
    )

    elapsed = time.time() - t0

    return {
        "analysis": analysis,
        "decision": decision_result,
        "time": elapsed,
        "total_documents": len(all_docs),
    }


def run_optimized(client: Optional[OpenAI], model: str) -> dict:
    """Run the pipeline with both optimisations enabled.

    Optimization #1 — Context Pruning:
        Irrelevant documents are removed before the analyzer call.
    Optimization #2 — Structured State Compression:
        The analyzer outputs a compact structured state that omits verbose
        reasoning, per-document commentary, and conversation history. The
        decision agent receives *only* this compressed state.
    """
    data = generate_dataset()
    query = data["query"]
    all_docs = data["all_documents"]
    job_skills = data["job"]["required_skills"]

    total_docs = len(all_docs)

    t0 = time.time()

    # ── Optimization #1: prune irrelevant documents ──────────────────────
    relevant_docs, removed_docs = prune_context(query, all_docs, job_skills)

    # Analyzer receives only the relevant documents (no extraneous context)
    analysis = analyze_candidate(
        query=query,
        documents=relevant_docs,
        client=client,
        model=model,
        context="",  # no wasteful conversation history
    )

    # ── Optimization #2: compress the analyzer output ────────────────────
    compressed = compress_state(analysis)

    # Decision receives ONLY the compressed state — no original documents,
    # no conversation history, no verbose analyzer reasoning.
    decision_result = decide(
        query=query,
        analysis=compressed,
        client=client,
        model=model,
        documents=None,
        context="",
    )

    elapsed = time.time() - t0

    return {
        "analysis": analysis,
        "decision": decision_result,
        "compressed": compressed,
        "time": elapsed,
        "total_documents": total_docs,
        "relevant_count": len(relevant_docs),
        "removed_count": len(removed_docs),
    }
