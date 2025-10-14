"""
===============================================================================
AutoDocGPT - Environment (Action Execution) Module
===============================================================================

This module defines the environment layer that executes actions (tools)
registered in the ActionRegistry. It is responsible for:

- Validating incoming arguments against the action's parameter schema (basic).
- Executing the action and capturing its result.
- Handling exceptions and returning structured execution metadata.
- Optional dry-run mode to validate invocation without executing side effects.

Returned execution record format (dict):
{
    "tool_executed": bool,
    "action_name": str,
    "args_used": dict,
    "result": Any,            # only present if tool_executed == True
    "error": str | None,      # error message if execution failed
    "traceback": str | None,  # full traceback when error occurred
    "timestamp": "ISO8601 string"
}

===============================================================================
"""

import time
import traceback
import logging
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from agent_core.registry import Action

# Configure module logger (the application can reconfigure logging as needed)
logger = logging.getLogger("autodocgpt.environment")
if not logger.handlers:
    # Avoid adding multiple handlers if module imported multiple times
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(ch)
logger.setLevel(logging.INFO)


@dataclass
class Environment:
    """
    Environment executes Actions and returns structured metadata about execution.

    Args:
        dry_run: if True, validate args but do not actually call the function.
        on_post_execute: optional callback invoked after successful execution:
            Callable[[Action, Dict[str,Any], Any], Any]
    """
    dry_run: bool = False
    on_post_execute: Optional[Callable[[Action, Dict[str, Any], Any], Any]] = None
    # you can add other config parameters here (e.g., timeouts) if needed
    default_max_message_length: int = field(default=2000)

    def _now_iso(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S%z")

    def _validate_args(self, action: Action, args: Dict[str, Any]) -> Optional[str]:
        """
        Basic validation: check required parameters declared in action.parameters.
        This is intentionally light-weight (checks presence only), because the
        registry parameters are derived from function signature.
        Returns: None if ok, otherwise error message string.
        """
        params_schema = action.parameters or {}
        required = params_schema.get("required", [])
        missing = [p for p in required if p not in args]
        if missing:
            return f"Missing required parameters: {missing}"
        return None

    def execute_action(self, action: Action, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the given Action with provided args and return structured result.

        Returns an execution record dict (see top docstring).
        """
        logger.info("Executing action: %s with args: %s", action.name, args)
        record: Dict[str, Any] = {
            "tool_executed": False,
            "action_name": action.name,
            "args_used": args.copy() if isinstance(args, dict) else {},
            "result": None,
            "error": None,
            "traceback": None,
            "timestamp": self._now_iso(),
        }

        # 1) validate arguments
        validation_err = self._validate_args(action, args or {})
        if validation_err:
            record["error"] = validation_err
            logger.warning("Validation failed for %s: %s", action.name, validation_err)
            return record

        # 2) dry-run mode: do not execute, just confirm validation
        if self.dry_run:
            record["tool_executed"] = False
            record["result"] = None
            logger.info("Dry-run enabled: skipping actual execution of %s", action.name)
            return record

        # 3) try to execute the action
        try:
            result = action.execute(**(args or {}))
            record["tool_executed"] = True
            record["result"] = result

            logger.info("Action %s executed successfully.", action.name)

            # optional post-execution callback for side-effects (indexing, logging, etc.)
            if self.on_post_execute:
                try:
                    self.on_post_execute(action, args, result)
                except Exception as cb_exc:
                    logger.exception("on_post_execute callback failed: %s", cb_exc)
                    # do not treat callback failure as action failure

            return record

        except Exception as exc:
            tb = traceback.format_exc()
            record["error"] = str(exc)
            record["traceback"] = tb
            logger.exception("Action %s raised an exception: %s", action.name, exc)
            return record


# -------------------------
# Quick unit-style demonstration
# -------------------------
# if __name__ == "__main__":
#     # Example action (stand-in) to demonstrate environment.execute_action
#     def sample_action(x: int, y: int = 1) -> int:
#         "Sample action that returns x + y"
#         return x + y
#
#     # Create a fake Action object like registry.Action
#     example_action = Action(
#         name="sample_add",
#         function=sample_action,
#         description="Add two numbers",
#
#         parameters={
#             "type": "object",
#             "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
#             "required": ["x"]
#         },
#         terminal=False
#     )
#
#     env = Environment(dry_run=False)
#     print("Run valid call:")
#     print(env.execute_action(example_action, {"x": 3, "y": 4}))
#
#     print("\nRun missing param:")
#     print(env.execute_action(example_action, {"y": 4}))
#
#     print("\nRun with error in function:")
#     def bad_action():
#         raise RuntimeError("boom")
#     bad = Action(
#         name="bad",
#         function=bad_action,
#         description="Always fails",
#         parameters={"type": "object", "properties": {}, "required": []},
#         terminal=False
#     )
#     print(env.execute_action(bad, {}))
