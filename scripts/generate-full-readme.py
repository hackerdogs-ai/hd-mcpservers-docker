#!/usr/bin/env python3
"""Generate comprehensive READMEs for all MCP servers following the zap-mcp template.

Only rewrites servers with minimal READMEs (missing "## What is" section).
Extracts tool info from mcp_server.py and port/env from Dockerfile.
"""
import ast, json, os, re, sys, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HACKERDOGS_HEADER = """\
<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>
"""

INSTALLING_IN_HACKERDOGS = """\
## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use naabu to scan example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).
"""


def extract_tools_from_py(server_dir):
    """Extract tool names, docstrings, and parameters from mcp_server.py."""
    py_path = os.path.join(server_dir, "mcp_server.py")
    if not os.path.isfile(py_path):
        return []

    source = open(py_path, encoding="utf-8", errors="replace").read()
    tools = []

    # Find @mcp.tool() decorated functions
    pattern = r'@mcp\.tool\([^)]*\)\s*\nasync\s+def\s+(\w+)\(([^)]*)\)\s*(?:->\s*\w+)?\s*:\s*\n\s*"""([^"]*(?:""[^"]*)*?)"""'
    for m in re.finditer(pattern, source, re.DOTALL):
        name = m.group(1)
        params_str = m.group(2)
        docstring = m.group(3).strip()

        params = []
        for p in params_str.split(","):
            p = p.strip()
            if not p or p == "self":
                continue
            # Parse "name: type = default"
            pm = re.match(r'(\w+)\s*:\s*([^=]+?)(?:\s*=\s*(.+))?$', p)
            if pm:
                pname = pm.group(1)
                ptype = pm.group(2).strip()
                pdefault = pm.group(3).strip() if pm.group(3) else None
                params.append({"name": pname, "type": ptype, "default": pdefault,
                               "required": pdefault is None})
            else:
                # Simple "name" without type
                pm2 = re.match(r'(\w+)', p)
                if pm2:
                    params.append({"name": pm2.group(1), "type": "string",
                                   "default": None, "required": True})

        tools.append({"name": name, "docstring": docstring, "params": params})

    return tools


def extract_server_info(server_dir):
    """Extract server metadata from mcp_server.py and Dockerfile."""
    name = os.path.basename(server_dir)
    info = {"name": name, "port": None, "bin": None, "description": "",
            "title": name.replace("-mcp", "").replace("-", " ").title(),
            "env_vars": [], "needs_key": False}

    # From mcp_server.py
    py_path = os.path.join(server_dir, "mcp_server.py")
    if os.path.isfile(py_path):
        src = open(py_path, encoding="utf-8", errors="replace").read()
        # Extract description from docstring
        m = re.match(r'.*?"""(.+?)"""', src, re.DOTALL)
        if m:
            desc = m.group(1).strip().split("\n")[0]
            desc = re.sub(r'^[\w\s]+ MCP Server\s*[—–-]\s*', '', desc)
            desc = desc.rstrip(". ")
            info["description"] = desc

        # Extract BIN
        m = re.search(r'BIN\s*=\s*os\.environ\.get\(["\']BIN["\']\s*,\s*["\'](\w+)["\']\)', src)
        if m:
            info["bin"] = m.group(1)

        # Extract port
        m = re.search(r'MCP_PORT\s*=\s*int\(os\.environ\.get\(["\']MCP_PORT["\']\s*,\s*["\'](\d+)["\']\)\)', src)
        if m:
            info["port"] = m.group(1)

        # Check for API key requirements
        if re.search(r'API_KEY|_TOKEN|_SECRET|_APIKEY', src, re.IGNORECASE):
            info["needs_key"] = True

    # From Dockerfile
    df_path = os.path.join(server_dir, "Dockerfile")
    if os.path.isfile(df_path):
        df = open(df_path, encoding="utf-8", errors="replace").read()
        if not info["port"]:
            m = re.search(r'MCP_PORT[=\s]+(\d{4,5})', df)
            if m:
                info["port"] = m.group(1)
            else:
                m = re.search(r'EXPOSE\s+(\d{4,5})', df)
                if m:
                    info["port"] = m.group(1)

        # Extract extra env vars
        for m in re.finditer(r'ENV\s+(\w+)=([^\s]+)', df):
            k, v = m.group(1), m.group(2)
            if k not in ("PYTHONUNBUFFERED", "MCP_TRANSPORT", "MCP_PORT", "DEBIAN_FRONTEND",
                         "GOTOOLCHAIN", "CGO_ENABLED", "PATH", "GOPATH", "GOROOT"):
                info["env_vars"].append((k, v))

    # From mcpServer.json
    json_path = os.path.join(server_dir, "mcpServer.json")
    if os.path.isfile(json_path):
        try:
            j = json.load(open(json_path))
            servers = j.get("mcpServers", {})
            for sname, sconf in servers.items():
                env = sconf.get("env", {})
                for k, v in env.items():
                    if k not in ("MCP_TRANSPORT", "MCP_PORT") and ("KEY" in k or "TOKEN" in k or "SECRET" in k):
                        info["needs_key"] = True
                        info["env_vars"].append((k, v))
        except Exception:
            pass

    return info


def generate_readme(server_dir):
    """Generate full README following the zap-mcp template."""
    name = os.path.basename(server_dir)
    info = extract_server_info(server_dir)
    tools = extract_tools_from_py(server_dir)
    port = info["port"] or "8000"
    desc = info["description"] or "security tool"
    title = info["title"]
    bin_name = info["bin"] or name.replace("-mcp", "")

    # Determine tool name for display
    tool_display = title
    key_note = ""
    if info["needs_key"]:
        key_note = f"\n**API key required** — Set the required environment variable(s) when running the container."
    else:
        key_note = f"\n**No API keys required** — {tool_display} runs locally inside the Docker container."

    # Build tools summary
    tools_summary = ""
    tools_reference = ""
    if tools:
        tools_summary = "\n".join(f"- `{t['name']}` — {t['docstring']}" for t in tools)
        for t in tools:
            tools_reference += f"\n### `{t['name']}`\n\n{t['docstring']}\n\n"
            if t["params"]:
                tools_reference += "| Parameter | Type | Required | Default | Description |\n"
                tools_reference += "|-----------|------|----------|---------|-------------|\n"
                for p in t["params"]:
                    req = "Yes" if p["required"] else "No"
                    default = f"`{p['default']}`" if p["default"] else "—"
                    pdesc = p["name"].replace("_", " ").capitalize()
                    if p["name"] == "arguments":
                        pdesc = 'Command-line arguments (e.g. `"--help"`)'
                    elif p["name"] == "timeout_seconds":
                        pdesc = "Maximum execution time in seconds"
                    tools_reference += f"| `{p['name']}` | {p['type']} | {req} | {default} | {pdesc} |\n"
                tools_reference += "\n"
                tools_reference += f"<details>\n<summary>Example response</summary>\n\n```json\n{{\n  \"raw\": \"{bin_name} output will appear here\"\n}}\n```\n\n</details>\n"
    else:
        tools_summary = f"- `run_{bin_name.replace('-', '_')}` — Run {bin_name} with the given arguments."

    # Example prompts
    example_prompts = f"""## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run {bin_name} with --help to see all available options."
- "Use {bin_name} to scan the target 192.168.1.1."
- "What options does {bin_name} support? Show me its help output."
- "Run {bin_name} against example.com with default settings."
- "Execute {bin_name} with verbose output enabled."
- "Use the {bin_name} tool to analyze the target and report findings."
"""

    # Env vars table
    env_table = f"""## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `{port}` | HTTP port (only used with `streamable-http`) |
"""
    for k, v in info["env_vars"]:
        env_table += f"| `{k}` | `{v}` | {k.replace('_', ' ').capitalize()} |\n"

    # First tool name for curl example
    first_tool = tools[0]["name"] if tools else f"run_{bin_name.replace('-', '_')}"

    readme = f"""{HACKERDOGS_HEADER}
# {title} MCP Server

MCP server wrapper for {title} — {desc}.

## What is {title}?

{title} ({bin_name}) is a security tool that provides: **{desc.capitalize()}.**
{key_note}

**Summary.** MCP server wrapper for {title} — {desc}.

**Tools:**
{tools_summary}

## Tools Reference
{tools_reference}
{example_prompts}
## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/{name}:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  -e MCP_PORT={port} \\
  hackerdogs/{name}:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{{
  "mcpServers": {{
    "{name}": {{
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/{name}:latest"],
      "env": {{
        "MCP_TRANSPORT": "stdio"
      }}
    }}
  }}
}}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{{
  "mcpServers": {{
    "{name}": {{
      "url": "http://localhost:{port}/mcp"
    }}
  }}
}}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

{env_table}
{INSTALLING_IN_HACKERDOGS}
## Build

```bash
docker build -t hackerdogs/{name}:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name {name}-test -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  hackerdogs/{name}:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -d '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"test","version":"0.1"}}}}}}' \\
  2>&1 | grep -i mcp-session-id | awk '{{print $2}}' | tr -d '\\r\\n')

curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{{"name":"{first_tool}","arguments":{{"arguments":"--help"}}}}}}'
```

**4. Clean up:**

```bash
docker stop {name}-test
```

## Running the tool directly (bypassing MCP)

You can run the {title} CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint {bin_name} hackerdogs/{name}:latest --help
```
"""
    return readme.strip() + "\n"


def main():
    servers = sys.argv[1:] if sys.argv[1:] else sorted(
        d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d))
        and os.path.isfile(os.path.join(ROOT, d, "Dockerfile"))
        and os.path.isfile(os.path.join(ROOT, d, "README.md"))
        and not d.startswith(".")
        and d not in ("mcpfarm", "mcpfarm-ui", "scripts", "docs", "webservice")
    )

    updated = skipped = already = 0
    for s in servers:
        sd = os.path.join(ROOT, s)
        readme_path = os.path.join(sd, "README.md")

        # Check if already has full template
        existing = open(readme_path, encoding="utf-8", errors="replace").read()
        if "## What is" in existing:
            already += 1
            continue

        port = None
        df = os.path.join(sd, "Dockerfile")
        if os.path.isfile(df):
            dft = open(df).read()
            m = re.search(r'MCP_PORT[=\s]+(\d{4,5})', dft)
            if m:
                port = m.group(1)
            elif re.search(r'EXPOSE\s+(\d{4,5})', dft):
                port = re.search(r'EXPOSE\s+(\d{4,5})', dft).group(1)

        if not port:
            print(f"  SKIP {s}: no port found")
            skipped += 1
            continue

        readme_content = generate_readme(sd)
        open(readme_path, "w", encoding="utf-8").write(readme_content)
        updated += 1

    print(f"\nUpdated: {updated}, Already full: {already}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
