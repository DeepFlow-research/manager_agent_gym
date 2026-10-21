"""
Team-membership non-stationarity metrics for existing runs
(docs/team_non_stationarity/metrics.md).

Reads only already-generated files under <outputs>/<mode>/<workflow>/run_<id>/
(workflow_outputs/ per-timestep snapshots), where <outputs> is dashboard/outputs or
$MAG_OUTPUTS_DIR. It never launches a simulation or calls an LLM.

For each (workflow, manager mode) it computes post-change score, baseline score, and
disruption cost, prints a comparison table, and writes team_change_metrics.json into the
run directory (read by the dashboard's Metrics page).

A scenario opts in by providing, under examples/specialist_loss/<workflow>/:
  - team_change_spec.py exposing create_team_change_spec() -> TeamChangeSpec
  - workflow.py exposing create_workflow(), whose tasks carry `requirements`
    (TaskRequirement with a `pattern`) for every affected task

Usage:
    python dashboard/analysis/analyze_team_changes.py --workflow legal_m_and_a_team --mode cot random
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from dashboard.analysis.analyze_runs import (  # noqa: E402
    extract_run_id,
    find_run_dir,
    load_json,
)
from manager_agent_gym.core.evaluation.task_requirements_evaluator import (  # noqa: E402
    requirements_by_task_name,
)
from manager_agent_gym.core.evaluation.team_change_metrics import (  # noqa: E402
    TeamChangeSpec,
    compute_team_change_metrics,
)
from manager_agent_gym.schemas.core.tasks import TaskRequirement  # noqa: E402


SCENARIO_PACKAGE = "examples.specialist_loss"
OUTPUT_NAME = "team_change_metrics.json"
# Managers benchmarked for this focus; assign_all is excluded (docs/team_non_stationarity/index.md).
DEFAULT_MODES = ["cot", "random"]


def load_scenario(workflow: str) -> tuple[TeamChangeSpec, dict[str, list[TaskRequirement]]]:
    """Import the scenario's spec and its tasks' checklists (by task name).
    `workflow` may be the run label (`legal_m_and_a_team`) or the scenario name."""
    workflow = workflow.removesuffix('_team_static').removesuffix('_team')
    try:
        spec_mod = importlib.import_module(f"{SCENARIO_PACKAGE}.{workflow}.team_change_spec")
    except ModuleNotFoundError as e:
        raise SystemExit(
            f"No team-change spec for '{workflow}': expected "
            f"{SCENARIO_PACKAGE}.{workflow}.team_change_spec ({e})"
        )
    workflow_mod = importlib.import_module(f"{SCENARIO_PACKAGE}.{workflow}.workflow")
    wf = workflow_mod.create_workflow()
    requirements = requirements_by_task_name(wf.tasks.values())
    return spec_mod.create_team_change_spec(), requirements


def load_snapshots(run_dir: Path, run_id: str) -> dict[int, dict]:
    """timestep -> workflow snapshot, from workflow_outputs/workflow_execution_<id>_t<NNNN>.json."""
    prefix = f"workflow_execution_{run_id}_t"
    snapshots: dict[int, dict] = {}
    for path in (run_dir / "workflow_outputs").glob(f"{prefix}*.json"):
        snap = load_json(path)
        if snap:
            snapshots[int(path.stem[len(prefix):])] = snap
    return snapshots


def analyze(workflow: str, mode: str, seed: int | None, spec, requirements) -> dict | None:
    run_dir = find_run_dir(workflow, mode, seed)
    if run_dir is None:
        print(f"[skip] no run for {workflow}/{mode} (seed={seed})")
        return None
    snapshots = load_snapshots(run_dir, extract_run_id(run_dir))
    if not snapshots:
        print(f"[skip] no workflow snapshots in {run_dir}")
        return None
    metrics = compute_team_change_metrics(spec, snapshots, requirements)
    metrics.update(workflow=workflow, manager_mode=mode, run_dir=str(run_dir))
    (run_dir / OUTPUT_NAME).write_text(json.dumps(metrics, indent=2))
    return metrics


def _fmt(v: float | None) -> str:
    return "n/a" if v is None else f"{v:.3f}"


def print_table(results: list[dict]) -> None:
    header = (
        f"{'workflow':<22} {'mode':<10} {'post_change':>11} {'baseline':>9} {'gap':>7} "
        f"{'disruption':>11}  by_case"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['workflow']:<22} {r['manager_mode']:<10} {_fmt(r['post_change_score']):>11} "
            f"{_fmt(r['baseline_score']):>9} {_fmt(r['post_change_gap']):>7} "
            f"{_fmt(r['disruption_cost']):>11}  "
            + " ".join(f"{c}={_fmt(v['post_change_score'])}" for c, v in r["by_case"].items())
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workflow", nargs="+", required=True)
    ap.add_argument("--mode", nargs="+", default=DEFAULT_MODES)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    results: list[dict] = []
    for workflow in args.workflow:
        spec, requirements = load_scenario(workflow)
        for mode in args.mode:
            res = analyze(workflow, mode, args.seed, spec, requirements)
            if res:
                results.append(res)
    print_table(results)


if __name__ == "__main__":
    main()
