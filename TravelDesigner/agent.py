"""Agent base class following the action/execute/loop pattern."""

import os

import yaml

from .agent_env import AgentEnv
from .llm_client import LLMClient
from .models import ChatMessage, Role


class Agent:
    """Base agent with action/execute/loop pattern.

    Subclasses override loop() to implement domain-specific logic.
    The base class provides the core mechanics: LLM calling with tools,
    tool execution dispatch, and chat history management.
    """

    def __init__(
        self,
        config_path: str,
        agent_env: AgentEnv,
        llm_client: LLMClient,
        language: str = "en",
    ) -> None:
        self.agent_env = agent_env
        self.llm_client = llm_client
        self.language = language
        self.chat_history: list[ChatMessage] = []
        self.turn_count: int = 0
        self.max_turns: int = 30

        # Load role configuration from YAML
        self._load_role_config(config_path)

    def _load_role_config(self, config_path: str) -> None:
        """Load role configuration from YAML file."""
        # Resolve path relative to this package's roles/ directory
        if not os.path.isabs(config_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, config_path)

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.system_prompt = config["system"].get(self.language, config["system"].get("en", ""))
        self.instruction_template = config.get("instruction", "")
        self.use_model = config.get("use_model", None)

    def _init_chat(self, **template_vars: str) -> None:
        """Initialize chat history with system prompt and rendered instruction."""
        rendered_instruction = self.instruction_template.format(**template_vars)

        self.chat_history = [
            ChatMessage(role=Role.SYSTEM, content=self.system_prompt),
            ChatMessage(role=Role.USER, content=rendered_instruction),
        ]
        self.turn_count = 0

    def action(self) -> ChatMessage:
        """Call LLM with current chat history and tools.

        Returns the assistant's response (may contain tool_calls or content).
        """
        self.turn_count += 1
        if self.turn_count > self.max_turns:
            raise RuntimeError(
                f"Agent exceeded max turns ({self.max_turns}). "
                "Possible infinite loop."
            )

        tools = self.agent_env.get_tool_definitions()
        if tools:
            response = self.llm_client.chat_with_tools(
                self.chat_history, tools
            )
        else:
            response = self.llm_client.chat(self.chat_history)

        self.chat_history.append(response)
        return response

    def execute(self, tool_calls: list) -> list[str]:
        """Execute tool calls and append results to chat history.

        Args:
            tool_calls: List of ToolCall objects from the LLM response.

        Returns:
            List of tool result strings.
        """
        results = []
        for tc in tool_calls:
            print(f"  [Tool] {tc.function_name}({tc.arguments})")
            result = self.agent_env.tool_execute(tc)

            # Truncate very long results to avoid context overflow
            if len(result) > 8000:
                result = result[:8000] + "\n... (truncated)"

            self.chat_history.append(
                ChatMessage(
                    role=Role.TOOL,
                    content=result,
                    tool_call_id=tc.id,
                    name=tc.function_name,
                )
            )
            results.append(result)

        return results

    def loop(self, **template_vars: str) -> str:
        """Default action-execute loop. Runs until LLM stops calling tools.

        Subclasses should override this for custom loop logic.
        """
        self._init_chat(**template_vars)

        while True:
            response = self.action()

            if response.tool_calls:
                self.execute(response.tool_calls)
            else:
                # No tool calls = agent is done, return content
                return response.content or ""
