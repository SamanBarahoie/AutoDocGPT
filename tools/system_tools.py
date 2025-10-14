"""
===============================================================================
AutoDocGPT - System Tools
===============================================================================

A collection of system-related tools registered for use by the AutoDocGPT agent.

Tools provided:
- terminate(message: str) -> str
- get_current_time() -> str
- get_working_directory() -> str
- list_environment_variables() -> dict

These functions are registered with the central registry via the
`@register_tool` decorator so the agent can call them through function-calling.
===============================================================================
"""

import os
import time
from typing import Dict
from agent_core.registry import register_tool


@register_tool(tags=["system"], terminal=True)
def terminate(message: str) -> str:
    """
    Terminate the agent with a final message.

    Args:
        message: The message to display before termination.

    Returns:
        Formatted message with termination note.
    """
    return f"{message}\n[Agent terminated]"


@register_tool(tags=["system", "info"])
def get_current_time() -> str:
    """
    Return the current system time in ISO format.

    Returns:
        Current time as string (ISO 8601).
    """
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


@register_tool(tags=["system", "info"])
def get_working_directory() -> str:
    """
    Return the current working directory.

    Returns:
        Absolute path to the current working directory.
    """
    return os.getcwd()


@register_tool(tags=["system", "info"])
def list_environment_variables() -> Dict[str, str]:
    """
    Return all environment variables as a dictionary.

    Returns:
        Dict mapping environment variable names to their values.
    """
    return dict(os.environ)


# -------------------------
# Quick demo (run this file directly to exercise tools)
# -------------------------
# if __name__ == "__main__":
#     print("Current time:", get_current_time())
#     print("Working directory:", get_working_directory())
#     print("Environment variables (top-5):", dict(list(list_environment_variables().items())[:5]))
#     print(terminate("Shutting down AutoDocGPT..."))
