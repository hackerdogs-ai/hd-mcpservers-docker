"""
MCP Docker Client - Generic Docker Wrapper for MCP Servers

This module provides a generic Docker-based execution layer for MCP servers.
It can dynamically build Docker images and run MCP servers in isolated containers.

Features:
- Dynamic Docker image building from MCP server definitions
- On-demand container creation and execution
- Automatic cleanup of temporary containers
- Support for pip-installable MCP servers
- Custom Dockerfile generation for complex setups
"""

import os
import json
import subprocess
import tempfile
import shutil
from typing import Optional, Dict, Any, List
from pathlib import Path
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

logger = setup_logger(__name__, log_file_path="logs/mcp_docker_client.log")


class MCPDockerClient:
    """
    Docker client for executing MCP servers in containers.
    
    This client manages Docker image building and container lifecycle for MCP servers.
    It automatically handles:
    - Dynamic Docker image building
    - Container creation/startup
    - MCP server execution via stdio
    - Output parsing
    - Error handling
    - Cleanup
    """
    
    def __init__(
        self,
        docker_runtime: str = "docker",
        build_cache_dir: Optional[str] = None,
        image_prefix: str = "hackerdogs-mcp",
        dockerhub_username: str = "hackerdogs"
    ):
        """
        Initialize MCP Docker client.
        
        Args:
            docker_runtime: Docker runtime ("docker" or "podman")
            build_cache_dir: Directory to cache Dockerfiles and build contexts
            image_prefix: Prefix for built Docker images
            dockerhub_username: Docker Hub username for pulling pre-built images
        """
        self.docker_runtime = docker_runtime
        self.image_prefix = image_prefix
        self.dockerhub_username = dockerhub_username
        self.build_cache_dir = build_cache_dir or os.path.join(
            os.path.expanduser("~"), ".hackerdogs", "mcp-docker-builds"
        )
        os.makedirs(self.build_cache_dir, exist_ok=True)
        
        # Check if Docker is available
        self.docker_available = self._check_docker_available()
        
        if self.docker_available:
            logger.info(f"[MCPDockerClient] Initialized | runtime={docker_runtime}, cache_dir={self.build_cache_dir}, dockerhub={dockerhub_username}")
        else:
            logger.error("[MCPDockerClient] Docker not available")
    
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
    
    def _image_exists(self, image_name: str) -> bool:
        """Check if Docker image exists."""
        try:
            result = subprocess.run(
                [self.docker_runtime, "image", "inspect", image_name],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _pull_image_from_dockerhub(self, image_name: str) -> bool:
        """
        Pull Docker image from Docker Hub.
        
        Args:
            image_name: Local image name (e.g., "hackerdogs-mcp-rss-mcp:latest" or "rss-mcp:latest")
        
        Returns:
            True if pull succeeded, False otherwise
        """
        if not self.docker_available:
            return False
        
        # Construct Docker Hub image name
        # For RSS container: use hackerdogs/{name} format
        # For others: use hackerdogs/{local-image-name} format
 
            # Other containers use hackerdogs/{local-image-name} format
        dockerhub_image = f"{self.dockerhub_username}/{image_name}"
        
        try:
            logger.info(f"[MCPDockerClient] Pulling image from Docker Hub: {dockerhub_image}")
            result = subprocess.run(
                [self.docker_runtime, "pull", dockerhub_image],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for pulls
                check=False
            )
            
            if result.returncode == 0:
                # Tag the pulled image with the local name
                logger.info(f"[MCPDockerClient] Tagging pulled image as {image_name}")
                tag_result = subprocess.run(
                    [self.docker_runtime, "tag", dockerhub_image, image_name],
                    capture_output=True,
                    timeout=10,
                    check=False
                )
                
                if tag_result.returncode == 0:
                    logger.info(f"[MCPDockerClient] ✅ Successfully pulled and tagged image: {image_name}")
                    return True
                else:
                    logger.warning(f"[MCPDockerClient] Pull succeeded but tagging failed: {tag_result.stderr}")
                    return False
            else:
                logger.debug(f"[MCPDockerClient] Image not found on Docker Hub: {dockerhub_image} (will build locally)")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning(f"[MCPDockerClient] Pull timed out for {dockerhub_image}")
            return False
        except Exception as e:
            logger.debug(f"[MCPDockerClient] Error pulling from Docker Hub: {e}")
            return False
    
    def _build_image_from_pip(
        self,
        package_name: str,
        image_name: str,
        base_image: str = "python:3.11-slim",
        additional_packages: Optional[List[str]] = None,
        entrypoint: Optional[str] = None
    ) -> bool:
        """
        Build Docker image from a pip-installable package.
        
        Args:
            package_name: PyPI package name (e.g., "mcp-ocr")
            image_name: Docker image name to build
            base_image: Base Docker image
            additional_packages: Additional system packages to install
            entrypoint: Custom entrypoint command (default: python -m <package_name>)
        
        Returns:
            True if build succeeded, False otherwise
        """
        if not self.docker_available:
            logger.error("[MCPDockerClient] Docker not available for building")
            return False
        
        # Create temporary build directory
        build_dir = os.path.join(self.build_cache_dir, package_name.replace("-", "_"))
        os.makedirs(build_dir, exist_ok=True)
        
        # Generate Dockerfile
        dockerfile_path = os.path.join(build_dir, "Dockerfile")
        
        # Determine entrypoint
        if entrypoint is None:
            # Try to infer module name from package name
            module_name = package_name.replace("-", "_")
            entrypoint = f"python -m {module_name}"
        
        # Generate Dockerfile content
        dockerfile_content = f"""FROM {base_image}

# Install system dependencies if needed
"""
        
        # Add system packages if specified
        if additional_packages:
            packages_str = " ".join(additional_packages)
            dockerfile_content += f"""RUN apt-get update && apt-get install -y \\
    {packages_str} \\
    && rm -rf /var/lib/apt/lists/*
"""
        
        # Install Python package
        dockerfile_content += f"""
# Install MCP server package
RUN pip install --no-cache-dir {package_name}

        # Set entrypoint
"""
        
        # Format entrypoint properly for Docker (support multiple arguments)
        entrypoint_parts = entrypoint.split()
        if len(entrypoint_parts) == 1:
            dockerfile_content += f'ENTRYPOINT ["{entrypoint_parts[0]}"]\n'
        else:
            # Format as JSON array for ENTRYPOINT
            entrypoint_json = json.dumps(entrypoint_parts)
            dockerfile_content += f'ENTRYPOINT {entrypoint_json}\n'
        
        # Write Dockerfile
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        
        logger.info(f"[MCPDockerClient] Building image | package={package_name}, image={image_name}")
        logger.debug(f"[MCPDockerClient] Dockerfile content:\n{dockerfile_content}")
        
        # Build image
        try:
            cmd = [
                self.docker_runtime, "build",
                "-t", image_name,
                "-f", dockerfile_path,
                build_dir
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for builds
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"[MCPDockerClient] Image built successfully | image={image_name}")
                return True
            else:
                logger.error(f"[MCPDockerClient] Build failed | stderr={result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"[MCPDockerClient] Build timed out | package={package_name}")
            return False
        except Exception as e:
            logger.error(f"[MCPDockerClient] Build error: {str(e)}", exc_info=True)
            return False
    
    def _build_image_from_npm(
        self,
        package_name: str,
        image_name: str,
        base_image: str = "node:20-slim",
        additional_packages: Optional[List[str]] = None,
        entrypoint: Optional[str] = None
    ) -> bool:
        """
        Build Docker image from an npm-installable package.
        
        Args:
            package_name: npm package name (e.g., "@sylphx/pdf-reader-mcp")
            image_name: Docker image name to build
            base_image: Base Docker image (default: node:20-slim)
            additional_packages: Additional system packages to install
            entrypoint: Custom entrypoint command (default: npx <package_name>)
        
        Returns:
            True if build succeeded, False otherwise
        """
        if not self.docker_available:
            logger.error("[MCPDockerClient] Docker not available for building")
            return False
        
        # Create temporary build directory
        build_dir = os.path.join(self.build_cache_dir, package_name.replace("@", "").replace("/", "_").replace("-", "_"))
        os.makedirs(build_dir, exist_ok=True)
        
        # Generate Dockerfile
        dockerfile_path = os.path.join(build_dir, "Dockerfile")
        
        # Determine entrypoint
        if entrypoint is None:
            entrypoint = f"npx {package_name}"
        
        # Generate Dockerfile content
        dockerfile_content = f"""FROM {base_image}

# Install system dependencies if needed
"""
        
        # Add system packages if specified
        if additional_packages:
            packages_str = " ".join(additional_packages)
            dockerfile_content += f"""RUN apt-get update && apt-get install -y \\
    {packages_str} \\
    && rm -rf /var/lib/apt/lists/*
"""
        
        # Install npm package globally (npx will use it)
        dockerfile_content += f"""
# Install MCP server package globally
RUN npm install -g {package_name}

# Set entrypoint
"""
        
        # Format entrypoint properly for Docker
        entrypoint_parts = entrypoint.split()
        if len(entrypoint_parts) == 1:
            dockerfile_content += f'ENTRYPOINT ["{entrypoint_parts[0]}"]\n'
        else:
            entrypoint_json = json.dumps(entrypoint_parts)
            dockerfile_content += f'ENTRYPOINT {entrypoint_json}\n'
        
        # Write Dockerfile
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        
        logger.info(f"[MCPDockerClient] Building image | package={package_name}, image={image_name}")
        logger.debug(f"[MCPDockerClient] Dockerfile content:\n{dockerfile_content}")
        
        # Build image
        try:
            cmd = [
                self.docker_runtime, "build",
                "-t", image_name,
                "-f", dockerfile_path,
                build_dir
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"[MCPDockerClient] Image built successfully | image={image_name}")
                return True
            else:
                logger.error(f"[MCPDockerClient] Build failed | stderr={result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"[MCPDockerClient] Build timed out | package={package_name}")
            return False
        except Exception as e:
            logger.error(f"[MCPDockerClient] Build error: {str(e)}", exc_info=True)
            return False
    
    def _build_image_from_dockerfile(
        self,
        dockerfile_content: str,
        image_name: str,
        build_context: Optional[str] = None
    ) -> bool:
        """
        Build Docker image from custom Dockerfile content.
        
        Args:
            dockerfile_content: Dockerfile content as string
            image_name: Docker image name to build
            build_context: Optional build context directory
        
        Returns:
            True if build succeeded, False otherwise
        """
        if not self.docker_available:
            logger.error("[MCPDockerClient] Docker not available for building")
            return False
        
        # Create temporary build directory
        build_dir = build_context or tempfile.mkdtemp(prefix="mcp-docker-build-")
        
        try:
            # Write Dockerfile
            dockerfile_path = os.path.join(build_dir, "Dockerfile")
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)
            
            logger.info(f"[MCPDockerClient] Building image from custom Dockerfile | image={image_name}")
            
            # Build image
            cmd = [
                self.docker_runtime, "build",
                "-t", image_name,
                "-f", dockerfile_path,
                build_dir
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"[MCPDockerClient] Image built successfully | image={image_name}")
                return True
            else:
                logger.error(f"[MCPDockerClient] Build failed | stderr={result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"[MCPDockerClient] Build error: {str(e)}", exc_info=True)
            return False
        finally:
            # Cleanup temporary directory if we created it
            if build_context is None and os.path.exists(build_dir):
                shutil.rmtree(build_dir, ignore_errors=True)
    
    def ensure_image(
        self,
        mcp_config: Dict[str, Any],
        force_rebuild: bool = False
    ) -> Optional[str]:
        """
        Ensure Docker image exists for an MCP server.
        
        Strategy:
        1. Check if image exists locally
        2. If not, try pulling from Docker Hub
           - RSS: hackerdogs/rss-mcp:latest
           - Others: hackerdogs/hackerdogs-mcp-{name}:latest
        3. If pull fails, build locally from config
        
        Args:
            mcp_config: MCP server configuration dict with:
                - name: Server name
                - package_name: PyPI package name (for pip install)
                - dockerfile: Custom Dockerfile content (optional)
                - base_image: Base Docker image (optional, default: python:3.11-slim)
                - additional_packages: System packages to install (optional)
                - entrypoint: Custom entrypoint (optional)
            force_rebuild: Force rebuild even if image exists (skips Docker Hub pull)
        
        Returns:
            Docker image name if successful, None otherwise
        """
        server_name = mcp_config.get("name", "unknown")
        # Build with same naming as other containers
        image_name = f"{self.image_prefix}-{server_name}:latest"
        
        # Check if image already exists locally
        if not force_rebuild and self._image_exists(image_name):
            logger.info(f"[MCPDockerClient] Image already exists locally | image={image_name}")
            return image_name
        
        # Try pulling from Docker Hub first (unless force_rebuild is True)
        if not force_rebuild:
            if self._pull_image_from_dockerhub(image_name):
                # Verify the image exists after pull
                if self._image_exists(image_name):
                    return image_name
                else:
                    logger.warning(f"[MCPDockerClient] Pull succeeded but image not found. Building locally...")
            # If pull failed, continue to local build
        
        # Build image locally (fallback or if force_rebuild=True)
        logger.info(f"[MCPDockerClient] Building image locally | image={image_name}")
        
        if "dockerfile" in mcp_config:
            # Custom Dockerfile
            success = self._build_image_from_dockerfile(
                mcp_config["dockerfile"],
                image_name,
                mcp_config.get("build_context")
            )
        elif "npm_package" in mcp_config:
            # npm-installable package
            success = self._build_image_from_npm(
                mcp_config["npm_package"],
                image_name,
                mcp_config.get("base_image", "node:20-slim"),
                mcp_config.get("additional_packages"),
                mcp_config.get("entrypoint")
            )
        elif "package_name" in mcp_config:
            # Pip-installable package (Python)
            success = self._build_image_from_pip(
                mcp_config["package_name"],
                image_name,
                mcp_config.get("base_image", "python:3.11-slim"),
                mcp_config.get("additional_packages"),
                mcp_config.get("entrypoint")
            )
        else:
            logger.error(f"[MCPDockerClient] No build method specified | server={server_name}")
            return None
        
        if success:
            return image_name
        else:
            logger.error(f"[MCPDockerClient] Failed to build image | server={server_name}")
            return None
    
    def get_docker_command(
        self,
        image_name: str,
        container_name: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate Docker run command configuration for MCP server.
        
        Args:
            image_name: Docker image name
            container_name: Optional container name (deprecated - not used to avoid conflicts)
            env_vars: Optional environment variables
        
        Returns:
            Dictionary with 'command' and 'args' for MCP configuration
        
        Note:
            Container name is not included to allow Docker to auto-generate unique names.
            This prevents conflicts when multiple discovery calls happen concurrently.
            Containers are ephemeral (--rm) so names don't need to be predictable.
        """
        args = [
            "run",
            "--rm",  # Auto-remove container after execution
            "-i"     # Interactive mode for stdio
            # Note: No --name parameter to allow Docker to auto-generate unique names.
            # This prevents conflicts when multiple discovery calls happen concurrently.
        ]
        
        # Add environment variables
        env_vars_dict = dict(env_vars) if env_vars else {}
        # Add PYTHONUNBUFFERED for Python-based servers (won't hurt Node.js servers)
        if "PYTHONUNBUFFERED" not in env_vars_dict:
            env_vars_dict["PYTHONUNBUFFERED"] = "1"
        
        for key, value in env_vars_dict.items():
            args.extend(["--env", f"{key}={value}"])
        
        args.append(image_name)
        
        return {
            "command": self.docker_runtime,
            "args": args
        }
    
    def build_and_configure(
        self,
        mcp_config: Dict[str, Any],
        force_rebuild: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Build Docker image and generate MCP server configuration.
        
        Args:
            mcp_config: MCP server configuration
            force_rebuild: Force rebuild even if image exists
        
        Returns:
            MCP server configuration dict with Docker command, or None if failed
        """
        # Build image (uses local naming: hackerdogs-mcp-{name}:latest)
        image_name = self.ensure_image(mcp_config, force_rebuild=force_rebuild)
        if not image_name:
            return None
        
        server_name = mcp_config.get("name", "unknown")
        
        # For RSS container, use Docker Hub format in MCP config (hackerdogs/rss-mcp:latest)
        # For other containers, use local image name (hackerdogs-mcp-{name}:latest)
        if server_name == "rss-mcp":
            # Use Docker Hub format for MCP config
            mcp_image_name = f"hackerdogs/rss-mcp:latest"
        else:
            # Use local image name for MCP config
            mcp_image_name = image_name
        
        # Generate Docker command using the MCP config image name
        docker_cmd = self.get_docker_command(
            mcp_image_name,
            mcp_config.get("container_name"),
            mcp_config.get("env")
        )
        
        # Return MCP configuration
        return {
            "name": server_name,
            **docker_cmd
        }


# Global instance (lazy initialization)
_mcp_docker_client: Optional[MCPDockerClient] = None


def get_mcp_docker_client() -> Optional[MCPDockerClient]:
    """Get or create global MCP Docker client instance."""
    global _mcp_docker_client
    if _mcp_docker_client is None:
        _mcp_docker_client = MCPDockerClient()
    return _mcp_docker_client


def build_mcp_server_docker(
    mcp_config: Dict[str, Any],
    force_rebuild: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to build and configure an MCP server for Docker execution.
    
    Args:
        mcp_config: MCP server configuration dict
        force_rebuild: Force rebuild even if image exists
    
    Returns:
        MCP server configuration with Docker command, or None if failed
    """
    client = get_mcp_docker_client()
    if client is None:
        logger.error("[build_mcp_server_docker] MCP Docker client not available")
        return None
    
    return client.build_and_configure(mcp_config, force_rebuild=force_rebuild)

