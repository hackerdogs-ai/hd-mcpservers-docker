# excel-tools-mcp

MCP server for reading, writing, and analyzing Excel/CSV spreadsheets.

## Tools

| Tool | Description |
|------|------------|
| read_excel | Read Excel file to JSON |
| read_csv | Read CSV file to JSON |
| describe_spreadsheet | Summary statistics |
| list_sheets | List Excel workbook sheets |
| write_csv | Write data to CSV |

## Quick Start

```bash
docker build -t excel-tools-mcp .
docker run -p 8505:8505 -e MCP_TRANSPORT=streamable-http excel-tools-mcp
```
