# visualization-tools-mcp

MCP server for generating charts and graphs using matplotlib.

## Tools

| Tool | Description |
|------|------------|
| create_bar_chart | Create a bar chart from JSON data |
| create_line_chart | Create a line chart (single or multi-series) |
| create_pie_chart | Create a pie chart |
| create_scatter_plot | Create a scatter plot |

## Quick Start

```bash
docker build -t visualization-tools-mcp .
docker run -p 8506:8506 -e MCP_TRANSPORT=streamable-http visualization-tools-mcp
```
