"""LLM client with OpenAI function calling support."""

import json
import os
import traceback

from tenacity import retry, stop_after_attempt, wait_exponential

from .models import ChatMessage, Role, ToolCall

# Support Langfuse integration
if os.getenv("LANGFUSE_SECRET_KEY"):
    from langfuse.openai import OpenAI
else:
    from openai import OpenAI


class LLMClient:
    """OpenAI-compatible LLM client with function calling.

    Replaces the text-completion approach in chat_model.py with structured
    tool calling following the modular agent pattern.
    """

    def __init__(self, model: str = "gpt-4o", temperature: float = 0) -> None:
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE"),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def chat_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[dict],
        tool_choice: str = "auto",
    ) -> ChatMessage:
        """Call LLM with tools (non-streaming, returns structured tool_calls)."""
        openai_messages = [m.to_openai_dict() for m in messages]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=self.temperature,
            )
        except Exception as e:
            print(f"LLM API error: {e}")
            traceback.print_exc()
            raise

        message = response.choices[0].message

        # Parse tool calls if present
        tool_calls = None
        if message.tool_calls:
            tool_calls = []
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        function_name=tc.function.name,
                        arguments=args,
                    )
                )

        return ChatMessage(
            role=Role.ASSISTANT,
            content=message.content,
            tool_calls=tool_calls,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def chat(self, messages: list[ChatMessage]) -> ChatMessage:
        """Call LLM without tools (for checker agent)."""
        openai_messages = [m.to_openai_dict() for m in messages]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
            )
        except Exception as e:
            print(f"LLM API error: {e}")
            traceback.print_exc()
            raise

        message = response.choices[0].message

        return ChatMessage(
            role=Role.ASSISTANT,
            content=message.content,
        )
