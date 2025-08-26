# 🚀 Getting Started Examples

These examples demonstrate the core features of Manager Agent Gym with crystal-clear narratives.

## What You'll Learn

The **Manager Agent Gym** is a research platform for autonomous workflow management. These examples show you how AI managers can orchestrate complex workflows involving both human and AI collaborators.

## Examples in This Folder

### 1. `hello_manager_agent.py` - Your First Workflow
**Goal**: See the complete workflow execution cycle in action

**What it demonstrates**:
- ✅ Creating workflows with the `WorkflowBuilder`
- ✅ Setting up manager agents with preferences
- ✅ Running execution with the `WorkflowExecutionEngine`
- ✅ Observing manager decision-making in real-time

**Run it**: 
```bash
cd manager_agent_gym
python examples/getting_started/hello_manager_agent.py
```

**What you'll see**: A manager agent taking charge of a simple research workflow, making decisions about task assignment and coordination.

---

## Key Concepts Illustrated

### 🧠 **Manager Agents**
AI agents that observe workflow state and make strategic decisions:
- Assign tasks to agents
- Create new tasks when needed
- Monitor progress and adapt to changes
- Balance multiple preferences (quality, time, cost, etc.)

### 📋 **Workflows** 
Collections of interconnected tasks with:
- Task dependencies and scheduling
- Resource requirements and outputs
- Regulatory constraints
- Mixed human and AI agent teams

### 🎯 **Preferences**
The manager's optimization criteria:
- **Quality**: Focus on excellent deliverables
- **Time**: Minimize delays and optimize timelines
- **Cost**: Resource efficiency and budget consciousness
- **Oversight**: Balance supervision needs

### 🚀 **Execution Engine**
The simulation environment that:
- Runs discrete timesteps
- Manages task execution asynchronously
- Provides observations to managers
- Tracks comprehensive metrics

---

## Next Steps

After running these basic examples, explore:
- **Research Examples**: See how the platform tackles cutting-edge research challenges
- **Advanced Features**: Preference dynamics, regret analysis, governance constraints
- **Custom Implementations**: Build your own manager agents and evaluation metrics

The goal is to make autonomous workflow management research both accessible and rigorous! 🎊
