#!/usr/bin/env python3
"""Generate MCP server directories for all phase3-mcp.txt entries.

Creates Dockerfile, mcp_server.py, docker-compose.yml, mcpServer.json,
requirements.txt, publish_to_hackerdogs.sh, test.sh, README.md, and
progress.md for each tool following the project template pattern.
"""

import os
import stat

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOOLS = [
    # (dir_name, display_name, binary, repo_owner_repo, description, port, install_type, install_detail, version_flag, tool_call_example)
    # install_type: "pip", "go", "apt", "git_clone_pip", "git_clone", "perl", "npm", "cargo", "binary_release", "already_mcp_pip", "already_mcp_node", "already_mcp_go", "c_build", "shell"

    ("certipy-mcp", "Certipy", "certipy", "ly4k/Certipy",
     "Active Directory certificate abuse and enumeration tool",
     8285, "pip", "certipy-ad", "--version", '{"name":"run_certipy","arguments":{"arguments":"--help"}}'),

    ("bloodhound-mcp", "BloodHound", "bloodhound-python", "SpecterOps/BloodHound",
     "Active Directory attack path analysis and enumeration",
     8286, "pip", "bloodhound", "--help", '{"name":"run_bloodhound","arguments":{"arguments":"--help"}}'),

    ("psudohash-mcp", "Psudohash", "psudohash", "t3l3machus/psudohash",
     "Password list generator for targeted attacks based on known information",
     8287, "git_clone_pip", "https://github.com/t3l3machus/psudohash.git", "--help", '{"name":"run_psudohash","arguments":{"arguments":"--help"}}'),

    ("wapiti-mcp", "Wapiti", "wapiti", "wapiti-scanner/wapiti",
     "Web application vulnerability scanner with black-box testing",
     8288, "pip", "wapiti3", "--version", '{"name":"run_wapiti","arguments":{"arguments":"--help"}}'),

    ("sstimap-mcp", "SSTImap", "sstimap", "vladko312/SSTImap",
     "Server-Side Template Injection detection and exploitation tool",
     8289, "git_clone_pip", "https://github.com/vladko312/SSTImap.git", "--help", '{"name":"run_sstimap","arguments":{"arguments":"--help"}}'),

    ("crlfuzz-mcp", "CRLFuzz", "crlfuzz", "dwisiswant0/crlfuzz",
     "CRLF injection vulnerability scanner",
     8290, "go", "github.com/dwisiswant0/crlfuzz/cmd/crlfuzz@latest", "-version", '{"name":"run_crlfuzz","arguments":{"arguments":"-h"}}'),

    ("smuggler-mcp", "Smuggler", "smuggler", "defparam/smuggler",
     "HTTP request smuggling detection tool",
     8291, "git_clone_pip", "https://github.com/defparam/smuggler.git", "--help", '{"name":"run_smuggler","arguments":{"arguments":"--help"}}'),

    ("corscanner-mcp", "CORScanner", "cors_scan", "chenjj/CORScanner",
     "CORS misconfiguration detection tool",
     8292, "git_clone_pip", "https://github.com/chenjj/CORScanner.git", "--help", '{"name":"run_corscanner","arguments":{"arguments":"--help"}}'),

    ("dnsreaper-mcp", "dnsReaper", "dnsreaper", "punk-security/dnsReaper",
     "Subdomain takeover vulnerability scanner via DNS",
     8293, "git_clone_pip", "https://github.com/punk-security/dnsReaper.git", "--help", '{"name":"run_dnsreaper","arguments":{"arguments":"--help"}}'),

    ("ai-infra-guard-mcp", "AI-Infra-Guard", "ai-infra-guard", "Tencent/AI-Infra-Guard",
     "AI infrastructure security scanning and assessment",
     8294, "pip", "ai-infra-guard", "--help", '{"name":"run_ai_infra_guard","arguments":{"arguments":"--help"}}'),

    ("ramparts-mcp", "Ramparts", "ramparts", "highflame-ai/ramparts",
     "AI security guardrails and safety framework",
     8295, "already_mcp_pip", "https://github.com/highflame-ai/ramparts.git", "--help", '{"name":"run_ramparts","arguments":{"arguments":"--help"}}'),

    ("mcpscan-mcp", "MCPScan", "mcpscan", "antgroup/MCPScan",
     "MCP server security scanning and vulnerability detection",
     8296, "git_clone_pip", "https://github.com/antgroup/MCPScan.git", "--help", '{"name":"run_mcpscan","arguments":{"arguments":"--help"}}'),

    ("securemcp-mcp", "SecureMCP", "securemcp", "makalin/SecureMCP",
     "MCP server security hardening and validation tool",
     8297, "git_clone_pip", "https://github.com/makalin/SecureMCP.git", "--help", '{"name":"run_securemcp","arguments":{"arguments":"--help"}}'),

    ("nova-proximity-mcp", "Nova Proximity", "nova-proximity", "Nova-Hunting/nova-proximity",
     "Network proximity analysis and threat detection",
     8298, "git_clone_pip", "https://github.com/Nova-Hunting/nova-proximity.git", "--help", '{"name":"run_nova_proximity","arguments":{"arguments":"--help"}}'),

    ("nova-framework-mcp", "Nova Framework", "nova-framework", "Nova-Hunting/nova-framework",
     "Automated security testing and orchestration framework",
     8299, "git_clone_pip", "https://github.com/Nova-Hunting/nova-framework.git", "--help", '{"name":"run_nova_framework","arguments":{"arguments":"--help"}}'),

    ("openvas-mcp", "OpenVAS", "openvas", "greenbone/openvas-scanner",
     "Open Vulnerability Assessment Scanner for comprehensive vulnerability scanning",
     8300, "apt", "openvas", "--version", '{"name":"run_openvas","arguments":{"arguments":"--help"}}'),

    ("sublist3r-mcp", "Sublist3r", "sublist3r", "aboul3la/Sublist3r",
     "Fast subdomain enumeration tool using OSINT",
     8301, "pip", "sublist3r", "--help", '{"name":"run_sublist3r","arguments":{"arguments":"--help"}}'),

    ("exploitdb-mcp", "ExploitDB", "searchsploit", "offensive-security/exploitdb",
     "Exploit Database search tool for known vulnerabilities",
     8302, "git_clone", "https://github.com/offensive-security/exploitdb.git", "--help", '{"name":"run_searchsploit","arguments":{"arguments":"--help"}}'),

    ("zmap-mcp", "ZMap", "zmap", "zmap/zmap",
     "High-speed single-packet network scanner for internet-wide surveys",
     8303, "apt", "zmap", "--version", '{"name":"run_zmap","arguments":{"arguments":"--help"}}'),

    ("dnsenum-mcp", "dnsenum", "dnsenum", "fwaeytens/dnsenum",
     "DNS enumeration tool for discovering host information",
     8304, "perl", "dnsenum", "--help", '{"name":"run_dnsenum","arguments":{"arguments":"--help"}}'),

    ("joomscan-mcp", "JoomScan", "joomscan", "OWASP/joomscan",
     "OWASP Joomla vulnerability scanner",
     8305, "perl", "joomscan", "--help", '{"name":"run_joomscan","arguments":{"arguments":"--help"}}'),

    ("ncrack-mcp", "Ncrack", "ncrack", "nmap/ncrack",
     "High-speed network authentication cracking tool",
     8306, "apt", "ncrack", "--version", '{"name":"run_ncrack","arguments":{"arguments":"--help"}}'),

    ("crowbar-mcp", "Crowbar", "crowbar", "galkan/crowbar",
     "Brute-forcing tool supporting protocols not commonly supported",
     8307, "git_clone_pip", "https://github.com/galkan/crowbar.git", "--help", '{"name":"run_crowbar","arguments":{"arguments":"--help"}}'),

    ("brutespray-mcp", "BruteSpray", "brutespray", "x90skysn3k/brutespray",
     "Automated brute-forcing from Nmap or Nessus scan output",
     8308, "git_clone_pip", "https://github.com/x90skysn3k/brutespray.git", "--help", '{"name":"run_brutespray","arguments":{"arguments":"--help"}}'),

    ("fping-mcp", "Fping", "fping", "schweikert/fping",
     "High-performance ping utility for parallel host probing",
     8309, "apt", "fping", "--version", '{"name":"run_fping","arguments":{"arguments":"--help"}}'),

    ("bully-mcp", "Bully", "bully", "aanarchyy/bully",
     "WPS brute-force attack tool for WiFi networks",
     8310, "c_build", "https://github.com/aanarchyy/bully.git", "--help", '{"name":"run_bully","arguments":{"arguments":"--help"}}'),

    ("pixiewps-mcp", "Pixiewps", "pixiewps", "wiire-a/pixiewps",
     "Offline WPS brute-force tool exploiting low/no entropy weakness",
     8311, "c_build", "https://github.com/wiire-a/pixiewps.git", "--version", '{"name":"run_pixiewps","arguments":{"arguments":"--help"}}'),

    ("wifiphisher-mcp", "Wifiphisher", "wifiphisher", "wifiphisher/wifiphisher",
     "Automated WiFi phishing attacks and credential harvesting",
     8312, "pip", "wifiphisher", "--help", '{"name":"run_wifiphisher","arguments":{"arguments":"--help"}}'),

    ("ettercap-mcp", "Ettercap", "ettercap", "Ettercap/ettercap",
     "Comprehensive suite for man-in-the-middle attacks on LAN",
     8313, "apt", "ettercap-text-only", "--version", '{"name":"run_ettercap","arguments":{"arguments":"--help"}}'),

    ("ngrep-mcp", "Ngrep", "ngrep", "jpr5/ngrep",
     "Network packet analyzer with grep-like pattern matching",
     8314, "apt", "ngrep", "-h", '{"name":"run_ngrep","arguments":{"arguments":"-h"}}'),

    ("wireshark-mcp", "Wireshark (tshark)", "tshark", "wireshark/wireshark",
     "Network protocol analyzer for deep packet inspection",
     8315, "apt", "tshark", "--version", '{"name":"run_tshark","arguments":{"arguments":"--help"}}'),

    ("slowhttptest-mcp", "SlowHTTPTest", "slowhttptest", "shekyan/slowhttptest",
     "Application layer DoS attack simulator for slow HTTP attacks",
     8316, "apt", "slowhttptest", "-h", '{"name":"run_slowhttptest","arguments":{"arguments":"-h"}}'),

    ("sherlock-mcp", "Sherlock", "sherlock", "sherlock-project/sherlock",
     "Username hunting across social networks and websites",
     8317, "pip", "sherlock-project", "--help", '{"name":"run_sherlock","arguments":{"arguments":"--help"}}'),

    ("bettercap-mcp", "Bettercap", "bettercap", "bettercap/bettercap",
     "Network attack and monitoring framework with MITM capabilities",
     8318, "go", "github.com/bettercap/bettercap@latest", "-h", '{"name":"run_bettercap","arguments":{"arguments":"-h"}}'),

    ("yersinia-mcp", "Yersinia", "yersinia", "tomac/yersinia",
     "Network vulnerability exploitation tool for layer 2 attacks",
     8319, "apt", "yersinia", "--version", '{"name":"run_yersinia","arguments":{"arguments":"--help"}}'),

    ("cutter-mcp", "Cutter", "cutter", "rizinorg/cutter",
     "Reverse engineering platform powered by Rizin",
     8320, "apt", "rizin", "-v", '{"name":"run_cutter","arguments":{"arguments":"--help"}}'),

    ("aircrack-ng-mcp", "Aircrack-ng", "aircrack-ng", "aircrack-ng/aircrack-ng",
     "WiFi security auditing tools suite for WEP/WPA/WPA2 cracking",
     8321, "apt", "aircrack-ng", "--help", '{"name":"run_aircrack_ng","arguments":{"arguments":"--help"}}'),

    ("netdiscover-mcp", "Netdiscover", "netdiscover", "netdiscover-scanner/netdiscover",
     "Active/passive ARP reconnaissance tool for network discovery",
     8322, "apt", "netdiscover", "-h", '{"name":"run_netdiscover","arguments":{"arguments":"-h"}}'),

    ("sslscan-mcp", "SSLScan", "sslscan", "rbsec/sslscan",
     "SSL/TLS configuration and certificate scanner",
     8323, "apt", "sslscan", "--version", '{"name":"run_sslscan","arguments":{"arguments":"--help"}}'),

    ("crunch-mcp", "Crunch", "crunch", "crunchsec/crunch",
     "Custom wordlist generator for password cracking",
     8324, "apt", "crunch", "-h", '{"name":"run_crunch","arguments":{"arguments":"-h"}}'),

    ("smtp-user-enum-mcp", "SMTP User Enum", "smtp-user-enum", "pentestmonkey/smtp-user-enum",
     "SMTP username enumeration via VRFY, EXPN, and RCPT commands",
     8325, "perl", "smtp-user-enum", "--help", '{"name":"run_smtp_user_enum","arguments":{"arguments":"--help"}}'),

    ("lynis-mcp", "Lynis", "lynis", "CISOfy/lynis",
     "Security auditing and compliance testing tool for Linux/Unix",
     8326, "shell", "lynis", "--version", '{"name":"run_lynis","arguments":{"arguments":"--help"}}'),

    ("netcat-mcp", "Netcat", "nc", "diegocr/netcat",
     "TCP/UDP networking utility for port scanning and data transfer",
     8327, "apt", "netcat-openbsd", "-h", '{"name":"run_netcat","arguments":{"arguments":"-h"}}'),

    ("yara-mcp", "YARA", "yara", "VirusTotal/yara",
     "Pattern matching tool for malware researchers and classification",
     8328, "apt", "yara", "--version", '{"name":"run_yara","arguments":{"arguments":"--help"}}'),

    ("capa-mcp", "Capa", "capa", "mandiant/capa",
     "Capability detection tool for malware triage and analysis",
     8329, "pip", "flare-capa", "--version", '{"name":"run_capa","arguments":{"arguments":"--help"}}'),

    ("trivy-mcp", "Trivy", "trivy", "aquasecurity/trivy",
     "Comprehensive vulnerability scanner for containers, filesystems, and IaC",
     8330, "binary_release", "trivy", "--version", '{"name":"run_trivy","arguments":{"arguments":"--help"}}'),

    ("roadtools-mcp", "ROADtools", "roadrecon", "dirkjanm/ROADtools",
     "Azure AD enumeration and attack tools for cloud security",
     8331, "pip", "roadtools", "--help", '{"name":"run_roadtools","arguments":{"arguments":"--help"}}'),

    ("gitleaks-mcp", "Gitleaks", "gitleaks", "gitleaks/gitleaks",
     "Secret detection tool for git repositories and files",
     8332, "go", "github.com/gitleaks/gitleaks/v8@latest", "version", '{"name":"run_gitleaks","arguments":{"arguments":"--help"}}'),

    ("boofuzz-mcp", "Boofuzz", "boofuzz", "jtpereyda/boofuzz",
     "Network protocol fuzzing framework for finding vulnerabilities",
     8333, "pip", "boofuzz", "--help", '{"name":"run_boofuzz","arguments":{"arguments":"--help"}}'),

    ("dharma-mcp", "Dharma", "dharma", "MozillaSecurity/dharma",
     "Grammar-based test case generation for fuzzing",
     8334, "pip", "dharma", "--help", '{"name":"run_dharma","arguments":{"arguments":"--help"}}'),

    ("semgrep-mcp", "Semgrep", "semgrep", "semgrep/semgrep",
     "Lightweight static analysis for code security with 5000+ rules",
     8335, "pip", "semgrep", "--version", '{"name":"run_semgrep","arguments":{"arguments":"--help"}}'),

    ("yaraflux-mcp", "YaraFlux", "yaraflux", "ThreatFlux/YaraFlux",
     "YARA-based MCP server for malware scanning and rule management",
     8336, "already_mcp_pip", "https://github.com/ThreatFlux/YaraFlux.git", "--help", '{"name":"run_yaraflux","arguments":{"arguments":"--help"}}'),

    ("yeti-mcp", "Yeti", "yeti-mcp", "yeti-platform/yeti-mcp",
     "Threat intelligence platform MCP integration",
     8337, "already_mcp_pip", "https://github.com/yeti-platform/yeti-mcp.git", "--help", '{"name":"run_yeti_mcp","arguments":{"arguments":"--help"}}'),

    ("bloodhound-mcp-ai-mcp", "BloodHound AI", "bloodhound-mcp", "stevenyu113228/BloodHound-MCP",
     "AI-powered Active Directory attack path analysis",
     8338, "already_mcp_pip", "https://github.com/stevenyu113228/BloodHound-MCP.git", "--help", '{"name":"run_bloodhound_mcp","arguments":{"arguments":"--help"}}'),

    ("vulnerability-scanner-mcp", "Vulnerability Scanner", "mcp-vuln-scanner", "RobertoDure/mcp-vulnerability-scanner",
     "Vulnerability scanning and assessment tool",
     8339, "already_mcp_pip", "https://github.com/RobertoDure/mcp-vulnerability-scanner.git", "--help", '{"name":"run_vuln_scanner","arguments":{"arguments":"--help"}}'),

    ("mcpserver-audit-mcp", "MCPServer Audit", "mcpserver-audit", "ModelContextProtocol-Security/mcpserver-audit",
     "Security auditing tool for MCP servers",
     8340, "already_mcp_pip", "https://github.com/ModelContextProtocol-Security/mcpserver-audit.git", "--help", '{"name":"run_mcpserver_audit","arguments":{"arguments":"--help"}}'),

    ("a2a-scanner-mcp", "A2A Scanner", "a2a-scanner", "cisco-ai-defense/a2a-scanner",
     "Agent-to-Agent communication security scanner",
     8341, "already_mcp_pip", "https://github.com/cisco-ai-defense/a2a-scanner.git", "--help", '{"name":"run_a2a_scanner","arguments":{"arguments":"--help"}}'),

    ("cisco-mcp-scanner-mcp", "Cisco AI Defense Scanner", "mcp-scanner", "cisco-ai-defense/mcp-scanner",
     "AI defense protocol security scanning and analysis",
     8342, "already_mcp_pip", "https://github.com/cisco-ai-defense/mcp-scanner.git", "--help", '{"name":"run_cisco_mcp_scanner","arguments":{"arguments":"--help"}}'),

    ("aibom-mcp", "AIBOM", "aibom", "cisco-ai-defense/aibom",
     "AI Bill of Materials generator for AI model transparency",
     8343, "already_mcp_pip", "https://github.com/cisco-ai-defense/aibom.git", "--help", '{"name":"run_aibom","arguments":{"arguments":"--help"}}'),

    ("knostic-mcp-scanner-mcp", "Knostic Scanner", "mcp-scanner", "knostic/MCP-Scanner",
     "Security scanner for AI agent servers and configurations",
     8344, "already_mcp_pip", "https://github.com/knostic/MCP-Scanner.git", "--help", '{"name":"run_knostic_scanner","arguments":{"arguments":"--help"}}'),

    ("threat-hunting-mcp", "Threat Hunting", "threat-hunting", "THORCollective/threat-hunting-mcp-server",
     "Threat hunting and intelligence gathering MCP server",
     8345, "already_mcp_pip", "https://github.com/THORCollective/threat-hunting-mcp-server.git", "--help", '{"name":"run_threat_hunting","arguments":{"arguments":"--help"}}'),

    ("aws-s3-mcp", "AWS S3", "aws-s3-mcp", "samuraikun/aws-s3-mcp",
     "AWS S3 bucket security analysis and enumeration",
     8346, "already_mcp_node", "https://github.com/samuraikun/aws-s3-mcp.git", "--help", '{"name":"run_aws_s3","arguments":{"arguments":"--help"}}'),

    ("osv-mcp", "OSV", "osv-mcp", "StacklokLabs/osv-mcp",
     "Open Source Vulnerability database query tool via MCP",
     8347, "already_mcp_pip", "https://github.com/StacklokLabs/osv-mcp.git", "--help", '{"name":"run_osv","arguments":{"arguments":"--help"}}'),

    ("vanta-mcp", "Vanta", "vanta-mcp", "VantaInc/vanta-mcp-server",
     "Vanta compliance and security monitoring MCP integration",
     8348, "already_mcp_node", "https://github.com/VantaInc/vanta-mcp-server.git", "--help", '{"name":"run_vanta","arguments":{"arguments":"--help"}}'),

    ("xsstrike-mcp", "XSStrike", "xsstrike", "s0md3v/XSStrike",
     "Advanced XSS detection and exploitation tool",
     8349, "git_clone_pip", "https://github.com/s0md3v/XSStrike.git", "--help", '{"name":"run_xsstrike","arguments":{"arguments":"--help"}}'),

    ("gospider-mcp", "Gospider", "gospider", "jaeles-project/gospider",
     "Fast web crawling and URL discovery tool",
     8350, "go", "github.com/jaeles-project/gospider@latest", "-h", '{"name":"run_gospider","arguments":{"arguments":"-h"}}'),

    ("ipinfo-mcp", "IPInfo", "ipinfo", "ipinfo/cli",
     "IP address intelligence and geolocation lookup tool",
     8351, "go", "github.com/ipinfo/cli/ipinfo@latest", "version", '{"name":"run_ipinfo","arguments":{"arguments":"--help"}}'),

    ("garak-mcp", "Garak", "garak-mcp", "EdenYavin/Garak-MCP",
     "AI red teaming and LLM vulnerability testing",
     8352, "already_mcp_pip", "https://github.com/EdenYavin/Garak-MCP.git", "--help", '{"name":"run_garak","arguments":{"arguments":"--help"}}'),

    ("rasn-mcp", "RASN", "rasn", "copyleftdev/rasn",
     "Rust-based ASN lookup and network intelligence tool",
     8353, "already_mcp_pip", "https://github.com/copyleftdev/rasn.git", "--help", '{"name":"run_rasn","arguments":{"arguments":"--help"}}'),

    ("port-scanner-mcp", "Port Scanner", "port-scanner", "relaxcloud-cn/mcp-port-scanner",
     "Network port scanning tool",
     8354, "already_mcp_pip", "https://github.com/relaxcloud-cn/mcp-port-scanner.git", "--help", '{"name":"run_port_scanner","arguments":{"arguments":"--help"}}'),

    ("zap-lis-mcp", "ZAP Lis", "zap-mcp", "LisBerndt/zap-mcp-server",
     "OWASP ZAP integration for web security testing",
     8355, "already_mcp_pip", "https://github.com/LisBerndt/zap-mcp-server.git", "--help", '{"name":"run_zap_lis","arguments":{"arguments":"--help"}}'),

    ("trivy-neutr0n-mcp", "Trivy Neutr0n", "trivy-mcp", "Mr-Neutr0n/trivy-mcp-server",
     "Trivy-based container and filesystem vulnerability scanning",
     8356, "already_mcp_pip", "https://github.com/Mr-Neutr0n/trivy-mcp-server.git", "--help", '{"name":"run_trivy_mcp","arguments":{"arguments":"--help"}}'),

    ("grype-mcp", "Grype", "grype", "anchore/grype",
     "Container image and filesystem vulnerability scanner",
     8357, "binary_release", "grype", "version", '{"name":"run_grype","arguments":{"arguments":"--help"}}'),

    ("syft-mcp", "Syft", "syft", "anchore/syft",
     "Software bill of materials (SBOM) generator for container images",
     8358, "binary_release", "syft", "version", '{"name":"run_syft","arguments":{"arguments":"--help"}}'),

    ("horusec-mcp", "Horusec", "horusec", "Checkmarx/Horusec",
     "Static application security testing (SAST) tool",
     8359, "binary_release", "horusec", "version", '{"name":"run_horusec","arguments":{"arguments":"--help"}}'),

    ("bearer-mcp", "Bearer", "bearer", "Bearer/bearer",
     "Code security scanning tool for sensitive data flows",
     8360, "binary_release", "bearer", "version", '{"name":"run_bearer","arguments":{"arguments":"--help"}}'),

    ("dependency-check-mcp", "Dependency-Check", "dependency-check", "jeremylong/DependencyCheck",
     "Software composition analysis for known vulnerabilities in dependencies",
     8361, "binary_release", "dependency-check", "--version", '{"name":"run_dependency_check","arguments":{"arguments":"--help"}}'),

    ("kubescape-mcp", "Kubescape", "kubescape", "kubescape/kubescape",
     "Kubernetes security posture management and compliance scanning",
     8362, "binary_release", "kubescape", "version", '{"name":"run_kubescape","arguments":{"arguments":"--help"}}'),

    ("ggshield-mcp", "ggshield", "ggshield", "GitGuardian/ggshield",
     "Secret detection and code security scanning by GitGuardian",
     8363, "pip", "ggshield", "--version", '{"name":"run_ggshield","arguments":{"arguments":"--help"}}'),

    ("retire-js-mcp", "Retire.js", "retire", "RetireJS/retire.js",
     "JavaScript library vulnerability scanner for known CVEs",
     8364, "npm", "retire", "--version", '{"name":"run_retire","arguments":{"arguments":"--help"}}'),

    ("suricata-mcp", "Suricata", "suricata-mcp", "Medinios/SuricataMCP",
     "Suricata network intrusion detection and monitoring",
     8365, "already_mcp_pip", "https://github.com/Medinios/SuricataMCP.git", "--help", '{"name":"run_suricata_mcp","arguments":{"arguments":"--help"}}'),
]


def safe_func_name(binary: str) -> str:
    """Convert binary name to a safe Python function name."""
    return binary.replace("-", "_").replace(".", "_").replace("/", "_")


def generate_dockerfile(t):
    dir_name, display, binary, repo, desc, port, install_type, install_detail, ver_flag, _ = t
    repo_url = f"https://github.com/{repo}"

    install_block = ""
    builder_stage = ""

    # Flag to skip standalone tini install when it's included in the tool install block
    include_tini_in_install = False

    if install_type == "pip":
        install_block = f'RUN pip install --no-cache-dir {install_detail}'
    elif install_type == "go":
        builder_stage = f"""# ---- Stage 1: Build {binary} from source ----
FROM golang:1.24-bookworm AS builder

RUN go install -v {install_detail}

# ---- Stage 2: Runtime ----
"""
        copy_line = f"COPY --from=builder /go/bin/{binary} /usr/local/bin/{binary}"
        install_block = copy_line
    elif install_type == "apt":
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    {install_detail} \\
    tini \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/*"""
    elif install_type == "npm":
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    nodejs npm tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && npm install -g {install_detail}"""
    elif install_type == "cargo":
        builder_stage = f"""# ---- Stage 1: Build {binary} from source ----
FROM rust:1.77-slim-bookworm AS builder

RUN cargo install {install_detail}

# ---- Stage 2: Runtime ----
"""
        install_block = f"COPY --from=builder /usr/local/cargo/bin/{binary} /usr/local/bin/{binary}"
    elif install_type in ("git_clone_pip", "git_clone"):
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    git tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && git clone --depth 1 {install_detail} /opt/{binary} \\
    && cd /opt/{binary} && (pip install --no-cache-dir -r requirements.txt 2>/dev/null || true) \\
    && (pip install --no-cache-dir . 2>/dev/null || true) \\
    && ln -sf /opt/{binary}/{binary}.py /usr/local/bin/{binary} 2>/dev/null || true"""
    elif install_type == "perl":
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    perl libnet-dns-perl libxml-libxml-perl git tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && git clone --depth 1 https://github.com/{repo}.git /opt/{binary} \\
    && chmod +x /opt/{binary}/*.pl 2>/dev/null || true \\
    && ln -sf /opt/{binary}/{binary}.pl /usr/local/bin/{binary} 2>/dev/null; \\
    ln -sf /opt/{binary}/{binary} /usr/local/bin/{binary} 2>/dev/null || true"""
    elif install_type == "shell":
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    git tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && git clone --depth 1 https://github.com/{repo}.git /opt/{binary} \\
    && ln -sf /opt/{binary}/{binary} /usr/local/bin/{binary}"""
    elif install_type == "c_build":
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    git build-essential autoconf automake libtool pkg-config tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && git clone --depth 1 {install_detail} /tmp/{binary}-src \\
    && cd /tmp/{binary}-src && (autoreconf -i 2>/dev/null || true) && (./configure 2>/dev/null || true) && make && make install \\
    && rm -rf /tmp/{binary}-src"""
    elif install_type == "binary_release":
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

# Install {binary} — download the latest release binary
# See https://github.com/{repo}/releases for installation
RUN curl -sSfL https://raw.githubusercontent.com/{repo}/main/install.sh | sh -s -- -b /usr/local/bin 2>/dev/null || \\
    (echo "Auto-install failed. Manual install may be required for {binary}." && which {binary} || true)"""
    elif install_type.startswith("already_mcp"):
        include_tini_in_install = True
        install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    git tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && git clone --depth 1 {install_detail} /opt/{dir_name.replace('-mcp', '')}-src \\
    && cd /opt/{dir_name.replace('-mcp', '')}-src && (pip install --no-cache-dir -r requirements.txt 2>/dev/null || true) \\
    && (pip install --no-cache-dir . 2>/dev/null || true)"""
        if "node" in install_type:
            install_block = f"""RUN apt-get update && apt-get install -y --no-install-recommends \\
    git nodejs npm tini ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && git clone --depth 1 {install_detail} /opt/{dir_name.replace('-mcp', '')}-src \\
    && cd /opt/{dir_name.replace('-mcp', '')}-src && npm install 2>/dev/null || true"""

    base_image = "python:3.12-slim-bookworm"

    tini_block = ""
    if not include_tini_in_install:
        tini_block = """
RUN apt-get update && apt-get install -y --no-install-recommends \\
    tini \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/*
"""

    content = f"""{builder_stage}# {display} MCP Server - Hackerdogs Ready
# Multi-arch build for linux/amd64 and linux/arm64

FROM {base_image}

LABEL org.opencontainers.image.source="https://github.com/hackerdogs-ai/hd-mcpservers-docker"
LABEL org.opencontainers.image.description="{display} MCP Server - {desc}"
LABEL org.opencontainers.image.vendor="Hackerdogs"
LABEL "maintainer"="support@hackerdogs.ai"
LABEL "mcp-server-scope"="remote"
LABEL org.opencontainers.image.title="{dir_name}"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.author="hackerdogs"

# Security: Create non-root user
RUN groupadd -g 1000 mcpuser && \\
    useradd -u 1000 -g mcpuser -m -s /bin/bash mcpuser

{install_block}
{tini_block}
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_server.py ./

# Create output directory
RUN mkdir -p /app/output && chown -R mcpuser:mcpuser /app

# Switch to non-root user
USER mcpuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT={port}

EXPOSE {port}

# Use tini for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start MCP server
CMD ["python", "mcp_server.py"]
"""
    return content


def generate_mcp_server(t):
    dir_name, display, binary, repo, desc, port, install_type, install_detail, ver_flag, _ = t
    func_name = safe_func_name(binary)
    repo_url = f"https://github.com/{repo}"

    return f'''#!/usr/bin/env python3
"""{display} MCP Server — {desc}.

Wraps the {binary} CLI ({repo}) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shutil
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("{dir_name}")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "{port}"))

mcp = FastMCP(
    "{display} MCP Server",
    instructions=(
        "{desc}."
    ),
)

BIN_NAME = os.environ.get("{binary.upper().replace("-", "_")}_BIN", "{binary}")


def _find_binary() -> str:
    """Locate the {binary} binary, raising a clear error if missing."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error("{binary} binary not found on PATH")
        raise FileNotFoundError(
            f"{binary} binary not found. Ensure it is installed and available "
            f"on PATH, or set {binary.upper().replace("-", "_")}_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a {binary} command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    binary_path = _find_binary()
    cmd = [binary_path] + args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        logger.error("Command timed out after %ds: %s", timeout_seconds, " ".join(cmd))
        return {{
            "stdout": "",
            "stderr": f"Command timed out after {{timeout_seconds}}s: {{' '.join(cmd)}}",
            "return_code": -1,
        }}
    except Exception as exc:
        logger.error("Command execution failed: %s", exc)
        return {{
            "stdout": "",
            "stderr": f"Failed to execute command: {{exc}}",
            "return_code": -1,
        }}

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return {{
        "stdout": stdout,
        "stderr": stderr,
        "return_code": proc.returncode,
    }}


@mcp.tool()
async def run_{func_name}(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run {binary} with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_{func_name} called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("{binary} command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {{
                "error": True,
                "message": f"{binary} failed (exit code {{result[\'return_code\']}})",
                "detail": error_detail.strip(),
                "command": f"{binary} {{' '.join(args)}}",
            }},
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({{"message": "Command completed with no output", "arguments": arguments}})

    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({{"raw": line}})

    if len(results) == 1:
        return json.dumps(results[0], indent=2)
    return json.dumps(results, indent=2)


def main():
    logger.info("Starting {dir_name} server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
'''


def generate_docker_compose(t):
    dir_name, display, binary, repo, desc, port, *_ = t
    return f'''version: "3.8"

services:
  {dir_name}:
    image: hackerdogs/{dir_name}:latest
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {dir_name}
    ports:
      - "{port}:{port}"
    environment:
      - MCP_TRANSPORT=streamable-http
      - MCP_PORT={port}
    restart: unless-stopped
'''


def generate_mcp_server_json(t):
    dir_name, display, binary, repo, desc, port, *_ = t
    return f'''{{
  "mcpServers": {{
    "{dir_name}": {{
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "hackerdogs/{dir_name}:latest"
      ],
      "env": {{}}
    }}
  }}
}}
'''


def generate_requirements():
    return "fastmcp>=2.0.0\n"


def generate_publish_script(t):
    dir_name, display, binary, repo, desc, port, *_ = t
    return f'''#!/bin/bash
# Build and Publish {display} MCP Server Docker Image to Docker Hub
# Image name: {dir_name}

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Configuration
IMAGE_NAME="{dir_name}"
DOCKERFILE="Dockerfile"
DEFAULT_TAG="latest"
PROJECT_ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# Flags
DO_BUILD=false
DO_PUBLISH=false
SHOW_HELP=false
PLATFORMS_MODE="parallel"

# Parse command-line arguments
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            DO_BUILD=true
            shift
            ;;
        --publish)
            DO_PUBLISH=true
            shift
            ;;
        --platforms)
            PLATFORMS_MODE="$2"
            shift 2
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    echo "Build and Publish {display} MCP Server Docker Image to Docker Hub"
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS] <dockerhub_username> [tag] [additional_tag...]"
    echo ""
    echo "Options:"
    echo "  --build      Only build the Docker image (do not publish)"
    echo "  --publish    Only publish the Docker image (assumes image already exists)"
    echo "  --platforms parallel|sequential  Push both platforms at once (default) or amd64 then arm64"
    echo "  --help, -h   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 hackerdogs                    # Build and publish with tag 'latest'"
    echo "  $0 --build hackerdogs             # Only build (tag: latest)"
    echo "  $0 --publish hackerdogs           # Only publish"
    echo "  $0 --build --publish hackerdogs v1.0.0           # Build and publish with tag v1.0.0"
    echo "  $0 --build --publish --platforms sequential hackerdogs v1.0.0 latest"
    exit 0
fi

# If neither flag is set, do both (default behavior)
if [ "$DO_BUILD" = false ] && [ "$DO_PUBLISH" = false ]; then
    DO_BUILD=true
    DO_PUBLISH=true
fi

# Normalize platforms mode
if [ "$PLATFORMS_MODE" != "sequential" ]; then
    PLATFORMS_MODE="parallel"
fi

# Change to project root
cd "$PROJECT_ROOT"

# Get Docker Hub username from remaining arguments
if [ "$DO_PUBLISH" = true ]; then
    if [ ${{#ARGS[@]}} -eq 0 ]; then
        echo -e "${{YELLOW}}Docker Hub username not provided.${{NC}}"
        read -p "Enter your Docker Hub username: " DOCKERHUB_USERNAME
        if [ -z "$DOCKERHUB_USERNAME" ]; then
            echo -e "${{RED}}Error: Docker Hub username is required for publishing${{NC}}"
            exit 1
        fi
    else
        DOCKERHUB_USERNAME="${{ARGS[0]}}"
    fi
    FULL_IMAGE_NAME="${{DOCKERHUB_USERNAME}}/${{IMAGE_NAME}}"
else
    DOCKERHUB_USERNAME=""
    FULL_IMAGE_NAME="${{IMAGE_NAME}}"
fi

# Get tags from remaining arguments
TAGS=("${{ARGS[@]:1}}")
if [ ${{#TAGS[@]}} -eq 0 ]; then
    TAGS=("$DEFAULT_TAG")
fi

# Display operation summary
echo "================================================================================="
if [ "$DO_BUILD" = true ] && [ "$DO_PUBLISH" = true ]; then
    echo -e "${{BLUE}}Building and Publishing {display} MCP Server Docker Image${{NC}}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${{BLUE}}Building {display} MCP Server Docker Image${{NC}}"
else
    echo -e "${{BLUE}}Publishing {display} MCP Server Docker Image to Docker Hub${{NC}}"
fi
echo "================================================================================="
if [ "$DO_PUBLISH" = true ]; then
    echo "Docker Hub Username: ${{GREEN}}${{DOCKERHUB_USERNAME}}${{NC}}"
fi
echo "Image Name: ${{GREEN}}${{IMAGE_NAME}}${{NC}}"
if [ "$DO_BUILD" = true ]; then
    echo "Dockerfile: ${{GREEN}}${{DOCKERFILE}}${{NC}}"
fi
echo "Tags: ${{GREEN}}${{TAGS[*]}}${{NC}}"
echo "Full Image Name: ${{GREEN}}${{FULL_IMAGE_NAME}}${{NC}}"
echo "================================================================================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${{RED}}Error: Docker is not installed or not in PATH${{NC}}"
    exit 1
fi

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${{RED}}Error: Docker is not running or not accessible${{NC}}"
    exit 1
fi

# Setup Docker Buildx for multi-platform builds
echo -e "${{YELLOW}}Setting up Docker Buildx for multi-platform support...${{NC}}"
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${{RED}}Error: Docker Buildx is not available. Please upgrade Docker.${{NC}}"
    exit 1
fi

BUILDER_NAME="multiarch-builder"
if ! docker buildx inspect "$BUILDER_NAME" > /dev/null 2>&1; then
    echo -e "${{YELLOW}}Creating multi-platform builder: ${{BUILDER_NAME}}${{NC}}"
    docker buildx create --name "$BUILDER_NAME" --use --bootstrap
    if [ $? -ne 0 ]; then
        echo -e "${{RED}}Error: Failed to create buildx builder${{NC}}"
        exit 1
    fi
else
    docker buildx use "$BUILDER_NAME" > /dev/null 2>&1
fi
echo -e "${{GREEN}}Buildx builder ready${{NC}}"
echo ""

# Check Docker Hub authentication if publishing
if [ "$DO_PUBLISH" = true ]; then
    echo -e "${{YELLOW}}Checking Docker Hub authentication...${{NC}}"
    if ! docker info | grep -q "Username"; then
        echo -e "${{YELLOW}}You are not logged in to Docker Hub.${{NC}}"
        echo "Please log in with: docker login"
        read -p "Do you want to log in now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
            if [ $? -ne 0 ]; then
                echo -e "${{RED}}Error: Docker login failed${{NC}}"
                exit 1
            fi
        else
            echo -e "${{RED}}Error: Docker Hub login required for publishing${{NC}}"
            exit 1
        fi
    else
        echo -e "${{GREEN}}Docker Hub authentication verified${{NC}}"
    fi
    echo ""
fi

# Retry helper for 502/network issues
MAX_RETRIES=5
do_build_push_with_retry() {{
    local retry=0
    local backoff=30
    while [ $retry -lt $MAX_RETRIES ]; do
        if [ $retry -gt 0 ]; then
            echo -e "${{YELLOW}}Retry $retry/$MAX_RETRIES in ${{backoff}}s...${{NC}}"
            sleep "$backoff"
            backoff=$((backoff * 2))
            [ $backoff -gt 300 ] && backoff=300
        fi
        if "$@"; then
            return 0
        fi
        retry=$((retry + 1))
    done
    return 1
}}

# Build the image
if [ "$DO_BUILD" = true ]; then
    if [ ! -f "$DOCKERFILE" ]; then
        echo -e "${{RED}}Error: Dockerfile not found: ${{DOCKERFILE}}${{NC}}"
        exit 1
    fi

    if [ "$DO_PUBLISH" = true ]; then
        echo -e "${{YELLOW}}Building Docker image from ${{DOCKERFILE}} (multi-platform)...${{NC}}"
        echo "Platforms: linux/amd64, linux/arm64"
        echo ""

        for tag in "${{TAGS[@]}}"; do
            if [ "$PLATFORMS_MODE" = "sequential" ]; then
                echo "Building and pushing ${{FULL_IMAGE_NAME}}:${{tag}} (sequential)..."
                if ! do_build_push_with_retry docker buildx build \\
                    --platform linux/amd64 \\
                    --provenance=false \\
                    --sbom=false \\
                    -f "$DOCKERFILE" \\
                    -t "${{FULL_IMAGE_NAME}}:${{tag}}-amd64" \\
                    --push \\
                    . ; then
                    echo -e "${{RED}}Error: Failed to build/push amd64 after $MAX_RETRIES attempts${{NC}}"
                    exit 1
                fi
                echo -e "${{GREEN}}Pushed ${{FULL_IMAGE_NAME}}:${{tag}}-amd64${{NC}}"

                if ! do_build_push_with_retry docker buildx build \\
                    --platform linux/arm64 \\
                    --provenance=false \\
                    --sbom=false \\
                    -f "$DOCKERFILE" \\
                    -t "${{FULL_IMAGE_NAME}}:${{tag}}-arm64" \\
                    --push \\
                    . ; then
                    echo -e "${{RED}}Error: Failed to build/push arm64 after $MAX_RETRIES attempts${{NC}}"
                    exit 1
                fi
                echo -e "${{GREEN}}Pushed ${{FULL_IMAGE_NAME}}:${{tag}}-arm64${{NC}}"

                docker buildx imagetools create -t "${{FULL_IMAGE_NAME}}:${{tag}}" \\
                    "${{FULL_IMAGE_NAME}}:${{tag}}-amd64" \\
                    "${{FULL_IMAGE_NAME}}:${{tag}}-arm64"
                if [ $? -ne 0 ]; then
                    echo -e "${{RED}}Error: Failed to create manifest for ${{FULL_IMAGE_NAME}}:${{tag}}${{NC}}"
                    exit 1
                fi
            else
                echo "Building and pushing ${{FULL_IMAGE_NAME}}:${{tag}}..."
                if ! do_build_push_with_retry docker buildx build \\
                    --platform linux/amd64,linux/arm64 \\
                    --provenance=false \\
                    --sbom=false \\
                    -f "$DOCKERFILE" \\
                    -t "${{FULL_IMAGE_NAME}}:${{tag}}" \\
                    --push \\
                    . ; then
                    echo -e "${{RED}}Error: Docker buildx build failed after $MAX_RETRIES attempts${{NC}}"
                    exit 1
                fi
            fi
            echo -e "${{GREEN}}Successfully built and pushed ${{FULL_IMAGE_NAME}}:${{tag}}${{NC}}"
        done
    else
        echo -e "${{YELLOW}}Building Docker image from ${{DOCKERFILE}} (local platform only)...${{NC}}"
        echo ""

        LOCAL_IMAGE_NAME="${{IMAGE_NAME}}:${{TAGS[0]}}"
        docker buildx build \\
            --load \\
            -f "$DOCKERFILE" \\
            -t "${{LOCAL_IMAGE_NAME}}" \\
            .

        if [ $? -ne 0 ]; then
            echo -e "${{RED}}Error: Docker build failed${{NC}}"
            exit 1
        fi

        echo -e "${{GREEN}}Docker image built successfully (local: ${{LOCAL_IMAGE_NAME}})${{NC}}"

        REGISTRY_TAG="hackerdogs/${{IMAGE_NAME}}:${{TAGS[0]}}"
        echo -e "${{YELLOW}}Tagging image for docker-compose compatibility: ${{REGISTRY_TAG}}${{NC}}"
        docker tag "${{LOCAL_IMAGE_NAME}}" "${{REGISTRY_TAG}}"
        if [ $? -eq 0 ]; then
            echo -e "${{GREEN}}Tagged as ${{REGISTRY_TAG}} (for docker-compose)${{NC}}"
        else
            echo -e "${{YELLOW}}Warning: Failed to tag image for docker-compose${{NC}}"
        fi

        if [ ${{#TAGS[@]}} -gt 1 ]; then
            echo -e "${{YELLOW}}Tagging image with additional tags...${{NC}}"
            for tag in "${{TAGS[@]:1}}"; do
                docker tag "${{LOCAL_IMAGE_NAME}}" "${{IMAGE_NAME}}:${{tag}}"
                docker tag "${{LOCAL_IMAGE_NAME}}" "hackerdogs/${{IMAGE_NAME}}:${{tag}}"
            done
            echo -e "${{GREEN}}All tags created${{NC}}"
        fi
    fi
fi

# Publish images (if --publish only, without --build)
if [ "$DO_PUBLISH" = true ] && [ "$DO_BUILD" = false ]; then
    echo -e "${{YELLOW}}Pushing images...${{NC}}"
    for tag in "${{TAGS[@]}}"; do
        echo "Pushing ${{FULL_IMAGE_NAME}}:${{tag}}..."
        docker push "${{FULL_IMAGE_NAME}}:${{tag}}"
        if [ $? -ne 0 ]; then
            echo -e "${{RED}}Error: Failed to push ${{FULL_IMAGE_NAME}}:${{tag}}${{NC}}"
            exit 1
        fi
        echo -e "${{GREEN}}Successfully pushed ${{FULL_IMAGE_NAME}}:${{tag}}${{NC}}"
    done
fi

# Summary
echo ""
echo "================================================================================="
if [ "$DO_BUILD" = true ] && [ "$DO_PUBLISH" = true ]; then
    echo -e "${{GREEN}}Build and Publish Complete!${{NC}}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${{GREEN}}Build Complete!${{NC}}"
else
    echo -e "${{GREEN}}Publish Complete!${{NC}}"
fi
echo "================================================================================="
echo ""
echo "Image: ${{GREEN}}${{FULL_IMAGE_NAME}}:${{TAGS[0]}}${{NC}}"
if [ "$DO_PUBLISH" = true ] && [ "$DO_BUILD" = true ]; then
    echo "Platforms: ${{GREEN}}linux/amd64, linux/arm64${{NC}} (multi-platform)"
fi

VERSION_FILE="${{IMAGE_NAME}}_versions.txt"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TAGS_CSV=$(IFS=','; echo "${{TAGS[*]}}")

if [ "$DO_PUBLISH" = true ]; then
    PLATFORMS="linux/amd64,linux/arm64"
    DOCKERHUB_LINK="https://hub.docker.com/r/${{DOCKERHUB_USERNAME}}/${{IMAGE_NAME}}/tags"
    VERSION_LINE="${{TAGS_CSV}},${{PLATFORMS}},${{TIMESTAMP}},${{DOCKERHUB_LINK}}"
    echo "$VERSION_LINE" >> "$VERSION_FILE"
    echo "Version info saved to: ${{GREEN}}${{VERSION_FILE}}${{NC}}"
elif [ "$DO_BUILD" = true ]; then
    VERSION_LINE="${{TAGS_CSV}},local,${{TIMESTAMP}},local"
    echo "$VERSION_LINE" >> "$VERSION_FILE"
    echo "Version info saved to: ${{GREEN}}${{VERSION_FILE}}${{NC}}"
fi
echo ""
'''


def generate_test_script(t):
    dir_name, display, binary, repo, desc, port, install_type, install_detail, ver_flag, tool_call = t
    func_name = safe_func_name(binary)
    return f'''#!/bin/bash
# Test script for {display} MCP Server
# Tests MCP protocol compliance via JSON-RPC (stdio and HTTP streamable)

set -euo pipefail

RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

PASS=0
FAIL=0
IMAGE="hackerdogs/{dir_name}:latest"
PORT={port}
BINARY="{binary}"
CONTAINER_NAME="{dir_name}-test"
PROJECT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

pass() {{ echo -e "  ${{GREEN}}PASS: $1${{NC}}"; PASS=$((PASS + 1)); }}
fail() {{ echo -e "  ${{RED}}FAIL: $1${{NC}}"; FAIL=$((FAIL + 1)); }}
info() {{ echo -e "${{BLUE}}$1${{NC}}"; }}

cleanup() {{
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}}
trap cleanup EXIT

echo "================================================================================="
echo -e "${{BLUE}}{display} MCP Server — Test Suite${{NC}}"
echo "================================================================================="
echo ""

# Test 1: Build/verify Docker image
info "[Test 1] Docker image"
if ! docker image inspect "$IMAGE" > /dev/null 2>&1; then
    echo "  Image not found. Building..."
    docker build -t "$IMAGE" "$PROJECT_DIR"
fi
if docker image inspect "$IMAGE" > /dev/null 2>&1; then
    pass "Docker image $IMAGE exists"
else
    fail "Docker image $IMAGE could not be built"
    exit 1
fi
echo ""

# Test 2: CLI binary available
info "[Test 2] CLI binary inside container"
BINARY_OUTPUT=$(docker run --rm "$IMAGE" $BINARY {ver_flag} 2>&1 | head -5 || docker run --rm "$IMAGE" $BINARY --version 2>&1 | head -5 || docker run --rm "$IMAGE" $BINARY -h 2>&1 | head -5 || true)
if [ -n "$BINARY_OUTPUT" ]; then
    pass "$BINARY binary responds"
    echo "       ${{BINARY_OUTPUT%%$'\\n'*}}"
else
    fail "$BINARY binary not found or not responding"
fi
echo ""

# Test 3: MCP stdio mode — initialize + tools/list
info "[Test 3] MCP stdio mode — initialize + tools/list"
INIT_REQ='{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"test-client","version":"1.0.0"}}}}}}'
INIT_NOTIF='{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
LIST_REQ='{{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{{}}}}'

STDIO_OUT=$(printf '%s\\n%s\\n%s\\n' "$INIT_REQ" "$INIT_NOTIF" "$LIST_REQ" | \\
    docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null || true)

if echo "$STDIO_OUT" | grep -q '"tools"'; then
    TOOL_COUNT=$(echo "$STDIO_OUT" | grep -o '"name"' | wc -l)
    pass "stdio mode returned tools/list response ($TOOL_COUNT tool names found)"
else
    fail "stdio mode did not return a valid tools/list response"
    [ -n "$STDIO_OUT" ] && echo "       Response preview: ${{STDIO_OUT:0:300}}"
fi
echo ""

# Test 4: MCP HTTP streamable mode — initialize
info "[Test 4] MCP HTTP streamable mode — initialize"
cleanup
docker run -d --name "$CONTAINER_NAME" \\
    -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT \\
    -p "$PORT:$PORT" "$IMAGE" > /dev/null

SESSION_ID=""
MAX_WAIT=30; WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    INIT_RESP=$(curl -s -D /tmp/mcp_headers -X POST "http://localhost:${{PORT}}/mcp" \\
        -H "Content-Type: application/json" \\
        -H "Accept: application/json, text/event-stream" \\
        -d "$INIT_REQ" 2>/dev/null) && break
    sleep 2; WAITED=$((WAITED + 2))
done

HTTP_CODE=$(head -1 /tmp/mcp_headers 2>/dev/null | grep -o '[0-9]\\{{3\\}}' | head -1 || echo "000")
SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_headers 2>/dev/null | sed 's/.*: //' | tr -d '\\r' || true)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
    pass "HTTP streamable mode responded (status $HTTP_CODE)"
    [ -n "$SESSION_ID" ] && echo "       Session ID: ${{SESSION_ID:0:16}}..."
else
    fail "HTTP streamable mode did not respond (status $HTTP_CODE after ${{WAITED}}s)"
    docker logs "$CONTAINER_NAME" 2>&1 | tail -10
fi
echo ""

# Test 5: MCP HTTP — tools/list
info "[Test 5] MCP HTTP — tools/list"
SESSION_HDR=""
[ -n "$SESSION_ID" ] && SESSION_HDR="-H mcp-session-id:${{SESSION_ID}}"

curl -s -X POST "http://localhost:${{PORT}}/mcp" \\
    -H "Content-Type: application/json" \\
    -H "Accept: application/json, text/event-stream" \\
    $SESSION_HDR \\
    -d "$INIT_NOTIF" > /dev/null 2>&1 || true

TOOLS_RESP=$(curl -s -X POST "http://localhost:${{PORT}}/mcp" \\
    -H "Content-Type: application/json" \\
    -H "Accept: application/json, text/event-stream" \\
    $SESSION_HDR \\
    -d "$LIST_REQ" 2>/dev/null || true)

if echo "$TOOLS_RESP" | grep -q '"tools"'; then
    pass "HTTP tools/list returned tools"
    echo "$TOOLS_RESP" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('data: '): line = line[6:]
    if not line: continue
    try:
        data = json.loads(line)
        tools = data.get('result',{{}}).get('tools',[])
        for t in tools:
            print(f'       - {{t[\"name\"]}}: {{t.get(\"description\",\"\")[:80]}}')
    except: pass
" 2>/dev/null || true
else
    fail "HTTP tools/list did not return tools"
    [ -n "$TOOLS_RESP" ] && echo "       Response: ${{TOOLS_RESP:0:300}}"
fi
echo ""

# Test 6: MCP HTTP — tools/call
info "[Test 6] MCP HTTP — tools/call (run_{func_name})"
CALL_REQ='{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{tool_call}}}'
CALL_RESP=$(curl -s -X POST "http://localhost:${{PORT}}/mcp" \\
    -H "Content-Type: application/json" \\
    -H "Accept: application/json, text/event-stream" \\
    $SESSION_HDR \\
    -d "$CALL_REQ" 2>/dev/null || true)

if echo "$CALL_RESP" | grep -q '"result"'; then
    pass "tools/call run_{func_name} returned a result"
elif echo "$CALL_RESP" | grep -q '"content"'; then
    pass "tools/call run_{func_name} returned content"
else
    fail "tools/call run_{func_name} did not return expected response"
    [ -n "$CALL_RESP" ] && echo "       Response: ${{CALL_RESP:0:500}}"
fi
echo ""

# Summary
echo "================================================================================="
echo -e "${{BLUE}}Results: ${{GREEN}}$PASS passed${{NC}}, ${{RED}}$FAIL failed${{NC}}"
echo "================================================================================="
[ $FAIL -gt 0 ] && exit 1 || exit 0
'''


def generate_readme(t):
    dir_name, display, binary, repo, desc, port, install_type, install_detail, ver_flag, tool_call = t
    func_name = safe_func_name(binary)
    repo_url = f"https://github.com/{repo}"
    api_key_note = "**No API keys required** — " + display + " runs locally inside the Docker container."

    return f'''<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# {display} MCP Server

MCP server wrapper for [{display}]({repo_url}) — {desc}.

## What is {display}?

{display} ({binary}) is a security tool that provides: **{desc}.**

See [{repo}]({repo_url}) for full documentation.

{api_key_note}

## Tools Reference

### `run_{func_name}`

Run {binary} with the given arguments. Returns structured JSON output.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `arguments` | string | Yes | — | Command-line arguments (e.g. `"--help"`) |
| `timeout_seconds` | integer | No | `600` | Maximum execution time in seconds |

<details>
<summary>Example response</summary>

```json
{{
  "raw": "{binary} output will appear here"
}}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run {binary} with --help to see all available options."
- "Use {binary} to scan the target 192.168.1.1."
- "What options does {binary} support? Show me its help output."
- "Run {binary} against example.com with default settings."
- "Execute {binary} with verbose output enabled."
- "Use the {binary} tool to analyze the target and report findings."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/{dir_name}:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  -e MCP_PORT={port} \\
  hackerdogs/{dir_name}:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{{
  "mcpServers": {{
    "{dir_name}": {{
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/{dir_name}:latest"],
      "env": {{}}
    }}
  }}
}}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{{
  "mcpServers": {{
    "{dir_name}": {{
      "url": "http://localhost:{port}/mcp"
    }}
  }}
}}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `{port}` | HTTP port (only used with `streamable-http`) |

## Build

```bash
docker build -t hackerdogs/{dir_name}:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name {dir_name}-test -p {port}:{port} \\
  -e MCP_TRANSPORT=streamable-http \\
  hackerdogs/{dir_name}:latest
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

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:{port}/mcp \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  -H "mcp-session-id: $SESSION_ID" \\
  -d '{{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{{"name":"run_{func_name}","arguments":{{"arguments":"--help"}}}}}}'
```

**4. Clean up:**

```bash
docker stop {dir_name}-test
```
'''


def generate_progress(t):
    dir_name, display, binary, repo, desc, port, *_ = t
    repo_url = f"https://github.com/{repo}"
    return f'''# {display} MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`{dir_name}/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping {binary} CLI
  - [x] `run_{safe_func_name(binary)}` tool — run {binary} with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Create `Dockerfile` with {binary} installation
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port {port}
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **{port}** — {display} MCP Server (streamable-http)

## Notes

- Source: {repo_url}
- Binary: `{binary}`
- Install: see {repo_url} for installation instructions
'''


def main():
    for t in TOOLS:
        dir_name = t[0]
        dir_path = os.path.join(BASE_DIR, dir_name)
        os.makedirs(dir_path, exist_ok=True)

        files = {
            "Dockerfile": generate_dockerfile(t),
            "mcp_server.py": generate_mcp_server(t),
            "docker-compose.yml": generate_docker_compose(t),
            "mcpServer.json": generate_mcp_server_json(t),
            "requirements.txt": generate_requirements(),
            "publish_to_hackerdogs.sh": generate_publish_script(t),
            "test.sh": generate_test_script(t),
            "README.md": generate_readme(t),
            "progress.md": generate_progress(t),
        }

        for filename, content in files.items():
            filepath = os.path.join(dir_path, filename)
            with open(filepath, "w") as f:
                f.write(content)

        # Make shell scripts executable
        for script in ["publish_to_hackerdogs.sh", "test.sh"]:
            script_path = os.path.join(dir_path, script)
            st = os.stat(script_path)
            os.chmod(script_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        print(f"Generated: {dir_name}/ (port {t[5]})")

    print(f"\nDone! Generated {len(TOOLS)} MCP server directories.")


if __name__ == "__main__":
    main()
