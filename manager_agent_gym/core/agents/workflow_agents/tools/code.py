"""Code execution tools (Python, JavaScript) - two-layer architecture."""

import json
from typing import TYPE_CHECKING, Any

from agents import Tool, function_tool

if TYPE_CHECKING:
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager


# ============================================================================
# LAYER 1: CODE EXECUTION (Core Business Logic)
# ============================================================================


async def _execute_python_code(
    code: str, timeout_seconds: int, executor: Any
) -> dict[str, Any]:
    """Execute Python code in sandbox."""
    try:
        result = await executor.execute_python(code, timeout_seconds)
        return {
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "error": result.get("error"),
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": f"Unexpected error: {str(e)}",
        }


async def _execute_node_code(
    code: str, timeout_seconds: int, executor: Any
) -> dict[str, Any]:
    """Execute JavaScript code in sandbox."""
    try:
        result = await executor.execute_javascript(code, timeout_seconds)
        return {
            "success": result["success"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
            "error": result.get("error"),
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": f"Unexpected error: {str(e)}",
        }


# ============================================================================
# LAYER 2: OPENAI TOOL WRAPPERS
# ============================================================================


def create_code_tools(
    resource_manager: "ResourceFileManager", e2b_api_key: str | None = None
) -> list[Tool]:
    """Create code execution tools for OpenAI SDK."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)

    @function_tool
    async def execute_python_code(code: str, timeout_seconds: int = 30) -> str:
        """
        Execute Python code in a secure, isolated sandbox environment with full package support.

        This tool runs Python code in a secure E2B sandbox with internet access and common
        scientific/data packages pre-installed (numpy, pandas, matplotlib, requests, etc.).
        Perfect for data analysis, calculations, web scraping, or any computational tasks.
        The code runs in complete isolation for security.

        Parameters:
            code (str):
                The Python code to execute. Can be multiple lines and import any standard
                or pre-installed packages. Example: "import pandas as pd\ndf = pd.DataFrame(...)"
            timeout_seconds (int):
                Maximum execution time in seconds before the code is terminated.
                Default: 30 seconds.

        Returns:
            str:
                JSON string containing execution results:
                - success: Whether the code executed successfully
                - stdout: Standard output from the code (print statements, etc.)
                - stderr: Error messages or warnings
                - exit_code: Process exit code (0 for success, non-zero for errors)
                - error: Human-readable error description if execution failed

        Usage:
            Call this tool when you need to run Python code for calculations, data processing,
            analysis, or any computational task. Use it for: data analysis with pandas,
            numerical computations, web scraping, API calls, file processing, or testing
            algorithms. The sandbox provides a safe environment for code execution.
        """
        result = await _execute_python_code(code, timeout_seconds, executor)
        return json.dumps(result, indent=2)

    @function_tool
    async def execute_node_code(code: str, timeout_seconds: int = 30) -> str:
        """
        Execute JavaScript/Node.js code in a secure sandbox environment.

        This tool runs JavaScript code using Node.js in an isolated E2B sandbox environment.
        Use it for JavaScript-specific tasks, web development testing, or Node.js operations.
        Note: For most computational tasks, Python is recommended as it has better
        data science library support.

        Parameters:
            code (str):
                The JavaScript/Node.js code to execute. Can use Node.js built-in modules
                and features. Example: "const fs = require('fs'); console.log('Hello');"
            timeout_seconds (int):
                Maximum execution time in seconds before the code is terminated.
                Default: 30 seconds.

        Returns:
            str:
                JSON string containing execution results:
                - success: Whether the code executed successfully
                - stdout: Standard output from the code (console.log, etc.)
                - stderr: Error messages or warnings
                - exit_code: Process exit code (0 for success, non-zero for errors)
                - error: Human-readable error description if execution failed

        Usage:
            Use this tool when you specifically need JavaScript/Node.js execution. Common
            uses include: testing JavaScript code, working with Node.js APIs, or handling
            JavaScript-specific operations. For data analysis or scientific computing,
            consider using Python instead.
        """
        result = await _execute_node_code(code, timeout_seconds, executor)
        return json.dumps(result, indent=2)

    return [execute_python_code, execute_node_code]
