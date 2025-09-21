from __future__ import annotations

import importlib
import sys
import inspect
from pathlib import Path
import os
from typing import Any, Callable
import importlib.util
from textwrap import shorten


DOCS_DIR = Path(__file__).parent
ROOT = DOCS_DIR.parent
EXAMPLES_PKG = "examples.end_to_end_examples"


def discover_scenarios() -> list[tuple[str, Path]]:
    """Return list of (scenario_name, directory_path) for each scenario.

    Includes both package (with __init__.py) and plain directories.
    """
    # Ensure project root is on path so `examples` is importable
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    base_pkg = importlib.import_module(EXAMPLES_PKG)
    base_dir = Path(base_pkg.__file__).parent  # type: ignore
    scenarios: list[tuple[str, Path]] = []
    for child in base_dir.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        # Skip caches/hidden
        if name.startswith("_") or name == "__pycache__":
            continue
        # Only include scenarios that actually have a workflow file
        if (child / "workflow.py").exists():
            scenarios.append((name, child))
    return scenarios


def import_module_from_path(module_path: Path, qualname: str) -> Any | None:
    try:
        if not module_path.exists():
            return None
        spec = importlib.util.spec_from_file_location(qualname, module_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[qualname] = mod
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod
    except Exception:
        return None


def get_callable(module: Any, *names: str) -> Callable[..., Any] | None:
    for n in names:
        fn = getattr(module, n, None)
        if callable(fn):
            return fn
    return None


def extract_goal_text(workflow_obj: Any) -> str:
    try:
        # Pydantic model with field `workflow_goal`
        goal = getattr(workflow_obj, "workflow_goal", None)
        if goal:
            return str(goal).strip()
    except Exception:
        pass
    return ""


def _try_call_zero_arg(fn: Callable[..., Any]) -> Any | None:
    try:
        sig = inspect.signature(fn)
        if any(
            p.default is inspect._empty
            and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            for p in sig.parameters.values()
        ):
            return None
        return fn()
    except Exception:
        return None


def find_workflow_factory(module: Any) -> Any | None:
    """Heuristic: find a function that returns a Workflow without requiring args."""
    if module is None:
        return None
    # Preferred names
    for name in ("create_workflow", "build_workflow", "make_workflow", "init_workflow"):
        fn = getattr(module, name, None)
        if callable(fn):
            wf = _try_call_zero_arg(fn)
            if getattr(wf, "workflow_goal", None) is not None:
                return wf
    # Any zero-arg function with "workflow" in name
    for name, fn in inspect.getmembers(module, inspect.isfunction):
        if "workflow" in name and callable(fn):
            wf = _try_call_zero_arg(fn)
            if getattr(wf, "workflow_goal", None) is not None:
                return wf
    # Global objects
    for name in ("WORKFLOW", "workflow"):
        obj = getattr(module, name, None)
        if getattr(obj, "workflow_goal", None) is not None:
            return obj
    return None


def summarize_workflow_stats(
    wf: Any,
    team_details: list[dict[str, Any]],
    schedule: dict[int, list[tuple[str, str]]],
) -> dict[str, int]:
    """Compute simple statistics for badges: tasks, constraints, team size, timeline length."""

    def _count_all_tasks(tasks_dict: dict) -> int:
        seen: set = set()
        total = 0
        try:
            for t in tasks_dict.values():
                if getattr(t, "id", None) in seen:
                    continue
                seen.add(getattr(t, "id", None))
                total += 1
                for st in getattr(t, "subtasks", []) or []:
                    if getattr(st, "id", None) not in seen:
                        total += 1
        except Exception:
            total = len(tasks_dict or {})
        return total

    stats = {
        "tasks": 0,
        "constraints": 0,
        "team": len(team_details or []),
        "timesteps": max(schedule.keys()) if schedule else 0,
    }
    try:
        stats["constraints"] = len(getattr(wf, "constraints", []) or [])
    except Exception:
        stats["constraints"] = 0
    try:
        tasks_dict = getattr(wf, "tasks", {}) or {}
        stats["tasks"] = _count_all_tasks(tasks_dict)
    except Exception:
        stats["tasks"] = 0
    return stats


def format_goal(goal_text: str) -> list[str]:
    """Pretty-format a long workflow goal string into sections.

    - Wrap main objective in an info admonition
    - Convert 'Primary deliverables:' lines to a bullet list when found
    - Convert 'Acceptance criteria' block to a bullet list when found
    """
    lines_out: list[str] = []
    text = goal_text.strip()
    # Split on Acceptance criteria to isolate it
    acc_idx = text.lower().find("acceptance criteria")
    objective = text if acc_idx == -1 else text[:acc_idx].strip()
    acceptance = "" if acc_idx == -1 else text[acc_idx:].strip()

    # Primary deliverables as bullets
    prim_idx = objective.lower().find("primary deliverables:")
    if prim_idx != -1:
        head = objective[:prim_idx].strip()
        rest = objective[prim_idx:].splitlines()
        lines_out.append('!!! info "Objective"\n')
        for ln in head.splitlines():
            lines_out.append(f"    {ln}\n")
        # Render deliverables bullets
        lines_out.append("\n")
        lines_out.append('??? note "Primary deliverables"\n')
        for ln in rest[1:]:
            ln = ln.strip(" -\t")
            if not ln:
                continue
            lines_out.append(f"    - {ln}\n")
        lines_out.append("\n")
    else:
        lines_out.append('!!! info "Objective"\n')
        for ln in objective.splitlines():
            lines_out.append(f"    {ln}\n")
        lines_out.append("\n")

    # Acceptance criteria bullets
    if acceptance:
        acc_lines = acceptance.splitlines()
        # Strip heading line
        if acc_lines:
            heading = acc_lines[0].strip(": ")
            lines_out.append(f'??? success "{heading}"\n')
            bullet_block = acc_lines[1:]
            for ln in bullet_block:
                clean = ln.strip(" -\t")
                if not clean:
                    continue
                lines_out.append(f"    - {clean}\n")
            lines_out.append("\n")
    return lines_out


def build_mermaid_workflow(wf: Any) -> list[str]:
    """Create a Mermaid DAG from workflow tasks and dependencies.

    - Uses dependency_task_ids for edges
    - Adds parent→subtask edges for structure
    """
    try:
        tasks: dict = getattr(wf, "tasks", {}) or {}
    except Exception:
        tasks = {}

    if not tasks:
        return []

    # Stable order
    task_items = list(tasks.items())
    task_items.sort(key=lambda kv: str(getattr(kv[1], "name", kv[0])))

    id_map: dict[str, str] = {}
    lines: list[str] = ["```mermaid\n", "flowchart TD\n"]

    def _clean(text: str) -> str:
        text = text.replace("\\", " ").replace("\n", " ")
        return text.replace('"', "'")

    # Nodes
    for idx, (tid, t) in enumerate(task_items, start=1):
        nid = f"n{idx}"
        id_map[str(tid)] = nid
        label = _clean(str(getattr(t, "name", str(tid))))
        # truncate long labels for readability
        if len(label) > 60:
            label = label[:57] + "..."
        lines.append(f'  {nid}["{label}"]\n')

    # Edges: dependencies
    for tid, t in task_items:
        to_id = id_map.get(str(tid))
        for dep in getattr(t, "dependency_task_ids", []) or []:
            from_id = id_map.get(str(dep))
            if from_id and to_id:
                lines.append(f"  {from_id} --> {to_id}\n")

        # Parent -> subtask edges (non-directional structure)
        for st in getattr(t, "subtasks", []) or []:
            child_id = id_map.get(str(getattr(st, "id", "")))
            if child_id and to_id:
                lines.append(f"  {to_id} --- {child_id}\n")

    lines.append("```\n\n")
    return lines


def write_graphviz_svg(
    wf: Any, scenario: str, out_dir: Path, use_gen: bool
) -> str | None:
    """Render a Graphviz DOT diagram of the workflow to SVG and return relative path.

    When running under mkdocs-gen-files, write into docs/benchmark/assets; else to disk.
    """
    try:
        from graphviz import Digraph  # type: ignore
    except Exception as e:
        print(f"[bench] graphviz import failed for {scenario}: {e}")
        return None

    tasks: dict = getattr(wf, "tasks", {}) or {}
    if not tasks:
        print(f"[bench] no tasks found for {scenario}; skipping graphviz")
        return None

    dot = Digraph(
        comment=f"Workflow {scenario}",
        graph_attr={"rankdir": "LR", "splines": "spline"},
    )
    dot.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fillcolor="#E8F1FC",
        color="#5B8DEF",
    )
    dot.attr("edge", color="#8FAADC", penwidth="1.5")

    id_map: dict[str, str] = {}
    for tid, t in tasks.items():
        node_id = str(tid)
        id_map[str(tid)] = node_id
        label = shorten(str(getattr(t, "name", tid)), width=42, placeholder="…")
        dot.node(node_id, label)

    for tid, t in tasks.items():
        to_id = id_map.get(str(tid))
        for dep in getattr(t, "dependency_task_ids", []) or []:
            from_id = id_map.get(str(dep))
            if from_id and to_id:
                dot.edge(from_id, to_id)

    assets_rel = Path("benchmark/assets")
    assets_dir = out_dir / assets_rel
    # Always ensure disk path exists; we'll write to disk and embed relative path
    assets_dir.mkdir(parents=True, exist_ok=True)

    svg_filename = f"{scenario}.svg"
    # Path where the Markdown page (benchmark/<scenario>.md) should reference the SVG
    md_rel_path = f"assets/{svg_filename}"

    try:
        # Render to bytes and write exact filename to avoid extensionless artifacts
        svg_bytes = dot.pipe(format="svg")
        out_file = assets_dir / svg_filename
        with open(out_file, "wb") as f:
            f.write(svg_bytes)
        print(f"[bench] wrote SVG: {out_file}")
    except Exception as e:
        print(f"[bench] graphviz pipe failed for {scenario}: {e}")
        return None

    return md_rel_path


def extract_team_schedule(
    module: Any,
) -> tuple[list[dict[str, Any]], dict[int, list[tuple[str, str]]]]:
    """Return (team_details, schedule) where
    - team_details: list of {id,type,description,capabilities}
    - schedule: {timestep: [(agent_id, note), ...]}
    """
    team_details: list[dict[str, Any]] = []
    schedule: dict[int, list[tuple[str, str]]] = {}
    create_cfg = get_callable(module, "create_team_configs")
    create_tl = get_callable(module, "create_team_timeline")
    try:
        cfg = create_cfg() if create_cfg else {}
        if isinstance(cfg, dict):
            for key, obj in cfg.items():
                agent_id = getattr(obj, "agent_id", key)
                agent_type = getattr(obj, "agent_type", "")
                description = getattr(
                    obj, "agent_description", getattr(obj, "description", "")
                )
                capabilities = getattr(obj, "agent_capabilities", [])
                # Human agents sometimes have name/role fields
                name = getattr(obj, "name", "")
                role = getattr(obj, "role", "")
                if isinstance(capabilities, list):
                    caps = [str(c) for c in capabilities]
                else:
                    caps = []
                team_details.append(
                    {
                        "id": str(agent_id),
                        "type": str(agent_type),
                        "name": str(name),
                        "role": str(role),
                        "description": str(description),
                        "capabilities": caps,
                    }
                )
    except Exception:
        team_details = []
    # Fallback: scan for any function returning an agent config dict
    if not team_details and module is not None:
        for name, fn in inspect.getmembers(module, inspect.isfunction):
            if "team" in name and ("config" in name or "agent" in name):
                out = _try_call_zero_arg(fn)
                if isinstance(out, dict) and out:
                    for key, obj in out.items():
                        agent_id = getattr(obj, "agent_id", key)
                        agent_type = getattr(obj, "agent_type", "")
                        description = getattr(
                            obj, "agent_description", getattr(obj, "description", "")
                        )
                        capabilities = getattr(obj, "agent_capabilities", [])
                        name_v = getattr(obj, "name", "")
                        role = getattr(obj, "role", "")
                        caps = (
                            [str(c) for c in capabilities]
                            if isinstance(capabilities, list)
                            else []
                        )
                        team_details.append(
                            {
                                "id": str(agent_id),
                                "type": str(agent_type),
                                "name": str(name_v),
                                "role": str(role),
                                "description": str(description),
                                "capabilities": caps,
                            }
                        )
                    break
    try:
        tl = create_tl() if create_tl else {}
        if isinstance(tl, dict):
            for ts, ops in tl.items():
                labels: list[tuple[str, str]] = []
                for op in ops:
                    try:
                        # op like ("add", AIAgentConfig(...), "desc")
                        agent_id = getattr(op[1], "agent_id", None) or str(op[1])
                        note = op[2] if len(op) > 2 else ""
                        labels.append((str(agent_id), str(note)))
                    except Exception:
                        continue
                schedule[int(ts)] = labels
    except Exception:
        schedule = {}
    # Fallback: any function with 'timeline' in name
    if not schedule and module is not None:
        for name, fn in inspect.getmembers(module, inspect.isfunction):
            if "timeline" in name:
                tl = _try_call_zero_arg(fn)
                if isinstance(tl, dict):
                    tmp: dict[int, list[tuple[str, str]]] = {}
                    for ts, ops in tl.items():
                        row: list[tuple[str, str]] = []
                        try:
                            for op in ops:
                                agent_id = getattr(op[1], "agent_id", None) or str(
                                    op[1]
                                )
                                note = op[2] if len(op) > 2 else ""
                                row.append((str(agent_id), str(note)))
                        except Exception:
                            pass
                        if row:
                            tmp[int(ts)] = row
                    if tmp:
                        schedule = tmp
                        break
    return team_details, schedule


def has_preferences(module: Any) -> bool:
    # Heuristic: presence of evaluator/rubric constructors
    text = inspect.getsource(module) if module else ""
    return any(k in text for k in ["WorkflowRubric", "Evaluator", "PreferenceWeights"])


def main() -> None:
    # Use mkdocs-gen-files virtual FS when running under mkdocs; fall back to disk writes.
    try:
        import mkdocs_gen_files  # type: ignore

        use_gen = True
    except Exception:
        mkdocs_gen_files = None  # type: ignore
        use_gen = False
    # Default to disk writes when running as a standalone script unless explicitly enabled
    if os.environ.get("GEN_BENCHMARKS_USE_GEN") != "1":
        use_gen = False

    bench_rel = "benchmark"
    bench_dir = DOCS_DIR / bench_rel
    if not use_gen:
        bench_dir.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "## Benchmarks\n",
        "\n",
        "The following scenario pages are generated from the example code at build time.\n",
        "\n",
    ]

    scenarios = discover_scenarios()
    print(f"[bench] discovered {len(scenarios)} scenarios under {EXAMPLES_PKG}")
    for pkg_name, dir_path in sorted(scenarios):
        print(f"[bench] building {pkg_name}")
        wf_mod = import_module_from_path(
            dir_path / "workflow.py", f"bench.{pkg_name}.workflow"
        )
        team_mod = import_module_from_path(
            dir_path / "team.py", f"bench.{pkg_name}.team"
        )
        pref_mod = import_module_from_path(
            dir_path / "preferences.py", f"bench.{pkg_name}.preferences"
        )

        workflow_goal = ""
        wf_obj = find_workflow_factory(wf_mod)
        if wf_obj is not None:
            workflow_goal = extract_goal_text(wf_obj)

        team_details, schedule = (
            extract_team_schedule(team_mod) if team_mod else ([], {})
        )
        pref_note = "Yes" if (pref_mod and has_preferences(pref_mod)) else "Unknown"

        # Write scenario page
        lines: list[str] = []
        title = pkg_name.replace("_", " ").title()
        lines.append(f"## {title}\n\n")

        # Stats badges
        if wf_obj is not None:
            stats = summarize_workflow_stats(wf_obj, team_details, schedule)
            # Render simple badge-like chips using inline code blocks
            lines.append(
                f"`tasks: {stats['tasks']}` `constraints: {stats['constraints']}` `team: {stats['team']}` `timesteps: {stats['timesteps']}`\n\n"
            )

        # Workflow goal as an admonition for readability
        lines.append("### Workflow Goal\n\n")
        if workflow_goal:
            lines.extend(format_goal(workflow_goal))
        else:
            lines.append("(No goal text found)\n\n")

        # Team structure as a table
        lines.append("### Team Structure\n\n")
        if team_details:

            def _fmt(val: str) -> str:
                return str(val).replace("|", "\\|")

            lines.append("| Agent ID | Type | Name / Role | Capabilities |\n")
            lines.append("|---|---|---|---|\n")
            for info in team_details:
                name_role = " ".join(
                    [
                        x
                        for x in [
                            info.get("name") or "",
                            f"({info.get('role')})" if info.get("role") else "",
                        ]
                        if x
                    ]
                ).strip()
                caps = info.get("capabilities") or []
                caps_str = "<br>".join(_fmt(c) for c in caps) if caps else ""
                lines.append(
                    f"| {_fmt(info['id'])} | {_fmt(info['type'])} | {_fmt(name_role)} | {caps_str} |\n"
                )
            lines.append("\n")
        else:
            lines.append("(No team config found)\n\n")

        # Schedule as a table
        lines.append("### Join/Leave Schedule\n\n")
        if schedule:
            lines.append("| Timestep | Agents / Notes |\n")
            lines.append("|---:|---|\n")
            for ts in sorted(schedule.keys()):
                entries = schedule[ts]
                if entries:
                    items = []
                    for agent_id, note in entries:
                        if note:
                            items.append(f"**{agent_id}** — {note}")
                        else:
                            items.append(f"**{agent_id}**")
                    lines.append(
                        f"| {ts} | " + "<br>".join(items).replace("|", "\\|") + " |\n"
                    )
            lines.append("\n")
        else:
            lines.append("(No timeline found)\n\n")

        # Workflow diagram via Graphviz (SVG) with Mermaid fallback
        if wf_obj is not None:
            lines.append("### Workflow Diagram\n\n")
            svg_rel = write_graphviz_svg(wf_obj, pkg_name, DOCS_DIR, use_gen)
            if svg_rel is None:
                # Explicitly note when graphviz generation failed
                lines.append(
                    "> Diagram generation failed; falling back to Mermaid.\n\n"
                )
                print(f"[bench] diagram failed for {pkg_name}; using Mermaid fallback")
            if svg_rel:
                # Add size attributes and wrap in a self-link to open full-size in a new tab
                lines.append(
                    f"[![Workflow DAG]({svg_rel}){{ width=1200 }}]({svg_rel}){{ target=_blank }}\n\n"
                )
            else:
                lines.extend(build_mermaid_workflow(wf_obj))

        # Preferences note + source links
        lines.append("### Preferences & Rubrics\n\n")
        lines.append(f"Defined: {pref_note}.\n\n")
        lines.append("#### Sources\n\n")
        lines.append(f"- Workflow: `{dir_path / 'workflow.py'}`\n")
        lines.append(f"- Team: `{dir_path / 'team.py'}`\n")
        lines.append(f"- Preferences: `{dir_path / 'preferences.py'}`\n\n")

        if use_gen and mkdocs_gen_files is not None:
            with mkdocs_gen_files.open(f"{bench_rel}/{pkg_name}.md", "w") as f:
                f.write("".join(lines))
        else:
            out = bench_dir / f"{pkg_name}.md"
            out.write_text("".join(lines))

        index_lines.append(f"- [{title}](./{pkg_name}.md)\n")

    # Ensure index includes a note when no scenarios were found (debugging aid)
    if len(scenarios) == 0:
        index_lines.append(
            "(No scenarios discovered. Check import paths and packaging.)\n"
        )

    # Write index
    if use_gen and mkdocs_gen_files is not None:
        with mkdocs_gen_files.open(f"{bench_rel}/index.md", "w") as f:
            f.write("".join(index_lines))
    else:
        (bench_dir / "index.md").write_text("".join(index_lines))

    # Repair any extensionless SVG files from earlier runs (best-effort)
    assets_dir = DOCS_DIR / bench_rel / "assets"
    try:
        assets_dir.mkdir(parents=True, exist_ok=True)
        for child in assets_dir.iterdir():
            if child.is_file() and child.suffix == "":
                with open(child, "rb") as f:
                    head = f.read(200)
                if b"<svg" in head[:200].lower():
                    target = child.with_suffix(".svg")
                    # Avoid overwriting if already exists
                    if not target.exists():
                        child.rename(target)
    except Exception:
        pass


if __name__ == "__main__":
    main()
