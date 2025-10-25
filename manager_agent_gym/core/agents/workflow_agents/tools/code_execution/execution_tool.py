"""Code execution tools wrapping E2B sandbox."""

from typing import TYPE_CHECKING

from agents import Tool, function_tool

if TYPE_CHECKING:
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager


def create_code_execution_tools(
    resource_manager: "ResourceFileManager", e2b_api_key: str | None = None
) -> list[Tool]:
    """
    Create code execution tools.

    Args:
        resource_manager: File storage manager
        e2b_api_key: E2B API key (optional, can be loaded from env)

    Returns:
        List of code execution tools
    """
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)

    @function_tool
    async def execute_python_code(code: str, timeout_seconds: int = 30) -> str:
        """
        Execute Python code in a secure sandbox environment.

        The code runs in an isolated E2B sandbox with network access and
        packages available:
        - Base E2B: numpy, pandas, scipy, matplotlib, scikit-learn, requests
        - Auto-installed: openpyxl, xlsxwriter, python-docx, statsmodels, seaborn, plotly

        Common use cases:
        - Excel files: pandas.to_excel(), xlsxwriter.Workbook(), openpyxl
        - Statistical analysis: statsmodels (time series, regression, ARIMA)
        - Visualization: seaborn (statistical plots), plotly (interactive charts)
        - Documents: python-docx for Word files

        Args:
            code: Python code to execute
            timeout_seconds: Maximum execution time in seconds (default: 30)

        Returns:
            JSON string with execution results (stdout, stderr, exit_code)
        """
        import json

        try:
            result = await executor.execute_python(code, timeout_seconds)

            # Format output
            output = {
                "success": result["success"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "exit_code": result["exit_code"],
            }

            if result.get("error"):
                output["error"] = result["error"]

            return json.dumps(output, indent=2)

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "error": f"Unexpected error: {str(e)}",
                },
                indent=2,
            )

    @function_tool
    async def execute_node_code(code: str, timeout_seconds: int = 30) -> str:
        """
        Execute Node.js/JavaScript code in a sandbox environment.

        Note: This feature is currently limited. Consider using Python for
        computational tasks.

        Args:
            code: JavaScript code to execute
            timeout_seconds: Maximum execution time in seconds (default: 30)

        Returns:
            JSON string with execution results
        """
        import json

        try:
            result = await executor.execute_javascript(code, timeout_seconds)

            output = {
                "success": result["success"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "exit_code": result["exit_code"],
            }

            if result.get("error"):
                output["error"] = result["error"]

            return json.dumps(output, indent=2)

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "error": f"Unexpected error: {str(e)}",
                },
                indent=2,
            )

    return [execute_python_code, execute_node_code]
