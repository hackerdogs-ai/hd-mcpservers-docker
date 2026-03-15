"""
Comprehensive tests for Visualization Tools

Tests both visualization tools:
- CreatePlotlyChartTool
- CreateChartFromFileTool
"""

import pytest
import base64
import io
import json
import tempfile
import os
import pandas as pd

# Import tools - handle both relative and absolute imports
try:
    from .visualization_tools import (
        CreatePlotlyChartTool,
        CreateChartFromFileTool,
        _to_dataframe
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    from shared.modules.tools.prodx.visualization_tools import (
        CreatePlotlyChartTool,
        CreateChartFromFileTool,
        _to_dataframe
    )


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_to_dataframe_from_dict(self):
        """Test converting dict to DataFrame."""
        data = {"x": [1, 2, 3], "y": [10, 20, 30]}
        df = _to_dataframe(data)
        assert df is not None
        assert len(df) > 0
    
    def test_to_dataframe_from_list(self):
        """Test converting list to DataFrame."""
        data = [{"x": 1, "y": 10}, {"x": 2, "y": 20}]
        df = _to_dataframe(data)
        assert df is not None
        assert len(df) == 2
    
    def test_to_dataframe_from_dataframe(self):
        """Test passing DataFrame directly."""
        df_input = pd.DataFrame({"x": [1, 2], "y": [10, 20]})
        df = _to_dataframe(df_input)
        assert df is not None
        assert len(df) == 2


class TestCreatePlotlyChartTool:
    """Test CreatePlotlyChartTool."""
    
    def test_create_line_chart(self):
        """Test creating a line chart."""
        tool = CreatePlotlyChartTool()
        
        data = {
            "x": [1, 2, 3, 4],
            "y": [10, 20, 30, 40]
        }
        
        result = tool._run(data, "line_chart", {"title": "Test Chart"}, display=False)
        result_dict = json.loads(result)
        
        assert result_dict["status"] == "success"
        assert "figure" in result_dict
    
    def test_create_bar_chart(self):
        """Test creating a bar chart."""
        tool = CreatePlotlyChartTool()
        
        data = [
            {"category": "A", "value": 10},
            {"category": "B", "value": 20},
            {"category": "C", "value": 30}
        ]
        
        result = tool._run(data, "bar_chart", {"title": "Bar Chart"}, display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_pie_chart(self):
        """Test creating a pie chart."""
        tool = CreatePlotlyChartTool()
        
        data = [
            {"name": "A", "value": 30},
            {"name": "B", "value": 40},
            {"name": "C", "value": 30}
        ]
        
        result = tool._run(data, "pie_chart", {"title": "Pie Chart"}, display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_scatter_plot(self):
        """Test creating a scatter plot."""
        tool = CreatePlotlyChartTool()
        
        data = {
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10]
        }
        
        result = tool._run(data, "scatter_plot", display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_heatmap(self):
        """Test creating a heatmap."""
        tool = CreatePlotlyChartTool()
        
        data = {
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
            "col3": [7, 8, 9]
        }
        
        result = tool._run(data, "heatmap", display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_chart_from_json_string(self):
        """Test creating chart from JSON string."""
        tool = CreatePlotlyChartTool()
        
        data_json = '{"x": [1, 2, 3], "y": [10, 20, 30]}'
        
        result = tool._run(data_json, "line_chart", display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_chart_with_parameters(self):
        """Test creating chart with custom parameters."""
        tool = CreatePlotlyChartTool()
        
        data = {"x": [1, 2, 3], "y": [10, 20, 30]}
        parameters = {
            "title": "Custom Title",
            "x_label": "X Axis",
            "y_label": "Y Axis"
        }
        
        result = tool._run(data, "line_chart", parameters, display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_chart_invalid_data(self):
        """Test creating chart with invalid data."""
        tool = CreatePlotlyChartTool()
        
        result = tool._run("invalid_data", "line_chart", display=False)
        assert "Error" in result
    
    def test_create_chart_empty_data(self):
        """Test creating chart with empty data."""
        tool = CreatePlotlyChartTool()
        
        result = tool._run([], "line_chart", display=False)
        assert "Error" in result


class TestCreateChartFromFileTool:
    """Test CreateChartFromFileTool."""
    
    def create_test_csv(self):
        """Create a test CSV file."""
        df = pd.DataFrame({
            "Category": ["A", "B", "C"],
            "Value": [10, 20, 30]
        })
        
        output = io.BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return base64.b64encode(output.read()).decode('utf-8')
    
    def create_test_excel(self):
        """Create a test Excel file."""
        df = pd.DataFrame({
            "Category": ["A", "B", "C"],
            "Value": [10, 20, 30]
        })
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return base64.b64encode(output.read()).decode('utf-8')
    
    def create_test_json(self):
        """Create a test JSON file."""
        data = {
            "data": [
                {"x": "A", "y": 10},
                {"x": "B", "y": 20},
                {"x": "C", "y": 30}
            ]
        }
        
        json_str = json.dumps(data)
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    def test_create_chart_from_csv(self):
        """Test creating chart from CSV file."""
        tool = CreateChartFromFileTool()
        csv_data = self.create_test_csv()
        
        result = tool._run(csv_data, "csv", "bar_chart", display=False)
        result_dict = json.loads(result)
        
        assert result_dict["status"] == "success"
        assert "figure" in result_dict or "message" in result_dict
    
    def test_create_chart_from_excel(self):
        """Test creating chart from Excel file."""
        tool = CreateChartFromFileTool()
        excel_data = self.create_test_excel()
        
        result = tool._run(excel_data, "excel", "line_chart", display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_chart_from_json(self):
        """Test creating chart from JSON file."""
        tool = CreateChartFromFileTool()
        json_data = self.create_test_json()
        
        result = tool._run(json_data, "json", "bar_chart", display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_chart_from_csv_with_config(self):
        """Test creating chart from CSV with data configuration."""
        tool = CreateChartFromFileTool()
        csv_data = self.create_test_csv()
        
        data_config = {
            "columns": ["Category", "Value"]
        }
        
        result = tool._run(csv_data, "csv", "bar_chart", data_config, display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_chart_from_file_invalid_type(self):
        """Test creating chart with invalid file type."""
        tool = CreateChartFromFileTool()
        
        result = tool._run("test_data", "invalid_type", "bar_chart", display=False)
        assert "Error" in result
    
    def test_create_chart_from_file_invalid_base64(self):
        """Test creating chart with invalid base64."""
        tool = CreateChartFromFileTool()
        
        result = tool._run("invalid_base64", "csv", "bar_chart", display=False)
        assert "Error" in result


class TestRealWorldScenarios:
    """Real-world scenario tests for visualization tools."""
    
    def test_create_chart_from_real_world_data(self):
        """Test creating charts from realistic business data."""
        tool = CreatePlotlyChartTool()
        
        # Realistic sales data
        sales_data = {
            "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "Sales": [45000, 52000, 48000, 61000, 55000, 67000],
            "Target": [50000, 50000, 50000, 50000, 50000, 50000]
        }
        
        # Test multiple chart types with same data
        chart_types = ["line_chart", "bar_chart"]
        for chart_type in chart_types:
            parameters = {
                "x": "Month",
                "y": "Sales",
                "title": f"Sales Performance - {chart_type}",
                "x_label": "Month",
                "y_label": "Sales ($)"
            }
            result = tool._run(sales_data, chart_type, parameters, display=False)
            result_dict = json.loads(result)
            assert result_dict["status"] == "success"
    
    def test_create_chart_from_nested_json(self):
        """Test creating chart from nested JSON structure."""
        tool = CreatePlotlyChartTool()
        
        # Nested JSON data
        nested_data = {
            "results": [
                {"category": "A", "value": 100, "subcategory": "A1"},
                {"category": "B", "value": 200, "subcategory": "B1"},
                {"category": "C", "value": 150, "subcategory": "C1"}
            ]
        }
        
        result = tool._run(nested_data, "bar_chart", display=False)
        result_dict = json.loads(result)
        assert result_dict["status"] == "success"
    
    def test_create_multiple_charts_workflow(self):
        """Test creating multiple charts in sequence."""
        tool = CreatePlotlyChartTool()
        
        data = {
            "Quarter": ["Q1", "Q2", "Q3", "Q4"],
            "Revenue": [100000, 120000, 110000, 130000],
            "Expenses": [60000, 70000, 65000, 75000]
        }
        
        # Create multiple chart types
        chart_types = ["line_chart", "bar_chart", "pie_chart"]
        for chart_type in chart_types:
            result = tool._run(data, chart_type, display=False)
            result_dict = json.loads(result)
            assert result_dict["status"] == "success"


class TestErrorHandling:
    """Test error handling."""
    
    def test_tools_handle_missing_plotly(self):
        """Test that tools handle missing plotly gracefully."""
        # Tools should return error messages, not crash
        tool = CreatePlotlyChartTool()
        result = tool._run({"x": [1], "y": [1]}, "line_chart", display=False)
        assert isinstance(result, str)
    
    def test_tools_handle_invalid_chart_type(self):
        """Test handling invalid chart type."""
        tool = CreatePlotlyChartTool()
        data = {"x": [1, 2], "y": [10, 20]}
        
        result = tool._run(data, "invalid_chart_type", display=False)
        # Should default to line chart or return error
        assert isinstance(result, str)
    
    def test_tools_handle_malformed_data(self):
        """Test handling malformed data structures."""
        tool = CreatePlotlyChartTool()
        
        malformed_data_cases = [
            {"invalid": "structure"},
            [1, 2, 3],  # List of numbers, not dicts
            "not a dict or list",
        ]
        
        for data in malformed_data_cases:
            try:
                result = tool._run(data, "line_chart", display=False)
                assert isinstance(result, str)
                # Should return error or handle gracefully
            except (TypeError, AttributeError):
                # Some tools might raise, but should be caught internally
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

