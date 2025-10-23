# RL Training - Exact Code Locations

## Summary

This document provides exact file paths and line numbers for implementing RL training for the rubric generation manager.

---

## 1. Local Model Integration Points

### 1.1 Current LLM Interface
**File**: `manager_agent_gym/core/common/llm_interface.py`

**Key Functions**:
- `generate_structured_response()` - Lines 161-283
  - This is the main entry point for all LLM calls
  - Currently uses OpenAI client with Instructor patching
  - Takes: system_prompt, user_prompt, response_type (Pydantic model)
  - Returns: Validated Pydantic object

**Action**: Create parallel interface for local models

---

### 1.2 Manager Agent LLM Call
**File**: `manager_agent_gym/core/agents/manager_agent/implementations/rubric_generation_manager/rubric_decomposition_manager.py`

**Key Method**: `take_action()` - Lines 221-316

**Specific LLM Call**: Lines 253-260
```python
response = await generate_structured_response(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    response_type=constrained_schema,
    model=self.model_name,  # <-- REPLACE THIS
    seed=self._seed,
    return_usage=True,
)
```

**Action**: Add conditional logic to call local model interface

---

### 1.3 Rubric Generation Service
**File**: `manager_agent_gym/core/agents/manager_agent/reward_shaping/service.py`

**Key Function**: `decompose_preference_to_evaluator()` - Lines 31-87

**LLM Call**: Lines 68-75
```python
rubric_spec: ManagerAgentGeneratedRubric = await generate_structured_response(
    model=model_name,
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    response_type=ManagerAgentGeneratedRubric,
    temperature=1.0,
    seed=seed,
)
```

**Action**: This also needs local model support (same pattern as 1.2)

---

## 2. Rubric Evaluation Points

### 2.1 Validation Engine - Main Entry
**File**: `manager_agent_gym/core/evaluation/engine/validation_engine.py`

**Key Method**: `evaluate_timestep()` - Lines 119-293

**What it does**:
- Takes a workflow and list of rubrics to evaluate
- Runs all rubric criteria concurrently (lines 175-227)
- Returns `EvaluationResult` with scores

**Usage Pattern**:
```python
eval_result = await validation_engine.evaluate_timestep(
    workflow=workflow,
    timestep=0,
    cadence=None,
    communications=None,
    manager_actions=None,
    workflow_evaluators=[rubric],  # Pass rubric here
)
```

**Key for RL**: Call this TWICE - once with synthetic rubric, once with ground truth

---

### 2.2 Single Rubric Evaluation
**File**: `manager_agent_gym/core/evaluation/engine/validation_engine.py`

**Key Method**: `_evaluate_single_rubric()` - Lines 358-414

**What it does**:
- Evaluates one rubric criterion (code or LLM judge)
- Lines 374-399: Code rule execution
- Lines 401-414: LLM judge execution
- Returns `EvaluatedScore` object

**Used by**: `evaluate_timestep()` to run each criterion

---

### 2.3 Code Rule Executor
**File**: `manager_agent_gym/core/evaluation/engine/code_rule_executor.py`

**Key Method**: `execute()` - Lines 22-82

**What it does**:
- Compiles and executes Python code rules
- Passes `workflow` and `context` to the evaluate function
- Returns (score, feedback)

---

### 2.4 Stakeholder Evaluation Hook
**File**: `manager_agent_gym/core/agents/stakeholder_agent/rubric_stakeholder.py`

**Key Method**: `evaluate_for_timestep()` - Lines 220-244

**What it does**:
- Called by workflow engine at each timestep
- Passes `self.generated_rubrics` to validation engine
- This is where synthetic rubrics get evaluated

**Current Flow**:
```python
async def evaluate_for_timestep(self, timestep, validation_engine, workflow, ...):
    await validation_engine.evaluate_timestep(
        workflow=workflow,
        timestep=timestep,
        preferences=None,
        workflow_evaluators=self.generated_rubrics,  # Synthetic rubrics
        cadence=RunCondition.EACH_TIMESTEP,
        communications=communications,
        manager_actions=manager_actions,
    )
```

**Action**: This is one place to hook for dual evaluation

---

## 3. Pre-Execution Phase (Where Rubrics are Generated)

### 3.1 Pre-Execution Phase Runner
**File**: `manager_agent_gym/core/execution/pre_execution_phase.py`

**Key Class**: `InitialRubricGenerationPhase` - Lines 102-375

**Key Method**: `run()` - Lines 232-375

**What it does**:
- Orchestrates clarification dialogue (lines 257-349)
- Manager asks questions → Stakeholder responds → Manager generates rubric
- Stores result in `workflow.metadata['pre_execution_logs']`

**Dialogue Loop** - Lines 257-349:
```python
for turn in range(self.max_turns):
    # 1. Stakeholder responds (line 261-264)
    await self.stakeholder.policy_step(...)
    
    # 2. Manager observes (line 267-271)
    observation = await self.manager.create_observation(...)
    
    # 3. Manager acts (line 273)
    action = await self.manager.take_action(observation)  # <-- LLM call here
    
    # 4. Execute action (line 275-278)
    action_result = await action.execute(...)
    
    # 5. Check if rubric generated (line 281-349)
    if isinstance(action, GeneratePreferenceRubricAction) and action_result.success:
        # Rubric generation complete!
        break
```

**Action**: This is the main rollout for RL training

---

### 3.2 Rubric Generation Action
**File**: `manager_agent_gym/core/agents/manager_agent/actions/preference_clarification.py`

**Key Class**: `GeneratePreferenceRubricAction` - Lines 112-205

**Key Method**: `execute()` - Lines 122-205

**What it does** (lines 166-171):
```python
evaluator, rubric_spec = await decompose_preference_to_evaluator(
    workflow=workflow,
    stakeholder_manager_messages=communication_history,
    model_name="gpt-5",  # TODO: make this configurable
    seed=workflow.seed,
)
```

**Then** (lines 173-178):
- Adds rubric to `stakeholder.generated_rubrics[]`
- Broadcasts to all agents

**Action**: This is where the synthetic rubric is created

---

## 4. Workflow Engine Integration

### 4.1 Engine Pre-Execution
**File**: `manager_agent_gym/core/workflow/engine.py`

**Key Method**: `run_full_execution()` - Lines 284-389

**Pre-execution Phase** - Lines 294-312:
```python
if self.pre_execution_phases:
    logger.info(f"Running {len(self.pre_execution_phases)} pre-execution phase(s)...")
    
    for idx, phase in enumerate(self.pre_execution_phases, 1):
        logger.info(f"Pre-execution phase {idx}/{len(self.pre_execution_phases)}: ...")
        await phase.run(workflow=self.workflow)  # <-- Rubric generation happens here
        logger.info(f"Phase {idx} complete")
    
    logger.info("All pre-execution phases complete")
    
    self.output_writer.save_pre_execution_phase(workflow=self.workflow)
```

**Then Main Execution Loop** - Lines 314-389

---

### 4.2 Engine Timestep Execution
**File**: `manager_agent_gym/core/workflow/engine.py`

**Key Method**: `execute_timestep()` - Lines 391-570

**Evaluation Hook** - Lines 445-471:
```python
if self.evaluation_cadence in (RunCondition.EACH_TIMESTEP, RunCondition.BOTH):
    # Get communications and actions
    comms_by_sender = self.communication_service.get_messages_grouped_by_sender(...)
    manager_actions = self.manager_agent.get_action_buffer()
    
    # Let stakeholder trigger its own evaluation
    await self.stakeholder_agent.evaluate_for_timestep(
        timestep=self.current_timestep,
        validation_engine=self.validation_engine,
        workflow=self.workflow,
        communications=comms_by_sender,
        manager_actions=manager_actions,
    )
    did_eval_this_step = True
```

**Action**: This is where synthetic rubric evaluation happens during main execution

---

## 5. Example: Multi-Agent ML Task

### 5.1 Rubric-Based Scoring
**File**: `examples/research/multi_agent_ml_task.py`

**Key Function**: `create_rubric_based_scorer()` - Lines 61-147

**Shows How To**:
- Get generated rubric from stakeholder (line 92)
- Build validation context (lines 95-98)
- Evaluate each criterion (lines 105-131)
- Calculate weighted score (line 134)

**Usage Pattern**:
```python
rubric = stakeholder.generated_rubrics[0]

for criterion in rubric.criteria:
    evaluated_score, error_msg, raw_output = await validation_engine._evaluate_single_rubric(
        workflow=workflow,
        rubric_criteria=criterion,
        context=context,
    )
    
    criterion_score = evaluated_score.score
    criterion_weight = getattr(criterion, "weight", 1.0)
    total_score += criterion_score * criterion_weight
```

**Action**: This pattern shows how to manually evaluate with a rubric (useful for training)

---

## 6. Where to Add New RL Training Code

### 6.1 NEW: Local Model Interface
**Path**: `manager_agent_gym/core/common/vllm_interface.py` (CREATE NEW)

**Contents**:
- `VLLMInterface` class with `generate_structured()` method
- JSON schema formatting
- Response parsing and validation

---

### 6.2 NEW: SGLang Interface (for gradients)
**Path**: `manager_agent_gym/core/training/sglang_interface.py` (CREATE NEW)

**Contents**:
- `SGLangInterface` class with `generate_with_gradients()` method
- Returns logprobs for RL training
- Gradient-enabled generation

---

### 6.3 NEW: Ground Truth Store
**Path**: `manager_agent_gym/core/training/ground_truth_store.py` (CREATE NEW)

**Contents**:
- `GroundTruthRubricStore` class
- Methods: `register_ground_truth()`, `get_ground_truth()`

---

### 6.4 NEW: Reward Function
**Path**: `manager_agent_gym/core/training/reward_functions.py` (CREATE NEW)

**Contents**:
- `RubricAlignmentReward` class
- Method: `compute_reward(synthetic_eval, ground_truth_eval, ...)`
- Returns: (reward, metrics_dict)

---

### 6.5 NEW: Training Loop
**Path**: `manager_agent_gym/core/training/train_rubric_manager.py` (CREATE NEW)

**Contents**:
- `RubricManagerTrainer` class
- Methods:
  - `collect_rollout()` - Run episode, get reward
  - `compute_advantages()` - GAE calculation
  - `update_policy()` - PPO/GRPO update
  - `train()` - Main training loop

---

### 6.6 NEW: Dataset Builder
**Path**: `manager_agent_gym/core/training/dataset_builder.py` (CREATE NEW)

**Contents**:
- Functions to load existing benchmarks
- Convert to training examples
- Create ground truth rubrics

---

## 7. Modification Points in Existing Code

### 7.1 Modify: RubricDecompositionManager
**File**: `manager_agent_gym/core/agents/manager_agent/implementations/rubric_generation_manager/rubric_decomposition_manager.py`

**Changes**:

1. **Add to `__init__()`** (after line 97):
```python
self.use_local_model = False
self.local_llm = None
self._action_logprobs = []  # For RL training
```

2. **Add method** (after line 316):
```python
def set_local_model(self, local_llm_interface):
    """Set local model interface for RL training."""
    self.use_local_model = True
    self.local_llm = local_llm_interface

def get_action_logprobs(self):
    """Get stored action logprobs for RL training."""
    return self._action_logprobs
```

3. **Modify `take_action()`** (lines 253-274):
```python
# Replace this block:
if self.use_local_model and self.local_llm:
    response = await self.local_llm.generate_with_gradients(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=schema_str,
        return_logprobs=True,
    )
    if response.get("logprobs"):
        self._action_logprobs.append(torch.tensor(response["logprobs"]))
    parsed_action = self._parse_response(response["text"])
else:
    response = await generate_structured_response(...)  # Original
```

---

### 7.2 Modify: Workflow Engine (Optional)
**File**: `manager_agent_gym/core/workflow/engine.py`

**Add** (after line 137):
```python
ground_truth_rubrics: list[Rubric] | None = None,  # For RL training
```

**Then in `execute_timestep()`** (after line 471):
```python
# For RL training: also evaluate with ground truth
if self.ground_truth_rubrics:
    gt_eval = await self.validation_engine.evaluate_timestep(
        workflow=self.workflow,
        timestep=self.current_timestep,
        workflow_evaluators=self.ground_truth_rubrics,
        ...
    )
    # Store for reward calculation
    self.workflow.metadata['ground_truth_eval'] = gt_eval.model_dump()
```

---

## 8. Testing Locations

### 8.1 Existing Tests
**Directory**: `tests/`

**Relevant Tests**:
- `test_manager_actions.py` - Tests for manager actions
- `test_preference_engine_integration.py` - Preference evaluation tests
- `tests/integration/` - Integration tests

**Action**: Add new test file `tests/test_rl_training.py`

---

### 8.2 Example Scripts
**Directory**: `examples/`

**Relevant Examples**:
- `examples/research/multi_agent_ml_task.py` - Shows rubric evaluation
- `examples/run_examples.py` - Main runner (lines 79-322)

**Action**: Add `examples/training/train_rubric_generation.py`

---

## 9. Configuration Locations

### 9.1 PyProject Dependencies
**File**: `pyproject.toml`

**Add** (after line 62):
```toml
# RL Training
"torch>=2.0.0",
"vllm>=0.6.0",
"sglang>=0.3.0",
```

---

### 9.2 Config File
**File**: `manager_agent_gym/config.py`

**Currently**: Only has `VERBOSE_LOGGING` flag

**Add**:
```python
# RL Training Configuration
USE_LOCAL_MODELS = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", "Qwen/Qwen2.5-32B-Instruct")
TRAINING_MODE = os.getenv("TRAINING_MODE", "false").lower() == "true"
```

---

## 10. Quick Reference: Call Stack

### Rubric Generation Call Stack:
```
1. WorkflowExecutionEngine.run_full_execution() (engine.py:284)
   ↓
2. InitialRubricGenerationPhase.run() (pre_execution_phase.py:232)
   ↓
3. RubricDecompositionManager.take_action() (rubric_decomposition_manager.py:221)
   ↓
4. generate_structured_response() (llm_interface.py:161)
   ← REPLACE WITH LOCAL MODEL HERE
   ↓
5. GeneratePreferenceRubricAction.execute() (preference_clarification.py:122)
   ↓
6. decompose_preference_to_evaluator() (service.py:31)
   ↓
7. Rubric stored in stakeholder.generated_rubrics[]
```

### Evaluation Call Stack:
```
1. WorkflowExecutionEngine.execute_timestep() (engine.py:391)
   ↓
2. StakeholderAgent.evaluate_for_timestep() (rubric_stakeholder.py:220)
   ↓
3. ValidationEngine.evaluate_timestep() (validation_engine.py:119)
   ↓
4. ValidationEngine._evaluate_single_rubric() (validation_engine.py:358)
   ↓
5a. CodeRuleExecutor.execute() (code_rule_executor.py:22)
    OR
5b. WorkflowValidationRule._llm_validate() (validation_rules.py:165)
   ↓
6. EvaluationResult returned with scores
```

### RL Training Call Stack (NEW):
```
1. RubricManagerTrainer.train() (train_rubric_manager.py - NEW)
   ↓
2. RubricManagerTrainer.collect_rollout() (NEW)
   ↓
3. InitialRubricGenerationPhase.run() [with trainable model]
   ↓
4. [Workflow execution produces outputs]
   ↓
5. ValidationEngine.evaluate_timestep() [with synthetic rubric]
   ↓
6. ValidationEngine.evaluate_timestep() [with ground truth rubric]
   ↓
7. RubricAlignmentReward.compute_reward() (reward_functions.py - NEW)
   ↓
8. RubricManagerTrainer.update_policy() (NEW)
   ↓
9. loss.backward() + optimizer.step()
```

---

## Summary Table

| Component | File | Lines | Action |
|-----------|------|-------|--------|
| LLM Interface | `core/common/llm_interface.py` | 161-283 | Create parallel local interface |
| Manager LLM Call | `core/agents/.../rubric_decomposition_manager.py` | 253-260 | Add local model conditional |
| Rubric Service | `core/agents/.../reward_shaping/service.py` | 68-75 | Add local model support |
| Validation Engine | `core/evaluation/engine/validation_engine.py` | 119-293 | Use for dual evaluation |
| Pre-execution Phase | `core/execution/pre_execution_phase.py` | 232-375 | Hook for RL rollout |
| Rubric Generation | `core/agents/.../actions/preference_clarification.py` | 166-178 | Where synthetic rubric created |
| Stakeholder Eval | `core/agents/.../rubric_stakeholder.py` | 220-244 | Hook for dual evaluation |
| Engine Integration | `core/workflow/engine.py` | 294-312 | Pre-execution phases run here |
| **NEW: vLLM Interface** | `core/common/vllm_interface.py` | - | CREATE NEW |
| **NEW: Reward Function** | `core/training/reward_functions.py` | - | CREATE NEW |
| **NEW: Training Loop** | `core/training/train_rubric_manager.py` | - | CREATE NEW |
| **NEW: GT Store** | `core/training/ground_truth_store.py` | - | CREATE NEW |

---

## Next: Start with Local Model Integration

1. Create `manager_agent_gym/core/common/vllm_interface.py`
2. Test with existing workflow (no training yet)
3. Verify output quality matches API models
4. Then proceed to reward function and training loop

