"""
OCR Tools
---------
LangChain tools for extracting text from images and documents using OCR.
"""

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, List, Optional, Any
import sys
import os
# Add project root to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))
try:
    from shared.logger import setup_logger
except ImportError:
    # Fallback for testing environments
    import logging
    def setup_logger(name, log_file_path=None, **kwargs):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
import base64
import io
import json
import numpy as np

logger = setup_logger(__name__, log_file_path="logs/ocr_tools.log")

# Try to import required libraries
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available. OCR tools will not work.")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available. Tesseract OCR will not work.")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("easyocr not available. EasyOCR will not work.")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("opencv-python not available. Image preprocessing may be limited.")

try:
    import PyPDF2
    from pdf2image import convert_from_bytes
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2/pdf2image not available. PDF OCR will not work.")


def _decode_image_input(image_input: str) -> Image.Image:
    """Decode image input which can be either a base64 string or file path."""
    try:
        # Try to decode as base64 first
        image_bytes = base64.b64decode(image_input)
        image = Image.open(io.BytesIO(image_bytes))
        return image
    except Exception:
        # If that fails, treat as file path
        try:
            return Image.open(image_input)
        except Exception as e:
            raise ValueError(f"Invalid image input: {e}")


def _preprocess_image(image: Image.Image) -> Image.Image:
    """Preprocess image for better OCR results."""
    if not CV2_AVAILABLE:
        return image
    
    try:
        # Convert PIL to OpenCV format
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_cv = img_array
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY) if len(img_cv.shape) == 3 else img_cv
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL
        return Image.fromarray(thresh)
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}, using original image")
        return image


# --- OCR Tools ---

class ExtractTextFromImageInput(BaseModel):
    """Input schema for ExtractTextFromImageTool."""
    image_data: str = Field(..., description="Base64-encoded image or file path")
    language: Optional[str] = Field("eng", description="Language code for OCR (default: 'eng')")
    ocr_engine: str = Field("auto", description="OCR engine: 'tesseract', 'easyocr', or 'auto' (default: 'auto')")
    preprocess: bool = Field(True, description="Apply image preprocessing for better results (default: True)")
    output_format: str = Field("text", description="Output format: 'text' or 'structured' (default: 'text')")


class ExtractTextFromImageTool(BaseTool):
    """
    Extract text from images using OCR (Optical Character Recognition).
    
    This tool extracts text from images using advanced OCR technology. It supports two OCR engines
    (Tesseract OCR and EasyOCR) with automatic selection, image preprocessing for better accuracy,
    and multiple output formats. The tool can handle various image types including screenshots,
    scanned documents, photos, and image-based content.
    
    **When to use this tool:**
    - Extracting text from screenshots
    - Reading text from images and photos
    - Processing scanned documents
    - Extracting data from image-based documents
    - Reading text from diagrams or charts
    - Converting image text to searchable/editable format
    - Extracting information from image uploads
    
    **When NOT to use this tool:**
    - For PDF files with text layers (use PDF text extraction)
    - When text is already available in structured format
    - For very low-quality images (may not work well)
    - When you need perfect accuracy (OCR has limitations)
    - For handwritten text (EasyOCR works better but not perfect)
    
    **Input requirements:**
    - Must provide a valid image file (PNG, JPEG, etc.) as base64 or file path
    - Image should be clear and readable for best results
    - Language code is optional (default: "eng" for English)
    - OCR engine selection is automatic (EasyOCR preferred, Tesseract fallback)
    
    **Output:**
    - If output_format="text": Returns plain text string with extracted text
    - If output_format="structured": Returns JSON with:
      - Full text string
      - Word-level data with bounding boxes and confidence scores
      - OCR engine used
      - Language detected
    - Returns error message if OCR fails
    
    **OCR Engines:**
    - **Tesseract OCR** (pytesseract):
      - Fast and reliable
      - Supports 100+ languages
      - Good for printed text
      - Requires Tesseract binary installation
    - **EasyOCR**:
      - Better accuracy for many use cases
      - Supports 80+ languages
      - Better for handwritten text
      - Works out of the box (no binary required)
      - Slower but more accurate
    
    **Image Preprocessing:**
    - Converts to grayscale for better OCR accuracy
    - Applies thresholding to enhance text contrast
    - Improves results for low-quality images
    - Can be disabled if image is already optimized
    
    **Limitations:**
    - OCR accuracy depends on image quality
    - Complex layouts may not be preserved
    - Handwritten text accuracy varies
    - Very small or blurry text may not be recognized
    - Some fonts may not be recognized well
    
    **Example use cases:**
    1. "Extract all text from this screenshot"
    2. "Read the text from this scanned document image"
    3. "Extract text from this image with bounding boxes and confidence scores"
    4. "Read the text from this diagram or chart image"
    
    **Configuration:**
    Requires pytesseract or easyocr library. Tesseract requires the Tesseract OCR binary to be
    installed on the system. EasyOCR works out of the box but downloads models on first use.
    Image preprocessing uses OpenCV if available, otherwise uses basic PIL operations.
    """
    name: str = "extract_text_from_image"
    description: str = (
        "Extract text from images using OCR (Optical Character Recognition). "
        "Supports Tesseract OCR and EasyOCR engines with automatic selection. "
        "Can return plain text or structured output with bounding boxes and confidence scores. "
        "IMPORTANT: Image can be base64-encoded string or file path. Image preprocessing improves accuracy. "
        "Best for: extracting text from screenshots, scanned documents, image-based content. "
        "NOT suitable for: PDF files with text layers, very low-quality images, or perfect accuracy requirements."
    )
    args_schema: Type[BaseModel] = ExtractTextFromImageInput

    def _run(
        self,
        image_data: str,
        language: str = "eng",
        ocr_engine: str = "auto",
        preprocess: bool = True,
        output_format: str = "text"
    ) -> str:
        """
        Extract text from image using OCR.
        
        This method performs the OCR operation:
        1. Decodes image input (base64 or file path)
        2. Applies image preprocessing if requested (grayscale, thresholding)
        3. Selects OCR engine (auto-selects EasyOCR if available, else Tesseract)
        4. Performs OCR on the image
        5. Formats output as text or structured JSON
        6. Returns extracted text or structured data
        
        Args:
            image_data: Base64-encoded image or file path.
                       Example: base64 string from file upload or "image.png"
            language: Language code for OCR (default: "eng" for English).
                     Examples: "eng", "spa", "fra", "deu", "jpn"
                     See Tesseract/EasyOCR documentation for full language list
            ocr_engine: OCR engine to use:
                       - "auto": Automatically select (EasyOCR preferred, Tesseract fallback)
                       - "tesseract": Use Tesseract OCR
                       - "easyocr": Use EasyOCR
            preprocess: If True, applies image preprocessing (grayscale, thresholding) for better results.
                       Default: True. Set to False if image is already optimized.
            output_format: Output format:
                          - "text": Plain text string (default)
                          - "structured": JSON with text, bounding boxes, confidence scores
        
        Returns:
            str: If output_format="text": Plain text string with extracted text.
                 If output_format="structured": JSON string with:
                 - text: Full extracted text
                 - words: List of word objects with text, confidence, bbox
                 - engine: OCR engine used
                 - language: Language code used
                 Returns error message string if OCR fails.
        
        Raises:
            No exceptions are raised - all errors are caught and returned as error message strings.
        """
        if not PIL_AVAILABLE:
            return "Error: PIL/Pillow library is not installed. Please install it with: pip install Pillow"
        
        if not TESSERACT_AVAILABLE and not EASYOCR_AVAILABLE:
            return "Error: No OCR engine available. Please install pytesseract or easyocr."
        
        try:
            logger.info(f"Extracting text from image using {ocr_engine} OCR engine")
            
            # Decode image
            image = _decode_image_input(image_data)
            
            # Preprocess if requested
            if preprocess:
                image = _preprocess_image(image)
            
            # Select OCR engine
            if ocr_engine == "auto":
                # Prefer EasyOCR if available, fallback to Tesseract
                ocr_engine = "easyocr" if EASYOCR_AVAILABLE else "tesseract"
            
            # Perform OCR
            if ocr_engine == "easyocr" and EASYOCR_AVAILABLE:
                try:
                    # Initialize EasyOCR reader (cache it for performance)
                    if not hasattr(self, '_easyocr_reader'):
                        self._easyocr_reader = easyocr.Reader([language], gpu=False)
                    
                    # Convert PIL to numpy array
                    img_array = np.array(image)
                    results = self._easyocr_reader.readtext(img_array)
                    
                    if output_format == "structured":
                        structured_results = []
                        full_text = []
                        for (bbox, text, confidence) in results:
                            structured_results.append({
                                "text": text,
                                "confidence": float(confidence),
                                "bbox": bbox
                            })
                            full_text.append(text)
                        
                        return json.dumps({
                            "text": " ".join(full_text),
                            "words": structured_results,
                            "engine": "easyocr",
                            "language": language
                        }, indent=2)
                    else:
                        text = " ".join([result[1] for result in results])
                        return text
                        
                except Exception as e:
                    logger.warning(f"EasyOCR failed: {e}, falling back to Tesseract")
                    ocr_engine = "tesseract"
            
            if ocr_engine == "tesseract" and TESSERACT_AVAILABLE:
                try:
                    if output_format == "structured":
                        # Get detailed data with bounding boxes
                        data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
                        
                        words = []
                        full_text = []
                        for i in range(len(data['text'])):
                            if int(data['conf'][i]) > 0:  # Confidence > 0
                                word_info = {
                                    "text": data['text'][i],
                                    "confidence": int(data['conf'][i]),
                                    "bbox": {
                                        "left": data['left'][i],
                                        "top": data['top'][i],
                                        "width": data['width'][i],
                                        "height": data['height'][i]
                                    },
                                    "level": data['level'][i],
                                    "page_num": data['page_num'][i],
                                    "block_num": data['block_num'][i],
                                    "par_num": data['par_num'][i],
                                    "line_num": data['line_num'][i],
                                    "word_num": data['word_num'][i]
                                }
                                words.append(word_info)
                                full_text.append(data['text'][i])
                        
                        return json.dumps({
                            "text": " ".join(full_text),
                            "words": words,
                            "engine": "tesseract",
                            "language": language
                        }, indent=2)
                    else:
                        text = pytesseract.image_to_string(image, lang=language)
                        return text.strip()
                        
                except Exception as e:
                    return f"Error: Tesseract OCR failed: {str(e)}"
            
            return "Error: No OCR engine available or OCR failed"
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}", exc_info=True)
            return f"Error extracting text from image: {str(e)}"
    
    async def _arun(
        self,
        image_data: str,
        language: str = "eng",
        ocr_engine: str = "auto",
        preprocess: bool = True,
        output_format: str = "text"
    ) -> str:
        """
        Async version of _run for better performance in async contexts.
        
        This method provides an asynchronous interface for OCR operations,
        allowing it to be used efficiently in async agent execution flows. Currently
        delegates to the synchronous _run method, but structured for future async optimization.
        
        Args:
            image_data: Base64-encoded image or file path
            language: Language code for OCR
            ocr_engine: OCR engine to use (auto, tesseract, easyocr)
            preprocess: Whether to apply image preprocessing
            output_format: Output format (text or structured)
        
        Returns:
            str: Extracted text or structured JSON, same as _run().
        
        Note:
            Currently implemented as a wrapper around _run() for compatibility.
            Future versions may implement true async OCR processing for better performance.
        """
        return self._run(image_data, language, ocr_engine, preprocess, output_format)


class ExtractTextFromPDFImagesInput(BaseModel):
    """Input schema for ExtractTextFromPDFImagesTool."""
    file_path: str = Field(..., description="Path to PDF file or base64-encoded file data")
    pages: Optional[List[int]] = Field(None, description="Specific pages to process (default: all pages)")
    ocr_engine: str = Field("auto", description="OCR engine: 'tesseract', 'easyocr', or 'auto' (default: 'auto')")
    output_format: str = Field("text", description="Output format: 'text' or 'structured' (default: 'text')")


class ExtractTextFromPDFImagesTool(BaseTool):
    """
    Extract text from images embedded in PDF files using OCR.
    
    This tool extracts text from PDF files that contain images (scanned PDFs, image-based PDFs).
    It converts each PDF page to an image, applies OCR to extract text, and combines the results
    from all pages. This is essential for PDFs that don't have selectable text layers.
    
    **When to use this tool:**
    - Extracting text from scanned PDFs
    - Processing image-based PDF documents
    - Reading PDFs that don't have selectable text
    - Converting scanned documents to searchable text
    - Processing PDFs with embedded images containing text
    - Extracting text from PDFs with poor text layer quality
    
    **When NOT to use this tool:**
    - For PDFs with good text layers (use regular PDF text extraction)
    - When PDF text is already selectable (OCR is unnecessary)
    - For very large PDFs with many pages (may be slow)
    - When you only need specific pages (can specify pages parameter)
    
    **Input requirements:**
    - Must provide a valid PDF file (.pdf format) as base64 or file path
    - Pages parameter is optional (defaults to all pages)
    - OCR engine selection is automatic (EasyOCR preferred, Tesseract fallback)
    - Output format can be text or structured
    
    **Output:**
    - If output_format="text": Returns text from all pages with page break markers
    - If output_format="structured": Returns JSON with:
      - pages: List of page objects with text, words, confidence scores
      - full_text: Combined text from all pages
      - total_pages: Number of pages processed
    - Returns error message if PDF processing or OCR fails
    
    **Processing:**
    1. Converts PDF pages to images using pdf2image
    2. Filters to specified pages if provided
    3. Applies OCR to each page image
    4. Combines results from all pages
    5. Returns formatted output
    
    **Limitations:**
    - Processing time increases with number of pages
    - Large PDFs may consume significant memory
    - OCR accuracy depends on image quality in PDF
    - Complex layouts may not be preserved
    - Requires pdf2image and poppler system dependency
    
    **Example use cases:**
    1. "Extract all text from this scanned PDF document"
    2. "Read text from pages 1-5 of this image-based PDF"
    3. "Extract text from this PDF with structured output showing page numbers"
    4. "Convert this scanned PDF to searchable text"
    
    **Configuration:**
    Requires pdf2image library and poppler system dependency. The tool uses ExtractTextFromImageTool
    internally for OCR on each page. Processing is sequential (one page at a time) to manage memory.
    """
    name: str = "extract_text_from_pdf_images"
    description: str = (
        "Extract text from images embedded in PDF files using OCR. "
        "Converts PDF pages to images and applies OCR to extract text. "
        "Useful for scanned PDFs or image-based PDF documents. "
        "IMPORTANT: PDF can be base64-encoded string or file path. Pages parameter is optional (defaults to all). "
        "Best for: scanned PDFs, image-based PDFs, PDFs without selectable text. "
        "NOT suitable for: PDFs with good text layers, very large PDFs, or when text is already selectable."
    )
    args_schema: Type[BaseModel] = ExtractTextFromPDFImagesInput

    def _run(
        self,
        file_path: str,
        pages: Optional[List[int]] = None,
        ocr_engine: str = "auto",
        output_format: str = "text"
    ) -> str:
        """
        Extract text from PDF images.
        
        This method performs the PDF OCR operation:
        1. Decodes PDF input (base64 or file path)
        2. Converts PDF pages to images using pdf2image
        3. Filters to specified pages if provided
        4. Applies OCR to each page using ExtractTextFromImageTool
        5. Combines results from all pages
        6. Returns formatted output (text or structured)
        
        Args:
            file_path: Path to PDF file or base64-encoded file data.
                      Example: "document.pdf" or base64 string from file upload
            pages: Optional list of page numbers (0-based index) to process.
                  If None, processes all pages.
                  Example: [0, 1, 2] for first 3 pages, [5, 6, 7] for pages 6-8
            ocr_engine: OCR engine to use (auto, tesseract, easyocr).
                       Passed to ExtractTextFromImageTool for each page
            output_format: Output format:
                          - "text": Plain text with page break markers
                          - "structured": JSON with per-page data
        
        Returns:
            str: If output_format="text": Text from all pages with "--- Page Break ---" separators.
                 If output_format="structured": JSON string with:
                 - pages: List of page objects (text, words, confidence, page number)
                 - full_text: Combined text from all pages
                 - total_pages: Number of pages processed
                 Returns error message string if PDF processing or OCR fails.
        
        Raises:
            No exceptions are raised - all errors are caught and returned as error message strings.
        """
        if not PDF_AVAILABLE:
            return "Error: PyPDF2 and pdf2image libraries are not installed. Please install them with: pip install PyPDF2 pdf2image"
        
        if not PIL_AVAILABLE:
            return "Error: PIL/Pillow library is not installed."
        
        try:
            logger.info(f"Extracting text from PDF images (pages: {pages or 'all'})")
            
            # Decode PDF if base64
            try:
                pdf_bytes = base64.b64decode(file_path)
            except Exception:
                with open(file_path, 'rb') as f:
                    pdf_bytes = f.read()
            
            # Convert PDF pages to images
            images = convert_from_bytes(pdf_bytes)
            
            # Filter pages if specified
            if pages:
                images = [images[i] for i in pages if 0 <= i < len(images)]
            
            # Use ExtractTextFromImageTool for each image
            ocr_tool = ExtractTextFromImageTool()
            all_text = []
            all_structured = []
            
            for i, image in enumerate(images):
                # Convert PIL image to base64
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                
                result = ocr_tool._run(
                    image_data=img_base64,
                    language="eng",
                    ocr_engine=ocr_engine,
                    preprocess=True,
                    output_format=output_format
                )
                
                if output_format == "structured":
                    try:
                        result_dict = json.loads(result)
                        result_dict["page"] = i + 1
                        all_structured.append(result_dict)
                        all_text.append(result_dict.get("text", ""))
                    except:
                        all_text.append(result)
                else:
                    all_text.append(result)
            
            if output_format == "structured":
                return json.dumps({
                    "pages": all_structured,
                    "full_text": "\n\n".join(all_text),
                    "total_pages": len(images)
                }, indent=2)
            else:
                return "\n\n--- Page Break ---\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF images: {str(e)}", exc_info=True)
            return f"Error extracting text from PDF images: {str(e)}"
    
    async def _arun(
        self,
        file_path: str,
        pages: Optional[List[int]] = None,
        ocr_engine: str = "auto",
        output_format: str = "text"
    ) -> str:
        """
        Async version of _run for better performance in async contexts.
        
        This method provides an asynchronous interface for PDF OCR operations,
        allowing it to be used efficiently in async agent execution flows. Currently
        delegates to the synchronous _run method, but structured for future async optimization.
        
        Args:
            file_path: Path to PDF file or base64-encoded file data
            pages: Optional list of page numbers to process
            ocr_engine: OCR engine to use
            output_format: Output format (text or structured)
        
        Returns:
            str: Extracted text or structured JSON, same as _run().
        
        Note:
            Currently implemented as a wrapper around _run() for compatibility.
            Future versions may implement true async PDF processing for better performance.
        """
        return self._run(file_path, pages, ocr_engine, output_format)


class AnalyzeDocumentStructureInput(BaseModel):
    """Input schema for AnalyzeDocumentStructureTool."""
    file_path: str = Field(..., description="Path to document or base64-encoded file data")
    file_type: str = Field(..., description="File type: pdf, image, docx, pptx")
    include_images: bool = Field(True, description="Extract text from images using OCR (default: True)")
    output_format: str = Field("structured", description="Output format: 'text', 'structured', or 'markdown' (default: 'structured')")


class AnalyzeDocumentStructureTool(BaseTool):
    """
    Analyze document structure and extract text with layout information.
    
    This tool provides comprehensive document analysis, extracting not just text but also
    structure, layout, and metadata. It supports multiple document formats and can optionally
    extract text from images within documents using OCR. The tool provides structured output
    that preserves document organization and hierarchy.
    
    **When to use this tool:**
    - Extracting structured content from documents
    - Understanding document layout and organization
    - Processing documents with embedded images
    - Getting comprehensive document analysis
    - Extracting text while preserving structure
    - Analyzing document format and metadata
    - Processing multi-format documents (PDF, DOCX, images)
    
    **When NOT to use this tool:**
    - For simple text extraction (use document reading tools)
    - When you only need raw text (structure adds overhead)
    - For very large documents (may be slow)
    - When structure doesn't matter
    
    **Input requirements:**
    - Must provide a valid document file (PDF, image, DOCX, PPTX) as base64 or file path
    - File type must be specified
    - include_images flag controls OCR extraction from images
    - Output format can be text, structured, or markdown
    
    **Output:**
    - If output_format="text": Plain text with structure markers
    - If output_format="markdown": Markdown-formatted text
    - If output_format="structured": JSON with:
      - file_type: Document type
      - content: List of content blocks with type, content, metadata
      - images: List of image OCR results (if include_images=True)
      - metadata: Document metadata (pages, sections, etc.)
    - Returns error message if analysis fails
    
    **Supported File Types:**
    - pdf: PDF files - extracts text and optionally OCR from images
    - image/png/jpg/jpeg: Image files - extracts text using OCR
    - docx: Word documents - extracts paragraphs with styles
    - pptx: PowerPoint files (future enhancement)
    
    **Features:**
    - Text content extraction with structure preservation
    - Layout information (headers, paragraphs, sections)
    - Images with OCR text extraction (optional)
    - Metadata extraction (page numbers, styles, etc.)
    - Multi-format support
    
    **Limitations:**
    - Complex layouts may not be perfectly preserved
    - Table extraction is basic (text only, no structure)
    - Image OCR adds processing time
    - Some document formats have limited structure extraction
    
    **Example use cases:**
    1. "Analyze the structure of this PDF document and extract all text with layout information"
    2. "Extract text from this document including OCR from images"
    3. "Get structured content from this Word document showing paragraphs and styles"
    4. "Analyze this image document and extract all text with bounding boxes"
    
    **Configuration:**
    Requires appropriate libraries for each file type (PyPDF2, python-docx, PIL, OCR tools).
    The tool automatically detects file type and applies appropriate extraction methods.
    OCR from images uses ExtractTextFromImageTool when include_images=True.
    """
    name: str = "analyze_document_structure"
    description: str = (
        "Analyze document structure and extract text with layout information. "
        "Provides structured output with text, layout, images, and metadata. "
        "Supports PDF, images, DOCX, and PPTX files. "
        "IMPORTANT: File can be base64-encoded string or file path. File type must be specified. "
        "Best for: structured content extraction, document layout analysis, comprehensive document processing. "
        "NOT suitable for: simple text extraction, very large documents, or when structure doesn't matter."
    )
    args_schema: Type[BaseModel] = AnalyzeDocumentStructureInput

    def _run(
        self,
        file_path: str,
        file_type: str,
        include_images: bool = True,
        output_format: str = "structured"
    ) -> str:
        """
        Analyze document structure.
        
        This method performs the document structure analysis:
        1. Decodes file input (base64 or file path)
        2. Detects file type and applies appropriate extraction
        3. Extracts text content with structure information
        4. Optionally extracts text from images using OCR
        5. Formats output based on requested format
        6. Returns structured analysis
        
        Args:
            file_path: Path to document or base64-encoded file data.
                      Example: "document.pdf", "image.png", or base64 string
            file_type: File type string: "pdf", "image", "png", "jpg", "jpeg", "docx", "pptx"
            include_images: If True, extracts text from images using OCR (default: True).
                          Applies to PDFs with embedded images and image files.
            output_format: Output format:
                          - "text": Plain text with structure markers
                          - "markdown": Markdown-formatted text
                          - "structured": JSON with full structure (default)
        
        Returns:
            str: If output_format="text": Plain text with content blocks.
                 If output_format="markdown": Markdown-formatted text.
                 If output_format="structured": JSON string with:
                 - file_type: Document type
                 - content: List of content blocks (type, content, metadata)
                 - images: List of image OCR results (if include_images=True)
                 - metadata: Document metadata
                 Returns error message string if analysis fails.
        
        Raises:
            No exceptions are raised - all errors are caught and returned as error message strings.
        """
        try:
            logger.info(f"Analyzing {file_type} document structure")
            
            result = {
                "file_type": file_type,
                "content": [],
                "images": [],
                "metadata": {}
            }
            
            # Handle different file types
            if file_type.lower() == "pdf":
                if not PDF_AVAILABLE:
                    return "Error: PyPDF2 required for PDF files"
                
                try:
                    pdf_bytes = base64.b64decode(file_path) if len(file_path) > 100 else open(file_path, 'rb').read()
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                    
                    result["metadata"]["pages"] = len(pdf_reader.pages)
                    
                    for i, page in enumerate(pdf_reader.pages):
                        text = page.extract_text()
                        result["content"].append({
                            "page": i + 1,
                            "type": "text",
                            "content": text
                        })
                    
                    if include_images:
                        # Extract text from images in PDF
                        ocr_tool = ExtractTextFromPDFImagesTool()
                        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                        ocr_result = ocr_tool._run(pdf_base64, None, "auto", "structured")
                        result["images"] = json.loads(ocr_result).get("pages", [])
                        
                except Exception as e:
                    return f"Error processing PDF: {str(e)}"
            
            elif file_type.lower() in ["image", "png", "jpg", "jpeg"]:
                if include_images:
                    ocr_tool = ExtractTextFromImageTool()
                    ocr_result = ocr_tool._run(file_path, "eng", "auto", True, "structured")
                    result["content"].append({
                        "type": "ocr_text",
                        "content": json.loads(ocr_result).get("text", "")
                    })
                    result["images"] = [json.loads(ocr_result)]
            
            elif file_type.lower() == "docx":
                try:
                    import docx
                    doc_bytes = base64.b64decode(file_path) if len(file_path) > 100 else open(file_path, 'rb').read()
                    doc = docx.Document(io.BytesIO(doc_bytes))
                    
                    for para in doc.paragraphs:
                        if para.text.strip():
                            result["content"].append({
                                "type": "paragraph",
                                "content": para.text,
                                "style": para.style.name
                            })
                except ImportError:
                    return "Error: python-docx required for DOCX files"
                except Exception as e:
                    return f"Error processing DOCX: {str(e)}"
            
            else:
                return f"Error: Unsupported file type: {file_type}"
            
            # Format output
            if output_format == "text":
                text_parts = [item.get("content", "") for item in result["content"]]
                return "\n\n".join(text_parts)
            elif output_format == "markdown":
                # Convert to markdown format
                md_parts = []
                for item in result["content"]:
                    if item.get("type") == "paragraph":
                        md_parts.append(item["content"])
                return "\n\n".join(md_parts)
            else:
                return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing document structure: {str(e)}", exc_info=True)
            return f"Error analyzing document structure: {str(e)}"
    
    async def _arun(
        self,
        file_path: str,
        file_type: str,
        include_images: bool = True,
        output_format: str = "structured"
    ) -> str:
        """
        Async version of _run for better performance in async contexts.
        
        This method provides an asynchronous interface for document structure analysis,
        allowing it to be used efficiently in async agent execution flows. Currently
        delegates to the synchronous _run method, but structured for future async optimization.
        
        Args:
            file_path: Path to document or base64-encoded file data
            file_type: File type string
            include_images: Whether to extract text from images using OCR
            output_format: Output format (text, markdown, structured)
        
        Returns:
            str: Document structure analysis, same as _run().
        
        Note:
            Currently implemented as a wrapper around _run() for compatibility.
            Future versions may implement true async document processing for better performance.
        """
        return self._run(file_path, file_type, include_images, output_format)

