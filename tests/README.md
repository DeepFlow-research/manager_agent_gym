## Test Suite Overview

This directory contains unit and integration tests for `manager_agent_gym`. The tests aim to cover the core workflow engine, manager actions, communication layer, validation pipeline, and preference dynamics using fast, deterministic stubs (no network calls).

### Structure

- `conftest.py`: Adds the project root to `sys.path` so test imports work consistently.
- `integration/`
  - `test_engine_e2e.py`: End‑to‑end execution of the `WorkflowExecutionEngine` over multiple timesteps using stub agents/managers. Ensures terminal states, logging, and validations complete.
- Unit tests (top‑level):
  - `test_agent_registry.py`: Agent registration and retrieval semantics.
  - `test_communication_graph.py`: Message routing, multicast, threads, read tracking, and analytics.
  - `test_communication_service.py`: Public API for sending/broadcasting messages and querying views.
  - `test_engine_coordination_prefdyn.py`: Agent coordination and scheduled preference dynamics.
  - `test_engine_errors.py`: Defensive checks and failure modes in the execution engine.
  - `test_engine_outputs.py`: Engine output payloads, per‑timestep results, and metrics.
  - `test_manager_actions.py`: Mutation actions (create/assign/refine/dependency management).
  - `test_manager_factory.py`: Manager factory construction and defaults.
  - `test_manager_info_actions.py`: Read‑only info actions and expected payload shapes.
  - `test_manager_llm_fallbacks.py`: Graceful fallbacks and structured responses for LLM validators.
  - `test_manager_observation.py`: Observation composition and fields available to the manager.
  - `test_preferences.py`: Preference models and helpers.
  - `test_random_manager_agent.py`: Baseline manager behavior.
  - `test_validation_engine.py`: Validation engine orchestration and result aggregation.
  - `test_validation_frequency.py`: Frequency gating for validations (every timestep vs on completion).
  - `test_workflow_core.py`: Core workflow/Task semantics and readiness logic.
  - `test_workflow_evaluator.py`: Evaluation helpers around regret and category scoring.

### How to Run

From the repository root:

```bash
pytest -q
```

Most tests use `pytest.mark.asyncio` and rely on the default event loop. No external services are required.

### Assumptions and Test Doubles

- LLM calls are not made in unit tests. Where LLM‑based validators exist, they are exercised through stubbed or function‑based validators. The suite validates that the engine orchestrates validations, not model quality.
- Communication tests use the in‑memory `CommunicationService` and `CommunicationGraph` only.
- The execution engine tests rely on stub `AgentInterface` and `ManagerAgent` implementations to ensure determinism and speed.

### Limitations

- No network I/O or real LLM integrations are exercised; behavior is verified via functional validators and structure of results. Real provider errors, rate limits, and latency are out of scope.
- Performance, concurrency races, and stress scenarios are lightly covered. The suite uses small synthetic workflows; it does not simulate heavy loads.
- Compatibility is targeted at the library’s public Python API. CLI/long‑running demo scripts under `examples/` are not exercised by default.
- Visualization and plotting scripts are not tested.

### Conventions

- Tests prefer deterministic inputs and avoid time‑based flakiness.
- Assertions focus on public behavior and serialized payload shapes, not private internals.
- If adding tests that require asynchronous fixtures, set explicit loop scope in the fixture to avoid `pytest-asyncio` deprecation warnings.

### Troubleshooting

- If imports fail, ensure the project root is on `PYTHONPATH` (handled by `conftest.py`).
- If new actions or payloads are added, keep response keys backward‑compatible where tests assert on specific shapes (e.g., `available_agents`).


