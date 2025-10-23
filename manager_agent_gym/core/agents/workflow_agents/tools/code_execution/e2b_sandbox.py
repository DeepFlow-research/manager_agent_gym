"""E2B sandbox integration for secure code execution."""

from typing import Any
from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


class E2BSandboxExecutor:
    """Manages E2B sandbox execution."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize E2B executor.

        Args:
            api_key: E2B API key (if None, loads from environment)
        """
        self.api_key = api_key
        self._sandbox = None

    async def execute_python(
        self, code: str, timeout_seconds: int = 30
    ) -> dict[str, Any]:
        """
        Execute Python code in E2B sandbox.

        Args:
            code: Python code to execute
            timeout_seconds: Execution timeout

        Returns:
            Dictionary with stdout, stderr, exit_code, and error fields
        """
        sandbox = None
        try:
            # Create sandbox
            sandbox = await AsyncSandbox.create(
                api_key=self.api_key, timeout=timeout_seconds
            )

            # Execute code
            execution = await sandbox.run_code(
                code, language="python", timeout=timeout_seconds
            )

            # Collect results
            stdout_parts = []
            stderr_parts = []
            error_msg = None

            # Process execution results
            if execution.error:
                error_msg = (
                    str(execution.error.value)
                    if hasattr(execution.error, "value")
                    else str(execution.error)
                )
                stderr_parts.append(error_msg)

            # Collect output from logs
            if execution.logs:
                for log in execution.logs.stdout:
                    stdout_parts.append(log)
                for log in execution.logs.stderr:
                    stderr_parts.append(log)

            # Get final result
            if execution.results:
                for result in execution.results:
                    if hasattr(result, "text") and result.text:
                        stdout_parts.append(result.text)
                    elif hasattr(result, "png") and result.png:
                        stdout_parts.append(f"[Image output: {len(result.png)} bytes]")
                    elif hasattr(result, "json") and result.json:
                        import json

                        stdout_parts.append(json.dumps(result.json, indent=2))

            return {
                "success": error_msg is None,
                "stdout": "\n".join(stdout_parts),
                "stderr": "\n".join(stderr_parts),
                "exit_code": 0 if error_msg is None else 1,
                "error": error_msg,
            }

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "error": f"Execution error: {str(e)}",
            }
        finally:
            # Ensure sandbox is properly closed
            if sandbox is not None:
                await sandbox.kill()

    async def execute_javascript(
        self, code: str, timeout_seconds: int = 30
    ) -> dict[str, Any]:
        """
        Execute JavaScript/Node.js code in E2B sandbox.

        Note: Currently E2B Code Interpreter focuses on Python. For Node.js,
        we wrap the code in a Python subprocess call as a workaround.

        Args:
            code: JavaScript code to execute
            timeout_seconds: Execution timeout

        Returns:
            Dictionary with stdout, stderr, exit_code, and error fields
        """
        # For now, return an informative message about Node.js support
        # In production, you might use a different E2B template or sandbox
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "error": "JavaScript execution not yet supported in E2B Code Interpreter. Consider using Python or implementing a custom E2B template.",
        }
