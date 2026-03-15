import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import mcp_server_code_execution_mode as bridge_module
from mcp_server_code_execution_mode import RootlessContainerSandbox


class IPCStreamLimitTests(unittest.TestCase):
    def test_asyncio_default_pipe_limit_can_overrun(self) -> None:
        """
        Reproduces the class of failure seen with large MCP payloads (e.g. GitHub list_tools):
        asyncio's default StreamReader limit (~64KiB) can error when reading a single long line.
        """

        async def _run() -> None:
            # 200KB single line (plus newline)
            payload = "x" * 200_000
            proc = await asyncio.create_subprocess_exec(
                "python3",
                "-c",
                f"print('{payload}')",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            assert proc.stdout is not None
            with self.assertRaises(ValueError):
                # This uses StreamReader.readline() under the hood.
                await proc.stdout.readline()
            proc.kill()
            await proc.wait()

        asyncio.run(_run())

    def test_asyncio_pipe_with_large_limit_succeeds(self) -> None:
        """Same as above, but with an explicit large limit so readline() succeeds."""

        async def _run() -> None:
            payload = "x" * 200_000
            proc = await asyncio.create_subprocess_exec(
                "python3",
                "-c",
                f"print('{payload}')",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=300_000,
            )
            assert proc.stdout is not None
            line = await proc.stdout.readline()
            text = line.decode(errors="replace").strip("\n")
            self.assertEqual(len(text), len(payload))
            self.assertTrue(text.startswith("x"))
            await proc.wait()

        asyncio.run(_run())

    def test_sandbox_process_is_started_with_ipc_limit(self) -> None:
        """
        Validates that RootlessContainerSandbox passes limit=DEFAULT_IPC_LINE_LIMIT when
        spawning the sandbox subprocess. This prevents LimitOverrunError/ValueError when
        the sandbox emits large single-line JSON (e.g. tool lists).
        """

        async def _run() -> None:
            sandbox = RootlessContainerSandbox(runtime="docker")

            # Avoid probing the real container runtime in a unit test.
            async def _noop_runtime_ready() -> None:
                return None

            sandbox._ensure_runtime_ready = _noop_runtime_ready  # type: ignore[attr-defined]

            captured: dict[str, object] = {}

            async def _fake_create_subprocess_exec(*args, **kwargs):
                captured["args"] = args
                captured["kwargs"] = kwargs
                # Minimal process object for _ensure_started().
                return SimpleNamespace(returncode=None)

            with tempfile.TemporaryDirectory() as td:
                host_dir = Path(td)
                with patch.object(
                    bridge_module.asyncio, "create_subprocess_exec", _fake_create_subprocess_exec
                ):
                    await sandbox._ensure_started(  # type: ignore[attr-defined]
                        servers_metadata=(),
                        discovered_servers={},
                        container_env=None,
                        volume_mounts=None,
                        host_dir=host_dir,
                    )

            kwargs = captured.get("kwargs", {})
            self.assertIsInstance(kwargs, dict)
            self.assertEqual(kwargs.get("limit"), bridge_module.DEFAULT_IPC_LINE_LIMIT)

        asyncio.run(_run())


