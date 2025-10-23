"""
Code rule executor with workflow and context API.

Executes Python code rules for evaluation with ValidationContext helpers.
"""

import asyncio
import logging
from typing import Any, TYPE_CHECKING

from manager_agent_gym.schemas.domain.resource import Resource

if TYPE_CHECKING:
    from manager_agent_gym.schemas.domain.workflow import Workflow
    from manager_agent_gym.core.evaluation.schemas.success_criteria import ValidationContext

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
            (score, feedback) tuple
        """
        try:
            # Import types for exec scope (avoid circular imports)
            from manager_agent_gym.schemas.domain.workflow import Workflow
            from manager_agent_gym.core.evaluation.schemas.success_criteria import ValidationContext
            
            # Prepare execution scope with helpful imports
            exec_scope: dict[str, Any] = {
                "Resource": Resource,
                "Workflow": Workflow,
                "ValidationContext": ValidationContext,
                "__builtins__": __builtins__,  # Allow normal Python operations
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
                return float(result), None
            elif isinstance(result, tuple):
                if len(result) == 2:
                    score = (
                        float(result[0]) if isinstance(result[0], (int, float)) else 0.0
                    )
                    reason = str(result[1]) if result[1] is not None else None
                    return score, reason
                elif len(result) == 1 and isinstance(result[0], (int, float)):
                    return float(result[0]), None
                else:
                    # Invalid tuple format
                    return 0.0, f"Invalid result format: {result}"
            else:
                # Try to coerce to float
                try:
                    return float(result), None  # type: ignore
                except (ValueError, TypeError):
                    return 0.0, f"Cannot convert result to float: {result}"

        except Exception as e:
            logger.error(f"Code rule execution failed: {e}", exc_info=True)
            return 0.0, f"Execution error: {str(e)}"
