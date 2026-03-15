# LLM Agent Integration Tests

Comprehensive LLM-based testing for prodx tools using LangChain agents with Ollama.

## Overview

This test suite uses LangChain agents (similar to Chat.py) to test all prodx tools through natural language prompts. The agent uses Ollama with qwen3:latest running on a remote server to simulate real-world usage scenarios.

## Configuration

### Default Settings
- **Model**: `qwen3:latest`
- **Provider**: Ollama
- **Base URL**: `http://192.168.5.217:11434`
- **Timeout**: 300 seconds (5 minutes) per test

### Environment Variables

You can override defaults using environment variables:

```bash
export OLLAMA_TEST_BASE_URL="http://192.168.5.217:11434"
export OLLAMA_TEST_MODEL="qwen3:latest"
export OLLAMA_TEST_TIMEOUT="300"
```

## Files

### Core Test Files

1. **`test_llm_agent_integration.py`** (900+ lines)
   - Main test file with LLM agent integration
   - Test classes for each tool category
   - Complex workflow tests
   - Error handling tests

2. **`test_llm_prompts.py`** (500+ lines)
   - Comprehensive, detailed prompts for each tool
   - Organized by tool category
   - Real-world scenario prompts
   - Edge case prompts

3. **`run_llm_tests.py`**
   - Test runner script
   - Supports filtering by tool category
   - Verbose output option
   - Results summary and JSON export

## Running Tests

### Quick Start

```bash
cd streamlit_app/modules/tools/prodx

# Run all LLM agent tests
python3 run_llm_tests.py

# Run with verbose output
python3 run_llm_tests.py --verbose

# Test specific tool category
python3 run_llm_tests.py --tool excel
python3 run_llm_tests.py --tool powerpoint
python3 run_llm_tests.py --tool visualization
python3 run_llm_tests.py --tool ocr
python3 run_llm_tests.py --tool workflows
```

### Using pytest

```bash
# Run all LLM tests
pytest test_llm_agent_integration.py -v -s

# Run specific test class
pytest test_llm_agent_integration.py::TestExcelToolsWithLLM -v -s

# Run specific test method
pytest test_llm_agent_integration.py::TestExcelToolsWithLLM::test_read_excel_with_agent -v -s

# Run with custom Ollama URL
OLLAMA_TEST_BASE_URL="http://192.168.5.217:11434" pytest test_llm_agent_integration.py -v
```

## Test Structure

### Test Classes

1. **TestExcelToolsWithLLM** (4 tests)
   - `test_read_excel_with_agent` - Read Excel with detailed analysis
   - `test_modify_excel_with_agent` - Modify Excel with multiple operations
   - `test_create_chart_with_agent` - Create charts in Excel
   - `test_analyze_security_with_agent` - Security analysis

2. **TestPowerPointToolsWithLLM** (2 tests)
   - `test_create_presentation_with_agent` - Create business presentations
   - `test_add_slide_with_agent` - Add slides to existing presentations

3. **TestVisualizationToolsWithLLM** (2 tests)
   - `test_create_chart_with_agent` - Create charts from data
   - `test_create_chart_from_csv_with_agent` - Create charts from files

4. **TestOCRToolsWithLLM** (2 tests)
   - `test_extract_text_with_agent` - Extract text from images
   - `test_analyze_structure_with_agent` - Analyze document structure

5. **TestFileOperationsWithLLM** (1 test)
   - `test_convert_format_with_agent` - Convert file formats

6. **TestComplexWorkflowsWithLLM** (2 tests)
   - `test_excel_to_powerpoint_workflow` - Multi-tool workflow
   - `test_data_analysis_workflow` - Data analysis workflow

7. **TestAgentErrorHandling** (2 tests)
   - `test_agent_handles_invalid_input` - Error resilience
   - `test_agent_with_no_tools` - Behavior without tools

## Detailed Prompts

The `test_llm_prompts.py` file contains comprehensive prompts organized by category:

### Excel Prompts
- **EXCEL_READ_PROMPTS**: Basic read, read with formulas, large file handling
- **EXCEL_MODIFY_PROMPTS**: Add rows, update with formulas, complex modifications
- **EXCEL_CHART_PROMPTS**: Bar charts, line charts, pie charts
- **EXCEL_SECURITY_PROMPTS**: Comprehensive security analysis, data privacy checks

### PowerPoint Prompts
- **POWERPOINT_CREATE_PROMPTS**: Business presentations, technical presentations, presentations with images
- **POWERPOINT_ADD_SLIDE_PROMPTS**: Add summary slides, add chart slides

### Visualization Prompts
- **VISUALIZATION_CHART_PROMPTS**: Sales performance, comparison charts, multi-series charts, pie charts
- **VISUALIZATION_FILE_CHART_PROMPTS**: Charts from Excel, CSV, JSON

### OCR Prompts
- **OCR_EXTRACTION_PROMPTS**: Detailed extraction, extraction with analysis, multi-region extraction
- **OCR_STRUCTURE_PROMPTS**: Document layout analysis, structure with regions

### File Operations Prompts
- **FILE_CONVERSION_PROMPTS**: CSV to JSON, Excel to CSV, JSON to Excel

### Workflow Prompts
- **WORKFLOW_PROMPTS**: Excel to PowerPoint, data analysis, OCR to Excel, multi-format workflows

## How It Works

### Agent Creation

```python
# Create Ollama LLM
llm = ChatOllama(
    model="qwen3:latest",
    base_url="http://192.168.5.217:11434",
    temperature=0.1
)

# Create agent with tools
agent = create_agent(
    model=llm,
    tools=[ReadExcelStructuredTool(), ModifyExcelTool(), ...],
    system_prompt="You are a helpful productivity assistant..."
)
```

### Test Execution

```python
# Run agent test
result = await tester.run_agent_test(
    prompt="Read this Excel file and analyze the data...",
    expected_keywords=["data", "analysis", "excel"],
    verbose=True
)
```

### Event Streaming

The test runner captures:
- Tool start/end events
- Response chunks
- Tool errors
- Agent iterations
- Execution time

## Expected Behavior

### Successful Test
- Agent receives prompt
- Agent decides to use appropriate tool(s)
- Tool executes successfully
- Agent processes tool output
- Agent provides comprehensive response
- Response contains expected keywords
- No errors occurred

### Tool Call Tracking
- Each tool call is tracked with:
  - Tool name
  - Start/end times
  - Input/output lengths
  - Status (started/completed/error)

### Error Handling
- Invalid inputs return error messages (not crashes)
- Network failures are handled gracefully
- Tool errors are captured and reported
- Agent provides helpful error explanations

## Test Results

### Output Format

Each test produces:
```json
{
  "prompt": "User prompt...",
  "response": "Agent response...",
  "tool_calls": [
    {
      "tool": "ReadExcelStructuredTool",
      "status": "completed",
      "time": "2024-01-01T12:00:00",
      "end_time": "2024-01-01T12:00:05",
      "output_length": 1234
    }
  ],
  "errors": [],
  "success": true,
  "iterations": 5,
  "expected_keywords_found": ["data", "analysis"],
  "expected_keywords_missing": []
}
```

### Results File

Test results are saved to `llm_test_results.json` with:
- Test class and method names
- Status (passed/failed/error)
- Timestamps
- Error messages (if any)

## Troubleshooting

### Connection Issues

If Ollama connection fails:
1. Verify Ollama is running on `192.168.5.217:11434`
2. Check network connectivity
3. Verify model `qwen3:latest` is available
4. Test with: `curl http://192.168.5.217:11434/api/tags`

### Model Not Found

If model is not available:
1. Pull the model: `ollama pull qwen3:latest` (on the server)
2. Or change model: `--model llama3.1:8b`

### Timeout Issues

If tests timeout:
1. Increase timeout: `--timeout 600`
2. Check server performance
3. Reduce test complexity
4. Check network latency

### Tool Execution Errors

If tools fail:
1. Check tool dependencies are installed
2. Verify tool imports work
3. Check tool error messages in verbose output
4. Review tool logs

## Best Practices

### Writing New Tests

1. **Use detailed prompts** from `test_llm_prompts.py`
2. **Include expected keywords** for validation
3. **Set appropriate timeouts** for complex operations
4. **Use verbose mode** for debugging
5. **Test error cases** as well as success cases

### Prompt Design

1. **Be specific** - Clearly state what you want
2. **Provide context** - Include file data or examples
3. **Request verification** - Ask agent to confirm actions
4. **Request summaries** - Ask for explanations of results

### Debugging

1. **Use verbose mode** (`-v` flag) to see agent reasoning
2. **Check tool calls** in results to see what tools were used
3. **Review error messages** for tool failures
4. **Check response content** for agent explanations

## Integration with Chat.py

These tests use the same patterns as Chat.py:
- Same `create_agent` API
- Same event streaming (`astream_events`)
- Same tool integration
- Same error handling

This ensures that tools work correctly in the actual Chat.py environment.

## Performance Expectations

- **Simple operations**: 10-30 seconds
- **Complex operations**: 30-120 seconds
- **Multi-tool workflows**: 60-300 seconds
- **Large files**: May take longer

## Next Steps

1. **Run tests**: `python3 run_llm_tests.py --verbose`
2. **Review results**: Check `llm_test_results.json`
3. **Fix issues**: Address any tool or agent problems
4. **Iterate**: Refine prompts based on results
5. **Go live**: Deploy with confidence! 🚀

---

**Status**: ✅ Ready for execution
**Model**: qwen3:latest on 192.168.5.217:11434
**Framework**: LangChain agents (same as Chat.py)

