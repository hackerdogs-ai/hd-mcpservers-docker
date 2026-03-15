"""
Docker Client for OSINT Tools

This module provides a Docker-based execution layer for OSINT binary tools. Those
tools are LangChain tools (not MCP servers): they run in-process in the chat-solo
Celery worker. This client runs there and uses the host Docker daemon (via mounted
socket) to start/exec the project's internal osint-tools container. OCR and similar
features are MCP servers (separate containers, invoked via MCP); they do not use
this client. See docs/docker for socket and DOCKER_GID setup.
"""

import os
import json
import subprocess
import shutil
from typing import Optional, Dict, Any, List
from hd_logging import setup_logger

logger = setup_logger(__name__, log_file_path="logs/docker_client.log")


class DockerOSINTClient:
    """
    Docker client for executing OSINT tools in containers.
    
    This client manages Docker container lifecycle and executes tools
    via `docker exec` commands. It automatically handles:
    - Container creation/startup
    - Tool execution
    - Output parsing
    - Error handling
    
    Container Lifecycle:
    - By default, containers are PERSISTENT (reused for performance)
    - Use cleanup() to stop and remove containers
    - Official Docker images (subfinder, nuclei) auto-cleanup with --rm
    """
    
    def __init__(
        self,
        image_name: Optional[str] = None,
        container_name: str = "osint-tools",
        docker_runtime: str = "docker",
        auto_start: bool = True,
        workspace: str = "/tmp/osint-workspace"
    ):
        """
        Initialize Docker OSINT client.
        
        This client works both on host and inside Docker containers.
        When running in a container, ensure Docker socket is mounted:
        -v /var/run/docker.sock:/var/run/docker.sock
        
        Args:
            image_name: Docker image name (default: from env or "hackerdogs/osint-tools:latest")
            container_name: Container name to use/create
            docker_runtime: Docker runtime ("docker" or "podman")
            auto_start: Automatically start container if not running
            workspace: Host workspace directory to mount
        """
        # Default to hackerdogs registry image, but allow override via env var
        default_image = os.getenv("OSINT_DOCKER_IMAGE", "hackerdogs/osint-tools:latest")
        self.image_name = image_name or default_image
        self.container_name = container_name
        self.docker_runtime = docker_runtime
        self.auto_start = auto_start
        self.workspace = workspace
        
        # Detect if running in Docker container
        self.in_container = os.path.exists("/.dockerenv")
        self.docker_socket = "/var/run/docker.sock"
        
        # Check if Docker is available
        self.docker_available = self._check_docker_available()
        
        if self.docker_available:
            execution_context = "container" if self.in_container else "host"
            logger.info(f"[DockerOSINTClient] Initialized (default container for tools without official images) | "
                       f"default_image={self.image_name}, container={self.container_name}, "
                       f"context={execution_context}, "
                       f"note=Tools with official Docker images (sherlock, maigret, nuclei, etc.) use their own images, not this default")
            
            if self.in_container:
                # Check if Docker socket is mounted (recommended for container execution)
                if os.path.exists(self.docker_socket):
                    logger.debug("[DockerOSINTClient] Docker socket mounted - can control host Docker")
                else:
                    logger.info("[DockerOSINTClient] Running in container without socket mount - using docker command")
        else:
            if self.in_container:
                logger.error("[DockerOSINTClient] Docker not available in container. "
                           "Mount Docker socket: -v /var/run/docker.sock:/var/run/docker.sock")
            else:
                logger.error("[DockerOSINTClient] Docker not available on host")
    
    def _check_docker_available(self) -> bool:
        """Check if Docker/Podman is available and running."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "ps"],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _container_exists(self) -> bool:
        """Check if container exists."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "ps", "-a", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return self.container_name in result.stdout
        except Exception:
            return False
    
    def _container_running(self) -> bool:
        """Check if container is running."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return self.container_name in result.stdout
        except Exception:
            return False
    
    def _image_exists_locally(self, image_name: str) -> bool:
        """Check if Docker image exists locally."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "images", "-q", image_name],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            return bool(result.stdout.strip())
        except Exception:
            return False
    
    def _get_registry_image_name(self, image_name: str) -> str:
        """
        Get the registry image name for pulling.
        
        If image_name is 'osint-tools:latest' (no registry prefix),
        returns 'hackerdogs/osint-tools:latest' for pulling from Docker Hub.
        Otherwise returns the image_name as-is.
        """
        # If image already has a registry prefix (contains '/'), use as-is
        if '/' in image_name:
            return image_name
        
        # For 'osint-tools:latest', try hackerdogs registry
        if image_name == "osint-tools:latest" or image_name.startswith("osint-tools:"):
            # Extract tag if present, default to 'latest'
            tag = image_name.split(':')[1] if ':' in image_name else 'latest'
            return f"hackerdogs/osint-tools:{tag}"
        
        # For other images without registry, return as-is (Docker will try Docker Hub)
        return image_name
    
    def _pull_image(self, image_name: str) -> bool:
        """Pull Docker image from registry."""
        registry_image = self._get_registry_image_name(image_name)
        
        logger.info(f"[DockerOSINTClient] Pulling image | local_name={image_name}, registry_name={registry_image}")
        
        try:
            result = subprocess.run(
                [self.docker_runtime, "pull", registry_image],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout for large images
                check=False
            )
            
            if result.returncode == 0:
                # If we pulled from a different name, tag it with the expected name
                if registry_image != image_name:
                    logger.info(f"[DockerOSINTClient] Tagging image | from={registry_image}, to={image_name}")
                    tag_result = subprocess.run(
                        [self.docker_runtime, "tag", registry_image, image_name],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False
                    )
                    if tag_result.returncode == 0:
                        logger.info(f"[DockerOSINTClient] Image tagged successfully | {image_name}")
                    else:
                        logger.warning(
                            f"[DockerOSINTClient] Failed to tag image, but pull succeeded | "
                            f"registry_image={registry_image}, requested_name={image_name}, error={tag_result.stderr}"
                        )
                        # Verify registry image exists (it should, since pull succeeded)
                        if self._image_exists_locally(registry_image):
                            logger.info(
                                f"[DockerOSINTClient] Image available with registry name | {registry_image}. "
                                f"Container will use this name if {image_name} is not available."
                            )
                        # Still return True since the image is available with registry name
                
                logger.info(f"[DockerOSINTClient] Image pulled successfully | {registry_image}")
                return True
            else:
                logger.error(f"[DockerOSINTClient] Failed to pull image | registry_name={registry_image}, error={result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"[DockerOSINTClient] Image pull timed out | registry_name={registry_image}")
            return False
        except Exception as e:
            logger.error(f"[DockerOSINTClient] Error pulling image: {str(e)}", exc_info=True)
            return False
    
    def _ensure_image(self) -> bool:
        """
        Ensure Docker image exists locally, pulling from registry if needed.
        
        Returns:
            True if image exists locally (or was successfully pulled), False otherwise
        """
        # Check if image exists locally
        if self._image_exists_locally(self.image_name):
            logger.debug(f"[DockerOSINTClient] Image exists locally | {self.image_name}")
            return True
        
        # Image not found locally, try to pull from registry
        logger.info(f"[DockerOSINTClient] Image not found locally, attempting to pull | {self.image_name}")
        return self._pull_image(self.image_name)
    
    def _ensure_container(self) -> bool:
        """Ensure container exists and is running."""
        if not self.docker_available:
            return False
        
        # Check if container exists
        if not self._container_exists():
            logger.info(f"[DockerOSINTClient] Creating container: {self.container_name}")
            return self._create_container()
        
        # Check if container is running
        if not self._container_running():
            if self.auto_start:
                logger.info(f"[DockerOSINTClient] Starting container: {self.container_name}")
                return self._start_container()
            else:
                logger.error(f"[DockerOSINTClient] Container exists but not running: {self.container_name}")
                return False
        
        return True
    
    def _create_container(self) -> bool:
        """Create Docker container."""
        try:
            # Ensure image exists locally (pull from registry if needed)
            if not self._ensure_image():
                error_msg = (
                    f"Failed to ensure Docker image '{self.image_name}' is available. "
                    f"Please ensure the image exists locally or can be pulled from Docker Hub. "
                    f"If using hackerdogs registry, ensure you're logged in: docker login"
                )
                logger.error(f"[DockerOSINTClient] {error_msg}")
                return False
            
            # Determine which image name to use for container creation
            # Prefer the requested image name, but fall back to registry name if needed
            image_to_use = self.image_name
            if not self._image_exists_locally(self.image_name):
                registry_image = self._get_registry_image_name(self.image_name)
                if self._image_exists_locally(registry_image):
                    logger.info(
                        f"[DockerOSINTClient] Using registry image name for container | "
                        f"requested={self.image_name}, using={registry_image}"
                    )
                    image_to_use = registry_image
                else:
                    logger.error(
                        f"[DockerOSINTClient] Neither requested nor registry image found | "
                        f"requested={self.image_name}, registry={registry_image}"
                    )
                    return False
            
            # Create workspace directory
            os.makedirs(self.workspace, exist_ok=True)
            
            cmd = [
                self.docker_runtime, "run",
                "-d",
                "--name", self.container_name,
                "-v", f"{os.path.abspath(self.workspace)}:/workspace",
                "--restart", "unless-stopped",
                image_to_use
            ]
            
            logger.debug(f"[DockerOSINTClient] Creating container | cmd={' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"[DockerOSINTClient] Container created: {self.container_name}")
                return True
            else:
                logger.error(f"[DockerOSINTClient] Failed to create container: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"[DockerOSINTClient] Error creating container: {str(e)}", exc_info=True)
            return False
    
    def _start_container(self) -> bool:
        """Start existing container."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "start", self.container_name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"[DockerOSINTClient] Container started: {self.container_name}")
                return True
            else:
                logger.error(f"[DockerOSINTClient] Failed to start container: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"[DockerOSINTClient] Error starting container: {str(e)}", exc_info=True)
            return False
    
    def execute(
        self,
        tool: str,
        args: List[str],
        timeout: Optional[int] = None,
        workdir: str = "/workspace",
        capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool command in the Docker container.
        
        Args:
            timeout: Execution timeout in seconds. If None, uses DOCKER_TOOL_EXECUTION_TIMEOUT env var (default: 300)
        Execute a tool in the Docker container.
        
        Args:
            tool: Tool name (e.g., "amass", "nuclei")
            args: List of arguments for the tool
            timeout: Execution timeout in seconds
            workdir: Working directory inside container
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            Dictionary with:
            - status: "success" or "error"
            - stdout: Standard output (if capture_output=True)
            - stderr: Standard error (if capture_output=True)
            - returncode: Exit code
            - execution_time: Execution time in seconds
        """
        if not self.docker_available:
            return {
                "status": "error",
                "message": "Docker not available",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }
        
        if not self._ensure_container():
            return {
                "status": "error",
                "message": f"Failed to ensure container {self.container_name} is running",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }
        
        # Get timeout from parameter or environment variable (default: 300 seconds)
        if timeout is None:
            timeout = int(os.getenv("DOCKER_TOOL_EXECUTION_TIMEOUT", "300"))
        
        import time
        start_time = time.time()
        
        try:
            # Build docker exec command
            cmd = [
                self.docker_runtime, "exec",
                "-w", workdir,
                self.container_name,
                tool
            ] + args
            
            logger.debug(f"[DockerOSINTClient] Executing | tool={tool}, args={args}")
            
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False
            )
            
            execution_time = time.time() - start_time
            
            response = {
                "status": "success" if result.returncode == 0 else "error",
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "returncode": result.returncode,
                "execution_time": execution_time
            }
            
            logger.info(f"[DockerOSINTClient] Execution complete | tool={tool}, returncode={result.returncode}, time={execution_time}")
            
            return response
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            logger.error(f"[DockerOSINTClient] Execution timed out | tool={tool}, timeout={timeout}")
            return {
                "status": "error",
                "message": f"Execution timed out after {timeout} seconds",
                "stdout": "",
                "stderr": "",
                "returncode": -1,
                "execution_time": execution_time
            }
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"[DockerOSINTClient] Execution error: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "stdout": "",
                "stderr": "",
                "returncode": -1,
                "execution_time": execution_time
            }
    
    def stop_container(self) -> bool:
        """Stop the container."""
        if not self.docker_available:
            return False
        
        if not self._container_running():
            logger.info(f"[DockerOSINTClient] Container not running: {self.container_name}")
            return True
        
        try:
            result = subprocess.run(
                [self.docker_runtime, "stop", self.container_name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"[DockerOSINTClient] Container stopped: {self.container_name}")
                return True
            else:
                logger.error(f"[DockerOSINTClient] Failed to stop container: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"[DockerOSINTClient] Error stopping container: {str(e)}", exc_info=True)
            return False
    
    def remove_container(self) -> bool:
        """Remove the container (must be stopped first)."""
        if not self.docker_available:
            return False
        
        if self._container_running():
            logger.error(f"[DockerOSINTClient] Cannot remove running container. Stop it first: {self.container_name}")
            return False
        
        if not self._container_exists():
            logger.info(f"[DockerOSINTClient] Container does not exist: {self.container_name}")
            return True
        
        try:
            result = subprocess.run(
                [self.docker_runtime, "rm", self.container_name],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"[DockerOSINTClient] Container removed: {self.container_name}")
                return True
            else:
                logger.error(f"[DockerOSINTClient] Failed to remove container: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"[DockerOSINTClient] Error removing container: {str(e)}", exc_info=True)
            return False
    
    def cleanup(self) -> bool:
        """Stop and remove the container (full cleanup)."""
        if not self.docker_available:
            return False
        
        stopped = self.stop_container()
        if stopped:
            return self.remove_container()
        return False
    
    def test(self) -> Dict[str, Any]:
        """Test Docker setup by running a simple command."""
        result = self.execute("echo", ["test"], timeout=5)
        return {
            "docker_available": self.docker_available,
            "container_exists": self._container_exists() if self.docker_available else False,
            "container_running": self._container_running() if self.docker_available else False,
            "test_execution": result
        }


# Global instance (lazy initialization)
_docker_client: Optional[DockerOSINTClient] = None


def get_docker_client() -> Optional[DockerOSINTClient]:
    """Get or create global Docker client instance."""
    global _docker_client
    if _docker_client is None:
        _docker_client = DockerOSINTClient()
    return _docker_client


def execute_in_docker(
    tool: str,
    args: List[str],
    timeout: Optional[int] = None,
    volumes: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    platform: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute a tool in Docker.
    
    This function first checks if the tool has an official Docker image.
    If available, uses the official image. Otherwise, uses the custom osint-tools container.
    
    Official images supported:
    - subfinder: projectdiscovery/subfinder:latest
    - nuclei: projectdiscovery/nuclei:latest
    - amass: owaspamass/amass:latest (Official OWASP Amass image)
    
    Args:
        tool: Tool name
        args: Tool arguments
        timeout: Execution timeout
        volumes: Optional list of volume mounts (format: "host_path:container_path")
    
    Returns:
        Execution result dictionary
    """
    # Get timeout from parameter or environment variable (default: 300 seconds)
    if timeout is None:
        timeout = int(os.getenv("DOCKER_TOOL_EXECUTION_TIMEOUT", "300"))
    
    # Check for official Docker images
    official_images = {
        "subfinder": "projectdiscovery/subfinder:latest",
        "nuclei": "projectdiscovery/nuclei:latest",
        "amass": "owaspamass/amass:latest",  # Official OWASP Amass image
        "sherlock": "sherlock/sherlock:latest",  # Official Sherlock image
        "maigret": "soxoj/maigret:latest",  # Official Maigret image
        "phoneinfoga": "sundowndev/phoneinfoga:latest",  # Official PhoneInfoga image (may require linux/amd64 on Apple Silicon)
        # Certificate graph / CT enumeration
        # Image entrypoint is `certgraph`, so args should be certgraph CLI flags + HOST.
        "certgraph": "ghcr.io/lanrat/certgraph:latest",
    }
    
    # Try official image first if available
    if tool in official_images:
        official_image = official_images[tool]
        logger.info(f"[execute_in_docker] Using official Docker image | tool={tool}, image={official_image}, execution_method=docker run")
        return execute_official_docker_image(
            official_image,
            args,
            timeout=timeout,
            volumes=volumes,
            env=env,
            platform=platform,
        )
    
    # Fall back to custom container
    logger.info(f"[execute_in_docker] Using custom container | tool={tool}, container=osint-tools, execution_method=docker exec")
    client = get_docker_client()
    if client is None:
        return {
            "status": "error",
            "message": "Docker client not available",
            "stdout": "",
            "stderr": "",
            "returncode": -1
        }
    return client.execute(tool, args, timeout=timeout)


def execute_official_docker_image(
    image: str,
    args: List[str],
    timeout: Optional[int] = None,
    docker_runtime: str = "docker",
    volumes: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    platform: Optional[str] = None,
    tty: bool = False,
) -> Dict[str, Any]:
    """
    Execute a command using an official Docker image (docker run).
    
    This is preferred for tools with official images as they are:
    - Always up-to-date
    
    Args:
        timeout: Execution timeout in seconds. If None, uses DOCKER_TOOL_EXECUTION_TIMEOUT env var (default: 300)
    - Maintained by the tool authors
    - No need to build custom images
    
    Reference: https://docs.projectdiscovery.io/opensource/subfinder/running
    
    Args:
        image: Docker image name (e.g., "projectdiscovery/subfinder:latest")
        args: Command arguments
        timeout: Execution timeout
        docker_runtime: Docker runtime ("docker" or "podman")
        volumes: Optional list of volume mounts (e.g., ["/host/path:/container/path:ro"])
    
    Returns:
        Execution result dictionary
    """
    import time
    import os
    start_time = time.time()
    
    # Get timeout from parameter or environment variable (default: 300 seconds)
    if timeout is None:
        timeout = int(os.getenv("DOCKER_TOOL_EXECUTION_TIMEOUT", "300"))

    def _redact_args(cli_args: List[str]) -> List[str]:
        """
        Redact sensitive CLI args from logs.

        Some tools pass secrets via CLI flags (e.g. certgraph -censys-secret <secret>).
        Never log these values.
        """
        if not cli_args:
            return []

        redact_next_for = {
            "-censys-secret",
            "--censys-secret",
        }
        out: List[str] = []
        i = 0
        while i < len(cli_args):
            a = cli_args[i]
            out.append(a)
            if a in redact_next_for and i + 1 < len(cli_args):
                out.append("***REDACTED***")
                i += 2
                continue
            i += 1
        return out
    
    try:
        # Build docker run command
        # Use --rm to auto-remove container after execution
        cmd = [
            docker_runtime, "run",
            "--rm",
            "-i",  # Interactive mode for stdin
        ]

        # Optional pseudo-TTY (some tools format output differently / require it)
        if tty:
            cmd.append("-t")

        # Optional platform (useful on Apple Silicon when upstream image is amd64-only)
        if platform:
            cmd.extend(["--platform", platform])
        
        # Add volume mounts if provided
        if volumes:
            for volume in volumes:
                cmd.extend(["-v", volume])
        else:
            # Auto-mount subfinder config if it exists
            home = os.path.expanduser("~")
            config_dir = os.path.join(home, ".config", "subfinder")
            if os.path.exists(config_dir):
                # Mount config directory to default location in container
                cmd.extend(["-v", f"{config_dir}:/root/.config/subfinder:ro"])

        # Add environment variables if provided.
        # IMPORTANT: Do not log env values (may contain secrets).
        if env:
            for k, v in env.items():
                # If caller passes None values, skip them
                if v is None:
                    continue
                cmd.extend(["-e", f"{k}={v}"])
        
        cmd.append(image)
        cmd.extend(args)
        
        redacted_args = _redact_args(args)
        logger.debug(
            f"[execute_official_docker_image] Running | image={image}, args={redacted_args}, "
            f"platform={platform if platform else 'default'}, "
            f"env_keys={list(env.keys()) if env else []}"
        )
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        
        execution_time = time.time() - start_time
        
        response = {
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "execution_time": execution_time,
            "execution_method": "official_docker_image"
        }
        
        logger.info(f"[execute_official_docker_image] Execution complete | image={image}, returncode={result.returncode}, time={execution_time}")
        
        return response
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        logger.error(f"[execute_official_docker_image] Execution timed out | image={image}, timeout={timeout}")
        return {
            "status": "error",
            "message": f"Execution timed out after {timeout} seconds",
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "execution_time": execution_time,
            "execution_method": "official_docker_image"
        }
    except FileNotFoundError:
        logger.error(f"[execute_official_docker_image] Docker not found | docker_runtime={docker_runtime}")
        return {
            "status": "error",
            "message": f"{docker_runtime} not found. Please install Docker.",
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "execution_time": 0,
            "execution_method": "official_docker_image"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"[execute_official_docker_image] Execution error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "stdout": "",
            "stderr": "",
            "returncode": -1,
            "execution_time": execution_time,
            "execution_method": "official_docker_image"
        }

