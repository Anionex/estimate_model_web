import json
from evaluation.schemas import DIMENSION_DESCRIPTIONS


def build_dimension_rubric(dimensions: list[str]) -> str:
    lines = []
    for dim in dimensions:
        desc = DIMENSION_DESCRIPTIONS.get(dim, f"Evaluate the itinerary on: {dim}")
        lines.append(f"- **{dim}**: {desc}")
    return "\n".join(lines)


# ============ Single-Itinerary Scoring ============

SCORING_SYSTEM_PROMPT = """\
You are an expert travel itinerary evaluator. You will be given a user's travel request and an AI-generated itinerary.

Score the itinerary on each of the following dimensions using a 1-10 integer scale.

Evaluation dimensions:
{dimension_rubric}

Rules:
- Evaluate each dimension independently. A high score on one dimension must not influence another.
- Provide a brief justification (1-2 sentences) for each score.
- Be rigorous but fair. A score of 7 means "good with minor issues", not "average"."""

SCORING_USER_PROMPT = """\
## User's Travel Request
{user_request}

## AI-Generated Itinerary
{itinerary}

Evaluate this itinerary on the specified dimensions."""

SCORING_OUTPUT_FORMAT = """\
{{
    "scores": [
        {{
            "dimension": string,
            "score": integer (1-10),
            "justification": string
        }}
    ]
}}"""


def build_scoring_prompts(user_request: str, itinerary: str, dimensions: list[str]):
    rubric = build_dimension_rubric(dimensions)
    system_prompt = SCORING_SYSTEM_PROMPT.format(dimension_rubric=rubric)
    user_prompt = SCORING_USER_PROMPT.format(
        user_request=user_request,
        itinerary=itinerary,
    )
    return system_prompt, user_prompt, SCORING_OUTPUT_FORMAT


# ============ Pairwise Comparison ============

COMPARISON_SYSTEM_PROMPT = """\
You are an expert travel itinerary evaluator performing a pairwise comparison. You will be given a user's travel request and two AI-generated itineraries (labeled A and B).

For each of the following dimensions, decide which itinerary is better:
{dimension_rubric}

Rules:
- For each dimension, output the winner: "A", "B", or "tie".
- Provide a brief justification (1-2 sentences) for each judgment.
- Do NOT favor an itinerary based on its label or position. Judge purely on quality.
- Evaluate each dimension independently."""

COMPARISON_USER_PROMPT = """\
## User's Travel Request
{user_request}

## Itinerary A
{itinerary_a}

## Itinerary B
{itinerary_b}

Compare these two itineraries on the specified dimensions."""

COMPARISON_OUTPUT_FORMAT = """\
{{
    "comparisons": [
        {{
            "dimension": string,
            "winner": string ("A", "B", or "tie"),
            "justification": string
        }}
    ]
}}"""


def build_comparison_prompts(
    user_request: str,
    itinerary_a: str,
    itinerary_b: str,
    dimensions: list[str],
):
    rubric = build_dimension_rubric(dimensions)
    system_prompt = COMPARISON_SYSTEM_PROMPT.format(dimension_rubric=rubric)
    user_prompt = COMPARISON_USER_PROMPT.format(
        user_request=user_request,
        itinerary_a=itinerary_a,
        itinerary_b=itinerary_b,
    )
    return system_prompt, user_prompt, COMPARISON_OUTPUT_FORMAT
