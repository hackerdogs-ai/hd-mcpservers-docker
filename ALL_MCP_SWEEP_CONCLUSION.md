# MCP test sweep — conclusion

Source: `ALL_MCP_TESTS_SUMMARY.tsv` (machine) and `all-mcp-servers.csv` (human-readable).

| Metric | Value |
|--------|------:|
| Servers exercised | **386** |
| **PASS** | **350** |
| **FAIL** | **36** |

**Overall: FAILED** — the suite does not fully pass until all 386 rows are PASS.

Details per server: **`all-mcp-servers.csv`** (`result`, `notes`). Evidence: **`<server>/test-results.txt`**.

Common failure themes (see `notes` column):

- **HTTP `tools/list` / streamable HTTP** — AWS, API, and several third-party images (credentials, startup time, or HTTP transport).
- **stdio `tools/list`** — Azure, Notion, Cloudflare, Brave, Bright Data, etc. (auth / env / upstream).
- **`hd_fetch` missing** — dirb, dirsearch, feroxbuster, gobuster (shared Python dependency gap).
- **Docker build** — Bettercap, Gitleaks, Horusec, Subjack, vulnerability-scanner (install / network / Dockerfile step).
- **Upstream / infra** — ai-humanizer (`api.edgeshop.ai` DNS), x8-mcp (invalid `x8-builder` base image).
- **Environment** — boofuzz-mcp (port **8333** already in use during sweep).

Regenerate CSV from the TSV (after a new sweep):

```bash
# Re-run the generator in scripts/ or use the committed all-mcp-servers.csv as reference;
# TSV is written by scripts/run-all-mcp-tests.sh
```
