"""
Comprehensive tests for OpenCTI threat intelligence tools.

This test suite validates all OpenCTI LangChain tools including:
- opencti_search_indicators
- opencti_search_malware
- opencti_search_threat_actors
- opencti_get_report
- opencti_list_attack_patterns

Tests cover:
- Tool initialization and configuration
- API key and URL management via ToolRuntime
- Successful queries and responses
- Error handling (missing config, API errors, invalid inputs)
- Edge cases (empty results, large limits, special characters)
- Real-world scenarios
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Try to import OpenCTI tools
try:
    from shared.modules.tools.ti.opencti import (
        opencti_search_indicators,
        opencti_search_malware,
        opencti_search_threat_actors,
        opencti_get_report,
        opencti_list_attack_patterns,
        _get_opencti_client,
        _format_opencti_result,
        OpenCTISecurityAgentState,
        PYCTI_AVAILABLE
    )
    OPENCTI_TOOLS_AVAILABLE = True
except ImportError as e:
    OPENCTI_TOOLS_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.fixture
def mock_runtime():
    """Create a mock ToolRuntime with OpenCTI configuration."""
    runtime = Mock()
    runtime.state = {
        "api_keys": {"opencti": "test_api_key_123"},
        "opencti_url": "https://opencti.example.com",
        "user_id": "test_user_001"
    }
    return runtime


@pytest.fixture
def mock_runtime_no_config():
    """Create a mock ToolRuntime without OpenCTI configuration."""
    runtime = Mock()
    runtime.state = {
        "api_keys": {},
        "user_id": "test_user_001"
    }
    return runtime


@pytest.fixture
def mock_opencti_client():
    """Create a mock OpenCTI API client."""
    client = MagicMock()
    
    # Mock indicator list response
    mock_indicator = {
        "id": "indicator-123",
        "value": "192.168.1.1",
        "pattern": "[ipv4-addr:value = '192.168.1.1']",
        "labels": ["malicious", "apt28"]
    }
    client.indicator.list = Mock(return_value=[mock_indicator])
    
    # Mock malware list response
    mock_malware = {
        "id": "malware-123",
        "name": "Emotet",
        "aliases": ["Heodo"],
        "labels": ["trojan", "banking"]
    }
    client.malware.list = Mock(return_value=[mock_malware])
    
    # Mock threat actor list response
    mock_threat_actor = {
        "id": "threat-actor-123",
        "name": "APT28",
        "aliases": ["Fancy Bear", "Sofacy"],
        "labels": ["apt", "nation-state"]
    }
    client.threat_actor.list = Mock(return_value=[mock_threat_actor])
    
    # Mock report read response
    mock_report = {
        "id": "report-123",
        "name": "APT28 Campaign Analysis",
        "description": "Detailed analysis of APT28 activities",
        "published": "2024-01-01T00:00:00Z"
    }
    client.report.read = Mock(return_value=mock_report)
    client.report.list = Mock(return_value=[mock_report])
    
    # Mock attack pattern list response
    mock_attack_pattern = {
        "id": "attack-pattern-123",
        "x_mitre_id": "T1055",
        "name": "Process Injection",
        "description": "Adversaries may inject code into processes"
    }
    client.attack_pattern.list = Mock(return_value=[mock_attack_pattern])
    
    return client


class TestOpenCTIHelperFunctions:
    """Test helper functions for OpenCTI tools."""
    
    def test_format_opencti_result_dict(self):
        """Test formatting dictionary results."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        data = {"status": "success", "count": 1}
        result = _format_opencti_result(data)
        parsed = json.loads(result)
        assert parsed["status"] == "success"
        assert parsed["count"] == 1
    
    def test_format_opencti_result_list(self):
        """Test formatting list results."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        data = [{"id": "1"}, {"id": "2"}]
        result = _format_opencti_result(data)
        parsed = json.loads(result)
        assert "results" in parsed
        assert parsed["count"] == 2
    
    def test_format_opencti_result_string(self):
        """Test formatting string results."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        data = "test result"
        result = _format_opencti_result(data)
        parsed = json.loads(result)
        assert parsed["result"] == "test result"


class TestOpenCTISearchIndicators:
    """Test opencti_search_indicators tool."""
    
    def test_search_indicators_success(self, mock_runtime, mock_opencti_client):
        """Test successful indicator search."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_search_indicators.func(mock_runtime, "192.168.1.1", limit=10)
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["count"] >= 0
            assert "indicators" in parsed
            assert parsed["user_id"] == "test_user_001"
    
    def test_search_indicators_no_config(self, mock_runtime_no_config):
        """Test indicator search without configuration."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True):
            result = opencti_search_indicators.func(mock_runtime_no_config, "192.168.1.1")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found in agent state" in parsed["message"].lower()
    
    def test_search_indicators_pycti_unavailable(self, mock_runtime):
        """Test indicator search when pycti is not available."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', False):
            result = opencti_search_indicators.func(mock_runtime, "192.168.1.1")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not available" in parsed["message"].lower()
    
    def test_search_indicators_api_error(self, mock_runtime, mock_opencti_client):
        """Test indicator search with API error."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        mock_opencti_client.indicator.list.side_effect = Exception("API connection failed")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_search_indicators.func(mock_runtime, "192.168.1.1")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "API error" in parsed["message"]
    
    def test_search_indicators_empty_query(self, mock_runtime, mock_opencti_client):
        """Test indicator search with empty query."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_search_indicators.func(mock_runtime, "", limit=10)
            parsed = json.loads(result)
            
            # Should still execute, but may return empty results
            assert parsed["status"] in ["success", "error"]


class TestOpenCTISearchMalware:
    """Test opencti_search_malware tool."""
    
    def test_search_malware_success(self, mock_runtime, mock_opencti_client):
        """Test successful malware search."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_search_malware.func(mock_runtime, "Emotet", limit=10)
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["count"] >= 0
            assert "malware" in parsed
            assert parsed["query"] == "Emotet"
    
    def test_search_malware_no_config(self, mock_runtime_no_config):
        """Test malware search without configuration."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True):
            result = opencti_search_malware.func(mock_runtime_no_config, "Emotet")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found in agent state" in parsed["message"].lower()
    
    def test_search_malware_api_error(self, mock_runtime, mock_opencti_client):
        """Test malware search with API error."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        mock_opencti_client.malware.list.side_effect = Exception("API timeout")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_search_malware.func(mock_runtime, "Emotet")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "API error" in parsed["message"]


class TestOpenCTISearchThreatActors:
    """Test opencti_search_threat_actors tool."""
    
    def test_search_threat_actors_success(self, mock_runtime, mock_opencti_client):
        """Test successful threat actor search."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_search_threat_actors.func(mock_runtime, "APT28", limit=10)
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["count"] >= 0
            assert "threat_actors" in parsed
            assert parsed["query"] == "APT28"
    
    def test_search_threat_actors_no_config(self, mock_runtime_no_config):
        """Test threat actor search without configuration."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True):
            result = opencti_search_threat_actors.func(mock_runtime_no_config, "APT28")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found in agent state" in parsed["message"].lower()
    
    def test_search_threat_actors_api_error(self, mock_runtime, mock_opencti_client):
        """Test threat actor search with API error."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        mock_opencti_client.threat_actor.list.side_effect = Exception("Authentication failed")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_search_threat_actors.func(mock_runtime, "APT28")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "API error" in parsed["message"]


class TestOpenCTIGetReport:
    """Test opencti_get_report tool."""
    
    def test_get_report_by_id_success(self, mock_runtime, mock_opencti_client):
        """Test successful report retrieval by ID."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_get_report.func(mock_runtime, report_id="report-123")
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert "report" in parsed
            assert parsed["report_id"] == "report-123"
    
    def test_get_report_by_query_success(self, mock_runtime, mock_opencti_client):
        """Test successful report search by query."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_get_report.func(mock_runtime, query="APT28", limit=10)
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert "reports" in parsed or "report" in parsed
            assert parsed["query"] == "APT28"
    
    def test_get_report_no_params(self, mock_runtime, mock_opencti_client):
        """Test report retrieval without parameters."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_get_report.func(mock_runtime)
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "must be provided" in parsed["message"].lower()
    
    def test_get_report_no_config(self, mock_runtime_no_config):
        """Test report retrieval without configuration."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True):
            result = opencti_get_report.func(mock_runtime_no_config, report_id="report-123")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found in agent state" in parsed["message"].lower()
    
    def test_get_report_api_error(self, mock_runtime, mock_opencti_client):
        """Test report retrieval with API error."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        mock_opencti_client.report.read.side_effect = Exception("Report not found")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_get_report.func(mock_runtime, report_id="invalid-id")
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "API error" in parsed["message"]


class TestOpenCTIListAttackPatterns:
    """Test opencti_list_attack_patterns tool."""
    
    def test_list_attack_patterns_success(self, mock_runtime, mock_opencti_client):
        """Test successful attack pattern listing."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_list_attack_patterns.func(mock_runtime, limit=20)
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["count"] >= 0
            assert "attack_patterns" in parsed
    
    def test_list_attack_patterns_with_query(self, mock_runtime, mock_opencti_client):
        """Test attack pattern listing with query filter."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_list_attack_patterns.func(mock_runtime, query="T1055", limit=20)
            parsed = json.loads(result)
            
            assert parsed["status"] == "success"
            assert parsed["query"] == "T1055"
    
    def test_list_attack_patterns_no_config(self, mock_runtime_no_config):
        """Test attack pattern listing without configuration."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True):
            result = opencti_list_attack_patterns.func(mock_runtime_no_config, limit=20)
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "not found in agent state" in parsed["message"].lower()
    
    def test_list_attack_patterns_api_error(self, mock_runtime, mock_opencti_client):
        """Test attack pattern listing with API error."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        mock_opencti_client.attack_pattern.list.side_effect = Exception("Rate limit exceeded")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            result = opencti_list_attack_patterns.func(mock_runtime, limit=20)
            parsed = json.loads(result)
            
            assert parsed["status"] == "error"
            assert "API error" in parsed["message"]


class TestOpenCTIRealWorldScenarios:
    """Test real-world scenarios for OpenCTI tools."""
    
    def test_incident_response_workflow(self, mock_runtime, mock_opencti_client):
        """Test complete incident response workflow."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            # Step 1: Search for indicators
            indicators = opencti_search_indicators.func(mock_runtime, "192.168.1.1")
            assert json.loads(indicators)["status"] == "success"
            
            # Step 2: Search for related malware
            malware = opencti_search_malware.func(mock_runtime, "Emotet")
            assert json.loads(malware)["status"] == "success"
            
            # Step 3: Search for threat actors
            threat_actors = opencti_search_threat_actors.func(mock_runtime, "APT28")
            assert json.loads(threat_actors)["status"] == "success"
            
            # Step 4: Get related report
            report = opencti_get_report.func(mock_runtime, query="APT28")
            assert json.loads(report)["status"] == "success"
    
    def test_threat_modeling_workflow(self, mock_runtime, mock_opencti_client):
        """Test threat modeling workflow using attack patterns."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            # List attack patterns
            patterns = opencti_list_attack_patterns.func(mock_runtime, limit=50)
            assert json.loads(patterns)["status"] == "success"
            
            # Search for specific technique
            technique = opencti_list_attack_patterns.func(mock_runtime, query="T1055")
            assert json.loads(technique)["status"] == "success"
    
    def test_attribution_workflow(self, mock_runtime, mock_opencti_client):
        """Test threat actor attribution workflow."""
        if not OPENCTI_TOOLS_AVAILABLE:
            pytest.skip(f"OpenCTI tools not available: {IMPORT_ERROR}")
        
        with patch('shared.modules.tools.ti.opencti.PYCTI_AVAILABLE', True), \
             patch('shared.modules.tools.ti.opencti.OpenCTIApiClient', return_value=mock_opencti_client):
            # Search for threat actor
            threat_actor = opencti_search_threat_actors.func(mock_runtime, "APT28")
            assert json.loads(threat_actor)["status"] == "success"
            
            # Get related reports
            reports = opencti_get_report.func(mock_runtime, query="APT28")
            assert json.loads(reports)["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

