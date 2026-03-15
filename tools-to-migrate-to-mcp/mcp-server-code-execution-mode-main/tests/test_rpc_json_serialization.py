import json
import unittest

import mcp_server_code_execution_mode as bridge_module
from mcp.types import CallToolResult, TextContent


class RPCJsonSerializationTests(unittest.TestCase):
    def test_to_jsonable_handles_call_tool_result(self) -> None:
        result = CallToolResult(content=[TextContent(type="text", text="ok")])
        payload = {"success": True, "result": result}
        normalized = bridge_module._to_jsonable(payload)
        # Must be JSON serializable
        json.dumps(normalized)
        self.assertIsInstance(normalized, dict)


