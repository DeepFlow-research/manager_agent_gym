"""Comprehensive tests for spreadsheet processing tools.

Tests Excel, CSV, and chart operations.
"""

from pathlib import Path

import pytest

from manager_agent_gym.core.agents.workflow_agents.tools.spreadsheets import (
    CSVData,
    ExcelData,
    _add_excel_chart,
    _add_excel_sheet,
    _analyze_csv,
    _create_excel,
    _format_excel_cells,
    _get_excel_info,
    _read_csv,
    _read_excel,
    _write_csv,
)


# ============================================================================
# EXCEL TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_read_excel_success(sample_excel: Path) -> None:
    """Test reading Excel file successfully."""
    result = await _read_excel(str(sample_excel))

    assert result["success"] is True
    assert "data" in result
    assert result["num_rows"] > 0
    assert result["num_cols"] > 0


@pytest.mark.asyncio
async def test_read_excel_missing_file() -> None:
    """Test reading non-existent Excel file."""
    result = await _read_excel("/nonexistent/file.xlsx")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_create_excel(tmp_path: Path) -> None:
    """Test creating Excel file."""
    output_path = tmp_path / "created.xlsx"

    data = ExcelData(
        headers=["Name", "Age", "City"],
        rows=[
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ],
    )

    result = await _create_excel(data, str(output_path))

    assert result["success"] is True
    assert output_path.exists()
    assert result["num_rows"] == 2


@pytest.mark.asyncio
async def test_add_excel_sheet(sample_excel: Path, tmp_path: Path) -> None:
    """Test adding sheet to Excel file."""
    output_path = tmp_path / "multi_sheet.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    new_data = ExcelData(
        headers=["Product", "Quantity"],
        rows=[["Apple", "10"], ["Banana", "20"]],
    )

    result = await _add_excel_sheet(str(output_path), "Products", new_data)

    assert result["success"] is True


@pytest.mark.asyncio
async def test_format_excel_cells(sample_excel: Path, tmp_path: Path) -> None:
    """Test formatting Excel cells."""
    output_path = tmp_path / "formatted.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    result = await _format_excel_cells(
        str(output_path), "Data", "D2:D5", "currency", "$#,##0.00"
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_format_excel_cells_color_rgb(sample_excel: Path, tmp_path: Path) -> None:
    """Test formatting Excel cells with RGB color (auto-conversion to aRGB)."""
    output_path = tmp_path / "formatted_color_rgb.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    # Test with standard RGB hex color (#RRGGBB)
    result = await _format_excel_cells(
        str(output_path), "Data", "A1:A5", "color", "#FF0000"
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_format_excel_cells_color_argb(
    sample_excel: Path, tmp_path: Path
) -> None:
    """Test formatting Excel cells with aRGB color (already in correct format)."""
    output_path = tmp_path / "formatted_color_argb.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    # Test with aRGB hex color (#AARRGGBB)
    result = await _format_excel_cells(
        str(output_path), "Data", "B1:B5", "color", "#FFFF0000"
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_format_excel_cells_color_no_hash(
    sample_excel: Path, tmp_path: Path
) -> None:
    """Test formatting Excel cells with color without # prefix."""
    output_path = tmp_path / "formatted_color_no_hash.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    # Test with RGB color without # prefix (should be handled)
    result = await _format_excel_cells(
        str(output_path), "Data", "C1:C5", "color", "00FF00"
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_format_excel_cells_color_invalid(
    sample_excel: Path, tmp_path: Path
) -> None:
    """Test formatting Excel cells with invalid color format."""
    output_path = tmp_path / "formatted_color_invalid.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    # Test with invalid color (too short)
    result = await _format_excel_cells(
        str(output_path), "Data", "D1:D5", "color", "#FFF"
    )

    assert result["success"] is False
    assert "Invalid color format" in result["error"]


@pytest.mark.asyncio
async def test_get_excel_info(sample_excel: Path) -> None:
    """Test getting Excel file info."""
    result = await _get_excel_info(str(sample_excel))

    assert result["success"] is True
    assert "sheets" in result
    assert result["num_sheets"] > 0


# ============================================================================
# CSV TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_read_csv_success(sample_csv: Path) -> None:
    """Test reading CSV file successfully."""
    result = await _read_csv(str(sample_csv))

    assert result["success"] is True
    assert "columns" in result
    assert "data" in result
    assert result["num_rows"] > 0


@pytest.mark.asyncio
async def test_read_csv_missing_file() -> None:
    """Test reading non-existent CSV file."""
    result = await _read_csv("/nonexistent/file.csv")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_read_csv_max_rows(sample_csv: Path) -> None:
    """Test reading CSV with row limit."""
    result = await _read_csv(str(sample_csv), max_rows=2)

    assert result["success"] is True
    assert result["num_rows"] <= 2


@pytest.mark.asyncio
async def test_write_csv(tmp_path: Path) -> None:
    """Test writing CSV file."""
    output_path = tmp_path / "output.csv"

    data = CSVData(
        columns=["Name", "Age", "City"],
        data=[
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ],
    )

    result = await _write_csv(data, str(output_path))

    assert result["success"] is True
    assert output_path.exists()


@pytest.mark.asyncio
async def test_analyze_csv(sample_csv: Path) -> None:
    """Test analyzing CSV file."""
    result = await _analyze_csv(str(sample_csv))

    assert result["success"] is True
    assert "num_rows" in result
    assert "columns" in result
    assert "dtypes" in result


# ============================================================================
# CHART TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_add_excel_chart(sample_excel: Path, tmp_path: Path) -> None:
    """Test adding chart to Excel."""
    output_path = tmp_path / "with_chart.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    result = await _add_excel_chart(
        str(output_path),
        "Data",
        "bar",
        "A1:B5",
        "Sample Chart",
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_add_excel_chart_line(sample_excel: Path, tmp_path: Path) -> None:
    """Test adding line chart to Excel."""
    output_path = tmp_path / "line_chart.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    result = await _add_excel_chart(
        str(output_path),
        "Data",
        "line",
        "A1:B5",
        "Line Chart",
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_add_excel_chart_invalid_type(sample_excel: Path, tmp_path: Path) -> None:
    """Test adding invalid chart type."""
    output_path = tmp_path / "bad_chart.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    result = await _add_excel_chart(
        str(output_path),
        "Data",
        "invalid_type",
        "A1:B5",
        "Bad Chart",
    )

    assert result["success"] is False
    assert "error" in result


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_excel_empty_data() -> None:
    """Test creating Excel with empty data."""
    data = ExcelData(headers=["A", "B"], rows=[])

    result = await _create_excel(data, "/tmp/empty.xlsx")

    # Should succeed but with 0 rows
    assert result["success"] is True


@pytest.mark.asyncio
async def test_add_excel_sheet_missing_file(tmp_path: Path) -> None:
    """Test adding sheet to non-existent Excel."""
    data = ExcelData(headers=["A"], rows=[["1"]])

    result = await _add_excel_sheet("/nonexistent.xlsx", "Sheet2", data)

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_format_cells_invalid_range(sample_excel: Path, tmp_path: Path) -> None:
    """Test formatting with invalid cell range."""
    output_path = tmp_path / "bad_format.xlsx"

    import shutil

    shutil.copy(str(sample_excel), str(output_path))

    result = await _format_excel_cells(str(output_path), "Data", "INVALID", "bold")

    assert result["success"] is False


@pytest.mark.asyncio
async def test_write_csv_no_columns() -> None:
    """Test writing CSV with no columns."""
    data = CSVData(columns=[], data=[])

    result = await _write_csv(data, "/tmp/bad.csv")

    assert result["success"] is False
    assert "error" in result
