from manager_agent_gym.core.workflow_agents.registry import AgentRegistry
from manager_agent_gym.core.workflow_agents.interface import AgentInterface
from manager_agent_gym.schemas.workflow_agents import AgentConfig
from manager_agent_gym.schemas.core import Task, Resource
from manager_agent_gym.schemas.unified_results import (
    ExecutionResult,
    create_task_result,
)


def test_register_and_list_agents() -> None:
    class MockConfig(AgentConfig):
        agent_id: str
        agent_type: str
        system_prompt: str = "dummy system prompt"
        model_name: str = "o3"

    class _A(AgentInterface[MockConfig]):
        def __init__(self, aid: str, atype: str) -> None:
            super().__init__(
                MockConfig(
                    agent_id=aid,
                    agent_type=atype,
                    system_prompt="dummy prompt",
                    model_name="o3",
                    agent_description="dummy agent",
                    agent_capabilities=["dummy agent"],
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

    reg = AgentRegistry()

    a1 = _A("a1", "ai")
    a2 = _A("a2", "human_mock")

    reg.register_agent(a1)
    reg.register_agent(a2)

    agents = reg.list_agents()
    assert len(agents) == 2
    assert {a.agent_id for a in agents} == {"a1", "a2"}
