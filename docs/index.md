# Manager Agent Gym

<p align="center">
  <img src="docs/logo.png" alt="MA-Gym Logo" width="420" />
</p>

*A research platform for developing and evaluating autonomous agents that orchestrate complex workflows involving both human and AI collaborators*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**📚 Online Docs:** [deepflow-research.github.io/manager_agent_gym](https://deepflow-research.github.io/manager_agent_gym)

## 🎯 Overview
This repository contains the research platform and reference implementation for autonomous Manager Agents that orchestrate complex workflows with human and AI collaborators. For complete documentation, head to the docs below.

## 🏁 Run the Benchmark

Quick way to run the benchmark suite across scenarios using the CLI.

```bash
# Activate uv virtualenv (create it first if needed: `uv venv`)
source .venv/bin/activate

# From repo root, launch the interactive runner
python -m examples.cli

# Tip: non-interactive example
# python -m examples.cli --non-interactive --manager-mode cot --model-name o3 --max-timesteps 50
```

Outputs are written under directories like `simulation_outputs_cot_rerun/`, `simulation_outputs_random_rerun/`, etc., grouped by model.

The CLI entrypoint lives at `examples/cli.py`.

## 🧩 Key Concepts

- **worker**: A workflow-executing agent that performs tasks and produces resources. In code these implement `AgentInterface` (see `manager_agent_gym/core/workflow_agents/interface.py`). Workers can represent simulated humans or tool-using AIs.
- **manager**: The decision-making agent that observes the workflow each timestep and issues actions (e.g., assign, split, refine, message). See manager actions in `manager_agent_gym/schemas/execution/manager_actions.py` and manager agents under `manager_agent_gym/core/manager_agent/`.
- **task**: An atomic or composite unit of work with dependencies and inputs/outputs, modeled by `Task` (`manager_agent_gym/schemas/core/tasks.py`).
- **resource**: A digital artifact produced/consumed by tasks (documents, datasets, code), modeled by `Resource` (`manager_agent_gym/schemas/core/resources.py`).
- **workflow**: The container holding tasks, agents, resources, constraints, and messages; evolves over discrete timesteps. Modeled by `Workflow` (`manager_agent_gym/schemas/core/workflow.py`).
- **stakeholder**: The persona owning preferences and providing feedback/approvals; exposed to the manager via a public profile. See `StakeholderBase`/`StakeholderConfig` (`manager_agent_gym/core/workflow_agents/interface.py`, `manager_agent_gym/schemas/workflow_agents/stakeholder.py`).

## 🚀 Your First Manager Agent

```python
import asyncio
from manager_agent_gym import (
    create_toy_workflow_example,
    ChainOfThoughtManagerAgent,
    WorkflowExecutionEngine,
    AgentRegistry,
    PreferenceWeights,
    Preference,
)

def create_basic_preferences() -> PreferenceWeights:
    """Create simple preferences focused on quality and reasonable timelines."""
    return PreferenceWeights(
        preferences=[
            Preference(name="quality", weight=0.4, description="High-quality deliverables"),
            Preference(name="time", weight=0.3, description="Reasonable timeline"),
            Preference(name="cost", weight=0.2, description="Cost-effective execution"),
            Preference(name="oversight", weight=0.1, description="Manageable oversight"),
        ]
    )

async def main():
    # Create workflow and agent registry
    workflow = create_toy_workflow_example()
    agent_registry = AgentRegistry()
    
    # Register agents from the workflow
    for agent in workflow.agents.values():
        agent_registry.register_agent(agent)
    
    # Create manager agent with preferences
    preferences = create_basic_preferences()
    manager = ChainOfThoughtManagerAgent(
        preferences=preferences,
        model_name="o3",
        manager_persona="Organized Project Coordinator",
    )
    
    # Set up execution engine
    engine = WorkflowExecutionEngine(
        workflow=workflow,
        agent_registry=agent_registry,
        manager_agent=manager,
        max_timesteps=20,
        enable_timestep_logging=True,
    )
    
    # Run the workflow
    results = await engine.run_full_execution()
    
    print(f"Workflow completed: {workflow.is_complete()}")
    print(f"Total timesteps: {len(results)}")
    print(f"Tasks completed: {len(engine.completed_task_ids)}")

if __name__ == "__main__":
    asyncio.run(main())
```


## 📚 Documentation & Resources

- **Online Docs**: [https://deepflow-research.github.io/manager_agent_gym](https://deepflow-research.github.io/manager_agent_gym)
- **Repository Home**: [This repository](.)
- **Docs Home**: [docs/index.md](docs/index.md)
- **Quick Start**: [docs/QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md)
- **Library Guide**: [docs/LIBRARY_DOCUMENTATION.md](docs/LIBRARY_DOCUMENTATION.md)
- **Technical Architecture**: [docs/TECHNICAL_ARCHITECTURE.md](docs/TECHNICAL_ARCHITECTURE.md)
- **Build/Serve Docs**: [docs/README.md](docs/README.md)
- **Research Paper (PDF)**: [docs/Orchestrating_Human_AI_Teams__The_Manager_Agent_as_a_Unifying_Research_Challenge.pdf](docs/Orchestrating_Human_AI_Teams__The_Manager_Agent_as_a_Unifying_Research_Challenge.pdf)

## 🧪 Examples & Workflows

- Browse examples: [examples/](examples/)
- Getting started walkthrough: [examples/getting_started/README.md](examples/getting_started/README.md)
- End-to-end demos: [examples/end_to_end_examples/](examples/end_to_end_examples/)

## 📝 License

MIT License — see [LICENSE](LICENSE).

## 📖 Citation

If you use Manager Agent Gym in your work, please cite the accompanying paper:

Charlie Masters, Advaith Vellanki, Jiangbo Shangguan, Bart Kultys, Alastair Moore, Stefano V. Albrecht. "Orchestrating Human-AI Teams: The Manager Agent as a Unifying Research Challenge." In Proceedings of the International Conference on Distributed Artificial Intelligence (DAI 2025), London, United Kingdom. Available at `docs/Orchestrating_Human_AI_Teams__The_Manager_Agent_as_a_Unifying_Research_Challenge.pdf`.

```bibtex
@inproceedings{manager_agent_gym_2025,
  title     = {Orchestrating Human-AI Teams: The Manager Agent as a Unifying Research Challenge},
  author    = {Masters, Charlie and Vellanki, Advaith and Shangguan, Jiangbo and Kultys, Bart and Moore, Alastair and Albrecht, Stefano V.},
  booktitle = {Proceedings of the International Conference on Distributed Artificial Intelligence (DAI 2025)},
  year      = {2025},
  address   = {London, United Kingdom},
  note      = {Manager Agent Gym},
  url       = {docs/Orchestrating_Human_AI_Teams__The_Manager_Agent_as_a_Unifying_Research_Challenge.pdf}
}
```

—

Manager Agent Gym: Where AI learns to manage complex work in realistic environments.