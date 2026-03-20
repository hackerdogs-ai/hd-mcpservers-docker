#!/usr/bin/env python3
"""
Full test of all 75 Phase 4 servers — stdio and HTTP.
v3: Complete env vars, better SSE parsing, curl-based HTTP tests.
"""
import csv, json, subprocess, sys, time, os

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
TIMEOUT_STDIO = 60
HTTP_STARTUP_WAIT = 20

INIT_MSG = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}})
NOTIF_MSG = json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})
TOOLS_MSG = json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
STDIO_INPUT = f"{INIT_MSG}\n{NOTIF_MSG}\n{TOOLS_MSG}\n"

ENV_MAP = {
    "aws-api-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-aurora-dsql-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-bedrock-agentcore-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-bedrock-custom-model-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-cloudtrail-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-cloudwatch-appsignals-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-cloudwatch-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-core-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-documentation-mcp": {},
    "aws-documentdb-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-dynamodb-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-ecs-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-eks-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-iam-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-mq-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-neptune-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-network-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-postgres-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-prometheus-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-redshift-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-s3-tables-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-serverless-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-sns-sqs-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-stepfunctions-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "aws-well-architected-security-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},
    "azure-mcp": {"AZURE_CLIENT_ID":"PLACEHOLDER","AZURE_CLIENT_SECRET":"PLACEHOLDER","AZURE_TENANT_ID":"PLACEHOLDER","AZURE_SUBSCRIPTION_ID":"PLACEHOLDER"},
    "baidu-search-mcp-server-mcp": {},
    "brave-search-mcp": {"BRAVE_API_KEY":"PLACEHOLDER"},
    "brightdata-mcp-server-mcp": {"API_TOKEN":"PLACEHOLDER"},
    "chrome-devtools-mcp": {},
    "cloudflare-mcp": {"CLOUDFLARE_API_TOKEN":"PLACEHOLDER","CLOUDFLARE_ACCOUNT_ID":"PLACEHOLDER"},
    "exa-mcp": {"EXA_API_KEY":"PLACEHOLDER"},
    "fetch-mcp": {},
    "firecrawl-mcp": {"FIRECRAWL_API_KEY":"PLACEHOLDER"},
    "geocoding-mcp": {},
    "gitlab-mcp": {"GITLAB_PERSONAL_ACCESS_TOKEN":"PLACEHOLDER"},
    "google-threat-intelligence-mcp": {"VIRUSTOTAL_API_KEY":"PLACEHOLDER"},
    "greynoise-mcp": {"GREYNOISE_API_KEY":"PLACEHOLDER"},
    "hibp-mcp": {"HIBP_API_KEY":"PLACEHOLDER"},
    "imf-data-mcp": {},
    "jira-mcp": {"JIRA_URL":"https://placeholder.atlassian.net","JIRA_API_TOKEN":"PLACEHOLDER"},
    "ms-fabric-rti-mcp": {},
    "octagon-mcp-server-mcp": {"OCTAGON_API_KEY":"PLACEHOLDER"},
    "osm-mcp-server-mcp": {},
    "postman-mcp": {"POSTMAN_API_KEY":"PLACEHOLDER"},
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": {"RAPIDAPI_KEY":"PLACEHOLDER"},
    "reddit-mcp": {},
    "s3-mcp-server-mcp": {"AWS_ACCESS_KEY_ID":"AKIAIOSFODNN7EXAMPLE","AWS_SECRET_ACCESS_KEY":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY","AWS_REGION":"us-east-1"},
    "scc-mcp": {},
    "search1api-mcp": {"SEARCH1API_KEY":"PLACEHOLDER"},
    "sentry-mcp": {"SENTRY_AUTH_TOKEN":"PLACEHOLDER"},
    "serper-search-mcp": {"SERPER_API_KEY":"PLACEHOLDER"},
    "steampipe-mcp": {"STEAMPIPE_DATABASE_URL":"postgresql://steampipe:pass@localhost:9193/steampipe"},
    "stripe-mcp": {"STRIPE_SECRET_KEY":"sk_test_PLACEHOLDER"},
    "winston-ai-mcp": {"WINSTONAI_API_KEY":"PLACEHOLDER"},
}


def test_stdio(name, envs):
    """Test a server in stdio mode."""
    cmd = ["docker", "run", "-i", "--rm", "-e", "MCP_TRANSPORT=stdio"]
    for k, v in envs.items():
        cmd.extend(["-e", f"{k}={v}"])
    cmd.append(f"{name}:latest")

    try:
        proc = subprocess.run(cmd, input=STDIO_INPUT, capture_output=True, text=True, timeout=TIMEOUT_STDIO)
        for line in proc.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                if msg.get("id") == 2 and "result" in msg:
                    tools = msg["result"].get("tools", [])
                    return True, len(tools), ""
            except json.JSONDecodeError:
                continue
        stderr = proc.stderr[-300:] if proc.stderr else ""
        return False, 0, f"exit={proc.returncode} {stderr}"
    except subprocess.TimeoutExpired:
        return False, 0, "TIMEOUT"


def test_http(name, port, envs):
    """Test a server in HTTP mode using curl for robust SSE handling."""
    cname = f"test-http-{name}"
    subprocess.run(["docker", "rm", "-f", cname], capture_output=True)

    cmd = ["docker", "run", "-d", "--name", cname, "-p", f"{port}:{port}",
           "-e", "MCP_TRANSPORT=streamable-http", "-e", f"MCP_PORT={port}"]
    for k, v in envs.items():
        cmd.extend(["-e", f"{k}={v}"])
    cmd.append(f"{name}:latest")

    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(HTTP_STARTUP_WAIT)

    url = f"http://localhost:{port}/mcp"
    try:
        # Step 1: Initialize — use curl for reliability
        init_result = subprocess.run(
            ["curl", "-s", "-D", "-", "-X", "POST", url,
             "-H", "Content-Type: application/json",
             "-H", "Accept: application/json, text/event-stream",
             "-d", INIT_MSG],
            capture_output=True, text=True, timeout=15
        )
        init_out = init_result.stdout

        # Extract session ID from headers
        session_id = ""
        for line in init_out.split("\n"):
            if line.lower().startswith("mcp-session-id:"):
                session_id = line.split(":", 1)[1].strip()
                break

        if not session_id:
            # For proxied servers, try to parse init response and proceed anyway
            for line in init_out.split("\n"):
                line = line.strip()
                if line.startswith("data:"):
                    line = line[5:].strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get("id") == 1 and "result" in msg:
                        session_id = "__stateless__"
                        break
                except:
                    continue
            if not session_id:
                return False, 0, f"no session_id in init response"

        # Step 2: Send initialized notification
        subprocess.run(
            ["curl", "-s", "-X", "POST", url,
             "-H", "Content-Type: application/json",
             "-H", f"mcp-session-id: {session_id}",
             "-d", NOTIF_MSG],
            capture_output=True, text=True, timeout=10
        )

        # Step 3: Request tools/list
        tools_result = subprocess.run(
            ["curl", "-s", "-X", "POST", url,
             "-H", "Content-Type: application/json",
             "-H", "Accept: application/json, text/event-stream",
             "-H", f"mcp-session-id: {session_id}",
             "-d", TOOLS_MSG],
            capture_output=True, text=True, timeout=15
        )
        body = tools_result.stdout

        # Parse SSE or direct JSON response
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                line = line[5:].strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                if msg.get("id") == 2 and "result" in msg:
                    tools = msg["result"].get("tools", [])
                    return True, len(tools), ""
            except:
                continue

        return False, 0, f"no tools in response: {body[:150]}"
    except subprocess.TimeoutExpired:
        return False, 0, "curl timeout"
    except Exception as e:
        return False, 0, str(e)[:200]
    finally:
        subprocess.run(["docker", "rm", "-f", cname], capture_output=True)


def main():
    servers = []
    with open(os.path.join(ROOT, "tools-to-migrate-to-mcp/phase4_mapping.csv")) as f:
        for r in csv.DictReader(f):
            servers.append((r["server_name"], int(r["port"])))

    results = []
    print(f"Testing {len(servers)} servers...\n")

    for i, (name, port) in enumerate(servers):
        envs = ENV_MAP.get(name, {})
        print(f"[{i+1}/{len(servers)}] {name}...", end=" ", flush=True)

        s_pass, s_tools, s_err = test_stdio(name, envs)
        h_pass, h_tools, h_err = test_http(name, port, envs)

        status = "PASS" if s_pass and h_pass else "PARTIAL" if s_pass or h_pass else "FAIL"
        print(f"stdio={'PASS' if s_pass else 'FAIL'}({s_tools}) http={'PASS' if h_pass else 'FAIL'}({h_tools}) {status}")
        if not s_pass:
            print(f"    stdio err: {s_err[:150]}")
        if not h_pass:
            print(f"    http err: {h_err[:150]}")

        results.append({
            "server": name, "port": port,
            "stdio_pass": s_pass, "stdio_tools": s_tools, "stdio_err": s_err,
            "http_pass": h_pass, "http_tools": h_tools, "http_err": h_err
        })

    s_total = sum(1 for r in results if r["stdio_pass"])
    h_total = sum(1 for r in results if r["http_pass"])
    both = sum(1 for r in results if r["stdio_pass"] and r["http_pass"])

    print(f"\n{'='*80}")
    print(f"RESULTS: {len(results)} servers")
    print(f"  Stdio PASS: {s_total}/{len(results)}")
    print(f"  HTTP  PASS: {h_total}/{len(results)}")
    print(f"  Both  PASS: {both}/{len(results)}")

    if both < len(results):
        print(f"\nFailing servers:")
        for r in results:
            if not r["stdio_pass"] or not r["http_pass"]:
                flags = []
                if not r["stdio_pass"]:
                    flags.append(f"stdio: {r['stdio_err'][:80]}")
                if not r["http_pass"]:
                    flags.append(f"http: {r['http_err'][:80]}")
                print(f"  {r['server']}: {' | '.join(flags)}")

    with open(os.path.join(ROOT, "tools-to-migrate-to-mcp/test_results_v3.json"), "w") as f:
        json.dump(results, f, indent=2)

    return 0 if both == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
