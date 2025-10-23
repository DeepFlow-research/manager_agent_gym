"""Script to help review generated rubrics.

Randomly samples N tasks and displays their rubrics in detail for manual review.
"""

import json
import random
from pathlib import Path
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def display_rubric(rubric_data: dict, task_number: int):
    """Display a single rubric in rich format."""
    task_id = rubric_data["task_id"]
    rubric = rubric_data["rubric"]

    # Header
    console.print(f"\n{'=' * 100}", style="bold blue")
    console.print(f"TASK {task_number}: {rubric['category_name']}", style="bold cyan")
    console.print(f"Task ID: {task_id}", style="dim")
    console.print(f"Max Score: {rubric['max_total_score']} points", style="bold yellow")
    console.print(f"{'=' * 100}", style="bold blue")

    # Rationale
    console.print("\n[bold]Rationale:[/bold]")
    console.print(Panel(rubric["rationale"], border_style="green"))

    # Stages
    for stage_idx, stage in enumerate(rubric["stages"], 1):
        console.print(
            f"\n[bold magenta]━━━ STAGE {stage_idx}: {stage['name']} ({stage['max_points']} pts) ━━━[/bold magenta]"
        )
        console.print(f"[yellow]Required:[/yellow] {stage['is_required']}")
        console.print(
            f"[yellow]Min Score to Pass:[/yellow] {stage['min_score_to_pass']}"
        )
        console.print(f"[yellow]On Failure:[/yellow] {stage['on_failure_action']}\n")

        # Rules
        for rule_idx, rule in enumerate(stage["rules"], 1):
            rule_type_color = "cyan" if rule["type"] == "llm_judge" else "green"
            console.print(
                f"  [bold {rule_type_color}]Rule {rule_idx}: [{rule['type'].upper()}] {rule['name']}[/bold {rule_type_color}]"
            )
            console.print(f"  Weight: {rule['weight']}")
            console.print(f"  Description: {rule['description']}\n")

            if rule["type"] == "llm_judge":
                console.print("  [italic]LLM Judge Prompt:[/italic]")
                # Truncate long prompts
                prompt = rule.get("judge_prompt", "N/A")
                if len(prompt) > 500:
                    prompt = prompt[:500] + "\n  ... (truncated)"
                console.print(Panel(prompt, border_style="blue", padding=(0, 1)))

            elif rule["type"] == "code":
                console.print("  [italic]Code Rule:[/italic]")
                code = rule.get("code", "N/A")
                # Truncate long code
                if len(code) > 600:
                    code = code[:600] + "\n  # ... (truncated)"

                # Check for quality indicators
                indicators = []
                if "try:" in code and "except" in code:
                    indicators.append("✓ Error handling")
                if (
                    "pd.read_excel(candidate_output" in code
                    or "open(candidate_output" in code
                ):
                    indicators.append("✓ Opens file correctly")
                if ".str.contains" in code or ".lower()" in code:
                    indicators.append("✓ Flexible matching")
                if "required_columns = [" in code and ("'" in code or '"' in code):
                    indicators.append("⚠️  Possible exact matching")

                if indicators:
                    console.print(f"  Quality: {', '.join(indicators)}", style="dim")

                syntax = Syntax(code, "python", theme="monokai", line_numbers=False)
                console.print(Panel(syntax, border_style="green", padding=(0, 1)))

            console.print()  # Blank line between rules


def main():
    parser = argparse.ArgumentParser(description="Review generated rubrics")
    parser.add_argument(
        "--version", default="staged_v4", help="Rubric version to review"
    )
    parser.add_argument(
        "--sample", type=int, default=10, help="Number of rubrics to sample"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    parser.add_argument(
        "--indices", type=str, help="Comma-separated indices to review (e.g., '0,5,10')"
    )
    args = parser.parse_args()

    # Load rubrics
    rubrics_file = (
        Path(__file__).parent.parent
        / "data"
        / "generated"
        / args.version
        / "staged_rubrics.jsonl"
    )

    if not rubrics_file.exists():
        console.print(f"[red]Error: Rubrics file not found at {rubrics_file}[/red]")
        return

    with open(rubrics_file, "r") as f:
        all_rubrics = [json.loads(line) for line in f]

    console.print(
        f"\n[bold green]Loaded {len(all_rubrics)} rubrics from {rubrics_file.name}[/bold green]\n"
    )

    # Sample rubrics
    if args.indices:
        indices = [int(i.strip()) for i in args.indices.split(",")]
        sampled_rubrics = [
            (i, all_rubrics[i]) for i in indices if 0 <= i < len(all_rubrics)
        ]
    else:
        random.seed(args.seed)
        sample_size = min(args.sample, len(all_rubrics))
        sampled_indices = random.sample(range(len(all_rubrics)), sample_size)
        sampled_rubrics = [(i, all_rubrics[i]) for i in sorted(sampled_indices)]

    console.print(f"[bold cyan]Reviewing {len(sampled_rubrics)} rubrics:[/bold cyan]")
    console.print(f"Indices: {[i for i, _ in sampled_rubrics]}\n")

    # Display each rubric
    for task_number, (original_idx, rubric_data) in enumerate(sampled_rubrics, 1):
        console.print(f"\n[dim]Original index: {original_idx}[/dim]")
        display_rubric(rubric_data, task_number)

        # Pause between rubrics (except last)
        if task_number < len(sampled_rubrics):
            console.print("\n" * 2)
            try:
                input("[dim]Press Enter to continue to next rubric...[/dim]")
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Review interrupted.[/yellow]")
                break

    console.print("\n\n[bold green]✓ Review complete![/bold green]")
    console.print("\nTo review different tasks, use: [cyan]--indices 0,5,10,15[/cyan]")
    console.print("Or re-sample with different seed: [cyan]--seed 123[/cyan]\n")


if __name__ == "__main__":
    main()
