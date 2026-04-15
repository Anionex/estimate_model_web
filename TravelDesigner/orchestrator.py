"""TravelOrchestrator - Coordinates planner-checker loop."""

import os
import sys

# Ensure project root is on the path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from utils.config import MAX_CHECK_ITER, GLOBAL_LANGUAGE

from .agent_env import AgentEnv
from .checker_agent import CheckerAgent
from .llm_client import LLMClient
from .models import PlanResult
from .tool_wrappers import (
    get_accommodations,
    get_attractions,
    get_distance_matrix,
    get_flights,
    get_restaurants,
    search_web,
)
from .travel_agent import TravelAgent


class TravelOrchestrator:
    """Coordinates the TravelAgent and CheckerAgent in a generate-check-revise loop.

    This replaces planner_checker_system.py with the modular agent architecture.
    """

    def __init__(self, model: str = "gpt-4o", language: str | None = None) -> None:
        # Determine language from config
        lang = language or ("zh" if GLOBAL_LANGUAGE == "zh-cn" else "en")

        # Set up tool environment
        env = AgentEnv()
        env.register_tool(search_web)
        env.register_tool(get_attractions)
        env.register_tool(get_restaurants)
        env.register_tool(get_accommodations)
        env.register_tool(get_flights)
        env.register_tool(get_distance_matrix)

        # Create LLM client
        llm_client = LLMClient(model=model, temperature=0)

        # Create agents
        self.travel_agent = TravelAgent(env, llm_client, language=lang)
        self.checker_agent = CheckerAgent()
        self.max_check_iterations = MAX_CHECK_ITER

    def run(self, query: str, extra_requirements: str = "") -> PlanResult:
        """Execute the full planner-checker loop.

        Args:
            query: The user's travel request.
            extra_requirements: Additional constraints.

        Returns:
            PlanResult with itinerary, expense_info, and average_rating.
        """
        itinerary = ""
        expense_info = {}
        average_rating = {}

        for iteration in range(1, self.max_check_iterations + 1):
            print(f"\n{'='*50}")
            print(f"Iteration {iteration}/{self.max_check_iterations}")
            print(f"{'='*50}\n")

            # Generate or revise itinerary
            if iteration == 1:
                itinerary = self.travel_agent.loop(query, extra_requirements)
            else:
                self.travel_agent.inject_feedback(advice)
                itinerary = self.travel_agent.loop_continue()

            # Check the itinerary
            print("\n=====\nChecking result.\n=====")
            advice, expense_info, average_rating = self.checker_agent.check(
                itinerary, query, extra_requirements
            )

            # Check if the plan passes
            if "No more suggestion" in advice or "Something went wrong" in advice:
                print("=====\nPlan approved.\n=====")
                break
            else:
                print(f"=====\nFeedback: {advice[:200]}...\n=====")

        return PlanResult(
            itinerary=itinerary,
            expense_info=expense_info,
            average_rating=average_rating,
        )
