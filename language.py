"""
===============================================================================
AutoDocGPT - Agent Language Abstractions
===============================================================================

This module defines the communication logic between the agent and the
language model (LLM). It provides an abstraction layer that allows different
agent types (e.g., function-calling, text-only) to construct structured prompts
and interpret model responses in a unified way.

Key Responsibilities:
---------------------
1. Define a base `AgentLanguage` interface for how prompts and responses
   should be structured.
2. Implement a concrete subclass `FunctionCallingLanguage` that supports
   OpenAI-style function (tool) calling.
3. Handle prompt construction from goals, actions, and memory context.
4. Parse model responses into structured invocation data.

===============================================================================
"""

import json
from typing import List, Dict, Any
from agent_core.base_agent import Prompt
from agent_core.memory import AgentMemory
from agent_core.registry import Action, Goal


class AgentLanguage:
    """Abstract base class defining how the agent communicates with the model."""

    def construct_prompt(
        self,
        actions: List[Action],
        goals: List[Goal],
        memory: AgentMemory
    ) -> Prompt:
        """Build the complete prompt object for the LLM."""
        raise NotImplementedError("Subclasses must implement construct_prompt()")

    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse model response into a structured format."""
        raise NotImplementedError("Subclasses must implement parse_response()")


class FunctionCallingLanguage(AgentLanguage):
    """
    A concrete language implementation that supports OpenAI-style
    function calling, used for agents that can invoke registered tools.
    """

    def format_goals(self, goals: List[Goal]) -> List[Dict[str, str]]:
        """Convert list of goals into a single system-level message."""
        sep = "\n-------------------\n"
        content = "\n\n".join(
            [f"{g.name}:{sep}{g.description}{sep}" for g in goals]
        )
        return [{"role": "system", "content": content}]

    def format_memory(self, memory: AgentMemory) -> List[Dict[str, str]]:
        """Convert the agent's memory into LLM-compatible message format."""
        formatted = []
        for msg in memory.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            formatted.append({"role": role, "content": content})
        return formatted

    def format_actions(self, actions: List[Action]) -> List[Dict[str, Any]]:
        """Build OpenAI-style tool metadata for available actions."""
        tools = []
        for action in actions:
            tools.append({
                "type": "function",
                "function": {
                    "name": action.name,
                    "description": action.description[:1024],
                    "parameters": action.parameters,
                },
            })
        return tools

    def construct_prompt(
        self,
        actions: List[Action],
        goals: List[Goal],
        memory: AgentMemory
    ) -> Prompt:
        """Assemble goals, memory, and tools into a single prompt."""
        messages = self.format_goals(goals) + self.format_memory(memory)
        tools = self.format_actions(actions)
        return Prompt(messages=messages, tools=tools)

    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse model response; detect function call or plain content."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"tool": "terminate", "args": {"message": response}}
