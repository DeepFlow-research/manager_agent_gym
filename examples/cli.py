from __future__ import annotations

import os
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

import typer
import questionary


app = typer.Typer(
    help=(
        "Interactive CLI to run Manager Agent Gym examples in batch.\n\n"
        "Examples:\n"
        "  python -m examples.cli --non-interactive\n"
        "  python -m examples.cli --scenarios icaap --max-timesteps 5 --manager-mode cot --model-name o3\n"
        "  python -m examples.cli --scenarios data_science_analytics --scenarios brand_crisis_management --parallel-jobs 2\n"
    )
)


DEFAULT_SCENARIOS: list[str] = [
    "banking_license_application",
    "brand_crisis_management",
    "data_science_analytics",
    "global_product_recall",
    "icaap",  # note: scenario key is 'icaap'
    "legal_contract_negotiation",
    "legal_litigation_ediscovery",
    "legal_contract_negotiation",
    "legal_global_data_breach",
    "enterprise_saas_negotiation_pipeline",
    "mnc_workforce_restructuring",
    "legal_m_and_a",
    "marketing_campaign",
    "orsa",
    "supply_chain_planning",
    "tech_company_acquisition",
    "genai_feature_launch",
    "ipo_readiness_program",
    "pharmaceutical_product_launch",
    "uk_university_accreditation",
    "airline_launch_program",
]

MANAGER_MODE_CHOICES: list[str] = ["cot", "random", "assign_all"]
MODEL_NAME_SUGGESTIONS: list[str] = [
    "gpt-5",
    "gpt-5-mini",
    "o3",
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-7-sonnet",
    "gemini-2.0-flash",
    "gpt-4.1-mini",
]


def _project_root() -> Path:
    this_file = Path(__file__).resolve()
    # manager_agent_gym/cli.py → project root is parent of package dir
    return this_file.parent.parent


def _default_output_dir(manager_mode: str) -> Path:
    label = manager_mode.lower()
    return _project_root() / f"simulation_outputs_{label}_rerun"


def _sanitize_for_path(value: str) -> str:
    """Make a safe directory name from the given value.

    Keeps alphanumerics, dash, underscore, and dot; replaces others with underscore.
    Lowercases and trims leading/trailing underscores for cleanliness.
    """
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    sanitized = "".join((ch if ch in allowed else "_") for ch in value)
    return sanitized.strip("_").lower() or "model"


def _run_one(
    workflow_name: str,
    max_timesteps: int,
    manager_mode: str,
    model_name: str,
    output_dir: Path,
    seed: int,
    run_suffix: str | None,
) -> int:
    env = os.environ.copy()
    env.setdefault("MAG_MAX_TIMESTEPS", str(max_timesteps))
    env.setdefault("MAG_MANAGER_MODE", manager_mode)
    env.setdefault("MAG_MODEL_NAME", model_name)
    env.setdefault("MAG_OUTPUT_DIR", str(output_dir))
    if run_suffix:
        env["MAG_RUN_SUFFIX"] = run_suffix

    # Per-seed subdir now encoded via MAG_RUN_SUFFIX and label subdir; keep base output_dir constant
    cmd = [
        sys.executable,
        "-m",
        "examples.run_examples",
        "--workflow_name",
        workflow_name,
        "--max-timesteps",
        str(max_timesteps),
        "--model-name",
        model_name,
        "--output-dir",
        str(output_dir),
        "--manager-agent-mode",
        manager_mode,
        "--seed",
        str(seed),
    ]

    proc = subprocess.Popen(
        cmd,
        cwd=str(_project_root()),
        env=env,
    )
    return proc.wait()


def _select_scenarios_interactively(
    all_keys: list[str], defaults: list[str]
) -> list[str]:
    if questionary is None:
        # Fallback: no interactive dependency installed
        return defaults

    choices = [
        questionary.Choice(title=key, value=key, checked=(key in defaults))  # debug
        for key in all_keys
    ]

    result: list[str] = (
        questionary.checkbox(
            "Select end-to-end examples to run",
            choices=choices,
        ).ask()
        or []
    )

    # Ensure at least defaults if user submits empty
    return result or defaults


def _prompt_if_missing(
    *,
    scenarios: list[str] | None,
    max_timesteps: int,
    manager_mode: list[str] | None,
    model_name: list[str] | None,
    seed: int,
    num_seeds: int,
) -> tuple[list[str], int, list[str], list[str], int, int]:
    """Prompt interactively (checkboxes/selects) for any missing values, including seeds."""
    if questionary is None:
        # No interactive prompts available
        return (
            scenarios or DEFAULT_SCENARIOS,
            max_timesteps,
            list(manager_mode or [MANAGER_MODE_CHOICES[0]]),
            list(model_name or [MODEL_NAME_SUGGESTIONS[0]]),
            seed,
            num_seeds,
        )

    # Scenarios checkbox
    from examples.scenarios import SCENARIOS as _SC  # type: ignore

    all_keys = sorted(list(_SC.keys()))
    chosen_scenarios = scenarios or _select_scenarios_interactively(
        all_keys, DEFAULT_SCENARIOS
    )

    # Manager mode multi-select
    chosen_manager_modes: list[str] = manager_mode or (
        questionary.checkbox(
            "Select manager agent modes (space to toggle)",
            choices=[
                questionary.Choice(
                    title=m, value=m, checked=(m == MANAGER_MODE_CHOICES[0])
                )
                for m in MANAGER_MODE_CHOICES
            ],
        ).ask()
        or [MANAGER_MODE_CHOICES[0]]
    )

    # Model names multi-select (allow custom entries when "Other" chosen)
    chosen_model_names: list[str] = model_name or (
        questionary.checkbox(
            "Select LLM models (space to toggle)",
            choices=[*MODEL_NAME_SUGGESTIONS, "Other (enter manually)"],
        ).ask()
        or [MODEL_NAME_SUGGESTIONS[0]]
    )
    if any(m.startswith("Other") for m in chosen_model_names):
        extra = (
            questionary.text(
                "Enter additional model names (comma-separated)", default=""
            ).ask()
            or ""
        )
        extra_models = [s.strip() for s in extra.split(",") if s.strip()]
        chosen_model_names = [
            m for m in chosen_model_names if not m.startswith("Other")
        ] + extra_models

    # Max timesteps numeric prompt
    max_ts_str = questionary.text(
        "Max timesteps", default=str(max_timesteps)
    ).ask() or str(max_timesteps)
    try:
        resolved_max_ts = int(max_ts_str)
    except ValueError:
        resolved_max_ts = max_timesteps

    # Seed prompts
    seed_str = questionary.text("Base seed", default=str(seed)).ask() or str(seed)
    try:
        resolved_seed = int(seed_str)
    except ValueError:
        resolved_seed = seed

    num_seeds_str = questionary.text(
        "Number of seeds", default=str(num_seeds)
    ).ask() or str(num_seeds)
    try:
        resolved_num_seeds = int(num_seeds_str)
    except ValueError:
        resolved_num_seeds = num_seeds

    return (
        chosen_scenarios,
        resolved_max_ts,
        chosen_manager_modes,
        chosen_model_names,
        resolved_seed,
        resolved_num_seeds,
    )


@app.command()
def main(
    scenarios: Optional[List[str]] = typer.Option(
        None,
        help=(
            "Scenario keys to run (e.g., icaap, data_science_analytics). "
            "If omitted, will prompt with checkboxes."
        ),
    ),
    max_timesteps: int = typer.Option(50, help="Max timesteps to run each example"),
    manager_mode: Optional[List[str]] = typer.Option(
        None,
        help=(
            "Manager agent mode(s). Repeat to run multiple baselines. "
            f"Choices: {', '.join(MANAGER_MODE_CHOICES)}"
        ),
    ),
    model_name: Optional[List[str]] = typer.Option(
        None,
        help=(
            "LLM model name(s). Repeat to run multiple models (e.g., --model-name o3 --model-name gpt-4.1)"
        ),
    ),
    output_dir: Optional[Path] = typer.Option(
        None, help="Base output directory for simulation outputs"
    ),
    parallel_jobs: int = typer.Option(16, help="Number of parallel runs"),
    seed: int = typer.Option(42, help="Base random seed"),
    num_seeds: int = typer.Option(
        1, help="Number of seeds to run per scenario (seeds are seed, seed+1, ...)"
    ),
    non_interactive: bool = typer.Option(
        False, help="Run without interactive prompts (use options/defaults)"
    ),
    offline_run_dir: Optional[Path] = typer.Option(
        None, help="Offline run directory for evaluation-only mode"
    ),
) -> None:
    """Run selected end-to-end examples in parallel."""
    # Load available scenario keys from examples.scenarios
    try:
        from examples.scenarios import SCENARIOS  # type: ignore
    except Exception as exc:  # pragma: no cover
        typer.echo(f"Failed to import scenarios: {exc}")
        raise typer.Exit(code=1)

    # Available keys kept for potential validation in future; interactive prompt pulls directly
    _ = sorted(list(SCENARIOS.keys()))

    # Resolve interactive vs non-interactive values
    if non_interactive:
        selected = scenarios or DEFAULT_SCENARIOS
        resolved_manager_modes = list(manager_mode or [MANAGER_MODE_CHOICES[0]])
        resolved_model_names = list(model_name or [MODEL_NAME_SUGGESTIONS[0]])
        resolved_max_ts = max_timesteps
        resolved_seed = seed
        resolved_num_seeds = num_seeds
    else:
        (
            selected,
            resolved_max_ts,
            resolved_manager_modes,
            resolved_model_names,
            resolved_seed,
            resolved_num_seeds,
        ) = _prompt_if_missing(
            scenarios=scenarios,
            max_timesteps=max_timesteps,
            manager_mode=manager_mode,
            model_name=model_name,
            seed=seed,
            num_seeds=num_seeds,
        )

    if not selected:
        typer.echo("No scenarios selected; exiting.")
        raise typer.Exit(code=0)

    # Ensure base output dir exists if provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(
        f"Running {len(selected)} scenarios | max_timesteps={resolved_max_ts} "
        f"manager_modes={resolved_manager_modes} models={resolved_model_names} "
        f"base_output_dir={str(output_dir) if output_dir else '<per-mode default>'} "
        f"parallel_jobs={parallel_jobs} seed={resolved_seed} num_seeds={resolved_num_seeds}"
    )

    # Submit in a thread pool; each job is a separate Python process
    with ThreadPoolExecutor(max_workers=max(1, parallel_jobs)) as executor:
        futures = {}
        for name in selected:
            for mm in resolved_manager_modes:
                for model in resolved_model_names:
                    model_dirname = _sanitize_for_path(model)
                    base_dir = output_dir or _default_output_dir(mm)
                    for i in range(max(1, resolved_num_seeds)):
                        current_seed = resolved_seed + i
                        per_run_output_dir = base_dir / model_dirname
                        per_run_output_dir.mkdir(parents=True, exist_ok=True)

                        run_suffix = f"seed_{current_seed}"
                        futures[
                            executor.submit(
                                _run_one,
                                name,
                                resolved_max_ts,
                                mm,
                                model,
                                per_run_output_dir,
                                current_seed,
                                run_suffix,
                            )
                        ] = f"{name} [{mm}/{model}] (seed {current_seed})"

        any_failed = False
        for future in as_completed(futures):
            name = futures[future]
            try:
                code = future.result()
                if code == 0:
                    typer.echo(f"✅ {name} completed successfully")
                else:
                    any_failed = True
                    typer.echo(f"❌ {name} failed with exit code {code}")
            except Exception as exc:  # pragma: no cover
                any_failed = True
                typer.echo(f"💥 {name} raised exception: {exc}")

    if any_failed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
