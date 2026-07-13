<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
  <br/>
  <a href="https://hackerdogs.ai">
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

---

## Disclaimer

**No liability.** Hackerdogs Inc. does not take any liability for the code in this repository. These MCP servers are provided for **educational purposes only**. Use at your own risk. We do not promise that any tool will work or be fit for any particular purpose.

**By continuing,** you confirm that you will use [Hackerdogs.ai](https://hackerdogs.ai) lawfully, ethically, and responsibly. You acknowledge that the platform provides OSINT intelligence and AI-assisted outputs for informational purposes only, without guarantee of accuracy, and that AI-generated outputs may contain errors, omissions, or biases. Do not enter any private, sensitive, personal, or regulated data. Always apply appropriate human oversight before acting on outputs. You agree not to target minors, private individuals, or protected entities without legal authorization, and not to engage in harassment, doxxing, unauthorized access, or any illegal surveillance. You consent to automated/agentic processing, OSINT analysis, audit logging, and cross‑border data handling as described in our Terms, Privacy Policy, DPA, and Acceptable Use Policy. Content may be used to improve the service. Hackerdogs.ai may suspend accounts for misuse or violations of ethical or legal standards. Your use is subject to applicable international laws (including export controls) and our Shared Responsibility Model.

For more information, see [Hackerdogs Legal & Compliance](https://hackerdogs.ai/legal).

---

### 👉 **[Try Hackerdogs Here For Free](https://preview.hackerdogs.ai)**

---

# hd-mcpservers-docker

Registry of **400 containerized MCP servers** for security, OSINT, cloud, and developer tools, ready for deployment on [Hackerdogs](https://hackerdogs.ai).

Each tool is wrapped as a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server using [FastMCP](https://github.com/jlowin/fastmcp), supporting both **stdio** and **HTTP streamable** transports. All tools are packaged as multi-architecture Docker images (linux/amd64, linux/arm64).

## Table of Contents

- [Installing in Hackerdogs](#installing-in-hackerdogs)
- [Tool Registry](#tool-registry) — all 400 MCP servers
- [Deploy Individual Servers (Without the Farm)](#deploy-individual-servers-without-the-farm)
- [Environment Variables](#environment-variables) · [URL-Based File Ingestion](#url-based-file-ingestion)
- [MCP Farm](#mcp-farm) — local and production Docker deployment
- [Directory Structure](#directory-structure)
- [Publishing](#publishing)
- [Testing](#testing)

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use naabu to scan example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Tool Registry

Complete catalog of all **400** MCP servers registered in [`mcpfarm/port-map.json`](./mcpfarm/port-map.json). Sorted by port. Ports and image names are verified against the farm registry; descriptions and sources are taken from each tool's README when available.

| Category | Count |
|----------|------:|
| misc | 86 |
| cloud-container | 52 |
| network-recon | 52 |
| web-app | 44 |
| osint | 41 |
| binary-re | 31 |
| core | 23 |
| vuln-scanning | 22 |
| appsec | 19 |
| exploitation | 18 |
| network-attacks | 8 |
| recon | 4 |

### All servers (400)

| # | Tool | Source | Description | Port | Image | Category |
|---|------|--------|-------------|------|-------|----------|
| 1 | [julius-mcp](./julius-mcp/) | [Julius](https://github.com/praetorian-inc/julius) | LLM service fingerprinting tool by Praetorian | 8100 | `hackerdogs/julius-mcp` | core |
| 2 | [augustus-mcp](./augustus-mcp/) | [Augustus](https://github.com/praetorian-inc/augustus) | LLM adversarial vulnerability testing with 210+ probes and support for 28 LLM providers | 8101 | `hackerdogs/augustus-mcp` | core |
| 3 | [brutus-mcp](./brutus-mcp/) | [Brutus](https://github.com/praetorian-inc/brutus) | credential testing tool across 24 protocols by Praetorian | 8102 | `hackerdogs/brutus-mcp` | exploitation |
| 4 | [titus-mcp](./titus-mcp/) | [Titus](https://github.com/praetorian-inc/titus) | secret detection tool by Praetorian that scans source code, files, and git history for leaked cre… | 8103 | `hackerdogs/titus-mcp` | core |
| 5 | [nerva-mcp](./nerva-mcp/) | [Nerva](https://github.com/praetorian-inc/nerva) | network service fingerprinting tool by Praetorian | 8104 | `hackerdogs/nerva-mcp` | core |
| 6 | [naabu-mcp](./naabu-mcp/) | [Naabu](https://github.com/projectdiscovery/naabu) | fast port scanner by ProjectDiscovery | 8105 | `hackerdogs/naabu-mcp` | network-recon |
| 7 | [cvemap-mcp](./cvemap-mcp/) | [Cvemap](https://github.com/projectdiscovery/cvemap) | CVE and vulnerability search, filtering, and analysis | 8106 | `hackerdogs/cvemap-mcp` | vuln-scanning |
| 8 | [uncover-mcp](./uncover-mcp/) | [Uncover](https://github.com/projectdiscovery/uncover) | discovers exposed hosts via internet search APIs including Shodan, Censys, FOFA, Hunter, Quake, Z… | 8107 | `hackerdogs/uncover-mcp` | osint |
| 9 | [dnsx-mcp](./dnsx-mcp/) | [DNSx](https://github.com/projectdiscovery/dnsx) | multi-purpose DNS toolkit by ProjectDiscovery | 8108 | `hackerdogs/dnsx-mcp` | network-recon |
| 10 | [tlsx-mcp](./tlsx-mcp/) | [TLSx](https://github.com/projectdiscovery/tlsx) | fast TLS grabber by ProjectDiscovery | 8109 | `hackerdogs/tlsx-mcp` | network-recon |
| 11 | [asnmap-mcp](./asnmap-mcp/) | [Asnmap](https://github.com/projectdiscovery/asnmap) | maps organization network ranges from ASN, IP, domain, and organization lookups for network recon… | 8110 | `hackerdogs/asnmap-mcp` | network-recon |
| 12 | [cloudlist-mcp](./cloudlist-mcp/) | [Cloudlist](https://github.com/projectdiscovery/cloudlist) | lists assets from multiple cloud providers (AWS, GCP, Azure, DigitalOcean, Fastly, etc | 8111 | `hackerdogs/cloudlist-mcp` | cloud-container |
| 13 | [urlfinder-mcp](./urlfinder-mcp/) | [URLFinder](https://github.com/projectdiscovery/urlfinder) | passive URL discovery tool by ProjectDiscovery | 8112 | `hackerdogs/urlfinder-mcp` | web-app |
| 14 | [tldfinder-mcp](./tldfinder-mcp/) | [TLDFinder](https://github.com/projectdiscovery/tldfinder) | TLD and subdomain discovery tool by ProjectDiscovery | 8113 | `hackerdogs/tldfinder-mcp` | network-recon |
| 15 | [wappalyzergo-mcp](./wappalyzergo-mcp/) | [Wappalyzergo](https://github.com/projectdiscovery/wappalyzergo) | web technology detection tool by ProjectDiscovery | 8114 | `hackerdogs/wappalyzergo-mcp` | network-recon |
| 16 | [openrisk-mcp](./openrisk-mcp/) | [OpenRisk](https://github.com/projectdiscovery/openrisk) | generates risk scores from Nuclei scan output using OpenAI GPT-4o for intelligent vulnerability r… | 8115 | `hackerdogs/openrisk-mcp` | core |
| 17 | [vulnx-mcp](./vulnx-mcp/) | [Vulnx](https://github.com/projectdiscovery/vulnx) | next-generation vulnerability search and analysis (successor to cvemap) | 8116 | `hackerdogs/vulnx-mcp` | vuln-scanning |
| 18 | [rustscan-mcp](./rustscan-mcp/) | [Rustscan](https://github.com/RustScan/RustScan) | Ultra-fast port scanning | 8200 | `hackerdogs/rustscan-mcp` | network-recon |
| 19 | [autorecon-mcp](./autorecon-mcp/) | [Autorecon](https://github.com/Tib3rius/AutoRecon) | Automated reconnaissance | 8201 | `hackerdogs/autorecon-mcp` | network-recon |
| 20 | [fierce-mcp](./fierce-mcp/) | [Fierce](https://github.com/msaffron/fierce) | DNS reconnaissance and zone transfer testing | 8202 | `hackerdogs/fierce-mcp` | misc |
| 21 | [dnsrecon-mcp](./dnsrecon-mcp/) | [Dnsrecon](https://github.com/darkoperator/dnsrecon) | DNS information gathering and brute forcing | 8203 | `hackerdogs/dnsrecon-mcp` | network-recon |
| 22 | [theharvester-mcp](./theharvester-mcp/) | [Theharvester](https://github.com/laramies/theHarvester) | Email and subdomain harvesting from multiple sources | 8204 | `hackerdogs/theharvester-mcp` | osint |
| 23 | [arp-scan-mcp](./arp-scan-mcp/) | [Arp Scan](https://github.com/royhills/arp-scan) | Network discovery using ARP requests | 8205 | `hackerdogs/arp-scan-mcp` | network-recon |
| 24 | [nbtscan-mcp](./nbtscan-mcp/) | [Nbtscan](https://github.com/residuum/nbtscan) | NetBIOS name scanning | 8206 | `hackerdogs/nbtscan-mcp` | network-recon |
| 25 | [responder-mcp](./responder-mcp/) | [Responder](https://github.com/lgandx/Responder) | LLMNR/NBT-NS/MDNS poisoner for credential harvesting | 8207 | `hackerdogs/responder-mcp` | exploitation |
| 26 | [crackmapexec-mcp](./crackmapexec-mcp/) | [Crackmapexec](https://github.com/byt3bl33d3r/CrackMapExec) | Network service exploitation (SMB, WinRM, etc | 8208 | `hackerdogs/crackmapexec-mcp` | exploitation |
| 27 | [enum4linux-mcp](./enum4linux-mcp/) | [Enum4Linux](https://github.com/CiscoCXSecurity/enum4linux) | SMB enumeration (users, groups, shares) | 8209 | `hackerdogs/enum4linux-mcp` | network-recon |
| 28 | [enum4linux-ng-mcp](./enum4linux-ng-mcp/) | [Enum4Linux Ng](https://github.com/cddmp/enum4linux-ng) | Advanced SMB enumeration with enhanced logging | 8210 | `hackerdogs/enum4linux-ng-mcp` | network-recon |
| 29 | [smbmap-mcp](./smbmap-mcp/) | [Smbmap](https://github.com/ShaunBarton/smbmap) | SMB share enumeration and exploitation | 8211 | `hackerdogs/smbmap-mcp` | network-recon |
| 30 | [netexec-mcp](./netexec-mcp/) | [Netexec](https://github.com/PwnDexter/NetExec) | Network service exploitation (formerly CrackMapExec) | 8212 | `hackerdogs/netexec-mcp` | exploitation |
| 31 | [gobuster-mcp](./gobuster-mcp/) | [Gobuster](https://github.com/OWASP/gobuster) | Directory/file/DNS enumeration for web and vhosts | 8213 | `hackerdogs/gobuster-mcp` | web-app |
| 32 | [dirb-mcp](./dirb-mcp/) | [Dirb](https://github.com/darkoperator/dirb) | Web content scanner with recursive scanning | 8214 | `hackerdogs/dirb-mcp` | web-app |
| 33 | [dirsearch-mcp](./dirsearch-mcp/) | [Dirsearch](https://github.com/maurosoria/dirsearch) | Directory and file discovery | 8215 | `hackerdogs/dirsearch-mcp` | web-app |
| 34 | [dnsdumpster-mcp](./dnsdumpster-mcp/) | [API-dnsdumpster.com](https://github.com/PaulSec/API-dnsdumpster.com) | Passive DNS reconnaissance and subdomain enumeration | 8216 | `hackerdogs/dnsdumpster-mcp` | network-recon |
| 35 | [hakrawler-mcp](./hakrawler-mcp/) | [Hakrawler](https://github.com/hakluke/hakrawler) | Fast web endpoint discovery and crawling | 8217 | `hackerdogs/hakrawler-mcp` | web-app |
| 36 | [gau-mcp](./gau-mcp/) | [Gau](https://github.com/lc/gau) | Get All URLs (Wayback, Common Crawl, etc | 8218 | `hackerdogs/gau-mcp` | web-app |
| 37 | [holehe-mcp](./holehe-mcp/) | [Holehe](https://github.com/megadose/holehe) | Check email registration across 120+ websites | 8219 | `hackerdogs/holehe-mcp` | osint |
| 38 | [blackbird-mcp](./blackbird-mcp/) | [Blackbird](https://github.com/p1ngul1n0/blackbird) | Username OSINT search across 500+ sites | 8220 | `hackerdogs/blackbird-mcp` | osint |
| 39 | [dalfox-mcp](./dalfox-mcp/) | [Dalfox](https://github.com/hahwul/dalfox) | XSS vulnerability scanning with DOM analysis | 8221 | `hackerdogs/dalfox-mcp` | web-app |
| 40 | [xsser-mcp](./xsser-mcp/) | [Xsser](https://github.com/epsylon/xsser) | XSS vulnerability testing | 8222 | `hackerdogs/xsser-mcp` | web-app |
| 41 | [dotdotpwn-mcp](./dotdotpwn-mcp/) | [Dotdotpwn](https://github.com/wireghoul/dotdotpwn) | Directory traversal testing | 8223 | `hackerdogs/dotdotpwn-mcp` | web-app |
| 42 | [wfuzz-mcp](./wfuzz-mcp/) | [Wfuzz](https://github.com/xmendez/wfuzz) | Web application fuzzer | 8224 | `hackerdogs/wfuzz-mcp` | web-app |
| 43 | [commix-mcp](./commix-mcp/) | [Commix](https://github.com/commixproject/commix) | Command injection exploitation | 8225 | `hackerdogs/commix-mcp` | web-app |
| 44 | [paramspider-mcp](./paramspider-mcp/) | [Paramspider](https://github.com/devanshbatham/ParamSpider) | Parameter mining from web archives | 8226 | `hackerdogs/paramspider-mcp` | web-app |
| 45 | [qsreplace-mcp](./qsreplace-mcp/) | [Qsreplace](https://github.com/projectdiscovery/qsreplace) | Query string parameter replacement | 8227 | `hackerdogs/qsreplace-mcp` | web-app |
| 46 | [uro-mcp](./uro-mcp/) | [Uro](https://github.com/projectdiscovery/uro) | URL filtering and deduplication | 8228 | `hackerdogs/uro-mcp` | web-app |
| 47 | [anew-mcp](./anew-mcp/) | [Anew](https://github.com/projectdiscovery/anew) | Append new lines for efficient data processing | 8229 | `hackerdogs/anew-mcp` | web-app |
| 48 | [wafw00f-mcp](./wafw00f-mcp/) | [Wafw00F](https://github.com/EnableSecurity/wafw00f) | Web application firewall fingerprinting | 8230 | `hackerdogs/wafw00f-mcp` | network-recon |
| 49 | [zap-mcp](./zap-mcp/) | [Zap](https://github.com/zaproxy/zap-core) | Automated security scanning proxy (headless) | 8231 | `hackerdogs/zap-mcp` | web-app |
| 50 | [jaeles-mcp](./jaeles-mcp/) | [Jaeles](https://github.com/jaeles-project/jaeles) | Vulnerability scanning with custom signatures | 8232 | `hackerdogs/jaeles-mcp` | vuln-scanning |
| 51 | [hydra-mcp](./hydra-mcp/) | [Hydra](https://github.com/vanhauser-thc/thc-hydra) | Network login cracker (50+ protocols) | 8233 | `hackerdogs/hydra-mcp` | exploitation |
| 52 | [john-mcp](./john-mcp/) | [John](https://github.com/openwall/john) | Password hash cracking with custom rules | 8234 | `hackerdogs/john-mcp` | exploitation |
| 53 | [hashcat-mcp](./hashcat-mcp/) | [Hashcat](https://github.com/hashcat/hashcat) | GPU-accelerated password recovery | 8235 | `hackerdogs/hashcat-mcp` | exploitation |
| 54 | [metasploit-mcp](./metasploit-mcp/) | [Metasploit](https://github.com/rapid7/metasploit-framework) | Exploitation framework (module runner) | 8236 | `hackerdogs/metasploit-mcp` | exploitation |
| 55 | [peda-mcp](./peda-mcp/) | [Peda](https://github.com/longld/peda) | GNU Debugger with PEDA (exploit development) | 8237 | `hackerdogs/peda-mcp` | binary-re |
| 56 | [gef-mcp](./gef-mcp/) | [Gef](https://github.com/hugsy/gef) | GDB Enhanced Features for exploit development | 8238 | `hackerdogs/gef-mcp` | binary-re |
| 57 | [radare2-mcp](./radare2-mcp/) | [Radare2](https://github.com/radareorg/radare2) | Reverse engineering framework | 8239 | `hackerdogs/radare2-mcp` | binary-re |
| 58 | [ghidra-mcp](./ghidra-mcp/) | [Ghidra](https://github.com/NationalSecurityAgency/ghidra) | NSA reverse engineering suite (headless) | 8240 | `hackerdogs/ghidra-mcp` | binary-re |
| 59 | [binwalk-mcp](./binwalk-mcp/) | [Binwalk](https://github.com/ReFirmLabs/binwalk) | Firmware analysis and extraction | 8241 | `hackerdogs/binwalk-mcp` | binary-re |
| 60 | [ropgadget-mcp](./ropgadget-mcp/) | [Ropgadget](https://github.com/JonathanSalwan/ROPgadget) | ROP/JOP gadget finder | 8242 | `hackerdogs/ropgadget-mcp` | binary-re |
| 61 | [ropper-mcp](./ropper-mcp/) | [Ropper](https://github.com/sashs/Ropper) | ROP gadget finder and exploit dev tool | 8243 | `hackerdogs/ropper-mcp` | binary-re |
| 62 | [checksec-mcp](./checksec-mcp/) | [Checksec](https://github.com/slimm609/checksec.sh) | Binary security property checker | 8244 | `hackerdogs/checksec-mcp` | binary-re |
| 63 | [pwntools-mcp](./pwntools-mcp/) | [Pwntools](https://github.com/Gallopsled/pwntools) | CTF framework and exploit development (use -c with pwntools) | 8245 | `hackerdogs/pwntools-mcp` | binary-re |
| 64 | [angr-mcp](./angr-mcp/) | [Angr](https://github.com/angr/angr) | Binary analysis with symbolic execution | 8246 | `hackerdogs/angr-mcp` | binary-re |
| 65 | [volatility3-mcp](./volatility3-mcp/) | [Volatility3](https://github.com/volatilityfoundation/volatility3) | Next-generation memory forensics | 8247 | `hackerdogs/volatility3-mcp` | binary-re |
| 66 | [volatility-mcp](./volatility-mcp/) | [Volatility](https://github.com/volatilityfoundation/volatility) | Memory forensics framework (v2) | 8248 | `hackerdogs/volatility-mcp` | binary-re |
| 67 | [foremost-mcp](./foremost-mcp/) | [Foremost](https://github.com/kdz/foremost) | File carving and data recovery | 8249 | `hackerdogs/foremost-mcp` | binary-re |
| 68 | [steghide-mcp](./steghide-mcp/) | [Steghide](https://github.com/StefanHetze/steghide) | Steganography detection and extraction | 8250 | `hackerdogs/steghide-mcp` | binary-re |
| 69 | [scoutsuite-mcp](./scoutsuite-mcp/) | [Scoutsuite](https://github.com/nccgroup/ScoutSuite) | Multi-cloud security auditing | 8251 | `hackerdogs/scoutsuite-mcp` | cloud-container |
| 70 | [kube-hunter-mcp](./kube-hunter-mcp/) | [Kube Hunter](https://github.com/aquasecurity/kube-hunter) | Kubernetes penetration testing | 8252 | `hackerdogs/kube-hunter-mcp` | cloud-container |
| 71 | [kube-bench-mcp](./kube-bench-mcp/) | [Kube Bench](https://github.com/aquasecurity/kube-bench) | CIS Kubernetes benchmark checker | 8253 | `hackerdogs/kube-bench-mcp` | cloud-container |
| 72 | [docker-bench-security-mcp](./docker-bench-security-mcp/) | [Docker Bench Security](https://github.com/docker/docker-bench-security) | Docker security assessment (CIS) | 8254 | `hackerdogs/docker-bench-security-mcp` | cloud-container |
| 73 | [social-analyzer-mcp](./social-analyzer-mcp/) | [Social Analyzer](https://github.com/qeeqbox/social-analyzer) | Social media analysis and OSINT | 8255 | `hackerdogs/social-analyzer-mcp` | osint |
| 74 | [recon-ng-mcp](./recon-ng-mcp/) | [Recon Ng](https://github.com/lanmaster53/recon-ng) | Web reconnaissance framework (modular) | 8256 | `hackerdogs/recon-ng-mcp` | osint |
| 75 | [spiderfoot-mcp](./spiderfoot-mcp/) | [Spiderfoot](https://github.com/smicallef/spiderfoot) | OSINT automation (200+ modules) | 8257 | `hackerdogs/spiderfoot-mcp` | osint |
| 76 | [trufflehog-mcp](./trufflehog-mcp/) | [Trufflehog](https://github.com/trufflesecurity/trufflehog) | Git repository secret scanning | 8258 | `hackerdogs/trufflehog-mcp` | appsec |
| 77 | [aquatone-mcp](./aquatone-mcp/) | [Aquatone](https://github.com/michenriksen/aquatone) | Visual inspection of websites across hosts | 8259 | `hackerdogs/aquatone-mcp` | web-app |
| 78 | [subjack-mcp](./subjack-mcp/) | [Subjack](https://github.com/haccer/subjack) | Subdomain takeover vulnerability checker | 8260 | `hackerdogs/subjack-mcp` | misc |
| 79 | [medusa-mcp](./medusa-mcp/) | [Medusa](https://github.com/jmk-foofus/medusa) | Parallel modular login brute-forcer | 8261 | `hackerdogs/medusa-mcp` | exploitation |
| 80 | [patator-mcp](./patator-mcp/) | [Patator](https://github.com/lanjelot/patator) | Multi-purpose brute-forcer | 8262 | `hackerdogs/patator-mcp` | exploitation |
| 81 | [evil-winrm-mcp](./evil-winrm-mcp/) | [Evil Winrm](https://github.com/Hackplayers/evil-winrm) | Windows Remote Management shell | 8263 | `hackerdogs/evil-winrm-mcp` | exploitation |
| 82 | [hashid-mcp](./hashid-mcp/) | [Hashid](https://github.com/psypanda/hashid) | Hash algorithm identifier | 8264 | `hackerdogs/hashid-mcp` | binary-re |
| 83 | [jwt-tool-mcp](./jwt-tool-mcp/) | [Jwt Tool](https://github.com/ticarpi/jwt_tool) | JWT testing and algorithm confusion | 8265 | `hackerdogs/jwt-tool-mcp` | web-app |
| 84 | [nosqlmap-mcp](./nosqlmap-mcp/) | [Nosqlmap](https://github.com/codingo/NoSQLMap) | NoSQL injection testing | 8266 | `hackerdogs/nosqlmap-mcp` | web-app |
| 85 | [tplmap-mcp](./tplmap-mcp/) | [Tplmap](https://github.com/epinna/tplmap) | Server-side template injection exploitation | 8267 | `hackerdogs/tplmap-mcp` | web-app |
| 86 | [cloudmapper-mcp](./cloudmapper-mcp/) | [Cloudmapper](https://github.com/duo-labs/cloudmapper) | AWS network visualization and security | 8268 | `hackerdogs/cloudmapper-mcp` | cloud-container |
| 87 | [pacu-mcp](./pacu-mcp/) | [Pacu](https://github.com/RhinoSecurityLabs/pacu) | AWS exploitation framework | 8269 | `hackerdogs/pacu-mcp` | cloud-container |
| 88 | [clair-mcp](./clair-mcp/) | [Clair](https://github.com/quay/clair) | Container vulnerability analysis | 8270 | `hackerdogs/clair-mcp` | cloud-container |
| 89 | [falco-mcp](./falco-mcp/) | [Falco](https://github.com/falcosecurity/falco) | Runtime security monitoring (containers/K8s) | 8271 | `hackerdogs/falco-mcp` | cloud-container |
| 90 | [checkov-mcp](./checkov-mcp/) | [Checkov](https://github.com/bridgecrewio/checkov) | Infrastructure as code security scanning | 8272 | `hackerdogs/checkov-mcp` | cloud-container |
| 91 | [terrascan-mcp](./terrascan-mcp/) | [Terrascan](https://github.com/tenable/terrascan) | Infrastructure security scanner (policy-as-code) | 8273 | `hackerdogs/terrascan-mcp` | cloud-container |
| 92 | [hashpump-mcp](./hashpump-mcp/) | [Hashpump](https://github.com/mheistermann/HashPump-partialhash) | Hash length extension attacks | 8274 | `hackerdogs/hashpump-mcp` | binary-re |
| 93 | [x8-mcp](./x8-mcp/) | [X8](https://github.com/sh1yo/x8) | Hidden parameter discovery | 8275 | `hackerdogs/x8-mcp` | web-app |
| 94 | [one-gadget-mcp](./one-gadget-mcp/) | [One Gadget](https://github.com/david942j/one_gadget) | Find one-shot RCE gadgets in libc | 8276 | `hackerdogs/one-gadget-mcp` | binary-re |
| 95 | [libc-database-mcp](./libc-database-mcp/) | [Libc Database](https://github.com/niklasb/libc-database) | Libc identification and offset lookup (use find script) | 8277 | `hackerdogs/libc-database-mcp` | binary-re |
| 96 | [pwninit-mcp](./pwninit-mcp/) | [Pwninit](https://github.com/icecream94/pwninit) | Automate binary exploitation setup | 8278 | `hackerdogs/pwninit-mcp` | binary-re |
| 97 | [testssl-mcp](./testssl-mcp/) | [Testssl](https://github.com/drwetter/testssl.sh) | SSL/TLS configuration testing | 8279 | `hackerdogs/testssl-mcp` | network-recon |
| 98 | [sslyze-mcp](./sslyze-mcp/) | [Sslyze](https://github.com/nablac0d3/sslyze) | SSL/TLS configuration analyzer | 8280 | `hackerdogs/sslyze-mcp` | network-recon |
| 99 | [whatweb-mcp](./whatweb-mcp/) | [Whatweb](https://github.com/urbanadventurer/WhatWeb) | Web technology identification and fingerprinting | 8281 | `hackerdogs/whatweb-mcp` | network-recon |
| 100 | [graphql-voyager-mcp](./graphql-voyager-mcp/) | [Graphql Voyager](https://github.com/APIs-guru/graphql-voyager) | GraphQL schema exploration (use voyager CLI if available) | 8282 | `hackerdogs/graphql-voyager-mcp` | web-app |
| 101 | [testdisk-mcp](./testdisk-mcp/) | [Testdisk](https://github.com/cgsecurity/testdisk) | Disk partition recovery and file carving | 8283 | `hackerdogs/testdisk-mcp` | binary-re |
| 102 | [upx-mcp](./upx-mcp/) | [Upx](https://github.com/upx/upx) | Executable packer/unpacker | 8284 | `hackerdogs/upx-mcp` | binary-re |
| 103 | [certipy-mcp](./certipy-mcp/) | [Certipy](https://github.com/ly4k/Certipy) | Active Directory certificate abuse and enumeration tool | 8285 | `hackerdogs/certipy-mcp` | exploitation |
| 104 | [bloodhound-mcp](./bloodhound-mcp/) | [BloodHound](https://github.com/SpecterOps/BloodHound) | Active Directory attack path analysis and enumeration | 8286 | `hackerdogs/bloodhound-mcp` | exploitation |
| 105 | [psudohash-mcp](./psudohash-mcp/) | [Psudohash](https://github.com/t3l3machus/psudohash) | Password list generator for targeted attacks based on known information | 8287 | `hackerdogs/psudohash-mcp` | binary-re |
| 106 | [wapiti-mcp](./wapiti-mcp/) | [Wapiti](https://github.com/wapiti-scanner/wapiti) | Web application vulnerability scanner with black-box testing | 8288 | `hackerdogs/wapiti-mcp` | vuln-scanning |
| 107 | [sstimap-mcp](./sstimap-mcp/) | [SSTImap](https://github.com/vladko312/SSTImap) | Server-Side Template Injection detection and exploitation tool | 8289 | `hackerdogs/sstimap-mcp` | web-app |
| 108 | [crlfuzz-mcp](./crlfuzz-mcp/) | [CRLFuzz](https://github.com/dwisiswant0/crlfuzz) | CRLF injection vulnerability scanner | 8290 | `hackerdogs/crlfuzz-mcp` | web-app |
| 109 | [smuggler-mcp](./smuggler-mcp/) | [Smuggler](https://github.com/defparam/smuggler) | HTTP request smuggling detection tool | 8291 | `hackerdogs/smuggler-mcp` | web-app |
| 110 | [corscanner-mcp](./corscanner-mcp/) | [CORScanner](https://github.com/chenjj/CORScanner) | CORS misconfiguration detection tool | 8292 | `hackerdogs/corscanner-mcp` | web-app |
| 111 | [dnsreaper-mcp](./dnsreaper-mcp/) | [dnsReaper](https://github.com/punk-security/dnsReaper) | Subdomain takeover vulnerability scanner via DNS | 8293 | `hackerdogs/dnsreaper-mcp` | network-recon |
| 112 | [ai-infra-guard-mcp](./ai-infra-guard-mcp/) | [AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | AI infrastructure security scanning and assessment | 8294 | `hackerdogs/ai-infra-guard-mcp` | cloud-container |
| 113 | [ramparts-mcp](./ramparts-mcp/) | [Ramparts](https://github.com/highflame-ai/ramparts) | AI security guardrails and safety framework | 8295 | `hackerdogs/ramparts-mcp` | appsec |
| 114 | [mcpscan-mcp](./mcpscan-mcp/) | [MCPScan](https://github.com/antgroup/MCPScan) | MCP server security scanning and vulnerability detection | 8296 | `hackerdogs/mcpscan-mcp` | appsec |
| 115 | [securemcp-mcp](./securemcp-mcp/) | [SecureMCP](https://github.com/makalin/SecureMCP) | MCP server security hardening and validation tool | 8297 | `hackerdogs/securemcp-mcp` | appsec |
| 116 | [nova-proximity-mcp](./nova-proximity-mcp/) | [Nova Proximity](https://github.com/Nova-Hunting/nova-proximity) | Network proximity analysis and threat detection | 8298 | `hackerdogs/nova-proximity-mcp` | core |
| 117 | [nova-framework-mcp](./nova-framework-mcp/) | [Nova Framework](https://github.com/Nova-Hunting/nova-framework) | Automated security testing and orchestration framework | 8299 | `hackerdogs/nova-framework-mcp` | core |
| 118 | [openvas-mcp](./openvas-mcp/) | [OpenVAS](https://github.com/greenbone/openvas-scanner) | Open Vulnerability Assessment Scanner for comprehensive vulnerability scanning | 8300 | `hackerdogs/openvas-mcp` | vuln-scanning |
| 119 | [sublist3r-mcp](./sublist3r-mcp/) | [Sublist3r](https://github.com/aboul3la/Sublist3r) | Fast subdomain enumeration tool using OSINT | 8301 | `hackerdogs/sublist3r-mcp` | network-recon |
| 120 | [exploitdb-mcp](./exploitdb-mcp/) | [ExploitDB](https://github.com/offensive-security/exploitdb) | Exploit Database search tool for known vulnerabilities | 8302 | `hackerdogs/exploitdb-mcp` | exploitation |
| 121 | [zmap-mcp](./zmap-mcp/) | [ZMap](https://github.com/zmap/zmap) | High-speed single-packet network scanner for internet-wide surveys | 8303 | `hackerdogs/zmap-mcp` | network-recon |
| 122 | [dnsenum-mcp](./dnsenum-mcp/) | [dnsenum](https://github.com/fwaeytens/dnsenum) | DNS enumeration tool for discovering host information | 8304 | `hackerdogs/dnsenum-mcp` | network-recon |
| 123 | [joomscan-mcp](./joomscan-mcp/) | [JoomScan](https://github.com/OWASP/joomscan) | OWASP Joomla vulnerability scanner | 8305 | `hackerdogs/joomscan-mcp` | web-app |
| 124 | [ncrack-mcp](./ncrack-mcp/) | [Ncrack](https://github.com/nmap/ncrack) | High-speed network authentication cracking tool | 8306 | `hackerdogs/ncrack-mcp` | exploitation |
| 125 | [crowbar-mcp](./crowbar-mcp/) | [Crowbar](https://github.com/galkan/crowbar) | Brute-forcing tool supporting protocols not commonly supported | 8307 | `hackerdogs/crowbar-mcp` | exploitation |
| 126 | [brutespray-mcp](./brutespray-mcp/) | [BruteSpray](https://github.com/x90skysn3k/brutespray) | Automated brute-forcing from Nmap or Nessus scan output | 8308 | `hackerdogs/brutespray-mcp` | exploitation |
| 127 | [fping-mcp](./fping-mcp/) | [Fping](https://github.com/schweikert/fping) | High-performance ping utility for parallel host probing | 8309 | `hackerdogs/fping-mcp` | network-recon |
| 128 | [bully-mcp](./bully-mcp/) | [Bully](https://github.com/aanarchyy/bully) | WPS brute-force attack tool for WiFi networks | 8310 | `hackerdogs/bully-mcp` | network-attacks |
| 129 | [pixiewps-mcp](./pixiewps-mcp/) | [Pixiewps](https://github.com/wiire-a/pixiewps) | Offline WPS brute-force tool exploiting low/no entropy weakness | 8311 | `hackerdogs/pixiewps-mcp` | network-attacks |
| 130 | [wifiphisher-mcp](./wifiphisher-mcp/) | [Wifiphisher](https://github.com/wifiphisher/wifiphisher) | Automated WiFi phishing attacks and credential harvesting | 8312 | `hackerdogs/wifiphisher-mcp` | network-attacks |
| 131 | [ettercap-mcp](./ettercap-mcp/) | [Ettercap](https://github.com/Ettercap/ettercap) | Comprehensive suite for man-in-the-middle attacks on LAN | 8313 | `hackerdogs/ettercap-mcp` | network-attacks |
| 132 | [ngrep-mcp](./ngrep-mcp/) | [Ngrep](https://github.com/jpr5/ngrep) | Network packet analyzer with grep-like pattern matching | 8314 | `hackerdogs/ngrep-mcp` | network-recon |
| 133 | [wireshark-mcp](./wireshark-mcp/) | [Wireshark (tshark)](https://github.com/wireshark/wireshark) | Network protocol analyzer for deep packet inspection | 8315 | `hackerdogs/wireshark-mcp` | network-recon |
| 134 | [slowhttptest-mcp](./slowhttptest-mcp/) | [SlowHTTPTest](https://github.com/shekyan/slowhttptest) | Application layer DoS attack simulator for slow HTTP attacks | 8316 | `hackerdogs/slowhttptest-mcp` | network-attacks |
| 135 | [sherlock-mcp](./sherlock-mcp/) | [Sherlock](https://github.com/sherlock-project/sherlock) | Username hunting across social networks and websites | 8317 | `hackerdogs/sherlock-mcp` | osint |
| 136 | [bettercap-mcp](./bettercap-mcp/) | [Bettercap](https://github.com/bettercap/bettercap) | Network attack and monitoring framework with MITM capabilities | 8318 | `hackerdogs/bettercap-mcp` | network-attacks |
| 137 | [yersinia-mcp](./yersinia-mcp/) | [Yersinia](https://github.com/tomac/yersinia) | Network vulnerability exploitation tool for layer 2 attacks | 8319 | `hackerdogs/yersinia-mcp` | network-attacks |
| 138 | [cutter-mcp](./cutter-mcp/) | [Cutter](https://github.com/rizinorg/cutter) | Reverse engineering platform powered by Rizin | 8320 | `hackerdogs/cutter-mcp` | binary-re |
| 139 | [aircrack-ng-mcp](./aircrack-ng-mcp/) | [Aircrack-ng](https://github.com/aircrack-ng/aircrack-ng) | WiFi security auditing tools suite for WEP/WPA/WPA2 cracking | 8321 | `hackerdogs/aircrack-ng-mcp` | network-attacks |
| 140 | [netdiscover-mcp](./netdiscover-mcp/) | [Netdiscover](https://github.com/netdiscover-scanner/netdiscover) | Active/passive ARP reconnaissance tool for network discovery | 8322 | `hackerdogs/netdiscover-mcp` | network-recon |
| 141 | [sslscan-mcp](./sslscan-mcp/) | [SSLScan](https://github.com/rbsec/sslscan) | SSL/TLS configuration and certificate scanner | 8323 | `hackerdogs/sslscan-mcp` | network-recon |
| 142 | [crunch-mcp](./crunch-mcp/) | [Crunch](https://github.com/crunchsec/crunch) | Custom wordlist generator for password cracking | 8324 | `hackerdogs/crunch-mcp` | misc |
| 143 | [smtp-user-enum-mcp](./smtp-user-enum-mcp/) | [SMTP User Enum](https://github.com/pentestmonkey/smtp-user-enum) | SMTP username enumeration via VRFY, EXPN, and RCPT commands | 8325 | `hackerdogs/smtp-user-enum-mcp` | misc |
| 144 | [lynis-mcp](./lynis-mcp/) | [Lynis](https://github.com/CISOfy/lynis) | Security auditing and compliance testing tool for Linux/Unix | 8326 | `hackerdogs/lynis-mcp` | vuln-scanning |
| 145 | [netcat-mcp](./netcat-mcp/) | [Netcat](https://github.com/diegocr/netcat) | TCP/UDP networking utility for port scanning and data transfer | 8327 | `hackerdogs/netcat-mcp` | network-recon |
| 146 | [yara-mcp](./yara-mcp/) | [YARA](https://github.com/VirusTotal/yara) | Pattern matching tool for malware researchers and classification | 8328 | `hackerdogs/yara-mcp` | binary-re |
| 147 | [capa-mcp](./capa-mcp/) | [Capa](https://github.com/mandiant/capa) | Capability detection tool for malware triage and analysis | 8329 | `hackerdogs/capa-mcp` | binary-re |
| 148 | [trivy-mcp](./trivy-mcp/) | [Trivy](https://github.com/aquasecurity/trivy) | Comprehensive vulnerability scanner for containers, filesystems, and IaC | 8330 | `hackerdogs/trivy-mcp` | cloud-container |
| 149 | [roadtools-mcp](./roadtools-mcp/) | [ROADtools](https://github.com/dirkjanm/ROADtools) | Azure AD enumeration and attack tools for cloud security | 8331 | `hackerdogs/roadtools-mcp` | cloud-container |
| 150 | [gitleaks-mcp](./gitleaks-mcp/) | [Gitleaks](https://github.com/gitleaks/gitleaks) | Secret detection tool for git repositories and files | 8332 | `hackerdogs/gitleaks-mcp` | appsec |
| 151 | [boofuzz-mcp](./boofuzz-mcp/) | [Boofuzz](https://github.com/jtpereyda/boofuzz) | Network protocol fuzzing framework for finding vulnerabilities | 8333 | `hackerdogs/boofuzz-mcp` | web-app |
| 152 | [dharma-mcp](./dharma-mcp/) | [Dharma](https://github.com/MozillaSecurity/dharma) | Grammar-based test case generation for fuzzing | 8334 | `hackerdogs/dharma-mcp` | binary-re |
| 153 | [semgrep-mcp](./semgrep-mcp/) | [Semgrep](https://github.com/semgrep/semgrep) | Lightweight static analysis for code security with 5000+ rules | 8335 | `hackerdogs/semgrep-mcp` | appsec |
| 154 | [yaraflux-mcp](./yaraflux-mcp/) | [YaraFlux](https://github.com/ThreatFlux/YaraFlux) | YARA-based MCP server for malware scanning and rule management | 8336 | `hackerdogs/yaraflux-mcp` | binary-re |
| 155 | [yeti-mcp](./yeti-mcp/) | [Yeti](https://github.com/yeti-platform/yeti-mcp) | Threat intelligence platform MCP integration | 8337 | `hackerdogs/yeti-mcp` | vuln-scanning |
| 156 | [bloodhound-mcp-ai-mcp](./bloodhound-mcp-ai-mcp/) | [BloodHound AI](https://github.com/stevenyu113228/BloodHound-MCP) | AI-powered Active Directory attack path analysis | 8338 | `hackerdogs/bloodhound-mcp-ai-mcp` | exploitation |
| 157 | [vulnerability-scanner-mcp](./vulnerability-scanner-mcp/) | [Vulnerability Scanner](https://github.com/RobertoDure/mcp-vulnerability-scanner) | Vulnerability scanning and assessment tool | 8339 | `hackerdogs/vulnerability-scanner-mcp` | vuln-scanning |
| 158 | [mcpserver-audit-mcp](./mcpserver-audit-mcp/) | [MCPServer Audit](https://github.com/ModelContextProtocol-Security/mcpserver-audit) | Security auditing tool for MCP servers | 8340 | `hackerdogs/mcpserver-audit-mcp` | appsec |
| 159 | [a2a-scanner-mcp](./a2a-scanner-mcp/) | [A2A Scanner](https://github.com/cisco-ai-defense/a2a-scanner) | Agent-to-Agent communication security scanner | 8341 | `hackerdogs/a2a-scanner-mcp` | misc |
| 160 | [cisco-mcp-scanner-mcp](./cisco-mcp-scanner-mcp/) | [Cisco AI Defense Scanner](https://github.com/cisco-ai-defense/mcp-scanner) | AI defense protocol security scanning and analysis | 8342 | `hackerdogs/cisco-mcp-scanner-mcp` | misc |
| 161 | [aibom-mcp](./aibom-mcp/) | [AIBOM](https://github.com/cisco-ai-defense/aibom) | AI Bill of Materials generator for AI model transparency | 8343 | `hackerdogs/aibom-mcp` | appsec |
| 162 | [knostic-mcp-scanner-mcp](./knostic-mcp-scanner-mcp/) | [Knostic Scanner](https://github.com/knostic/MCP-Scanner) | Security scanner for AI agent servers and configurations | 8344 | `hackerdogs/knostic-mcp-scanner-mcp` | appsec |
| 163 | [threat-hunting-mcp](./threat-hunting-mcp/) | [Threat Hunting](https://github.com/THORCollective/threat-hunting-mcp-server) | Threat hunting and intelligence gathering MCP server | 8345 | `hackerdogs/threat-hunting-mcp` | vuln-scanning |
| 164 | [aws-s3-mcp](./aws-s3-mcp/) | [AWS S3](https://github.com/samuraikun/aws-s3-mcp) | AWS S3 bucket security analysis and enumeration | 8346 | `hackerdogs/aws-s3-mcp` | cloud-container |
| 165 | [osv-mcp](./osv-mcp/) | [OSV](https://github.com/StacklokLabs/osv-mcp) | Open Source Vulnerability database query tool via MCP | 8347 | `hackerdogs/osv-mcp` | appsec |
| 166 | [vanta-mcp](./vanta-mcp/) | [Vanta](https://github.com/VantaInc/vanta-mcp-server) | Vanta compliance and security monitoring MCP integration | 8348 | `hackerdogs/vanta-mcp` | misc |
| 167 | [xsstrike-mcp](./xsstrike-mcp/) | [XSStrike](https://github.com/s0md3v/XSStrike) | Advanced XSS detection and exploitation tool | 8349 | `hackerdogs/xsstrike-mcp` | web-app |
| 168 | [gospider-mcp](./gospider-mcp/) | [Gospider](https://github.com/jaeles-project/gospider) | Fast web crawling and URL discovery tool | 8350 | `hackerdogs/gospider-mcp` | web-app |
| 169 | [ipinfo-mcp](./ipinfo-mcp/) | [IPInfo](https://github.com/ipinfo/cli) | IP address intelligence and geolocation lookup tool | 8351 | `hackerdogs/ipinfo-mcp` | osint |
| 170 | [garak-mcp](./garak-mcp/) | [Garak](https://github.com/EdenYavin/Garak-MCP) | AI red teaming and LLM vulnerability testing | 8352 | `hackerdogs/garak-mcp` | appsec |
| 171 | [rasn-mcp](./rasn-mcp/) | [RASN](https://github.com/copyleftdev/rasn) | Rust-based ASN lookup and network intelligence tool | 8353 | `hackerdogs/rasn-mcp` | binary-re |
| 172 | [port-scanner-mcp](./port-scanner-mcp/) | [Port Scanner](https://github.com/relaxcloud-cn/mcp-port-scanner) | Network port scanning tool | 8354 | `hackerdogs/port-scanner-mcp` | network-recon |
| 173 | [zap-lis-mcp](./zap-lis-mcp/) | [ZAP Lis](https://github.com/LisBerndt/zap-mcp-server) | OWASP ZAP integration for web security testing | 8355 | `hackerdogs/zap-lis-mcp` | web-app |
| 174 | [trivy-neutr0n-mcp](./trivy-neutr0n-mcp/) | [Trivy Neutr0n](https://github.com/Mr-Neutr0n/trivy-mcp-server) | Trivy-based container and filesystem vulnerability scanning | 8356 | `hackerdogs/trivy-neutr0n-mcp` | cloud-container |
| 175 | [grype-mcp](./grype-mcp/) | [Grype](https://github.com/anchore/grype) | Container image and filesystem vulnerability scanner | 8357 | `hackerdogs/grype-mcp` | appsec |
| 176 | [syft-mcp](./syft-mcp/) | [Syft](https://github.com/anchore/syft) | Software bill of materials (SBOM) generator for container images | 8358 | `hackerdogs/syft-mcp` | misc |
| 177 | [horusec-mcp](./horusec-mcp/) | [Horusec](https://github.com/ZupIT/horusec) | Static application security testing (SAST) tool | 8359 | `hackerdogs/horusec-mcp` | appsec |
| 178 | [bearer-mcp](./bearer-mcp/) | [Bearer](https://github.com/Bearer/bearer) | Code security scanning tool for sensitive data flows | 8360 | `hackerdogs/bearer-mcp` | appsec |
| 179 | [dependency-check-mcp](./dependency-check-mcp/) | [Dependency-Check](https://github.com/jeremylong/DependencyCheck) | Software composition analysis for known vulnerabilities in dependencies | 8361 | `hackerdogs/dependency-check-mcp` | appsec |
| 180 | [kubescape-mcp](./kubescape-mcp/) | [Kubescape](https://github.com/kubescape/kubescape) | Kubernetes security posture management and compliance scanning | 8362 | `hackerdogs/kubescape-mcp` | cloud-container |
| 181 | [ggshield-mcp](./ggshield-mcp/) | [ggshield](https://github.com/GitGuardian/ggshield) | Secret detection and code security scanning by GitGuardian | 8363 | `hackerdogs/ggshield-mcp` | appsec |
| 182 | [retire-js-mcp](./retire-js-mcp/) | [Retire.js](https://github.com/RetireJS/retire.js) | JavaScript library vulnerability scanner for known CVEs | 8364 | `hackerdogs/retire-js-mcp` | appsec |
| 183 | [suricata-mcp](./suricata-mcp/) | [Suricata](https://suricata.io/) | network intrusion detection and prevention system (IDS/IPS) | 8365 | `hackerdogs/suricata-mcp` | vuln-scanning |
| 184 | [ivre-mcp](./ivre-mcp/) | [IVRE](https://github.com/ivre/ivre) | query an existing IVRE deployment for active scan results, passive reconnaissance, DNS records, a… | 8366 | `hackerdogs/ivre-mcp` | network-recon |
| 185 | [subfinder-mcp](./subfinder-mcp/) | [subfinder](https://github.com/projectdiscovery/subfinder) | passive subdomain enumeration | 8367 | `hackerdogs/subfinder-mcp` | network-recon |
| 186 | [otx-mcp](./otx-mcp/) | [AlienVault OTX](https://otx.alienvault.com) | open threat intelligence platform with crowd-sourced threat data | 8368 | `hackerdogs/otx-mcp` | osint |
| 187 | [virustotal-mcp](./virustotal-mcp/) | [VirusTotal](https://www.virustotal.com) | file, URL, domain & IP threat intelligence via the VT API v3 | 8369 | `hackerdogs/virustotal-mcp` | vuln-scanning |
| 188 | [opencti-mcp](./opencti-mcp/) | [OpenCTI](https://github.com/OpenCTI-Platform/opencti) | threat intelligence platform queries via the pycti Python client | 8370 | `hackerdogs/opencti-mcp` | vuln-scanning |
| 189 | [misp-mcp](./misp-mcp/) | [MISP](https://www.misp-project.org/) | Malware Information Sharing Platform (threat intelligence, IOC search, event management) | 8371 | `hackerdogs/misp-mcp` | vuln-scanning |
| 190 | [onionsearch-mcp](./onionsearch-mcp/) | [OnionSearch](https://github.com/megadose/OnionSearch) | Dark Web | 8372 | `hackerdogs/onionsearch-mcp` | osint |
| 191 | [abusech-mcp](./abusech-mcp/) | [Abuse.ch](https://abuse.ch/) | threat intelligence via MalwareBazaar, URLhaus, and ThreatFox | 8373 | `hackerdogs/abusech-mcp` | misc |
| 192 | [abuseipdb-mcp](./abuseipdb-mcp/) | [AbuseIPDB](https://www.abuseipdb.com/) | community-powered IP reputation and abuse reporting database | 8374 | `hackerdogs/abuseipdb-mcp` | misc |
| 193 | [builtwith-mcp](./builtwith-mcp/) | [BuiltWith](https://builtwith.com/) | Website technology stack detection | 8375 | `hackerdogs/builtwith-mcp` | osint |
| 194 | [code-execution-mcp](./code-execution-mcp/) | — | Safe sandboxed code execution (stub) | 8376 | `hackerdogs/code-execution-mcp` | core |
| 195 | [deepwebresearch-mcp](./deepwebresearch-mcp/) | [mcp-DEEPwebresearch](https://github.com/nickspaargaren/mcp-DEEPwebresearch) | Deep web research (stub) | 8377 | `hackerdogs/deepwebresearch-mcp` | osint |
| 196 | [pagespeed-mcp](./pagespeed-mcp/) | [PageSpeed Insights](https://pagespeed.web.dev/) | Google PageSpeed Insights | 8378 | `hackerdogs/pagespeed-mcp` | misc |
| 197 | [secops-mcp](./secops-mcp/) | — | SecOps hub: nuclei, ffuf, wfuzz, sqlmap, nmap (stub) | 8379 | `hackerdogs/secops-mcp` | vuln-scanning |
| 198 | [ctgov-mcp-docker-mcp](./ctgov-mcp-docker-mcp/) | [AACT ClinicalTrials.gov](https://aact.ctti-clinicaltrials.org) | query the AACT database for structured ClinicalTrials | 8401 | `hackerdogs/ctgov-mcp-docker-mcp` | misc |
| 199 | [alphavantage-mcp](./alphavantage-mcp/) | [Alpha Vantage](https://www.alphavantage.co) | real-time and historical financial market data including stock quotes, forex rates, cryptocurrenc… | 8402 | `hackerdogs/alphavantage-mcp` | misc |
| 200 | [acuvity-mcp-server-atlas-docs-mcp](./acuvity-mcp-server-atlas-docs-mcp/) | [Atlas Docs MCP Server](https://github.com/acuvity/mcp-servers-registry) | technical documentation provider that converts official library and framework docs into clean, AI… | 8403 | `hackerdogs/acuvity-mcp-server-atlas-docs-mcp` | misc |
| 201 | [acuvity-mcp-server-atlassian-mcp](./acuvity-mcp-server-atlassian-mcp/) | [Atlassian MCP Server](https://github.com/acuvity/mcp-servers-registry) | AI integration for Jira and Confluence task automation and content management | 8404 | `hackerdogs/acuvity-mcp-server-atlassian-mcp` | misc |
| 202 | [acuvity-mcp-server-bing-search-mcp](./acuvity-mcp-server-bing-search-mcp/) | [Bing Search API](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) | web search integration via the Microsoft Bing Search API | 8405 | `hackerdogs/acuvity-mcp-server-bing-search-mcp` | misc |
| 203 | [acuvity-mcp-server-brave-search-mcp](./acuvity-mcp-server-brave-search-mcp/) | [Brave Search API](https://brave.com/search/api/) | independent web search powered by Brave's own index, free from Google and Bing tracking | 8406 | `hackerdogs/acuvity-mcp-server-brave-search-mcp` | osint |
| 204 | [acuvity-mcp-server-calculator-mcp](./acuvity-mcp-server-calculator-mcp/) | [Calculator MCP Server](https://github.com/acuvity/mcp-servers-registry) | a tool that gives AI agents access to a reliable calculator for precise numerical computations | 8407 | `hackerdogs/acuvity-mcp-server-calculator-mcp` | misc |
| 205 | [acuvity-mcp-server-chroma-mcp](./acuvity-mcp-server-chroma-mcp/) | [Chroma](https://www.trychroma.com/) | open-source AI-native vector database for embedding storage and semantic similarity search | 8408 | `hackerdogs/acuvity-mcp-server-chroma-mcp` | misc |
| 206 | [mcp-server-code-runner-mcp](./mcp-server-code-runner-mcp/) | [mcp-server-code-runner](https://github.com/formulahendry/mcp-server-code-runner) | execute code snippets in multiple programming languages and return the output | 8409 | `hackerdogs/mcp-server-code-runner-mcp` | core |
| 207 | [cortex-mcp](./cortex-mcp/) | [Cortex](https://github.com/TheHive-Project/Cortex) | security orchestration platform for running threat intelligence analyzers and active response act… | 8410 | `hackerdogs/cortex-mcp` | vuln-scanning |
| 208 | [crunchbase-mcp](./crunchbase-mcp/) | [Crunchbase](https://www.crunchbase.com) | search and retrieve company profiles, funding rounds, investor information, and acquisitions via… | 8411 | `hackerdogs/crunchbase-mcp` | osint |
| 209 | [acuvity-mcp-server-docker-mcp](./acuvity-mcp-server-docker-mcp/) | [Docker MCP Server](https://github.com/docker/mcp-server) | natural-language management of Docker containers, images, and Compose stacks | 8412 | `hackerdogs/acuvity-mcp-server-docker-mcp` | misc |
| 210 | [duckduckgo-mcp](./duckduckgo-mcp/) | [DuckDuckGo](https://duckduckgo.com) | privacy-preserving web search that returns organic results without tracking or requiring an API key | 8413 | `hackerdogs/duckduckgo-mcp` | osint |
| 211 | [acuvity-mcp-server-duckduckgo-mcp](./acuvity-mcp-server-duckduckgo-mcp/) | [DuckDuckGo Search](https://github.com/nickscamara/mcp-duckduckgo) | privacy-respecting web search without API keys or tracking | 8414 | `hackerdogs/acuvity-mcp-server-duckduckgo-mcp` | osint |
| 212 | [edgartools-mcp-server-mcp](./edgartools-mcp-server-mcp/) | [edgartools](https://github.com/dgunning/edgartools) | retrieve and parse SEC EDGAR filings including 10-K annual reports, 10-Q quarterly reports, 8-K c… | 8415 | `hackerdogs/edgartools-mcp-server-mcp` | misc |
| 213 | [edu-data-mcp](./edu-data-mcp/) | [edu-data-mcp-server](https://github.com/ousepachn/edu-data-mcp-server) | query the Urban Institute's Education Data API for K–12 and postsecondary education statistics ac… | 8416 | `hackerdogs/edu-data-mcp` | misc |
| 214 | [acuvity-mcp-server-elevenlabs-mcp](./acuvity-mcp-server-elevenlabs-mcp/) | [ElevenLabs](https://github.com/elevenlabs/elevenlabs-mcp) | AI-powered text-to-speech and audio generation via the ElevenLabs API | 8417 | `hackerdogs/acuvity-mcp-server-elevenlabs-mcp` | misc |
| 215 | [acuvity-mcp-server-everything-wrong-mcp](./acuvity-mcp-server-everything-wrong-mcp/) | [Everything Wrong MCP Server](https://github.com/acuvity/mcp-servers-registry) | a security-testing reference server that exposes intentionally dangerous and misbehaving MCP tools | 8418 | `hackerdogs/acuvity-mcp-server-everything-wrong-mcp` | misc |
| 216 | [acuvity-mcp-server-fetch-mcp](./acuvity-mcp-server-fetch-mcp/) | [Fetch MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | an HTTP client that retrieves and processes web content for AI assistants | 8419 | `hackerdogs/acuvity-mcp-server-fetch-mcp` | misc |
| 217 | [financial-datasets-mcp](./financial-datasets-mcp/) | [Financial Datasets](https://github.com/virattt/financial-datasets-mcp) | access real-time and historical stock market data including income statements, balance sheets, an… | 8420 | `hackerdogs/financial-datasets-mcp` | misc |
| 218 | [acuvity-mcp-server-firecrawl-mcp](./acuvity-mcp-server-firecrawl-mcp/) | [Firecrawl](https://github.com/mendableai/firecrawl-mcp-server) | advanced web scraping and crawling that returns clean Markdown from JavaScript-heavy pages | 8421 | `hackerdogs/acuvity-mcp-server-firecrawl-mcp` | misc |
| 219 | [flights-mcp](./flights-mcp/) | [Flights MCP](https://github.com/aiXplain/flights-mcp) | search for flights and retrieve fare data via the Aviasales Flight Search API | 8422 | `hackerdogs/flights-mcp` | misc |
| 220 | [fred-mcp](./fred-mcp/) | [FRED](https://fred.stlouisfed.org/) | access over 800,000 economic time series from the Federal Reserve Bank of St | 8423 | `hackerdogs/fred-mcp` | misc |
| 221 | [acuvity-mcp-server-google-maps-mcp](./acuvity-mcp-server-google-maps-mcp/) | [Google Maps MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/google-maps) | location search, geocoding, routing, and place details via the Google Maps Platform API | 8424 | `hackerdogs/acuvity-mcp-server-google-maps-mcp` | misc |
| 222 | [acuvity-mcp-server-grafana-mcp](./acuvity-mcp-server-grafana-mcp/) | [Grafana MCP Server](https://github.com/grafana/mcp-grafana) | query dashboards, explore metrics, and manage alerts in your Grafana instance via natural language | 8425 | `hackerdogs/acuvity-mcp-server-grafana-mcp` | misc |
| 223 | [acuvity-mcp-server-harness-mcp](./acuvity-mcp-server-harness-mcp/) | [Harness MCP Server](https://github.com/harness/mcp-server) | CI/CD pipeline management and DevOps automation via the Harness platform API | 8426 | `hackerdogs/acuvity-mcp-server-harness-mcp` | misc |
| 224 | [acuvity-mcp-server-hyperbrowser-mcp](./acuvity-mcp-server-hyperbrowser-mcp/) | [Hyperbrowser](https://github.com/hyperbrowserai/mcp) | cloud browser automation and web scraping with built-in anti-detection and session management | 8427 | `hackerdogs/acuvity-mcp-server-hyperbrowser-mcp` | misc |
| 225 | [acuvity-mcp-server-kagisearch-mcp](./acuvity-mcp-server-kagisearch-mcp/) | [Kagi Search MCP Server](https://github.com/kagisearch/mcp) | high-quality ad-free web search and YouTube video summarization via the Kagi API | 8428 | `hackerdogs/acuvity-mcp-server-kagisearch-mcp` | misc |
| 226 | [mapboxserver-mcp](./mapboxserver-mcp/) | [Mapbox](https://docs.mapbox.com) | geospatial mapping, geocoding, routing, and directions powered by the Mapbox platform | 8429 | `hackerdogs/mapboxserver-mcp` | misc |
| 227 | [marinetraffic-mcp](./marinetraffic-mcp/) | [MarineTraffic](https://www.marinetraffic.com) | real-time vessel tracking, AIS data, and maritime intelligence | 8430 | `hackerdogs/marinetraffic-mcp` | network-recon |
| 228 | [acuvity-mcp-server-everything-mcp](./acuvity-mcp-server-everything-mcp/) | [MCP Server Everything](https://github.com/modelcontextprotocol/servers/tree/main/src/everything) | a comprehensive reference implementation that exercises every MCP protocol feature | 8431 | `hackerdogs/acuvity-mcp-server-everything-mcp` | misc |
| 229 | [acuvity-mcp-server-azure-mcp](./acuvity-mcp-server-azure-mcp/) | [Microsoft Azure MCP Server](https://github.com/acuvity/mcp-servers-registry) | AI agent integration with Microsoft Azure cloud services | 8432 | `hackerdogs/acuvity-mcp-server-azure-mcp` | cloud-container |
| 230 | [acuvity-mcp-server-microsoft-graph-mcp](./acuvity-mcp-server-microsoft-graph-mcp/) | [Microsoft Graph MCP Server](https://github.com/microsoftgraph/msgraph-mcp) | access Microsoft 365 data including users, applications, mail, calendar, and Teams via the Micros… | 8433 | `hackerdogs/acuvity-mcp-server-microsoft-graph-mcp` | misc |
| 231 | [aistor-mcp](./aistor-mcp/) | [MinIO AIStor](https://github.com/minio/mcp-server-aistor) | the official MCP server for MinIO's exabyte-scale object storage, enabling AI agents to manage bu… | 8434 | `hackerdogs/aistor-mcp` | appsec |
| 232 | [n2yo-mcp](./n2yo-mcp/) | [N2YO](https://www.n2yo.com/) | real-time satellite tracking and orbital pass predictions via the N2YO | 8435 | `hackerdogs/n2yo-mcp` | misc |
| 233 | [netutils-mcp](./netutils-mcp/) | — | Common network utility helpers | 8436 | `hackerdogs/netutils-mcp` | network-recon |
| 234 | [acuvity-mcp-server-notion-mcp](./acuvity-mcp-server-notion-mcp/) | [Notion MCP Server](https://github.com/makenotion/notion-mcp-server) | read and write your Notion workspace pages, databases, and blocks via the official Notion API | 8437 | `hackerdogs/acuvity-mcp-server-notion-mcp` | misc |
| 235 | [ocr-mcp](./ocr-mcp/) | [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | extract text from images and scanned PDFs using Tesseract with optional structured bounding-box o… | 8438 | `hackerdogs/ocr-mcp` | core |
| 236 | [open-legal-mcp](./open-legal-mcp/) | [Open Legal Compliance MCP](https://github.com/TCoder920x/open-legal-compliance-mcp) | legal compliance checking and regulatory analysis assistant | 8439 | `hackerdogs/open-legal-mcp` | misc |
| 237 | [opencv-mcp-server-mcp](./opencv-mcp-server-mcp/) | [OpenCV MCP Server](https://github.com/GrasshopperBears/opencv-mcp-server) | image and video processing via OpenCV's computer vision library | 8440 | `hackerdogs/opencv-mcp-server-mcp` | misc |
| 238 | [acuvity-mcp-server-oshp-mcp](./acuvity-mcp-server-oshp-mcp/) | [OSHP MCP Server](https://github.com/acuvity/mcp-servers-registry) | HTTP security header analysis against OWASP Secure Headers Project recommendations | 8441 | `hackerdogs/acuvity-mcp-server-oshp-mcp` | misc |
| 239 | [pdf-reader-mcp](./pdf-reader-mcp/) | [PDF Reader MCP (Sylphx)](https://github.com/sylphxltd/pdf-reader-mcp) | extract and query text content from PDF files via URL or local path | 8442 | `hackerdogs/pdf-reader-mcp` | core |
| 240 | [pentest-agent-mcp](./pentest-agent-mcp/) | [PentestAgent MCP](https://github.com/Iam0TI/PentestAgent-MCP) | an all-in-one offensive security toolbox and AI-driven red team assistant | 8443 | `hackerdogs/pentest-agent-mcp` | core |
| 241 | [acuvity-mcp-server-playwright-mcp](./acuvity-mcp-server-playwright-mcp/) | [Playwright MCP Server](https://github.com/microsoft/playwright-mcp) | full browser automation using Microsoft Playwright, enabling click, type, screenshot, and navigat… | 8444 | `hackerdogs/acuvity-mcp-server-playwright-mcp` | web-app |
| 242 | [polygon-mcp](./polygon-mcp/) | [Polygon.io](https://polygon.io/) | real-time and historical stock, options, forex, and crypto market data via the Polygon | 8445 | `hackerdogs/polygon-mcp` | misc |
| 243 | [pubmed-mcp](./pubmed-mcp/) | [PubMed MCP](https://github.com/YUZongmin/pubmed-mcp-server) | search and analyze biomedical literature from the NCBI PubMed database | 8446 | `hackerdogs/pubmed-mcp` | misc |
| 244 | [reddit-mcp-server-mcp](./reddit-mcp-server-mcp/) | — | Reddit search and content retrieval | 8447 | `hackerdogs/reddit-mcp-server-mcp` | osint |
| 245 | [rss-mcp](./rss-mcp/) | — | RSS/Atom feed fetching and parsing | 8448 | `hackerdogs/rss-mcp` | osint |
| 246 | [scan-url-mcp](./scan-url-mcp/) | [urlscan.io](https://urlscan.io/) | URL scanning and security checks | 8449 | `hackerdogs/scan-url-mcp` | vuln-scanning |
| 247 | [acuvity-mcp-server-scrapezy-mcp](./acuvity-mcp-server-scrapezy-mcp/) | [Scrapezy](https://github.com/acuvity/mcp-servers) | web scraping and structured data extraction from websites via the Scrapezy MCP server | 8450 | `hackerdogs/acuvity-mcp-server-scrapezy-mcp` | misc |
| 248 | [sec-edgar-mcp](./sec-edgar-mcp/) | [SEC EDGAR](https://www.sec.gov/edgar) | SEC EDGAR filings search and retrieval | 8451 | `hackerdogs/sec-edgar-mcp` | misc |
| 249 | [acuvity-mcp-server-sentry-mcp](./acuvity-mcp-server-sentry-mcp/) | [Sentry](https://github.com/acuvity/mcp-servers) | retrieve and analyze application error issues from Sentry | 8452 | `hackerdogs/acuvity-mcp-server-sentry-mcp` | misc |
| 250 | [shodan-mcp](./shodan-mcp/) | [Shodan](https://www.shodan.io/) | Shodan search and host intelligence | 8453 | `hackerdogs/shodan-mcp` | osint |
| 251 | [slack-mcp](./slack-mcp/) | [Slack](https://slack.com) | interact with Slack workspaces to read messages, post to channels, and search conversations | 8454 | `hackerdogs/slack-mcp` | misc |
| 252 | [acuvity-mcp-server-slack-mcp](./acuvity-mcp-server-slack-mcp/) | [Slack](https://github.com/acuvity/mcp-servers) | interact with Slack workspaces, channels, and messages via the Acuvity MCP server | 8455 | `hackerdogs/acuvity-mcp-server-slack-mcp` | misc |
| 253 | [trivy-security-mcp](./trivy-security-mcp/) | [Trivy](https://github.com/aquasecurity/trivy) | comprehensive vulnerability and misconfiguration scanner for containers, filesystems, IaC, and SBOMs | 8456 | `hackerdogs/trivy-security-mcp` | cloud-container |
| 254 | [earthquake-mcp](./earthquake-mcp/) | [USGS Earthquake Hazards Program](https://earthquake.usgs.gov) | query real-time and historical seismic event data from the USGS and IRIS networks | 8457 | `hackerdogs/earthquake-mcp` | misc |
| 255 | [wiremcp-mcp](./wiremcp-mcp/) | [WireMCP](https://github.com/bstefanescu/wiremcp) | AI-assisted real-time network traffic analysis via Wireshark/tshark | 8458 | `hackerdogs/wiremcp-mcp` | misc |
| 256 | [world-bank-mcp](./world-bank-mcp/) | [World Bank MCP](https://github.com/anshumax/world-bank-mcp) | access to the open World Bank data API for global economic and development indicators | 8459 | `hackerdogs/world-bank-mcp` | misc |
| 257 | [yfmcp-mcp](./yfmcp-mcp/) | [yfmcp](https://github.com/narumiruna/yfmcp) | Yahoo Finance stock and market data access via the `yfinance` Python library | 8460 | `hackerdogs/yfmcp-mcp` | misc |
| 258 | [yaraflux-mcp-server-mcp](./yaraflux-mcp-server-mcp/) | [YaraFlux](https://github.com/ThreatFlux/YaraFlux) | YARA-based malware scanning and threat analysis via an MCP-native server | 8461 | `hackerdogs/yaraflux-mcp-server-mcp` | binary-re |
| 259 | [youtube-mcp](./youtube-mcp/) | [YouTube MCP Server](https://github.com/ZubeidHendricks/youtube-mcp-server) | YouTube video search, metadata retrieval, and content interaction via an MCP-native server | 8462 | `hackerdogs/youtube-mcp` | misc |
| 260 | [zscaler-mcp-server-mcp](./zscaler-mcp-server-mcp/) | [Zscaler MCP Server](https://github.com/zscaler/zscaler-terraformer) | Zscaler cloud security platform management via AI-accessible MCP tools | 8463 | `hackerdogs/zscaler-mcp-server-mcp` | cloud-container |
| 261 | [abstract-mcp](./abstract-mcp/) | [AbstractAPI](https://www.abstractapi.com/) | multi-endpoint data enrichment for phone, email, IP, IBAN, VAT, holidays, FX, company, and timezo… | 8501 | `hackerdogs/abstract-mcp` | osint |
| 262 | [exiftool-mcp](./exiftool-mcp/) | [ExifTool](https://exiftool.org/) | extract metadata from images, PDFs, video, and audio files via a custom FastMCP server backed by… | 8502 | `hackerdogs/exiftool-mcp` | binary-re |
| 263 | [phoneinfoga-mcp](./phoneinfoga-mcp/) | [PhoneInfoga](https://github.com/sundowndev/phoneinfoga) | phone number OSINT via local, Numverify, Google Search, and OVH scanners | 8503 | `hackerdogs/phoneinfoga-mcp` | osint |
| 264 | [webc-mcp](./webc-mcp/) | — | Web content fetch and extraction helpers | 8504 | `hackerdogs/webc-mcp` | core |
| 265 | [excel-tools-mcp](./excel-tools-mcp/) | [Excel Tools](https://pypi.org/project/openpyxl/) | read, write, and analyze Excel and CSV spreadsheets using openpyxl and pandas | 8505 | `hackerdogs/excel-tools-mcp` | core |
| 266 | [visualization-tools-mcp](./visualization-tools-mcp/) | — | Generate bar, line, and pie charts | 8506 | `hackerdogs/visualization-tools-mcp` | core |
| 267 | [powerpoint-tools-mcp](./powerpoint-tools-mcp/) | — | PowerPoint slide generation utilities | 8507 | `hackerdogs/powerpoint-tools-mcp` | core |
| 268 | [adblock-mcp](./adblock-mcp/) | [EasyList](https://easylist.to/) | Adblock / filter list lookups | 8508 | `hackerdogs/adblock-mcp` | osint |
| 269 | [adguard-dns-mcp](./adguard-dns-mcp/) | — | AdGuard DNS lookups and filtering helpers | 8509 | `hackerdogs/adguard-dns-mcp` | network-recon |
| 270 | [ahmia-mcp](./ahmia-mcp/) | [Ahmia](https://ahmia.fi) | search Tor hidden services ( | 8510 | `hackerdogs/ahmia-mcp` | osint |
| 271 | [apple-itunes-mcp](./apple-itunes-mcp/) | [iTunes Search API](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/index.html) | Apple iTunes / App Store lookup API | 8511 | `hackerdogs/apple-itunes-mcp` | misc |
| 272 | [archiveorg-mcp](./archiveorg-mcp/) | [Internet Archive](https://archive.org/) | Internet Archive / Wayback Machine queries | 8512 | `hackerdogs/archiveorg-mcp` | osint |
| 273 | [arin-mcp](./arin-mcp/) | [ARIN](https://www.arin.net/) | ARIN WHOIS / network registry lookups | 8513 | `hackerdogs/arin-mcp` | network-recon |
| 274 | [baidusearch-mcp](./baidusearch-mcp/) | — | Baidu web search | 8514 | `hackerdogs/baidusearch-mcp` | osint |
| 275 | [bevigil-mcp](./bevigil-mcp/) | [BeVigil](https://osint.bevigil.com) | mobile app OSINT for domain subdomains and URLs | 8515 | `hackerdogs/bevigil-mcp` | osint |
| 276 | [bitbucket-mcp](./bitbucket-mcp/) | [Bitbucket](https://bitbucket.org) | public code search for email and hostname exposure | 8516 | `hackerdogs/bitbucket-mcp` | misc |
| 277 | [bravesearch-mcp](./bravesearch-mcp/) | [Brave Search](https://brave.com/search/api/) | privacy-respecting web search via the Brave Search API | 8517 | `hackerdogs/bravesearch-mcp` | osint |
| 278 | [browserless-mcp](./browserless-mcp/) | [Browserless](https://browserless.io) | headless Chrome automation for content rendering, screenshots, PDFs, and scraping | 8518 | `hackerdogs/browserless-mcp` | misc |
| 279 | [certgraph-mcp](./certgraph-mcp/) | [CertGraph](https://github.com/lanrat/certgraph) | subdomain and domain discovery through TLS certificate relationship graphs | 8519 | `hackerdogs/certgraph-mcp` | network-recon |
| 280 | [cloud-datacenter-mcp](./cloud-datacenter-mcp/) | — | Cloud datacenter / ASN range helpers | 8520 | `hackerdogs/cloud-datacenter-mcp` | cloud-container |
| 281 | [crawl4ai-mcp](./crawl4ai-mcp/) | [Crawl4AI](https://github.com/unclecode/crawl4ai) | high-performance, AI-ready web crawler that extracts clean markdown content from any URL | 8521 | `hackerdogs/crawl4ai-mcp` | core |
| 282 | [file-operations-mcp](./file-operations-mcp/) | — | File read/write and workspace helpers | 8522 | `hackerdogs/file-operations-mcp` | core |
| 283 | [graphviz-dot-mcp](./graphviz-dot-mcp/) | [Graphviz](https://graphviz.org) | render DOT language diagrams to SVG or PNG | 8523 | `hackerdogs/graphviz-dot-mcp` | core |
| 284 | [mermaid-mcp](./mermaid-mcp/) | [Mermaid](https://github.com/mermaid-js/mermaid-cli) | render Mermaid diagram source into SVG or PNG output | 8524 | `hackerdogs/mermaid-mcp` | core |
| 285 | [name-server-mcp](./name-server-mcp/) | — | DNS nameserver and record helpers | 8525 | `hackerdogs/name-server-mcp` | network-recon |
| 286 | [scrapy-mcp](./scrapy-mcp/) | [Scrapy](https://scrapy.org/) | programmatic web crawling and content extraction via Scrapy spiders | 8526 | `hackerdogs/scrapy-mcp` | misc |
| 287 | [victorialogs-mcp](./victorialogs-mcp/) | [VictoriaLogs](https://docs.victoriametrics.com/victorialogs/) | query and analyze logs stored in VictoriaLogs using LogsQL | 8527 | `hackerdogs/victorialogs-mcp` | misc |
| 288 | [whatsmyname-mcp](./whatsmyname-mcp/) | [WhatsMyName](https://github.com/WebBreacher/WhatsMyName) | OSINT username enumeration across hundreds of websites | 8528 | `hackerdogs/whatsmyname-mcp` | osint |
| 289 | [ai-humanizer-mcp](./ai-humanizer-mcp/) | [github.com/Text2Go/ai-humanizer-mcp-s…](https://github.com/Text2Go/ai-humanizer-mcp-server) | Hackerdogs Docker packaging of Text2Go’s **ai-humanizer-mcp-server** + HTTP gateway (see `Dockerf… | 8601 | `hackerdogs/ai-humanizer-mcp` | misc |
| 290 | [aws-api-mcp](./aws-api-mcp/) | [AWS API](https://github.com/awslabs/mcp/tree/main/src/aws-api-mcp-server) | broad AWS service access via AWS CLI commands for any service and resource type | 8602 | `hackerdogs/aws-api-mcp` | cloud-container |
| 291 | [aws-aurora-dsql-mcp](./aws-aurora-dsql-mcp/) | [Aurora DSQL](https://github.com/awslabs/mcp/tree/main/src/aurora-dsql-mcp-server) | interact with Amazon Aurora DSQL serverless distributed SQL clusters via natural language | 8603 | `hackerdogs/aws-aurora-dsql-mcp` | cloud-container |
| 292 | [aws-bedrock-agentcore-mcp](./aws-bedrock-agentcore-mcp/) | [Bedrock AgentCore](https://github.com/awslabs/mcp/tree/main/src/amazon-bedrock-agentcore-mcp-server) | build, configure, and operate Amazon Bedrock AgentCore resources including Runtime, Memory, Gatew… | 8604 | `hackerdogs/aws-bedrock-agentcore-mcp` | cloud-container |
| 293 | [aws-bedrock-custom-model-mcp](./aws-bedrock-custom-model-mcp/) | [Bedrock Custom Model Import](https://github.com/awslabs/mcp/tree/main/src/aws-bedrock-custom-model-import-mcp-server) | import and manage custom fine-tuned models in Amazon Bedrock | 8605 | `hackerdogs/aws-bedrock-custom-model-mcp` | cloud-container |
| 294 | [aws-cloudtrail-mcp](./aws-cloudtrail-mcp/) | [AWS CloudTrail](https://github.com/awslabs/mcp/tree/main/src/cloudtrail-mcp-server) | query and analyze AWS account activity logs for security investigations, compliance auditing, and… | 8606 | `hackerdogs/aws-cloudtrail-mcp` | cloud-container |
| 295 | [aws-cloudwatch-appsignals-mcp](./aws-cloudwatch-appsignals-mcp/) | [CloudWatch Application Signals](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-appsignals-mcp-server) | monitor application health, service-level objectives (SLOs), and dependency topology through Clou… | 8607 | `hackerdogs/aws-cloudwatch-appsignals-mcp` | cloud-container |
| 296 | [aws-cloudwatch-mcp](./aws-cloudwatch-mcp/) | [AWS CloudWatch](https://github.com/awslabs/mcp/tree/main/src/cloudwatch-mcp-server) | query metrics, search logs with Insights, inspect alarms, and retrieve dashboards for AI-powered… | 8608 | `hackerdogs/aws-cloudwatch-mcp` | cloud-container |
| 297 | [aws-core-mcp](./aws-core-mcp/) | [AWS Core](https://github.com/awslabs/mcp/tree/main/src/core-mcp-server) | orchestration and planning hub for the AWS MCP server suite, providing cross-service task plannin… | 8609 | `hackerdogs/aws-core-mcp` | cloud-container |
| 298 | [aws-documentation-mcp](./aws-documentation-mcp/) | [AWS Documentation](https://github.com/awslabs/mcp/tree/main/src/aws-documentation-mcp-server) | search and retrieve up-to-date AWS service documentation, API references, and best practice guides | 8610 | `hackerdogs/aws-documentation-mcp` | cloud-container |
| 299 | [aws-documentdb-mcp](./aws-documentdb-mcp/) | [Amazon DocumentDB](https://github.com/awslabs/mcp/tree/main/src/documentdb-mcp-server) | query collections, manage indexes, and inspect cluster health on your MongoDB-compatible Amazon D… | 8611 | `hackerdogs/aws-documentdb-mcp` | cloud-container |
| 300 | [aws-dynamodb-mcp](./aws-dynamodb-mcp/) | [Amazon DynamoDB](https://github.com/awslabs/mcp/tree/main/src/dynamodb-mcp-server) | table management, item queries, data modeling guidance, and capacity planning for DynamoDB from y… | 8612 | `hackerdogs/aws-dynamodb-mcp` | cloud-container |
| 301 | [aws-ecs-mcp](./aws-ecs-mcp/) | [Amazon ECS](https://github.com/awslabs/mcp/tree/main/src/ecs-mcp-server) | deploy, scale, and troubleshoot containerized applications running on Amazon Elastic Container Se… | 8613 | `hackerdogs/aws-ecs-mcp` | cloud-container |
| 302 | [aws-eks-mcp](./aws-eks-mcp/) | [Amazon EKS](https://github.com/awslabs/mcp/tree/main/src/eks-mcp-server) | inspect and manage Kubernetes clusters on Amazon EKS, including nodes, workloads, namespaces, and… | 8614 | `hackerdogs/aws-eks-mcp` | cloud-container |
| 303 | [aws-iam-mcp](./aws-iam-mcp/) | [AWS IAM](https://github.com/awslabs/mcp/tree/main/src/iam-mcp-server) | inspect and manage AWS Identity and Access Management users, roles, policies, and permission boun… | 8615 | `hackerdogs/aws-iam-mcp` | cloud-container |
| 304 | [aws-mq-mcp](./aws-mq-mcp/) | [Amazon MQ](https://github.com/awslabs/mcp/tree/main/src/amazon-mq-mcp-server) | list, describe, and monitor Amazon MQ message brokers running ActiveMQ or RabbitMQ | 8616 | `hackerdogs/aws-mq-mcp` | cloud-container |
| 305 | [aws-neptune-mcp](./aws-neptune-mcp/) | [Amazon Neptune](https://github.com/awslabs/mcp/tree/main/src/amazon-neptune-mcp-server) | query and explore Amazon Neptune graph databases using openCypher, Gremlin, or SPARQL | 8617 | `hackerdogs/aws-neptune-mcp` | cloud-container |
| 306 | [aws-network-mcp](./aws-network-mcp/) | [AWS Network](https://github.com/awslabs/mcp/tree/main/src/aws-network-mcp-server) | read-only inspection and troubleshooting of AWS networking resources including Cloud WAN, Transit… | 8618 | `hackerdogs/aws-network-mcp` | cloud-container |
| 307 | [aws-postgres-mcp](./aws-postgres-mcp/) | [AWS PostgreSQL MCP](https://github.com/awslabs/mcp/tree/main/src/postgres-mcp-server) | connect to Amazon Aurora PostgreSQL or RDS PostgreSQL databases, inspect schemas, and run read-on… | 8619 | `hackerdogs/aws-postgres-mcp` | cloud-container |
| 308 | [aws-prometheus-mcp](./aws-prometheus-mcp/) | [AWS Managed Prometheus](https://github.com/awslabs/mcp/tree/main/src/prometheus-mcp-server) | execute PromQL queries and inspect metrics stored in Amazon Managed Service for Prometheus (AMP)… | 8620 | `hackerdogs/aws-prometheus-mcp` | cloud-container |
| 309 | [aws-redshift-mcp](./aws-redshift-mcp/) | [Amazon Redshift](https://github.com/awslabs/mcp/tree/main/src/redshift-mcp-server) | discover clusters and serverless workgroups, browse schemas, and run analytical SQL queries again… | 8621 | `hackerdogs/aws-redshift-mcp` | cloud-container |
| 310 | [aws-s3-tables-mcp](./aws-s3-tables-mcp/) | [AWS S3 Tables](https://github.com/awslabs/mcp/tree/main/src/s3-tables-mcp-server) | create, query, and manage Apache Iceberg tables stored natively in Amazon S3 using the S3 Tables… | 8622 | `hackerdogs/aws-s3-tables-mcp` | cloud-container |
| 311 | [aws-serverless-mcp](./aws-serverless-mcp/) | [AWS Serverless](https://github.com/awslabs/mcp/tree/main/src/aws-serverless-mcp-server) | build, deploy, and monitor serverless applications using AWS SAM (Serverless Application Model) a… | 8623 | `hackerdogs/aws-serverless-mcp` | cloud-container |
| 312 | [aws-sns-sqs-mcp](./aws-sns-sqs-mcp/) | [Amazon SNS/SQS](https://github.com/awslabs/mcp/tree/main/src/amazon-sns-sqs-mcp-server) | list, inspect, and interact with Amazon Simple Notification Service topics and Simple Queue Servi… | 8624 | `hackerdogs/aws-sns-sqs-mcp` | cloud-container |
| 313 | [aws-stepfunctions-mcp](./aws-stepfunctions-mcp/) | [awslabs/mcp](https://github.com/awslabs/mcp) | AWS Step Functions workflow management | 8625 | `hackerdogs/aws-stepfunctions-mcp` | cloud-container |
| 314 | [aws-well-architected-security-mcp](./aws-well-architected-security-mcp/) | [AWS Well-Architected Security](https://github.com/awslabs/mcp/tree/main/src/well-architected-security-mcp-server) | assess your AWS workloads against the Security pillar of the AWS Well-Architected Framework and s… | 8626 | `hackerdogs/aws-well-architected-security-mcp` | cloud-container |
| 315 | [azure-mcp](./azure-mcp/) | [Azure MCP](https://github.com/Azure/azure-mcp) | explore and manage Microsoft Azure resources including subscriptions, resource groups, storage ac… | 8627 | `hackerdogs/azure-mcp` | cloud-container |
| 316 | [baidu-search-mcp-server-mcp](./baidu-search-mcp-server-mcp/) | [baidu-mcp-server](https://pypi.org/project/baidu-mcp-server/) | search Baidu's web index and retrieve results optimized for Chinese-language and Asia-Pacific que… | 8628 | `hackerdogs/baidu-search-mcp-server-mcp` | osint |
| 317 | [brave-search-mcp](./brave-search-mcp/) | [Brave Search](https://brave.com/search/api/) | independent web search across web, news, videos, and images via the Brave Search API | 8629 | `hackerdogs/brave-search-mcp` | osint |
| 318 | [brightdata-mcp-server-mcp](./brightdata-mcp-server-mcp/) | [Bright Data](https://github.com/brightdata/brightdata-mcp) | scalable web scraping and data collection with built-in proxy infrastructure and bot bypass | 8630 | `hackerdogs/brightdata-mcp-server-mcp` | misc |
| 319 | [chrome-devtools-mcp](./chrome-devtools-mcp/) | [Chrome DevTools Protocol](https://github.com/hangxingliu/mcp-chrome-devtools) | upstream package `@mcp-b/chrome-devtools-mcp` | 8631 | `hackerdogs/chrome-devtools-mcp` | web-app |
| 320 | [clinicaltrialsgov-mcp-server-mcp](./clinicaltrialsgov-mcp-server-mcp/) | [ClinicalTrials.gov](https://github.com/pauljunsukhan/clinicaltrialsgov-mcp) | search the NLM's global registry of clinical studies by condition, intervention, location, and st… | 8632 | `hackerdogs/clinicaltrialsgov-mcp-server-mcp` | misc |
| 321 | [cloudflare-mcp](./cloudflare-mcp/) | [Cloudflare](https://github.com/cloudflare/mcp-server-cloudflare) | manage Workers, DNS, KV, R2, D1, and Pages through the Cloudflare API | 8633 | `hackerdogs/cloudflare-mcp` | cloud-container |
| 322 | [context7-mcp](./context7-mcp/) | [Context7](https://github.com/upstash/context7-mcp) | fetch live library documentation and code examples to eliminate hallucinated API references | 8634 | `hackerdogs/context7-mcp` | core |
| 323 | [dns-mcp-server-mcp](./dns-mcp-server-mcp/) | [dns-mcp-server](https://github.com/cenemiljezweb/dns-mcp-server) | perform DNS record lookups (A, AAAA, MX, TXT, NS, CNAME, SOA) directly from your AI assistant | 8635 | `hackerdogs/dns-mcp-server-mcp` | network-recon |
| 324 | [dnstwist-mcp](./dnstwist-mcp/) | [dnstwist](https://github.com/burtthecoder/mcp-dnstwist) | upstream package `@burtthecoder/mcp-dnstwist` | 8636 | `hackerdogs/dnstwist-mcp` | network-recon |
| 325 | [exa-mcp](./exa-mcp/) | [Exa](https://github.com/exa-labs/exa-mcp-server) | neural search engine with semantic similarity ranking for web, research papers, code, and company… | 8637 | `hackerdogs/exa-mcp` | osint |
| 326 | [exiftool-agent-mcp](./exiftool-agent-mcp/) | [ExifTool](https://exiftool.org/) | extract and analyze metadata from images, video, audio, and document files via the `exiftool-mcp-… | 8638 | `hackerdogs/exiftool-agent-mcp` | binary-re |
| 327 | [fetch-mcp](./fetch-mcp/) | [mcp-server-fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | retrieve web page content as clean markdown or plain text for AI consumption | 8639 | `hackerdogs/fetch-mcp` | misc |
| 328 | [firecrawl-mcp](./firecrawl-mcp/) | [Firecrawl](https://firecrawl.dev/) | JavaScript-rendered web scraping and full-site crawling with clean markdown output | 8640 | `hackerdogs/firecrawl-mcp` | core |
| 329 | [geocoding-mcp](./geocoding-mcp/) | [geocode-mcp](https://pypi.org/project/geocode-mcp/) | convert street addresses to geographic coordinates (forward geocoding) and GPS coordinates to hum… | 8641 | `hackerdogs/geocoding-mcp` | misc |
| 330 | [gitlab-mcp](./gitlab-mcp/) | [GitLab](https://gitlab.com/) | manage repositories, issues, merge requests, and CI/CD pipelines via the GitLab API using the `@z… | 8642 | `hackerdogs/gitlab-mcp` | misc |
| 331 | [globalping-mcp](./globalping-mcp/) | [Globalping](https://www.jsdelivr.com/globalping) | run ping, traceroute, DNS lookup, MTR, and HTTP measurements from a distributed network of probes… | 8643 | `hackerdogs/globalping-mcp` | network-recon |
| 332 | [google-threat-intelligence-mcp](./google-threat-intelligence-mcp/) | [Google Threat Intelligence](https://www.virustotal.com/gui/home/search) | Google Threat Intelligence / VT GTI queries | 8644 | `hackerdogs/google-threat-intelligence-mcp` | vuln-scanning |
| 333 | [greynoise-mcp](./greynoise-mcp/) | [GreyNoise](https://github.com/GreyNoise-Intelligence/greynoise-mcp) | internet noise intelligence platform for IP classification and threat context | 8645 | `hackerdogs/greynoise-mcp` | vuln-scanning |
| 334 | [hibp-mcp](./hibp-mcp/) | [Have I Been Pwned](https://github.com/darrenjrobinson/hibp-mcp) | check email addresses, domains, and passwords against the world's largest data breach database | 8646 | `hackerdogs/hibp-mcp` | osint |
| 335 | [imf-data-mcp](./imf-data-mcp/) | [IMF Data](https://pypi.org/project/mseep-imf-data-mcp/) | query the International Monetary Fund's public economic data APIs | 8647 | `hackerdogs/imf-data-mcp` | misc |
| 336 | [iplocate-mcp](./iplocate-mcp/) | [IPLocate](https://www.iplocate.io) | IP geolocation and organization lookup via the IPLocate API | 8648 | `hackerdogs/iplocate-mcp` | osint |
| 337 | [jira-mcp](./jira-mcp/) | [Jira](https://github.com/smithery-ai/mcp-server-jira) | manage Atlassian Jira issues, projects, and workflows via the Jira REST API | 8649 | `hackerdogs/jira-mcp` | misc |
| 338 | [ms-fabric-rti-mcp](./ms-fabric-rti-mcp/) | [Microsoft Fabric RTI](https://github.com/microsoft/fabric-rti-mcp) | upstream package `microsoft-fabric-rti-mcp` | 8650 | `hackerdogs/ms-fabric-rti-mcp` | misc |
| 339 | [nasa-mcp](./nasa-mcp/) | [NASA](https://github.com/programcomputer/nasa-mcp-server) | upstream package `@programcomputer/nasa-mcp-server` | 8651 | `hackerdogs/nasa-mcp` | misc |
| 340 | [notion-mcp](./notion-mcp/) | [Notion](https://github.com/notionhq/notion-mcp-server) | upstream package `@notionhq/notion-mcp-server` | 8652 | `hackerdogs/notion-mcp` | misc |
| 341 | [octagon-mcp-server-mcp](./octagon-mcp-server-mcp/) | [Octagon](https://github.com/octagon-agents/octagon-mcp) | upstream package `octagon-mcp` | 8653 | `hackerdogs/octagon-mcp-server-mcp` | misc |
| 342 | [octocode-mcp](./octocode-mcp/) | [OctoCode](https://github.com/nicholasgasior/octocode-mcp) | upstream package `octocode-mcp` | 8654 | `hackerdogs/octocode-mcp` | misc |
| 343 | [openfda-mcp](./openfda-mcp/) | [OpenFDA](https://github.com/ythalorossy/openfda) | FDA drug, device, and food safety data via the openFDA API | 8655 | `hackerdogs/openfda-mcp` | misc |
| 344 | [osm-mcp-server-mcp](./osm-mcp-server-mcp/) | [OpenStreetMap](https://github.com/nicholasgasior/osm-mcp-server) | geographic search and POI lookup via the OpenStreetMap Nominatim and Overpass APIs | 8656 | `hackerdogs/osm-mcp-server-mcp` | misc |
| 345 | [pinecone-mcp](./pinecone-mcp/) | [Pinecone](https://github.com/pinecone-io/pinecone-mcp) | managed vector database for semantic search, RAG, and AI application development | 8657 | `hackerdogs/pinecone-mcp` | misc |
| 346 | [postman-mcp](./postman-mcp/) | [Postman](https://github.com/postmanlabs/postman-mcp-server) | manage Postman workspaces, collections, environments, and APIs from your AI assistant | 8658 | `hackerdogs/postman-mcp` | misc |
| 347 | [puppeteer-mcp](./puppeteer-mcp/) | [Puppeteer](https://pptr.dev/) | headless Chrome browser automation for navigation, screenshots, PDFs, and form interaction | 8659 | `hackerdogs/puppeteer-mcp` | web-app |
| 348 | [rapidapi-hub-reverse-image-search-by-copyseeker-mcp](./rapidapi-hub-reverse-image-search-by-copyseeker-mcp/) | [RapidAPI](https://rapidapi.com/) | Reverse image search via Copyseeker (RapidAPI) | 8660 | `hackerdogs/rapidapi-hub-reverse-image-search-by-copyseeker-mcp` | misc |
| 349 | [reddit-mcp](./reddit-mcp/) | [mcp-server-reddit](https://pypi.org/project/mcp-server-reddit/) | read-only Reddit access for browsing subreddits, searching posts, and reading comment threads | 8661 | `hackerdogs/reddit-mcp` | osint |
| 350 | [s3-mcp-server-mcp](./s3-mcp-server-mcp/) | [geunoh/s3-mcp-server](https://github.com/geunoh/s3-mcp-server) | list, read, upload, and delete objects in Amazon S3 buckets from AI assistants | 8662 | `hackerdogs/s3-mcp-server-mcp` | misc |
| 351 | [scc-mcp](./scc-mcp/) | [SCC](https://github.com/nicholasgasior/scc-mcp) | upstream package `scc-mcp` | 8663 | `hackerdogs/scc-mcp` | misc |
| 352 | [search1api-mcp](./search1api-mcp/) | [Search1API](https://search1api.com/) | unified web search, news search, webpage content extraction, and sitemap retrieval through a sing… | 8664 | `hackerdogs/search1api-mcp` | osint |
| 353 | [sentry-mcp](./sentry-mcp/) | [Sentry](https://sentry.io/) | query issues, stack traces, release health, and Seer AI analysis from Sentry directly within AI c… | 8665 | `hackerdogs/sentry-mcp` | misc |
| 354 | [serper-search-mcp](./serper-search-mcp/) | [Serper](https://serper.dev/) | Google Search API with web search, news, images, shopping results, and webpage scraping via a sin… | 8666 | `hackerdogs/serper-search-mcp` | osint |
| 355 | [splunk-mcp](./splunk-mcp/) | [Splunk](https://github.com/splunk/splunk-mcp) | run SPL searches, query indexes, and investigate security events in Splunk | 8667 | `hackerdogs/splunk-mcp` | vuln-scanning |
| 356 | [steampipe-mcp](./steampipe-mcp/) | [Steampipe](https://github.com/turbot/steampipe-mcp) | query cloud infrastructure, SaaS APIs, and security data using SQL | 8668 | `hackerdogs/steampipe-mcp` | cloud-container |
| 357 | [stripe-mcp](./stripe-mcp/) | [Stripe](https://github.com/stripe/agent-toolkit) | manage payments, customers, subscriptions, and invoices via the Stripe API | 8669 | `hackerdogs/stripe-mcp` | misc |
| 358 | [terraform-mcp](./terraform-mcp/) | [Terraform](https://github.com/hashicorp/terraform-mcp-server) | access Terraform provider documentation, resource schemas, and module registry data | 8670 | `hackerdogs/terraform-mcp` | cloud-container |
| 359 | [tomtom-mcp](./tomtom-mcp/) | [TomTom](https://github.com/tomtom-org/tomtom-mcp) | geocoding, routing, traffic, and point-of-interest search via TomTom's mapping APIs | 8671 | `hackerdogs/tomtom-mcp` | misc |
| 360 | [variflight-mcp](./variflight-mcp/) | [VariFlight](https://github.com/AirSavvy/variflight-mcp) | real-time flight tracking, historical flight data, and airport/airline information via VariFlight… | 8672 | `hackerdogs/variflight-mcp` | misc |
| 361 | [whois-mcp](./whois-mcp/) | [whois-mcp](https://www.npmjs.com/package/whois-mcp) | domain WHOIS registration lookups via the `whois-mcp` npm package | 8673 | `hackerdogs/whois-mcp` | network-recon |
| 362 | [winston-ai-mcp](./winston-ai-mcp/) | [Winston AI](https://gowinston.ai) | AI content detection and plagiarism checking via the `winston-ai-mcp` npm package | 8674 | `hackerdogs/winston-ai-mcp` | misc |
| 363 | [youtube-transcript-mcp](./youtube-transcript-mcp/) | [mcp-server-youtube-transcript](https://github.com/kimtaeyoon83/mcp-server-youtube-transcript) | extract YouTube video transcripts and captions in multiple languages via the `@kimtaeyoon83/mcp-s… | 8675 | `hackerdogs/youtube-transcript-mcp` | misc |
| 364 | [feroxbuster-mcp](./feroxbuster-mcp/) | [Feroxbuster](https://github.com/epi052/feroxbuster) | Recursive content discovery with filtering | 8676 | `hackerdogs/feroxbuster-mcp` | web-app |
| 365 | [ghunt-mcp](./ghunt-mcp/) | [GHunt](https://github.com/mxrch/GHunt) | Google account OSINT (emails, Gaia IDs, documents) | 8677 | `hackerdogs/ghunt-mcp` | osint |
| 366 | [maigret-mcp](./maigret-mcp/) | [Maigret](https://github.com/soxoj/maigret) | Username OSINT across 3000+ sites with false-positive detection | 8678 | `hackerdogs/maigret-mcp` | osint |
| 367 | [nikto-mcp](./nikto-mcp/) | [Nikto](https://github.com/sullo/nikto) | Web server vulnerability scanner | 8679 | `hackerdogs/nikto-mcp` | vuln-scanning |
| 368 | [wpscan-mcp](./wpscan-mcp/) | [Wpscan](https://github.com/wpscanteam/wpscan) | WordPress security scanner | 8680 | `hackerdogs/wpscan-mcp` | web-app |
| 369 | [alterx-mcp](./alterx-mcp/) | [Alterx](https://github.com/projectdiscovery/alterx) | fast, pattern-based subdomain permutation wordlist generator by ProjectDiscovery | 8681 | `hackerdogs/alterx-mcp` | network-recon |
| 370 | [amass-mcp](./amass-mcp/) | [Amass](https://github.com/owasp-amass/amass) | advanced subdomain enumeration and attack surface mapping tool by OWASP | 8682 | `hackerdogs/amass-mcp` | network-recon |
| 371 | [arjun-mcp](./arjun-mcp/) | [Arjun](https://github.com/s0md3v/Arjun) | HTTP parameter discovery tool that finds hidden GET and POST parameters on web endpoints | 8683 | `hackerdogs/arjun-mcp` | web-app |
| 372 | [assetfinder-mcp](./assetfinder-mcp/) | [Assetfinder](https://github.com/tomnomnom/assetfinder) | passive subdomain enumeration by querying certificate transparency logs, DNS datasets, and web sc… | 8684 | `hackerdogs/assetfinder-mcp` | network-recon |
| 373 | [cero-mcp](./cero-mcp/) | [Cero](https://github.com/glebarez/cero) | subdomain discovery via TLS certificate scraping | 8685 | `hackerdogs/cero-mcp` | misc |
| 374 | [crtsh-mcp](./crtsh-mcp/) | [crt.sh](https://crt.sh) | discover subdomains and certificate history by querying the public SSL/TLS Certificate Transparen… | 8686 | `hackerdogs/crtsh-mcp` | network-recon |
| 375 | [ffuf-mcp](./ffuf-mcp/) | [ffuf](https://github.com/ffuf/ffuf) | fast web fuzzer for directory brute-forcing, parameter discovery, and vhost enumeration | 8687 | `hackerdogs/ffuf-mcp` | web-app |
| 376 | [gowitness-mcp](./gowitness-mcp/) | [Gowitness](https://github.com/sensepost/gowitness) | headless Chrome screenshot tool for web reconnaissance | 8688 | `hackerdogs/gowitness-mcp` | web-app |
| 377 | [http-headers-security-mcp](./http-headers-security-mcp/) | — | HTTP security headers analysis | 8689 | `hackerdogs/http-headers-security-mcp` | web-app |
| 378 | [httpx-mcp](./httpx-mcp/) | [httpx](https://github.com/projectdiscovery/httpx) | fast multi-purpose HTTP probing toolkit from ProjectDiscovery | 8690 | `hackerdogs/httpx-mcp` | network-recon |
| 379 | [katana-mcp](./katana-mcp/) | [Katana](https://github.com/projectdiscovery/katana) | fast web crawler and spider from ProjectDiscovery for URL discovery and attack surface mapping | 8691 | `hackerdogs/katana-mcp` | web-app |
| 380 | [masscan-mcp](./masscan-mcp/) | [Masscan](https://github.com/robertdavidgraham/masscan) | the fastest TCP port scanner capable of scanning the entire internet in under six minutes | 8692 | `hackerdogs/masscan-mcp` | network-recon |
| 381 | [mobsf-mcp](./mobsf-mcp/) | [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF) | automated static and dynamic security analysis of Android and iOS mobile applications | 8693 | `hackerdogs/mobsf-mcp` | web-app |
| 382 | [nmap-mcp](./nmap-mcp/) | [Nmap](https://nmap.org/) | network discovery, port scanning, service/version detection, and OS fingerprinting | 8694 | `hackerdogs/nmap-mcp` | network-recon |
| 383 | [nuclei-mcp](./nuclei-mcp/) | [Nuclei](https://github.com/projectdiscovery/nuclei) | fast, template-based vulnerability scanner from ProjectDiscovery | 8695 | `hackerdogs/nuclei-mcp` | vuln-scanning |
| 384 | [shuffledns-mcp](./shuffledns-mcp/) | [shuffledns](https://github.com/projectdiscovery/shuffledns) | high-speed subdomain enumeration and DNS resolution using massDNS | 8696 | `hackerdogs/shuffledns-mcp` | network-recon |
| 385 | [sqlmap-mcp](./sqlmap-mcp/) | [sqlmap](https://github.com/sqlmapproject/sqlmap) | automated detection and exploitation of SQL injection vulnerabilities | 8697 | `hackerdogs/sqlmap-mcp` | web-app |
| 386 | [waybackurls-mcp](./waybackurls-mcp/) | [waybackurls](https://github.com/tomnomnom/waybackurls) | fetch all URLs ever crawled by the Wayback Machine for a domain | 8698 | `hackerdogs/waybackurls-mcp` | web-app |
| 387 | [censys-platform-mcp](./censys-platform-mcp/) | [Censys Platform](https://censys.io) | internet-wide host and certificate search with attack surface intelligence | 8699 | `hackerdogs/censys-platform-mcp` | network-recon |
| 388 | [github-mcp](./github-mcp/) | [GitHub MCP](https://github.com/github/github-mcp-server) | interact with GitHub repositories, issues, pull requests, and code search via the GitHub Copilot API | 8700 | `hackerdogs/github-mcp` | core |
| 389 | [mcp-docker-mcp](./mcp-docker-mcp/) | [Docker MCP Toolkit](https://mcp.docker.com) | local compliance stub and gateway reference for the Docker MCP cloud endpoint | 8701 | `hackerdogs/mcp-docker-mcp` | cloud-container |
| 390 | [mitre-attack-remote-mcp](./mitre-attack-remote-mcp/) | [MITRE ATT&CK](https://attack.mitre.org/) | local compliance stub that surfaces the official remote MCP endpoint at `https://attack-mcp | 8702 | `hackerdogs/mitre-attack-remote-mcp` | vuln-scanning |
| 391 | [prowler-mcp](./prowler-mcp/) | [Prowler](https://github.com/prowler-cloud/prowler) | cloud security posture management and compliance auditing for AWS, Azure, GCP, and Kubernetes | 8703 | `hackerdogs/prowler-mcp` | cloud-container |
| 392 | [serpapi-mcp](./serpapi-mcp/) | [SerpApi](https://serpapi.com/) | a local compliance stub that returns the official remote MCP endpoint URL for the full SerpApi in… | 8704 | `hackerdogs/serpapi-mcp` | osint |
| 393 | [tavily-remote-mcp](./tavily-remote-mcp/) | [Tavily](https://tavily.com) | AI-optimized web search API designed for retrieval-augmented generation and research agents | 8705 | `hackerdogs/tavily-remote-mcp` | osint |
| 394 | [whoisxmlapi-mcp](./whoisxmlapi-mcp/) | [WhoisXML API](https://whoisxmlapi.com) | local compliance stub that points to the hosted production MCP endpoint at https://mcp | 8706 | `hackerdogs/whoisxmlapi-mcp` | network-recon |
| 395 | [xpoz-mcp-server-mcp](./xpoz-mcp-server-mcp/) | [XPoz](https://xpoz.io) | local compliance stub that points to the hosted production MCP endpoint at https://mcp | 8707 | `hackerdogs/xpoz-mcp-server-mcp` | appsec |
| 396 | [acuvity-mcp-server-alterx-mcp](./acuvity-mcp-server-alterx-mcp/) | [Alterx](https://github.com/projectdiscovery/alterx) | fast, customizable subdomain wordlist generator for reconnaissance workflows | 8708 | `hackerdogs/acuvity-mcp-server-alterx-mcp` | recon |
| 397 | [acuvity-mcp-server-amass-mcp](./acuvity-mcp-server-amass-mcp/) | [Amass](https://github.com/owasp-amass/amass) | in-depth attack surface mapping and subdomain enumeration by OWASP | 8709 | `hackerdogs/acuvity-mcp-server-amass-mcp` | recon |
| 398 | [acuvity-mcp-server-arjun-mcp](./acuvity-mcp-server-arjun-mcp/) | [Arjun](https://github.com/s0md3v/Arjun) | HTTP parameter discovery tool for finding hidden GET and POST parameters in web applications | 8710 | `hackerdogs/acuvity-mcp-server-arjun-mcp` | recon |
| 399 | [acuvity-mcp-server-assetfinder-mcp](./acuvity-mcp-server-assetfinder-mcp/) | [Assetfinder](https://github.com/tomnomnom/assetfinder) | fast passive subdomain enumeration tool by Tom Hudson | 8711 | `hackerdogs/acuvity-mcp-server-assetfinder-mcp` | recon |
| 400 | [hackerdogs-mcp-server-mcp](./hackerdogs-mcp-server-mcp/) | [Hackerdogs](https://hackerdogs.ai) | Hackerdogs platform MCP integration (remote URL) | 8712 | `https://mcp.hackerdogs.ai/mcp` | misc |

### Port Allocation

| Range | Purpose | Count |
|-------|---------|------:|
| 8100–8116 | Core / early security tools | 17 |
| 8200–8365 | Offensive / extended security | 166 |
| 8366–8379 | Threat intel & OSINT | 14 |
| 8400–8712 | Cloud, OSINT, developer & utility | 203 |
| **Total** | | **400** |

> **Note:** A few per-tool `docker-compose.yml` files still hardcode older ports. Prefer the ports in this table (and `port-map.json`) for standalone and farm deploys.

### Reserved Ports (do not use)

- 80 (HTTP)
- 8000-8010 (general app servers)
- 8485 (MCP Farm — Caddy reverse proxy)
- 9000-9010 (monitoring)
- 9090 (auth-gateway)

## Deploy Individual Servers (Without the Farm)

Every MCP server can run **standalone** — no farm, no auth gateway, no Caddy. Use this when you need one or a few tools on a laptop, in CI, or behind your own reverse proxy.

### Prerequisites

- Docker Desktop or Docker Engine (20.10+)
- `docker compose` v2+ (optional, for per-tool compose files)

### Option 1 — Pull a pre-built image (fastest)

All images are published to Docker Hub as `hackerdogs/<tool-name>:latest` (multi-arch: amd64 + arm64).

```bash
# Example: naabu-mcp on port 8105
docker pull hackerdogs/naabu-mcp:latest
docker run -d --name naabu-mcp -p 8105:8105 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8105 \
  hackerdogs/naabu-mcp:latest
```

Find the port for any server in the [Tool Registry](#tool-registry) or `mcpfarm/port-map.json`.

### Option 2 — Build and run from source

```bash
cd naabu-mcp
docker build -t hackerdogs/naabu-mcp:latest .
docker run -d --name naabu-mcp -p 8105:8105 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8105 \
  hackerdogs/naabu-mcp:latest
```

Or use the tool's bundled compose file:

```bash
cd naabu-mcp
docker compose up -d
```

### Option 3 — Farm compose (many servers, no auth gateway needed for direct ports)

To run several MCP containers from the farm's compose file **without** going through Caddy auth, use `mcpfarm/docker-compose.yml` and publish their ports as defined in `port-map.json`:

```bash
cd mcpfarm

# One or more MCP servers (direct host ports)
docker compose up -d --no-deps naabu-mcp dnsx-mcp

# Or via deploy.sh (preferred when you also want farm infra)
./deploy.sh start naabu-mcp dnsx-mcp
```

For the full authenticated farm (Caddy + API keys + UI), see [MCP Farm](#mcp-farm).

### Accessing a standalone server

Each server exposes MCP over **stdio** (default) or **streamable-http** when `MCP_TRANSPORT=streamable-http`.

#### HTTP (streamable-http) — direct URL

Endpoint pattern:

```
http://<host>:<port>/mcp
```

No API key is required when running outside the farm.

**Cursor / Claude Desktop** (`mcp.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "naabu": {
      "type": "http",
      "url": "http://localhost:8105/mcp"
    }
  }
}
```

**MCP Inspector** (browser):

```bash
npx @modelcontextprotocol/inspector
```

Set transport to **Streamable HTTP** and URL to `http://localhost:8105/mcp`.

**curl** (initialize → list tools → call tool):

```bash
PORT=8105
SESSION_ID=$(curl -s -D - -X POST "http://localhost:${PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST "http://localhost:${PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

curl -s -X POST "http://localhost:${PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

See each tool's `README.md` for tool-specific examples (e.g. [julius-mcp](./julius-mcp/README.md)).

#### stdio — Docker subprocess (desktop clients)

Each tool ships an `mcpServer.json`. Example for julius-mcp:

```json
{
  "mcpServers": {
    "julius-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/julius-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

Copy the contents of `<tool>-mcp/mcpServer.json` into your Cursor or Claude Desktop MCP config.

### Tool-specific environment variables

Many servers accept vendor API keys via environment variables. Set them at `docker run` time or in the tool's `docker-compose.yml`:

```bash
docker run -d --name virustotal-mcp -p 8369:8369 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8369 \
  -e VIRUSTOTAL_API_KEY=your-key \
  hackerdogs/virustotal-mcp:latest
```

Check the tool's README or `mcpfarm/port-map.json` (`env` array) for required keys.

### Local vs production (standalone)

| Concern | Local development | Production |
|---------|-------------------|------------|
| **Image source** | `docker build` or `docker pull hackerdogs/...` | Pull pinned tags from Docker Hub or your private registry |
| **Networking** | Publish port to `localhost` (`-p 8105:8105`) | Place behind TLS reverse proxy (Caddy, nginx, ALB); do not expose MCP ports publicly without auth |
| **Secrets** | Pass `-e` flags or a local `.env` file | Use Docker secrets, K8s secrets, or your vault — never commit keys |
| **Persistence** | Containers are ephemeral; use `download_file` + URL ingestion for inputs | Mount volumes only when the tool requires local state (e.g. IVRE) |
| **Scaling** | One container per tool is typical | Run one replica per tool; use orchestrator health checks on `/mcp` initialize |

### Special case: IVRE

[ivre-mcp](./ivre-mcp/) does not bundle IVRE itself — it connects to an external IVRE Web API. See [ivre-mcp/DEPLOY_IVRE.md](./ivre-mcp/DEPLOY_IVRE.md) for standalone deployment.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | Transport protocol: `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (when using streamable-http) | per-tool (see table) |
| `OPENAI_API_KEY` | Required for openrisk-mcp only | — |
| `HD_MAX_DOWNLOAD_MB` | Max file download size in MB (URL fetch) | `500` |
| `HD_FETCH_TIMEOUT` | Download timeout in seconds (URL fetch) | `120` |
| `HD_FETCH_ALLOW_PRIVATE` | Allow downloads from private/internal IPs | `false` |
| `HD_FETCH_AUTH_HEADER` | Auth header for private URL downloads | — |

### URL-Based File Ingestion

Tools that analyze local files (source code scanners, binary analyzers, forensics tools, etc.) support downloading files directly from URLs — no host volume mounts required. This works in both cloud and local desktop deployments.

**How it works:** 57 file-dependent tools include a shared `hd_fetch` module that handles HTTP(S) downloads, git clone, and archive extraction into the container workspace.

**Supported URL types:**
- Direct HTTP(S) file downloads
- Archives (`.zip`, `.tar.gz`, `.tar.bz2`) — auto-extracted
- GitHub/GitLab repository URLs — shallow-cloned via `git clone --depth=1`
- `data:` URIs (base64-encoded) — for small inline payloads

**Usage patterns:**

1. **`source_url` parameter** (generic-argument tools like semgrep, trivy, radare2):

```
run_semgrep(
  source_url="https://github.com/org/repo",
  arguments="scan {source} --config auto"
)
```

2. **Direct URL in path parameters** (explicit-path tools like titus):

```
scan_path(path="https://github.com/org/repo")
```

3. **`download_file` tool** (all file-dependent tools — download once, analyze multiple times):

```
download_file(url="https://example.com/firmware.bin")
# Returns: {"path": "/app/workdir/abc123/firmware.bin", "job_id": "abc123"}

run_binwalk(arguments="/app/workdir/abc123/firmware.bin")
run_checksec(arguments="--file /app/workdir/abc123/firmware.bin")

cleanup_downloads(job_id="abc123")
```

## Directory Structure

Each tool follows this structure:

```
<tool>-mcp/
├── Dockerfile              # Multi-stage Docker build
├── mcp_server.py           # FastMCP server wrapping the CLI tool
├── hd_fetch.py             # URL download utility (file-dependent tools)
├── requirements.txt        # Python dependencies
├── publish_to_hackerdogs.sh # Build & publish script
├── mcpServer.json          # MCP client configuration
├── docker-compose.yml      # Standalone compose file
├── test.sh                 # Test script
├── README.md               # Tool-specific documentation
└── progress.md             # Implementation progress tracking
```

## Publishing

Each tool has a `publish_to_hackerdogs.sh` script:

```bash
cd julius-mcp
./publish_to_hackerdogs.sh --build                    # Build locally
./publish_to_hackerdogs.sh --publish hackerdogs       # Publish to Docker Hub
./publish_to_hackerdogs.sh --build --publish hackerdogs # Build and publish
./publish_to_hackerdogs.sh --help                     # Show help
```

## Testing

Each tool has a `test.sh` script:

```bash
cd julius-mcp
./test.sh
```

## IVRE — Network Reconnaissance Platform

[ivre-mcp](./ivre-mcp/) is architecturally different from every other tool above. Instead of wrapping a CLI binary, it acts as an **HTTP client** to an existing [IVRE](https://ivre.rocks/) deployment's Web API — a full network reconnaissance platform that combines active scanning (Nmap, Masscan, ZGrab2, Nuclei), passive intelligence (Zeek, p0f), passive DNS, network flows, and IP geolocation into a single queryable database.

| | |
|---|---|
| **Directory** | [ivre-mcp](./ivre-mcp/) |
| **Source** | [ivre/ivre](https://github.com/ivre/ivre) |
| **Port** | 8366 |
| **Image** | `hackerdogs/ivre-mcp` |
| **Architecture** | Web API client (httpx) connecting to a running IVRE stack |
| **Requires** | A deployed IVRE instance (`ivre/web` + `ivre/db` + `ivre/client`) |

**Why it's different:**
- Does **not** bundle a database or IVRE itself — it queries an external IVRE Web API over HTTP
- Requires `IVRE_WEB_URL` environment variable pointing to a running IVRE web interface
- Provides **12 tools**: host queries, passive recon, passive DNS, flow analysis, IP geolocation, aggregations (top/distinct values), and specialized views (IPs-only, IPs+ports, timeline)
- Includes [DEPLOY_IVRE.md](./ivre-mcp/DEPLOY_IVRE.md) with a step-by-step guide to deploying IVRE with Docker

```
MCP Client (Cursor/Claude) ──MCP──▶ ivre-mcp ──HTTP──▶ IVRE Web (Nginx+uWSGI) ──▶ MongoDB
```

**stdio mode:**

```json
{
  "mcpServers": {
    "ivre-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--network", "ivre-deployment_default",
               "-e", "IVRE_WEB_URL", "-e", "MCP_TRANSPORT",
               "hackerdogs/ivre-mcp:latest"],
      "env": {
        "IVRE_WEB_URL": "http://ivreweb:80",
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

**streamable-http mode:**

```bash
docker run -d --rm --network ivre-deployment_default \
  -e IVRE_WEB_URL=http://ivreweb:80 \
  -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8366 \
  -p 8366:8366 hackerdogs/ivre-mcp:latest
```

Then connect your MCP client to `http://localhost:8366/mcp`.

## MCP Farm

The **MCP Farm** is a self-hosted control plane for running all 400 servers behind a **single authenticated endpoint**. It combines Caddy (reverse proxy), a FastAPI auth gateway, Redis-backed vector search, and the [mcpfarm-ui](./mcpfarm-ui/) web dashboard.

| Guide | Audience |
|-------|----------|
| [mcpfarm/DEPLOY.md](./mcpfarm/DEPLOY.md) | Operators — install, configure, API reference |
| [mcpfarm-ui/docs/USERS-GUIDE.md](./mcpfarm-ui/docs/USERS-GUIDE.md) | End users — catalog, chat, keys, tool execution |

### Architecture

```
Client → Caddy (:8485) → forward_auth → auth-gateway (:9090) → MCP server containers
                                              │
                                         SQLite + Redis
                                         (keys, audit, vectors)
```

### What you get

- **Single endpoint**: `https://your-domain/{server-name}/mcp` for all 400 servers
- **API key auth**: create, revoke, scope, and rate-limit keys
- **Admin API**: server CRUD, batch ops, search/filter, health checks, audit log
- **LLM key vault**: store provider API keys encrypted at rest for server-side chat
- **Vector search**: Redis-backed tool index for dynamic MCP tool binding
- **Web dashboard**: manage servers, keys, and run tools from a browser

### Local deployment (Docker)

```bash
git clone <repo-url>
cd hd-mcpservers-docker/mcpfarm

ADMIN_SECRET=<your-secret> ./deploy.sh up --skip-build
./deploy.sh start naabu-mcp
./deploy.sh status
```

| Command | Purpose |
|---------|---------|
| `./deploy.sh up` | Start Caddy + auth-gateway + UI, seed DB, load routes |
| `./deploy.sh start <name>…` / `--all` | Start MCP servers |
| `./deploy.sh stop …` / `down` | Stop servers or tear down the farm |
| `./deploy.sh status` | Health + running containers |

**What starts on `up`:**

| Container | Port | Purpose |
|-----------|------|---------|
| `mcpfarm-caddy` | `8485` (default) | Reverse proxy + `forward_auth` |
| `mcpfarm-auth` | `9090` (internal) | Auth gateway + admin API |
| `mcpfarm-ui` | via Caddy `/` | Web dashboard |
| `{tool}-mcp` | per `port-map.json` | MCP servers (on demand via `start`) |

Save the **Admin API Key** printed by `up`/`seed` — shown only once.

**Open the dashboard:** [http://localhost:8485](http://localhost:8485)

**Connect a client:**

```json
{
  "mcpServers": {
    "naabu": {
      "type": "http",
      "url": "http://localhost:8485/naabu-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <API_KEY>"
      }
    }
  }
}
```

### Production deployment (Docker)

Same farm deploy. Put TLS / a public edge **in front of** `:8485` yourself — the farm does not manage tunnels or certificates.

```bash
cd mcpfarm
ADMIN_SECRET=<strong-secret> \
MCPFARM_SECRETS_KEY=<fernet-key> \
./deploy.sh up --skip-build
```

Point Cloudflare Tunnel, Caddy, nginx, ALB, etc. at `http://<farm-host>:8485`. Forward `Authorization` and `mcp-session-id` unchanged.

**Production checklist:**

- [ ] Strong `ADMIN_SECRET` in a secrets manager
- [ ] Set `MCPFARM_SECRETS_KEY` for the LLM key vault — see [mcpfarm/.env.example](./mcpfarm/.env.example)
- [ ] Configure `REDIS_URL` if using an external Redis
- [ ] Use `./deploy.sh up --skip-build` on fresh machines to pull from Docker Hub
- [ ] Start only the servers you need (`./deploy.sh start …`)
- [ ] Create scoped API keys via `POST /admin/keys`
- [ ] Run `POST /admin/vectors/reindex` after first deploy for chat tool binding

**Environment variables** (see [mcpfarm/DEPLOY.md](./mcpfarm/DEPLOY.md)):

| Variable | Required | Description |
|----------|----------|-------------|
| `ADMIN_SECRET` | Recommended | Admin API password |
| `FARM_PORT` | No | Host port (default `8485`) |
| `MCPFARM_SECRETS_KEY` | Production | Fernet key for encrypted LLM provider keys |
| `REDIS_URL` | No | Redis for vector index |
| `OPENAI_API_KEY` | No | Embeddings + server-side chat proxy |

Full CLI and API reference: [mcpfarm/DEPLOY.md](./mcpfarm/DEPLOY.md).

### Farm images

| Image | Description |
|-------|-------------|
| `hackerdogs/auth-gateway` | FastAPI auth gateway + admin API |
| `hackerdogs/mcpfarm-ui` | SvelteKit web dashboard |

Both are multi-arch (amd64 + arm64) and published to Docker Hub.

---

## License

See [LICENSE](./LICENSE) for details.
