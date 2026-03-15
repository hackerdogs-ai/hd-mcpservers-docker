"""
Detailed Test Prompts for LLM Agent Testing

This file contains comprehensive, detailed prompts for testing each prodx tool
with LLM agents. These prompts are designed to be clear, specific, and test
various aspects of each tool's functionality.
"""

# Excel Tools Prompts

EXCEL_READ_PROMPTS = {
    "basic_read": """Read this Excel file and provide me with a summary:
1. List all sheet names
2. For each sheet, tell me:
   - Number of rows (excluding header)
   - Column names
   - Data types in each column
3. Show me the first 3 rows of data from the first sheet

File data: [BASE64_DATA]""",
    
    "read_with_formulas": """Read this Excel file and extract all formulas. For each formula:
1. Tell me which cell contains the formula
2. Show me the formula itself
3. Calculate and show the result value
4. Identify any cells that reference this formula

File data: [BASE64_DATA]""",
    
    "read_large_file": """This is a large Excel file with sales data. Please:
1. Read the file structure
2. Count total number of data rows across all sheets
3. Identify the sheet with the most data
4. Provide summary statistics for numeric columns (sum, average, min, max)
5. List any empty or null values

File data: [BASE64_DATA]"""
}

EXCEL_MODIFY_PROMPTS = {
    "add_multiple_rows": """Modify this Excel file by adding the following new rows:
Row 1: Product="Laptop", Category="Electronics", Price=999.99, Stock=50
Row 2: Product="Mouse", Category="Electronics", Price=29.99, Stock=200
Row 3: Product="Keyboard", Category="Electronics", Price=79.99, Stock=150

Add these rows after the existing data. Ensure all columns are properly filled.

File data: [BASE64_DATA]""",
    
    "update_with_formulas": """Update this Excel file:
1. Add a new column "Total" in column E
2. In each row, add a formula that calculates: Quantity * Price
3. Add a summary row at the bottom with:
   - "TOTAL" in column A
   - Sum of all quantities in column B
   - Sum of all prices in column C
   - Sum of all totals in column E

File data: [BASE64_DATA]""",
    
    "complex_modifications": """Perform these modifications to the Excel file:
1. Update all prices in column C by increasing them by 10%
2. Add a new column "Discount" (column D) with a 5% discount for items with quantity > 100
3. Add a column "Final Price" (column E) that calculates: Price * (1 - Discount/100)
4. Format the "Final Price" column to show 2 decimal places
5. Add a header row with bold formatting

File data: [BASE64_DATA]"""
}

EXCEL_CHART_PROMPTS = {
    "bar_chart_sales": """Create a bar chart in this Excel file showing monthly sales.
Requirements:
- Chart type: Bar chart
- Data range: A1:B13 (Month names in A, Sales values in B)
- Chart title: "Monthly Sales Report 2024"
- X-axis label: "Month"
- Y-axis label: "Sales ($)"
- Position the chart below the data

File data: [BASE64_DATA]""",
    
    "line_chart_trend": """Create a line chart showing the trend of revenue and expenses over time.
Requirements:
- Chart type: Line chart
- Data: Revenue in column B, Expenses in column C
- Show both lines on the same chart
- Add a legend
- Title: "Revenue vs Expenses Trend"
- Add data labels to the points

File data: [BASE64_DATA]""",
    
    "pie_chart_distribution": """Create a pie chart showing the distribution of sales by product category.
Requirements:
- Chart type: Pie chart
- Data: Category names in column A, Sales values in column B
- Title: "Sales by Category"
- Show percentages on each slice
- Use distinct colors for each category

File data: [BASE64_DATA]"""
}

EXCEL_SECURITY_PROMPTS = {
    "comprehensive_analysis": """Perform a comprehensive security analysis of this Excel file:
1. Check for external links to other files or websites
2. Identify any macros or VBA code
3. Look for hidden sheets or hidden rows/columns
4. Check for password protection
5. Identify any suspicious formulas (like INDIRECT, HYPERLINK)
6. Check for embedded objects or OLE links
7. Provide a security risk assessment with recommendations

File data: [BASE64_DATA]""",
    
    "data_privacy_check": """Analyze this Excel file for data privacy concerns:
1. Identify any personally identifiable information (PII)
2. Check for sensitive data like credit card numbers, SSNs, passwords
3. Look for hidden data in cells
4. Check for data in comments or notes
5. Identify any external data sources
6. Provide recommendations for data protection

File data: [BASE64_DATA]"""
}

# PowerPoint Tools Prompts

POWERPOINT_CREATE_PROMPTS = {
    "business_presentation": """Create a comprehensive business presentation titled "Annual Business Review 2024" with the following structure:

Slide 1 (Title): "Annual Business Review 2024" with subtitle "Year in Review"

Slide 2 (Content): "Executive Summary"
- Revenue: $5.2M (up 15% from last year)
- Expenses: $3.1M (down 5% from last year)
- Net Profit: $2.1M (up 30% from last year)
- Key Achievement: Expanded to 3 new markets

Slide 3 (Content): "Revenue Breakdown"
- Product Sales: $3.5M (67%)
- Services: $1.2M (23%)
- Licensing: $0.5M (10%)

Slide 4 (Content): "Top Performers"
- Product A: $1.5M
- Product B: $1.2M
- Product C: $0.8M

Slide 5 (Content): "Challenges & Solutions"
- Challenge: Supply chain disruptions
- Solution: Diversified suppliers
- Challenge: Market competition
- Solution: Enhanced product features

Slide 6 (Content): "2025 Goals"
- Increase revenue by 20%
- Expand to 2 additional markets
- Launch 3 new products
- Improve customer satisfaction to 95%

Please create this presentation with professional formatting.""",
    
    "technical_presentation": """Create a technical presentation about "Cloud Security Architecture" with:

Slide 1: Title slide "Cloud Security Architecture" with your name

Slide 2: "Overview"
- Multi-layered security approach
- Defense in depth strategy
- Zero trust principles

Slide 3: "Security Layers"
- Network security (firewalls, VPNs)
- Application security (WAF, API security)
- Data security (encryption, access controls)
- Identity security (MFA, SSO)

Slide 4: "Threat Model"
- Threat actors: External attackers, insiders
- Attack vectors: Phishing, malware, misconfigurations
- Assets: Customer data, intellectual property

Slide 5: "Mitigation Strategies"
- Regular security audits
- Automated threat detection
- Incident response procedures
- Employee training

Create this with a technical, professional style.""",
    
    "presentation_with_images": """Create a presentation titled "Product Launch 2024" with:

Slide 1: Title "Product Launch 2024 - New Innovation"

Slide 2: "Product Features" with an image placeholder
- Feature 1: Advanced AI capabilities
- Feature 2: User-friendly interface
- Feature 3: Enterprise-grade security

Slide 3: "Market Opportunity"
- Target market size: $2B
- Growth rate: 25% annually
- Our market share goal: 5%

Slide 4: "Pricing Strategy"
- Basic: $99/month
- Professional: $299/month
- Enterprise: Custom pricing

Include appropriate images where mentioned."""
}

POWERPOINT_ADD_SLIDE_PROMPTS = {
    "add_summary_slide": """Add a new slide to this presentation with:
- Title: "Key Takeaways"
- Content:
  * Revenue growth of 15% achieved
  * Cost reduction of 5% implemented
  * Market expansion successful
  * Customer satisfaction improved

Position this slide at the end of the presentation.

File data: [BASE64_DATA]""",
    
    "add_chart_slide": """Add a new slide showing financial data:
- Title: "Financial Overview"
- Include a chart showing quarterly revenue
- Add bullet points with key metrics:
  * Q1: $1.2M
  * Q2: $1.3M
  * Q3: $1.4M
  * Q4: $1.3M

File data: [BASE64_DATA]"""
}

# Visualization Tools Prompts

VISUALIZATION_CHART_PROMPTS = {
    "sales_performance_chart": """Create a comprehensive sales performance chart with the following data:

Monthly Sales Data:
- January: $45,000
- February: $52,000
- March: $48,000
- April: $61,000
- May: $55,000
- June: $67,000

Requirements:
1. Create a line chart showing the trend
2. Title: "Monthly Sales Performance - H1 2024"
3. X-axis: Month names
4. Y-axis: Sales amount in dollars
5. Add a trend line
6. Highlight the best performing month
7. Add data labels to each point

Provide the chart and explain the trends you observe.""",
    
    "comparison_chart": """Create a comparison chart for the following data:

Product Sales Comparison:
- Product A: $150,000
- Product B: $120,000
- Product C: $180,000
- Product D: $90,000
- Product E: $110,000

Requirements:
1. Create a bar chart comparing all products
2. Title: "Product Sales Comparison Q4 2024"
3. Use different colors for each bar
4. Add value labels on top of each bar
5. Sort bars from highest to lowest
6. Add a horizontal line showing the average

Explain which products are performing best and worst.""",
    
    "multi_series_chart": """Create a chart showing revenue and expenses over 6 months:

Data:
Month | Revenue | Expenses
Jan   | $50,000 | $30,000
Feb   | $55,000 | $32,000
Mar   | $60,000 | $35,000
Apr   | $65,000 | $38,000
May   | $70,000 | $40,000
Jun   | $75,000 | $42,000

Requirements:
1. Create a line chart with two lines (Revenue and Expenses)
2. Title: "Revenue vs Expenses - H1 2024"
3. Add a legend
4. Show profit margin (Revenue - Expenses) as a third line
5. Add annotations for the month with highest profit
6. Use different line styles for each series

Analyze the trends and provide insights.""",
    
    "pie_chart_distribution": """Create a pie chart showing market share:

Market Share Data:
- Company A: 35%
- Company B: 25%
- Company C: 20%
- Company D: 15%
- Others: 5%

Requirements:
1. Create a pie chart with distinct colors
2. Title: "Market Share Distribution"
3. Show percentages on each slice
4. Add a legend
5. Highlight the largest segment
6. Calculate and show total market size if possible

Explain the market dynamics."""
}

VISUALIZATION_FILE_CHART_PROMPTS = {
    "chart_from_excel": """Create a chart from this Excel file:
1. Read the Excel file
2. Identify the data columns
3. Create a bar chart comparing the values in the second column
4. Use the first column for labels
5. Title: "Data Analysis from Excel"
6. Add appropriate axis labels

File data: [BASE64_DATA]""",
    
    "chart_from_csv": """Create a visualization from this CSV file:
1. Read the CSV data
2. Create a line chart showing trends over time
3. If there are multiple data series, show them all
4. Add a title based on the data content
5. Format the chart professionally

File data: [BASE64_DATA]""",
    
    "chart_from_json": """Create a chart from this JSON data:
1. Parse the JSON structure
2. Identify the data points
3. Create an appropriate chart type (bar, line, or pie)
4. Use meaningful labels and titles
5. Add data annotations

File data: [BASE64_DATA]"""
}

# OCR Tools Prompts

OCR_EXTRACTION_PROMPTS = {
    "extract_text_detailed": """Extract all text from this image using OCR. Please:
1. Extract all readable text from the image
2. Preserve the structure and layout if possible
3. Identify headings, paragraphs, and lists
4. Extract any numbers, dates, or special characters
5. Provide the text in a readable format
6. If text is unclear, indicate which parts are uncertain

Image data: [BASE64_DATA]""",
    
    "extract_with_analysis": """Extract text from this image and analyze it:
1. Extract all text content
2. Identify the document type (invoice, report, letter, etc.)
3. Extract key information (dates, amounts, names, etc.)
4. Identify the language
5. Assess the quality of the text extraction
6. Provide suggestions for improving OCR accuracy if needed

Image data: [BASE64_DATA]""",
    
    "extract_from_multiple_regions": """Extract text from specific regions of this image:
1. Extract text from the header area (top 20% of image)
2. Extract text from the main content area (middle 60%)
3. Extract text from the footer area (bottom 20%)
4. Identify any text in margins or sidebars
5. Provide a structured output showing text by region

Image data: [BASE64_DATA]"""
}

OCR_STRUCTURE_PROMPTS = {
    "analyze_document_layout": """Analyze the structure and layout of this document image:
1. Identify the document type and format
2. Detect headers and footers
3. Identify main content regions
4. Detect columns and text blocks
5. Identify images, tables, or graphics
6. Map the overall layout structure
7. Provide coordinates for each region

Image data: [BASE64_DATA]""",
    
    "analyze_with_regions": """Perform detailed structure analysis:
1. Detect all text regions
2. Identify reading order (top to bottom, left to right)
3. Classify regions (header, body, footer, sidebar)
4. Detect tables and their structure
5. Identify images and their captions
6. Map relationships between regions
7. Provide a visual description of the layout

Image data: [BASE64_DATA]"""
}

# File Operations Prompts

FILE_CONVERSION_PROMPTS = {
    "csv_to_json_detailed": """Convert this CSV file to JSON format with the following requirements:
1. Parse the CSV structure correctly
2. Use the first row as keys for the JSON objects
3. Create an array of objects, one per data row
4. Handle empty cells appropriately
5. Preserve data types (numbers as numbers, not strings)
6. Format the JSON with proper indentation
7. Validate the JSON structure

File data: [BASE64_DATA]""",
    
    "excel_to_csv": """Convert this Excel file to CSV format:
1. Read all sheets or just the first sheet
2. Convert to CSV format
3. Preserve column headers
4. Handle special characters correctly
5. Maintain data formatting where possible
6. Provide the CSV output

File data: [BASE64_DATA]""",
    
    "json_to_excel": """Convert this JSON data to Excel format:
1. Parse the JSON structure
2. Create an Excel file with appropriate columns
3. Handle nested JSON structures (flatten if needed)
4. Preserve data types
5. Add headers
6. Format the Excel file professionally

File data: [BASE64_DATA]"""
}

# Complex Workflow Prompts

WORKFLOW_PROMPTS = {
    "excel_to_powerpoint_full": """I have an Excel file with quarterly financial data. Please:
1. Read the Excel file and extract all data
2. Analyze the financial trends
3. Create a PowerPoint presentation with:
   - Title slide: "Q4 2024 Financial Report"
   - Slide for each quarter showing revenue, expenses, and profit
   - A summary slide with year-end totals
   - A chart slide showing trends over the year
4. Include insights and recommendations
5. Format the presentation professionally

Excel file data: [BASE64_DATA]""",
    
    "data_analysis_workflow": """Perform a complete data analysis workflow:
1. Read the Excel file with sales data
2. Analyze the data:
   - Calculate totals, averages, and trends
   - Identify top performers
   - Find anomalies or outliers
3. Create visualizations:
   - Bar chart for top products
   - Line chart for trends over time
   - Pie chart for category distribution
4. Create a PowerPoint presentation summarizing:
   - Key findings
   - Visualizations
   - Recommendations

Excel file data: [BASE64_DATA]""",
    
    "ocr_to_excel_workflow": """Extract data from an image and organize it:
1. Extract all text from the image using OCR
2. Identify structured data (tables, lists, etc.)
3. Create an Excel file organizing the extracted data:
   - Put data in appropriate columns
   - Add headers
   - Format numbers correctly
4. Create a summary of what was extracted
5. Highlight any data that couldn't be extracted clearly

Image data: [BASE64_DATA]""",
    
    "multi_format_workflow": """Process multiple files and create a report:
1. Read the Excel file with data
2. Extract text from the image document
3. Combine insights from both sources
4. Create a PowerPoint presentation with:
   - Data from Excel in charts
   - Information from the image document
   - Combined analysis
5. Export the presentation for review

Excel file data: [BASE64_DATA]
Image data: [BASE64_DATA]"""
}

# Error Handling and Edge Case Prompts

EDGE_CASE_PROMPTS = {
    "invalid_file_handling": """I'm going to give you some file data, but it might be corrupted or invalid. Please:
1. Try to process it
2. If it fails, explain clearly what went wrong
3. Suggest what type of file was expected
4. Provide guidance on how to fix the issue

File data: invalid_base64_data_here""",
    
    "empty_file_handling": """Process this file. It might be empty or have minimal content:
1. Attempt to read/process the file
2. If empty, explain what an empty file means
3. Suggest what data should be in the file
4. Provide an example of valid file structure

File data: [BASE64_DATA]""",
    
    "large_file_handling": """This is a large file. Please:
1. Process it efficiently
2. Provide a summary rather than all details
3. Identify key information
4. Report on file size and complexity
5. Suggest optimizations if needed

File data: [BASE64_DATA]"""
}

# All prompts organized by tool
ALL_PROMPTS = {
    "excel_read": EXCEL_READ_PROMPTS,
    "excel_modify": EXCEL_MODIFY_PROMPTS,
    "excel_chart": EXCEL_CHART_PROMPTS,
    "excel_security": EXCEL_SECURITY_PROMPTS,
    "powerpoint_create": POWERPOINT_CREATE_PROMPTS,
    "powerpoint_add_slide": POWERPOINT_ADD_SLIDE_PROMPTS,
    "visualization_chart": VISUALIZATION_CHART_PROMPTS,
    "visualization_file": VISUALIZATION_FILE_CHART_PROMPTS,
    "ocr_extraction": OCR_EXTRACTION_PROMPTS,
    "ocr_structure": OCR_STRUCTURE_PROMPTS,
    "file_conversion": FILE_CONVERSION_PROMPTS,
    "workflows": WORKFLOW_PROMPTS,
    "edge_cases": EDGE_CASE_PROMPTS
}

