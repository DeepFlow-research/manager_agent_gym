"""Load GDPEval staged rubrics into MA-Gym format."""

import json
from pathlib import Path

from manager_agent_gym.core.agents.manager_agent.implementations.rubric_generation_manager.rubric_generation import (
    ManagerAgentGeneratedStagedRubric,
    EvaluationStageSpec,
    CodeRule,
    LLMJudgeRule,
)


def load_gdpeval_rubric(
    jsonl_path: Path | str, task_id: str
) -> ManagerAgentGeneratedStagedRubric:
    """Load a staged rubric from GDPEval JSONL file by task ID.
    
    Args:
        jsonl_path: Path to staged_rubrics.jsonl file
        task_id: GDPEval task ID to load
        
    Returns:
        ManagerAgentGeneratedStagedRubric ready for MA-Gym use
        
    Raises:
        ValueError: If task_id not found in file
    """
    jsonl_path = Path(jsonl_path)
    
    with open(jsonl_path) as f:
        for line in f:
            rubric_data = json.loads(line)
            if rubric_data["task_id"] == task_id:
                # Convert dict rules to proper Rule objects
                stages = []
                for stage_dict in rubric_data["rubric"]["stages"]:
                    rules = []
                    for rule_dict in stage_dict["rules"]:
                        if rule_dict["type"] == "code":
                            rules.append(CodeRule(**rule_dict))
                        elif rule_dict["type"] == "llm_judge":
                            rules.append(LLMJudgeRule(**rule_dict))
                    
                    stages.append(
                        EvaluationStageSpec(
                            name=stage_dict["name"],
                            description=stage_dict["description"],
                            is_required=stage_dict["is_required"],
                            min_score_to_pass=stage_dict["min_score_to_pass"],
                            rules=rules,
                            max_points=stage_dict["max_points"],
                            on_failure_action=stage_dict["on_failure_action"],
                            on_failure_score=stage_dict.get("on_failure_score", 0.0),
                        )
                    )
                
                return ManagerAgentGeneratedStagedRubric(
                    category_name=rubric_data["rubric"]["category_name"],
                    rationale=rubric_data["rubric"].get("rationale"),
                    max_total_score=rubric_data["rubric"]["max_total_score"],
                    stages=stages,
                )
    
    raise ValueError(f"Task {task_id} not found in {jsonl_path}")


def load_all_gdpeval_rubrics(
    jsonl_path: Path | str,
) -> dict[str, ManagerAgentGeneratedStagedRubric]:
    """Load all rubrics from GDPEval JSONL file.
    
    Args:
        jsonl_path: Path to staged_rubrics.jsonl file
        
    Returns:
        Dictionary mapping task_id to ManagerAgentGeneratedStagedRubric
    """
    jsonl_path = Path(jsonl_path)
    rubrics = {}
    
    with open(jsonl_path) as f:
        for line in f:
            rubric_data = json.loads(line)
            task_id = rubric_data["task_id"]
            
            # Convert using single rubric loader logic
            try:
                rubric = load_gdpeval_rubric(jsonl_path, task_id)
                rubrics[task_id] = rubric
            except Exception as e:
                print(f"Warning: Failed to load rubric for {task_id}: {e}")
                continue
    
    return rubrics


def get_default_gdpeval_rubrics_path() -> Path:
    """Get default path to GDPEval rubrics file.
    
    Returns:
        Path to staged_rubrics.jsonl in curation/gdpeval/data/generated/staged_v4/
    """
    # Assumes we're in manager_agent_gym package
    from manager_agent_gym import __file__ as pkg_file
    pkg_root = Path(pkg_file).parent.parent
    
    return pkg_root / "curation" / "gdpeval" / "data" / "generated" / "staged_v4" / "staged_rubrics.jsonl"

