#!/usr/bin/env python3
"""Enrich docs/schema/insert_farm_mcp_tools.sql with real capabilities and prompt examples.

Pulls tools + example prompts from each server's README (and mcp_server.py as
fallback) so the g_tools description, capabilities[], and search_terms[] fields
are accurate for Weaviate vectorization and execution grouping.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_PATH = ROOT / "docs" / "schema" / "insert_farm_mcp_tools.sql"

GENERIC_TAGS = {
    "mcp", "mcp-server", "docker", "mcp-farm", "git", "core", "port",
    "wrapper", "server", "tool", "tools", "oss", "hackerdogs", "latest",
    "http", "https", "localhost", "cloud", "free", "community", "system",
}

GENERIC_PROMPT_MARKERS = (
    "with --help",
    "see all available options",
    "scan the target 192.168.1.1",
    "with default settings",
    "verbose output enabled",
    "analyze the target and report findings",
    "what options does",
    "show me its help output",
)

GENERIC_TOOL_DOC = re.compile(
    r"^run\s+\S+\s+with\s+(the\s+given\s+)?(cli\s+)?arguments",
    re.I,
)
HEALTH_CHECK_TOOLS = re.compile(r"(health_check|_info|_status)$", re.I)
ACTION_SPLIT = re.compile(r",\s+and\s+|,\s+|\s+and\s+|;\s+")

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "from", "that", "this",
    "into", "onto", "over", "under", "using", "used", "use", "via", "its",
    "is", "are", "was", "were", "be", "to", "of", "in", "on", "by", "at",
    "as", "it", "can", "will", "your", "you", "our", "all", "any", "more",
    "than", "also", "not", "no", "yes", "see", "full", "documentation",
    "mcp", "server", "wrapper", "tool", "tools", "given", "arguments",
    "returns", "structured", "json", "output", "inside", "docker",
    "container", "required", "keys", "api", "runs", "locally", "provides",
    "without", "requiring", "along", "requested", "useful", "following",
    "handles", "platform", "global", "official", "toolkit", "wraps",
    "giving", "assistants", "ability", "ideal", "turning", "instead",
            "against", "example", "findings", "summarize", "should", "which",
            "ones", "tell", "their", "when", "most", "quick", "help", "need",
            "what", "these", "there", "them", "then", "than", "some", "such",
        }

MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MD_BOLD = re.compile(r"\*\*([^*]+)\*\*")
MD_CODE = re.compile(r"`([^`]+)`")
MD_HEAD = re.compile(r"^#+\s+", re.M)
WHITESPACE = re.compile(r"\s+")


def strip_md(text: str) -> str:
    text = MD_LINK.sub(r"\1", text or "")
    text = MD_BOLD.sub(r"\1", text)
    text = MD_CODE.sub(r"\1", text)
    text = MD_HEAD.sub("", text)
    text = text.replace("*", " ").replace("_", " ")
    return WHITESPACE.sub(" ", text).strip()


def sql_str(value: str) -> str:
    return "'" + (value or "").replace("'", "''") + "'"


def sql_array(items: list[str]) -> str:
    seen = set()
    out = []
    for item in items:
        item = WHITESPACE.sub(" ", (item or "").strip())
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(sql_str(item))
    if not out:
        out = [sql_str("mcp-server")]
    return "ARRAY[" + ", ".join(out) + "]"


def parse_sql_values(inner: str) -> list[str]:
    """Split the inside of VALUES (...) into raw SQL value tokens."""
    values = []
    i = 0
    n = len(inner)
    while i < n:
        while i < n and inner[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        if inner.startswith("ARRAY[", i):
            depth = 0
            j = i
            in_str = False
            while j < n:
                c = inner[j]
                if in_str:
                    if c == "'" and inner[j:j + 2] == "''":
                        j += 2
                        continue
                    if c == "'":
                        in_str = False
                    j += 1
                    continue
                if c == "'":
                    in_str = True
                    j += 1
                    continue
                if inner.startswith("ARRAY[", j):
                    depth += 1
                    j += 6
                    continue
                if c == "[":
                    depth += 1
                elif c == "]":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
            values.append(inner[i:j].strip())
            i = j
            continue
        if inner[i] == "'":
            j = i + 1
            while j < n:
                if inner[j] == "'" and inner[j:j + 2] == "''":
                    j += 2
                    continue
                if inner[j] == "'":
                    j += 1
                    break
                j += 1
            values.append(inner[i:j])
            i = j
            continue
        j = i
        while j < n and inner[j] not in ",\n":
            j += 1
        values.append(inner[i:j].strip())
        i = j
    return values


def unquote(token: str) -> str:
    token = token.strip()
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1].replace("''", "'")
    return token


def image_to_dir(config_json: str, title: str = "") -> str | None:
    try:
        data = json.loads(config_json)
    except json.JSONDecodeError:
        data = {}
    servers = (data or {}).get("mcpServers") or {}
    for conf in servers.values():
        image = (conf or {}).get("image") or ""
        name = image.split("/")[-1].split(":")[0].strip()
        if name:
            return name
    # Fallbacks when image is empty (remote-only catalog entries)
    for candidate in (
        title,
        re.sub(r"\s+", "-", (title or "").lower()) + "-mcp",
        re.sub(r"\s+MCP Server$", "", title or "", flags=re.I).lower() + "-mcp",
    ):
        cand = (candidate or "").strip()
        if cand and (ROOT / cand).is_dir():
            return cand
    return None


def extract_readme(server_dir: Path) -> dict:
    readme = server_dir / "README.md"
    if not readme.is_file():
        return {"what": "", "summary": "", "tools": [], "prompts": []}

    text = readme.read_text(encoding="utf-8", errors="replace")
    # Drop HTML header / images
    text = re.sub(r"<[^>]+>", " ", text)

    summary = ""
    m = re.search(r"^# .+\n\n(.+)", text, re.M)
    if m:
        summary = strip_md(m.group(1).split("\n")[0])

    what = ""
    m = re.search(
        r"## What is[^\n]*\n+(.*?)(?=\n## |\n\*\*Tools:\*\*|\n\*\*Summary\.\*\*|\Z)",
        text,
        re.S,
    )
    if m:
        block = m.group(1)
        # Prefer the first real paragraph, skip "No API keys" / "Summary" lines
        paras = [p.strip() for p in re.split(r"\n\s*\n", block) if p.strip()]
        keep = []
        for p in paras:
            sp = strip_md(p)
            if not sp:
                continue
            low = sp.lower()
            if low.startswith("no api keys") or low.startswith("api key required"):
                continue
            if low.startswith("summary."):
                continue
            if low.startswith("see ") and ("github" in low or "documentation" in low):
                continue
            keep.append(sp)
        what = " ".join(keep[:2])

    tools = []
    seen_tools = set()

    def add_tool(name: str, doc: str) -> None:
        name = (name or "").strip()
        if not name or name in seen_tools:
            return
        seen_tools.add(name)
        tools.append({"name": name, "docstring": strip_md(doc or name.replace("_", " "))})

    m = re.search(r"\*\*Tools:\*\*\s*\n((?:- .+\n)+)", text)
    if m:
        for line in m.group(1).splitlines():
            tm = re.match(r"- `([^`]+)`\s*[—–-]\s*(.+)", line.strip())
            if tm:
                add_tool(tm.group(1), tm.group(2))

    # Only parse Tool/Description tables, not Parameter/Type tables.
    ref = re.search(r"## Tools Reference\n(.*?)(?=\n## |\Z)", text, re.S)
    if ref:
        block = ref.group(1)
        in_tool_table = False
        for line in block.splitlines():
            header = line.strip().lower()
            if header.startswith("|") and "tool" in header.split("|")[1] and "description" in header:
                in_tool_table = True
                continue
            if header.startswith("| ---") or header.startswith("|---"):
                continue
            if in_tool_table:
                if not line.strip().startswith("|"):
                    in_tool_table = False
                    continue
                tm = re.match(r"\|\s*`([^`]+)`\s*\|\s*([^|]+)\|", line.strip())
                if tm:
                    add_tool(tm.group(1), tm.group(2))
        for hm in re.finditer(
            r"### `([^`]+)`\s*\n+(.*?)(?=\n### |\n<details>|\n\| Parameter|\Z)",
            block,
            re.S,
        ):
            para = hm.group(2).split("\n\n")[0]
            if para.startswith("|"):
                para = ""
            add_tool(hm.group(1), para)

    prompts = []
    m = re.search(
        r"## Example Prompts\n(.*?)(?=\n## |\Z)",
        text,
        re.S,
    )
    if m:
        for line in m.group(1).splitlines():
            raw = line.strip()
            pm = re.match(r"^-\s+[\u201c\u201d\"'](.+?)[\u201c\u201d\"']\s*$", raw)
            if not pm:
                pm = re.match(r'^- "(.+)"\s*$', raw)
            if pm:
                prompts.append(pm.group(1).strip().rstrip("."))
    return {"what": what, "summary": summary, "tools": tools, "prompts": prompts}


def extract_py_tools(server_dir: Path) -> list[dict]:
    py_path = server_dir / "mcp_server.py"
    if not py_path.is_file():
        return []
    source = py_path.read_text(encoding="utf-8", errors="replace")
    tools = []
    pattern = (
        r"@mcp\.tool\([^)]*\)\s*\n(?:async\s+)?def\s+(\w+)\(([^)]*)\)"
        r"\s*(?:->\s*[^:]+)?\s*:\s*\n\s*\"\"\"(.*?)\"\"\""
    )
    for m in re.finditer(pattern, source, re.S):
        doc = strip_md(m.group(3).strip().split("\n")[0])
        tools.append({"name": m.group(1), "docstring": doc})
    return tools


def prompts_are_generic(prompts: list[str]) -> bool:
    if not prompts:
        return True
    hits = 0
    for p in prompts:
        low = p.lower()
        if any(marker in low for marker in GENERIC_PROMPT_MARKERS):
            hits += 1
    return hits >= max(3, int(len(prompts) * 0.5))


def first_sentence(text: str) -> str:
    text = strip_md(text).strip()
    if not text:
        return ""
    m = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
    return m[0].rstrip(".")


def core_purpose(sql_desc: str, summary: str, what: str) -> str:
    """Short one-line purpose, without 'MCP server wrapper for'."""
    candidates = []
    for candidate in (sql_desc, summary, first_sentence(what)):
        c = strip_md(candidate)
        if not c:
            continue
        c = re.sub(r"^MCP server wrapper for\s+", "", c, flags=re.I)
        c = re.sub(r"^MCP server for\s+", "", c, flags=re.I)
        c = re.sub(r"^>\s*", "", c)
        c = re.sub(r"^[^—–-]+[—–-]\s+", "", c, count=1)
        c = c.strip().rstrip(".")
        if len(c) >= 12:
            candidates.append(c)
    if not candidates:
        return strip_md(sql_desc).rstrip(".")
    # Prefer the shortest reasonably complete phrase
    candidates.sort(key=lambda x: (len(x) > 160, len(x)))
    return candidates[0][:200]


def doc_echoes_name(name: str, doc: str) -> bool:
    n = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    d = re.sub(r"[^a-z0-9]+", " ", (doc or "").lower()).strip()
    return bool(n) and n == d


def tool_is_useful(tool: dict) -> bool:
    name = (tool.get("name") or "").lower()
    doc = tool.get("docstring") or ""
    if name in {"download_file", "cleanup_downloads"}:
        return False
    if HEALTH_CHECK_TOOLS.search(name) and len(doc) < 40:
        return False
    if GENERIC_TOOL_DOC.search(doc or ""):
        return False
    if doc_echoes_name(name, doc):
        return False
    return True


def action_phrases(what: str, purpose: str) -> list[str]:
    """Pull verb/noun capability phrases from What-is / purpose prose."""
    text = " ".join(x for x in (what, purpose) if x)
    if not text:
        return []
    phrases = []
    seen = set()
    for pat in (
        r"ability to ([^.]+)",
        r"tools for ([^.]+)",
        r"used to ([^.]+)",
        r"exposes tools for ([^.]+)",
        r"handles ([^.]+)",
        r"provides[:\s]+([^.]+)",
        r"including ([^.]+)",
        r"detects ([^.]+)",
        r"identif(?:y|ies) ([^.]+)",
        r"cover(?:s)? ([^.]+)",
        r"enumerat(?:e|ion of) ([^.]+)",
    ):
        for m in re.finditer(pat, text, re.I):
            for part in ACTION_SPLIT.split(m.group(1)):
                part = strip_md(part).strip(" .")
                key = part.lower()
                if (
                    8 <= len(part) <= 80
                    and key not in seen
                    and not key.startswith(("the ", "is ", "are ", "and "))
                    and "so you" not in key
                    and "instead of" not in key
                ):
                    seen.add(key)
                    phrases.append(part)
    return phrases[:10]


def synthesize_prompts(title: str, purpose: str, tools: list[dict]) -> list[str]:
    prompts = []
    short_title = re.sub(r"\s+MCP Server$", "", title, flags=re.I).strip() or title
    purpose = first_sentence(purpose)[:160]
    if purpose:
        if re.match(r"^(use|run|scan|call|list|find|check|probe)\b", purpose, re.I):
            prompts.append(purpose)
        elif purpose.lower().startswith(short_title.lower()):
            rest = purpose[len(short_title):].strip(" :,-")
            prompts.append(f"Use {short_title} for {rest}" if rest else f"Use {short_title}")
        else:
            if re.match(r"^[A-Z]{2,}", purpose):
                pl = purpose
            else:
                pl = purpose[0].lower() + purpose[1:]
            prompts.append(f"Use {short_title} for {pl}")

    for t in tools:
        if not tool_is_useful(t):
            continue
        doc = first_sentence(t.get("docstring") or "")
        if not doc or doc_echoes_name(t.get("name") or "", doc):
            continue
        doc_l = doc if re.match(r"^[A-Z]{2,}", doc) else doc[0].lower() + doc[1:]
        prompts.append(f"Call {t['name']} to {doc_l}")
        if len(prompts) >= 5:
            break

    if len(prompts) < 4:
        prompts.append(f"When should I use {short_title} instead of similar tools?")
        prompts.append(f"Run {short_title} and summarize the findings")

    seen = set()
    out = []
    for p in prompts:
        k = p.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out[:6]


def kebab(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:48]


def tokens_from(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]{2,}", text or "")
    out = []
    for w in words:
        lw = w.lower()
        if lw in STOPWORDS or lw in GENERIC_TAGS:
            continue
        if lw.isdigit():
            continue
        out.append(lw)
    return out


def build_capabilities(pillar: str, purpose: str, tools: list[dict], extra_terms: list[str]) -> list[str]:
    caps: list[str] = []
    if pillar:
        caps.append(pillar)

    for t in tools:
        name = t.get("name") or ""
        if name and not HEALTH_CHECK_TOOLS.search(name) and name not in {
            "download_file",
            "cleanup_downloads",
        }:
            caps.append(kebab(name.replace("_", "-")))
        doc = first_sentence(t.get("docstring") or "")
        if doc and tool_is_useful(t):
            phrase = doc[:90].rstrip(" .,")
            if len(phrase) >= 12:
                caps.append(phrase)

    for phrase in extra_terms:
        if phrase and phrase.lower() not in GENERIC_TAGS:
            caps.append(phrase)

    # Distinctive purpose fragments as kebab tags
    for tok in tokens_from(purpose):
        if len(tok) >= 5:
            caps.append(tok)
        if len(caps) >= 22:
            break

    seen = set()
    out = []
    for c in caps:
        k = c.lower()
        if k in seen or k in GENERIC_TAGS:
            continue
        seen.add(k)
        out.append(c)
        if len(out) >= 18:
            break
    return out


def build_search_terms(
    pillar: str,
    vendor: str,
    title: str,
    purpose: str,
    tools: list[dict],
    prompts: list[str],
    existing: list[str],
) -> list[str]:
    terms: list[str] = []
    short_title = re.sub(r"\s+MCP Server$", "", title, flags=re.I)
    for item in [short_title, vendor, pillar]:
        if item:
            terms.append(item.lower())

    for t in tools:
        if not t.get("name") or t["name"] in {"download_file", "cleanup_downloads"}:
            continue
        terms.append(t["name"].replace("_", "-"))
        terms.append(t["name"].replace("_", " "))

    blob = " ".join([purpose] + prompts)
    for tok in tokens_from(blob):
        if len(tok) >= 4:
            terms.append(tok)

    for t in existing:
        tl = t.strip().strip("'\"")
        if tl.lower() not in GENERIC_TAGS:
            terms.append(tl)

    seen = set()
    out = []
    for t in terms:
        t = WHITESPACE.sub(" ", t.strip().lower())
        if not t or t in seen or t in GENERIC_TAGS or len(t) < 3:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= 22:
            break
    return out


def existing_array_items(token: str) -> list[str]:
    if not token.startswith("ARRAY["):
        return []
    inner = token[len("ARRAY[") : -1] if token.endswith("]") else token[len("ARRAY[") :]
    items = []
    for part in parse_sql_values(inner):
        items.append(unquote(part))
    return items


def build_description(sql_desc: str, what: str, summary: str, tools: list[dict], prompts: list[str]) -> str:
    purpose = core_purpose(sql_desc, summary, what)
    # Prefer the What-is prose when it is richer than the one-liner
    body = what if what and len(what) > len(purpose) + 20 else purpose
    body = strip_md(body).rstrip(".")
    body = re.sub(r"^MCP server wrapper for\s+", "", body, flags=re.I)
    body = re.sub(r"\s*See \S+ for full documentation\.?", "", body, flags=re.I)
    body = re.sub(r"\s*No API keys are required[^.]*\.?", "", body, flags=re.I)
    body = re.sub(r"\s+", " ", body).strip().rstrip(".")

    parts = [body + "."]

    useful = [
        t for t in tools
        if t.get("name")
        and not HEALTH_CHECK_TOOLS.search(t.get("name") or "")
        and t.get("name") not in {"download_file", "cleanup_downloads"}
    ]
    actions = action_phrases(what, purpose)
    cap_bits = []
    for t in useful[:10]:
        doc = first_sentence(t.get("docstring") or "")
        if doc and tool_is_useful(t):
            cap_bits.append(f"{t['name']} — {doc}")
        else:
            parts_name = t["name"].split("_")
            human = " ".join(parts_name[1:] if len(parts_name) > 1 else parts_name)
            cap_bits.append(f"{t['name']} — {human}" if human else t["name"])
    if actions:
        # Prefer prose capabilities when tool docs are generic
        if not any(tool_is_useful(t) for t in useful):
            cap_bits = actions + cap_bits[:6]
        else:
            cap_bits = cap_bits + actions
    if cap_bits:
        parts.append("Key capabilities: " + "; ".join(dict.fromkeys(cap_bits)) + ".")
    elif purpose:
        parts.append("Key capabilities: " + purpose + ".")

    if prompts:
        quoted = []
        for p in prompts[:6]:
            p = p.strip()
            if p and p[-1] not in ".!?":
                p += "."
            quoted.append(f'"{p}"')
        parts.append("Example prompts: " + " ".join(quoted))

    desc = " ".join(parts)
    desc = WHITESPACE.sub(" ", desc).strip()
    if len(desc) > 3800:
        desc = desc[:3797].rsplit(" ", 1)[0] + "..."
    return desc


def load_server_meta(values: list[str]) -> dict:
    config = unquote(values[19])
    dirname = image_to_dir(config, unquote(values[3]))
    return {
        "id": unquote(values[0]),
        "domain": unquote(values[1]),
        "pillar": unquote(values[2]),
        "title": unquote(values[3]),
        "vendor": unquote(values[5]),
        "sql_desc": unquote(values[7]),
        "dirname": dirname,
        "existing_caps": existing_array_items(values[13]),
        "existing_terms": existing_array_items(values[20]),
    }


def enrich_server(meta: dict) -> tuple[str, list[str], list[str], dict]:
    server_dir = ROOT / (meta["dirname"] or "")
    readme = extract_readme(server_dir) if server_dir.is_dir() else {
        "what": "", "summary": "", "tools": [], "prompts": []
    }
    py_tools = extract_py_tools(server_dir) if server_dir.is_dir() else []

    tools = readme["tools"] or py_tools
    if py_tools and readme["tools"]:
        # Prefer README order; fill missing docs from py
        py_map = {t["name"]: t for t in py_tools}
        merged = []
        seen = set()
        for t in readme["tools"]:
            seen.add(t["name"])
            if (not t.get("docstring") or GENERIC_TOOL_DOC.search(t["docstring"])) and t["name"] in py_map:
                merged.append(py_map[t["name"]])
            else:
                merged.append(t)
        for t in py_tools:
            if t["name"] not in seen:
                merged.append(t)
        tools = merged

    prompts = readme["prompts"]
    purpose = core_purpose(meta["sql_desc"], readme["summary"], readme["what"])
    used_synth = False
    if prompts_are_generic(prompts):
        prompts = synthesize_prompts(meta["title"], purpose, tools)
        used_synth = True

    desc = build_description(meta["sql_desc"], readme["what"], readme["summary"], tools, prompts)
    extra = action_phrases(readme["what"], purpose)
    if meta["vendor"]:
        extra.append(meta["vendor"])
    caps = build_capabilities(meta["pillar"], purpose, tools, extra)
    terms = build_search_terms(
        meta["pillar"], meta["vendor"], meta["title"], purpose, tools, prompts, meta["existing_terms"]
    )

    stats = {
        "id": meta["id"],
        "dir": meta["dirname"],
        "dir_exists": server_dir.is_dir(),
        "n_tools": len(tools),
        "n_prompts": len(prompts),
        "synth_prompts": used_synth,
        "readme_prompts": len(readme["prompts"]),
        "has_what": bool(readme["what"]),
        "desc_len": len(desc),
    }
    return desc, caps, terms, stats


def reconstruct_insert(raw_block: str, values: list[str], desc: str, caps: list[str], terms: list[str]) -> str:
    values = list(values)
    values[7] = sql_str(desc)
    values[13] = sql_array(caps)
    values[20] = sql_array(terms)
    body = ",\n".join("    " + v for v in values)
    return "INSERT INTO hdtm.g_tools VALUES (\n" + body + "\n);"


def find_inserts(sql: str) -> list[tuple[int, int, str, str]]:
    """Find INSERT blocks without matching ); that appears inside quoted strings."""
    matches = []
    needle = "INSERT INTO hdtm.g_tools VALUES ("
    i = 0
    while True:
        start = sql.find(needle, i)
        if start < 0:
            break
        inner_start = start + len(needle)
        j = inner_start
        in_str = False
        found = False
        while j < len(sql):
            c = sql[j]
            if in_str:
                if c == "'" and sql[j:j + 2] == "''":
                    j += 2
                    continue
                if c == "'":
                    in_str = False
                j += 1
                continue
            if c == "'":
                in_str = True
                j += 1
                continue
            if sql.startswith(");", j):
                block = sql[start:j + 2]
                inner = sql[inner_start:j]
                matches.append((start, j + 2, inner, block))
                i = j + 2
                found = True
                break
            j += 1
        if not found:
            break
    return matches


def main() -> int:
    dry = "--dry-run" in sys.argv
    preview = "--preview" in sys.argv
    sql = SQL_PATH.read_text(encoding="utf-8")
    matches = find_inserts(sql)
    if not matches:
        print("No INSERT statements found", file=sys.stderr)
        return 1

    if preview:
        show = {
            "farm_mcp_julius_001",
            "farm_mcp_nuclei_001",
            "farm_mcp_naabu_001",
            "farm_mcp_stripe_001",
            "farm_mcp_firecrawl_001",
            "farm_mcp_youtube_transcript_001",
            "farm_mcp_aws_s3_001",
        }
        for start, end, inner, block in matches:
            values = parse_sql_values(inner)
            meta = load_server_meta(values)
            if meta["id"] not in show:
                continue
            desc, caps, terms, st = enrich_server(meta)
            print("=" * 72)
            print(st)
            print("DESC:", desc[:1200])
            print("CAPS:", caps)
            print("TERMS:", terms[:15])
        return 0

    stats_all = []
    missing_dir = []
    no_tools = []
    synth = []
    new_sql = sql
    arity_warn = 0
    for start, end, inner, block in reversed(matches):
        values = parse_sql_values(inner)
        if len(values) != 34:
            arity_warn += 1
            print(f"WARN {values[0] if values else '?'}: expected 34 values, got {len(values)}")
        meta = load_server_meta(values)
        desc, caps, terms, st = enrich_server(meta)
        stats_all.append(st)
        if not st["dir_exists"]:
            missing_dir.append(st)
        if st["n_tools"] == 0:
            no_tools.append(st)
        if st["synth_prompts"]:
            synth.append(st)
        rebuilt = reconstruct_insert(block, values, desc, caps, terms)
        if not dry:
            new_sql = new_sql[:start] + rebuilt + new_sql[end:]

    if "-- Auto-indexing fields" in new_sql and "key capabilities + example prompts" not in new_sql:
        new_sql = new_sql.replace(
            "--   - description is stripped of markdown for clean vectorization\n",
            "--   - description is stripped of markdown and includes key capabilities + example prompts\n"
            "--   - capabilities[] lists real MCP tool actions (not generic mcp/docker tags)\n",
        )

    if not dry:
        SQL_PATH.write_text(new_sql, encoding="utf-8")

    n = len(stats_all)
    print(f"servers: {n}")
    print(f"missing dir: {len(missing_dir)}")
    print(f"no tools: {len(no_tools)}")
    print(f"synthesized prompts (generic README): {len(synth)}")
    print(f"avg desc len: {sum(s['desc_len'] for s in stats_all) / n:.0f}")
    print(f"avg tools: {sum(s['n_tools'] for s in stats_all) / n:.1f}")
    print(f"avg prompts: {sum(s['n_prompts'] for s in stats_all) / n:.1f}")
    if missing_dir:
        print("missing dirs:")
        for s in missing_dir[:20]:
            print(f"  {s['id']} -> {s['dir']}")
    if no_tools:
        print("no tools:")
        for s in no_tools[:20]:
            print(f"  {s['id']} dir={s['dir']}")

    if not dry:
        verify = find_inserts(new_sql)
        bad = 0
        generic = 0
        for start, end, inner, block in verify:
            vals = parse_sql_values(inner)
            if len(vals) != 34:
                bad += 1
            if "ARRAY['mcp', 'mcp-server', 'docker', 'mcp-farm'" in block:
                generic += 1
        print(f"verify inserts: {len(verify)} bad_arity: {bad} still_generic_caps: {generic}")
        if len(verify) != 401 or bad:
            print("ERROR: verification failed", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
