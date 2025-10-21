from __future__ import annotations

from manager_agent_gym.schemas.domain.workflow import Workflow
from manager_agent_gym.schemas.preferences.preference import (
    Preference,
    PreferenceSnapshot,
)
from manager_agent_gym.schemas.preferences.evaluator import (
    Rubric,
    AggregationStrategy,
)
from manager_agent_gym.schemas.preferences.rubric import RubricCriteria, RunCondition
from manager_agent_gym.schemas.preferences import PreferenceWeightUpdateRequest
from examples.end_to_end_examples.standard_rules import (
    speed_rubric,
    cost_rubric,
)


def _reproducibility_signal(workflow: Workflow) -> float:
    keywords = (
        "seed",
        "deterministic",
        "requirements.txt",
        "environment.yml",
        "docker",
        "pip freeze",
        "mlflow",
        "wandb",
        "comet",
        "run id",
        "experiment id",
    )
    total = 0
    hits = 0
    for res in workflow.resources.values():
        total += 1
        try:
            content = (res.content or "").lower()
            if any(k in content for k in keywords):
                hits += 1
        except Exception:
            continue
    if total == 0:
        return 0.0
    return min(1.0, hits / max(1, total))


def _experiment_tracking_signal(workflow: Workflow) -> float:
    keywords = ("mlflow", "wandb", "weights & biases", "comet", "tensorboard")
    total = 0
    hits = 0
    for res in workflow.resources.values():
        total += 1
        try:
            content = (res.content or "").lower()
            if any(k in content for k in keywords):
                hits += 1
        except Exception:
            continue
    if total == 0:
        return 0.0
    return min(1.0, hits / max(1, total))


def _dq_test_density(workflow: Workflow) -> float:
    keywords = ("test", "assert", "validation", "great expectations", "dq check")
    total = 0
    hits = 0
    for res in workflow.resources.values():
        total += 1
        try:
            content = (res.content or "").lower()
            if any(k in content for k in keywords):
                hits += 1
        except Exception:
            continue
    if total == 0:
        return 0.0
    return min(1.0, hits / max(1, total))


def _pct_tasks_completed(workflow: Workflow, name_contains: str | None = None) -> float:
    tasks = list(workflow.tasks.values())
    if name_contains:
        tasks = [t for t in tasks if name_contains.lower() in (t.name or "").lower()]
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if t.status.value == "completed")
    return done / len(tasks)


def create_preferences() -> PreferenceSnapshot:
    # Technical quality rubrics
    quality_rubrics = [
        RubricCriteria(
            name="beam_training_stability",
            llm_prompt=(
                "Assess beam training stability: convergence reliability, sensitivity to pose changes, and RIS-on vs off delta. "
                "Return numeric score [0, 10] with evidence."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="dataset_quality",
            llm_prompt=(
                "Evaluate sounding dataset quality: coverage of poses, metadata completeness, labeling consistency, and baseline comparisons. "
                "Return numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="reproducibility_signal",
            evaluator_function=_reproducibility_signal,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="experiment_tracking_signal",
            evaluator_function=_experiment_tracking_signal,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
        RubricCriteria(
            name="dq_test_density",
            evaluator_function=_dq_test_density,
            max_score=1.0,
            run_condition=RunCondition.EACH_TIMESTEP,
        ),
    ]

    # Security and compliance rubrics
    seccomp_rubrics = [
        RubricCriteria(
            name="security_telemetry_present",
            llm_prompt=(
                "Assess presence and usefulness of security telemetry: jamming/spoofing detection signals, logging, and alerting. "
                "Return numeric score [0, 10]."
            ),
            max_score=10.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="threat_model_and_drill",
            llm_prompt=(
                "Evaluate threat model completeness and execution of at least one drill; capture observations and mitigations. "
                "Return numeric score [0, 8]."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="indoor_compliance_and_safety",
            llm_prompt=(
                "Evaluate indoor compliance: spectrum plan, EIRP limits, safety/ethics approvals, and signage. "
                "Return numeric score [0, 8]."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    # Speed & cost
    speed_rubrics = [
        RubricCriteria(
            name="speed_efficiency",
            evaluator_function=speed_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]
    cost_rubrics = [
        RubricCriteria(
            name="cost_efficiency",
            evaluator_function=cost_rubric,
            max_score=1.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]

    return PreferenceSnapshot(
        preferences=[
            Preference(
                name="technical_quality",
                weight=0.45,
                evaluator=Rubric(
                    name="technical_quality_eval",
                    description="THz+RIS prototype technical quality and reproducibility",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=quality_rubrics,
                ),
            ),
            Preference(
                name="security_compliance",
                weight=0.25,
                evaluator=Rubric(
                    name="security_compliance_eval",
                    description="Security telemetry, drills, and indoor compliance",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=seccomp_rubrics,
                ),
            ),
            Preference(
                name="speed",
                weight=0.15,
                evaluator=Rubric(
                    name="speed_eval",
                    description="delivery speed",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=speed_rubrics,
                ),
            ),
            Preference(
                name="cost",
                weight=0.15,
                evaluator=Rubric(
                    name="cost_eval",
                    description="cost discipline",
                    aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
                    criteria=cost_rubrics,
                ),
            ),
        ],
        timestep=0,
    )


def create_preference_update_requests() -> list[PreferenceWeightUpdateRequest]:
    timeline: dict[int, PreferenceSnapshot] = {
        0: PreferenceSnapshot(
            preferences=[
                Preference(name="technical_quality", weight=0.45),
                Preference(name="security_compliance", weight=0.25),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.15),
            ]
        ),
        15: PreferenceSnapshot(
            preferences=[
                Preference(name="technical_quality", weight=0.4),
                Preference(name="security_compliance", weight=0.3),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.15),
            ]
        ),
        30: PreferenceSnapshot(
            preferences=[
                Preference(name="technical_quality", weight=0.35),
                Preference(name="security_compliance", weight=0.35),
                Preference(name="speed", weight=0.15),
                Preference(name="cost", weight=0.15),
            ]
        ),
    }
    requests: list[PreferenceWeightUpdateRequest] = []
    for ts, weights in sorted(timeline.items(), key=lambda kv: kv[0]):
        changes = weights.get_preference_dict()
        if not changes:
            continue
        requests.append(
            PreferenceWeightUpdateRequest(
                timestep=ts,
                changes=changes,
                mode="absolute",
                normalize=True,
                clamp_zero=True,
                missing="create_zero",
                redistribution="proportional",
            )
        )
    return requests


def create_evaluator_to_measure_goal_achievement() -> Rubric:
    goal_achievement_rubrics = [
        RubricCriteria(
            name="nlos_demo_with_ris_gain",
            llm_prompt=(
                "Confirm NLOS demo achieves RIS-on vs off delta ≥ 8 dB SNR or ≥2× throughput; cite measured logs and plots. "
                "Return 18.0 if met, deduct 6.0 if partially met, else 0.0."
            ),
            max_score=18.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="sounding_dataset_and_release",
            llm_prompt=(
                "Verify dataset release completeness: ≥200 poses, metadata, scripts, and environment pinning. "
                "Return 15.0 if complete, 8.0 if partial, 0.0 otherwise."
            ),
            max_score=15.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="security_drill_observed",
            llm_prompt=(
                "Confirm at least one adversarial drill executed with telemetry captures and observations documented. "
                "Return 12.0 if complete, 6.0 if partial, 0.0 otherwise."
            ),
            max_score=12.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
        RubricCriteria(
            name="final_report_submitted",
            llm_prompt=(
                "Verify final report presence with methods, baselines, limitations, and reproducibility notes. "
                "Return 8.0 if complete, 4.0 if partial, 0.0 otherwise."
            ),
            max_score=8.0,
            run_condition=RunCondition.ON_COMPLETION,
        ),
    ]
    return Rubric(
        name="sixg_thz_ris_goal_achievement_eval",
        description="6G THz+RIS prototype achievement",
        aggregation=AggregationStrategy.WEIGHTED_AVERAGE,
        criteria=goal_achievement_rubrics,
    )
