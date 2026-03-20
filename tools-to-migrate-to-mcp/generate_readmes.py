#!/usr/bin/env python3
"""Generate production-grade README.md files for all Phase 4 servers with env vars."""
import json, os, textwrap

ROOT = "/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"

SERVERS = {
    "aws-api-mcp": {
        "title": "AWS API MCP Server",
        "upstream": "awslabs.aws-api-mcp-server",
        "upstream_url": "https://github.com/awslabs/mcp",
        "runtime": "pip",
        "port": 8602,
        "what": "AWS API",
        "description": "AWS API MCP Server enables AI assistants to interact with AWS services and resources through AWS CLI commands. It provides programmatic access to any AWS service API, allowing agents to manage cloud infrastructure, query services, and automate operations across your AWS account.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8602", "desc": "HTTP port (only used with `streamable-http`)"},
            "AWS_REGION": {"default": "", "desc": "AWS region (e.g. `us-east-1`)"},
            "AWS_ACCESS_KEY_ID": {"default": "", "desc": "AWS access key ID"},
            "AWS_SECRET_ACCESS_KEY": {"default": "", "desc": "AWS secret access key"},
        },
        "api_key_note": "**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.",
        "prompts": [
            "List all S3 buckets in my account.",
            "Describe the EC2 instances running in us-east-1.",
            "What Lambda functions do I have deployed?",
        ],
    },
    "aws-aurora-dsql-mcp": {
        "title": "AWS Aurora DSQL MCP Server",
        "upstream": "awslabs.aurora-dsql-mcp-server",
        "upstream_url": "https://github.com/awslabs/mcp",
        "runtime": "pip",
        "port": 8603,
        "what": "Aurora DSQL",
        "description": "MCP server for Amazon Aurora DSQL, a distributed SQL database. Provides AI assistants with tools to query, manage, and interact with Aurora DSQL clusters and databases.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8603", "desc": "HTTP port (only used with `streamable-http`)"},
            "AWS_REGION": {"default": "", "desc": "AWS region (e.g. `us-east-1`)"},
            "AWS_ACCESS_KEY_ID": {"default": "", "desc": "AWS access key ID"},
            "AWS_SECRET_ACCESS_KEY": {"default": "", "desc": "AWS secret access key"},
        },
        "api_key_note": "**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.",
        "prompts": ["Query my Aurora DSQL cluster for active connections.", "Show me the tables in my DSQL database."],
    },
    "aws-bedrock-agentcore-mcp": {
        "title": "AWS Bedrock AgentCore MCP Server",
        "upstream": "awslabs.amazon-bedrock-agentcore-mcp-server",
        "upstream_url": "https://github.com/awslabs/mcp",
        "runtime": "pip",
        "port": 8604,
        "what": "Bedrock AgentCore",
        "description": "MCP server for Amazon Bedrock AgentCore services. Provides search and retrieval of AgentCore documentation, browser automation tools, and access to Runtime, Memory, Code Interpreter, Browser, Gateway, Observability, and Identity services.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8604", "desc": "HTTP port (only used with `streamable-http`)"},
            "AWS_REGION": {"default": "", "desc": "AWS region (e.g. `us-east-1`)"},
            "AWS_ACCESS_KEY_ID": {"default": "", "desc": "AWS access key ID"},
            "AWS_SECRET_ACCESS_KEY": {"default": "", "desc": "AWS secret access key"},
        },
        "api_key_note": "**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.",
        "prompts": ["Search for AgentCore documentation on Runtime services.", "List available Bedrock agents in my account."],
    },
    "brave-search-mcp": {
        "title": "Brave Search MCP Server",
        "upstream": "@modelcontextprotocol/server-brave-search",
        "upstream_url": "https://github.com/modelcontextprotocol/servers",
        "runtime": "npx",
        "port": 8629,
        "what": "Brave Search",
        "description": "MCP server for [Brave Search](https://brave.com/search/api/). Performs comprehensive web searches using Brave's independent search index with rich result types including web pages, news, videos, and more. Supports advanced filtering and localization options.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8629", "desc": "HTTP port (only used with `streamable-http`)"},
            "BRAVE_API_KEY": {"default": "", "desc": "Brave Search API key — get one at [brave.com/search/api](https://brave.com/search/api/)"},
        },
        "api_key_note": "**API key required** — get a free key at [brave.com/search/api](https://brave.com/search/api/).",
        "prompts": [
            "Search the web for 'latest CVE vulnerabilities 2026' using Brave.",
            "Find recent news about AI security using Brave Search.",
            "Search for documentation on Kubernetes network policies.",
        ],
    },
    "brightdata-mcp-server-mcp": {
        "title": "Bright Data MCP Server",
        "upstream": "@brightdata/mcp",
        "upstream_url": "https://github.com/brightdata/brightdata-mcp",
        "runtime": "npx",
        "port": 8630,
        "what": "Bright Data",
        "description": "MCP server for [Bright Data](https://brightdata.com/) — a web scraping and data collection platform. Provides reliable, scalable access to public web data with built-in proxy infrastructure, CAPTCHA solving, and anti-bot bypass.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8630", "desc": "HTTP port (only used with `streamable-http`)"},
            "API_TOKEN": {"default": "", "desc": "Bright Data API token"},
        },
        "api_key_note": "**API token required** — sign up at [brightdata.com](https://brightdata.com/).",
        "prompts": ["Scrape the pricing page of example.com.", "Collect product data from an e-commerce site."],
    },
    "cloudflare-mcp": {
        "title": "Cloudflare MCP Server",
        "upstream": "@cloudflare/mcp-server-cloudflare",
        "upstream_url": "https://github.com/cloudflare/mcp-server-cloudflare",
        "runtime": "npx",
        "port": 8633,
        "what": "Cloudflare",
        "description": "MCP server for [Cloudflare](https://cloudflare.com/). Manage Workers, KV namespaces, R2 buckets, D1 databases, and other Cloudflare services. Deploy, configure, and monitor your Cloudflare infrastructure through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8633", "desc": "HTTP port (only used with `streamable-http`)"},
            "CLOUDFLARE_API_TOKEN": {"default": "", "desc": "Cloudflare API token with appropriate permissions"},
            "CLOUDFLARE_ACCOUNT_ID": {"default": "", "desc": "Cloudflare account ID"},
        },
        "api_key_note": "**API token required** — create one at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens).",
        "prompts": ["List all my Cloudflare Workers.", "Show DNS records for example.com.", "Deploy a new Worker script."],
    },
    "exa-mcp": {
        "title": "Exa MCP Server",
        "upstream": "exa-mcp-server",
        "upstream_url": "https://github.com/exa-labs/exa-mcp-server",
        "runtime": "npx",
        "port": 8637,
        "what": "Exa",
        "description": "MCP server for [Exa](https://exa.ai/) — a neural search engine. Provides real-time web search, code search, research paper search, and company research capabilities using Exa's embedding-based search index.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8637", "desc": "HTTP port (only used with `streamable-http`)"},
            "EXA_API_KEY": {"default": "", "desc": "Exa API key — get one at [exa.ai](https://exa.ai/)"},
        },
        "api_key_note": "**API key required** — sign up at [exa.ai](https://exa.ai/).",
        "prompts": ["Search for recent papers on LLM security.", "Find companies working on MCP protocol tooling."],
    },
    "firecrawl-mcp": {
        "title": "Firecrawl MCP Server",
        "upstream": "firecrawl-mcp",
        "upstream_url": "https://github.com/mendableai/firecrawl-mcp",
        "runtime": "npx",
        "port": 8640,
        "what": "Firecrawl",
        "description": "MCP server for [Firecrawl](https://firecrawl.dev/) — a web scraping API that handles JavaScript rendering, anti-bot bypasses, and outputs clean markdown. Crawl entire sites or scrape individual pages with structured data extraction.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8640", "desc": "HTTP port (only used with `streamable-http`)"},
            "FIRECRAWL_API_KEY": {"default": "", "desc": "Firecrawl API key — get one at [firecrawl.dev](https://firecrawl.dev/)"},
        },
        "api_key_note": "**API key required** — sign up at [firecrawl.dev](https://firecrawl.dev/).",
        "prompts": ["Scrape the content of https://example.com and return it as markdown.", "Crawl all pages on docs.example.com."],
    },
    "gitlab-mcp": {
        "title": "GitLab MCP Server",
        "upstream": "@zereight/mcp-gitlab",
        "upstream_url": "https://github.com/zereight/mcp-gitlab",
        "runtime": "npx",
        "port": 8642,
        "what": "GitLab",
        "description": "MCP server for [GitLab](https://gitlab.com/). Enables AI clients to make authenticated API calls to GitLab, including managing repositories, issues, merge requests, pipelines, and CI/CD configurations.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8642", "desc": "HTTP port (only used with `streamable-http`)"},
            "GITLAB_PERSONAL_ACCESS_TOKEN": {"default": "", "desc": "GitLab personal access token with `api` scope"},
        },
        "api_key_note": "**Personal access token required** — create one at GitLab → Settings → Access Tokens with `api` scope.",
        "prompts": ["List open merge requests in my project.", "Show the latest pipeline status for my repo.", "Create a new issue in project X."],
    },
    "google-threat-intelligence-mcp": {
        "title": "Google Threat Intelligence MCP Server",
        "upstream": "gti-mcp",
        "upstream_url": "https://github.com/google/mcp-security",
        "runtime": "pip",
        "port": 8644,
        "what": "Google Threat Intelligence",
        "description": "MCP server for [Google Threat Intelligence](https://cloud.google.com/threat-intelligence) (GTI), including insights from Mandiant and VirusTotal. Query file hashes, URLs, domains, and IP addresses for threat data, malware analysis, and reputation scores.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8644", "desc": "HTTP port (only used with `streamable-http`)"},
            "VIRUSTOTAL_API_KEY": {"default": "", "desc": "VirusTotal / Google TI API key"},
        },
        "api_key_note": "**API key required** — get one at [virustotal.com](https://www.virustotal.com/).",
        "prompts": ["Look up the hash abc123... on VirusTotal.", "Check the reputation of domain example.com.", "Analyze this suspicious URL for threats."],
    },
    "greynoise-mcp": {
        "title": "GreyNoise MCP Server",
        "upstream": "@greynoise/greynoise-mcp-server",
        "upstream_url": "https://github.com/GreyNoise-Intelligence/greynoise-mcp",
        "runtime": "npx",
        "port": 8645,
        "what": "GreyNoise",
        "description": "MCP server for [GreyNoise](https://greynoise.io/) — internet scanner and noise intelligence platform. Query IP addresses for scan activity, classification (benign/malicious), tags, and metadata. Identify mass-scanning infrastructure vs targeted attacks.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8645", "desc": "HTTP port (only used with `streamable-http`)"},
            "GREYNOISE_API_KEY": {"default": "", "desc": "GreyNoise API key — get one at [greynoise.io](https://greynoise.io/)"},
        },
        "api_key_note": "**API key required** — sign up at [greynoise.io](https://greynoise.io/).",
        "prompts": ["Check if IP 1.2.3.4 is a known scanner.", "What is GreyNoise seeing for this IP address?", "Show me the top malicious scanners targeting port 22."],
    },
    "hibp-mcp": {
        "title": "Have I Been Pwned MCP Server",
        "upstream": "@darrenjrobinson/hibp-mcp",
        "upstream_url": "https://github.com/darrenjrobinson/hibp-mcp",
        "runtime": "npx",
        "port": 8646,
        "what": "Have I Been Pwned",
        "description": "MCP server for [Have I Been Pwned](https://haveibeenpwned.com/) (HIBP). Check email addresses and domains against known data breaches, search for compromised passwords, and retrieve breach details.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8646", "desc": "HTTP port (only used with `streamable-http`)"},
            "HIBP_API_KEY": {"default": "", "desc": "HIBP API key — purchase at [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key)"},
        },
        "api_key_note": "**API key required** — purchase at [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key).",
        "prompts": ["Has the email user@example.com been in any data breaches?", "Show me all breaches for the domain example.com."],
    },
    "jira-mcp": {
        "title": "Jira MCP Server",
        "upstream": "mcp-server-jira",
        "upstream_url": "https://github.com/smithery-ai/mcp-server-jira",
        "runtime": "pip",
        "port": 8649,
        "what": "Jira",
        "description": "MCP server for [Jira](https://www.atlassian.com/software/jira). Create, search, update, and manage Jira issues, projects, and workflows. Supports JQL queries, issue transitions, and comment management.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8649", "desc": "HTTP port (only used with `streamable-http`)"},
            "JIRA_URL": {"default": "", "desc": "Jira instance URL (e.g. `https://your-org.atlassian.net`)"},
            "JIRA_EMAIL": {"default": "", "desc": "Jira account email address"},
            "JIRA_API_TOKEN": {"default": "", "desc": "Jira API token — create at [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)"},
        },
        "api_key_note": "**API token required** — create one at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens).",
        "prompts": ["Show me all open bugs assigned to me in Jira.", "Create a new task in project DEVOPS.", "Search for Jira issues with JQL: project = SEC AND status = Open."],
    },
    "stripe-mcp": {
        "title": "Stripe MCP Server",
        "upstream": "@stripe/mcp",
        "upstream_url": "https://github.com/stripe/agent-toolkit",
        "runtime": "npx",
        "port": 8669,
        "what": "Stripe",
        "description": "MCP server for [Stripe](https://stripe.com/). Interact with Stripe's payment platform — manage customers, subscriptions, invoices, charges, and payment methods through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8669", "desc": "HTTP port (only used with `streamable-http`)"},
            "STRIPE_SECRET_KEY": {"default": "", "desc": "Stripe secret API key — find at [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)"},
        },
        "api_key_note": "**API key required** — find yours at [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys).",
        "prompts": ["List recent charges on my Stripe account.", "Show all active subscriptions.", "Look up customer cus_abc123."],
    },
    "sentry-mcp": {
        "title": "Sentry MCP Server",
        "upstream": "@sentry/mcp-server",
        "upstream_url": "https://github.com/getsentry/sentry-mcp",
        "runtime": "npx",
        "port": 8665,
        "what": "Sentry",
        "description": "MCP server for [Sentry](https://sentry.io/). Access issues, errors, projects, and Seer AI analysis. Investigate error stack traces, triage production incidents, and track error trends directly from your AI coding assistant.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8665", "desc": "HTTP port (only used with `streamable-http`)"},
            "SENTRY_AUTH_TOKEN": {"default": "", "desc": "Sentry user auth token — create at [sentry.io/settings/account/api/auth-tokens](https://sentry.io/settings/account/api/auth-tokens/)"},
        },
        "api_key_note": "**Auth token required** — create at Sentry → Settings → Auth Tokens.",
        "prompts": ["Show me the top unresolved issues in my Sentry project.", "What caused the latest crash in production?"],
    },
    "notion-mcp": {
        "title": "Notion MCP Server",
        "upstream": "@notionhq/notion-mcp-server",
        "upstream_url": "https://github.com/notionhq/notion-mcp-server",
        "runtime": "npx",
        "port": 8652,
        "what": "Notion",
        "description": "MCP server for [Notion](https://notion.so/). Search, read, create, and update pages, databases, and blocks in your Notion workspace. Manage content, knowledge bases, and project documentation through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8652", "desc": "HTTP port (only used with `streamable-http`)"},
            "OPENAI_API_KEY": {"default": "", "desc": "OpenAI API key (used for AI features)"},
            "NOTION_TOKEN": {"default": "", "desc": "Notion integration token — create at [notion.so/my-integrations](https://www.notion.so/my-integrations)"},
        },
        "api_key_note": "**Integration token required** — create at [notion.so/my-integrations](https://www.notion.so/my-integrations).",
        "prompts": ["Search my Notion workspace for pages about 'security'.", "Create a new page in my project database."],
    },
    "pinecone-mcp": {
        "title": "Pinecone MCP Server",
        "upstream": "@pinecone-database/mcp",
        "upstream_url": "https://github.com/pinecone-io/pinecone-mcp",
        "runtime": "npx",
        "port": 8657,
        "what": "Pinecone",
        "description": "MCP server for [Pinecone](https://www.pinecone.io/) — a managed vector database. Create and manage indexes, upsert and query vectors, and build semantic search and RAG applications through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8657", "desc": "HTTP port (only used with `streamable-http`)"},
            "PINECONE_API_KEY": {"default": "", "desc": "Pinecone API key — find at [app.pinecone.io](https://app.pinecone.io/)"},
        },
        "api_key_note": "**API key required** — find yours at [app.pinecone.io](https://app.pinecone.io/).",
        "prompts": ["List my Pinecone indexes.", "Query the 'documents' index for vectors similar to this text."],
    },
    "postman-mcp": {
        "title": "Postman MCP Server",
        "upstream": "@postman/postman-mcp-server",
        "upstream_url": "https://github.com/postmanlabs/postman-mcp-server",
        "runtime": "npx",
        "port": 8658,
        "what": "Postman",
        "description": "MCP server for [Postman](https://www.postman.com/). Access your Postman collections, environments, APIs, and workspaces. Run API requests, inspect responses, and manage your API development workflow through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8658", "desc": "HTTP port (only used with `streamable-http`)"},
            "POSTMAN_API_KEY": {"default": "", "desc": "Postman API key — generate at [postman.co/settings/me/api-keys](https://go.postman.co/settings/me/api-keys)"},
        },
        "api_key_note": "**API key required** — generate at [Postman API Keys](https://go.postman.co/settings/me/api-keys).",
        "prompts": ["List my Postman collections.", "Show the API endpoints in my 'Auth Service' collection."],
    },
    "search1api-mcp": {
        "title": "Search1API MCP Server",
        "upstream": "search1api-mcp",
        "upstream_url": "https://github.com/fatwang2/search1api-mcp",
        "runtime": "npx",
        "port": 8664,
        "what": "Search1API",
        "description": "MCP server for [Search1API](https://search1api.com/). Web search, news search, web page content extraction, and website sitemap retrieval through a unified API.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8664", "desc": "HTTP port (only used with `streamable-http`)"},
            "SEARCH1API_KEY": {"default": "", "desc": "Search1API key — get one at [search1api.com](https://search1api.com/)"},
        },
        "api_key_note": "**API key required** — sign up at [search1api.com](https://search1api.com/).",
        "prompts": ["Search the web for 'Kubernetes security best practices'.", "Extract the content of this URL as text."],
    },
    "serper-search-mcp": {
        "title": "Serper Search MCP Server",
        "upstream": "serper-search-scrape-mcp-server",
        "upstream_url": "https://github.com/nicholasoxford/serper-search-scrape-mcp",
        "runtime": "npx",
        "port": 8666,
        "what": "Serper",
        "description": "MCP server for [Serper](https://serper.dev/) — a Google Search API. Perform Google searches, scrape web pages, and extract structured search results with news, images, and shopping data.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8666", "desc": "HTTP port (only used with `streamable-http`)"},
            "SERPER_API_KEY": {"default": "", "desc": "Serper API key — get one at [serper.dev](https://serper.dev/)"},
        },
        "api_key_note": "**API key required** — sign up at [serper.dev](https://serper.dev/).",
        "prompts": ["Google search for 'OWASP Top 10 2025'.", "Scrape the content of this search result page."],
    },
    "splunk-mcp": {
        "title": "Splunk MCP Server",
        "upstream": "splunk-mcp",
        "upstream_url": "https://github.com/splunk/splunk-mcp",
        "runtime": "npx",
        "port": 8667,
        "what": "Splunk",
        "description": "MCP server for [Splunk](https://www.splunk.com/). Run SPL searches, query indexes, manage saved searches, and access dashboards. Investigate security events and operational data through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8667", "desc": "HTTP port (only used with `streamable-http`)"},
            "SPLUNK_URL": {"default": "", "desc": "Splunk instance URL (e.g. `https://splunk.example.com:8089`)"},
            "SPLUNK_TOKEN": {"default": "", "desc": "Splunk bearer token or session key"},
        },
        "api_key_note": "**Splunk credentials required** — set `SPLUNK_URL` and `SPLUNK_TOKEN`.",
        "prompts": ["Search Splunk for failed SSH logins in the last 24 hours.", "Show me the top 10 source IPs in the firewall index."],
    },
    "nasa-mcp": {
        "title": "NASA MCP Server",
        "upstream": "@programcomputer/nasa-mcp-server",
        "upstream_url": "https://github.com/programcomputer/nasa-mcp-server",
        "runtime": "npx",
        "port": 8651,
        "what": "NASA",
        "description": "MCP server for [NASA Open APIs](https://api.nasa.gov/). Access 20+ NASA data sources including Astronomy Picture of the Day (APOD), Mars Rover photos, Near-Earth Object tracking, satellite imagery, and more.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8651", "desc": "HTTP port (only used with `streamable-http`)"},
            "NASA_API_KEY": {"default": "", "desc": "NASA API key — get a free key at [api.nasa.gov](https://api.nasa.gov/)"},
        },
        "api_key_note": "**API key required** — get a free key at [api.nasa.gov](https://api.nasa.gov/).",
        "prompts": ["Show me today's Astronomy Picture of the Day.", "Find near-Earth asteroids approaching this week."],
    },
    "openfda-mcp": {
        "title": "OpenFDA MCP Server",
        "upstream": "@ythalorossy/openfda",
        "upstream_url": "https://github.com/ythalorossy/openfda",
        "runtime": "npx",
        "port": 8655,
        "what": "OpenFDA",
        "description": "MCP server for the [OpenFDA API](https://open.fda.gov/). Query FDA drug information, adverse event reports, drug labels, device recalls, and safety data.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8655", "desc": "HTTP port (only used with `streamable-http`)"},
            "OPENFDA_API_KEY": {"default": "", "desc": "OpenFDA API key — get one at [open.fda.gov/apis/authentication](https://open.fda.gov/apis/authentication/)"},
        },
        "api_key_note": "**API key required** — get one at [open.fda.gov](https://open.fda.gov/apis/authentication/).",
        "prompts": ["Look up drug information for ibuprofen.", "Show adverse events for a specific drug."],
    },
    "rapidapi-hub-reverse-image-search-by-copyseeker-mcp": {
        "title": "RapidAPI Reverse Image Search MCP Server",
        "upstream": "mcp-remote",
        "upstream_url": "https://rapidapi.com/",
        "runtime": "npx",
        "port": 8660,
        "what": "RapidAPI Reverse Image Search",
        "description": "MCP server for reverse image search via [RapidAPI](https://rapidapi.com/) and CopySeeker. Upload or link images to find visually similar results across the web.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8660", "desc": "HTTP port (only used with `streamable-http`)"},
            "RAPIDAPI_KEY": {"default": "", "desc": "RapidAPI key — sign up at [rapidapi.com](https://rapidapi.com/)"},
        },
        "api_key_note": "**API key required** — sign up at [rapidapi.com](https://rapidapi.com/).",
        "prompts": ["Reverse image search this URL to find similar images.", "Find the original source of this image."],
    },
    "s3-mcp-server-mcp": {
        "title": "S3 MCP Server",
        "upstream": "@geunoh/s3-mcp-server",
        "upstream_url": "https://github.com/geunoh/s3-mcp-server",
        "runtime": "npx",
        "port": 8662,
        "what": "Amazon S3",
        "description": "MCP server for [Amazon S3](https://aws.amazon.com/s3/). List buckets, browse objects, upload and download files, and manage S3 storage through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8662", "desc": "HTTP port (only used with `streamable-http`)"},
            "AWS_REGION": {"default": "", "desc": "AWS region (e.g. `us-east-1`)"},
            "AWS_ACCESS_KEY_ID": {"default": "", "desc": "AWS access key ID"},
            "AWS_SECRET_ACCESS_KEY": {"default": "", "desc": "AWS secret access key"},
        },
        "api_key_note": "**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.",
        "prompts": ["List all S3 buckets in my account.", "Show the contents of the 'my-data' bucket."],
    },
    "ms-fabric-rti-mcp": {
        "title": "Microsoft Fabric RTI MCP Server",
        "upstream": "microsoft-fabric-rti-mcp",
        "upstream_url": "https://github.com/microsoft/fabric-rti-mcp",
        "runtime": "pip",
        "port": 8650,
        "what": "Microsoft Fabric RTI",
        "description": "MCP server for [Microsoft Fabric](https://www.microsoft.com/en-us/microsoft-fabric) Real-Time Intelligence. Query and analyze real-time data streams, KQL databases, and eventhouses.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8650", "desc": "HTTP port (only used with `streamable-http`)"},
            "FABRIC_API_KEY": {"default": "", "desc": "Microsoft Fabric API key"},
        },
        "api_key_note": "**API key required** — configure in your Microsoft Fabric workspace.",
        "prompts": ["Query real-time data from my Fabric eventhouse.", "Show recent events in my KQL database."],
    },
    "octagon-mcp-server-mcp": {
        "title": "Octagon MCP Server",
        "upstream": "octagon-mcp",
        "upstream_url": "https://github.com/octagon-agents/octagon-mcp",
        "runtime": "npx",
        "port": 8653,
        "what": "Octagon",
        "description": "MCP server for [Octagon](https://www.octagon.ai/) — financial data and analysis platform. Access company financials, funding rounds, market data, and investment intelligence through AI assistants.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8653", "desc": "HTTP port (only used with `streamable-http`)"},
            "OCTAGON_API_KEY": {"default": "", "desc": "Octagon API key"},
        },
        "api_key_note": "**API key required** — sign up at [octagon.ai](https://www.octagon.ai/).",
        "prompts": ["Show me the latest funding rounds for AI startups.", "Get financial data for company X."],
    },
    "tomtom-mcp": {
        "title": "TomTom MCP Server",
        "upstream": "@tomtom-org/tomtom-mcp",
        "upstream_url": "https://github.com/tomtom-org/tomtom-mcp",
        "runtime": "npx",
        "port": 8671,
        "what": "TomTom",
        "description": "MCP server for [TomTom](https://developer.tomtom.com/) Maps and Routing APIs. Geocoding, reverse geocoding, route calculation, traffic data, and point-of-interest search.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8671", "desc": "HTTP port (only used with `streamable-http`)"},
            "TOMTOM_API_KEY": {"default": "", "desc": "TomTom API key — get one at [developer.tomtom.com](https://developer.tomtom.com/)"},
        },
        "api_key_note": "**API key required** — sign up at [developer.tomtom.com](https://developer.tomtom.com/).",
        "prompts": ["Calculate a driving route from New York to Boston.", "Find restaurants near Times Square."],
    },
    "variflight-mcp": {
        "title": "VariFlight MCP Server",
        "upstream": "@variflight-ai/variflight-mcp",
        "upstream_url": "https://github.com/AirSavvy/variflight-mcp",
        "runtime": "npx",
        "port": 8672,
        "what": "VariFlight",
        "description": "MCP server for [VariFlight](https://www.variflight.com/) — flight tracking and aviation data. Real-time flight status, historical flight data, airport information, and airline schedules.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8672", "desc": "HTTP port (only used with `streamable-http`)"},
            "VARIFLIGHT_API_KEY": {"default": "", "desc": "VariFlight API key"},
        },
        "api_key_note": "**API key required** — sign up at [variflight.com](https://www.variflight.com/).",
        "prompts": ["Track flight UA123 in real time.", "Show arrival flights at SFO today."],
    },
    "winston-ai-mcp": {
        "title": "Winston AI MCP Server",
        "upstream": "winston-ai-mcp",
        "upstream_url": "https://github.com/winston-ai/winston-ai-mcp",
        "runtime": "npx",
        "port": 8674,
        "what": "Winston AI",
        "description": "MCP server for [Winston AI](https://gowinston.ai/) — AI content detection platform. Analyze text to determine if it was written by a human or generated by AI. Useful for content moderation, academic integrity, and editorial workflows.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8674", "desc": "HTTP port (only used with `streamable-http`)"},
            "WINSTONAI_API_KEY": {"default": "", "desc": "Winston AI API key — get one at [gowinston.ai](https://gowinston.ai/)"},
        },
        "api_key_note": "**API key required** — sign up at [gowinston.ai](https://gowinston.ai/).",
        "prompts": ["Check if this text was written by AI.", "Analyze this article for AI-generated content."],
    },
}

# Add all remaining AWS servers with standard template
AWS_BASE = {
    "runtime": "pip",
    "upstream_url": "https://github.com/awslabs/mcp",
    "api_key_note": "**AWS credentials required** — set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION`.",
}
AWS_ENV = {
    "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
    "AWS_REGION": {"default": "", "desc": "AWS region (e.g. `us-east-1`)"},
    "AWS_ACCESS_KEY_ID": {"default": "", "desc": "AWS access key ID"},
    "AWS_SECRET_ACCESS_KEY": {"default": "", "desc": "AWS secret access key"},
}
AWS_SERVERS = {
    "aws-bedrock-custom-model-mcp": ("AWS Bedrock Custom Model MCP Server", "awslabs.aws-bedrock-custom-model-import-mcp-server", 8605, "Bedrock Custom Model Import", "MCP server for Amazon Bedrock Custom Model Import. Streamlines the process of importing custom models into Amazon Bedrock, including creating, listing, and managing model import jobs."),
    "aws-cloudtrail-mcp": ("AWS CloudTrail MCP Server", "awslabs.cloudtrail-mcp-server", 8606, "CloudTrail", "MCP server for AWS CloudTrail. Query AWS account activity for security investigations, compliance auditing, and operational troubleshooting."),
    "aws-cloudwatch-appsignals-mcp": ("AWS CloudWatch App Signals MCP Server", "awslabs.cloudwatch-appsignals-mcp-server", 8607, "CloudWatch Application Signals", "MCP server for AWS CloudWatch Application Signals. Monitor and analyze application performance, service health, and operational metrics."),
    "aws-cloudwatch-mcp": ("AWS CloudWatch MCP Server", "awslabs.cloudwatch-mcp-server", 8608, "CloudWatch", "MCP server for AWS CloudWatch. Query metrics, alarms, logs, and dashboards for AI-powered cloud monitoring and troubleshooting."),
    "aws-core-mcp": ("AWS Core MCP Server", "awslabs.core-mcp-server", 8609, "AWS Core", "Starting point for using AWS MCP servers through a dynamic proxy server strategy based on role-based environment variables. Includes planning and orchestration tools."),
    "aws-documentdb-mcp": ("AWS DocumentDB MCP Server", "awslabs.documentdb-mcp-server", 8611, "DocumentDB", "MCP server for AWS DocumentDB. Interact with DocumentDB databases — query collections, manage indexes, and inspect cluster health."),
    "aws-dynamodb-mcp": ("AWS DynamoDB MCP Server", "awslabs.dynamodb-mcp-server", 8612, "DynamoDB", "MCP server for Amazon DynamoDB. Expert design guidance, data modeling assistance, and table management for DynamoDB."),
    "aws-ecs-mcp": ("AWS ECS MCP Server", "awslabs.ecs-mcp-server", 8613, "ECS", "MCP server for Amazon ECS. Deploy, manage, and monitor containerized applications on Amazon Elastic Container Service."),
    "aws-eks-mcp": ("AWS EKS MCP Server", "awslabs.eks-mcp-server", 8614, "EKS", "MCP server for Amazon EKS. Resource management tools and real-time cluster state visibility for Kubernetes on AWS."),
    "aws-iam-mcp": ("AWS IAM MCP Server", "awslabs.iam-mcp-server", 8615, "IAM", "MCP server for AWS Identity and Access Management. Manage users, roles, policies, and permissions for comprehensive AWS access control."),
    "aws-mq-mcp": ("AWS MQ MCP Server", "awslabs.amazon-mq-mcp-server", 8616, "Amazon MQ", "MCP server for Amazon MQ. Manage RabbitMQ and ActiveMQ message brokers — create brokers, manage queues, and monitor broker health."),
    "aws-neptune-mcp": ("AWS Neptune MCP Server", "awslabs.amazon-neptune-mcp-server", 8617, "Neptune", "MCP server for Amazon Neptune. Query graph databases using openCypher, Gremlin, and SPARQL. Fetch status, schema, and run graph traversals."),
    "aws-network-mcp": ("AWS Network MCP Server", "awslabs.aws-network-mcp-server", 8618, "AWS Networking", "MCP server for AWS networking services. Troubleshoot and analyze Cloud WAN, Transit Gateway, VPC, Network Firewall, and VPN."),
    "aws-postgres-mcp": ("AWS Aurora PostgreSQL MCP Server", "awslabs.postgres-mcp-server", 8619, "Aurora PostgreSQL", "MCP server for Aurora PostgreSQL. Translate human-readable questions into SQL queries, inspect schemas, and manage database operations."),
    "aws-prometheus-mcp": ("AWS Prometheus MCP Server", "awslabs.prometheus-mcp-server", 8620, "Prometheus", "MCP server for AWS Managed Prometheus. Execute PromQL queries, inspect metrics, and analyze time-series monitoring data."),
    "aws-redshift-mcp": ("AWS Redshift MCP Server", "awslabs.redshift-mcp-server", 8621, "Redshift", "MCP server for Amazon Redshift. Discover, explore, and query data warehouse tables and views."),
    "aws-s3-tables-mcp": ("AWS S3 Tables MCP Server", "awslabs.s3-tables-mcp-server", 8622, "S3 Tables", "MCP server for S3 Tables. Generate and query tables stored in S3, manage table metadata, and run analytics."),
    "aws-serverless-mcp": ("AWS Serverless MCP Server", "awslabs.aws-serverless-mcp-server", 8623, "Serverless", "MCP server for AWS Serverless. AI-powered serverless development with tools for SAM application lifecycle, deployment, and monitoring."),
    "aws-sns-sqs-mcp": ("AWS SNS/SQS MCP Server", "awslabs.amazon-sns-sqs-mcp-server", 8624, "SNS/SQS", "MCP server for Amazon SNS and SQS. Manage topics, queues, subscriptions, and messages for event-driven architectures."),
    "aws-stepfunctions-mcp": ("AWS Step Functions MCP Server", "Custom FastMCP (boto3)", 8625, "Step Functions", "MCP server for AWS Step Functions. List, describe, and manage state machines and workflow executions."),
    "aws-well-architected-security-mcp": ("AWS Well-Architected Security MCP Server", "awslabs.well-architected-security-mcp-server", 8626, "Well-Architected Security", "MCP server for the AWS Well-Architected Security pillar. Monitor and assess AWS environments against security best practices and compliance frameworks."),
}

for name, (title, upstream, port, what, desc) in AWS_SERVERS.items():
    if name not in SERVERS:
        env = dict(AWS_ENV)
        env["MCP_PORT"] = {"default": str(port), "desc": "HTTP port (only used with `streamable-http`)"}
        SERVERS[name] = {
            "title": title,
            "upstream": upstream,
            "upstream_url": AWS_BASE["upstream_url"],
            "runtime": "pip",
            "port": port,
            "what": what,
            "description": desc,
            "env_vars": env,
            "api_key_note": AWS_BASE["api_key_note"],
            "prompts": [f"Show me {what} resources in my AWS account.", f"Describe the current state of my {what} setup."],
        }

# Also add azure-mcp
if "azure-mcp" not in SERVERS:
    SERVERS["azure-mcp"] = {
        "title": "Azure MCP Server",
        "upstream": "@azure/mcp",
        "upstream_url": "https://github.com/Azure/azure-mcp",
        "runtime": "npx",
        "port": 8627,
        "what": "Azure",
        "description": "MCP server for [Microsoft Azure](https://azure.microsoft.com/). Authenticate with Azure and interact with Azure resources through the Azure APIs. Manage subscriptions, resource groups, VMs, storage, and more.",
        "env_vars": {
            "MCP_TRANSPORT": {"default": "stdio", "desc": "Transport mode: `stdio` or `streamable-http`"},
            "MCP_PORT": {"default": "8627", "desc": "HTTP port (only used with `streamable-http`)"},
            "AZURE_CLIENT_ID": {"default": "", "desc": "Azure AD application (client) ID"},
            "AZURE_CLIENT_SECRET": {"default": "", "desc": "Azure AD client secret"},
            "AZURE_TENANT_ID": {"default": "", "desc": "Azure AD tenant ID"},
            "AZURE_SUBSCRIPTION_ID": {"default": "", "desc": "Azure subscription ID"},
        },
        "api_key_note": "**Azure credentials required** — register an app in Azure AD and set client ID, secret, tenant, and subscription.",
        "prompts": ["List all resource groups in my Azure subscription.", "Show me the VMs running in my account."],
    }


HEADER = """<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>"""

HACKERDOGS_SECTION = """## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM)."""


def _docker_lines(base_parts, env_keys, image, trailing_newline=True):
    """Build a multi-line docker run command from parts + env keys."""
    lines = list(base_parts)
    for k in env_keys:
        lines.append(f"  -e {k}")
    lines.append(f"  {image}")
    return " \\\n".join(lines)


def make_readme(name, s):
    port = s["port"]
    env_vars = s["env_vars"]
    user_env_keys = [k for k in env_vars if k not in ("MCP_TRANSPORT", "MCP_PORT")]
    image = f"hackerdogs/{name}:latest"

    # Build args for stdio JSON
    args = ["run", "-i", "--rm", "-e", "MCP_TRANSPORT"]
    for k in user_env_keys:
        args.extend(["-e", k])
    args.append(image)

    stdio_json = json.dumps({"mcpServers": {name: {"command": "docker", "args": args, "env": {**{"MCP_TRANSPORT": "stdio"}, **{k: "" for k in user_env_keys}}}}}, indent=2)
    http_json = json.dumps({"mcpServers": {name: {"url": f"http://localhost:{port}/mcp"}}}, indent=2)

    env_table_rows = ""
    for k, v in env_vars.items():
        default = f"`{v['default']}`" if v['default'] else "—"
        env_table_rows += f"| `{k}` | {default} | {v['desc']} |\n"

    stdio_cmd = _docker_lines(["docker run -i --rm"], user_env_keys, image)
    http_cmd = _docker_lines([
        f"docker run -d -p {port}:{port}",
        "  -e MCP_TRANSPORT=streamable-http",
        f"  -e MCP_PORT={port}",
    ], user_env_keys, image)
    test_cmd = _docker_lines([
        f"docker run -d --rm --name {name}-test -p {port}:{port}",
        "  -e MCP_TRANSPORT=streamable-http",
    ], user_env_keys, image)

    prompts_md = "\n".join([f'- "{p}"' for p in s.get("prompts", [])])

    readme = f"""{HEADER}

# {s['title']}

MCP server wrapper for [{s['what']}]({s['upstream_url']}) — upstream package `{s['upstream']}`.

## What is {s['what']}?

{s['description']}

{s['api_key_note']}

**Summary.** {s['title']} — Dockerized from upstream `{s['upstream']}` package.

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

{prompts_md}

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
{stdio_cmd}
```

### Docker Run (HTTP streamable mode)

```bash
{http_cmd}
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{stdio_json}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{http_json}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
{env_table_rows}
{HACKERDOGS_SECTION}

## Build

```bash
docker build -t {image} .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
{test_cmd}
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -d '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"test","version":"0.1"}}}}}}' \\
  2>&1 | grep -i mcp-session-id | awk '{{print $2}}' | tr -d '\\r\\n')

curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{{}}}}'
```

**4. Clean up:**

```bash
docker stop {name}-test
```
"""
    return readme.strip() + "\n"


count = 0
for name, s in sorted(SERVERS.items()):
    path = os.path.join(ROOT, name, "README.md")
    if not os.path.isdir(os.path.join(ROOT, name)):
        print(f"SKIP {name} (no dir)")
        continue
    with open(path, "w") as f:
        f.write(make_readme(name, s))
    count += 1
    print(f"  {name}")

print(f"\nGenerated {count} production-grade README.md files")
