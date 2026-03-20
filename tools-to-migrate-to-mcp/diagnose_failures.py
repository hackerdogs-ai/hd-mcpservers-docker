#!/usr/bin/env python3
"""Diagnose all stdio and HTTP failures with detailed stderr capture."""
import json, subprocess, sys, os, time

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
TIMEOUT = 20

STDIO_FAILS = [
    "aws-api-mcp", "aws-bedrock-agentcore-mcp", "aws-bedrock-custom-model-mcp",
    "aws-ecs-mcp", "aws-mq-mcp", "aws-neptune-mcp", "aws-network-mcp",
    "aws-prometheus-mcp", "aws-serverless-mcp", "aws-sns-sqs-mcp",
    "azure-mcp", "baidu-search-mcp-server-mcp", "brightdata-mcp-server-mcp",
    "chrome-devtools-mcp", "cloudflare-mcp", "exa-mcp",
    "google-threat-intelligence-mcp", "imf-data-mcp", "jira-mcp",
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp", "scc-mcp",
    "sentry-mcp", "steampipe-mcp", "stripe-mcp",
]

HTTP_ONLY_FAILS = [
    "aws-aurora-dsql-mcp", "aws-cloudtrail-mcp", "aws-cloudwatch-appsignals-mcp",
    "aws-cloudwatch-mcp", "aws-documentation-mcp", "aws-documentdb-mcp",
    "aws-dynamodb-mcp", "aws-eks-mcp", "aws-iam-mcp", "aws-postgres-mcp",
    "aws-redshift-mcp", "aws-s3-tables-mcp", "aws-well-architected-security-mcp",
    "dnstwist-mcp", "fetch-mcp", "geocoding-mcp", "ms-fabric-rti-mcp",
    "osm-mcp-server-mcp", "postman-mcp", "reddit-mcp",
]

ENV_MAP = {
    "aws-api-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-bedrock-agentcore-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-bedrock-custom-model-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-ecs-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-mq-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-neptune-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-network-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-prometheus-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-serverless-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "aws-sns-sqs-mcp": ["AWS_REGION=us-east-1", "AWS_ACCESS_KEY_ID=PLACEHOLDER", "AWS_SECRET_ACCESS_KEY=PLACEHOLDER"],
    "azure-mcp": ["AZURE_CLIENT_ID=PLACEHOLDER", "AZURE_CLIENT_SECRET=PLACEHOLDER", "AZURE_TENANT_ID=PLACEHOLDER", "AZURE_SUBSCRIPTION_ID=PLACEHOLDER"],
    "brightdata-mcp-server-mcp": ["API_TOKEN=PLACEHOLDER"],
    "cloudflare-mcp": ["CLOUDFLARE_API_TOKEN=PLACEHOLDER", "CLOUDFLARE_ACCOUNT_ID=PLACEHOLDER"],
    "exa-mcp": ["EXA_API_KEY=PLACEHOLDER"],
    "google-threat-intelligence-mcp": ["VIRUSTOTAL_API_KEY=PLACEHOLDER"],
    "jira-mcp": ["JIRA_URL=https://placeholder.atlassian.net", "JIRA_EMAIL=test@test.com", "JIRA_API_TOKEN=PLACEHOLDER"],
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": ["RAPIDAPI_KEY=PLACEHOLDER"],
    "sentry-mcp": ["SENTRY_AUTH_TOKEN=PLACEHOLDER"],
    "stripe-mcp": ["STRIPE_SECRET_KEY=sk_test_PLACEHOLDER"],
    "search1api-mcp": ["SEARCH1API_KEY=PLACEHOLDER"],
}

INIT_PAYLOAD = json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}})
NOTIF_PAYLOAD = json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"})
TOOLS_PAYLOAD = json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
STDIO_INPUT = f"{INIT_PAYLOAD}\n{NOTIF_PAYLOAD}\n{TOOLS_PAYLOAD}\n"


def diagnose_stdio(name):
    env_args = ["-e", "MCP_TRANSPORT=stdio"]
    for e in ENV_MAP.get(name, []):
        env_args.extend(["-e", e])

    cmd = ["docker", "run", "-i", "--rm"] + env_args + [f"{name}:latest"]
    try:
        proc = subprocess.run(cmd, input=STDIO_INPUT, capture_output=True, text=True, timeout=TIMEOUT)
        return {"exit": proc.returncode, "stdout": proc.stdout[-500:] if proc.stdout else "", "stderr": proc.stderr[-800:] if proc.stderr else ""}
    except subprocess.TimeoutExpired:
        return {"exit": -1, "stdout": "TIMEOUT", "stderr": "TIMEOUT after 20s"}


def diagnose_http(name, port):
    """Check what happens when we start in HTTP mode."""
    env_args = ["-e", f"MCP_TRANSPORT=streamable-http", "-e", f"MCP_PORT={port}"]
    for e in ENV_MAP.get(name, []):
        env_args.extend(["-e", e])

    cname = f"diag-{name}"
    subprocess.run(["docker", "rm", "-f", cname], capture_output=True)

    cmd = ["docker", "run", "-d", "--name", cname, "-p", f"{port}:{port}"] + env_args + [f"{name}:latest"]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(6)

    logs = subprocess.run(["docker", "logs", cname], capture_output=True, text=True)
    subprocess.run(["docker", "rm", "-f", cname], capture_output=True)
    return {"stdout": logs.stdout[-500:] if logs.stdout else "", "stderr": logs.stderr[-500:] if logs.stderr else ""}


PORTS = {}
import csv
with open(os.path.join(ROOT, "tools-to-migrate-to-mcp/phase4_mapping.csv")) as f:
    for r in csv.DictReader(f):
        PORTS[r["server_name"]] = int(r["port"])

print("=" * 100)
print("STDIO FAILURE DIAGNOSIS")
print("=" * 100)
for name in STDIO_FAILS:
    print(f"\n--- {name} ---")
    r = diagnose_stdio(name)
    print(f"exit={r['exit']}")
    if r["stderr"]:
        print(f"STDERR: {r['stderr']}")
    if r["stdout"]:
        for line in r["stdout"].split("\n"):
            line = line.strip()
            if line:
                try:
                    msg = json.loads(line)
                    if msg.get("id") == 2 and "result" in msg:
                        print(f"tools/list OK: {len(msg['result'].get('tools',[]))} tools")
                except:
                    pass

print("\n\n" + "=" * 100)
print("HTTP-ONLY FAILURE DIAGNOSIS (stdio passes, HTTP fails)")
print("=" * 100)
for name in HTTP_ONLY_FAILS:
    port = PORTS.get(name, 8600)
    print(f"\n--- {name} (port {port}) ---")
    r = diagnose_http(name, port)
    if r["stderr"]:
        print(f"STDERR: {r['stderr']}")
    if r["stdout"]:
        print(f"STDOUT: {r['stdout']}")
