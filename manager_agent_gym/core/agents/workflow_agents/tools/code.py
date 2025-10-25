"""Code execution tools (Python, JavaScript) - two-layer architecture."""

import json
from typing import TYPE_CHECKING, Any

from agents import RunContextWrapper, Tool, function_tool

if TYPE_CHECKING:
    from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager


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
    from manager_agent_gym.core.workflow.context import AgentExecutionContext

    executor = E2BSandboxExecutor(api_key=e2b_api_key)

    @function_tool
    async def execute_python_code(
        ctx: RunContextWrapper[AgentExecutionContext],
        code: str,
        timeout_seconds: int = 30,
    ) -> str:
        """
        Execute Python code in a secure, isolated sandbox environment with full package support.

        This tool runs Python code in a secure E2B sandbox with internet access and common
        scientific/data packages pre-installed (numpy, pandas, matplotlib, requests, etc.).
        Perfect for data analysis, calculations, file creation, web scraping, or any computational tasks.

        **🔄 COMPLETE WORKFLOW:**

        1. **Input Files Uploaded**: ALL input resources from your task (Excel, PDF, CSV, etc.)
           are automatically uploaded to /home/user/ in the sandbox. Just use the original file
           paths in your code - they're automatically rewritten to work in the sandbox.

        2. **Code Executes**: Your Python code runs with full package access in a secure container.

        3. **Output Files Downloaded**: ANY files you create in /home/user/ are automatically
           downloaded to your local system after execution completes.

        4. **Iterative Workflow**: Files created in previous calls are automatically available
           in subsequent calls, enabling multi-step workflows (e.g., create data → analyze → visualize).

        **💡 WHEN TO USE THIS TOOL:**
        - Complex data analysis requiring pandas, numpy, statsmodels, scikit-learn
        - Creating output files: Excel (.xlsx), charts (.png), reports (.csv)
        - Statistical analysis, time series, regression, forecasting
        - Multi-step data processing pipelines
        - Any calculation too complex for other tools

        **✨ AUTOMATIC FILE TRACKING:**

        Files you create are **automatically tracked as resources**! You no longer need to:
        - Parse JSON responses
        - Manually construct Resource objects
        - Worry about file paths or sandbox locations

        Just create files and describe your work - the system handles the rest.

        Example workflow:
        ```python
        # 1. Call the tool to create files
        result = execute_python_code("df.to_excel('/home/user/analysis.xlsx')")

        # 2. You'll see: "✅ Created 1 file(s): analysis.xlsx (50KB)"

        # 3. File is automatically registered - just reference it in your notes!
        # No need to create Resource objects manually.
        ```

        Parameters:
            code (str):
                The Python code to execute. Save outputs to /home/user/filename.ext
                Example: "df.to_excel('/home/user/report.xlsx', index=False)"
            timeout_seconds (int):
                Maximum execution time in seconds (default: 30)

        Returns:
            str:
                Human-readable summary of execution results including:
                - Success status
                - List of created files (automatically tracked!)
                - Standard output from your code
                - Any error messages if execution failed
        """
        # Get input files and context key from execution context
        input_file_paths = []
        context_key = None
        try:
            context = ctx.context
            if context:
                # Get context key for state isolation
                context_key = f"{context.agent_id}:{context.current_task_id}"

                # Get ALL available resources (input + intermediary)
                # This ensures files created by previous execute_python_code calls
                # are available in subsequent calls (iterative workflow support)
                all_resources = context.get_all_available_resources()
                if all_resources:
                    input_file_paths = [
                        r.file_path for r in all_resources if r.file_path
                    ]
        except Exception as e:
            from manager_agent_gym.core.common.logging import logger

            logger.error(
                f"❌ Failed to get input files from context: {e}", exc_info=True
            )
            # If context not available, proceed without input files or isolation
            pass

        # Execute with context-aware state management
        result = await executor.execute_python(
            code=code,
            timeout_seconds=timeout_seconds,
            upload_files=True,
            context_key=context_key,
            input_files=input_file_paths if input_file_paths else None,
        )

        # AUTO-REGISTER: Track created files as intermediary resources
        try:
            from manager_agent_gym.core.common.logging import logger

            if not ctx.context:
                logger.warning(
                    "⚠️ execute_python_code: No context available for auto-registration"
                )
            elif not result.get("success"):
                logger.warning(
                    "⚠️ execute_python_code: Execution failed, skipping auto-registration"
                )
            elif not result.get("output_files"):
                logger.info("ℹ️ execute_python_code: No output files to register")
            else:
                from manager_agent_gym.schemas.domain.resource import Resource

                logger.info(
                    f"🔄 Auto-registering {len(result['output_files'])} file(s) from code execution"
                )
                for file_info in result.get("output_files", []):
                    resource = Resource(
                        name=f"Generated: {file_info['file_name']}",
                        description="Auto-created by code execution",
                        file_path=file_info["file_path"],
                        mime_type=file_info.get(
                            "mime_type", "application/octet-stream"
                        ),
                        size_bytes=file_info.get("size_bytes", 0),
                        resource_role="intermediary",
                    )
                    ctx.context.register_created_resource(resource)
                    logger.info(
                        f"  ✅ Registered: {file_info['file_name']} at {file_info['file_path']}"
                    )
        except Exception as e:
            # Don't fail execution if auto-registration fails
            from manager_agent_gym.core.common.logging import logger

            logger.error(f"❌ Failed to auto-register resources: {e}", exc_info=True)

        # RETURN: Human-readable text for LLM (keeping JSON for backwards compatibility but adding summary)
        if result.get("success"):
            files_created = result.get("output_files", [])
            if files_created:
                files_summary = "\n".join(
                    [f"  • {f['file_name']} at {f['file_path']}" for f in files_created]
                )
                summary = f"✅ Code executed successfully!\n\nCreated {len(files_created)} file(s):\n{files_summary}"
                if result.get("stdout"):
                    summary += f"\n\nOutput:\n{result['stdout']}"
                return summary

        # Fallback: return JSON for backwards compatibility
        return json.dumps(result, indent=2)

    return [execute_python_code]
