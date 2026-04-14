import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.jsonify_chat_model import get_json_response
from evaluation.schemas import (
    EvalInput,
    DimensionScore,
    EvalResult,
    DEFAULT_DIMENSIONS,
)
from evaluation.prompts import build_scoring_prompts


class ItineraryScorer:
    def __init__(self, dimensions: list[str] | None = None):
        self.dimensions = dimensions or DEFAULT_DIMENSIONS

    def score_single(self, eval_input: EvalInput) -> EvalResult:
        system_prompt, user_prompt, output_format = build_scoring_prompts(
            user_request=eval_input.user_request,
            itinerary=eval_input.itinerary,
            dimensions=self.dimensions,
        )

        raw = get_json_response(system_prompt, user_prompt, output_format)

        scores = []
        for entry in raw.get("scores", []):
            score_val = int(entry["score"])
            score_val = max(1, min(10, score_val))
            scores.append(
                DimensionScore(
                    dimension=entry["dimension"],
                    score=score_val,
                    justification=entry.get("justification", ""),
                )
            )

        aggregate = (
            sum(s.score for s in scores) / len(scores) if scores else 0.0
        )

        return EvalResult(
            input_id=eval_input.id,
            scores=scores,
            aggregate_score=round(aggregate, 2),
        )

    def score_batch(self, inputs: list[EvalInput]) -> list[EvalResult]:
        results = []
        for inp in inputs:
            results.append(self.score_single(inp))
        return results
