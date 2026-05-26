"""
Caddy configuration generator and reload helper.
"""
from __future__ import annotations

import logging
from typing import List

import httpx

logger = logging.getLogger(__name__)

ROUTES_PATH = "/etc/caddy/dynamic/routes.conf"

CADDYFILE_TEMPLATE = """{
    admin 0.0.0.0:2019
    auto_https off
}

:80, :11459 {
    header Access-Control-Allow-Origin *
    header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, mcp-session-id, X-Admin-Secret"
    header Access-Control-Allow-Methods "GET, POST, DELETE, OPTIONS"
    header Access-Control-Expose-Headers "mcp-session-id"

    @options method OPTIONS
    handle @options {
        respond "" 204
    }

    handle /health {
        respond "OK" 200
    }

    handle /admin/* {
        reverse_proxy auth-gateway:9090
    }

    handle /services {
        reverse_proxy auth-gateway:9090
    }

    handle /ui-config {
        reverse_proxy auth-gateway:9090
    }

    handle /verify {
        reverse_proxy auth-gateway:9090
    }

    handle /claude {
        reverse_proxy auth-gateway:9090
    }

    import /etc/caddy/dynamic/routes.conf

    handle {
        reverse_proxy mcpfarm-ui:3000
    }
}
"""


def generate_routes_conf(servers: list) -> str:
    """Generate routes.conf content for all provided servers."""
    blocks = []
    for server in servers:
        name = server.name if hasattr(server, "name") else server["name"]
        port = server.port if hasattr(server, "port") else server["port"]
        block = (
            f"@{name} path /{name}/*\n"
            f"handle @{name} {{\n"
            f"    forward_auth auth-gateway:9090 {{\n"
            f"        uri /verify\n"
            f"        copy_headers Authorization\n"
            f"    }}\n"
            f"    uri strip_prefix /{name}\n"
            f"    reverse_proxy {name}:{port}\n"
            f"}}"
        )
        blocks.append(block)
    return "\n\n".join(blocks) + "\n" if blocks else ""


async def reload_caddy(routes_path: str = ROUTES_PATH) -> bool:
    """Write routes.conf and signal Caddy to reload via its admin API."""
    try:
        # Write the routes file (should already be written by caller, but just in case)
        logger.info("Reloading Caddy via admin API...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://caddy:2019/load",
                content=CADDYFILE_TEMPLATE,
                headers={"Content-Type": "text/caddyfile"},
            )
            if resp.status_code in (200, 204):
                logger.info("Caddy reloaded successfully.")
                return True
            else:
                logger.warning("Caddy reload returned status %d: %s", resp.status_code, resp.text)
                return False
    except httpx.ConnectError:
        logger.warning("Could not connect to Caddy admin API (may not be ready yet).")
        return False
    except Exception as exc:
        logger.error("Error reloading Caddy: %s", exc)
        return False


async def write_and_reload(servers: list, routes_path: str = ROUTES_PATH) -> bool:
    """Write routes.conf to disk then reload Caddy."""
    conf = generate_routes_conf(servers)
    try:
        with open(routes_path, "w") as f:
            f.write(conf)
        logger.info("Wrote %d routes to %s", len(servers), routes_path)
    except Exception as exc:
        logger.error("Failed to write routes.conf: %s", exc)
        return False
    return await reload_caddy(routes_path)
