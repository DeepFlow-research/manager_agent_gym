# RL Training Plan for Rubric Generation Manager

## Overview

This document outlines the architecture and implementation plan for training the rubric generation manager agent using reinforcement learning (GRPO/PPO) with local models.

---

## Part 1: Local Model Implementation for Rubric Generation

### Current Architecture

The rubric generation manager (`RubricDecompositionManagerAgent`) currently uses:
- **LLM Interface**: `manager_agent_gym/core/common/llm_interface.py`
- **Model Selection**: Line 253 in `rubric_decomposition_manager.py` calls `generate_structured_response()`
- **API-based**: Uses OpenAI's client with Instructor patching for structured outputs
- **Models**: Currently supports OpenAI (gpt-*), Anthropic (claude-*), Google (gemini-*)

### Implementation Strategy for Local Models

#### Option 1: vLLM Backend (Recommended)

**Architecture:**
```python
# New file: manager_agent_gym/core/common/local_llm_interface.py

from vllm import LLM, SamplingParams
from typing import Type, TypeVar
from pydantic import BaseModel
import json

T = TypeVar("T", bound=BaseModel)

class LocalLLMInterface:
    """Interface for local model inference with vLLM."""
    
    def __init__(
        self,
        model_path: str,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9,
        dtype: str = "auto"
    ):
        self.llm = LLM(
            model=model_path,
            tensor_parallel_size=tensor_parallel_size,
            gpu_memory_utilization=gpu_memory_utilization,
            dtype=dtype,
            trust_remote_code=True
        )
    
    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_type: Type[T],
        temperature: float = 1.0,
        max_tokens: int = 4096,
        seed: int = 42,
        return_usage: bool = False,
    ) -> T | tuple[T, dict]:
        """Generate structured response from local model."""
        
        # Build prompt with JSON schema
        schema = response_type.model_json_schema()
        full_prompt = self._build_prompt_with_schema(
            system_prompt, user_prompt, schema
        )
        
        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            stop=["</response>", "\n\n---"]  # Custom stop tokens
        )
        
        outputs = self.llm.generate([full_prompt], sampling_params)
        response_text = outputs[0].outputs[0].text
        
        # Parse JSON and validate with Pydantic
        try:
            response_json = self._extract_json(response_text)
            parsed = response_type.model_validate_json(response_json)
            
            if return_usage:
                usage = {
                    "input_tokens": len(outputs[0].prompt_token_ids),
                    "output_tokens": len(outputs[0].outputs[0].token_ids),
                }
                return parsed, usage
            return parsed
            
        except Exception as e:
            raise ValueError(f"Failed to parse model output: {e}\nRaw: {response_text}")
    
    def _build_prompt_with_schema(
        self, system: str, user: str, schema: dict
    ) -> str:
        """Build prompt with JSON schema instructions."""
        return f"""<|system|>
{system}

You must respond with valid JSON matching this schema:
{json.dumps(schema, indent=2)}
<|end|>
<|user|>
{user}
<|end|>
<|assistant|>
"""
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from model output."""
        # Try to find JSON in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        # Try to find raw JSON
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return text[start:end]
        return text
```

**Integration into RubricDecompositionManagerAgent:**

```python
# Modified: manager_agent_gym/core/agents/manager_agent/implementations/rubric_generation_manager/rubric_decomposition_manager.py

class RubricDecompositionManagerAgent(ChainOfThoughtManagerAgent):
    def __init__(
        self,
        model_name: str = "gpt-4o",
        max_clarification_budget: int = 5,
        seed: int = 42,
        use_local_model: bool = False,  # NEW
        local_model_path: str | None = None,  # NEW
    ):
        super().__init__(...)
        
        self.use_local_model = use_local_model
        if use_local_model:
            from manager_agent_gym.core.common.local_llm_interface import LocalLLMInterface
            self.local_llm = LocalLLMInterface(
                model_path=local_model_path or "Qwen/Qwen2.5-32B-Instruct",
                tensor_parallel_size=1,
            )
    
    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        # ... existing code ...
        
        # Replace this call:
        if self.use_local_model:
            response = await self.local_llm.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_type=constrained_schema,
                temperature=1.0,
                seed=self._seed,
                return_usage=True,
            )
        else:
            response = await generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_type=constrained_schema,
                model=self.model_name,
                seed=self._seed,
                return_usage=True,
            )
        
        # ... rest of existing code ...
```

#### Option 2: SGLang (For Training with Gradients)

For RL training, we need gradients. Use SGLang with custom backend:

```python
# manager_agent_gym/core/training/sglang_backend.py

import sglang as sgl
from sglang import function, gen
import torch

@sgl.function
def rubric_generation_program(s, system_prompt, user_prompt, schema):
    """SGLang program for structured generation."""
    s += sgl.system(system_prompt)
    s += sgl.user(user_prompt)
    s += "You must respond with JSON matching this schema:\n"
    s += schema
    s += "\n\nResponse:\n"
    s += gen("response", max_tokens=4096, temperature=1.0)

class SGLangLLMInterface:
    """SGLang interface with gradient support for RL training."""
    
    def __init__(self, model_path: str, device: str = "cuda"):
        self.runtime = sgl.Runtime(
            model_path=model_path,
            device=device,
            mem_fraction_static=0.8,
        )
        sgl.set_default_backend(self.runtime)
    
    async def generate_with_gradients(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: str,
        return_logprobs: bool = True,
    ):
        """Generate with log probabilities for RL training."""
        state = rubric_generation_program.run(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            return_logprob=return_logprobs,
            return_text_logprob=True,
        )
        
        return {
            "text": state["response"],
            "logprobs": state.get_meta_info("logprob") if return_logprobs else None,
            "token_ids": state.get_meta_info("token_ids"),
        }
```

---

## Part 2: RL Training Loop Architecture

### Overview

Train the rubric generation manager to create rubrics that better match ground truth evaluation.

### Training Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Training Episode                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Pre-Execution Phase (Rollout)                          │
│     ┌──────────────────────────────────────┐               │
│     │ RubricDecompositionManager (Policy)  │               │
│     │   - Ask clarification questions      │               │
│     │   - Generate synthetic rubric        │               │
│     │   - Store action logprobs            │               │
│     └──────────────────────────────────────┘               │
│                      │                                       │
│                      ↓                                       │
│  2. Main Execution (Evaluation)                            │
│     ┌──────────────────────────────────────┐               │
│     │  Workers execute task                │               │
│     │  Generate outputs/resources          │               │
│     └──────────────────────────────────────┘               │
│                      │                                       │
│                      ↓                                       │
│  3. Reward Calculation                                      │
│     ┌──────────────────────────────────────┐               │
│     │  Compare:                            │               │
│     │   • Score from SYNTHETIC rubric      │               │
│     │   • Score from GROUND TRUTH rubric   │               │
│     │                                       │               │
│     │  Reward = -|| S_synthetic - S_true ||│               │
│     │         + alignment_bonus             │               │
│     └──────────────────────────────────────┘               │
│                      │                                       │
│                      ↓                                       │
│  4. Gradient Update (GRPO/PPO)                             │
│     ┌──────────────────────────────────────┐               │
│     │  Update policy parameters            │               │
│     │  Maximize expected reward            │               │
│     └──────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Ground Truth Rubric Storage

```python
# manager_agent_gym/core/training/ground_truth_store.py

from manager_agent_gym.schemas.preferences.evaluator import Rubric
from typing import Dict

class GroundTruthRubricStore:
    """Store ground truth rubrics for training tasks."""
    
    def __init__(self):
        self.rubrics: Dict[str, Rubric] = {}
    
    def register_ground_truth(
        self,
        task_id: str,
        rubric: Rubric,
        metadata: dict | None = None
    ):
        """Register a ground truth rubric for a task."""
        self.rubrics[task_id] = rubric
        if metadata:
            rubric.metadata = metadata
    
    def get_ground_truth(self, task_id: str) -> Rubric | None:
        """Get ground truth rubric for evaluation."""
        return self.rubrics.get(task_id)
```

#### 2. Reward Function

**Key Location**: After both rubrics evaluate the same output

```python
# manager_agent_gym/core/training/reward_functions.py

from manager_agent_gym.schemas.preferences.evaluation import EvaluationResult
import numpy as np

class RubricAlignmentReward:
    """Reward function for rubric generation RL training."""
    
    def __init__(
        self,
        alignment_weight: float = 1.0,
        quality_weight: float = 0.5,
        coverage_weight: float = 0.3,
    ):
        self.alignment_weight = alignment_weight
        self.quality_weight = quality_weight
        self.coverage_weight = coverage_weight
    
    def compute_reward(
        self,
        synthetic_eval: EvaluationResult,
        ground_truth_eval: EvaluationResult,
        num_criteria: int,
        num_clarification_questions: int,
    ) -> tuple[float, dict]:
        """Compute reward for generated rubric.
        
        Args:
            synthetic_eval: Evaluation using generated rubric
            ground_truth_eval: Evaluation using ground truth rubric  
            num_criteria: Number of criteria in generated rubric
            num_clarification_questions: Questions asked
            
        Returns:
            (reward, metrics_dict)
        """
        
        # 1. Alignment reward: How close are the scores?
        synthetic_scores = self._extract_scores(synthetic_eval)
        ground_truth_scores = self._extract_scores(ground_truth_eval)
        
        # L2 distance between score vectors
        alignment_error = np.linalg.norm(
            np.array(synthetic_scores) - np.array(ground_truth_scores)
        )
        alignment_reward = -alignment_error * self.alignment_weight
        
        # 2. Quality reward: Penalize too many/few criteria
        quality_penalty = 0.0
        if num_criteria < 3:
            quality_penalty = -0.5 * (3 - num_criteria)
        elif num_criteria > 10:
            quality_penalty = -0.3 * (num_criteria - 10)
        quality_reward = quality_penalty * self.quality_weight
        
        # 3. Efficiency reward: Penalize excessive questions
        efficiency_penalty = -0.1 * max(0, num_clarification_questions - 3)
        
        # 4. Coverage bonus: Reward if all ground truth aspects covered
        coverage_score = self._compute_coverage(
            synthetic_eval, ground_truth_eval
        )
        coverage_reward = coverage_score * self.coverage_weight
        
        total_reward = (
            alignment_reward 
            + quality_reward 
            + efficiency_penalty 
            + coverage_reward
        )
        
        metrics = {
            "alignment_reward": alignment_reward,
            "alignment_error": alignment_error,
            "quality_reward": quality_reward,
            "num_criteria": num_criteria,
            "efficiency_penalty": efficiency_penalty,
            "num_questions": num_clarification_questions,
            "coverage_reward": coverage_reward,
            "coverage_score": coverage_score,
            "total_reward": total_reward,
        }
        
        return total_reward, metrics
    
    def _extract_scores(self, eval_result: EvaluationResult) -> list[float]:
        """Extract normalized scores from evaluation."""
        scores = []
        for pref_score in eval_result.preference_scores.values():
            for rubric_result in pref_score.ruberic_group_results.rubric_scores:
                scores.append(rubric_result.normalized_score)
        return scores
    
    def _compute_coverage(
        self,
        synthetic_eval: EvaluationResult,
        ground_truth_eval: EvaluationResult,
    ) -> float:
        """Compute how well synthetic rubric covers ground truth aspects."""
        # Check if synthetic criteria align with ground truth criteria names/descriptions
        # This is a semantic similarity check
        synthetic_criteria = set(
            rubric.name 
            for ps in synthetic_eval.preference_scores.values()
            for rubric in ps.ruberic_group_results.rubric_scores
        )
        ground_truth_criteria = set(
            rubric.name
            for ps in ground_truth_eval.preference_scores.values()
            for rubric in ps.ruberic_group_results.rubric_scores
        )
        
        # Simple set overlap (can be improved with semantic similarity)
        overlap = len(synthetic_criteria & ground_truth_criteria)
        coverage = overlap / len(ground_truth_criteria) if ground_truth_criteria else 0.0
        
        return coverage
```

#### 3. Training Loop Integration Point

**Location**: Create new training script that wraps the execution engine

```python
# manager_agent_gym/core/training/train_rubric_manager.py

import torch
from torch.optim import Adam
import asyncio
from typing import List, Dict
from dataclasses import dataclass

from manager_agent_gym.core.workflow.engine import WorkflowExecutionEngine
from manager_agent_gym.core.execution.pre_execution_phase import (
    InitialRubricGenerationPhase
)
from manager_agent_gym.core.training.reward_functions import RubricAlignmentReward
from manager_agent_gym.core.training.ground_truth_store import GroundTruthRubricStore
from manager_agent_gym.core.evaluation.engine.validation_engine import ValidationEngine

@dataclass
class RolloutData:
    """Data collected during rollout for gradient computation."""
    action_logprobs: List[torch.Tensor]
    states: List[dict]
    rewards: List[float]
    advantages: List[float]
    
class RubricManagerTrainer:
    """GRPO/PPO trainer for rubric generation manager."""
    
    def __init__(
        self,
        model_path: str,
        learning_rate: float = 1e-5,
        gamma: float = 0.99,
        lam: float = 0.95,
        clip_epsilon: float = 0.2,
        value_coef: float = 0.5,
        entropy_coef: float = 0.01,
    ):
        # Initialize local model with gradient support
        from manager_agent_gym.core.training.sglang_backend import SGLangLLMInterface
        self.policy_model = SGLangLLMInterface(model_path)
        
        # Optimizer
        self.optimizer = Adam(
            self.policy_model.runtime.model.parameters(),
            lr=learning_rate
        )
        
        # Hyperparameters
        self.gamma = gamma
        self.lam = lam
        self.clip_epsilon = clip_epsilon
        self.value_coef = value_coef
        self.entropy_coef = entropy_coef
        
        # Reward function
        self.reward_fn = RubricAlignmentReward()
        
        # Ground truth store
        self.gt_store = GroundTruthRubricStore()
    
    async def collect_rollout(
        self,
        workflow,
        stakeholder,
        communication_service,
        max_turns: int = 3,
    ) -> tuple[RolloutData, dict]:
        """Collect rollout data from one episode.
        
        Returns:
            (rollout_data, metrics)
        """
        
        # Create decomposition manager with trainable policy
        from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_decomposition_manager import (
            RubricDecompositionManagerAgent
        )
        
        decomp_manager = RubricDecompositionManagerAgent(
            model_name="local",
            max_clarification_budget=max_turns,
            seed=42,
            use_local_model=True,
            local_model_interface=self.policy_model,  # Pass trainable model
        )
        
        # Run pre-execution phase
        phase = InitialRubricGenerationPhase(
            manager=decomp_manager,
            stakeholder=stakeholder,
            communication_service=communication_service,
            max_turns=max_turns,
        )
        
        await phase.run(workflow=workflow)
        
        # Get generated rubric
        synthetic_rubric = stakeholder.generated_rubrics[0] if stakeholder.generated_rubrics else None
        
        if not synthetic_rubric:
            # Failed to generate rubric
            return RolloutData([], [], [-10.0], []), {"success": False}
        
        # Execute workflow to generate outputs
        # (Workers do their task, create resources)
        # ... workflow execution code ...
        
        # Evaluate with BOTH rubrics
        validation_engine = ValidationEngine(seed=42)
        
        # Evaluate with synthetic rubric
        synthetic_eval = await validation_engine.evaluate_timestep(
            workflow=workflow,
            timestep=0,
            cadence=None,
            communications=None,
            manager_actions=None,
            workflow_evaluators=[synthetic_rubric],
        )
        
        # Evaluate with ground truth rubric
        gt_rubric = self.gt_store.get_ground_truth(workflow.name)
        if not gt_rubric:
            raise ValueError(f"No ground truth rubric for {workflow.name}")
        
        ground_truth_eval = await validation_engine.evaluate_timestep(
            workflow=workflow,
            timestep=0,
            cadence=None,
            communications=None,
            manager_actions=None,
            workflow_evaluators=[gt_rubric],
        )
        
        # Compute reward
        reward, metrics = self.reward_fn.compute_reward(
            synthetic_eval=synthetic_eval,
            ground_truth_eval=ground_truth_eval,
            num_criteria=len(synthetic_rubric.criteria),
            num_clarification_questions=len(decomp_manager._processed_message_ids),
        )
        
        # Extract logprobs from manager's actions
        # (Need to store these during action generation)
        action_logprobs = decomp_manager.get_action_logprobs()  # NEW METHOD NEEDED
        
        rollout = RolloutData(
            action_logprobs=action_logprobs,
            states=[],  # TODO: Add state representations
            rewards=[reward],
            advantages=[],  # Computed in update step
        )
        
        return rollout, metrics
    
    def compute_advantages(
        self,
        rewards: List[float],
        values: List[float],
    ) -> List[float]:
        """Compute GAE advantages."""
        advantages = []
        gae = 0.0
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] - values[t]
            if t < len(rewards) - 1:
                delta += self.gamma * values[t + 1]
            
            gae = delta + self.gamma * self.lam * gae
            advantages.insert(0, gae)
        
        return advantages
    
    def update_policy(self, rollouts: List[RolloutData]) -> Dict[str, float]:
        """Update policy using GRPO/PPO.
        
        Args:
            rollouts: List of collected rollouts
            
        Returns:
            Training metrics
        """
        
        # Combine all rollouts
        all_logprobs = []
        all_advantages = []
        all_returns = []
        
        for rollout in rollouts:
            # Compute advantages (simplified - assumes single reward per episode)
            advantages = [rollout.rewards[0]]  # Single reward per episode
            
            all_logprobs.extend(rollout.action_logprobs)
            all_advantages.extend(advantages * len(rollout.action_logprobs))
            all_returns.extend([rollout.rewards[0]] * len(rollout.action_logprobs))
        
        # Convert to tensors
        old_logprobs = torch.stack(all_logprobs)
        advantages = torch.tensor(all_advantages, dtype=torch.float32)
        returns = torch.tensor(all_returns, dtype=torch.float32)
        
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # PPO update
        # Re-evaluate actions with current policy
        # (This requires re-running the model - simplified here)
        new_logprobs = old_logprobs  # TODO: Re-evaluate with current policy
        
        # Compute ratio and clipped objective
        ratio = torch.exp(new_logprobs - old_logprobs.detach())
        clipped_ratio = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon)
        
        # Policy loss
        policy_loss = -torch.min(
            ratio * advantages,
            clipped_ratio * advantages
        ).mean()
        
        # Total loss
        loss = policy_loss
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.policy_model.runtime.model.parameters(),
            max_norm=0.5
        )
        self.optimizer.step()
        
        metrics = {
            "loss": loss.item(),
            "policy_loss": policy_loss.item(),
            "mean_advantage": advantages.mean().item(),
            "mean_return": returns.mean().item(),
        }
        
        return metrics
    
    async def train(
        self,
        num_episodes: int,
        workflows: List,  # List of training workflows
        batch_size: int = 4,
    ):
        """Main training loop."""
        
        for episode in range(num_episodes):
            print(f"\n{'='*60}")
            print(f"Episode {episode + 1}/{num_episodes}")
            print(f"{'='*60}")
            
            # Collect batch of rollouts
            rollouts = []
            episode_metrics = []
            
            for workflow_idx in range(batch_size):
                workflow = workflows[workflow_idx % len(workflows)]
                
                # TODO: Create stakeholder, communication service, etc.
                # ...
                
                rollout, metrics = await self.collect_rollout(
                    workflow=workflow,
                    stakeholder=None,  # TODO
                    communication_service=None,  # TODO
                    max_turns=3,
                )
                
                rollouts.append(rollout)
                episode_metrics.append(metrics)
            
            # Update policy
            train_metrics = self.update_policy(rollouts)
            
            # Log metrics
            avg_reward = sum(r.rewards[0] for r in rollouts) / len(rollouts)
            print(f"Average Reward: {avg_reward:.4f}")
            print(f"Loss: {train_metrics['loss']:.4f}")
            
            # TODO: Save checkpoint periodically
```

#### 4. Modifications to RubricDecompositionManager

**Key change**: Store action logprobs during generation

```python
# In rubric_decomposition_manager.py

class RubricDecompositionManagerAgent(ChainOfThoughtManagerAgent):
    
    def __init__(self, ...):
        # ... existing code ...
        self._action_logprobs: list[torch.Tensor] = []  # NEW
    
    async def take_action(self, observation: ManagerObservation) -> BaseManagerAction:
        # ... existing code up to LLM call ...
        
        if self.use_local_model:
            response = await self.local_llm.generate_with_gradients(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=schema_str,
                return_logprobs=True,
            )
            
            # Store logprobs for training
            if response.get("logprobs"):
                self._action_logprobs.append(
                    torch.tensor(response["logprobs"], requires_grad=True)
                )
            
            parsed_action = self._parse_response(response["text"])
        
        # ... rest of method ...
    
    def get_action_logprobs(self) -> list[torch.Tensor]:
        """Get stored action logprobs for RL training."""
        return self._action_logprobs
    
    def reset(self):
        super().reset()
        self._action_logprobs.clear()
```

---

## Part 3: Dataset Requirements

### Training Data Structure

```python
@dataclass
class RubricTrainingExample:
    """Single training example for rubric generation."""
    
    # Task specification
    task_id: str
    task_description: str
    workflow_context: dict
    
    # Ground truth rubric (human-designed or from expert)
    ground_truth_rubric: Rubric
    
    # Optional: Exemplar outputs for evaluation
    exemplar_outputs: List[Resource]
    
    # Optional: Stakeholder persona/preferences
    stakeholder_config: StakeholderConfig
```

### Creating Training Dataset

```python
# manager_agent_gym/core/training/dataset_builder.py

def build_training_dataset_from_benchmarks():
    """Convert existing benchmarks to training examples."""
    
    examples = []
    
    # Load from examples/end_to_end_examples/
    for workflow_dir in EXAMPLE_DIRS:
        # Load workflow
        workflow = load_workflow(workflow_dir)
        
        # Load ground truth preferences/rubrics
        preferences = load_preferences(workflow_dir)
        
        # Convert to Rubric format if needed
        gt_rubric = convert_preferences_to_rubric(preferences)
        
        example = RubricTrainingExample(
            task_id=workflow.name,
            task_description=workflow.workflow_goal,
            workflow_context={...},
            ground_truth_rubric=gt_rubric,
            exemplar_outputs=[],
            stakeholder_config=create_stakeholder_config(preferences),
        )
        
        examples.append(example)
    
    return examples
```

---

## Part 4: Implementation Checklist

### Phase 1: Local Model Integration (Week 1-2)
- [ ] Implement `LocalLLMInterface` with vLLM
- [ ] Add `use_local_model` flag to `RubricDecompositionManagerAgent`
- [ ] Test local model with existing workflows
- [ ] Benchmark inference speed and quality
- [ ] Add configuration for model selection

### Phase 2: Evaluation Infrastructure (Week 3)
- [ ] Implement `GroundTruthRubricStore`
- [ ] Implement `RubricAlignmentReward`
- [ ] Add dual evaluation (synthetic + ground truth)
- [ ] Test reward function on sample data
- [ ] Add metrics logging and visualization

### Phase 3: Gradient-Enabled Generation (Week 4)
- [ ] Implement `SGLangLLMInterface` with gradient support
- [ ] Modify `RubricDecompositionManagerAgent` to store logprobs
- [ ] Test gradient flow through generation
- [ ] Verify logprob computation accuracy

### Phase 4: Training Loop (Week 5-6)
- [ ] Implement `RubricManagerTrainer` class
- [ ] Add rollout collection
- [ ] Implement PPO/GRPO update
- [ ] Add checkpointing and resumption
- [ ] Add training metrics and logging

### Phase 5: Dataset & Experiments (Week 7-8)
- [ ] Build training dataset from benchmarks
- [ ] Create ground truth rubrics for 20+ tasks
- [ ] Run baseline experiments (no training)
- [ ] Run training for 100+ episodes
- [ ] Evaluate on held-out test set
- [ ] Analyze failure modes

---

## Part 5: Expected Outcomes

### Metrics to Track

1. **Alignment Metrics**:
   - L1/L2 distance between synthetic and ground truth scores
   - Spearman correlation of rankings
   - Precision@K for top outputs

2. **Quality Metrics**:
   - Number of criteria generated
   - Code rule compilation success rate
   - LLM judge prompt quality (human eval)

3. **Efficiency Metrics**:
   - Number of clarification questions
   - Generation time
   - Token usage

4. **Training Metrics**:
   - Episode reward
   - Policy loss
   - Value loss
   - Gradient norms

### Success Criteria

- **Baseline**: Random rubric generation → ~30-40% alignment
- **Target**: Trained model → 75-85% alignment with ground truth
- **Stretch**: Surpass ground truth on some metrics (e.g., fewer criteria, faster eval)

---

## References

### Relevant Code Locations

1. **Rubric Generation**:
   - `manager_agent_gym/core/agents/manager_agent/implementations/rubric_generation_manager/rubric_decomposition_manager.py`
   - `manager_agent_gym/core/agents/manager_agent/reward_shaping/service.py`

2. **Evaluation**:
   - `manager_agent_gym/core/evaluation/engine/validation_engine.py`
   - `manager_agent_gym/core/evaluation/engine/code_rule_executor.py`

3. **Pre-Execution Phase**:
   - `manager_agent_gym/core/execution/pre_execution_phase.py`

4. **Workflow Engine**:
   - `manager_agent_gym/core/workflow/engine.py` (lines 284-312)

5. **Stakeholder**:
   - `manager_agent_gym/core/agents/stakeholder_agent/rubric_stakeholder.py` (lines 220-244)

### Papers/Resources

- GRPO: Group Relative Policy Optimization
- PPO: Proximal Policy Optimization
- Constitutional AI: Learning from AI Feedback
- RLHF: Reinforcement Learning from Human Feedback
- vLLM: Efficient LLM inference
- SGLang: Structured generation with gradients

