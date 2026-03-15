"""
Productivity Tools (prodx) - LangChain Tools

This module contains LangChain tools for productivity and file operations:
- Excel file manipulation and chart creation
- PowerPoint presentation generation
- Streamlit Plotly visualization
- OCR text extraction
- File operations and format conversion
"""

from .excel_tools import (
    ReadExcelStructuredTool,
    ModifyExcelTool,
    CreateExcelChartTool,
    AnalyzeExcelSecurityTool
)
from .powerpoint_tools import (
    CreatePresentationTool,
    AddSlideTool,
    AddChartToSlideTool
)
from .visualization_tools import (
    CreatePlotlyChartTool,
    CreateChartFromFileTool
)
from .ocr_tools import (
    ExtractTextFromImageTool,
    ExtractTextFromPDFImagesTool,
    AnalyzeDocumentStructureTool
)
from .file_operations_tools import (
    SaveFileForDownloadTool,
    ConvertFileFormatTool
)

__all__ = [
    # Excel tools
    "ReadExcelStructuredTool",
    "ModifyExcelTool",
    "CreateExcelChartTool",
    "AnalyzeExcelSecurityTool",
    # PowerPoint tools
    "CreatePresentationTool",
    "AddSlideTool",
    "AddChartToSlideTool",
    # Visualization tools
    "CreatePlotlyChartTool",
    "CreateChartFromFileTool",
    # OCR tools
    "ExtractTextFromImageTool",
    "ExtractTextFromPDFImagesTool",
    "AnalyzeDocumentStructureTool",
    # File operations
    "SaveFileForDownloadTool",
    "ConvertFileFormatTool",
]

__version__ = "0.1.0"

