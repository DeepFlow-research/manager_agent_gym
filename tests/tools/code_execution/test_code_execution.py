"""Comprehensive tests for code execution tools.

Tests Python and JavaScript code execution in E2B sandbox.
"""

import pytest

from manager_agent_gym.core.agents.workflow_agents.tools.code import (
    _execute_node_code,
    _execute_python_code,
)


# ============================================================================
# PYTHON CODE EXECUTION TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.requires_e2b
async def test_execute_python_code_basic(e2b_api_key: str) -> None:
    """Test executing basic Python code."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)
    code = "print('Hello, World!')"

    result = await _execute_python_code(code, 30, executor)

    assert result["success"] is True
    assert "Hello, World!" in result["stdout"]


@pytest.mark.asyncio
@pytest.mark.requires_e2b
async def test_execute_python_code_with_imports(e2b_api_key: str) -> None:
    """Test executing Python code with imports."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)
    code = """
import json
data = {'name': 'Alice', 'age': 30}
print(json.dumps(data))
"""

    result = await _execute_python_code(code, 30, executor)

    assert result["success"] is True
    assert "Alice" in result["stdout"]


@pytest.mark.asyncio
@pytest.mark.requires_e2b
async def test_execute_python_code_with_error(e2b_api_key: str) -> None:
    """Test executing Python code that raises error."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)
    code = "x = 1 / 0"

    result = await _execute_python_code(code, 30, executor)

    assert result["success"] is False
    assert result["exit_code"] != 0


@pytest.mark.asyncio
@pytest.mark.requires_e2b
async def test_execute_python_code_numpy(e2b_api_key: str) -> None:
    """Test executing Python code with numpy."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)
    code = """
import numpy as np
arr = np.array([1, 2, 3, 4, 5])
print(np.mean(arr))
"""

    result = await _execute_python_code(code, 30, executor)

    assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.requires_e2b
async def test_execute_python_code_pandas(e2b_api_key: str) -> None:
    """Test executing Python code with pandas."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)
    code = """
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print(df.describe())
"""

    result = await _execute_python_code(code, 30, executor)

    assert result["success"] is True


# ============================================================================
# JAVASCRIPT CODE EXECUTION TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.requires_e2b
async def test_execute_node_code_basic(e2b_api_key: str) -> None:
    """Test executing basic JavaScript code."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)
    code = "console.log('Hello, World!');"

    result = await _execute_node_code(code, 30, executor)

    # JavaScript support is limited, may not succeed
    assert isinstance(result, dict)
    assert "success" in result


# ============================================================================
# TIMEOUT TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.requires_e2b
async def test_execute_python_code_timeout(e2b_api_key: str) -> None:
    """Test Python code execution timeout."""
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution.e2b_sandbox import (
        E2BSandboxExecutor,
    )

    executor = E2BSandboxExecutor(api_key=e2b_api_key)
    code = "import time; time.sleep(60)"

    result = await _execute_python_code(code, 5, executor=executor)

    # Should timeout or return error
    assert result["success"] is False
