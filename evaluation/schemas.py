from dataclasses import dataclass, field


DIMENSION_DESCRIPTIONS = {
    "route_rationality": (
        "Logical geographic flow of the itinerary. "
        "1 = chaotic routing with excessive backtracking; "
        "5 = generally logical but some unnecessary detours; "
        "10 = optimal geographic flow with no wasted travel."
    ),
    "detail_level": (
        "Specificity of venue names, addresses, opening hours, costs, and timing. "
        "1 = vague suggestions with no concrete details; "
        "5 = most activities named but missing practical info; "
        "10 = every activity has specific venue, time, cost, and logistics."
    ),
    "representativeness": (
        "Coverage of iconic and must-see attractions for the destination. "
        "1 = misses all major landmarks and cultural highlights; "
        "5 = covers some popular spots but misses key ones; "
        "10 = comprehensive coverage of essential experiences."
    ),
    "budget_reasonability": (
        "Realism and consistency of cost estimates. "
        "1 = costs are fabricated or wildly inaccurate; "
        "5 = rough estimates, some clearly wrong; "
        "10 = all costs are realistic and internally consistent."
    ),
    "feasibility": (
        "Whether the schedule is physically achievable within time constraints. "
        "1 = impossible timing, overlapping activities, ignores travel time; "
        "5 = mostly doable but some days are overpacked; "
        "10 = every day has realistic pacing with appropriate travel time."
    ),
    "personalization": (
        "How well the itinerary responds to the user's specific preferences and constraints. "
        "1 = generic plan ignoring all stated preferences; "
        "5 = addresses some preferences but misses others; "
        "10 = every stated preference is reflected in the plan."
    ),
}

DEFAULT_DIMENSIONS = list(DIMENSION_DESCRIPTIONS.keys())


@dataclass
class EvalInput:
    id: str
    user_request: str
    itinerary: str
    metadata: dict = field(default_factory=dict)


@dataclass
class DimensionScore:
    dimension: str
    score: int
    justification: str


@dataclass
class EvalResult:
    input_id: str
    scores: list[DimensionScore]
    aggregate_score: float


@dataclass
class PairwiseResult:
    itinerary_a_id: str
    itinerary_b_id: str
    dimension: str
    winner: str  # "A", "B", or "tie"
    justification: str


@dataclass
class ABTestResult:
    pairwise_results: list[PairwiseResult]
    rankings: dict[str, list[str]]  # dimension -> ordered list of itinerary IDs
    overall_ranking: list[str]
