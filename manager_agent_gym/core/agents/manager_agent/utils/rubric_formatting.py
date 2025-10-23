"""
Utilities for formatting rubrics as human-readable text for workers.

Workers should receive clean, readable evaluation criteria without
implementation details like Python code or complex JSON structures.
"""

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedRubricWithMetadata,
    ManagerAgentGeneratedStagedRubric,
    CodeRule,
    LLMJudgeRule,
)


def format_rubric_for_worker(rubric: ManagerAgentGeneratedRubricWithMetadata) -> str:
    """Format a rubric as clean markdown for worker consumption.

    Workers get complete transparency:
    - What criteria they'll be evaluated on
    - The relative importance (weights)
    - Whether it's automated or human review
    - The actual Python code that will evaluate automated checks
    - Judge prompts for LLM evaluations
    - What's expected for qualitative criteria

    This allows workers to understand exactly how they'll be evaluated
    and write code/content that explicitly addresses each criterion.

    Args:
        rubric: Rubric to format

    Returns:
        Clean markdown representation with full evaluation details
    """
    lines = []

    # Header
    lines.append("## Evaluation Criteria")
    lines.append("")

    # Optional rationale (helps worker understand overall approach)
    if rubric.rationale:
        lines.append(f"**Evaluation Strategy:** {rubric.rationale}")
        lines.append("")

    lines.append("Your work will be assessed against these specific criteria:")
    lines.append("")

    # Calculate total weight for percentage display
    total_weight = rubric.get_total_weight()

    # Format each rule
    for i, rule in enumerate(rubric.rules, 1):
        # Calculate percentage
        weight_pct = (rule.weight / total_weight * 100) if total_weight > 0 else 0

        # Rule header with weight
        lines.append(f"### {i}. {rule.name} (Weight: {weight_pct:.0f}%)")

        # Type indicator (automated vs human review)
        if isinstance(rule, CodeRule):
            rule_type = "Automated Check"
        elif isinstance(rule, LLMJudgeRule):
            rule_type = "Expert Review"
        else:
            rule_type = "Evaluation"
        lines.append(f"**Type:** {rule_type}")

        # Description
        lines.append(f"**Description:** {rule.description}")

        # For code rules, show the actual evaluation code
        if isinstance(rule, CodeRule):
            lines.append("")
            lines.append("**Evaluation Code:**")
            lines.append("```python")
            lines.append(rule.code)
            lines.append("```")

        # For LLM judge rules, include expectations and judge prompt
        if isinstance(rule, LLMJudgeRule):
            if rule.expectation:
                lines.append(f"**Expected Outcome:** {rule.expectation}")
            lines.append("")
            lines.append("**Judge Evaluation Prompt:**")
            lines.append(f"> {rule.judge_prompt}")

        lines.append("")

    # Footer note
    lines.append("---")
    lines.append(
        "**Note:** Address each criterion in your work. For automated checks, you can see exactly what will be validated. For expert reviews, ensure your work addresses the evaluation prompt."
    )

    return "\n".join(lines)


def format_rubric_summary(rubric: ManagerAgentGeneratedRubricWithMetadata) -> str:
    """Create a brief summary of the rubric.

    Useful for logging or quick overview.

    Args:
        rubric: Rubric to summarize

    Returns:
        Brief text summary
    """
    rule_count = len(rubric.rules)
    code_count = sum(1 for r in rubric.rules if isinstance(r, CodeRule))
    llm_count = sum(1 for r in rubric.rules if isinstance(r, LLMJudgeRule))

    return (
        f"Rubric '{rubric.rubric_id}': {rule_count} criteria "
        f"({code_count} automated, {llm_count} expert review)"
    )


def format_staged_rubric_for_worker(rubric: ManagerAgentGeneratedStagedRubric) -> str:
    """Format a STAGED rubric as clean markdown for worker consumption.
    
    Stages provide clear progression: validation gates → correctness → quality.
    Workers understand what MUST pass vs what contributes to final score.
    
    Args:
        rubric: Staged rubric to format
    
    Returns:
        Clean markdown with stage structure
    """
    lines = []
    
    # Header
    lines.append(f"## Evaluation Rubric: {rubric.category_name}")
    lines.append("")
    
    # Rationale
    if rubric.rationale:
        lines.append(f"**Evaluation Approach:** {rubric.rationale}")
        lines.append("")
    
    lines.append(f"**Maximum Score:** {rubric.max_total_score:.1f} points")
    lines.append("")
    lines.append("Your work will be evaluated in sequential stages:")
    lines.append("")
    
    # Format each stage
    for stage_num, stage in enumerate(rubric.stages, 1):
        # Stage header with gate indicator
        gate_indicator = "🚪 **GATE**" if stage.is_required else ""
        lines.append(f"### Stage {stage_num}: {stage.name} {gate_indicator}")
        lines.append("")
        lines.append(f"**Description:** {stage.description}")
        lines.append(f"**Max Points:** {stage.max_points:.1f}")
        
        if stage.is_required:
            lines.append(f"**Gate Threshold:** Must score at least {stage.min_score_to_pass:.0%} to proceed")
            lines.append(f"**On Failure:** {stage.on_failure_action}")
        
        lines.append("")
        lines.append(f"**Criteria in this stage:** ({len(stage.rules)} rules)")
        lines.append("")
        
        # Format rules in this stage
        for rule_num, rule in enumerate(stage.rules, 1):
            # Rule header
            lines.append(f"#### {stage_num}.{rule_num} {rule.name} ({rule.weight:.1f} pts)")
            
            # Type
            rule_type = "Automated Check" if rule.type == "code" else "Expert Review"
            lines.append(f"**Type:** {rule_type}")
            lines.append(f"**Description:** {rule.description}")
            
            # Show code or judge prompt
            if rule.type == "code":
                lines.append("")
                lines.append("**Evaluation Code:**")
                lines.append("```python")
                lines.append(rule.code)
                lines.append("```")
            elif rule.type == "llm_judge":
                if rule.expectation:
                    lines.append(f"**Expected:** {rule.expectation}")
                lines.append("")
                lines.append("**Judge Prompt:**")
                lines.append(f"> {rule.judge_prompt}")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Footer
    lines.append("**Note:** Stages are evaluated sequentially. If you fail a required gate, ")
    lines.append("evaluation may stop early. Ensure you meet all gate requirements!")
    
    return "\n".join(lines)


def format_staged_rubric_summary(rubric: ManagerAgentGeneratedStagedRubric) -> str:
    """Create a brief summary of a staged rubric.
    
    Args:
        rubric: Staged rubric to summarize
    
    Returns:
        Brief text summary
    """
    total_rules = sum(len(stage.rules) for stage in rubric.stages)
    gates = sum(1 for stage in rubric.stages if stage.is_required)
    
    return (
        f"Staged Rubric '{rubric.category_name}': {len(rubric.stages)} stages, "
        f"{total_rules} rules, {gates} gates, max score {rubric.max_total_score:.1f}"
    )
