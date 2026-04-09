#!/usr/bin/env python3
"""Fix supergateway layer with proper multi-stage build."""
import os

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
SERVERS = open(os.path.join(ROOT, "tools-to-migrate-to-mcp/rebuild_list.txt")).read().strip().split("\n")

OLD_LAYER = """# Add Node.js + supergateway for HTTP mode
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node:20-slim /usr/local/bin/npm /usr/local/bin/npm
COPY --from=node:20-slim /usr/local/bin/npx /usr/local/bin/npx
RUN npm install -g supergateway && npm cache clean --force"""

NEW_LAYER = """# Add Node.js + supergateway for HTTP mode
COPY --from=supergateway-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=supergateway-builder /opt/supergateway /opt/supergateway"""

count = 0
for server in SERVERS:
    df_path = os.path.join(ROOT, server, "Dockerfile")
    if not os.path.isfile(df_path):
        continue
    content = open(df_path).read()
    if OLD_LAYER not in content:
        continue

    content = content.replace(OLD_LAYER, NEW_LAYER)

    # Add the build stage at the top if not already there
    if "supergateway-builder" not in content.split(NEW_LAYER)[0]:
        content = "FROM node:20-slim AS supergateway-builder\nRUN npm install -g supergateway && npm cache clean --force\n\n" + content

    with open(df_path, "w") as f:
        f.write(content)
    print(f"  fixed {server}")
    count += 1

# Also fix entrypoints to use the new supergateway path
for server in SERVERS:
    ep_path = os.path.join(ROOT, server, "entrypoint.sh")
    if not os.path.isfile(ep_path):
        continue
    content = open(ep_path).read()
    old = "node /usr/local/lib/node_modules/supergateway/bin/supergateway.mjs"
    new = "node /opt/supergateway/lib/node_modules/supergateway/bin/supergateway.mjs"
    if old in content:
        content = content.replace(old, new)
        with open(ep_path, "w") as f:
            f.write(content)
        print(f"  fixed entrypoint: {server}")

print(f"\nFixed {count} Dockerfiles")
