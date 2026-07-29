#!/usr/bin/env python3

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

from src.agents import tracker
from src.pipeline import run_baseline, run_optimized
from src.quality import compare


BENCHMARKS_FILE = "benchmarks/results.json"


def _validate_nvidia_env():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("ERROR: NVIDIA_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    base_url = os.getenv("NVIDIA_BASE_URL")
    if not base_url:
        print("ERROR: NVIDIA_BASE_URL is not set.", file=sys.stderr)
        sys.exit(1)

    model = os.getenv("NVIDIA_MODEL")
    if not model:
        print("ERROR: NVIDIA_MODEL is not set.", file=sys.stderr)
        sys.exit(1)

    return api_key, base_url, model


def _print_separator(title: str) -> None:
    width = 50
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def _print_token_line(label: str, input_tok: int, output_tok: int) -> None:
    print(f"  {label}: locally estimated input={input_tok}  output={output_tok}  total={input_tok + output_tok}")


def _save_benchmark(results: dict) -> str:
    os.makedirs("benchmarks", exist_ok=True)

    existing = []
    if os.path.exists(BENCHMARKS_FILE):
        with open(BENCHMARKS_FILE) as f:
            try:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = [existing]
            except (json.JSONDecodeError, ValueError):
                existing = []

    existing.append(results)

    with open(BENCHMARKS_FILE, "w") as f:
        json.dump(existing, f, indent=2)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bench_path = os.path.join("benchmarks", f"benchmark_{ts}.json")
    with open(bench_path, "w") as f:
        json.dump(results, f, indent=2)

    return bench_path


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Cost Optimization Benchmark")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real LLM API (requires NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL in .env)",
    )
    args = parser.parse_args()

    client = None
    model = "mock"

    if args.live:
        load_dotenv()
        api_key, base_url, model = _validate_nvidia_env()
        client = OpenAI(api_key=api_key, base_url=base_url)
        print("Running in LIVE mode (real LLM calls)")
    else:
        print("Running in deterministic mode (no API calls). Pass --live for real LLM inference.")

    _print_separator("BASELINE")
    tracker.reset()
    baseline = run_baseline(client, model)
    b_agent = tracker.by_agent()
    b_total_in = tracker.total_input()
    b_total_out = tracker.total_output()

    _print_token_line("Analyzer", b_agent.get("analyzer", {}).get("input_tokens", 0),
                      b_agent.get("analyzer", {}).get("output_tokens", 0))
    _print_token_line("Decision", b_agent.get("decision", {}).get("input_tokens", 0),
                      b_agent.get("decision", {}).get("output_tokens", 0))
    _print_token_line("Total", b_total_in, b_total_out)
    print(f"  Execution time: {baseline['time']:.2f}s")

    _print_separator("OPTIMIZED")
    tracker.reset()
    optimized = run_optimized(client, model)
    o_agent = tracker.by_agent()
    o_total_in = tracker.total_input()
    o_total_out = tracker.total_output()

    print(f"  Documents: {optimized['total_documents']} -> {optimized['relevant_count']}")
    _print_token_line("Analyzer", o_agent.get("analyzer", {}).get("input_tokens", 0),
                      o_agent.get("analyzer", {}).get("output_tokens", 0))
    _print_token_line("Decision", o_agent.get("decision", {}).get("input_tokens", 0),
                      o_agent.get("decision", {}).get("output_tokens", 0))
    _print_token_line("Total", o_total_in, o_total_out)
    print(f"  Execution time: {optimized['time']:.2f}s")

    _print_separator("COMPARISON")
    savings = b_total_in - o_total_in
    reduction_pct = (savings / b_total_in * 100) if b_total_in > 0 else 0.0

    print("  Locally estimated input tokens")
    print(f"    Baseline:  {b_total_in}")
    print(f"    Optimized: {o_total_in}")
    print(f"    Saved:     {savings}")
    print(f"    Reduction: {reduction_pct:.1f}%")

    quality = compare(baseline, optimized)
    print(f"\n  Quality:")
    print(f"    Recommendation agreement: {quality['recommendation_agreement']}")
    print(f"    Score difference:         {quality['score_difference']}")
    print(f"    Shared matched skills:    {quality['shared_matched_skills']}")
    print(f"    Shared missing skills:    {quality['shared_missing_skills']}")

    _print_separator("OPTIMIZATION TRADEOFFS")
    print("  Context pruning:")
    print("    Risk: relevant context may be removed if relevance selection is too aggressive.")
    print("    Mitigation: preserve requirement-related documents/facts and validate important facts.")
    print("  Structured state compression:")
    print("    Risk: nuanced upstream information may be lost.")
    print("    Mitigation: explicitly preserve fields required by downstream decisions.")

    projected_optimized = round(100000 * (1 - reduction_pct / 100))
    projected_saving = 100000 - projected_optimized

    _print_separator("100K TOKEN PROJECTION")
    print(f"  Production baseline: 100,000 input tokens/query")
    print(f"  Projected optimized: {projected_optimized} input tokens/query")
    print(f"  Projected saving:    {projected_saving} input tokens/query")
    print(f"  (Projection based on measured benchmark reduction — not an actual 100K-token API run.)")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "live": args.live,
        "baseline": {
            "total_input_tokens": b_total_in,
            "total_output_tokens": b_total_out,
            "execution_time_s": baseline["time"],
            "documents_count": baseline["total_documents"],
            "by_agent": b_agent,
        },
        "optimized": {
            "total_input_tokens": o_total_in,
            "total_output_tokens": o_total_out,
            "execution_time_s": optimized["time"],
            "total_documents": optimized["total_documents"],
            "relevant_documents": optimized["relevant_count"],
            "removed_documents": optimized["removed_count"],
            "by_agent": o_agent,
        },
        "comparison": {
            "tokens_saved": savings,
            "reduction_percent": round(reduction_pct, 1),
            "quality": quality,
        },
        "optimization_tradeoffs": {
            "context_pruning": {
                "risk": "relevant context may be removed if relevance selection is too aggressive",
                "mitigation": "preserve requirement-related documents/facts and validate important facts",
            },
            "structured_state_compression": {
                "risk": "nuanced upstream information may be lost",
                "mitigation": "explicitly preserve fields required by downstream decisions",
            },
        },
        "projection_100k": {
            "baseline_tokens": 100000,
            "projected_optimized_tokens": projected_optimized,
            "projected_saving": projected_saving,
            "reduction_percent": round(reduction_pct, 1),
            "note": "Projection based on measured benchmark reduction — not an actual 100K-token API run",
        },
    }

    bench_path = _save_benchmark(results)
    print(f"\n  Benchmark saved to {bench_path}")
    print(f"  Benchmark results appended to {BENCHMARKS_FILE}")


if __name__ == "__main__":
    main()
