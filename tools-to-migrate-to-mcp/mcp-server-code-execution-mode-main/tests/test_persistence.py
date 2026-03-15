import pytest

from mcp_server_code_execution_mode import MCPBridge


@pytest.mark.asyncio
async def test_persistence():
    bridge = MCPBridge()
    try:
        # 1. Set a variable
        result1 = await bridge.execute_code("x = 42")
        assert result1.success, f"Failed to set variable: {result1.stderr}"

        # 2. Read the variable
        result2 = await bridge.execute_code("print(x)")
        assert result2.success, f"Failed to read variable: {result2.stderr}"
        assert result2.stdout.strip() == "42"

        # 3. Import a module
        result3 = await bridge.execute_code("import math")
        assert result3.success, f"Failed to import module: {result3.stderr}"

        # 4. Use the module
        result4 = await bridge.execute_code("print(math.pi)")
        assert result4.success, f"Failed to use module: {result4.stderr}"
        assert "3.14" in result4.stdout

    finally:
        await bridge.sandbox._stop_runtime()
