"""
Example: Multimodal Evaluation with File-Based Resources

Demonstrates the new file-based resource system with:
1. Resources as files (Excel, PDF, markdown)
2. Clean ValidationContext API
3. Multimodal LLM evaluation with GPT-4 Vision
4. Code rules with direct file access
"""

import asyncio
import tempfile
from pathlib import Path
from uuid import uuid4

from manager_agent_gym.schemas.domain.resource import Resource
from manager_agent_gym.schemas.domain.workflow import Workflow, Task
from manager_agent_gym.core.evaluation.schemas.success_criteria import (
    ValidationContext,
)
from manager_agent_gym.core.evaluation.engine.code_rule_executor import CodeRuleExecutor
from manager_agent_gym.core.evaluation.engine.multimodal_llm import MultimodalEvaluator


async def example_excel_code_rule():
    """Example: Code rule evaluating an Excel file."""

    # Create a temporary Excel file
    import pandas as pd  # type: ignore

    temp_dir = Path(tempfile.mkdtemp(prefix="eval_example_"))
    excel_path = temp_dir / "analysis.xlsx"

    # Create sample Excel data
    df = pd.DataFrame(
        {
            "Year": [0, 1, 2, 3],
            "Revenue": [0, 500000, 750000, 1000000],
            "Costs": [1000000, 200000, 300000, 400000],
            "Net Cash Flow": [-1000000, 300000, 450000, 600000],
        }
    )
    df.to_excel(excel_path, sheet_name="NPV Analysis", index=False)

    # Create Resource
    resource = Resource(
        name="NPV Analysis",
        description="Financial analysis spreadsheet",
        file_path=str(excel_path),
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        size_bytes=excel_path.stat().st_size,
        file_format_metadata={"sheet_names": ["NPV Analysis"]},
    )

    # Create Workflow with Task
    task_id = uuid4()
    task = Task(
        id=task_id,
        name="Financial Analysis",
        description="Create NPV analysis",
        output_resource_ids=[resource.id],
    )

    workflow = Workflow(
        id=uuid4(),
        name="Test Workflow",
        workflow_goal="Analyze investment opportunity",
        owner_id=uuid4(),
        tasks={task_id: task},
        resources={resource.id: resource},
    )

    # Create ValidationContext
    context = ValidationContext(workflow=workflow, timestep=0)

    # Define code rule using new API
    code_rule = """
def evaluate(workflow, context):
    \"\"\"Check if Excel has required columns using context helpers.\"\"\"
    import pandas as pd
    
    try:
        # Use context helper to get primary output
        output = context.get_primary_output()
        if not output:
            return 0.0, "No output resources found"
        
        if not output.is_spreadsheet:
            return 0.0, "Primary output is not a spreadsheet"
        
        # Use context.files helper to read Excel
        df = context.files.read_excel(output.id, sheet_name='NPV Analysis')
        
        # Check for required columns (flexible matching)
        required = ['year', 'revenue', 'costs', 'net cash flow']
        columns_lower = [col.lower() for col in df.columns]
        
        found = sum(1 for req in required if any(req in col for col in columns_lower))
        score = found / len(required)
        
        return score, f"Found {found}/{len(required)} required columns"
        
    except Exception as e:
        return 0.0, f"Error: {str(e)}"
"""

    # Execute code rule
    executor = CodeRuleExecutor()
    score, feedback = await executor.execute(code_rule, workflow, context)

    print("=" * 80)
    print("CODE RULE EVALUATION EXAMPLE")
    print("=" * 80)
    print(f"Resource: {resource.name}")
    print(f"File: {resource.file_path}")
    print(f"Score: {score:.2f}")
    print(f"Feedback: {feedback}")
    print()

    return score, feedback


async def example_multimodal_llm_evaluation():
    """Example: LLM evaluation with GPT-4 Vision (multimodal)."""

    # Create a temporary markdown file
    temp_dir = Path(tempfile.mkdtemp(prefix="eval_example_"))
    md_path = temp_dir / "report.md"

    md_content = """# Quarterly Business Review

## Executive Summary

Our Q4 results exceeded expectations with 25% revenue growth YoY.

## Key Metrics

| Metric | Q3 | Q4 | Change |
|--------|----|----|--------|
| Revenue | $2.5M | $3.1M | +24% |
| Customers | 450 | 580 | +29% |
| CSAT | 4.2 | 4.5 | +7% |

## Recommendations

1. Expand sales team by 3 FTEs
2. Invest in customer success platform
3. Launch enterprise tier in Q1

---
*Prepared by: Finance Team*
*Date: January 15, 2025*
"""

    md_path.write_text(md_content)

    # Create Resource
    resource = Resource(
        name="Q4 Business Review",
        description="Quarterly business review document",
        file_path=str(md_path),
        mime_type="text/markdown",
        size_bytes=md_path.stat().st_size,
    )

    # Create Workflow
    task_id = uuid4()
    task = Task(
        id=task_id,
        name="Create Business Review",
        description="Write quarterly review",
        output_resource_ids=[resource.id],
    )

    workflow = Workflow(
        id=uuid4(),
        name="Test Workflow",
        workflow_goal="Document Q4 performance",
        owner_id=uuid4(),
        tasks={task_id: task},
        resources={resource.id: resource},
    )

    # Create ValidationContext
    context = ValidationContext(workflow=workflow, timestep=0)

    # Multimodal LLM evaluation
    evaluator = MultimodalEvaluator()

    evaluation_prompt = """
Evaluate this quarterly business review document:

**Criteria**:
1. **Structure** (0.4 points): Clear sections, executive summary, recommendations
2. **Data Quality** (0.3 points): Includes metrics with comparison data
3. **Professionalism** (0.3 points): Proper formatting, attribution, date

Return a score from 0.0 to 1.0 based on overall quality.
"""

    outputs = context.get_all_outputs()
    score, reasoning = await evaluator.evaluate_with_vision(
        prompt=evaluation_prompt, resources=outputs, max_score=1.0
    )

    print("=" * 80)
    print("MULTIMODAL LLM EVALUATION EXAMPLE")
    print("=" * 80)
    print(f"Resource: {resource.name}")
    print(f"File: {resource.file_path}")
    print(f"Score: {score:.2f}/1.0")
    print(f"Reasoning: {reasoning}")
    print()

    return score, reasoning


async def example_resource_type_checking():
    """Example: Resource type checking and file access."""

    temp_dir = Path(tempfile.mkdtemp(prefix="eval_example_"))

    # Create different resource types
    resources_to_create = [
        ("report.md", "text/markdown", "# Report\n\nThis is a report."),
        ("data.csv", "text/csv", "name,value\nitem1,100\nitem2,200"),
    ]

    resources = []

    for filename, mime_type, content in resources_to_create:
        file_path = temp_dir / filename
        file_path.write_text(content)

        resource = Resource(
            name=filename,
            description=f"Example {mime_type} file",
            file_path=str(file_path),
            mime_type=mime_type,
            size_bytes=file_path.stat().st_size,
        )
        resources.append(resource)

    print("=" * 80)
    print("RESOURCE TYPE CHECKING EXAMPLE")
    print("=" * 80)

    for resource in resources:
        print(f"\nResource: {resource.name}")
        print(f"  MIME type: {resource.mime_type}")
        print(f"  Extension: {resource.file_extension}")
        print(f"  Is text format: {resource.is_text_format}")
        print(f"  Is document: {resource.is_document}")
        print(f"  Is spreadsheet: {resource.is_spreadsheet}")
        print(f"  Is image: {resource.is_image}")

        if resource.is_text_format:
            content = resource.load_text()
            print(f"  Content preview: {content[:50]}...")

    print()


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("MULTIMODAL EVALUATION SYSTEM EXAMPLES")
    print("=" * 80 + "\n")

    # Example 1: Code rule with Excel
    await example_excel_code_rule()

    # Example 2: LLM evaluation with markdown
    await example_multimodal_llm_evaluation()

    # Example 3: Resource type checking
    await example_resource_type_checking()

    print("=" * 80)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
