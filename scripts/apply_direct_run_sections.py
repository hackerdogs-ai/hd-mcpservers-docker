#!/usr/bin/env python3
"""Replace generic 'Running the tool directly' sections with tool-specific content."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.direct_run_content import DIRECT_RUN_CONTENT

def extract_binary(mcp_server_path: Path) -> str:
    if not mcp_server_path.exists():
        return ""
    text = mcp_server_path.read_text()
    m = re.search(
        r'(?:BIN_NAME|[A-Z_]*BIN[A-Z_]*)\s*=\s*os\.environ\.get\s*\(\s*["\'][^"\']+["\']\s*,\s*["\']([^"\']+)["\']\s*\)',
        text,
    )
    if m:
        return m.group(1)
    m = re.search(r'shutil\.which\s*\(\s*["\']([^"\']+)["\']\s*\)', text)
    if m:
        return m.group(1)
    return ""

def main():
    skip = {"naabu-mcp", "nikto-mcp"}  # Already have custom sections
    section_header = "## Running the tool directly (bypassing MCP)"

    for dir_name, (intro, examples) in DIRECT_RUN_CONTENT.items():
        if dir_name in skip:
            continue
        readme = ROOT / dir_name / "README.md"
        mcp_server = ROOT / dir_name / "mcp_server.py"
        if not readme.exists():
            print(f"Skip (no README): {dir_name}")
            continue
        content = readme.read_text()
        if section_header not in content:
            print(f"Skip (no direct-run section): {dir_name}")
            continue

        binary = extract_binary(mcp_server)
        if not binary:
            print(f"Skip (no binary): {dir_name}")
            continue

        image = f"hackerdogs/{dir_name}:latest"
        lines = [
            "",
            "## Running the tool directly (bypassing MCP)",
            "",
            intro,
            "",
        ]
        for title, cmd_suffix in examples:
            cmd = f"docker run -i --rm --entrypoint {binary} {image} {cmd_suffix}".strip()
            lines.append(f"**{title}:**")
            lines.append("")
            lines.append("```bash")
            lines.append(cmd)
            lines.append("```")
            lines.append("")

        new_section = "\n".join(lines).rstrip()

        old_section_start = "\n" + section_header + "\n\n"
        idx = content.find(old_section_start)
        if idx == -1:
            print(f"Could not find section start: {dir_name}")
            continue
        # Find end of section: next ## or end of file
        rest = content[idx + len(old_section_start):]
        next_h2 = rest.find("\n## ")
        if next_h2 >= 0:
            end_idx = idx + len(old_section_start) + next_h2
        else:
            end_idx = len(content)
        new_content = content[:idx] + new_section + content[end_idx:]

        readme.write_text(new_content)
        print(f"Updated: {dir_name}")

if __name__ == "__main__":
    main()
