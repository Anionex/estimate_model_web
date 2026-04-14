"""TravelAgent - Concrete travel planner agent."""

from datetime import datetime

from .agent import Agent
from .agent_env import AgentEnv
from .llm_client import LLMClient
from .models import ChatMessage, Role


class TravelAgent(Agent):
    """Travel planning agent that gathers information via tools and produces itineraries.

    Uses OpenAI function calling to decide which tools to invoke, following
    the PPTAgent action/execute/loop pattern.
    """

    def __init__(self, agent_env: AgentEnv, llm_client: LLMClient, language: str = "en") -> None:
        super().__init__(
            config_path="roles/travel_planner.yaml",
            agent_env=agent_env,
            llm_client=llm_client,
            language=language,
        )
        self.max_turns = 30

    def loop(self, query: str, extra_requirements: str = "") -> str:
        """Run the planning loop: gather info via tools, then output itinerary.

        Args:
            query: The user's travel request.
            extra_requirements: Additional constraints or preferences.

        Returns:
            The generated itinerary text.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        self._init_chat(
            query=query,
            extra_requirements=extra_requirements,
            current_date=current_date,
        )

        print(f"[TravelAgent] Starting planning for: {query[:80]}...")
        iteration = 0

        while True:
            iteration += 1
            print(f"[TravelAgent] Turn {iteration}")

            response = self.action()

            if response.tool_calls:
                self.execute(response.tool_calls)
            else:
                print(f"[TravelAgent] Completed after {iteration} turns")
                return response.content or ""

    def inject_feedback(self, feedback: str) -> None:
        """Inject checker feedback into the conversation for revision."""
        self.chat_history.append(
            ChatMessage(
                role=Role.USER,
                content=(
                    f"System feedback on your itinerary:\n{feedback}\n\n"
                    "Please revise the itinerary based on this feedback. "
                    "You may call tools again if needed to gather missing information. "
                    "When done, output the complete revised itinerary."
                ),
            )
        )

    def loop_continue(self) -> str:
        """Continue the action-execute loop from existing chat history.

        Used after inject_feedback() to let the agent revise its plan.
        """
        print("[TravelAgent] Continuing with feedback...")
        iteration = 0

        while True:
            iteration += 1
            print(f"[TravelAgent] Revision turn {iteration}")

            response = self.action()

            if response.tool_calls:
                self.execute(response.tool_calls)
            else:
                print(f"[TravelAgent] Revision completed after {iteration} turns")
                return response.content or ""
