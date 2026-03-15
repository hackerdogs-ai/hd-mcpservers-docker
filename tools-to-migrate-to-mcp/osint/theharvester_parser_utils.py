"""
theHarvester Parser Utilities (Hackerdogs)

This module ports a small, stable subset of theHarvester's parsing logic so we can
implement "theHarvester-style" LangChain tools without importing theHarvester as a
dependency.

References:
- theHarvester/theHarvester/parsers/myparser.py
"""

from __future__ import annotations

import re
from typing import List


def generic_clean(results: str) -> str:
    """
    Port of theHarvester `myparser.Parser.generic_clean()` (best-effort).
    """
    s = results or ""
    s = (
        s.replace("<em>", "")
        .replace("<b>", "")
        .replace("</b>", "")
        .replace("</em>", "")
        .replace("%3a", "")
        .replace("<strong>", "")
        .replace("</strong>", "")
        .replace("<wbr>", "")
        .replace("</wbr>", "")
    )

    for search in ("<", ">", ":", "=", ";", "&", "%3A", "%3D", "%3C", "%2f", "/", "\\"):
        s = s.replace(search, " ")
    return s


def extract_emails(results: str, word: str) -> List[str]:
    """
    Port of theHarvester `myparser.Parser.emails()`.

    Note: this intentionally constrains extracted emails to those whose domain contains
    the provided `word` (minus an optional leading `www.`), matching upstream behavior.
    """
    cleaned = generic_clean(results)
    w = (word or "").strip()
    w_no_www = w.replace("www.", "")
    # Local part required; domain constrained to include searched word's domain.
    reg_emails = re.compile(
        r"[a-zA-Z0-9.\-_+#~!$&',;=:]+" + "@" + r"[a-zA-Z0-9.-]*" + re.escape(w_no_www)
    )
    raw = reg_emails.findall(cleaned)
    uniq = list(set(raw))
    true_emails = set()
    for email in uniq:
        e = str(email).lower().strip()
        if len(e) > 1 and e[0] == ".":
            e = e[1:].strip()
        if e and "@" in e:
            true_emails.add(e)
    return sorted(true_emails)


def extract_hostnames(results: str, word: str) -> List[str]:
    """
    Port of theHarvester `myparser.Parser.hostnames()`.
    """
    cleaned = generic_clean(results)
    w = (word or "").strip()
    w_no_www = w.replace("www.", "")
    hostnames: List[str] = []
    # should check both www. and not www.
    reg_hosts_1 = re.compile(r"[a-zA-Z0-9.-]*\." + re.escape(w))
    hostnames.extend(reg_hosts_1.findall(cleaned))
    reg_hosts_2 = re.compile(r"[a-zA-Z0-9.-]*\." + re.escape(w_no_www))
    hostnames.extend(reg_hosts_2.findall(cleaned))
    out = sorted({h.lower().strip(".") for h in hostnames if h and "." in h})
    return out


