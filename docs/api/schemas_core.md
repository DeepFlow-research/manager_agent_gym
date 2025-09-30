## Core Models

Fundamental Pydantic models representing the workflow state machine.

### Workflow

High-level container for tasks, resources, agents, and governance constraints.

::: manager_agent_gym.schemas.core.workflow.Workflow

### Task

Individual work items with dependencies, status, and assignment metadata.

::: manager_agent_gym.schemas.core.tasks.Task

### Resource

Artifacts produced or consumed by tasks while a workflow executes.

::: manager_agent_gym.schemas.core.resources.Resource

### Message

Structured communications exchanged between agents and stakeholders.

::: manager_agent_gym.schemas.core.communication.Message

