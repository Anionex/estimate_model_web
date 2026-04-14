"""AgentEnv - Tool registration and dispatch following PPTAgent pattern."""

import inspect
import re
import traceback
from typing import Any, Callable, get_type_hints

from .models import ToolCall, ToolDefinition


# Python type -> JSON Schema type mapping
_TYPE_MAP: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def _python_type_to_json_schema(annotation: Any) -> dict[str, str]:
    """Convert a Python type annotation to JSON Schema type."""
    if annotation in _TYPE_MAP:
        return {"type": _TYPE_MAP[annotation]}
    return {"type": "string"}


def _parse_docstring_params(docstring: str | None) -> dict[str, str]:
    """Parse Google-style docstring Args section for parameter descriptions."""
    if not docstring:
        return {}

    params: dict[str, str] = {}
    in_args = False
    current_param = None
    current_desc = []

    for line in docstring.split("\n"):
        stripped = line.strip()

        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        elif in_args and stripped and not stripped.startswith(" ") and ":" not in stripped:
            # Left the Args section
            if stripped.lower().startswith(("returns:", "raises:", "yields:", "note:")):
                break

        if in_args:
            # Match "param_name: description" or "param_name (type): description"
            match = re.match(r"(\w+)\s*(?:\([^)]*\))?\s*:\s*(.*)", stripped)
            if match:
                if current_param:
                    params[current_param] = " ".join(current_desc).strip()
                current_param = match.group(1)
                current_desc = [match.group(2)]
            elif current_param and stripped:
                current_desc.append(stripped)

    if current_param:
        params[current_param] = " ".join(current_desc).strip()

    return params


class AgentEnv:
    """Manages tool registration and dispatch.

    Following PPTAgent's AgentEnv pattern: tools are registered with auto-generated
    JSON Schema from type hints, and dispatched to local Python functions.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._functions: dict[str, Callable] = {}

    def register_tool(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
        param_descriptions: dict[str, str] | None = None,
    ) -> None:
        """Register a callable as a tool with auto-generated JSON Schema.

        Args:
            func: The Python function to register.
            name: Override tool name (defaults to func.__name__).
            description: Override description (defaults to first line of docstring).
            param_descriptions: Override parameter descriptions (defaults to docstring Args section).
        """
        tool_name = name or func.__name__
        tool_desc = description or (inspect.getdoc(func) or "").split("\n")[0]

        # Get type hints and signature
        hints = get_type_hints(func)
        sig = inspect.signature(func)

        # Parse docstring for param descriptions
        doc_params = _parse_docstring_params(inspect.getdoc(func))
        if param_descriptions:
            doc_params.update(param_descriptions)

        # Build JSON Schema properties
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            annotation = hints.get(param_name, str)
            prop = _python_type_to_json_schema(annotation)

            if param_name in doc_params:
                prop["description"] = doc_params[param_name]

            properties[param_name] = prop

            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        schema = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required

        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_desc,
            parameters=schema,
        )

        self._tools[tool_name] = tool_def
        self._functions[tool_name] = func

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return all tools in OpenAI function calling format."""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def tool_execute(self, tool_call: ToolCall) -> str:
        """Execute a tool call and return the result as string."""
        func_name = tool_call.function_name
        if func_name not in self._functions:
            return f"Error: Unknown tool '{func_name}'"

        func = self._functions[func_name]
        try:
            result = func(**tool_call.arguments)
            return str(result)
        except Exception as e:
            traceback.print_exc()
            return f"Error executing {func_name}: {e}"
