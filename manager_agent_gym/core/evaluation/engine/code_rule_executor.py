"""
Code rule executor with workflow and context API.

Executes Python code rules for evaluation with ValidationContext helpers.
"""

import asyncio
import io
import logging
import sys
import traceback
from typing import Any, TYPE_CHECKING

from manager_agent_gym.schemas.domain.resource import Resource

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.evaluation.schemas.success_criteria import (
        ValidationContext,
    )

logger = logging.getLogger(__name__)


class CodeRuleExecutor:
    """Executes code-based evaluation rules with workflow context signature."""

    async def execute(
        self,
        code: str,
        workflow: "Workflow",
        context: "ValidationContext",
    ) -> tuple[float, str | None]:
        """
        Execute a code rule with workflow and validation context.

        Code rules receive:
        - workflow: Workflow - current workflow being evaluated
        - context: ValidationContext - provides helper methods and file accessors

        Expected function signature:
            def evaluate(workflow: Workflow, context: ValidationContext) -> float | tuple[float, str]

        Args:
            code: Python code string (must define 'evaluate' function)
            workflow: Workflow object being evaluated
            context: ValidationContext with helpers and file access

        Returns:
            (score, feedback) tuple - feedback includes stdout/stderr and any errors
        """
        # Log the code being executed for debugging
        logger.info("=" * 80)
        logger.info("EXECUTING CODE RULE:")
        logger.info("-" * 80)
        logger.info(code)
        logger.info("=" * 80)

        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            # Redirect stdout/stderr
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            # Import types for exec scope (avoid circular imports)
            from manager_agent_gym.schemas.domain.workflow import Workflow
            from manager_agent_gym.core.evaluation.schemas.success_criteria import (
                ValidationContext,
            )

            # Prepare execution scope with helpful imports
            exec_scope: dict[str, Any] = {
                "Resource": Resource,
                "Workflow": Workflow,
                "ValidationContext": ValidationContext,
                "__builtins__": __builtins__,  # Allow normal Python operations
                "print": print,  # Explicitly allow print (will be captured by stdout)
                "DEBUG": True,  # Flag to enable debug mode in rubrics
            }

            # Import commonly used libraries (only if available)
            try:
                import pandas as pd  # type: ignore

                exec_scope["pd"] = pd
                exec_scope["pandas"] = pd  # Also make available as 'pandas' for imports
            except ImportError:
                exec_scope["pd"] = None
                exec_scope["pandas"] = None
                logger.debug("pandas not available in eval environment")

            try:
                import numpy as np  # type: ignore

                exec_scope["np"] = np
                exec_scope["numpy"] = np  # Also make available as 'numpy' for imports
            except ImportError:
                exec_scope["np"] = None
                exec_scope["numpy"] = None
                logger.debug("numpy not available in eval environment")

            import re
            import json
            from pathlib import Path

            exec_scope["re"] = re
            exec_scope["json"] = json
            exec_scope["Path"] = Path

            # Add a helper for debugging exceptions in rubric code
            def debug_exception(e: Exception, context_msg: str = "") -> None:
                """Helper for rubric code to log exceptions for debugging."""
                import traceback

                print(f"DEBUG: Exception in rubric code: {type(e).__name__}: {e}")
                if context_msg:
                    print(f"DEBUG: Context: {context_msg}")
                print(f"DEBUG: Traceback:\n{traceback.format_exc()}")

            exec_scope["debug_exception"] = debug_exception

            # Strip common import statements that are already provided
            # This prevents import errors in environments where pandas/numpy aren't installed
            code_cleaned = code
            import_patterns = [
                r"^\s*import\s+re\s*$",
                r"^\s*import\s+json\s*$",
                r"^\s*import\s+pandas\s+as\s+pd\s*$",
                r"^\s*import\s+numpy\s+as\s+np\s*$",
                r"^\s*from\s+pathlib\s+import\s+Path\s*$",
            ]
            for pattern in import_patterns:
                code_cleaned = re.sub(pattern, "", code_cleaned, flags=re.MULTILINE)

            # Compile and execute code
            # Use same dict for globals and locals so helper functions are accessible
            exec(code_cleaned, exec_scope)
            evaluate_fn = exec_scope.get("evaluate")

            if not evaluate_fn:
                raise ValueError("Code rule must define 'evaluate' function")

            # Call with workflow and context
            if asyncio.iscoroutinefunction(evaluate_fn):
                result = await evaluate_fn(workflow, context)
            else:
                result = evaluate_fn(workflow, context)

            # Normalize result
            if isinstance(result, (int, float)):
                score = float(result)
                reason = None
            elif isinstance(result, tuple):
                if len(result) == 2:
                    score = (
                        float(result[0]) if isinstance(result[0], (int, float)) else 0.0
                    )
                    reason = str(result[1]) if result[1] is not None else None
                elif len(result) == 1 and isinstance(result[0], (int, float)):
                    score = float(result[0])
                    reason = None
                else:
                    # Invalid tuple format
                    score = 0.0
                    reason = f"❌ Invalid result format: {result}"
            else:
                # Try to coerce to float
                try:
                    score = float(result)  # type: ignore
                    reason = None
                except (ValueError, TypeError):
                    score = 0.0
                    reason = f"❌ Cannot convert result to float: {result}"

            # Collect stdout/stderr
            stdout_text = stdout_capture.getvalue()
            stderr_text = stderr_capture.getvalue()

            # Build comprehensive feedback
            feedback_parts = []
            if reason:
                feedback_parts.append(f"**Result**: {reason}")
            if stdout_text:
                feedback_parts.append(f"**stdout**:\n```\n{stdout_text}\n```")
            if stderr_text:
                feedback_parts.append(f"**stderr**:\n```\n{stderr_text}\n```")

            final_feedback = "\n\n".join(feedback_parts) if feedback_parts else reason

            # Log execution details
            logger.info(f"✅ Code rule executed successfully - Score: {score}")
            if stdout_text:
                logger.info(f"📤 stdout:\n{stdout_text}")
            if stderr_text:
                logger.warning(f"⚠️ stderr:\n{stderr_text}")
            if reason:
                logger.info(f"💬 Feedback: {reason}")

            return score, final_feedback

        except Exception as e:
            # Capture full traceback
            tb_str = traceback.format_exc()

            # Collect stdout/stderr
            stdout_text = stdout_capture.getvalue()
            stderr_text = stderr_capture.getvalue()

            # Build detailed error feedback
            feedback_parts = [
                f"❌ **Execution Error**: {type(e).__name__}: {str(e)}",
                "",
                "**Traceback**:",
                "```",
                tb_str,
                "```",
            ]
            if stdout_text:
                feedback_parts.extend(
                    ["", "**stdout before error**:", "```", stdout_text, "```"]
                )
            if stderr_text:
                feedback_parts.extend(["", "**stderr**:", "```", stderr_text, "```"])

            error_feedback = "\n".join(feedback_parts)

            # Log comprehensive error details
            logger.error("=" * 80)
            logger.error("❌ CODE RULE EXECUTION FAILED")
            logger.error("-" * 80)
            logger.error(f"Error: {type(e).__name__}: {str(e)}")
            logger.error("-" * 80)
            logger.error("Traceback:")
            logger.error(tb_str)
            if stdout_text:
                logger.error(f"stdout before error:\n{stdout_text}")
            if stderr_text:
                logger.error(f"stderr:\n{stderr_text}")
            logger.error("=" * 80)

            return 0.0, error_feedback

        finally:
            # Always restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
