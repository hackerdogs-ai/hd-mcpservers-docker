import unittest

from mcp.shared.exceptions import McpError

from mcp_server_code_execution_mode import (
    CAPABILITY_RESOURCE_URI,
    SANDBOX_HELPERS_SUMMARY,
    list_resources,
    read_resource,
)


class ResourceEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_resources_exposes_capability_document(self) -> None:
        resources = await list_resources()
        capability = next((res for res in resources if str(res.uri) == CAPABILITY_RESOURCE_URI), None)
        self.assertIsNotNone(capability)
        assert capability is not None  # help type-checkers
        self.assertEqual(capability.name, "code-execution-capabilities")
        self.assertEqual(capability.mimeType, "text/markdown")
        self.assertGreater(capability.size or 0, 0)

    async def test_read_resource_returns_helper_summary(self) -> None:
        body = await read_resource(CAPABILITY_RESOURCE_URI)
        self.assertIn("Code Execution MCP Capabilities", body)
        self.assertIn(SANDBOX_HELPERS_SUMMARY, body)

    async def test_read_resource_mentions_cwd(self) -> None:
        body = await read_resource(CAPABILITY_RESOURCE_URI)
        self.assertIn("cwd", body)

    async def test_read_resource_rejects_unknown_uris(self) -> None:
        with self.assertRaises(McpError):
            await read_resource("resource://mcp-server-code-execution-mode/unknown")


if __name__ == "__main__":  # pragma: no cover - convenience for direct runs
    unittest.main()
