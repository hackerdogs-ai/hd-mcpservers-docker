#!/usr/bin/env python3
"""Add an SEO-friendly summary and tools list paragraph just above ## Tools Reference in each MCP README."""

import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
README_GLOB = "*-mcp/README.md"
TOOLS_REF = "## Tools Reference"
BLOCK_MARKER = "**Summary.**"  # used to skip already-updated READMEs


def get_summary(content: str, tools_ref_pos: int) -> str:
    """Extract a one-sentence summary from content before Tools Reference."""
    before = content[:tools_ref_pos]
    # Prefer "MCP server wrapper for ..." line
    m = re.search(r"MCP server wrapper for \[[^\]]+\][^\n]*", before)
    if m:
        line = m.group(0).strip()
        # Strip trailing "**No API keys..." if on same line (unlikely)
        return line
    # Fallback: first non-empty, non-html, non-image line after last ##
    lines = before.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if not line or line.startswith("<") or line.startswith("!") or line.startswith("#"):
            continue
        if re.match(r"^\[.*\]\(.*\)", line) and len(line) < 200:
            continue
        if len(line) > 20 and "MCP" in line or "wrapper" in line or "tool" in line.lower():
            return line
    return "MCP server exposing security tooling via the Model Context Protocol."


def get_tools(content: str, tools_ref_pos: int) -> list[tuple[str, str]]:
    """Extract tool names and their first-line description from Tools Reference section."""
    section = content[tools_ref_pos:]
    tools = []
    # Find each ### `name` and the first following non-empty line that isn't a table or _No parameters._
    for m in re.finditer(r"###\s+`([^`]+)`\s*\n", section):
        name = m.group(1).strip()
        rest = section[m.end() :]
        desc = ""
        for line in rest.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("|") or line.startswith("_No parameters") or line.startswith("<details") or line.startswith("```"):
                break
            if line.startswith("###"):
                break
            desc = line
            break
        if not desc:
            desc = "See Tools Reference for details."
        desc = re.sub(r"\*\*([^*]+)\*\*", r"\1", desc)
        desc = re.sub(r"`([^`]+)`", r"\1", desc)
        if len(desc) > 200:
            desc = desc[:197] + "..."
        tools.append((name, desc))
    return tools


def build_block(summary: str, tools: list[tuple[str, str]]) -> str:
    """Build the SEO block: summary paragraph + list of tools and purpose (no parameters)."""
    lines = [
        "",
        "**Summary.** " + summary,
        "",
        "**Tools:**",
    ]
    for name, purpose in tools:
        lines.append(f"- `{name}` — {purpose}")
    lines.append("")
    return "\n".join(lines)


def add_seo_block(readme_path: Path) -> bool:
    """Insert SEO block just above ## Tools Reference. Returns True if updated."""
    content = readme_path.read_text()
    if BLOCK_MARKER in content and content.find(BLOCK_MARKER) < content.find(TOOLS_REF):
        return False
    idx = content.find(TOOLS_REF)
    if idx == -1:
        return False
    summary = get_summary(content, idx)
    tools = get_tools(content, idx)
    if not tools:
        return False
    block = build_block(summary, tools)
    new_content = content[:idx].rstrip() + "\n\n" + block.strip() + "\n\n" + TOOLS_REF + content[idx + len(TOOLS_REF):]
    readme_path.write_text(new_content)
    return True


def main():
    readmes = sorted(BASE.glob(README_GLOB))
    updated = 0
    for path in readmes:
        if add_seo_block(path):
            print(f"  UPDATED: {path.parent.name}")
            updated += 1
    print(f"\nDone: {updated}/{len(readmes)} READMEs updated.")


if __name__ == "__main__":
    main()
