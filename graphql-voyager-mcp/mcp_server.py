#!/usr/bin/env python3
"""GraphQL-Voyager MCP Server — GraphQL schema exploration.

Generates a standalone HTML file embedding GraphQL Voyager
to visualize the target GraphQL schema.
"""

import json
import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("graphql-voyager-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8282"))

mcp = FastMCP(
    "GraphQL-Voyager MCP Server",
    instructions=(
        "GraphQL schema exploration. Generates interactive Voyager HTML reports."
    ),
)

OUTPUT_DIR = "/app/output"

@mcp.tool()
async def generate_voyager_report(
    graphql_url: str,
    output_filename: str = "voyager.html",
    auth_header: str = ""
) -> str:
    """Generate an interactive GraphQL Voyager HTML report for a target API.

    Args:
        graphql_url: The full HTTP/HTTPS endpoint of the target GraphQL API.
        output_filename: Name of the generated HTML file (default: voyager.html).
        auth_header: Optional Authorization header value (e.g., 'Bearer <token>') if required.
    """
    logger.info(f"Generating Voyager report for {graphql_url}")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    file_path = os.path.join(OUTPUT_DIR, output_filename)

    # Inject authentication into the JavaScript fetch request if provided
    auth_script = f"headers['Authorization'] = '{auth_header}';" if auth_header else ""

    # Generate the standalone HTML payload using CDNs to ensure it works beautifully on the host machine
    html_content = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GraphQL Voyager - {graphql_url}</title>
    <style>
      body {{ padding: 0; margin: 0; width: 100%; height: 100vh; overflow: hidden; }}
      #voyager {{ height: 100vh; width: 100vw; }}
    </style>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-voyager/dist/voyager.css" />
    <script src="https://cdn.jsdelivr.net/npm/react@16/umd/react.production.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/react-dom@16/umd/react-dom.production.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/graphql-voyager/dist/voyager.min.js"></script>
  </head>
  <body>
    <div id="voyager">Loading...</div>
    <script>
      function introspectionProvider(introspectionQuery) {{
        const headers = {{
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }};
        {auth_script}

        return fetch('{graphql_url}', {{
          method: 'post',
          headers: headers,
          body: JSON.stringify({{query: introspectionQuery}}),
        }}).then(response => response.json());
      }}

      GraphQLVoyager.init(document.getElementById('voyager'), {{
        introspection: introspectionProvider
      }});
    </script>
  </body>
</html>
"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return json.dumps({
            "success": True,
            "message": f"Successfully generated Voyager report.",
            "file_path": file_path,
            "instructions": f"Open {file_path} in your host machine's browser to view the interactive schema."
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to write HTML file: {e}")
        return json.dumps({
            "error": True,
            "message": f"Failed to write file: {str(e)}"
        })

def main():
    logger.info("Starting graphql-voyager-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)

if __name__ == "__main__":
    main()