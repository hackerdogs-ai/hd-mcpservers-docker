import json
import unittest

from mcp_server_code_execution_mode import SANDBOX_HELPERS_SUMMARY, list_tools as list_tools_handler


class ListToolsMetadataTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_python_tool_mentions_helper_summary(self) -> None:
        tools = await list_tools_handler()
        self.assertEqual(len(tools), 1)
        tool = tools[0]
        schema_json = json.dumps(tool.inputSchema)
        self.assertIn(SANDBOX_HELPERS_SUMMARY, schema_json)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
