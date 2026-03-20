#!/usr/bin/env python3
"""Fix the supergateway Dockerfile layer to use proper multi-stage build."""
import os, re

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"

SERVERS = open(os.path.join(ROOT, "tools-to-migrate-to-mcp/rebuild_list.txt")).read().strip().split("\n")

OLD_LAYER = """
# Add Node.js + supergateway for HTTP mode
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
RUN node -e "const{execSync:e}=require('child_process');e('npm install -g supergateway',{stdio:'inherit'})"
"""

NEW_LAYER = """
# Add Node.js + supergateway for HTTP mode
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node:20-slim /usr/local/bin/npm /usr/local/bin/npm
COPY --from=node:20-slim /usr/local/bin/npx /usr/local/bin/npx
RUN npm install -g supergateway && npm cache clean --force
"""

count = 0
for server in SERVERS:
    df_path = os.path.join(ROOT, server, "Dockerfile")
    if not os.path.isfile(df_path):
        continue
    content = open(df_path).read()
    if OLD_LAYER.strip() in content:
        content = content.replace(OLD_LAYER.strip(), NEW_LAYER.strip())
        with open(df_path, "w") as f:
            f.write(content)
        print(f"  fixed {server}")
        count += 1

print(f"\nFixed {count} Dockerfiles")
