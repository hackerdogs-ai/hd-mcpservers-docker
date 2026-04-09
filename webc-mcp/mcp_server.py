#!/usr/bin/env python3
"""Web Content Analysis MCP Server — webpage, domain, network, and text intelligence.

Curated from the original 30-tool webc_langchain.py down to 13 validated,
self-contained tools.  No external shared modules required.
"""

import asyncio
import json
import logging
import os
import re
import socket
import ssl
import sys
from typing import Optional
from urllib.parse import urlparse

import dns.resolver
import httpx
import tldextract
import whois
from bs4 import BeautifulSoup
from langdetect import detect, detect_langs

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("webc-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8504"))

mcp = FastMCP(
    "Web Content Analysis MCP Server",
    instructions=(
        "Comprehensive web content and domain intelligence: "
        "webpage analysis, text extraction, entity/email/PII detection, "
        "DNS/WHOIS/SSL lookups, port scanning, language detection, key-term extraction."
    ),
)

HTTP_TIMEOUT = 30.0
_HEADERS = {"User-Agent": "webc-mcp/1.0 (+https://hackerdogs.ai)"}


def _fetch(url: str) -> httpx.Response:
    with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True, headers=_HEADERS) as c:
        return c.get(url)


def _json_safe(obj):
    """Best-effort JSON serialisation for WHOIS-like objects."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]
    return str(obj)


# ── Web Content Tools ───────────────────────────────────────────────────────


@mcp.tool()
def analyze_webpage(url: str) -> str:
    """Fetch a URL and return structured analysis: title, meta, text preview, links, images, headers.

    Args:
        url: Full URL (https://example.com).
    """
    try:
        r = _fetch(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta = {}
        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property") or ""
            content = tag.get("content", "")
            if name and content:
                meta[name] = content

        text = soup.get_text(separator=" ", strip=True)[:3000]
        links = [a["href"] for a in soup.find_all("a", href=True)][:100]
        images = [img.get("src", "") for img in soup.find_all("img") if img.get("src")][:50]

        return json.dumps({
            "url": str(r.url),
            "status_code": r.status_code,
            "title": title,
            "meta": meta,
            "text_preview": text,
            "links_count": len(links),
            "links": links,
            "images_count": len(images),
            "images": images,
            "content_type": r.headers.get("content-type", ""),
            "content_length": len(r.content),
        }, indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "url": url})
    except Exception as e:
        return json.dumps({"error": str(e), "url": url})


@mcp.tool()
def extract_text(url: str, max_chars: int = 10000) -> str:
    """Extract clean text content from a webpage.

    Args:
        url: Full URL to fetch.
        max_chars: Maximum characters to return (default 10 000).
    """
    try:
        r = _fetch(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return json.dumps({"url": str(r.url), "text": text[:max_chars], "total_chars": len(text)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "url": url})


@mcp.tool()
def extract_emails(text_or_url: str) -> str:
    """Extract email addresses from text or a webpage URL.

    Args:
        text_or_url: Plain text or a URL to fetch and scan.
    """
    try:
        if text_or_url.startswith(("http://", "https://")):
            r = _fetch(text_or_url)
            r.raise_for_status()
            text = r.text
        else:
            text = text_or_url

        emails = sorted(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))
        return json.dumps({"emails": emails, "count": len(emails)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def extract_entities(text_or_url: str) -> str:
    """Extract entities (URLs, emails, IPs, phone numbers, hashes) from text or a webpage.

    Args:
        text_or_url: Plain text or a URL to fetch and scan.
    """
    try:
        if text_or_url.startswith(("http://", "https://")):
            r = _fetch(text_or_url)
            r.raise_for_status()
            text = r.text
        else:
            text = text_or_url

        patterns = {
            "emails": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "urls": r"https?://[^\s<>\"']+",
            "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "phone_numbers": r"\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
            "md5_hashes": r"\b[a-fA-F0-9]{32}\b",
            "sha256_hashes": r"\b[a-fA-F0-9]{64}\b",
        }
        entities = {}
        for name, pattern in patterns.items():
            found = sorted(set(re.findall(pattern, text)))
            if found:
                entities[name] = found

        return json.dumps(entities, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def find_sensitive_data(text: str) -> str:
    """Scan text for sensitive data: credit card numbers, SSNs, API keys, JWTs, private keys.

    Args:
        text: Text to scan for PII/secrets.
    """
    patterns = {
        "credit_cards": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "aws_access_key": r"\bAKIA[0-9A-Z]{16}\b",
        "jwt_tokens": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
        "private_keys": r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----",
        "generic_api_keys": r"\b[A-Za-z0-9]{32,64}\b",
    }
    findings = {}
    for name, pattern in patterns.items():
        if name == "generic_api_keys":
            continue  # too noisy — only report if nothing else found
        matches = re.findall(pattern, text)
        if matches:
            findings[name] = [m[:8] + "..." for m in matches]

    return json.dumps({
        "findings": findings,
        "categories_found": len(findings),
        "has_sensitive_data": len(findings) > 0,
    }, indent=2)


# ── Domain / Network Tools ──────────────────────────────────────────────────


@mcp.tool()
def analyze_domain(domain: str) -> str:
    """Combined DNS + WHOIS + TLD analysis for a domain.

    Args:
        domain: Domain name (e.g. example.com).
    """
    result = {"domain": domain}

    # TLD info
    try:
        ext = tldextract.extract(domain)
        result["tld_info"] = {"subdomain": ext.subdomain, "domain": ext.domain, "suffix": ext.suffix, "fqdn": ext.fqdn}
    except Exception as e:
        result["tld_error"] = str(e)

    # DNS
    try:
        records = {}
        for rtype in ["A", "AAAA", "MX", "NS", "TXT"]:
            try:
                answers = dns.resolver.resolve(domain, rtype)
                records[rtype] = [str(r) for r in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                pass
        result["dns"] = records
    except Exception as e:
        result["dns_error"] = str(e)

    # WHOIS
    try:
        w = whois.whois(domain)
        result["whois"] = _json_safe(dict(w) if hasattr(w, "items") else w)
    except Exception as e:
        result["whois_error"] = str(e)

    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def resolve_dns(domain: str, record_types: str = "A,AAAA,MX,NS,TXT") -> str:
    """Resolve DNS records for a domain.

    Args:
        domain: Domain name.
        record_types: Comma-separated record types (default: A,AAAA,MX,NS,TXT).
    """
    types = [t.strip().upper() for t in record_types.split(",")]
    records = {}
    for rtype in types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            records[rtype] = [str(r) for r in answers]
        except Exception as e:
            records[rtype] = {"error": str(e)}
    return json.dumps({"domain": domain, "records": records}, indent=2)


@mcp.tool()
def get_whois(domain_or_ip: str) -> str:
    """WHOIS lookup for a domain or IP address.

    Args:
        domain_or_ip: Domain name or IP address.
    """
    try:
        w = whois.whois(domain_or_ip)
        return json.dumps(_json_safe(dict(w) if hasattr(w, "items") else w), indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "query": domain_or_ip})


@mcp.tool()
def get_ip_location(ip_address: str) -> str:
    """GeoIP lookup for an IP address (uses ip-api.com free tier).

    Args:
        ip_address: IPv4 or IPv6 address.
    """
    try:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(f"http://ip-api.com/json/{ip_address}?fields=66846719")
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "ip": ip_address})


@mcp.tool()
def get_ssl_certificate(hostname: str, port: int = 443) -> str:
    """Retrieve SSL/TLS certificate details for a hostname.

    Args:
        hostname: Hostname to connect to.
        port: Port number (default 443).
    """
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return json.dumps({
                    "hostname": hostname,
                    "port": port,
                    "subject": dict(x[0] for x in cert.get("subject", ())),
                    "issuer": dict(x[0] for x in cert.get("issuer", ())),
                    "serial_number": cert.get("serialNumber"),
                    "not_before": cert.get("notBefore"),
                    "not_after": cert.get("notAfter"),
                    "san": [entry[1] for entry in cert.get("subjectAltName", ())],
                    "version": cert.get("version"),
                }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "hostname": hostname, "port": port})


@mcp.tool()
def scan_port(host: str, port: int, timeout_seconds: float = 5.0) -> str:
    """Check if a TCP port is open on a host.

    Args:
        host: Hostname or IP.
        port: Port number.
        timeout_seconds: Connection timeout (default 5s).
    """
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds) as s:
            return json.dumps({"host": host, "port": port, "status": "open"})
    except socket.timeout:
        return json.dumps({"host": host, "port": port, "status": "filtered", "detail": "timeout"})
    except ConnectionRefusedError:
        return json.dumps({"host": host, "port": port, "status": "closed"})
    except Exception as e:
        return json.dumps({"host": host, "port": port, "status": "error", "detail": str(e)})


# ── Text / NLP Tools ────────────────────────────────────────────────────────


@mcp.tool()
def detect_language(text: str) -> str:
    """Detect the language of a text passage.

    Args:
        text: Text to analyse (at least a few words for accuracy).
    """
    if not text or len(text.strip()) < 3:
        return json.dumps({"error": "Text too short for language detection"})
    try:
        primary = detect(text)
        ranked = detect_langs(text)
        return json.dumps({
            "language": primary,
            "probabilities": [{"lang": str(l).split(":")[0], "prob": round(l.prob, 4)} for l in ranked],
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def extract_keyterms(text: str, top_n: int = 15) -> str:
    """Extract key terms from text using word-frequency analysis.

    Args:
        text: Text to analyse.
        top_n: Number of top terms to return (default 15).
    """
    import collections
    import string

    stop = {
        "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it",
        "for", "not", "on", "with", "he", "as", "you", "do", "at", "this",
        "but", "his", "by", "from", "they", "we", "say", "her", "she", "or",
        "an", "will", "my", "one", "all", "would", "there", "their", "what",
        "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
        "when", "make", "can", "like", "time", "no", "just", "him", "know",
        "take", "people", "into", "year", "your", "good", "some", "could",
        "them", "see", "other", "than", "then", "now", "look", "only", "come",
        "its", "over", "think", "also", "back", "after", "use", "two", "how",
        "our", "work", "first", "well", "way", "even", "new", "want", "because",
        "any", "these", "give", "day", "most", "us", "is", "are", "was", "were",
        "been", "has", "had", "did", "does", "may", "more", "very", "much",
    }
    words = [
        w.lower().strip(string.punctuation)
        for w in text.split()
        if len(w.strip(string.punctuation)) > 2
    ]
    words = [w for w in words if w and w not in stop and not w.isdigit()]
    freq = collections.Counter(words)
    top = freq.most_common(top_n)
    return json.dumps({"keyterms": [{"term": t, "count": c} for t, c in top], "total_words": len(words)}, indent=2)


# ── Main ────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    logger.info("Starting webc-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
