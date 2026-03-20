# ocr-mcp

MCP server for extracting text from images and PDFs using Tesseract OCR.

## Tools

| Tool | Description |
|------|------------|
| extract_text_from_image | OCR text from image (base64 or file path), with structured output option |
| extract_text_from_pdf | OCR text from scanned PDF pages |
| ocr_info | Server status and engine availability |

## Quick Start

```bash
docker build -t ocr-mcp .
docker run -p 8438:8438 -e MCP_TRANSPORT=streamable-http ocr-mcp
```
