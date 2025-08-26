# Manager Agent Gym

*A research platform for developing and evaluating autonomous agents that orchestrate complex workflows involving both human and AI collaborators*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

Manager Agent Gym implements the **Autonomous Manager Agent** research challenge described in ["Orchestrating Human-AI Teams: The Manager Agent as a Unifying Research Challenge for Distributed AI"](paper.md). This platform provides a complete implementation of the formal POSG (Partially Observable Stochastic Game) framework for building and evaluating autonomous workflow management systems.

### What is the Manager Agent Challenge?

The Manager Agent is an autonomous entity responsible for end-to-end management of complex workflows within dynamic, multi-agent environments. It must:

- 🧩 **Decompose complex goals** into executable task graphs using hierarchical reasoning
- ⚖️ **Balance competing objectives** (cost, quality, time) under changing preferences  
- 🤝 **Coordinate ad hoc teams** of human and AI workers without prior joint training
- 📋 **Maintain governance compliance** while adapting to evolving constraints

This challenge serves as a unifying research problem that bridges multiple AI sub-fields: multi-agent coordination, compositional reasoning, preference learning, and AI governance.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/manager-agent-gym
cd manager-agent-gym

# Install in development mode
pip install -e .

# Configure API keys
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

### Your First Manager Agent

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

## 📚 Documentation

> **📄 Paper Documentation**: Academic research documentation and guides can be found in `/docs`

### Quick Start & Library Guides

- **[Quick Start Guide](docs/QUICK_START_GUIDE.md)** - Get up and running in 10 minutes
- **[Library Documentation](docs/LIBRARY_DOCUMENTATION.md)** - Comprehensive library overview
- **[Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)** - Deep dive into system design

### For Different Audiences

- **[Researchers](docs/RESEARCH_GUIDE.md)** - Implementation guide for the four research challenges
- **[Developers](docs/DEVELOPER_GUIDE.md)** - API reference and integration examples
- **[Examples](docs/EXAMPLES.md)** - Progressive tutorials from basic to advanced usage

### Key Concepts

- POSG Framework overview is covered in **[Simulator Architecture](docs/SIMULATOR_ARCHITECTURE.md)**
- Manager Agents: see `manager_agent_gym/core/manager_agent/` and **[Developer Guide](docs/DEVELOPER_GUIDE.md)**
- Worker Agents: see `manager_agent_gym/core/workflow_agents/` and **[Developer Guide](docs/DEVELOPER_GUIDE.md)**
- **[Evaluation Guide](docs/EVALUATION_GUIDE.md)** - Comprehensive multi-objective evaluation framework

### Technical Documentation

- **[API Reference](docs/API.md)** - Complete API documentation with evaluation system
- **[Simulator Architecture](docs/SIMULATOR_ARCHITECTURE.md)** - Technical specification of the simulation environment
- **[Paper Context Summary](docs/PAPER_CONTEXT_SUMMARY.md)** - Context for research paper revision

## 🧩 Core Architecture

### POSG Implementation

The system implements the formal framework `⟨I, S, b⁰, {Aᵢ}, {Oᵢ}, P, {Rᵢ}⟩`:

- **I (Agents)**: Manager + Worker agent implementations
- **S (State)**: `Workflow` containing tasks, resources, agents, messages  
- **Aᵢ (Actions)**: `BaseManagerAction` hierarchy for manager decisions
- **Oᵢ (Observations)**: `ManagerObservation` for partial state visibility
- **P (Transitions)**: `WorkflowExecutionEngine` manages state evolution
- **Rᵢ (Rewards)**: Multi-objective evaluation via `ValidationEngine` and regret analysis

### Module Organization

```
manager_agent_gym/
├── core/                   # Core implementations
│   ├── manager_agent/         # Manager agent implementations
│   ├── workflow_agents/       # Worker agent implementations  
│   ├── execution/            # Workflow execution engine
│   └── evaluation/           # Validation and regret calculation
├── schemas/                # Data models and type definitions
│   ├── core/                 # POSG state components
│   ├── execution/            # Runtime state and actions
│   └── evaluation/           # Success criteria and metrics
└── examples/               # Progressive tutorials and demos
```

## 🔬 Research Applications

### Four Foundational Challenges

1. **[Hierarchical Task Decomposition](docs/CHALLENGE_1_DECOMPOSITION.md)**
   - Moving beyond pattern matching to compositional reasoning
   - Systematic hierarchical planning for novel scenarios

2. **[Multi-Objective Optimization](docs/CHALLENGE_2_PREFERENCES.md)**  
   - Balancing competing objectives under non-stationary preferences
   - Adaptation without costly retraining

3. **[Ad Hoc Team Coordination](docs/CHALLENGE_3_COORDINATION.md)**
   - Orchestrating heterogeneous teams without prior coordination
   - Dynamic capability inference and role assignment

4. **[Governance by Design](docs/CHALLENGE_4_GOVERNANCE.md)**
   - Maintaining compliance across dynamic workflows
   - Interpretable natural language constraint handling

### Evaluation Framework

The platform implements the comprehensive evaluation methodology from the research paper:

- **Workflow-Level Quality**: Task completion, coordination efficiency, resource optimization
- **Compliance & Human-Centric**: Oversight burden, governance adherence, transparency
- **Preference Adherence**: Multi-objective regret analysis under preference changes

## 🎓 Examples & Tutorials

### Progressive Learning Path

1. Getting Started: `examples/getting_started/`
2. Timestep Evaluation: `examples/timestep_evaluation_demo.py`
3. Comprehensive Research Demo: `examples/comprehensive_research_demo.py`
4. ICAAP Demo: `examples/icaap_demo.py`

### Featured Examples

- **Hello World Manager** - Your first autonomous manager agent
- **Custom Validation Rules** - Flexible success criteria definition
- **Dynamic Preference Adaptation** - Handling changing objectives
- **Structured Manager Agent** - LLM-based autonomous management
- **Workflow Decomposition Challenge** - Hierarchical reasoning research

## 🔧 Key Features

### Manager Agent Capabilities

- **Structured Decision Making**: LLM-based reasoning with action constraints
- **Dynamic Planning**: Real-time task creation, modification, and assignment
- **Multi-Objective Optimization**: Preference-aware decision making
- **Team Coordination**: Heterogeneous human-AI team management
- **Governance Integration**: Built-in compliance and transparency

### Worker Agent Types

- **AI Agents**: LLM-based task execution with tool integration
- **Human Agents**: Realistic human simulation with noise modeling
- **Custom Agents**: Extensible interface for specialized implementations

### Evaluation Tools

- **Validation Engine**: Flexible rule-based success criteria
- **Regret Calculator**: Multi-objective performance analysis
- **Preference Dynamics**: Non-stationary objective modeling
- **Comprehensive Metrics**: From coordination efficiency to human oversight

## 🤝 Contributing

We welcome contributions from the research community! See our [Contributing Guide](CONTRIBUTING.md) for details on:

- Implementing new manager agent architectures
- Adding evaluation metrics and benchmarks
- Creating examples and documentation
- Reporting bugs and requesting features


## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.
---

**Manager Agent Gym**: *Where AI learns to manage complex work in realistic environments.*