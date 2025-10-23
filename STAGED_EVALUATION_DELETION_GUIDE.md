# Staged Evaluation Migration - Deletion Guide

## ✅ What's Complete

- **Staged evaluation works** - Full pipeline from GDPEval JSON → score
- **Flat→Staged converter** - Backward compatibility for existing rubrics
- **Unified path** - `evaluate_timestep_staged()` handles everything
- **Code rules updated** - New `evaluate(workflow, context)` signature
- **Tests pass** - End-to-end validation complete

---

## 🗑️ What Can Be Deleted

### **1. OLD EVALUATION ENGINE METHODS** (~400 lines)

**File**: `manager_agent_gym/core/evaluation/engine/validation_engine.py`

**Delete**:
```python
# Lines ~117-395: Old evaluate_timestep() 
async def evaluate_timestep(
    self,
    workflow: Workflow,
    timestep: int,
    cadence: RunCondition,  # ← Not needed anymore
    communications: list[SenderMessagesView] | None,
    manager_actions: list[ActionResult] | None,
    preferences: PreferenceSnapshot | None = None,
    workflow_evaluators: list[Rubric] | None = None,  # ← Old flat rubrics
) -> EvaluationResult:
    # ... 280 lines of complex aggregation logic ...
```

**Keep**:
- `evaluate_staged_rubric()` (lines 506-655)
- `evaluate_timestep_staged()` (lines 657-709)
- `_evaluate_single_rubric()` (still needed by staged eval)

**Action**: Mark old `evaluate_timestep` as deprecated, replace calls with `evaluate_timestep_staged`

---

### **2. AGGREGATION STRATEGY ENUM** (~50 lines)

**File**: `manager_agent_gym/schemas/preferences/evaluator.py`

**Delete entire enum**:
```python
class AggregationStrategy(str, Enum):
    """Strategy for combining rubric scores into single preference value."""
    WEIGHTED_AVERAGE = "weighted_average"
    MIN = "min"
    MAX = "max"
    PRODUCT = "product"
    # ... not needed, stages sum scores!
```

**Reason**: Stages handle scoring internally. No aggregation needed!

---

### **3. FLAT RUBRIC CLASS** (~100 lines)

**File**: `manager_agent_gym/schemas/preferences/evaluator.py`

**Delete or alias**:
```python
class Rubric(BaseModel):
    """Old flat rubric - DEPRECATED."""
    name: str
    description: str
    criteria: list[RubricCriteria]  # ← Flat list
    aggregation: AggregationStrategy  # ← Not needed
    metadata: Any | None = None
```

**Replace with**:
```python
# Option A: Alias (backward compat)
Rubric = StagedRubric

# Option B: Subclass (maintain both temporarily)
class Rubric(StagedRubric):
    """Legacy flat rubric - use StagedRubric instead."""
    pass
```

---

### **4. RUBRICGROUPRESULT CLASS** (~80 lines)

**File**: `manager_agent_gym/schemas/preferences/evaluation.py`

**Delete**:
```python
class RubricGroupResult(BaseModel):
    evaluator_name: str
    generation_metadata: Any = None
    rubric_scores: list[RubricResult]  # ← Flat results
    aggregated_score: float | None = None  # ← Aggregation
    aggregation_strategy: str | None = None
```

**Replace all uses with**: `StagedRubricResult`

**Reason**: Staged results have built-in breakdown. No need for separate class!

---

### **5. PREFERENCE SCORE COMPLEXITY** (~50 lines)

**File**: `manager_agent_gym/schemas/preferences/evaluation.py`

**Delete**:
```python
class PreferenceScore(BaseModel):
    name: str
    score: float
    weight: float
    ruberic_group_results: RubricGroupResult  # ← Old format
    aggregation_strategy: str  # ← Not needed
```

**Replace with**:
```python
class PreferenceScore(BaseModel):
    """Simplified preference score using staged rubrics."""
    name: str
    score: float
    weight: float
    staged_result: StagedRubricResult  # ← New format
```

---

### **6. EVALUATION RESULT COMPLEXITY** (~40 lines)

**File**: `manager_agent_gym/schemas/preferences/evaluation.py`

**Simplify**:
```python
class EvaluationResult(BaseModel):
    workflow_id: UUID
    timestep: int
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # OLD - Delete these:
    preference_scores: dict[str, PreferenceScore] = Field(...)
    evaluation_results: list[RubricGroupResult] = Field(...)
    weighted_preference_total: float = Field(...)
    metrics: dict[str, Any] = Field(default_factory=dict)
    
    # NEW - Keep this:
    staged_results: dict[str, StagedRubricResult]  # All results
    total_utility: float  # Sum of normalized scores
```

---

### **7. CONVERT_TO_RUBRIC FUNCTIONS** (~100 lines)

**File**: `rubric_generation_manager/utils.py`

**Delete**:
```python
def convert_to_rubric_criteria(...) -> list[RubricCriteria]:
    """Old flat conversion."""
    # Not needed anymore
    
def convert_to_rubric(...) -> Rubric:
    """Old flat conversion."""
    # Not needed anymore
```

**Keep**:
```python
def convert_staged_rubric_to_executable(...) -> StagedRubric:
    """NEW - primary conversion path"""
    
def convert_flat_to_staged(...) -> ManagerAgentGeneratedStagedRubric:
    """NEW - backward compat adapter"""
```

---

### **8. ADDITIONAL CONTEXT ITEM ENUM** (~30 lines)

**File**: `manager_agent_gym/schemas/preferences/rubric.py`

**Delete**:
```python
class AdditionalContextItem(str, Enum):
    """Optional context items for rubrics."""
    MANAGER_ACTIONS = "manager_actions"
    COMMS_BY_SENDER = "comms_by_sender"
    # ... not needed, ValidationContext has everything
```

**Reason**: `ValidationContext` always has full context. No need to cherry-pick!

---

### **9. RUNCONDITION COMPLEXITY** (~50 lines)

**File**: `manager_agent_gym/schemas/preferences/rubric.py`

**Simplify or delete**:
```python
class RunCondition(str, Enum):
    """When to run rubric criteria."""
    ON_COMPLETION = "on_completion"
    EVERY_N_STEPS = "every_n_steps"
    ON_MILESTONES = "on_milestones"
    # Complex cadence checking logic...
```

**Reason**: Caller decides when to evaluate. Just pass timestep to `evaluate_timestep_staged()`.

**Alternative**: Keep minimal version if needed for RL training cadence.

---

### **10. OLD EVALUATION EXAMPLES** (~300 lines)

**Delete entire files**:
- `manager_agent_gym/core/evaluation/examples/aggregation_examples.py`
- Any examples showing flat rubric evaluation

**Keep/Update**:
- `multimodal_evaluation_example.py` - update to use staged format

---

### **11. REWARD AGGREGATOR COMPLEXITY** (~200 lines)

**File**: `manager_agent_gym/core/evaluation/schemas/reward.py`

**Simplify**:
```python
# Delete complex aggregators:
class WeightedAverageRewardAggregator(BaseRewardAggregator): ...
class MinRewardAggregator(BaseRewardAggregator): ...
class MaxRewardAggregator(BaseRewardAggregator): ...

# Keep simple version:
class StagedRewardAggregator(BaseRewardAggregator):
    def aggregate(self, eval_result: dict[str, StagedRubricResult]) -> float:
        return sum(r.normalized_score for r in eval_result.values())
```

---

### **12. TEST FILES IN WRONG LOCATIONS** (cleanup)

**Move to `tests/`**:
- `test_gdpeval_integration.py` → `tests/integration/test_gdpeval_loader.py`
- `test_staged_rubric_end_to_end.py` → `tests/integration/test_staged_evaluation_end_to_end.py`
- `test_staged_only_evaluation.py` → `tests/integration/test_staged_unified_path.py`

---

## 📊 Summary

| Category | Lines Deleted | Files Affected |
|----------|---------------|----------------|
| Old evaluate_timestep | ~400 | 1 |
| Aggregation logic | ~300 | 3 |
| Flat rubric classes | ~200 | 2 |
| Result complexity | ~200 | 1 |
| Conversion utils | ~100 | 1 |
| Examples | ~300 | 2 |
| Reward aggregators | ~200 | 1 |
| Context enums | ~80 | 1 |
| **TOTAL** | **~1,780 lines** | **12 files** |

---

## 🚀 Migration Steps

### **Step 1: Mark as Deprecated** (Safe)
Add deprecation warnings to old methods:
```python
@deprecated("Use evaluate_timestep_staged instead")
async def evaluate_timestep(...):
    ...
```

### **Step 2: Update All Callers** (Required)
Find and update all calls to:
- `evaluate_timestep()` → `evaluate_timestep_staged()`
- `Rubric(criteria=...)` → `convert_flat_to_staged()` → `convert_staged_rubric_to_executable()`

### **Step 3: Delete Old Code** (Final)
Once all callers updated, delete the old methods and classes.

---

## ✅ What We Gain

1. **~1,800 lines deleted** - 60% reduction in evaluation code
2. **One evaluation path** - No more flat vs staged confusion
3. **No aggregation complexity** - Stages sum scores naturally
4. **Simpler testing** - One path to test
5. **Better performance** - Less code to execute
6. **Clearer architecture** - Everything is staged

---

## 🎯 Next Actions

1. ✅ Staged evaluation works (DONE)
2. ✅ Flat→Staged converter works (DONE)
3. ⏳ Update callers to use new path
4. ⏳ Delete old code
5. ⏳ Update documentation

**Ready to proceed with deletion?**

