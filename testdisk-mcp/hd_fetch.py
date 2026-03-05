"""hd_fetch -- download files from URLs into the container workspace.

Supports HTTP(S) direct downloads, git clone, and automatic archive
extraction.  Designed to be copied into every MCP-tool container that
needs to operate on user-supplied files.

Usage
-----
Context-manager (auto-cleanup)::

    with hd_fetch.resolve("https://example.com/repo.tar.gz") as local_path:
        subprocess.run(["tool", local_path])

Explicit download (caller manages cleanup)::

    info = hd_fetch.fetch("https://example.com/firmware.bin")
    # info["path"]  -> /app/workdir/<uuid>/firmware.bin
    # info["job_id"] -> uuid used for this download
    hd_fetch.cleanup(info["job_id"])
"""

from __future__ import annotations

import base64
import contextlib
import ipaddress
import logging
import os
import re
import shutil
import socket
import subprocess
import tarfile
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path
from typing import Generator

logger = logging.getLogger("hd_fetch")

WORKDIR = Path(os.environ.get("HD_WORKDIR", "/app/workdir"))
MAX_DOWNLOAD_MB = int(os.environ.get("HD_MAX_DOWNLOAD_MB", "500"))
FETCH_TIMEOUT = int(os.environ.get("HD_FETCH_TIMEOUT", "120"))
ALLOW_PRIVATE = os.environ.get("HD_FETCH_ALLOW_PRIVATE", "false").lower() in ("1", "true", "yes")
AUTH_HEADER = os.environ.get("HD_FETCH_AUTH_HEADER", "")

_ARCHIVE_EXTENSIONS = {
    ".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz",
}

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_GIT_URL_RE = re.compile(
    r"^(https?://(?:github\.com|gitlab\.com|bitbucket\.org)/[^\s]+?)(?:\.git)?$",
    re.IGNORECASE,
)


class FetchError(Exception):
    """Raised when a download or extraction fails."""


def is_url(value: str) -> bool:
    """Return True if *value* looks like a fetchable URL rather than a local path."""
    return bool(re.match(r"^(https?://|git://|data:)", value, re.IGNORECASE))


def _is_git_url(url: str) -> bool:
    if url.startswith("git://"):
        return True
    if _GIT_URL_RE.match(url):
        parsed = urllib.parse.urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if len(path_parts) == 2:
            return True
    return False


def _check_ssrf(url: str) -> None:
    """Block requests to private/link-local addresses unless explicitly allowed."""
    if ALLOW_PRIVATE:
        return
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise FetchError(f"Cannot parse hostname from URL: {url}")
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise FetchError(f"Cannot resolve hostname: {hostname}")
    for _family, _type, _proto, _canonname, sockaddr in infos:
        addr = ipaddress.ip_address(sockaddr[0])
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                raise FetchError(
                    f"Blocked request to private/link-local address {addr} "
                    f"(hostname {hostname}). Set HD_FETCH_ALLOW_PRIVATE=true to allow."
                )


def _archive_suffix(filename: str) -> str | None:
    """Return the matched archive extension or None."""
    lower = filename.lower()
    for ext in sorted(_ARCHIVE_EXTENSIONS, key=len, reverse=True):
        if lower.endswith(ext):
            return ext
    return None


def _extract_archive(archive_path: Path, dest_dir: Path) -> Path:
    """Extract an archive and return the path to the extracted content."""
    name = archive_path.name.lower()
    dest_resolved = dest_dir.resolve()
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            for member in zf.namelist():
                resolved = (dest_dir / member).resolve()
                if not str(resolved).startswith(str(dest_resolved)):
                    raise FetchError(f"Path traversal detected in archive: {member}")
            zf.extractall(dest_dir)
    elif tarfile.is_tarfile(str(archive_path)):
        with tarfile.open(archive_path, "r:*") as tf:
            for member in tf.getmembers():
                resolved = (dest_dir / member.name).resolve()
                if not str(resolved).startswith(str(dest_resolved)):
                    raise FetchError(f"Path traversal detected in archive: {member.name}")
            if hasattr(tarfile, "data_filter"):
                tf.extractall(dest_dir, filter="data")
            else:
                tf.extractall(dest_dir)
    else:
        raise FetchError(f"Unsupported archive format: {archive_path.name}")

    archive_path.unlink(missing_ok=True)

    entries = list(dest_dir.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return dest_dir


def _download_http(url: str, dest_dir: Path, *, extract: bool = True) -> Path:
    """Download a file via HTTP(S) with size-limit enforcement."""
    _check_ssrf(url)

    parsed = urllib.parse.urlparse(url)
    filename = os.path.basename(parsed.path) or "download"
    filename = re.sub(r"[^\w.\-]", "_", filename)

    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "hd-fetch/1.0")
    if AUTH_HEADER:
        req.add_header("Authorization", AUTH_HEADER)

    max_bytes = MAX_DOWNLOAD_MB * 1024 * 1024
    dest_path = dest_dir / filename

    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            content_length = resp.headers.get("Content-Length")
            if content_length and int(content_length) > max_bytes:
                raise FetchError(
                    f"File too large: {int(content_length)} bytes "
                    f"(limit {MAX_DOWNLOAD_MB} MB)"
                )
            downloaded = 0
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > max_bytes:
                        dest_path.unlink(missing_ok=True)
                        raise FetchError(
                            f"Download exceeded size limit of {MAX_DOWNLOAD_MB} MB"
                        )
                    f.write(chunk)
    except urllib.error.URLError as exc:
        raise FetchError(f"Download failed: {exc}") from exc

    if extract and _archive_suffix(filename):
        return _extract_archive(dest_path, dest_dir)

    return dest_path


def _clone_git(url: str, dest_dir: Path) -> Path:
    """Shallow-clone a git repository."""
    _check_ssrf(url)

    clone_url = url.rstrip("/")
    if not clone_url.endswith(".git"):
        clone_url += ".git"

    repo_dir = dest_dir / "repo"
    cmd = ["git", "clone", "--depth=1", "--single-branch", clone_url, str(repo_dir)]

    env = os.environ.copy()
    if AUTH_HEADER:
        env["GIT_TERMINAL_PROMPT"] = "0"
        header_line = f"Authorization: {AUTH_HEADER}"
        env["GIT_CONFIG_COUNT"] = "1"
        env["GIT_CONFIG_KEY_0"] = "http.extraHeader"
        env["GIT_CONFIG_VALUE_0"] = header_line

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=FETCH_TIMEOUT,
            env=env,
        )
    except FileNotFoundError:
        raise FetchError("git binary not found. Ensure git is installed.")
    except subprocess.TimeoutExpired:
        raise FetchError(f"git clone timed out after {FETCH_TIMEOUT}s")

    if result.returncode != 0:
        raise FetchError(f"git clone failed: {result.stderr.strip()}")

    return repo_dir


def _decode_data_uri(uri: str, dest_dir: Path) -> Path:
    """Decode a data: URI and write to a file."""
    match = re.match(r"data:([^;]*)?(?:;([^,]*))?,(.*)", uri, re.DOTALL)
    if not match:
        raise FetchError(f"Invalid data URI: {uri[:80]}...")

    _mime, encoding, payload = match.groups()
    encoding = (encoding or "").lower()
    if encoding == "base64":
        content = base64.b64decode(payload)
    else:
        content = payload.encode("utf-8")

    max_bytes = MAX_DOWNLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise FetchError(f"Data URI payload exceeds {MAX_DOWNLOAD_MB} MB limit")

    dest_path = dest_dir / "data_payload"
    dest_path.write_bytes(content)
    return dest_path


def fetch(url: str, extract: bool = True) -> dict:
    """Download a file/repo from *url* into the workspace.

    Returns a dict with keys:
        - ``path``: absolute path to the downloaded content
        - ``job_id``: unique ID for this download (use for cleanup)

    Set *extract* to False to skip automatic archive extraction.
    """
    job_id = uuid.uuid4().hex[:12]
    job_dir = WORKDIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        if url.startswith("data:"):
            path = _decode_data_uri(url, job_dir)
        elif _is_git_url(url):
            path = _clone_git(url, job_dir)
        else:
            path = _download_http(url, job_dir, extract=extract)
    except Exception:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise

    return {
        "path": str(path),
        "job_id": job_id,
    }


def cleanup(job_id: str) -> None:
    """Remove the workspace directory for *job_id*."""
    job_dir = WORKDIR / job_id
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
        logger.info("Cleaned up workdir for job %s", job_id)


def cleanup_all() -> None:
    """Remove all job directories under the workspace."""
    if WORKDIR.exists():
        for entry in WORKDIR.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
        logger.info("Cleaned up all workdir contents")


@contextlib.contextmanager
def resolve(path_or_url: str, extract: bool = True) -> Generator[str, None, None]:
    """Context manager that transparently resolves a path or URL.

    If *path_or_url* is a URL, downloads it and yields the local path.
    On exit, cleans up the downloaded content.  If it is already a local
    path, yields it unchanged with no cleanup.
    """
    if not is_url(path_or_url):
        yield path_or_url
        return

    info = fetch(path_or_url, extract=extract)
    try:
        yield info["path"]
    finally:
        cleanup(info["job_id"])
