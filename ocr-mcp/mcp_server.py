#!/usr/bin/env python3
"""OCR MCP Server — extract text from images and PDFs using Tesseract OCR."""
import base64
import io
import json
import logging
import os
import sys
from typing import Optional

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("ocr-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8438"))

mcp = FastMCP("OCR MCP Server", instructions="Extract text from images and PDFs using Tesseract OCR. Supports base64 input, file paths, and structured output with bounding boxes.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def _decode_image(image_input: str) -> "Image.Image":
    try:
        image_bytes = base64.b64decode(image_input)
        return Image.open(io.BytesIO(image_bytes))
    except Exception:
        return Image.open(image_input)


@mcp.tool()
def extract_text_from_image(
    image_data: str,
    language: str = "eng",
    output_format: str = "text",
) -> str:
    """Extract text from an image using Tesseract OCR.

    Args:
        image_data: Base64-encoded image string or local file path.
        language: Tesseract language code (default 'eng'). Examples: eng, spa, fra, deu.
        output_format: 'text' for plain text, 'structured' for JSON with bounding boxes and confidence.
    """
    if not PIL_AVAILABLE:
        return json.dumps({"error": "Pillow not installed"})
    if not TESSERACT_AVAILABLE:
        return json.dumps({"error": "pytesseract not installed"})

    try:
        image = _decode_image(image_data)

        if output_format == "structured":
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            words = []
            full_text = []
            for i in range(len(data["text"])):
                if int(data["conf"][i]) > 0:
                    word = {
                        "text": data["text"][i],
                        "confidence": int(data["conf"][i]),
                        "bbox": {"left": data["left"][i], "top": data["top"][i], "width": data["width"][i], "height": data["height"][i]},
                    }
                    words.append(word)
                    full_text.append(data["text"][i])
            return json.dumps({"text": " ".join(full_text), "words": words, "engine": "tesseract", "language": language}, indent=2)
        else:
            text = pytesseract.image_to_string(image, lang=language)
            return text.strip() if text.strip() else "No text found."
    except Exception as e:
        return json.dumps({"error": f"OCR failed: {str(e)}"})


@mcp.tool()
def extract_text_from_pdf(
    file_path: str,
    pages: Optional[str] = None,
    language: str = "eng",
) -> str:
    """Extract text from a scanned PDF by converting pages to images and running OCR.

    Args:
        file_path: Path to PDF file or base64-encoded PDF data.
        pages: Comma-separated page numbers (1-based) to process, or empty for all.
        language: Tesseract language code.
    """
    if not PIL_AVAILABLE or not TESSERACT_AVAILABLE:
        return json.dumps({"error": "Pillow and pytesseract required"})
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        return json.dumps({"error": "pdf2image not installed"})

    try:
        try:
            pdf_bytes = base64.b64decode(file_path)
        except Exception:
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

        images = convert_from_bytes(pdf_bytes)
        if pages:
            indices = [int(p.strip()) - 1 for p in pages.split(",") if p.strip().isdigit()]
            images = [images[i] for i in indices if 0 <= i < len(images)]

        all_text = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang=language).strip()
            all_text.append(f"--- Page {i+1} ---\n{text}")

        return "\n\n".join(all_text) if all_text else "No text found."
    except Exception as e:
        return json.dumps({"error": f"PDF OCR failed: {str(e)}"})


@mcp.tool()
def ocr_info() -> str:
    """Return OCR server status and available engines."""
    return json.dumps({
        "status": "running",
        "tesseract_available": TESSERACT_AVAILABLE,
        "pillow_available": PIL_AVAILABLE,
        "tesseract_version": pytesseract.get_tesseract_version().decode() if TESSERACT_AVAILABLE else None,
    }, indent=2, default=str)


if __name__ == "__main__":
    logger.info("Starting ocr-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
