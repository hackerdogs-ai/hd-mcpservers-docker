"""
MCP Docker Host Fix Utilities

This module provides utilities to fix DOCKER_HOST environment variable issues
for mcp-server-docker and other Docker-based MCP servers.

The mcp-server-docker package uses docker.from_env() which may try to connect
via SSH if DOCKER_HOST is set incorrectly (e.g., ssh://user@localhost).
This module detects and fixes such invalid configurations while preserving
legitimate remote Docker setups.
"""

import os
import platform
import subprocess
import json
import uuid
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse

# Try to import BaseExceptionGroup (Python 3.11+)
try:
    from exceptiongroup import BaseExceptionGroup
except ImportError:
    # Python < 3.11 or exceptiongroup not installed
    # Create a dummy class that will never match
    class BaseExceptionGroup(Exception):
        pass

try:
    from hd_logging import setup_logger
except ImportError:
    # Fallback for environments where hd_logging is not installed
    import logging
    def setup_logger(name, log_file_path=None):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = setup_logger(__name__, log_file_path="logs/mcp_docker_host_fix.log")


def get_docker_socket_path() -> Optional[str]:
    """
    Detect the correct Docker socket path for the current platform.
    
    Returns:
        Docker socket path in format 'unix://...' or 'npipe://...', or None if not found.
        
    Platform-specific paths:
    - macOS (Docker Desktop): ~/.docker/run/docker.sock (newer) or /var/run/docker.sock (older)
    - Linux (Native): /var/run/docker.sock
    - Linux (Rootless): $XDG_RUNTIME_DIR/docker.sock or /run/user/{uid}/docker.sock
    - Windows (Docker Desktop): npipe:////./pipe/docker_engine
    - Windows (WSL2): /var/run/docker.sock (same as Linux)
    - Container: /var/run/docker.sock (must be mounted from host)
    """
    system = platform.system()
    is_container = os.path.exists('/.dockerenv')
    
    # Windows: Always use named pipe
    if system == 'Windows':
        return 'npipe:////./pipe/docker_engine'
    
    # macOS: Check newer Docker Desktop path first, then fallback
    if system == 'Darwin':
        # Newer Docker Desktop uses user-specific socket
        home = os.path.expanduser('~')
        newer_socket = os.path.join(home, '.docker', 'run', 'docker.sock')
        if os.path.exists(newer_socket):
            return f'unix://{newer_socket}'
        
        # Older Docker Desktop or system-wide installation
        legacy_socket = '/var/run/docker.sock'
        if os.path.exists(legacy_socket):
            return f'unix://{legacy_socket}'
        
        logger.warning("Docker socket not found on macOS. Check if Docker Desktop is running.")
        return None
    
    # Linux: Check standard locations
    if system == 'Linux':
        # Standard system-wide socket
        standard_socket = '/var/run/docker.sock'
        if os.path.exists(standard_socket):
            return f'unix://{standard_socket}'
        
        # Rootless Docker: Check XDG_RUNTIME_DIR first
        xdg_runtime = os.getenv('XDG_RUNTIME_DIR')
        if xdg_runtime:
            rootless_socket = os.path.join(xdg_runtime, 'docker.sock')
            if os.path.exists(rootless_socket):
                return f'unix://{rootless_socket}'
        
        # Rootless Docker: Check /run/user/{uid}/docker.sock
        uid = os.getuid()
        user_socket = f'/run/user/{uid}/docker.sock'
        if os.path.exists(user_socket):
            return f'unix://{user_socket}'
        
        # Container: Use standard socket (must be mounted)
        if is_container:
            logger.debug("Running in container, using /var/run/docker.sock (must be mounted from host)")
            return 'unix:///var/run/docker.sock'
        
        logger.warning("Docker socket not found on Linux. Check if Docker is running and socket is accessible.")
        return None
    
    # Unknown platform
    logger.warning(f"Unknown platform '{system}', cannot determine Docker socket path")
    return None


def inject_docker_config_for_stdio_env(env: Dict[str, str]) -> Dict[str, str]:
    """
    Add DOCKER_CONFIG to stdio MCP subprocess env when set in parent process.
    Prevents docker-credential-desktop errors when MCP servers (e.g. npx-based dnstwist)
    run Docker (docker pull) inside containers.
    Apply for ALL stdio servers, not only when command=='docker'.
    Non-intrusive: on any error returns env unchanged; never raises.
    """
    if not isinstance(env, dict):
        logger.debug("inject_docker_config_for_stdio_env: env is not a dict, skipping")
        return env
    try:
        docker_config = os.environ.get('DOCKER_CONFIG')
        if not docker_config:
            try:
                with open('/proc/self/environ', 'rb') as f:
                    env_data = f.read().decode('utf-8', errors='ignore')
                    proc_env = dict(line.split('=', 1) for line in env_data.split('\x00') if '=' in line)
                    docker_config = proc_env.get('DOCKER_CONFIG')
            except (FileNotFoundError, PermissionError, OSError) as e:
                logger.debug("inject_docker_config_for_stdio_env: could not read /proc/self/environ: %s", e)
        if docker_config:
            if os.path.exists(docker_config):
                env['DOCKER_CONFIG'] = docker_config
                logger.debug("Added DOCKER_CONFIG=%s to stdio MCP subprocess env", docker_config)
            else:
                logger.warning(
                    "DOCKER_CONFIG=%s is set but path does not exist; not injecting (Docker subprocesses may use default config)",
                    docker_config,
                )
        else:
            logger.debug("DOCKER_CONFIG not found in process environment; subprocesses will use default Docker config")
    except Exception as e:
        logger.warning(
            "inject_docker_config_for_stdio_env failed (non-fatal, env unchanged): %s",
            e,
            exc_info=False,
        )
    return env


def fix_docker_host_for_mcp_server(env: Dict[str, str], command: str, args: List[str]) -> Dict[str, str]:
    """
    Fix DOCKER_HOST environment variable for ALL Docker-based MCP servers.
    
    This function ensures Docker-based MCP servers use the correct Docker socket path,
    especially when running inside containers. It applies globally to ALL Docker-based
    servers (not just mcp-server-docker) to prevent connection errors.
    
    Key behaviors:
    - When inside a container: Always forces DOCKER_HOST=unix:///var/run/docker.sock
    - When on host: Auto-detects correct socket path for the platform
    - Preserves legitimate remote Docker configurations (SSH/TCP to remote hosts)
    
    Args:
        env: Environment variables dict (will be modified in place)
        command: Command being executed (e.g., 'docker', 'uvx', 'npx', etc.)
        args: Command arguments (e.g., ['run', '...', 'image'] or ['mcp', 'gateway', 'run'])
        
    Returns:
        Modified environment dict with DOCKER_HOST set correctly
    """
    # Check if we're running inside a Docker container
    is_container = os.path.exists('/.dockerenv')
    
    # Check if this is a Docker-based command
    # This includes: docker run, docker exec, docker mcp gateway, etc.
    is_docker_command = command == 'docker'
    
    # If not a Docker command, return early (no fix needed)
    if not is_docker_command:
        return env
    
    current_docker_host = env.get('DOCKER_HOST', '')
    
    # CRITICAL: When inside a container, ALWAYS force DOCKER_HOST to container socket
    # This prevents Docker clients from auto-detecting wrong paths (e.g., macOS paths
    # from mounted ~/.docker directory) and ensures all Docker-based MCP servers work.
    if is_container:
        # Force container socket path - this is the ONLY valid path inside a container
        container_socket = 'unix:///var/run/docker.sock'
        logger.debug(f"[DOCKER_HOST] Container socket: {container_socket}")
        # Only override if current DOCKER_HOST is wrong or not set
        if current_docker_host != container_socket:
            if current_docker_host:
                logger.debug(
                    f"Inside container: Overriding DOCKER_HOST from '{current_docker_host}' "
                    f"to '{container_socket}' for Docker-based MCP server"
                )
            else:
                logger.debug(
                    f"Inside container: Setting DOCKER_HOST={container_socket} "
                    f"for Docker-based MCP server"
                )
            env['DOCKER_HOST'] = container_socket
            logger.info(f"[DOCKER_HOST] Final Container socket set: {container_socket}")
        return env
    
    # When NOT in a container (running on host), handle different DOCKER_HOST scenarios:
    # 1. SSH to localhost (invalid - causes the error we're fixing)
    # 2. SSH to remote host (valid - preserve it)
    # 3. TCP/HTTPS to remote host (valid - preserve it)
    # 4. Unix socket/named pipe (valid - preserve it)
    # 5. Not set or empty (auto-detect local socket)
    
    if current_docker_host.startswith('ssh://'):
        # Check if SSH URL points to localhost (invalid case)
        try:
            parsed = urlparse(current_docker_host)
            hostname = parsed.hostname or ''
            # Check if it's localhost (127.0.0.1, ::1, or 'localhost')
            is_localhost = (
                hostname in ('127.0.0.1', '::1', 'localhost', '') or
                hostname.startswith('127.') or
                hostname.startswith('::')
            )
            
            if is_localhost:
                # Invalid: SSH to localhost doesn't make sense, fix it
                logger.warning(
                    f"DOCKER_HOST is set to SSH URL pointing to localhost '{current_docker_host}', "
                    f"fixing to use Unix socket/named pipe"
                )
                env.pop('DOCKER_HOST', None)
                # Will auto-detect local socket below
            else:
                # Valid: SSH to remote host, preserve it
                logger.debug(f"Preserving remote Docker SSH connection: {current_docker_host}")
                return env
        except Exception as e:
            # If parsing fails, assume it's invalid and fix it
            logger.warning(f"Could not parse DOCKER_HOST '{current_docker_host}': {e}, fixing to use local socket")
            env.pop('DOCKER_HOST', None)
    elif current_docker_host.startswith(('tcp://', 'https://', 'http://')):
        # Valid remote Docker via TCP/HTTPS, preserve it
        logger.debug(f"Preserving remote Docker connection: {current_docker_host}")
        return env
    elif current_docker_host.startswith(('unix://', 'npipe://')):
        # Valid local socket/named pipe, preserve it
        logger.debug(f"Preserving local Docker socket: {current_docker_host}")
        return env
    elif current_docker_host:
        # Unknown format, log warning but preserve it (might be valid)
        logger.warning(f"Unknown DOCKER_HOST format '{current_docker_host}', preserving it")
        return env
    
    # DOCKER_HOST is not set or was invalid (SSH to localhost), auto-detect local socket
    docker_socket = get_docker_socket_path()
    if docker_socket:
        env['DOCKER_HOST'] = docker_socket
        logger.debug(f"Auto-detected and set DOCKER_HOST={docker_socket} for Docker-based MCP server")
    else:
        # If socket not found, unset DOCKER_HOST to let Docker client use defaults
        env.pop('DOCKER_HOST', None)
        logger.warning(
            "Docker socket not found locally and DOCKER_HOST not set. "
            "Docker-based MCP server will use Docker client defaults. "
            "If using remote Docker, set DOCKER_HOST manually."
        )
    
    return env


def get_docker_container_fallback_command(command: str, args: List[str]) -> Tuple[str, List[str]]:
    """
    Implement fallback strategy for Docker containers with name conflicts.
    
    Strategy:
    1. Try docker run (original command) - if container doesn't exist
    2. If container exists and is running, try docker exec (preferred), fallback to attach
    3. If container exists but stopped, start it then attach
    4. If all fails, use unique name for docker run
    
    Args:
        command: Original command (should be 'docker')
        args: Original args (e.g., ['run', '-i', '--rm', '--name', 'container-name', 'image'])
        
    Returns:
        Tuple of (command, args) to use, potentially modified for fallback
    """
    if command != 'docker' or not args or args[0] != 'run':
        # Not a docker run command, return as-is
        return command, args
    
    # Extract container name from args
    container_name = None
    for i, arg in enumerate(args):
        if arg == '--name' and i + 1 < len(args):
            container_name = args[i + 1]
            break
    
    if not container_name:
        # No container name specified, return original
        return command, args
    
    # Check if container exists
    try:
        # Check if container exists (running or stopped)
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', f'name=^{container_name}$', '--format', '{{.Names}}'],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        container_exists = container_name in result.stdout
        
        if container_exists:
            # Check if container is running
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name=^{container_name}$', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            container_running = container_name in result.stdout
            
            if container_running:
                # Container is running - try docker exec first (preferred)
                # For MCP servers, we need to exec the same command the container runs
                # Try to get the container's entrypoint/command
                logger.info(f"Container '{container_name}' is running. Trying 'docker exec' first.")
                try:
                    # Get container's entrypoint and cmd
                    entrypoint_result = subprocess.run(
                        ['docker', 'inspect', '--format', '{{json .Config.Entrypoint}}', container_name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False
                    )
                    cmd_result = subprocess.run(
                        ['docker', 'inspect', '--format', '{{json .Config.Cmd}}', container_name],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=False
                    )
                    
                    # Parse JSON outputs
                    entrypoint = json.loads(entrypoint_result.stdout.strip()) if entrypoint_result.stdout.strip() else []
                    cmd = json.loads(cmd_result.stdout.strip()) if cmd_result.stdout.strip() else []
                    
                    # Build exec command: exec -i container [entrypoint...] [cmd...]
                    exec_args = ['exec', '-i', container_name]
                    if entrypoint:
                        exec_args.extend(entrypoint)
                    if cmd:
                        exec_args.extend(cmd)
                    
                    # If we have a command to exec, use it
                    if len(exec_args) > 3:  # More than just 'exec', '-i', container_name
                        logger.debug(f"Using docker exec with command: {exec_args[3:]}")
                        return 'docker', exec_args
                    else:
                        # No command found, fall through to attach
                        logger.warning(f"Container '{container_name}' has no entrypoint/cmd. Will try attach.")
                except Exception as e:
                    logger.warning(f"Could not get container command for '{container_name}': {e}. Will try attach.")
                
                # Fallback to attach if exec doesn't work or no command found
                logger.info(f"Container '{container_name}' is running. Using 'docker attach' as fallback.")
                attach_args = ['attach', container_name]
                return 'docker', attach_args
            else:
                # Container exists but is stopped - start it first, then attach
                logger.info(f"Container '{container_name}' exists but is stopped. Starting it, then using 'docker attach'.")
                try:
                    start_result = subprocess.run(
                        ['docker', 'start', container_name],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False
                    )
                    if start_result.returncode == 0:
                        # Wait a moment for container to fully start
                        time.sleep(1)
                        attach_args = ['attach', container_name]
                        return 'docker', attach_args
                    else:
                        logger.warning(f"Could not start container '{container_name}': {start_result.stderr}. Will try unique name.")
                        # Fall through to unique name
                except Exception as e:
                    logger.warning(f"Error starting container '{container_name}': {e}. Will try unique name.")
                    # Fall through to unique name
        else:
            # Container doesn't exist, original docker run should work
            return command, args
            
    except Exception as e:
        logger.warning(f"Error checking container status for '{container_name}': {e}. Using original command.")
        # On error, return original - let docker run fail naturally
        return command, args
    
    # If we get here and container exists but start/attach failed, try unique name
    if container_exists:
        logger.info(f"Container '{container_name}' exists but start/attach failed. Using unique name for new container.")
        # Generate unique name
        unique_name = f"{container_name}-{uuid.uuid4().hex[:8]}"
        # Replace --name value in args, preserving ALL other flags (including --platform)
        new_args = []
        skip_next = False
        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                new_args.append(unique_name)
                continue
            if arg == '--name':
                new_args.append(arg)
                skip_next = True
            else:
                new_args.append(arg)  # Preserve all other args including --platform
        return command, new_args
    
    return command, args


def detect_platform_error_and_get_fallback(error: Exception, is_docker_command: bool = False) -> Optional[str]:
    """
    Detect if an error is a Docker platform error and return the fallback platform.
    Handles ExceptionGroup by checking all nested exceptions.
    
    Args:
        error: The exception that occurred (can be ExceptionGroup)
        is_docker_command: If True, treat "Connection closed" as potential platform error for Docker commands
        
    Returns:
        Fallback platform string (e.g., 'linux/amd64' or 'linux/arm64') if platform error detected, None otherwise
    """
    import platform as platform_module
    
    # Extract all error messages including nested exceptions (ExceptionGroup, etc.)
    # Uses cycle detection to prevent infinite recursion on circular exception chains
    def extract_all_messages(exc, visited=None):
        if visited is None:
            visited = set()
        
        # Use id() to track visited exceptions and prevent cycles
        exc_id = id(exc)
        if exc_id in visited:
            # Circular reference detected - return empty to break cycle
            return []
        visited.add(exc_id)
        
        messages = [str(exc).lower()]
        
        # Check for ExceptionGroup nested exceptions
        if hasattr(exc, 'exceptions'):
            for nested in exc.exceptions:
                messages.extend(extract_all_messages(nested, visited))
        
        # Check for __cause__ or __context__
        if hasattr(exc, '__cause__') and exc.__cause__:
            messages.extend(extract_all_messages(exc.__cause__, visited))
        if hasattr(exc, '__context__') and exc.__context__:
            messages.extend(extract_all_messages(exc.__context__, visited))
        
        return messages
    
    all_messages = ' '.join(extract_all_messages(error))
    
    # Debug logging to see what messages were extracted
    logger.debug(f"Platform error detection - extracted messages: {all_messages[:500]}")
    # Docker platform errors can manifest as:
    # 1. Direct "no matching manifest" errors from Docker
    # 2. "manifest" + "platform" keywords together
    # 3. "not found" + "platform" keywords together  
    # 4. "connection closed" can happen when Docker subprocess fails due to platform mismatch
    #    (but we need to be careful - connection closed can happen for other reasons too)
    #    So we only treat it as platform error if we also see platform-related keywords
    is_platform_error = (
        'no matching manifest' in all_messages or
        ('manifest' in all_messages and 'platform' in all_messages) or
        ('not found' in all_messages and 'platform' in all_messages) or
        ('connection closed' in all_messages and any(x in all_messages for x in ['platform', 'manifest', 'no matching'])) or
        # For Docker commands, "Connection closed" often indicates platform mismatch (Docker error in stderr not in exception)
        (is_docker_command and 'connection closed' in all_messages)
    )
    
    if not is_platform_error:
        return None
    
    # Detect host architecture
    host_arch = platform_module.machine().lower()
    is_arm64 = host_arch in ('arm64', 'aarch64')
    is_amd64 = host_arch in ('x86_64', 'amd64')
    
    # Determine fallback platform
    if is_arm64:
        fallback = 'linux/amd64'
        logger.info(f"Platform error detected on ARM64 host, will retry with {fallback}")
    elif is_amd64:
        fallback = 'linux/arm64'
        logger.info(f"Platform error detected on AMD64 host, will retry with {fallback}")
    else:
        logger.warning(f"Platform error detected but unknown host architecture: {host_arch}, no fallback available")
        return None
    
    return fallback


def add_platform_flag_to_docker_args(args: List[str], platform: str) -> List[str]:
    """
    Add --platform flag to Docker run args if not already present.
    
    Args:
        args: Docker command arguments (e.g., ['run', '-i', '--rm', 'image:tag'])
        platform: Platform to use (e.g., 'linux/amd64')
        
    Returns:
        New args list with platform flag added
    """
    if '--platform' in args:
        logger.debug(f"Platform flag already exists in args, not adding")
        return args
    
    # Find where to insert (after 'run' but before image name)
    # Platform flag must come before the image name
    insert_idx = 1
    new_args = args.copy()
    new_args.insert(insert_idx, '--platform')
    new_args.insert(insert_idx + 1, platform)
    logger.debug(f"Added --platform {platform} to Docker args at index {insert_idx}")
    return new_args


def add_platform_flag_to_connections(connections: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """
    Add --platform flag to Docker stdio connections in connections dict.
    
    Args:
        connections: Connections dict for MultiServerMCPClient
        platform: Platform string (e.g., 'linux/amd64')
        
    Returns:
        New connections dict with platform flags added (does not modify original)
    """
    if not connections:
        return {}
    
    retry_connections = {}
    for server_name, conn_config in connections.items():
        if not isinstance(conn_config, dict):
            # Not a dict, preserve as-is
            retry_connections[server_name] = conn_config
            continue
            
        try:
            conn_config = conn_config.copy()
            command = conn_config.get('command', '')
            args = conn_config.get('args', [])
            
            # Only modify Docker run commands
            if command == 'docker' and isinstance(args, list) and args and args[0] == 'run':
                # Check if platform flag already exists
                if '--platform' not in args:
                    new_args = add_platform_flag_to_docker_args(args, platform)
                    conn_config['args'] = new_args
                    logger.warning(f"Added --platform {platform} to {server_name} for platform error retry")
        except Exception as e:
            # If anything fails, preserve original config
            logger.warning(f"Error adding platform flag to {server_name}: {e}, preserving original config")
        
        retry_connections[server_name] = conn_config
    
    return retry_connections


async def get_tools_with_platform_fallback(
    mcp_client: Any,
    connections: Dict[str, Any],
    max_retries: int = 1
) -> List[Any]:
    """
    Get tools from MCP client with automatic platform error retry.
    
    Handles both regular exceptions and ExceptionGroup (Python 3.11+).
    If a platform error is detected, retries with --platform flag added to Docker connections.
    
    Args:
        mcp_client: MultiServerMCPClient instance
        connections: Original connections dict (for retry)
        max_retries: Maximum retry attempts (1 for UI, 2 for chat-sd)
    
    Returns:
        List of tools
        
    Raises:
        Original exception if not a platform error or all retries fail
    """
    # Import MultiServerMCPClient at function level (may not be available in all contexts)
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError:
        logger.error("Failed to import MultiServerMCPClient - platform fallback will not work")
        # Fallback: just call get_tools() without retry
        return await mcp_client.get_tools()
    
    # Validate inputs
    if not connections:
        logger.debug("Empty connections dict, calling get_tools() directly")
        return await mcp_client.get_tools()
    
    # Check if any connection is Docker-based
    has_docker_connection = any(
        isinstance(conn, dict) and conn.get('command') == 'docker'
        for conn in connections.values()
    )
    
    # First attempt
    try:
        return await mcp_client.get_tools()
    except BaseExceptionGroup as eg:
        # Handle ExceptionGroup (Python 3.12+)
        # Check each exception in the group for platform errors
        platform_error_found = False
        fallback_platform = None
        
        for exc in eg.exceptions:
            fallback = detect_platform_error_and_get_fallback(exc, is_docker_command=has_docker_connection)
            if fallback:
                platform_error_found = True
                fallback_platform = fallback
                break
        
        if not platform_error_found:
            # Not a platform error, re-raise original ExceptionGroup
            raise
        
        # Platform error detected, retry with platform flag
        logger.warning(f"Platform error detected in ExceptionGroup, retrying with --platform {fallback_platform} (attempt 1/{max_retries})")
        
        # Check if platform flag already exists in any connection
        has_platform_flag = any(
            isinstance(conn, dict) and '--platform' in conn.get('args', [])
            for conn in connections.values()
        )
        if has_platform_flag:
            logger.warning("Platform flag already exists in connections, cannot retry")
            raise
        
        # Retry with platform flag
        for attempt in range(1, max_retries + 1):
            try:
                retry_connections = add_platform_flag_to_connections(connections, fallback_platform)
                if not retry_connections:
                    logger.error("Failed to build retry connections, cannot retry")
                    raise eg
                retry_client = MultiServerMCPClient(retry_connections)
                tools = await retry_client.get_tools()
                logger.warning(f"Platform error retry succeeded with --platform {fallback_platform} (attempt {attempt})")
                return tools
            except Exception as retry_error:
                if attempt < max_retries:
                    logger.warning(f"Platform error retry {attempt} failed, retrying again (attempt {attempt + 1}/{max_retries}): {retry_error}")
                else:
                    logger.error(f"Platform error retry failed after {max_retries} attempt(s): {retry_error}")
                    # Re-raise original ExceptionGroup
                    raise eg
        
        # Should not reach here, but just in case
        raise eg
        
    except Exception as e:
        # Handle regular exceptions
        fallback_platform = detect_platform_error_and_get_fallback(e, is_docker_command=has_docker_connection)
        
        if not fallback_platform:
            # Not a platform error, re-raise original exception
            raise
        
        # Platform error detected, retry with platform flag
        logger.warning(f"Platform error detected, retrying with --platform {fallback_platform} (attempt 1/{max_retries})")
        
        # Check if platform flag already exists in any connection
        has_platform_flag = any(
            isinstance(conn, dict) and '--platform' in conn.get('args', [])
            for conn in connections.values()
        )
        if has_platform_flag:
            logger.warning("Platform flag already exists in connections, cannot retry")
            raise
        
        # Retry with platform flag
        for attempt in range(1, max_retries + 1):
            try:
                retry_connections = add_platform_flag_to_connections(connections, fallback_platform)
                if not retry_connections:
                    logger.error("Failed to build retry connections, cannot retry")
                    raise e
                retry_client = MultiServerMCPClient(retry_connections)
                tools = await retry_client.get_tools()
                logger.warning(f"Platform error retry succeeded with --platform {fallback_platform} (attempt {attempt})")
                return tools
            except Exception as retry_error:
                if attempt < max_retries:
                    logger.warning(f"Platform error retry {attempt} failed, retrying again (attempt {attempt + 1}/{max_retries}): {retry_error}")
                else:
                    logger.error(f"Platform error retry failed after {max_retries} attempt(s): {retry_error}")
                    # Re-raise original exception
                    raise e
        
        # Should not reach here, but just in case
        raise e

