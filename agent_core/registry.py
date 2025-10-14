"""
===============================================================================
AutoDocGPT - Action and Tool Registry
===============================================================================

This module defines the logic for registering and managing "actions" (tools)
that the AutoDocGPT agent can use during its reasoning and execution cycle.

Key Responsibilities:
---------------------
1. Define `Action` objects that encapsulate callable tools, their metadata,
   parameter schema, and descriptions.
2. Maintain a central `ActionRegistry` that holds all available actions.
3. Provide a `register_tool` decorator to automatically register tools
   from other modules (e.g., file operations, system utilities).
4. Enable filtered loading of actions by tags or tool names.

===============================================================================
"""

import inspect
from typing import Callable, Dict, List, Any, Optional, get_type_hints
from dataclasses import dataclass, field


# Global registries for tools
TOOLS: Dict[str, dict] = {}
TOOLS_BY_TAG: Dict[str, List[str]] = {}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _get_json_type(param_type) -> str:
    """Convert Python types into JSON schema types."""
    if param_type == str:
        return "string"
    elif param_type == int:
        return "integer"
    elif param_type == float:
        return "number"
    elif param_type == bool:
        return "boolean"
    elif param_type == list:
        return "array"
    elif param_type == dict:
        return "object"
    return "string"


def _get_tool_metadata(
    func: Callable,
    tool_name: Optional[str] = None,
    description: Optional[str] = None,
    parameters_override: Optional[dict] = None,
    terminal: bool = False,
    tags: Optional[List[str]] = None
) -> dict:
    """Extracts function metadata for registration into the tool registry."""

    tool_name = tool_name or func.__name__
    description = description or (func.__doc__.strip() if func.__doc__ else "No description provided.")
    tags = tags or []

    if parameters_override:
        args_schema = parameters_override
    else:
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)
        args_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        for name, param in signature.parameters.items():
            if name in ["action_context", "action_agent"]:
                continue

            param_type = type_hints.get(name, str)
            args_schema["properties"][name] = {"type": _get_json_type(param_type)}

            if param.default == inspect.Parameter.empty:
                args_schema["required"].append(name)

    return {
        "tool_name": tool_name,
        "description": description,
        "parameters": args_schema,
        "function": func,
        "terminal": terminal,
        "tags": tags
    }


# ---------------------------------------------------------------------------
# Decorator for tool registration
# ---------------------------------------------------------------------------

def register_tool(
    tool_name: Optional[str] = None,
    description: Optional[str] = None,
    parameters_override: Optional[dict] = None,
    terminal: bool = False,
    tags: Optional[List[str]] = None
):
    """Decorator for registering a Python function as a tool."""
    def decorator(func: Callable):
        metadata = _get_tool_metadata(
            func,
            tool_name,
            description,
            parameters_override,
            terminal,
            tags
        )

        TOOLS[metadata["tool_name"]] = metadata
        for tag in metadata["tags"]:
            TOOLS_BY_TAG.setdefault(tag, []).append(metadata["tool_name"])

        return func
    return decorator


# ---------------------------------------------------------------------------
# Action and Registry Classes
# ---------------------------------------------------------------------------

@dataclass
class Action:
    """Encapsulates a callable action/tool used by the agent."""
    name: str
    function: Callable
    description: str
    parameters: Dict[str, Any]
    terminal: bool = False

    def execute(self, **kwargs) -> Any:
        """Execute the action's function with given arguments."""
        return self.function(**kwargs)
@dataclass
class Goal:
    """Represents a high-level task or objective for the agent."""
    name: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        """Convert goal into a serializable dictionary."""
        return {"name": self.name, "description": self.description}

class ActionRegistry:
    """Manages registration, lookup, and retrieval of all available actions."""

    def __init__(self):
        self.actions: Dict[str, Action] = {}

    def register(self, action: Action):
        """Register an action instance in the registry."""
        self.actions[action.name] = action

    def get_action(self, name: str) -> Optional[Action]:
        """Retrieve a registered action by its name."""
        return self.actions.get(name)

    def get_actions(self) -> List[Action]:
        """Return all registered actions."""
        return list(self.actions.values())


class PythonActionRegistry(ActionRegistry):
    """
    Loads all registered Python tools (functions) based on tag or name filters.
    """

    def __init__(
        self,
        tags: Optional[List[str]] = None,
        tool_names: Optional[List[str]] = None
    ):
        super().__init__()

        self.terminate_tool = None

        for name, meta in TOOLS.items():
            if name == "terminate":
                self.terminate_tool = meta

            if tool_names and name not in tool_names:
                continue

            if tags and not any(tag in meta.get("tags", []) for tag in tags):
                continue

            self.register(Action(
                name=name,
                function=meta["function"],
                description=meta["description"],
                parameters=meta["parameters"],
                terminal=meta.get("terminal", False)
            ))

    def register_terminate_tool(self):
        """Explicitly register the terminate tool if defined."""
        if not self.terminate_tool:
            raise RuntimeError("Terminate tool not found in registry.")

        meta = self.terminate_tool
        self.register(Action(
            name="terminate",
            function=meta["function"],
            description=meta["description"],
            parameters=meta["parameters"],
            terminal=meta["terminal"]
        ))
