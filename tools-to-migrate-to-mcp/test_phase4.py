#!/usr/bin/env python3
"""Comprehensive test harness for all 75 Phase 4 MCP servers.

Tests:
  1. stdio  — tools/list via docker run -i
  2. HTTP   — tools/list via streamable-http
  3. keyed  — tools/call with one tool (expects auth/key error = acceptable)
"""
import csv, json, os, signal, subprocess, sys, time, urllib.request, urllib.error

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
TIMEOUT_STDIO = 30
TIMEOUT_HTTP_START = 15
TIMEOUT_HTTP_REQ = 10

ENV_MAP = {
    "aws-api-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-aurora-dsql-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-bedrock-agentcore-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-bedrock-custom-model-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-cloudtrail-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-cloudwatch-appsignals-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-cloudwatch-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-core-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-documentdb-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-dynamodb-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-ecs-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-eks-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-iam-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-mq-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-neptune-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-network-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-postgres-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-prometheus-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-redshift-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-s3-tables-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-serverless-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-sns-sqs-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-stepfunctions-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-well-architected-security-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "azure-mcp": ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID"],
    "brave-search-mcp": ["BRAVE_API_KEY"],
    "brightdata-mcp-server-mcp": ["API_TOKEN"],
    "cloudflare-mcp": ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"],
    "exa-mcp": ["EXA_API_KEY"],
    "firecrawl-mcp": ["FIRECRAWL_API_KEY"],
    "gitlab-mcp": ["GITLAB_PERSONAL_ACCESS_TOKEN"],
    "google-threat-intelligence-mcp": ["VIRUSTOTAL_API_KEY"],
    "greynoise-mcp": ["GREYNOISE_API_KEY"],
    "hibp-mcp": ["HIBP_API_KEY"],
    "jira-mcp": ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"],
    "ms-fabric-rti-mcp": ["FABRIC_API_KEY"],
    "nasa-mcp": ["NASA_API_KEY"],
    "notion-mcp": ["OPENAI_API_KEY", "NOTION_TOKEN"],
    "octagon-mcp-server-mcp": ["OCTAGON_API_KEY"],
    "openfda-mcp": ["OPENFDA_API_KEY"],
    "pinecone-mcp": ["PINECONE_API_KEY"],
    "postman-mcp": ["POSTMAN_API_KEY"],
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": ["RAPIDAPI_KEY"],
    "s3-mcp-server-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "search1api-mcp": ["SEARCH1API_KEY"],
    "sentry-mcp": ["SENTRY_AUTH_TOKEN"],
    "serper-search-mcp": ["SERPER_API_KEY"],
    "splunk-mcp": ["SPLUNK_URL", "SPLUNK_TOKEN"],
    "stripe-mcp": ["STRIPE_SECRET_KEY"],
    "tomtom-mcp": ["TOMTOM_API_KEY"],
    "variflight-mcp": ["VARIFLIGHT_API_KEY"],
    "winston-ai-mcp": ["WINSTONAI_API_KEY"],
}

TOOL_CALLS = {
    "brave-search-mcp": {"name": "brave_web_search", "arguments": {"query": "test"}},
    "stripe-mcp": {"name": "list_customers", "arguments": {}},
    "gitlab-mcp": {"name": "list_projects", "arguments": {}},
    "cloudflare-mcp": {"name": "list_accounts", "arguments": {}},
    "exa-mcp": {"name": "search", "arguments": {"query": "test"}},
    "firecrawl-mcp": {"name": "firecrawl_scrape", "arguments": {"url": "https://example.com"}},
    "greynoise-mcp": {"name": "greynoise_ip_lookup", "arguments": {"ip": "8.8.8.8"}},
    "hibp-mcp": {"name": "get_breaches_for_account", "arguments": {"account": "test@test.com"}},
    "jira-mcp": {"name": "search_issues", "arguments": {"jql": "project=TEST"}},
    "nasa-mcp": {"name": "apod", "arguments": {}},
    "notion-mcp": {"name": "search", "arguments": {"query": "test"}},
    "pinecone-mcp": {"name": "list_indexes", "arguments": {}},
    "postman-mcp": {"name": "list_collections", "arguments": {}},
    "sentry-mcp": {"name": "list_issues", "arguments": {}},
    "search1api-mcp": {"name": "search", "arguments": {"query": "test"}},
    "serper-search-mcp": {"name": "google_search", "arguments": {"query": "test"}},
    "splunk-mcp": {"name": "search", "arguments": {"query": "index=main | head 1"}},
    "tomtom-mcp": {"name": "geocode", "arguments": {"query": "New York"}},
    "google-threat-intelligence-mcp": {"name": "get_ip_address_report", "arguments": {"ip": "8.8.8.8"}},
}

for aws in [k for k in ENV_MAP if k.startswith("aws-")]:
    if aws not in TOOL_CALLS:
        TOOL_CALLS[aws] = {"name": "help", "arguments": {}}

for k in ENV_MAP:
    if k not in TOOL_CALLS:
        TOOL_CALLS[k] = {"name": "help", "arguments": {}}


def mcp_stdio_payload():
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                   "clientInfo": {"name": "test", "version": "0.1"}}})
    notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
    tools = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    return f"{init}\n{notif}\n{tools}\n"


def mcp_stdio_payload_with_call(tool_name, arguments):
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                   "clientInfo": {"name": "test", "version": "0.1"}}})
    notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
    tools = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    call = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": tool_name, "arguments": arguments}})
    return f"{init}\n{notif}\n{tools}\n{call}\n"


def test_stdio(server_name, port, has_keys):
    """Test stdio mode: tools/list and optionally tools/call."""
    image = f"{server_name}:latest"
    env_args = ["-e", "MCP_TRANSPORT=stdio"]
    env_vars = ENV_MAP.get(server_name, [])
    for v in env_vars:
        env_args.extend(["-e", f"{v}=PLACEHOLDER"])

    if has_keys and server_name in TOOL_CALLS:
        tc = TOOL_CALLS[server_name]
        payload = mcp_stdio_payload_with_call(tc["name"], tc["arguments"])
    else:
        payload = mcp_stdio_payload()

    cmd = ["docker", "run", "-i", "--rm"] + env_args + [image]
    try:
        proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=TIMEOUT_STDIO)
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return {"list": "TIMEOUT", "tools": [], "call": "TIMEOUT", "raw": "timeout"}
    except Exception as e:
        return {"list": "ERROR", "tools": [], "call": str(e), "raw": str(e)}

    tools_found = []
    list_ok = False
    call_result = None

    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except:
            continue
        if isinstance(msg, dict) and msg.get("id") == 2:
            if "result" in msg and "tools" in msg["result"]:
                tools_found = [t.get("name", "?") for t in msg["result"]["tools"]]
                list_ok = True
            elif "error" in msg:
                list_ok = False
        elif isinstance(msg, dict) and msg.get("id") == 3:
            call_result = msg

    result = {
        "list": "PASS" if list_ok else "FAIL",
        "tools": tools_found,
        "tool_count": len(tools_found),
    }
    if has_keys and call_result:
        result["call_result"] = json.dumps(call_result, indent=2)[:500]
    elif has_keys:
        result["call_result"] = "no response"

    return result


def test_http(server_name, port):
    """Test HTTP streamable mode: tools/list."""
    container_name = f"test-{server_name}"
    image = f"{server_name}:latest"

    env_args = ["-e", "MCP_TRANSPORT=streamable-http", "-e", f"MCP_PORT={port}"]
    env_vars = ENV_MAP.get(server_name, [])
    for v in env_vars:
        env_args.extend(["-e", f"{v}=PLACEHOLDER"])

    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

    cmd = ["docker", "run", "-d", "--rm", "--name", container_name,
           "-p", f"{port}:{port}"] + env_args + [image]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return {"list": "FAIL_START", "error": r.stderr[:200]}

    time.sleep(5)

    url = f"http://localhost:{port}/mcp"
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

    try:
        init_data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                 "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                            "clientInfo": {"name": "test", "version": "0.1"}}}).encode()
        req = urllib.request.Request(url, data=init_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=TIMEOUT_HTTP_REQ) as resp:
            session_id = resp.headers.get("mcp-session-id", "")
            init_body = resp.read().decode()
    except Exception as e:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        return {"list": "FAIL_INIT", "error": str(e)[:200]}

    if not session_id:
        for line in init_body.split('\n'):
            if 'mcp-session-id' in line.lower():
                session_id = line.split(':')[-1].strip()
                break
        if not session_id and 'event:' in init_body:
            for line in init_body.split('\n'):
                if line.startswith('data:'):
                    try:
                        d = json.loads(line[5:])
                        if isinstance(d, dict) and d.get("id") == 1:
                            pass
                    except:
                        pass

    try:
        notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode()
        h2 = dict(headers)
        if session_id:
            h2["mcp-session-id"] = session_id
        req2 = urllib.request.Request(url, data=notif, headers=h2, method="POST")
        urllib.request.urlopen(req2, timeout=TIMEOUT_HTTP_REQ)
    except:
        pass

    try:
        tools_data = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}).encode()
        h3 = dict(headers)
        if session_id:
            h3["mcp-session-id"] = session_id
        req3 = urllib.request.Request(url, data=tools_data, headers=h3, method="POST")
        with urllib.request.urlopen(req3, timeout=TIMEOUT_HTTP_REQ) as resp3:
            body = resp3.read().decode()
    except Exception as e:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        return {"list": "FAIL_TOOLS", "error": str(e)[:200]}

    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

    tools_found = []
    for line in body.split('\n'):
        line = line.strip()
        if line.startswith('data:'):
            line = line[5:].strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if isinstance(msg, dict) and "result" in msg and "tools" in msg["result"]:
                tools_found = [t.get("name", "?") for t in msg["result"]["tools"]]
        except:
            continue

    if not tools_found:
        try:
            msg = json.loads(body)
            if "result" in msg and "tools" in msg["result"]:
                tools_found = [t.get("name", "?") for t in msg["result"]["tools"]]
        except:
            pass

    return {
        "list": "PASS" if tools_found else "FAIL",
        "tools": tools_found,
        "tool_count": len(tools_found),
    }


def main():
    with open(os.path.join(ROOT, 'tools-to-migrate-to-mcp/phase4_mapping.csv')) as f:
        servers = list(csv.DictReader(f))

    results = []
    total = len(servers)

    for i, row in enumerate(servers):
        name = row['server_name']
        port = int(row['port'])
        has_keys = name in ENV_MAP and len(ENV_MAP[name]) > 0

        print(f"\n[{i+1}/{total}] {name} (port {port}, keys={'yes' if has_keys else 'no'})")
        print(f"  stdio...", end=" ", flush=True)
        stdio = test_stdio(name, port, has_keys)
        print(f"{stdio['list']} ({stdio.get('tool_count', 0)} tools)")

        print(f"  http ...", end=" ", flush=True)
        http = test_http(name, port)
        print(f"{http['list']} ({http.get('tool_count', 0)} tools)")

        result = {
            "server": name,
            "port": port,
            "has_keys": has_keys,
            "stdio_list": stdio["list"],
            "stdio_tools": stdio.get("tool_count", 0),
            "http_list": http["list"],
            "http_tools": http.get("tool_count", 0),
        }
        if has_keys and "call_result" in stdio:
            result["call_result"] = stdio["call_result"]

        results.append(result)

    print("\n" + "=" * 100)
    print("PHASE 4 TEST RESULTS")
    print("=" * 100)
    print(f"{'Server':<50} {'stdio':>8} {'#tools':>7} {'http':>8} {'#tools':>7} {'keys':>5}")
    print("-" * 100)

    stdio_pass = http_pass = keyed_tested = 0
    for r in results:
        keys_str = "yes" if r["has_keys"] else "-"
        print(f"{r['server']:<50} {r['stdio_list']:>8} {r['stdio_tools']:>7} {r['http_list']:>8} {r['http_tools']:>7} {keys_str:>5}")
        if r["stdio_list"] == "PASS":
            stdio_pass += 1
        if r["http_list"] == "PASS":
            http_pass += 1
        if r["has_keys"]:
            keyed_tested += 1

    print("-" * 100)
    print(f"stdio PASS: {stdio_pass}/{total}")
    print(f"http  PASS: {http_pass}/{total}")
    print(f"keyed servers tested: {keyed_tested}")

    print("\n\n" + "=" * 100)
    print("KEYED SERVERS — TOOL CALL RESULTS")
    print("=" * 100)
    for r in results:
        if r.get("call_result"):
            print(f"\n--- {r['server']} ---")
            print(r["call_result"])

    with open(os.path.join(ROOT, 'tools-to-migrate-to-mcp/phase4_test_results.json'), 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to tools-to-migrate-to-mcp/phase4_test_results.json")


if __name__ == "__main__":
    main()
