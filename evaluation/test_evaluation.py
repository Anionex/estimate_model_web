"""
Unit tests for the evaluation framework.
Tests module imports, data models, prompt construction, and ranking aggregation.
Does NOT require an OpenAI API key — no LLM calls.
"""

import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluation.schemas import (
    EvalInput,
    DimensionScore,
    EvalResult,
    PairwiseResult,
    ABTestResult,
    DEFAULT_DIMENSIONS,
    DIMENSION_DESCRIPTIONS,
)
from evaluation.prompts import (
    build_scoring_prompts,
    build_comparison_prompts,
    build_dimension_rubric,
)
from evaluation.comparator import ItineraryComparator
from dataclasses import asdict


def test_schemas():
    inp = EvalInput(id="test", user_request="Plan a trip", itinerary="Day 1: ...", metadata={"model": "gpt"})
    assert inp.id == "test"
    assert inp.metadata == {"model": "gpt"}

    score = DimensionScore(dimension="feasibility", score=8, justification="Good pacing")
    assert score.score == 8

    result = EvalResult(input_id="test", scores=[score], aggregate_score=8.0)
    d = asdict(result)
    assert d["input_id"] == "test"
    assert len(d["scores"]) == 1

    pr = PairwiseResult(itinerary_a_id="a", itinerary_b_id="b", dimension="feasibility", winner="A", justification="A is better")
    assert pr.winner == "A"

    ab = ABTestResult(pairwise_results=[pr], rankings={"feasibility": ["a", "b"]}, overall_ranking=["a", "b"])
    d = asdict(ab)
    assert json.dumps(d)  # must be JSON-serializable

    print("[PASS] test_schemas")


def test_default_dimensions():
    assert len(DEFAULT_DIMENSIONS) == 6
    for dim in DEFAULT_DIMENSIONS:
        assert dim in DIMENSION_DESCRIPTIONS
        assert len(DIMENSION_DESCRIPTIONS[dim]) > 20
    print("[PASS] test_default_dimensions")


def test_build_scoring_prompts():
    sys_prompt, user_prompt, output_format = build_scoring_prompts(
        user_request="Plan a 3-day trip to Tokyo",
        itinerary="Day 1: Visit Shibuya\nDay 2: Visit Asakusa\nDay 3: Visit Akihabara",
        dimensions=["feasibility", "detail_level"],
    )
    assert "expert travel itinerary evaluator" in sys_prompt
    assert "feasibility" in sys_prompt
    assert "detail_level" in sys_prompt
    assert "Tokyo" in user_prompt
    assert "Shibuya" in user_prompt
    assert "score" in output_format
    print("[PASS] test_build_scoring_prompts")


def test_build_comparison_prompts():
    sys_prompt, user_prompt, output_format = build_comparison_prompts(
        user_request="Plan a trip",
        itinerary_a="Day 1: Plan A content",
        itinerary_b="Day 1: Plan B content",
        dimensions=["route_rationality"],
    )
    assert "pairwise comparison" in sys_prompt
    assert "Itinerary A" in user_prompt
    assert "Itinerary B" in user_prompt
    assert "Plan A content" in user_prompt
    assert "Plan B content" in user_prompt
    assert "winner" in output_format
    print("[PASS] test_build_comparison_prompts")


def test_aggregate_rankings():
    # Simulate: 3 itineraries, 2 dimensions, round-robin results
    pairwise_results = [
        # dim: feasibility — A beats B, A beats C, B beats C
        PairwiseResult("a", "b", "feasibility", "A", "A is better"),
        PairwiseResult("a", "c", "feasibility", "A", "A is better"),
        PairwiseResult("b", "c", "feasibility", "A", "B is better"),
        # dim: detail_level — C beats A, C beats B, tie A vs B
        PairwiseResult("a", "c", "detail_level", "B", "C is better"),
        PairwiseResult("b", "c", "detail_level", "B", "C is better"),
        PairwiseResult("a", "b", "detail_level", "tie", "Equal"),
    ]

    rankings, overall = ItineraryComparator.aggregate_rankings(
        pairwise_results,
        itinerary_ids=["a", "b", "c"],
        dimensions=["feasibility", "detail_level"],
    )

    # Feasibility: a=2wins, b=1win, c=0 → [a, b, c]
    assert rankings["feasibility"][0] == "a"
    assert rankings["feasibility"][1] == "b"
    assert rankings["feasibility"][2] == "c"

    # Detail_level: c=2wins, a=0, b=0 → [c, ...]
    assert rankings["detail_level"][0] == "c"

    # Overall: a=2, c=2, b=1 → a and c tie, b last
    # (a and c both have 2 wins total)
    assert overall[2] == "b"
    assert set(overall[:2]) == {"a", "c"}

    print("[PASS] test_aggregate_rankings")


def test_dimension_rubric():
    rubric = build_dimension_rubric(["feasibility", "detail_level"])
    assert "feasibility" in rubric
    assert "detail_level" in rubric
    assert "1 =" in rubric
    assert "10 =" in rubric

    # Custom unknown dimension
    rubric2 = build_dimension_rubric(["my_custom_dim"])
    assert "my_custom_dim" in rubric2
    print("[PASS] test_dimension_rubric")


def test_cli_dimensions(capsys=None):
    from evaluation.cli import cmd_dimensions
    import argparse
    args = argparse.Namespace(json=True)
    # Just test it doesn't crash
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_dimensions(args)
    output = buf.getvalue()
    data = json.loads(output)
    assert len(data) == 6
    assert all("name" in d and "description" in d for d in data)
    print("[PASS] test_cli_dimensions")


def test_eval_result_serialization():
    """Ensure full evaluation results are JSON-serializable (needed for API responses)."""
    result = EvalResult(
        input_id="gpt-4o",
        scores=[
            DimensionScore("feasibility", 8, "Good"),
            DimensionScore("detail_level", 6, "Moderate"),
        ],
        aggregate_score=7.0,
    )
    d = asdict(result)
    s = json.dumps(d, ensure_ascii=False)
    parsed = json.loads(s)
    assert parsed["input_id"] == "gpt-4o"
    assert len(parsed["scores"]) == 2
    print("[PASS] test_eval_result_serialization")


if __name__ == "__main__":
    test_schemas()
    test_default_dimensions()
    test_build_scoring_prompts()
    test_build_comparison_prompts()
    test_aggregate_rankings()
    test_dimension_rubric()
    test_cli_dimensions()
    test_eval_result_serialization()
    print("\n===== All tests passed =====")
