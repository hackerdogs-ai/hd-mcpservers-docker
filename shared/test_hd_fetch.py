#!/usr/bin/env python3
"""Tests for hd_fetch module -- validates URL download, git clone,
archive extraction, SSRF protection, size limits, and cleanup."""

import base64
import http.server
import json
import os
import shutil
import tarfile
import tempfile
import threading
import zipfile
from pathlib import Path
from unittest import mock

import hd_fetch

TEST_WORKDIR = Path(tempfile.mkdtemp(prefix="hd_fetch_test_"))
PASSED = 0
FAILED = 0


def setup():
    """Override workdir to a temp directory for testing."""
    hd_fetch.WORKDIR = TEST_WORKDIR
    TEST_WORKDIR.mkdir(parents=True, exist_ok=True)


def teardown():
    """Clean up test workdir."""
    shutil.rmtree(TEST_WORKDIR, ignore_errors=True)


def _assert(condition, msg):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS: {msg}")
    else:
        FAILED += 1
        print(f"  FAIL: {msg}")


class _TestHTTPHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP server for download tests."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/hello.txt":
            content = b"hello world\n"
            self.send_response(200)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/test.zip":
            buf = _make_zip()
            self.send_response(200)
            self.send_header("Content-Length", str(len(buf)))
            self.end_headers()
            self.wfile.write(buf)
        elif self.path == "/test.tar.gz":
            buf = _make_targz()
            self.send_response(200)
            self.send_header("Content-Length", str(len(buf)))
            self.end_headers()
            self.wfile.write(buf)
        elif self.path == "/large.bin":
            self.send_response(200)
            self.send_header("Content-Length", str(2 * 1024 * 1024))
            self.end_headers()
            self.wfile.write(b"X" * (2 * 1024 * 1024))
        else:
            self.send_response(404)
            self.end_headers()


def _make_zip() -> bytes:
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("inner/file.txt", "zip content\n")
    return buf.getvalue()


def _make_targz() -> bytes:
    import io
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        data = b"tar content\n"
        info = tarfile.TarInfo(name="inner/file.txt")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _start_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), _TestHTTPHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_is_url():
    print("\n--- test_is_url ---")
    _assert(hd_fetch.is_url("https://example.com/file.txt"), "https URL detected")
    _assert(hd_fetch.is_url("http://example.com/file.txt"), "http URL detected")
    _assert(hd_fetch.is_url("git://github.com/org/repo"), "git URL detected")
    _assert(hd_fetch.is_url("data:text/plain;base64,aGVsbG8="), "data URI detected")
    _assert(not hd_fetch.is_url("/tmp/local/path"), "local path not a URL")
    _assert(not hd_fetch.is_url("relative/path.txt"), "relative path not a URL")


def test_download_http():
    print("\n--- test_download_http ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = True
    try:
        server, port = _start_server()
        try:
            info = hd_fetch.fetch(f"http://127.0.0.1:{port}/hello.txt")
            _assert(Path(info["path"]).exists(), "downloaded file exists")
            _assert(Path(info["path"]).read_text().strip() == "hello world", "content matches")
            _assert(info["job_id"], "job_id returned")
            hd_fetch.cleanup(info["job_id"])
            _assert(not Path(info["path"]).exists(), "cleanup removed file")
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_download_zip():
    print("\n--- test_download_zip ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = True
    try:
        server, port = _start_server()
        try:
            info = hd_fetch.fetch(f"http://127.0.0.1:{port}/test.zip")
            path = Path(info["path"])
            _assert(path.exists(), "extracted directory exists")
            inner = path / "file.txt" if (path / "file.txt").exists() else path
            found = list(Path(info["path"]).rglob("file.txt"))
            _assert(len(found) == 1, "found extracted file.txt")
            _assert("zip content" in found[0].read_text(), "zip content matches")
            hd_fetch.cleanup(info["job_id"])
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_download_targz():
    print("\n--- test_download_targz ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = True
    try:
        server, port = _start_server()
        try:
            info = hd_fetch.fetch(f"http://127.0.0.1:{port}/test.tar.gz")
            found = list(Path(info["path"]).rglob("file.txt"))
            _assert(len(found) == 1, "found extracted file.txt from tar.gz")
            _assert("tar content" in found[0].read_text(), "tar.gz content matches")
            hd_fetch.cleanup(info["job_id"])
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_data_uri():
    print("\n--- test_data_uri ---")
    payload = base64.b64encode(b"secret data").decode()
    info = hd_fetch.fetch(f"data:application/octet-stream;base64,{payload}")
    _assert(Path(info["path"]).read_bytes() == b"secret data", "data URI decoded correctly")
    hd_fetch.cleanup(info["job_id"])


def test_ssrf_blocked():
    print("\n--- test_ssrf_blocked ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = False
    try:
        try:
            hd_fetch.fetch("http://127.0.0.1:9999/evil")
            _assert(False, "should have raised FetchError")
        except hd_fetch.FetchError as exc:
            _assert("private" in str(exc).lower() or "blocked" in str(exc).lower(),
                    f"SSRF blocked with message: {exc}")
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_ssrf_allowed_when_configured():
    print("\n--- test_ssrf_allowed_when_configured ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = True
    try:
        server, port = _start_server()
        try:
            info = hd_fetch.fetch(f"http://127.0.0.1:{port}/hello.txt")
            _assert(Path(info["path"]).exists(), "download succeeded with ALLOW_PRIVATE=true")
            hd_fetch.cleanup(info["job_id"])
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_size_limit():
    print("\n--- test_size_limit ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    old_max = hd_fetch.MAX_DOWNLOAD_MB
    hd_fetch.ALLOW_PRIVATE = True
    hd_fetch.MAX_DOWNLOAD_MB = 1  # 1 MB limit
    try:
        server, port = _start_server()
        try:
            try:
                hd_fetch.fetch(f"http://127.0.0.1:{port}/large.bin")
                _assert(False, "should have raised FetchError for oversized file")
            except hd_fetch.FetchError as exc:
                _assert("size" in str(exc).lower() or "limit" in str(exc).lower(),
                        f"size limit enforced: {exc}")
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow
        hd_fetch.MAX_DOWNLOAD_MB = old_max


def test_resolve_passthrough():
    print("\n--- test_resolve_passthrough ---")
    with hd_fetch.resolve("/some/local/path") as p:
        _assert(p == "/some/local/path", "local path passed through unchanged")


def test_resolve_url():
    print("\n--- test_resolve_url ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = True
    try:
        server, port = _start_server()
        try:
            with hd_fetch.resolve(f"http://127.0.0.1:{port}/hello.txt") as p:
                _assert(Path(p).exists(), "resolve yielded existing path")
                _assert("hello world" in Path(p).read_text(), "resolve content correct")
            _assert(not Path(p).exists(), "resolve cleaned up after context exit")
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_cleanup_all():
    print("\n--- test_cleanup_all ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = True
    try:
        server, port = _start_server()
        try:
            info1 = hd_fetch.fetch(f"http://127.0.0.1:{port}/hello.txt")
            info2 = hd_fetch.fetch(f"http://127.0.0.1:{port}/hello.txt")
            _assert(Path(info1["path"]).exists(), "first download exists")
            _assert(Path(info2["path"]).exists(), "second download exists")
            hd_fetch.cleanup_all()
            _assert(not Path(info1["path"]).exists(), "first cleaned up")
            _assert(not Path(info2["path"]).exists(), "second cleaned up")
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_git_url_detection():
    print("\n--- test_git_url_detection ---")
    _assert(hd_fetch._is_git_url("https://github.com/org/repo"), "github repo URL detected")
    _assert(hd_fetch._is_git_url("https://gitlab.com/org/repo"), "gitlab repo URL detected")
    _assert(hd_fetch._is_git_url("git://github.com/org/repo"), "git:// URL detected")
    _assert(not hd_fetch._is_git_url("https://example.com/file.zip"), "non-git URL not detected")
    _assert(not hd_fetch._is_git_url("https://github.com/org/repo/blob/main/file.py"),
            "deep github path not treated as clone target")


def test_invalid_url():
    print("\n--- test_invalid_url ---")
    try:
        hd_fetch.fetch("http://this-host-does-not-exist-xyz123.invalid/file.txt")
        _assert(False, "should have raised FetchError")
    except hd_fetch.FetchError as exc:
        _assert(True, f"invalid URL raised FetchError: {exc}")
    jobs = list(TEST_WORKDIR.iterdir())
    _assert(len(jobs) == 0, "no orphaned workdir after failed fetch")


def test_extract_false():
    """Verify extract=False skips archive extraction (thread-safe path)."""
    print("\n--- test_extract_false ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    hd_fetch.ALLOW_PRIVATE = True
    try:
        server, port = _start_server()
        try:
            info = hd_fetch.fetch(f"http://127.0.0.1:{port}/test.zip", extract=False)
            path = Path(info["path"])
            _assert(path.exists(), "raw archive file exists")
            _assert(path.name == "test.zip", "file kept original name (not extracted)")
            _assert(path.stat().st_size > 0, "file is non-empty")
            hd_fetch.cleanup(info["job_id"])
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow


def test_auth_header():
    """Verify HD_FETCH_AUTH_HEADER is sent in requests."""
    print("\n--- test_auth_header ---")
    old_allow = hd_fetch.ALLOW_PRIVATE
    old_auth = hd_fetch.AUTH_HEADER
    hd_fetch.ALLOW_PRIVATE = True
    hd_fetch.AUTH_HEADER = "Bearer test-token-123"
    try:
        server, port = _start_server()
        try:
            info = hd_fetch.fetch(f"http://127.0.0.1:{port}/hello.txt")
            _assert(Path(info["path"]).exists(), "download with auth header succeeded")
            hd_fetch.cleanup(info["job_id"])
        finally:
            server.shutdown()
    finally:
        hd_fetch.ALLOW_PRIVATE = old_allow
        hd_fetch.AUTH_HEADER = old_auth


if __name__ == "__main__":
    setup()
    try:
        test_is_url()
        test_download_http()
        test_download_zip()
        test_download_targz()
        test_data_uri()
        test_ssrf_blocked()
        test_ssrf_allowed_when_configured()
        test_size_limit()
        test_resolve_passthrough()
        test_resolve_url()
        test_cleanup_all()
        test_git_url_detection()
        test_invalid_url()
        test_extract_false()
        test_auth_header()
    finally:
        teardown()

    print(f"\n{'='*50}")
    print(f"Results: {PASSED} passed, {FAILED} failed")
    print(f"{'='*50}")
    exit(1 if FAILED else 0)
