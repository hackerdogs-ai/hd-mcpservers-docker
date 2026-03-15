# Productivity Tools (prodx) - LangChain Tools Documentation

## Overview

This directory contains LangChain tools for productivity and file operations, including Excel manipulation, PowerPoint generation, visualization, and OCR capabilities.

## Directory Structure

```
prodx/
├── __init__.py                    # Tool exports
├── README.md                      # This file
├── excel_tools.py                  # Excel file operations
├── powerpoint_tools.py             # PowerPoint generation
├── visualization_tools.py          # Streamlit Plotly chart generation
├── ocr_tools.py                    # OCR text extraction
└── file_operations_tools.py        # General file operations
```

---

## Tool List

### 1. Excel Operations Tools (`excel_tools.py`)

#### 1.1 `read_excel_structured`
**Purpose**: Read Excel files while preserving structure (cells, formulas, formatting)

**Input Schema**:
```python
{
    "file_path": str,              # Path to Excel file or base64 encoded file
    "sheet_name": Optional[str],   # Specific sheet name (default: first sheet)
    "include_formulas": bool,      # Include formulas in output (default: False)
    "include_formatting": bool     # Include formatting info (default: False)
}
```

**Output**: Structured JSON with:
- Sheet names
- Cell data with coordinates
- Formulas (if requested)
- Formatting information (if requested)

**Libraries**: `openpyxl`, `pandas`

---

#### 1.2 `modify_excel_file`
**Purpose**: Modify Excel files (add data, update cells, format cells)

**Input Schema**:
```python
{
    "file_path": str,              # Path to Excel file or base64 encoded file
    "operations": List[Dict],      # List of operations to perform
    "output_format": str           # "base64" or "file_path" (default: "base64")
}
```

**Operations Format**:
```python
[
    {
        "type": "set_cell",        # or "set_range", "add_formula", "format_cell"
        "sheet": str,              # Sheet name
        "cell": str,               # Cell reference (e.g., "A1")
        "value": Any,              # Value to set
        "formula": Optional[str]   # Formula (if type is "add_formula")
    },
    {
        "type": "format_cell",
        "sheet": str,
        "cell": str,
        "format": {
            "font": {"bold": True, "size": 12},
            "fill": {"fgColor": "FFFF00"},
            "alignment": {"horizontal": "center"}
        }
    }
]
```

**Output**: Base64-encoded Excel file or file path

**Libraries**: `openpyxl`

---

#### 1.3 `create_excel_chart`
**Purpose**: Create charts in Excel files

**Input Schema**:
```python
{
    "file_path": str,              # Path to Excel file or base64 encoded file
    "chart_config": {
        "sheet": str,              # Sheet name
        "chart_type": str,         # "bar", "line", "pie", "scatter", etc.
        "data_range": str,         # Data range (e.g., "A1:B10")
        "title": str,              # Chart title
        "position": str,           # Chart position (e.g., "E2")
        "x_axis_title": Optional[str],
        "y_axis_title": Optional[str]
    },
    "output_format": str           # "base64" or "file_path"
}
```

**Output**: Base64-encoded Excel file with chart or file path

**Libraries**: `openpyxl`

---

#### 1.4 `analyze_excel_security`
**Purpose**: Analyze Excel file for security issues (macros, external links, etc.)

**Input Schema**:
```python
{
    "file_path": str,              # Path to Excel file or base64 encoded file
    "checks": List[str]            # Optional: specific checks to perform
}
```

**Output**: Security analysis report with:
- Macro detection
- External link detection
- Hidden sheets
- Embedded objects
- Security recommendations

**Libraries**: `openpyxl`

---

### 2. PowerPoint Generation Tools (`powerpoint_tools.py`)

#### 2.1 `create_presentation_deck`
**Purpose**: Create PowerPoint presentation from structured data

**Input Schema**:
```python
{
    "title": str,                  # Presentation title
    "slides": List[Dict],          # List of slide configurations
    "template": Optional[str],     # Template name or path
    "output_format": str           # "base64" or "file_path"
}
```

**Slide Format**:
```python
{
    "layout": str,                 # "title", "content", "two_content", etc.
    "title": str,                  # Slide title
    "content": List[Dict],         # Content blocks
    "images": Optional[List[str]],  # Base64 encoded images
    "charts": Optional[List[Dict]]  # Chart configurations
}
```

**Output**: Base64-encoded PowerPoint file or file path

**Libraries**: `python-pptx`

---

#### 2.2 `add_slide_to_presentation`
**Purpose**: Add a slide to an existing presentation

**Input Schema**:
```python
{
    "file_path": str,              # Path to PowerPoint file or base64 encoded
    "slide_config": Dict,          # Slide configuration (same as above)
    "position": Optional[int],     # Position to insert (default: append)
    "output_format": str
}
```

**Output**: Base64-encoded PowerPoint file or file path

**Libraries**: `python-pptx`

---

#### 2.3 `add_chart_to_slide`
**Purpose**: Add a chart to a PowerPoint slide

**Input Schema**:
```python
{
    "file_path": str,              # Path to PowerPoint file or base64 encoded
    "slide_index": int,            # Slide number (0-based)
    "chart_config": {
        "chart_type": str,         # "bar", "line", "pie", etc.
        "data": List[Dict],        # Chart data
        "position": Dict,          # {"left": Inches(1), "top": Inches(2), ...}
        "size": Dict               # {"width": Inches(6), "height": Inches(4)}
    },
    "output_format": str
}
```

**Output**: Base64-encoded PowerPoint file or file path

**Libraries**: `python-pptx`, `matplotlib` or `plotly` (for chart generation)

---

### 3. Visualization Tools (`visualization_tools.py`)

#### 3.1 `create_streamlit_plotly_chart`
**Purpose**: Create Streamlit Plotly charts from structured input

**Input Schema**:
```python
{
    "data": Union[Dict, List, pd.DataFrame],  # Data to visualize
    "chart_type": str,                        # Chart type (see VizType enum)
    "parameters": Dict,                       # Chart-specific parameters
    "display": bool                           # Whether to display immediately (default: True)
}
```

**Supported Chart Types** (from existing `VizType` enum):
- **Trend**: `line_chart`, `area_chart`, `step_chart`, `bump_chart`, `slope_chart`
- **Comparison**: `bar_chart`, `column_chart`, `grouped_bar`, `stacked_bar`, `lollipop_chart`
- **Composition**: `pie_chart`, `donut_chart`, `waterfall_chart`, `treemap`, `sunburst_chart`
- **Distribution**: `histogram`, `box_plot`, `violin_plot`, `dot_plot`
- **Relationship**: `scatter_plot`, `bubble_chart`, `heatmap`
- **Flow**: `sankey_diagram`, `alluvial_diagram`
- **Geospatial**: `choropleth_map`, `symbol_map`, `density_map`
- **Performance**: `gauge_chart`, `bullet_chart`
- **Network**: `network_graph`, `chord_diagram`

**Parameters Example**:
```python
{
    "x": "timestamp",              # X-axis column
    "y": "value",                  # Y-axis column
    "color": Optional[str],         # Color grouping column
    "title": str,                  # Chart title
    "x_label": Optional[str],       # X-axis label
    "y_label": Optional[str],      # Y-axis label
    "width": Optional[int],         # Chart width
    "height": Optional[int]         # Chart height
}
```

**Output**: 
- If `display=True`: Chart is displayed in Streamlit, returns success message
- If `display=False`: Returns Plotly figure object (JSON-serializable)

**Libraries**: `plotly`, `plotly.express`, `pandas`, `streamlit`

**Note**: This tool leverages existing `PlotlyRenderer` class from `streamlit_app/modules/viz_intelligence/viz_renderer/plotly_renderer.py`

---

#### 3.2 `create_chart_from_file`
**Purpose**: Create chart from file data (Excel, CSV, JSON, etc.)

**Input Schema**:
```python
{
    "file_path": str,              # Path to file or base64 encoded file
    "file_type": str,              # "excel", "csv", "json"
    "chart_type": str,             # Chart type
    "data_config": Dict,           # Data extraction configuration
    "parameters": Dict,           # Chart parameters
    "display": bool                # Display immediately
}
```

**Output**: Same as `create_streamlit_plotly_chart`

**Libraries**: `pandas`, `openpyxl`, `plotly`

---

### 4. OCR Tools (`ocr_tools.py`)

#### 4.1 `extract_text_from_image`
**Purpose**: Extract text from images using OCR

**Input Schema**:
```python
{
    "image_data": str,             # Base64-encoded image or file path
    "language": Optional[str],     # Language code (default: "eng")
    "ocr_engine": str,             # "tesseract", "easyocr", or "auto" (default: "auto")
    "preprocess": bool,            # Apply image preprocessing (default: True)
    "output_format": str           # "text" or "structured" (default: "text")
}
```

**Output**:
- If `output_format="text"`: Plain text string
- If `output_format="structured"`: JSON with:
  - Extracted text
  - Bounding boxes
  - Confidence scores
  - Line/word segmentation

**Libraries**: `pytesseract`, `easyocr`, `PIL`, `opencv-python`

**Note**: Check if LangChain has existing OCR tools - if yes, integrate them

---

#### 4.2 `extract_text_from_pdf_images`
**Purpose**: Extract text from images embedded in PDF files

**Input Schema**:
```python
{
    "file_path": str,              # Path to PDF file or base64 encoded
    "pages": Optional[List[int]],  # Specific pages (default: all pages)
    "ocr_engine": str,             # "tesseract", "easyocr", or "auto"
    "output_format": str           # "text" or "structured"
}
```

**Output**: Same as `extract_text_from_image`

**Libraries**: `PyPDF2`, `pdf2image`, `pytesseract`, `easyocr`

---

#### 4.3 `analyze_document_structure`
**Purpose**: Analyze document structure and extract text with layout information

**Input Schema**:
```python
{
    "file_path": str,              # Path to document or base64 encoded
    "file_type": str,              # "pdf", "image", "docx", "pptx"
    "include_images": bool,       # Extract text from images (default: True)
    "output_format": str           # "text", "structured", or "markdown"
}
```

**Output**: Structured document with:
- Text content
- Layout information (headers, paragraphs, tables)
- Images with OCR text (if `include_images=True`)
- Metadata (page numbers, sections, etc.)

**Libraries**: `unstructured`, `pytesseract`, `easyocr`, `PyPDF2`, `python-docx`

---

### 5. File Operations Tools (`file_operations_tools.py`)

#### 5.1 `save_file_for_download`
**Purpose**: Save generated/modified files for download in Streamlit

**Input Schema**:
```python
{
    "file_data": str,              # Base64-encoded file data
    "file_name": str,              # File name
    "mime_type": str,              # MIME type (e.g., "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    "storage_location": str        # "session_state" or "temp_file" (default: "session_state")
}
```

**Output**: File identifier for download button

**Integration**: Works with `st.download_button()` in Chat.py

---

#### 5.2 `convert_file_format`
**Purpose**: Convert files between formats

**Input Schema**:
```python
{
    "file_path": str,              # Path to file or base64 encoded
    "source_format": str,          # Source format
    "target_format": str,          # Target format
    "options": Optional[Dict]       # Conversion options
}
```

**Supported Conversions**:
- Excel ↔ CSV
- PDF → Images
- Images → PDF
- PowerPoint → Images
- And more...

**Output**: Base64-encoded converted file

---

## Implementation Status

| Tool | Status | Priority | Notes |
|------|--------|----------|-------|
| `read_excel_structured` | ⏳ Pending | High | Core Excel functionality |
| `modify_excel_file` | ⏳ Pending | High | Core Excel functionality |
| `create_excel_chart` | ⏳ Pending | High | Chart generation in Excel |
| `analyze_excel_security` | ⏳ Pending | Medium | Security analysis |
| `create_presentation_deck` | ⏳ Pending | High | PowerPoint generation |
| `add_slide_to_presentation` | ⏳ Pending | Medium | PowerPoint operations |
| `add_chart_to_slide` | ⏳ Pending | Medium | PowerPoint charts |
| `create_streamlit_plotly_chart` | ⏳ Pending | High | Visualization (leverage existing code) |
| `create_chart_from_file` | ⏳ Pending | Medium | File-based visualization |
| `extract_text_from_image` | ⏳ Pending | High | OCR core functionality |
| `extract_text_from_pdf_images` | ⏳ Pending | High | PDF OCR |
| `analyze_document_structure` | ⏳ Pending | Medium | Advanced document analysis |
| `save_file_for_download` | ⏳ Pending | High | File download mechanism |
| `convert_file_format` | ⏳ Pending | Low | Format conversion |

---

## Dependencies

### Required Python Packages:
```txt
# Excel Operations
openpyxl>=3.1.0
pandas>=2.0.0
xlsxwriter>=3.1.0  # Alternative Excel library

# PowerPoint Operations
python-pptx>=0.6.21

# Visualization
plotly>=5.17.0
plotly.express>=5.17.0
pandas>=2.0.0

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

## Existing Code to Leverage

### Visualization Library
**Location**: `streamlit_app/modules/viz_intelligence/viz_renderer/plotly_renderer.py`

**Salvageable Components**:
- ✅ `PlotlyRenderer` class structure
- ✅ Chart type definitions (`VizType` enum)
- ✅ Data conversion methods (`_to_dataframe`)
- ✅ Chart rendering methods (`_render_line_chart`, `_render_bar_chart`, etc.)
- ✅ Validation logic (`_has_valid_render_data`)

**Issues to Fix**:
- ⚠️ Check why visualization library doesn't work
- ⚠️ Fix any data validation issues
- ⚠️ Ensure Streamlit integration works correctly

### OCR Usage
**Location**: `tm_samples_svg.py` (lines 869-894)

**Existing OCR Code**:
```python
# Uses both EasyOCR and Tesseract
if self.ocr_reader:
    results = self.ocr_reader.readtext(np.array(image))
    text_content = ' '.join([result[1] for result in results]).lower()
else:
    text_content = pytesseract.image_to_string(image).lower()
```

**Can Leverage**:
- ✅ EasyOCR integration pattern
- ✅ Tesseract fallback pattern
- ✅ Image preprocessing logic

---

## LangChain OCR Tools Research

### Research Results:
- ❌ **No dedicated LangChain OCR tool found**
- ✅ **Can use `unstructured` library** (has OCR capabilities)
- ✅ **Can create custom LangChain tool** using `pytesseract` or `easyocr`

### Recommendation:
Create custom OCR tools using:
- `pytesseract` (Tesseract OCR) - Fast, reliable
- `easyocr` (EasyOCR) - Better accuracy, supports 80+ languages
- `unstructured` - Document parsing with OCR support

---

## Tool Registration

### Integration with Existing System

Tools will be registered in the `g_tools` table with:
- `tool_type`: "langchain"
- `tool_class`: Full class path (e.g., `shared.modules.tools.prodx.excel_tools.ModifyExcelTool`)
- `tool_module`: Module name (e.g., `excel_tools`)
- `integration_methods`: `["langchain", "direct"]`
- `config_metadata`: Tool-specific configuration

### Example Tool Registration:
```json
{
  "tool_type": "langchain",
  "tool_class": "shared.modules.tools.prodx.excel_tools.ModifyExcelTool",
  "tool_module": "excel_tools",
  "parameters": {
    "max_file_size_mb": 50,
    "allowed_formats": ["xlsx", "xls"]
  }
}
```

---

## Next Steps

1. ✅ Create `prodx` directory structure
2. ⏳ Implement Excel tools (`excel_tools.py`)
3. ⏳ Implement PowerPoint tools (`powerpoint_tools.py`)
4. ⏳ Implement visualization tools (`visualization_tools.py`) - leverage existing code
5. ⏳ Implement OCR tools (`ocr_tools.py`)
6. ⏳ Implement file operations tools (`file_operations_tools.py`)
7. ⏳ Create `__init__.py` with tool exports
8. ⏳ Test tools in Chat.py
9. ⏳ Register tools in database
10. ⏳ Document usage examples

---

## Usage Examples

### Example 1: Create Excel Chart
```python
# User uploads Excel file and asks: "Create a bar chart of sales by region"

# Tool execution:
result = create_excel_chart(
    file_path=uploaded_file,
    chart_config={
        "sheet": "Sales",
        "chart_type": "bar",
        "data_range": "A1:B10",
        "title": "Sales by Region"
    }
)

# File is saved and download button appears
```

### Example 2: Generate Presentation
```python
# User asks: "Create a security analysis presentation based on this data"

# Tool execution:
result = create_presentation_deck(
    title="Security Analysis Report",
    slides=[
        {"layout": "title", "title": "Security Analysis"},
        {"layout": "content", "title": "Findings", "content": [...]}
    ]
)
```

### Example 3: OCR from Image
```python
# User uploads image and asks: "Extract text from this image"

# Tool execution:
text = extract_text_from_image(
    image_data=uploaded_image,
    ocr_engine="auto",
    output_format="text"
)
```

---

## Notes

- All tools should handle both file paths and base64-encoded files
- Tools should return base64-encoded files for download in Streamlit
- Error handling and logging should use `hd_logging`
- Tools should be async-compatible (implement `_arun` method)
- File size limits should be configurable
- Security: Validate file types and sanitize inputs

