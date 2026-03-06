# Tool-specific "Running the tool directly (bypassing MCP)" content.
# Each key is the *-mcp directory name. Value: (intro_sentence, [(example_title, cmd_suffix), ...])
# cmd_suffix is the part after: docker run -i --rm --entrypoint <binary> hackerdogs/<dir>:latest
# Use --help or -h for "Show help" as the last example.

DIRECT_RUN_CONTENT = {
    "a2a-scanner-mcp": (
        "You can run the a2a-scanner CLI in the same container by overriding the entrypoint to scan Agent-to-Agent communication security without starting the MCP server.",
        [("Scan an MCP or A2A endpoint URL", "-h"), ("Show help", "--help")],
    ),
    "ai-infra-guard-mcp": (
        "You can run the ai-infra-guard CLI in the same container by overriding the entrypoint to scan and assess AI infrastructure security without starting the MCP server.",
        [("Run AI infrastructure assessment", "-h"), ("Show help", "--help")],
    ),
    "aibom-mcp": (
        "You can run the aibom CLI in the same container by overriding the entrypoint to generate AI/ML bill-of-materials without starting the MCP server.",
        [("Generate AI BOM for a path (mount repo)", "-h"), ("Show help", "--help")],
    ),
    "aircrack-ng-mcp": (
        "You can run the aircrack-ng suite in the same container by overriding the entrypoint to audit Wi-Fi or crack WEP/WPA without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "anew-mcp": (
        "You can run the anew CLI in the same container by overriding the entrypoint to append new lines from stdin without starting the MCP server.",
        [("Filter new lines from stdin", ""), ("Show help", "--help")],
    ),
    "angr-mcp": (
        "You can run angr (Python) in the same container by overriding the entrypoint for binary analysis without starting the MCP server.",
        [("Python REPL", "-c \"import angr; print(angr.__version__)\""), ("Show help", "--help")],
    ),
    "aquatone-mcp": (
        "You can run the aquatone CLI in the same container by overriding the entrypoint to visualize and discover subdomains without starting the MCP server.",
        [("Scan subdomains (pipe domains on stdin)", "-scan"), ("Show help", "-h")],
    ),
    "arp-scan-mcp": (
        "You can run arp-scan in the same container by overriding the entrypoint to discover hosts on the local network without starting the MCP server.",
        [("Scan local network (needs --network=host)", "--localnet"), ("Show help", "--help")],
    ),
    "asnmap-mcp": (
        "You can run the asnmap CLI in the same container by overriding the entrypoint to map ASNs and IP ranges without starting the MCP server.",
        [("Query ASN", "-asn 15169"), ("Show help", "-h")],
    ),
    "augustus-mcp": (
        "You can run the augustus CLI in the same container by overriding the entrypoint for vulnerability and risk assessment without starting the MCP server.",
        [("Run vulnerability scan", "-h"), ("Show help", "--help")],
    ),
    "autorecon-mcp": (
        "You can run the autorecon CLI in the same container by overriding the entrypoint to perform automated recon without starting the MCP server.",
        [("Scan a target", "example.com"), ("Show help", "--help")],
    ),
    "aws-s3-mcp": (
        "You can run the aws-s3-mcp CLI in the same container by overriding the entrypoint (if the image includes it) without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "bearer-mcp": (
        "You can run the bearer CLI in the same container by overriding the entrypoint to scan code for secrets and misconfigurations without starting the MCP server.",
        [("Scan current directory", "scan ."), ("Show help", "--help")],
    ),
    "bettercap-mcp": (
        "You can run bettercap in the same container by overriding the entrypoint for network attacks and monitoring without starting the MCP server.",
        [("Interactive caplet", "-eval \"help\""), ("Show help", "-h")],
    ),
    "binwalk-mcp": (
        "You can run the binwalk CLI in the same container by overriding the entrypoint to analyze and extract firmware/binaries without starting the MCP server.",
        [("Scan a file (mount it)", "-B /path/to/file"), ("Show help", "--help")],
    ),
    "bloodhound-mcp": (
        "You can run bloodhound-python in the same container by overriding the entrypoint to collect Active Directory data without starting the MCP server.",
        [("Ingest from domain", "-d example.com -u user -p pass -c All"), ("Show help", "-h")],
    ),
    "bloodhound-mcp-ai-mcp": (
        "You can run the bloodhound-mcp CLI in the same container by overriding the entrypoint to run BloodHound AI–powered analysis without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "boofuzz-mcp": (
        "You can run the boofuzz CLI in the same container by overriding the entrypoint to fuzz network protocols or APIs without starting the MCP server.",
        [("Run fuzzer against target", "-h"), ("Show help", "--help")],
    ),
    "brutespray-mcp": (
        "You can run the brutespray CLI in the same container by overriding the entrypoint to brute-force from Nmap XML without starting the MCP server.",
        [("Run with Nmap XML (mount file)", "-f /path/to/nmap.xml"), ("Show help", "-h")],
    ),
    "brutus-mcp": (
        "You can run the brutus CLI in the same container by overriding the entrypoint for network brute-forcing without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "bully-mcp": (
        "You can run the bully CLI in the same container by overriding the entrypoint to attack WPS without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "capa-mcp": (
        "You can run the capa CLI in the same container by overriding the entrypoint to identify capabilities in executables without starting the MCP server.",
        [("Analyze a binary (mount it)", "/path/to/binary"), ("Show help", "-h")],
    ),
    "certipy-mcp": (
        "You can run the certipy CLI in the same container by overriding the entrypoint to abuse Active Directory certificates without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "checkov-mcp": (
        "You can run the checkov CLI in the same container by overriding the entrypoint to scan IaC for misconfigurations without starting the MCP server.",
        [("Scan a directory (mount it)", "scan -d /path/to/iac"), ("Show help", "--help")],
    ),
    "checksec-mcp": (
        "You can run the checksec CLI in the same container by overriding the entrypoint to check binary security hardening without starting the MCP server.",
        [("Check a binary (mount it)", "--file=/path/to/binary"), ("Show help", "--help")],
    ),
    "cisco-mcp-scanner-mcp": (
        "You can run the mcp-scanner CLI in the same container by overriding the entrypoint to scan MCP servers or Cisco environments without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "clair-mcp": (
        "You can run the clair CLI in the same container by overriding the entrypoint to analyze container images for vulnerabilities without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "cloudlist-mcp": (
        "You can run the cloudlist CLI in the same container by overriding the entrypoint to enumerate cloud provider assets without starting the MCP server.",
        [("Enumerate cloud assets (set cloud creds)", "-h"), ("Show help", "--help")],
    ),
    "cloudmapper-mcp": (
        "You can run the cloudmapper CLI in the same container by overriding the entrypoint to audit AWS environments without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "commix-mcp": (
        "You can run the commix CLI in the same container by overriding the entrypoint to test for command injection without starting the MCP server.",
        [("Test a URL", "-u \"https://example.com/page?cmd=test\""), ("Show help", "--help")],
    ),
    "corscanner-mcp": (
        "You can run the cors_scan CLI in the same container by overriding the entrypoint to find CORS misconfigurations without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "crackmapexec-mcp": (
        "You can run the crackmapexec CLI in the same container by overriding the entrypoint to attack Windows/AD networks without starting the MCP server.",
        [("List SMB shares", "-u user -p pass 192.168.1.0/24"), ("Show help", "-h")],
    ),
    "crlfuzz-mcp": (
        "You can run the crlfuzz CLI in the same container by overriding the entrypoint to find CRLF injection without starting the MCP server.",
        [("Fuzz a URL", "-u https://example.com"), ("Show help", "-h")],
    ),
    "crowbar-mcp": (
        "You can run the crowbar CLI in the same container by overriding the entrypoint for brute-forcing (e.g. VPN, RDP) without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "crunch-mcp": (
        "You can run the crunch CLI in the same container by overriding the entrypoint to generate wordlists without starting the MCP server.",
        [("Generate wordlist", "8 8 0123456789 -o /tmp/out.txt"), ("Show help", "-h")],
    ),
    "cutter-mcp": (
        "You can run the cutter CLI in the same container by overriding the entrypoint for reverse engineering (GUI tool; may need display) without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "cvemap-mcp": (
        "You can run the cvemap CLI in the same container by overriding the entrypoint to query CVE data without starting the MCP server.",
        [("Search CVE", "-cve CVE-2024-1234"), ("Show help", "-h")],
    ),
    "dalfox-mcp": (
        "You can run the dalfox CLI in the same container by overriding the entrypoint to find XSS without starting the MCP server.",
        [("Scan URL", "url https://example.com"), ("Show help", "--help")],
    ),
    "dependency-check-mcp": (
        "You can run the dependency-check CLI in the same container by overriding the entrypoint to scan dependencies for CVEs without starting the MCP server.",
        [("Scan project (mount it)", "--project myapp -s /path/to/project"), ("Show help", "--help")],
    ),
    "dharma-mcp": (
        "You can run the dharma CLI in the same container by overriding the entrypoint to generate fuzzing grammars without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "dirb-mcp": (
        "You can run the dirb CLI in the same container by overriding the entrypoint to brute-force directories without starting the MCP server.",
        [("Scan a URL", "https://example.com"), ("Show help", "-h")],
    ),
    "dirsearch-mcp": (
        "You can run the dirsearch CLI in the same container by overriding the entrypoint to discover directories and files without starting the MCP server.",
        [("Scan a URL", "-u https://example.com"), ("Show help", "--help")],
    ),
    "dnsenum-mcp": (
        "You can run the dnsenum CLI in the same container by overriding the entrypoint to enumerate DNS information without starting the MCP server.",
        [("Enumerate domain", "example.com"), ("Show help", "--help")],
    ),
    "dnsreaper-mcp": (
        "You can run the dnsreaper CLI in the same container by overriding the entrypoint to find subdomain takeovers and DNS issues without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "dnsrecon-mcp": (
        "You can run the dnsrecon CLI in the same container by overriding the entrypoint to perform DNS recon without starting the MCP server.",
        [("Recon a domain", "-d example.com"), ("Show help", "-h")],
    ),
    "dnsx-mcp": (
        "You can run the dnsx CLI in the same container by overriding the entrypoint to query DNS (A, AAAA, CNAME, etc.) without starting the MCP server.",
        [("Resolve domains from stdin", "-silent"), ("Show help", "-h")],
    ),
    "docker-bench-security-mcp": (
        "You can run the docker-bench-security script in the same container by overriding the entrypoint to audit Docker configuration without starting the MCP server.",
        [("Run audit", ""), ("Show help", "--help")],
    ),
    "dotdotpwn-mcp": (
        "You can run the dotdotpwn CLI in the same container by overriding the entrypoint to find path traversal without starting the MCP server.",
        [("Test a URL", "-u https://example.com/test -f /etc/passwd"), ("Show help", "-h")],
    ),
    "enum4linux-mcp": (
        "You can run the enum4linux CLI in the same container by overriding the entrypoint to enumerate SMB/Windows without starting the MCP server.",
        [("Enumerate host", "192.168.1.1"), ("Show help", "-h")],
    ),
    "enum4linux-ng-mcp": (
        "You can run the enum4linux-ng CLI in the same container by overriding the entrypoint to enumerate SMB/LDAP without starting the MCP server.",
        [("Enumerate host", "192.168.1.1"), ("Show help", "-h")],
    ),
    "ettercap-mcp": (
        "You can run the ettercap CLI in the same container by overriding the entrypoint for ARP spoofing and MITM without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "evil-winrm-mcp": (
        "You can run the evil-winrm CLI in the same container by overriding the entrypoint to get a WinRM shell without starting the MCP server.",
        [("Connect to host", "-i 192.168.1.1 -u Administrator -p Pass"), ("Show help", "-h")],
    ),
    "exploitdb-mcp": (
        "You can run the searchsploit CLI in the same container by overriding the entrypoint to search Exploit-DB without starting the MCP server.",
        [("Search for a term", "apache 2.4"), ("Show help", "-h")],
    ),
    "falco-mcp": (
        "You can run the falco CLI in the same container by overriding the entrypoint to detect runtime security issues without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "fierce-mcp": (
        "You can run the fierce CLI in the same container by overriding the entrypoint to discover DNS subdomains without starting the MCP server.",
        [("Discover domain", "example.com"), ("Show help", "--help")],
    ),
    "foremost-mcp": (
        "You can run the foremost CLI in the same container by overriding the entrypoint to recover files from disk images without starting the MCP server.",
        [("Recover from image (mount it)", "-i /path/to/image -o /out"), ("Show help", "-h")],
    ),
    "fping-mcp": (
        "You can run the fping CLI in the same container by overriding the entrypoint to ping multiple hosts without starting the MCP server.",
        [("Ping hosts", "-g 192.168.1.0/24"), ("Show help", "-h")],
    ),
    "garak-mcp": (
        "You can run the garak-mcp CLI in the same container by overriding the entrypoint to probe LLMs for vulnerabilities without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "gau-mcp": (
        "You can run the gau CLI in the same container by overriding the entrypoint to fetch URLs from AlienVault/Wayback without starting the MCP server.",
        [("Get URLs for domain", "example.com"), ("Show help", "--help")],
    ),
    "gef-mcp": (
        "You can run gdb with GEF in the same container by overriding the entrypoint for exploit development without starting the MCP server.",
        [("Debug a binary (mount it)", "/path/to/binary"), ("Show help", "--help")],
    ),
    "ggshield-mcp": (
        "You can run the ggshield CLI in the same container by overriding the entrypoint to scan for secrets (e.g. GitGuardian) without starting the MCP server.",
        [("Scan repo (mount it)", "secret scan path /path/to/repo"), ("Show help", "--help")],
    ),
    "ghidra-mcp": (
        "You can run the analyzeHeadless CLI in the same container by overriding the entrypoint to run Ghidra headless analysis without starting the MCP server.",
        [("Run headless analysis (project path and binary path)", "/path/to/project /path/to/binary"), ("Show help", "--help")],
    ),
    "gitleaks-mcp": (
        "You can run the gitleaks CLI in the same container by overriding the entrypoint to detect secrets in Git repos without starting the MCP server.",
        [("Scan repo (mount it)", "detect -s /path/to/repo"), ("Show help", "--help")],
    ),
    "gospider-mcp": (
        "You can run the gospider CLI in the same container by overriding the entrypoint to crawl and discover URLs without starting the MCP server.",
        [("Crawl a domain", "-s https://example.com"), ("Show help", "-h")],
    ),
    "graphql-voyager-mcp": (
        "You can run the graphql-voyager CLI in the same container by overriding the entrypoint to introspect and explore GraphQL schemas without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "grype-mcp": (
        "You can run the grype CLI in the same container by overriding the entrypoint to scan images/filesystems for vulnerabilities without starting the MCP server.",
        [("Scan an image", "image alpine:latest"), ("Show help", "--help")],
    ),
    "hakrawler-mcp": (
        "You can run the hakrawler CLI in the same container by overriding the entrypoint to crawl URLs without starting the MCP server.",
        [("Crawl URL", "-url https://example.com"), ("Show help", "-h")],
    ),
    "hashcat-mcp": (
        "You can run the hashcat CLI in the same container by overriding the entrypoint to crack hashes (mount wordlists/hashes) without starting the MCP server.",
        [("Show hash types", "--help"), ("Example crack", "-m 0 -a 0 hashes.txt wordlist.txt")],
    ),
    "hashid-mcp": (
        "You can run the hashid CLI in the same container by overriding the entrypoint to identify hash types without starting the MCP server.",
        [("Identify hash", "-j '$2a$10$...'"), ("Show help", "-h")],
    ),
    "hashpump-mcp": (
        "You can run the HashPump CLI in the same container by overriding the entrypoint for hash length-extension attacks without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "horusec-mcp": (
        "You can run the horusec CLI in the same container by overriding the entrypoint to scan code for security issues without starting the MCP server.",
        [("Scan directory (mount it)", "start -p /path/to/project"), ("Show help", "--help")],
    ),
    "ipinfo-mcp": (
        "You can run the ipinfo CLI in the same container by overriding the entrypoint to look up IP info (API key may be required) without starting the MCP server.",
        [("Look up IP", "8.8.8.8"), ("Show help", "--help")],
    ),
    "ivre-mcp": (
        "You can run the ivre CLI in the same container by overriding the entrypoint for network recon and passive collection without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "jaeles-mcp": (
        "You can run the jaeles CLI in the same container by overriding the entrypoint to run signature-based web application scans without starting the MCP server.",
        [("Scan a target URL", "-u https://example.com"), ("Show help", "-h")],
    ),
    "john-mcp": (
        "You can run the john CLI in the same container by overriding the entrypoint to crack passwords (mount hashes/wordlists) without starting the MCP server.",
        [("Crack password file (mount it)", "/path/to/passwd"), ("Show help", "--help")],
    ),
    "joomscan-mcp": (
        "You can run the joomscan CLI in the same container by overriding the entrypoint to scan Joomla! sites without starting the MCP server.",
        [("Scan URL", "-u https://example.com"), ("Show help", "-h")],
    ),
    "julius-mcp": (
        "You can run the julius CLI in the same container by overriding the entrypoint to run Julius security checks without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "jwt-tool-mcp": (
        "You can run the jwt_tool.py script in the same container by overriding the entrypoint to audit JWTs without starting the MCP server.",
        [("Decode a JWT", "eyJhbGc..."), ("Show help", "-h")],
    ),
    "knostic-mcp-scanner-mcp": (
        "You can run the mcp-scanner CLI in the same container by overriding the entrypoint to scan Kubernetes or MCP environments (Knostic) without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "kube-bench-mcp": (
        "You can run the kube-bench CLI in the same container by overriding the entrypoint to audit Kubernetes clusters without starting the MCP server.",
        [("Run audit", ""), ("Show help", "--help")],
    ),
    "kube-hunter-mcp": (
        "You can run the kube-hunter CLI in the same container by overriding the entrypoint to find weaknesses in Kubernetes without starting the MCP server.",
        [("Hunt (remote)", "--remote 192.168.1.1"), ("Show help", "--help")],
    ),
    "kubescape-mcp": (
        "You can run the kubescape CLI in the same container by overriding the entrypoint to scan Kubernetes manifests and clusters for misconfigurations without starting the MCP server.",
        [("Scan current directory or cluster", "scan"), ("Show help", "--help")],
    ),
    "libc-database-mcp": (
        "You can run the find (libc-database) CLI in the same container by overriding the entrypoint to search libc database without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "lynis-mcp": (
        "You can run the lynis CLI in the same container by overriding the entrypoint to audit system security without starting the MCP server.",
        [("Run audit", "audit system"), ("Show help", "--help")],
    ),
    "mcpscan-mcp": (
        "You can run the mcpscan CLI in the same container by overriding the entrypoint to scan or audit MCP servers without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "mcpserver-audit-mcp": (
        "You can run the mcpserver-audit CLI in the same container by overriding the entrypoint to audit MCP server configurations without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "medusa-mcp": (
        "You can run the medusa CLI in the same container by overriding the entrypoint to brute-force services without starting the MCP server.",
        [("HTTP brute-force", "-h 192.168.1.1 -M http -m DIR:/admin -u admin -P /path/to/pass.txt"), ("Show help", "-h")],
    ),
    "metasploit-mcp": (
        "You can run the msfconsole CLI in the same container by overriding the entrypoint to use Metasploit without starting the MCP server.",
        [("Start console", "-q"), ("Show help", "-h")],
    ),
    "nbtscan-mcp": (
        "You can run the nbtscan CLI in the same container by overriding the entrypoint to scan NetBIOS without starting the MCP server.",
        [("Scan range", "192.168.1.0/24"), ("Show help", "-h")],
    ),
    "ncrack-mcp": (
        "You can run the ncrack CLI in the same container by overriding the entrypoint to crack network services without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "nerva-mcp": (
        "You can run the nerva CLI in the same container by overriding the entrypoint for vulnerability scanning and assessment without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "netcat-mcp": (
        "You can run the nc (netcat) CLI in the same container by overriding the entrypoint for network debugging without starting the MCP server.",
        [("Connect to host", "-v example.com 80"), ("Show help", "-h")],
    ),
    "netdiscover-mcp": (
        "You can run the netdiscover CLI in the same container by overriding the entrypoint to discover hosts (ARP) without starting the MCP server.",
        [("Active scan", "-r 192.168.1.0/24"), ("Show help", "-h")],
    ),
    "netexec-mcp": (
        "You can run the netexec CLI in the same container by overriding the entrypoint to attack Windows/AD (successor to crackmapexec) without starting the MCP server.",
        [("List shares", "-u user -p pass 192.168.1.0/24"), ("Show help", "-h")],
    ),
    "ngrep-mcp": (
        "You can run the ngrep CLI in the same container by overriding the entrypoint to match packets by pattern without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "nosqlmap-mcp": (
        "You can run the nosqlmap CLI in the same container by overriding the entrypoint to exploit NoSQL injection without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "nova-framework-mcp": (
        "You can run the nova-framework CLI in the same container by overriding the entrypoint for Nova security framework checks without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "nova-proximity-mcp": (
        "You can run the nova-proximity CLI in the same container by overriding the entrypoint for Nova proximity scanning without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "one-gadget-mcp": (
        "You can run the one_gadget CLI in the same container by overriding the entrypoint to find one-gadget RCE in libc without starting the MCP server.",
        [("Find gadgets (mount libc)", "/path/to/libc.so"), ("Show help", "-h")],
    ),
    "openrisk-mcp": (
        "You can run the openrisk CLI in the same container by overriding the entrypoint to assess open-source risk without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "openvas-mcp": (
        "You can run the gvm-cli (OpenVAS) in the same container by overriding the entrypoint to manage vulnerability scans and OpenVAS data without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "osv-mcp": (
        "You can run the osv-mcp CLI in the same container by overriding the entrypoint to query OSV vulnerability data without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "pacu-mcp": (
        "You can run the pacu CLI in the same container by overriding the entrypoint to exploit AWS without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "paramspider-mcp": (
        "You can run the paramspider CLI in the same container by overriding the entrypoint to find parameters from Wayback without starting the MCP server.",
        [("Find params for domain", "-d example.com"), ("Show help", "--help")],
    ),
    "patator-mcp": (
        "You can run the patator CLI in the same container by overriding the entrypoint for generic brute-force without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "peda-mcp": (
        "You can run gdb with PEDA in the same container by overriding the entrypoint for exploit development without starting the MCP server.",
        [("Debug binary (mount it)", "/path/to/binary"), ("Show help", "--help")],
    ),
    "pixiewps-mcp": (
        "You can run the pixiewps CLI in the same container by overriding the entrypoint to recover WPS PIN without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "port-scanner-mcp": (
        "You can run the port-scanner CLI in the same container by overriding the entrypoint to scan target hosts for open ports without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "psudohash-mcp": (
        "You can run the psudohash CLI in the same container by overriding the entrypoint to generate password variants without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "pwninit-mcp": (
        "You can run the pwninit CLI in the same container by overriding the entrypoint to set up pwn challenges without starting the MCP server.",
        [("Process binary (mount it)", "/path/to/binary"), ("Show help", "--help")],
    ),
    "pwntools-mcp": (
        "You can run Python with pwntools in the same container by overriding the entrypoint for exploit development without starting the MCP server.",
        [("Python REPL", "-c \"from pwn import *; print(context)\""), ("Show help", "--help")],
    ),
    "qsreplace-mcp": (
        "You can run the qsreplace CLI in the same container by overriding the entrypoint to replace query string values from stdin without starting the MCP server.",
        [("Replace with value", "-a"), ("Show help", "-h")],
    ),
    "radare2-mcp": (
        "You can run the r2 CLI in the same container by overriding the entrypoint for reverse engineering without starting the MCP server.",
        [("Analyze binary (mount it)", "-q -c 'aaa' /path/to/binary"), ("Show help", "-h")],
    ),
    "ramparts-mcp": (
        "You can run the ramparts CLI in the same container by overriding the entrypoint for security or compliance checks without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "rasn-mcp": (
        "You can run the rasn CLI in the same container by overriding the entrypoint for ASN or routing analysis without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "recon-ng-mcp": (
        "You can run the recon-ng CLI in the same container by overriding the entrypoint for recon without starting the MCP server.",
        [("Start console", ""), ("Show help", "--help")],
    ),
    "responder-mcp": (
        "You can run the Responder CLI in the same container by overriding the entrypoint to capture hashes (LLMNR/NBT-NS) without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "retire-js-mcp": (
        "You can run the retire CLI in the same container by overriding the entrypoint to find vulnerable JavaScript libraries without starting the MCP server.",
        [("Scan path (mount it)", "/path/to/project"), ("Show help", "--help")],
    ),
    "roadtools-mcp": (
        "You can run the roadrecon CLI in the same container by overriding the entrypoint to explore Azure AD without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "ropgadget-mcp": (
        "You can run the ROPgadget CLI in the same container by overriding the entrypoint to find ROP gadgets without starting the MCP server.",
        [("Analyze binary (mount it)", "/path/to/binary"), ("Show help", "--help")],
    ),
    "ropper-mcp": (
        "You can run the ropper CLI in the same container by overriding the entrypoint to find ROP gadgets without starting the MCP server.",
        [("Show gadgets (mount binary)", "--file /path/to/binary"), ("Show help", "--help")],
    ),
    "rustscan-mcp": (
        "You can run the rustscan CLI in the same container by overriding the entrypoint for fast port scanning without starting the MCP server.",
        [("Scan host and run Nmap", "-a 192.168.1.1 -- -sV"), ("Show help", "--help")],
    ),
    "scoutsuite-mcp": (
        "You can run the scout CLI in the same container by overriding the entrypoint to audit AWS, Azure, or GCP environments (set cloud credentials) without starting the MCP server.",
        [("Run cloud audit (pass provider and creds)", "--help"), ("Show help", "--help")],
    ),
    "securemcp-mcp": (
        "You can run the securemcp CLI in the same container by overriding the entrypoint to audit or harden MCP server security without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "semgrep-mcp": (
        "You can run the semgrep CLI in the same container by overriding the entrypoint to find bugs and secrets in code without starting the MCP server.",
        [("Scan path (mount it)", "scan --config auto /path/to/repo"), ("Show help", "--help")],
    ),
    "sherlock-mcp": (
        "You can run the sherlock CLI in the same container by overriding the entrypoint to find usernames across social networks without starting the MCP server.",
        [("Search username", "username"), ("Show help", "--help")],
    ),
    "slowhttptest-mcp": (
        "You can run the slowhttptest CLI in the same container by overriding the entrypoint to run slow HTTP DoS tests without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "smbmap-mcp": (
        "You can run the smbmap CLI in the same container by overriding the entrypoint to enumerate SMB shares without starting the MCP server.",
        [("List shares", "-H 192.168.1.1 -u user -p pass"), ("Show help", "-h")],
    ),
    "smtp-user-enum-mcp": (
        "You can run the smtp-user-enum CLI in the same container by overriding the entrypoint to enumerate valid SMTP users on a server without starting the MCP server.",
        [("Enumerate users on SMTP server", "-h"), ("Show help", "--help")],
    ),
    "smuggler-mcp": (
        "You can run the smuggler CLI in the same container by overriding the entrypoint to detect HTTP request smuggling without starting the MCP server.",
        [("Scan URL", "-u https://example.com"), ("Show help", "-h")],
    ),
    "social-analyzer-mcp": (
        "You can run the social-analyzer CLI in the same container by overriding the entrypoint to analyze social media without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "spiderfoot-mcp": (
        "You can run the sf.py (SpiderFoot) CLI in the same container by overriding the entrypoint to run OSINT scans and automate footprinting without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "sslscan-mcp": (
        "You can run the sslscan CLI in the same container by overriding the entrypoint to check SSL/TLS configuration without starting the MCP server.",
        [("Scan host", "example.com"), ("Show help", "--help")],
    ),
    "sslyze-mcp": (
        "You can run the sslyze CLI in the same container by overriding the entrypoint to analyze SSL/TLS without starting the MCP server.",
        [("Scan host", "--certinfo example.com"), ("Show help", "--help")],
    ),
    "sstimap-mcp": (
        "You can run the sstimap CLI in the same container by overriding the entrypoint to find server-side template injection without starting the MCP server.",
        [("Scan URL", "-u https://example.com"), ("Show help", "--help")],
    ),
    "steghide-mcp": (
        "You can run the steghide CLI in the same container by overriding the entrypoint to extract data from steganography without starting the MCP server.",
        [("Extract (mount file)", "extract -sf /path/to/file"), ("Show help", "--help")],
    ),
    "subjack-mcp": (
        "You can run the subjack CLI in the same container by overriding the entrypoint to find subdomain takeovers without starting the MCP server.",
        [("Check subdomains (from stdin)", "-w /path/to/wordlist -t target"), ("Show help", "-h")],
    ),
    "sublist3r-mcp": (
        "You can run the sublist3r CLI in the same container by overriding the entrypoint to enumerate subdomains without starting the MCP server.",
        [("Enumerate domain", "-d example.com"), ("Show help", "-h")],
    ),
    "suricata-mcp": (
        "You can run the suricata-mcp CLI in the same container by overriding the entrypoint to run Suricata IDS/IPS or flow analysis without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "syft-mcp": (
        "You can run the syft CLI in the same container by overriding the entrypoint to generate SBOMs from images/filesystems without starting the MCP server.",
        [("Generate SBOM for image", "alpine:latest"), ("Show help", "--help")],
    ),
    "terrascan-mcp": (
        "You can run the terrascan CLI in the same container by overriding the entrypoint to scan IaC for misconfigurations without starting the MCP server.",
        [("Scan path (mount it)", "scan -d /path/to/iac"), ("Show help", "--help")],
    ),
    "testdisk-mcp": (
        "You can run the testdisk CLI in the same container by overriding the entrypoint to recover partitions/files without starting the MCP server.",
        [("Analyze device (mount it)", "/path/to/disk"), ("Show help", "--help")],
    ),
    "testssl-mcp": (
        "You can run the testssl.sh script in the same container by overriding the entrypoint to check SSL/TLS without starting the MCP server.",
        [("Check host", "https://example.com"), ("Show help", "--help")],
    ),
    "theharvester-mcp": (
        "You can run the theHarvester CLI in the same container by overriding the entrypoint to gather emails/subdomains without starting the MCP server.",
        [("Collect for domain", "-d example.com -b all"), ("Show help", "-h")],
    ),
    "threat-hunting-mcp": (
        "You can run the threat-hunting CLI in the same container by overriding the entrypoint to run threat-hunting queries and detections without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "titus-mcp": (
        "You can run the titus CLI in the same container by overriding the entrypoint for Titus container security without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "tldfinder-mcp": (
        "You can run the tldfinder CLI in the same container by overriding the entrypoint to find TLDs for domains without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "tlsx-mcp": (
        "You can run the tlsx CLI in the same container by overriding the entrypoint to grab TLS data from hosts without starting the MCP server.",
        [("Grab from host", "-u example.com"), ("Show help", "-h")],
    ),
    "tplmap-mcp": (
        "You can run the tplmap CLI in the same container by overriding the entrypoint to find server-side template injection without starting the MCP server.",
        [("Test URL", "-u 'https://example.com/page?name=test'"), ("Show help", "--help")],
    ),
    "trivy-neutr0n-mcp": (
        "You can run the trivy-mcp CLI in the same container by overriding the entrypoint for Trivy Neutr0n scanning without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "trufflehog-mcp": (
        "You can run the trufflehog CLI in the same container by overriding the entrypoint to find secrets in code/git without starting the MCP server.",
        [("Scan repo (mount it)", "filesystem /path/to/repo"), ("Show help", "--help")],
    ),
    "uncover-mcp": (
        "You can run the uncover CLI in the same container by overriding the entrypoint to discover hosts via search engines without starting the MCP server.",
        [("Query", "-q example.com"), ("Show help", "-h")],
    ),
    "upx-mcp": (
        "You can run the upx CLI in the same container by overriding the entrypoint to pack/unpack executables without starting the MCP server.",
        [("Pack binary (mount it)", "/path/to/binary"), ("Show help", "--help")],
    ),
    "urlfinder-mcp": (
        "You can run the urlfinder CLI in the same container by overriding the entrypoint to find URLs in JS/code without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "uro-mcp": (
        "You can run the uro CLI in the same container by overriding the entrypoint to normalize and filter URLs without starting the MCP server.",
        [("Normalize URLs from stdin", ""), ("Show help", "-h")],
    ),
    "vanta-mcp": (
        "You can run the vanta-mcp CLI in the same container by overriding the entrypoint for Vanta compliance and security checks without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "volatility-mcp": (
        "You can run the vol.py (Volatility 2) CLI in the same container by overriding the entrypoint to analyze memory dumps without starting the MCP server.",
        [("List plugins", "-h"), ("Analyze image (mount it)", "-f /path/to/dump imageinfo")],
    ),
    "volatility3-mcp": (
        "You can run the volatility CLI in the same container by overriding the entrypoint to analyze memory dumps without starting the MCP server.",
        [("List plugins", "-h"), ("Analyze (mount dump)", "-f /path/to/dump windows.info")],
    ),
    "vulnerability-scanner-mcp": (
        "You can run the mcp-vuln-scanner CLI in the same container by overriding the entrypoint to scan for vulnerabilities without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "vulnx-mcp": (
        "You can run the vulnx CLI in the same container by overriding the entrypoint to scan for vulnerabilities without starting the MCP server.",
        [("Scan target", "-u https://example.com"), ("Show help", "-h")],
    ),
    "wafw00f-mcp": (
        "You can run the wafw00f CLI in the same container by overriding the entrypoint to detect WAFs without starting the MCP server.",
        [("Detect WAF", "https://example.com"), ("Show help", "-h")],
    ),
    "wapiti-mcp": (
        "You can run the wapiti CLI in the same container by overriding the entrypoint to scan web apps for vulnerabilities without starting the MCP server.",
        [("Scan URL", "-u https://example.com"), ("Show help", "--help")],
    ),
    "wappalyzergo-mcp": (
        "You can run the wappalyzergo-cli in the same container by overriding the entrypoint to detect technologies without starting the MCP server.",
        [("Analyze URL", "https://example.com"), ("Show help", "-h")],
    ),
    "wfuzz-mcp": (
        "You can run the wfuzz CLI in the same container by overriding the entrypoint to fuzz web parameters without starting the MCP server.",
        [("Fuzz a URL", "-u https://example.com/FUZZ -w /path/to/wordlist"), ("Show help", "--help")],
    ),
    "whatweb-mcp": (
        "You can run the whatweb CLI in the same container by overriding the entrypoint to identify web technologies without starting the MCP server.",
        [("Scan URL", "https://example.com"), ("Show help", "--help")],
    ),
    "wifiphisher-mcp": (
        "You can run the wifiphisher CLI in the same container by overriding the entrypoint for Wi-Fi phishing (needs wireless) without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "wireshark-mcp": (
        "You can run the tshark CLI in the same container by overriding the entrypoint to analyze packets without starting the MCP server.",
        [("Read pcap (mount it)", "-r /path/to/capture.pcap"), ("Show help", "-h")],
    ),
    "x8-mcp": (
        "You can run the x8 CLI in the same container by overriding the entrypoint to find hidden parameters without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "xsser-mcp": (
        "You can run the xsser CLI in the same container by overriding the entrypoint to find XSS without starting the MCP server.",
        [("Scan URL", "-u https://example.com"), ("Show help", "--help")],
    ),
    "xsstrike-mcp": (
        "You can run the xsstrike CLI in the same container by overriding the entrypoint to find XSS without starting the MCP server.",
        [("Scan URL", "-u https://example.com"), ("Show help", "--help")],
    ),
    "yara-mcp": (
        "You can run the yara CLI in the same container by overriding the entrypoint to match rules against files without starting the MCP server.",
        [("Scan path (mount rules/file)", "-r /rules /path/to/file"), ("Show help", "--help")],
    ),
    "yaraflux-mcp": (
        "You can run the yaraflux CLI in the same container by overriding the entrypoint to run Yara rules at scale without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "yersinia-mcp": (
        "You can run the yersinia CLI in the same container by overriding the entrypoint to attack network protocols without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "yeti-mcp": (
        "You can run the yeti-mcp CLI in the same container by overriding the entrypoint for Yeti threat intelligence or security workflows without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "zap-lis-mcp": (
        "You can run the zap-mcp CLI in the same container by overriding the entrypoint to run ZAP or MCP-related scans without starting the MCP server.",
        [("Show help", "--help")],
    ),
    "zap-mcp": (
        "You can run the zap.sh (OWASP ZAP) CLI in the same container by overriding the entrypoint for headless passive or active scanning without starting the MCP server.",
        [("Show help", "-h")],
    ),
    "zmap-mcp": (
        "You can run the zmap CLI in the same container by overriding the entrypoint for fast internet-scale scanning without starting the MCP server.",
        [("Scan port (needs capabilities)", "-p 80 10.0.0.0/8"), ("Show help", "--help")],
    ),
}
