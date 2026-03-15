# Productivity Tools (prodx) - Complete Tool List

## Overview

This document lists all tools to be implemented in the `prodx` directory for productivity and file operations.

---

## Tool Categories

### 1. Excel Operations (4 tools)
### 2. PowerPoint Operations (3 tools)
### 3. Visualization Tools (2 tools)
### 4. OCR Tools (3 tools)
### 5. File Operations (2 tools)

**Total: 14 tools**

---

## Detailed Tool List

### Category 1: Excel Operations

#### Tool 1.1: `read_excel_structured`
- **File**: `excel_tools.py`
- **Class**: `ReadExcelStructuredTool`
- **Purpose**: Read Excel files with structure preservation
- **Input**: File path/base64, sheet name, include formulas/formatting flags
- **Output**: Structured JSON with cells, formulas, formatting
- **Libraries**: `openpyxl`, `pandas`
- **Priority**: High
- **Status**: ⏳ Pending

#### Tool 1.2: `modify_excel_file`
- **File**: `excel_tools.py`
- **Class**: `ModifyExcelTool`
- **Purpose**: Modify Excel files (cells, formulas, formatting)
- **Input**: File path/base64, list of operations
- **Output**: Base64-encoded modified Excel file
- **Libraries**: `openpyxl`
- **Priority**: High
- **Status**: ⏳ Pending

#### Tool 1.3: `create_excel_chart`
- **File**: `excel_tools.py`
- **Class**: `CreateExcelChartTool`
- **Purpose**: Create charts in Excel files
- **Input**: File path/base64, chart configuration
- **Output**: Base64-encoded Excel file with chart
- **Libraries**: `openpyxl`
- **Priority**: High
- **Status**: ⏳ Pending

#### Tool 1.4: `analyze_excel_security`
- **File**: `excel_tools.py`
- **Class**: `AnalyzeExcelSecurityTool`
- **Purpose**: Security analysis of Excel files
- **Input**: File path/base64, optional checks list
- **Output**: Security analysis report
- **Libraries**: `openpyxl`
- **Priority**: Medium
- **Status**: ⏳ Pending

---

### Category 2: PowerPoint Operations

#### Tool 2.1: `create_presentation_deck`
- **File**: `powerpoint_tools.py`
- **Class**: `CreatePresentationTool`
- **Purpose**: Create PowerPoint presentations from structured data
- **Input**: Title, slides list, optional template
- **Output**: Base64-encoded PowerPoint file
- **Libraries**: `python-pptx`
- **Priority**: High
- **Status**: ⏳ Pending

#### Tool 2.2: `add_slide_to_presentation`
- **File**: `powerpoint_tools.py`
- **Class**: `AddSlideTool`
- **Purpose**: Add slide to existing presentation
- **Input**: File path/base64, slide configuration, position
- **Output**: Base64-encoded PowerPoint file
- **Libraries**: `python-pptx`
- **Priority**: Medium
- **Status**: ⏳ Pending

#### Tool 2.3: `add_chart_to_slide`
- **File**: `powerpoint_tools.py`
- **Class**: `AddChartToSlideTool`
- **Purpose**: Add chart to PowerPoint slide
- **Input**: File path/base64, slide index, chart configuration
- **Output**: Base64-encoded PowerPoint file
- **Libraries**: `python-pptx`, `matplotlib`/`plotly`
- **Priority**: Medium
- **Status**: ⏳ Pending

---

### Category 3: Visualization Tools

#### Tool 3.1: `create_streamlit_plotly_chart`
- **File**: `visualization_tools.py`
- **Class**: `CreatePlotlyChartTool`
- **Purpose**: Create Streamlit Plotly charts from structured input
- **Input**: Data (dict/list/DataFrame), chart type, parameters
- **Output**: Displays chart in Streamlit or returns figure object
- **Libraries**: `plotly`, `plotly.express`, `pandas`, `streamlit`
- **Priority**: High
- **Status**: ⏳ Pending
- **Note**: Leverage existing `PlotlyRenderer` from `streamlit_app/modules/viz_intelligence/viz_renderer/plotly_renderer.py`

#### Tool 3.2: `create_chart_from_file`
- **File**: `visualization_tools.py`
- **Class**: `CreateChartFromFileTool`
- **Purpose**: Create chart from file data (Excel, CSV, JSON)
- **Input**: File path/base64, file type, chart type, data config, parameters
- **Output**: Displays chart in Streamlit or returns figure object
- **Libraries**: `pandas`, `openpyxl`, `plotly`
- **Priority**: Medium
- **Status**: ⏳ Pending

---

### Category 4: OCR Tools

#### Tool 4.1: `extract_text_from_image`
- **File**: `ocr_tools.py`
- **Class**: `ExtractTextFromImageTool`
- **Purpose**: Extract text from images using OCR
- **Input**: Image data (base64/path), language, OCR engine, preprocessing flag, output format
- **Output**: Plain text or structured JSON with bounding boxes
- **Libraries**: `pytesseract`, `easyocr`, `PIL`, `opencv-python`
- **Priority**: High
- **Status**: ⏳ Pending
- **Note**: Check if LangChain has existing OCR tools (research shows: ❌ No dedicated tool found)

#### Tool 4.2: `extract_text_from_pdf_images`
- **File**: `ocr_tools.py`
- **Class**: `ExtractTextFromPDFImagesTool`
- **Purpose**: Extract text from images embedded in PDF files
- **Input**: PDF file path/base64, pages list, OCR engine, output format
- **Output**: Plain text or structured JSON
- **Libraries**: `PyPDF2`, `pdf2image`, `pytesseract`, `easyocr`
- **Priority**: High
- **Status**: ⏳ Pending

#### Tool 4.3: `analyze_document_structure`
- **File**: `ocr_tools.py`
- **Class**: `AnalyzeDocumentStructureTool`
- **Purpose**: Analyze document structure and extract text with layout
- **Input**: File path/base64, file type, include images flag, output format
- **Output**: Structured document with text, layout, images, metadata
- **Libraries**: `unstructured`, `pytesseract`, `easyocr`, `PyPDF2`, `python-docx`
- **Priority**: Medium
- **Status**: ⏳ Pending

---

### Category 5: File Operations

#### Tool 5.1: `save_file_for_download`
- **File**: `file_operations_tools.py`
- **Class**: `SaveFileForDownloadTool`
- **Purpose**: Save generated/modified files for download in Streamlit
- **Input**: File data (base64), file name, MIME type, storage location
- **Output**: File identifier for download button
- **Libraries**: `streamlit` (for `st.download_button`)
- **Priority**: High
- **Status**: ⏳ Pending
- **Integration**: Works with `st.download_button()` in Chat.py

#### Tool 5.2: `convert_file_format`
- **File**: `file_operations_tools.py`
- **Class**: `ConvertFileFormatTool`
- **Purpose**: Convert files between formats
- **Input**: File path/base64, source format, target format, options
- **Output**: Base64-encoded converted file
- **Libraries**: Various (format-specific)
- **Priority**: Low
- **Status**: ⏳ Pending

---

## Existing Code to Leverage

### Visualization Library
**Location**: `streamlit_app/modules/viz_intelligence/viz_renderer/plotly_renderer.py`

**Salvageable Components**:
- ✅ `PlotlyRenderer` class (lines 17-663)
- ✅ `VizType` enum (from `interfaces.py`) - 30+ chart types
- ✅ `_to_dataframe()` method (lines 107-278) - Handles nested structures, columnar data, JSON
- ✅ `_has_valid_render_data()` method (lines 280-310) - Data validation
- ✅ Chart rendering methods:
  - `_render_line_chart()` (line ~61)
  - `_render_bar_chart()` (line ~70)
  - `_render_pie_chart()` (line ~77)
  - `_render_scatter_plot()` (line ~84)
  - `_render_heatmap()` (line ~86)
  - And more...

**Issues to Investigate**:
- ⚠️ Why doesn't visualization library work?
- ⚠️ Check data validation logic
- ⚠️ Verify Streamlit integration

**Recommendation**: Extract core rendering logic into reusable functions for the LangChain tool.

### OCR Code
**Location**: `tm_samples_svg.py` (lines 869-894)

**Existing Implementation**:
```python
def _validate_image_with_ocr(self, image: Image.Image, filename: str) -> bool:
    """Validate image using OCR to detect architecture-related text."""
    try:
        if self.ocr_reader:
            # Use EasyOCR
            results = self.ocr_reader.readtext(np.array(image))
            text_content = ' '.join([result[1] for result in results]).lower()
        else:
            # Fallback to Tesseract
            text_content = pytesseract.image_to_string(image).lower()
        # ... keyword matching logic
    except Exception as e:
        # Error handling
```

**Can Leverage**:
- ✅ EasyOCR integration pattern
- ✅ Tesseract fallback pattern
- ✅ Image preprocessing (if exists)

---

## LangChain OCR Tools Research

### Research Results:
- ❌ **No dedicated LangChain OCR tool found** in official documentation
- ✅ **`unstructured` library** has OCR capabilities and can be used
- ✅ **Custom tool creation** is the recommended approach

### Available OCR Libraries:
1. **pytesseract** (Tesseract OCR)
   - Fast, reliable
   - Supports 100+ languages
   - Good for printed text

2. **easyocr**
   - Better accuracy for complex images
   - Supports 80+ languages
   - Better for handwritten text and complex layouts

3. **unstructured**
   - Document parsing with OCR
   - Handles multiple file formats
   - Structured output

**Recommendation**: Create custom OCR tools using `pytesseract` and `easyocr` with automatic engine selection.

---

## Implementation Priority

### Phase 1: Core Functionality (High Priority)
1. ✅ `read_excel_structured` - Excel reading
2. ✅ `modify_excel_file` - Excel modification
3. ✅ `create_excel_chart` - Excel charts
4. ✅ `create_presentation_deck` - PowerPoint generation
5. ✅ `create_streamlit_plotly_chart` - Visualization (leverage existing code)
6. ✅ `extract_text_from_image` - OCR core
7. ✅ `save_file_for_download` - File download mechanism

### Phase 2: Enhanced Features (Medium Priority)
8. ⏳ `analyze_excel_security` - Security analysis
9. ⏳ `add_slide_to_presentation` - PowerPoint operations
10. ⏳ `add_chart_to_slide` - PowerPoint charts
11. ⏳ `create_chart_from_file` - File-based visualization
12. ⏳ `extract_text_from_pdf_images` - PDF OCR
13. ⏳ `analyze_document_structure` - Advanced document analysis

### Phase 3: Additional Features (Low Priority)
14. ⏳ `convert_file_format` - Format conversion

---

## Tool Registration Schema

Each tool will be registered in the `g_tools` table with the following structure:

```json
{
  "tool_id": "ULID",
  "tool_name": "Tool Display Name",
  "description": "Tool description for LLM",
  "tool_type": "langchain",
  "tool_class": "shared.modules.tools.prodx.excel_tools.ModifyExcelTool",
  "tool_module": "excel_tools",
  "tool_function_name": "modify_excel_file",
  "integration_methods": ["langchain", "direct"],
  "config_metadata": {
    "tool_type": "langchain",
    "parameters": {
      "max_file_size_mb": 50,
      "allowed_formats": ["xlsx", "xls"]
    },
    "dependencies": ["openpyxl", "pandas"],
    "args_schema": {
      "file_path": {"type": "string", "required": true},
      "operations": {"type": "array", "required": true}
    }
  },
  "is_chat_enabled": true,
  "is_mcp_server": false
}
```

---

## Dependencies Summary

### Required Packages:
```txt
# Excel Operations
openpyxl>=3.1.0
pandas>=2.0.0
xlsxwriter>=3.1.0

# PowerPoint Operations
python-pptx>=0.6.21

# Visualization
plotly>=5.17.0
plotly.express>=5.17.0

# OCR
pytesseract>=0.3.10
easyocr>=1.7.0
Pillow>=10.0.0
opencv-python>=4.8.0
pdf2image>=1.16.0

# Document Processing
unstructured>=0.10.0
PyPDF2>=3.0.0
python-docx>=1.1.0

# LangChain
langchain>=0.1.0
langchain-core>=0.1.0
```

---

## Next Steps

1. ✅ Create `prodx` directory structure
2. ✅ Document tool list (this file)
3. ⏳ Create `__init__.py` with tool exports
4. ⏳ Implement Phase 1 tools (7 tools)
5. ⏳ Test tools in Chat.py
6. ⏳ Register tools in database
7. ⏳ Implement Phase 2 tools (6 tools)
8. ⏳ Implement Phase 3 tools (1 tool)
9. ⏳ Create usage examples and documentation

---

## Notes

- All tools should follow the pattern from `browserless_tool.py`
- Use `BaseTool` from `langchain_core.tools`
- Implement both `_run()` and `_arun()` methods
- Use `hd_logging` for logging
- Handle both file paths and base64-encoded files
- Return base64-encoded files for Streamlit download
- Validate inputs and handle errors gracefully
- Support async execution for better performance

