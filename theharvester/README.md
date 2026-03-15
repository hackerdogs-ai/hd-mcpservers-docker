# theHarvester MCP Server

## Important: Patch Files

This service requires patch files (`fix_aiosqli.py` and `patch_theharvester.py`) to be present in the service directory for building.

These files are copied from the root directory. If they're missing, copy them:

```bash
cp ../../fix_aiosqli.py .
cp ../../patch_theharvester.py .
```

## Building

### From Service Directory (for publishing):
```bash
cd services/theharvester
docker build -t theharvester-mcp-server:latest .
```

### From Services Directory (docker-compose):
```bash
cd services
docker-compose build theharvester
```

Both methods require the patch files to be in the `theharvester/` directory.
