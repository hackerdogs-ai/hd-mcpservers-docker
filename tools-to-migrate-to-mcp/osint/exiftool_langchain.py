"""
exiftool Tool for LangChain Agents

Extract metadata from images/PDFs. This is a LangChain tool (not an MCP server):
it runs inside the chat-solo Celery process and uses DockerOSINTClient to run the
project's internal osint-tools container via the host Docker daemon (socket must be
mounted in chat-solo). Contrast with OCR, which is an MCP server in its own container.

Reference: https://exiftool.org/

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following configuration:

1. Docker Environment (Required)
   - Description: ExifTool runs inside this project's OSINT Docker container.
   - Setup (from repo root):
     a) Build: cd shared/modules/tools/docker && docker build -t osint-tools:latest .
     b) The chat/solo container must have the Docker socket mounted and Celery able to
        run `docker ps` (see docs/docker: socket permissions, DOCKER_GID wrapper on Linux).
   - The tool checks Docker availability and returns a JSON error if not available.

2. Inputs
   - Local path: Pass a local file path accessible to the running process.
   - Remote URL: Pass an http(s) URL and the tool will download it to a temp file first.

Security Notes:
- Metadata extracted from files may include sensitive identifiers (GPS, author, device serials).
- This tool runs the extractor in Docker for isolation.
"""

import json
import subprocess
import os
import tempfile
import uuid
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Optional, List, Tuple
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/exiftool_tool.log")


class ExifToolSecurityAgentState(AgentState):
    """Extended agent state for ExifTool operations."""
    user_id: str = ""


def _is_http_url(value: str) -> bool:
    """
    Check whether the provided value is an http(s) URL.

    Args:
        value: String to check.

    Returns:
        True if value is a valid http(s) URL, False otherwise.
    """
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _guess_suffix_from_url(url: str) -> str:
    """Best-effort suffix selection for temp file names based on URL path."""
    try:
        path = urlparse(url).path or ""
        _, ext = os.path.splitext(path)
        if ext and len(ext) <= 10:
            return ext
    except Exception:
        pass
    return ""


def _download_url_to_tempfile(url: str, timeout_s: int = 30, max_bytes: int = 50 * 1024 * 1024) -> Tuple[str, int]:
    """
    Download a remote file to a temporary file.

    This is used so the OSINT Docker container can process external images/PDFs by URL.

    Args:
        url: http(s) URL to download.
        timeout_s: Network timeout in seconds.
        max_bytes: Max allowed download size in bytes (default: 50MB).

    Returns:
        (local_file_path, bytes_written)

    Raises:
        ValueError: if the download exceeds max_bytes or URL is invalid.
        URLError/HTTPError: for network errors.
    """
    if not _is_http_url(url):
        raise ValueError("Only http(s) URLs are supported for download")

    suffix = _guess_suffix_from_url(url)
    tmp = tempfile.NamedTemporaryFile(prefix="exiftool_", suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()

    bytes_written = 0
    req = Request(url, headers={"User-Agent": "hackerdogs-exiftool/1.0"})
    try:
        with urlopen(req, timeout=timeout_s) as resp, open(tmp_path, "wb") as out:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise ValueError(f"Download too large (> {max_bytes} bytes)")
                out.write(chunk)
        return tmp_path, bytes_written
    except Exception:
        # Ensure we don't leave partial files behind on download errors
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        raise


@tool
def exiftool_search(
    runtime: ToolRuntime,
    file_path: str,
    extract_gps: bool = True,
    extract_author: bool = True,
    output_format: str = "json"
) -> str:
    """
    Extract metadata from images, PDFs, and other files using ExifTool.
    
    Use cases:
    1. Geospatial Intelligence (GEOINT): Extract GPS coordinates from photos
    2. Device Fingerprinting: Identify camera/device make, model, software
    3. Document Attribution: Extract author, creator, creation dates from PDFs
    4. Timeline Reconstruction: Extract timestamps (DateTimeOriginal, CreateDate)
    5. Image Authenticity: Detect editing software and manipulation history
    
    Args:
        runtime: ToolRuntime instance (automatically injected).
        file_path: Local file path OR an http(s) URL to an image/PDF.
            - If a URL is provided, the tool downloads it to a temporary file first.
        extract_gps: If False, GPS-related tags are excluded from the output (default: True).
        extract_author: If False, common author/creator tags are excluded from the output (default: True).
        output_format: Output format - "json" (default) or "text".
    
    Returns:
        JSON string with extracted metadata.
        
        - If output_format="json": returns verbatim ExifTool JSON output (array of objects).
        - If output_format="text": returns ExifTool stdout/stderr in short format.
        
        Common fields include:
        - GPS: GPSLatitude, GPSLongitude, GPSAltitude, GPSDateTime
        - Author: Author, Creator, Producer, XMP:Creator
        - Device: Make, Model, SerialNumber, Software
        - Time: DateTimeOriginal, CreateDate, ModifyDate
        - Image: ImageWidth, ImageHeight, ColorSpace, Compression
    """
    try:
        safe_log_info(
            logger,
            "[exiftool_search] Starting",
            file_path=file_path,
            extract_gps=extract_gps,
            extract_creator_metadata=extract_author,
            output_format=output_format,
        )
        
        # Validate inputs
        if not file_path or not isinstance(file_path, str):
            error_msg = "file_path must be a non-empty string"
            safe_log_error(logger, "[exiftool_search] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})
        
        if output_format not in ["json", "text"]:
            error_msg = "output_format must be 'json' or 'text'"
            safe_log_error(logger, "[exiftool_search] Validation failed", error_msg=error_msg, output_format=output_format)
            return json.dumps({"status": "error", "message": error_msg})
        
        # Docker-only execution (consistent with other OSINT tools)
        safe_log_debug(logger, "[exiftool_search] Checking Docker availability")
        docker_client = get_docker_client()
        
        if not docker_client or not docker_client.docker_available:
            error_msg = (
                "Docker is required for this project's OSINT container. Setup:\n"
                "1. Build image (from repo root): cd shared/modules/tools/docker && docker build -t osint-tools:latest .\n"
                "2. Ensure the chat/solo container has the Docker socket mounted and can run 'docker ps' (use compose-with-docker-gid.sh on Linux)."
            )
            safe_log_error(logger, "[exiftool_search] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        local_source_path = file_path
        temp_download_path: Optional[str] = None
        container_file_path: Optional[str] = None

        try:
            # URL support: download to temp file first
            if _is_http_url(file_path):
                safe_log_info(logger, "[exiftool_search] Detected URL input; downloading", url=file_path)
                try:
                    temp_download_path, bytes_written = _download_url_to_tempfile(file_path)
                    local_source_path = temp_download_path
                    safe_log_info(
                        logger,
                        "[exiftool_search] Download complete",
                        url=file_path,
                        downloaded_path=temp_download_path,
                        bytes=bytes_written,
                    )
                except (HTTPError, URLError, ValueError) as e:
                    error_msg = f"Failed to download URL: {str(e)}"
                    safe_log_error(logger, "[exiftool_search] Download failed", error_msg=error_msg, url=file_path, exc_info=True)
                    return json.dumps({"status": "error", "message": error_msg})
                except Exception as e:
                    error_msg = f"Unexpected error downloading URL: {str(e)}"
                    safe_log_error(logger, "[exiftool_search] Download error", error_msg=error_msg, url=file_path, exc_info=True)
                    return json.dumps({"status": "error", "message": error_msg})

            # Check if local file exists (after optional download)
            if not os.path.exists(local_source_path):
                error_msg = f"File not found: {local_source_path}"
                safe_log_error(logger, "[exiftool_search] File missing", error_msg=error_msg, file_path=local_source_path)
                return json.dumps({"status": "error", "message": error_msg})

            # Build ExifTool command arguments
            args = []
            
            # Output format
            if output_format == "json":
                args.append("-j")  # JSON output
                args.append("-G")  # Include group names (e.g., "EXIF:Make")
            else:
                args.append("-S")  # Short format for text output
            
            # Always include all metadata
            args.append("-a")  # Show all tags (not just EXIF)
            args.append("-u")  # Show unknown tags too

            # Optional exclusions (keep output type consistent while honoring flags)
            # ExifTool supports -x <tag> to exclude tags (wildcards allowed).
            if not extract_gps:
                args.extend(["-x", "GPS*"])
                args.extend(["-x", "Composite:GPS*"])
            if not extract_author:
                # Common creator/author tags across images and PDFs
                args.extend(["-x", "Author"])
                args.extend(["-x", "Creator"])
                args.extend(["-x", "Producer"])
                args.extend(["-x", "CreatorTool"])
                args.extend(["-x", "Artist"])
                args.extend(["-x", "Copyright"])
                args.extend(["-x", "Rights"])
                args.extend(["-x", "XMP:Creator*"])
            
            # For docker exec, copy the file into the running persistent container.
            # Note: We generate a unique name to avoid collisions in /workspace.
            original_name = os.path.basename(local_source_path)
            unique_name = f"{uuid.uuid4().hex}_{original_name}" if original_name else f"{uuid.uuid4().hex}"
            container_file_path = f"/workspace/{unique_name}"
            
            # Copy file into container
            try:
                copy_cmd = [
                    docker_client.docker_runtime, "cp", local_source_path, f"{docker_client.container_name}:{container_file_path}"
                ]
                safe_log_debug(logger, "[exiftool_search] Copying file into container", copy_cmd=" ".join(copy_cmd))
                copy_result = subprocess.run(
                    copy_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False
                )
                
                if copy_result.returncode != 0:
                    error_msg = f"Failed to copy file into container: {copy_result.stderr}"
                    safe_log_error(logger, "[exiftool_search] docker cp failed", error_msg=error_msg, stderr=copy_result.stderr)
                    return json.dumps({"status": "error", "message": error_msg})
                
                safe_log_info(
                    logger,
                    "[exiftool_search] File copied to container",
                    host_path=local_source_path,
                    container_path=container_file_path,
                )
            except Exception as e:
                error_msg = f"Failed to copy file into container: {str(e)}"
                safe_log_error(logger, "[exiftool_search] Copy error", error_msg=error_msg, exc_info=True)
                return json.dumps({"status": "error", "message": error_msg})
            
            args.append(container_file_path)
            
            # Execute ExifTool in Docker
            safe_log_info(logger, "[exiftool_search] Executing in Docker", command="exiftool", args_count=len(args), timeout=60)
            docker_result = execute_in_docker("exiftool", args, timeout=60, volumes=None)
            
            if docker_result["status"] != "success":
                error_msg = f"ExifTool failed: {docker_result.get('stderr', docker_result.get('message', 'Unknown error'))}"
                safe_log_error(
                    logger,
                    "[exiftool_search] Docker execution failed",
                    error_msg=error_msg,
                    stderr=docker_result.get("stderr", ""),
                    message=docker_result.get("message", ""),
                )
                return json.dumps({"status": "error", "message": error_msg})
            
            # Parse output
            stdout = docker_result.get("stdout", "")
            stderr = docker_result.get("stderr", "")
            
            # For JSON output, return verbatim
            if output_format == "json":
                if stdout:
                    # ExifTool JSON output is already valid JSON (array of objects)
                    # Return it verbatim
                    safe_log_info(logger, "[exiftool_search] Complete - returning JSON verbatim", file_path=file_path)
                    return stdout
                else:
                    # No metadata found or empty output
                    safe_log_info(logger, "[exiftool_search] Complete - no metadata found", file_path=file_path)
                    return json.dumps([])  # Empty array for no results
            
            # For text output, return stdout verbatim
            safe_log_info(logger, "[exiftool_search] Complete - returning text verbatim", file_path=file_path)
            return stdout if stdout else stderr
        finally:
            # Cleanup downloaded temp file, if any
            if temp_download_path:
                try:
                    os.remove(temp_download_path)
                    safe_log_debug(logger, "[exiftool_search] Temp download cleaned up", temp_path=temp_download_path)
                except Exception:
                    safe_log_debug(logger, "[exiftool_search] Temp download cleanup failed (ignored)", temp_path=temp_download_path)

            # Best-effort cleanup of container file, if it was created
            if docker_client and container_file_path:
                try:
                    cleanup_result = docker_client.execute("rm", ["-f", container_file_path], timeout=10)
                    safe_log_debug(logger, "[exiftool_search] Container cleanup attempted", cleanup_status=cleanup_result.get("status"))
                except Exception:
                    safe_log_debug(logger, "[exiftool_search] Container cleanup failed (ignored)", container_path=container_file_path)
        
    except Exception as e:
        safe_log_error(logger, "[exiftool_search] Error", exc_info=True, error=str(e), file_path=file_path)
        return json.dumps({"status": "error", "message": f"ExifTool extraction failed: {str(e)}"})
