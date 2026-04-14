"""Pydantic data models for the TravelDesigner agent system."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """Represents a single tool invocation from the LLM."""
    id: str
    function_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """A message in the agent's chat history."""
    role: Role
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_openai_dict(self) -> dict[str, Any]:
        """Serialize to OpenAI API message format."""
        msg: dict[str, Any] = {"role": self.role.value}

        if self.content is not None:
            msg["content"] = self.content
        elif self.role != Role.ASSISTANT:
            msg["content"] = ""

        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function_name,
                        "arguments": __import__("json").dumps(
                            tc.arguments, ensure_ascii=False
                        ),
                    },
                }
                for tc in self.tool_calls
            ]

        if self.tool_call_id is not None:
            msg["tool_call_id"] = self.tool_call_id

        if self.name is not None:
            msg["name"] = self.name

        return msg


class ToolDefinition(BaseModel):
    """Definition of a tool available to the agent."""
    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_tool(self) -> dict[str, Any]:
        """Serialize to OpenAI tools format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class PlanResult(BaseModel):
    """Final output of the travel planning process."""
    itinerary: str
    expense_info: dict[str, Any] = Field(default_factory=dict)
    average_rating: dict[str, float] = Field(default_factory=dict)
