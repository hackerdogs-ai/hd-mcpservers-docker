#!/bin/sh
export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
export AWS_DEFAULT_PROFILE=
export FASTMCP_TRANSPORT=${MCP_TRANSPORT:-stdio}
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=${MCP_PORT:-8668}
# Patch lifespan to handle missing database gracefully
python3 << 'PYEOF'
import pathlib
p = pathlib.Path('/usr/local/lib/python3.11/site-packages/steampipe_mcp_server/server.py')
if p.exists():
    t = p.read_text()
    t = t.replace(
        "await db_service.connect()\n        yield {\"db_service\": db_service}",
        "try:\n            await db_service.connect()\n        except Exception:\n            logger.warning('Database connection failed')\n        yield {\"db_service\": db_service}"
    )
    t = t.replace(
        "await db_service.close()",
        "try:\n            await db_service.close()\n        except Exception:\n            pass"
    )
    p.write_text(t)
PYEOF
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec steampipe-mcp-server --database-url "${STEAMPIPE_DATABASE_URL:-postgresql://steampipe:pass@localhost:9193/steampipe}"
else
  export FASTMCP_TRANSPORT=stdio
  exec python /mcp_http_proxy.py --port ${MCP_PORT:-8668} -- steampipe-mcp-server --database-url "${STEAMPIPE_DATABASE_URL:-postgresql://steampipe:pass@localhost:9193/steampipe}"
fi
