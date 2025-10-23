# GDPEval Examples

This directory contains examples for running GDPEval benchmark tasks using the Manager Agent Gym toolkit.

## Overview

GDPEval (GDP Evaluation) is an OpenAI benchmark dataset that tests AI agents on realistic workplace tasks involving document processing, data analysis, and deliverable generation.

The ma-gym GDPEval toolkit provides comprehensive tools for:

- **Document Processing**: PDF and DOCX reading, writing, and conversion
- **Spreadsheets**: Excel and CSV manipulation with formatting and charts
- **RAG (Retrieval-Augmented Generation)**: BM25-based document search with optional Cohere reranking
- **OCR**: Text extraction from images and scanned PDFs
- **Code Execution**: Sandboxed Python code execution via E2B
- **Chart Generation**: Create publication-quality charts with matplotlib

## Installation

Install the GDPEval dependencies:

```bash
uv sync --group gdpeval
```

For code execution support, you'll also need an E2B API key. Add it to your `.env` file:

```bash
E2B_API_KEY=your_e2b_api_key_here
```

Get an E2B API key at: https://e2b.dev

For OCR support, install Tesseract:

- **macOS**: `brew install tesseract`
- **Ubuntu**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

## Running the Example

Run the sample task execution:

```bash
python -m examples.gdpeval.run_gdpeval_task
```

This example demonstrates:

1. Creating an AI agent with the full GDPEval toolkit
2. Processing a sample CSV data file
3. Generating Excel workbooks with charts
4. Creating Word documents with formatted content
5. Converting documents to PDF

## Tool Categories

### 1. Document Tools

**PDF Tools:**
- `read_pdf`: Extract text from PDFs with page markers
- `extract_pdf_tables`: Extract tables from PDFs
- `merge_pdfs`: Combine multiple PDFs
- `create_simple_pdf`: Generate PDFs from text

**DOCX Tools:**
- `read_docx`: Extract text from Word documents
- `create_docx`: Generate formatted Word documents
- `add_table_to_docx`: Insert tables into Word documents
- `extract_docx_structure`: Get document structure metadata

**Converters:**
- `convert_docx_to_pdf`: Convert Word to PDF (requires LibreOffice)
- `convert_markdown_to_docx`: Convert Markdown to Word
- `convert_text_to_docx`: Convert plain text to Word

### 2. Spreadsheet Tools

**Excel Tools:**
- `read_excel`: Read Excel files to JSON
- `create_excel`: Generate Excel workbooks with formatting
- `add_excel_sheet`: Add sheets to existing workbooks
- `format_excel_cells`: Apply number/currency/date formatting
- `add_excel_chart`: Insert charts into Excel files

**CSV Tools:**
- `read_csv`: Read CSV to JSON
- `write_csv`: Write data to CSV
- `analyze_csv`: Get summary statistics
- `filter_csv`: Filter CSV data by conditions

### 3. RAG Tools

- `index_reference_documents`: Create searchable BM25 index from PDFs/DOCX/TXT
- `search_documents`: Semantic search with optional Cohere reranking
- `get_document_chunk`: Retrieve specific document chunks
- `list_document_indices`: List all active indices

### 4. Chart Tools

- `create_chart`: Generate bar/line/pie/scatter charts
- `create_multi_series_chart`: Multi-series charts
- `create_chart_from_csv`: Direct CSV to chart

### 5. OCR Tools

- `extract_text_from_image`: OCR from image files
- `extract_text_from_pdf_images`: OCR scanned PDFs
- `get_image_text_confidence`: OCR with confidence scores

### 6. Code Execution Tools

- `execute_python_code`: Run Python in E2B sandbox
- `execute_node_code`: Run Node.js in E2B sandbox (limited support)

## Using with Real GDPEval Tasks

To use this toolkit with actual GDPEval tasks:

1. **Download the dataset:**

```python
from datasets import load_dataset
dataset = load_dataset("openai/gdpval")
```

2. **Load a task:**

```python
task_data = dataset["test"][0]  # Get first test task
```

3. **Create a Task object:**

```python
from manager_agent_gym.schemas.domain import Task

task = Task(
    name=task_data["task_name"],
    description=task_data["task_description"],
)
```

4. **Download reference files:**

Many GDPEval tasks include reference files (PDFs, Excel sheets, etc.). Download these and create Resource objects:

```python
from manager_agent_gym.schemas.domain import Resource

reference_files = []
for file_info in task_data.get("reference_files", []):
    # Download file
    file_path = download_file(file_info["url"])
    
    resource = Resource(
        name=file_info["name"],
        description=file_info["description"],
        file_path=str(file_path),
        mime_type=file_info["mime_type"],
        resource_role="intermediary",
    )
    reference_files.append(resource)
```

5. **Execute the task:**

```python
agent = AIAgent(config=agent_config, tools=gdpeval_tools)
result = await agent.execute_task(task, resources=reference_files)
```

6. **Validate outputs:**

Compare the agent's output resources against the GDPEval ground truth deliverables.

## Resource Management

The toolkit uses `ResourceFileManager` for task-scoped file storage:

```python
from manager_agent_gym.core.workflow.resource_storage import ResourceFileManager

# Create manager
resource_manager = ResourceFileManager(base_dir="./my_workspace")

# Get task workspace
workspace = resource_manager.get_workspace_for_task(task_id)

# Save a file
file_path = resource_manager.save_resource_file(
    resource, 
    file_content_bytes,
    task_id=task_id
)

# Clean up after task
resource_manager.cleanup_task_files(task_id)
```

## Troubleshooting

**OCR not working:**
- Ensure Tesseract is installed and in your PATH
- Try: `tesseract --version`

**DOCX to PDF conversion fails:**
- Install LibreOffice: https://www.libreoffice.org/download/
- Ensure `soffice` is in your PATH

**Code execution fails:**
- Verify E2B_API_KEY is set in `.env`
- Check E2B credits at https://e2b.dev/dashboard

**Import errors:**
- Run `uv sync --group gdpeval` to install all dependencies

## Next Steps

- Implement evaluation metrics for GDPEval outputs
- Add support for additional document formats
- Integrate with existing ma-gym workflow system
- Build automated GDPEval benchmark runner
- Create leaderboard tracking for different agent configurations

## License

See the main project LICENSE file.

