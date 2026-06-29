"""
Caddy configuration generator and reload helper.
"""
from __future__ import annotations

import logging
import os
from typing import List

import httpx

logger = logging.getLogger(__name__)

ROUTES_PATH = "/etc/caddy/dynamic/routes.conf"
UI_UPSTREAM = os.environ.get("UI_UPSTREAM", "mcpfarm-ui:3000")

CADDYFILE_HEADER = """{
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

    handle /services* {
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

"""

CADDYFILE_FOOTER = """
    handle {{
        reverse_proxy {ui_upstream}
    }}
}}
"""


def ui_caddyfile_footer() -> str:
    return CADDYFILE_FOOTER.format(ui_upstream=UI_UPSTREAM)


def generate_route_block(name: str, port: int) -> str:
    return (
        f"    @{name} path /{name}/*\n"
        f"    handle @{name} {{\n"
        f"        forward_auth auth-gateway:9090 {{\n"
        f"            uri /verify\n"
        f"            copy_headers Authorization\n"
        f"        }}\n"
        f"        uri strip_prefix /{name}\n"
        f"        reverse_proxy {name}:{port}\n"
        f"    }}"
    )


def generate_routes_conf(servers: list) -> str:
    """Generate routes.conf content for all provided servers."""
    blocks = []
    for server in servers:
        name = server.name if hasattr(server, "name") else server["name"]
        port = server.port if hasattr(server, "port") else server["port"]
        blocks.append(generate_route_block(name, port))
    return "\n\n".join(blocks) + "\n" if blocks else ""


def build_full_caddyfile(servers: list) -> str:
    """Build a complete Caddyfile with all routes inlined."""
    route_blocks = []
    for server in servers:
        name = server.name if hasattr(server, "name") else server["name"]
        port = server.port if hasattr(server, "port") else server["port"]
        route_blocks.append(generate_route_block(name, port))
    return CADDYFILE_HEADER + "\n".join(route_blocks) + ui_caddyfile_footer()


async def reload_caddy(servers: list) -> bool:
    """Build a full Caddyfile with inlined routes and load it via the admin API."""
    try:
        caddyfile = build_full_caddyfile(servers)
        logger.info("Reloading Caddy via admin API (%d routes)...", len(servers))
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "http://caddy:2019/load",
                content=caddyfile,
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
    """Write routes.conf to disk (for Caddy file-based reload) then reload via API."""
    conf = generate_routes_conf(servers)
    try:
        with open(routes_path, "w") as f:
            f.write(conf)
        logger.info("Wrote %d routes to %s", len(servers), routes_path)
    except Exception as exc:
        logger.error("Failed to write routes.conf: %s", exc)
        return False
    return await reload_caddy(servers)
