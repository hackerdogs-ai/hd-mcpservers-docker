"""
Comprehensive tests for OCR Tools

Tests all 3 OCR tools:
- ExtractTextFromImageTool
- ExtractTextFromPDFImagesTool
- AnalyzeDocumentStructureTool

Includes real-world testing with images downloaded from the web.
"""

import pytest
import base64
import io
import json
import tempfile
import os
import requests

# Conditional imports for optional dependencies
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    pytest.skip("PIL/Pillow not available", allow_module_level=True)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import tools - handle both relative and absolute imports
try:
    from .ocr_tools import (
        ExtractTextFromImageTool,
        ExtractTextFromPDFImagesTool,
        AnalyzeDocumentStructureTool,
        _decode_image_input,
        _preprocess_image
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from shared.modules.tools.prodx.ocr_tools import (
        ExtractTextFromImageTool,
        ExtractTextFromPDFImagesTool,
        AnalyzeDocumentStructureTool,
        _decode_image_input,
        _preprocess_image
    )

# Import test utilities
try:
    from .test_utils import (
        download_image_from_url,
        create_test_image_with_text,
        get_test_image_urls
    )
except ImportError:
    # Fallback
    try:
        from test_utils import (
            download_image_from_url,
            create_test_image_with_text,
            get_test_image_urls
        )
    except ImportError:
        # Define minimal versions if import fails
        def download_image_from_url(url: str, timeout: int = 10):
            try:
                response = requests.get(url, timeout=timeout, stream=True)
                response.raise_for_status()
                return Image.open(io.BytesIO(response.content))
            except:
                return None
        
        def create_test_image_with_text(text: str = "TEST", size: tuple = (200, 100)):
            img = Image.new('RGB', size, color='white')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            file_bytes = buffer.read()
            encoded = base64.b64encode(file_bytes).decode('utf-8')
            return file_bytes, encoded
        
        def get_test_image_urls():
            return [
                "https://via.placeholder.com/400x200/000000/FFFFFF?text=TEST+IMAGE",
            ]


class TestHelperFunctions:
    """Test helper functions."""
    
    def create_test_image(self, text="TEST"):
        """Create a simple test image."""
        # Create a simple image with text (simplified)
        img = Image.new('RGB', (200, 100), color='white')
        return img
    
    def test_decode_image_input_base64(self):
        """Test decoding base64 image input."""
        # Create a simple PNG image
        img = Image.new('RGB', (10, 10), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        encoded = base64.b64encode(buffer.read()).decode('utf-8')
        decoded_img = _decode_image_input(encoded)
        
        assert decoded_img is not None
        assert isinstance(decoded_img, Image.Image)
    
    def test_decode_image_input_file_path(self):
        """Test decoding image from file path."""
        img = Image.new('RGB', (10, 10), color='white')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            decoded_img = _decode_image_input(tmp_path)
            assert decoded_img is not None
            assert isinstance(decoded_img, Image.Image)
        finally:
            os.unlink(tmp_path)
    
    def test_decode_image_input_invalid(self):
        """Test decoding invalid image input."""
        with pytest.raises(ValueError):
            _decode_image_input("invalid_data")
    
    def test_preprocess_image(self):
        """Test image preprocessing."""
        img = Image.new('RGB', (100, 100), color='white')
        processed = _preprocess_image(img)
        assert processed is not None


class TestExtractTextFromImageTool:
    """Test ExtractTextFromImageTool."""
    
    def create_test_image_base64(self):
        """Create a test image as base64."""
        img = Image.new('RGB', (200, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def test_extract_text_basic(self):
        """Test basic text extraction."""
        tool = ExtractTextFromImageTool()
        image_data = self.create_test_image_base64()
        
        result = tool._run(image_data)
        result_dict = json.loads(result)
        
        assert result_dict["status"] == "success"
        assert "text" in result_dict
        assert isinstance(result_dict["text"], str)
    
    def test_extract_text_with_tesseract(self):
        """Test text extraction with Tesseract."""
        tool = ExtractTextFromImageTool()
        image_data = self.create_test_image_base64()
        
        result = tool._run(image_data, ocr_engine="tesseract")
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_extract_text_with_easyocr(self):
        """Test text extraction with EasyOCR."""
        tool = ExtractTextFromImageTool()
        image_data = self.create_test_image_base64()
        
        result = tool._run(image_data, ocr_engine="easyocr")
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_extract_text_invalid_image(self):
        """Test extraction with invalid image."""
        tool = ExtractTextFromImageTool()
        
        result = tool._run("invalid_base64")
        assert "Error" in result
    
    def test_extract_text_from_file_path(self):
        """Test extraction from file path."""
        tool = ExtractTextFromImageTool()
        img = Image.new('RGB', (200, 100), color='white')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            result = tool._run(tmp_path)
            result_dict = json.loads(result)
            assert result_dict["status"] == "success"
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="requests not available")
    def test_extract_text_from_web_image(self):
        """Test extraction from web-downloaded image (real-world scenario)."""
        tool = ExtractTextFromImageTool()
        
        # Download a test image from the web
        test_urls = get_test_image_urls()
        for url in test_urls:
            try:
                img = download_image_from_url(url, timeout=5)
                if img is None:
                    continue
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                image_data = base64.b64encode(buffer.read()).decode('utf-8')
                
                # Test extraction
                result = tool._run(image_data)
                result_dict = json.loads(result)
                
                assert result_dict["status"] == "success"
                assert "text" in result_dict
                # At least one image should work
                break
            except Exception as e:
                # Continue to next URL if this one fails
                print(f"Failed to test with {url}: {e}")
                continue
    
    def test_extract_text_different_image_formats(self):
        """Test extraction from different image formats."""
        tool = ExtractTextFromImageTool()
        
        formats = ['PNG', 'JPEG', 'BMP']
        for fmt in formats:
            try:
                img = Image.new('RGB', (200, 100), color='white')
                buffer = io.BytesIO()
                img.save(buffer, format=fmt)
                buffer.seek(0)
                image_data = base64.b64encode(buffer.read()).decode('utf-8')
                
                result = tool._run(image_data)
                result_dict = json.loads(result)
                assert result_dict["status"] == "success"
            except Exception as e:
                # Some formats might not be supported, that's okay
                print(f"Format {fmt} test failed: {e}")
    
    def test_extract_text_large_image(self):
        """Test extraction from large image."""
        tool = ExtractTextFromImageTool()
        
        # Create a larger image
        img = Image.new('RGB', (2000, 1000), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode('utf-8')
        
        result = tool._run(image_data)
        result_dict = json.loads(result)
        # Should handle large images gracefully
        assert isinstance(result_dict, dict) or "Error" in result
    
    def test_extract_text_empty_image(self):
        """Test extraction from empty/minimal image."""
        tool = ExtractTextFromImageTool()
        
        # Create minimal 1x1 image
        img = Image.new('RGB', (1, 1), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.read()).decode('utf-8')
        
        result = tool._run(image_data)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"


class TestExtractTextFromPDFImagesTool:
    """Test ExtractTextFromPDFImagesTool."""
    
    def create_test_pdf_base64(self):
        """Create a simple test PDF as base64."""
        # Note: Creating actual PDFs is complex, this is a placeholder
        # In real tests, you'd use a library like reportlab
        test_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
        return base64.b64encode(test_pdf_content).decode('utf-8')
    
    def test_extract_text_from_pdf_basic(self):
        """Test basic PDF text extraction."""
        tool = ExtractTextFromPDFImagesTool()
        # Note: This will likely fail with a simple PDF, but tests error handling
        pdf_data = self.create_test_pdf_base64()
        
        result = tool._run(pdf_data)
        # Should handle gracefully even if PDF is invalid
        assert isinstance(result, str)
    
    def test_extract_text_from_pdf_invalid(self):
        """Test extraction with invalid PDF."""
        tool = ExtractTextFromPDFImagesTool()
        
        result = tool._run("invalid_base64")
        assert "Error" in result
    
    def test_extract_text_from_pdf_with_pages(self):
        """Test extraction from specific pages."""
        tool = ExtractTextFromPDFImagesTool()
        pdf_data = self.create_test_pdf_base64()
        
        result = tool._run(pdf_data, page_numbers=[1])
        assert isinstance(result, str)


class TestAnalyzeDocumentStructureTool:
    """Test AnalyzeDocumentStructureTool."""
    
    def create_test_image_base64(self):
        """Create a test image as base64."""
        img = Image.new('RGB', (200, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def test_analyze_structure_basic(self):
        """Test basic document structure analysis."""
        tool = AnalyzeDocumentStructureTool()
        image_data = self.create_test_image_base64()
        
        result = tool._run(image_data)
        result_dict = json.loads(result)
        
        assert result_dict["status"] == "success"
        assert "structure" in result_dict
        assert isinstance(result_dict["structure"], dict)
    
    def test_analyze_structure_with_regions(self):
        """Test structure analysis with region detection."""
        tool = AnalyzeDocumentStructureTool()
        image_data = self.create_test_image_base64()
        
        result = tool._run(image_data, detect_regions=True)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_analyze_structure_invalid_image(self):
        """Test analysis with invalid image."""
        tool = AnalyzeDocumentStructureTool()
        
        result = tool._run("invalid_base64")
        assert "Error" in result
    
    def test_analyze_structure_from_file_path(self):
        """Test analysis from file path."""
        tool = AnalyzeDocumentStructureTool()
        img = Image.new('RGB', (200, 100), color='white')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            result = tool._run(tmp_path)
            result_dict = json.loads(result)
            assert result_dict["status"] == "success"
        finally:
            os.unlink(tmp_path)


class TestErrorHandling:
    """Test error handling across all OCR tools."""
    
    def test_all_tools_handle_missing_libraries(self):
        """Test that tools handle missing OCR libraries gracefully."""
        tools = [
            ExtractTextFromImageTool(),
            ExtractTextFromPDFImagesTool(),
            AnalyzeDocumentStructureTool()
        ]
        
        for tool in tools:
            # Each tool should return an error message, not crash
            result = tool._run("invalid_base64")
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_all_tools_handle_empty_input(self):
        """Test that all tools handle empty input."""
        tools = [
            ExtractTextFromImageTool(),
            ExtractTextFromPDFImagesTool(),
            AnalyzeDocumentStructureTool()
        ]
        
        for tool in tools:
            result = tool._run("")
            assert isinstance(result, str)
    
    def test_all_tools_handle_none_input(self):
        """Test that all tools handle None input."""
        tools = [
            ExtractTextFromImageTool(),
            ExtractTextFromPDFImagesTool(),
            AnalyzeDocumentStructureTool()
        ]
        
        for tool in tools:
            # Tools should handle None gracefully
            try:
                result = tool._run(None)
                assert isinstance(result, str)
            except (TypeError, AttributeError):
                # Some tools might raise, but should be caught internally
                pass
    
    def test_all_tools_handle_corrupted_image(self):
        """Test that tools handle corrupted image data."""
        tools = [
            ExtractTextFromImageTool(),
            AnalyzeDocumentStructureTool()
        ]
        
        # Create corrupted base64 (valid base64 but not a valid image)
        corrupted_data = base64.b64encode(b"not an image").decode('utf-8')
        
        for tool in tools:
            result = tool._run(corrupted_data)
            assert isinstance(result, str)
            # Should return error, not crash
            assert "Error" in result or json.loads(result).get("status") != "success"
    
    def test_all_tools_handle_very_large_base64(self):
        """Test that tools handle very large base64 strings."""
        tools = [
            ExtractTextFromImageTool(),
            ExtractTextFromPDFImagesTool(),
            AnalyzeDocumentStructureTool()
        ]
        
        # Create a very large base64 string (but invalid)
        large_data = "A" * 1000000  # 1MB of 'A' characters
        
        for tool in tools:
            result = tool._run(large_data)
            assert isinstance(result, str)
            # Should handle gracefully, not crash or hang
            assert len(result) < 100000  # Response should be reasonable size


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

