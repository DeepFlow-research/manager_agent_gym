# Manager Agent Gym - Comprehensive Library Documentation

*Version 0.1.0*

## 🎯 Executive Summary

**Manager Agent Gym** is a research platform for developing and evaluating autonomous agents that orchestrate complex workflows involving both human and AI collaborators. The library implements the **Autonomous Manager Agent** research challenge as described in the accompanying [research paper](https://arxiv.org/abs/2510.02557), providing a complete POSG (Partially Observable Stochastic Game) framework for building and evaluating autonomous workflow management systems.

### Key Capabilities

- **🧩 Hierarchical Task Decomposition**: AI managers break down complex goals into executable task graphs using structured reasoning
- **⚖️ Multi-Objective Optimization**: Balance competing objectives (cost, quality, time, oversight) under dynamic preferences  
- **🤝 Ad Hoc Team Coordination**: Orchestrate mixed human and AI teams without prior joint training
- **📋 Governance Compliance**: Maintain regulatory compliance while adapting to evolving constraints
- **🔬 Research Evaluation**: Comprehensive evaluation framework with multi-objective regret analysis

## 🏗️ Core Architecture

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
│   ├── evaluation/           # Validation and regret calculation
│   ├── communication/        # Agent communication system
│   ├── decomposition/        # Task decomposition services
│   └── common/              # Shared utilities and LLM interface
├── schemas/                # Data models and type definitions
│   ├── core/                 # POSG state components
│   ├── execution/            # Runtime state and actions
│   ├── evaluation/           # Success criteria and metrics
│   ├── preferences/          # Preferences and evaluators
│   └── workflow_agents/      # Agent configurations and outputs
└── examples/               # Progressive tutorials and demos
```

## 💡 Key Concepts

### Manager Agents

AI agents that observe workflow state and make strategic decisions:
- **Assign tasks** to specialized agents
- **Create new tasks** when needed through decomposition
- **Monitor progress** and adapt to changes
- **Balance multiple preferences** (quality, time, cost, oversight)
- **Communicate with stakeholders** to clarify requirements

**Available Implementations:**
- `ChainOfThoughtManagerAgent`: LLM-based structured decision making with constrained action generation
- `RandomManagerAgentV2`: Baseline random action selection for comparison
- `OneShotDelegateManagerAgent`: Simple assignment-only manager

### Workflow Agents (Workers)

Specialized agents that execute tasks:
- **AIAgent**: LLM-based task execution with structured tools and OpenAI Agents SDK
- **MockHumanAgent**: Realistic human simulation with noise modeling and capacity constraints
- **StakeholderAgent**: Represents stakeholders who provide requirements and feedback

### Workflows

Collections of interconnected tasks with:
- **Task dependencies** and hierarchical subtask structures
- **Resource requirements** and outputs
- **Regulatory constraints** and governance rules
- **Mixed human and AI agent teams**
- **Communication history** and coordination state

### Execution Engine

The simulation environment that:
- **Runs discrete timesteps** with manager observation and action phases
- **Manages task execution** asynchronously across multiple agents
- **Tracks comprehensive metrics** for evaluation
- **Handles preference dynamics** and stakeholder updates
- **Provides callbacks** for custom monitoring and analysis

### Evaluation Framework

Comprehensive multi-objective evaluation including:
- **Preference adherence** via rubric-based scoring
- **Constraint compliance** validation
- **Workflow quality metrics** (completion rate, coordination efficiency)
- **Human-centric metrics** (oversight burden, transparency)
- **Regret analysis** for multi-objective optimization

## 🚀 Installation & Setup

### Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- OpenAI API key (for LLM-based agents)
- Optional: Anthropic API key for Claude models

### Installation

```bash
# Clone the repository
git clone https://github.com/DeepFlow-research/manager_agent_gym
cd manager_agent_gym

# Install with uv (recommended)
uv pip install -e .

# Install provider integrations (LLM + agents tooling)
uv pip install -e ".[openai,agents]"

# Alternative: Install with pip
pip install -e ".[openai,agents]"

# Configure API keys
cp .env.example .env
# Edit .env file with your API keys:
# OPENAI_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key-here  # Optional
```

> **Note**: The library uses `pydantic-settings` which automatically loads configuration from the `.env` file.

### Dependencies

Key dependencies include:
- `pydantic` (2.10.5+): Type validation and data models
- `openai` (1.58.0+): LLM inference
- `litellm` (1.60.8+): Multi-model LLM interface
- `openai-agents` (0.2.4+): Structured agent execution
- `fastapi` (0.115.7+): Optional web interfaces
- `rich` (13.9.4+): Console output formatting
- `typer` (0.12.5+): CLI interfaces

## 📖 Usage Guide

### Basic Usage

```python
import asyncio

from examples.common_stakeholders import create_stakeholder_agent
from examples.end_to_end_examples.icap.workflow import create_workflow
from manager_agent_gym import (
    ChainOfThoughtManagerAgent,
    WorkflowExecutionEngine,
    AgentRegistry,
    PreferenceWeights,
    Preference,
)


# Configure manager priorities
preferences = PreferenceWeights(
    preferences=[
        Preference(name="quality", weight=0.4, description="High-quality deliverables"),
        Preference(name="time", weight=0.3, description="Reasonable timeline"),
        Preference(name="cost", weight=0.2, description="Cost-effective execution"),
        Preference(name="oversight", weight=0.1, description="Manageable oversight"),
    ]
)


# Instantiate the Chain-of-Thought manager
manager = ChainOfThoughtManagerAgent(
    preferences=preferences,
    model_name="gpt-4o-mini",
    manager_persona="Strategic Project Coordinator",
)


async def run_workflow() -> None:
    workflow = create_workflow()
    agent_registry = AgentRegistry()

    for agent in workflow.agents.values():
        agent_registry.register_agent(agent)

    stakeholder = create_stakeholder_agent(persona="balanced", preferences=preferences)

    engine = WorkflowExecutionEngine(
        workflow=workflow,
        agent_registry=agent_registry,
        manager_agent=manager,
        stakeholder_agent=stakeholder,
        max_timesteps=20,
        seed=42,
    )

    await engine.run_full_execution()


asyncio.run(run_workflow())
```

### Configuration Options

**Manager Agent Modes:**
- `"cot"`: Chain of Thought Manager (default, LLM-based)
- `"random"`: Random baseline for comparison
- `"assign_all"`: Simple one-shot delegation

**Model Selection:**
- `"gpt-4o"`, `"gpt-4o-mini"`: OpenAI GPT-4 variants
- `"o3"`: OpenAI o3 reasoning model (default)
- `"claude-3-5-sonnet"`: Anthropic Claude
- `"gemini-2.0-flash"`: Google Gemini

**Environment Variables:**
- `MAG_MANAGER_MODE`: Default manager mode
- `MAG_MODEL_NAME`: Default model name
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key

## 📋 Core Data Models

### Workflow Schema

```python
class Workflow(BaseModel):
    # Identity
    id: UUID
    name: str
    workflow_goal: str
    owner_id: UUID
    
    # POSG Components  
    tasks: dict[UUID, Task]           # Task graph (G)
    resources: dict[UUID, Resource]   # Resource registry (R)
    agents: dict[str, AgentInterface] # Available agents (W)
    messages: list[Message]           # Communication history (C)
    
    # Constraints and governance
    constraints: list[Constraint]
    
    # Execution state
    total_cost: float
    total_simulated_hours: float
    is_active: bool
```

### Task Schema

```python
class Task(BaseModel):
    id: UUID
    name: str
    description: str
    status: TaskStatus  # PENDING, READY, RUNNING, COMPLETED, FAILED
    
    # Dependencies and hierarchy
    dependency_task_ids: list[UUID]
    subtasks: list[Task]
    
    # Assignment and execution
    assigned_agent_id: str | None
    estimated_duration_hours: float | None
    estimated_cost: float | None
    
    # Outputs
    output_resource_ids: list[UUID]
```

### Agent Configuration

```python
class AIAgentConfig(AgentConfig):
    agent_type: str = "ai_agent"
    model_name: str = "gpt-4o"
    system_prompt: str
    max_concurrent_tasks: int = 3

class HumanAgentConfig(AgentConfig):
    agent_type: str = "human_agent"
    availability_schedule: str
    skill_areas: list[str]
    hourly_rate: float
```

## 🎓 Examples & Scenarios

### Getting Started Examples

Located in `examples/getting_started/`:

1. **`hello_manager_agent.py`**: Complete workflow execution cycle
2. **`basic_agent_communication.py`**: Agent coordination patterns

### End-to-End Scenarios

The library includes 20+ realistic business scenarios in `examples/end_to_end_examples/`:

**Financial Services:**
- `banking_license_application/`: Regulatory compliance workflow
- `icaap/`: Internal Capital Adequacy Assessment Process
- `orsa/`: Own Risk and Solvency Assessment

**Legal & Compliance:**
- `legal_global_data_breach/`: Crisis response and remediation
- `legal_contract_negotiation/`: Multi-party agreement workflows
- `legal_m_and_a/`: Merger and acquisition due diligence

**Technology:**
- `genai_feature_launch/`: AI product development lifecycle
- `tech_company_acquisition/`: Technical integration planning
- `data_science_analytics/`: ML model development pipeline

**Marketing & Operations:**
- `marketing_campaign/`: Multi-channel campaign execution
- `supply_chain_planning/`: Global logistics optimization
- `mnc_workforce_restructuring/`: Large-scale organizational change

### Running Examples

**Interactive CLI (Recommended):**
```bash
# Interactive mode with scenario selection
python -m examples.cli

# Batch mode with specific scenarios
python -m examples.cli \
  --scenarios icaap data_science_analytics \
  --manager-mode cot \
  --model-name gpt-4o \
  --max-timesteps 30 \
  --parallel-jobs 4
```

> **Note**: The CLI is the recommended way to run simulations as it provides comprehensive experiment management and configuration options.

**Programmatic Usage:**
```python
from examples.run_examples import run_demo

# Run specific scenario
results = await run_demo(
    workflow_name="icaap",
    max_timesteps=25,
    model_name="gpt-4o",
    manager_agent_mode="cot",
    seed=42
)
```

## 🔬 Research Applications

### Four Foundational Research Challenges

1. **Hierarchical Task Decomposition**
   - Moving beyond pattern matching to compositional reasoning
   - Systematic hierarchical planning for novel scenarios
   - Dynamic task creation and refinement

2. **Multi-Objective Optimization**  
   - Balancing competing objectives under non-stationary preferences
   - Adaptation without costly retraining
   - Preference learning from stakeholder feedback

3. **Ad Hoc Team Coordination**
   - Orchestrating heterogeneous teams without prior coordination
   - Dynamic capability inference and role assignment
   - Mixed human-AI collaboration patterns

4. **Governance by Design**
   - Maintaining compliance across dynamic workflows
   - Interpretable natural language constraint handling
   - Audit trails and transparency requirements

### Evaluation Methodology

The platform implements comprehensive evaluation including:

**Workflow-Level Quality:**
- Task completion rates and success criteria
- Coordination efficiency and deadtime metrics
- Resource optimization and budget adherence

**Compliance & Human-Centric:**
- Oversight burden on human stakeholders
- Governance adherence and constraint violations
- Communication effectiveness and transparency

**Preference Adherence:**
- Multi-objective regret analysis
- Preference weight sensitivity
- Dynamic preference adaptation

**Performance Metrics:**
- Execution time and computational cost
- LLM token usage and API costs
- Scalability across workflow complexity

## 🛠️ Advanced Features

### Custom Manager Agents

```python
class CustomManagerAgent(ManagerAgent):
    def __init__(self, preferences: PreferenceWeights):
        super().__init__("custom_manager", preferences)
    
    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        # Custom decision logic
        return action

# Register with factory
def create_custom_manager(preferences: PreferenceWeights) -> ManagerAgent:
    return CustomManagerAgent(preferences)
```

### Custom Evaluation Rubrics

```python
from manager_agent_gym.schemas.preferences.rubric import WorkflowRubric

# Code-based rubric
def quality_validator(context: ValidationContext) -> EvaluatedScore:
    # Custom validation logic
    score = evaluate_quality(context.workflow)
    return EvaluatedScore(score=score, reasoning="Quality assessment")

quality_rubric = WorkflowRubric(
    name="quality_check",
    validator=quality_validator,
    max_score=1.0,
    run_condition=RunCondition.EACH_TIMESTEP
)

# LLM-based rubric
llm_rubric = WorkflowRubric(
    name="stakeholder_satisfaction",
    llm_prompt="Evaluate stakeholder satisfaction based on communication quality...",
    max_score=1.0,
    model="gpt-4o"
)
```

### Custom Workflow Agents

```python
class CustomAgent(AgentInterface[AgentConfig]):
    async def execute_task(self, task: Task, resources: list[Resource]) -> ExecutionResult:
        # Custom task execution logic
        return ExecutionResult(
            success=True,
            outputs=[output_resource],
            metadata={"custom_metric": value}
        )
```

### State Restoration and Checkpointing

```python
# Save workflow state
from manager_agent_gym.core.execution.state_restorer import WorkflowStateRestorer

restorer = WorkflowStateRestorer()
checkpoint = await restorer.create_checkpoint(workflow, timestep=10)

# Restore from checkpoint
restored_workflow = await restorer.restore_from_checkpoint(checkpoint)
```

## 📊 Output and Analysis

### Execution Results

```python
class ExecutionResult(BaseModel):
    timestep: int
    workflow_state: str  # JSON snapshot
    manager_action: dict | None
    tasks_started: list[UUID]
    tasks_completed: list[UUID]
    tasks_failed: list[UUID]
    metrics: dict[str, float]
    evaluation_scores: dict[str, float]
```

### Analysis Tools

The library provides analysis utilities in `analysis_outputs/`:
- Cost correction analysis
- Manager action pattern analysis
- Preference adherence tracking
- Cross-scenario performance comparison

### Visualization Support

See the scripts in `examples/analysis/` for plotting and reporting utilities that operate on saved simulation outputs (e.g., comparing manager strategies or building workflow timelines).

## 🧪 Testing

### Test Structure

```
tests/
├── integration/           # End-to-end integration tests
├── unit/                 # Component unit tests
└── simulation_outputs/   # Test execution outputs
```

### Running Tests

```bash
# Run all tests
pytest

# Run integration suite only
pytest tests/integration/

# Run with coverage
pytest --cov=manager_agent_gym
```

Component-level tests live alongside the package modules (for example `tests/test_manager_actions.py`). See `tests/README.md` for fixtures and guidance on adding new coverage.

## 🔧 Configuration Reference

### Environment Variables

| Variable | Description | Default | Examples |
|----------|-------------|---------|----------|
| `MAG_MANAGER_MODE` | Default manager type | `"cot"` | `"cot"`, `"random"`, `"assign_all"` |
| `MAG_MODEL_NAME` | Default LLM model | `"o3"` | `"gpt-4o"`, `"claude-3-5-sonnet"` |
| `OPENAI_API_KEY` | OpenAI API key | Required | `"sk-..."` |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional | `"sk-ant-..."` |

### OutputConfig

```python
from manager_agent_gym.schemas.config import OutputConfig

output_config = OutputConfig(
    base_dir="outputs/",
    save_workflow_snapshots=True,
    save_agent_communications=True,
    save_evaluation_details=True
)
```

## 🤝 Contributing

### Development Setup

```bash
# Install development dependencies with uv (recommended)
uv pip install -e ".[dev]"

# Alternative: Install with pip
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Install pre-commit hooks
pre-commit install

# Run linting
ruff check manager_agent_gym/
ruff format manager_agent_gym/
```

### Adding New Scenarios

1. Create scenario module in `examples/end_to_end_examples/`
2. Implement required functions:
   - `create_workflow()`
   - `create_preferences()`
   - `create_team_timeline()`
   - `create_preference_update_requests()`
   - `create_evaluator_to_measure_goal_achievement()`
3. Register in `examples/scenarios.py`

### Adding New Manager Agents

1. Inherit from `ManagerAgent` base class
2. Implement `take_action()` method
3. Register in factory system
4. Add tests and documentation

## 📚 API Reference

### Core Classes

**Manager Agents:**
- `ManagerAgent`: Abstract base class
- `ChainOfThoughtManagerAgent`: LLM-based structured manager
- `RandomManagerAgentV2`: Random baseline manager

**Workflow Components:**
- `Workflow`: Complete workflow state
- `Task`: Individual work items with dependencies
- `Resource`: Workflow artifacts and deliverables
- `AgentInterface`: Worker agent base class

**Execution:**
- `WorkflowExecutionEngine`: Main simulation engine
- `AgentRegistry`: Agent discovery and management
- `CommunicationService`: Inter-agent messaging

**Evaluation:**
- `ValidationEngine`: Rubric-based evaluation
- `Evaluator`: Preference evaluation configuration
- `WorkflowRubric`: Individual evaluation criteria

### Manager Actions

Available manager actions:
- `AssignTaskAction`: Assign tasks to agents
- `CreateTaskAction`: Create new tasks through decomposition
- `RefineTaskAction`: Modify existing task specifications
- `SendMessageAction`: Communicate with agents/stakeholders
- `UpdatePreferencesAction`: Adjust optimization weights
- `CreateResourceAction`: Define new workflow resources

## 🔗 References

- **Research Paper**: https://arxiv.org/abs/2510.02557
- **API Documentation**: Generated reference in `docs/api/`
- **Architecture Guide**: Technical details in `docs/TECHNICAL_ARCHITECTURE.md`
- **Research Guide**: Implementation guide in `docs/dev/building-docs.md`

---

**Manager Agent Gym v0.1.0** - *Where AI learns to manage complex work in realistic environments.*

For questions, issues, or contributions, please refer to the GitHub repository or contact the development team.
