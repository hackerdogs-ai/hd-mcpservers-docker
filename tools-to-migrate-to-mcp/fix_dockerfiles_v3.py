#!/usr/bin/env python3
"""Fix supergateway Dockerfile and entrypoint paths."""
import os

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
SERVERS = open(os.path.join(ROOT, "tools-to-migrate-to-mcp/rebuild_list.txt")).read().strip().split("\n")

OLD_SG = """# Add Node.js + supergateway for HTTP mode
COPY --from=supergateway-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=supergateway-builder /opt/supergateway /opt/supergateway"""

NEW_SG = """# Add Node.js + supergateway for HTTP mode
COPY --from=supergateway-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=supergateway-builder /usr/local/lib/node_modules/supergateway /usr/local/lib/node_modules/supergateway"""

count = 0
for server in SERVERS:
    df_path = os.path.join(ROOT, server, "Dockerfile")
    if not os.path.isfile(df_path):
        continue
    content = open(df_path).read()
    if OLD_SG in content:
        content = content.replace(OLD_SG, NEW_SG)
        with open(df_path, "w") as f:
            f.write(content)
        print(f"  fixed Dockerfile: {server}")
        count += 1

# Fix entrypoints to use the correct supergateway path
for server in SERVERS:
    ep_path = os.path.join(ROOT, server, "entrypoint.sh")
    if not os.path.isfile(ep_path):
        continue
    content = open(ep_path).read()
    old_ep = "node /opt/supergateway/lib/node_modules/supergateway/bin/supergateway.mjs"
    new_ep = "node /usr/local/lib/node_modules/supergateway/dist/index.js"
    if old_ep in content:
        content = content.replace(old_ep, new_ep)
        with open(ep_path, "w") as f:
            f.write(content)
        print(f"  fixed entrypoint: {server}")

print(f"\nFixed {count} Dockerfiles")
