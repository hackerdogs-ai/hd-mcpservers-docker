from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, Optional

import requests

import constants

async def _check_hash(hash_str: str) -> str:
    """
    Checks whether the given hash is a valid MD5 or SHA-256 hash.
    Returns the hash type as a string ('md5', 'sha256') or 'invalid' if not valid.
    """
    hash_str = hash_str.lower()
    if re.fullmatch(r'[a-f0-9A-F]{32}', hash_str):
        return 'md5_hash'
    elif re.fullmatch(r'[a-f0-9A-F]{64}', hash_str):
        return 'sha256_hash'
    else:
        return 'invalid'
    
async def _format_url(url: str) -> str:
    if not re.match(r'^http.*?\:\/\/', url, re.IGNORECASE):
        url = 'http://' + url
    return url

async def _make_abusech_http_request(
    url: str,
    req_params: Optional[Dict[str, Any]] = None,
    req_data: Optional[Dict[str, Any]] = None,
    req_headers: Optional[Dict[str, Any]] = None,
    is_req_data_json: bool = False,
    abusech_api_key: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """
    Make a POST request to an abuse.ch API endpoint.

    The abuse.ch services (MalwareBazaar, URLhaus, ThreatFox) require an Auth-Key header.
    This function supports explicit key passing (preferred) and falls back to the
    environment-derived key from `constants.ABUSECH_API_KEY`.
    """

    resolved_key = abusech_api_key or constants.ABUSECH_API_KEY
    if not resolved_key:
        return {"error": "ABUSECH_API_KEY not provided (pass abusech_api_key or set env ABUSECH_API_KEY)"}

    headers: Dict[str, str] = {
        "User-Agent": "abusech-mcp-server/1.0",
        "Accept": "application/json",
        "Auth-Key": str(resolved_key),
    }
    if req_headers:
        headers.update(req_headers)

    def _do_request() -> dict:
        try:
            logging.debug(f"Making POST request to {url} with params: {req_params} and data: {req_data}")
            if is_req_data_json:
                resp = requests.post(
                    url,
                    params=req_params,
                    json=req_data,
                    headers=headers,
                    timeout=timeout,
                )
            else:
                resp = requests.post(
                    url,
                    params=req_params,
                    data=req_data,
                    headers=headers,
                    timeout=timeout,
                )

            try:
                return resp.json()
            except Exception:
                return {
                    "error": "non_json_response",
                    "status_code": resp.status_code,
                    "text": (resp.text or "")[:500],
                }
        except requests.exceptions.Timeout as e:
            return {"error": f"timeout: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"request_error: {str(e)}"}
        except Exception as e:
            return {"error": f"unexpected_error: {str(e)}"}

    # Run requests in a worker thread to preserve async concurrency with asyncio.gather
    return await asyncio.to_thread(_do_request)