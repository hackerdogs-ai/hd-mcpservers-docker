# Autonomous Threat Exposure Management — Use Cases

> Adversarial path modeling across traditional and AI infrastructure using orchestrated security tooling.

This document defines high-impact, multi-tool use cases that power the core capabilities of the platform:

| Capability | Question Answered |
|---|---|
| **Outside-In Exposure** | How does a hacker see us from the outside, and how might they penetrate? |
| **Lateral Movement Modeling** | Once inside, how can a hacker navigate through our infrastructure? |
| **Mitigation & Containment** | How do we prioritize remediation and contain active threats? |

---

## Tool Inventory (17 Tools, 45 Endpoints)

| Tool | Category | What It Does |
|---|---|---|
| **cloudlist** | Asset Discovery | Enumerates assets across AWS, GCP, Azure, and other cloud providers |
| **asnmap** | Network Intelligence | Maps organization network ranges from ASN, IP, domain, and org lookups |
| **tldfinder** | Domain Discovery | Discovers TLDs and subdomains via passive and active DNS sources |
| **dnsx** | DNS Resolution | Multi-record DNS resolution (A, AAAA, CNAME, MX, TXT, NS, SOA, PTR) and subdomain brute-forcing |
| **uncover** | Internet Reconnaissance | Discovers exposed hosts via Shodan, Censys, FOFA, and other search engines |
| **urlfinder** | URL Intelligence | Passive URL discovery from Wayback Machine, Common Crawl, and other archives |
| **naabu** | Port Scanning | Fast SYN/CONNECT/UDP port scanning across hosts |
| **nerva** | Service Fingerprinting | Identifies 120+ network services and versions on open ports |
| **tlsx** | TLS/Certificate Analysis | Scans TLS configurations, certificates, SANs, JARM/JA3 fingerprints, and misconfigurations |
| **wappalyzergo** | Web Tech Detection | Fingerprints web technologies — frameworks, CMS, servers, libraries |
| **julius** | AI Service Fingerprinting | Detects and fingerprints exposed LLM services (Ollama, vLLM, LiteLLM, TGI) |
| **augustus** | AI Adversarial Testing | Tests LLMs for prompt injection, jailbreaks, and adversarial vulnerabilities (210+ probes) |
| **cvemap** | CVE Intelligence | Searches, filters, and analyzes CVEs by product, vendor, severity, and CVSS |
| **vulnx** | Vulnerability Analysis | Advanced vulnerability search and correlation (successor to cvemap) |
| **openrisk** | Risk Scoring | AI-powered risk scoring and remediation recommendations for scan findings |
| **titus** | Secret Detection | Detects leaked secrets in source code and git history using 459 detection rules |
| **brutus** | Credential Testing | Tests credentials across 24 protocols (SSH, RDP, MySQL, Redis, SMB, etc.) |

---

## Use Case 1: Full-Spectrum External Attack Surface Mapping

**Capability:** Outside-In Exposure — _"How does a hacker see us from the outside?"_

**Business Impact:** Provides complete visibility into every asset, service, and entry point an external attacker can discover — the foundational step for adversarial path modeling.

### Tools Chain

```
                    Organization Name / Seed Domains
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
    ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
    │  cloudlist     │  │  asnmap       │  │  uncover      │
    │  Cloud assets  │  │  ASN/IP/Org   │  │  Shodan/      │
    │  AWS/GCP/Azure │  │  network maps │  │  Censys/FOFA  │
    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               ▼
              ┌────────────────────────────────┐
              │  tldfinder                     │
              │  TLD + subdomain discovery     │
              │  (passive + active DNS)        │
              └───────────────┬────────────────┘
                              ▼
              ┌────────────────────────────────┐
              │  dnsx                          │
              │  DNS resolution + brute-force  │
              │  A/AAAA/CNAME/MX/TXT/NS/SOA   │
              └───────────────┬────────────────┘
                              ▼
              ┌────────────────────────────────┐
              │  naabu                         │
              │  Port scanning (SYN/CONNECT)   │
              │  Discover open services        │
              └───────────────┬────────────────┘
                              ▼
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
    ┌───────────────┐ ┌──────────────┐ ┌──────────────┐
    │  nerva        │ │  tlsx        │ │ wappalyzergo │
    │  Service      │ │  TLS/cert    │ │  Web tech    │
    │  fingerprint  │ │  analysis    │ │  detection   │
    └───────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             ▼
              ┌────────────────────────────────┐
              │  urlfinder                     │
              │  Historical URL discovery      │
              │  (Wayback, Common Crawl)       │
              └───────────────┬────────────────┘
                              ▼
              ┌────────────────────────────────┐
              │  cvemap + vulnx                │
              │  CVE correlation against       │
              │  discovered tech stacks        │
              └───────────────┬────────────────┘
                              ▼
              ┌────────────────────────────────┐
              │  openrisk                      │
              │  AI risk scoring + adversarial │
              │  path prioritization           │
              └────────────────────────────────┘
```

### Output: Attack Surface Report

| Section | Content |
|---|---|
| **Asset Inventory** | All domains, subdomains, IPs, cloud resources, and historical URLs |
| **Network Topology** | ASN mappings, IP ranges, DNS hierarchy |
| **Service Map** | Open ports, identified services and versions, web technologies |
| **Certificate Landscape** | TLS versions, certificate chains, SANs, expiration, JARM fingerprints |
| **Vulnerability Overlay** | CVEs mapped to discovered tech stacks, ranked by exploitability |
| **Risk-Prioritized Entry Points** | AI-scored adversarial paths from internet to internal services |

### Adversarial Path Example

```
Attacker discovers org via asnmap → finds forgotten subdomain via tldfinder
→ resolves to IP via dnsx → discovers open port 8080 via naabu → identifies
Apache Tomcat 9.0.30 via nerva + wappalyzergo → matches CVE-2020-1938
(GhostCat, CVSS 9.8) via cvemap → openrisk scores critical entry point
→ ADVERSARIAL PATH: Internet → subdomain → Tomcat → file read/RCE
```

---

## Use Case 2: AI Infrastructure Threat Assessment

**Capability:** Outside-In Exposure + Adversarial Testing — _"Are our AI/LLM services exposed, and can they be exploited?"_

**Business Impact:** As organizations deploy LLMs, exposed inference endpoints become high-value targets. This use case discovers shadow AI deployments, fingerprints them, and tests for adversarial exploitation — a threat vector most security programs miss entirely.

### Tools Chain

```
              Organization IP Ranges / Domains
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────┐
    │  uncover     │ │  naabu   │ │  dnsx    │
    │  Search for  │ │  Scan    │ │  Resolve │
    │  exposed LLM │ │  common  │ │  AI-     │
    │  endpoints   │ │  LLM     │ │  related │
    │  (Shodan/    │ │  ports   │ │  subdoms │
    │  Censys)     │ │          │ │          │
    └──────┬───────┘ └────┬─────┘ └────┬─────┘
           │              │            │
           └──────────────┼────────────┘
                          ▼
            ┌──────────────────────────────┐
            │  julius                      │
            │  LLM service fingerprinting  │
            │  Ollama / vLLM / LiteLLM /   │
            │  TGI / OpenAI-compatible     │
            └─────────────┬────────────────┘
                          ▼
            ┌──────────────────────────────┐
            │  wappalyzergo                │
            │  Detect AI frameworks,       │
            │  Gradio, Streamlit, etc.     │
            └─────────────┬────────────────┘
                          ▼
            ┌──────────────────────────────┐
            │  augustus                     │
            │  Adversarial LLM testing     │
            │  210+ probes:                │
            │  • Prompt injection          │
            │  • Jailbreaks                │
            │  • Data exfiltration         │
            │  • Encoding bypasses         │
            └─────────────┬────────────────┘
                          ▼
            ┌──────────────────────────────┐
            │  cvemap + vulnx              │
            │  CVEs on LLM frameworks      │
            │  (e.g., Ollama RCE, vLLM     │
            │  SSRF, LangChain injection)  │
            └─────────────┬────────────────┘
                          ▼
            ┌──────────────────────────────┐
            │  openrisk                    │
            │  AI-specific risk scoring    │
            │  + remediation guidance      │
            └──────────────────────────────┘
```

### Output: AI Threat Exposure Report

| Section | Content |
|---|---|
| **Exposed AI Services** | All discovered LLM/AI endpoints, models served, API versions |
| **Shadow AI Deployments** | Unregistered or developer-deployed AI services |
| **Adversarial Vulnerabilities** | Prompt injection success rates, jailbreak vectors, data leak paths |
| **Framework CVEs** | Known vulnerabilities in detected AI frameworks |
| **Risk Assessment** | Scored risk per endpoint with remediation priorities |

### Adversarial Path Example

```
uncover finds Ollama on port 11434 exposed to internet → julius confirms
Ollama v0.1.29 serving llama2 → augustus discovers prompt injection allowing
system prompt extraction → extracted system prompt reveals internal API
endpoints and credentials → cvemap matches CVE-2024-39720 (Ollama RCE)
→ ADVERSARIAL PATH: Internet → Ollama API → prompt injection → credential
leak → internal API access → potential RCE
```

---

## Use Case 3: Credential & Secret Exposure Assessment

**Capability:** Lateral Movement Modeling — _"What credentials are exposed that let an attacker move through our systems?"_

**Business Impact:** Leaked secrets are the #1 enabler of lateral movement. This use case discovers exposed credentials in code, validates them against live services, and maps the blast radius of each leaked secret.

### Tools Chain

```
           Code Repositories / Git History / URLs
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
    ┌─────────────┐ ┌──────────┐ ┌───────────┐
    │  titus      │ │ urlfinder│ │  uncover  │
    │  Scan code  │ │ Historical│ │ Search for│
    │  + git for  │ │ URLs with │ │ exposed   │
    │  secrets    │ │ tokens/  │ │ admin     │
    │  (459 rules)│ │ keys     │ │ panels    │
    └──────┬──────┘ └────┬─────┘ └─────┬─────┘
           │             │             │
           └─────────────┼─────────────┘
                         ▼
           ┌──────────────────────────────┐
           │  Credential Correlation      │
           │  Deduplicate & classify:     │
           │  • API keys (cloud, SaaS)    │
           │  • DB connection strings     │
           │  • SSH keys / passwords      │
           │  • OAuth tokens              │
           │  • JWT secrets               │
           └─────────────┬────────────────┘
                         ▼
           ┌──────────────────────────────┐
           │  dnsx + naabu                │
           │  Resolve targets where       │
           │  credentials may be valid    │
           │  + verify ports are open     │
           └─────────────┬────────────────┘
                         ▼
           ┌──────────────────────────────┐
           │  brutus                      │
           │  Test credentials across     │
           │  24 protocols:               │
           │  SSH, RDP, MySQL, Redis,     │
           │  PostgreSQL, MSSQL, SMB,     │
           │  FTP, LDAP, Telnet, etc.     │
           └─────────────┬────────────────┘
                         ▼
           ┌──────────────────────────────┐
           │  nerva                       │
           │  Fingerprint services on     │
           │  validated credential        │
           │  targets (assess blast       │
           │  radius)                     │
           └─────────────┬────────────────┘
                         ▼
           ┌──────────────────────────────┐
           │  openrisk                    │
           │  Score blast radius per      │
           │  leaked credential           │
           └──────────────────────────────┘
```

### Output: Credential Exposure Report

| Section | Content |
|---|---|
| **Leaked Secrets** | All discovered secrets by type, source, and commit/file |
| **Validated Credentials** | Secrets confirmed active against live services |
| **Blast Radius Map** | Per-credential: which systems, protocols, and data are reachable |
| **Lateral Movement Paths** | Chains of credentials that enable pivoting across systems |
| **Remediation Priority** | Ranked by exposure × blast radius × data sensitivity |

### Adversarial Path Example

```
titus finds AWS_SECRET_ACCESS_KEY in git history (commit 3 months ago)
→ urlfinder discovers old staging URL with .env file → .env contains
Redis password + DB connection string → dnsx resolves staging host
→ naabu confirms ports 6379 (Redis) + 5432 (Postgres) open → brutus
validates Redis password works → nerva shows Redis 6.2 with no ACL
→ ADVERSARIAL PATH: GitHub leak → AWS credentials → staging env →
Redis (unauthenticated write) → potential SSRF/RCE via Redis modules
→ PostgreSQL access → customer data exfiltration
```

---

## Use Case 4: Cloud-to-Perimeter Adversarial Path Modeling

**Capability:** Outside-In + Lateral Movement — _"How does our cloud footprint create exploitable attack paths?"_

**Business Impact:** Cloud misconfigurations are the fastest-growing attack vector. This use case maps the path from cloud asset discovery through to exploitable services, identifying where cloud-specific weaknesses (public S3 buckets, exposed APIs, misconfigured security groups) create adversarial paths.

### Tools Chain

```
                  Cloud Provider Credentials
                           │
                           ▼
              ┌────────────────────────────┐
              │  cloudlist                 │
              │  Enumerate ALL cloud       │
              │  assets across providers:  │
              │  • AWS (EC2, ELB, S3, RDS) │
              │  • GCP (GCE, GKE, Cloud    │
              │    Functions)              │
              │  • Azure (VMs, AKS, etc.)  │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  asnmap                    │
              │  Map cloud IPs to ASN      │
              │  ownership — identify      │
              │  which assets belong to    │
              │  the org vs third-party    │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  dnsx                      │
              │  Resolve all cloud DNS     │
              │  records — find dangling   │
              │  DNS (subdomain takeover)  │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  naabu                     │
              │  Port scan cloud hosts     │
              │  — find unexpected open    │
              │  ports (security group     │
              │  misconfigs)               │
              └────────────┬───────────────┘
                           ▼
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │  nerva       │ │  tlsx    │ │ wappalyzergo │
    │  Service     │ │  TLS     │ │  Web stack   │
    │  versions    │ │  config  │ │  detection   │
    └──────┬───────┘ └────┬─────┘ └──────┬───────┘
           │              │              │
           └──────────────┼──────────────┘
                          ▼
              ┌────────────────────────────┐
              │  vulnx                     │
              │  Vulnerability matching    │
              │  against discovered cloud  │
              │  service versions          │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  openrisk                  │
              │  Risk scoring with cloud-  │
              │  context prioritization    │
              └────────────────────────────┘
```

### Output: Cloud Attack Path Report

| Section | Content |
|---|---|
| **Cloud Asset Inventory** | All assets per provider, region, and service type |
| **Ownership Validation** | ASN-verified asset ownership, third-party dependencies |
| **DNS Hygiene** | Dangling DNS records, subdomain takeover risks |
| **Exposed Services** | Unexpected open ports on cloud hosts (security group audit) |
| **Service + TLS Audit** | Versions, TLS configs, certificate issues per cloud service |
| **Cloud-Specific Attack Paths** | Ranked adversarial paths through cloud infrastructure |

### Adversarial Path Example

```
cloudlist enumerates 847 AWS assets → asnmap confirms 12 IPs outside
known org ranges (shadow infrastructure) → dnsx finds CNAME pointing
to decommissioned S3 bucket (subdomain takeover) → naabu discovers
port 9200 (Elasticsearch) open on an EC2 instance → nerva confirms
Elasticsearch 7.10 with no auth → wappalyzergo finds Kibana dashboard
→ vulnx matches CVE-2021-22145 (info disclosure) → openrisk scores
critical path → ADVERSARIAL PATH: Subdomain takeover → phishing
landing page + Elasticsearch → unauthenticated data access → sensitive
log data (PII, tokens) → lateral movement via leaked tokens
```

---

## Use Case 5: TLS & Cryptographic Weakness Discovery

**Capability:** Outside-In Exposure + Mitigation — _"Where are our cryptographic weaknesses that attackers can exploit?"_

**Business Impact:** Weak TLS, expired certificates, and misconfigured crypto create MITM opportunities, trust chain breakdowns, and compliance violations. This use case systematically identifies all cryptographic weaknesses across the entire infrastructure.

### Tools Chain

```
                    Organization Domains
                           │
                           ▼
              ┌────────────────────────────┐
              │  tldfinder                 │
              │  Discover all domains      │
              │  and subdomains            │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  dnsx                      │
              │  Resolve all discovered    │
              │  domains to IPs            │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  naabu                     │
              │  Scan for TLS-enabled      │
              │  ports (443, 8443, etc.)   │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  tlsx                      │
              │  Deep TLS analysis:        │
              │  • Certificate chains      │
              │  • SAN enumeration         │
              │  • JARM fingerprinting     │
              │  • JA3 signatures          │
              │  • Version enumeration     │
              │  • Cipher suite audit      │
              │  • Expired certs           │
              │  • Self-signed certs       │
              │  • Hostname mismatches     │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  wappalyzergo              │
              │  Identify web servers and  │
              │  frameworks (correlate     │
              │  with TLS configs)         │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  vulnx                     │
              │  Match CVEs against TLS    │
              │  implementations           │
              │  (OpenSSL, GnuTLS, etc.)   │
              └────────────┬───────────────┘
                           ▼
              ┌────────────────────────────┐
              │  openrisk                  │
              │  Risk score crypto         │
              │  weaknesses + compliance   │
              │  impact assessment         │
              └────────────────────────────┘
```

### Output: Cryptographic Posture Report

| Section | Content |
|---|---|
| **Certificate Inventory** | All certificates, issuers, expiration dates, SANs |
| **TLS Configuration Audit** | Protocol versions, cipher suites, known weak configs |
| **JARM/JA3 Fingerprints** | Server/client fingerprints for threat intel correlation |
| **Misconfigurations** | Expired, self-signed, hostname-mismatched, and weak-key certs |
| **CVE Exposure** | Vulnerabilities in TLS libraries and implementations |
| **Compliance Impact** | PCI-DSS, HIPAA, SOC 2 implications of findings |

### Adversarial Path Example

```
tldfinder discovers 340 subdomains → dnsx resolves 280 live hosts
→ naabu finds 45 hosts with port 443 open → tlsx reveals 3 hosts
using TLS 1.0 + RC4 cipher, 7 expired certificates, 2 self-signed
→ wappalyzergo identifies nginx/1.14 on the TLS 1.0 hosts → vulnx
matches CVE-2019-6111 → openrisk flags MITM opportunity
→ ADVERSARIAL PATH: Public WiFi → MITM on TLS 1.0 endpoint →
session hijack → authenticated access → internal API calls
```

---

## Use Case 6: Shadow IT & Unknown Asset Discovery

**Capability:** Outside-In Exposure — _"What assets exist that we don't know about?"_

**Business Impact:** 30-40% of enterprise attack surface is unknown to security teams — developer side projects, acquired company assets, forgotten staging environments, and unauthorized cloud deployments. This use case finds them all.

### Tools Chain

```
                Organization Name + Known Domains
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
    ┌───────────────┐ ┌─────────────┐ ┌──────────┐
    │  asnmap       │ │  uncover    │ │ cloudlist│
    │  Map all ASNs │ │  Search all │ │ Enumerate│
    │  owned by org │ │  internet   │ │ all cloud│
    │  → find ALL   │ │  search     │ │ accounts │
    │  IP ranges    │ │  engines    │ │          │
    └──────┬────────┘ └──────┬──────┘ └────┬─────┘
           │                 │             │
           └─────────────────┼─────────────┘
                             ▼
               ┌──────────────────────────────┐
               │  Compare against known asset  │
               │  inventory → identify UNKNOWN │
               │  assets (shadow IT)           │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  tldfinder + dnsx            │
               │  Expand discovery on unknown │
               │  assets — find related       │
               │  subdomains and DNS records  │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  naabu + nerva               │
               │  Port scan + service         │
               │  fingerprint unknown hosts   │
               └──────────────┬───────────────┘
                              ▼
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────┐
    │ wappalyzergo │  │  julius      │  │  tlsx    │
    │ Web tech     │  │  Is it an    │  │  Cert    │
    │ detection    │  │  LLM service?│  │  analysis │
    └──────┬───────┘  └──────┬───────┘  └────┬─────┘
           │                 │               │
           └─────────────────┼───────────────┘
                             ▼
               ┌──────────────────────────────┐
               │  openrisk                    │
               │  Score risk of each unknown  │
               │  asset — prioritize by       │
               │  exposure + data sensitivity │
               └──────────────────────────────┘
```

### Output: Shadow IT Report

| Section | Content |
|---|---|
| **Unknown Assets** | Assets discovered but not in CMDB/asset inventory |
| **Asset Classification** | Type (web app, API, database, AI service, dev tool) per unknown asset |
| **Owner Attribution** | Best-effort mapping of unknown assets to teams/individuals |
| **Risk Ranking** | Each unknown asset scored by exposure, vulnerabilities, and data access |
| **Governance Gaps** | Cloud accounts, domains, and services outside security governance |

---

## Use Case 7: Vulnerability-to-Exploit Path Prioritization

**Capability:** Mitigation & Containment — _"Which vulnerabilities actually matter and how do we fix them first?"_

**Business Impact:** Organizations face thousands of CVEs. This use case moves beyond CVSS scores to build actual exploit paths — combining live service data, technology stacks, and vulnerability intelligence to prioritize what an attacker would actually exploit.

### Tools Chain

```
           Discovered Infrastructure (from Use Cases 1-6)
                              │
                              ▼
               ┌──────────────────────────────┐
               │  naabu                       │
               │  Verify which ports are      │
               │  currently open (live state) │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  nerva                       │
               │  Fingerprint exact service   │
               │  versions on open ports      │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  wappalyzergo                │
               │  Identify full web tech      │
               │  stack (framework, CMS,      │
               │  libraries with versions)    │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  cvemap                      │
               │  Match CVEs against every    │
               │  discovered version:         │
               │  • Filter by severity        │
               │  • Filter by exploitability  │
               │  • Check for public exploits │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  vulnx                       │
               │  Deep vulnerability analysis │
               │  • Exploit availability      │
               │  • Weaponization status      │
               │  • Threat actor associations │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  tlsx                        │
               │  Check if vulnerable service │
               │  has TLS weaknesses that     │
               │  compound the risk           │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  openrisk                    │
               │  AI-powered exploit path     │
               │  scoring:                    │
               │  • Reachability from internet│
               │  • Exploit maturity          │
               │  • Business data at risk     │
               │  • Compound vulnerability    │
               │    chains                    │
               │                              │
               │  OUTPUT: Prioritized         │
               │  remediation plan            │
               └──────────────────────────────┘
```

### Output: Exploit Path Prioritization Report

| Section | Content |
|---|---|
| **Exploitable Vulnerabilities** | CVEs with confirmed public exploits mapped to live services |
| **Compound Vulnerability Chains** | Multi-vulnerability paths (e.g., info-disclosure → auth-bypass → RCE) |
| **Exploit Path Graph** | Visual adversarial paths from internet to critical data |
| **Prioritized Remediation** | Fix order based on actual risk, not just CVSS |
| **Quick Wins** | Immediate actions (patch, config change, firewall rule) with highest impact |

### Adversarial Path Example

```
naabu confirms 3 hosts with port 8080 open → nerva identifies
Apache Struts 2.5.20 on host-A, Jenkins 2.289 on host-B, Confluence
7.13.0 on host-C → wappalyzergo confirms versions → cvemap finds:
host-A: CVE-2023-50164 (Struts file upload, CVSS 9.8, exploit available)
host-B: CVE-2024-23897 (Jenkins file read, CVSS 9.8, weaponized)
host-C: CVE-2023-22515 (Confluence admin create, CVSS 10.0, active exploit)
→ vulnx confirms all three are weaponized with public PoCs → tlsx shows
host-C uses self-signed cert (no monitoring) → openrisk builds chain:
→ PRIORITY 1: Confluence (unmonitored + CVSS 10 + active exploitation)
→ PRIORITY 2: Jenkins (file read → credential extraction → lateral movement)
→ PRIORITY 3: Struts (RCE but behind WAF, lower reachability)
```

---

## Use Case 8: Continuous Threat Exposure Monitoring

**Capability:** All Three — _"How does our exposure change over time?"_

**Business Impact:** Attack surfaces are not static. This use case orchestrates all tools on a schedule to detect drift — new assets, new vulnerabilities, expired certificates, new credential leaks, and newly exposed services — before attackers find them.

### Scheduled Pipeline

```
    ┌──────────────────────────────────────────────────────┐
    │                 CONTINUOUS MONITORING                 │
    │                                                      │
    │  ┌─────────────┐    Frequency: Daily                 │
    │  │ cloudlist    │    Detect new/removed cloud assets  │
    │  │ asnmap       │    Detect ASN/IP range changes      │
    │  │ tldfinder    │    Detect new subdomains            │
    │  │ uncover      │    Detect newly exposed services    │
    │  └──────┬──────┘                                     │
    │         │                                            │
    │  ┌──────▼──────┐    Frequency: Daily                 │
    │  │ dnsx        │    Detect DNS changes               │
    │  │ naabu       │    Detect new open ports             │
    │  │ nerva       │    Detect service version changes    │
    │  │ julius      │    Detect new AI service deployments │
    │  └──────┬──────┘                                     │
    │         │                                            │
    │  ┌──────▼──────┐    Frequency: Weekly                │
    │  │ tlsx        │    Cert expiration countdown        │
    │  │ wappalyzergo│    Tech stack drift                 │
    │  │ titus       │    New secret leaks                 │
    │  └──────┬──────┘                                     │
    │         │                                            │
    │  ┌──────▼──────┐    Frequency: On-Change             │
    │  │ cvemap      │    New CVEs for our tech stacks     │
    │  │ vulnx       │    New exploit availability         │
    │  └──────┬──────┘                                     │
    │         │                                            │
    │  ┌──────▼──────┐    Frequency: On-Trigger            │
    │  │ brutus      │    Validate new leaked credentials  │
    │  │ augustus     │    Test new AI deployments          │
    │  │ openrisk    │    Re-score on any change           │
    │  └─────────────┘                                     │
    │                                                      │
    │  OUTPUT: Delta reports, alerts, trend dashboards     │
    └──────────────────────────────────────────────────────┘
```

### Delta Alert Examples

| Alert Type | Trigger | Tools |
|---|---|---|
| **New Subdomain** | tldfinder discovers subdomain not in previous scan | tldfinder → dnsx → naabu → nerva |
| **New Open Port** | naabu finds port that was previously closed | naabu → nerva → vulnx → openrisk |
| **Expiring Certificate** | tlsx detects cert expiring within 30 days | tlsx |
| **New CVE Match** | cvemap/vulnx finds new CVE matching our tech stack | cvemap → vulnx → openrisk |
| **Secret Leaked** | titus finds new secret in latest commits | titus → brutus → openrisk |
| **Shadow AI Deployed** | julius detects new LLM endpoint | julius → augustus → openrisk |
| **Cloud Asset Drift** | cloudlist detects new asset not in CMDB | cloudlist → naabu → nerva → openrisk |

---

## Cross-Cutting: Adversarial Path Model

All use cases feed into a unified adversarial path graph that represents the attacker's view:

```
    ┌─────────────────────────────────────────────────────────────────┐
    │                    ADVERSARIAL PATH MODEL                       │
    │                                                                 │
    │   RECONNAISSANCE          INITIAL ACCESS        LATERAL MOVEMENT│
    │   ─────────────          ──────────────        ────────────────│
    │                                                                 │
    │   cloudlist ──┐                                                 │
    │   asnmap ─────┤          ┌─ Exploit CVE ─┐     ┌─ Leaked creds │
    │   tldfinder ──┼── Asset  │  (cvemap/vulnx)│     │  (titus) ────┤
    │   dnsx ───────┤  Map  ──►│               │──►  │              │
    │   uncover ────┤          │  Weak TLS     │     │  Default     │
    │   urlfinder ──┘          │  (tlsx)       │     │  creds ──────┤
    │                          │               │     │  (brutus)    │
    │   naabu ──────┐          │  Prompt       │     │              │
    │   nerva ──────┤  Service │  Injection    │     │  Service     │
    │   tlsx ───────┼── Intel  │  (augustus)    │     │  pivot ──────┤
    │   wappalyzergo┤  ──────►│               │──►  │  (nerva)     │
    │   julius ─────┘          │  Valid creds  │     │              │
    │                          │  (brutus)     │     └──────────────┤
    │   titus ──────┐          └───────────────┘                    │
    │   cvemap ─────┤  Vuln                           IMPACT        │
    │   vulnx ──────┼── Intel ──────────────────►    ────────       │
    │   openrisk ───┘                                 openrisk      │
    │                                                 scores all    │
    │                                                 paths         │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Tool Contribution Matrix

Each tool's role across the three core capabilities:

| Tool | Outside-In Exposure | Lateral Movement | Mitigation & Containment |
|---|:---:|:---:|:---:|
| **cloudlist** | Asset enumeration | Cloud pivot points | Cloud governance gaps |
| **asnmap** | Network range mapping | Org boundary identification | Ownership validation |
| **tldfinder** | Subdomain discovery | Takeover opportunities | DNS hygiene |
| **dnsx** | DNS resolution | Dangling DNS detection | DNS record audit |
| **uncover** | Exposed service discovery | Shadow IT detection | Exposure alerting |
| **urlfinder** | Historical URL intelligence | Leaked endpoint discovery | URL monitoring |
| **naabu** | Port discovery | Internal port scanning | Port drift detection |
| **nerva** | Service fingerprinting | Service version mapping | Version compliance |
| **tlsx** | TLS/cert analysis | MITM opportunity detection | Cert lifecycle mgmt |
| **wappalyzergo** | Tech stack detection | Framework exploit matching | Patch prioritization |
| **julius** | AI service discovery | AI endpoint mapping | AI governance |
| **augustus** | — | LLM exploitation testing | AI security hardening |
| **cvemap** | CVE matching | Exploit chain building | Patch prioritization |
| **vulnx** | Vulnerability correlation | Weaponization tracking | Remediation scoring |
| **openrisk** | Risk scoring | Path risk assessment | Prioritized remediation |
| **titus** | Credential leak detection | Lateral movement enablers | Secret rotation |
| **brutus** | Credential validation | Multi-protocol pivoting | Access control audit |
