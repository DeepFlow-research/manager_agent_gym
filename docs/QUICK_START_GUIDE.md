# Manager Agent Gym - Quick Start Guide

> **📄 Paper Documentation**: Academic research documentation and guides can be found in `/docs`

*Get up and running with autonomous workflow management in 10 minutes*

## 🚀 What You'll Build

By the end of this guide, you'll have:
- A working manager agent that orchestrates complex workflows
- Understanding of how AI agents coordinate and execute tasks
- A complete example running on your machine

## 📋 Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key (get one at [platform.openai.com](https://platform.openai.com))

## ⚡ 5-Minute Setup

### Step 1: Install the Library

```bash
# Clone the repository
git clone https://github.com/your-org/manager-agent-gym
cd manager-agent-gym

# Install with uv (recommended)
uv pip install -e .

# Alternative: Install with pip
pip install -e .
```

### Step 2: Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys
# The file should contain:
# OPENAI_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key-here  # Optional
```

> **Note**: The library uses `pydantic-settings` which automatically picks up variables from the `.env` file - no need to export environment variables manually.

### Step 3: Run Your First Example

```bash
# Run the hello world example
python examples/getting_started/hello_manager_agent.py

# Or run simulations via the CLI (recommended)
python -m examples.cli
```

You should see output like:
```
🚀 Welcome to Manager Agent Gym!
📋 Creating workflow...
✅ Created workflow 'ICAAP Workflow' with 8 tasks
👥 Setting up agent registry...
✅ Registered 4 agents
🧠 Creating manager agent...
✅ Manager agent created with quality-focused preferences
🚀 Setting up execution engine...
✅ Execution engine ready
🎬 Starting workflow execution...
```

## 🎯 What Just Happened?

Your first manager agent just:

1. **📋 Analyzed a complex workflow** with 8 interconnected tasks
2. **🧠 Made strategic decisions** about task assignment and timing
3. **👥 Coordinated a team** of AI and simulated human agents
4. **⚖️ Balanced multiple objectives** (quality, time, cost, oversight)
5. **📊 Tracked progress** through discrete timesteps

## 🔧 Understanding the Code

Let's break down the key components:

### Manager Agent Creation

```python
from manager_agent_gym import ChainOfThoughtManagerAgent, PreferenceWeights, Preference

# Define what the manager cares about
preferences = PreferenceWeights(
    preferences=[
        Preference(name="quality", weight=0.4, description="High-quality deliverables"),
        Preference(name="time", weight=0.3, description="Reasonable timeline"),
        Preference(name="cost", weight=0.2, description="Cost-effective execution"),
        Preference(name="oversight", weight=0.1, description="Manageable oversight"),
    ]
)

# Create the AI manager
manager = ChainOfThoughtManagerAgent(
    preferences=preferences,
    model_name="gpt-4o",  # Choose your LLM
    manager_persona="Strategic Project Coordinator"
)
```

### Workflow Execution

```python
from manager_agent_gym import WorkflowExecutionEngine, AgentRegistry

# Set up the execution environment
engine = WorkflowExecutionEngine(
    workflow=workflow,              # The work to be done
    agent_registry=agent_registry,  # Available workers
    manager_agent=manager,          # The AI manager
    stakeholder_agent=stakeholder,  # The stakeholder
    max_timesteps=20,              # Maximum simulation steps
    seed=42                        # For reproducible results
)

# Run the simulation
results = await engine.run_full_execution()
```

## 🎨 Customization Options

### Different Manager Types

```python
# Strategic LLM-based manager (default)
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="gpt-4o")

# Random baseline for comparison
from manager_agent_gym.core.manager_agent import RandomManagerAgentV2
manager = RandomManagerAgentV2(preferences=prefs, seed=42)

# Simple one-shot delegation
from manager_agent_gym.core.manager_agent import OneShotDelegateManagerAgent
manager = OneShotDelegateManagerAgent(preferences=prefs)
```

### Different LLM Models

```python
# OpenAI models
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="gpt-4o")
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="gpt-4o-mini")
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="o3")

# Anthropic models
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="claude-3-5-sonnet")

# Google models
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="gemini-2.0-flash")
```

### Preference Tuning

```python
# Quality-focused preferences
quality_focused = PreferenceWeights(preferences=[
    Preference(name="quality", weight=0.6, description="Exceptional deliverables"),
    Preference(name="time", weight=0.2, description="Reasonable timeline"),
    Preference(name="cost", weight=0.1, description="Cost consideration"),
    Preference(name="oversight", weight=0.1, description="Minimal oversight"),
])

# Speed-focused preferences  
speed_focused = PreferenceWeights(preferences=[
    Preference(name="time", weight=0.5, description="Fast delivery"),
    Preference(name="quality", weight=0.3, description="Adequate quality"),
    Preference(name="cost", weight=0.1, description="Cost consideration"),
    Preference(name="oversight", weight=0.1, description="Minimal oversight"),
])

# Cost-focused preferences
cost_focused = PreferenceWeights(preferences=[
    Preference(name="cost", weight=0.5, description="Minimize expenses"),
    Preference(name="quality", weight=0.2, description="Acceptable quality"),
    Preference(name="time", weight=0.2, description="Reasonable timeline"),
    Preference(name="oversight", weight=0.1, description="Efficient oversight"),
])
```

## 🌟 Try More Examples

### Interactive CLI (Recommended)

```bash
# Interactive example selector with full scenario menu
python -m examples.cli
```

This opens an interactive menu where you can:
- Choose from 20+ realistic business scenarios
- Select different manager types and models
- Run parallel experiments
- Compare results across configurations

**The CLI is the recommended way to run simulations** as it provides the most comprehensive interface for experimentation.

### Specific Scenarios

```bash
# Run a banking compliance workflow
python -m examples.cli --scenarios banking_license_application --manager-mode cot

# Run multiple scenarios in parallel
python -m examples.cli \
  --scenarios data_science_analytics marketing_campaign \
  --manager-mode cot \
  --model-name gpt-4o \
  --parallel-jobs 2

# Compare different manager types
python -m examples.cli \
  --scenarios icaap \
  --manager-mode cot random \
  --model-name gpt-4o
```

### Programmatic Examples

```python
from examples.run_examples import run_demo

# Run a specific scenario
results = await run_demo(
    workflow_name="data_science_analytics",  # ML model development workflow
    max_timesteps=30,
    model_name="gpt-4o",
    manager_agent_mode="cot",
    seed=42
)

# Analyze results
print(f"Completion rate: {results.completion_rate:.1%}")
print(f"Total cost: ${results.total_cost:.2f}")
print(f"Manager actions taken: {len(results.manager_actions)}")
```

## 📊 Understanding Results

After running an example, you'll see:

### Execution Summary
```
📊 SUMMARY:
• Total timesteps: 15
• Tasks completed: 8/8
• Completion rate: 100.0%
• Final execution state: COMPLETED
```

### Manager Actions
```
🧠 MANAGER ACTIONS TAKEN:
• assign_task: 5 times
• refine_task: 2 times
• send_message: 3 times
• create_task: 1 times
```

### Performance Metrics
- **Completion rate**: Percentage of tasks successfully finished
- **Timesteps**: Discrete simulation steps taken
- **Manager actions**: Types and frequency of decisions made
- **Cost tracking**: Estimated and actual costs
- **Quality scores**: Evaluation against preferences

## 🔍 Key Features Demonstrated

### 1. Autonomous Decision Making
The manager agent observes the workflow state and makes strategic decisions without human intervention.

### 2. Multi-Objective Optimization
Balances competing goals like quality vs. speed vs. cost based on your preferences.

### 3. Dynamic Coordination
Adapts to changing conditions, task failures, and new requirements in real-time.

### 4. Realistic Simulation
Models human agent availability, AI agent capabilities, and real-world constraints.

### 5. Comprehensive Evaluation
Tracks multiple metrics beyond just task completion.

## 🎯 Next Steps

### Explore More Scenarios

1. **Financial Services**: `banking_license_application`, `icaap`, `orsa`
2. **Legal & Compliance**: `legal_global_data_breach`, `legal_contract_negotiation`
3. **Technology**: `genai_feature_launch`, `data_science_analytics`
4. **Marketing**: `marketing_campaign`, `brand_crisis_management`

### Customize for Your Use Case

1. **Create your own workflows** by extending the `Workflow` class
2. **Define custom preferences** for your specific domain
3. **Add specialized agents** with domain-specific capabilities
4. **Implement custom evaluation metrics** for your success criteria

### Dive Deeper

- Read the full [Library Documentation](LIBRARY_DOCUMENTATION.md)
- Explore the research paper (`paper.md`)
- Check out advanced examples in `examples/`
- Review the API reference in `docs/`

## 💡 Pro Tips

### Performance Optimization
```python
# Use faster models for experimentation
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="gpt-4o-mini")

# Limit timesteps for faster iteration
engine = WorkflowExecutionEngine(..., max_timesteps=10)

# Run multiple scenarios in parallel
python -m examples.cli --parallel-jobs 4
```

### Debugging and Analysis
```python
# Enable detailed logging
engine = WorkflowExecutionEngine(..., enable_timestep_logging=True)

# Save outputs for analysis
engine = WorkflowExecutionEngine(..., output_config=OutputConfig(base_dir="my_results/"))

# Use deterministic seeds
engine = WorkflowExecutionEngine(..., seed=42)
```

### Cost Management
```python
# Use cost-effective models
manager = ChainOfThoughtManagerAgent(preferences=prefs, model_name="gpt-4o-mini")

# Monitor token usage in outputs
# Check the execution results for API cost tracking
```

## 🚨 Troubleshooting

### Common Issues

**API Key Not Found**
```bash
# Check your .env file exists and contains your API key
cat .env
# Should show: OPENAI_API_KEY=sk-your-key-here

# If missing, copy from example and edit
cp .env.example .env
# Edit .env with your actual API keys
```

**Module Import Errors**
```bash
# Ensure you're in the project directory
cd manager-agent-gym

# Reinstall with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

**Slow Execution**
- Use smaller models (`gpt-4o-mini`)
- Reduce `max_timesteps`
- Check your internet connection

**Out of API Credits**
- Check your OpenAI usage at [platform.openai.com](https://platform.openai.com)
- Consider using smaller models for testing

## 🎉 You're Ready!

You now have a working autonomous manager agent system! The AI manager can:

- 🧩 Break down complex goals into manageable tasks
- 👥 Coordinate teams of specialized agents  
- ⚖️ Balance multiple competing objectives
- 📊 Adapt to changing conditions in real-time
- 📋 Maintain governance and compliance

**What's next?** Try different scenarios, experiment with preferences, and see how the manager adapts to various challenges!

---

*Happy orchestrating! 🎼*
