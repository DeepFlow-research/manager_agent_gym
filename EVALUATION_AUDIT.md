# Evaluation System Audit: Duplication & Refactoring Opportunities

## 🎯 **Overview**

The codebase currently has **MULTIPLE overlapping evaluation/validation paths** that have evolved over time. This audit maps all evaluation systems, identifies duplication, and proposes consolidation strategies.

---

## 📋 **Current Evaluation Paths**

### **1. ValidationEngine (Timestep-Level Evaluation)**
- **Location**: `manager_agent_gym/core/evaluation/engine/validation_engine.py`
- **Purpose**: Evaluates workflow state at each timestep against stakeholder preferences and workflow-level rubrics
- **Key Features**:
  - Runs rubric criteria in parallel with concurrency control
  - Aggregates scores hierarchically (criteria → rubrics → preferences)
  - Maintains reward vector over time for RL training
  - Supports both code-based and LLM-based criteria
- **Context**: Uses `ValidationContext` from `success_criteria.py`
- **Entry Point**: `ValidationEngine.evaluate_timestep()`

**Evaluation Flow**:
```
WorkflowExecutionEngine.run_timestep()
  → ValidationEngine.evaluate_timestep()
    → _evaluate_single_rubric() for each criterion
      → CodeRuleExecutor.execute() [for code rules]
      → MultimodalEvaluator.evaluate_with_vision() [for LLM judges]
```

---

### **2. Task Completion Evaluators (Multi-Agent Ranking)**
- **Location**: `manager_agent_gym/core/workflow/engine.py::_evaluate_and_rank_executions()`
- **Purpose**: Evaluate and rank multiple TaskExecution outputs after task completion
- **Key Features**:
  - Evaluates resource bundles (groups of outputs) per execution
  - Supports both `Rubric` objects and callable functions
  - Stores scores/ranks directly on `TaskExecution` objects
  - **NEW**: Integrates with `ValidationEngine._evaluate_single_rubric()` for `Rubric` objects
- **Context**: Creates `ValidationContext` from `success_criteria.py` with explicit resources
- **Entry Point**: `_evaluate_and_rank_executions()`

**Evaluation Flow**:
```
WorkflowExecutionEngine._handle_multi_agent_completion()
  → _evaluate_and_rank_executions()
    → For Rubric objects:
        ValidationContext.set_evaluable_resources()
        → ValidationEngine._evaluate_single_rubric() per criterion
    → For callable functions:
        evaluator(resources, task, workflow)
```

---

### **3. Pre-Execution Rubric Generation (GRPO Training)**
- **Location**: `manager_agent_gym/core/workflow/phases/multi_rubric_training.py`
- **Purpose**: Generate synthetic rubrics via manager-stakeholder dialogue for GRPO training
- **Key Features**:
  - Generates N synthetic rubrics through dialogue
  - Creates workers with rubrics injected into system prompts
  - Tracks rubric generation metadata (cost, turns, cognitive burden)
  - Sets ground truth rubric as `completion_evaluator` on all tasks
- **Context**: Uses rubric generation dialogue loop
- **Entry Point**: `MultiRubricTrainingPhase.run()`

**Flow**:
```
MultiRubricTrainingPhase.run()
  → _generate_single_rubric() × N [synthetic rubrics]
  → convert_to_rubric() [ground truth]
  → _create_worker_with_rubric() for each synthetic
  → task.completion_evaluators = [gt_rubric]
```

---

### **4. WorkflowValidationRule (Legacy Validation System)**
- **Location**: `manager_agent_gym/core/evaluation/engine/validation_rules.py`
- **Purpose**: Legacy workflow-level validation rules (pre-rubric system)
- **Key Features**:
  - Supports both function-based and LLM-based validation
  - Uses `ValidationContext` from `success_criteria.py`
  - Has its own LLM prompt formatting and scoring
  - Returns `ValidationResult` objects
- **Status**: **APPEARS TO BE LEGACY / UNUSED?**
- **Entry Point**: `WorkflowValidationRule.validate()`

---

### **5. CodeRuleExecutor (Direct Code Execution)**
- **Location**: `manager_agent_gym/core/evaluation/engine/code_rule_executor.py`
- **Purpose**: Execute Python code rules with simple `list[Resource]` API
- **Key Features**:
  - Sandboxed execution with helpful imports (pandas, numpy, etc.)
  - Simple signature: `evaluate(resources: list[Resource]) → float | tuple[float, str]`
  - Used by `ValidationEngine._evaluate_single_rubric()`
- **Used By**: ValidationEngine, Task Completion Evaluators (via ValidationEngine)

---

### **6. MultimodalEvaluator (LLM Judge with Vision)**
- **Location**: `manager_agent_gym/core/evaluation/engine/multimodal_llm.py`
- **Purpose**: GPT-4 Vision-based evaluation of multimodal outputs
- **Key Features**:
  - Converts PDFs, Excel, images to multimodal prompts
  - Single LLM call with structured output parsing
  - Detailed scoring rubric in system prompt
  - Used by `ValidationEngine._evaluate_single_rubric()`
- **Used By**: ValidationEngine, Task Completion Evaluators (via ValidationEngine)

---

### **7. Constraint/Stakeholder/Efficiency Evaluators (Domain-Specific Rules)**
- **Locations**:
  - `manager_agent_gym/core/evaluation/rules/constraint_evaluator.py`
  - `manager_agent_gym/core/evaluation/rules/stakeholder_evaluator.py`
  - `manager_agent_gym/core/evaluation/rules/operational_efficiency_evaluator.py`
  - `manager_agent_gym/core/evaluation/rules/common_evaluators.py`
- **Purpose**: Domain-specific validation logic for workflow properties
- **Status**: **UNCLEAR IF STILL USED?**

---

## 🔴 **Key Duplications & Inconsistencies**

### **1. TWO ValidationContext Classes**

**Problem**: There are two `ValidationContext` classes with overlapping but different APIs:

| Feature | `success_criteria.ValidationContext` | `validation_context.ValidationContext` |
|---------|--------------------------------------|---------------------------------------|
| **File** | `core/evaluation/schemas/success_criteria.py` | `core/evaluation/schemas/validation_context.py` |
| **Resources API** | `get_evaluable_resources()` | `get_evaluable_resources()` + `files` property |
| **Set Override** | ✅ `set_evaluable_resources()` (NEW) | ✅ `set_evaluable_resources()` |
| **Context Fields** | Many optional fields (manager_actions, communications, etc.) | Minimal (workflow, timestep) |
| **File Accessor** | ❌ None | ✅ `FileAccessor` with `read_excel()`, `read_pdf()`, etc. |
| **Used By** | ValidationEngine, Task Completion Evaluators | **UNCLEAR - may be unused?** |

**Status**: Just added `set_evaluable_resources()` to `success_criteria.ValidationContext` to fix task evaluation bug. **But the other one has better file access API!**

---

### **2. Multiple LLM Judge Implementations**

**Problem**: Three different ways to evaluate using LLM:

1. **MultimodalEvaluator** (`multimodal_llm.py`):
   - Modern, multimodal, uses Instructor for structured outputs
   - Detailed scoring rubric in system prompt
   - Used by ValidationEngine

2. **WorkflowValidationRule with LLM** (`validation_rules.py`):
   - Legacy system with custom prompt formatting
   - Uses `LLMScoredResponse` schema
   - **Possibly unused?**

3. **RubricCriteria.llm_prompt** (in ValidationEngine):
   - Delegates to `MultimodalEvaluator`
   - This is the modern path

**Recommendation**: Deprecate WorkflowValidationRule LLM path if not used.

---

### **3. Multiple Evaluation Result Types**

**Problem**: Different evaluation methods return different result types:

1. **EvaluatedScore** (`core/common/schemas/evaluators.py`):
   - Used by ValidationEngine internals
   - Fields: `score`, `reasoning`

2. **ValidationResult** (`success_criteria.py`):
   - Used by WorkflowValidationRule
   - Fields: `score`, `max_score`, `passed`, `message`, `level`, `metric`, `weight`, `meta`

3. **RubricResult** (`schemas/preferences/evaluation.py`):
   - Used by ValidationEngine output
   - Fields: `name`, `score`, `max_score`, `normalized_score`, `message`, `error`, `raw_output`

4. **EvaluationResult** (engine.py, local to `_evaluate_and_rank_executions`):
   - Just for task completion evaluators
   - Fields: `score`, `evaluation_metadata`

**Status**: Too many overlapping types. **Should consolidate to 1-2 core types.**

---

### **4. Rubric Execution in Two Places**

**Problem**: Rubric criteria can be evaluated in two different contexts:

1. **Timestep Evaluation** (ValidationEngine):
   - Context has many optional fields
   - Resources come from `workflow.tasks[].output_resource_ids`
   - Used for preference evaluation during workflow execution

2. **Task Completion Evaluation** (WorkflowExecutionEngine):
   - Context has explicit resources set
   - Resources come from `TaskExecution.output_resource_ids`
   - Used for multi-agent ranking

**Current Solution**: Both now use `ValidationEngine._evaluate_single_rubric()` with `set_evaluable_resources()` override.

**Good!** ✅ This unification was the fix we just implemented.

---

### **5. Legacy Evaluator Rules (Unclear if Used)**

**Problem**: Several evaluator modules exist but their usage is unclear:

- `constraint_evaluator.py`
- `stakeholder_evaluator.py`
- `operational_efficiency_evaluator.py`
- `common_evaluators.py`
- `validation_rules.py` (WorkflowValidationRule)

**Recommendation**: Audit usage and deprecate if not actively used.

---

## ✅ **What's Working Well**

1. **CodeRuleExecutor**: Clean, simple API. Reused correctly.
2. **MultimodalEvaluator**: Modern, powerful, well-designed.
3. **ValidationEngine**: Central orchestrator with good concurrency control.
4. **Recent Unification**: Task completion evaluators now use `ValidationEngine._evaluate_single_rubric()` ✅

---

## 🎯 **Refactoring Recommendations**

### **Priority 1: Consolidate ValidationContext** 🔥

**Problem**: Two `ValidationContext` classes with different features.

**Recommendation**:
1. **Merge features** from `validation_context.py` into `success_criteria.py`:
   - Keep the `FileAccessor` with `read_excel()`, `read_pdf()`, etc.
   - Keep the `set_evaluable_resources()` method (just added)
   - Keep the optional context fields for timestep evaluation
2. **Delete** `validation_context.py`
3. **Update all imports** to use single `ValidationContext`

**Impact**: Low risk, high clarity. All code using `ValidationEngine` already uses the right one.

---

### **Priority 2: Audit & Remove Legacy Evaluators** 🔍

**Problem**: Many evaluator modules with unclear usage.

**Action Items**:
1. Search codebase for usage of:
   - `WorkflowValidationRule`
   - `constraint_evaluator.*`
   - `stakeholder_evaluator.*`
   - `operational_efficiency_evaluator.*`
   - `common_evaluators.*`
2. If unused, deprecate and remove
3. If used, document their purpose and integration point

---

### **Priority 3: Consolidate Result Types** 📦

**Problem**: 4 different evaluation result types.

**Recommendation**:
1. Keep **EvaluatedScore** as internal type for ValidationEngine
2. Keep **RubricResult** for ValidationEngine public API
3. **Deprecate** ValidationResult (if WorkflowValidationRule is removed)
4. Task completion evaluators can continue using ad-hoc dicts (OK for now)

---

### **Priority 4: Document Evaluation Paths** 📚

**Problem**: No clear documentation of when/how each evaluation system is used.

**Recommendation**: Create architecture doc explaining:
- **Timestep Evaluation** (ValidationEngine + preferences): When, why, what
- **Task Completion Evaluation** (multi-agent ranking): When, why, what
- **Pre-Execution Rubric Generation** (GRPO training): When, why, what

---

## 📊 **Evaluation System Decision Tree**

```
┌─ Need to evaluate workflow state at a timestep? (e.g., preferences, constraints)
│  └─> Use ValidationEngine.evaluate_timestep()
│      - Handles code rules + LLM judges
│      - Aggregates scores hierarchically
│      - Maintains reward vector
│
├─ Need to rank N worker outputs for a task?
│  └─> Use task.completion_evaluators (evaluated by engine)
│      - Can be Rubric objects (delegates to ValidationEngine)
│      - Can be callable functions
│      - Results stored on TaskExecution
│
├─ Need to generate rubrics via dialogue?
│  └─> Use MultiRubricTrainingPhase (or baseline phases)
│      - Generates synthetic rubrics
│      - Creates workers with rubric guidance
│      - Sets ground truth as completion_evaluator
│
└─ Need custom validation logic?
   └─> Write CodeRule (Python function) or LLMJudgeRule (prompt)
       - Both work via RubricCriteria
       - Executed by ValidationEngine
```

---

## 🚀 **Next Steps**

1. **✅ DONE**: Task completion evaluators now use `ValidationEngine._evaluate_single_rubric()`
2. **✅ DONE**: Added `set_evaluable_resources()` to `success_criteria.ValidationContext`
3. **🔍 TODO**: Audit legacy evaluator usage (constraint, stakeholder, operational_efficiency)
4. **🔥 TODO**: Merge `validation_context.py` features into `success_criteria.py` and delete duplicate
5. **📚 TODO**: Document evaluation architecture in main docs

---

## 💡 **Discussion Points**

1. **Should we keep `validation_context.py`'s `FileAccessor`?**
   - YES - it's a much better API for code rules
   - Merge it into the main ValidationContext

2. **Should we deprecate WorkflowValidationRule?**
   - Need to check usage first
   - If unused, remove it

3. **Should task.completion_evaluators support only Rubric objects?**
   - Current design allows both Rubric and callable
   - Callable is more flexible for custom logic
   - Keep both for now

4. **Should we have a unified "Evaluator" interface?**
   - Currently: Rubric, callable functions, legacy validators
   - Could simplify to: `Evaluator` ABC with `evaluate(resources) → score`
   - But current design is working well after recent fixes

---

**End of Audit**

