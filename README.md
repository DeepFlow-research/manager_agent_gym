# Manager Agent Gym

![DeepFlow Logo](docs/logo.png)

*A research platform for developing and evaluating autonomous agents that orchestrate complex workflows involving both human and AI collaborators*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview
This repository contains the research platform and reference implementation for autonomous Manager Agents that orchestrate complex workflows with human and AI collaborators. For complete documentation, head to the docs below.

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

Charlie Masters, Advaith Vellanki, Jiangbo Shangguan, Bart Kultys, Alastair Moore, Stefano V. Albrecht. "Orchestrating Human-AI Teams: The Manager Agent as a Unifying Research Challenge." DeepFlow, London, United Kingdom, 2025. Available at `docs/Orchestrating_Human_AI_Teams__The_Manager_Agent_as_a_Unifying_Research_Challenge.pdf`.

```bibtex
@misc{manager_agent_gym_2025,
  title        = {Orchestrating Human-AI Teams: The Manager Agent as a Unifying Research Challenge},
  author       = {Masters, Charlie and Vellanki, Advaith and Shangguan, Jiangbo and Kultys, Bart and Moore, Alastair and Albrecht, Stefano V.},
  howpublished = {DeepFlow Whitepaper},
  year         = {2025},
  note         = {Manager Agent Gym},
  url          = {docs/Orchestrating_Human_AI_Teams__The_Manager_Agent_as_a_Unifying_Research_Challenge.pdf}
}
```

—

Manager Agent Gym: Where AI learns to manage complex work in realistic environments.