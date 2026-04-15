#!/usr/bin/env python3
"""TravelDesigner - Modular agent-based travel planner.

Usage:
    uv run python TravelDesigner/run.py "Plan a 3-day trip from New York to San Francisco..."
    uv run python -m TravelDesigner.run "Plan a 3-day trip..."
"""

import json
import os
import sys
import time
from datetime import datetime

# Path setup
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

import dotenv

dotenv.load_dotenv(os.path.join(root_dir, ".env"))

from TravelDesigner.orchestrator import TravelOrchestrator


def main() -> None:
    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Plan a 3-day trip from Kennesaw, GA to San Francisco for 1 person "
        "with a budget of $2000, from April 20 to April 22, 2026."
    )

    start_time = time.time()
    print(f"Query: {query}", file=sys.stderr)

    # Determine model from env or default
    model = os.getenv("OPENAI_API_MODEL", "gpt-4o")
    orchestrator = TravelOrchestrator(model=model)
    result = orchestrator.run(query)

    # Format expense table (same format as planner_checker_system.py)
    if result.expense_info:
        unit = result.expense_info.get("Unit", "")
        expense_rows = []
        for k, v in result.expense_info.items():
            if k != "Unit":
                expense_rows.append(f"| {k} | {v} |")
        expense_table = (
            f"| Item | Cost ({unit}) |\n|------|----------------|\n"
            + "\n".join(expense_rows)
        )
        result.itinerary = (
            result.itinerary + "\n\n---Expense Summary---\n\n" + expense_table
        )

    # Save logs
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    with open(
        os.path.join(log_dir, f"itinerary_{timestamp}.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(result.itinerary)

    with open(
        os.path.join(log_dir, f"plan_info_{timestamp}.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    print(f"Runtime: {elapsed:.2f} seconds", file=sys.stderr)

    # Print for subprocess communication (same protocol as planner_checker_system.py)
    print("\n=====RETURN=====\n")
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
