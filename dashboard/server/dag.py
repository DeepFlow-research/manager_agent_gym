"""Scenario discovery and task graphs.

Builds each scenario's workflow exactly as authored (workflow.py only constructs pydantic
Task objects, no LLM or network call) and lays graphs out in layers. The side-by-side
comparison built on top of this lives in compare.py.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from manager_agent_gym.core.evaluation.task_requirements_evaluator import flatten_tasks

from .data import REPO_ROOT

# Scenario collections, in the order they are offered. `end_to_end_examples` holds the
# originals; `specialist_loss` holds the team-membership non-stationarity variants.
SCENARIO_ROOTS = ["end_to_end_examples", "specialist_loss"]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def list_scenarios() -> list[dict[str, str]]:
    out = []
    for root in SCENARIO_ROOTS:
        base = REPO_ROOT / "examples" / root
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if (d / "workflow.py").exists():
                out.append({"id": f"{root}/{d.name}", "collection": root, "name": d.name})
    return out


def _try_call_zero_arg(fn) -> Any | None:
    try:
        sig = inspect.signature(fn)
        if any(
            p.default is inspect.Parameter.empty
            and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            for p in sig.parameters.values()
        ):
            return None
        return fn()
    except Exception:
        return None


def _find_workflow(module: Any) -> Any | None:
    """Conventional factory names first, then any zero-arg function with 'workflow' in its name."""
    for name in ("create_workflow", "build_workflow", "make_workflow", "init_workflow"):
        fn = getattr(module, name, None)
        if callable(fn):
            wf = _try_call_zero_arg(fn)
            if getattr(wf, "tasks", None) is not None:
                return wf
    for name, fn in inspect.getmembers(module, inspect.isfunction):
        if "workflow" in name.lower():
            wf = _try_call_zero_arg(fn)
            if getattr(wf, "tasks", None) is not None:
                return wf
    return None


def _load_workflow(scenario_id: str) -> Any:
    root, _, name = scenario_id.partition("/")
    if root not in SCENARIO_ROOTS or not name or "/" in name or ".." in name:
        raise KeyError(scenario_id)
    path: Path = REPO_ROOT / "examples" / root / name / "workflow.py"
    if not path.exists():
        raise KeyError(scenario_id)
    spec = importlib.util.spec_from_file_location(f"_dashboard_{root}_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    wf = _find_workflow(module)
    if wf is None:
        raise ValueError(f"no workflow factory found in {path}")
    return wf


def _task_view(t: Any) -> dict[str, Any]:
    """A top-level task as one graph node. Its checklist also counts its subtasks', since only
    top-level tasks are drawn; `covers` lists every task name the node stands for."""
    flat = flatten_tasks([t])
    items = [{"key": r.key, "pattern": r.pattern} for x in flat for r in x.requirements]
    return {
        "name": t.name,
        "description": t.description or "",
        "subtask_count": len(getattr(t, "subtasks", None) or []),
        "requirements": [i["key"] for i in items],
        "requirement_items": items,
        "covers": [x.name for x in flat],
    }


@lru_cache(maxsize=32)
def _load_graph_cached(scenario_id: str, mtime: float) -> dict[str, Any]:
    wf = _load_workflow(scenario_id)
    by_id = {str(tid): t for tid, t in wf.tasks.items()}
    tasks = {t.name: _task_view(t) for t in by_id.values()}
    edges = sorted(
        {
            (by_id[str(d)].name, t.name)
            for t in by_id.values()
            for d in (t.dependency_task_ids or [])
            if str(d) in by_id
        }
    )
    return {"tasks": tasks, "edges": edges}


def load_graph(scenario_id: str) -> dict[str, Any]:
    root, _, name = scenario_id.partition("/")
    path = REPO_ROOT / "examples" / root / name / "workflow.py"
    # Keyed on mtime so an edited workflow.py is picked up without restarting the server.
    return _load_graph_cached(scenario_id, path.stat().st_mtime if path.exists() else 0.0)


def _layout(names: list[str], edges: list[tuple[str, str]]) -> dict[str, tuple[int, int]]:
    """name -> (layer, row). Longest-path layering, then one barycenter pass per layer."""
    deps: dict[str, list[str]] = {n: [] for n in names}
    for a, b in edges:
        deps[b].append(a)
    layer: dict[str, int] = {}

    def depth(n: str, seen: tuple[str, ...] = ()) -> int:
        if n in layer:
            return layer[n]
        if n in seen:  # cycle guard: should not happen for a real workflow
            return 0
        layer[n] = 1 + max((depth(d, (*seen, n)) for d in deps[n]), default=-1)
        return layer[n]

    for n in names:
        depth(n)

    layers: dict[int, list[str]] = {}
    for n in sorted(names):
        layers.setdefault(layer[n], []).append(n)

    pos: dict[str, tuple[int, int]] = {}
    prev: dict[str, float] = {}
    for l in range(max(layers, default=-1) + 1):
        nodes = layers.get(l, [])
        if prev:

            def bary(n: str) -> float:
                ps = [prev[d] for d in deps[n] if d in prev]
                return sum(ps) / len(ps) if ps else float(len(prev))

            nodes.sort(key=bary)
        for row, n in enumerate(nodes):
            pos[n] = (l, row)
        prev = {n: float(i) for i, n in enumerate(nodes)}
    return pos

