import sys
import os
import random
from collections import defaultdict
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.jsonify_chat_model import get_json_response
from evaluation.schemas import (
    EvalInput,
    PairwiseResult,
    ABTestResult,
    DEFAULT_DIMENSIONS,
)
from evaluation.prompts import build_comparison_prompts


class ItineraryComparator:
    def __init__(self, dimensions: list[str] | None = None):
        self.dimensions = dimensions or DEFAULT_DIMENSIONS

    def compare_pair(
        self,
        user_request: str,
        a: EvalInput,
        b: EvalInput,
        dimensions: list[str] | None = None,
    ) -> list[PairwiseResult]:
        dims = dimensions or self.dimensions

        # Randomize position to mitigate position bias
        if random.random() < 0.5:
            first, second = a, b
            swapped = False
        else:
            first, second = b, a
            swapped = True

        system_prompt, user_prompt, output_format = build_comparison_prompts(
            user_request=user_request,
            itinerary_a=first.itinerary,
            itinerary_b=second.itinerary,
            dimensions=dims,
        )

        raw = get_json_response(system_prompt, user_prompt, output_format)

        results = []
        for entry in raw.get("comparisons", []):
            winner_label = entry.get("winner", "tie").upper()

            # Map back to original A/B labels (undo randomization)
            if winner_label == "TIE":
                winner = "tie"
            elif winner_label == "A":
                winner = "A" if not swapped else "B"
            elif winner_label == "B":
                winner = "B" if not swapped else "A"
            else:
                winner = "tie"

            results.append(
                PairwiseResult(
                    itinerary_a_id=a.id,
                    itinerary_b_id=b.id,
                    dimension=entry["dimension"],
                    winner=winner,
                    justification=entry.get("justification", ""),
                )
            )

        return results

    def compare_all(
        self,
        user_request: str,
        itineraries: list[EvalInput],
        dimensions: list[str] | None = None,
    ) -> ABTestResult:
        dims = dimensions or self.dimensions
        all_pairwise: list[PairwiseResult] = []

        for a, b in combinations(itineraries, 2):
            pair_results = self.compare_pair(user_request, a, b, dims)
            all_pairwise.extend(pair_results)

        id_list = [it.id for it in itineraries]
        rankings, overall = self.aggregate_rankings(all_pairwise, id_list, dims)

        return ABTestResult(
            pairwise_results=all_pairwise,
            rankings=rankings,
            overall_ranking=overall,
        )

    @staticmethod
    def aggregate_rankings(
        pairwise_results: list[PairwiseResult],
        itinerary_ids: list[str],
        dimensions: list[str],
    ) -> tuple[dict[str, list[str]], list[str]]:
        # Per-dimension win counts
        dim_wins: dict[str, dict[str, int]] = {
            dim: defaultdict(int) for dim in dimensions
        }
        overall_wins: dict[str, int] = defaultdict(int)

        for pr in pairwise_results:
            if pr.winner == "tie":
                continue
            # winner is "A" or "B" — map to actual ID
            winner_id = pr.itinerary_a_id if pr.winner == "A" else pr.itinerary_b_id
            dim_wins[pr.dimension][winner_id] += 1
            overall_wins[winner_id] += 1

        # Build per-dimension rankings sorted by wins desc
        rankings: dict[str, list[str]] = {}
        for dim in dimensions:
            rankings[dim] = sorted(
                itinerary_ids,
                key=lambda x: dim_wins[dim].get(x, 0),
                reverse=True,
            )

        overall_ranking = sorted(
            itinerary_ids,
            key=lambda x: overall_wins.get(x, 0),
            reverse=True,
        )

        return rankings, overall_ranking
