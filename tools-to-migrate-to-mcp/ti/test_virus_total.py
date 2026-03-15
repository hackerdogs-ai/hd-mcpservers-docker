"""
Comprehensive tests for VirusTotal threat intelligence tools.

This test suite validates all VirusTotal LangChain tools including:
- virustotal_file_report
- virustotal_url_report
- virustotal_domain_report
- virustotal_ip_report
- scan_url

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

# Try to import VirusTotal tools
try:
    from shared.modules.tools.ti.virus_total import (
        virustotal_file_report,
        virustotal_url_report,
        virustotal_domain_report,
        virustotal_ip_report,
        scan_url,
        _calculate_threat_verdict,
        VirusTotalSecurityAgentState
    )
    VIRUSTOTAL_TOOLS_AVAILABLE = True
except ImportError as e:
    VIRUSTOTAL_TOOLS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.fixture
def mock_runtime():
    """Create a mock ToolRuntime with VirusTotal configuration."""
    runtime = Mock()
    runtime.state = {
        "api_keys": {"virustotal": "test_api_key_123"},
        "user_id": "test_user_001"
    }
    return runtime


@pytest.fixture
def mock_runtime_no_config():
    """Create a mock ToolRuntime without VirusTotal configuration."""
    runtime = Mock()
    runtime.state = {
        "api_keys": {},
        "user_id": "test_user_001"
    }
    return runtime


@pytest.fixture
def mock_vt_response():
    """Create a mock VirusTotal API response."""
    return {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "malicious": 5,
                    "suspicious": 2,
                    "undetected": 50,
                    "harmless": 10
                },
                "last_analysis_date": 1640995200,
                "meaningful_name": "malware.exe",
                "size": 1024,
                "type_description": "PE32 executable"
            }
        }
    }


class TestVirusTotalHelperFunctions:
    """Test helper functions for VirusTotal tools."""
    
    def test_calculate_threat_verdict_malicious(self):
        """Test threat verdict calculation for malicious file."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        stats = {"malicious": 5, "suspicious": 0, "undetected": 50}
        verdict = _calculate_threat_verdict(stats)
        assert "MALICIOUS" in verdict
        assert "5" in verdict
    
    def test_calculate_threat_verdict_suspicious(self):
        """Test threat verdict calculation for suspicious file."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        stats = {"malicious": 0, "suspicious": 3, "undetected": 50}
        verdict = _calculate_threat_verdict(stats)
        assert "SUSPICIOUS" in verdict
    
    def test_calculate_threat_verdict_undetected(self):
        """Test threat verdict calculation for undetected file."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        stats = {"malicious": 0, "suspicious": 0, "undetected": 50}
        verdict = _calculate_threat_verdict(stats)
        assert verdict == "UNDETECTED"
    
    def test_calculate_threat_verdict_clean(self):
        """Test threat verdict calculation for clean file."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        stats = {"malicious": 0, "suspicious": 0, "undetected": 0}
        verdict = _calculate_threat_verdict(stats)
        assert verdict == "CLEAN"


class TestVirusTotalFileReport:
    """Test virustotal_file_report tool."""
    
    def test_file_report_success(self, mock_runtime, mock_vt_response):
        """Test successful file hash lookup."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vt_response
            mock_get.return_value = mock_response
            
            result = virustotal_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["hash"] == "44d88612fea8a8f36de82e1278abb02f"
            assert "threat_verdict" in parsed
            assert parsed["user_id"] == "test_user_001"
    
    def test_file_report_no_config(self, mock_runtime_no_config):
        """Test file report without API key."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        result = virustotal_file_report.func(mock_runtime_no_config, "44d88612fea8a8f36de82e1278abb02f")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()
    
    def test_file_report_invalid_api_key(self, mock_runtime):
        """Test file report with invalid API key."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            result = virustotal_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "Invalid" in parsed["message"]
    
    def test_file_report_not_found(self, mock_runtime):
        """Test file report for hash not in database."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = virustotal_file_report.func(mock_runtime, "nonexistent_hash")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found" in parsed["message"].lower()
    
    def test_file_report_timeout(self, mock_runtime):
        """Test file report with network timeout."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            from requests.exceptions import Timeout
            mock_get.side_effect = Timeout("Request timeout")
            
            result = virustotal_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "timeout" in parsed["message"].lower()
    
    def test_file_report_invalid_hash_format(self, mock_runtime, mock_vt_response):
        """Test file report with invalid hash format."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        # VirusTotal API will handle invalid hash format
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid hash format"
            mock_get.return_value = mock_response
            
            result = virustotal_file_report.func(mock_runtime, "invalid_hash")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"


class TestVirusTotalURLReport:
    """Test virustotal_url_report tool."""
    
    def test_url_report_success(self, mock_runtime, mock_vt_response):
        """Test successful URL lookup."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vt_response
            mock_get.return_value = mock_response
            
            result = virustotal_url_report.func(mock_runtime, "https://example.com")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["url"] == "https://example.com"
            assert "threat_verdict" in parsed
    
    def test_url_report_no_config(self, mock_runtime_no_config):
        """Test URL report without API key."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        result = virustotal_url_report.func(mock_runtime_no_config, "https://example.com")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()
    
    def test_url_report_not_found(self, mock_runtime):
        """Test URL report for URL not in database."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = virustotal_url_report.func(mock_runtime, "https://nonexistent.com")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found" in parsed["message"].lower()


class TestVirusTotalDomainReport:
    """Test virustotal_domain_report tool."""
    
    def test_domain_report_success(self, mock_runtime, mock_vt_response):
        """Test successful domain lookup."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vt_response
            mock_get.return_value = mock_response
            
            result = virustotal_domain_report.func(mock_runtime, "example.com")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["domain"] == "example.com"
            assert "threat_verdict" in parsed
    
    def test_domain_report_no_config(self, mock_runtime_no_config):
        """Test domain report without API key."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        result = virustotal_domain_report.func(mock_runtime_no_config, "example.com")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()


class TestVirusTotalIPReport:
    """Test virustotal_ip_report tool."""
    
    def test_ip_report_success(self, mock_runtime, mock_vt_response):
        """Test successful IP address lookup."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        mock_vt_response["data"]["attributes"]["country"] = "US"
        mock_vt_response["data"]["attributes"]["asn"] = 15169
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vt_response
            mock_get.return_value = mock_response
            
            result = virustotal_ip_report.func(mock_runtime, "8.8.8.8")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["ip_address"] == "8.8.8.8"
            assert "country" in parsed
            assert "asn" in parsed
            assert "threat_verdict" in parsed
    
    def test_ip_report_no_config(self, mock_runtime_no_config):
        """Test IP report without API key."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        result = virustotal_ip_report.func(mock_runtime_no_config, "8.8.8.8")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()


class TestVirusTotalScanURL:
    """Test scan_url tool."""
    
    def test_scan_url_success(self, mock_runtime):
        """Test successful URL submission for scanning."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        mock_response_data = {
            "data": {
                "id": "analysis-123",
                "type": "analysis"
            }
        }
        
        with patch('shared.modules.tools.ti.virus_total.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value = mock_response
            
            result = scan_url.func(mock_runtime, "https://example.com")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["url"] == "https://example.com"
            assert "analysis_id" in parsed
    
    def test_scan_url_no_config(self, mock_runtime_no_config):
        """Test URL scan without API key."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        result = scan_url.func(mock_runtime_no_config, "https://example.com")
        parsed = json.loads(result)
        
        assert parsed["status"] == "error"
        assert "not found in agent state" in parsed["message"].lower()
    
    def test_scan_url_api_error(self, mock_runtime):
        """Test URL scan with API error."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid URL format"
            mock_post.return_value = mock_response
            
            result = scan_url.func(mock_runtime, "invalid-url")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "API error" in parsed["message"]


class TestVirusTotalRealWorldScenarios:
    """Test real-world scenarios for VirusTotal tools."""
    
    def test_incident_response_workflow(self, mock_runtime, mock_vt_response):
        """Test complete incident response workflow."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.virus_total.requests.get') as mock_get, \
             patch('shared.modules.tools.ti.virus_total.requests.post') as mock_post:
            
            # Mock successful responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vt_response
            mock_get.return_value = mock_response
            
            mock_post_response = Mock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {"data": {"id": "analysis-123"}}
            mock_post.return_value = mock_post_response
            
            # Step 1: Check file hash
            file_result = virustotal_file_report.func(mock_runtime, "44d88612fea8a8f36de82e1278abb02f")
            assert json.loads(file_result)["status"] == "success"
            
            # Step 2: Check URL
            url_result = virustotal_url_report.func(mock_runtime, "https://suspicious-site.com")
            assert json.loads(url_result)["status"] == "success"
            
            # Step 3: Check domain
            domain_result = virustotal_domain_report.func(mock_runtime, "suspicious-site.com")
            assert json.loads(domain_result)["status"] == "success"
            
            # Step 4: Check IP
            ip_result = virustotal_ip_report.func(mock_runtime, "192.168.1.1")
            assert json.loads(ip_result)["status"] == "success"
            
            # Step 5: Submit new URL for scanning
            scan_result = scan_url.func(mock_runtime, "https://new-suspicious-site.com")
            assert json.loads(scan_result)["status"] == "success"
    
    def test_threat_verdict_calculation_scenarios(self):
        """Test threat verdict calculation with various scenarios."""
        if not VIRUSTOTAL_TOOLS_AVAILABLE:
            pytest.skip(f"VirusTotal tools not available: {IMPORT_ERROR}")
        
        # High confidence malicious
        stats1 = {"malicious": 50, "suspicious": 5, "undetected": 10}
        verdict1 = _calculate_threat_verdict(stats1)
        assert "MALICIOUS" in verdict1
        
        # Low confidence suspicious
        stats2 = {"malicious": 0, "suspicious": 1, "undetected": 60}
        verdict2 = _calculate_threat_verdict(stats2)
        assert "SUSPICIOUS" in verdict2
        
        # Clean file
        stats3 = {"malicious": 0, "suspicious": 0, "undetected": 0, "harmless": 70}
        verdict3 = _calculate_threat_verdict(stats3)
        assert verdict3 == "CLEAN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

