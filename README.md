# Manager Agent Gym

<p align="center">
  <img src="docs/logo.png" alt="MA-Gym Logo" width="420" />
</p>

*A research platform for developing and evaluating autonomous Manager Agents that orchestrate complex workflows involving both human and AI collaborators*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**📚 Online Docs:** [deepflow-research.github.io/manager_agent_gym](https://deepflow-research.github.io/manager_agent_gym)

## 🎯 Overview
This repository contains the research codebase and reference implementation for autonomous Manager Agents that orchestrate complex workflows with human and AI collaborators, as described in our recent paper ["Orchestrating Human-AI Teams: The Manager Agent as a Unifying Research Challenge"](arxivLink) published in [DAI 2025](https://www.adai.ai/dai/2025). For complete documentation, head to the docs below.

## 🏁 Run the Benchmark

Quick way to run the benchmark suite across workflow scenarios using the CLI.

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

The easiest way to launch a working manager agent is the `hello_manager_agent.py` example. Run:

```bash
python examples/getting_started/hello_manager_agent.py
```

That script builds an `ICAAP` workflow, registers the agents, and executes a `ChainOfThoughtManagerAgent` using your configured model (default `gpt-4o-mini`).


## 📚 Documentation & Resources

- **Online Docs**: [https://deepflow-research.github.io/manager_agent_gym](https://deepflow-research.github.io/manager_agent_gym)
- **Repository Home**: [This repository](.)
- **Docs Home**: [docs/index.md](https://deepflow-research.github.io/manager_agent_gym/)
- **Quick Start**: [Quick Start Guide](https://deepflow-research.github.io/manager_agent_gym/QUICK_START_GUIDE/)
- **Library Guide**: [Library Documentation](https://deepflow-research.github.io/manager_agent_gym/LIBRARY_DOCUMENTATION/)
- **Technical Architecture**: [Technical Architecture](https://deepflow-research.github.io/manager_agent_gym/TECHNICAL_ARCHITECTURE/)
- **Research Paper (PDF)**: [Orchestrating Human-AI Teams (PDF)](https://www.arxiv.org/abs/2510.02557)

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
  url       = {(https://www.arxiv.org/abs/2510.02557)}
}
```
