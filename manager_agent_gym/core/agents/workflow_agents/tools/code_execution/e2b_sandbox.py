"""E2B sandbox integration for secure code execution."""

from typing import Any
from pathlib import Path
from e2b_code_interpreter.code_interpreter_async import AsyncSandbox


class E2BSandboxExecutor:
    """Manages E2B sandbox execution."""

    def __init__(
        self,
        api_key: str | None = None,
        input_files: list[str] | None = None,
        output_dir: str | None = None,
    ):
        """
        Initialize E2B executor.

        Args:
            api_key: E2B API key (if None, loads from environment)
            input_files: List of local file paths to upload to sandbox (deprecated - use context-based isolation)
            output_dir: Directory to download sandbox outputs to (if None, uses temp directory)
        """
        self.api_key = api_key
        self._sandbox = None
        self.output_dir = output_dir

        # State isolation per agent/task to prevent cross-contamination
        # Key format: f"{agent_id}:{task_id}"
        self._state_per_context: dict[str, dict[str, Any]] = {}
        self.path_mapping: dict[str, str] = {}  # Maps local paths to sandbox paths

    async def execute_python(
        self,
        code: str,
        timeout_seconds: int = 30,
        upload_files: bool = True,
        context_key: str | None = None,
        input_files: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute Python code in E2B sandbox with state isolation.

        Args:
            code: Python code to execute
            timeout_seconds: Execution timeout
            upload_files: Whether to upload input files
            context_key: Context key for state isolation (format: "agent_id:task_id")
            input_files: List of input file paths to upload (overrides context state)

        Returns:
            Dictionary with stdout, stderr, exit_code, error, and output_files
        """
        sandbox = None
        try:
            # Create sandbox
            sandbox = await AsyncSandbox.create(
                api_key=self.api_key, timeout=timeout_seconds
            )

            # Install packages needed for GDPEval business/professional tasks
            # Kept minimal for fast installation (<10s) on every code execution
            # Base E2B already has: numpy, pandas, matplotlib, scikit-learn, scipy, requests
            await sandbox.commands.run(
                "pip install -q openpyxl xlsxwriter python-docx statsmodels seaborn plotly"
            )

            # Get or initialize state for this context
            if context_key and context_key not in self._state_per_context:
                self._state_per_context[context_key] = {"input_files": []}

            # Determine which files to upload
            if input_files is not None:
                # Explicit input_files provided - use those
                files_to_upload = input_files
            elif context_key and self._state_per_context[context_key]["input_files"]:
                # Use accumulated files from previous executions in this context
                files_to_upload = self._state_per_context[context_key]["input_files"]
            else:
                # No files to upload
                files_to_upload = []

            # Upload input files to sandbox working directory
            self.path_mapping = {}  # Reset mapping for each execution
            if upload_files and files_to_upload:
                for local_path in files_to_upload:
                    if Path(local_path).exists():
                        # Map to sandbox working directory preserving filename
                        # E2B sandbox working directory is /home/user
                        filename = Path(local_path).name
                        sandbox_path = f"/home/user/{filename}"

                        # Store mapping for potential path rewriting
                        self.path_mapping[local_path] = sandbox_path

                        # Upload file to sandbox working directory
                        with open(local_path, "rb") as f:
                            file_data = f.read()
                        await sandbox.files.write(sandbox_path, file_data)

            # Rewrite code to use sandbox paths
            rewritten_code = code
            for local_path, sandbox_path in self.path_mapping.items():
                # Replace absolute paths in code with sandbox paths
                rewritten_code = rewritten_code.replace(local_path, sandbox_path)

            # Execute rewritten code with mapped paths
            execution = await sandbox.run_code(
                rewritten_code, language="python", timeout=timeout_seconds
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

            # Download any output files created in sandbox
            downloaded_files = await self._download_sandbox_outputs(sandbox)

            # Add downloaded files to context state for next execution (iterative workflow support)
            # This allows subsequent calls to access files created in previous calls
            # But only within the same agent+task context (prevents cross-contamination)
            if context_key:
                for file_info in downloaded_files:
                    if (
                        file_info["file_path"]
                        not in self._state_per_context[context_key]["input_files"]
                    ):
                        self._state_per_context[context_key]["input_files"].append(
                            file_info["file_path"]
                        )

            return {
                "success": error_msg is None,
                "stdout": "\n".join(stdout_parts),
                "stderr": "\n".join(stderr_parts),
                "exit_code": 0 if error_msg is None else 1,
                "error": error_msg,
                "output_files": downloaded_files,
            }

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "error": f"Execution error: {str(e)}",
                "output_files": [],
            }
        finally:
            # Ensure sandbox is properly closed
            if sandbox is not None:
                await sandbox.kill()

    async def _download_sandbox_outputs(
        self, sandbox: AsyncSandbox
    ) -> list[dict[str, Any]]:
        """
        Download files created in the sandbox working directory.

        Args:
            sandbox: Active E2B sandbox instance

        Returns:
            List of dicts with info about downloaded files (file_path, file_name, size_bytes)
        """
        downloaded_files: list[dict[str, Any]] = []

        try:
            # List all files in sandbox working directory
            result = await sandbox.commands.run("ls -la /home/user/")

            if result.exit_code != 0:
                return downloaded_files

            # Get uploaded filenames to exclude them from downloads
            uploaded_filenames = {Path(sp).name for sp in self.path_mapping.values()}

            # System files to skip (already in sandbox, not user-created)
            system_files = {".bash_logout", ".bashrc", ".profile", ".bash_history"}

            # Parse ls output to find new files
            # ls -la output format: permissions links owner group size month day time filename
            for line in result.stdout.split("\n"):
                line = line.strip()
                if not line or line.startswith("total") or line.startswith("d"):
                    continue  # Skip directory entries and header

                parts = line.split()
                if len(parts) < 9:
                    continue

                filename = " ".join(parts[8:])  # Handle filenames with spaces

                # Skip . and .., uploaded files, and system files
                if (
                    filename in (".", "..")
                    or filename in uploaded_filenames
                    or filename in system_files
                ):
                    continue

                # This is a new file created by the code - download it
                sandbox_path = f"/home/user/{filename}"

                try:
                    # Determine output directory
                    import tempfile

                    if self.output_dir:
                        output_dir = Path(self.output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                    else:
                        output_dir = Path(tempfile.mkdtemp(prefix="e2b_output_"))

                    # Determine MIME type and whether file is binary
                    mime_type = self._guess_mime_type(filename)
                    is_binary = self._is_binary_mime_type(mime_type)

                    # Read file from sandbox with appropriate format
                    # Binary files MUST be read with format="bytes" to avoid corruption
                    if is_binary:
                        file_content = await sandbox.files.read(
                            sandbox_path, format="bytes"
                        )
                    else:
                        # Text files can be read as text (default)
                        file_content = await sandbox.files.read(sandbox_path)

                    # Save to local file
                    local_path = output_dir / filename
                    if is_binary:
                        # Binary files: write as bytes (bytearray from E2B)
                        if isinstance(file_content, (bytes, bytearray)):
                            local_path.write_bytes(file_content)
                        else:
                            print(
                                f"Warning: Expected bytes for binary file {filename}, got {type(file_content)}. Skipping."
                            )
                            continue
                    else:
                        # Text files: handle both str and bytes
                        if isinstance(file_content, bytes):
                            local_path.write_bytes(file_content)
                        else:
                            local_path.write_text(str(file_content), encoding="utf-8")

                    downloaded_files.append(
                        {
                            "file_path": str(local_path.absolute()),
                            "file_name": filename,
                            "size_bytes": local_path.stat().st_size,
                            "mime_type": mime_type,
                        }
                    )

                except Exception as e:
                    # Log error but continue with other files
                    print(f"Warning: Could not download {filename}: {e}")
                    continue

        except Exception as e:
            # If anything fails, just return empty list (don't break execution)
            print(f"Warning: Error downloading sandbox outputs: {e}")

        return downloaded_files

    def _guess_mime_type(self, filename: str) -> str:
        """Guess MIME type from file extension."""
        ext = Path(filename).suffix.lower()
        mime_map = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".csv": "text/csv",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".html": "text/html",
            ".xml": "application/xml",
            ".zip": "application/zip",
        }
        return mime_map.get(ext, "application/octet-stream")

    def _is_binary_mime_type(self, mime_type: str) -> bool:
        """Check if MIME type indicates a binary file."""
        # Text MIME types
        text_prefixes = ("text/", "application/json", "application/xml")
        if mime_type.startswith(text_prefixes):
            return False

        # Everything else is binary (images, Excel, PDF, Word, ZIP, etc.)
        return True

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
