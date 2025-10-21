import pytest
from uuid import uuid4
from typing import Any

from manager_agent_gym.core.agents.workflow_agents.common.interface import (
    AgentInterface,
)
from manager_agent_gym.schemas.agents import AgentConfig
from manager_agent_gym.schemas.domain import Task, Resource
from manager_agent_gym.core.execution.schemas.results import (
    ExecutionResult,
    create_task_result,
)
from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.core.workflow.services import WorkflowMutations
from manager_agent_gym.schemas.domain.task import Task as WorkflowTask
from manager_agent_gym.core.agents.stakeholder_agent.stakeholder_agent import (
    StakeholderAgent,
)
from manager_agent_gym.schemas.agents.stakeholder import StakeholderConfig
from manager_agent_gym.schemas.preferences.preference import PreferenceSnapshot
from manager_agent_gym.core.workflow.schemas.config import OutputConfig


class MockConfig(AgentConfig):
    agent_id: str
    agent_type: str
    system_prompt: str | None = None


class DummyAI(AgentInterface[MockConfig]):
    def __init__(self, agent_id: str = "ai_dummy") -> None:
        super().__init__(
            MockConfig(
                agent_id=agent_id,
                agent_type="ai",
                system_prompt="dummy system prompt",
                agent_description="dummy ai agent",
                agent_capabilities=["dummy ai agent"],
            )
        )

    async def execute_task(
        self, task: Task, resources: list[Resource]
    ) -> ExecutionResult:
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.0,
            resources=[],
            cost=0.0,
            simulated_duration_hours=0.0,
        )


class DummyHuman(AgentInterface[MockConfig]):
    def __init__(self, agent_id: str = "human_dummy") -> None:
        super().__init__(
            MockConfig(
                agent_id=agent_id,
                agent_type="human_mock",
                system_prompt="dummy system prompt",
                model_name="o3",
                agent_description="dummy human agent",
                agent_capabilities=["dummy human agent"],
            )
        )

    async def execute_task(
        self, task: Task, resources: list[Resource]
    ) -> ExecutionResult:
        return create_task_result(
            task_id=task.id,
            agent_id=self.agent_id,
            success=True,
            execution_time=0.0,
            resources=[],
            cost=0.0,
            simulated_duration_hours=0.0,
        )


# CLI options / marks
def pytest_addoption(parser: pytest.Parser) -> None:  # pragma: no cover
    parser.addoption(
        "--fast",
        action="store_true",
        default=False,
        help="Skip tests that call live LLMs (marked live_llm)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:  # pragma: no cover
    if config.getoption("--fast"):
        skip_live = pytest.mark.skip(reason="--fast: skipping live LLM tests")
        for item in items:
            if "live_llm" in item.keywords:
                item.add_marker(skip_live)


def pytest_configure(config: pytest.Config) -> None:  # pragma: no cover
    config.addinivalue_line(
        "markers",
        "live_llm: marks tests that call live LLMs (skipped with --fast)",
    )


# Shared fixtures / factories


@pytest.fixture
def empty_workflow() -> Workflow:
    return Workflow(name="test_workflow", workflow_goal="desc", owner_id=uuid4())


@pytest.fixture
def workflow_two_step() -> Workflow:
    w = Workflow(name="w", workflow_goal="d", owner_id=uuid4())
    a = WorkflowTask(name="A", description="d")
    b = WorkflowTask(name="B", description="d", dependency_task_ids=[a.id])
    WorkflowMutations.add_task(w, a)
    WorkflowMutations.add_task(w, b)
    return w


@pytest.fixture
def stakeholder_agent_empty_prefs() -> StakeholderAgent:
    cfg = StakeholderConfig(
        agent_id="stakeholder",
        agent_type="stakeholder",
        system_prompt="Stakeholder",
        model_name="o3",
        name="Stakeholder",
        role="Owner",
        preference_data=PreferenceSnapshot(preferences=[]),
        agent_description="Stakeholder",
        agent_capabilities=["Stakeholder"],
    )
    return StakeholderAgent(config=cfg)


@pytest.fixture
def output_config(tmp_path: Any) -> OutputConfig:
    return OutputConfig(base_output_dir=tmp_path, create_run_subdirectory=False)


@pytest.fixture
def dummy_ai_agent() -> DummyAI:
    return DummyAI()


@pytest.fixture
def dummy_human_agent() -> DummyHuman:
    return DummyHuman()
