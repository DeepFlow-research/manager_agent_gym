import pytest
from manager_agent_gym.core.workflow_agents.interface import AgentInterface
from manager_agent_gym.schemas.workflow_agents import AgentConfig
from manager_agent_gym.schemas.core import Task, Resource
from manager_agent_gym.schemas.unified_results import (
    ExecutionResult,
    create_task_result,
)


class MockConfig(AgentConfig):
    agent_id: str
    agent_type: str
    system_prompt: str


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


@pytest.fixture
def dummy_ai_agent() -> DummyAI:
    return DummyAI()


@pytest.fixture
def dummy_human_agent() -> DummyHuman:
    return DummyHuman()
