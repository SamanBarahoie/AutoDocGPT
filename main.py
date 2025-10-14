# main.py
"""
===============================================================================
AutoDocGPT - Main entrypoint
===============================================================================

This script wires together the components of AutoDocGPT:
- Loads/registers tools (file_tools, system_tools)
- Builds memory, language, registry and environment
- Connects to OpenRouter via OpenRouterClient
- Runs a simple reasoning->action->observation loop until termination

Usage:
    python main.py --task "Write a README for this project."

Environment:
    - Put your OpenRouter API key in a .env file or environment variable:
      OPENROUTER_API_KEY, OPENROUTER_API_BASE (optional)
===============================================================================
"""

import os
import json
import argparse
import logging
from typing import List

# Import core components
from agent_core.base_agent import OpenRouterClient, Prompt
from agent_core.memory import AgentMemory
from agent_core.language import FunctionCallingLanguage
from agent_core.registry import PythonActionRegistry, Goal
from agent_core.environment import Environment

# Import tools modules so that their @register_tool runs and registers them
# (these modules use the register_tool decorator from registry.py)
import tools.file_tools   # noqa: F401
import tools.system_tools  # noqa: F401

# Configure simple logging for the app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("autodocgpt.main")


def build_agent_components(max_memory_messages: int = 20):
    """
    Construct memory, language, registry, environment and OpenRouter client.
    Returns a dict with components.
    """
    # Memory
    memory = AgentMemory(max_messages=max_memory_messages)

    # Language layer (function-calling style)
    language = FunctionCallingLanguage()

    # Load all registered tools into a PythonActionRegistry (no tag filtering -> load all)
    registry = PythonActionRegistry()

    # Environment for executing actions
    env = Environment(dry_run=False)

    # OpenRouter client (reads .env via base_agent; ensure .env exists or env var set)
    client = OpenRouterClient()

    return {
        "memory": memory,
        "language": language,
        "registry": registry,
        "env": env,
        "client": client,
    }


def run_agent_loop(task: str, components: dict, model: str = "gpt-4o", max_iterations: int = 20):
    """
    A simple reasoning loop:
    1. add user task to memory
    2. construct prompt from goals + memory + tool metadata
    3. call LLM via OpenRouterClient
    4. parse response (expecting tool call JSON or plain text)
    5. execute requested tool via environment and register result to memory
    6. repeat until terminate or iterations exhausted
    """
    memory: AgentMemory = components["memory"]
    language: FunctionCallingLanguage = components["language"]
    registry: PythonActionRegistry = components["registry"]
    env: Environment = components["env"]
    client: OpenRouterClient = components["client"]

    # Define agent goals (example)
    goals: List[Goal] = [
        Goal(name="Gather Information", description="Read project files and build a README."),
        Goal(name="Terminate", description="Call terminate when the README is ready.")
    ]

    # Put initial user task into memory
    memory.add_message("user", task)

    logger.info("Starting agent loop with task: %s", task)
    for iteration in range(1, max_iterations + 1):
        logger.info("Iteration %d/%d", iteration, max_iterations)

        # Build prompt (goals + memory + tools metadata)
        actions = registry.get_actions()
        prompt: Prompt = language.construct_prompt(actions=actions, goals=goals, memory=memory)

        # Ask LLM what to do next
        try:
            raw_response = client.complete(prompt, model=model, max_tokens=1024)
        except Exception as e:
            logger.exception("LLM call failed: %s", e)
            memory.add_message("assistant", f"[error] LLM call failed: {e}")
            break

        logger.info("LLM raw response: %s", raw_response)

        # Parse LLM response (FunctionCallingLanguage.parse_response expects JSON string or returns terminate)
        parsed = language.parse_response(raw_response)

        # Normalized structure: parsed should be dict {"tool": "<name>", "args": {...}}
        tool_name = parsed.get("tool")
        args = parsed.get("args", {}) if isinstance(parsed.get("args", {}), dict) else {}

        # If the model returned a termination or plain message, handle it
        if tool_name is None or tool_name == "terminate":
            # If model returned terminate with a message, print it and break
            message = args.get("message") if isinstance(args, dict) else raw_response
            logger.info("Termination requested by model. Message: %s", message)
            memory.add_message("assistant", str(message))
            break

        logger.info("Model requested tool: %s with args: %s", tool_name, args)

        # Lookup the action from registry
        action = registry.get_action(tool_name)
        if not action:
            err_msg = f"Requested tool '{tool_name}' not found in registry."
            logger.warning(err_msg)
            memory.add_message("assistant", err_msg)
            # continue loop so LLM can pick something else
            continue

        # Execute the action in the environment
        exec_record = env.execute_action(action, args)
        logger.info("Execution record: %s", exec_record)

        # Store the decision and result in memory for next turns
        # We store a short assistant message indicating the tool call and outcome
        assistant_content = json.dumps({
            "tool": tool_name,
            "args": args,
            "result": exec_record
        }, ensure_ascii=False)
        memory.add_message("assistant", assistant_content)

        # If action is terminal, stop
        if action.terminal:
            logger.info("Terminal action executed, stopping loop.")
            break

    logger.info("Agent loop finished. Memory length: %d", len(memory))
    return memory


def main():
    parser = argparse.ArgumentParser(description="Run AutoDocGPT agent.")
    parser.add_argument("--task", type=str, default="Write a README for this project.", help="Initial task for the agent")
    parser.add_argument("--model", type=str, default="gpt-4o", help="Model name to use via OpenRouter")
    parser.add_argument("--max-iter", type=int, default=20, help="Max iterations of agent loop")
    args = parser.parse_args()

    # Build components
    components = build_agent_components()

    # Run the agent
    final_memory = run_agent_loop(task=args.task, components=components, model=args.model, max_iterations=args.max_iter)

    # Print final memory (last few messages) for inspection
    print("\n=== Final Memory (last 20 messages) ===")
    for m in final_memory.messages[-20:]:
        role = m.get("role")
        content = m.get("content")
        print(f"{role.upper()}: {content}\n")


if __name__ == "__main__":
    main()
