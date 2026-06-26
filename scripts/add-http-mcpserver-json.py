#!/usr/bin/env python3
"""Add HTTP streamable-http mcpServer.json config to all server READMEs.

Reads each server's Dockerfile for MCP_PORT, then appends/updates the
mcpServer.json section in README.md to include both stdio AND HTTP configs.
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_port(server_dir):
    df = os.path.join(server_dir, "Dockerfile")
    if not os.path.isfile(df):
        return None
    text = open(df).read()
    m = re.search(r'MCP_PORT[=\s]+(\d{4,5})', text)
    if m:
        return m.group(1)
    m = re.search(r'EXPOSE\s+(\d{4,5})', text)
    if m:
        return m.group(1)
    return None

def build_mcpserver_block(name, port, image):
    return f"""## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{{
  "mcpServers": {{
    "{name}": {{
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/{image}"],
      "env": {{}}
    }}
  }}
}}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p {port}:{port} -e MCP_TRANSPORT=streamable-http hackerdogs/{image}
```

```json
{{
  "mcpServers": {{
    "{name}": {{
      "url": "http://localhost:{port}/mcp/",
      "transport": "streamable-http"
    }}
  }}
}}
```
"""

def update_readme(server_dir):
    name = os.path.basename(server_dir)
    readme_path = os.path.join(server_dir, "README.md")
    if not os.path.isfile(readme_path):
        return False, "no README.md"

    port = get_port(server_dir)
    if not port:
        return False, "no port found"

    image = f"{name}:latest"
    readme = open(readme_path, encoding="utf-8", errors="replace").read()

    new_block = build_mcpserver_block(name, port, image)

    # Remove existing mcpServer.json section (everything from ## mcpServer to next ## or EOF)
    # Handle variations: "## mcpServer.json", "## mcpServer.json (Cursor / Claude)"
    pattern = r'## mcpServer\.json[^\n]*\n(?:(?!^## |\Z).*\n?)*'
    cleaned = re.sub(pattern, '', readme, flags=re.MULTILINE).rstrip()

    # Also remove stray "For HTTP: use ..." lines
    cleaned = re.sub(r'\nFor HTTP:.*$', '', cleaned, flags=re.MULTILINE).rstrip()

    updated = cleaned + "\n\n" + new_block.rstrip() + "\n"
    open(readme_path, "w", encoding="utf-8").write(updated)
    return True, port

def main():
    servers = sys.argv[1:] if sys.argv[1:] else sorted(
        d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d))
        and os.path.isfile(os.path.join(ROOT, d, "Dockerfile"))
        and not d.startswith(".")
        and d not in ("mcpfarm", "mcpfarm-ui", "scripts", "docs", "webservice")
    )
    ok = skip = 0
    for s in servers:
        sd = os.path.join(ROOT, s) if not os.path.isabs(s) else s
        success, info = update_readme(sd)
        if success:
            ok += 1
        else:
            print(f"  SKIP {s}: {info}")
            skip += 1
    print(f"\nUpdated {ok} READMEs, skipped {skip}")

if __name__ == "__main__":
    main()
