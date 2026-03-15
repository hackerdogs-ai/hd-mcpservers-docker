# Required Packages for Productivity Tools (prodx)

This document lists all Python packages required for the productivity tools in the `prodx` directory.

## Installation

Install all required packages with:

```bash
pip install -r streamlit_app/modules/tools/prodx/requirements.txt
```

Or install individually as needed for specific tools.

---

## Package List by Category

### Excel Operations (4 tools)
**Required for:** `ReadExcelStructuredTool`, `ModifyExcelTool`, `CreateExcelChartTool`, `AnalyzeExcelSecurityTool`

```bash
pip install openpyxl>=3.1.0
pip install pandas>=2.0.0
```

- **openpyxl** (>=3.1.0): Excel file manipulation (.xlsx files)
- **pandas** (>=2.0.0): Data operations and Excel reading

**Optional:**
- **xlsxwriter** (>=3.1.0): Alternative Excel library for advanced features

---

### PowerPoint Operations (3 tools)
**Required for:** `CreatePresentationTool`, `AddSlideTool`, `AddChartToSlideTool`

```bash
pip install python-pptx>=0.6.21
```

- **python-pptx** (>=0.6.21): PowerPoint file generation and manipulation

**Note:** Chart embedding in PowerPoint requires matplotlib/plotly (see Visualization section).

---

### Visualization (2 tools)
**Required for:** `CreatePlotlyChartTool`, `CreateChartFromFileTool`

```bash
pip install plotly>=5.17.0
pip install pandas>=2.0.0
```

- **plotly** (>=5.17.0): Interactive chart creation
- **pandas** (>=2.0.0): Data manipulation for charts

**Note:** These tools leverage the existing `PlotlyRenderer` from `viz_intelligence` module.

---

### OCR (3 tools)
**Required for:** `ExtractTextFromImageTool`, `ExtractTextFromPDFImagesTool`, `AnalyzeDocumentStructureTool`

#### Core OCR Libraries
```bash
pip install pytesseract>=0.3.10
pip install easyocr>=1.7.0
pip install Pillow>=10.0.0
```

- **pytesseract** (>=0.3.10): Tesseract OCR wrapper
- **easyocr** (>=1.7.0): EasyOCR library (80+ languages, better accuracy)
- **Pillow** (>=10.0.0): Image processing (PIL)

#### Image Preprocessing
```bash
pip install opencv-python>=4.8.0
```

- **opencv-python** (>=4.8.0): Image preprocessing for better OCR results

#### PDF Processing
```bash
pip install pdf2image>=1.16.0
pip install PyPDF2>=3.0.0
```

- **pdf2image** (>=1.16.0): PDF to image conversion for OCR
- **PyPDF2** (>=3.0.0): PDF file reading and manipulation

#### System Dependencies (Not installable via pip)

**Tesseract OCR Binary:**
- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

**Poppler (for pdf2image):**
- **macOS**: `brew install poppler`
- **Ubuntu/Debian**: `sudo apt-get install poppler-utils`
- **Windows**: Download from https://github.com/oschwartz10612/poppler-windows/releases

---

### Document Processing
**Required for:** `AnalyzeDocumentStructureTool` (DOCX support)

```bash
pip install python-docx>=1.1.0
```

- **python-docx** (>=1.1.0): Word document processing

---

### File Operations (2 tools)
**Required for:** `SaveFileForDownloadTool`, `ConvertFileFormatTool`

These tools use libraries from other categories:
- **pandas**: For Excel/CSV/JSON conversions
- **openpyxl**: For Excel operations
- **pdf2image**: For PDF to image conversion
- **Pillow**: For image operations

No additional packages required beyond those listed above.

---

### LangChain (Should already be installed)
**Required for:** All tools (base framework)

```bash
pip install langchain>=0.1.0
pip install langchain-core>=0.1.0
```

- **langchain** (>=0.1.0): LangChain framework
- **langchain-core** (>=0.1.0): LangChain core components

---

## Complete Installation Command

Install all required packages at once:

```bash
pip install \
  openpyxl>=3.1.0 \
  pandas>=2.0.0 \
  python-pptx>=0.6.21 \
  plotly>=5.17.0 \
  pytesseract>=0.3.10 \
  easyocr>=1.7.0 \
  Pillow>=10.0.0 \
  opencv-python>=4.8.0 \
  pdf2image>=1.16.0 \
  PyPDF2>=3.0.0 \
  python-docx>=1.1.0 \
  langchain>=0.1.0 \
  langchain-core>=0.1.0
```

---

## System Dependencies Summary

### Required System Binaries

1. **Tesseract OCR** (for pytesseract)
   - Required for Tesseract OCR engine
   - Install using system package manager

2. **Poppler** (for pdf2image)
   - Required for PDF to image conversion
   - Install using system package manager

### Installation by OS

**macOS:**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows:**
- Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases

---

## Verification

After installation, verify packages are available:

```python
# Test imports
import openpyxl
import pandas as pd
from pptx import Presentation
import plotly.express as px
import pytesseract
import easyocr
from PIL import Image
import cv2
from pdf2image import convert_from_bytes
import PyPDF2
import docx
```

If all imports succeed, packages are correctly installed.

---

## Notes

- **EasyOCR** downloads models on first use (may take time and require internet)
- **Tesseract** requires the binary to be in PATH or configured via `pytesseract.pytesseract.tesseract_cmd`
- **pdf2image** requires poppler to be installed and accessible
- Some tools gracefully degrade if optional libraries are missing (check tool documentation)
- All tools include error handling for missing dependencies

---

## Minimum Requirements

For basic functionality, you need at least:
- **pandas** (for data operations)
- **openpyxl** (for Excel tools)
- **python-pptx** (for PowerPoint tools)
- **plotly** (for visualization tools)
- **Pillow** (for image/OCR tools)
- **langchain-core** (for tool framework)

OCR tools require additional packages and system dependencies as listed above.

