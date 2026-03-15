# Testing Guide for Prodx Tools

This directory contains comprehensive test suites for all productivity tools.

## Test Files

- `test_excel_tools.py` - Tests for 4 Excel tools
- `test_powerpoint_tools.py` - Tests for 3 PowerPoint tools
- `test_visualization_tools.py` - Tests for 2 visualization tools
- `test_ocr_tools.py` - Tests for 3 OCR tools
- `test_file_operations_tools.py` - Tests for 2 file operations tools

## Running Tests

### Run All Tests

```bash
# From the prodx directory
python run_tests.py

# Or using pytest directly
pytest test_*.py -v
```

### Run Specific Test File

```bash
python run_tests.py test_excel_tools.py

# Or using pytest
pytest test_excel_tools.py -v
```

### Run with Verbose Output

```bash
python run_tests.py -v

# Or using pytest
pytest test_*.py -v --tb=short
```

### Run Specific Test Class

```bash
pytest test_excel_tools.py::TestReadExcelStructuredTool -v
```

### Run Specific Test Method

```bash
pytest test_excel_tools.py::TestReadExcelStructuredTool::test_read_excel_basic -v
```

## Test Coverage

Each test file includes:

1. **Helper Function Tests** - Tests for utility functions (encoding/decoding, data conversion)
2. **Tool Functionality Tests** - Tests for each tool's main functionality
3. **Error Handling Tests** - Tests that verify tools handle errors gracefully
4. **Edge Case Tests** - Tests for boundary conditions and unusual inputs

## Test Requirements

Tests require the same dependencies as the tools:

```bash
pip install pytest openpyxl pandas python-pptx plotly streamlit pytesseract easyocr pillow opencv-python pdf2image PyPDF2
```

## Test Structure

Each test class follows this pattern:

```python
class TestToolName:
    """Test ToolName."""
    
    def test_basic_functionality(self):
        """Test basic tool usage."""
        # Arrange
        tool = ToolName()
        test_data = create_test_data()
        
        # Act
        result = tool._run(test_data)
        
        # Assert
        assert result is not None
        assert "status" in result
```

## Common Test Patterns

### Testing Base64 Input

```python
def test_with_base64_input(self):
    tool = ToolName()
    test_data = b"test content"
    encoded = base64.b64encode(test_data).decode('utf-8')
    result = tool._run(encoded)
    assert result is not None
```

### Testing File Path Input

```python
def test_with_file_path(self):
    tool = ToolName()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name
    
    try:
        result = tool._run(tmp_path)
        assert result is not None
    finally:
        os.unlink(tmp_path)
```

### Testing Error Handling

```python
def test_error_handling(self):
    tool = ToolName()
    result = tool._run("invalid_input")
    assert "Error" in result
    assert isinstance(result, str)
```

## Notes

- Tests use relative imports (`.tool_name`) to work within the package structure
- Tests handle missing optional dependencies gracefully
- All tests verify that tools return error messages instead of crashing
- Tests create temporary files and clean them up automatically

## Continuous Integration

These tests are designed to run in CI/CD pipelines. They:
- Don't require external services
- Clean up temporary files
- Handle missing dependencies gracefully
- Provide clear error messages

