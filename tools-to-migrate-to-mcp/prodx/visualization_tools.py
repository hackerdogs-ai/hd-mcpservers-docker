"""
Simplified Visualization Tools for LangChain Agents

This module provides simple, focused LangChain tools for creating Plotly charts.
Each chart type is a separate tool, following the pattern from virus_total.py.

Tools:
- create_line_chart: Create line charts for time series and trends
- create_bar_chart: Create bar charts for comparisons
- create_pie_chart: Create pie charts for composition/proportions
- create_scatter_plot: Create scatter plots for relationships
- create_heatmap: Create heatmaps for correlation matrices
- create_histogram: Create histograms for distributions
- recommend_chart_type: Recommend the best chart type for given data
- create_chart_from_file: Create charts from Excel, CSV, or JSON files
"""

import json
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from langchain.tools import tool
from hd_logging import setup_logger

logger = setup_logger(__name__, log_file_path="logs/visualization_tools.log")

# Try to import required libraries
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("plotly not available. Visualization tools will not work.")

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    logger.warning("streamlit not available. Charts cannot be displayed.")


def _to_dataframe(data: Any) -> Optional[pd.DataFrame]:
    """Convert data to pandas DataFrame."""
    try:
        if isinstance(data, pd.DataFrame):
            return data
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            # If dict has list values, treat as columnar data
            if all(isinstance(v, list) for v in data.values()):
                return pd.DataFrame(data)
            # Otherwise, treat as single row
            return pd.DataFrame([data])
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return _to_dataframe(parsed)
            except json.JSONDecodeError:
                return None
        return None
    except Exception as e:
        logger.error(f"Error converting data to DataFrame: {e}", exc_info=True)
        return None


def _display_chart(fig, chart_type: str) -> str:
    """Display chart in Streamlit if available."""
    if STREAMLIT_AVAILABLE:
        try:
            st.plotly_chart(fig, width="stretch")
            return json.dumps({
                "status": "success",
                "message": f"{chart_type} displayed successfully",
                "chart_type": chart_type
            })
        except Exception as e:
            logger.error(f"Error displaying chart: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Error displaying chart: {str(e)}"
            })
    else:
        # Return figure as JSON if Streamlit not available
        return json.dumps({
            "status": "success",
            "chart_type": chart_type,
            "figure": fig.to_json()
        })


# --- Individual Chart Tools ---

@tool
def create_line_chart(data: Union[Dict, List, str], x: str, y: str, title: Optional[str] = None) -> str:
    """
    Create a line chart for time series data or trends over time.
    
    When to use:
        - Showing trends over time (e.g., security incidents over months)
        - Displaying time series data
        - Comparing multiple series over time
        - Showing changes in values over a continuous axis
    
    Args:
        data: Data to visualize. Can be:
            - List of dicts: [{"date": "2024-01", "value": 10}, ...]
            - Dict with lists: {"date": ["2024-01", ...], "value": [10, ...]}
            - JSON string: '{"date": [...], "value": [...]}'
        x: Column name for X-axis (e.g., "date", "time", "month")
        y: Column name for Y-axis (e.g., "count", "value", "incidents")
        title: Optional chart title
    
    Returns:
        JSON string with status and chart information
    """
    if not PLOTLY_AVAILABLE:
        return json.dumps({"status": "error", "message": "plotly library not installed"})
    
    try:
        df = _to_dataframe(data)
        if df is None or df.empty:
            return json.dumps({"status": "error", "message": "Could not convert data to DataFrame or data is empty"})
        
        if x not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{x}' not found in data"})
        if y not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{y}' not found in data"})
        
        fig = px.line(df, x=x, y=y, title=title or "Line Chart")
        return _display_chart(fig, "line_chart")
    
    except Exception as e:
        logger.error(f"Error creating line chart: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error creating line chart: {str(e)}"})


@tool
def create_bar_chart(data: Union[Dict, List, str], x: str, y: str, title: Optional[str] = None) -> str:
    """
    Create a bar chart for comparing categories or values.
    
    When to use:
        - Comparing values across categories (e.g., vulnerabilities by severity)
        - Showing rankings or comparisons
        - Displaying categorical data with numeric values
    
    Args:
        data: Data to visualize (list of dicts, dict with lists, or JSON string)
        x: Column name for X-axis (categories, e.g., "severity", "category")
        y: Column name for Y-axis (values, e.g., "count", "total")
        title: Optional chart title
    
    Returns:
        JSON string with status and chart information
    """
    if not PLOTLY_AVAILABLE:
        return json.dumps({"status": "error", "message": "plotly library not installed"})
    
    try:
        df = _to_dataframe(data)
        if df is None or df.empty:
            return json.dumps({"status": "error", "message": "Could not convert data to DataFrame or data is empty"})
        
        if x not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{x}' not found in data"})
        if y not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{y}' not found in data"})
        
        fig = px.bar(df, x=x, y=y, title=title or "Bar Chart")
        return _display_chart(fig, "bar_chart")
    
    except Exception as e:
        logger.error(f"Error creating bar chart: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error creating bar chart: {str(e)}"})


@tool
def create_pie_chart(data: Union[Dict, List, str], names: str, values: str, title: Optional[str] = None) -> str:
    """
    Create a pie chart for showing proportions or composition.
    
    When to use:
        - Showing proportions or percentages (e.g., threat distribution)
        - Displaying composition of a whole
        - Comparing parts to the whole
    
    Args:
        data: Data to visualize (list of dicts, dict with lists, or JSON string)
        names: Column name for pie slice labels (e.g., "threat_type", "category")
        values: Column name for pie slice values (e.g., "count", "percentage")
        title: Optional chart title
    
    Returns:
        JSON string with status and chart information
    """
    if not PLOTLY_AVAILABLE:
        return json.dumps({"status": "error", "message": "plotly library not installed"})
    
    try:
        df = _to_dataframe(data)
        if df is None or df.empty:
            return json.dumps({"status": "error", "message": "Could not convert data to DataFrame or data is empty"})
        
        if names not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{names}' not found in data"})
        if values not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{values}' not found in data"})
        
        fig = px.pie(df, names=names, values=values, title=title or "Pie Chart")
        return _display_chart(fig, "pie_chart")
    
    except Exception as e:
        logger.error(f"Error creating pie chart: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error creating pie chart: {str(e)}"})


@tool
def create_scatter_plot(data: Union[Dict, List, str], x: str, y: str, title: Optional[str] = None) -> str:
    """
    Create a scatter plot for showing relationships between two variables.
    
    When to use:
        - Showing correlation between two numeric variables
        - Displaying relationships in data
        - Identifying patterns or clusters in data
    
    Args:
        data: Data to visualize (list of dicts, dict with lists, or JSON string)
        x: Column name for X-axis (numeric variable)
        y: Column name for Y-axis (numeric variable)
        title: Optional chart title
    
    Returns:
        JSON string with status and chart information
    """
    if not PLOTLY_AVAILABLE:
        return json.dumps({"status": "error", "message": "plotly library not installed"})
    
    try:
        df = _to_dataframe(data)
        if df is None or df.empty:
            return json.dumps({"status": "error", "message": "Could not convert data to DataFrame or data is empty"})
        
        if x not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{x}' not found in data"})
        if y not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{y}' not found in data"})
        
        fig = px.scatter(df, x=x, y=y, title=title or "Scatter Plot")
        return _display_chart(fig, "scatter_plot")
    
    except Exception as e:
        logger.error(f"Error creating scatter plot: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error creating scatter plot: {str(e)}"})


@tool
def create_heatmap(data: Union[Dict, List, str], title: Optional[str] = None) -> str:
    """
    Create a heatmap showing correlation matrix or 2D data patterns.
    
    When to use:
        - Showing correlation between multiple numeric variables
        - Displaying 2D data patterns
        - Visualizing relationships in a matrix format
    
    Args:
        data: Data to visualize (list of dicts, dict with lists, or JSON string)
            Should contain multiple numeric columns for correlation
        title: Optional chart title
    
    Returns:
        JSON string with status and chart information
    """
    if not PLOTLY_AVAILABLE:
        return json.dumps({"status": "error", "message": "plotly library not installed"})
    
    try:
        df = _to_dataframe(data)
        if df is None or df.empty:
            return json.dumps({"status": "error", "message": "Could not convert data to DataFrame or data is empty"})
        
        # Select only numeric columns
        numeric_df = df.select_dtypes(include=['number'])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return json.dumps({"status": "error", "message": "Heatmap requires at least 2 numeric columns"})
        
        # Compute correlation matrix
        corr_matrix = numeric_df.corr()
        fig = px.imshow(corr_matrix, title=title or "Correlation Heatmap", aspect="auto")
        return _display_chart(fig, "heatmap")
    
    except Exception as e:
        logger.error(f"Error creating heatmap: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error creating heatmap: {str(e)}"})


@tool
def create_histogram(data: Union[Dict, List, str], column: str, title: Optional[str] = None) -> str:
    """
    Create a histogram showing distribution of a numeric variable.
    
    When to use:
        - Showing distribution of a single numeric variable
        - Displaying frequency of values
        - Understanding data distribution patterns
    
    Args:
        data: Data to visualize (list of dicts, dict with lists, or JSON string)
        column: Column name for the numeric variable to analyze
        title: Optional chart title
    
    Returns:
        JSON string with status and chart information
    """
    if not PLOTLY_AVAILABLE:
        return json.dumps({"status": "error", "message": "plotly library not installed"})
    
    try:
        df = _to_dataframe(data)
        if df is None or df.empty:
            return json.dumps({"status": "error", "message": "Could not convert data to DataFrame or data is empty"})
        
        if column not in df.columns:
            return json.dumps({"status": "error", "message": f"Column '{column}' not found in data"})
        
        if not pd.api.types.is_numeric_dtype(df[column]):
            return json.dumps({"status": "error", "message": f"Column '{column}' must be numeric"})
        
        fig = px.histogram(df, x=column, title=title or "Histogram")
        return _display_chart(fig, "histogram")
    
    except Exception as e:
        logger.error(f"Error creating histogram: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error creating histogram: {str(e)}"})


@tool
def recommend_chart_type(data: Union[Dict, List, str], description: Optional[str] = None) -> str:
    """
    Recommend the best chart type for the given data.
    
    Analyzes the data structure and provides a recommendation for the most appropriate
    chart type based on the number of columns, data types, and user description.
    
    When to use:
        - User asks "what chart should I use?" or "how should I visualize this?"
        - Need guidance on best visualization approach
        - Analyzing data structure to suggest visualization
    
    Args:
        data: Data to analyze (list of dicts, dict with lists, or JSON string)
        description: Optional description of what user wants to show (e.g., "trends over time", "compare categories")
    
    Returns:
        JSON string with recommended chart type and reasoning
    """
    try:
        df = _to_dataframe(data)
        if df is None or df.empty:
            return json.dumps({
                "status": "error",
                "message": "Could not convert data to DataFrame or data is empty"
            })
        
        num_cols = len(df.columns)
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=['number']).columns.tolist()
        
        recommendation = None
        reasoning = []
        
        # Analyze based on description
        if description:
            desc_lower = description.lower()
            if any(word in desc_lower for word in ["time", "trend", "over time", "temporal"]):
                recommendation = "line_chart"
                reasoning.append("Description suggests time series data")
            elif any(word in desc_lower for word in ["compare", "comparison", "versus", "vs"]):
                recommendation = "bar_chart"
                reasoning.append("Description suggests comparison")
            elif any(word in desc_lower for word in ["proportion", "percentage", "composition", "part of"]):
                recommendation = "pie_chart"
                reasoning.append("Description suggests proportions")
            elif any(word in desc_lower for word in ["relationship", "correlation", "scatter"]):
                recommendation = "scatter_plot"
                reasoning.append("Description suggests relationship analysis")
            elif any(word in desc_lower for word in ["distribution", "frequency", "histogram"]):
                recommendation = "histogram"
                reasoning.append("Description suggests distribution analysis")
        
        # Analyze based on data structure
        if not recommendation:
            if num_cols == 1:
                if len(numeric_cols) == 1:
                    recommendation = "histogram"
                    reasoning.append("Single numeric column - good for distribution")
                else:
                    recommendation = "bar_chart"
                    reasoning.append("Single categorical column - good for counts")
            elif num_cols == 2:
                if len(numeric_cols) == 2:
                    recommendation = "scatter_plot"
                    reasoning.append("Two numeric columns - good for relationships")
                elif len(numeric_cols) == 1 and len(categorical_cols) == 1:
                    recommendation = "bar_chart"
                    reasoning.append("One category and one value - good for comparison")
            elif num_cols >= 3:
                if len(numeric_cols) >= 2:
                    recommendation = "heatmap"
                    reasoning.append("Multiple numeric columns - good for correlation")
                else:
                    recommendation = "bar_chart"
                    reasoning.append("Multiple columns - bar chart for comparison")
        
        # Check for time-like columns
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ["date", "time", "month", "year", "day"]):
                if not recommendation or recommendation == "bar_chart":
                    recommendation = "line_chart"
                    reasoning.append(f"Found time-like column '{col}' - good for trends")
                break
        
        return json.dumps({
            "status": "success",
            "recommended_chart": recommendation or "bar_chart",
            "reasoning": "; ".join(reasoning) if reasoning else "Default recommendation",
            "data_summary": {
                "total_columns": num_cols,
                "numeric_columns": len(numeric_cols),
                "categorical_columns": len(categorical_cols),
                "rows": len(df)
            }
        })
    
    except Exception as e:
        logger.error(f"Error recommending chart type: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error analyzing data: {str(e)}"})


@tool
def create_chart_from_file(file_path: str, file_type: str, chart_type: str, x: Optional[str] = None, y: Optional[str] = None, title: Optional[str] = None) -> str:
    """
    Create a chart from data in a file (Excel, CSV, or JSON).
    
    When to use:
        - User provides a file and wants to visualize it
        - Need to read data from file and create chart
        - Analyzing file data visually
    
    Args:
        file_path: Path to file or base64-encoded file data
        file_type: File type - "excel", "csv", or "json"
        chart_type: Chart type - "line_chart", "bar_chart", "pie_chart", "scatter_plot", "heatmap", or "histogram"
        x: Column name for X-axis (required for line, bar, scatter)
        y: Column name for Y-axis (required for line, bar, scatter)
        title: Optional chart title
    
    Returns:
        JSON string with status and chart information
    """
    if not PLOTLY_AVAILABLE:
        return json.dumps({"status": "error", "message": "plotly library not installed"})
    
    try:
        import base64
        import io
        
        # Read file
        df = None
        if file_type.lower() == "excel":
            try:
                import openpyxl
            except ImportError:
                return json.dumps({"status": "error", "message": "openpyxl required for Excel files. Install with: pip install openpyxl"})
            
            try:
                # Try base64 decode
                try:
                    file_bytes = base64.b64decode(file_path)
                    file_obj = io.BytesIO(file_bytes)
                    df = pd.read_excel(file_obj)
                except Exception:
                    df = pd.read_excel(file_path)
            except Exception as e:
                return json.dumps({"status": "error", "message": f"Error reading Excel file: {str(e)}"})
        
        elif file_type.lower() == "csv":
            try:
                try:
                    file_bytes = base64.b64decode(file_path)
                    file_obj = io.BytesIO(file_bytes)
                    df = pd.read_csv(file_obj)
                except Exception:
                    df = pd.read_csv(file_path)
            except Exception as e:
                return json.dumps({"status": "error", "message": f"Error reading CSV file: {str(e)}"})
        
        elif file_type.lower() == "json":
            try:
                try:
                    file_bytes = base64.b64decode(file_path)
                    json_data = json.loads(file_bytes.decode('utf-8'))
                except Exception:
                    with open(file_path, 'r') as f:
                        json_data = json.load(f)
                df = pd.json_normalize(json_data)
            except Exception as e:
                return json.dumps({"status": "error", "message": f"Error reading JSON file: {str(e)}"})
        
        else:
            return json.dumps({"status": "error", "message": f"Unsupported file type: {file_type}. Supported: excel, csv, json"})
        
        if df is None or df.empty:
            return json.dumps({"status": "error", "message": "File is empty or contains no data"})
        
        # Convert to dict format for chart tools
        data_dict = df.to_dict('records')
        
        # Call appropriate chart tool
        chart_type_lower = chart_type.lower()
        if chart_type_lower == "line_chart":
            if not x or not y:
                return json.dumps({"status": "error", "message": "line_chart requires x and y parameters"})
            return create_line_chart(data_dict, x, y, title)
        elif chart_type_lower == "bar_chart":
            if not x or not y:
                return json.dumps({"status": "error", "message": "bar_chart requires x and y parameters"})
            return create_bar_chart(data_dict, x, y, title)
        elif chart_type_lower == "pie_chart":
            if not x or not y:
                return json.dumps({"status": "error", "message": "pie_chart requires names and values parameters (use x for names, y for values)"})
            return create_pie_chart(data_dict, x, y, title)
        elif chart_type_lower == "scatter_plot":
            if not x or not y:
                return json.dumps({"status": "error", "message": "scatter_plot requires x and y parameters"})
            return create_scatter_plot(data_dict, x, y, title)
        elif chart_type_lower == "heatmap":
            return create_heatmap(data_dict, title)
        elif chart_type_lower == "histogram":
            if not x:
                return json.dumps({"status": "error", "message": "histogram requires column parameter (use x)"})
            return create_histogram(data_dict, x, title)
        else:
            return json.dumps({"status": "error", "message": f"Unsupported chart type: {chart_type}. Supported: line_chart, bar_chart, pie_chart, scatter_plot, heatmap, histogram"})
    
    except Exception as e:
        logger.error(f"Error creating chart from file: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Error creating chart from file: {str(e)}"})
