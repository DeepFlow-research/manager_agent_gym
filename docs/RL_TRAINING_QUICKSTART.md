# RL Training Quick Start Guide

## TL;DR - Key Insights

### 1. **Local Model Integration** ✅

The rubric generation happens in **one place**:
```python
# File: rubric_decomposition_manager.py, Line 253
response = await generate_structured_response(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    response_type=constrained_schema,
    model=self.model_name,  # <-- Swap this for local model
    seed=self._seed,
    return_usage=True,
)
```

**Implementation**: Create a thin wrapper that calls vLLM or SGLang instead of OpenAI API.

---

### 2. **RL Training Location** 🎯

The reward calculation should happen **after both rubrics evaluate the same output**:

```
Location: NEW file - manager_agent_gym/core/training/train_rubric_manager.py

Flow:
  1. Pre-execution phase generates SYNTHETIC rubric
     ↓
  2. Main execution produces task outputs
     ↓
  3. Evaluate outputs with SYNTHETIC rubric → Score_synthetic
     ↓
  4. Evaluate outputs with GROUND TRUTH rubric → Score_gt
     ↓
  5. Calculate reward: -||Score_synthetic - Score_gt||²
     ↓
  6. Backprop through policy model
```

**Hook Point**: After line 244 in `rubric_stakeholder.py` where evaluation completes.

---

### 3. **Where to Calculate Loss** 📊

```python
# manager_agent_gym/core/training/train_rubric_manager.py (NEW FILE)

async def collect_rollout(...):
    # 1. Run pre-execution → generates synthetic rubric
    await phase.run(workflow=workflow)
    synthetic_rubric = stakeholder.generated_rubrics[0]
    
    # 2. Execute workflow → creates outputs
    # (workers do their tasks)
    
    # 3. Evaluate with BOTH rubrics
    synthetic_eval = await validation_engine.evaluate_timestep(
        workflow=workflow,
        workflow_evaluators=[synthetic_rubric],  # Generated
    )
    
    ground_truth_eval = await validation_engine.evaluate_timestep(
        workflow=workflow,
        workflow_evaluators=[gt_rubric],  # Ground truth
    )
    
    # 4. COMPUTE LOSS HERE
    reward = -torch.norm(
        synthetic_eval.weighted_preference_total - 
        ground_truth_eval.weighted_preference_total
    )
    
    # 5. Backprop
    loss = -reward * action_logprobs.sum()
    loss.backward()
```

---

## Minimal Working Example

### Step 1: Add Local Model Support (30 minutes)

```python
# manager_agent_gym/core/common/vllm_interface.py (NEW)

from vllm import LLM, SamplingParams
import json

class VLLMInterface:
    def __init__(self, model_path: str):
        self.llm = LLM(model=model_path, dtype="auto")
    
    async def generate_structured(self, system_prompt: str, user_prompt: str, 
                                  response_type, temperature: float, seed: int):
        # Build prompt with schema
        schema = response_type.model_json_schema()
        full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nRespond with JSON matching:\n{json.dumps(schema)}"
        
        # Generate
        sampling_params = SamplingParams(temperature=temperature, max_tokens=4096, seed=seed)
        outputs = self.llm.generate([full_prompt], sampling_params)
        
        # Parse and validate
        response_text = outputs[0].outputs[0].text
        json_str = self._extract_json(response_text)
        return response_type.model_validate_json(json_str)
    
    def _extract_json(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}") + 1
        return text[start:end] if start != -1 and end > start else text
```

### Step 2: Integrate into Manager (15 minutes)

```python
# Modify: rubric_decomposition_manager.py

class RubricDecompositionManagerAgent:
    def __init__(self, ..., use_local: bool = False, model_path: str = None):
        self.use_local = use_local
        if use_local:
            from manager_agent_gym.core.common.vllm_interface import VLLMInterface
            self.local_llm = VLLMInterface(model_path)
    
    async def take_action(self, observation):
        # ... existing code ...
        
        if self.use_local:
            response = await self.local_llm.generate_structured(...)
        else:
            response = await generate_structured_response(...)  # Original
```

### Step 3: Create Training Script (1 hour)

```python
# manager_agent_gym/core/training/train.py (NEW)

import torch
from torch.optim import Adam

async def train_one_episode(workflow, gt_rubric):
    # 1. Run pre-execution with trainable model
    decomp_manager = RubricDecompositionManagerAgent(
        use_local=True,
        model_path="Qwen/Qwen2.5-32B-Instruct"
    )
    
    phase = InitialRubricGenerationPhase(
        manager=decomp_manager,
        stakeholder=stakeholder,
        communication_service=comm,
        max_turns=3,
    )
    
    await phase.run(workflow)
    synthetic_rubric = stakeholder.generated_rubrics[0]
    
    # 2. Execute workflow (workers create outputs)
    # ... execution code ...
    
    # 3. Dual evaluation
    validation_engine = ValidationEngine(seed=42)
    
    synthetic_scores = await validation_engine.evaluate_timestep(
        workflow=workflow,
        workflow_evaluators=[synthetic_rubric],
        timestep=0, cadence=None, communications=None, manager_actions=None,
    )
    
    gt_scores = await validation_engine.evaluate_timestep(
        workflow=workflow,
        workflow_evaluators=[gt_rubric],
        timestep=0, cadence=None, communications=None, manager_actions=None,
    )
    
    # 4. Compute reward
    synthetic_score = synthetic_scores.weighted_preference_total
    gt_score = gt_scores.weighted_preference_total
    reward = -abs(synthetic_score - gt_score)  # Negative L1 distance
    
    print(f"Synthetic: {synthetic_score:.3f}, GT: {gt_score:.3f}, Reward: {reward:.3f}")
    
    return reward

# Main training loop
async def main():
    workflows = load_training_workflows()
    gt_rubrics = load_ground_truth_rubrics()
    
    for episode in range(100):
        workflow = workflows[episode % len(workflows)]
        gt_rubric = gt_rubrics[workflow.name]
        
        reward = await train_one_episode(workflow, gt_rubric)
        
        # TODO: Add actual gradient update here
        # (requires storing logprobs during generation)

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Run Training

```bash
# Install dependencies
pip install vllm torch

# Run training
python -m manager_agent_gym.core.training.train
```

---

## Key Code Locations

### 1. **Where Rubrics are Generated**
- File: `manager_agent_gym/core/agents/manager_agent/reward_shaping/service.py`
- Function: `decompose_preference_to_evaluator()` (lines 31-87)
- LLM Call: Line 68-75

### 2. **Where Rubrics are Evaluated**
- File: `manager_agent_gym/core/evaluation/engine/validation_engine.py`
- Method: `evaluate_timestep()` (lines 119-293)
- Scoring: Lines 195-211 (calls `_evaluate_single_rubric`)

### 3. **Where to Hook RL Training**
- **Pre-execution**: `manager_agent_gym/core/execution/pre_execution_phase.py`
  - Line 232-375: `InitialRubricGenerationPhase.run()`
- **Evaluation**: `manager_agent_gym/core/agents/stakeholder_agent/rubric_stakeholder.py`
  - Lines 220-244: `evaluate_for_timestep()` calls validation engine
- **NEW FILE**: Create `manager_agent_gym/core/training/train_rubric_manager.py`
  - This wraps the above and adds reward calculation + gradient updates

### 4. **Existing Evaluation Example**
- File: `examples/research/multi_agent_ml_task.py`
- Shows how to use validation engine to score with generated rubrics
- Lines 61-147: `create_rubric_based_scorer()`

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Training Episode                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Pre-Execution (Rubric Generation)                 │
│  ─────────────────────────────────────────────              │
│  File: manager_agent_gym/core/execution/                    │
│        pre_execution_phase.py                                │
│                                                              │
│  RubricDecompositionManagerAgent.take_action()              │
│  ├─ Observe workflow context                                │
│  ├─ Ask clarification questions (1-3 turns)                 │
│  └─ Generate rubric via LLM                                  │
│      └─ HOOK: Replace with local model here                 │
│          (rubric_decomposition_manager.py:253)              │
│                                                              │
│  Output: Synthetic Rubric (stored in                        │
│          stakeholder.generated_rubrics)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Main Execution (Task Completion)                  │
│  ────────────────────────────────────────                   │
│  File: manager_agent_gym/core/workflow/engine.py            │
│                                                              │
│  Workers execute tasks:                                      │
│  ├─ Read input resources                                    │
│  ├─ Perform work (analysis, coding, etc.)                   │
│  └─ Create output resources                                 │
│                                                              │
│  Output: Task outputs (spreadsheets, docs, code)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Dual Evaluation                                   │
│  ──────────────────────────                                 │
│  File: manager_agent_gym/core/evaluation/engine/            │
│        validation_engine.py                                  │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ Synthetic Rubric     │  │ Ground Truth Rubric  │        │
│  │ (Generated by agent) │  │ (Human-designed)     │        │
│  └──────────────────────┘  └──────────────────────┘        │
│           │                          │                      │
│           ↓                          ↓                      │
│   evaluate_timestep()       evaluate_timestep()            │
│           │                          │                      │
│           ↓                          ↓                      │
│   Score_synthetic            Score_gt                       │
│   (e.g., 0.72)               (e.g., 0.85)                   │
│                                                              │
│  Output: Two evaluation results                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: Reward Calculation & Gradient Update             │
│  ─────────────────────────────────────────────              │
│  File: manager_agent_gym/core/training/                     │
│        train_rubric_manager.py (NEW)                         │
│                                                              │
│  reward_fn.compute_reward():                                 │
│  ├─ Alignment: -||Score_synthetic - Score_gt||²            │
│  ├─ Quality: Penalize too many/few criteria                │
│  ├─ Efficiency: Penalize excessive questions                │
│  └─ Coverage: Reward covering all aspects                   │
│                                                              │
│  Total Reward: -0.13² + quality + efficiency + coverage    │
│              = -0.017 + 0.1 - 0.05 + 0.8 = 0.833           │
│                                                              │
│  policy_loss = -reward * action_logprobs.sum()              │
│  policy_loss.backward()                                     │
│  optimizer.step()                                           │
│                                                              │
│  Output: Updated model parameters                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    Repeat for N episodes
```

---

## Next Steps

1. **Start Simple**: Test local model integration first (no training)
   - Verify local model can generate valid rubrics
   - Compare quality with GPT-4o baseline

2. **Build Dataset**: Create 20 ground truth rubrics
   - Use existing benchmarks (examples/end_to_end_examples/)
   - Start with simple tasks, add complexity

3. **Implement Reward Function**: Test reward calculation
   - Run dual evaluation on sample tasks
   - Verify reward correlates with rubric quality

4. **Add Gradients**: Enable gradient computation
   - Use SGLang or custom autograd
   - Store logprobs during generation

5. **Train**: Run full RL loop
   - Start with 10 episodes, verify convergence
   - Scale to 100+ episodes
   - Evaluate on held-out test set

---

## Expected Timeline

- **Week 1**: Local model integration + testing
- **Week 2**: Dataset creation (ground truth rubrics)
- **Week 3**: Reward function + dual evaluation
- **Week 4**: Gradient-enabled generation
- **Week 5-6**: Training loop + experiments
- **Week 7**: Evaluation + analysis
- **Week 8**: Iteration + improvements

**Total**: ~2 months to working RL training system

