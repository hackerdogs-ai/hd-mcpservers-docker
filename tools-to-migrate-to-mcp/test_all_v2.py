#!/usr/bin/env python3
"""
Full test of all 75 Phase 4 servers — stdio and HTTP.
Outputs JSON results and a summary table.
"""
import csv, json, subprocess, sys, time, os, urllib.request

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
TIMEOUT_STDIO = 30
TIMEOUT_HTTP = 25
HTTP_STARTUP_WAIT = 8

INIT_MSG = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}})
NOTIF_MSG = json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})
TOOLS_MSG = json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
STDIO_INPUT = f"{INIT_MSG}\n{NOTIF_MSG}\n{TOOLS_MSG}\n"

ENV_MAP = {
    "aws-api-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-aurora-dsql-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-bedrock-agentcore-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-bedrock-custom-model-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-cloudtrail-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-cloudwatch-appsignals-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-cloudwatch-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-core-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-documentation-mcp": {},
    "aws-documentdb-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-dynamodb-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-ecs-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-eks-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-iam-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-mq-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-neptune-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-network-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-postgres-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-prometheus-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-redshift-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-s3-tables-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-serverless-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-sns-sqs-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-stepfunctions-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "aws-well-architected-security-mcp": {"AWS_REGION":"us-east-1","AWS_ACCESS_KEY_ID":"PLACEHOLDER","AWS_SECRET_ACCESS_KEY":"PLACEHOLDER"},
    "azure-mcp": {"AZURE_CLIENT_ID":"PLACEHOLDER","AZURE_CLIENT_SECRET":"PLACEHOLDER","AZURE_TENANT_ID":"PLACEHOLDER","AZURE_SUBSCRIPTION_ID":"PLACEHOLDER"},
    "baidu-search-mcp-server-mcp": {},
    "brave-search-mcp": {"BRAVE_API_KEY":"PLACEHOLDER"},
    "brightdata-mcp-server-mcp": {"API_TOKEN":"PLACEHOLDER"},
    "chrome-devtools-mcp": {},
    "cloudflare-mcp": {"CLOUDFLARE_API_TOKEN":"PLACEHOLDER","CLOUDFLARE_ACCOUNT_ID":"PLACEHOLDER"},
    "exa-mcp": {"EXA_API_KEY":"PLACEHOLDER"},
    "fetch-mcp": {},
    "geocoding-mcp": {},
    "google-threat-intelligence-mcp": {"VIRUSTOTAL_API_KEY":"PLACEHOLDER"},
    "imf-data-mcp": {},
    "jira-mcp": {"JIRA_URL":"https://placeholder.atlassian.net","JIRA_API_TOKEN":"PLACEHOLDER"},
    "ms-fabric-rti-mcp": {},
    "osm-mcp-server-mcp": {},
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": {"RAPIDAPI_KEY":"PLACEHOLDER"},
    "reddit-mcp": {},
    "scc-mcp": {"GOOGLE_APPLICATION_CREDENTIALS":"PLACEHOLDER"},
    "search1api-mcp": {"SEARCH1API_KEY":"PLACEHOLDER"},
    "sentry-mcp": {"SENTRY_AUTH_TOKEN":"PLACEHOLDER"},
    "steampipe-mcp": {"STEAMPIPE_DATABASE_URL":"postgresql://steampipe:pass@localhost:9193/steampipe"},
    "stripe-mcp": {"STRIPE_SECRET_KEY":"sk_test_PLACEHOLDER"},
}


def test_stdio(name, envs):
    """Test a server in stdio mode. Returns (pass, num_tools, error)."""
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
    """Test a server in HTTP mode. Returns (pass, num_tools, error)."""
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
        req = urllib.request.Request(url, data=INIT_MSG.encode(),
                                     headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"})
        resp = urllib.request.urlopen(req, timeout=10)
        body = resp.read().decode()
        session_id = resp.headers.get("mcp-session-id", "")

        if not session_id:
            for line in body.split("\n"):
                if "session" in line.lower():
                    pass

        if session_id:
            req2 = urllib.request.Request(url, data=NOTIF_MSG.encode(),
                                          headers={"Content-Type":"application/json","mcp-session-id":session_id})
            try:
                urllib.request.urlopen(req2, timeout=5)
            except:
                pass

            req3 = urllib.request.Request(url, data=TOOLS_MSG.encode(),
                                          headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","mcp-session-id":session_id})
            resp3 = urllib.request.urlopen(req3, timeout=10)
            body3 = resp3.read().decode()

            for line in body3.split("\n"):
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

        return False, 0, "no tools/list response"
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
            print(f"    stdio err: {s_err[:120]}")
        if not h_pass:
            print(f"    http err: {h_err[:120]}")

        results.append({
            "server": name, "port": port,
            "stdio_pass": s_pass, "stdio_tools": s_tools, "stdio_err": s_err,
            "http_pass": h_pass, "http_tools": h_tools, "http_err": h_err
        })

    # Summary
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

    with open(os.path.join(ROOT, "tools-to-migrate-to-mcp/test_results_v2.json"), "w") as f:
        json.dump(results, f, indent=2)

    return 0 if both == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
