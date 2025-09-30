## Execution Models

Execution-level data structures track state transitions, observations, and action
results as the engine runs.

### Manager Observation

`ManagerObservation` captures the partial view presented to the manager each timestep.

::: manager_agent_gym.schemas.execution.manager.ManagerObservation

### Execution State

`ExecutionState` contains bookkeeping information about the current timestep, finished
tasks, and overall workflow status.

::: manager_agent_gym.schemas.execution.state.ExecutionState

### Manager Action Result

`ActionResult` records validation feedback and side effects produced by manager actions.

::: manager_agent_gym.schemas.execution.manager_actions.ActionResult

