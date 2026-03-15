# Comprehensive Testing Guide for Prodx Tools

This guide provides instructions for running comprehensive, world-class tests for all productivity tools.

## Test Files Overview

### Individual Tool Test Files
- **`test_excel_tools.py`** - 4 Excel tools (ReadExcelStructuredTool, ModifyExcelTool, CreateExcelChartTool, AnalyzeExcelSecurityTool)
- **`test_powerpoint_tools.py`** - 3 PowerPoint tools (CreatePresentationTool, AddSlideTool, AddChartToSlideTool)
- **`test_visualization_tools.py`** - 2 Visualization tools (CreatePlotlyChartTool, CreateChartFromFileTool)
- **`test_ocr_tools.py`** - 3 OCR tools (ExtractTextFromImageTool, ExtractTextFromPDFImagesTool, AnalyzeDocumentStructureTool)
- **`test_file_operations_tools.py`** - 2 File operations tools (SaveFileForDownloadTool, ConvertFileFormatTool)

### Comprehensive Test Files
- **`test_comprehensive_real_world.py`** - End-to-end workflow tests, performance tests, integration tests

### Utility Files
- **`test_utils.py`** - Helper functions for creating test data, downloading images, etc.
- **`validate_tests.py`** - Script to validate test file structure and imports
- **`run_tests.py`** - Test runner script

## Installation

### Required Python Packages

```bash
# Core testing framework
pip install pytest pytest-cov

# For downloading test images
pip install requests

# Tool dependencies (if not already installed)
pip install openpyxl pandas python-pptx plotly streamlit pytesseract easyocr pillow opencv-python pdf2image PyPDF2
```

### System Dependencies

**For OCR tools:**
- Tesseract OCR: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- EasyOCR dependencies: Automatically installed with easyocr package

## Running Tests

### Quick Validation

```bash
cd streamlit_app/modules/tools/prodx
python3 validate_tests.py
```

This validates that all test files can be imported and have proper structure.

### Run All Tests

```bash
# Using the test runner
python3 run_tests.py

# Or using pytest directly
pytest test_*.py -v

# With coverage
pytest test_*.py -v --cov=. --cov-report=html
```

### Run Specific Test File

```bash
# Excel tools only
pytest test_excel_tools.py -v

# PowerPoint tools only
pytest test_powerpoint_tools.py -v

# OCR tools with web image downloads
pytest test_ocr_tools.py -v -k "web"

# Real-world comprehensive tests
pytest test_comprehensive_real_world.py -v
```

### Run Specific Test Classes

```bash
# Test helper functions only
pytest test_excel_tools.py::TestHelperFunctions -v

# Test real-world scenarios
pytest test_excel_tools.py::TestRealWorldScenarios -v

# Test error handling
pytest test_excel_tools.py::TestErrorHandling -v
```

### Run Specific Test Methods

```bash
# Single test method
pytest test_excel_tools.py::TestReadExcelStructuredTool::test_read_excel_basic -v

# All tests matching a pattern
pytest test_ocr_tools.py -k "web" -v
```

## Test Coverage

### What Each Test File Covers

#### test_excel_tools.py
- ✅ Helper function tests (encoding/decoding)
- ✅ Basic functionality for all 4 tools
- ✅ Reading Excel with formulas and formatting
- ✅ Complex modification operations
- ✅ Chart creation with various chart types
- ✅ Security analysis
- ✅ Real-world scenarios (large files, multiple sheets)
- ✅ Error handling (invalid input, corrupted files, large files)

#### test_powerpoint_tools.py
- ✅ Helper function tests
- ✅ Creating presentations with various layouts
- ✅ Adding slides at different positions
- ✅ Adding charts to slides
- ✅ Image embedding
- ✅ Error handling

#### test_visualization_tools.py
- ✅ Data conversion (dict, list, JSON, DataFrame)
- ✅ Chart creation (line, bar, pie, scatter, heatmap)
- ✅ Chart creation from files (CSV, Excel, JSON)
- ✅ Parameter customization
- ✅ Error handling

#### test_ocr_tools.py
- ✅ Image decoding (base64, file path)
- ✅ Text extraction with Tesseract and EasyOCR
- ✅ PDF image extraction
- ✅ Document structure analysis
- ✅ **Real-world web image downloads** 🌐
- ✅ Different image formats (PNG, JPEG, BMP)
- ✅ Large images
- ✅ Error handling (corrupted images, invalid input)

#### test_file_operations_tools.py
- ✅ File saving for download
- ✅ Format conversion (CSV↔JSON, Excel↔CSV, etc.)
- ✅ Different file types
- ✅ Error handling

#### test_comprehensive_real_world.py
- ✅ End-to-end workflows (Excel → PowerPoint, Image OCR → Excel, CSV → Chart → PowerPoint)
- ✅ Performance tests (large files, many slides)
- ✅ Error recovery across all tools
- ✅ Data integrity tests

## Real-World Testing Features

### Web Image Downloads for OCR Tests

The OCR tests include real-world scenarios that download images from the web:

```python
@pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests not available")
def test_extract_text_from_web_image(self):
    """Test extraction from web-downloaded image."""
    # Downloads actual images from test URLs
    # Tests with real-world image data
```

**Test Image URLs Used:**
- `https://via.placeholder.com/400x200/000000/FFFFFF?text=TEST+IMAGE`
- `https://httpbin.org/image/png`
- `https://httpbin.org/image/jpeg`

### Large File Testing

Tests include scenarios with:
- Excel files with 1000+ rows
- PowerPoint files with 50+ slides
- Large images (2000x1000 pixels)
- Performance validation

### Error Resilience Testing

All tools are tested for:
- Invalid base64 input
- Corrupted files
- Missing dependencies
- Empty input
- Very large inputs
- Network failures (for web downloads)

## Test Execution Best Practices

### 1. Run Validation First

```bash
python3 validate_tests.py
```

### 2. Run Tests in Order of Complexity

```bash
# 1. Helper functions
pytest test_*_tools.py -k "Helper" -v

# 2. Basic functionality
pytest test_*_tools.py -k "test_" -v

# 3. Real-world scenarios
pytest test_*_tools.py -k "RealWorld" -v

# 4. Error handling
pytest test_*_tools.py -k "Error" -v

# 5. Comprehensive integration
pytest test_comprehensive_real_world.py -v
```

### 3. Check Coverage

```bash
pytest test_*.py --cov=. --cov-report=term-missing
```

### 4. Run with Verbose Output

```bash
pytest test_*.py -v -s  # -s shows print statements
```

## Expected Test Results

### Success Criteria

✅ **All tests should:**
- Complete without crashing the application
- Return proper error messages (not exceptions) on failures
- Handle missing dependencies gracefully
- Clean up temporary files
- Provide clear error messages

### Common Test Outcomes

**Passing Tests:**
- Tool executes successfully
- Returns JSON with `"status": "success"`
- Data is correctly processed

**Expected Failures (Still Valid):**
- Missing optional dependencies (skipped with reason)
- Network timeouts for web downloads (skipped)
- Invalid input handling (returns error message, doesn't crash)

## Troubleshooting

### Import Errors

If you see import errors:
1. Check that you're in the correct directory
2. Verify all dependencies are installed
3. Check Python path configuration

### Missing Dependencies

Tests will skip if dependencies are missing. Install them:

```bash
pip install openpyxl pandas python-pptx plotly streamlit pytesseract easyocr pillow opencv-python pdf2image PyPDF2 requests
```

### Network Issues

Web image download tests will skip if:
- Network is unavailable
- URLs are unreachable
- Timeout occurs

This is expected and tests will skip gracefully.

## Continuous Integration

These tests are designed for CI/CD:

- ✅ No external services required (except optional web downloads)
- ✅ Automatic cleanup of temporary files
- ✅ Graceful handling of missing dependencies
- ✅ Clear error messages
- ✅ Fast execution (most tests complete in seconds)

## Test Maintenance

### Adding New Tests

1. Follow existing test patterns
2. Use helper functions from `test_utils.py`
3. Include error handling tests
4. Add real-world scenario tests
5. Update this guide

### Updating Tests

When tools change:
1. Update corresponding test file
2. Run validation: `python3 validate_tests.py`
3. Run affected tests: `pytest test_[tool]_tools.py -v`
4. Verify all tests pass

## Performance Benchmarks

Expected performance (on modern hardware):
- Excel tools: < 1 second per operation
- PowerPoint tools: < 2 seconds per operation
- Visualization tools: < 1 second per chart
- OCR tools: 2-10 seconds (depends on image size and OCR engine)
- File operations: < 1 second per operation

Large file tests may take longer but should complete within reasonable time.

## Next Steps

After running tests:

1. **Review failures** - Check if they're expected (missing deps, network issues)
2. **Fix any real issues** - Update tools if tests reveal bugs
3. **Check coverage** - Ensure all code paths are tested
4. **Document findings** - Note any edge cases discovered

---

**Remember:** The goal is "rock solid and worldclass" - these tests should catch issues before production! 🚀

