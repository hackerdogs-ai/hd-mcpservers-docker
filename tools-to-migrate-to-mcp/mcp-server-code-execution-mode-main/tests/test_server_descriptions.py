from unittest.mock import MagicMock, patch

import pytest

from mcp_server_code_execution_mode import (
    MCPBridge,
    RootlessContainerSandbox,
)


@pytest.mark.asyncio
async def test_server_descriptions_in_sandbox():
    """Verify that server descriptions are accessible in the sandbox."""

    # Mock bridge and sandbox
    bridge = MagicMock(spec=MCPBridge)
    bridge.servers = {"test-server": MagicMock(description="A test server description")}

    # Mock sandbox execution
    sandbox = MagicMock(spec=RootlessContainerSandbox)
    sandbox.execute.return_value = MagicMock(
        stdout='[{"name": "test-server", "description": "A test server description"}]',
        stderr="",
    )

    # We can't easily test the full integration without a real container runtime or complex mocking of the sandbox internals.
    # Instead, let's test the _render_entrypoint method directly to ensure it generates the correct code.

    real_sandbox = RootlessContainerSandbox(runtime="podman")

    servers_metadata = []
    discovered_servers = {"test-server": "A test server description"}

    entrypoint_script = real_sandbox._render_entrypoint(
        servers_metadata, discovered_servers
    )

    # Check if the description is present in the generated script
    # Note: json.dumps uses separators=(",", ":") so there are no spaces after colons
    assert '"test-server":"A test server description"' in entrypoint_script

    # Check if the helper function logic is present
    assert "def discovered_servers(detailed=False):" in entrypoint_script
    assert "if detailed:" in entrypoint_script
    assert '"description": v' in entrypoint_script


@pytest.mark.asyncio
async def test_discover_servers_returns_dict():
    """Verify discover_servers returns a dictionary."""
    # We need to patch CONFIG_SOURCES and _load_server_config

    with (
        patch("mcp_server_code_execution_mode.CONFIG_SOURCES", []),
        patch(
            "mcp_server_code_execution_mode.MCPBridge._load_server_config"
        ) as mock_load,
    ):
        bridge = MCPBridge()
        # Mock _load_server_config to return a dict with description
        # But wait, discover_servers iterates CONFIG_SOURCES.
        # Let's mock a source.

        from mcp_server_code_execution_mode import ConfigSource

        mock_source = MagicMock(spec=ConfigSource)
        mock_source.path.exists.return_value = True
        mock_source.type = "file"
        mock_source.format = "json"
        mock_source.name = "TestConfig"

        with patch("mcp_server_code_execution_mode.CONFIG_SOURCES", [mock_source]):
            mock_load.return_value = {
                "test-server": ({"command": "echo"}, "Description from config")
            }

            discovered = await bridge.discover_servers()

            assert isinstance(discovered, dict)
            assert discovered["test-server"] == "Description from config"
            assert (
                bridge.servers["test-server"].description == "Description from config"
            )
