#!/usr/bin/env python3
"""
Generate docker-compose.yml and caddy/routes.conf from port-map.json.

Run from the mcpfarm/ directory:
    python scripts/generate-compose.py
"""
from __future__ import annotations

import json
import os
import sys
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MCPFARM_DIR = os.path.dirname(SCRIPT_DIR)
PORT_MAP_PATH = os.path.join(MCPFARM_DIR, "port-map.json")
COMPOSE_PATH = os.path.join(MCPFARM_DIR, "docker-compose.yml")
ROUTES_CONF_PATH = os.path.join(MCPFARM_DIR, "caddy", "routes.conf")


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

COMPOSE_HEADER = """\
version: "3.8"

services:
  # -----------------------------------------------------------------------
  # Caddy reverse proxy
  # -----------------------------------------------------------------------
  caddy:
    image: caddy:2-alpine
    container_name: mcpfarm-caddy
    ports:
      - "${FARM_PORT:-8485}:80"
      - "2019:2019"
    volumes:
      - ./caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_routes:/etc/caddy/dynamic
    networks:
      - mcpfarm
    depends_on:
      auth-gateway:
        condition: service_healthy
    restart: unless-stopped

  # -----------------------------------------------------------------------
  # Auth Gateway
  # -----------------------------------------------------------------------
  auth-gateway:
    build: ./auth-gateway
    image: hackerdogs/auth-gateway:latest
    container_name: mcpfarm-auth
    environment:
      - ADMIN_SECRET=${ADMIN_SECRET}
      - AUTH_DB_PATH=/data/auth.db
    volumes:
      - auth_data:/data
      - caddy_routes:/etc/caddy/dynamic
      - /var/run/docker.sock:/var/run/docker.sock
      - ./port-map.json:/app/port-map.json:ro
    networks:
      - mcpfarm
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9090/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  # -----------------------------------------------------------------------
  # MCP Servers (auto-generated from port-map.json)
  # -----------------------------------------------------------------------
"""

COMPOSE_FOOTER = """\

networks:
  mcpfarm:
    name: mcpfarm_internal
    driver: bridge

volumes:
  auth_data:
    name: mcpfarm_auth_data
  caddy_routes:
    name: mcpfarm_caddy_routes
"""


def _env_lines(env_keys: list, indent: str = "      ") -> str:
    """Generate environment variable lines for docker-compose service."""
    if not env_keys:
        return ""
    lines = []
    for key in env_keys:
        lines.append(f"{indent}- {key}=${{{key}}}")
    return "\n".join(lines)


def _service_block(name: str, image: str, port: int, env_keys: list) -> str:
    """Render a single MCP server service block."""
    env_section = ""
    base_env = f"      - MCP_TRANSPORT=streamable-http\n      - MCP_PORT={port}"
    if env_keys:
        extra = _env_lines(env_keys)
        env_section = base_env + "\n" + extra
    else:
        env_section = base_env

    return f"""\
  {name}:
    image: {image}
    container_name: {name}
    environment:
{env_section}
    networks:
      - mcpfarm
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
"""


def _route_block(name: str, port: int) -> str:
    """Render a single Caddy route block."""
    return (
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.path.exists(PORT_MAP_PATH):
        print(f"ERROR: port-map.json not found at {PORT_MAP_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(PORT_MAP_PATH) as f:
        port_map: dict = json.load(f)

    servers = sorted(port_map.items())  # sorted by name for determinism
    n = len(servers)

    # Build docker-compose.yml
    compose_parts = [COMPOSE_HEADER]
    for name, info in servers:
        block = _service_block(
            name=name,
            image=info["image"],
            port=info["port"],
            env_keys=info.get("env", []),
        )
        compose_parts.append(block)
    compose_parts.append(COMPOSE_FOOTER)

    compose_content = "\n".join(compose_parts)
    with open(COMPOSE_PATH, "w") as f:
        f.write(compose_content)

    # Build caddy/routes.conf
    os.makedirs(os.path.dirname(ROUTES_CONF_PATH), exist_ok=True)
    route_blocks = []
    for name, info in servers:
        route_blocks.append(_route_block(name, info["port"]))
    routes_content = "\n\n".join(route_blocks) + "\n"

    with open(ROUTES_CONF_PATH, "w") as f:
        f.write(routes_content)

    print(f"Generated docker-compose.yml with {n} MCP servers and caddy/routes.conf with {n} routes.")


if __name__ == "__main__":
    main()
