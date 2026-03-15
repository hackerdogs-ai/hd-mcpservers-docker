"""
Comprehensive tests for MISP threat intelligence tools.

This test suite validates all MISP LangChain tools including:
- misp_file_report
- misp_url_report
- misp_domain_report
- misp_ip_report
- misp_submit_url

Tests cover:
- Tool initialization and configuration
- API key management via ToolRuntime
- Successful queries and responses
- Error handling (missing config, API errors, invalid inputs)
- Edge cases (empty results, invalid hashes, network errors)
- Real-world scenarios
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Try to import MISP tools
try:
    from shared.modules.tools.ti.misp import (
        misp_file_report,
        misp_url_report,
        misp_domain_report,
        misp_ip_report,
        misp_submit_url,
        _calculate_threat_verdict,
        MISPSecurityAgentState
    )
    MISP_TOOLS_AVAILABLE = True
except ImportError as e:
    MISP_TOOLS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.fixture
def mock_runtime():
    """Create a mock ToolRuntime with MISP configuration."""
    runtime = Mock()
    runtime.state = {
        "api_keys": {"misp": "test_api_key_123"},
        "user_id": "test_user_001"
    }
    return runtime


@pytest.fixture
def mock_runtime_no_config():
    """Create a mock ToolRuntime without MISP configuration."""
    runtime = Mock()
    runtime.state = {
        "api_keys": {},
        "user_id": "test_user_001"
    }
    return runtime


@pytest.fixture
def mock_misp_response():
    """Create a mock MISP API response."""
    return {
        "response": {
            "attributes": [
                {
                    "id": "attr-123",
                    "value": "44d88612fea8a8f36de82e1278abb02f",
                    "type": "md5",
                    "first_analysis_date": 1640995200,
                    "tags": ["malicious", "apt28"],
                    "confidence": 95
                }
            ]
        }
    }


class TestMISPHelperFunctions:
    """Test helper functions for MISP tools."""
    
    def test_calculate_threat_verdict_malicious(self):
        """Test threat verdict calculation for malicious indicator."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        attributes = {"tags": ["malicious"], "confidence": 95}
        verdict = _calculate_threat_verdict(attributes)
        assert verdict == "MALICIOUS"
    
    def test_calculate_threat_verdict_suspicious(self):
        """Test threat verdict calculation for suspicious indicator."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        attributes = {"tags": ["suspicious"], "confidence": 75}
        verdict = _calculate_threat_verdict(attributes)
        assert verdict == "SUSPICIOUS"
    
    def test_calculate_threat_verdict_clean(self):
        """Test threat verdict calculation for clean indicator."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        attributes = {"tags": ["clean"], "confidence": 30}
        verdict = _calculate_threat_verdict(attributes)
        assert verdict == "CLEAN"
    
    def test_calculate_threat_verdict_unknown(self):
        """Test threat verdict calculation for unknown indicator."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        attributes = {"tags": [], "confidence": 60}
        verdict = _calculate_threat_verdict(attributes)
        assert verdict == "UNKNOWN"
    
    def test_calculate_threat_verdict_high_confidence(self):
        """Test threat verdict calculation with high confidence."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        attributes = {"tags": [], "confidence": 95}
        verdict = _calculate_threat_verdict(attributes)
        assert verdict == "MALICIOUS"


class TestMISPFileReport:
    """Test misp_file_report tool."""
    
    def test_file_report_success(self, mock_runtime, mock_misp_response):
        """Test successful file hash lookup."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_misp_response
            mock_get.return_value = mock_response
            
            result = misp_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["hash"] == "44d88612fea8a8f36de82e1278abb02f"
            assert "threat_verdict" in parsed
            assert "tags" in parsed
            assert parsed["user_id"] == "test_user_001"
    
    def test_file_report_no_config(self, mock_runtime_no_config):
        """Test file report without API key."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        result = misp_file_report.func(mock_runtime_no_config, "44d88612fea8a8f36de82e1278abb02f")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()
    
    def test_file_report_invalid_api_key(self, mock_runtime):
        """Test file report with invalid API key."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            result = misp_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "Invalid" in parsed["message"]
    
    def test_file_report_not_found(self, mock_runtime):
        """Test file report for hash not in database."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = misp_file_report.func(mock_runtime, "nonexistent_hash")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found" in parsed["message"].lower()
    
    def test_file_report_no_attributes(self, mock_runtime):
        """Test file report with no attributes found."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        mock_response_empty = {
            "response": {
                "attributes": []
            }
        }
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_empty
            mock_get.return_value = mock_response
            
            result = misp_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "No attributes found" in parsed["message"]
    
    def test_file_report_timeout(self, mock_runtime):
        """Test file report with network timeout."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            from requests.exceptions import Timeout
            mock_get.side_effect = Timeout("Request timeout")
            
            result = misp_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "timeout" in parsed["message"].lower()


class TestMISPURLReport:
    """Test misp_url_report tool."""
    
    def test_url_report_success(self, mock_runtime, mock_misp_response):
        """Test successful URL lookup."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_misp_response
            mock_get.return_value = mock_response
            
            result = misp_url_report.func(mock_runtime, "https://example.com")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["url"] == "https://example.com"
            assert "threat_verdict" in parsed
            assert "tags" in parsed
    
    def test_url_report_no_config(self, mock_runtime_no_config):
        """Test URL report without API key."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        result = misp_url_report.func(mock_runtime_no_config, "https://example.com")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()


class TestMISPDomainReport:
    """Test misp_domain_report tool."""
    
    def test_domain_report_success(self, mock_runtime, mock_misp_response):
        """Test successful domain lookup."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_misp_response
            mock_get.return_value = mock_response
            
            result = misp_domain_report.func(mock_runtime, "example.com")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["domain"] == "example.com"
            assert "threat_verdict" in parsed
            assert "tags" in parsed
    
    def test_domain_report_no_config(self, mock_runtime_no_config):
        """Test domain report without API key."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        result = misp_domain_report.func(mock_runtime_no_config, "example.com")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()


class TestMISPIPReport:
    """Test misp_ip_report tool."""
    
    def test_ip_report_success(self, mock_runtime, mock_misp_response):
        """Test successful IP address lookup."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_misp_response
            mock_get.return_value = mock_response
            
            result = misp_ip_report.func(mock_runtime, "8.8.8.8")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["ip_address"] == "8.8.8.8"
            assert "threat_verdict" in parsed
            assert "tags" in parsed
    
    def test_ip_report_no_config(self, mock_runtime_no_config):
        """Test IP report without API key."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        result = misp_ip_report.func(mock_runtime_no_config, "8.8.8.8")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()


class TestMISPSubmitURL:
    """Test misp_submit_url tool."""
    
    def test_submit_url_success(self, mock_runtime):
        """Test successful URL submission."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        mock_response_data = {
            "id": "attr-123"
        }
        
        with patch('shared.modules.tools.ti.misp.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response
            
            result = misp_submit_url.func(mock_runtime, "https://example.com")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["url"] == "https://example.com"
            assert "attribute_id" in parsed
    
    def test_submit_url_no_config(self, mock_runtime_no_config):
        """Test URL submission without API key."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        result = misp_submit_url.func(mock_runtime_no_config, "https://example.com")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()
    
    def test_submit_url_api_error(self, mock_runtime):
        """Test URL submission with API error."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid URL format"
            mock_post.return_value = mock_response
            
            result = misp_submit_url.func(mock_runtime, "invalid-url")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "API error" in parsed["message"]


class TestMISPRealWorldScenarios:
    """Test real-world scenarios for MISP tools."""
    
    def test_incident_response_workflow(self, mock_runtime, mock_misp_response):
        """Test complete incident response workflow."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.misp.requests.get') as mock_get, \
             patch('shared.modules.tools.ti.misp.requests.post') as mock_post:
            
            # Mock successful responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_misp_response
            mock_get.return_value = mock_response
            
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {"id": "attr-123"}
            mock_post.return_value = mock_post_response
            
            # Step 1: Check file hash
            file_result = misp_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            assert json.loads(file_result)["status"] == "success"
            
            # Step 2: Check URL
            url_result = misp_url_report.func(mock_runtime, "https://suspicious-site.com")
            assert json.loads(url_result)["status"] == "success"
            
            # Step 3: Check domain
            domain_result = misp_domain_report.func(mock_runtime, "suspicious-site.com")
            assert json.loads(domain_result)["status"] == "success"
            
            # Step 4: Check IP
            ip_result = misp_ip_report.func(mock_runtime, "192.168.1.1")
            assert json.loads(ip_result)["status"] == "success"
            
            # Step 5: Submit new URL
            submit_result = misp_submit_url.func(mock_runtime, "https://new-suspicious-site.com")
            assert json.loads(submit_result)["status"] == "success"
    
    def test_threat_verdict_calculation_scenarios(self):
        """Test threat verdict calculation with various scenarios."""
        if not MISP_TOOLS_AVAILABLE:
            pytest.skip(f"MISP tools not available: {IMPORT_ERROR}")
        
        # Malicious tag
        attributes1 = {"tags": ["malicious"], "confidence": 95}
        verdict1 = _calculate_threat_verdict(attributes1)
        assert verdict1 == "MALICIOUS"
        
        # Suspicious tag
        attributes2 = {"tags": ["suspicious"], "confidence": 75}
        verdict2 = _calculate_threat_verdict(attributes2)
        assert verdict2 == "SUSPICIOUS"
        
        # High confidence without tags
        attributes3 = {"tags": [], "confidence": 95}
        verdict3 = _calculate_threat_verdict(attributes3)
        assert verdict3 == "MALICIOUS"
        
        # Clean tag
        attributes4 = {"tags": ["clean"], "confidence": 30}
        verdict4 = _calculate_threat_verdict(attributes4)
        assert verdict4 == "CLEAN"
        
        # Unknown
        attributes5 = {"tags": [], "confidence": 60}
        verdict5 = _calculate_threat_verdict(attributes5)
        assert verdict5 == "UNKNOWN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

