# MCP Servers 124–183 — Status Report

| # | Server Name | Status | Comments |
|---|-------------|--------|----------|
| 1 | roadtools-mcp | ✅ Successful | |
| 2 | ropgadget-mcp | ✅ Successful | |
| 3 | ropper-mcp | ✅ Successful | |
| 4 | rustscan-mcp | ✅ Successful | |
| 5 | scoutsuite-mcp | ✅ Successful | |
| 6 | securemcp-mcp | ❌ Failed | Server is connected but the container can't find the securemcp binary. Rebuild the image after the Dockerfile fix. |
| 7 | semgrep-mcp | ✅ Successful | |
| 8 | sherlock-mcp | ✅ Successful | |
| 9 | slowhttptest-mcp | ✅ Successful | |
| 10 | smbmap-mcp | ✅ Successful | |
| 11 | smtp-user-enum-mcp | ❌ Failed | MCP server isn't loading, so the tool isn't available (same issue as SpiderFoot). |
| 12 | smuggler-mcp | ✅ Successful | |
| 13 | social-analyzer-mcp | ✅ Successful | |
| 14 | spiderfoot-mcp | ❌ Failed | MCP server isn't loading or connecting, so the tool never appears. |
| 15 | sslscan-mcp | ✅ Successful | |
| 16 | sslyze-mcp | ✅ Successful | |
| 17 | sstimap-mcp | ✅ Successful | |
| 18 | steghide-mcp | ✅ Successful | |
| 19 | subjack-mcp | ✅ Successful | |
| 20 | sublist3r-mcp | ✅ Successful | |
| 21 | suricata-mcp | ❌ Failed | Only part of the server loaded; the run/CLI tool isn't available. Wrong integration or image needs rebuild. |
| 22 | syft-mcp | ✅ Successful | |
| 23 | terrascan-mcp | ✅ Successful | |
| 24 | testdisk-mcp | ✅ Successful | |
| 25 | testssl-mcp | ✅ Successful | |
| 26 | theharvester-mcp | ✅ Successful | |
| 27 | threat-hunting-mcp | ❌ Failed | Dockerfile installs upstream repo's requirements (discord.py, splunk-sdk, stix2, etc.) which conflict with the MCP server and cause startup crashes. |
| 28 | titus-mcp | ✅ Successful | |
| 29 | tldfinder-mcp | ✅ Successful | |
| 30 | tlsx-mcp | ✅ Successful | |
| 31 | tplmap-mcp | ✅ Successful | |
| 32 | trivy-mcp | ✅ Successful | |
| 33 | trivy-neutr0n-mcp | ✅ Successful | |
| 34 | trufflehog-mcp | ✅ Successful | |
| 35 | uncover-mcp | ✅ Successful | |
| 36 | upx-mcp | ✅ Successful | |
| 37 | urlfinder-mcp | ✅ Successful | |
| 38 | uro-mcp | ✅ Successful | |
| 39 | vanta-mcp | ❌ Failed | Vanta is a paid compliance/security platform. Not usable without valid Vanta API credentials. Fails on startup — no MCP tools are ever exposed or callable. |
| 40 | volatility-mcp | ✅ Successful | |
| 41 | volatility3-mcp | ✅ Successful | |
| 42 | vulnerability-scanner-mcp | ✅ Successful | |
| 43 | vulnx-mcp | ✅ Successful | |
| 44 | wafw00f-mcp | ✅ Successful | |
| 45 | wapiti-mcp | ✅ Successful | |
| 46 | wappalyzergo-mcp | ✅ Successful | |
| 47 | wfuzz-mcp | ✅ Successful | |
| 48 | whatweb-mcp | ✅ Successful | |
| 49 | wifiphisher-mcp | ✅ Successful | |
| 50 | wireshark-mcp | ✅ Successful | |
| 51 | wpscan-mcp | ✅ Successful | |
| 52 | x8-mcp | ✅ Successful | |
| 53 | xsser-mcp | ✅ Successful | |
| 54 | xsstrike-mcp | ✅ Successful | |
| 55 | yara-mcp | ✅ Successful | |
| 56 | yaraflux-mcp | ✅ Successful | |
| 57 | yersinia-mcp | ✅ Successful | |
| 58 | yeti-mcp | ✅ Successful | |
| 59 | zap-lis-mcp | ✅ Successful | |
| 60 | zmap-mcp | ✅ Successful | |
| 61 | zap-mcp | ✅ Successful | |
