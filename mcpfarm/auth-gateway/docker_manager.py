"""
Docker SDK wrapper for managing MCP server containers dynamically.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import docker
import docker.errors

logger = logging.getLogger(__name__)


def _get_client() -> docker.DockerClient:
    return docker.from_env()


def start_server(
    name: str,
    image: str,
    port: int,
    env_vars: Dict[str, str],
    network: str = "mcpfarm_internal",
) -> None:
    """Pull image if needed, then create and start container."""
    client = _get_client()

    # Pull image if not present locally
    try:
        client.images.get(image)
        logger.info("Image %s already present locally.", image)
    except docker.errors.ImageNotFound:
        logger.info("Pulling image %s ...", image)
        client.images.pull(image)

    # Remove any existing container with the same name
    try:
        existing = client.containers.get(name)
        logger.info("Removing existing container %s ...", name)
        existing.remove(force=True)
    except docker.errors.NotFound:
        pass

    # Build environment dict
    env = {
        "MCP_TRANSPORT": "streamable-http",
        "MCP_PORT": str(port),
    }
    env.update(env_vars)

    container = client.containers.run(
        image=image,
        name=name,
        detach=True,
        environment=env,
        network=network,
        restart_policy={"Name": "unless-stopped"},
        # No host port bindings — internal network only
    )
    logger.info("Started container %s (id=%s).", name, container.short_id)


def stop_server(name: str) -> None:
    """Stop and remove a container."""
    client = _get_client()
    try:
        container = client.containers.get(name)
        container.stop(timeout=10)
        container.remove()
        logger.info("Stopped and removed container %s.", name)
    except docker.errors.NotFound:
        logger.warning("Container %s not found when stopping.", name)


def restart_server(
    name: str,
    image: str,
    port: int,
    env_vars: Dict[str, str],
    network: str = "mcpfarm_internal",
) -> None:
    """Stop then start a container."""
    stop_server(name)
    start_server(name, image, port, env_vars, network)


def get_logs(name: str, tail: int = 100) -> str:
    """Return the last `tail` lines of container logs."""
    client = _get_client()
    try:
        container = client.containers.get(name)
        raw = container.logs(tail=tail, timestamps=True)
        return raw.decode("utf-8", errors="replace")
    except docker.errors.NotFound:
        return f"Container {name} not found."
    except Exception as exc:
        return f"Error fetching logs for {name}: {exc}"


def recover_dynamic_servers(servers: list) -> None:
    """
    Re-launch dynamic servers after an auth-gateway restart.
    `servers` is a list of Server ORM objects with source='dynamic'.
    """
    import json

    for srv in servers:
        try:
            env_vars = json.loads(srv.env) if srv.env else {}
            # Remove MCP_TRANSPORT and MCP_PORT from stored env — they are added by start_server
            env_vars.pop("MCP_TRANSPORT", None)
            env_vars.pop("MCP_PORT", None)
            start_server(srv.name, srv.image, srv.port, env_vars)
            logger.info("Recovered dynamic server %s.", srv.name)
        except Exception as exc:
            logger.error("Failed to recover server %s: %s", srv.name, exc)
