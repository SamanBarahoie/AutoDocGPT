# autodocgpt/agent_core/memory.py

"""
===============================================================================
AutoDocGPT - Memory Management Module
===============================================================================

This module implements the conversation memory for the AutoDocGPT agent.

Key Responsibilities:
---------------------
1. Maintain structured chat history:
   - Stores messages exchanged between user, assistant, and system.
   - Keeps memory size under control using configurable limits.

2. Support persistent and ephemeral memory:
   - Allows saving and reloading chat sessions (optional future extension).
   - Currently operates in-memory for simplicity.

3. Provides convenient methods:
   - `add_message(role, content)` to append messages.
   - `to_prompt()` to convert the memory into a Prompt object compatible with OpenRouterClient.

Usage Example:
--------------
from autodocgpt.agent_core.memory import AgentMemory
from autodocgpt.agent_core.base_agent import Prompt

memory = AgentMemory(max_messages=10)
memory.add_message("user", "Summarize this project.")
memory.add_message("assistant", "This project analyzes source code automatically.")

prompt = memory.to_prompt()
print(prompt.messages)

===============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict
from agent_core.base_agent import Prompt


@dataclass
class AgentMemory:
    """
    A lightweight conversation memory that stores recent messages.
    It keeps track of dialogue context for the AutoDocGPT agent.
    """

    max_messages: int = 20
    messages: List[Dict[str, str]] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        """Append a message to memory, trimming old ones if exceeding the limit."""
        if not isinstance(role, str) or not isinstance(content, str):
            raise TypeError("Both 'role' and 'content' must be strings.")
        self.messages.append({"role": role, "content": content})
        # Keep only the most recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def clear(self) -> None:
        """Reset the memory (useful between sessions)."""
        self.messages.clear()

    def to_prompt(self) -> Prompt:
        """Convert the memory into a Prompt object compatible with OpenRouterClient."""
        return Prompt(messages=self.messages.copy())

    def __len__(self) -> int:
        """Return the number of stored messages."""
        return len(self.messages)

    def __repr__(self) -> str:
        """Human-readable representation for debugging."""
        return f"<AgentMemory messages={len(self.messages)} / max={self.max_messages}>"


from agent_core.base_agent import Prompt

memory = AgentMemory(max_messages=10)
memory.add_message("user", "Summarize this project.")
memory.add_message("assistant", "This project analyzes source code automatically.")

prompt = memory.to_prompt()
print(prompt.messages)
