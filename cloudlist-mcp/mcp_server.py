"""Cloudlist MCP Server - Cloud Asset Discovery via FastMCP."""

import json
import os
import subprocess
import shutil
import tempfile
import sys
import logging

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("cloudlist-mcp")

mcp = FastMCP(
    "cloudlist-mcp",
    instructions="MCP server for Cloudlist - lists assets from multiple cloud providers (AWS, GCP, Azure, etc.) for attack surface management.",
)

CLOUDLIST_BIN = shutil.which("cloudlist") or "cloudlist"


def _run_cloudlist(args: list[str], timeout: int = 120) -> dict:
    """Execute cloudlist CLI and return structured result."""
    try:
        result = subprocess.run(
            [CLOUDLIST_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("cloudlist exited with code %d: %s", result.returncode, stderr)

        parsed = None
        if output:
            lines = output.splitlines()
            json_results = []
            for line in lines:
                try:
                    json_results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            if json_results:
                parsed = json_results
            elif lines:
                parsed = lines

        return {
            "success": result.returncode == 0,
            "output": parsed if parsed is not None else output,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("cloudlist binary not found at '%s'", CLOUDLIST_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"cloudlist binary not found at '{CLOUDLIST_BIN}'. Ensure cloudlist is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("cloudlist command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"cloudlist command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("cloudlist command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def list_cloud_assets(
    providers: str | None = None,
    hosts_only: bool = False,
    ips_only: bool = False,
    exclude_private: bool = False,
    service: str | None = None,
    config_content: str | None = None,
) -> dict:
    """List assets from cloud providers using cloudlist.

    Discovers assets (hosts, IPs) across cloud providers such as AWS, GCP, Azure,
    DigitalOcean, Fastly, and more. Requires a YAML configuration with provider
    credentials either mounted at /app/config/provider-config.yaml or passed
    via config_content.

    Args:
        providers: Comma-separated cloud provider names to query (e.g. "aws,gcp,azure"). Omit to query all configured providers.
        hosts_only: If True, return only hostnames. Default False.
        ips_only: If True, return only IP addresses. Default False.
        exclude_private: If True, exclude private/internal IPs from results. Default False.
        service: Filter results by specific service type (e.g. "ec2", "s3", "route53").
        config_content: YAML configuration content with cloud provider credentials. If provided, written to a temp file and used as the config.

    Returns:
        Dictionary with cloud asset discovery results.
    """
    logger.info("list_cloud_assets called with providers=%s", providers)
    args = ["-json", "-silent"]
    config_path = None
    tmp_config = None

    try:
        if config_content:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            )
            tmp.write(config_content)
            tmp.close()
            tmp_config = tmp.name
            config_path = tmp_config
        else:
            default_config = "/app/config/provider-config.yaml"
            if os.path.isfile(default_config):
                config_path = default_config

        if config_path:
            args.extend(["-config", config_path])

        if providers:
            for p in providers.split(","):
                p = p.strip()
                if p:
                    args.extend(["-provider", p])

        if hosts_only:
            args.append("-host")

        if ips_only:
            args.append("-ip")

        if exclude_private:
            args.append("-exclude-private")

        if service:
            args.extend(["-service", service.strip()])

        return _run_cloudlist(args)
    finally:
        if tmp_config:
            try:
                os.unlink(tmp_config)
            except OSError:
                pass


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8111"))
    logger.info("Starting cloudlist-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
