"""
Example script demonstrating how to run a GDPEval task with ma-gym tools.

This example shows:
1. Loading a task from the GDPEval dataset
2. Creating an AI agent with the full GDPEval toolkit
3. Executing the task with reference documents
4. Validating deliverable outputs

Usage:
    python -m examples.gdpeval.run_gdpeval_task
"""

import asyncio

from manager_agent_gym.core.agents.workflow_agents.tools.tool_factory import ToolFactory
from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager
from manager_agent_gym.schemas.agents import AIAgentConfig
from manager_agent_gym.schemas.domain import Task, Resource
from manager_agent_gym.config import get_settings
from manager_agent_gym.core.common.logging import logger


async def main():
    """Main example function."""

    logger.info("=== GDPEval Task Execution Example ===\n")

    # 1. Setup resource file manager
    logger.info("Setting up resource file manager...")
    resource_manager = ResourceFileManager(base_dir="./gdpeval_workspace")

    # 2. Create GDPEval tools
    logger.info("Creating GDPEval toolkit...")
    settings = get_settings()
    gdpeval_tools = ToolFactory.create_gdpeval_tools(
        resource_manager=resource_manager,
        e2b_api_key=settings.E2B_API_KEY if settings.E2B_API_KEY != "na" else None,
    )

    logger.info(f"Created {len(gdpeval_tools)} GDPEval tools:")
    for tool in gdpeval_tools[:5]:  # Show first 5
        logger.info(f"  - {tool.name}")
    if len(gdpeval_tools) > 5:
        logger.info(f"  ... and {len(gdpeval_tools) - 5} more")

    # 3. Create a sample GDPEval-style task
    logger.info("\nCreating sample task...")
    task = Task(
        name="Create Revenue Analysis Report",
        description="""
You are tasked with creating a comprehensive revenue analysis report.

Requirements:
1. Read the provided CSV data file containing quarterly revenue data
2. Create an Excel workbook with:
   - A summary sheet with total revenue by quarter
   - Formatted cells with currency formatting
   - A bar chart showing quarterly revenue trends
3. Generate a Word document report that includes:
   - Executive summary (2-3 paragraphs)
   - Key findings from the data analysis
   - Recommendations for Q4
4. Export the Word document as a PDF

Deliverables:
- Excel file: revenue_analysis.xlsx
- Word file: revenue_report.docx
- PDF file: revenue_report.pdf
        """.strip(),
    )

    # 4. Create sample reference CSV data
    logger.info("Creating sample reference data...")
    task_workspace = resource_manager.get_workspace_for_task(task.id)

    # Create a sample CSV file
    sample_csv_path = task_workspace / "revenue_data.csv"
    sample_csv_content = """Quarter,Revenue,Region
Q1 2024,125000,North America
Q2 2024,138000,North America
Q3 2024,145000,North America
Q1 2024,95000,Europe
Q2 2024,102000,Europe
Q3 2024,110000,Europe
Q1 2024,78000,Asia
Q2 2024,85000,Asia
Q3 2024,92000,Asia"""

    sample_csv_path.write_text(sample_csv_content)
    logger.info(f"Created sample data at: {sample_csv_path}")

    # 5. Create reference resource
    reference_resource = Resource(
        name="Revenue Data CSV",
        description="Quarterly revenue data by region",
        file_path=str(sample_csv_path),
        mime_type="text/csv",
        resource_role="intermediary",
    )

    # 6. Create AI agent with GDPEval tools
    logger.info("\nCreating AI agent with GDPEval tools...")
    from manager_agent_gym.core.agents.workflow_agents.workers.ai_agent import AIAgent

    agent_config = AIAgentConfig(
        agent_id="gdpeval_worker",
        agent_type="ai",
        system_prompt="You are a capable AI agent with access to comprehensive document processing, data analysis, and file manipulation tools. Complete tasks thoroughly and accurately.",
        model_name="gpt-4o",
        agent_description="GDPEval worker agent with full document processing toolkit",
        agent_capabilities=[
            "PDF processing",
            "Word document creation",
            "Excel data analysis",
            "CSV manipulation",
            "Chart generation",
            "Document search and retrieval",
            "OCR text extraction",
            "Code execution",
        ],
    )

    agent = AIAgent(config=agent_config, tools=gdpeval_tools)

    # 7. Execute the task
    logger.info("\nExecuting task...")
    logger.info("Task description:")
    logger.info(task.description)
    logger.info(f"\nReference resource: {reference_resource.name}")

    try:
        result = await agent.execute_task(task, resources=[reference_resource])

        logger.info("\n=== Task Execution Complete ===")
        logger.info(f"Success: {result.success}")
        logger.info(f"Execution time: {result.execution_time_seconds:.2f}s")
        logger.info(f"Output resources: {len(result.output_resources)}")

        if result.output_resources:
            logger.info("\nGenerated resources:")
            for resource in result.output_resources:
                logger.info(
                    f"  - {resource.name} ({resource.get_effective_mime_type()})"
                )
                if resource.file_path:
                    logger.info(f"    Path: {resource.file_path}")

        if result.execution_notes:
            logger.info("\nExecution notes:")
            for note in result.execution_notes:
                logger.info(f"  - {note}")

        if not result.success and result.error_message:
            logger.error(f"\nError: {result.error_message}")

    except Exception as e:
        logger.error(f"\nTask execution failed: {e}", exc_info=True)

    # 8. Cleanup (optional)
    logger.info("\n=== Cleanup ===")
    logger.info("Note: Task files are preserved in ./gdpeval_workspace for inspection")
    logger.info(f"Task workspace: {task_workspace}")

    # Optional: Clean up after inspection
    # resource_manager.cleanup_task_files(task.id)


def demo_individual_tools():
    """Demonstrate individual GDPEval tools."""

    logger.info("\n=== Individual Tool Demonstrations ===\n")

    # Setup
    resource_manager = ResourceFileManager(base_dir="./gdpeval_demo")
    demo_workspace = resource_manager.base_dir / "demo"
    demo_workspace.mkdir(parents=True, exist_ok=True)

    # 1. CSV Tool Demo
    logger.info("1. CSV Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.spreadsheets import (
        create_csv_tools,
    )

    csv_tools = create_csv_tools(resource_manager)
    logger.info(f"   Available CSV tools: {[t.name for t in csv_tools]}")

    # 2. Excel Tool Demo
    logger.info("\n2. Excel Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.spreadsheets import (
        create_excel_tools,
    )

    excel_tools = create_excel_tools(resource_manager)
    logger.info(f"   Available Excel tools: {[t.name for t in excel_tools]}")

    # 3. PDF Tool Demo
    logger.info("\n3. PDF Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.documents import (
        create_pdf_tools,
    )

    pdf_tools = create_pdf_tools(resource_manager)
    logger.info(f"   Available PDF tools: {[t.name for t in pdf_tools]}")

    # 4. DOCX Tool Demo
    logger.info("\n4. DOCX Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.documents import (
        create_docx_tools,
    )

    docx_tools = create_docx_tools(resource_manager)
    logger.info(f"   Available DOCX tools: {[t.name for t in docx_tools]}")

    # 5. RAG Tool Demo
    logger.info("\n5. RAG Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.rag import create_rag_tools

    rag_tools = create_rag_tools(resource_manager)
    logger.info(f"   Available RAG tools: {[t.name for t in rag_tools]}")

    # 6. Chart Tool Demo
    logger.info("\n6. Chart Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.charts import (
        create_chart_tools,
    )

    chart_tools = create_chart_tools(resource_manager)
    logger.info(f"   Available Chart tools: {[t.name for t in chart_tools]}")

    # 7. OCR Tool Demo
    logger.info("\n7. OCR Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.ocr import create_ocr_tools

    ocr_tools = create_ocr_tools(resource_manager)
    logger.info(f"   Available OCR tools: {[t.name for t in ocr_tools]}")

    # 8. Code Execution Tool Demo
    logger.info("\n8. Code Execution Tool Demo")
    from manager_agent_gym.core.agents.workflow_agents.tools.code_execution import (
        create_code_execution_tools,
    )

    code_tools = create_code_execution_tools(resource_manager)
    logger.info(f"   Available Code Execution tools: {[t.name for t in code_tools]}")

    logger.info("\n=== Total GDPEval Tools Summary ===")
    total_tools = (
        len(csv_tools)
        + len(excel_tools)
        + len(pdf_tools)
        + len(docx_tools)
        + len(rag_tools)
        + len(chart_tools)
        + len(ocr_tools)
        + len(code_tools)
    )
    logger.info(f"Total available tools: {total_tools}")


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())

    # Optionally, run individual tool demonstrations
    print("\n" + "=" * 60)
    demo_individual_tools()

    logger.info("\n=== Example Complete ===")
    logger.info(
        """
Next Steps:
1. Install GDPEval dependencies: uv sync --group gdpeval
2. Set E2B_API_KEY in your .env file for code execution support
3. Download actual GDPEval tasks from Hugging Face: huggingface.co/datasets/openai/gdpval
4. Modify this script to load real GDPEval tasks and reference files
5. Run evaluations and compare outputs against ground truth
    """
    )
