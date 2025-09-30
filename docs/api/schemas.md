## Schemas Overview

Data models define the observable state shared between the execution engine, manager,
and workers. The sections below highlight the most commonly used Pydantic models.

### Workflow

The `Workflow` model represents the full task graph, resources, and constraint state that
is passed to the execution engine.

::: manager_agent_gym.schemas.core.workflow.Workflow

### Task

Tasks are the atomic or composite units of work that make up a workflow. They contain
status, dependencies, and assignment metadata.

::: manager_agent_gym.schemas.core.tasks.Task

### Manager Observation

`ManagerObservation` describes what a manager sees at each timestep, including available
tasks, resources, and communications.

::: manager_agent_gym.schemas.execution.manager.ManagerObservation

### Preferences

`PreferenceWeights` encodes stakeholder priorities across objectives such as quality,
time, cost, and oversight.

::: manager_agent_gym.schemas.preferences.preference.PreferenceWeights

### Manager Actions

`ActionResult` captures the outcome of manager-issued actions, including validation
messages and state transitions.

::: manager_agent_gym.schemas.execution.manager_actions.ActionResult

