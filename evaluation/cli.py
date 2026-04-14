"""
Evaluation framework CLI.

Usage:
    python -m evaluation.cli score --config eval_input.json
    python -m evaluation.cli compare --config eval_input.json
    python -m evaluation.cli dimensions

    Add --json for machine-readable JSON output.
"""

import argparse
import json
import sys
import os
from dataclasses import asdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dotenv
dotenv.load_dotenv()

from evaluation.schemas import (
    EvalInput,
    DEFAULT_DIMENSIONS,
    DIMENSION_DESCRIPTIONS,
)
from evaluation.scorer import ItineraryScorer
from evaluation.comparator import ItineraryComparator


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_itineraries(config: dict) -> list[EvalInput]:
    items = []
    for entry in config["itineraries"]:
        itinerary_text = entry.get("itinerary", "")
        if not itinerary_text and "file" in entry:
            with open(entry["file"], "r", encoding="utf-8") as f:
                itinerary_text = f.read()
        items.append(
            EvalInput(
                id=entry["id"],
                user_request=config.get("user_request", entry.get("user_request", "")),
                itinerary=itinerary_text,
                metadata=entry.get("metadata", {}),
            )
        )
    return items


def cmd_score(args):
    config = load_config(args.config)
    dimensions = config.get("dimensions", DEFAULT_DIMENSIONS)
    inputs = load_itineraries(config)

    scorer = ItineraryScorer(dimensions=dimensions)
    results = scorer.score_batch(inputs)

    if args.json:
        print(json.dumps([asdict(r) for r in results], indent=2, ensure_ascii=False))
        return

    for result in results:
        print(f"\n{'='*60}")
        print(f"  Itinerary: {result.input_id}")
        print(f"  Aggregate Score: {result.aggregate_score}/10")
        print(f"{'='*60}")
        for s in result.scores:
            print(f"  [{s.score:>2}/10] {s.dimension}")
            print(f"         {s.justification}")
        print()


def cmd_compare(args):
    config = load_config(args.config)
    dimensions = config.get("dimensions", DEFAULT_DIMENSIONS)
    user_request = config["user_request"]
    inputs = load_itineraries(config)

    comparator = ItineraryComparator(dimensions=dimensions)
    result = comparator.compare_all(user_request, inputs, dimensions)

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return

    print(f"\n{'='*60}")
    print(f"  Overall Ranking: {' > '.join(result.overall_ranking)}")
    print(f"{'='*60}")

    print("\n  Per-Dimension Rankings:")
    for dim, ranking in result.rankings.items():
        print(f"    {dim}: {' > '.join(ranking)}")

    print(f"\n  Pairwise Details:")
    for pr in result.pairwise_results:
        winner_display = pr.winner if pr.winner == "tie" else (
            pr.itinerary_a_id if pr.winner == "A" else pr.itinerary_b_id
        )
        print(f"    [{pr.dimension}] {pr.itinerary_a_id} vs {pr.itinerary_b_id} -> {winner_display}")
        print(f"      {pr.justification}")
    print()


def cmd_dimensions(args):
    if args.json:
        dims = [{"name": k, "description": v} for k, v in DIMENSION_DESCRIPTIONS.items()]
        print(json.dumps(dims, indent=2, ensure_ascii=False))
        return

    print("\nAvailable evaluation dimensions:\n")
    for name, desc in DIMENSION_DESCRIPTIONS.items():
        print(f"  {name}")
        print(f"    {desc}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="evaluation",
        description="Travel itinerary evaluation framework",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score", help="Score itineraries on multiple dimensions")
    score_parser.add_argument("--config", required=True, help="Path to JSON config file")
    score_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    compare_parser = subparsers.add_parser("compare", help="Pairwise A/B comparison of itineraries")
    compare_parser.add_argument("--config", required=True, help="Path to JSON config file")
    compare_parser.add_argument("--json", action="store_true", help="Output results as JSON")

    dims_parser = subparsers.add_parser("dimensions", help="List available evaluation dimensions")
    dims_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "score":
        cmd_score(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "dimensions":
        cmd_dimensions(args)


if __name__ == "__main__":
    main()
