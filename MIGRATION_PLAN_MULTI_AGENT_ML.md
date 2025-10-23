# Migration Plan: multi_agent_ml_task.py → Staged Evaluation

## 🎯 Goal
Migrate `examples/research/multi_agent_ml_task.py` from deprecated flat rubric evaluation to new staged evaluation system.

---

## 📊 Current Architecture

```
Ground Truth Flat Rubric (hardcoded)
    ↓
convert_to_rubric() → Executable Rubric
    ↓
Stakeholder.preference_data
    ↓
Stakeholder.evaluate_for_timestep()
    ↓
ValidationEngine.evaluate_timestep() [DEPRECATED]
    ↓
EvaluationResult (single aggregated score)
    ↓
Ranking & Selection
```

**Issues:**
- ❌ Uses deprecated `evaluate_timestep()` (shows warning)
- ❌ Flat rubric structure (no gates)
- ❌ Complex aggregation logic
- ❌ Indirect evaluation through stakeholder
- ❌ Limited result details

---

## ✨ Target Architecture

```
Ground Truth Staged Rubric (converted or GDPEval)
    ↓
convert_staged_rubric_to_executable() → StagedRubric
    ↓
Direct call: ValidationEngine.evaluate_timestep_staged()
    ↓
StagedRubricResult (per-stage breakdown)
    ↓
Ranking & Selection
```

**Benefits:**
- ✅ Uses production-ready staged evaluation
- ✅ Gate logic (shape validation before quality checks)
- ✅ Simple score summation
- ✅ Direct evaluation (no stakeholder wrapper)
- ✅ Rich per-stage results

---

## 🔄 Migration Steps

### **Phase 1: Convert Ground Truth Rubric to Staged Format**

**File**: `examples/research/multi_agent_ml_task.py`

**Option A: Convert Existing Flat Rubric** (Quick)
```python
def create_ground_truth_rubric() -> ManagerAgentGeneratedStagedRubric:
    """Create staged ground truth rubric with gate logic."""
    from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
        LLMJudgeRule,
        CodeRule,
        EvaluationStageSpec,
        ManagerAgentGeneratedStagedRubric,
    )
    
    # Stage 1: Shape Enforcement Gate (must pass to continue)
    shape_stage = EvaluationStageSpec(
        name="Output File Validation",
        description="Verify required output files are created",
        is_required=True,  # GATE!
        min_score_to_pass=0.8,  # Must score 0.8/1.0 to proceed
        rules=[
            CodeRule(
                name="Output Files Created",
                description="Check that both Excel and Markdown outputs exist",
                weight=1.0,
                code='''
def evaluate(workflow, context):
    """Check that both Excel and Markdown outputs exist."""
    outputs = context.get_all_outputs()
    
    has_excel = any(
        r.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        or (r.file_path and r.file_path.endswith('.xlsx'))
        for r in outputs
    )
    
    has_markdown = any(
        r.mime_type == 'text/markdown'
        or (r.file_path and r.file_path.endswith('.md'))
        for r in outputs
    )
    
    if has_excel and has_markdown:
        return 1.0
    elif has_excel or has_markdown:
        return 0.5
    else:
        return 0.0
'''
            ),
        ],
        max_points=1.0,
        on_failure_action="skip_remaining",  # If gate fails, stop evaluation
    )
    
    # Stage 2: Quality Assessment (only runs if Stage 1 passes)
    quality_stage = EvaluationStageSpec(
        name="Content Quality Evaluation",
        description="Assess analysis completeness and accuracy",
        is_required=False,  # Not a gate, always contributes to score
        min_score_to_pass=0.0,
        rules=[
            LLMJudgeRule(
                name="Data Analysis Completeness",
                description="All features analyzed thoroughly",
                weight=1.5,
                judge_prompt="Evaluate whether the analysis examines all customer features (tenure, monthly spend, support tickets, usage score) and identifies meaningful patterns. Score 0-10 where 10 means all features analyzed thoroughly.",
            ),
            LLMJudgeRule(
                name="Risk Classification Accuracy",
                description="Churn risk predictions are logical",
                weight=2.0,
                judge_prompt="Evaluate whether the churn risk classifications (High/Medium/Low) are logical and defensible based on customer data patterns. Score 0-10 where 10 means perfect alignment between data and risk levels.",
            ),
            LLMJudgeRule(
                name="Excel Output Quality",
                description="Excel file has required sheets and formatting",
                weight=1.5,
                judge_prompt="Evaluate the Excel file quality: does it have Analysis and Summary sheets, proper formatting, and correct calculations? Score 0-10 where 10 means perfect Excel structure.",
            ),
        ],
        max_points=5.0,
        on_failure_action="continue",
    )
    
    # Stage 3: Insight Quality (only runs if Stage 1 passes)
    insight_stage = EvaluationStageSpec(
        name="Insights and Recommendations",
        description="Clarity and actionability of insights",
        is_required=False,
        min_score_to_pass=0.0,
        rules=[
            LLMJudgeRule(
                name="Methodology Clarity",
                description="Analysis approach clearly explained",
                weight=1.0,
                judge_prompt="Evaluate whether the methodology is clearly explained: analysis approach, risk scoring algorithm, and decision criteria. Score 0-10 where 10 means crystal clear explanation.",
            ),
            LLMJudgeRule(
                name="Actionable Insights",
                description="Specific recommendations provided",
                weight=1.5,
                judge_prompt="Evaluate whether the report provides specific, actionable recommendations for addressing high-risk customers. Score 0-10 where 10 means highly actionable insights.",
            ),
        ],
        max_points=2.5,
        on_failure_action="continue",
    )
    
    return ManagerAgentGeneratedStagedRubric(
        category_name="Customer Churn Analysis Quality",
        rationale="3-stage evaluation: gate on outputs, then assess quality and insights",
        max_total_score=8.5,  # 1.0 + 5.0 + 2.5
        stages=[shape_stage, quality_stage, insight_stage],
    )
```

**Option B: Use GDPEval Rubric** (Ideal for real eval set)
```python
def load_ground_truth_rubric() -> ManagerAgentGeneratedStagedRubric:
    """Load pre-generated GDPEval rubric for this task."""
    from pathlib import Path
    from manager_agent_gym.core.evaluation.loaders.gdpeval_loader import load_gdpeval_rubric
    
    gdpeval_path = Path(__file__).parent.parent.parent / "curation" / "gdpeval" / "data" / "generated" / "staged_v4" / "staged_rubrics.jsonl"
    
    # Map your task to a GDPEval task ID (you'd need to create this mapping)
    task_id = "customer_churn_analysis"  # Replace with actual task ID
    
    return load_gdpeval_rubric(gdpeval_path, task_id)
```

---

### **Phase 2: Update Rubric Preparation**

**Change**: Lines 390-438

**Before**:
```python
print("🔧 Step 3: Creating ground truth rubric...")
ground_truth_rubric = create_ground_truth_rubric()  # Flat

# Convert to executable for stakeholder
gt_rubric_executable = convert_to_rubric(
    spec=ground_truth_rubric,
    preference_name="customer_churn_quality",
)

stakeholder_config = StakeholderConfig(
    # ...
    preference_data=gt_rubric_executable,  # Used for evaluation
)
```

**After**:
```python
print("🔧 Step 3: Creating ground truth rubric...")
ground_truth_rubric_spec = create_ground_truth_rubric()  # Staged spec

# Convert to executable staged rubric
from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.utils import (
    convert_staged_rubric_to_executable,
)

gt_rubric_executable = convert_staged_rubric_to_executable(ground_truth_rubric_spec)

print(f"  ✓ Created staged ground truth rubric: '{gt_rubric_executable.category_name}'")
print(f"  ✓ Number of stages: {len(gt_rubric_executable.stages)}")
for stage in gt_rubric_executable.stages:
    gate_marker = "🚪 GATE" if stage.is_required else "✓"
    print(f"    {gate_marker} {stage.name}: {len(stage.rules)} rules, max {stage.max_points} pts")

# Stakeholder no longer needs preference_data for evaluation
# (only used for rubric GENERATION via clarification dialogue)
stakeholder_config = StakeholderConfig(
    agent_id="ml_stakeholder",
    # ... other config ...
    preference_data=None,  # Not used for evaluation anymore
)
```

---

### **Phase 3: Replace Evaluation Call**

**Option A: Evaluate in Engine** (Recommended for integration)

**File**: `manager_agent_gym/core/workflow/engine.py`

Add method to engine:
```python
async def evaluate_with_staged_rubrics(
    self,
    timestep: int,
    staged_rubrics: list[StagedRubric],
) -> dict[str, StagedRubricResult]:
    """Evaluate workflow using staged rubrics.
    
    Args:
        timestep: Current timestep
        staged_rubrics: List of staged rubrics to evaluate
        
    Returns:
        Dict mapping category_name to result
    """
    from manager_agent_gym.core.evaluation.engine.validation_engine import ValidationEngine
    
    validation_engine = ValidationEngine(
        seed=self.seed,
        log_preference_progress=True,
    )
    
    results = await validation_engine.evaluate_timestep_staged(
        workflow=self.workflow,
        timestep=timestep,
        staged_rubrics=staged_rubrics,
        communications=self.communication_service.get_all_communications(),
        manager_actions=None,  # Could track manager actions if needed
    )
    
    # Store results in workflow for ranking
    for category_name, result in results.items():
        # Map to task executions and update scores
        for task in self.workflow.tasks.values():
            for execution in task.get_executions(self.workflow):
                if execution.is_completed():
                    execution.aggregate_score = result.total_score
                    execution.evaluation_details = {
                        "category": category_name,
                        "normalized_score": result.normalized_score,
                        "stages_passed": result.stages_passed,
                        "failed_gate": result.failed_gate,
                        "stage_results": result.stage_results,
                    }
    
    return results
```

**Then in `multi_agent_ml_task.py`**, after execution:

```python
# Line ~618: After engine.run_full_execution()
await engine.run_full_execution()

# NEW: Evaluate with staged rubric
print()
print("🔍 Evaluating outputs with staged ground truth rubric...")
print("-" * 80)

evaluation_results = await engine.evaluate_with_staged_rubrics(
    timestep=engine.current_timestep,
    staged_rubrics=[gt_rubric_executable],
)

# Display evaluation results
for category, result in evaluation_results.items():
    print(f"\n📊 {category}")
    print(f"  Total Score: {result.total_score:.2f}/{result.max_score:.2f}")
    print(f"  Normalized: {result.normalized_score:.2%}")
    print(f"  Stages Evaluated: {result.stages_evaluated}/{len(gt_rubric_executable.stages)}")
    
    if result.failed_gate:
        print(f"  ❌ FAILED GATE: {result.failed_gate}")
        print(f"     Evaluation stopped at: {result.stopped_at}")
    
    print(f"\n  Stage Breakdown:")
    for stage_result in result.stage_results:
        status = "✅ PASS" if stage_result["passed"] else "❌ FAIL"
        print(f"    {status} {stage_result['name']}")
        print(f"         Score: {stage_result['score']:.2f}/{stage_result['max_points']:.2f}")
        
        # Show rule-level details
        for rule_result in stage_result["rules"]:
            print(f"           - {rule_result['name']}: {rule_result['score']:.2f}/{rule_result['max_score']:.2f}")
            if "feedback" in rule_result:
                print(f"             {rule_result['feedback']}")

print()
print("=" * 80)
```

**Option B: Direct Call** (Quick & Simple)

**In `multi_agent_ml_task.py`**, after execution:

```python
# Line ~618: After engine.run_full_execution()
await engine.run_full_execution()

# NEW: Direct evaluation with staged rubric
print()
print("🔍 Evaluating outputs with staged ground truth rubric...")
print("-" * 80)

from manager_agent_gym.core.evaluation.engine.validation_engine import ValidationEngine

validation_engine = ValidationEngine(seed=SEED, log_preference_progress=True)

evaluation_results = await validation_engine.evaluate_timestep_staged(
    workflow=workflow,
    timestep=1,  # Or engine.current_timestep
    staged_rubrics=[gt_rubric_executable],
    communications=None,
    manager_actions=None,
)

# [Same display code as above]
```

---

### **Phase 4: Update Result Handling**

**File**: `examples/research/multi_agent_ml_task.py`

**Lines 663-729**: Update ranking display to use staged results

**Before**:
```python
if execution.aggregate_score:
    print(f"    Score: {execution.aggregate_score:.2f}/10")
```

**After**:
```python
if execution.evaluation_details:
    details = execution.evaluation_details
    print(f"    Score: {details['normalized_score']:.2%}")
    print(f"    Stages Passed: {details['stages_passed']}/{len(details['stage_results'])}")
    if details['failed_gate']:
        print(f"    ⚠️  Failed Gate: {details['failed_gate']}")
```

---

### **Phase 5: Remove Stakeholder Evaluation Hook** (Optional)

**Decision Point**: Do you still need stakeholder for rubric GENERATION?

**If YES (keep stakeholder for generation)**:
- Keep stakeholder agent
- Remove only the evaluation path from stakeholder
- Stakeholder still participates in clarification dialogue during rubric generation

**If NO (pure evaluation only)**:
- Remove stakeholder entirely
- Use pre-generated GDPEval rubrics only
- Simpler architecture

**Change for Option A (keep generation, remove evaluation)**:

Comment out stakeholder evaluation in engine:
```python
# In engine.py or execution flow
# Don't call: await stakeholder.evaluate_for_timestep(...)
# Instead: Use engine.evaluate_with_staged_rubrics()
```

---

## 🧪 Testing Strategy

### **Step 1: Run with Deprecation Warning**
```bash
# Current code - should show deprecation warning
python -m examples.research.multi_agent_ml_task --mode train --n-synthetic 2
# Expected: DeprecationWarning about evaluate_timestep()
```

### **Step 2: Run with Staged Evaluation**
```bash
# After Phase 1-3 migration
python -m examples.research.multi_agent_ml_task --mode train --n-synthetic 2
# Expected: No warnings, staged evaluation results displayed
```

### **Step 3: Compare Results**
- Run both versions
- Compare scores
- Verify flat→staged conversion preserved semantics

### **Step 4: Test Gate Logic**
- Modify code to fail shape validation
- Verify evaluation stops at gate
- Confirm quality stages are skipped

---

## 📋 Migration Checklist

- [ ] **Phase 1**: Convert ground truth rubric to staged format
  - [ ] Define stages with gate logic
  - [ ] Update code rules to use new signature
  - [ ] Set gate thresholds and failure actions

- [ ] **Phase 2**: Update rubric preparation
  - [ ] Use `convert_staged_rubric_to_executable()`
  - [ ] Remove stakeholder preference_data (or keep for generation)
  - [ ] Add staging logging

- [ ] **Phase 3**: Replace evaluation call
  - [ ] Add `evaluate_with_staged_rubrics()` to engine OR
  - [ ] Call `ValidationEngine.evaluate_timestep_staged()` directly
  - [ ] Store StagedRubricResult in workflow

- [ ] **Phase 4**: Update result handling
  - [ ] Display per-stage breakdown
  - [ ] Show gate failures
  - [ ] Update ranking logic

- [ ] **Phase 5**: Clean up old code
  - [ ] Remove stakeholder evaluation hook
  - [ ] Delete unused conversion functions
  - [ ] Update documentation

- [ ] **Testing**: Verify migration
  - [ ] Run both versions
  - [ ] Compare scores
  - [ ] Test gate logic
  - [ ] Validate GRPO metadata

---

## 🎯 Expected Outcomes

### **Before Migration**:
```
Output Rankings:
  Rank 1:
    Score: 7.5/10
    Agent: ml_researcher_variant_0
```

### **After Migration**:
```
Evaluation Results:
  📊 Customer Churn Analysis Quality
    Total Score: 6.5/8.5
    Normalized: 76.47%
    Stages Evaluated: 3/3
    
    Stage Breakdown:
      ✅ PASS Output File Validation
           Score: 1.0/1.0
             - Output Files Created: 1.0/1.0
      ✅ PASS Content Quality Evaluation
           Score: 3.8/5.0
             - Data Analysis Completeness: 1.2/1.5
             - Risk Classification Accuracy: 1.6/2.0
             - Excel Output Quality: 1.0/1.5
      ✅ PASS Insights and Recommendations
           Score: 1.7/2.5
             - Methodology Clarity: 0.7/1.0
             - Actionable Insights: 1.0/1.5

Output Rankings:
  Rank 1:
    Score: 76.47%
    Agent: ml_researcher_variant_0
    Stages Passed: 3/3
```

---

## 🚀 Next Steps After Migration

1. **Generate GDPEval rubrics** for all your benchmark tasks
2. **Replace hardcoded rubric** with GDPEval loader
3. **Use gate logic** to enforce shape validation
4. **Collect richer metadata** for GRPO training
5. **Optional**: Remove old evaluation path entirely

---

## 📞 Support

See also:
- `STAGED_EVALUATION_COMPLETE.md` - Implementation summary
- `STAGED_EVALUATION_DELETION_GUIDE.md` - What to delete
- `tests/test_staged_evaluation_end_to_end.py` - Working example

