#!/usr/bin/env python3
"""Generate corrected mcpServer.json for all 75 Phase 4 servers."""
import json, os

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"

ENV_MAP = {
    "ai-humanizer-mcp": [],
    "aws-api-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-aurora-dsql-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-bedrock-agentcore-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-bedrock-custom-model-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-cloudtrail-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-cloudwatch-appsignals-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-cloudwatch-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-core-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "aws-documentation-mcp": [],
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
    "baidu-search-mcp-server-mcp": [],
    "brave-search-mcp": ["BRAVE_API_KEY"],
    "brightdata-mcp-server-mcp": ["API_TOKEN"],
    "chrome-devtools-mcp": [],
    "clinicaltrialsgov-mcp-server-mcp": [],
    "cloudflare-mcp": ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"],
    "context7-mcp": [],
    "dns-mcp-server-mcp": [],
    "dnstwist-mcp": [],
    "exa-mcp": ["EXA_API_KEY"],
    "exiftool-agent-mcp": [],
    "fetch-mcp": [],
    "firecrawl-mcp": ["FIRECRAWL_API_KEY"],
    "geocoding-mcp": [],
    "gitlab-mcp": ["GITLAB_PERSONAL_ACCESS_TOKEN"],
    "globalping-mcp": [],
    "google-threat-intelligence-mcp": ["VIRUSTOTAL_API_KEY"],
    "greynoise-mcp": ["GREYNOISE_API_KEY"],
    "hibp-mcp": ["HIBP_API_KEY"],
    "imf-data-mcp": [],
    "iplocate-mcp": [],
    "jira-mcp": ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"],
    "ms-fabric-rti-mcp": ["FABRIC_API_KEY"],
    "nasa-mcp": ["NASA_API_KEY"],
    "notion-mcp": ["OPENAI_API_KEY", "NOTION_TOKEN"],
    "octagon-mcp-server-mcp": ["OCTAGON_API_KEY"],
    "octocode-mcp": [],
    "openfda-mcp": ["OPENFDA_API_KEY"],
    "osm-mcp-server-mcp": [],
    "pinecone-mcp": ["PINECONE_API_KEY"],
    "postman-mcp": ["POSTMAN_API_KEY"],
    "puppeteer-mcp": [],
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": ["RAPIDAPI_KEY"],
    "reddit-mcp": [],
    "s3-mcp-server-mcp": ["AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
    "scc-mcp": [],
    "search1api-mcp": ["SEARCH1API_KEY"],
    "sentry-mcp": ["SENTRY_AUTH_TOKEN"],
    "serper-search-mcp": ["SERPER_API_KEY"],
    "splunk-mcp": ["SPLUNK_URL", "SPLUNK_TOKEN"],
    "steampipe-mcp": [],
    "stripe-mcp": ["STRIPE_SECRET_KEY"],
    "terraform-mcp": [],
    "tomtom-mcp": ["TOMTOM_API_KEY"],
    "variflight-mcp": ["VARIFLIGHT_API_KEY"],
    "whois-mcp": [],
    "winston-ai-mcp": ["WINSTONAI_API_KEY"],
    "youtube-transcript-mcp": [],
}

updated = 0
for server_name, env_vars in ENV_MAP.items():
    server_dir = os.path.join(ROOT, server_name)
    if not os.path.isdir(server_dir):
        print(f"SKIP (no dir): {server_name}")
        continue

    image = f"hackerdogs/{server_name}:latest"

    args = ["run", "-i", "--rm", "-e", "MCP_TRANSPORT"]
    for v in env_vars:
        args.extend(["-e", v])
    args.append(image)

    env_block = {"MCP_TRANSPORT": "stdio"}
    for v in env_vars:
        env_block[v] = ""

    config = {
        "mcpServers": {
            server_name: {
                "command": "docker",
                "args": args,
                "env": env_block
            }
        }
    }

    out_path = os.path.join(server_dir, "mcpServer.json")
    with open(out_path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    env_str = ", ".join(env_vars) if env_vars else "(none)"
    print(f"  {server_name}: {env_str}")
    updated += 1

print(f"\nUpdated {updated}/75 mcpServer.json files")
