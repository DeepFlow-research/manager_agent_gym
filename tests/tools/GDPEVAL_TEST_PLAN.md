# GDPEval Tools Test Suite Plan

## Overview

Comprehensive test suite for validating all GDPEval tools work correctly, including document processing, spreadsheets, RAG, OCR, code execution, and chart generation.

## Test Structure

```
tests/
├── tools/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures for tool tests
│   ├── fixtures/                      # Sample test files
│   │   ├── sample.pdf
│   │   ├── sample.docx
│   │   ├── sample.xlsx
│   │   ├── sample.csv
│   │   ├── sample_image.png
│   │   └── sample_text.txt
│   ├── test_resource_storage.py       # ResourceFileManager tests
│   ├── test_resource_multimodal.py    # Enhanced Resource schema tests
│   ├── documents/
│   │   ├── __init__.py
│   │   ├── test_pdf_tools.py
│   │   ├── test_docx_tools.py
│   │   └── test_converters.py
│   ├── spreadsheets/
│   │   ├── __init__.py
│   │   ├── test_excel_tools.py
│   │   ├── test_csv_tools.py
│   │   └── test_charts.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── test_chunking.py
│   │   ├── test_search.py
│   │   └── test_retrieval.py
│   ├── ocr/
│   │   └── test_ocr_tools.py
│   ├── code_execution/
│   │   ├── __init__.py
│   │   ├── test_e2b_sandbox.py        # Mocked E2B tests
│   │   └── test_execution_tools.py
│   ├── charts/
│   │   └── test_matplotlib_charts.py
│   ├── integration/
│   │   ├── test_tool_factory.py       # ToolFactory integration
│   │   ├── test_gdpeval_workflow.py   # End-to-end workflow
│   │   └── test_cross_tool_usage.py   # Multi-tool scenarios
│   └── live/                          # Expensive/live API tests
│       ├── test_e2b_live.py
│       ├── test_ocr_live.py
│       └── test_libreoffice_live.py
```

## Test Categories

### 1. Unit Tests (Fast, No External Dependencies)

#### 1.1 Resource Schema Tests (`test_resource_multimodal.py`)

**Purpose**: Validate enhanced Resource schema with file support

**Tests**:
- ✅ `test_resource_file_path_storage` - file_path field works
- ✅ `test_resource_role_field` - output vs intermediary roles
- ✅ `test_resource_mime_type` - MIME type handling
- ✅ `test_is_file_resource` - Helper method works
- ✅ `test_is_text_resource` - Helper method works
- ✅ `test_get_effective_mime_type` - Falls back to content_type
- ✅ `test_load_file_content` - Loading binary content
- ✅ `test_save_to_file` - Saving binary content
- ✅ `test_load_file_content_missing` - Error handling
- ✅ `test_pretty_print_file_resource` - Display formatting

#### 1.2 Resource Storage Tests (`test_resource_storage.py`)

**Purpose**: Validate ResourceFileManager lifecycle

**Tests**:
- ✅ `test_resource_manager_init` - Initialization
- ✅ `test_get_workspace_for_task` - Task-scoped directories
- ✅ `test_save_resource_file` - Save and path tracking
- ✅ `test_load_resource_file` - Load saved files
- ✅ `test_save_resource_file_unique_names` - Collision handling
- ✅ `test_cleanup_task_files` - Cleanup works
- ✅ `test_cleanup_all` - Full cleanup
- ✅ `test_get_file_path_for_resource` - Path generation
- ✅ `test_sanitize_filename` - Unsafe character handling
- ✅ `test_context_manager` - Context manager protocol

#### 1.3 Document Tools Tests

**`test_pdf_tools.py`**:
- ✅ `test_read_pdf` - Extract text from PDF
- ✅ `test_read_pdf_with_pages` - Page marker format
- ✅ `test_extract_pdf_tables` - Table extraction
- ✅ `test_extract_pdf_tables_specific_page` - Single page tables
- ✅ `test_merge_pdfs` - PDF merging
- ✅ `test_merge_pdfs_missing_file` - Error handling
- ✅ `test_create_simple_pdf` - PDF generation
- ✅ `test_create_simple_pdf_with_title` - Titled PDF
- ❌ `test_read_pdf_missing_file` - File not found handling
- ❌ `test_read_pdf_empty` - Empty PDF handling

**`test_docx_tools.py`**:
- ✅ `test_read_docx` - Extract text from Word
- ✅ `test_read_docx_with_tables` - Table extraction
- ✅ `test_create_docx` - DOCX generation
- ✅ `test_create_docx_with_title` - Titled document
- ✅ `test_create_docx_with_styles` - Style templates (normal/formal/memo)
- ✅ `test_create_docx_with_markdown_headings` - Heading detection
- ✅ `test_add_table_to_docx` - Table insertion
- ✅ `test_add_table_to_docx_with_header` - Header formatting
- ✅ `test_extract_docx_structure` - Structure metadata
- ❌ `test_read_docx_missing_file` - Error handling
- ❌ `test_create_docx_invalid_path` - Path validation

**`test_converters.py`**:
- ✅ `test_convert_markdown_to_docx` - MD→DOCX conversion
- ✅ `test_convert_markdown_to_docx_with_lists` - List handling
- ✅ `test_convert_markdown_to_docx_with_code` - Code blocks
- ✅ `test_convert_text_to_docx` - Plain text→DOCX
- ❌ `test_convert_docx_to_pdf` - DOCX→PDF (needs LibreOffice, mark as live)
- ❌ `test_convert_markdown_complex` - Complex MD features

#### 1.4 Spreadsheet Tools Tests

**`test_excel_tools.py`**:
- ✅ `test_read_excel` - Read Excel to JSON
- ✅ `test_read_excel_specific_sheet` - Sheet selection
- ✅ `test_read_excel_nonexistent_sheet` - Error handling
- ✅ `test_create_excel` - Excel creation with data
- ✅ `test_create_excel_with_headers` - Header formatting
- ✅ `test_create_excel_with_formatting` - Styled cells
- ✅ `test_add_excel_sheet` - Add sheet to existing workbook
- ✅ `test_add_excel_sheet_duplicate_name` - Duplicate detection
- ✅ `test_format_excel_cells_currency` - Currency formatting
- ✅ `test_format_excel_cells_percent` - Percent formatting
- ✅ `test_format_excel_cells_date` - Date formatting
- ✅ `test_get_excel_info` - Workbook metadata
- ❌ `test_read_excel_missing_file` - File not found
- ❌ `test_format_excel_cells_invalid_range` - Range validation

**`test_csv_tools.py`**:
- ✅ `test_read_csv` - Read CSV to JSON
- ✅ `test_read_csv_with_max_rows` - Row limiting
- ✅ `test_write_csv` - Write CSV from data
- ✅ `test_write_csv_with_index` - Index inclusion
- ✅ `test_analyze_csv` - Summary statistics
- ✅ `test_analyze_csv_with_numeric` - Numeric summaries
- ✅ `test_filter_csv_equals` - Equality filter
- ✅ `test_filter_csv_contains` - String contains filter
- ✅ `test_filter_csv_numeric_comparison` - Numeric filters
- ❌ `test_read_csv_missing_file` - Error handling
- ❌ `test_filter_csv_invalid_column` - Column validation

**`test_charts.py`**:
- ✅ `test_add_excel_chart_bar` - Bar chart in Excel
- ✅ `test_add_excel_chart_line` - Line chart in Excel
- ✅ `test_add_excel_chart_pie` - Pie chart in Excel
- ✅ `test_create_excel_with_chart` - New Excel with chart
- ✅ `test_add_excel_chart_invalid_type` - Unknown chart type
- ❌ `test_add_excel_chart_missing_file` - File not found
- ❌ `test_add_excel_chart_invalid_range` - Range validation

#### 1.5 RAG Tools Tests

**`test_chunking.py`**:
- ✅ `test_chunk_by_paragraphs` - Paragraph chunking
- ✅ `test_chunk_by_paragraphs_with_overlap` - Overlap handling
- ✅ `test_chunk_by_paragraphs_size_limit` - Size limits
- ✅ `test_chunk_by_sentences` - Sentence chunking
- ✅ `test_chunk_by_sentences_with_overlap` - Sentence overlap
- ✅ `test_chunk_by_pages` - Page-based chunking
- ✅ `test_chunk_by_pages_with_markers` - Page number extraction
- ✅ `test_chunk_with_headers` - Markdown header context
- ❌ `test_chunk_empty_text` - Empty text handling
- ❌ `test_chunk_very_long_paragraph` - Long paragraph handling

**`test_search.py`**:
- ✅ `test_document_index_init` - Index initialization
- ✅ `test_add_documents` - Add documents to index
- ✅ `test_build_index` - Build BM25 index
- ✅ `test_search_basic` - Basic search
- ✅ `test_search_top_k` - Top-k results
- ✅ `test_search_min_score` - Score thresholding
- ✅ `test_get_document` - Retrieve document by ID
- ✅ `test_document_index_manager` - Manager lifecycle
- ✅ `test_create_multiple_indices` - Multiple indices
- ❌ `test_search_before_build` - Build validation
- ❌ `test_search_empty_index` - Empty index handling

**`test_retrieval.py`**:
- ✅ `test_index_reference_documents_pdf` - Index PDFs
- ✅ `test_index_reference_documents_docx` - Index DOCX
- ✅ `test_index_reference_documents_txt` - Index text files
- ✅ `test_index_reference_documents_chunking_strategies` - Different strategies
- ✅ `test_search_documents_basic` - Basic search
- ✅ `test_search_documents_top_k` - Result limiting
- ✅ `test_search_documents_with_citations` - Source attribution
- ✅ `test_get_document_chunk` - Retrieve specific chunk
- ✅ `test_list_document_indices` - List all indices
- ❌ `test_index_unsupported_file_type` - Unsupported file error
- ❌ `test_search_nonexistent_index` - Index not found error
- ❌ `test_index_missing_file` - Missing file error

#### 1.6 Chart Generation Tests

**`test_matplotlib_charts.py`**:
- ✅ `test_create_chart_bar` - Bar chart generation
- ✅ `test_create_chart_line` - Line chart generation
- ✅ `test_create_chart_pie` - Pie chart generation
- ✅ `test_create_chart_scatter` - Scatter plot generation
- ✅ `test_create_chart_with_labels` - Axis labels
- ✅ `test_create_multi_series_chart_bar` - Multi-series bar
- ✅ `test_create_multi_series_chart_line` - Multi-series line
- ✅ `test_create_chart_from_csv` - Direct CSV plotting
- ✅ `test_create_chart_invalid_type` - Unknown chart type
- ❌ `test_create_chart_missing_data` - Missing data handling
- ❌ `test_create_chart_invalid_csv_column` - Column validation

#### 1.7 Code Execution Tests (Mocked)

**`test_execution_tools.py`**:
- ✅ `test_execute_python_code_mock` - Mocked Python execution
- ✅ `test_execute_python_code_mock_error` - Error handling
- ✅ `test_execute_python_code_mock_timeout` - Timeout handling
- ✅ `test_execute_node_code_mock` - Mocked Node execution (limited)
- ❌ `test_execute_python_code_invalid_syntax` - Syntax error handling

### 2. Integration Tests

#### 2.1 Tool Factory Tests (`test_tool_factory.py`)

**Purpose**: Validate tool creation and configuration

**Tests**:
- ✅ `test_create_gdpeval_tools` - All tools created
- ✅ `test_create_gdpeval_tools_count` - Expected tool count
- ✅ `test_create_gdpeval_tools_with_resource_manager` - Custom manager
- ✅ `test_create_gdpeval_tools_with_e2b_key` - E2B key passing
- ✅ `test_create_gdpeval_tools_no_duplicates` - No duplicate tool names
- ❌ `test_gdpeval_tools_callable` - All tools are callable

#### 2.2 Cross-Tool Usage Tests (`test_cross_tool_usage.py`)

**Purpose**: Test tools working together

**Tests**:
- ✅ `test_csv_to_excel_with_chart` - CSV→Excel→Chart pipeline
- ✅ `test_pdf_to_excel_analysis` - PDF→Extract→Excel
- ✅ `test_rag_to_docx_report` - Index→Search→DOCX
- ✅ `test_markdown_to_pdf_via_docx` - MD→DOCX→PDF
- ✅ `test_data_analysis_to_chart` - Analyze→Chart
- ❌ `test_full_gdpeval_task_simulation` - Complete task simulation

#### 2.3 Workflow Integration Tests (`test_gdpeval_workflow.py`)

**Purpose**: Test GDPEval tools in ma-gym workflow

**Tests**:
- ✅ `test_ai_agent_with_gdpeval_tools` - Agent creation
- ✅ `test_task_execution_with_file_resources` - File resource handling
- ✅ `test_resource_cleanup_after_task` - Cleanup lifecycle
- ✅ `test_multimodal_resource_flow` - Resources between tasks
- ❌ `test_gdpeval_example_runner` - Run example script

### 3. Live/Expensive Tests (Marked with pytest markers)

#### 3.1 E2B Live Tests (`test_e2b_live.py`)

**Marker**: `@pytest.mark.live_api`

**Tests**:
- ⏸️ `test_e2b_python_execution_live` - Real E2B Python execution
- ⏸️ `test_e2b_python_execution_with_packages` - numpy/pandas imports
- ⏸️ `test_e2b_python_execution_timeout` - Real timeout behavior
- ⏸️ `test_e2b_python_execution_error` - Real error handling

**Requirements**: E2B_API_KEY in environment

#### 3.2 OCR Live Tests (`test_ocr_live.py`)

**Marker**: `@pytest.mark.live_ocr`

**Tests**:
- ⏸️ `test_ocr_extract_text_from_image_live` - Real Tesseract OCR
- ⏸️ `test_ocr_extract_text_from_pdf_images_live` - Scanned PDF OCR
- ⏸️ `test_ocr_confidence_scores_live` - Confidence extraction

**Requirements**: Tesseract installed on system

#### 3.3 LibreOffice Conversion Tests (`test_libreoffice_live.py`)

**Marker**: `@pytest.mark.live_conversion`

**Tests**:
- ⏸️ `test_convert_docx_to_pdf_live` - Real DOCX→PDF conversion
- ⏸️ `test_convert_docx_to_pdf_with_images` - Image preservation

**Requirements**: LibreOffice (soffice) installed

#### 3.4 Cohere Reranking Tests

**Marker**: `@pytest.mark.live_api`

**Tests**:
- ⏸️ `test_rag_search_with_cohere_rerank` - Real Cohere reranking
- ⏸️ `test_rag_search_fallback_without_cohere` - Graceful fallback

**Requirements**: COHERE_API_KEY in environment

## Test Fixtures

### Shared Fixtures (`tests/tools/conftest.py`)

```python
@pytest.fixture
def resource_manager(tmp_path):
    """ResourceFileManager with temp directory."""
    return ResourceFileManager(base_dir=tmp_path / "test_resources")

@pytest.fixture
def sample_pdf(tmp_path):
    """Sample PDF file for testing."""
    # Generate using reportlab
    
@pytest.fixture
def sample_docx(tmp_path):
    """Sample DOCX file for testing."""
    # Generate using python-docx

@pytest.fixture
def sample_csv(tmp_path):
    """Sample CSV file for testing."""
    # Generate sample data

@pytest.fixture
def sample_excel(tmp_path):
    """Sample Excel file for testing."""
    # Generate using openpyxl

@pytest.fixture
def sample_image(tmp_path):
    """Sample image with text for OCR testing."""
    # Generate using PIL with text overlay

@pytest.fixture
def sample_text_file(tmp_path):
    """Sample text file for RAG testing."""
    # Multi-paragraph text

@pytest.fixture
def gdpeval_tools(resource_manager):
    """Full GDPEval toolkit."""
    return ToolFactory.create_gdpeval_tools(resource_manager)

@pytest.fixture
def mock_e2b_executor():
    """Mocked E2B executor for fast tests."""
    # Return mock with predictable responses
```

## Running the Tests

### Run all tests (fast only):
```bash
pytest tests/tools/ --fast
```

### Run with live API tests:
```bash
pytest tests/tools/ -m live_api
```

### Run specific tool category:
```bash
pytest tests/tools/documents/
pytest tests/tools/spreadsheets/
pytest tests/tools/rag/
```

### Run integration tests only:
```bash
pytest tests/tools/integration/
```

### Run with coverage:
```bash
pytest tests/tools/ --cov=manager_agent_gym.core.agents.workflow_agents.tools --cov-report=html
```

## Pytest Markers

Add to `conftest.py`:

```python
pytest.mark.live_api: "Requires live API keys (E2B, Cohere)"
pytest.mark.live_ocr: "Requires Tesseract installed"
pytest.mark.live_conversion: "Requires LibreOffice installed"
pytest.mark.slow: "Slow tests (>5s)"
```

## Success Criteria

- [ ] All unit tests pass in <30s
- [ ] 90%+ code coverage for tool modules
- [ ] All error paths tested
- [ ] All file I/O edge cases covered
- [ ] Integration tests validate cross-tool usage
- [ ] Live tests pass with real dependencies
- [ ] No test pollution (tests clean up after themselves)
- [ ] Tests are deterministic (no flaky tests)

## Implementation Priority

1. **Phase 1** (Critical Path):
   - Resource schema tests
   - Resource storage tests
   - Document tool tests (PDF, DOCX)
   - Spreadsheet tool tests (Excel, CSV)
   
2. **Phase 2** (Core Functionality):
   - RAG tool tests (chunking, search)
   - Chart generation tests
   - Tool factory integration tests
   
3. **Phase 3** (Special Cases):
   - OCR tests (with mocked Tesseract)
   - Code execution tests (fully mocked)
   - Converter tests
   
4. **Phase 4** (Live Tests):
   - E2B live tests
   - OCR live tests
   - LibreOffice live tests
   - Cohere reranking tests

## Dependencies for Testing

Add to `pyproject.toml` dev dependencies:
```toml
[dependency-groups]
dev = [
    # ... existing ...
    "pytest-mock>=3.12.0",      # Mocking support
    "pytest-cov>=4.1.0",        # Coverage reporting
    "pytest-timeout>=2.2.0",    # Timeout handling
    "Faker>=20.0.0",            # Generate test data
]
```

## Notes

- Use `tmp_path` fixture for all file operations
- Mock expensive operations (E2B, OCR, LibreOffice) by default
- Provide opt-in live tests for CI/manual verification
- Generate test fixtures programmatically (don't check in large binary files)
- Test both success and failure paths
- Validate error messages are helpful
- Test resource cleanup to prevent test pollution

