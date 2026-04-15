"""CheckerAgent - Plan validation wrapping existing PlanChecker."""

import os
import sys
from typing import Any

# Ensure project root is on the path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from utils.plan_checker import PlanChecker


class CheckerAgent:
    """Wraps the existing PlanChecker into the modular agent architecture.

    The checker does not use tools — it delegates to the battle-tested
    PlanChecker which performs multi-step LLM evaluation (budget check,
    reasonability check, rating summary, POI counting).
    """

    def __init__(self) -> None:
        self.plan_checker = PlanChecker()

    def check(
        self,
        itinerary: str,
        query: str,
        extra_requirements: str = "",
    ) -> tuple[str, dict[str, Any], dict[str, float]]:
        """Validate an itinerary and return feedback with metrics.

        Args:
            itinerary: The generated itinerary text.
            query: The original user query.
            extra_requirements: Additional constraints.

        Returns:
            Tuple of (advice_string, expense_info_dict, average_rating_dict).
            advice_string contains "No more suggestion" if the plan passes.
        """
        print("[CheckerAgent] Checking plan...")

        try:
            advice = self.plan_checker.check_plan(itinerary, query, extra_requirements)
        except Exception as e:
            print(f"[CheckerAgent] Check failed: {e}")
            advice = "Something went wrong!!!"

        # Ensure expense_info and average_rating are populated
        expense_info = getattr(self.plan_checker, "expense_info", {}) or {}
        average_rating = getattr(self.plan_checker, "average_rating", {}) or {}

        # If check passed but metrics are missing, try to compute them
        if not expense_info or not average_rating:
            self._try_compute_metrics(itinerary, query, extra_requirements)
            expense_info = getattr(self.plan_checker, "expense_info", {}) or {}
            average_rating = getattr(self.plan_checker, "average_rating", {}) or {}

        print(f"[CheckerAgent] Advice: {advice[:100]}...")
        print(f"[CheckerAgent] Expense: {expense_info}")
        print(f"[CheckerAgent] Ratings: {average_rating}")

        return advice, expense_info, average_rating

    def _try_compute_metrics(
        self, itinerary: str, query: str, extra_requirements: str
    ) -> None:
        """Attempt to compute expense and rating metrics if they're missing."""
        try:
            self.plan_checker._budget_check(itinerary, query, extra_requirements)
        except Exception as e:
            print(f"[CheckerAgent] Budget computation failed: {e}")

        try:
            self.plan_checker._rating_summary(itinerary)
            self.plan_checker._count_poi(itinerary)

            # Calculate averages
            self.plan_checker.average_rating = {}
            categories = [
                ("Attractions", "Total Attraction Ratings", "Total Attractions"),
                ("Accommodations", "Total Accommodation Ratings", "Total Accommodations"),
                ("Restaurants", "Total Restaurant Ratings", "Total Restaurants"),
                ("Overall", "Total", "Total"),
            ]
            for category, rating_key, count_key in categories:
                total_rating = self.plan_checker.rating_info.get(rating_key, 0)
                total_count = self.plan_checker.poi_count.get(count_key, 0)
                self.plan_checker.average_rating[category] = (
                    round(total_rating / total_count, 2) if total_count > 0 else 0.0
                )
        except Exception as e:
            print(f"[CheckerAgent] Rating computation failed: {e}")
